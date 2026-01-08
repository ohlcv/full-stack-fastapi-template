"""File-related models."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field as SQLField, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class FileBase(SQLModel):
    """Base file model."""
    filename: str = SQLField(max_length=255)
    original_filename: str = SQLField(max_length=255)
    file_path: str = SQLField(max_length=512)
    file_size: int
    content_type: str | None = SQLField(default=None, max_length=100)
    file_hash: str | None = SQLField(default=None, max_length=64)
    owner_id: uuid.UUID = SQLField(foreign_key="user.id", index=True)


class File(FileBase, table=True):
    """File database model."""
    id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))
    
    owner: "User" = Relationship(back_populates="files")


class FileCreate(BaseModel):
    """File creation schema."""
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    content_type: str | None = None
    file_hash: str | None = None


class FilePublic(BaseModel):
    """Public file schema."""
    id: uuid.UUID
    filename: str
    original_filename: str
    file_size: int
    content_type: str | None
    created_at: datetime


class FilesPublic(BaseModel):
    """Files list response."""
    data: list[FilePublic]
    count: int
