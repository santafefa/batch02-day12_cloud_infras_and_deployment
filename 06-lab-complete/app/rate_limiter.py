import redis
from datetime import datetime
from fastapi import HTTPException, Depends
from .config import settings
from .auth import verify_api_key

# Initialize Redis client
r = redis.from_url(settings.REDIS_URL)

def check_rate_limit(user_id: str = Depends(verify_api_key)):
    """
    Implements a sliding window rate limiting algorithm using Redis.
    Raises HTTPException 429 if the rate limit is exceeded.
    """
    limit = settings.RATE_LIMIT_PER_MINUTE
    window = 60  # seconds

    now = datetime.now().timestamp()
    key = f"rate:{user_id}"

    # Remove old entries (outside the window)
    r.zremrangebyscore(key, 0, now - window)

    # Count current requests
    current_requests = r.zcard(key)

    if current_requests >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")

    # Add new request timestamp and set expiration
    r.zadd(key, {str(now): now})
    r.expire(key, window + 5) # Set expiration slightly longer than window