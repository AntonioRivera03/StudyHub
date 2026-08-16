# Data Model

This document separates the implemented Phase 0/1 model from planned entities. Phase labels identify delivery timing, not separate databases.

## Common Rules

- Public identifiers are server-generated UUID strings. Foreign keys use the same identifier form.
- Mutable records have `created_at` and `updated_at` UTC instants. The API serializes timestamps as UTC RFC3339 values.
- Implemented soft deletion applies to categories and study sessions through nullable `deleted_at`. Normal reads exclude deleted rows; restore clears `deleted_at`.
- Soft-deleting a category does not delete related content. A deleted category cannot be selected for a new assignment until restored.
- Planned user-content entities follow the same soft-delete rule unless their phase contract states otherwise.
- Durations are non-negative whole seconds.
- Category is optional on resources. A resource has at most one category; there are no resource/category join tables.

## Implemented Phase 1 Entities

### Category

| Field | Rule |
| --- | --- |
| `id` | UUID primary key |
| `name` | Trimmed, 1-120 characters; not required to be unique |
| `color` | Nullable trimmed string, 1-32 characters when present |
| `created_at`, `updated_at`, `deleted_at` | Common timestamps and soft delete |

Deletion does not delete related resources. Category assignment is optional throughout the Phase 1 model.

### PomodoroSettings

Singleton settings row created when first needed.

| Field | Rule |
| --- | --- |
| `focus_minutes` | Integer, default 25, range 1-180 |
| `short_break_minutes` | Integer, default 5, range 1-60 |
| `long_break_minutes` | Integer, default 15, range 1-120 |
| `long_break_every` | Integer, default 4, range 1-12 |
| `created_at`, `updated_at` | Common timestamps; not soft-deletable |

Settings are copied when a timer starts. Changes do not alter an existing timer.

### Timer

| Field | Rule |
| --- | --- |
| `id` | UUID primary key |
| `phase` | `focus`, `short_break`, or `long_break` |
| `state` | `running`, `paused`, `completed`, or `cancelled` |
| `category_id` | Nullable category foreign key; accepted only for focus |
| `title` | Nullable string; accepted only for focus |
| `duration_seconds` | Planned duration copied from settings |
| `remaining_seconds` | Persisted whole-second snapshot at lifecycle transitions |
| `started_at` | Start instant |
| `expected_end_at` | Planned end instant; recalculated on resume |
| `paused_at` | Nullable pause instant |
| `completed_at` | Nullable completion instant |
| `cancelled_at` | Nullable cancellation instant |
| `created_at`, `updated_at` | Common timestamps; no public delete lifecycle |

`running` and `paused` are active states. There can be at most one active timer across all phases; the application checks this and SQLite supplies a conditional unique index.

A focus timer creates one linked study session. The session owns the relationship through unique nullable `StudySession.timer_id`. Break timers create no study session.

### StudySession

| Field | Rule |
| --- | --- |
| `id` | UUID primary key |
| `title` | Trimmed, 1-200 characters |
| `category_id` | Nullable category foreign key |
| `started_at` | UTC activity start |
| `ended_at` | Nullable UTC activity end |
| `duration_seconds` | Actual activity duration |
| `notes` | Nullable text, at most 10,000 characters |
| `source` | `manual` or `pomodoro`; server-managed |
| `status` | `active`, `completed`, or `cancelled`; server-managed |
| `timer_id` | Unique nullable timer foreign key; set for Pomodoro sessions |
| `created_at`, `updated_at`, `deleted_at` | Common timestamps and soft delete |

Manual sessions may be created without `ended_at`; they start as `active` with zero duration and become `completed` when a later PATCH supplies a valid end. Their duration is derived from `ended_at - started_at`. Clearing `ended_at` through PATCH makes a manual session active again.

A focus start creates an active `pomodoro` session. Timer completion or natural expiry closes it as `completed`; timer cancellation closes it as `cancelled`. Pomodoro duration is actual active timer time, excluding pauses and unused planned time. Cancelled focus sessions remain persisted as audit records, are not automatically soft-deleted, and are excluded from completed totals.

Pomodoro timestamps are timer-managed. Session metadata may be updated separately. Any active session, manual or Pomodoro, cannot be deleted.

## Focus State Machines

### Timer Transitions

```text
start -> running
running -> paused | completed | cancelled
paused -> running | completed | cancelled
completed -> terminal
cancelled -> terminal
```

| Command/event | Implemented effect |
| --- | --- |
| Start | Reject a non-expired active timer; copy settings duration; create a running timer; create an active linked session only for focus |
| Pause | Compute remaining whole seconds and move a running timer to paused |
| Resume | Move a paused timer to running and set a new `expected_end_at` |
| Natural expiry | Complete at the persisted `expected_end_at`; close a linked focus session with full elapsed active duration |
| Complete early | Complete now; close a linked focus session using elapsed active seconds only |
| Cancel | Cancel now; close a linked focus session as cancelled using elapsed active seconds only |

A naturally expired running timer is reconciled before active-timer reads and before a new start. Completion is idempotent for an already completed timer; cancellation is idempotent for an already cancelled timer. The opposite terminal action returns a conflict. No background worker is required for correctness.

### Study Session Lifecycle

```text
manual create without end -> active -> completed when ended_at is set
manual create with end ----------------> completed
focus start -> active -> completed | cancelled
completed/cancelled -> deleted <-> restored
```

Active sessions cannot be deleted. Only completed sessions contribute to current dashboard counts; cancelled sessions remain visible history but do not count.

## Planned Entities

### Flashcards: Phase 2

**FlashcardDeck**

- `id`, `name`, optional `description`, nullable `category_id`, common timestamps, and `deleted_at`.
- Owns many cards and review sessions.

