# API Contract

Phase 0 and Phase 1 are implemented. This document describes the current HTTP contract. Groups under **Planned APIs** are not implemented.

## Conventions

- Every application endpoint, including health, is under `/api/v1`.
- JSON fields and query parameters use `snake_case`.
- Public IDs are UUID strings.
- Instants are UTC RFC3339 values. Input timestamps must include an offset and are normalized to UTC.
- Durations are whole seconds unless a field is explicitly named in minutes.
- Successful create operations return `201`; reads, updates, actions, and restores return `200`; deletes return `204`.
- Category and session reads hide soft-deleted records unless `include_deleted=true` is supported and supplied.
- Current collection endpoints return JSON arrays directly. Phase 1 has no `limit`, cursor, pagination envelope, or total count. Pagination will be introduced before collection growth makes it necessary.
- FastAPI generates OpenAPI from the transport schemas. The generated components are consumed through aliases in `UI/src/api/contracts.ts`.

## Errors

Application errors use only `code` and `message`:

```json
{
  "error": {
    "code": "conflict",
    "message": "Another timer is already active"
  }
}
```

Current application error codes are `not_found` (`404`), `conflict` (`409`), and `validation_error` (`422`). FastAPI request/schema validation retains its standard `422` response with a top-level `detail` array. Framework errors such as unmatched routes may also use FastAPI's standard `detail` response. No request ID, application `details` array, uniqueness code, or persistence-specific code is part of the current contract.

## Schemas

### Category

```json
{
  "id": "27f33332-2df3-48e6-bef0-0cf0bb4d28ae",
  "name": "Mathematics",
  "color": "#3366ff",
  "created_at": "2026-08-16T14:30:00Z",
  "updated_at": "2026-08-16T14:30:00Z",
  "deleted_at": null
}
```

- `name` is trimmed and has 1-120 characters.
- `color` is nullable. A supplied value is trimmed and has 1-32 characters.
- Category names are not required to be unique.

### PomodoroSettings

```json
{
  "focus_minutes": 25,
  "short_break_minutes": 5,
  "long_break_minutes": 15,
  "long_break_every": 4,
  "created_at": "2026-08-16T14:30:00Z",
  "updated_at": "2026-08-16T14:30:00Z"
}
```

Ranges are `focus_minutes` 1-180, `short_break_minutes` 1-60, `long_break_minutes` 1-120, and `long_break_every` 1-12. Defaults are 25, 5, 15, and 4.

### Timer

```json
{
  "id": "21ee3114-18d7-438a-91b7-f64fc59fef34",
  "phase": "focus",
  "state": "running",
  "category_id": "27f33332-2df3-48e6-bef0-0cf0bb4d28ae",
  "title": "Calculus review",
  "duration_seconds": 1500,
  "remaining_seconds": 1500,
  "started_at": "2026-08-16T14:30:00Z",
  "expected_end_at": "2026-08-16T14:55:00Z",
  "paused_at": null,
  "completed_at": null,
  "cancelled_at": null,
  "created_at": "2026-08-16T14:30:00Z",
  "updated_at": "2026-08-16T14:30:00Z"
}
```

- `phase` is `focus`, `short_break`, or `long_break`.
- `state` is `running`, `paused`, `completed`, or `cancelled`.
- `category_id` and `title` are nullable and are accepted only for focus starts.
- `duration_seconds` is the planned duration copied from settings. `remaining_seconds` is persisted at lifecycle transitions; clients use `expected_end_at` for a running display countdown.

### StudySession

```json
{
  "id": "61496c22-feaa-4807-810f-fea21dca093b",
  "title": "Calculus review",
  "category_id": "27f33332-2df3-48e6-bef0-0cf0bb4d28ae",
  "started_at": "2026-08-16T14:30:00Z",
  "ended_at": "2026-08-16T14:45:00Z",
  "duration_seconds": 900,
  "notes": null,
  "source": "pomodoro",
  "status": "completed",
  "timer_id": "21ee3114-18d7-438a-91b7-f64fc59fef34",
  "created_at": "2026-08-16T14:30:00Z",
  "updated_at": "2026-08-16T14:45:00Z",
  "deleted_at": null
}
```

- `source` is `manual` or `pomodoro`; `status` is `active`, `completed`, or `cancelled`.
- `category_id`, `ended_at`, `notes`, and `timer_id` are nullable.
- `source`, `status`, `timer_id`, and `duration_seconds` are server-managed.

## Implemented Endpoints

### Health

#### `GET /api/v1/health`

Returns `200`:

```json
{"status": "ok"}
```

### Categories

#### `GET /api/v1/categories`

Accepts `include_deleted=false`. Returns `200` with a `Category[]` directly. There is no pagination.

#### `POST /api/v1/categories`

```json
{"name": "Mathematics", "color": "#3366ff"}
```

`name` is required; `color` is optional and nullable. Returns `201` with `Category`. Duplicate names are permitted.

#### `GET /api/v1/categories/{category_id}`

Accepts `include_deleted=false`. Returns `Category` or `404`.

#### `PATCH /api/v1/categories/{category_id}`

Accepts optional `name` and `color`. Explicit `color: null` clears the color; `name` cannot be null. Returns the updated `Category`.

#### `DELETE /api/v1/categories/{category_id}`

Soft-deletes an active category and returns `204`. It does not delete related resources.

#### `POST /api/v1/categories/{category_id}/restore`

Restores a deleted category and returns `200` with `Category`. Restoring a category that is not deleted returns `409`.

### Pomodoro Settings

#### `GET /api/v1/settings/pomodoro`

