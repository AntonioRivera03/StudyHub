# System Architecture Document

## Context

StudyHub is a local, single-user study application. Phase 0 and Phase 1 are implemented with a React browser client, FastAPI, synchronous SQLAlchemy, Alembic, and SQLite. The server is localhost-only and has no authentication.

```text
React UI -> /api/v1 HTTP -> FastAPI routes -> application services -> repository ports
                                                                      ^
                                                                      |
                                            SQLAlchemy repositories -> SQLite
```

## Components

### React UI

- Owns routing, presentation, interaction state, responsive behavior, and accessible feedback.
- Calls relative `/api/v1` paths and does not access persistence types.
- Uses generated OpenAPI components through stable aliases in `UI/src/api/contracts.ts`.
- During development, Vite proxies `/api` to the localhost FastAPI process.

### FastAPI HTTP Layer

- Mounts all implemented application routes, including health, below `/api/v1`.
- Owns request/schema validation, response serialization, HTTP status mapping, and OpenAPI generation.
- Maps application errors to `{ "error": { "code", "message" } }`; FastAPI request validation retains its standard `detail` array.
- Calls application services rather than issuing SQLAlchemy queries from routes.

### Application Services And Domain

- Application services own use-case orchestration, timer reconciliation, state transitions, transaction boundaries, and clock use.
- Services depend on repository/unit-of-work interfaces and an injectable UTC clock.
- Domain entities and repository ports do not depend on FastAPI or SQLAlchemy implementations.
- These services remain the intended invocation boundary for a later MCP adapter.

### Persistence

- Synchronous SQLAlchemy repositories implement domain repository ports.
- A unit of work scopes sessions and commits or rolls back service operations.
- SQLite foreign keys are enabled and Alembic owns schema evolution.
- Application startup runs `alembic upgrade head` before exposing the database-backed application state.

## Dependency Direction

```text
UI -> HTTP/OpenAPI contract
HTTP -> application -> domain
infrastructure -> application/domain ports
composition root -> concrete adapters
future MCP adapter -> application
```

HTTP routes and a future MCP adapter are peer adapters. MCP must not call HTTP routes, serialize ORM rows, or query repository implementations directly.

## Contract Boundary

- `API.md` is the human-readable current transport contract.
- FastAPI's generated OpenAPI is the machine-readable contract.
- `UI/src/api/generated.ts` contains generated components; `UI/src/api/contracts.ts` exposes aliases used by UI code.
- ORM records are not transport schemas.
- Current collection responses are direct JSON arrays. Pagination is deferred until collection growth requires it.

## Runtime And Delivery

### Development

- FastAPI runs on localhost, normally port 8000.
- Vite serves the React client and proxies `/api` to `http://127.0.0.1:8000`.
- Development CORS is limited to configured localhost Vite origins.

### Production

- FastAPI serves the built `UI/dist` files when the directory and `index.html` exist.
- Existing static files are returned directly.
- Unmatched frontend paths fall back to `UI/dist/index.html` for the React SPA router.
- API, OpenAPI, and documentation paths remain reserved and do not receive the SPA fallback.

## Security Boundary

- The supported server bind is loopback only. There is no authentication, authorization, account, tenancy, or cloud synchronization layer.
- The SQLite file is local user data; host access and file permissions are the current security boundary.
- Exposing StudyHub to another machine or untrusted network requires a new security design and is not supported by this architecture.

## Time And Timer Correctness

- Application services receive an injectable UTC clock.
- Persisted timestamps represent UTC instants and API timestamps are RFC3339.
- Running timer expiry is reconciled from `expected_end_at` before active reads and new starts; no background worker is required for correctness.
- Dashboard local-day boundaries use `timezone_offset_minutes` with JavaScript `getTimezoneOffset()` semantics: `local = UTC - offset`.

## Supported Shape

The current supported shape is one local FastAPI process, one SQLite database, and one browser UI. Multi-user operation, remote deployment, asynchronous SQLAlchemy, background workers, external databases, and offline synchronization remain out of scope.
