# Task 00: Foundation

## Handoff

- **Phase:** 0
- **Status:** Complete
- **Coordinator:** 5.6 Sol, architecture, HTTP contract, UI system, and integration ownership
- **Dependencies:** None

## Objective

Provide the runnable local backend/frontend foundation used by the completed Focus loop and later phase handoffs.

## Delivered Scope

### Backend And Architecture

- FastAPI application with all application routes below `/api/v1`, including `GET /api/v1/health`.
- Synchronous SQLAlchemy, repository/unit-of-work interfaces, SQLite foreign-key configuration, and Alembic.
- Application startup runs Alembic upgrade to head before database-backed requests are served.
- Localhost-oriented configuration and development CORS for configured Vite origins, with no authentication surface.
- Production FastAPI serving for `UI/dist`, direct static files, and SPA fallback while reserving API/OpenAPI/documentation paths.
- Application error mapping to `{error:{code,message}}`; FastAPI request validation retains its standard `detail` array.
- Injectable clock and temporary database overrides for deterministic tests.

### UI And Contract

- React/Vite application shell using the Solitude visual tokens and responsive navigation.
- Vite development proxy from `/api` to the localhost FastAPI process.
- Shared API client rooted at `/api/v1`.
- OpenAPI-generated components in `UI/src/api/generated.ts`, consumed through stable aliases in `UI/src/api/contracts.ts`.
- Vitest/RTL/MSW and Playwright harnesses plus lint, typecheck, and production-build commands.

## Implemented Contracts

- Architecture and deployment: `SAD.md`.
- HTTP prefix, errors, and direct-array collection convention: `API.md`.
- Persistence and timestamp rules: `DATA_MODEL.md`.
- Tokens and responsive/accessibility behavior: `UI_DESIGN.md`.
- Verification layers and commands: `TEST_STRATEGY.md`.
- Phase 1 does not implement pagination. It must be added by a later accepted contract before collection growth requires it.

## Completion Criteria Met

- `GET /api/v1/health` returns `200 {"status":"ok"}` and is present in generated OpenAPI.
- Startup applies Alembic head to an empty temporary file-backed SQLite database.
- SQLite foreign keys and the Phase 1 schema are covered by integration tests.
- The server remains localhost/no-auth and development API traffic works through Vite's proxy.
- A production build can be served by FastAPI with SPA fallback.
- Generated OpenAPI components back the UI contract aliases.
- Backend and frontend quality commands pass for the completed baseline.

## Out Of Scope

- Authentication, remote deployment, cloud synchronization, external databases, asynchronous SQLAlchemy, and background workers.
- Flashcards, Notes, Planner, Quizzes, and MCP tools.
- Pagination before measured collection growth requires it.

## Verification

```bash
cd Server && uv run ruff check .
cd Server && uv run ruff format --check .
cd Server && uv run mypy app
cd Server && uv run pytest
cd Server && uv run alembic upgrade head
npm --prefix UI run lint
npm --prefix UI run typecheck
npm --prefix UI test -- --run
npm --prefix UI run build
npm --prefix UI run e2e
```

Future model handoffs must preserve the route prefix, startup migration, localhost security boundary, production SPA behavior, and generated OpenAPI alias boundary unless an explicit replacement decision is accepted.
