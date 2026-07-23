import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from httpx import AsyncClient, ASGITransport

from app.config import Settings


@pytest.fixture
def test_settings():
    return Settings(
        secret_key="test-secret-key-at-least-32-characters-long!!",
        database_url="sqlite+aiosqlite:///test.db",
        redis_url="memory://",
        environment="development",
        log_level="debug",
        allowed_origins="http://localhost:3000",
        celery_broker_url="redis://localhost:6379/1",
        max_file_size_mb=500,
        max_request_size_mb=10,
        rate_limit_per_minute=60,
        rate_limit_download_per_minute=10,
        access_token_expire_minutes=60,
        refresh_token_expire_days=30,
        algorithm="HS256",
        frontend_url="http://localhost:3000",
        download_dir="/tmp/test_downloads",
        temp_dir="/tmp/test_temp",
        download_timeout=300,
        info_timeout=30,
        cache_ttl=3600,
        file_retention_hours=1,
        cleanup_interval_seconds=3600,
        allowed_domains="*",
        razorpay_key_id="",
        razorpay_key_secret="",
        razorpay_webhook_secret="",
        razorpay_pro_plan_id="",
        razorpay_unlimited_plan_id="",
        currency="USD",
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        smtp_from_email="noreply@test.local",
        admin_email="admin@test.local",
        support_email="support@test.local",
        dmca_email="dmca@test.local",
        privacy_email="privacy@test.local",
        google_client_id="",
        google_client_secret="",
        google_redirect_uri="http://localhost:3000/auth/google/callback",
        request_id_header="X-Request-ID",
        csrf_cookie_name="csrf_token",
        csrf_cookie_secure=False,
        csrf_cookie_httponly=True,
        csrf_cookie_samesite="lax",
    )


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
async def client(test_settings):
    with patch("app.config.get_settings", return_value=test_settings):
        with patch("app.models.database.init_db", AsyncMock()):
            from app.main import app
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac


@pytest_asyncio.fixture
async def client_with_mock_db(test_settings, mock_db_session):
    with patch("app.config.get_settings", return_value=test_settings):
        with patch("app.models.database.init_db", AsyncMock()):
            with patch("app.models.database.get_db", return_value=iter([mock_db_session])):
                from app.main import app
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    yield ac
