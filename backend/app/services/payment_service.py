import razorpay
import json
import hashlib
import hmac
import logging
from typing import Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.user import User
from app.models.monetization import (
    Subscription, SubscriptionTier, SubscriptionStatus,
    Payment, PaymentStatus,
)

settings = get_settings()
logger = logging.getLogger("gotot.payment")

client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
razorpay_webhook_secret = settings.razorpay_webhook_secret

PLANS = {
    SubscriptionTier.PRO: {
        "plan_id": settings.razorpay_pro_plan_id,
        "monthly_price": 4.99,
        "amount_in_cents": 499,
        "daily_downloads": 100,
        "max_quality": "4k",
        "features": {
            "batch_download": True,
            "mp3_conversion": True,
            "api_access": True,
            "no_ads": True,
            "concurrent_downloads": 3,
        },
    },
    SubscriptionTier.UNLIMITED: {
        "plan_id": settings.razorpay_unlimited_plan_id,
        "monthly_price": 9.99,
        "amount_in_cents": 999,
        "daily_downloads": 1000,
        "max_quality": "4k",
        "features": {
            "batch_download": True,
            "mp3_conversion": True,
            "api_access": True,
            "no_ads": True,
            "concurrent_downloads": 10,
            "priority_support": True,
        },
    },
}

PAY_PER_DOWNLOAD_CENTS = 50


def get_plan(tier: SubscriptionTier) -> Optional[dict]:
    return PLANS.get(tier)


def get_max_daily_downloads(tier: SubscriptionTier) -> int:
    plan = PLANS.get(tier)
    if plan:
        return plan["daily_downloads"]
    return 5


def has_feature(tier: SubscriptionTier, feature: str) -> bool:
    if tier == SubscriptionTier.UNLIMITED:
        return True
    plan = PLANS.get(tier)
    if plan:
        return plan["features"].get(feature, False)
    return False


def _cents_for_currency(cents_usd: int) -> int:
    if settings.currency == "INR":
        return cents_usd * 100
    return cents_usd


def _divisor() -> int:
    return 100


async def create_subscription_checkout(user: User, tier: SubscriptionTier) -> Optional[str]:
    try:
        plan = PLANS.get(tier)
        if not plan:
            logger.error(f"No plan configured for tier {tier}")
            return None

        plan_id = plan["plan_id"]
        if not plan_id:
            logger.error(f"No Razorpay plan ID for tier {tier}")
            return None

        subscription_data = {
            "plan_id": plan_id,
            "customer_notify": 1,
            "total_count": 12,
            "quantity": 1,
            "notes": {
                "user_id": str(user.id),
                "tier": tier.value,
            },
        }
        sub = client.subscription.create(subscription_data)
        short_url = sub.get("short_url")
        if short_url:
            return short_url

        logger.error(f"No short_url in Razorpay subscription response: {sub}")
        return None
    except Exception as e:
        logger.error(f"Failed to create Razorpay subscription: {e}")
        return None


async def create_pay_per_download_checkout(user: Optional[User], email: str = "") -> Optional[str]:
    try:
        amount = _cents_for_currency(PAY_PER_DOWNLOAD_CENTS)
        customer_email = email or (user.email if user else "")
        user_id = str(user.id) if user else "anonymous"

        link_data = {
            "amount": amount,
            "currency": settings.currency,
            "description": "Single Video Download - GoTot",
            "customer": {},
            "notify": {"sms": False, "email": bool(customer_email)},
            "callback_url": f"{settings.frontend_url}/dashboard?payment=success",
            "callback_method": "get",
            "notes": {
                "user_id": user_id,
                "type": "pay_per_download",
            },
        }

        if customer_email:
            link_data["customer"]["email"] = customer_email

        payment_link = client.payment_link.create(link_data)
        short_url = payment_link.get("short_url")
        if short_url:
            return short_url

        logger.error(f"No short_url in Razorpay payment link response: {payment_link}")
        return None
    except Exception as e:
        logger.error(f"Failed to create Razorpay payment link: {e}")
        return None


async def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    try:
        expected = hmac.new(
            razorpay_webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


async def handle_razorpay_webhook(payload: bytes, signature: str) -> dict:
    valid = await verify_webhook_signature(payload, signature)
    if not valid:
        logger.error("Invalid Razorpay webhook signature")
        return {"status": "error", "detail": "Invalid signature"}

    try:
        event = json.loads(payload)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid webhook payload: {e}")
        return {"status": "error", "detail": "Invalid payload"}

    event_type = event.get("event")
    handler = WEBHOOK_HANDLERS.get(event_type)
    if handler:
        return await handler(event.get("payload", {}))
    else:
        logger.info(f"Unhandled Razorpay event: {event_type}")
        return {"status": "ignored"}


async def handle_payment_captured(payload: dict) -> dict:
    payment = payload.get("payment", {}).get("entity", {})
    order_id = payment.get("order_id")
    payment_id = payment.get("id")
    amount = Decimal(str(payment.get("amount", 0))) / _divisor()
    currency = payment.get("currency", settings.currency)
    notes = payment.get("notes", {}) or {}
    user_id = notes.get("user_id")
    payment_type = notes.get("type", "one_time")

    payment_record = Payment(
        user_id=user_id if user_id and user_id != "anonymous" else None,
        razorpay_payment_id=payment_id,
        razorpay_order_id=order_id,
        amount=amount,
        currency=currency,
        status=PaymentStatus.COMPLETED,
        payment_type=payment_type,
        metadata_json=json.dumps(notes),
    )

    from app.models.database import async_session
    async with async_session() as db:
        db.add(payment_record)
        if user_id and user_id != "anonymous":
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user and payment_type == "pay_per_download":
                user.download_credits = (user.download_credits or 0) + 2
        await db.commit()
        logger.info(f"Payment captured: {payment_id} for {amount} {currency}")

    return {"status": "ok"}


async def handle_subscription_charged(payload: dict) -> dict:
    sub = payload.get("subscription", {}).get("entity", {})
    sub_id = sub.get("id")
    notes = sub.get("notes", {}) or {}
    user_id = notes.get("user_id")
    tier_str = notes.get("tier", "pro")
    tier = SubscriptionTier(tier_str)

    from app.models.database import async_session
    async with async_session() as db:
        result = await db.execute(
            select(Subscription).where(Subscription.razorpay_subscription_id == sub_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription and user_id:
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if user:
                user.role = tier
                subscription = Subscription(
                    user_id=user.id,
                    tier=tier,
                    status=SubscriptionStatus.ACTIVE,
                    razorpay_subscription_id=sub_id,
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=30),
                )
                db.add(subscription)
                await db.commit()
                logger.info(f"Subscription activated: {sub_id} for user {user_id}")

    return {"status": "ok"}


async def handle_subscription_cancelled(payload: dict) -> dict:
    sub = payload.get("subscription", {}).get("entity", {})
    sub_id = sub.get("id")

    from app.models.database import async_session
    async with async_session() as db:
        result = await db.execute(
            select(Subscription).where(Subscription.razorpay_subscription_id == sub_id)
        )
        subscription = result.scalar_one_or_none()
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.utcnow()
            user_result = await db.execute(select(User).where(User.id == subscription.user_id))
            user = user_result.scalar_one_or_none()
            if user:
                user.role = SubscriptionTier.FREE
            await db.commit()
            logger.info(f"Subscription cancelled: {sub_id}")

    return {"status": "ok"}


WEBHOOK_HANDLERS = {
    "payment.captured": handle_payment_captured,
    "subscription.charged": handle_subscription_charged,
    "subscription.cancelled": handle_subscription_cancelled,
}
