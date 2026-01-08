"""Tests for file upload and management routes."""

import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import File
from tests.utils.file import create_file_record, create_random_file
from tests.utils.user import create_random_user


def test_upload_file(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test file upload."""
    # Reset file pointer before upload
    test_content = b"test content"
    files = {"file": ("test.txt", test_content, "text/plain")}
    
    response = client.post(
        f"{settings.API_V1_STR}/files/upload",
        headers=superuser_token_headers,
        files=files,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["original_filename"] == "test.txt"
    assert content["file_size"] > 0
    assert "id" in content


def test_upload_file_invalid_type(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test file upload with invalid file type."""
    test_content = b"test content"
    files = {"file": ("test.exe", test_content, "application/x-msdownload")}
    
    response = client.post(
        f"{settings.API_V1_STR}/files/upload",
        headers=superuser_token_headers,
        files=files,
    )
    
    assert response.status_code == 400
    content = response.json()
    assert "not allowed" in content["detail"].lower()


def test_upload_file_too_large(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test file upload with file too large."""
    # Create a file larger than MAX_UPLOAD_SIZE
    large_content = b"x" * (settings.MAX_UPLOAD_SIZE + 1)
    files = {"file": ("test.txt", large_content, "text/plain")}
    
    response = client.post(
        f"{settings.API_V1_STR}/files/upload",
        headers=superuser_token_headers,
        files=files,
    )
    
    assert response.status_code == 400
    content = response.json()
    assert "too large" in content["detail"].lower()


def test_get_files(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test get files list."""
    user = create_random_user(db)
    file_path, _ = create_random_file(db, str(user.id))
    create_file_record(db, str(user.id), file_path)
    
    response = client.get(
        f"{settings.API_V1_STR}/files/",
        headers=superuser_token_headers,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert len(content["data"]) >= 1


def test_get_file(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test get file by ID."""
    user = create_random_user(db)
    file_path, _ = create_random_file(db, str(user.id))
    file_id = create_file_record(db, str(user.id), file_path)
    
    response = client.get(
        f"{settings.API_V1_STR}/files/{file_id}",
        headers=superuser_token_headers,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == file_id
    assert content["original_filename"] == file_path.name


def test_get_file_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test get file that doesn't exist."""
    response = client.get(
        f"{settings.API_V1_STR}/files/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "File not found"


def test_get_file_permission_denied(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test get file without permission."""
    user = create_random_user(db)
    file_path, _ = create_random_file(db, str(user.id))
    file_id = create_file_record(db, str(user.id), file_path)
    
    response = client.get(
        f"{settings.API_V1_STR}/files/{file_id}",
        headers=normal_user_token_headers,
    )
    
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_download_file(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test download file."""
    user = create_random_user(db)
    file_path, file_content = create_random_file(db, str(user.id), "test_download.txt")
    file_id = create_file_record(db, str(user.id), file_path, "test_download.txt")
    
    response = client.get(
        f"{settings.API_V1_STR}/files/{file_id}/download",
        headers=superuser_token_headers,
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert file_content.encode() in response.content


def test_delete_file(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test delete file."""
    user = create_random_user(db)
    file_path, _ = create_random_file(db, str(user.id))
    file_id = create_file_record(db, str(user.id), file_path)
    
    response = client.delete(
        f"{settings.API_V1_STR}/files/{file_id}",
        headers=superuser_token_headers,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "File deleted successfully"
    
    # Verify file is deleted from database
    db_file = db.get(File, uuid.UUID(file_id))
    assert db_file is None
    
    # Verify file is deleted from filesystem
    assert not file_path.exists()


def test_delete_file_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test delete file that doesn't exist."""
    response = client.delete(
        f"{settings.API_V1_STR}/files/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "File not found"


def test_delete_file_permission_denied(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test delete file without permission."""
    user = create_random_user(db)
    file_path, _ = create_random_file(db, str(user.id))
    file_id = create_file_record(db, str(user.id), file_path)
    
    response = client.delete(
        f"{settings.API_V1_STR}/files/{file_id}",
        headers=normal_user_token_headers,
    )
    
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"
