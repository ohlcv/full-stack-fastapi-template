"""File upload and management utilities."""

import hashlib
import secrets
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import UploadFile

from app.core.config import settings


def get_upload_dir() -> Path:
    """Get upload directory path."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure filename to prevent directory traversal and conflicts."""
    # Get file extension
    suffix = Path(original_filename).suffix
    
    # Generate random filename
    random_part = secrets.token_urlsafe(16)
    return f"{random_part}{suffix}"


def is_allowed_file(filename: str, content_type: str | None = None) -> bool:
    """Check if file is allowed based on extension and MIME type."""
    # Check extension
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        return False
    
    # Check MIME type if provided
    if content_type:
        if content_type not in settings.ALLOWED_MIME_TYPES:
            return False
    
    return True


async def save_upload_file(upload_file: UploadFile, user_id: str | None = None) -> Path:
    """Save uploaded file asynchronously.
    
    Args:
        upload_file: FastAPI UploadFile object
        user_id: Optional user ID for organizing files by user
        
    Returns:
        Path to saved file
        
    Raises:
        ValueError: If file is not allowed or too large
    """
    # Validate file
    if not is_allowed_file(upload_file.filename or "", upload_file.content_type):
        raise ValueError(f"File type not allowed: {upload_file.filename}")
    
    # Check file size (read in chunks to avoid loading entire file into memory)
    file_size = 0
    chunk_size = 1024 * 1024  # 1 MB chunks
    
    # Create user-specific directory if user_id provided
    upload_dir = get_upload_dir()
    if user_id:
        upload_dir = upload_dir / user_id
        upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate secure filename
    secure_filename = generate_secure_filename(upload_file.filename or "file")
    file_path = upload_dir / secure_filename
    
    # Save file asynchronously
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await upload_file.read(chunk_size):
            file_size += len(chunk)
            if file_size > settings.MAX_UPLOAD_SIZE:
                # Clean up partial file
                if file_path.exists():
                    file_path.unlink()
                raise ValueError(f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes")
            await f.write(chunk)
    
    # Reset file pointer for potential reuse
    await upload_file.seek(0)
    
    return file_path


async def read_file(file_path: Path) -> bytes:
    """Read file asynchronously."""
    async with aiofiles.open(file_path, "rb") as f:
        return await f.read()


async def delete_file(file_path: Path) -> None:
    """Delete file asynchronously."""
    if file_path.exists():
        file_path.unlink()


def get_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_info(file_path: Path) -> dict[str, Any]:
    """Get file information."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "name": file_path.name,
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "extension": file_path.suffix,
    }
