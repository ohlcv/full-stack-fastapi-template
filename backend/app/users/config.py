"""FastAPI Users configuration and setup."""

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.db import engine
from app.core.security import ALGORITHM
from app.models.user import User
from app.utils.email import generate_new_account_email, send_email
from fastapi_users import schemas


# Database adapter
# Note: fastapi-users expects async SQLAlchemy, but we use sync SQLModel
# We'll create an adapter that works with sync sessions
# SQLModel models are SQLAlchemy models, so this works
SessionLocal = sessionmaker(bind=engine, class_=SQLAlchemySession)


async def get_user_db() -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """Get user database adapter."""
    # Create sync SQLAlchemy session
    # SQLModel models are SQLAlchemy models, so this works
    session = SessionLocal()
    try:
        yield SQLAlchemyUserDatabase(session, User)
    finally:
        session.close()


# User manager
# BaseUserManager[ID, UCD, UPD, UDB]
# ID: user ID type (uuid.UUID)
# UCD: UserCreate schema
# UPD: UserUpdate schema
# UDB: User database model
class UserManager(BaseUserManager[uuid.UUID, schemas.UserCreate, schemas.UserUpdate, User]):
    """Custom user manager with email sending."""

    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(
        self, user: User, request: None = None
    ) -> None:
        """Send welcome email after registration."""
        if settings.emails_enabled:
            email_data = generate_new_account_email(
                email_to=user.email,
                username=user.email,
                password="[已通过注册设置]"  # Don't send password in email
            )
            send_email(
                email_to=user.email,
                subject=email_data.subject,
                html_content=email_data.html_content,
            )

    async def on_after_forgot_password(
        self, user: User, token: str, request: None = None
    ) -> None:
        """Send password reset email."""
        if settings.emails_enabled:
            from app.utils import generate_reset_password_email
            email_data = generate_reset_password_email(
                email_to=user.email, email=user.email, token=token
            )
            send_email(
                email_to=user.email,
                subject=email_data.subject,
                html_content=email_data.html_content,
            )

    async def on_after_update(
        self, user: User, update_dict: dict, request: None = None
    ) -> None:
        """Handle after user update."""
        pass


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase, Depends(get_user_db)]
) -> AsyncGenerator[UserManager, None]:
    """Get user manager."""
    yield UserManager(user_db)


# Authentication backend
bearer_transport = BearerTransport(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT authentication strategy."""
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        algorithm=ALGORITHM,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
# FastAPIUsers[UDB, ID] where UDB is User database model, ID is user ID type
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Type aliases for dependencies
CurrentUser = Annotated[User, Depends(fastapi_users.current_user(active=True))]
CurrentSuperuser = Annotated[
    User, Depends(fastapi_users.current_user(active=True, superuser=True))
]
