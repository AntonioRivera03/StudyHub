# API Contract

Phase 0 through Phase 2 are implemented. Groups under **Planned APIs** are not implemented.

## Conventions

- Every application endpoint, including health, is under `/api/v1`.
- JSON fields and query parameters use `snake_case`.
- Public IDs are UUID strings.
- Instants are UTC RFC3339 values. Input timestamps must include an offset and are normalized to UTC.
- Durations are whole seconds unless a field is explicitly named in minutes.
- Successful create operations return `201`; reads, updates, actions, and restores return `200`; deletes return `204`.
- Category, session, deck, card, and review reads hide soft-deleted records unless `include_deleted=true` is supported and supplied.
- Current collection endpoints return JSON arrays directly. Phases 1/2 have no `limit`, cursor, pagination envelope, or total count. Pagination will be introduced before collection growth makes it necessary.
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
  "study_flow_session_id": null,
  "study_flow_segment_index": null,
  "study_flow_confirmed_at": null,
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
- StudyFlow timers include their shared session ID and zero-based segment index. `study_flow_confirmed_at` records the explicit confirmation required after natural expiry.
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

- `source` is `manual`, `pomodoro`, or `study_flow`; `status` is `active`, `completed`, or `cancelled`.
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
  "title": "Calculus review",
  "study_flow_session_id": null,
  "study_flow_segment_index": 0
}
```

- `phase` is required.
- `category_id` and `title` are optional for focus and invalid for breaks.
- `title` has 1-200 characters when supplied. Category must identify an active category.
- Supplying `study_flow_segment_index` starts a StudyFlow segment. Segment zero creates the shared `study_flow` session; later segments require its returned `study_flow_session_id`. The server enforces the fixed six-segment phase order.
- Duration comes from current Pomodoro settings.
- If focus title is omitted, the Timer retains `title: null` and the linked session uses `Focus session`.

Returns `201` with `Timer`. A standalone focus start creates one active `pomodoro` study session linked by `StudySession.timer_id`. A StudyFlow start links every focus and break timer to one `study_flow` session. Standalone break starts create no session. Starting while a non-expired timer is active returns `409`.

#### `GET /api/v1/timer/study-flow/active`

Returns the active StudyFlow session ID, title/category, session status, current segment index, confirmation state, and active timer, or JSON `null`. Naturally expired segments remain current with `awaiting_confirmation: true` until confirmed.

#### `GET /api/v1/timer/study-flow/{session_id}`

Returns persisted StudyFlow state for recovery, including completed and cancelled pipelines. Returns `404` when the ID is not a StudyFlow session.

#### `POST /api/v1/timer/study-flow/{session_id}/segments/{segment_index}/confirm`

Confirms a naturally completed StudyFlow segment and unlocks the next segment. Returns the updated StudyFlow state. A segment that is not awaiting confirmation returns `409`.

#### `POST /api/v1/timer/{timer_id}/pause`

Pauses a running timer and persists its remaining whole seconds. Returns `200` with `Timer`; an invalid state returns `409`.

#### `POST /api/v1/timer/{timer_id}/resume`

Resumes a paused timer and recalculates `expected_end_at`. Returns `200` with `Timer`; an invalid state returns `409`.

#### `POST /api/v1/timer/{timer_id}/complete`

Completes a running or paused timer and closes a linked standalone focus session as `completed`. StudyFlow focus time accumulates on the shared session; completing the final long break closes that session at the timer completion instant. Repeating completion on an already completed timer is idempotent and returns that timer with `200`. Completing a cancelled timer returns `409`.

#### `POST /api/v1/timer/{timer_id}/cancel`

Cancels a running or paused timer and closes its standalone focus or StudyFlow session as `cancelled`. An already expired running timer is completed instead of cancelled. The cancelled session remains as an audit record and is not soft-deleted. Repeating cancellation on an already cancelled timer is idempotent and returns that timer with `200`. Cancelling a completed timer returns `409`.

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
  "today_completed_review_minutes": 12,
  "today_completed_review_session_count": 1,
  "today_reviewed_card_count": 7,
  "active_timer": null,
  "recent_sessions": []
}
```

