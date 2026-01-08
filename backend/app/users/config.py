"""FastAPI Users configuration and setup."""

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated, Optional

from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select
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
# We'll create an adapter that wraps sync sessions to work with async fastapi-users
SessionLocal = sessionmaker(bind=engine, class_=SQLAlchemySession)


class SyncSQLAlchemyUserDatabase(SQLAlchemyUserDatabase):
    """Adapter for SQLAlchemyUserDatabase that works with sync SQLAlchemy sessions."""
    
    def __init__(self, session: SQLAlchemySession, user_table: type[User]):
        """Initialize with sync SQLAlchemy session."""
        # Store session and user table
        self.session = session
        self.user_table = user_table
    
    async def get(self, id: uuid.UUID) -> Optional[User]:
        """Get user by ID (async wrapper for sync operation)."""
        def _get_sync():
            return self.session.get(self.user_table, id)
        return await run_in_threadpool(_get_sync)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (async wrapper for sync operation)."""
        def _get_by_email_sync():
            statement = select(self.user_table).where(self.user_table.email == email)
            result = self.session.execute(statement)
            return result.scalar_one_or_none()
        return await run_in_threadpool(_get_by_email_sync)
    
    async def get_by_oauth_account(self, oauth: str, account_id: str) -> Optional[User]:
        """Get user by OAuth account (not implemented for sync)."""
        # OAuth not implemented yet
        return None
    
    async def create(self, user: User | dict) -> User:
        """Create user (async wrapper for sync operation)."""
        def _create_sync():
            # If user is a dict (from create_update_dict), convert to User instance
            user_instance = user
            if isinstance(user, dict):
                user_instance = User(**user)
            self.session.add(user_instance)
            self.session.commit()
            self.session.refresh(user_instance)
            return user_instance
        return await run_in_threadpool(_create_sync)
    
    async def update(self, user: User, update_dict: dict) -> User:
        """Update user (async wrapper for sync operation)."""
        def _update_sync():
            # Update user attributes from update_dict
            for key, value in update_dict.items():
                setattr(user, key, value)
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user
        return await run_in_threadpool(_update_sync)
    
    async def delete(self, user: User) -> None:
        """Delete user (async wrapper for sync operation)."""
        def _delete_sync():
            self.session.delete(user)
            self.session.commit()
        await run_in_threadpool(_delete_sync)


async def get_user_db() -> AsyncGenerator[SyncSQLAlchemyUserDatabase, None]:
    """Get user database adapter."""
    # Create sync SQLAlchemy session
    session = SessionLocal()
    try:
        yield SyncSQLAlchemyUserDatabase(session, User)
    finally:
        session.close()


# User manager
# BaseUserManager[UDB, ID]
# UDB: User database model
# ID: user ID type (uuid.UUID)
class UserManager(BaseUserManager[User, uuid.UUID]):
    """Custom user manager with email sending."""

    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY
    
    def parse_id(self, value: str) -> uuid.UUID:
        """Parse user ID from string."""
        return uuid.UUID(value)

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
    user_db: Annotated[SyncSQLAlchemyUserDatabase, Depends(get_user_db)]
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
