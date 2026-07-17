import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.services.email_service import (
    send_welcome_email,
    send_premium_purchase_email,
    send_security_alert_email,
    send_referral_reward_email,
)

logger = logging.getLogger("gotot.notifications")


async def create_notification(
    db: AsyncSession,
    user_id: str,
    notif_type: NotificationType,
    title: str,
    message: str,
    data: dict | None = None,
    send_email: bool = True,
    send_push: bool = False,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message,
        data=data,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    if send_email:
        await _send_email_for_notification(db, user_id, notif_type, data or {})
        notification.is_email_sent = True
        await db.commit()

    return notification


async def _send_email_for_notification(db: AsyncSession, user_id: str, notif_type: NotificationType, data: dict):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.email:
        return

    prefs = user.email_preferences or {}
    if not prefs.get("security_alerts", True) and notif_type in (NotificationType.SECURITY_ALERT,):
        return
    if not prefs.get("product_updates", True) and notif_type in (
        NotificationType.PLAN_UPGRADE, NotificationType.ADMIN_ANNOUNCEMENT
    ):
        return
    if not prefs.get("marketing", True) and notif_type in (
        NotificationType.REFERRAL_REWARD, NotificationType.WELCOME
    ):
        return

    if notif_type == NotificationType.WELCOME:
        await send_welcome_email(user.email, user.username)
    elif notif_type == NotificationType.PLAN_UPGRADE:
        await send_premium_purchase_email(
            user.email, user.username,
            data.get("plan", "Pro"),
            data.get("amount", "$4.99"),
        )
    elif notif_type == NotificationType.REFERRAL_REWARD:
        await send_referral_reward_email(
            user.email, user.username,
            data.get("bonus", 3),
        )
    elif notif_type == NotificationType.SECURITY_ALERT:
        await send_security_alert_email(
            user.email, user.username,
            data.get("alert_type", "Unknown"),
            data.get("details", ""),
        )


async def get_notifications(
    db: AsyncSession,
    user_id: str,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
):
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()

    total = await db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    )
    unread = await db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read == False
        )
    )

    return {
        "notifications": [
            {
                "id": str(n.id),
                "type": n.type.value,
                "title": n.title,
                "message": n.message,
                "data": n.data,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
        "total": total or 0,
        "unread": unread or 0,
    }


async def mark_as_read(db: AsyncSession, user_id: str, notification_id: str):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()


async def mark_all_as_read(db: AsyncSession, user_id: str):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()


async def get_unread_count(db: AsyncSession, user_id: str) -> int:
    result = await db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read == False
        )
    )
    return result or 0
