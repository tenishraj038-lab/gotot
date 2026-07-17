import json
import time
import logging
import uuid
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class JSONLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("gotot.http")

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        request.state.request_id = request_id
        request.state.start_time = start_time

        response: Response = await call_next(request)

        elapsed_ms = int((time.time() - start_time) * 1000)
        status_code = response.status_code

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) if request.url.query else "",
            "status": status_code,
            "elapsed_ms": elapsed_ms,
            "ip": request.client.host if request.client else "",
            "user_agent": request.headers.get("user-agent", ""),
            "content_length": response.headers.get("content-length", 0),
        }

        if status_code >= 500:
            self.logger.error(json.dumps(log_entry))
        elif status_code >= 400:
            self.logger.warning(json.dumps(log_entry))
        else:
            self.logger.info(json.dumps(log_entry))

        return response


class JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)
