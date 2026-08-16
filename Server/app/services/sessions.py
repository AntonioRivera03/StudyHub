from datetime import datetime
from uuid import uuid4

from app.core.clock import Clock
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.domain.entities import SessionSource, SessionStatus, StudySession
from app.domain.repositories import UnitOfWork, UnitOfWorkFactory


class StudySessionService:
    def __init__(self, unit_of_work_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock

    def list(self, *, include_deleted: bool = False) -> list[StudySession]:
        with self._unit_of_work_factory() as unit_of_work:
            return unit_of_work.sessions.list(include_deleted=include_deleted)

    def get(self, session_id: str, *, include_deleted: bool = False) -> StudySession:
        with self._unit_of_work_factory() as unit_of_work:
            study_session = unit_of_work.sessions.get(session_id, include_deleted=include_deleted)
            if study_session is None:
                raise NotFoundError("Study session not found")
            return study_session

    def create(
        self,
        *,
        title: str,
        category_id: str | None,
        started_at: datetime,
        ended_at: datetime | None,
        notes: str | None,
    ) -> StudySession:
        self._validate_dates(started_at, ended_at)
        with self._unit_of_work_factory() as unit_of_work:
            self._validate_category(unit_of_work, category_id)
            now = self._clock.now()
            study_session = StudySession(
                id=str(uuid4()),
                title=title,
                category_id=category_id,
                started_at=started_at,
                ended_at=ended_at,
                duration_seconds=self._duration_seconds(started_at, ended_at),
                notes=notes,
                source=SessionSource.MANUAL,
                status=(SessionStatus.COMPLETED if ended_at is not None else SessionStatus.ACTIVE),
                timer_id=None,
                created_at=now,
                updated_at=now,
            )
            unit_of_work.sessions.add(study_session)
            unit_of_work.commit()
            return study_session

    def update(
        self,
        session_id: str,
        *,
        changes: dict[str, str | datetime | None],
    ) -> StudySession:
        with self._unit_of_work_factory() as unit_of_work:
            study_session = unit_of_work.sessions.get(session_id)
            if study_session is None:
                raise NotFoundError("Study session not found")
            if (
                study_session.source is SessionSource.POMODORO
                and {
                    "started_at",
                    "ended_at",
                }
                & changes.keys()
            ):
                raise ConflictError("Pomodoro session times are managed by its timer")
            if "category_id" in changes:
                category_id = changes["category_id"]
                if category_id is not None and not isinstance(category_id, str):
                    raise ValidationError("Invalid category")
                self._validate_category(unit_of_work, category_id)

            for field_name, value in changes.items():
                setattr(study_session, field_name, value)
            self._validate_dates(study_session.started_at, study_session.ended_at)
            if study_session.source is SessionSource.MANUAL:
                study_session.duration_seconds = self._duration_seconds(
                    study_session.started_at, study_session.ended_at
                )
            if "ended_at" in changes:
                study_session.status = (
                    SessionStatus.COMPLETED
                    if study_session.ended_at is not None
                    else SessionStatus.ACTIVE
                )
            study_session.updated_at = self._clock.now()
            unit_of_work.sessions.save(study_session)
            unit_of_work.commit()
            return study_session

    def delete(self, session_id: str) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            study_session = unit_of_work.sessions.get(session_id)
            if study_session is None:
                raise NotFoundError("Study session not found")
            if study_session.status is SessionStatus.ACTIVE:
                raise ConflictError("An active study session cannot be deleted")
            now = self._clock.now()
            study_session.deleted_at = now
            study_session.updated_at = now
            unit_of_work.sessions.save(study_session)
            unit_of_work.commit()

    def restore(self, session_id: str) -> StudySession:
        with self._unit_of_work_factory() as unit_of_work:
            study_session = unit_of_work.sessions.get(session_id, include_deleted=True)
            if study_session is None:
                raise NotFoundError("Study session not found")
            if study_session.deleted_at is None:
                raise ConflictError("Study session is not deleted")
            study_session.deleted_at = None
            study_session.updated_at = self._clock.now()
            unit_of_work.sessions.save(study_session)
            unit_of_work.commit()
            return study_session

    @staticmethod
    def _validate_dates(started_at: datetime, ended_at: datetime | None) -> None:
        if ended_at is not None and ended_at <= started_at:
            raise ValidationError("ended_at must be after started_at")

    @staticmethod
    def _duration_seconds(started_at: datetime, ended_at: datetime | None) -> int:
        if ended_at is None:
            return 0
        return int((ended_at - started_at).total_seconds())

    @staticmethod
    def _validate_category(unit_of_work: UnitOfWork, category_id: str | None) -> None:
        if category_id is not None and unit_of_work.categories.get(category_id) is None:
            raise ValidationError("Category not found")
