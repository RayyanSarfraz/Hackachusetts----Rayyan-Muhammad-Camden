# HTTP Client Integration

Use for applications that call HTTP APIs, including Axios integrations.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Inspect the existing HTTP client and runtime before choosing adapters or adding dependencies.
- Centralize base URLs, authentication, timeouts, and error normalization where the application benefits from shared behavior.
- Handle cancellation, network failures, non-success responses, and credential boundaries explicitly.
- Retry only suitable failures with bounded backoff; account for idempotency before retrying writes.
- Keep browser credentials and server secrets separate. Validate redirects and destinations for server-side requests.
- Verify request serialization, response handling, cancellation, and failure cases with the existing test framework.

## Related guidance

- [React Frontend](../react-frontend/AGENTS.md)
- [Django Backend](../django-backend/AGENTS.md)
- [Browser Testing and Automation](../playwright/AGENTS.md)
