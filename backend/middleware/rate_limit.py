"""
Rate limiting middleware for KusiSaaS Enterprise
Middleware de limitación de tasa para prevenir ataques de fuerza bruta
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit exception handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too many requests",
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": str(exc.retry_after) if hasattr(exc, 'retry_after') else "60"
        }
    )
