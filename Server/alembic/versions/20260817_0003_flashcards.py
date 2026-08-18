"""Add Phase 2 flashcards and review history.

Revision ID: 20260817_0003
Revises: 20260816_0002
Create Date: 2026-08-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260817_0003"
down_revision: str | None = "20260816_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "flashcard_decks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("length(trim(name)) BETWEEN 1 AND 160"),
        sa.CheckConstraint("description IS NULL OR length(description) <= 2000"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flashcard_decks_created_id", "flashcard_decks", ["created_at", "id"])

    op.create_table(
        "flashcards",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("deck_id", sa.String(length=36), nullable=False),
        sa.Column("front_markdown", sa.Text(), nullable=False),
        sa.Column("back_markdown", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("ease_factor", sa.Float(), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("length(front_markdown) <= 20000 AND length(trim(front_markdown)) > 0"),
        sa.CheckConstraint("length(back_markdown) <= 20000 AND length(trim(back_markdown)) > 0"),
        sa.CheckConstraint("position >= 0"),
        sa.CheckConstraint("repetitions >= 0"),
        sa.CheckConstraint("interval_days >= 0"),
        sa.CheckConstraint("ease_factor >= 1.3"),
        sa.ForeignKeyConstraint(["deck_id"], ["flashcard_decks.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flashcards_deck_position_id", "flashcards", ["deck_id", "position", "id"])
    op.create_index(
        "ix_flashcards_deck_due",
        "flashcards",
        ["deck_id", "due_at", "position", "id"],
    )

    op.create_table(
        "review_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("deck_id", sa.String(length=36), nullable=False),
        sa.Column("category_id_snapshot", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('in_progress', 'completed', 'abandoned')"),
        sa.CheckConstraint("duration_seconds >= 0"),
        sa.CheckConstraint("ended_at IS NULL OR ended_at >= started_at"),
        sa.CheckConstraint(
            "(status = 'in_progress' AND ended_at IS NULL) OR "
            "(status IN ('completed', 'abandoned') AND ended_at IS NOT NULL)"
        ),
        sa.CheckConstraint("deleted_at IS NULL OR status != 'in_progress'"),
        sa.ForeignKeyConstraint(["category_id_snapshot"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deck_id"], ["flashcard_decks.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_sessions_started_id", "review_sessions", ["started_at", "id"])
    op.create_index(
        "uq_review_sessions_one_in_progress",
        "review_sessions",
        [sa.text("1")],
        unique=True,
        sqlite_where=sa.text("status = 'in_progress'"),
    )

    op.create_table(
        "review_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("command_id", sa.String(length=36), nullable=False),
        sa.Column("review_session_id", sa.String(length=36), nullable=False),
        sa.Column("card_id", sa.String(length=36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("rating", sa.String(length=10), nullable=False),
        sa.Column("quality", sa.Integer(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False),
        sa.Column("previous_repetitions", sa.Integer(), nullable=False),
        sa.Column("previous_interval_days", sa.Integer(), nullable=False),
        sa.Column("previous_ease_factor", sa.Float(), nullable=False),
        sa.Column("previous_due_at", sa.DateTime(), nullable=False),
        sa.Column("previous_last_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("new_repetitions", sa.Integer(), nullable=False),
        sa.Column("new_interval_days", sa.Integer(), nullable=False),
        sa.Column("new_ease_factor", sa.Float(), nullable=False),
        sa.Column("new_due_at", sa.DateTime(), nullable=False),
        sa.Column("new_last_reviewed_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("sequence > 0"),
        sa.CheckConstraint(
            "(rating = 'again' AND quality = 1) OR "
            "(rating = 'hard' AND quality = 3) OR "
            "(rating = 'good' AND quality = 4) OR "
            "(rating = 'easy' AND quality = 5)"
        ),
        sa.CheckConstraint("previous_repetitions >= 0 AND new_repetitions >= 0"),
        sa.CheckConstraint("previous_interval_days >= 0 AND new_interval_days >= 1"),
        sa.CheckConstraint("previous_ease_factor >= 1.3 AND new_ease_factor >= 1.3"),
        sa.CheckConstraint("new_due_at > reviewed_at"),
        sa.CheckConstraint("new_last_reviewed_at = reviewed_at"),
        sa.ForeignKeyConstraint(["card_id"], ["flashcards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["review_session_id"], ["review_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("command_id", name="uq_review_events_command_id"),
        sa.UniqueConstraint(
            "review_session_id", "sequence", name="uq_review_events_session_sequence"
        ),
        sa.UniqueConstraint("review_session_id", "card_id", name="uq_review_events_session_card"),
    )
    op.create_index("ix_review_events_session", "review_events", ["review_session_id"])


def downgrade() -> None:
    op.drop_index("ix_review_events_session", table_name="review_events")
    op.drop_table("review_events")
    op.drop_index("uq_review_sessions_one_in_progress", table_name="review_sessions")
    op.drop_index("ix_review_sessions_started_id", table_name="review_sessions")
    op.drop_table("review_sessions")
    op.drop_index("ix_flashcards_deck_due", table_name="flashcards")
    op.drop_index("ix_flashcards_deck_position_id", table_name="flashcards")
    op.drop_table("flashcards")
    op.drop_index("ix_flashcard_decks_created_id", table_name="flashcard_decks")
    op.drop_table("flashcard_decks")
