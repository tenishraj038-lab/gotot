import uuid
from datetime import datetime
import json
from sqlalchemy import String, DateTime, Boolean, Text, Integer, Enum as SAEnum, BigInteger, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID


class JSONText(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json.dumps(value) if value else "{}"

    def process_result_value(self, value, dialect):
        return json.loads(value) if value else {}
from app.models.database import Base
from app.models.monetization import SubscriptionTier
import enum


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[SubscriptionTier] = mapped_column(SAEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_download_limit: Mapped[int] = mapped_column(Integer, default=5)
    downloads_today: Mapped[int] = mapped_column(Integer, default=0)
    download_credits: Mapped[int] = mapped_column(Integer, default=0)
    total_downloads: Mapped[int] = mapped_column(BigInteger, default=0)
    last_download_reset: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    refresh_token_version: Mapped[int] = mapped_column(Integer, default=0)
    email_preferences: Mapped[dict] = mapped_column(JSONText, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DownloadHistory(Base):
    __tablename__ = "download_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
