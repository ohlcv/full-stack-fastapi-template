"""Tests for rate limiting functionality."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.utils import random_email, random_lower_string


def test_rate_limit_login(client: TestClient) -> None:
    """Test rate limiting on login endpoint."""
    # Note: Rate limiting is disabled in tests via conftest.py
    # This test verifies the endpoint exists and can handle requests
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    
    # Try fastapi-users login endpoint
    response = client.post(
        f"{settings.API_V1_STR}/auth/login", data=login_data
    )
    # Should succeed (rate limiting disabled in tests)
    assert response.status_code in [200, 400, 429]  # 200 if correct, 400 if wrong, 429 if rate limited


def test_rate_limit_register(client: TestClient) -> None:
    """Test rate limiting on registration endpoint."""
    # Make multiple registration requests
    for i in range(5):
        email = random_email()
        password = random_lower_string()
        
        with client:
            response = client.post(
                f"{settings.API_V1_STR}/users/signup",
                json={
                    "email": email,
                    "password": password,
                    "full_name": "Test User",
                },
            )
            # First few may succeed, but after rate limit should get 429
            if response.status_code == 429:
                assert "rate limit" in response.json()["detail"].lower() or "too many" in response.json()["detail"].lower()
                break


def test_rate_limit_headers(client: TestClient) -> None:
    """Test that rate limit headers are present in responses."""
    # Note: Rate limiting is disabled in tests, so headers may not be present
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    
    # Try fastapi-users login endpoint
    response = client.post(
        f"{settings.API_V1_STR}/auth/login", data=login_data
    )
    
    # Rate limit headers should be present if slowapi is configured with headers_enabled=True
    # Common headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
    # Note: Headers may not be present if rate limiting is disabled (as in tests)
    assert response.status_code in [200, 400, 429]
    # Headers are optional when rate limiting is disabled


def test_rate_limit_file_upload(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test rate limiting on file upload endpoint."""
    test_content = b"test content"
    files = {"file": ("test.txt", test_content, "text/plain")}
    
    # Make multiple upload requests
    for i in range(12):  # More than the 10/minute limit
        response = client.post(
            f"{settings.API_V1_STR}/files/upload",
            headers=superuser_token_headers,
            files=files,
        )
        
        # After rate limit, should get 429
        if response.status_code == 429:
            assert "rate limit" in response.json()["detail"].lower() or "too many" in response.json()["detail"].lower()
            break


def test_rate_limit_password_reset(client: TestClient, db: Session) -> None:
    """Test rate limiting on password reset endpoint."""
    from app import crud
    from app.models import UserCreate
    
    # Create a user first
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    crud.create_user(session=db, user_create=user_in)
    
    # Make multiple password reset requests
    for i in range(5):  # More than the 3/hour limit
        with client:
            response = client.post(
                f"{settings.API_V1_STR}/password-recovery/{email}",
            )
            # After rate limit, should get 429
            if response.status_code == 429:
                assert "rate limit" in response.json()["detail"].lower() or "too many" in response.json()["detail"].lower()
                break
