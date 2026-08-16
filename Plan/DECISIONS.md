# Decision Log

These entries reflect the implemented Phase 0/1 baseline and the still-approved future phase direction. Changes require coordinated updates to code, OpenAPI, UI aliases, tests, and affected planning documents.

| ID | Date | Decision | Consequence | Status |
| --- | --- | --- | --- | --- |
| D-001 | 2026-08-16 | Phase 0 Foundation and Phase 1 Focus loop are complete; later phases remain planned. | Current documents describe Phase 0/1 as implemented, not aspirational. | Accepted |
| D-002 | 2026-08-16 | The backend uses FastAPI, synchronous SQLAlchemy, Alembic, and SQLite behind repository/unit-of-work interfaces. | Domain/application code remains independent of ORM implementations. | Implemented |
| D-003 | 2026-08-16 | Every current application endpoint, including health, is below `/api/v1`; health is `GET /api/v1/health`. | There is no unversioned application health route. | Implemented |
| D-004 | 2026-08-16 | Current category and session collections return direct JSON arrays and support `include_deleted` without pagination. | Pagination is added before collection growth requires it, not documented before implementation. | Implemented |
| D-005 | 2026-08-16 | Application startup runs Alembic upgrade to head. | The process applies pending schema revisions before using the database. | Implemented |
| D-006 | 2026-08-16 | Development uses the Vite `/api` proxy; production FastAPI serves `UI/dist` with SPA fallback. | API/documentation paths remain reserved from frontend fallback. | Implemented |
| D-007 | 2026-08-16 | StudyHub remains localhost-only and has no authentication. | Remote or untrusted-network use requires a new security design. | Accepted |
| D-008 | 2026-08-16 | Generated OpenAPI components are consumed through aliases in `UI/src/api/contracts.ts`. | Transport changes update generated types and aliases with the backend schema. | Implemented |
| D-009 | 2026-08-16 | Category transport is `id`, `name`, nullable `color`, and timestamps. Name is 1-120 characters, color is 1-32 when present, and names are not unique. | Clients cannot assume category-name uniqueness or a required color. | Implemented |
| D-010 | 2026-08-16 | Category is optional on resources; the UI represents no category as `Unsorted`. | Category forms and filters always provide a no-category path. | Implemented |
| D-011 | 2026-08-16 | Current category and study-session deletion is soft, with explicit restore. | Default reads hide deleted records; active sessions cannot be deleted. | Implemented |
| D-012 | 2026-08-16 | Pomodoro settings use `focus_minutes`, `short_break_minutes`, `long_break_minutes`, and `long_break_every` with ranges 1-180, 1-60, 1-120, and 1-12. | Backend schemas, OpenAPI aliases, and UI forms use these exact names. | Implemented |
| D-013 | 2026-08-16 | Timers use `phase` and `state`; active reads return a Timer or null, expiry is reconciled before active reads/new starts, and same-terminal complete/cancel actions are idempotent. | Clients consume the direct nullable response and may safely retry matching terminal actions. | Implemented |
| D-014 | 2026-08-16 | Focus timers create `pomodoro` study sessions; breaks do not. Session status is `active`, `completed`, or `cancelled`. | Timer/session linkage is exposed through `StudySession.timer_id`. | Implemented |
| D-015 | 2026-08-16 | Manual sessions may remain active without `ended_at`; Pomodoro duration records actual active seconds excluding pauses and unused planned time. | Duration totals use persisted session duration rather than planned timer duration. | Implemented |
| D-016 | 2026-08-16 | Cancelled focus sessions remain audited as cancelled and are neither automatically soft-deleted nor counted as completed. | Cancellation history remains visible without inflating completed totals. | Implemented |
| D-017 | 2026-08-16 | Dashboard transport is `today_completed_focus_minutes`, `today_completed_session_count`, `active_timer`, and `recent_sessions`. Its offset follows JavaScript `getTimezoneOffset()`: `local = UTC - offset`. | Current clients must not expect period, category, review, or quiz fields. | Implemented |
| D-018 | 2026-08-16 | Application errors are `{error:{code,message}}`; FastAPI request validation uses its standard `detail` array. | No request IDs, error details arrays, or persistence-specific codes are promised. | Implemented |
| D-019 | 2026-08-16 | A resource has at most one optional category; future cards inherit their deck category. | Cards do not receive a separate category relationship. | Accepted |
| D-020 | 2026-08-16 | Future flashcard scheduling uses standard SM-2 with Again=1, Hard=3, Good=4, Easy=5 and minimum ease 1.3. | Scheduler tests will lock mapping, formula, and ease floor. | Planned |
| D-021 | 2026-08-16 | Notes store Markdown; Planner scope is tasks/agenda; Quizzes use MCQ auto-grading and written self-grading. | These remain bounded future-phase contracts. | Planned |
| D-022 | 2026-08-16 | Review sessions and quiz attempts will aggregate as independent activity sources rather than duplicate `study_sessions`. | Future totals combine disjoint sources. | Planned |
| D-023 | 2026-08-16 | The Solitude UI uses the approved palette, IBM Plex Sans, JetBrains Mono, 6px radii, and sparse layout. | Shipped and future screens use shared visual tokens. | Accepted |
| D-024 | 2026-08-16 | Verification uses backend unit/integration/API/migration tests with fake time and temporary file SQLite, plus frontend Vitest/RTL/MSW and live Playwright. | Test counts may grow; passing behavior and contracts are the gate. | Implemented |
| D-025 | 2026-08-16 | A later MCP adapter calls application services rather than HTTP routes or ORM repositories. | MCP remains unimplemented until service contracts are hardened. | Planned |
| D-026 | 2026-08-16 | Delivery order remains Foundation, Focus loop, Flashcards, Notes, Planner, Quizzes, then Hardening/MCP readiness. | Phases 2-6 remain planned in this order. | Accepted |
