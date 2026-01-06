"""Add sent_notifications table

Revision ID: 14890e48fea4
Revises: 9cfd9a9708b2
Create Date: 2026-01-06 13:16:18.748961

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "14890e48fea4"
down_revision: Union[str, None] = "9cfd9a9708b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sent_notifications table
    op.create_table(
        "sent_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("deadline_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["deadline_id"],
            ["deadlines.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("sent_notifications")
