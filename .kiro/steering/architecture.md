---
inclusion: always
---

# Architecture

Part of the [unified team agent memory](team-agent-memory.md). Records backend and
frontend design. Update when the design changes.

## Backend — modular monolith

- Single Django project (`config`) composed of self-contained feature modules
  under `apps/`. Each module owns its models, views, serializers, admin,
  migrations, and URLConf.
- `apps/` is added to `sys.path` in `config/settings/base.py`, so modules are
  imported as `apps.<module>` and registered in `LOCAL_APPS`.
- Routing: each module exposes its own `urls.py`; `config/urls.py` mounts them
  under `/api/`. A health endpoint lives at `/api/health/`.

### API layer

- Django REST Framework with JSON-only rendering.
- Defaults: `JWTAuthentication` for authentication and `IsAuthenticated` for
  permissions. Endpoints that must be public (e.g. register, login) override
  these per-view.

### Authentication

- Custom user model `users.User` (`AUTH_USER_MODEL`): email is the login
  identifier; `username` is removed. **UUID primary key** (as are all models).
- SimpleJWT with short-lived access tokens (15 min) and rotating refresh tokens
  (7 days) that are blacklisted after rotation. Algorithm HS256, signed with
  `SECRET_KEY`, `Bearer` auth header. Verified to work with UUID `user_id`.
- Endpoints: `POST /api/users/auth/register/`, `/auth/login/`, `/auth/refresh/`,
  `/auth/logout/`, and `GET /api/users/me/`.

### engine app — intake → retrieval pipeline

- `POST /api/engine/intake/` (authed): `pipeline.run_intake` → validate
  (serializers) → extract entities from the note via `medical_extractor` +
  `model_client` (MedGemma, OpenAI-compatible) → `patient_processor.normalize`
  (dedupe, provenance tags user|extracted, flag conflicts without overwriting
  user values) → persist a `users.PatientProfile`.
- `POST /api/engine/trials/` (authed): `pipeline.run_trial_search` →
  `retriever` (ChromaDB semantic search, joined to Postgres `Trial`) →
  `ai_matcher` (eligibility model — NOT built yet, reports unavailable) →
  `ranker`.
- **No fabrication:** when the model or vector store is unconfigured, each stage
  reports `available: false` and returns empty — never invented facts/trials/
  eligibility.

### integration app — comparison/ranking (Camden)

- Pure-Python, dataclass-based (no DB models). Deterministic ranking (clinical
  status over practical convenience) + three-valued criteria (met/conflict/
  unknown) + clarification questions. Endpoints `/api/integration/{compare,
  answer,preferences,demo}/`. See [integration.md](integration.md). Also exposes
  frontend-seam endpoints `/api/trials/` and `/api/extract-facts/`.

### Data stores

- **PostgreSQL**: source of truth. `users.User`, `users.PatientProfile`,
  `engine.Trial` (keyed by UUID; `Trial` also has unique `nct_id`).
- **ChromaDB** (local persistent client, not the networked server): semantic
  index of trial text keyed by `nct_id`; default `all-MiniLM-L6-v2` embeddings.
  Loaded via `ingest_trials`; dev auto-seeds, prod does not.
- **AI model**: MedGemma via vLLM (OpenAI-compatible `/v1`) through LangChain
  `ChatOpenAI`; optional and degrades gracefully.

### Configuration & environments

- Twelve-factor style via `django-environ`. `base.py` shared; `development.py` /
  `production.py` override. `DATABASE_URL` configures PostgreSQL; `MODEL_*` and
  `CHROMA_*` configure the model + vector store.

## Frontend

- React 19 + TypeScript + Vite + Tailwind under `client/`. Three-step dashboard:
  intake → review extracted facts → match & refine. Business logic in `src/lib/`
  (pure, Vitest-tested); state in `src/state/`.
- **Currently runs on local mock data** via the `src/api/adapter.ts` seam
  (`LocalMockApi`); an `HttpTrialBridgeApi` against the live Django endpoints is
  not yet wired. JWT should be held in memory (not localStorage).
- Vite dev server on `:5173`; its dev proxy forwards `/api` to the backend.

## Deployment (Docker)

- `compose.yaml`: `db` (Postgres 17) + `api` + `client`. `entrypoint.sh` waits
  for the DB, runs `migrate`, and (dev only) auto-seeds trials; prod also
  `collectstatic` + gunicorn. Chroma index persists in a `chroma_data` volume.

## Cross-cutting

- CORS restricts browser origins to `DJANGO_CORS_ALLOWED_ORIGINS`.
- Keep secrets out of source. The committed default `SECRET_KEY` is local-only;
  override in production (and use a 32+ byte key). `.env` files are gitignored.
