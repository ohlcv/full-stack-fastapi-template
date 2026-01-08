"""Cache configuration using fastapi-cache2."""

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

from app.core.config import settings


async def init_cache() -> None:
    """Initialize cache backend."""
    try:
        redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        FastAPICache.init(RedisBackend(redis), prefix=settings.CACHE_KEY_PREFIX)
    except Exception:
        # In test environment or when Redis is unavailable, skip cache initialization
        # This allows tests to run without Redis connection
        pass


# Export cache decorator for easy use
__all__ = ["cache", "init_cache"]
