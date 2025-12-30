from datetime import timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session

from app import crud
from app.core import security
from app.core.config import settings
from app.models import Message, Token, User, UserPublic
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)


class AuthService:
    """Service layer for authentication-related business logic."""

    @staticmethod
    def login(*, session: Session, email: str, password: str) -> Token:
        """Authenticate user and return access token."""
        user = crud.authenticate(session=session, email=email, password=password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
        return Token(access_token=access_token)

    @staticmethod
    def test_token(*, current_user: User) -> UserPublic:
        """Test access token validity."""
        return current_user

    @staticmethod
    def recover_password(*, session: Session, email: str) -> Message:
        """Send password recovery email."""
        user = crud.get_user_by_email(session=session, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The user with this email does not exist in the system.",
            )

        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
        return Message(message="Password recovery email sent")

    @staticmethod
    def reset_password(*, session: Session, token: str, new_password: str) -> Message:
        """Reset password using recovery token."""
        email = verify_password_reset_token(token=token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )

        user = crud.get_user_by_email(session=session, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The user with this email does not exist in the system.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        crud.update_user_password(session=session, db_user=user, new_password=new_password)
        return Message(message="Password updated successfully")

    @staticmethod
    def get_password_recovery_html(*, session: Session, email: str) -> dict[str, str]:
        """Get password recovery email HTML content (for testing)."""
        user = crud.get_user_by_email(session=session, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The user with this username does not exist in the system.",
            )

        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )

        return {
            "html_content": email_data.html_content,
            "subject": email_data.subject,
        }

