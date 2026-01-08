import uuid
from typing import TYPE_CHECKING

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.item import Item


# Shared properties
# Note: email, is_active, is_superuser, is_verified are inherited from SQLAlchemyBaseUserTableUUID
class UserBase(SQLModel):
    """Base user properties (excluding fields from SQLAlchemyBaseUserTableUUID)."""
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(SQLModel):
    """User creation schema compatible with fastapi-users."""
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    """User update schema compatible with fastapi-users."""
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
# Inherit from SQLAlchemyBaseUserTableUUID for fastapi-users compatibility
class User(SQLAlchemyBaseUserTableUUID, UserBase, table=True):
    """User model compatible with fastapi-users."""
    # id, email, hashed_password, is_active, is_superuser, is_verified 
    # are inherited from SQLAlchemyBaseUserTableUUID
    
    full_name: str | None = Field(default=None, max_length=255)
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(SQLModel):
    """Public user schema for API responses."""
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool
    is_verified: bool
    full_name: str | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int

