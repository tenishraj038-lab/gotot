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
    "/auth/forgot-password",
    "/auth/reset-password",
    "/auth/verify-email",
    "/auth/google/login",
    "/api-keys/create",
    "/payment/webhook",
}


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)
            if not request.cookies.get(settings.csrf_cookie_name):
                token = secrets.token_hex(32)
                response.set_cookie(
                    key=settings.csrf_cookie_name,
                    value=token,
                    httponly=settings.csrf_cookie_httponly,
                    samesite=settings.csrf_cookie_samesite,
                    secure=settings.csrf_cookie_secure and settings.environment == "production",
                    max_age=3600,
                )
            return response

        if request.url.path in CSRF_EXEMPT_PATHS:
            response = await call_next(request)
            return response

        csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
        csrf_header = request.headers.get("X-CSRF-Token")

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
            if token.count(".") == 2 and len(token) > 20:
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

