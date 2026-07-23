import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.monetization import ApiKey, SubscriptionTier


def generate_api_key() -> str:
    return "gt_" + secrets.token_hex(32)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def create_api_key(
    db: AsyncSession,
    user_id: str,
    name: str,
    tier: SubscriptionTier = SubscriptionTier.FREE,
    expires_days: Optional[int] = None,
) -> tuple[ApiKey, str]:
    raw_key = generate_api_key()
    hashed = hash_api_key(raw_key)

    limits = {
        SubscriptionTier.FREE: 50,
        SubscriptionTier.PRO: 1000,
        SubscriptionTier.UNLIMITED: 10000,
    }

    api_key = ApiKey(
        user_id=user_id,
        key=hashed,
        name=name,
        tier=tier,
        daily_limit=limits.get(tier, 50),
        expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key, raw_key


async def validate_api_key(db: AsyncSession, raw_key: str) -> Optional[ApiKey]:
    hashed = hash_api_key(raw_key)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key == hashed,
            ApiKey.is_active == True,
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None
    if api_key.requests_count >= api_key.daily_limit:
        return None
    api_key.requests_count += 1
    api_key.last_used_at = datetime.utcnow()
    await db.commit()
    return api_key
