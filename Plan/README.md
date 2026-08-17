# StudyHub Planning Package

## Status

Phase 0 (Foundation) and Phase 1 (Focus loop) are complete. Later phases are planned and must not be treated as implemented.

## Document Index

| Document | Purpose |
| --- | --- |
| [ROADMAP.md](ROADMAP.md) | Delivery order, phase scope, and exit criteria |
| [SAD.md](SAD.md) | System structure, boundaries, and dependency direction |
| [DATA_MODEL.md](DATA_MODEL.md) | Implemented Phase 1 entities plus planned entities, relationships, lifecycle, and aggregation rules |
| [API.md](API.md) | HTTP conventions and endpoint contracts |
| [UI_DESIGN.md](UI_DESIGN.md) | Solitude visual system, information architecture, and accessibility rules |
| [TEST_STRATEGY.md](TEST_STRATEGY.md) | Test layers, fixtures, gates, and required commands |
| [DECISIONS.md](DECISIONS.md) | Accepted product and engineering decisions |
| [Tasks/](Tasks/) | Phase 01 completion record, completed Phase 00 records, and bounded handoff packets for planned phases |

## Source Of Truth

- `DECISIONS.md` records accepted choices and their status.
- `API.md` is authoritative for HTTP paths, payloads, status codes, and serialization.
- `DATA_MODEL.md` is authoritative for domain meaning, persistence relationships, state transitions, deletion, and aggregation.
- `SAD.md` is authoritative for component boundaries and dependency direction.
- `UI_DESIGN.md` is authoritative for navigation, tokens, responsive behavior, and accessibility.
- `ROADMAP.md` controls delivery order; task packets refine work but cannot expand a phase silently.
- Task packets are execution aids. They do not override the dedicated contract documents.
- Generated OpenAPI is the machine-readable implemented contract and must match `API.md`. UI code consumes its components through aliases in `UI/src/api/contracts.ts`.
- A contract change updates the relevant planning documents, backend schema, generated UI types/aliases, mocks, and tests in the same change.
- When documents conflict, use this order: accepted decision, dedicated contract document, roadmap, task packet. Resolve the conflict in documentation before implementation proceeds.

## Change Discipline

Keep the package factual and current. Mark future behavior as **Planned**, not available. Do not preserve obsolete contracts for compatibility unless released clients or persisted data require it.
