# StudyHub

StudyHub is a local-first study workspace. The current release contains the Foundation, Focus Loop, and Flashcards milestones: a persistent Pomodoro timer, audited study sessions, categories, timer settings, deck/card authoring, SM-2 reviews, and a daily summary.

The remaining notes, planner, quiz, and MCP-readiness work is defined in [`Plan/ROADMAP.md`](Plan/ROADMAP.md).

## Requirements

- Python 3.14 and [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- Chromium for the Playwright check

## Setup

```bash
make setup
```

## Development

Run the API and UI in separate terminals:

```bash
make server
make ui
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the FastAPI server on port 8000.

## Local Production

Build the UI and serve the complete application through FastAPI:

```bash
make run
```

Open `http://127.0.0.1:8000`. The server binds locally and does not provide authentication, so it must not be exposed to an untrusted network.

The default SQLite database is stored at `$XDG_DATA_HOME/studyhub/studyhub.db`, or `~/.local/share/studyhub/studyhub.db` when `XDG_DATA_HOME` is unset. Override it with `STUDYHUB_DATABASE_URL`.

## Verification

```bash
make check
```

This runs backend linting, formatting checks, strict typing and tests, followed by frontend linting, typing, component tests, production build, and the live Playwright focus and flashcard workflows.

## Documentation

- [`Plan/SAD.md`](Plan/SAD.md): architecture and boundaries
- [`Plan/API.md`](Plan/API.md): implemented HTTP contract
- [`Plan/DATA_MODEL.md`](Plan/DATA_MODEL.md): current and planned data model
- [`Plan/UI_DESIGN.md`](Plan/UI_DESIGN.md): Solitude visual system
- [`Plan/TEST_STRATEGY.md`](Plan/TEST_STRATEGY.md): quality gates
- [`Plan/Tasks/`](Plan/Tasks/): bounded model handoff packets
