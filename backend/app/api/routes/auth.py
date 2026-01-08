"""Authentication routes using fastapi-users."""

from fastapi import APIRouter
from fastapi_users import schemas

from app.models.user import User, UserCreate, UserPublic, UserUpdate
from app.users import fastapi_users
from app.users.config import auth_backend

router = APIRouter()

# Include fastapi-users authentication routes (login, logout)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)

# Include registration route
router.include_router(
    fastapi_users.get_register_router(UserPublic, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Include password reset routes
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

# Include verification route (email verification)
router.include_router(
    fastapi_users.get_verify_router(UserPublic),
    prefix="/auth",
    tags=["auth"],
)

# Note: We don't include fastapi_users.get_users_router() here because:
# 1. It requires superuser for GET/PATCH/DELETE /{id} routes by default
# 2. We have our own users.router with custom access control logic
# 3. Our users.router allows users to access their own profile
