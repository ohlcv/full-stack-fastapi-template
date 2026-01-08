"""Permission system configuration using fastapi-permissions."""

from typing import Annotated

from fastapi import Depends
from fastapi_permissions import Allow, Deny, Everyone

from app.api.deps import CurrentUser
from app.models import User


def get_user_principals(user: User | None) -> list[str]:
    """Get principals (roles/permissions) for a user."""
    if user is None:
        return [Everyone]
    
    principals = [Everyone, f"user:{user.id}"]
    
    if user.is_superuser:
        principals.append("role:admin")
    
    if user.is_active:
        principals.append("role:active")
    else:
        principals.append("role:inactive")
    
    return principals


# Dependency to get current user principals
def get_principals(current_user: CurrentUser | None = None) -> list[str]:
    """Get principals for the current user."""
    user = current_user if current_user else None
    return get_user_principals(user)


# Configure permissions dependency
Principal = Annotated[list[str], Depends(get_principals)]


def setup_permissions() -> None:
    """Setup fastapi-permissions system."""
    # Permissions are configured through dependencies
    # This function can be extended for global permission configuration
    pass
