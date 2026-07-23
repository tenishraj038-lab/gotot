from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.models.database import get_db
from app.models.user import User
from app.models.monetization import (
    Subscription, SubscriptionTier, SubscriptionStatus,
    Payment, PaymentStatus,
)
from app.services.auth_service import decode_token, parse_user_id
from app.services.payment_service import (
    create_subscription_checkout, create_pay_per_download_checkout,
    handle_razorpay_webhook, PLANS,
)
from app.config import get_settings
import razorpay

router = APIRouter(tags=["monetization"])
settings = get_settings()


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == parse_user_id(payload.get("sub"))))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user


class CheckoutRequest(BaseModel):
    tier: SubscriptionTier


class PayPerDownloadRequest(BaseModel):
    email: str = ""


@router.post("/payment/create-subscription")
async def create_subscription_checkout_route(
    data: CheckoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    url = await create_subscription_checkout(user, data.tier)
    if not url:
        raise HTTPException(status_code=400, detail="Could not create checkout session")
    return {"checkout_url": url}


@router.post("/payment/pay-per-download")
async def pay_per_download_route(
    data: PayPerDownloadRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload:
                result = await db.execute(select(User).where(User.id == parse_user_id(payload.get("sub"))))
                user = result.scalar_one_or_none()
        except Exception:
            pass

    url = await create_pay_per_download_checkout(user, data.email)
    if not url:
        raise HTTPException(status_code=400, detail="Could not create checkout")
    return {"checkout_url": url}


@router.post("/payment/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
):
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Signature header")
    payload = await request.body()
    result = await handle_razorpay_webhook(payload, x_razorpay_signature)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("detail"))
    return {"received": True}


@router.get("/subscription/status")
async def get_subscription_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == SubscriptionStatus.ACTIVE,
        ).order_by(Subscription.created_at.desc()).limit(1)
    )
    sub = result.scalar_one_or_none()
    plan = PLANS.get(user.role, {})
    return {
        "tier": user.role,
        "is_active": sub is not None or user.role != SubscriptionTier.FREE.value,
        "current_period_end": sub.current_period_end.isoformat() if sub else None,
        "features": plan.get("features", {}),
        "daily_downloads": plan.get("daily_downloads", 5),
        "max_quality": plan.get("max_quality", "720p"),
    }


@router.post("/subscription/cancel")
async def cancel_subscription(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == SubscriptionStatus.ACTIVE,
        ).order_by(Subscription.created_at.desc()).limit(1)
    )
    sub = result.scalar_one_or_none()
    if not sub or not sub.razorpay_subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription found")

    try:
        client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
        client.subscription.cancel(sub.razorpay_subscription_id)
        sub.status = SubscriptionStatus.CANCELED
        sub.canceled_at = datetime.utcnow()
        await db.commit()
        return {"status": "canceled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment/history")
async def get_payment_history(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payment).where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
        .offset(skip).limit(limit)
    )
    payments = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status.value if isinstance(p.status, PaymentStatus) else p.status,
            "payment_type": p.payment_type,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
        }
        for p in payments
    ]
