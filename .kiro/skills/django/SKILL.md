---
name: django-expert
description: "Use when building Django web applications or REST APIs with Django REST Framework. Invoke when working with settings.py, models.py, manage.py, or any Django project file. Creates Django models with proper indexes, optimizes ORM queries using select_related/prefetch_related, builds DRF serializers and viewsets, and configures JWT authentication. Trigger terms: Django, DRF, Django REST Framework, Django ORM, Django model, serializer, viewset, Python web."
license: MIT
metadata:
  author: https://github.com/Jeffallan
  company: https://synergetic.solutions
  version: "1.1.0"
  domain: backend
  triggers: Django, DRF, Django REST Framework, Django ORM, Django model, serializer, viewset, Python web
  role: specialist
  scope: implementation
  output-format: code
---

# Django Application Development

## Using this skill

Read the [shared guide](../../AGENTS.md). Apply this domain guidance with any capable assistant, editor, CLI, SDK, API, or supported UI. Follow installed versions and project conventions; examples do not require adopting their exact stack. Load related guidance only when its subject is part of the task.


## Workflow

1. Inspect the installed Django version, settings, models, database, and existing conventions.
2. Design models and constraints around actual access patterns. Follow the project's primary-key and authentication choices.
3. Generate and review migrations, including data migration and locking effects. Apply only to the intended authorized database.
4. Implement views or services with input validation, explicit permissions, and appropriate transaction boundaries.
5. Use select_related/prefetch_related for accessed relationships and indexes justified by queries.
6. Verify relevant behavior with the existing Django or pytest suite, including denied access and invalid input.

Keep secrets outside source, preserve CSRF protections where applicable, and parameterize raw SQL. Add authentication and authorization as part of endpoint design, before exposing protected behavior.

## Related guidance

- [django-backend](../../agents/django-backend/AGENTS.md)
- [django-rest-framework](../django-rest-framework/SKILL.md)
- [django-testing](../django-testing/SKILL.md)
- [postgreSQL](../postgreSQL/SKILL.md)
