from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, text
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
        Index(
            "uq_timers_one_active",
            text("1"),
            unique=True,
            sqlite_where=text("state IN ('running', 'paused')"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    phase: Mapped[str] = mapped_column(String(20), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    title: Mapped[str | None] = mapped_column(String(200))
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
        CheckConstraint("source IN ('manual', 'pomodoro')"),
        CheckConstraint("status IN ('active', 'completed', 'cancelled')"),
        CheckConstraint("ended_at IS NULL OR ended_at > started_at"),
        CheckConstraint("duration_seconds >= 0"),
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
