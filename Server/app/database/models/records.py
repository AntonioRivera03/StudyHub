from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, UTCDateTime


class CategoryRecord(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    color: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class PomodoroSettingsRecord(Base):
    __tablename__ = "pomodoro_settings"
    __table_args__ = (
        CheckConstraint("focus_minutes BETWEEN 1 AND 180"),
        CheckConstraint("short_break_minutes BETWEEN 1 AND 60"),
        CheckConstraint("long_break_minutes BETWEEN 1 AND 120"),
        CheckConstraint("long_break_every BETWEEN 1 AND 12"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    focus_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    short_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    long_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    long_break_every: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class TimerRecord(Base):
    __tablename__ = "timers"
    __table_args__ = (
        CheckConstraint("phase IN ('focus', 'short_break', 'long_break')"),
        CheckConstraint("state IN ('running', 'paused', 'completed', 'cancelled')"),
        CheckConstraint("duration_seconds > 0"),
        CheckConstraint("remaining_seconds >= 0"),
        CheckConstraint(
            "study_flow_segment_index IS NULL OR study_flow_segment_index BETWEEN 0 AND 5"
        ),
        CheckConstraint("study_flow_confirmed_at IS NULL OR study_flow_session_id IS NOT NULL"),
        Index(
            "uq_timers_one_active",
            text("1"),
            unique=True,
            sqlite_where=text("state IN ('running', 'paused')"),
        ),
        Index("ix_timers_study_flow_session_id", "study_flow_session_id"),
        Index(
            "uq_timers_study_flow_segment_success",
            "study_flow_session_id",
            "study_flow_segment_index",
            unique=True,
            sqlite_where=text("study_flow_session_id IS NOT NULL AND state != 'cancelled'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    phase: Mapped[str] = mapped_column(String(20), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    title: Mapped[str | None] = mapped_column(String(200))
    study_flow_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("study_sessions.id", ondelete="SET NULL")
    )
    study_flow_segment_index: Mapped[int | None] = mapped_column(Integer)
    study_flow_confirmed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    expected_end_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    paused_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class StudySessionRecord(Base):
    __tablename__ = "study_sessions"
    __table_args__ = (
        CheckConstraint("source IN ('manual', 'pomodoro', 'study_flow')"),
        CheckConstraint("status IN ('active', 'completed', 'cancelled')"),
        CheckConstraint("ended_at IS NULL OR ended_at > started_at"),
        CheckConstraint("duration_seconds >= 0"),
        Index(
            "uq_study_sessions_one_active_study_flow",
            text("1"),
            unique=True,
            sqlite_where=text("source = 'study_flow' AND status = 'active' AND deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text())
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    timer_id: Mapped[str | None] = mapped_column(
        ForeignKey("timers.id", ondelete="SET NULL"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class FlashcardDeckRecord(Base):
    __tablename__ = "flashcard_decks"
    __table_args__ = (
        CheckConstraint("length(trim(name)) BETWEEN 1 AND 160"),
        CheckConstraint("description IS NULL OR length(description) <= 2000"),
        Index("ix_flashcard_decks_created_id", "created_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class FlashcardRecord(Base):
    __tablename__ = "flashcards"
    __table_args__ = (
        CheckConstraint("length(front_markdown) <= 20000 AND length(trim(front_markdown)) > 0"),
        CheckConstraint("length(back_markdown) <= 20000 AND length(trim(back_markdown)) > 0"),
        CheckConstraint("position >= 0"),
        CheckConstraint("repetitions >= 0"),
        CheckConstraint("interval_days >= 0"),
        CheckConstraint("ease_factor >= 1.3"),
        Index("ix_flashcards_deck_position_id", "deck_id", "position", "id"),
        Index("ix_flashcards_deck_due", "deck_id", "due_at", "position", "id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    deck_id: Mapped[str] = mapped_column(
        ForeignKey("flashcard_decks.id", ondelete="RESTRICT"), nullable=False
    )
    front_markdown: Mapped[str] = mapped_column(Text(), nullable=False)
    back_markdown: Mapped[str] = mapped_column(Text(), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False)
    due_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ReviewSessionRecord(Base):
    __tablename__ = "review_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('in_progress', 'completed', 'abandoned')"),
        CheckConstraint("duration_seconds >= 0"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at"),
        CheckConstraint(
            "(status = 'in_progress' AND ended_at IS NULL) OR "
            "(status IN ('completed', 'abandoned') AND ended_at IS NOT NULL)"
        ),
        CheckConstraint("deleted_at IS NULL OR status != 'in_progress'"),
        Index("ix_review_sessions_started_id", "started_at", "id"),
        Index(
            "uq_review_sessions_one_in_progress",
            text("1"),
            unique=True,
            sqlite_where=text("status = 'in_progress'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    deck_id: Mapped[str] = mapped_column(
        ForeignKey("flashcard_decks.id", ondelete="RESTRICT"), nullable=False
    )
    category_id_snapshot: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ReviewEventRecord(Base):
    __tablename__ = "review_events"
    __table_args__ = (
        CheckConstraint("sequence > 0"),
        CheckConstraint(
            "(rating = 'again' AND quality = 1) OR "
            "(rating = 'hard' AND quality = 3) OR "
            "(rating = 'good' AND quality = 4) OR "
            "(rating = 'easy' AND quality = 5)"
        ),
        CheckConstraint("previous_repetitions >= 0 AND new_repetitions >= 0"),
        CheckConstraint("previous_interval_days >= 0 AND new_interval_days >= 1"),
        CheckConstraint("previous_ease_factor >= 1.3 AND new_ease_factor >= 1.3"),
        CheckConstraint("new_due_at > reviewed_at"),
        CheckConstraint("new_last_reviewed_at = reviewed_at"),
        UniqueConstraint("command_id", name="uq_review_events_command_id"),
        UniqueConstraint("review_session_id", "sequence", name="uq_review_events_session_sequence"),
        UniqueConstraint("review_session_id", "card_id", name="uq_review_events_session_card"),
        Index("ix_review_events_session", "review_session_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    command_id: Mapped[str] = mapped_column(String(36), nullable=False)
    review_session_id: Mapped[str] = mapped_column(
        ForeignKey("review_sessions.id", ondelete="CASCADE"), nullable=False
    )
    card_id: Mapped[str] = mapped_column(
        ForeignKey("flashcards.id", ondelete="RESTRICT"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[str] = mapped_column(String(10), nullable=False)
    quality: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    previous_repetitions: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_ease_factor: Mapped[float] = mapped_column(Float, nullable=False)
    previous_due_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    previous_last_reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    new_repetitions: Mapped[int] = mapped_column(Integer, nullable=False)
    new_interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    new_ease_factor: Mapped[float] = mapped_column(Float, nullable=False)
    new_due_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    new_last_reviewed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