- The local day is calculated from the server clock and supplied offset.
- `today_completed_focus_minutes` sums persisted `duration_seconds` for completed Pomodoro and StudyFlow sessions whose `ended_at` falls in that local day, then exposes whole minutes.
- `today_completed_session_count` counts all completed manual and Pomodoro sessions in that local day.
- Review totals are source-separated and documented under the Phase 2 dashboard extension below.
- Cancelled, active, and soft-deleted sessions do not contribute to completed totals.
- `active_timer` is the reconciled `Timer` or null.
- `recent_sessions` contains up to five non-deleted sessions, newest first.

## Implemented Phase 2 APIs

### Flashcards

Phase 2 collections continue to return direct arrays without pagination. Deck and card scheduling reads use the server clock. All deck/card mutations require an active parent resource unless a restore rule below says otherwise.

#### Schemas

`FlashcardDeck` contains:

```json
{
  "id": "46592503-cc8e-4dba-924a-88b208a4800e",
  "name": "Calculus identities",
  "description": "Core derivatives and integrals",
  "category_id": "27f33332-2df3-48e6-bef0-0cf0bb4d28ae",
  "active_card_count": 24,
  "due_card_count": 7,
  "created_at": "2026-08-17T14:30:00Z",
  "updated_at": "2026-08-17T14:30:00Z",
  "deleted_at": null
}
```

- `name` is trimmed and has 1-160 characters. `description` is nullable and has at most 2,000 characters.
- `category_id` is nullable and must identify an active category when assigned. Cards inherit this value and never accept or store their own category.
- `active_card_count` excludes deleted cards. `due_card_count` additionally requires `due_at <=` the server clock and is zero for a deleted deck.

`Flashcard` contains:

```json
{
  "id": "913cc4ac-d7d4-477d-90cf-a43ce9c37d05",
  "deck_id": "46592503-cc8e-4dba-924a-88b208a4800e",
  "front_markdown": "What is $d(x^2)/dx$?",
  "back_markdown": "$2x$",
  "position": 0,
  "schedule": {
    "repetitions": 0,
    "interval_days": 0,
    "ease_factor": 2.5,
    "due_at": "2026-08-17T14:30:00Z",
    "last_reviewed_at": null
  },
  "created_at": "2026-08-17T14:30:00Z",
  "updated_at": "2026-08-17T14:30:00Z",
  "deleted_at": null
}
```

- `front_markdown` and `back_markdown` preserve source exactly after requiring at least one non-whitespace character and at most 20,000 characters each.
- `position` is a non-negative integer. Card ordering is `position`, then `id`.
- `schedule` is server-managed. New cards start with zero repetitions, zero interval days, ease 2.5, `due_at` equal to creation time, and no last review.

`ReviewSession` contains `id`, `deck_id`, nullable `category_id_snapshot`, `status`, `started_at`, nullable `ended_at`, `duration_seconds`, common timestamps, and nullable `deleted_at`. `status` is `in_progress`, `completed`, or `abandoned`. The category snapshot is copied when review starts and never changes.

`ReviewEvent` contains:

```json
{
  "id": "9b3bbdfa-33af-414d-a00d-283d145f5c20",
  "command_id": "02438e47-43f2-44a5-9c2f-8c94a530c435",
  "review_session_id": "fba74e5e-5f83-4c30-ab6c-82fa218065c3",
  "card_id": "913cc4ac-d7d4-477d-90cf-a43ce9c37d05",
  "sequence": 1,
  "rating": "good",
  "quality": 4,
  "reviewed_at": "2026-08-17T14:31:00Z",
  "previous_schedule": {
    "repetitions": 0,
    "interval_days": 0,
    "ease_factor": 2.5,
    "due_at": "2026-08-17T14:30:00Z",
    "last_reviewed_at": null
  },
  "new_schedule": {
    "repetitions": 1,
    "interval_days": 1,
    "ease_factor": 2.5,
    "due_at": "2026-08-18T14:31:00Z",
    "last_reviewed_at": "2026-08-17T14:31:00Z"
  }
}
```

