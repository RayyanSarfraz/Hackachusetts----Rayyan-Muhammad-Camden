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
- Database: PostgreSQL via `psycopg[binary]` `3.2.10`.
- CORS: `django-cors-headers` `4.9.0`.
- Config: `django-environ` `0.12.0` (settings read from env; see `.env.example`).
- WSGI server: `gunicorn` `23.0.0`.
- Dependencies pinned in `api/requirements.txt`.

## Frontend (`client/`)

- Not yet scaffolded. CORS defaults point at a Vite dev server
  (`http://localhost:5173`), which suggests a Vite-based client is intended, but
  nothing is committed yet. Confirm before assuming a framework.

## Configuration

- Settings are environment-driven. `DJANGO_SETTINGS_MODULE` selects
  `config.settings.development` or `config.settings.production`.
- Required keys live in `api/.env.example`. Never read, echo, or commit values
  from `api/.env`; reference keys by name.

## Common commands (run from `api/`)

PowerShell on Windows — chain with `;`, not `&&`.

```powershell
python manage.py runserver        # start the dev server (run manually, not via agent)
python manage.py migrate          # apply migrations
python manage.py makemigrations   # create migrations after model changes
python manage.py test             # run the Django test suite
python manage.py createsuperuser  # create an admin user
```

Install dependencies: `pip install -r requirements.txt` (from `api/`).
