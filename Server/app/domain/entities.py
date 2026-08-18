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
    STUDY_FLOW = "study_flow"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReviewStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ReviewRating(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


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
    study_flow_session_id: str | None = None
    study_flow_segment_index: int | None = None
    study_flow_confirmed_at: datetime | None = None
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


@dataclass(slots=True)
class FlashcardDeck:
    id: str
    name: str
    description: str | None
    category_id: str | None
    active_card_count: int
    due_card_count: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ScheduleSnapshot:
    repetitions: int
    interval_days: int
    ease_factor: float
    due_at: datetime
    last_reviewed_at: datetime | None


@dataclass(slots=True)
class Flashcard:
    id: str
    deck_id: str
    front_markdown: str
    back_markdown: str
    position: int
    schedule: ScheduleSnapshot
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(slots=True)
class ReviewSession:
    id: str
    deck_id: str
    category_id_snapshot: str | None
    status: ReviewStatus
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ReviewEvent:
    id: str
    command_id: str
    review_session_id: str
    card_id: str
    sequence: int
    rating: ReviewRating
    quality: int
    reviewed_at: datetime
    previous_schedule: ScheduleSnapshot
    new_schedule: ScheduleSnapshot