Review events are immutable. `command_id` is a client-generated UUID used for retry safety. `sequence` is server-generated, starts at 1, and increases within the session.

`ReviewProgress` contains:

```json
{
  "session": {},
  "reviewed_card_count": 3,
  "remaining_due_card_count": 4,
  "next_card": null
}
```

`session` is a `ReviewSession`; `next_card` is the next `Flashcard` or null. The next card and remaining count exclude deleted cards/decks and cards already reviewed in that session. Selection requires `due_at <=` the server clock and orders by `due_at`, then `position`, then `id`.

`ReviewRatingResult` contains `event: ReviewEvent` and `progress: ReviewProgress`.

#### Decks

##### `GET /api/v1/decks`

Accepts `include_deleted=false`. Returns `FlashcardDeck[]`, ordered by `created_at`, then `id`.

##### `POST /api/v1/decks`

Accepts `name`, optional nullable `description`, and optional nullable `category_id`. Returns `201` with `FlashcardDeck`.

##### `GET /api/v1/decks/{deck_id}`

Accepts `include_deleted=false`. Returns `FlashcardDeck` or `404`.

##### `PATCH /api/v1/decks/{deck_id}`

Accepts optional `name`, `description`, and `category_id`. Explicit null clears nullable fields; `name` cannot be null. Returns the updated active deck.

##### `DELETE /api/v1/decks/{deck_id}`

Soft-deletes an active deck and returns `204`. Its cards are not individually deleted, but the deck and cards are excluded from normal and due reads. A deck with an in-progress review session returns `409`.

##### `POST /api/v1/decks/{deck_id}/restore`

Restores a deleted deck and returns it. Existing non-deleted cards become visible and due-eligible again. A retained category reference may point to a now-deleted category; it remains historical until changed or cleared. Restoring an active deck returns `409`.

#### Cards

##### `GET /api/v1/decks/{deck_id}/cards`

Accepts `include_deleted=false`. Returns the deck's `Flashcard[]` ordered by `position`, then `id`. `include_deleted=true` also permits reading cards under a deleted deck.

##### `POST /api/v1/decks/{deck_id}/cards`

Accepts required `front_markdown` and `back_markdown` plus optional `position`. When omitted, position is one greater than the current maximum, or zero for the first card. Returns `201` with `Flashcard`. Unknown fields, including `category_id`, return FastAPI `422` validation. A deck with an in-progress review session returns `409` because adding a card would invalidate the review queue.

##### `GET /api/v1/cards/{card_id}`

Accepts `include_deleted=false`. Returns `Flashcard` only when both card and deck are visible under the requested mode.

##### `PATCH /api/v1/cards/{card_id}`

Accepts optional `front_markdown`, `back_markdown`, and `position`. Required fields cannot be null. Scheduling and category fields are rejected as unknown fields. Returns the updated active card. A card in a deck with an in-progress review session returns `409`.

##### `DELETE /api/v1/cards/{card_id}`

Soft-deletes an active card and returns `204`. Existing review events remain immutable. A card in a deck with an in-progress review session returns `409` because deletion would invalidate the review queue.

##### `POST /api/v1/cards/{card_id}/restore`

Restores a deleted card and returns it. Its parent deck must be active; otherwise the request returns `409`. Restoring an active card returns `409`. A card in a deck with an in-progress review session returns `409` because restoring would invalidate the review queue.

##### `GET /api/v1/decks/{deck_id}/due-cards`

Returns all currently due active cards directly, ordered by `due_at`, then `position`, then `id`. Deleted decks return `404`.

#### Reviews

