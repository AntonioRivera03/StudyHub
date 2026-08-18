from datetime import datetime
from types import TracebackType

from app.domain.entities import (
    Category,
    Flashcard,
    FlashcardDeck,
    PomodoroSettings,
    ReviewEvent,
    ReviewSession,
    ReviewStatus,
    SessionSource,
    SessionStatus,
    StudySession,
    Timer,
    TimerState,
)


class FakeCategoryRepository:
    def __init__(self) -> None:
        self.items: dict[str, Category] = {}

    def list(self, *, include_deleted: bool = False) -> list[Category]:
        return [item for item in self.items.values() if include_deleted or item.deleted_at is None]

    def get(self, category_id: str, *, include_deleted: bool = False) -> Category | None:
        item = self.items.get(category_id)
        if item is not None and (include_deleted or item.deleted_at is None):
            return item
        return None

    def add(self, category: Category) -> None:
        self.items[category.id] = category

    def save(self, category: Category) -> None:
        self.items[category.id] = category


class FakeSettingsRepository:
    def __init__(self) -> None:
        self.item: PomodoroSettings | None = None

    def get(self) -> PomodoroSettings | None:
        return self.item

    def add(self, settings: PomodoroSettings) -> None:
        self.item = settings

    def save(self, settings: PomodoroSettings) -> None:
        self.item = settings


class FakeTimerRepository:
    def __init__(self) -> None:
        self.items: dict[str, Timer] = {}

    def get(self, timer_id: str) -> Timer | None:
        return self.items.get(timer_id)

    def get_active(self) -> Timer | None:
        return next(
            (
                timer
                for timer in self.items.values()
                if timer.state in {TimerState.RUNNING, TimerState.PAUSED}
            ),
            None,
        )

    def list_by_study_flow_session_id(self, session_id: str) -> list[Timer]:
        return [timer for timer in self.items.values() if timer.study_flow_session_id == session_id]

    def add(self, timer: Timer) -> None:
        self.items[timer.id] = timer

    def save(self, timer: Timer) -> None:
        self.items[timer.id] = timer


class FakeStudySessionRepository:
    def __init__(self) -> None:
        self.items: dict[str, StudySession] = {}

    def list(self, *, include_deleted: bool = False) -> list[StudySession]:
        return [item for item in self.items.values() if include_deleted or item.deleted_at is None]

    def list_recent(self, *, limit: int) -> list[StudySession]:
        return self.list()[:limit]

    def list_completed_between(self, start: datetime, end: datetime) -> list[StudySession]:
        return [
            item
            for item in self.items.values()
            if item.ended_at is not None and start <= item.ended_at < end
        ]

    def get(self, session_id: str, *, include_deleted: bool = False) -> StudySession | None:
        item = self.items.get(session_id)
        if item is not None and (include_deleted or item.deleted_at is None):
            return item
        return None

    def get_by_timer_id(self, timer_id: str) -> StudySession | None:
        return next((item for item in self.items.values() if item.timer_id == timer_id), None)

    def get_active_by_source(self, source: SessionSource) -> StudySession | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.source is source
                and item.status is SessionStatus.ACTIVE
                and item.deleted_at is None
            ),
            None,
        )

    def add(self, study_session: StudySession) -> None:
        self.items[study_session.id] = study_session

    def save(self, study_session: StudySession) -> None:
        self.items[study_session.id] = study_session


class FakeFlashcardDeckRepository:
    def __init__(self) -> None:
        self.items: dict[str, FlashcardDeck] = {}
        self.cards: FakeFlashcardRepository

    def list(self, now: datetime, *, include_deleted: bool = False) -> list[FlashcardDeck]:
        decks = [
            self._with_counts(item, now)
            for item in self.items.values()
            if include_deleted or item.deleted_at is None
        ]
        return sorted(decks, key=lambda item: (item.created_at, item.id))

    def get(
        self, deck_id: str, now: datetime, *, include_deleted: bool = False
    ) -> FlashcardDeck | None:
        item = self.items.get(deck_id)
        if item is not None and (include_deleted or item.deleted_at is None):
            return self._with_counts(item, now)
        return None

    def add(self, deck: FlashcardDeck) -> None:
        self.items[deck.id] = deck

    def save(self, deck: FlashcardDeck) -> None:
        self.items[deck.id] = deck

    def _with_counts(self, deck: FlashcardDeck, now: datetime) -> FlashcardDeck:
        active = [
            card
            for card in self.cards.items.values()
            if card.deck_id == deck.id and card.deleted_at is None
        ]
        deck.active_card_count = len(active)
        deck.due_card_count = (
            sum(card.schedule.due_at <= now for card in active) if deck.deleted_at is None else 0
        )
        return deck


