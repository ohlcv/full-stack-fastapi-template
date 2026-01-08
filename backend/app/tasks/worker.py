"""ARQ worker configuration and tasks."""

from arq import create_pool
from arq.connections import RedisSettings
from arq.worker import Worker

from app.core.config import settings


class WorkerSettings:
    """ARQ worker settings."""

    redis_settings = RedisSettings.from_dsn(settings.ARQ_REDIS_CONNECTION)
    functions = [
        "app.tasks.tasks.send_email_task",
        "app.tasks.tasks.process_data_task",
    ]
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    keep_result = 3600  # Keep results for 1 hour
    # cron_jobs = []  # Add cron jobs here if needed


async def get_arq_pool():
    """Get ARQ Redis pool."""
    return await create_pool(RedisSettings.from_dsn(settings.ARQ_REDIS_CONNECTION))


# Export for use in main.py
__all__ = ["WorkerSettings", "get_arq_pool"]
