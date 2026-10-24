---
inclusion: always
---

# Technology Stack

Part of the [unified team agent memory](team-agent-memory.md). Records the stack,
versions, and common commands. Prefer installed versions and lockfiles over this
list when they disagree, then update this file.

## Backend (`api/`)

- Python / Django `6.0.5`.
- Django REST Framework `3.18.0`.
- Auth: `djangorestframework-simplejwt` `5.5.1` (JWT, rotating + blacklisted
  refresh tokens).
- Database: PostgreSQL via `psycopg[binary]` `3.2.10`. **All models use UUID
  primary keys** (see decisions.md 2026-10-24).
- CORS: `django-cors-headers` `4.9.0`.
- Config: `django-environ` `0.12.0` (settings read from env; see `.env.example`).
- WSGI server: `gunicorn` `23.0.0`.
- AI orchestration: `langchain` `1.4.7` + `langchain-openai` `1.7.2` pointed at
  MedGemma (vLLM, OpenAI-compatible). Vector store: `chromadb` `1.5.9` (local
  persistent client). `huggingface_hub` `0.36.2`.
- Dependencies pinned in `api/requirements.txt`.

## Frontend (`client/`)

- Scaffolded: React 19 + TypeScript + Vite + Tailwind (Vitest tests). Dev server
  on `http://localhost:5173`; the Vite dev proxy forwards `/api` to the backend.

## Configuration

- Settings are environment-driven. `DJANGO_SETTINGS_MODULE` selects
  `config.settings.development` or `config.settings.production`.
- Required keys live in `api/.env.example`. Never read, echo, or commit values
  from `api/.env`; reference keys by name.
- `api/.env` is the single source for `MODEL_*` / `CHROMA_COLLECTION` on host
  runs and in Docker (it is bind-mounted into the api container). Don't add
  those keys to `compose.yaml` `environment:`: compose values, even empty ones,
  shadow `api/.env`. The root `.env` only feeds compose (Postgres, Django).

## Common commands (run from `api/`)

PowerShell on Windows — chain with `;`, not `&&`.

```powershell
python manage.py runserver        # start the dev server (run manually, not via agent)
python manage.py migrate          # apply migrations
python manage.py test             # run the Django test suite
python manage.py createsuperuser  # create an admin user
python manage.py ingest_trials ../data/trials/data.csv   # load trial data -> Postgres + ChromaDB
```

Install dependencies: `pip install -r requirements.txt` (from `api/`).

## First-run / after-pull: reset the DB (UUID PK change)

PKs were switched to UUID and the initial migrations were regenerated, so an
existing int-PK database is incompatible. Reset once before running:

```powershell
docker compose down -v ; docker compose up --build   # Docker: drops volumes, re-migrates, dev auto-seeds trials
```

Host Postgres: drop/recreate the DB, then `migrate` and `ingest_trials`.

## Gotchas

- `python manage.py makemigrations` that "hangs" with no output is waiting on
  an interactive question (rename / default-value prompts) the agent shell
  can't display. Run it in an interactive terminal, or use `--noinput` to get
  the error instead of a hang. Don't hand-write migrations with
  `MigrationWriter`: that skips those questions.
- Running `manage.py` on the host needs a reachable Postgres; for DB-free unit
  tests use `$env:DATABASE_URL="sqlite://:memory:"`.
- Trial ingestion downloads the ChromaDB default embedder (`all-MiniLM-L6-v2`,
  ~79MB) on first use; needs network once.
