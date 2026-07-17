from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.models.database import get_db
from app.models.user import User
from app.models.monetization import ApiKey, SubscriptionTier
from app.services.api_key_service import create_api_key
from app.routes.payments import get_current_user

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class CreateApiKeyRequest(BaseModel):
    name: str


@router.post("/create")
async def create_new_api_key(
    data: CreateApiKeyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == SubscriptionTier.FREE:
        existing = await db.execute(
            select(ApiKey).where(ApiKey.user_id == user.id, ApiKey.is_active == True)
        )
        if len(existing.scalars().all()) >= 2:
            raise HTTPException(
                status_code=403,
                detail="Free users can only create 2 API keys. Upgrade to Pro for more.",
            )

    api_key, raw_key = await create_api_key(db, user.id, data.name, user.role)
    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "key": raw_key,
        "daily_limit": api_key.daily_limit,
        "created_at": api_key.created_at.isoformat(),
    }


@router.get("/list")
async def list_api_keys(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "prefix": k.key[:12] + "...",
            "tier": k.tier.value if isinstance(k.tier, SubscriptionTier) else k.tier,
            "requests_count": k.requests_count,
            "daily_limit": k.daily_limit,
            "is_active": k.is_active,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat(),
        }
        for k in keys
    ]


@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    api_key.is_active = False
    await db.commit()
    return {"status": "revoked"}
