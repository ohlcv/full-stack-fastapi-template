"""Example routes demonstrating task queue usage."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.deps import CurrentUser
from app.utils.tasks import enqueue_email_task, enqueue_process_data_task, get_task_status

router = APIRouter(prefix="/tasks", tags=["tasks"])


class SendEmailRequest(BaseModel):
    """Request model for sending email."""

    email_to: EmailStr
    subject: str
    html_content: str


class ProcessDataRequest(BaseModel):
    """Request model for processing data."""

    data: dict[str, Any]


@router.post("/send-email")
async def send_email_async(request: SendEmailRequest, current_user: CurrentUser) -> dict[str, str]:
    """Enqueue email sending task.

    This endpoint enqueues an email sending task instead of sending it synchronously.
    """
    try:
        job_id = await enqueue_email_task(
            email_to=request.email_to,
            subject=request.subject,
            html_content=request.html_content,
        )
        return {
            "status": "enqueued",
            "job_id": job_id,
            "message": "Email task has been enqueued",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue email task: {str(e)}",
        )


@router.post("/process-data")
async def process_data_async(
    request: ProcessDataRequest, current_user: CurrentUser
) -> dict[str, str]:
    """Enqueue data processing task."""
    try:
        job_id = await enqueue_process_data_task(data=request.data)
        return {
            "status": "enqueued",
            "job_id": job_id,
            "message": "Data processing task has been enqueued",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue data processing task: {str(e)}",
        )


@router.get("/status/{job_id}")
async def get_task_status_endpoint(job_id: str, current_user: CurrentUser) -> dict[str, Any]:
    """Get task status by job ID."""
    status_info = await get_task_status(job_id)
    if status_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {job_id} not found",
        )
    return status_info
