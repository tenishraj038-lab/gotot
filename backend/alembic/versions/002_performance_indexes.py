"""Add performance indexes and feature_flags table

Revision ID: 002
Revises: 001
Create Date: 2025-07-17 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for sql in [
        "CREATE INDEX IF NOT EXISTS idx_download_history_created_at ON download_history USING brin(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_download_history_platform_created ON download_history(platform, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_download_history_user_status ON download_history(user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_download_history_url_trgm ON download_history USING gin(url gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS idx_users_role_created ON users(role, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_users_total_downloads ON users(total_downloads)",
        "CREATE INDEX IF NOT EXISTS idx_payments_status_created ON payments(status, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_payments_user_status ON payments(user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_status_tier ON subscriptions(status, tier)",
        "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    ]:
        try:
            op.execute(sql)
        except Exception:
            pass
    try:
        op.execute("""
            CREATE TABLE IF NOT EXISTS feature_flags (
                id UUID DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
                key VARCHAR(100) NOT NULL UNIQUE,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                enabled BOOLEAN DEFAULT FALSE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW() NOT NULL
            )
        """)
    except Exception:
        pass


def downgrade() -> None:
    op.drop_table("feature_flags")
    op.drop_index("idx_subscriptions_status_tier")
    op.drop_index("idx_payments_user_status")
    op.drop_index("idx_payments_status_created")
    op.drop_index("idx_users_total_downloads")
    op.drop_index("idx_users_role_created")
    op.drop_index("idx_download_history_url_trgm")
    op.drop_index("idx_download_history_user_status")
    op.drop_index("idx_download_history_platform_created")
    op.drop_index("idx_download_history_created_at")
