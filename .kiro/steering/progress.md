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

## In progress

- _(none recorded yet)_

## Next steps

- Define the concrete product goal and feature set (fill in `product.md`).
- Scaffold the `client/` frontend (CORS points at a Vite dev server on `:5173`).
- Add the first domain feature module(s) beyond `users`.
- Add tests for the auth flow (`apps/users/tests.py` is currently a stub).

## Blocked / open questions

- Product scope and the frontend framework choice are not yet documented in-repo.
