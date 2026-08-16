from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


@dataclass
class MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


@dataclass
class ApiContext:
    client: TestClient
    clock: MutableClock
    database_path: Path


@pytest.fixture
def api_context(tmp_path: Path) -> Iterator[ApiContext]:
    database_path = tmp_path / "studyhub-test.db"
    application = create_app(
        Settings(database_url=f"sqlite:///{database_path}", environment="test")
    )
    clock = MutableClock(datetime(2026, 8, 16, 10, 0, tzinfo=UTC))
    with TestClient(application) as client:
        application.state.clock = clock
        yield ApiContext(client=client, clock=clock, database_path=database_path)
