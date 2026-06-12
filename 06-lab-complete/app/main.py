"""
BASIC — Health Check + Graceful Shutdown

Hai tính năng tối thiểu cần có trước khi deploy:
  1. GET /health  — liveness: "agent có còn sống không?"
  2. GET /ready   — readiness: "agent có sẵn sàng nhận request chưa?"
  3. Graceful shutdown: hoàn thành request hiện tại trước khi tắt

Chạy:
    python app.py

Test health check:
    curl http://localhost:8000/health
    curl http://localhost:8000/ready

Simulate shutdown:
    # Trong terminal khác
    kill -SIGTERM <pid>
    # Xem agent log graceful shutdown message
"""
import os
import time
import signal
import json # Added import for json
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import psutil # Import psutil for memory check (for health check)
import redis

from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
import uvicorn
# Import custom modules
from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget
# Import mock LLM (now self-contained in app/)
from .mock_llm import ask

# Configure structured JSON logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

# Remove existing handlers to avoid duplicate logs if basicConfig was called elsewhere
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger(__name__)
_logger_level = settings.LOG_LEVEL.upper() if hasattr(settings, 'LOG_LEVEL') else "INFO"
logger.setLevel(_logger_level)
logger.addHandler(handler)

# Initialize Redis client for conversation history and other stateful operations
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

START_TIME = time.time() # For uptime calculation
_is_ready = False
_in_flight_requests = 0  # đếm số request đang xử lý


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    # ── Startup ──
    logger.info("Agent starting up...")
    logger.info("Loading model and checking dependencies...")
    try:
        redis_client.ping()
        logger.info("Redis connection successful.", extra={"event": "redis_connection_success"})
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}", extra={"event": "redis_connection_error"})
        # Depending on criticality, you might want to exit here or mark as not ready
        # For now, we'll let readiness probe handle it.

    time.sleep(0.2)  # Simulate startup time
    _is_ready = True
    logger.info("✅ Agent is ready!", extra={"event": "agent_ready"})

    yield
    # ── Shutdown ──
    _is_ready = False
    logger.info("🔄 Graceful shutdown initiated...", extra={"event": "shutdown_initiated"})

    # Chờ request đang xử lý hoàn thành (tối đa 30 giây)
    timeout = 30
    elapsed = 0
    while _in_flight_requests > 0 and elapsed < timeout:
        logger.info(f"Waiting for {_in_flight_requests} in-flight requests...", extra={"event": "waiting_for_requests", "in_flight": _in_flight_requests})
        time.sleep(1)
        elapsed += 1

    redis_client.close() # Close Redis connection
    logger.info("✅ Shutdown complete", extra={"event": "shutdown_complete"})


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)


@app.middleware("http")
async def track_requests(request, call_next):
    """Theo dõi số request đang xử lý."""
    global _in_flight_requests
    _in_flight_requests += 1
    try:
        response = await call_next(request)
        return response
    finally:
        _in_flight_requests -= 1


# ──────────────────────────────────────────────────────────
# Business Logic
# ──────────────────────────────────────────────────────────

@app.get("/") # Root endpoint for basic info
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
    }


class AskRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask_agent(
    request: AskRequest,
    user_id: str = Depends(verify_api_key), # user_id is the API key for simplicity
    _rate_limit: None = Depends(check_rate_limit),
    _budget: None = Depends(check_budget)
):
    if not _is_ready:
        raise HTTPException(503, "Agent not ready")

    # Retrieve conversation history from Redis
    history_key = f"conversation:{user_id}"
    conversation_history = redis_client.lrange(history_key, 0, -1)
    conversation_history = [json.loads(item) for item in conversation_history]

    # Add current question to history (for LLM context)
    current_conversation = conversation_history + [{"role": "user", "content": request.question}]

    # Simulate LLM call with mock_llm
    llm_response = ask(request.question) # Assuming mock_llm can take just question

    # Add LLM response to history
    current_conversation.append({"role": "assistant", "content": llm_response})

    # Store updated conversation history in Redis (trimming if necessary)
    redis_client.rpush(history_key, json.dumps({"role": "user", "content": request.question}))
    redis_client.rpush(history_key, json.dumps({"role": "assistant", "content": llm_response}))
    redis_client.ltrim(history_key, -settings.CONVERSATION_HISTORY_LENGTH, -1) # Keep last N entries
    redis_client.expire(history_key, settings.CONVERSATION_HISTORY_TTL_SECONDS) # Expire after some time

    return {"answer": llm_response, "conversation_history": current_conversation}


# ──────────────────────────────────────────────────────────
# HEALTH CHECKS — Phần quan trọng nhất của file này
# ──────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """
    LIVENESS PROBE — "Agent có còn sống không?"

    Cloud platform (Railway, Render, K8s) gọi endpoint này định kỳ.
    Nếu trả về non-200 hoặc timeout → platform restart container.

    Nên trả về:
    - status: "ok" hoặc "degraded"
    - uptime: seconds
    - version: để biết đang chạy version nào
    """
    uptime = round(time.time() - START_TIME, 1)

    # Kiểm tra dependencies quan trọng
    checks = {}

    # Check memory (ví dụ đơn giản)
    try: # psutil is imported at the top
        mem = psutil.virtual_memory()
        checks["memory"] = {
            "status": "ok" if mem.percent < 90 else "degraded",
            "used_percent": mem.percent,
        }
    except ImportError:
        checks["memory"] = {"status": "ok", "note": "psutil not installed"}
    except Exception as e:
        checks["memory"] = {"status": "degraded", "error": str(e)}

    overall_status = "ok" if all(
        v.get("status") == "ok" for v in checks.values()
    ) else "degraded"

    return {
        "status": overall_status,
        "uptime_seconds": uptime,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@app.get("/ready")
def ready():
    """
    READINESS PROBE — "Agent có sẵn sàng nhận request chưa?"

    Load balancer dùng endpoint này để quyết định có route
    traffic vào instance này không.

    Trả về 503 khi:
    - Đang khởi động (model chưa load xong)
    - Đang shutdown
    - Database/dependencies chưa connect
    """
    if not _is_ready:
        raise HTTPException(
            status_code=503,
            detail="Agent not ready. Check back in a few seconds.",
        )
    # Check Redis connection
    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Readiness check failed: Redis not connected: {e}", extra={"event": "readiness_redis_fail"})
        raise HTTPException(status_code=503, detail=f"Dependency not ready: Redis connection failed: {e}")
    return {
        "ready": True,
        "in_flight_requests": _in_flight_requests,
    }


# ──────────────────────────────────────────────────────────
# GRACEFUL SHUTDOWN
# ──────────────────────────────────────────────────────────

def handle_sigterm(signum, frame):
    """
    SIGTERM là signal platform gửi khi muốn dừng container.
    Khác với SIGKILL (không thể catch được).

    uvicorn bắt SIGTERM tự động và gọi lifespan shutdown.
    Hàm này để log thêm thông tin.
    """
    logger.info(f"Received signal {signum} — uvicorn will handle graceful shutdown", extra={"event": "sigterm_received", "signal": signum})


signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm) # Also handle Ctrl+C for local development


if __name__ == "__main__":
    logger.info(f"Starting {settings.APP_NAME} on port {settings.PORT}", extra={"event": "uvicorn_start"})
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG, # Only reload in debug mode
        # ✅ Cho phép graceful shutdown
        timeout_graceful_shutdown=30,
        log_config=None # Disable uvicorn's default logging to use our custom logger
    )