Returns the singleton `PomodoroSettings`, creating defaults when needed.

#### `PATCH /api/v1/settings/pomodoro`

Accepts any supplied settings fields using the documented ranges and returns the complete `PomodoroSettings`. Changes affect subsequently started timers, not an existing timer.

### Timer

Only one timer may be `running` or `paused` at a time. A naturally expired running timer is reconciled before active-timer reads and before a new start.

#### `GET /api/v1/timer/active`

Returns a `Timer` directly when one is running or paused, or JSON `null` when none remains active. There is no `{ "timer": ... }` wrapper.

#### `POST /api/v1/timer/start`

```json
{
  "phase": "focus",
  "category_id": "27f33332-2df3-48e6-bef0-0cf0bb4d28ae",
  "title": "Calculus review"
}
```

- `phase` is required.
- `category_id` and `title` are optional for focus and invalid for breaks.
- `title` has 1-200 characters when supplied. Category must identify an active category.
- Duration comes from current Pomodoro settings.
- If focus title is omitted, the Timer retains `title: null` and the linked session uses `Focus session`.

Returns `201` with `Timer`. Focus start also creates one active `pomodoro` study session linked by `StudySession.timer_id`. Break start creates no session. Starting while a non-expired timer is active returns `409`.

#### `POST /api/v1/timer/{timer_id}/pause`

Pauses a running timer and persists its remaining whole seconds. Returns `200` with `Timer`; an invalid state returns `409`.

#### `POST /api/v1/timer/{timer_id}/resume`

Resumes a paused timer and recalculates `expected_end_at`. Returns `200` with `Timer`; an invalid state returns `409`.

#### `POST /api/v1/timer/{timer_id}/complete`

Completes a running or paused timer and closes a linked focus session as `completed`. Repeating completion on an already completed timer is idempotent and returns that timer with `200`. Completing a cancelled timer returns `409`.

#### `POST /api/v1/timer/{timer_id}/cancel`

Cancels a running or paused timer and closes a linked focus session as `cancelled`. The cancelled session remains as an audit record and is not soft-deleted. Repeating cancellation on an already cancelled timer is idempotent and returns that timer with `200`. Cancelling a completed timer returns `409`.

Timer action endpoints take no request body.

### Study Sessions

#### `GET /api/v1/sessions`

Accepts `include_deleted=false`. Returns `200` with a `StudySession[]` directly, newest `started_at` first. There is no pagination or additional filtering in Phase 1.

#### `POST /api/v1/sessions`

```json
{
  "title": "Read chapter 4",
  "category_id": null,
  "started_at": "2026-08-16T12:00:00Z",
  "ended_at": null,
  "notes": "Optional notes"
}
```

- `title` and `started_at` are required. Title has 1-200 characters; notes has at most 10,000 characters.
- `category_id`, `ended_at`, and `notes` are optional and nullable.
- Omitting `ended_at` creates an `active` manual session with zero duration. A later PATCH can supply `ended_at` to complete it.
- When supplied, `ended_at` must be later than `started_at`; duration is derived by the server.

Returns `201` with a manual `StudySession`.

#### `GET /api/v1/sessions/{session_id}`

Accepts `include_deleted=false`. Returns `StudySession` or `404`.

#### `PATCH /api/v1/sessions/{session_id}`

Accepts `title`, `category_id`, `started_at`, `ended_at`, and `notes`. Explicit null clears nullable fields. Manual session duration and active/completed status are recalculated from timestamps. Pomodoro `started_at` and `ended_at` are timer-managed and cannot be patched; metadata and notes may be updated.

#### `DELETE /api/v1/sessions/{session_id}`

Soft-deletes a completed or cancelled session and returns `204`. An active session cannot be deleted and returns `409`.

#### `POST /api/v1/sessions/{session_id}/restore`

Restores a soft-deleted session and returns `StudySession`. Restoring a session that is not deleted returns `409`.

### Dashboard

#### `GET /api/v1/dashboard/summary`

Accepts `timezone_offset_minutes`, an integer from -840 through 840 with default `0`. It follows JavaScript `Date.getTimezoneOffset()`:

```text
local time = UTC - timezone_offset_minutes
```

Response:

```json
{
  "today_completed_focus_minutes": 25,
  "today_completed_session_count": 2,
  "active_timer": null,
  "recent_sessions": []
}
```

- The local day is calculated from the server clock and supplied offset.
- `today_completed_focus_minutes` sums persisted `duration_seconds` for completed Pomodoro sessions whose `ended_at` falls in that local day, then exposes whole minutes.
- `today_completed_session_count` counts all completed manual and Pomodoro sessions in that local day.
- Cancelled, active, and soft-deleted sessions do not contribute to completed totals.
- `active_timer` is the reconciled `Timer` or null.
- `recent_sessions` contains up to five non-deleted sessions, newest first.

## Planned APIs

These groups remain planned and must not be mounted as placeholder success endpoints:

- **Phase 2:** `/api/v1/decks`, `/api/v1/cards`, `/api/v1/reviews`, and due-card queries.
- **Phase 3:** `/api/v1/notes`, including search and soft delete/restore.
- **Phase 4:** `/api/v1/planner/tasks` and `/api/v1/planner/agenda`.
- **Phase 5:** `/api/v1/quizzes`, question/option authoring, attempts, answers, submission, and written self-grading.
- **Phase 6:** no MCP-over-HTTP namespace. MCP remains a separate future adapter over application services.

Each planned group requires an accepted endpoint contract before implementation. Future review and quiz activity must extend dashboard reporting without creating duplicate study sessions.
