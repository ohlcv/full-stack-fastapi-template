"""Authentication for SQLAdmin."""

import uuid

from fastapi import Request
from sqladmin.authentication import AuthenticationBackend
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.db import engine
from app.core.security import verify_password
from app.models import User


class AdminAuth(AuthenticationBackend):
    """Custom authentication backend for SQLAdmin."""

    async def login(self, request: Request) -> bool:
        """Handle login."""
        form = await request.form()
        email = form.get("email")
        password = form.get("password")

        if not email or not password:
            return False

        # Authenticate user
        with Session(engine) as session:
            user = crud.get_user_by_email(session=session, email=email)
            if not user:
                return False

            if not verify_password(password, user.hashed_password):
                return False

            if not user.is_active:
                return False

            # Only superusers can access admin
            if not user.is_superuser:
                return False

            # Store user in session
            request.session.update({"user_id": str(user.id)})
            return True

    async def logout(self, request: Request) -> bool:
        """Handle logout."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Check if user is authenticated."""
        user_id = request.session.get("user_id")
        if not user_id:
            return False

        # Verify user still exists and is superuser
        with Session(engine) as session:
            try:
                import uuid
                user = session.get(User, uuid.UUID(user_id))
                if not user or not user.is_active or not user.is_superuser:
                    request.session.clear()
                    return False
                return True
            except (ValueError, TypeError):
                request.session.clear()
                return False


# Create authentication backend instance
authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
