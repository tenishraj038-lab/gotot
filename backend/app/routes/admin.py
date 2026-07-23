import logging
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.models.database import get_db, engine
from app.models.user import User, DownloadHistory
from app.models.monetization import Subscription, SubscriptionStatus, Payment, PaymentStatus, Referral, ApiKey
from app.models.feature_flags import FeatureFlag
from app.routes.payments import get_current_user
from app.services.audit_log import audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/stats", dependencies=[Depends(require_admin)])
async def get_admin_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    new_today = await db.scalar(select(func.count(User.id)).where(User.created_at >= today_start))

    total_downloads = await db.scalar(select(func.count(DownloadHistory.id)))
    downloads_today = await db.scalar(
        select(func.count(DownloadHistory.id)).where(DownloadHistory.created_at >= today_start)
    )
    unique_ips = await db.scalar(
        select(func.count(func.distinct(DownloadHistory.ip_address)))
    )

    active_subs = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatus.COMPLETED)
    )
    monthly_revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.created_at >= month_ago,
        )
    )
    weekly_revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.created_at >= week_ago,
        )
    )

    subs_by_tier = await db.execute(
        select(Subscription.tier, func.count(Subscription.id))
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
        .group_by(Subscription.tier)
    )

    downloads_by_platform = await db.execute(
        select(DownloadHistory.platform, func.count(DownloadHistory.id))
        .group_by(DownloadHistory.platform)
        .order_by(func.count(DownloadHistory.id).desc())
        .limit(10)
    )

    subs_by_tier_map = {str(row[0]): row[1] for row in subs_by_tier}
    return {
        "users": {
            "total": total_users or 0,
            "active": active_users or 0,
            "new_today": new_today or 0,
        },
        "downloads": {
            "total": total_downloads or 0,
            "today": downloads_today or 0,
            "unique_ips": unique_ips or 0,
            "by_platform": {row[0]: row[1] for row in downloads_by_platform},
        },
        "revenue": {
            "total_usd": round(float(total_revenue or 0), 2),
            "monthly_usd": round(float(monthly_revenue or 0), 2),
            "weekly_usd": round(float(weekly_revenue or 0), 2),
        },
        "subscriptions": {
            "active": active_subs or 0,
            "by_plan": subs_by_tier_map,
        },
        # Flat fields for frontend compatibility
        "total_users": total_users or 0,
        "total_downloads": total_downloads or 0,
        "total_revenue": round(float(total_revenue or 0), 2),
        "active_subscriptions": active_subs or 0,
        "pro_users": subs_by_tier_map.get("pro", 0),
        "unlimited_users": subs_by_tier_map.get("unlimited", 0),
        "api_keys_count": 0,
        "completed_referrals": 0,
    }


@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).order_by(User.created_at.desc())

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_filter)) |
            (User.username.ilike(search_filter))
        )

    result = await db.execute(query.offset(skip).limit(limit))
    users = result.scalars().all()

    total = await db.scalar(
        select(func.count(User.id))
    )

    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "is_verified": u.is_verified,
                "tier": u.role,
                "daily_downloads": u.downloads_today,
                "total_downloads": u.total_downloads or 0,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
        "total": total or 0,
        "skip": skip,
        "limit": limit,
    }


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
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    await db.commit()
    audit_logger.admin_action(str(admin.id), "toggle_ban", f"user:{user_id}", {"is_active": user.is_active})
    return {"id": str(user.id), "is_active": user.is_active}


@router.post("/subscriptions/{sub_id}/cancel", dependencies=[Depends(require_admin)])
async def cancel_subscription_admin(
    sub_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(Subscription).where(Subscription.id == sub_id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    sub.status = SubscriptionStatus.CANCELED
    sub.canceled_at = datetime.utcnow()
    await db.commit()
    audit_logger.admin_action(str(admin.id), "cancel_subscription", f"sub:{sub_id}")
    return {"id": str(sub.id), "status": sub.status.value if hasattr(sub.status, 'value') else sub.status}


class FeatureFlagCreate(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    enabled: bool = False


class FeatureFlagUpdate(BaseModel):
    enabled: bool


@router.get("/feature-flags", dependencies=[Depends(require_admin)])
async def list_feature_flags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FeatureFlag).order_by(FeatureFlag.key))
    flags = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "key": f.key,
            "name": f.name,
            "description": f.description,
            "enabled": f.enabled,
            "updated_at": f.updated_at.isoformat(),
        }
        for f in flags
    ]


