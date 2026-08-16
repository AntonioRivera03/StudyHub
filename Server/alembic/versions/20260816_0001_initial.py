"""Create Phase 1 tables.

Revision ID: 20260816_0001
Revises:
Create Date: 2026-08-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260816_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "pomodoro_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("focus_minutes", sa.Integer(), nullable=False),
        sa.Column("short_break_minutes", sa.Integer(), nullable=False),
        sa.Column("long_break_minutes", sa.Integer(), nullable=False),
        sa.Column("long_break_every", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("focus_minutes BETWEEN 1 AND 180"),
        sa.CheckConstraint("short_break_minutes BETWEEN 1 AND 60"),
        sa.CheckConstraint("long_break_minutes BETWEEN 1 AND 120"),
        sa.CheckConstraint("long_break_every BETWEEN 1 AND 12"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "timers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("phase", sa.String(length=20), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("category_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("remaining_seconds", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("expected_end_at", sa.DateTime(), nullable=False),
        sa.Column("paused_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("duration_seconds > 0"),
        sa.CheckConstraint("phase IN ('focus', 'short_break', 'long_break')"),
        sa.CheckConstraint("remaining_seconds >= 0"),
        sa.CheckConstraint("state IN ('running', 'paused', 'completed', 'cancelled')"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_timers_one_active",
        "timers",
        [sa.text("1")],
        unique=True,
        sqlite_where=sa.text("state IN ('running', 'paused')"),
    )
    op.create_table(
        "study_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("category_id", sa.String(length=36), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("timer_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("ended_at IS NULL OR ended_at > started_at"),
        sa.CheckConstraint("duration_seconds >= 0"),
        sa.CheckConstraint("source IN ('manual', 'pomodoro')"),
        sa.CheckConstraint("status IN ('active', 'completed', 'cancelled')"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["timer_id"], ["timers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("timer_id"),
    )


def downgrade() -> None:
    op.drop_table("study_sessions")
    op.drop_index("uq_timers_one_active", table_name="timers")
    op.drop_table("timers")
    op.drop_table("pomodoro_settings")
    op.drop_table("categories")
