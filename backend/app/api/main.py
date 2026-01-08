from fastapi import APIRouter

from app.api.routes import auth, files, items, login, private, users, utils
from app.core.config import settings

api_router = APIRouter()

# FastAPI Users routes (replaces login and some user routes)
api_router.include_router(auth.router)

# Keep existing routes for backward compatibility
# Note: Some routes are replaced by fastapi-users, but we keep users.router for additional endpoints
api_router.include_router(users.router)  # Additional user management endpoints
# api_router.include_router(login.router)  # Deprecated: use /auth/login

# Other routes
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(files.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
