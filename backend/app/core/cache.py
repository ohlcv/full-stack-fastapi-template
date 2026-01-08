"""Cache configuration using fastapi-cache2."""

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

from app.core.config import settings


async def init_cache() -> None:
    """Initialize cache backend."""
    redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    FastAPICache.init(RedisBackend(redis), prefix=settings.CACHE_KEY_PREFIX)


# Export cache decorator for easy use
__all__ = ["cache", "init_cache"]
