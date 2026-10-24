# Browser Testing and Automation

Use for browser behavior verification and Playwright test suites.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Inspect the application test configuration and available browser interface before selecting commands.
- Use the existing runner, fixtures, base URL, and supported browsers. Do not assume the Playwright upstream source layout.
- Prefer role, label, and stable test-id locators; use observable assertions and automatic waits rather than fixed sleeps.
- Keep tests isolated with controlled data and explicit cleanup. Protect credentials and avoid unintended external writes.
- Exercise relevant user paths, permissions, validation, and error states; capture useful traces or screenshots on failures.
- Report the tested environment and observed results. A screenshot alone does not establish backend correctness.
- A browser API, CLI, or automation connector may be used when available; no particular assistant integration is required.

## Related guidance

- [React Frontend](../react-frontend/AGENTS.md)
- [HTTP Client Integration](../axios/AGENTS.md)
- [Full Stack Architecture](../full-stack-architecture/AGENTS.md)
