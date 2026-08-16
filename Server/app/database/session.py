from collections.abc import Callable
from sqlite3 import Connection as SQLiteConnection
from types import TracebackType

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import ConflictError
from app.core.settings import Settings
from app.database.repositories import (
    SQLAlchemyCategoryRepository,
    SQLAlchemyPomodoroSettingsRepository,
    SQLAlchemyStudySessionRepository,
    SQLAlchemyTimerRepository,
)


class SQLAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> SQLAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.categories = SQLAlchemyCategoryRepository(self._session)
        self.pomodoro_settings = SQLAlchemyPomodoroSettingsRepository(self._session)
        self.timers = SQLAlchemyTimerRepository(self._session)
        self.sessions = SQLAlchemyStudySessionRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        self._session.close()

    def commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise ConflictError("Operation conflicts with existing data") from error

    def flush(self) -> None:
        try:
            self._session.flush()
        except IntegrityError as error:
            self._session.rollback()
            raise ConflictError("Operation conflicts with existing data") from error

    def rollback(self) -> None:
        self._session.rollback()


class Database:
    def __init__(self, settings: Settings) -> None:
        settings.ensure_database_directory()
        connect_args = (
            {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        )
        self.engine = create_engine(settings.database_url, connect_args=connect_args)
        if self.engine.dialect.name == "sqlite":
            event.listen(self.engine, "connect", _configure_sqlite)
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False)

    def unit_of_work_factory(self) -> Callable[[], SQLAlchemyUnitOfWork]:
        return lambda: SQLAlchemyUnitOfWork(self._session_factory)

    def dispose(self) -> None:
        self.engine.dispose()


def _configure_sqlite(dbapi_connection: SQLiteConnection, connection_record: object) -> None:
    del connection_record
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()
