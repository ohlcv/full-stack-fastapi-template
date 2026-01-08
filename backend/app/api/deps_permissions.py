"""Permission dependencies for API routes."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi_permissions import Allow, All, Deny, Everyone
from fastapi_permissions.permissions import Permission

from app.api.deps import CurrentUser
from app.core.permissions import get_user_principals


def require_permission(action: str, resource: str | None = None):
    """Decorator to require specific permission."""
    def permission_checker(
        current_user: CurrentUser,
        principals: Annotated[list[str], Depends(get_user_principals)],
    ) -> bool:
        """Check if user has required permission."""
        # Admin has all permissions
        if "role:admin" in principals:
            return True
        
        # Check specific permission
        # This is a simplified version - you can extend it based on your needs
        if resource:
            resource_id = str(resource) if hasattr(resource, "__str__") else resource
            user_id = str(current_user.id)
            
            # User can perform actions on their own resources
            if f"user:{user_id}" in principals and resource_id == user_id:
                return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    return permission_checker


def require_admin(current_user: CurrentUser) -> bool:
    """Require admin role."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return True


RequireAdmin = Annotated[bool, Depends(require_admin)]
