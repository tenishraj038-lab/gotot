import logging
import time
import os
from contextlib import asynccontextmanager
from typing import Optional

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.logging import JSONLogMiddleware, JSONLogFormatter
from app.middleware.rate_limit import limiter
from app.middleware.csrf import CSRFMiddleware
from app.middleware.request_size import RequestSizeLimitMiddleware
from app.routes import auth, download, payments, api_keys, referrals, affiliates, admin, announcements, contact, ws, google_auth, notifications, feedback
from app.models.database import init_db, async_session, engine
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY, Counter, Histogram, Gauge, Info

settings = get_settings()

json_handler = logging.StreamHandler()
json_handler.setFormatter(JSONLogFormatter())
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    handlers=[json_handler],
)
logger = logging.getLogger("gotot")

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment, traces_sample_rate=0.1)

# Prometheus metrics
REQUEST_COUNT = Counter("gotot_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("gotot_request_latency_seconds", "Request latency", ["method", "endpoint"])
DOWNLOAD_COUNT = Counter("gotot_downloads_total", "Total downloads", ["platform", "status"])
UPTIME_GAUGE = Gauge("gotot_uptime_seconds", "Application uptime in seconds")
START_TIME = time.time()

UPTIME_GAUGE.set_function(lambda: time.time() - START_TIME)

app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting GoTot API...", extra={"version": "3.1.0", "environment": settings.environment})

    os.makedirs(settings.download_dir, exist_ok=True)
    os.makedirs(settings.temp_dir, exist_ok=True)

    if settings.environment == "production":
        _validate_config()

    start = time.time()
    try:
        await init_db()
        logger.info("Database initialized", extra={"elapsed_s": round(time.time() - start, 2)})
    except Exception as e:
        if settings.environment == "production":
            logger.critical("Database init failed in production - exiting", extra={"error": str(e)})
            raise
        logger.warning("Database init failed (will retry on demand)", extra={"error": str(e)})
    yield
    logger.info("Shutting down GoTot API...")


def _validate_config():
    issues = []
    if not settings.secret_key or len(settings.secret_key) < 32:
        issues.append("SECRET_KEY must be at least 32 characters")
    if not settings.database_url or "gotot_pass" in settings.database_url:
        issues.append("DATABASE_URL uses default password")
    if not settings.google_client_id:
        logger.warning("GOOGLE_CLIENT_ID not set")
    if not settings.razorpay_key_id:
        logger.warning("RAZORPAY_KEY_ID not set")
    if not settings.smtp_host:
        logger.warning("SMTP_HOST not set")
    for issue in issues:
        logger.error(issue)


app = FastAPI(
    title="GoTot API",
    description="Multi-platform video downloader API with monetization",
    version="3.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Razorpay-Signature",
                   "X-Ad-Completed", "X-API-Key", "X-CSRF-Token", "X-Google-Token"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
    max_age=600,
)

app.add_middleware(JSONLogMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)

if settings.environment == "production":
    app.add_middleware(CSRFMiddleware)

app.include_router(auth.router)
app.include_router(google_auth.router)
app.include_router(download.router)
app.include_router(payments.router)
app.include_router(api_keys.router)
app.include_router(referrals.router)
app.include_router(affiliates.router)
app.include_router(admin.router)
app.include_router(announcements.router)
app.include_router(contact.router)
app.include_router(ws.router)
app.include_router(notifications.router)
app.include_router(feedback.router)


@app.get("/health")
async def health():
    from app.services.downloader import get_ffmpeg_status
    db_status = "disconnected"
    db_latency_ms = 0
    try:
        from sqlalchemy import text
        start = time.time()
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            db_status = "connected"
        db_latency_ms = round((time.time() - start) * 1000, 1)
    except Exception:
        pass

    ffmpeg = get_ffmpeg_status()

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "version": "3.2.0",
        "environment": settings.environment,
        "database": db_status,
        "database_latency_ms": db_latency_ms,
        "ffmpeg": ffmpeg,
        "uptime_seconds": round(time.time() - app_start_time, 1),
        "timestamp": time.time(),
    }


@app.get("/health/readiness")
async def readiness():
    checks = {}
    healthy = True

    # Database check
    try:
        from sqlalchemy import text
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        healthy = False

    # Redis check
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.close()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:100]}"

    # Disk check
    try:
        dw_dir = settings.download_dir
        if not os.path.exists(dw_dir):
            os.makedirs(dw_dir, exist_ok=True)
        test_file = os.path.join(dw_dir, ".readiness_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        checks["disk"] = "ok"
    except Exception as e:
        checks["disk"] = f"error: {str(e)[:100]}"

    status_code = 200 if healthy else 503
    return JSONResponse(
        content={"status": "ready" if healthy else "not_ready", "checks": checks, "timestamp": time.time()},
        status_code=status_code,
    )


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/meta")
async def metadata():
    return {
        "name": "GoTot API",
        "version": "3.1.0",
        "environment": settings.environment,
        "supported_platforms": [
            "tiktok", "instagram", "twitter", "facebook",
            "reddit", "vimeo", "dailymotion", "twitch", "linkedin", "pinterest",
            "snapchat", "bilibili", "soundcloud", "rumble", "odysee",
        ],
        "documentation_url": f"{settings.frontend_url}/docs",
        "terms_url": f"{settings.frontend_url}/terms",
        "privacy_url": f"{settings.frontend_url}/privacy",
        "dmca_url": f"{settings.frontend_url}/dmca",
        "contact_email": settings.support_email,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled error",
        extra={
            "method": request.method,
            "path": str(request.url.path),
            "rid": getattr(request.state, "request_id", "N/A"),
        },
        exc_info=True,
    )
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status="500").inc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later.", "error_id": getattr(request.state, "request_id", None)},
    )