@router.post("/feature-flags", dependencies=[Depends(require_admin)])
async def create_feature_flag(
    data: FeatureFlagCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    existing = await db.execute(select(FeatureFlag).where(FeatureFlag.key == data.key))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Feature flag already exists")

    flag = FeatureFlag(
        key=data.key,
        name=data.name,
        description=data.description,
        enabled=data.enabled,
    )
    db.add(flag)
    await db.commit()
    audit_logger.admin_action(str(admin.id), "create_feature_flag", f"flag:{data.key}")
    return {"id": str(flag.id), "key": flag.key, "enabled": flag.enabled}


@router.patch("/feature-flags/{flag_id}", dependencies=[Depends(require_admin)])
async def update_feature_flag(
    flag_id: str,
    data: FeatureFlagUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    flag.enabled = data.enabled
    await db.commit()
    audit_logger.admin_action(str(admin.id), "toggle_feature_flag", f"flag:{flag.key}", {"enabled": data.enabled})
    return {"id": str(flag.id), "key": flag.key, "enabled": flag.enabled}


@router.get("/health/system", dependencies=[Depends(require_admin)])
async def system_health():
    checks = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        s = get_settings()
        r = aioredis.from_url(s.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.close()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"

    try:
        from app.config import get_settings
        s = get_settings()
        checks["environment"] = s.environment
        checks["version"] = "3.0.0"
    except Exception as e:
        checks["config"] = f"error: {e}"

    return checks


@router.get("/queue-status", dependencies=[Depends(require_admin)])
async def queue_status(
    db: AsyncSession = Depends(get_db),
):
    from app.models.download import DownloadTask

    try:
        total = await db.scalar(select(func.count(DownloadTask.id)))
        pending = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == "pending")
        )
        processing = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == "processing")
        )
        completed = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == "completed")
        )
        failed = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == "failed")
        )
        recent = await db.execute(
            select(DownloadTask).order_by(DownloadTask.created_at.desc()).limit(10)
        )
        return {
            "total": total or 0,
            "pending": pending or 0,
            "processing": processing or 0,
            "completed": completed or 0,
            "failed": failed or 0,
            "recent": [
                {
                    "id": str(t.id),
                    "url": t.url[:60] + "..." if len(t.url) > 60 else t.url,
                    "status": t.status,
                    "created_at": t.created_at.isoformat(),
                }
                for t in recent.scalars().all()
            ],
        }
    except Exception:
        return {
            "total": 0, "pending": 0, "processing": 0, "completed": 0, "failed": 0, "recent": [],
            "error": "Queue table not available",
        }


