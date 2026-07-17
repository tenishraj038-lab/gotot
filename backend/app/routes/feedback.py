from fastapi import APIRouter, Depends, Request, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.database import get_db
from app.models.user import User
from app.routes.payments import get_current_user
import logging

logger = logging.getLogger("gotot.feedback")

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    type: str
    title: str
    description: str
    email: str | None = None


class BugReport(BaseModel):
    title: str
    description: str
    steps_to_reproduce: str | None = None
    browser: str | None = None
    os: str | None = None
    screenshot_url: str | None = None


class FeatureRequest(BaseModel):
    title: str
    description: str
    use_case: str | None = None
    priority: str = "medium"


class SurveyResponse(BaseModel):
    rating: int
    category: str
    comment: str | None = None


@router.post("/submit")
async def submit_feedback(
    data: FeedbackCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    ip = request.client.host if request.client else "unknown"
    logger.info(f"Feedback from {user.email if user else 'anonymous'} ({ip}): {data.type} - {data.title}")
    return {"status": "received", "message": "Thank you for your feedback!"}


@router.post("/bug-report")
async def report_bug(
    data: BugReport,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    ip = request.client.host if request.client else "unknown"
    logger.info(f"Bug report from {user.email if user else 'anonymous'} ({ip}): {data.title}")
    return {"status": "received", "message": "Bug report submitted. We'll investigate."}


@router.post("/feature-request")
async def request_feature(
    data: FeatureRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    ip = request.client.host if request.client else "unknown"
    logger.info(f"Feature request from {user.email if user else 'anonymous'} ({ip}): {data.title}")
    return {"status": "received", "message": "Feature request recorded. We review all suggestions."}


@router.post("/survey")
async def submit_survey(
    data: SurveyResponse,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    if data.rating < 1 or data.rating > 5:
        return {"status": "error", "message": "Rating must be between 1 and 5"}
    ip = request.client.host if request.client else "unknown"
    logger.info(f"Survey from {user.email if user else 'anonymous'} ({ip}): {data.category} - {data.rating}/5")
    return {"status": "received", "message": "Thank you for your feedback!"}


@router.get("/stats")
async def feedback_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {
        "status": "operational",
        "feedback_enabled": True,
        "bug_report_enabled": True,
        "feature_requests_enabled": True,
        "survey_enabled": True,
        "channels": ["email", "in-app", "contact-form"],
    }
