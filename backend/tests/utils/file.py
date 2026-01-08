"""Test utilities for file operations."""

from pathlib import Path

from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import FileCreate
from tests.utils.utils import random_lower_string


def create_random_file(db: Session, owner_id: str, filename: str | None = None) -> tuple[Path, str]:
    """Create a random test file and return its path and content.
    
    Returns:
        tuple: (file_path, file_content)
    """
    if filename is None:
        filename = f"test_{random_lower_string()}.txt"
    
    upload_dir = Path(settings.UPLOAD_DIR)
    if owner_id:
        upload_dir = upload_dir / owner_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / filename
    content = f"Test file content: {random_lower_string()}"
    file_path.write_text(content)
    
    return file_path, content


def create_file_record(
    db: Session, owner_id: str, file_path: Path, original_filename: str | None = None
) -> str:
    """Create a file record in database.
    
    Returns:
        str: File ID
    """
    if original_filename is None:
        original_filename = file_path.name
    
    file_create = FileCreate(
        filename=file_path.name,
        original_filename=original_filename,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        content_type="text/plain",
    )
    
    import uuid
    db_file = crud.create_file(
        session=db, file_create=file_create, owner_id=uuid.UUID(owner_id)
    )
    return str(db_file.id)


# Note: For testing file uploads, use bytes directly in TestClient.files parameter
# Example: files={"file": ("test.txt", b"content", "text/plain")}