Only one review session may be in progress at a time. Starting another returns `409`; the client resumes or abandons the existing session first.

##### `GET /api/v1/reviews`

Accepts `include_deleted=false`. Returns `ReviewSession[]`, newest `started_at` first.

##### `POST /api/v1/reviews`

Accepts `{ "deck_id": "..." }`. The active deck must have at least one due card. Returns `201` with `ReviewProgress`. It snapshots the deck category and starts an in-progress review. No study session is created.

##### `GET /api/v1/reviews/active`

Returns the in-progress `ReviewProgress` or JSON null.

##### `GET /api/v1/reviews/{review_session_id}`

Accepts `include_deleted=false`. Returns current `ReviewProgress`. Reading this endpoint is the resume operation; review position and event history are not reset.

##### `GET /api/v1/reviews/{review_session_id}/next`

Returns the current next `Flashcard` or JSON null. Terminal or deleted sessions return `409`.

##### `POST /api/v1/reviews/{review_session_id}/ratings`

```json
{
  "command_id": "02438e47-43f2-44a5-9c2f-8c94a530c435",
  "card_id": "913cc4ac-d7d4-477d-90cf-a43ce9c37d05",
  "rating": "good"
}
```

- `rating` is `again`, `hard`, `good`, or `easy`, mapped to quality 1, 3, 4, or 5.
- The card must be the session's current next card. A card can be rated once per session.
- The event insert, card schedule update, and session `updated_at` update commit in one transaction.
- Repeating the same `command_id`, session, card, and rating returns the original event with current progress and does not apply scheduling again. Reusing a command ID with different values returns `409`.

Returns `200` with `ReviewRatingResult`.

##### `POST /api/v1/reviews/{review_session_id}/complete`

Completes an in-progress review at the server clock, persists whole elapsed wall-clock seconds, and returns `ReviewProgress`. Completion is explicit even when no due cards remain. Repeating completion is idempotent; an abandoned session returns `409`.

##### `POST /api/v1/reviews/{review_session_id}/abandon`

Abandons an in-progress review at the server clock, persists whole elapsed wall-clock seconds, and returns `ReviewProgress`. Existing events and card scheduling remain. Repeating abandon is idempotent; a completed session returns `409`.

##### `DELETE /api/v1/reviews/{review_session_id}`

Soft-deletes a terminal review and returns `204`. In-progress reviews return `409`. Events remain owned history but a deleted review does not contribute dashboard totals.

##### `POST /api/v1/reviews/{review_session_id}/restore`

Restores a deleted terminal review and returns `ReviewProgress`. The deck may currently be deleted because restoration concerns historical activity. Restoring a non-deleted review returns `409`.

#### Dashboard Extension

Phase 2 adds these fields to `GET /api/v1/dashboard/summary`:

```json
{
  "today_completed_review_minutes": 12,
  "today_completed_review_session_count": 1,
  "today_reviewed_card_count": 7
}
```

- Membership uses a completed, non-deleted review session's `ended_at` and the same local-day bounds as study sessions.
- Minutes sum review-session `duration_seconds` and truncate to whole minutes. Session count counts review sessions. Card count counts their review events.
- In-progress, abandoned, and deleted reviews contribute zero. Review events cannot multiply session duration/count. Existing Phase 1 dashboard fields keep their documented meaning.

## Planned APIs

These groups remain planned and must not be mounted as placeholder success endpoints:

- **Phase 3:** `/api/v1/notes`, including search and soft delete/restore.
- **Phase 4:** `/api/v1/planner/tasks` and `/api/v1/planner/agenda`.
- **Phase 5:** `/api/v1/quizzes`, question/option authoring, attempts, answers, submission, and written self-grading.
- **Phase 6:** no MCP-over-HTTP namespace. MCP remains a separate future adapter over application services.

Each planned group requires an accepted endpoint contract before implementation. Future quiz activity must extend dashboard reporting without creating duplicate study sessions.
