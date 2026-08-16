# Test Strategy

## Principles

- Test observable contracts and domain behavior rather than framework internals.
- Inject time and persistence location where determinism or isolation requires it.
- Tests never read or write the user's production SQLite database.
- Every defect fix adds the narrowest useful regression test at the owning layer.
- A phase passes when the current quality commands and all prior-phase tests pass; historical test counts are evidence, not frozen targets.

## Completed Phase 0/1 Verification

At Phase 1 completion, the suite contained 17 backend tests, 12 frontend component/unit tests, and one live Playwright flow. These counts may grow as coverage improves.

### Backend

- Unit tests use a fake clock for timer transitions, elapsed active duration, idempotent terminal actions, and expiry reconciliation.
- Integration/API tests use temporary file-backed SQLite databases and FastAPI dependency overrides.
- Startup/migration coverage runs Alembic to head and asserts the current schema can serve the health and Phase 1 API.
- API tests cover direct-array collection responses, `include_deleted`, category/settings validation, timer lifecycle, active manual sessions, soft delete/restore, cancelled-session auditing, and default-day dashboard totals.
- Tests assert current application error envelopes and FastAPI validation behavior separately.

### Frontend

- Vitest and React Testing Library cover API client behavior, focus/timer presentation, dashboard presentation, settings, and time helpers.
- MSW-backed component tests use the implemented API shapes and generated OpenAPI-derived types.
- OpenAPI components are generated into `UI/src/api/generated.ts` and consumed through aliases in `UI/src/api/contracts.ts`.
- The live Playwright flow starts an uncategorized focus session, pauses, resumes, completes it, and confirms the completed session on the dashboard through the real FastAPI/Vite stack.

## Backend Strategy

### Unit Tests

Run domain/application behavior without FastAPI or a real database.

- Timer transitions, active elapsed calculation, exact expiry boundaries, and invalid transitions.
- Dashboard local-day boundaries using JavaScript-style timezone offsets.
- SM-2 scheduling when Phase 2 begins.
- Planner agenda grouping and quiz grading in their planned phases.

Use a fake clock that can be set and advanced explicitly. Include exact boundary instants such as `now == expected_end_at`.

### Repository Integration Tests

Use a new temporary file-backed SQLite database per test or isolated test group. Do not rely only on `:memory:` because connection and transaction behavior differs from the deployed database.

- Run Alembic to head before exposing the fixture.
- Enable and assert SQLite foreign keys.
- Exercise synchronous SQLAlchemy sessions, commits, rollbacks, constraints, deterministic ordering, and soft-delete filters.
- Cover the one-active-timer constraint using separate sessions/connections when concurrency behavior changes.
- When review/quiz aggregation is added, prove child rows cannot multiply activity totals.

### API Tests

- Assert status codes, exact JSON shape, enums, UTC serialization, errors, and generated OpenAPI schemas.
- Cover happy paths, request validation, unknown/deleted IDs, conflicts, `include_deleted`, delete/restore, and transaction rollback.
- Current list assertions expect direct arrays. Add pagination tests only when pagination is introduced by an accepted contract.
- Exercise complete focus flows through application services and persistence, not controller mocks alone.

### Migration Tests

- Upgrade an empty database to head and inspect required tables, indexes, foreign keys, and defaults.
- Upgrade representative fixtures from each released schema revision after additional migrations exist.
- Verify IDs, timestamps, soft-delete state, and relationships survive upgrades.
- Test backup/restore rather than promising downgrade support unless downgrade becomes an explicit contract.

## Frontend Strategy

### Vitest, RTL, And MSW

- Test through roles, labels, visible text, and user events.
- Cover loading, empty, populated, pending, application-error, request-validation, and retry states.
- Use fake timers only for countdown display behavior; server reconciliation remains authoritative.
- Keep MSW handlers aligned with `API.md` and generated types.
- Test optional category selection with the `Unsorted` choice.

### Playwright

- Run against the real localhost FastAPI server, Vite proxy, and an isolated temporary SQLite file.
- Keep the completed Phase 1 focus loop as the baseline live flow.
- Add at least one real authoring/study critical path for each later phase.
- Add mobile, keyboard, and accessibility scenarios as those gates are implemented; do not claim unimplemented coverage.

## Quality Gate

For every change:

1. Backend formatting, lint, type checks, tests, migration checks, and relevant OpenAPI verification pass.
2. Frontend lint, type checks, component/unit tests, and production build pass.
3. Live Playwright critical paths pass for affected behavior.
4. Generated OpenAPI and `UI/src/api/contracts.ts` aliases remain compatible.
5. Planning documents are updated with intentional contract or lifecycle changes.

## Commands

```bash
# Backend
cd Server && uv run ruff check .
cd Server && uv run ruff format --check .
cd Server && uv run mypy app
cd Server && uv run pytest
cd Server && uv run alembic upgrade head

# Frontend
npm --prefix UI run lint
npm --prefix UI run typecheck
npm --prefix UI test -- --run
npm --prefix UI run build
npm --prefix UI run e2e
```

Generate UI API types from a running backend with `npm --prefix UI run openapi:generate` when transport schemas change.
