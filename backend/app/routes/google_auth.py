import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import get_db
from app.models.user import User
from app.services.auth_service import create_access_token, create_refresh_token
from app.services.audit_log import audit_logger
from app.config import get_settings

router = APIRouter(prefix="/auth/google", tags=["auth"])
settings = get_settings()
logger = logging.getLogger("gotot.google_auth")


class GoogleTokenRequest(BaseModel):
    id_token: str


class GoogleTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


@router.post("/login", response_model=GoogleTokenResponse)
async def google_login(
    request: Request,
    data: GoogleTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google authentication not configured")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": data.id_token},
                timeout=10,
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")

            google_info = resp.json()

            if google_info.get("aud") != settings.google_client_id:
                raise HTTPException(status_code=401, detail="Token audience mismatch")

            google_email = google_info.get("email", "")
            google_name = google_info.get("name", google_email.split("@")[0])
            google_sub = google_info.get("sub", "")

            if not google_email:
                raise HTTPException(status_code=400, detail="Email not provided by Google")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Failed to verify Google token")

    result = await db.execute(
        select(User).where(User.email == google_email)
    )
    user = result.scalar_one_or_none()

    is_new = False
    if not user:
        import secrets
        username_base = google_name.replace(" ", "_").lower()[:20]
        username = username_base
        counter = 1
        while True:
            existing = await db.execute(select(User).where(User.username == username))
            if not existing.scalar_one_or_none():
                break
            username = f"{username_base}{counter}"
            counter += 1

        import uuid
        user = User(
            email=google_email,
            username=username,
            hashed_password=f"google_{uuid.uuid4().hex}",
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        is_new = True

        ip = request.client.host if request.client else "unknown"
        audit_logger.register(str(user.id), google_email, ip)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    ip = request.client.host if request.client else "unknown"
    audit_logger.login_success(str(user.id), google_email, ip)

    return GoogleTokenResponse(
        access_token=create_access_token({"sub": str(user.id), "role": user.role.value}),
        refresh_token=create_refresh_token({"sub": str(user.id)}, token_version=user.refresh_token_version),
        is_new_user=is_new,
    )
