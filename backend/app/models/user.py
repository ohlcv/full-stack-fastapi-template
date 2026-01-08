import uuid
from typing import TYPE_CHECKING

from fastapi_users import schemas
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.item import Item


# Shared properties
class UserBase(SQLModel):
    """Base user properties."""
    email: EmailStr = Field(max_length=320, unique=True, index=True)
    hashed_password: str = Field(max_length=1024)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
# Inherit from BaseUserCreate to get create_update_dict method
class UserCreate(schemas.BaseUserCreate):
    """User creation schema compatible with fastapi-users."""
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
# Inherit from BaseUserUpdate to get create_update_dict method
class UserUpdate(schemas.BaseUserUpdate):
    """User update schema compatible with fastapi-users."""
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
# Compatible with fastapi-users: includes all required fields (id, email, hashed_password, is_active, is_superuser, is_verified)
class User(UserBase, table=True):
    """User model compatible with fastapi-users."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    files: list["File"] = Relationship(back_populates="owner", cascade_delete=True)


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

