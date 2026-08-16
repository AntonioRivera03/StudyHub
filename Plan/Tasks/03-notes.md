# Task 03: Notes

## Handoff

- **Phase:** 3
- **Status:** Planned
- **Coordinator:** 5.6 Sol, owning endpoint amendment, editor UX, safe rendering, and integration
- **Backend lane:** Delegable after endpoint details are accepted in `API.md`
- **Dependencies:** Task 02 complete; shared category and soft-delete contracts stable

## Objective

Deliver a focused Markdown notebook with category organization, deterministic browse/search, safe preview, and recoverable editing.

## Scope

### Architecture And Contract Lane

- Amend `API.md` with exact note list/search/create/get/patch/delete/restore routes before feature code.
- Define list sort/cursor behavior and case-insensitive search over title and Markdown source.
- Keep Markdown source canonical. Rendering is a frontend presentation concern unless a later accepted contract adds server rendering.
- Use explicit save for this phase; track unsaved changes and guard navigation rather than introducing an uncontracted autosave protocol.

### Delegated Backend Lane

- Add the `Note` migration, mapping, repository, and application services from `DATA_MODEL.md`.
- Implement paginated note browse with category, search, and deleted filters plus deterministic `updated_at`/ID ordering.
- Implement create, get, patch, soft delete, and restore with active-category validation.
- Preserve Markdown bytes after JSON decoding except for documented title trimming; do not normalize or render note content.
- Add repository, API, migration, cursor/filter, soft-delete, and OpenAPI tests.

### UI Lane

- Add Notes navigation only when browse/create/edit work.
- Build searchable note browse, category filter, editor, preview, unsaved-change guard, delete, deleted view, and restore.
- Use side-by-side edit/preview when space permits and a labeled mode switch on narrow screens.
- Sanitize rendered Markdown and keep raw HTML disabled or sanitized under a tested policy.
- Preserve draft input after validation, network, or persistence errors.

## Contracts

- Entity and soft-delete rules: `DATA_MODEL.md`.
- API conventions and reserved group: `API.md`.
- `markdown` stores source exactly as submitted; the API does not return trusted HTML.
- Search is case-insensitive substring matching over title and source, with deterministic pagination. It excludes deleted notes unless requested.
- Notes have zero or one active category. Deleting a category does not delete notes.
- Explicit save sends a PATCH containing changed fields; the UI does not claim persistence before a successful response.

## Acceptance Criteria

- Accepted endpoint detail exists in `API.md` before backend and frontend implementations diverge.
- Markdown source including code fences, Unicode, line endings accepted by JSON, and Markdown punctuation round-trips without lossy transformation.
- Search and category filters compose and maintain stable cursor ordering when timestamps tie.
- Deleted notes are hidden by default, remain retrievable only through documented deleted views, and restore without a new ID.
- Rendered links, raw HTML, script-like input, and unsafe URL schemes cannot execute script.
- Keyboard users can move between browse, editor, preview, save, delete, and restore; focus remains visible.
- RTL/MSW covers unsaved, saving, saved, failed-save, empty, filtered-empty, and restore states.
- Playwright covers create/edit/preview/search/delete/restore at desktop and mobile widths.

## Out Of Scope

- Rich-text/WYSIWYG editing, collaborative editing, note version history, backlinks, graph view, attachments, OCR, publishing, and server-rendered HTML.

## Verification

Run the full commands in `TEST_STRATEGY.md`, plus Markdown round-trip API tests and renderer security tests with hostile fixtures. Manually verify the unsaved-change guard and 320px edit/preview behavior.

## Handoff Output

The backend delegate returns migration revision, accepted endpoint implementation, search semantics tests, OpenAPI result, and commands run. The coordinator validates source preservation and sanitization independently.
