"""Rate limiting configuration using slowapi."""

# Patch slowapi's default handler BEFORE any slowapi imports
# This fixes the issue where AuthenticationError doesn't have 'detail' attribute
# Must be done before importing slowapi.middleware which caches the handler
import slowapi.extension

from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom rate limit exception handler that handles exceptions without 'detail' attribute."""
    # Get error message from exception
    # Some exceptions (like AuthenticationError) don't have 'detail' attribute
    if hasattr(exc, "detail"):
        error_message = str(exc.detail)
    elif hasattr(exc, "message"):
        error_message = str(exc.message)
    else:
        error_message = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": f"Rate limit exceeded: {error_message}"},
    )


# Patch the handler before initializing Limiter
slowapi.extension._rate_limit_exceeded_handler = rate_limit_exceeded_handler

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,  # Use IP address as key
    storage_uri=settings.RATE_LIMIT_STORAGE,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    headers_enabled=True,  # Add rate limit headers to response
)

# Also patch slowapi.middleware's cached reference
# slowapi.middleware imports _rate_limit_exceeded_handler at module level via:
# from slowapi import Limiter, _rate_limit_exceeded_handler
# So we need to patch it after slowapi.middleware is imported
# This will be done in main.py after importing SlowAPIMiddleware
