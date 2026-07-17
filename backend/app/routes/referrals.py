import secrets
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, text
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


def badge_for_rank(rank: int) -> str:
    if rank == 1:
        return "gold"
    if rank == 2:
        return "silver"
    if rank == 3:
        return "bronze"
    if rank <= 10:
        return "top10"
    if rank <= 50:
        return "top50"
    if rank <= 100:
        return "top100"
    return "referrer"


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
    referral.referred_email = user.email
    referral.status = "completed"
    referral.completed_at = datetime.utcnow()
    referral.reward_credits = REFERRAL_REWARD_DOWNLOADS

    user.daily_download_limit += REFERRAL_REWARD_DOWNLOADS
    await db.commit()

    return {
        "status": "completed",
        "bonus_downloads": REFERRAL_REWARD_DOWNLOADS,
    }


@router.get("/stats")
async def get_referral_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Referral).where(Referral.referrer_id == user.id).limit(1)
    )
    referral_entry = result.scalar_one_or_none()

    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total = await db.scalar(
        select(func.count()).select_from(Referral).where(
            Referral.referrer_id == user.id, Referral.status == "completed"
        )
    )
    this_week = await db.scalar(
        select(func.count()).select_from(Referral).where(
            Referral.referrer_id == user.id,
            Referral.status == "completed",
            Referral.completed_at >= week_start,
        )
    )
    this_month = await db.scalar(
        select(func.count()).select_from(Referral).where(
            Referral.referrer_id == user.id,
            Referral.status == "completed",
            Referral.completed_at >= month_start,
        )
    )
    pending = await db.scalar(
        select(func.count()).select_from(Referral).where(
            Referral.referrer_id == user.id, Referral.status == "pending"
        )
    )
    total_credits = await db.scalar(
        select(func.coalesce(func.sum(Referral.reward_credits), 0)).where(
            Referral.referrer_id == user.id, Referral.status == "completed"
        )
    )

    rank_subq = (
        select(
            Referral.referrer_id,
            func.count(Referral.id).label("cnt"),
            func.dense_rank().over(order_by=func.count(Referral.id).desc()).label("rank"),
        )
        .where(Referral.status == "completed")
        .group_by(Referral.referrer_id)
        .subquery()
    )
    my_rank = await db.scalar(
        select(rank_subq.c.rank).where(rank_subq.c.referrer_id == user.id)
    )

    return {
        "code": referral_entry.referral_code if referral_entry else None,
        "total_referred": total or 0,
        "this_week": this_week or 0,
        "this_month": this_month or 0,
        "pending": pending or 0,
        "total_credits": total_credits or 0,
        "rank": my_rank or 0,
        "badge": badge_for_rank(my_rank or 999),
        "reward_per_referral": REFERRAL_REWARD_DOWNLOADS,
    }


@router.get("/leaderboard")
async def get_leaderboard(
    period: str = Query("all_time", pattern="^(global|weekly|monthly|all_time)$"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    if period == "weekly":
        since = now - timedelta(days=7)
    elif period == "monthly":
        since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        since = datetime(2000, 1, 1)

    query = (
        select(
            Referral.referrer_id,
            User.username,
            func.count(Referral.id).label("count"),
            func.dense_rank().over(order_by=func.count(Referral.id).desc()).label("rank"),
        )
        .join(User, Referral.referrer_id == User.id)
        .where(Referral.status == "completed", Referral.completed_at >= since)
        .group_by(Referral.referrer_id, User.username)
        .order_by(func.count(Referral.id).desc())
        .limit(limit)
    )
    rows = await db.execute(query)
    entries = []
    for row in rows:
        entries.append({
            "rank": row.rank,
            "user_id": str(row.referrer_id),
            "username": row.username,
            "count": row.count,
            "badge": badge_for_rank(row.rank),
        })

    my_rank = None
    for entry in entries:
        if entry["user_id"] == str(user.id):
            my_rank = entry["rank"]
            break

    return {
        "period": period,
        "entries": entries,
        "my_rank": my_rank or len(entries) + 1,
    }


@router.get("/history")
async def get_referral_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Referral)
        .where(Referral.referrer_id == user.id)
        .order_by(Referral.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    referrals = result.scalars().all()

    total = await db.scalar(
        select(func.count()).select_from(Referral).where(Referral.referrer_id == user.id)
    )

    return {
        "referrals": [
            {
                "id": str(r.id),
                "referred_email": r.referred_email or "pending",
                "status": r.status,
                "reward_credits": r.reward_credits,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in referrals
        ],
        "total": total or 0,
        "skip": skip,
        "limit": limit,
    }
