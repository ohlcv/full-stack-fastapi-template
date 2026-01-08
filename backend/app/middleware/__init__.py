"""Middleware for the application."""

from app.middleware.request_id import RequestIDMiddleware
from app.middleware.setup import setup_middleware

__all__ = ["RequestIDMiddleware", "setup_middleware"]
