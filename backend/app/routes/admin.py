import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.database import get_db
from app.models.user import User
from app.models.monetization import Subscription, SubscriptionStatus, Payment, PaymentStatus
from app.routes.payments import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/stats", dependencies=[Depends(require_admin)])
async def get_admin_stats(db: AsyncSession = Depends(get_db)):
    total_users = await db.scalar(select(func.count(User.id)))
    active_subs = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatus.COMPLETED)
    )
    monthly_revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.created_at >= datetime.utcnow() - timedelta(days=30),
        )
    )

    subs_by_tier = await db.execute(
        select(Subscription.tier, func.count(Subscription.id))
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
        .group_by(Subscription.tier)
    )

    return {
        "total_users": total_users or 0,
        "active_subscriptions": active_subs or 0,
        "total_revenue_usd": round(float(total_revenue or 0), 2),
        "monthly_revenue_usd": round(float(monthly_revenue or 0), 2),
        "subscriptions_by_plan": [{"plan": row[0].value if hasattr(row[0], 'value') else row[0], "count": row[1]} for row in subs_by_tier],
    }


@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "tier": u.role.value,
            "daily_downloads": u.downloads_today,
            "total_downloads": u.total_downloads,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.get("/subscriptions", dependencies=[Depends(require_admin)])
async def list_subscriptions(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).order_by(Subscription.created_at.desc()).offset(skip).limit(limit)
    )
    subs = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "user_id": str(s.user_id),
            "plan_id": s.tier.value if hasattr(s.tier, 'value') else str(s.tier),
            "status": s.status.value if hasattr(s.status, 'value') else str(s.status),
            "current_period_start": s.current_period_start.isoformat() if s.current_period_start else None,
            "current_period_end": s.current_period_end.isoformat() if s.current_period_end else None,
            "created_at": s.created_at.isoformat(),
        }
        for s in subs
    ]


@router.post("/users/{user_id}/toggle-ban", dependencies=[Depends(require_admin)])
async def toggle_user_ban(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    await db.commit()
    return {"id": str(user.id), "is_active": user.is_active}


@router.post("/subscriptions/{sub_id}/cancel", dependencies=[Depends(require_admin)])
async def cancel_subscription_admin(
    sub_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Subscription).where(Subscription.id == sub_id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    sub.status = SubscriptionStatus.CANCELED
    sub.canceled_at = datetime.utcnow()
    await db.commit()
    return {"id": str(sub.id), "status": sub.status.value}
