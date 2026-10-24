# React Frontend

Use for React interfaces in any compatible application framework.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Read the package manifest, routing, component system, styles, and existing state management before making changes.
- Follow the installed React/framework APIs; do not mandate a specific framework version, compiler, design library, or directory layout.
- Keep state close to its owner, effects for external synchronization, and server/client boundaries explicit.
- Handle loading, empty, error, success, and disabled states. Use semantic elements, labels, keyboard access, and responsive layouts.
- Validate user input while retaining server-side validation and authorization for protected operations.
- Reuse the existing API client and visual components; add dependencies only for a demonstrated need.
- Run the available type, lint, and relevant component/browser checks for the affected behavior.

## Related guidance

- [HTTP Client Integration](../axios/AGENTS.md)
- [Browser Testing and Automation](../playwright/AGENTS.md)
- [Django Backend](../django-backend/AGENTS.md)
- [Full Stack Architecture](../full-stack-architecture/AGENTS.md)
