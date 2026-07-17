import secrets
import string
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.models.database import get_db
from app.models.user import User
from app.models.monetization import Referral
from app.routes.payments import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/referrals", tags=["referrals"])
settings = get_settings()

REFERRAL_REWARD_DOWNLOADS = 3


def generate_referral_code() -> str:
    return "GOTOT" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))


@router.get("/my-code")
async def get_my_referral_code(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Referral).where(Referral.referrer_id == user.id).limit(1)
    )
    referral = result.scalar_one_or_none()
    if not referral:
        code = generate_referral_code()
        referral = Referral(referrer_id=user.id, referral_code=code)
        db.add(referral)
        await db.commit()
        await db.refresh(referral)

    total = await db.execute(
        select(func.count()).select_from(Referral).where(
            Referral.referrer_id == user.id,
            Referral.status == "completed",
        )
    )
    total_completed = total.scalar() or 0

    frontend_url = settings.frontend_url.rstrip("/")

    return {
        "code": referral.referral_code,
        "referral_url": f"{frontend_url}?ref={referral.referral_code}",
        "total_referred": total_completed,
        "reward_per_referral": f"+{REFERRAL_REWARD_DOWNLOADS} free downloads",
    }


class ApplyReferralRequest(BaseModel):
    code: str


@router.post("/apply")
async def apply_referral_code(
    data: ApplyReferralRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Referral).where(Referral.referral_code == data.code.upper())
    )
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    if referral.referrer_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot use your own referral code")
    if referral.referred_id:
        raise HTTPException(status_code=400, detail="Referral code already used")

    referral.referred_id = user.id
    referral.status = "completed"
    referral.completed_at = datetime.utcnow()
    referral.reward_credits = REFERRAL_REWARD_DOWNLOADS

    user.daily_download_limit += REFERRAL_REWARD_DOWNLOADS
    await db.commit()

    return {
        "status": "completed",
        "bonus_downloads": REFERRAL_REWARD_DOWNLOADS,
    }
