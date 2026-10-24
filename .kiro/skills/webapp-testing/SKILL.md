---
name: webapp-testing
description: Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.
license: Complete terms in LICENSE.txt
---

# Web Application Testing

## Using this skill

Read the [shared guide](../../AGENTS.md). Use this guidance only when its technical domain fits the task. Follow the target project's installed versions, architecture, and conventions; example tools, paths, and dependencies are options rather than required changes.

Verify application behavior with the existing test suite or available browser automation. Python Playwright is one option; JavaScript/TypeScript suites and supported browser interfaces are also valid.

## Workflow

1. Discover the intended app URL, frontend/backend services, startup commands, and test data from the project.
2. Reuse an existing server or start only the services required for the task.
3. Inspect the rendered page and use stable role/label locators. Wait for the relevant visible state, response, or application readiness signal. Do not require `networkidle`: streaming and polling apps may never become idle.
4. Exercise the requested user path and relevant loading, error, authorization, and validation behavior.
5. Use the project browser configuration. Headless mode suits routine checks; headed mode is useful when requested or for supported interactive debugging.
6. Capture relevant console errors, screenshots, or traces and close resources started by the test.

## Optional helpers and examples

Paths below are relative to this skill directory, not the application working directory:

- `scripts/with_server.py`: starts and stops one or more development servers around a test command. Read its `--help` and inspect the implementation if platform behavior or cleanup needs checking.
- `examples/element_discovery.py`: page element inspection.
- `examples/static_html_automation.py`: local HTML example.
- `examples/console_logging.py`: browser log example.

Run the helper using its resolved absolute path while keeping the application directory as the working directory. Adapt example shell syntax, ports, and output paths to the current operating system. If the helper does not fit the environment, use the project's server lifecycle tooling.

## Related guidance

- [playwright](../playwright/SKILL.md)
- [python-testing-patterns](../python-testing-patterns/SKILL.md)
