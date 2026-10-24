# Full Stack Architecture

Use for work spanning frontend, backend, data, infrastructure, or model services.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Discover actual components, manifests, entry points, and deployment boundaries rather than assuming a monorepo layout.
- Define the user-visible behavior and API/data contracts before changing multiple components.
- Keep authentication, authorization, validation, error handling, and observability consistent across boundaries.
- Prefer existing libraries and deployment patterns; introduce services only when the requirements justify them.
- Plan schema and API changes for compatibility, migration order, rollback, and failure recovery.
- Verify each affected layer and at least one representative path across the changed boundaries.
- Share relevant contracts, changed files, validation evidence, and unresolved limitations when handing work between roles.

## Related guidance

- [React Frontend](../react-frontend/AGENTS.md)
- [Django Backend](../django-backend/AGENTS.md)
- [HTTP Client Integration](../axios/AGENTS.md)
- [Browser Testing and Automation](../playwright/AGENTS.md)
- [LLM Workflow Integration](../langchain/AGENTS.md)
- [Model Gateway Integration](../litellm/AGENTS.md)
- [Local Model Serving](../ollama/AGENTS.md)
- [Model and Dataset Workflows](../hugging-face/AGENTS.md)
- [Data Analysis and Transformation](../pandas/AGENTS.md)
- [aws](../../skills/aws/SKILL.md)
- [google-cloud](../../skills/google-cloud/SKILL.md)
- [docker-project-foundations](../../skills/docker-project-foundations/SKILL.md)
- [postgreSQL](../../skills/postgreSQL/SKILL.md)
