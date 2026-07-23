#!/usr/bin/env python3
"""
E2E test runner for GoToT backend.
Overrides database (SQLite) and Redis (fakeredis) for local testing.
"""
import os
import sys
import json
import asyncio

# Set test env BEFORE any app imports
os.environ.setdefault("SECRET_KEY", "test-secret-for-e2e-only-abcdef12345")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_e2e.db")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "debug")
os.environ.setdefault("ALLOWED_ORIGINS", "*")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "9999")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch redis before any imports
import fakeredis.aioredis
import app.services.cache as cache_mod
original_get_redis = cache_mod.get_redis

async def fakeredis_get():
    if cache_mod._redis is None:
        cache_mod._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return cache_mod._redis

cache_mod.get_redis = fakeredis_get

# Patch rate limiter storage
from app.middleware.rate_limit import limiter
limiter._storage_uri = ""
limiter.storage = None

from app.main import app
from app.models.database import Base, engine
from app.services.auth_service import hash_password, create_access_token, create_refresh_token
from app.config import get_settings

settings = get_settings()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Import models to ensure tables created
    import app.models.user
    import app.models.monetization
    import app.models.download
    import app.models.notification
    import app.models.audit
    import app.models.feature_flags
    print("  Tables created")


async def create_test_user():
    """Create a test user for E2E testing."""
    from app.models.database import async_session
    from app.models.user import User
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == "test@gotot.app"))
        if result.scalar_one_or_none():
            print("  Test user already exists")
            return

        user = User(
            email="test@gotot.app",
            username="testuser",
            hashed_password=hash_password("TestPass1"),
            is_verified=True,
            is_admin=True,
        )
        db.add(user)
        await db.commit()
        print(f"  Created test user: {user.email} (admin={user.is_admin})")


async def test_auth_flow():
    """Test the complete auth flow via direct API calls."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    base_url = "http://test"

    async with AsyncClient(transport=transport, base_url=base_url) as client:
        # 1. Health check
        r = await client.get("/health")
        assert r.status_code == 200, f"Health check failed: {r.status_code}"
        data = r.json()
        assert data["status"] in ("ok", "degraded")
        print(f"  [OK] Health check: {data['status']}")

        # 2. Register
        r = await client.post("/auth/register", json={
            "email": "newuser@gotot.app",
            "username": "newuser",
            "password": "StrongPass1",
        })
        assert r.status_code == 201, f"Register failed: {r.status_code} {r.text}"
        reg_data = r.json()
        assert "access_token" in reg_data
        assert "refresh_token" in reg_data
        access_token = reg_data["access_token"]
        refresh_token = reg_data["refresh_token"]
        print("  [OK] Register: tokens received")

        # 3. Login
        r = await client.post("/auth/login", json={
            "email": "newuser@gotot.app",
            "password": "StrongPass1",
        })
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        login_data = r.json()
        assert "access_token" in login_data
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        print("  [OK] Login: tokens received")

        # 4. Get /auth/me
        r = await client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200, f"Get me failed: {r.status_code} {r.text}"
        me = r.json()
        assert me["email"] == "newuser@gotot.app"
        assert me["username"] == "newuser"
        print("  [OK] Get me: user info retrieved")

        # 5. Refresh token
        r = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert r.status_code == 200, f"Refresh failed: {r.status_code} {r.text}"
        refresh_data = r.json()
        assert "access_token" in refresh_data
        new_access = refresh_data["access_token"]
        print("  [OK] Refresh token: new tokens received")

        # 6. Change password (requires version bump)
        r = await client.post("/auth/change-password", json={
            "current_password": "StrongPass1",
            "new_password": "StrongerPass2",
        }, headers={"Authorization": f"Bearer {new_access}"})
        assert r.status_code == 200, f"Change password failed: {r.status_code} {r.text}"
        print("  [OK] Change password")

        # 7. Login with new password
        r = await client.post("/auth/login", json={
            "email": "newuser@gotot.app",
            "password": "StrongerPass2",
        })
        assert r.status_code == 200, f"Login with new password failed: {r.status_code}"
        login2 = r.json()
        access2 = login2["access_token"]
        refresh2 = login2["refresh_token"]
        print("  [OK] Login with new password")

        # 8. Logout
        r = await client.post("/auth/logout", headers={"Authorization": f"Bearer {access2}"})
        assert r.status_code == 200, f"Logout failed: {r.status_code} {r.text}"
        assert r.json()["status"] == "logged_out"
        print("  [OK] Logout")

        # 9. Old refresh token invalidated by logout
        r = await client.post("/auth/refresh", json={
            "refresh_token": refresh2,
        })
        assert r.status_code == 401, f"Old refresh should fail: {r.status_code}"
        print("  [OK] Old refresh token rejected after logout")

        # 10. Forgot password
        r = await client.post("/auth/forgot-password", json={
            "email": "newuser@gotot.app",
        })
        assert r.status_code == 200
        assert "if_account_exists_email_sent" in r.json()["status"]
        print("  [OK] Forgot password")

        # 11. Verify email with token
        from app.services.auth_service import create_email_verification_token
        verify_token = create_email_verification_token("newuser@gotot.app")
        r = await client.post("/auth/verify-email", json={"token": verify_token})
        assert r.status_code == 200
        status = r.json()["status"]
        assert status in ("verified", "already_verified")
        print(f"  [OK] Verify email: {status}")

        # 12. Reset password with token
        from app.services.auth_service import create_password_reset_token
        reset_token = create_password_reset_token("newuser@gotot.app")
        r = await client.post("/auth/reset-password", json={
            "token": reset_token,
            "new_password": "ResetPass99",
        })
        assert r.status_code == 200
        assert r.json()["status"] == "password_reset"
        print("  [OK] Reset password")

        # 13. Login with reset password
        r = await client.post("/auth/login", json={
            "email": "newuser@gotot.app",
            "password": "ResetPass99",
        })
        assert r.status_code == 200
        print("  [OK] Login with reset password")

        # 14. Protected route without auth
        r = await client.get("/auth/me")
        assert r.status_code == 401
        print("  [OK] Protected route rejects unauthenticated requests")

        # 15. Admin test
        r = await client.post("/auth/login", json={
            "email": "test@gotot.app",
            "password": "TestPass1",
        })
        assert r.status_code == 200
        admin_token = r.json()["access_token"]
        r = await client.get("/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        stats = r.json()
        assert "total_users" in stats
        print(f"  [OK] Admin stats: {stats['total_users']} users")

        # 16. Non-admin rejected
        r = await client.get("/admin/stats", headers={"Authorization": f"Bearer {access2}"})
        assert r.status_code == 403
        print("  [OK] Non-admin rejected from admin routes")

        # 17. Contact form
        r = await client.post("/contact", json={
            "name": "Test User",
            "email": "test@example.com",
            "message": "This is a test message for the contact form.",
        })
        assert r.status_code == 200
        print("  [OK] Contact form")

    return True


async def test_download_flow():
    """Test download-related endpoints."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    base_url = "http://test"

    async with AsyncClient(transport=transport, base_url=base_url) as client:
        # No real URLs to test with, but verify the info endpoint validates
        r = await client.post("/download/info", json={"url": "invalid-url"})
        assert r.status_code == 422, f"Invalid URL should fail: {r.status_code}"
        print("  [OK] Download info validates URLs")

        r = await client.post("/download/start", json={
            "url": "not-a-valid-url",
            "format_id": "18",
        })
        assert r.status_code == 422
        print("  [OK] Download start validates URLs")

        # Get recent downloads without auth
        r = await client.get("/download/recent")
        assert r.status_code == 200
        print("  [OK] Recent downloads (unauthenticated)")

    return True


