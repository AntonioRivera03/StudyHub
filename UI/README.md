# StudyHub UI

React and TypeScript frontend for the StudyHub focus and flashcard workflows.

## Commands

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm test -- --run
npm run e2e
npm run build
```

The Vite development server proxies `/api` to `http://127.0.0.1:8000`. API calls use the `/api/v1` prefix.

The Playwright check starts the real backend and Vite server, uses the system Chromium installation, and stores its temporary SQLite database under `/tmp/opencode`. It covers the focus loop plus desktop and 320px flashcard authoring/review flows.

## API Types

Generate OpenAPI types from a running backend:

```bash
npm run openapi:generate
```

Set `OPENAPI_URL` to use another schema URL. `src/api/generated.ts` is generated output and should not be edited manually. `src/api/contracts.ts` is the stable application boundary; its exports can be replaced with aliases to generated schemas without changing components.

## Timer Behavior

Running countdowns are derived from the backend `expected_end_at` value and active timers are recovered when the app reopens. Closing the browser does not cancel a timer, but a closed browser cannot play an end alert.
