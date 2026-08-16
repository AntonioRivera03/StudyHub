from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.routes import api_router
from app.core.clock import SystemClock
from app.core.errors import ApplicationError
from app.core.settings import Settings, get_settings
from app.database.migrations import upgrade_database
from app.database.session import Database


def create_app(
    settings: Settings | None = None, *, frontend_dist_path: Path | None = None
) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        upgrade_database(resolved_settings)
        database = Database(resolved_settings)
        application.state.unit_of_work_factory = database.unit_of_work_factory()
        application.state.clock = SystemClock()
        yield
        database.dispose()

    application = FastAPI(title="StudyHub API", version="1.0.0", lifespan=lifespan)
    application.include_router(api_router, prefix="/api/v1")

    if resolved_settings.environment == "development":
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:4173",
                "http://127.0.0.1:4173",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @application.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, error: ApplicationError) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": error.message}},
        )

    if resolved_settings.environment == "production":
        dist_path = frontend_dist_path or Path(__file__).resolve().parents[2] / "UI" / "dist"
        _configure_frontend(application, dist_path)

    return application


def _configure_frontend(application: FastAPI, dist_path: Path) -> None:
    frontend_root = dist_path.resolve()
    index_path = frontend_root / "index.html"
    if not frontend_root.is_dir() or not index_path.is_file():
        return

    @application.get("/{requested_path:path}", include_in_schema=False)
    def serve_frontend(requested_path: str) -> FileResponse:
        first_segment = requested_path.partition("/")[0]
        if first_segment in {"api", "docs", "redoc"} or requested_path == "openapi.json":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        candidate = (frontend_root / requested_path).resolve()
        if not candidate.is_relative_to(frontend_root):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if candidate.is_file():
            return FileResponse(candidate)
        if candidate.is_dir() and (candidate / "index.html").is_file():
            return FileResponse(candidate / "index.html")
        return FileResponse(index_path)


app = create_app()
