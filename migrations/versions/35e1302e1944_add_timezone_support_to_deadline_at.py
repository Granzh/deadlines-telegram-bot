"""Add timezone support to deadline_at

Revision ID: 35e1302e1944
Revises: 14890e48fea4
Create Date: 2026-01-06 14:09:06.138452

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "35e1302e1944"
down_revision: Union[str, None] = "14890e48fea4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    # Create new table with timezone support
    op.create_table(
        "deadlines_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data from old table
    op.execute(
        "INSERT INTO deadlines_new (id, user_id, title, deadline_at, created_at) SELECT id, user_id, title, deadline_at, created_at FROM deadlines"
    )

    # Drop old table and rename new one
    op.drop_table("deadlines")
    op.rename_table("deadlines_new", "deadlines")

    # Create index
    op.create_index(op.f("ix_deadlines_id"), "deadlines", ["id"], unique=False)


def downgrade() -> None:
    # Revert by recreating table without timezone support
    op.create_table(
        "deadlines_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("deadline_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data from current table
    op.execute(
        "INSERT INTO deadlines_old (id, user_id, title, deadline_at, created_at) SELECT id, user_id, title, deadline_at, created_at FROM deadlines"
    )

    # Drop current table and rename old one
    op.drop_table("deadlines")
    op.rename_table("deadlines_old", "deadlines")

    # Create index
    op.create_index(op.f("ix_deadlines_id"), "deadlines", ["id"], unique=False)