**Flashcard**

- `id`, `deck_id`, `front_markdown`, `back_markdown`, `position`, scheduling fields, common timestamps, and `deleted_at`.
- Scheduling fields: `repetitions`, `interval_days`, `ease_factor` (initial 2.5, minimum 1.3), `due_at`, and nullable `last_reviewed_at`.
- Has no `category_id`; it always inherits the deck category.

**ReviewSession**

- `id`, `deck_id`, nullable `category_id_snapshot`, `status` (`in_progress`, `completed`, `abandoned`), `started_at`, nullable `ended_at`, `duration_seconds`, common timestamps, and `deleted_at`.
- Category is copied from the active deck when review starts so historical aggregation does not move when the deck changes category.

**ReviewEvent**

- `id`, `review_session_id`, `card_id`, `rating` (`again`, `hard`, `good`, `easy`), numeric quality, `reviewed_at`, and previous/new scheduling snapshots.
- Immutable history owned by its review session; it is not independently soft-deleted.
- A uniqueness key on `(review_session_id, card_id, sequence)` or an equivalent command ID prevents retry duplication.

SM-2 mapping is Again=1, Hard=3, Good=4, Easy=5. For quality below 3, repetitions reset to 0 and the next interval is 1 day. For successful reviews, intervals are 1 day, then 6 days, then the rounded prior interval multiplied by ease. Ease uses the standard formula and is clamped to 1.3 minimum:

```text
new_ease = max(1.3, ease + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
```

### Notes: Phase 3

**Note**

- `id`, `title`, `markdown`, nullable `category_id`, common timestamps, and `deleted_at`.
- Markdown source is canonical. Rendered HTML is derived and is not trusted persisted content.

### Planner: Phase 4

**PlannerTask**

- `id`, `title`, optional `description_markdown`, nullable `category_id`, `status` (`open`, `completed`), `priority` (`low`, `normal`, `high`), nullable `scheduled_for`, nullable `due_at`, nullable `completed_at`, common timestamps, and `deleted_at`.
- Agenda is a query/projection over tasks, not a separate persisted entity.

### Quizzes: Phase 5

**Quiz**

- `id`, `title`, optional `description`, nullable `category_id`, common timestamps, and `deleted_at`.
- Owns ordered questions.

**QuizQuestion**

- `id`, `quiz_id`, `question_type` (`mcq`, `written`), `prompt_markdown`, `position`, `points`, optional written-answer guidance, common timestamps, and `deleted_at`.

**QuizOption**

- `id`, `question_id`, `text_markdown`, `position`, `is_correct`, common timestamps, and `deleted_at`.
- Only MCQ questions have options. At least two active options and exactly one correct option are required before a quiz can be attempted.

**QuizAttempt**

- `id`, `quiz_id`, nullable `category_id_snapshot`, `status` (`in_progress`, `awaiting_self_grade`, `completed`, `abandoned`), `started_at`, nullable `submitted_at`, nullable `completed_at`, `duration_seconds`, `earned_points`, `possible_points`, common timestamps, and `deleted_at`.
- Category is copied from the quiz when the attempt starts.

**QuizAnswer**

- `id`, `attempt_id`, `question_id`, immutable `question_snapshot`, nullable `selected_option_id`, nullable `written_answer_markdown`, nullable `auto_score`, nullable `self_score`, and answer timestamps.
- One answer row per active question is initialized when the attempt starts. `question_snapshot` contains the type, prompt, points, guidance, and MCQ option IDs/text/correctness needed to render and grade that attempt independently of later quiz edits.
- MCQ receives `auto_score`; written answers require `self_score`. A uniqueness constraint on `(attempt_id, question_id)` makes answer replacement idempotent and prevents duplicate scoring.

## Relationships

```text
Category 1 <- 0..* StudySession
Category 1 <- 0..* Timer (focus only)
Timer 1 <- 0..1 StudySession through StudySession.timer_id

Category 1 <- 0..* FlashcardDeck -> 0..* Flashcard
Category 1 <- 0..* Note
Category 1 <- 0..* PlannerTask
Category 1 <- 0..* Quiz -> 0..* QuizQuestion -> 0..* QuizOption
FlashcardDeck 1 -> 0..* ReviewSession -> 0..* ReviewEvent
Quiz 1 -> 0..* QuizAttempt -> 0..* QuizAnswer
```

Category snapshot fields on planned review sessions and quiz attempts preserve historical attribution. They remain nullable single-category references.

## Activity Aggregation

### Current Dashboard

- Completed session membership in the local day is based on `ended_at` in the half-open UTC interval calculated from the client's JavaScript-style timezone offset.
- `today_completed_focus_minutes` sums persisted `duration_seconds` from non-deleted, completed `pomodoro` sessions and exposes whole minutes.
- `today_completed_session_count` counts non-deleted, completed manual and Pomodoro sessions.
- Active and cancelled sessions are excluded. Timers are never counted separately from their linked Pomodoro session.

### Planned Review And Quiz Totals

Future totals use three disjoint activity sources:

| Source | Included rows | Duration | Count |
| --- | --- | --- | --- |
| `study_sessions` | Non-deleted completed manual/Pomodoro sessions | `duration_seconds` | Sessions |
| `review_sessions` | Non-deleted `completed` sessions | `duration_seconds` | Review sessions; reviewed-card count comes from review events |
| `quiz_attempts` | Non-deleted `completed` attempts | `duration_seconds` | Quiz attempts |

- Review sessions and quiz attempts are never mirrored into `study_sessions`.
- Focus timer time contributes only through its linked Pomodoro study session, never directly from the timer row.
- Future category totals use the session category or immutable category snapshot.
- Aggregation queries operate per source before combining projections so child review events or quiz answers cannot multiply activity rows.
