"""Add notification_settings table

Revision ID: 9cfd9a9708b2
Revises: 4af7324cac5f
Create Date: 2026-01-06 11:16:33.140087

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9cfd9a9708b2"
down_revision: Union[str, None] = "4af7324cac5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notification_settings table
    op.create_table(
        "notification_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("notify_on_due", sa.Boolean(), nullable=False),
        sa.Column("notify_1_hour", sa.Boolean(), nullable=False),
        sa.Column("notify_3_hours", sa.Boolean(), nullable=False),
        sa.Column("notify_1_day", sa.Boolean(), nullable=False),
        sa.Column("notify_3_days", sa.Boolean(), nullable=False),
        sa.Column("notify_1_week", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("notification_settings")
