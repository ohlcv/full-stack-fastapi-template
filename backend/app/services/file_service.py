"""Service layer for file-related business logic."""

import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlmodel import Session

from app import crud
from app.models.file import File, FileCreate, FilePublic, FilesPublic
from app.models.user import User
from app.utils.files import get_file_hash, get_file_info, save_upload_file


class FileService:
    """Service layer for file-related business logic."""

    @staticmethod
    async def upload_file(
        *, session: Session, upload_file: UploadFile, current_user: User
    ) -> FilePublic:
        """Upload a file."""
        try:
            # Save file to filesystem (async)
            file_path = await save_upload_file(upload_file, user_id=str(current_user.id))
            
            # Get file information
            file_info = get_file_info(file_path)
            
            # Calculate file hash
            file_hash = get_file_hash(file_path)
            
            # Create file record
            file_create = FileCreate(
                filename=file_path.name,
                original_filename=upload_file.filename or "file",
                file_path=str(file_path),
                file_size=file_info["size"],
                content_type=upload_file.content_type,
                file_hash=file_hash,
            )
            
            db_file = crud.create_file(
                session=session, file_create=file_create, owner_id=current_user.id
            )
            return db_file
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}",
            )

    @staticmethod
    def get_files(
        *, session: Session, current_user: User, skip: int = 0, limit: int = 100
    ) -> FilesPublic:
        """Get files with access control."""
        # Regular users only see their own files, superusers see all
        owner_id = None if current_user.is_superuser else current_user.id
        files, count = crud.get_files(
            session=session, owner_id=owner_id, skip=skip, limit=limit
        )
        # Convert File models to FilePublic schemas
        file_publics = [FilePublic.model_validate(file) for file in files]
        return FilesPublic(data=file_publics, count=count)

    @staticmethod
    def get_file(*, session: Session, file_id: uuid.UUID, current_user: User) -> File:
        """Get a file by ID with access control. Returns File model (not FilePublic) for internal use."""
        db_file = crud.get_file(session=session, file_id=file_id)
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

        # Check access: superuser or owner
        if not current_user.is_superuser and db_file.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        return db_file
    
    @staticmethod
    def get_file_public(*, session: Session, file_id: uuid.UUID, current_user: User) -> FilePublic:
        """Get a file by ID with access control. Returns FilePublic schema for API responses."""
        db_file = FileService.get_file(session=session, file_id=file_id, current_user=current_user)
        return FilePublic.model_validate(db_file)

    @staticmethod
    def delete_file(*, session: Session, file_id: uuid.UUID, current_user: User) -> dict[str, str]:
        """Delete a file with access control."""
        db_file = crud.get_file(session=session, file_id=file_id)
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

        # Check access: superuser or owner
        if not current_user.is_superuser and db_file.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        crud.delete_file(session=session, db_file=db_file)
        return {"message": "File deleted successfully"}
