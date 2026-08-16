# Roadmap

Phases are sequential unless a task packet explicitly identifies safe parallel work. Phase 0 and Phase 1 are complete; all other phases are planned.

## Phase 0: Foundation

**Status: Complete**

**Delivered scope**

- Establish the FastAPI, synchronous SQLAlchemy, Alembic, SQLite, React, and test scaffolds.
- Enforce controller, application service, repository, and persistence boundaries.
- Add configuration for a localhost-only single-user process and database path.
- Establish UUID, UTC timestamp, current error, direct-array collection, OpenAPI, and soft-delete conventions.
- Build the responsive Solitude application shell and shared request/error primitives.
- Run Alembic upgrade to head during application startup.
- Serve `UI/dist` with SPA fallback in production and use the Vite `/api` proxy in development.

**Completion evidence**

- `GET /api/v1/health`, startup migration, frontend shell, and verification commands pass.
- SQLite foreign keys are enabled and a temporary file database is usable in integration tests.
- OpenAPI components are generated and consumed through aliases in `UI/src/api/contracts.ts`.
- Production static serving and SPA fallback are implemented without capturing API/documentation paths.
- No non-local bind or authentication surface is introduced.

## Phase 1: Focus Loop

**Status: Complete**

**Delivered scope**

- Categories, Pomodoro settings, one active timer, timer reconciliation, study sessions, and dashboard summary.
- Focus, short-break, and long-break timers with explicit lifecycle actions.
- Focus timers create and link a study session; break timers never do.
- Phase 1 screens: Dashboard, Focus, Sessions, Categories, and Pomodoro settings.
- Optional categories are represented as Unsorted in the UI.
- Category and session lists support `include_deleted` and return direct arrays without pagination.

**Completion evidence**

- Implemented Phase 1 endpoints and persistence behavior pass backend unit/integration tests.
- Timer transitions, one-active enforcement, pause/resume accounting, and expired-timer reconciliation pass fake-clock tests.
- Delete/restore behavior, audited cancellation, active manual sessions, and default-day dashboard totals pass API tests; the JavaScript offset sign is part of the implemented contract.
- The frontend completes the focus loop on desktop and mobile and exposes loading, empty, error, and recovery states.
- Generated OpenAPI components back the UI contract aliases.
- Completion verification included 17 backend tests, 12 frontend component/unit tests, and one live Playwright flow. Future gates require all current tests to pass rather than preserving these counts.

## Phase 2: Flashcards

**Scope**

- Deck and card authoring, category assignment at deck level, due-card selection, review sessions, and review events.
- SM-2 scheduling using the locked rating mapping and minimum ease factor.
- Dashboard aggregation from review sessions without creating study-session duplicates.

**Exit criteria**

- Cards inherit category from their deck and cannot store a separate category.
- Deterministic scheduler tests cover Again, Hard, Good, Easy, interval progression, and ease floor.
- Interrupted and completed review sessions preserve consistent review history and duration.
- Deck/card CRUD, review flow, soft delete/restore, and dashboard totals pass backend and frontend tests.

## Phase 3: Notes

**Scope**

- Markdown note create, edit, preview, browse, search, category assignment, and soft delete/restore.
- Safe Markdown rendering; raw HTML is not trusted.

**Exit criteria**

- Markdown source round-trips without lossy transformation.
- Rendering is sanitized and keyboard-accessible.
- Search, category filters, autosave or explicit-save behavior, conflict/error recovery, deletion, and restore are tested.

## Phase 4: Planner

**Scope**

- Planner tasks, due/scheduled times, completion, priority, category assignment, and agenda views.
- Day and upcoming agenda groupings use an explicit client-supplied UTC offset.

**Exit criteria**

- Task CRUD, complete/reopen, soft delete/restore, filters, and deterministic agenda boundaries pass tests.
- Overdue, today, upcoming, completed, and empty states are distinguishable without color alone.
- Desktop and mobile agenda workflows meet accessibility requirements.

## Phase 5: Quizzes

**Scope**

- Quiz and question authoring, MCQ automatic grading, written-answer self-grading, attempts, answers, and results.
- Dashboard aggregation from quiz attempts without creating study-session duplicates.

**Exit criteria**

- MCQ scoring is deterministic and written questions require an explicit self-grade before finalization.
- In-progress attempts can resume without duplicate answers or duplicate totals.
- Quiz CRUD, attempt lifecycle, results, soft delete/restore, and dashboard aggregation pass tests.

## Phase 6: Hardening And MCP Readiness

**Scope**

- Performance, accessibility, recovery, observability, migration, backup/restore, and packaging hardening.
- Stabilize application-service commands and queries for a later MCP adapter.
- Define MCP tool schemas only after service contracts stabilize; do not expose MCP in earlier phases.

**Exit criteria**

- Full backend, frontend, E2E, migration, accessibility, and OpenAPI checks pass as one quality gate.
- Upgrade, backup, restore, corrupted-input, and failed-write paths have documented and tested recovery.
- The server remains localhost-only and no-auth; deployment documentation states this security boundary.
- A proof adapter can call application services without importing HTTP controllers or SQLAlchemy models.
