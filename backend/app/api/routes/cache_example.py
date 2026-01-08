"""Example routes demonstrating cache usage."""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache

from app.api.deps import CurrentUser, SessionDep
from app.models.item import ItemPublic, ItemsPublic

router = APIRouter(prefix="/cache-example", tags=["cache-example"])


@router.get("/items", response_model=ItemsPublic)
@cache(expire=60)  # Cache for 60 seconds
async def get_cached_items(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Get items with caching.

    This endpoint is cached for 60 seconds.
    """
    from app.services import ItemService

    return ItemService.get_items(
        session=session, current_user=current_user, skip=skip, limit=limit
    )


@router.get("/items/{item_id}", response_model=ItemPublic)
@cache(expire=300, key_builder=lambda *args, **kwargs: f"item:{kwargs['item_id']}")
async def get_cached_item(
    item_id: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get a specific item with caching.

    This endpoint is cached for 5 minutes with a custom key.
    """
    from app.services import ItemService
    import uuid

    return ItemService.get_item(
        session=session, item_id=uuid.UUID(item_id), current_user=current_user
    )
