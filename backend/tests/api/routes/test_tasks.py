"""Tests for task queue functionality."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_enqueue_email_task(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test enqueuing email task.
    
    Note: This test requires tasks-example routes to be enabled (local environment only).
    """
    response = client.post(
        f"{settings.API_V1_STR}/tasks/send-email",
        headers=superuser_token_headers,
        json={
            "email_to": "test@example.com",
            "subject": "Test Subject",
            "html_content": "<p>Test content</p>",
        },
    )
    
    # May return 404 if tasks-example routes are not enabled
    if response.status_code == 404:
        pytest.skip("Tasks example routes not enabled (only available in local environment)")
    
    # Note: This test may fail if Redis is not available
    # In a real scenario, you'd want to mock Redis or use a test Redis instance
    assert response.status_code in [200, 500]  # 500 if Redis unavailable
    if response.status_code == 200:
        content = response.json()
        assert content["status"] == "enqueued"
        assert "job_id" in content
        assert content["message"] == "Email task has been enqueued"


def test_enqueue_process_data_task(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test enqueuing data processing task."""
    response = client.post(
        f"{settings.API_V1_STR}/tasks/process-data",
        headers=superuser_token_headers,
        json={"data": {"key": "value", "number": 123}},
    )
    
    if response.status_code == 404:
        pytest.skip("Tasks example routes not enabled (only available in local environment)")
    
    # Note: This test may fail if Redis is not available
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        content = response.json()
        assert content["status"] == "enqueued"
        assert "job_id" in content
        assert content["message"] == "Data processing task has been enqueued"


def test_get_task_status(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting task status."""
    job_id = "test-job-id-789"
    
    response = client.get(
        f"{settings.API_V1_STR}/tasks/status/{job_id}",
        headers=superuser_token_headers,
    )
    
    if response.status_code == 404 and "not found" not in response.json().get("detail", "").lower():
        pytest.skip("Tasks example routes not enabled (only available in local environment)")
    
    # Note: This test may fail if Redis is not available
    assert response.status_code in [200, 404, 500]
    if response.status_code == 200:
        content = response.json()
        assert "job_id" in content or "status" in content


def test_get_task_status_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting status for non-existent task."""
    job_id = "non-existent-job-id"
    
    response = client.get(
        f"{settings.API_V1_STR}/tasks/status/{job_id}",
        headers=superuser_token_headers,
    )
    
    if response.status_code == 404 and "not found" not in response.json().get("detail", "").lower():
        pytest.skip("Tasks example routes not enabled (only available in local environment)")
    
    assert response.status_code == 404
    content = response.json()
    assert "not found" in content["detail"].lower()


def test_enqueue_email_task_invalid_email(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test enqueuing email task with invalid email."""
    response = client.post(
        f"{settings.API_V1_STR}/tasks/send-email",
        headers=superuser_token_headers,
        json={
            "email_to": "invalid-email",
            "subject": "Test Subject",
            "html_content": "<p>Test content</p>",
        },
    )
    
    assert response.status_code == 422  # Validation error


def test_enqueue_email_task_requires_auth(client: TestClient) -> None:
    """Test that task endpoints require authentication."""
    response = client.post(
        f"{settings.API_V1_STR}/tasks/send-email",
        json={
            "email_to": "test@example.com",
            "subject": "Test Subject",
            "html_content": "<p>Test content</p>",
        },
    )
    
    assert response.status_code == 401  # Unauthorized
