---
inclusion: always
---

# Product

Part of the [unified team agent memory](team-agent-memory.md). Records what the
product is and what it should do. Update when goals or features change.

## Summary

- **Clinical-Trial Prescreening Copilot** ("TrialBridge") — a full-stack app that
  takes a patient's information, extracts/normalizes their medical facts, and
  retrieves + ranks clinical trials they might be eligible for, surfacing
  clarifying questions for unknowns.
- Django REST API (`api/`) + React 19/TypeScript frontend (`client/`).
- Hackathon project ("Hackachusetts"). Fictional/demo data only — not for
  clinical use.

## Goal

Help a user discover relevant clinical trials from free-text medical history:
normalize their profile, semantically match against a trial corpus, and rank by
clinical eligibility + practical fit — never fabricating medical facts or
eligibility verdicts, and explicitly tracking unknowns.

## Features

Current, verifiable capabilities:

- Email-based user accounts (custom `users.User`, email is the login identifier,
  **UUID primary key**). JWT auth: register / login / refresh / logout
  (refresh-token blacklist) + authenticated `/api/users/me/`.
- **Patient intake** (`POST /api/engine/intake/`, authed): validates and
  normalizes a patient profile, optionally extracts entities from the free-text
  note via MedGemma, preserves user-vs-extracted provenance, and persists a
  `PatientProfile`.
- **Trial retrieval** (`POST /api/engine/trials/`, authed): semantic search over
  a ChromaDB-indexed trial corpus, joined back to full `Trial` records in
  Postgres.
- **Trial comparison/ranking** (integration app): `/api/integration/compare/`,
  `/answer/`, `/preferences/`, `/demo/` — deterministic ranking + clarification
  questions (Camden; see integration.md).
- **Trial ingestion:** `python manage.py ingest_trials <csv>` loads the dataset
  into Postgres + ChromaDB (dev auto-seeds on `docker compose up`).
- Frontend: React/TS dashboard (intake → review facts → match & refine). Note it
  currently runs on local mock data via its `adapter.ts` seam; wiring it to the
  live API endpoints is pending.
- Health check at `/api/health/`; engine status at `/api/engine/status/`.

## Not yet built / pending

- Frontend wired to the real backend (still uses `LocalMockApi`).
- Eligibility-matching model (`engine.ai_matcher` reports "unavailable").
- Richer trial data (current CSV lacks eligibility-criteria text and city).
- Auth-flow tests (`apps/users/tests.py` is a stub).
