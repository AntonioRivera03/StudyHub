import builtins
from dataclasses import asdict
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import ScalarSelect

from app.database.models import (
    CategoryRecord,
    FlashcardDeckRecord,
    FlashcardRecord,
    PomodoroSettingsRecord,
    ReviewEventRecord,
    ReviewSessionRecord,
    StudySessionRecord,
    TimerRecord,
)
from app.domain.entities import (
    Category,
    Flashcard,
    FlashcardDeck,
    PomodoroSettings,
    ReviewEvent,
    ReviewRating,
    ReviewSession,
    ReviewStatus,
    ScheduleSnapshot,
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


def _deck_entity(
    record: FlashcardDeckRecord, active_card_count: int, due_card_count: int
) -> FlashcardDeck:
    return FlashcardDeck(
        id=record.id,
        name=record.name,
        description=record.description,
        category_id=record.category_id,
        active_card_count=active_card_count,
        due_card_count=due_card_count if record.deleted_at is None else 0,
        created_at=record.created_at,
        updated_at=record.updated_at,
        deleted_at=record.deleted_at,
    )


def _card_entity(record: FlashcardRecord) -> Flashcard:
    return Flashcard(
        id=record.id,
        deck_id=record.deck_id,
        front_markdown=record.front_markdown,
        back_markdown=record.back_markdown,
        position=record.position,
        schedule=ScheduleSnapshot(
            repetitions=record.repetitions,
            interval_days=record.interval_days,
            ease_factor=record.ease_factor,
            due_at=record.due_at,
            last_reviewed_at=record.last_reviewed_at,
        ),
        created_at=record.created_at,
        updated_at=record.updated_at,
        deleted_at=record.deleted_at,
    )


def _review_session_entity(record: ReviewSessionRecord) -> ReviewSession:
    return ReviewSession(
        id=record.id,
        deck_id=record.deck_id,
        category_id_snapshot=record.category_id_snapshot,
        status=ReviewStatus(record.status),
        started_at=record.started_at,
        ended_at=record.ended_at,
        duration_seconds=record.duration_seconds,
        created_at=record.created_at,
        updated_at=record.updated_at,
        deleted_at=record.deleted_at,
    )


def _review_event_entity(record: ReviewEventRecord) -> ReviewEvent:
    return ReviewEvent(
        id=record.id,
        command_id=record.command_id,
        review_session_id=record.review_session_id,
        card_id=record.card_id,
        sequence=record.sequence,
        rating=ReviewRating(record.rating),
        quality=record.quality,
        reviewed_at=record.reviewed_at,
        previous_schedule=ScheduleSnapshot(
            repetitions=record.previous_repetitions,
            interval_days=record.previous_interval_days,
            ease_factor=record.previous_ease_factor,
            due_at=record.previous_due_at,
            last_reviewed_at=record.previous_last_reviewed_at,
        ),
        new_schedule=ScheduleSnapshot(
            repetitions=record.new_repetitions,
            interval_days=record.new_interval_days,
            ease_factor=record.new_ease_factor,
            due_at=record.new_due_at,
            last_reviewed_at=record.new_last_reviewed_at,
        ),
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


class SQLAlchemyFlashcardDeckRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _counts(now: datetime) -> tuple[ScalarSelect[int], ScalarSelect[int]]:
        active_count = (
            select(func.count(FlashcardRecord.id))
            .where(
                FlashcardRecord.deck_id == FlashcardDeckRecord.id,
                FlashcardRecord.deleted_at.is_(None),
            )
            .correlate(FlashcardDeckRecord)
            .scalar_subquery()
        )
        due_count = (
            select(func.count(FlashcardRecord.id))
            .where(
                FlashcardRecord.deck_id == FlashcardDeckRecord.id,
                FlashcardRecord.deleted_at.is_(None),
                FlashcardRecord.due_at <= now,
            )
            .correlate(FlashcardDeckRecord)
            .scalar_subquery()
        )
        return active_count, due_count

    def list(self, now: datetime, *, include_deleted: bool = False) -> list[FlashcardDeck]:
        active_count, due_count = self._counts(now)
        statement = select(FlashcardDeckRecord, active_count, due_count).order_by(
            FlashcardDeckRecord.created_at, FlashcardDeckRecord.id
        )
        if not include_deleted:
            statement = statement.where(FlashcardDeckRecord.deleted_at.is_(None))
        return [
            _deck_entity(record, active, due)
            for record, active, due in self._session.execute(statement).tuples()
        ]

    def get(
        self, deck_id: str, now: datetime, *, include_deleted: bool = False
    ) -> FlashcardDeck | None:
        active_count, due_count = self._counts(now)
        statement = select(FlashcardDeckRecord, active_count, due_count).where(
            FlashcardDeckRecord.id == deck_id
        )
        if not include_deleted:
            statement = statement.where(FlashcardDeckRecord.deleted_at.is_(None))
        row = self._session.execute(statement).tuples().one_or_none()
        return _deck_entity(*row) if row is not None else None

    def add(self, deck: FlashcardDeck) -> None:
        self._session.add(
            FlashcardDeckRecord(
                id=deck.id,
                name=deck.name,
                description=deck.description,
                category_id=deck.category_id,
                created_at=deck.created_at,
                updated_at=deck.updated_at,
                deleted_at=deck.deleted_at,
            )
        )

    def save(self, deck: FlashcardDeck) -> None:
        record = self._session.get(FlashcardDeckRecord, deck.id)
        if record is None:
            return
        record.name = deck.name
        record.description = deck.description
        record.category_id = deck.category_id
        record.updated_at = deck.updated_at
        record.deleted_at = deck.deleted_at


class SQLAlchemyFlashcardRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_deck(
        self, deck_id: str, *, include_deleted: bool = False
    ) -> builtins.list[Flashcard]:
        statement = (
            select(FlashcardRecord)
            .where(FlashcardRecord.deck_id == deck_id)
            .order_by(FlashcardRecord.position, FlashcardRecord.id)
        )
        if not include_deleted:
            statement = statement.where(FlashcardRecord.deleted_at.is_(None))
        return [_card_entity(record) for record in self._session.scalars(statement)]

    def list_due(self, deck_id: str, now: datetime) -> builtins.list[Flashcard]:
        statement = (
            select(FlashcardRecord)
            .join(FlashcardDeckRecord, FlashcardRecord.deck_id == FlashcardDeckRecord.id)
            .where(
                FlashcardRecord.deck_id == deck_id,
                FlashcardRecord.deleted_at.is_(None),
                FlashcardDeckRecord.deleted_at.is_(None),
                FlashcardRecord.due_at <= now,
            )
            .order_by(FlashcardRecord.due_at, FlashcardRecord.position, FlashcardRecord.id)
        )
        return [_card_entity(record) for record in self._session.scalars(statement)]

    def list_due_excluding_review(
        self, deck_id: str, review_session_id: str, now: datetime
    ) -> builtins.list[Flashcard]:
        reviewed_cards = select(ReviewEventRecord.card_id).where(
            ReviewEventRecord.review_session_id == review_session_id
        )
        statement = (
            select(FlashcardRecord)
            .join(FlashcardDeckRecord, FlashcardRecord.deck_id == FlashcardDeckRecord.id)
            .where(
                FlashcardRecord.deck_id == deck_id,
                FlashcardRecord.deleted_at.is_(None),
                FlashcardDeckRecord.deleted_at.is_(None),
                FlashcardRecord.due_at <= now,
                FlashcardRecord.id.not_in(reviewed_cards),
            )
            .order_by(FlashcardRecord.due_at, FlashcardRecord.position, FlashcardRecord.id)
        )
        return [_card_entity(record) for record in self._session.scalars(statement)]

    def get(self, card_id: str, *, include_deleted: bool = False) -> Flashcard | None:
        statement = (
            select(FlashcardRecord)
            .join(FlashcardDeckRecord, FlashcardRecord.deck_id == FlashcardDeckRecord.id)
            .where(FlashcardRecord.id == card_id)
        )
        if not include_deleted:
            statement = statement.where(
                FlashcardRecord.deleted_at.is_(None), FlashcardDeckRecord.deleted_at.is_(None)
            )
        record = self._session.scalar(statement)
        return _card_entity(record) if record else None

    def max_position(self, deck_id: str) -> int | None:
        return self._session.scalar(
            select(func.max(FlashcardRecord.position)).where(
                FlashcardRecord.deck_id == deck_id, FlashcardRecord.deleted_at.is_(None)
            )
        )

    def add(self, card: Flashcard) -> None:
        self._session.add(
            FlashcardRecord(
                id=card.id,
                deck_id=card.deck_id,
                front_markdown=card.front_markdown,
                back_markdown=card.back_markdown,
                position=card.position,
                repetitions=card.schedule.repetitions,
                interval_days=card.schedule.interval_days,
                ease_factor=card.schedule.ease_factor,
                due_at=card.schedule.due_at,
                last_reviewed_at=card.schedule.last_reviewed_at,
                created_at=card.created_at,
                updated_at=card.updated_at,
                deleted_at=card.deleted_at,
            )
        )

    def save(self, card: Flashcard) -> None:
        record = self._session.get(FlashcardRecord, card.id)
        if record is None:
            return
        record.front_markdown = card.front_markdown
        record.back_markdown = card.back_markdown
        record.position = card.position
        record.repetitions = card.schedule.repetitions
        record.interval_days = card.schedule.interval_days
        record.ease_factor = card.schedule.ease_factor
        record.due_at = card.schedule.due_at
        record.last_reviewed_at = card.schedule.last_reviewed_at
        record.updated_at = card.updated_at
        record.deleted_at = card.deleted_at


class SQLAlchemyReviewSessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, *, include_deleted: bool = False) -> builtins.list[ReviewSession]:
        statement = select(ReviewSessionRecord).order_by(
            ReviewSessionRecord.started_at.desc(), ReviewSessionRecord.id
        )
        if not include_deleted:
            statement = statement.where(ReviewSessionRecord.deleted_at.is_(None))
        return [_review_session_entity(record) for record in self._session.scalars(statement)]

    def list_completed_between(
        self, start: datetime, end: datetime
    ) -> builtins.list[ReviewSession]:
        statement = select(ReviewSessionRecord).where(
            ReviewSessionRecord.deleted_at.is_(None),
            ReviewSessionRecord.status == ReviewStatus.COMPLETED.value,
            ReviewSessionRecord.ended_at >= start,
            ReviewSessionRecord.ended_at < end,
        )
        return [_review_session_entity(record) for record in self._session.scalars(statement)]

    def get(self, review_session_id: str, *, include_deleted: bool = False) -> ReviewSession | None:
        statement = select(ReviewSessionRecord).where(ReviewSessionRecord.id == review_session_id)
        if not include_deleted:
            statement = statement.where(ReviewSessionRecord.deleted_at.is_(None))
        record = self._session.scalar(statement)
        return _review_session_entity(record) if record else None

    def get_active(self) -> ReviewSession | None:
        record = self._session.scalar(
            select(ReviewSessionRecord).where(
                ReviewSessionRecord.status == ReviewStatus.IN_PROGRESS.value,
                ReviewSessionRecord.deleted_at.is_(None),
            )
        )
        return _review_session_entity(record) if record else None

    def get_active_for_deck(self, deck_id: str) -> ReviewSession | None:
        record = self._session.scalar(
            select(ReviewSessionRecord).where(
                ReviewSessionRecord.deck_id == deck_id,
                ReviewSessionRecord.status == ReviewStatus.IN_PROGRESS.value,
                ReviewSessionRecord.deleted_at.is_(None),
            )
        )
        return _review_session_entity(record) if record else None

    def add(self, review_session: ReviewSession) -> None:
        self._session.add(ReviewSessionRecord(**asdict(review_session)))

    def save(self, review_session: ReviewSession) -> None:
        record = self._session.get(ReviewSessionRecord, review_session.id)
        if record is None:
            return
        record.status = review_session.status.value
        record.ended_at = review_session.ended_at
        record.duration_seconds = review_session.duration_seconds
        record.updated_at = review_session.updated_at
        record.deleted_at = review_session.deleted_at


class SQLAlchemyReviewEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_session(self, review_session_id: str) -> builtins.list[ReviewEvent]:
        statement = (
            select(ReviewEventRecord)
            .where(ReviewEventRecord.review_session_id == review_session_id)
            .order_by(ReviewEventRecord.sequence)
        )
        return [_review_event_entity(record) for record in self._session.scalars(statement)]

    def get_by_command_id(self, command_id: str) -> ReviewEvent | None:
        record = self._session.scalar(
            select(ReviewEventRecord).where(ReviewEventRecord.command_id == command_id)
        )
        return _review_event_entity(record) if record else None

    def next_sequence(self, review_session_id: str) -> int:
        maximum = self._session.scalar(
            select(func.max(ReviewEventRecord.sequence)).where(
                ReviewEventRecord.review_session_id == review_session_id
            )
        )
        return (maximum or 0) + 1

    def count_for_sessions(self, review_session_ids: set[str]) -> int:
        if not review_session_ids:
            return 0
        count = self._session.scalar(
            select(func.count(ReviewEventRecord.id)).where(
                ReviewEventRecord.review_session_id.in_(review_session_ids)
            )
        )
        return count or 0

    def add(self, event: ReviewEvent) -> None:
        self._session.add(
            ReviewEventRecord(
                id=event.id,
                command_id=event.command_id,
                review_session_id=event.review_session_id,
                card_id=event.card_id,
                sequence=event.sequence,
                rating=event.rating.value,
                quality=event.quality,
                reviewed_at=event.reviewed_at,
                previous_repetitions=event.previous_schedule.repetitions,
                previous_interval_days=event.previous_schedule.interval_days,
                previous_ease_factor=event.previous_schedule.ease_factor,
                previous_due_at=event.previous_schedule.due_at,
                previous_last_reviewed_at=event.previous_schedule.last_reviewed_at,
                new_repetitions=event.new_schedule.repetitions,
                new_interval_days=event.new_schedule.interval_days,
                new_ease_factor=event.new_schedule.ease_factor,
                new_due_at=event.new_schedule.due_at,
                new_last_reviewed_at=event.new_schedule.last_reviewed_at,
            )
        )
