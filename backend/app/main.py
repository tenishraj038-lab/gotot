import logging
import time
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
from app.routes import auth, download, payments, api_keys, referrals, affiliates, admin, announcements, contact, ws, google_auth, notifications, feedback
from app.models.database import init_db
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting GoTot API...")
    start = time.time()
    try:
        await init_db()
        logger.info(f"Database initialized in {time.time() - start:.2f}s")
    except Exception as e:
        logger.warning(f"Database init failed (will retry on demand): {e}")
    yield
    logger.info("Shutting down GoTot API...")


app = FastAPI(
    title="GoTot API",
    description="Multi-platform video downloader API with monetization",
    version="3.0.0",
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
    expose_headers=["X-Request-ID"],
    max_age=600,
)

app.add_middleware(JSONLogMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

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
    db_ok = False
    try:
        from app.models.database import async_session
        from sqlalchemy import text
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "3.0.0",
        "environment": settings.environment,
        "database": "connected" if db_ok else "disconnected",
    }


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc} [rid={getattr(request.state, 'request_id', 'N/A')}]", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )