"""Tests for authentication endpoints (fastapi-users)."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.utils import random_email, random_lower_string


def test_get_access_token(client: TestClient) -> None:
    """Test getting access token via fastapi-users login endpoint."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


def test_get_access_token_incorrect_password(client: TestClient) -> None:
    """Test login with incorrect password."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert r.status_code == 400


def test_use_access_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test using access token with /users/me endpoint."""
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


def test_recovery_password(client: TestClient) -> None:
    """Test password recovery via fastapi-users /auth/forgot-password endpoint."""
    email = "test@example.com"
    
    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
        patch("app.users.config.send_email", return_value=None),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/auth/forgot-password",
            json={"email": email},
        )
        # fastapi-users returns 202 Accepted
        assert r.status_code == 202


def test_reset_password(client: TestClient, db: Session) -> None:
    """Test password reset flow via fastapi-users."""
    email = random_email()
    password = random_lower_string()

    # Register user via fastapi-users
    with patch("app.users.config.send_email", return_value=None):
        register_response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={"email": email, "password": password},
        )
        assert register_response.status_code == 201
        
        # Request password reset
        forgot_response = client.post(
            f"{settings.API_V1_STR}/auth/forgot-password",
            json={"email": email},
        )
        assert forgot_response.status_code == 202
        # Note: Actual token verification requires extracting token from email


def test_reset_password_invalid_token(client: TestClient) -> None:
    """Test password reset with invalid token."""
    data = {"new_password": "changethis", "token": "invalid"}
    r = client.post(
        f"{settings.API_V1_STR}/auth/reset-password",
        json=data,
    )
    response = r.json()

    assert "detail" in response
    # fastapi-users may return 400 (invalid token) or 422 (validation error)
    assert r.status_code in [400, 422]
