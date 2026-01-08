"""Exception handlers for FastAPI application."""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_development() -> bool:
    """Check if running in development environment."""
    return settings.ENVIRONMENT == "local"


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    content = {
        "error": True,
        "message": exc.detail,
        "status_code": exc.status_code,
    }
    
    # Add detailed information in development
    if _is_development():
        content["detail"] = str(exc.detail)
        if hasattr(exc, "headers") and exc.headers:
            content["headers"] = dict(exc.headers)
    
    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation error",
            "details": errors,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        },
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors."""
    logger.error(f"Database integrity error: {exc}", exc_info=True)
    
    content = {
        "error": True,
        "message": "Database integrity error",
        "status_code": status.HTTP_409_CONFLICT,
    }
    
    # Add detailed error information in development
    if _is_development():
        content["detail"] = str(exc)
        content["original_error"] = exc.__class__.__name__
        if hasattr(exc, "orig") and exc.orig:
            content["database_error"] = str(exc.orig)
    
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=content)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.exception(f"Unhandled exception: {exc}", exc_info=True)
    
    content = {
        "error": True,
        "message": "Internal server error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    # Add detailed error information in development
    if _is_development():
        content["detail"] = str(exc)
        content["exception_type"] = exc.__class__.__name__
        content["traceback"] = traceback.format_exc().split("\n")
        # Add request information for debugging
        content["request_info"] = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
