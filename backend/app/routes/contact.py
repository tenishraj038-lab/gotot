from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db

router = APIRouter(tags=["contact"])


class ContactRequest(BaseModel):
    name: str
    email: str
    message: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()[:100]

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v.lower().strip()

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Message must be at least 10 characters")
        return v.strip()[:2000]


@router.post("/contact")
async def submit_contact(data: ContactRequest, request: Request):
    import logging
    logger = logging.getLogger("gotot.contact")
    logger.info(f"Contact form submission from {data.email}: {data.message[:50]}...")
    from app.services.email_service import send_contact_notification
    sent = await send_contact_notification(data.name, data.email, data.message)
    if sent:
        logger.info("Contact notification emailed to admin")
    return {
        "status": "success",
        "message": "Thank you for your message. We'll get back to you within 24 hours.",
    }
