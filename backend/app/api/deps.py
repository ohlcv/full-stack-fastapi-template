"""Dependencies for API routes.

This module provides dependencies for database sessions and user authentication.
Now uses fastapi-users for authentication, but keeps backward compatibility.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.core.db import engine
from app.models.user import User
from app.users.config import CurrentUser as FastAPIUsersCurrentUser
from app.users.config import CurrentSuperuser as FastAPIUsersCurrentSuperuser

# Database session dependency
def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]

# User authentication dependencies (using fastapi-users)
CurrentUser = FastAPIUsersCurrentUser
CurrentSuperuser = FastAPIUsersCurrentSuperuser

# Function for backward compatibility
def get_current_active_superuser(
    current_user: CurrentSuperuser,
) -> User:
    """Get current active superuser (backward compatibility)."""
    return current_user
