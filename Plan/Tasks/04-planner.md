# Task 04: Planner

## Handoff

- **Phase:** 4
- **Status:** Planned
- **Coordinator:** 5.6 Sol, owning agenda semantics, endpoint amendment, responsive planning UI, and integration
- **Backend lane:** Delegable after endpoint details are accepted in `API.md`
- **Dependencies:** Task 03 complete; UTC-offset convention and category behavior stable

## Objective

Add study tasks and an agenda that groups work consistently for the client's local day without introducing a full calendar system.

## Scope

### Architecture And Contract Lane

- Amend `API.md` with exact planner task CRUD, complete, reopen, delete, restore, and agenda endpoints.
- Specify timestamp/date types, list filters, priority ordering, and agenda buckets using the existing JavaScript convention `local = UTC - offset`.
- Define agenda projection behavior before backend/UI work: `scheduled_for` is the primary agenda instant, `due_at` is the fallback, and tasks with neither remain in Backlog.
- Keep agenda as an application query, not a persisted aggregate or client-only regrouping.

### Delegated Backend Lane

- Add the `PlannerTask` migration, mapping, repository, services, and agenda projection.
- Implement task list/create/get/patch, complete/reopen, soft delete/restore, category/status/priority/time filters, and cursor pagination.
- Enforce completion timestamp transitions: complete sets `completed_at` once; reopen clears it.
- Compute Overdue, Today, Upcoming, and Backlog from an injected clock and explicit `timezone_offset_minutes`.
- Add unit boundary tests plus repository, API, migration, pagination, state transition, and OpenAPI tests.

### UI Lane

- Add Planner navigation only when task list and agenda are functional.
- Build agenda and all-task views, quick create, full edit, complete/reopen, filters, delete, deleted view, and restore.
- Present scheduled and due information distinctly; do not imply they are the same field.
- Keep quick entry keyboard-efficient and recover input after failures.
- Distinguish overdue, today, upcoming, completed, and backlog with labels/structure rather than color alone.

## Contracts

- Entity fields and states: `DATA_MODEL.md`.
- API conventions and UTC offset sign: `API.md`.
- Agenda accepts offsets from -840 through 840 and returns its UTC period boundaries.
- Open tasks with an agenda instant before local today are Overdue; within today are Today; after today are Upcoming; no agenda instant is Backlog.
- Completed tasks are excluded from active agenda buckets by default and available through an explicit filter/view.
- Category remains nullable and singular. Soft-deleted tasks never appear in normal agenda results.
- State changes are application-service commands, not arbitrary client writes to `completed_at`.

## Acceptance Criteria

- Accepted endpoint detail exists in `API.md` before backend and frontend implementations diverge.
- Fake-clock tests cover positive/negative offsets, exact local midnight, an instant at period end, daylight-offset changes supplied by the client, and tasks with both scheduled/due values.
- Complete/reopen is idempotent under the accepted API contract and cannot leave status/timestamp disagreement.
- Agenda results are deterministic and exclude deleted/completed content according to filters.
- Task CRUD and soft delete/restore preserve IDs and category relationships.
- UI supports keyboard quick create, edit, complete/reopen, filter, and restore at desktop and mobile widths.
- RTL/MSW and Playwright cover Overdue, Today, Upcoming, Backlog, completed, empty, and failed-mutation states.

## Out Of Scope

- Calendar events, recurring tasks, reminders/notifications, drag scheduling, external calendar sync, dependencies between tasks, shared planning, and timezone-name storage.

## Verification

Run the full commands in `TEST_STRATEGY.md`, plus focused agenda-boundary and completion-transition tests. Playwright must set a known clock/offset and verify each agenda bucket, quick create, complete/reopen, and delete/restore.

## Handoff Output

The backend delegate returns migration revision, accepted endpoint implementation, agenda boundary matrix, OpenAPI result, and commands run. The coordinator verifies bucket semantics against the same fake-clock examples before UI sign-off.
