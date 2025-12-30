import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session

from app import crud
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, User


class ItemService:
    """Service layer for item-related business logic."""

    @staticmethod
    def get_items(
        *, session: Session, current_user: User, skip: int = 0, limit: int = 100
    ) -> ItemsPublic:
        """Get items with access control."""
        # Superusers can see all items, regular users only see their own
        owner_id = None if current_user.is_superuser else current_user.id
        items, count = crud.get_items(
            session=session, skip=skip, limit=limit, owner_id=owner_id
        )
        return ItemsPublic(data=items, count=count)

    @staticmethod
    def get_item(*, session: Session, item_id: uuid.UUID, current_user: User) -> ItemPublic:
        """Get an item by ID with access control."""
        item = crud.get_item(session=session, item_id=item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        # Check access: superuser or owner
        if not current_user.is_superuser and item.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        return item

    @staticmethod
    def create_item(
        *, session: Session, item_in: ItemCreate, current_user: User
    ) -> ItemPublic:
        """Create a new item."""
        item = crud.create_item(
            session=session, item_in=item_in, owner_id=current_user.id
        )
        return item

    @staticmethod
    def update_item(
        *, session: Session, item_id: uuid.UUID, item_in: ItemUpdate, current_user: User
    ) -> ItemPublic:
        """Update an item with access control."""
        item = crud.get_item(session=session, item_id=item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        # Check access: superuser or owner
        if not current_user.is_superuser and item.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        updated_item = crud.update_item(session=session, db_item=item, item_in=item_in)
        return updated_item

    @staticmethod
    def delete_item(*, session: Session, item_id: uuid.UUID, current_user: User) -> dict[str, str]:
        """Delete an item with access control."""
        item = crud.get_item(session=session, item_id=item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        # Check access: superuser or owner
        if not current_user.is_superuser and item.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        crud.delete_item(session=session, db_item=item)
        return {"message": "Item deleted successfully"}

