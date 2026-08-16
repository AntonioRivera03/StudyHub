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
    assert revision == ("20260816_0001",)


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
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    assert {
        "alembic_version",
        "categories",
        "pomodoro_settings",
        "study_sessions",
        "timers",
    } <= tables
    assert "duration_seconds" in session_columns
    assert revision == ("20260816_0001",)


def test_startup_migration_is_idempotent(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'restart.db'}", environment="test")

    for _ in range(2):
        with TestClient(create_app(settings)) as client:
            assert client.get("/api/v1/health").status_code == 200

    with sqlite3.connect(tmp_path / "restart.db") as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    assert revision == ("20260816_0001",)


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
