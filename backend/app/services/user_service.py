import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    User,
    UserCreate,
    UserPublic,
    UserUpdate,
    UserUpdateMe,
    UsersPublic,
)
from app.utils import generate_new_account_email, send_email


class UserService:
    """Service layer for user-related business logic."""

    @staticmethod
    def get_users(*, session: Session, skip: int = 0, limit: int = 100) -> UsersPublic:
        """Get all users with pagination."""
        users, count = crud.get_users(session=session, skip=skip, limit=limit)
        return UsersPublic(data=users, count=count)

    @staticmethod
    def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User:
        """Get a user by ID."""
        user = crud.get_user(session=session, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    def get_current_user(*, current_user: User) -> UserPublic:
        """Get current authenticated user."""
        return current_user

    @staticmethod
    def create_user(*, session: Session, user_in: UserCreate) -> UserPublic:
        """Create a new user."""
        # Check if user already exists
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )

        # Create user
        user = crud.create_user(session=session, user_create=user_in)

        # Send welcome email if enabled
        if settings.emails_enabled and user_in.email:
            email_data = generate_new_account_email(
                email_to=user_in.email, username=user_in.email, password=user_in.password
            )
            send_email(
                email_to=user_in.email,
                subject=email_data.subject,
                html_content=email_data.html_content,
            )

        return user

    @staticmethod
    def register_user(*, session: Session, user_in: UserCreate) -> UserPublic:
        """Register a new user (public signup)."""
        # Check if user already exists
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system",
            )

        # Create user
        user = crud.create_user(session=session, user_create=user_in)
        return user

    @staticmethod
    def update_user(
        *, session: Session, user_id: uuid.UUID, user_in: UserUpdate
    ) -> UserPublic:
        """Update a user."""
        db_user = crud.get_user(session=session, user_id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The user with this id does not exist in the system",
            )

        # Check email uniqueness if email is being updated
        if user_in.email:
            existing_user = crud.get_user_by_email(session=session, email=user_in.email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )

        updated_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
        return updated_user

    @staticmethod
    def update_user_me(
        *, session: Session, user_in: UserUpdateMe, current_user: User
    ) -> UserPublic:
        """Update current user's own profile."""
        # Check email uniqueness if email is being updated
        if user_in.email:
            existing_user = crud.get_user_by_email(session=session, email=user_in.email)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )

        # Update user
        user_data = user_in.model_dump(exclude_unset=True)
        current_user.sqlmodel_update(user_data)
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
        return current_user

    @staticmethod
    def update_password_me(
        *, session: Session, current_password: str, new_password: str, current_user: User
    ) -> dict[str, str]:
        """Update current user's password."""
        # Verify current password
        if not verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
            )

        # Check if new password is different
        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be the same as the current one",
            )

        # Update password
        crud.update_user_password(
            session=session, db_user=current_user, new_password=new_password
        )
        return {"message": "Password updated successfully"}

    @staticmethod
    def delete_user(*, session: Session, user_id: uuid.UUID, current_user: User) -> dict[str, str]:
        """Delete a user."""
        user = crud.get_user(session=session, user_id=user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Prevent self-deletion for superusers
        if user == current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super users are not allowed to delete themselves",
            )

        crud.delete_user(session=session, db_user=user)
        return {"message": "User deleted successfully"}

    @staticmethod
    def delete_user_me(*, session: Session, current_user: User) -> dict[str, str]:
        """Delete current user's own account."""
        # Prevent superuser self-deletion
        if current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super users are not allowed to delete themselves",
            )

        crud.delete_user(session=session, db_user=current_user)
        return {"message": "User deleted successfully"}

    @staticmethod
    def check_user_access(*, user: User, target_user_id: uuid.UUID) -> bool:
        """Check if user has access to view/modify another user."""
        return user.is_superuser or user.id == target_user_id

