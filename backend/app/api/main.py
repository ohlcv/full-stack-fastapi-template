from fastapi import APIRouter

from app.api.routes import auth, files, items, login, private, users, utils
from app.core.config import settings

api_router = APIRouter()

# FastAPI Users routes (replaces login and some user routes)
api_router.include_router(auth.router)

# Keep existing routes for backward compatibility (can be removed later)
# api_router.include_router(login.router)  # Deprecated: use /auth/login
# api_router.include_router(users.router)  # Partially replaced by fastapi-users

# Other routes
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(files.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
