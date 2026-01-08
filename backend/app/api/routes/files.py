"""File upload and management routes."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File as FastAPIFile, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, SessionDep
from app.core.rate_limit import limiter
from app.models import FilePublic, FilesPublic, Message
from app.services import FileService

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FilePublic)
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = FastAPIFile(...),
) -> Any:
    """Upload a file."""
    return await FileService.upload_file(
        session=session, upload_file=file, current_user=current_user
    )


@router.get("/", response_model=FilesPublic)
def get_files(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Get files list."""
    return FileService.get_files(
        session=session, current_user=current_user, skip=skip, limit=limit
    )


@router.get("/{file_id}", response_model=FilePublic)
def get_file(
    file_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get file information."""
    return FileService.get_file_public(
        session=session, file_id=file_id, current_user=current_user
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Download a file."""
    from pathlib import Path

    db_file = FileService.get_file(
        session=session, file_id=file_id, current_user=current_user
    )
    
    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk"
        )
    
    return FileResponse(
        path=file_path,
        filename=db_file.original_filename,
        media_type=db_file.content_type or "application/octet-stream",
    )


@router.delete("/{file_id}", response_model=Message)
def delete_file(
    file_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Delete a file."""
    result = FileService.delete_file(
        session=session, file_id=file_id, current_user=current_user
    )
    return Message(message=result["message"])
