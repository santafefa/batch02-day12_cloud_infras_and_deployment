from fastapi import Header, HTTPException
from .config import settings

def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """
    Verifies the API key provided in the X-API-Key header.
    Returns the user_id (which is the API key itself for simplicity here) if valid.
    Raises HTTPException 401 if invalid.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key. Include header: X-API-Key")
    if x_api_key != settings.AGENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    # For simplicity, we use the API key itself as the user_id
    return x_api_key