"""SQLAdmin configuration."""

from fastapi import FastAPI
from sqladmin import Admin, ModelView

from app.admin.auth import authentication_backend
from app.core.db import engine
from app.models import Item, User


class UserAdmin(ModelView, model=User):
    """Admin view for User model."""

    column_list = [User.id, User.email, User.full_name, User.is_active, User.is_superuser]
    column_searchable_list = [User.email, User.full_name]
    column_filters = [User.is_active, User.is_superuser]
    column_sortable_list = [User.email, User.is_active, User.created_at] if hasattr(User, "created_at") else [User.email, User.is_active]
    
    # Exclude sensitive fields
    form_excluded_columns = ["hashed_password", "items"]
    column_exclude_list = ["hashed_password"]
    
    # Permissions
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"


class ItemAdmin(ModelView, model=Item):
    """Admin view for Item model."""

    column_list = [Item.id, Item.title, Item.description, Item.owner_id]
    column_searchable_list = [Item.title, Item.description]
    column_filters = [Item.owner_id]
    column_sortable_list = [Item.title]
    
    # Show relationship
    column_details_list = [Item.id, Item.title, Item.description, Item.owner_id, Item.owner]
    
    # Permissions
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    
    name = "Item"
    name_plural = "Items"
    icon = "fa-solid fa-box"


def setup_admin(app: FastAPI) -> None:
    """Setup SQLAdmin interface."""
    from app.core.config import settings
    
    # Enable admin in all environments (with authentication)
    admin = Admin(
        app,
        engine,
        title="Admin Panel",
        base_url="/admin",
        authentication_backend=authentication_backend,
    )
    
    # Register admin views
    admin.add_view(UserAdmin)
    admin.add_view(ItemAdmin)
