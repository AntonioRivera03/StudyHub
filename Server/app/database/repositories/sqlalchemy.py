import builtins
from dataclasses import asdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    CategoryRecord,
    PomodoroSettingsRecord,
    StudySessionRecord,
    TimerRecord,
)
from app.domain.entities import (
    Category,
    PomodoroSettings,
    SessionSource,
    SessionStatus,
    StudySession,
    Timer,
    TimerPhase,
    TimerState,
)


def _category_entity(record: CategoryRecord) -> Category:
    return Category(
        id=record.id,
        name=record.name,
        color=record.color,
        created_at=record.created_at,
        updated_at=record.updated_at,
        deleted_at=record.deleted_at,
    )


def _settings_entity(record: PomodoroSettingsRecord) -> PomodoroSettings:
    return PomodoroSettings(
        focus_minutes=record.focus_minutes,
        short_break_minutes=record.short_break_minutes,
        long_break_minutes=record.long_break_minutes,
        long_break_every=record.long_break_every,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _timer_entity(record: TimerRecord) -> Timer:
    return Timer(
        id=record.id,
        phase=TimerPhase(record.phase),
        state=TimerState(record.state),
        category_id=record.category_id,
        title=record.title,
        study_flow_session_id=record.study_flow_session_id,
        study_flow_segment_index=record.study_flow_segment_index,
        study_flow_confirmed_at=record.study_flow_confirmed_at,
        duration_seconds=record.duration_seconds,
        remaining_seconds=record.remaining_seconds,
        started_at=record.started_at,
        expected_end_at=record.expected_end_at,
        paused_at=record.paused_at,
        completed_at=record.completed_at,
        cancelled_at=record.cancelled_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _session_entity(record: StudySessionRecord) -> StudySession:
    return StudySession(
        id=record.id,
        title=record.title,
        category_id=record.category_id,
        started_at=record.started_at,
        ended_at=record.ended_at,
        duration_seconds=record.duration_seconds,
        notes=record.notes,
        source=SessionSource(record.source),
        status=SessionStatus(record.status),
        timer_id=record.timer_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        deleted_at=record.deleted_at,
    )


class SQLAlchemyCategoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, *, include_deleted: bool = False) -> list[Category]:
        statement = select(CategoryRecord).order_by(CategoryRecord.created_at)
        if not include_deleted:
            statement = statement.where(CategoryRecord.deleted_at.is_(None))
        return [_category_entity(record) for record in self._session.scalars(statement)]

    def get(self, category_id: str, *, include_deleted: bool = False) -> Category | None:
        statement = select(CategoryRecord).where(CategoryRecord.id == category_id)
        if not include_deleted:
            statement = statement.where(CategoryRecord.deleted_at.is_(None))
        record = self._session.scalar(statement)
        return _category_entity(record) if record else None

    def add(self, category: Category) -> None:
        self._session.add(CategoryRecord(**asdict(category)))

    def save(self, category: Category) -> None:
        record = self._session.get(CategoryRecord, category.id)
        if record is None:
            return
        record.name = category.name
        record.color = category.color
        record.updated_at = category.updated_at
        record.deleted_at = category.deleted_at


class SQLAlchemyPomodoroSettingsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self) -> PomodoroSettings | None:
        record = self._session.get(PomodoroSettingsRecord, 1)
        return _settings_entity(record) if record else None

    def add(self, settings: PomodoroSettings) -> None:
        self._session.add(PomodoroSettingsRecord(id=1, **asdict(settings)))

    def save(self, settings: PomodoroSettings) -> None:
        record = self._session.get(PomodoroSettingsRecord, 1)
        if record is None:
            return
        record.focus_minutes = settings.focus_minutes
        record.short_break_minutes = settings.short_break_minutes
        record.long_break_minutes = settings.long_break_minutes
        record.long_break_every = settings.long_break_every
        record.updated_at = settings.updated_at


class SQLAlchemyTimerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, timer_id: str) -> Timer | None:
        record = self._session.get(TimerRecord, timer_id)
        return _timer_entity(record) if record else None

    def get_active(self) -> Timer | None:
        statement = select(TimerRecord).where(TimerRecord.state.in_(("running", "paused")))
        record = self._session.scalar(statement)
        return _timer_entity(record) if record else None

    def list_by_study_flow_session_id(self, session_id: str) -> builtins.list[Timer]:
        statement = (
            select(TimerRecord)
            .where(TimerRecord.study_flow_session_id == session_id)
            .order_by(TimerRecord.created_at)
        )
        return [_timer_entity(record) for record in self._session.scalars(statement)]

    def add(self, timer: Timer) -> None:
        self._session.add(TimerRecord(**asdict(timer)))

    def save(self, timer: Timer) -> None:
        record = self._session.get(TimerRecord, timer.id)
        if record is None:
            return
        record.state = timer.state.value
        record.remaining_seconds = timer.remaining_seconds
        record.expected_end_at = timer.expected_end_at
        record.paused_at = timer.paused_at
        record.completed_at = timer.completed_at
        record.cancelled_at = timer.cancelled_at
        record.study_flow_confirmed_at = timer.study_flow_confirmed_at
        record.updated_at = timer.updated_at


class SQLAlchemyStudySessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, *, include_deleted: bool = False) -> builtins.list[StudySession]:
        statement = select(StudySessionRecord).order_by(StudySessionRecord.started_at.desc())
        if not include_deleted:
            statement = statement.where(StudySessionRecord.deleted_at.is_(None))
        return [_session_entity(record) for record in self._session.scalars(statement)]

    def list_recent(self, *, limit: int) -> builtins.list[StudySession]:
        statement = (
            select(StudySessionRecord)
            .where(StudySessionRecord.deleted_at.is_(None))
            .order_by(StudySessionRecord.started_at.desc())
            .limit(limit)
        )
        return [_session_entity(record) for record in self._session.scalars(statement)]

    def list_completed_between(self, start: datetime, end: datetime) -> builtins.list[StudySession]:
        statement = select(StudySessionRecord).where(
            StudySessionRecord.deleted_at.is_(None),
            StudySessionRecord.status == SessionStatus.COMPLETED.value,
            StudySessionRecord.ended_at >= start,
            StudySessionRecord.ended_at < end,
        )
        return [_session_entity(record) for record in self._session.scalars(statement)]

    def get(self, session_id: str, *, include_deleted: bool = False) -> StudySession | None:
        statement = select(StudySessionRecord).where(StudySessionRecord.id == session_id)
        if not include_deleted:
            statement = statement.where(StudySessionRecord.deleted_at.is_(None))
        record = self._session.scalar(statement)
        return _session_entity(record) if record else None

    def get_by_timer_id(self, timer_id: str) -> StudySession | None:
        statement = select(StudySessionRecord).where(StudySessionRecord.timer_id == timer_id)
        record = self._session.scalar(statement)
        return _session_entity(record) if record else None

    def get_active_by_source(self, source: SessionSource) -> StudySession | None:
        statement = select(StudySessionRecord).where(
            StudySessionRecord.source == source.value,
            StudySessionRecord.status == SessionStatus.ACTIVE.value,
            StudySessionRecord.deleted_at.is_(None),
        )
        record = self._session.scalar(statement)
        return _session_entity(record) if record else None

    def add(self, study_session: StudySession) -> None:
        self._session.add(StudySessionRecord(**asdict(study_session)))

    def save(self, study_session: StudySession) -> None:
        record = self._session.get(StudySessionRecord, study_session.id)
        if record is None:
            return
        record.title = study_session.title
        record.category_id = study_session.category_id
        record.started_at = study_session.started_at
        record.ended_at = study_session.ended_at
        record.duration_seconds = study_session.duration_seconds
        record.notes = study_session.notes
        record.status = study_session.status.value
        record.updated_at = study_session.updated_at
        record.deleted_at = study_session.deleted_at
