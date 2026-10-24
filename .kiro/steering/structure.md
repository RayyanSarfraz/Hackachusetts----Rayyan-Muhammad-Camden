---
inclusion: always
---

# Project Structure

Part of the [unified team agent memory](team-agent-memory.md). Records file
organization and naming conventions. Update when the layout changes.

## Top level

```
.
├── api/            # Django REST backend
├── client/         # frontend (empty / not yet scaffolded)
├── .kiro/          # agents, skills, and steering (team memory)
├── audit_guidance.py
├── skills-lock.json
└── README.md
```

## Backend (`api/`)

```
api/
├── manage.py
├── requirements.txt
├── .env / .env.example
├── config/                 # project configuration
│   ├── settings/           # base.py, development.py, production.py
│   ├── urls.py             # root URLConf, mounts modules under /api/
│   ├── asgi.py / wsgi.py
└── apps/                   # feature modules (modular monolith)
    └── users/              # email auth + JWT
        ├── models.py  serializers.py  views.py  urls.py
        ├── admin.py   apps.py        tests.py
        └── migrations/
```

## Conventions

- **Modular monolith.** Each feature is a self-contained module under `apps/`
  with its own `models`, `views`, `serializers`, `urls`, `admin`, and
  `migrations`. `apps/` is on `sys.path`, so import modules as `apps.<module>`.
- **URL mounting.** Each module exposes its own URLConf; `config/urls.py` mounts
  them under the `/api/` prefix (e.g. `/api/users/`).
- **Settings split.** Shared config in `config/settings/base.py`; environment
  overrides in `development.py` / `production.py`. `BASE_DIR` is the `api/` folder.
- **New feature module checklist:** create `apps/<name>/`, add it to `LOCAL_APPS`
  in `base.py`, give it a `urls.py`, and mount it in `config/urls.py`.
