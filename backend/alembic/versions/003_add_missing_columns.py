"""Add missing columns to users table

Revision ID: 003
Revises: 002
Create Date: 2025-07-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for sql in [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_version INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_preferences TEXT",
        "CREATE TABLE IF NOT EXISTS download_tasks (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), url TEXT NOT NULL, format_id VARCHAR(50), status VARCHAR(20) DEFAULT 'pending' NOT NULL, progress INTEGER DEFAULT 0 NOT NULL, file_size BIGINT, error_message TEXT, created_at TIMESTAMP DEFAULT NOW() NOT NULL, updated_at TIMESTAMP DEFAULT NOW() NOT NULL)",
        "CREATE TABLE IF NOT EXISTS notifications (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, type VARCHAR(50) NOT NULL, title VARCHAR(200) NOT NULL, message TEXT, data TEXT, is_read BOOLEAN DEFAULT FALSE NOT NULL, created_at TIMESTAMP DEFAULT NOW() NOT NULL)",
        "CREATE TABLE IF NOT EXISTS audit_logs (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), email VARCHAR(255), action VARCHAR(50) NOT NULL, resource VARCHAR(255), details TEXT, ip_address VARCHAR(45), status VARCHAR(20), created_at TIMESTAMP DEFAULT NOW() NOT NULL)",
        "CREATE INDEX IF NOT EXISTS idx_download_tasks_user_id ON download_tasks(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at)",
    ]:
        try:
            op.execute(sql)
        except Exception:
            pass


def downgrade() -> None:
    op.drop_index("idx_audit_logs_created")
    op.drop_index("idx_audit_logs_action")
    op.drop_index("idx_notifications_user_read")
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("download_tasks")
    op.drop_column("users", "email_preferences")
    op.drop_column("users", "refresh_token_version")
