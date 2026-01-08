"""CRUD operations for file management."""

import uuid
from pathlib import Path
from typing import Any

from sqlmodel import Session, select, func

from app.models.file import File, FileCreate


def create_file(*, session: Session, file_create: FileCreate, owner_id: uuid.UUID) -> File:
    """Create a new file record."""
    file_data = file_create.model_dump()
    file_data["owner_id"] = owner_id
    db_file = File.model_validate(file_data)
    session.add(db_file)
    session.commit()
    session.refresh(db_file)
    return db_file


def get_file(*, session: Session, file_id: uuid.UUID) -> File | None:
    """Get a file by ID."""
    return session.get(File, file_id)


def get_files(
    *, session: Session, owner_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
) -> tuple[list[File], int]:
    """Get files with optional filtering by owner."""
    if owner_id:
        count_statement = (
            select(func.count())
            .select_from(File)
            .where(File.owner_id == owner_id)
        )
        statement = (
            select(File)
            .where(File.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .order_by(File.created_at.desc())
        )
    else:
        count_statement = select(func.count()).select_from(File)
        statement = (
            select(File)
            .offset(skip)
            .limit(limit)
            .order_by(File.created_at.desc())
        )
    
    count = session.exec(count_statement).one()
    files = session.exec(statement).all()
    return list(files), count


def delete_file(*, session: Session, db_file: File) -> None:
    """Delete a file record and the actual file."""
    # Delete the actual file from filesystem
    file_path = Path(db_file.file_path)
    if file_path.exists():
        file_path.unlink()
    
    # Delete the database record
    session.delete(db_file)
    session.commit()
