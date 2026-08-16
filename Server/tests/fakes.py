from datetime import datetime
from types import TracebackType

from app.domain.entities import Category, PomodoroSettings, StudySession, Timer, TimerState


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

    def add(self, study_session: StudySession) -> None:
        self.items[study_session.id] = study_session

    def save(self, study_session: StudySession) -> None:
        self.items[study_session.id] = study_session


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.categories = FakeCategoryRepository()
        self.pomodoro_settings = FakeSettingsRepository()
        self.timers = FakeTimerRepository()
        self.sessions = FakeStudySessionRepository()
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
