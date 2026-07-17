from fastapi import APIRouter

router = APIRouter(tags=["announcements"])

ANNOUNCEMENTS = [
    {
        "id": "launch2026",
        "message": "GoTot v3 is live! Download up to 4K videos. Upgrade to Pro for unlimited access.",
        "type": "info",
    }
]


@router.get("/announcements/active")
async def get_active_announcement():
    return ANNOUNCEMENTS[0] if ANNOUNCEMENTS else None
