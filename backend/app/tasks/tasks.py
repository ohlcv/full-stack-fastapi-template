"""ARQ task definitions."""

import logging
from typing import Any

from arq import cron

from app.core.config import settings
from app.utils.email import send_email

logger = logging.getLogger(__name__)


async def send_email_task(
    ctx: dict[str, Any],
    email_to: str,
    subject: str,
    html_content: str,
) -> dict[str, str]:
    """Send email asynchronously.

    Args:
        ctx: ARQ context
        email_to: Recipient email address
        subject: Email subject
        html_content: Email HTML content

    Returns:
        dict with status message
    """
    try:
        if not settings.emails_enabled:
            logger.warning("Email sending is disabled")
            return {"status": "skipped", "message": "Email sending is disabled"}

        send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
        )
        logger.info(f"Email sent successfully to {email_to}")
        return {"status": "success", "message": f"Email sent to {email_to}"}
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {str(e)}")
        raise


async def process_data_task(
    ctx: dict[str, Any],
    data: dict[str, Any],
) -> dict[str, Any]:
    """Process data asynchronously.

    Args:
        ctx: ARQ context
        data: Data to process

    Returns:
        Processed data
    """
    try:
        logger.info(f"Processing data: {data}")
        # Add your data processing logic here
        processed = {"processed": True, **data}
        return processed
    except Exception as e:
        logger.error(f"Failed to process data: {str(e)}")
        raise


# Scheduled tasks (cron jobs)
class CronJobs:
    """Scheduled cron jobs."""

    # Example: Run every day at midnight
    # @cron(hour=0, minute=0)
    # async def daily_report(ctx: dict[str, Any]) -> None:
    #     """Generate daily report."""
    #     logger.info("Generating daily report")
    #     # Add your daily report logic here
    #     pass

    pass


# Add cron jobs to worker settings
# In worker.py, add: cron_jobs = CronJobs
