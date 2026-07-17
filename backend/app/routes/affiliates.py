from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import get_db
from app.models.monetization import AffiliateLink

router = APIRouter(prefix="/affiliates", tags=["affiliates"])


@router.get("/links")
async def get_affiliate_links(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AffiliateLink).where(AffiliateLink.is_active == True)
    )
    links = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "platform": l.platform,
            "name": l.name,
            "url": l.url,
            "description": l.description,
            "commission_rate": l.commission_rate,
        }
        for l in links
    ]


@router.post("/{link_id}/click")
async def record_affiliate_click(
    link_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AffiliateLink).where(AffiliateLink.id == link_id))
    link = result.scalar_one_or_none()
    if link:
        link.clicks += 1
        await db.commit()
    return {"status": "recorded"}
