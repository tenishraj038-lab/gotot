import time
import uuid
import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.config import get_settings

logger = logging.getLogger("gotot.security")
settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]

        request.state.request_id = request_id
        request.state.start_time = start_time

        try:
            response: Response = await call_next(request)
        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}", exc_info=True)
            raise

        elapsed = time.time() - start_time
        if elapsed > 5:
            logger.warning(f"Slow request: {request.method} {request.url.path} took {elapsed:.2f}s [rid={request_id}]")

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Request-ID"] = request_id
        response.headers["X-DNS-Prefetch-Control"] = "off"
        response.headers["X-Download-Options"] = "noopen"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        if settings.environment == "production":
            csp_parts = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://checkout.razorpay.com https://www.googletagmanager.com",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                "img-src 'self' data: https: blob:",
                "font-src 'self' https://fonts.gstatic.com",
                "connect-src 'self' https://api.razorpay.com https://sentry.io",
                "frame-src 'self' https://checkout.razorpay.com",
                "media-src 'self'",
                "object-src 'none'",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_parts)

        return response
