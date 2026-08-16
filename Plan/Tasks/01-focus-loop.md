# Task 01: Focus Loop

## Handoff

- **Phase:** 1
- **Status:** Complete
- **Coordinator:** 5.6 Sol, contract integrity, timer UX, responsive UI, and integration ownership
- **Dependencies:** Completed Task 00 foundation

## Objective

Deliver the local focus workflow: optional organization by category, Pomodoro settings, one reliable active timer, auditable study history, and a current-local-day dashboard.

## Delivered Scope

### Backend

- Category list/create/get/patch/delete/restore with nullable color and optional resource assignment.
- Pomodoro settings get/patch using `focus_minutes`, `short_break_minutes`, `long_break_minutes`, and `long_break_every`.
- Timer active/start/pause/resume/complete/cancel using `phase` and `state`.
- One running-or-paused timer, with natural expiry reconciled before active reads and new starts.
- Focus start creates an active linked `pomodoro` session; break starts create none.
- Complete records actual active focus seconds as a completed session. Cancel records actual active seconds as an audited cancelled session without soft-deleting it.
- Manual sessions can be active without `ended_at` and completed by PATCH. Active sessions cannot be deleted.
- Category and session list responses are direct arrays with `include_deleted` and no pagination.
- Dashboard summary returns the exact implemented fields documented in `API.md`.

### UI

- Dashboard, Focus, Sessions, Categories, and Pomodoro Settings workflows.
- Running countdown derived from `expected_end_at`, with the backend authoritative after lifecycle actions and recovery.
- Optional category selection represented by `Unsorted` and sent as `category_id: null`.
- Deleted category/session views and restore actions.
- Current generated OpenAPI schemas consumed through UI aliases.

## Implemented Contracts

- Routes and transport fields: `API.md`.
- Required enums: timer phase `focus|short_break|long_break`; timer state `running|paused|completed|cancelled`; session source `manual|pomodoro`; session status `active|completed|cancelled`.
- `GET /api/v1/timer/active` returns a Timer directly or JSON null.
- Completing an already completed timer and cancelling an already cancelled timer are idempotent.
- Pomodoro session duration excludes pauses and unused planned timer time.
- Cancelled focus sessions are retained, not soft-deleted, and excluded from completed totals.
- Dashboard offset follows JavaScript `getTimezoneOffset()`: `local = UTC - offset`.
- Current application errors contain only `code` and `message`; request-schema errors use FastAPI's `detail` array.

## Completion Criteria Met

- Focus start creates one timer and one linked Pomodoro session atomically; break start creates no session.
- The SQLite constraint and service checks prevent more than one active timer.
- Fake-clock tests cover pause/resume, elapsed active duration, natural expiry, new-start reconciliation, terminal action behavior, and early completion.
- Manual active/completed transitions, soft delete/restore, and active-delete conflicts pass API tests.
- Category validation, nullable color, optional assignment, delete/restore, and settings ranges pass API tests without a name-uniqueness assumption.
- Dashboard tests verify completed Pomodoro minutes, all completed-session counts, reconciled active timer, recent sessions, and the default UTC day; the API contract fixes the JavaScript timezone-offset sign for broader boundary coverage.
- UI component/unit tests cover the current contract; the live Playwright flow completes an Unsorted focus session through pause/resume and confirms it on the dashboard.
- Completion verification included 17 backend tests, 12 frontend component/unit tests, and one live Playwright flow. Passing the evolving suite, not preserving these counts, is the ongoing gate.

## Out Of Scope

- Pagination, server-side category/session filtering beyond `include_deleted`, automatic Pomodoro cycle advancement, notifications, and operating-system integration.
- Flashcards, Notes, Planner, Quizzes, MCP, authentication, remote access, and cloud synchronization.
- Review or quiz activity fields in the current dashboard response.

## Verification

Run the complete commands in `TEST_STRATEGY.md`. Backend tests own lifecycle edge cases and dashboard arithmetic; the live Playwright test owns the real browser/API baseline focus flow.

Future changes must update `API.md`, generated OpenAPI, `UI/src/api/contracts.ts`, tests, and this completion record together if they alter Phase 1 behavior.