class FakeFlashcardRepository:
    def __init__(self) -> None:
        self.items: dict[str, Flashcard] = {}
        self.decks: FakeFlashcardDeckRepository
        self.events: FakeReviewEventRepository

    def list_by_deck(self, deck_id: str, *, include_deleted: bool = False) -> list[Flashcard]:
        return sorted(
            [
                item
                for item in self.items.values()
                if item.deck_id == deck_id and (include_deleted or item.deleted_at is None)
            ],
            key=lambda item: (item.position, item.id),
        )

    def list_due(self, deck_id: str, now: datetime) -> list[Flashcard]:
        deck = self.decks.items.get(deck_id)
        if deck is None or deck.deleted_at is not None:
            return []
        return sorted(
            [
                item
                for item in self.items.values()
                if item.deck_id == deck_id
                and item.deleted_at is None
                and item.schedule.due_at <= now
            ],
            key=lambda item: (item.schedule.due_at, item.position, item.id),
        )

    def list_due_excluding_review(
        self, deck_id: str, review_session_id: str, now: datetime
    ) -> list[Flashcard]:
        reviewed_ids = {
            event.card_id
            for event in self.events.items.values()
            if event.review_session_id == review_session_id
        }
        return [item for item in self.list_due(deck_id, now) if item.id not in reviewed_ids]

    def get(self, card_id: str, *, include_deleted: bool = False) -> Flashcard | None:
        item = self.items.get(card_id)
        if item is None:
            return None
        deck = self.decks.items.get(item.deck_id)
        if include_deleted or (
            item.deleted_at is None and deck is not None and deck.deleted_at is None
        ):
            return item
        return None

    def max_position(self, deck_id: str) -> int | None:
        positions = [
            item.position
            for item in self.items.values()
            if item.deck_id == deck_id and item.deleted_at is None
        ]
        return max(positions, default=None)

    def add(self, card: Flashcard) -> None:
        self.items[card.id] = card

    def save(self, card: Flashcard) -> None:
        self.items[card.id] = card


class FakeReviewSessionRepository:
    def __init__(self) -> None:
        self.items: dict[str, ReviewSession] = {}

    def list(self, *, include_deleted: bool = False) -> list[ReviewSession]:
        return sorted(
            [item for item in self.items.values() if include_deleted or item.deleted_at is None],
            key=lambda item: (item.started_at, item.id),
            reverse=True,
        )

    def list_completed_between(self, start: datetime, end: datetime) -> list[ReviewSession]:
        return [
            item
            for item in self.items.values()
            if item.status is ReviewStatus.COMPLETED
            and item.deleted_at is None
            and item.ended_at is not None
            and start <= item.ended_at < end
        ]

    def get(self, review_session_id: str, *, include_deleted: bool = False) -> ReviewSession | None:
        item = self.items.get(review_session_id)
        if item is not None and (include_deleted or item.deleted_at is None):
            return item
        return None

    def get_active(self) -> ReviewSession | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.status is ReviewStatus.IN_PROGRESS and item.deleted_at is None
            ),
            None,
        )

    def get_active_for_deck(self, deck_id: str) -> ReviewSession | None:
        item = self.get_active()
        return item if item is not None and item.deck_id == deck_id else None

    def add(self, review_session: ReviewSession) -> None:
        self.items[review_session.id] = review_session

    def save(self, review_session: ReviewSession) -> None:
        self.items[review_session.id] = review_session


class FakeReviewEventRepository:
    def __init__(self) -> None:
        self.items: dict[str, ReviewEvent] = {}

    def list_by_session(self, review_session_id: str) -> list[ReviewEvent]:
        return sorted(
            [item for item in self.items.values() if item.review_session_id == review_session_id],
            key=lambda item: item.sequence,
        )

    def get_by_command_id(self, command_id: str) -> ReviewEvent | None:
        return next((item for item in self.items.values() if item.command_id == command_id), None)

    def next_sequence(self, review_session_id: str) -> int:
        return len(self.list_by_session(review_session_id)) + 1

    def count_for_sessions(self, review_session_ids: set[str]) -> int:
        return sum(item.review_session_id in review_session_ids for item in self.items.values())

    def add(self, event: ReviewEvent) -> None:
        self.items[event.id] = event


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.categories = FakeCategoryRepository()
        self.pomodoro_settings = FakeSettingsRepository()
        self.timers = FakeTimerRepository()
        self.sessions = FakeStudySessionRepository()
        self.decks = FakeFlashcardDeckRepository()
        self.cards = FakeFlashcardRepository()
        self.review_sessions = FakeReviewSessionRepository()
        self.review_events = FakeReviewEventRepository()
        self.decks.cards = self.cards
        self.cards.decks = self.decks
        self.cards.events = self.review_events
        self.commit_count = 0

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback

    def commit(self) -> None:
        self.commit_count += 1

    def flush(self) -> None:
        pass

    def rollback(self) -> None:
        pass
