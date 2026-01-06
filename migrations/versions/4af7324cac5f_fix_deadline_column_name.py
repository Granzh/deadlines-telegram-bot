"""Fix deadline column name

Revision ID: 4af7324cac5f
Revises: 001
Create Date: 2026-01-06 11:13:17.195233

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4af7324cac5f"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename deadline_date to deadline_at to match the model
    op.alter_column("deadlines", "deadline_date", new_column_name="deadline_at")


def downgrade() -> None:
    # Rename deadline_at back to deadline_date
    op.alter_column("deadlines", "deadline_at", new_column_name="deadline_date")
