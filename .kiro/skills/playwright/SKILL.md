---
name: playwright
description: Browser automation and E2E testing with Playwright. Auto-detects dev servers, writes clean test scripts. Test pages, fill forms, take screenshots, check responsive design, validate UX, test login flows, check links, automate any browser task. Use for cross-browser testing, visual regression, API testing, component testing in TypeScript/JavaScript and Python projects.
license: MIT
---

# Playwright Browser Testing

## Using this skill

Read the [shared guide](../../AGENTS.md). Use this guidance only when its technical domain fits the task. Follow the target project's installed versions, architecture, and conventions; example tools, paths, and dependencies are options rather than required changes.

Use Playwright for browser automation and end-to-end tests when it fits the project. JavaScript, TypeScript, and Python workflows are supported; follow the existing suite rather than requiring a bundled runner.

## Workflow

1. Inspect the project test configuration, package manager, supported browsers, and application startup commands.
2. Use the provided URL or the configured test server. If necessary, identify the correct running service from project evidence; a port scan alone does not establish which app to test.
3. Reuse the project's fixtures and test runner. For temporary automation, use a writable temporary directory appropriate to the operating system. Keep durable regression tests in the project's test directory.
4. Select headless mode for routine automated checks and headed mode when requested or helpful for interactive debugging and supported by the environment. Neither mode is mandatory for all tasks.
5. Prefer role/label locators and observable assertions. Wait for the relevant element or response rather than fixed sleeps or global network inactivity.
6. Keep contexts and test data isolated, close resources, and avoid unintended external changes. Run independent tests concurrently only when their data and environment permit it.
7. Check the affected success and failure paths. Record the environment, actual results, and useful traces/screenshots.

## Optional bundled helpers

Resolve paths relative to this skill's directory. Inspect the helper interface and source when needed; use it only if it fits the task.

- `run.js`: optional JavaScript automation runner.
- `lib/helpers.js`: optional server discovery and browser helpers.
- [API reference](references/API_REFERENCE.md): selectors, network interception, authentication, traces, and other detailed examples.

Helpers are alternatives to the existing runner, not prerequisites. Example ports, credentials, output paths, package managers, and browser options must be adapted. Use the project's dependency and install policy; do not change global package-manager settings or require a separate dependency-audit skill.

## Related guidance

- [webapp-testing](../webapp-testing/SKILL.md)
- [web-design-guidelines](../web-design-guidelines/SKILL.md)
