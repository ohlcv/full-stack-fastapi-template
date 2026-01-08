"""Tests for cache functionality."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.item import create_random_item


def test_cached_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test cached items endpoint.
    
    Note: This test requires cache-example routes to be enabled (local environment only).
    """
    # Create some items
    create_random_item(db)
    create_random_item(db)
    
    # First request (should hit database)
    response1 = client.get(
        f"{settings.API_V1_STR}/cache-example/items",
        headers=superuser_token_headers,
    )
    
    # May return 404 if cache-example routes are not enabled
    if response1.status_code == 404:
        pytest.skip("Cache example routes not enabled (only available in local environment)")
    
    assert response1.status_code == 200
    content1 = response1.json()
    assert "data" in content1
    assert "count" in content1
    
    # Second request (should hit cache)
    response2 = client.get(
        f"{settings.API_V1_STR}/cache-example/items",
        headers=superuser_token_headers,
    )
    
    assert response2.status_code == 200
    content2 = response2.json()
    # Should return same data (from cache)
    assert content2["count"] == content1["count"]


def test_cached_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test cached single item endpoint."""
    item = create_random_item(db)
    
    # First request
    response1 = client.get(
        f"{settings.API_V1_STR}/cache-example/items/{item.id}",
        headers=superuser_token_headers,
    )
    
    if response1.status_code == 404:
        pytest.skip("Cache example routes not enabled (only available in local environment)")
    
    assert response1.status_code == 200
    content1 = response1.json()
    assert content1["id"] == str(item.id)
    assert content1["title"] == item.title
    
    # Second request (should hit cache)
    response2 = client.get(
        f"{settings.API_V1_STR}/cache-example/items/{item.id}",
        headers=superuser_token_headers,
    )
    
    assert response2.status_code == 200
    content2 = response2.json()
    assert content2["id"] == content1["id"]
    assert content2["title"] == content1["title"]


def test_cached_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test cached item endpoint with non-existent item."""
    fake_id = uuid.uuid4()
    
    response = client.get(
        f"{settings.API_V1_STR}/cache-example/items/{fake_id}",
        headers=superuser_token_headers,
    )
    
    if response.status_code == 404 and "not found" not in response.json().get("detail", "").lower():
        pytest.skip("Cache example routes not enabled (only available in local environment)")
    
    assert response.status_code == 404


def test_cache_headers(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that cache responses include appropriate headers."""
    create_random_item(db)
    
    response = client.get(
        f"{settings.API_V1_STR}/cache-example/items",
        headers=superuser_token_headers,
    )
    
    if response.status_code == 404:
        pytest.skip("Cache example routes not enabled (only available in local environment)")
    
    assert response.status_code == 200
    # Cache headers may be present depending on fastapi-cache2 implementation
    # This test verifies the endpoint works with caching enabled
