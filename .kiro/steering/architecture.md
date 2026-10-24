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
  identifier; `username` is removed.
- SimpleJWT with short-lived access tokens (15 min) and rotating refresh tokens
  (7 days) that are blacklisted after rotation. Algorithm HS256, signed with
  `SECRET_KEY`, `Bearer` auth header.
- Endpoints: `POST /api/users/auth/register/`, `/auth/login/`, `/auth/refresh/`,
  `/auth/logout/`, and `GET /api/users/me/`.

### Configuration & environments

- Twelve-factor style: one image, behavior driven by environment variables via
  `django-environ`. `base.py` holds shared settings; `development.py` /
  `production.py` override per environment.
- `DATABASE_URL` configures PostgreSQL.

## Frontend

- Planned under `client/` (not yet built). CORS is pre-configured for a Vite dev
  server at `http://localhost:5173`. The client is expected to authenticate via
  JWT (store/refresh tokens, send `Authorization: Bearer <access>`). Confirm the
  framework and token-storage approach before implementing.

## Cross-cutting

- CORS restricts browser origins to the configured allowlist
  (`DJANGO_CORS_ALLOWED_ORIGINS`).
- Keep secrets out of source. The committed default `SECRET_KEY` is for local use
  only and must be overridden in production.
