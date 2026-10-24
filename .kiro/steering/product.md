---
inclusion: always
---

# Product

Part of the [unified team agent memory](team-agent-memory.md). Records what the
product is and what it should do. Update when goals or features change.

## Summary

- Full-stack web application: a Django REST API (`api/`) with a planned frontend
  client (`client/`, not yet scaffolded).
- Hackathon project ("Hackachusetts"). Keep scope focused and shippable.

## Goals

- _(2026-10-24) Record the concrete product goal here once defined. The repo
  currently ships an auth-ready API skeleton; the end-user feature set is not
  yet documented in-repo._

## Features

Current, verifiable capabilities:

- Email-based user accounts (custom `users.User`, email is the login identifier).
- JWT authentication: register, login, token refresh, and logout (refresh-token
  blacklist). See `api/apps/users/urls.py`.
- Authenticated profile endpoint (`/api/users/me/`).
- Health check at `/api/health/`.

## Not yet built

- Frontend client (`client/` is empty).
- Domain features beyond user auth.
