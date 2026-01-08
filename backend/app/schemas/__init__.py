"""Pydantic schemas for request/response validation.

This module contains schemas that are separate from database models.
Use this for:
- Request validation schemas
- Response schemas that differ from models
- API-specific schemas
"""

# Re-export common schemas from models for convenience
from app.models.common import Message, NewPassword, Token, TokenPayload

__all__ = ["Message", "NewPassword", "Token", "TokenPayload"]
