from fastapi import APIRouter

from app.api.routes import auth, files, items, private, users, utils
from app.core.config import settings

api_router = APIRouter()

# FastAPI Users routes (authentication, registration, password reset, etc.)
api_router.include_router(auth.router)

# User management routes (additional endpoints beyond fastapi-users)
api_router.include_router(users.router)

# Other routes
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(files.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