@router.get("/audit-logs", dependencies=[Depends(require_admin)])
async def search_audit_logs(
    query: str = Query("", max_length=200),
    action: str = Query("", max_length=50),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    from app.models.audit import AuditLog

    try:
        q = select(AuditLog).order_by(AuditLog.created_at.desc())

        if action:
            q = q.where(AuditLog.action == action.upper())
        if query:
            like = f"%{query}%"
            q = q.where(
                (AuditLog.details.ilike(like)) |
                (AuditLog.resource.ilike(like)) |
                (AuditLog.email.ilike(like))
            )

        total = await db.scalar(select(func.count()).select_from(q.subquery()))
        result = await db.execute(q.offset(skip).limit(limit))
        logs = result.scalars().all()

        return {
            "logs": [
                {
                    "id": str(l.id),
                    "action": l.action,
                    "user_id": str(l.user_id) if l.user_id else None,
                    "email": l.email,
                    "ip_address": l.ip_address,
                    "resource": l.resource,
                    "details": l.details,
                    "status": l.status,
                    "created_at": l.created_at.isoformat(),
                }
                for l in logs
            ],
            "total": total or 0,
        }
    except Exception:
        return {"logs": [], "total": 0, "error": "Audit log table not available"}


@router.get("/system-alerts", dependencies=[Depends(require_admin)])
async def system_alerts(
    db: AsyncSession = Depends(get_db),
):
    alerts = []

    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    try:
        from app.models.download import DownloadTask
        failed_recent = await db.scalar(
            select(func.count(DownloadTask.id)).where(
                DownloadTask.status == "failed",
                DownloadTask.created_at >= hour_ago,
            )
        )
        if failed_recent and failed_recent > 10:
            alerts.append({
                "severity": "warning",
                "message": f"{failed_recent} downloads failed in the last hour",
                "metric": "failed_downloads",
            })
    except Exception:
        pass

    try:
        from app.models.user import User
        new_users = await db.scalar(
            select(func.count(User.id)).where(User.created_at >= day_ago)
        )
        alerts.append({
            "severity": "info",
            "message": f"{new_users or 0} new users in the last 24 hours",
            "metric": "new_users",
        })
    except Exception:
        pass

    try:
        from app.models.monetization import Payment, PaymentStatus
        failed_payments = await db.scalar(
            select(func.count(Payment.id)).where(
                Payment.status == PaymentStatus.FAILED,
                Payment.created_at >= day_ago,
            )
        )
        if failed_payments and failed_payments > 0:
            alerts.append({
                "severity": "warning",
                "message": f"{failed_payments} failed payments in the last 24 hours",
                "metric": "failed_payments",
            })
    except Exception:
        pass

    return {"alerts": alerts, "generated_at": now.isoformat()}


@router.get("/download-analytics", dependencies=[Depends(require_admin)])
async def download_analytics(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)

    total = await db.scalar(
        select(func.count(DownloadHistory.id)).where(DownloadHistory.created_at >= since)
    )
    by_platform = await db.execute(
        select(DownloadHistory.platform, func.count(DownloadHistory.id))
        .where(DownloadHistory.created_at >= since)
        .group_by(DownloadHistory.platform)
        .order_by(func.count(DownloadHistory.id).desc())
    )
    by_format = await db.execute(
        select(DownloadHistory.format, func.count(DownloadHistory.id))
        .where(DownloadHistory.created_at >= since)
        .group_by(DownloadHistory.format)
        .order_by(func.count(DownloadHistory.id).desc())
    )
    daily_counts = await db.execute(
        select(
            func.date_trunc("day", DownloadHistory.created_at).label("day"),
            func.count(DownloadHistory.id),
        )
        .where(DownloadHistory.created_at >= since)
        .group_by(text("day"))
        .order_by(text("day"))
    )

    return {
        "total": total or 0,
        "days": days,
        "by_platform": {row[0]: row[1] for row in by_platform},
        "by_format": {row[0]: row[1] for row in by_format},
        "daily": [{"date": str(row[0]), "count": row[1]} for row in daily_counts],
    }


class AffiliateCreate(BaseModel):
    platform: str
    name: str
    url: str
    description: str | None = None
    commission_rate: str | None = None


class AffiliateUpdate(BaseModel):
    platform: str | None = None
    name: str | None = None
    url: str | None = None
    description: str | None = None
    commission_rate: str | None = None
    is_active: bool | None = None


@router.get("/affiliates", dependencies=[Depends(require_admin)])
async def list_affiliates(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    from app.models.monetization import AffiliateLink
    result = await db.execute(
        select(AffiliateLink).order_by(AffiliateLink.created_at.desc()).offset(skip).limit(limit)
    )
    links = result.scalars().all()
    total = await db.scalar(select(func.count(AffiliateLink.id)))
    return {
        "affiliates": [
            {
                "id": str(l.id),
                "platform": l.platform,
                "name": l.name,
                "url": l.url,
                "description": l.description,
                "commission_rate": l.commission_rate,
                "is_active": l.is_active,
                "clicks": l.clicks or 0,
                "created_at": l.created_at.isoformat(),
            }
            for l in links
        ],
        "total": total or 0,
    }


@router.post("/affiliates", dependencies=[Depends(require_admin)])
async def create_affiliate(
    data: AffiliateCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.monetization import AffiliateLink
    link = AffiliateLink(
        platform=data.platform,
        name=data.name,
        url=data.url,
        description=data.description,
        commission_rate=data.commission_rate,
    )
    db.add(link)
    await db.commit()
    audit_logger.admin_action(str(admin.id), "create_affiliate", f"affiliate:{data.name}")
    return {"id": str(link.id), "status": "created"}


@router.patch("/affiliates/{link_id}", dependencies=[Depends(require_admin)])
async def update_affiliate(
    link_id: str,
    data: AffiliateUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.monetization import AffiliateLink
    result = await db.execute(select(AffiliateLink).where(AffiliateLink.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Affiliate link not found")
    if data.platform is not None:
        link.platform = data.platform
    if data.name is not None:
        link.name = data.name
    if data.url is not None:
        link.url = data.url
    if data.description is not None:
        link.description = data.description
    if data.commission_rate is not None:
        link.commission_rate = data.commission_rate
    if data.is_active is not None:
        link.is_active = data.is_active
    await db.commit()
    audit_logger.admin_action(str(admin.id), "update_affiliate", f"affiliate:{link_id}")
    return {"id": str(link.id), "status": "updated"}


@router.delete("/affiliates/{link_id}", dependencies=[Depends(require_admin)])
async def delete_affiliate(
    link_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.monetization import AffiliateLink
    result = await db.execute(select(AffiliateLink).where(AffiliateLink.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Affiliate link not found")
    await db.delete(link)
    await db.commit()
    audit_logger.admin_action(str(admin.id), "delete_affiliate", f"affiliate:{link_id}")
    return {"status": "deleted"}


@router.get("/executive-analytics", dependencies=[Depends(require_admin)])
async def executive_analytics(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    period_start = now - timedelta(days=days)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = await db.scalar(select(func.count(User.id))) or 0
    users_today = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    ) or 0
    users_this_month = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at >= month_ago)
    ) or 0
    returning = await db.scalar(
        select(func.count(func.distinct(DownloadHistory.user_id)))
        .where(DownloadHistory.created_at >= week_ago)
    ) or 0

    downloads_total = await db.scalar(select(func.count(DownloadHistory.id))) or 0
    downloads_today = await db.scalar(
        select(func.count()).select_from(DownloadHistory).where(DownloadHistory.created_at >= today_start)
    ) or 0
    downloads_this_month = await db.scalar(
        select(func.count()).select_from(DownloadHistory).where(DownloadHistory.created_at >= month_ago)
    ) or 0

    queue_pending = 0
    queue_processing = 0
    queue_failed = 0
    try:
        from app.models.download import DownloadTask
        queue_pending = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == "pending")
        ) or 0
        queue_processing = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == "processing")
        ) or 0
        queue_failed = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == "failed")
        ) or 0
    except Exception:
        pass

    revenue_total = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatus.COMPLETED)
    ) or 0
    revenue_mtd = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.created_at >= month_ago,
        )
    ) or 0
    premium_users = await db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.status == SubscriptionStatus.ACTIVE)
    ) or 0
    conversions = await db.scalar(
        select(func.count()).select_from(Subscription).where(
            Subscription.created_at >= month_ago,
            Subscription.status == SubscriptionStatus.ACTIVE,
        )
    ) or 0

    referral_total = await db.scalar(
        select(func.count()).select_from(Referral).where(Referral.status == "completed")
    ) or 0
    referral_this_month = await db.scalar(
        select(func.count()).select_from(Referral).where(
            Referral.status == "completed",
            Referral.completed_at >= month_ago,
        )
    ) or 0

    api_key_usage = await db.scalar(
        select(func.coalesce(func.sum(ApiKey.requests_count), 0))
    ) or 0

    by_platform = await db.execute(
        select(DownloadHistory.platform, func.count(DownloadHistory.id))
        .where(DownloadHistory.created_at >= period_start)
        .group_by(DownloadHistory.platform)
        .order_by(func.count(DownloadHistory.id).desc())
        .limit(10)
    )

    return {
        "users": {
            "total": total_users,
            "today": users_today,
            "this_month": users_this_month,
            "returning_weekly": returning,
        },
        "downloads": {
            "total": downloads_total,
            "today": downloads_today,
            "this_month": downloads_this_month,
            "by_platform": {row[0]: row[1] for row in by_platform},
        },
        "queue": {
            "pending": queue_pending,
            "processing": queue_processing,
            "failed": queue_failed,
        },
        "revenue": {
            "total_usd": round(float(revenue_total), 2),
            "mtd_usd": round(float(revenue_mtd), 2),
        },
        "premium": {
            "active_subscriptions": premium_users,
            "monthly_conversions": conversions,
        },
        "referrals": {
            "total": referral_total,
            "this_month": referral_this_month,
        },
        "api": {
            "total_requests": api_key_usage,
        },
        "period_days": days,
    }


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=403, detail="Cannot delete admin users")

    # Delete child records
    await db.execute(
        DownloadHistory.__table__.delete().where(DownloadHistory.user_id == user.id)
    )
    from app.models.monetization import Subscription, Payment, ApiKey, Referral
    await db.execute(
        Subscription.__table__.delete().where(Subscription.user_id == user.id)
    )
    await db.execute(
        Payment.__table__.delete().where(Payment.user_id == user.id)
    )
    await db.execute(
        ApiKey.__table__.delete().where(ApiKey.user_id == user.id)
    )
    await db.execute(
        Referral.__table__.delete().where(
            (Referral.referrer_id == user.id) | (Referral.referred_id == user.id)
        )
    )
    await db.delete(user)
    await db.commit()
    audit_logger.admin_action(str(admin.id), "delete_user", f"user:{user_id}")
    return {"status": "deleted"}
