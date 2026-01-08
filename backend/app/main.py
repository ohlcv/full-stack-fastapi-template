import sentry_sdk
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.routing import APIRoute
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.admin import setup_admin
from app.api.main import api_router
from app.core.cache import init_cache
from app.core.config import settings
from app.core.i18n import get_i18n
from app.core.permissions import setup_permissions
from app.core.rate_limit import limiter, rate_limit_exceeded_handler

# Patch slowapi.middleware's cached reference to _rate_limit_exceeded_handler
# slowapi.middleware imports it at module level, so we need to patch it after import
import slowapi.middleware
if hasattr(slowapi.middleware, "_rate_limit_exceeded_handler"):
    slowapi.middleware._rate_limit_exceeded_handler = rate_limit_exceeded_handler


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    await init_cache()
    # Initialize i18n
    if settings.I18N_ENABLED:
        get_i18n()  # Initialize translations
    yield
    # Shutdown (if needed)


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Add rate limiting
if settings.RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

# Add session middleware for admin authentication
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# Setup permissions system
setup_permissions()

# Setup admin interface
setup_admin(app)
