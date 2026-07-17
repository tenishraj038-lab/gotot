from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.models.user import User
from app.routes.payments import get_current_user
from app.services.notification_service import (
    get_notifications,
    mark_as_read,
    mark_all_as_read,
    get_unread_count,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_notifications(db, str(user.id), skip, limit, unread_only)


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    count = await get_unread_count(db, str(user.id))
    return {"unread": count}


@router.post("/{notification_id}/read")
async def read_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await mark_as_read(db, str(user.id), notification_id)
    return {"status": "ok"}


@router.post("/read-all")
async def read_all_notifications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await mark_all_as_read(db, str(user.id))
    return {"status": "ok"}
