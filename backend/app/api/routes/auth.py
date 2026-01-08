"""Authentication routes using fastapi-users."""

from fastapi import APIRouter

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
    fastapi_users.get_register_router(),
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
    fastapi_users.get_verify_router(),
    prefix="/auth",
    tags=["auth"],
)

# Include users management routes (get current user, update, delete)
router.include_router(
    fastapi_users.get_users_router(),
    prefix="/users",
    tags=["users"],
)
