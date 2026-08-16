from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TimerPhase(StrEnum):
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class TimerState(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionSource(StrEnum):
    MANUAL = "manual"
    POMODORO = "pomodoro"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Category:
    id: str
    name: str
    color: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(slots=True)
class PomodoroSettings:
    focus_minutes: int
    short_break_minutes: int
    long_break_minutes: int
    long_break_every: int
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class Timer:
    id: str
    phase: TimerPhase
    state: TimerState
    duration_seconds: int
    remaining_seconds: int
    started_at: datetime
    expected_end_at: datetime
    created_at: datetime
    updated_at: datetime
    category_id: str | None = None
    title: str | None = None
    paused_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None


@dataclass(slots=True)
class StudySession:
    id: str
    title: str
    category_id: str | None
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    notes: str | None
    source: SessionSource
    status: SessionStatus
    timer_id: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
