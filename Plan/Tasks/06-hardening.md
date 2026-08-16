# Task 06: Hardening And MCP Readiness

## Handoff

- **Phase:** 6
- **Status:** Planned
- **Coordinator:** 5.6 Sol, owning architecture audit, accessibility/recovery UX, service-contract stabilization, and release gate
- **Backend lane:** Delegable in independently reviewable hardening slices; no broad feature rewrite
- **Dependencies:** Tasks 00-05 complete and all public/application contracts documented

## Objective

Make the local application recoverable, observable, accessible, migration-safe, and ready for a later MCP adapter without exposing MCP or weakening dependency boundaries.

## Scope

### Architecture And Contract Lane

- Audit actual imports and calls against `SAD.md`; remove controller/repository shortcuts before freezing service contracts.
- Inventory application-service commands/queries, inputs, outputs, errors, idempotency, and transaction boundaries suitable for non-HTTP invocation.
- Define a transport-neutral service conformance harness and a proof in-test adapter; do not publish MCP tools in this phase.
- Review local deployment documentation so loopback/no-auth limitations are unambiguous.
- Set measured performance/accessibility baselines from representative local data rather than arbitrary rewrites.

### Delegated Backend Lane

- Add structured local logs with operation/error codes while excluding note/card/answer content and other user payloads.
- Harden SQLite busy handling, transaction conflict translation, startup/migration failures, and database-path errors.
- Implement and test documented backup/restore around a consistent SQLite snapshot; never overwrite the only backup silently.
- Exercise migrations from every released revision with representative data and add metadata drift checks.
- Profile dashboard, due-card, note search, agenda, and quiz-history queries; add indexes only for measured plans.
- Verify application services can run through the proof adapter without FastAPI, Pydantic transport schemas, or ORM models crossing the boundary.

### UI Lane

- Complete keyboard, focus, screen-reader, zoom, reduced-motion, mobile, and contrast review for every shipped workflow.
- Add coherent recovery for disconnected server, `409`, `422`, `503`, failed startup/migration, and stale active-timer state.
- Verify all planned modules expose consistent loading, empty, filtered-empty, pending, failed, delete, and restore behavior.
- Remove dead navigation, placeholder copy, test-only controls, and accidental debug data.
- Measure production bundle and critical interaction/render paths; optimize only demonstrated bottlenecks.

## Contracts

- The localhost-only, no-auth boundary remains unchanged. No command may default to a non-loopback bind.
- Future MCP is a peer adapter to HTTP and calls application services only. It does not import controllers, SQLAlchemy mappings, or repository implementations.
- Service results and errors are transport-neutral. HTTP and proof-adapter mappings are tested separately.
- Logs contain IDs, operation names, durations, and stable codes where useful, but not user-authored content.
- Backup/restore preserves UUIDs, UTC timestamps, soft-delete state, relationships, attempt/review history, and current schema version.
- Hardening does not introduce alternate databases, asynchronous SQLAlchemy, a worker, accounts, or remote synchronization.

## Acceptance Criteria

- Full backend and frontend quality gates pass from a clean checkout with a migrated temporary database.
- Import/boundary checks prove application/domain code is independent of FastAPI, SQLAlchemy implementations, and MCP.
- The proof adapter invokes representative category, focus, note, planner, flashcard-review, and quiz services without HTTP.
- Backup followed by destructive test mutation and restore reproduces the original representative dataset and passes integrity checks.
- Every released migration fixture upgrades to head without data loss; schema drift check is clean.
- SQLite lock, unavailable path, malformed request, and stale timer conflicts return stable errors without raw internals.
- Critical screens have no serious automated accessibility findings and pass documented manual keyboard/screen-reader checks at 320px and 200% zoom.
- Representative query plans and UI measurements are recorded; any accepted regression has an explicit rationale.
- Production configuration and documentation state the local/no-auth security boundary.

## Out Of Scope

- Publishing MCP servers or tools, remote/network deployment, authentication, encryption/key management, multi-user support, cloud backup, telemetry services, database replacement, and unrelated redesign.

## Verification

Run the complete quality gate in `TEST_STRATEGY.md` from a clean setup. Also run migration-fixture upgrades, backup/restore integrity, boundary/conformance, representative query-plan, production bundle, desktop/mobile E2E, and accessibility checks. Record commands and measured results in the release evidence, not as unverifiable prose.

## Handoff Output

Each backend slice returns changed files, risk addressed, before/after evidence, tests and commands run, and any contract effect. The coordinator rejects opportunistic feature work and signs off only after the full cross-layer gate passes.
