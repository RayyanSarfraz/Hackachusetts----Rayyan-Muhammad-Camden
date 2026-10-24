---
name: shadcn
description: Manages shadcn components and projects — adding, searching, fixing, debugging, styling, and composing UI, including chat interfaces. Provides project context, component docs, and usage examples. Applies when working with shadcn/ui, component registries, presets, --preset codes, or any project with a components.json file. Also triggers for "shadcn init", "create an app with --preset", "switch to --preset", and for building a design system or applying a DESIGN.md or brand spec to shadcn/ui.
---

# shadcn/ui Integration

## Using this skill

Read the [shared guide](../../AGENTS.md). Use this guidance only when its technical domain fits the task. Follow the target project's installed versions, architecture, and conventions; example tools, paths, and dependencies are options rather than required changes.

Use this skill when the project already uses shadcn/ui or the user has selected it. It is not a requirement to replace another component library or initialize a new application.

## Discover the project

- Inspect `components.json`, dependency versions, installed component source, import aliases, Tailwind configuration, and the existing design system.
- If supported by the selected CLI version, run `shadcn info --json` using the project's package runner. This file does not execute commands or inject project context automatically.
- Match the existing package manager and compatible CLI version. Use official docs, installed source, CLI help, or a supported documentation interface to confirm APIs.

## Implementation

- Reuse existing components and theme tokens. Preserve the user's visual requirements and local component customizations.
- Check the actual primitive library and installed component props before choosing Radix/Base UI composition, loading indicators, form controls, or icon APIs.
- Use semantic form grouping, labels, validation, accessible dialog titles, focus management, and keyboard behavior.
- Apply layout and styling conventions already used by the project. The bundled rules describe specific component versions and design preferences; adopt them where compatible, rather than treating every preference as universal.
- Use chat primitives only if those components are installed and suit the product. A chat interface does not require a particular tracing or message library.

## Adding or updating components

1. Inspect installed source and configured registries before adding components. Use the configured/default registry unless the request requires another source.
2. Preview changes with supported dry-run/diff options or a temporary comparison, and review generated imports, dependencies, and styles.
3. Preserve local changes and apply only the requested update. Existing authorization covers the requested changes; clarify only when a choice would discard work outside that scope.
4. Initialize projects, switch presets, install all components, or overwrite customizations only when those changes are part of the task.
5. Verify relevant type, lint, accessibility, and browser behavior with the project's available checks.

## Supporting references

- [CLI reference](cli.md): inspect supported commands against the installed version.
- [Styling](rules/styling.md), [forms](rules/forms.md), [composition](rules/composition.md), [icons](rules/icons.md), and [chat](rules/chat.md): version-specific patterns and examples.
- [Base UI and Radix](rules/base-vs-radix.md): primitive-specific API differences.
- [Design system workflow](design-system.md) and [showcase page](design-system-page.md): only for a requested design-system build; preserve the existing app and install only needed components.

## Related guidance

- [frontend-design](../frontend-design/SKILL.md)
- [vercel-composition-patterns](../vercel-composition-patterns/SKILL.md)
- [web-design-guidelines](../web-design-guidelines/SKILL.md)
