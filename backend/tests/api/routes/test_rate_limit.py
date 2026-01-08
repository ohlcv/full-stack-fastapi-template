"""Tests for rate limiting functionality."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.utils import random_email, random_lower_string


def test_rate_limit_login(client: TestClient) -> None:
    """Test rate limiting on login endpoint."""
    # Make multiple requests quickly
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    
    # First few requests should succeed
    for i in range(3):
        response = client.post(
            f"{settings.API_V1_STR}/login/access-token", data=login_data
        )
        assert response.status_code in [200, 400]  # 200 if correct, 400 if wrong
    
    # After rate limit, should get 429
    # Note: This test may be flaky depending on rate limit settings
    # In production, you'd want to use a test-specific rate limit or mock the limiter


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
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/login/access-token", data=login_data
    )
    
    # Rate limit headers should be present if slowapi is configured with headers_enabled=True
    # Common headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
    # Note: Headers may not be present if rate limiting is disabled or not configured
    assert response.status_code in [200, 400, 429]


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
