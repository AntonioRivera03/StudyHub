import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app
from tests.conftest import ApiContext


def test_health(api_context: ApiContext) -> None:
    response = api_context.client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    with sqlite3.connect(api_context.database_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    assert revision == ("20260816_0002",)


def test_initial_alembic_migration(tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    environment = os.environ.copy()
    environment["STUDYHUB_DATABASE_URL"] = f"sqlite:///{database_path}"
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).parents[2],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        session_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(study_sessions)")
        }
        timer_columns = {row[1] for row in connection.execute("PRAGMA table_info(timers)")}
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    assert {
        "alembic_version",
        "categories",
        "pomodoro_settings",
        "study_sessions",
        "timers",
    } <= tables
    assert "duration_seconds" in session_columns
    assert {
        "study_flow_session_id",
        "study_flow_segment_index",
        "study_flow_confirmed_at",
    } <= timer_columns
    assert revision == ("20260816_0002",)


def test_startup_migration_is_idempotent(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'restart.db'}", environment="test")

    for _ in range(2):
        with TestClient(create_app(settings)) as client:
            assert client.get("/api/v1/health").status_code == 200

    with sqlite3.connect(tmp_path / "restart.db") as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    assert revision == ("20260816_0002",)


def test_study_flow_migration_preserves_existing_timer_session_link(tmp_path: Path) -> None:
    database_path = tmp_path / "existing.db"
    environment = os.environ.copy()
    environment["STUDYHUB_DATABASE_URL"] = f"sqlite:///{database_path}"
    server_root = Path(__file__).parents[2]
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "20260816_0001"],
        cwd=server_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    with sqlite3.connect(database_path) as connection:
        timestamp = "2026-08-16 10:00:00"
        connection.execute(
            """
            INSERT INTO timers (
                id, phase, state, duration_seconds, remaining_seconds, started_at,
                expected_end_at, created_at, updated_at
            ) VALUES (?, 'focus', 'completed', 1500, 0, ?, ?, ?, ?)
            """,
            ("timer-1", timestamp, timestamp, timestamp, timestamp),
        )
        connection.execute(
            """
            INSERT INTO study_sessions (
                id, title, started_at, ended_at, duration_seconds, source, status,
                timer_id, created_at, updated_at
            ) VALUES (?, 'Existing focus', ?, ?, 1500, 'pomodoro', 'completed', ?, ?, ?)
            """,
            ("session-1", timestamp, "2026-08-16 10:25:00", "timer-1", timestamp, timestamp),
        )
        connection.commit()

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=server_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    with sqlite3.connect(database_path) as connection:
        linked_timer_id = connection.execute(
            "SELECT timer_id FROM study_sessions WHERE id = 'session-1'"
        ).fetchone()
        flow_link = connection.execute(
            """
            SELECT study_flow_session_id, study_flow_segment_index, study_flow_confirmed_at
            FROM timers WHERE id = 'timer-1'
            """
        ).fetchone()
    assert linked_timer_id == ("timer-1",)
    assert flow_link == (None, None, None)


def test_production_frontend_serving_and_browser_fallback(tmp_path: Path) -> None:
    dist_path = tmp_path / "dist"
    assets_path = dist_path / "assets"
    assets_path.mkdir(parents=True)
    (dist_path / "index.html").write_text("<main>StudyHub</main>", encoding="utf-8")
    (assets_path / "app.js").write_text("window.studyhub = true;", encoding="utf-8")
    application = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path / 'production.db'}",
            environment="production",
        ),
        frontend_dist_path=dist_path,
    )

    with TestClient(application) as client:
        assert client.get("/api/v1/health").json() == {"status": "ok"}
        assert client.get("/courses/current").text == "<main>StudyHub</main>"
        assert client.get("/assets/app.js").text == "window.studyhub = true;"
        assert client.get("/api/v1/unknown").status_code == 404
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200
