# Task 02: Flashcards

## Handoff

- **Phase:** 2
- **Status:** Planned
- **Coordinator:** 5.6 Sol, owning API amendment, review UX, scheduling contract review, and integration
- **Backend lane:** Delegable after endpoint details are accepted in `API.md`
- **Dependencies:** Task 01 complete; current dashboard contract documented as the extension baseline

## Objective

Add deck/card authoring and a deterministic SM-2 review loop whose activity contributes once to dashboard totals.

## Scope

### Architecture And Contract Lane

- Before feature code, amend `API.md` with exact deck, card, due queue, review-session, answer/rating, completion, delete, restore, and dashboard-extension contracts.
- Lock request retry/idempotency behavior for recording a review event and define due ordering with an ID tie-breaker.
- Preserve the repository/application boundary; put SM-2 in a pure domain policy using the injected clock.
- Define OpenAPI schemas for schedule state and review progress without exposing ORM rows.

### Delegated Backend Lane

- Add `FlashcardDeck`, `Flashcard`, `ReviewSession`, and `ReviewEvent` migrations and repositories exactly as modeled.
- Implement deck/card CRUD, ordering, soft delete/restore, category assignment at deck level, and due-card queries.
- Reject `category_id` on cards; derive category through the deck.
- Implement review start, next-card query, rating command, resume, complete, and abandon service operations.
- Apply Again=1, Hard=3, Good=4, Easy=5 with standard SM-2 and minimum ease 1.3.
- Snapshot before/after scheduling state in immutable review events and prevent duplicate events on retry.
- Add completed review sessions to newly documented dashboard review totals and card counts without creating `study_sessions` or changing the meaning of current Phase 1 fields.

### UI Lane

- Add Flashcards navigation only when deck browse is functional.
- Build deck browse/create/edit, card list/editor, due state, review setup, review card, rating controls, completion summary, and deleted-item restore.
- Keep card category presentation inherited and direct category edits to the deck.
- Preserve Markdown source for card faces and sanitize rendered output.
- Support keyboard rating controls with visible labels; shortcuts supplement, not replace, buttons.

## Contracts

- Model, relationships, SM-2 formula, ratings, and activity source: `DATA_MODEL.md`.
- API conventions and reserved endpoint groups: `API.md`.
- A review event updates one card schedule and the owning session in one transaction.
- Due selection uses `due_at <= now`, excludes deleted cards/decks, and has deterministic ordering.
- Review-session `category_id_snapshot` is copied at start and does not move if the deck changes later.
- Only a completed, non-deleted review session contributes duration; review events supply `cards_reviewed`.
- No review operation creates, links, or updates a study session.

## Acceptance Criteria

- Accepted endpoint detail exists in `API.md` before backend and frontend implementations diverge.
- Scheduler unit tests cover every rating, first/second/later successful intervals, failed-review reset, ease changes, 1.3 floor, and due instant.
- A card cannot persist a category independent of its deck.
- Retried rating requests cannot duplicate events, repetitions, or dashboard card counts.
- Review interruption and resume preserve position/history; complete and abandon are distinct terminal outcomes.
- Soft-deleted decks/cards are excluded from due queues and can be restored under documented conflict rules.
- A completed review session adds its duration and event count exactly once while `today_completed_session_count` remains a count of completed manual/Pomodoro study sessions.
- Deck authoring and review pass RTL/MSW and desktop/mobile Playwright flows, including keyboard rating and error recovery.

## Out Of Scope

- Alternative spaced-repetition algorithms, shared decks, import/export, media attachments, card templates, remote sync, and AI generation.
- Recording reviews as focus/study sessions.

## Verification

Run the full commands in `TEST_STRATEGY.md`, plus focused scheduler, repository aggregation, and review API tests. Playwright must cover deck/card creation, due review with all four controls represented, interruption/resume, completion, delete/restore, and dashboard update.

## Handoff Output

The backend delegate returns migration revision, accepted endpoint implementation, SM-2 test matrix, idempotency approach, OpenAPI result, and commands run. The coordinator verifies scheduling labels, inherited category behavior, and aggregate totals against the real backend.
