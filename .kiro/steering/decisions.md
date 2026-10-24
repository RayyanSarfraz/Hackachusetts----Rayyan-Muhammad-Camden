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
