# Task 05: Quizzes

## Handoff

- **Phase:** 5
- **Status:** Planned
- **Coordinator:** 5.6 Sol, owning endpoint amendment, authoring/attempt UX, grading contract review, and integration
- **Backend lane:** Delegable after endpoint details are accepted in `API.md`
- **Dependencies:** Task 04 complete; dashboard multi-source aggregation proven by reviews

## Objective

Deliver quiz authoring and resumable attempts with deterministic MCQ auto-grading, explicit written self-grading, and non-duplicated activity totals.

## Scope

### Architecture And Contract Lane

- Amend `API.md` with exact quiz/question/option authoring, validation, attempt start/resume, answer upsert, submit, self-grade, result, delete, restore, and dashboard-extension contracts.
- Lock attempt retry/idempotency rules and define when a quiz is eligible to start.
- Define attempt snapshot transport so an attempt remains stable after later quiz edits.
- Keep grading in domain/application services; clients may display provisional results but never authoritatively calculate persisted scores.

### Delegated Backend Lane

- Add `Quiz`, `QuizQuestion`, `QuizOption`, `QuizAttempt`, and `QuizAnswer` migrations and repositories.
- Implement quiz/question/option CRUD, ordering, validation, and soft-delete/restore.
- On start, create one answer row per active question with an immutable question/options/points snapshot.
- Implement idempotent answer replacement, submit, MCQ grading, written self-grade, finalization, resume, and abandon.
- Require at least two active options and exactly one correct option for every MCQ before start.
- Add completed attempts to newly documented dashboard quiz totals exactly once using category snapshots; never create study sessions or change the meaning of current Phase 1 fields.
- Add pure grading tests, repository/API/migration tests, transaction rollback tests, and OpenAPI checks.

### UI Lane

- Add Quizzes navigation only when browse, authoring, and attempts are functional.
- Build quiz editor with ordered MCQ/written questions, option correctness controls, validation summary, and destructive confirmations.
- Build attempt progress, resume, answer persistence, submit review, written self-grade, and final result screens.
- Make unanswered and awaiting-self-grade states explicit. Do not present a final score prematurely.
- Ensure option groups use native radio semantics for one-answer MCQ and written grading controls are labeled with point ranges.

## Contracts

- Models, snapshots, statuses, and aggregation: `DATA_MODEL.md`.
- API conventions and reserved group: `API.md`.
- MCQ uses a single selected option and is graded against the immutable attempt snapshot.
- Written `self_score` is a numeric value from 0 through that question's points. All written answers require an explicit self-score before completion.
- Submit auto-grades MCQ. It completes an all-MCQ attempt or moves an attempt with written questions to `awaiting_self_grade`.
- Final totals sum answer scores once; one `(attempt_id, question_id)` answer prevents duplicate scoring.
- Only completed, non-deleted attempts contribute dashboard duration/count. No attempt creates a study session.

## Acceptance Criteria

- Accepted endpoint detail exists in `API.md` before backend and frontend implementations diverge.
- An invalid quiz cannot start and returns field-addressable errors for malformed MCQ/options/points.
- Attempt snapshots remain unchanged when the source quiz is edited or soft-deleted.
- Retried answer, submit, and self-grade requests cannot duplicate answers, points, completion, or dashboard totals.
- All-MCQ submit produces a final score automatically; mixed/written submit cannot complete before all self-grades exist.
- Resume returns the same snapshot, answers, status, and progress.
- Completed quiz duration/count appears exactly once while study-session totals remain unchanged.
- Authoring, MCQ attempt, mixed attempt/self-grade, resume, result, and delete/restore pass RTL/MSW and desktop/mobile Playwright flows.

## Out Of Scope

- Essay auto-grading, partial MCQ selection, question banks, randomization, timed exams, proctoring, certificates, sharing, import/export, and AI question generation.

## Verification

Run the full commands in `TEST_STRATEGY.md`, plus grading truth-table, snapshot immutability, idempotent retry, and aggregate multiplication tests. Playwright must cover one all-MCQ attempt and one written/mixed attempt through self-grade.

## Handoff Output

The backend delegate returns migration revision, accepted endpoint implementation, grading matrix, idempotency mechanism, OpenAPI result, and commands run. The coordinator independently verifies snapshot rendering, score states, and dashboard isolation.
