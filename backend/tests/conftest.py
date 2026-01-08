from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import File, Item, User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limit() -> Generator[None, None, None]:
    """Disable rate limiting for tests."""
    # Mock the limiter to be disabled and provide view_rate_limit attribute
    original_limiter = getattr(app.state, "limiter", None)
    if original_limiter:
        # Create a mock limiter that is disabled
        from unittest.mock import MagicMock
        mock_limiter = MagicMock()
        mock_limiter.enabled = False
        # Make limit() return a no-op decorator
        def no_op_limit(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        mock_limiter.limit = MagicMock(return_value=no_op_limit)
        app.state.limiter = mock_limiter
    yield
    if original_limiter:
        app.state.limiter = original_limiter


@pytest.fixture(scope="session", autouse=True)
def disable_cache_and_redis() -> Generator[None, None, None]:
    """Disable cache and Redis-dependent features for tests."""
    import os
    # Set environment variables to use in-memory storage
    original_redis_url = os.environ.get("REDIS_URL")
    original_rate_limit_storage = os.environ.get("RATE_LIMIT_STORAGE_URI")
    
    # Use in-memory storage for rate limiting
    os.environ["RATE_LIMIT_STORAGE_URI"] = "memory://"
    # Set a dummy Redis URL that won't be used (since we use memory:// for rate limiting)
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    yield
    
    # Restore original values
    if original_redis_url:
        os.environ["REDIS_URL"] = original_redis_url
    elif "REDIS_URL" in os.environ:
        del os.environ["REDIS_URL"]
    
    if original_rate_limit_storage:
        os.environ["RATE_LIMIT_STORAGE_URI"] = original_rate_limit_storage
    elif "RATE_LIMIT_STORAGE_URI" in os.environ:
        del os.environ["RATE_LIMIT_STORAGE_URI"]


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(File)
        session.execute(statement)
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
