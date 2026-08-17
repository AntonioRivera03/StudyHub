"""Add StudyFlow session logging.

Revision ID: 20260816_0002
Revises: 20260816_0001
Create Date: 2026-08-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260816_0002"
down_revision: str | None = "20260816_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "study_sessions_new",
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
        sa.CheckConstraint("source IN ('manual', 'pomodoro', 'study_flow')"),
        sa.CheckConstraint("status IN ('active', 'completed', 'cancelled')"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["timer_id"], ["timers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("timer_id"),
    )
    op.execute(
        """
        INSERT INTO study_sessions_new (
            id, title, category_id, started_at, ended_at, duration_seconds, notes,
            source, status, timer_id, created_at, updated_at, deleted_at
        )
        SELECT
            id, title, category_id, started_at, ended_at, duration_seconds, notes,
            source, status, timer_id, created_at, updated_at, deleted_at
        FROM study_sessions
        """
    )
    op.drop_table("study_sessions")
    op.rename_table("study_sessions_new", "study_sessions")

    op.execute(
        """
        ALTER TABLE timers
        ADD COLUMN study_flow_session_id VARCHAR(36)
        REFERENCES study_sessions(id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        ALTER TABLE timers
        ADD COLUMN study_flow_segment_index INTEGER
        CHECK (study_flow_segment_index IS NULL OR study_flow_segment_index BETWEEN 0 AND 5)
        """
    )
    op.execute(
        """
        ALTER TABLE timers
        ADD COLUMN study_flow_confirmed_at DATETIME
        CHECK (study_flow_confirmed_at IS NULL OR study_flow_session_id IS NOT NULL)
        """
    )
    op.create_index(
        "ix_timers_study_flow_session_id",
        "timers",
        ["study_flow_session_id"],
    )
    op.create_index(
        "uq_timers_study_flow_segment_success",
        "timers",
        ["study_flow_session_id", "study_flow_segment_index"],
        unique=True,
        sqlite_where=sa.text("study_flow_session_id IS NOT NULL AND state != 'cancelled'"),
    )
    op.create_index(
        "uq_study_sessions_one_active_study_flow",
        "study_sessions",
        [sa.text("1")],
        unique=True,
        sqlite_where=sa.text("source = 'study_flow' AND status = 'active' AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    connection = op.get_bind()
    active_study_flows = connection.scalar(
        sa.text("SELECT COUNT(*) FROM study_sessions WHERE source = 'study_flow'")
    )
    if active_study_flows:
        raise RuntimeError("StudyFlow sessions must be removed before downgrading")

    op.drop_index("uq_study_sessions_one_active_study_flow", table_name="study_sessions")
    op.drop_index("uq_timers_study_flow_segment_success", table_name="timers")
    op.drop_index("ix_timers_study_flow_session_id", table_name="timers")
    op.drop_column("timers", "study_flow_confirmed_at")
    op.drop_column("timers", "study_flow_segment_index")
    op.drop_column("timers", "study_flow_session_id")

    op.create_table(
        "study_sessions_old",
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
    op.execute(
        """
        INSERT INTO study_sessions_old (
            id, title, category_id, started_at, ended_at, duration_seconds, notes,
            source, status, timer_id, created_at, updated_at, deleted_at
        )
        SELECT
            id, title, category_id, started_at, ended_at, duration_seconds, notes,
            source, status, timer_id, created_at, updated_at, deleted_at
        FROM study_sessions
        """
    )
    op.drop_table("study_sessions")
    op.rename_table("study_sessions_old", "study_sessions")
