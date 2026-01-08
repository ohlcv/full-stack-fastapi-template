"""Rate limiting dependencies for API routes."""

from app.core.config import settings
from app.core.rate_limit import limiter

# Rate limit decorators for common use cases
rate_limit_login = limiter.limit(settings.RATE_LIMIT_LOGIN)
rate_limit_register = limiter.limit(settings.RATE_LIMIT_REGISTER)
rate_limit_password_reset = limiter.limit(settings.RATE_LIMIT_PASSWORD_RESET)
rate_limit_default = limiter.limit(settings.RATE_LIMIT_DEFAULT)
