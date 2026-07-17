from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
import secrets
import hashlib
import hmac
import logging
from app.config import get_settings

logger = logging.getLogger("gotot.csrf")

settings = get_settings()


CSRF_EXEMPT_PATHS = {
    "/health",
    "/contact",
    "/auth/register",
    "/auth/login",
    "/auth/refresh",
    "/api-keys/create",
}


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)
            token = secrets.token_hex(32)
            response.set_cookie(
                key="csrf_token",
                value=token,
                httponly=True,
                samesite="lax",
                secure=settings.environment == "production",
                max_age=3600,
            )
            return response

        if request.url.path in CSRF_EXEMPT_PATHS:
            response = await call_next(request)
            return response

        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and len(auth_header) > 20:
            response = await call_next(request)
            return response

        api_key = request.headers.get("X-API-Key", "")
        if api_key and len(api_key) > 16:
            response = await call_next(request)
            return response

        if not csrf_cookie or not csrf_header:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing"},
            )

        if not hmac.compare_digest(csrf_cookie, csrf_header):
            logger.warning(f"CSRF token mismatch for {request.method} {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch"},
            )

        response = await call_next(request)
        return response
