"""Setup middleware for FastAPI application."""

from fastapi import FastAPI

from app.middleware.request_id import RequestIDMiddleware


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware with the FastAPI app."""
    app.add_middleware(RequestIDMiddleware)
