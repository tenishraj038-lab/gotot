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
    # Performance indexes for download_history
    op.create_index("idx_download_history_created_at", "download_history", ["created_at"], postgresql_using="brin")
    op.create_index("idx_download_history_platform_created", "download_history", ["platform", "created_at"])
    op.create_index("idx_download_history_user_status", "download_history", ["user_id", "status"])
    op.create_index("idx_download_history_url_trgm", "download_history", ["url"], postgresql_using="gin",
                    postgresql_ops={"url": "gin_trgm_ops"})

    # Performance indexes for users
    op.create_index("idx_users_role_created", "users", ["role", "created_at"])
    op.create_index("idx_users_total_downloads", "users", ["total_downloads"])

    # Performance indexes for payments
    op.create_index("idx_payments_status_created", "payments", ["status", "created_at"])
    op.create_index("idx_payments_user_status", "payments", ["user_id", "status"])

    # Performance indexes for subscriptions
    op.create_index("idx_subscriptions_status_tier", "subscriptions", ["status", "tier"])

    # Feature flags table
    op.create_table(
        "feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(100), unique=True, index=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    # Enable pg_trgm extension for fuzzy search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


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
