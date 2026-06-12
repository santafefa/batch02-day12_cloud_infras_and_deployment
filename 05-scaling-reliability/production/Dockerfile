# ============================================================
# Dockerfile — Multi-stage build for 05-scaling-reliability/production
# ============================================================

# ──────────────────────────────────────────────────────────
# STAGE 1: Builder - Cài đặt tất cả dependencies
# ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy và cài requirements
# Dùng --user để install vào /root/.local (dễ copy sang stage 2)
COPY 05-scaling-reliability/production/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ──────────────────────────────────────────────────────────
# STAGE 2: Runtime - Chỉ copy những gì cần để CHẠY
# ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Tạo non-root user — security best practice
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages từ builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy source code (app.py)
COPY 05-scaling-reliability/production/app.py .

# Copy utils từ project root
RUN mkdir -p /app/utils
COPY utils/mock_llm.py /app/utils/mock_llm.py

# Đặt ownership cho appuser
RUN chown -R appuser:appuser /app

# Chuyển sang non-root user
USER appuser

# PATH để Python tìm được packages của --user install
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]