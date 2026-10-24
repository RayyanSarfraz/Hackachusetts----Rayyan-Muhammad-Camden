---
inclusion: always
---

# Decisions

Part of the [unified team agent memory](team-agent-memory.md). A dated log of
team decisions and their rationale. Newest first. Add an entry whenever a choice
is made that a future session should not relitigate.

Format:

```
## YYYY-MM-DD — Short title
Decision: what was decided.
Why: the rationale / tradeoff.
Status: active | superseded by <date/title>.
```

---

## 2026-10-24 — UUID primary keys on all DB tables
Decision: every Django model uses a UUID primary key
(`id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`) —
`users.User`, `users.PatientProfile`, `engine.Trial`. New models must follow
this. `engine.Trial` keeps `nct_id` as the public business key (ChromaDB + the
frontend key on `nct_id`, not the UUID).
Why: non-guessable IDs, no enumeration of users/patients, safe to expose in URLs.
Migration note: the initial migrations were REGENERATED (not added on top), so an
existing int-PK dev database is incompatible — reset it once (see progress.md
"Action required first"). JWT auth was verified to work with UUID `user_id`.
Status: active.

## 2026-10-24 — Trial data: ChromaDB (search) + PostgreSQL (full record)
Decision: ingest clinical-trial data into both stores keyed by `nct_id` —
embedded text (title + conditions [+ eligibility]) into a local persistent
ChromaDB collection for semantic retrieval, full rows into the `engine.Trial`
Postgres table. Load via `python manage.py ingest_trials <csv>` (idempotent
upsert). ChromaDB runs in LOCAL persistent-client mode (not the networked
server, which has a multi-tenant auth CVE); embeddings use Chroma's default
`all-MiniLM-L6-v2`, not MedGemma.
Why: semantic search needs vectors; Postgres is the source of truth joined back
in after retrieval.
Status: active.

## 2026-10-24 — Dev-only auto-seed of trial data
Decision: `api/entrypoint.sh` auto-runs `ingest_trials` ONLY when settings are
development, the CSV exists, and the `Trial` table is empty. Production never
auto-seeds — trial data there is loaded deliberately.
Why: zero-friction `docker compose up` for the team in dev; keep data loading an
explicit, observable step in prod.
Status: active.

## 2026-10-24 — AI model: MedGemma via vLLM (OpenAI-compatible)
Decision: the engine's `model_client` points at MedGemma
(`google/medgemma-1.5-4b-it`) on a Hugging Face Inference Endpoint via LangChain
`ChatOpenAI`. Config via `MODEL_API_BASE_URL` (ends in `/v1`), `MODEL_API_KEY`,
`MODEL_NAME`. Empty base URL => model "unavailable" and the engine degrades
gracefully (never fabricates). MedGemma is a reasoning model, so the extractor's
JSON parser strips the thinking block and takes the last JSON object.
Why: hosted, OpenAI-compatible, medical-domain model without self-hosting.
Status: active.

## 2026-10-24 — Modular monolith for the backend
Decision: organize Django features as self-contained modules under `apps/`,
mounted under `/api/`, instead of one large app or separate services.
Why: keeps features isolated and easy to add during a hackathon while staying a
single deployable.
Status: active.

## 2026-10-24 — Email-based auth with SimpleJWT
Decision: custom `users.User` keyed on email; JWT auth with rotating, blacklisted
refresh tokens (15-min access, 7-day refresh).
Why: stateless auth that a SPA client can consume; rotation + blacklist limits
the blast radius of a leaked token.
Status: active.

## 2026-10-24 — Environment-driven settings
Decision: split settings into `base/development/production`, read config from env
via `django-environ`, keep secrets in `.env` (never committed).
Why: one image runs in every environment; secrets stay out of source.
Status: active.

## 2026-10-24 — PostgreSQL as the database
Decision: PostgreSQL via `psycopg` 3, configured through `DATABASE_URL`.
Why: robust relational store suitable for the app's data and for production.
Status: active.

## 2026-10-24 — Integration layer as pure functions
Decision: Ranking and clarification are pure functions with no external dependencies.
Why: Deterministic behavior, easy testing, no LLM calls for preference changes.
Status: active.

## 2026-10-24 — Three-valued eligibility uncertainty
Decision: Criterion status is always `met`, `conflict`, or `unknown`. Never binary eligible/ineligible.
Why: Unknown information must be explicitly tracked, not conflated with ineligibility.
Status: active.

## 2026-10-24 — Clinical conflicts cannot be overridden by convenience
Decision: Ranking always prioritizes clinical status over practical convenience.
Why: A nearby trial with a clinical conflict is still a conflict; safety first.
Status: active.

## 2026-10-24 — Privacy boundary for patient profiles
Decision: Patient profiles are sanitized for display; raw medical notes never exposed.
Why: Privacy-conscious design even for fictional demo data.
Status: active.

## 2026-10-24 — Integration layer as pure functions
Decision: Ranking and clarification are pure functions with no external dependencies.
Why: Deterministic behavior, easy testing, no LLM calls for preference changes.
Status: active.

## 2026-10-24 — Three-valued eligibility uncertainty
Decision: Criterion status is always `met`, `conflict`, or `unknown`. Never binary eligible/ineligible.
Why: Unknown information must be explicitly tracked, not conflated with ineligibility.
Status: active.

## 2026-10-24 — Clinical conflicts cannot be overridden by convenience
Decision: Ranking always prioritizes clinical status over practical convenience.
Why: A nearby trial with a clinical conflict is still a conflict; safety first.
Status: active.

## 2026-10-24 — Privacy boundary for patient profiles
Decision: Patient profiles are sanitized for display; raw medical notes never exposed.
Why: Privacy-conscious design even for fictional demo data.
Status: active.
