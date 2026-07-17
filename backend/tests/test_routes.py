import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health(self):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "version" in data


@pytest.mark.asyncio
class TestContactEndpoint:
    async def test_contact_missing_fields(self):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/contact", json={})
            assert response.status_code in (400, 422)

    async def test_contact_invalid_email(self):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/contact", json={
                "name": "Test",
                "email": "not-an-email",
                "subject": "Hello",
                "message": "Test message"
            })
            assert response.status_code in (400, 422)
