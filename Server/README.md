# StudyHub Server

Install dependencies and run the API from this directory:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The API is served under `/api/v1`. `STUDYHUB_DATABASE_URL` overrides the default SQLite
database at `$XDG_DATA_HOME/studyhub/studyhub.db` (or
`~/.local/share/studyhub/studyhub.db`). Startup automatically applies all Alembic migrations.
Migrations can also be applied explicitly with `uv run alembic upgrade head`.

Set `STUDYHUB_ENVIRONMENT=production` to serve the built frontend from `../UI/dist` when
that directory contains `index.html`. Static assets are served directly and unmatched frontend
paths fall back to `index.html` for BrowserRouter, while API and documentation routes remain
reserved.

Study session responses include `duration_seconds`. Manual durations are derived from their
timestamps; Pomodoro durations contain elapsed active timer time and exclude pauses.

`GET /api/v1/dashboard/summary` uses UTC day boundaries by default. Pass
`timezone_offset_minutes` using the same sign convention as JavaScript's
`Date.getTimezoneOffset()` to calculate the caller's local day.

Run verification with:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```
