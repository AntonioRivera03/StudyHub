# UI Design: Solitude

## Design Intent

Solitude is quiet, sparse, and task-focused. It uses restrained contrast, generous negative space, short labels, and visible hierarchy instead of decoration. The interface should feel deliberate rather than empty: each screen has one clear primary task and only the supporting information needed for it.

## Tokens

### Color

```css
:root {
  --color-surface: #101315;
  --color-canvas: #0c0e10;
  --color-text: #cacccc;
  --color-muted: #798186;
  --color-line: #4b4e55;
}
```

| Token | Use |
| --- | --- |
| `--color-canvas` | Page and recessed backgrounds |
| `--color-surface` | Panels, controls, navigation, and elevated regions |
| `--color-text` | Primary text, selected state, and focus outline |
| `--color-muted` | Secondary labels, metadata, placeholders, and disabled content |
| `--color-line` | Borders, separators, tracks, and inactive outlines |

Do not rely on extra status colors. Pair status with text and an icon or shape. Destructive actions use explicit wording and confirmation, not red alone. Selected controls use text, border weight, and surface contrast.

### Typography

- UI and reading text: `IBM Plex Sans`, then `system-ui`, sans-serif.
- Timer digits, durations, timestamps, counts, and technical labels: `JetBrains Mono`, then `ui-monospace`, monospace.
- Body base: 16px with 1.5 line height. Metadata: 13-14px, never below 12px.
- Screen titles: 28-32px, medium weight. Section titles: 18-20px, medium weight.
- Use sentence case. Avoid all-caps except very short technical markers.
- Timer digits use tabular numerals and must not shift as time changes.

### Shape, Space, And Motion

- Radius: 6px for controls, panels, dialogs, and menus. Nested elements do not compound radii unnecessarily.
- Spacing follows a 4px base: 4, 8, 12, 16, 24, 32, 48, and 64px.
- Default control height is 40px; touch targets are at least 44 by 44px.
- Borders are 1px. Elevation is conveyed primarily by surface and border, not large shadows.
- Motion is limited to 120-180ms state transitions. Timer progress may move continuously but must honor reduced motion.

## Application Shell

### Desktop

- A narrow left navigation rail remains stable while the content pane scrolls.
- Product name and current section are visible without a decorative hero.
- Main content uses a readable maximum width of approximately 1120px and does not stretch data entry across the viewport.
- Primary actions sit near the screen title or the object they affect. Avoid a persistent global create button with changing meaning.

### Mobile

- Below 768px, navigation becomes a compact top bar and labeled bottom navigation for currently shipped primary destinations.
- Secondary destinations and settings use a menu; they remain keyboard reachable.
- Panels become a single column. Tables become labeled rows/cards without hiding essential fields.
- Timer controls remain reachable without horizontal scrolling and without being obscured by mobile navigation.

## Information Architecture

### Phase 1 Navigation

| Destination | Purpose |
| --- | --- |
| Dashboard | Today's completed focus/session totals, active timer, and recent sessions |
| Focus | Active timer, timer selection, and start/action controls |
| Sessions | Study history, filters, manual entry, edit, delete, and restore |
| Categories | Category management and restore |
| Settings | Pomodoro durations and cycle interval |

Dashboard and Focus are primary destinations. Sessions, Categories, and Settings may move into the mobile secondary menu if all labels do not fit.

### Planned Navigation

Add Flashcards, Notes, Planner, and Quizzes only when their phase is functional. Do not show dead links, fabricated counts, or controls that resolve to placeholder pages.

## Phase 1 Screen Rules

### Dashboard

- Start with today's completed focus minutes and completed session count, followed by the active timer and recent sessions.
- Explain that the local day uses the browser's JavaScript timezone offset.
- Zero totals show a useful empty state and a direct route to Focus; they do not show empty charts.

### Focus

- The timer value is the dominant element, followed by its phase and optional session/category context.
- With no active timer, show focus/short-break/long-break selection and only fields valid for that type.
- Running actions are Pause, Complete, and Cancel. Paused actions are Resume, Complete, and Cancel.
- Category is optional. Focus and manual-session forms provide an `Unsorted` choice that sends `category_id: null`.
- Complete and Cancel are visually and verbally distinct. Cancel confirmation explains that the linked focus session remains in history as cancelled and does not count in completed totals.
- The UI derives a smooth display countdown from `expected_end_at`, but the server response remains authoritative after visibility changes, reconnects, and actions.

### Sessions And Categories

- Default lists hide deleted rows. A clear toggle reveals deleted rows and restore actions.
- Phase 1 lists consume complete JSON arrays and have no pagination controls. Pagination is added before collection growth requires it.
- Empty, filtered-empty, loading, and failed states are distinct.
- Destructive actions state what remains linked; category deletion does not imply content deletion.

### Settings

- Group duration fields with minute units visible next to the value.
- Validate within the API ranges and preserve the user's entered values after a failed request.
- State that setting changes affect new timers, not the active timer.

## Interaction And Data Rules

- Server state is authoritative. Optimistic updates are permitted only when rollback is unambiguous; timer transitions are confirmed by the server before presenting the new state.
- On startup, reconnect, tab visibility change, and window focus, refetch the active timer.
- Do not decrement server data in global state each second. Render remaining time from the last `expected_end_at`, then reconcile with the server.
- Every request has visible pending and failure behavior. Disable duplicate submission while preserving keyboard focus.
- API error messages are translated into concise user language; field errors are associated with their controls.
- Dates and times are displayed in the user's locale, while requests continue to use UTC RFC3339.

## Responsive And Accessibility Rules

- Meet WCAG 2.2 AA for contrast, keyboard operation, labels, focus order, semantics, and error identification.
- Use native controls and landmarks before custom widgets. Every icon-only control has an accessible name.
- Focus is always visible with at least a 2px `#cacccc` outline and offset against both approved backgrounds.
- Muted color is for secondary text, not disabled-looking primary information. `#4b4e55` is not used for body text.
- Timer status changes use a polite live region. Do not announce every elapsed second.
- Dialog focus is trapped, Escape behavior is predictable, and focus returns to the invoking control.
- Respect `prefers-reduced-motion`; remove nonessential animation and replace continuous progress motion with discrete updates.
- At 200% zoom and 320 CSS px width, content remains operable without two-dimensional scrolling except intrinsically wide data.
- Empty and error states include text, not illustration alone. Status and chart distinctions never rely on color alone.
