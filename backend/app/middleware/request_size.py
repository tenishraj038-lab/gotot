from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
import logging

from app.config import get_settings

logger = logging.getLogger("gotot.security")
settings = get_settings()

MAX_REQUEST_SIZE = settings.max_request_size_mb * 1024 * 1024

SIZE_CHECK_PATHS = {
    "/download/info", "/download/start", "/download/batch", "/download/queue",
    "/download/playlist", "/download/subtitles", "/auth/register", "/auth/login",
    "/contact", "/payment/create-subscription",
}


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_size: int = MAX_REQUEST_SIZE):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        if request.method in ("GET", "HEAD", "OPTIONS", "DELETE"):
            return await call_next(request)

        if request.url.path not in SIZE_CHECK_PATHS:
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    logger.warning(
                        "Request body too large",
                        extra={
                            "path": request.url.path,
                            "size": size,
                            "max": self.max_size,
                            "ip": request.client.host if request.client else "",
                        },
                    )
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Request body too large. Maximum size is {settings.max_request_size_mb} MB."},
                    )
            except (ValueError, TypeError):
                pass

        return await call_next(request)
