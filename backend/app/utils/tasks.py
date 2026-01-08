"""Utility functions for task queue."""

from typing import Any

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from app.core.config import settings
from app.tasks.tasks import process_data_task, send_email_task

# Global ARQ pool (initialized on startup)
_arq_pool: ArqRedis | None = None


async def init_arq_pool() -> None:
    """Initialize ARQ Redis pool."""
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings.from_dsn(settings.ARQ_REDIS_CONNECTION))


async def get_arq_pool() -> ArqRedis:
    """Get ARQ Redis pool."""
    global _arq_pool
    if _arq_pool is None:
        await init_arq_pool()
    return _arq_pool  # type: ignore


async def enqueue_email_task(
    email_to: str,
    subject: str,
    html_content: str,
) -> str:
    """Enqueue email sending task.

    Args:
        email_to: Recipient email address
        subject: Email subject
        html_content: Email HTML content

    Returns:
        Task ID
    """
    pool = await get_arq_pool()
    job = await pool.enqueue_job(
        "send_email_task",
        email_to=email_to,
        subject=subject,
        html_content=html_content,
    )
    return job.job_id if job else ""


async def enqueue_process_data_task(data: dict[str, Any]) -> str:
    """Enqueue data processing task.

    Args:
        data: Data to process

    Returns:
        Task ID
    """
    pool = await get_arq_pool()
    job = await pool.enqueue_job(
        "process_data_task",
        data=data,
    )
    return job.job_id if job else ""


async def get_task_status(job_id: str) -> dict[str, Any] | None:
    """Get task status by job ID.

    Args:
        job_id: Task job ID

    Returns:
        Task status information or None if not found
    """
    pool = await get_arq_pool()
    job = await pool.get_job(job_id)
    if job is None:
        return None

    return {
        "job_id": job.job_id,
        "status": job.status,
        "result": job.result,
        "error": str(job.exc_info) if job.exc_info else None,
    }
