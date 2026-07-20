import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "test-user-id"
    user.email = "test@example.com"
    user.username = "testuser"
    user.role = "free"
    user.is_active = True
    user.is_admin = False
    user.downloads_today = 0
    user.daily_download_limit = 5
    user.download_credits = 0
    user.total_downloads = 0
    return user


@pytest_asyncio.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
