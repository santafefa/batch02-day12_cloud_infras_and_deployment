import redis
from datetime import datetime
from fastapi import HTTPException, Depends
from .config import settings
from .auth import verify_api_key

# Initialize Redis client
r = redis.from_url(settings.REDIS_URL)

def check_budget(user_id: str = Depends(verify_api_key)): 
    """
    Tracks and limits spending per user per month using Redis.
    Raises HTTPException 402 if the monthly budget is exceeded.
    """
    monthly_limit = settings.MONTHLY_BUDGET_USD
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    estimated_cost = 0.01 # Assume a small cost per request

    # Get current spending
    current_spending = float(r.get(key) or 0)

    if current_spending + estimated_cost > monthly_limit:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly budget of ${monthly_limit:.2f} exceeded. Current spending: ${current_spending:.2f}"
        )
    # Add estimated cost and set expiration
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600) # 32 days, plus a buffer

    return True