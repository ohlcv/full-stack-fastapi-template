"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,  # Use IP address as key
    storage_uri=settings.RATE_LIMIT_STORAGE,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    headers_enabled=True,  # Add rate limit headers to response
)
