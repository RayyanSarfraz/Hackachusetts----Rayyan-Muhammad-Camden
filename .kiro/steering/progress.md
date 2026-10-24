---
inclusion: always
---

# Progress

Part of the [unified team agent memory](team-agent-memory.md). Tracks current
state and next steps so any session can pick up where the last left off. Keep it
current: update after meaningful changes and prune stale items.

_Last updated: 2026-10-24 (UUID PKs + trial ingestion + MedGemma wired)_

## ⚠️ Action required first (after pulling)

**Primary keys were switched to UUID (2026-10-24).** The initial migrations were
regenerated, so the old integer-PK schema is incompatible. Before running or
testing anything, reset your local database once:

- Docker: `docker compose down -v` then `docker compose up --build`
  (drops the `postgres_data` + `chroma_data` volumes; dev auto-seeds trials).
- Host Postgres: drop/recreate the DB (or its tables), then
  `python manage.py migrate` and `python manage.py ingest_trials ../data/trials/data.csv`.

Skipping this causes migration/consistency errors against an int-PK database.

## Done

- Django backend skeleton: modular-monolith layout under `apps/`, split settings,
  `/api/health/` endpoint.
- `users` module: custom email-based user, JWT auth (register / login / refresh /
  logout with blacklist), and `/api/users/me/`.
- PostgreSQL + CORS + env-based configuration wired up (`.env.example` provided).
- **`integration` module (Camden)**: trial comparison, deterministic ranking,
  clarification engine; dataclass contracts; synthetic fixtures; endpoints
  `/api/integration/{compare,answer,preferences,demo}/` + frontend-seam
  `/api/trials/` and `/api/extract-facts/`. ~40+ tests.
- **`engine` module**: full intake→retrieval pipeline. Serializers, `IntakeView`
  (`/api/engine/intake/`) + `TrialSearchView` (`/api/engine/trials/`), services
  (patient_processor, medical_extractor, model_client, retriever, ai_matcher,
  ranker, pipeline), and `Trial` model.
- **MedGemma wired** (`google/medgemma-1.5-4b-it` via vLLM/LangChain). Reasoning-
  model JSON parsing + cold-start timeouts handled; verified live end to end.
- **Trial ingestion**: `ingest_trials` command → Postgres `Trial` + ChromaDB;
  retriever joins Chroma hits back to Postgres. Dev auto-seed in `entrypoint.sh`.
- **Dockerized**: `compose.yaml` (db + api + client), chroma persistence volume,
  model/chroma env wiring.
- **Frontend scaffolded**: React 19 + TS + Vite + Tailwind dashboard (runs on
  mock data for now).
- **UUID primary keys** on all models (migrations regenerated — DB reset needed).

## In progress / Next steps

- Wire the frontend's `adapter.ts` to the live Django endpoints (currently mock).
- Build/connect the eligibility-matching model (`engine.ai_matcher` stub).
- Enrich trial data with eligibility-criteria text + city for better matching.
- Add auth-flow tests (`apps/users/tests.py` is still a stub).

## Blocked / open questions

- Eligibility-matching model not yet available.
- Frontend↔backend contract: the client's seam expects `/api/trials/` and
  `/api/extract-facts/` (provided), but full intake/compare wiring is pending.
