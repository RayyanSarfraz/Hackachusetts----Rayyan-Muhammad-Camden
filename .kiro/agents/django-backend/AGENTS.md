# Django Backend

Use for Django applications and Django REST Framework APIs.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Inspect settings, models, URL routing, authentication, database backend, and installed versions first.
- Follow existing model identifiers, timestamps, service boundaries, and response conventions; do not impose a particular product schema or JSON:API format.
- Validate input and enforce authorization and tenant isolation on both collection and object access.
- Create migrations for model changes; inspect migration SQL and backfill/locking effects before applying to shared databases.
- Use transactions for related writes and select_related/prefetch_related where access patterns justify them.
- Verify successful requests, invalid input, anonymous access, object ownership, and relevant query behavior.

## Related guidance

- [Full Stack Architecture](../full-stack-architecture/AGENTS.md)
- [React Frontend](../react-frontend/AGENTS.md)
- [django](../../skills/django/SKILL.md)
- [django-rest-framework](../../skills/django-rest-framework/SKILL.md)
- [django-testing](../../skills/django-testing/SKILL.md)
- [postgreSQL](../../skills/postgreSQL/SKILL.md)
- [docker-project-foundations](../../skills/docker-project-foundations/SKILL.md)
