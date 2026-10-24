---
inclusion: always
---

# Progress

Part of the [unified team agent memory](team-agent-memory.md). Tracks current
state and next steps so any session can pick up where the last left off. Keep it
current: update after meaningful changes and prune stale items.

_Last updated: 2026-10-24_

## Done

- Django backend skeleton: modular-monolith layout under `apps/`, split settings,
  `/api/health/` endpoint.
- `users` module: custom email-based user, JWT auth (register / login / refresh /
  logout with blacklist), and `/api/users/me/`.
- PostgreSQL + CORS + env-based configuration wired up (`.env.example` provided).
- **`integration` module (2026-10-24)**: Trial comparison, ranking, clarification engine.
  - Data contracts for PatientProfile, TrialCandidate, CriterionAssessment
  - Deterministic ranking with conflict preservation
  - Clarification question extraction and deduplication
  - Privacy-conscious response sanitization
  - Synthetic demo fixtures with 3 trial scenarios
  - API endpoints: `/api/integration/compare/`, `/answer/`, `/preferences/`, `/demo/`
  - Comprehensive test suite (35+ tests)

## In progress

- Awaiting clinical assessment module integration from teammate
- Awaiting patient extraction integration from Muhammad
- Frontend integration pending

## Next steps

- Connect clinical assessment module to criterion evaluation
- Connect patient extraction to profile input
- Build frontend comparison UI
- Add tests for the auth flow (`apps/users/tests.py` is currently a stub)

## Blocked / open questions

- Clinical assessment API contract not yet defined by teammate
- Patient extraction output format not yet finalized by Muhammad
- Frontend framework and component structure not yet defined
