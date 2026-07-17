import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import limiter
from app.routes import auth, download, payments, api_keys, referrals, affiliates, admin, announcements, contact, ws
from app.models.database import init_db
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("gotot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting GoTot API...")
    await init_db()
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
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Razorpay-Signature", "X-Ad-Completed", "X-API-Key"],
    max_age=600,
)

app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router)
app.include_router(download.router)
app.include_router(payments.router)
app.include_router(api_keys.router)
app.include_router(referrals.router)
app.include_router(affiliates.router)
app.include_router(admin.router)
app.include_router(announcements.router)
app.include_router(contact.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0", "environment": settings.environment}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