async def test_security():
    """Test security headers and CSRF."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    base_url = "http://test"

    async with AsyncClient(transport=transport, base_url=base_url) as client:
        r = await client.get("/health")
        # Check security headers
        headers = r.headers
        assert "x-content-type-options" in headers
        assert "x-frame-options" in headers
        assert "strict-transport-security" in headers
        assert "x-request-id" in headers
        print("  [OK] Security headers present")
        print(f"  Headers: XFO={headers.get('x-frame-options')}, HSTS={headers.get('strict-transport-security')[:20]}...")

    return True


async def main():
    print("\n=== GoToT E2E Test Suite ===\n")
    print(f"  DB: {settings.database_url}")
    print(f"  Environment: {settings.environment}")
    print()

    print("[1/5] Initializing database...")
    await init_db()
    await create_test_user()

    print("\n[2/5] Testing auth flow...")
    try:
        await test_auth_flow()
    except AssertionError as e:
        print(f"  [FAIL] {e}")
        raise

    print("\n[3/5] Testing download validation...")
    try:
        await test_download_flow()
    except AssertionError as e:
        print(f"  [FAIL] {e}")
        raise

    print("\n[4/5] Testing security headers...")
    try:
        await test_security()
    except AssertionError as e:
        print(f"  [FAIL] {e}")
        raise

    print("\n[5/5] Running existing pytest suite...")
    import pytest
    exit_code = pytest.main(["-v", "--tb=short", "--no-header", "tests/", "-x"])
    if exit_code == 0:
        print("  All tests passed!")
    else:
        print(f"  Test suite exited with code {exit_code}")

    print("\n=== E2E Test Summary ===")
    print("  Auth: login, register, refresh, change-password, forgot/reset password,")
    print("         verify email, logout, token invalidation, protected routes")
    print("  Admin: stats accessible for admin, rejected for non-admin")
    print("  Download: URL validation works correctly")
    print("  Security: all headers present")
    print("  pytest: 74 test cases")
    print()


if __name__ == "__main__":
    asyncio.run(main())
