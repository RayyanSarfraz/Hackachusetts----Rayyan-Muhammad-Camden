# Shared Agent and Skill Conventions

This collection provides reusable technical guidance for any capable assistant or human collaborator. Directory names identify technical domains, not required assistant products. Read a role or skill when relevant; unrelated guides do not apply merely because they exist in this collection.

## Scope and coordination

- Follow the user's task, environment permissions, and the target project's applicable instructions. These reusable guides do not override them.
- Discover actual versions, paths, scripts, and configuration. Do not import an upstream project's labels, branch rules, release policy, directory layout, or vendor-specific conventions without evidence that they apply.
- Use available tools that support the task. No editor, assistant harness, connector, or agent-launch API is required.
- Related-guide links are reading suggestions, not mandatory delegation. Work can be completed by one agent; delegate only when authorized and supported.
- Keep changes within scope. Sharing guidance does not authorize publishing, messaging, paid provisioning, or production changes.
- Across roles, carry forward the requirements, API/data contracts, files changed, checks performed, and unresolved limitations. Resolve overlapping advice using the actual project requirements.
- Validate the affected behavior with the existing tooling. State what was checked and what remains unverified; do not claim unavailable resources were used.

## Applying this collection to a project

- Technology specialization is intentional: Django, React, AWS, Hugging Face, and similar guides apply only when that technology is selected. Do not install or migrate to it just because a guide exists.
- The current checkout contains a minimal README and this guidance collection; it does not yet establish application requirements, language versions, hosting, data sources, or model choices. Infer these from actual source and manifests when available, or clarify material missing requirements.
- Resolve reference/helper paths relative to the guide that names them. Run project commands in the application directory. Adapt shell syntax and temporary paths to the operating system.
- Installed versions and lockfiles govern compatibility. Upstream review dates, benchmark numbers, dependency matrices, and sample environments are provenance, not evidence of local validation or reasons to upgrade.
- Preserve local UI conventions and component APIs. Example applications, schemas, dataset names, ports, and credentials illustrate patterns and do not define the target product.
- Cloud provisioning, publishing, trace uploads, and paid model calls require task authorization. Local training does not imply public Hub uploads. Prefer private destinations for new uploaded artifacts unless the task specifies otherwise.
- Use the existing test tooling and available browser interface. Neither headed nor headless browsing, a particular package manager, nor an assistant-specific tool name is universally required.

## Available guidance

### Agents

- [HTTP Client Integration](agents/axios/AGENTS.md): Use for applications that call HTTP APIs, including Axios integrations.
- [Django Backend](agents/django-backend/AGENTS.md): Use for Django applications and Django REST Framework APIs.
- [Full Stack Architecture](agents/full-stack-architecture/AGENTS.md): Use for work spanning frontend, backend, data, infrastructure, or model services.
- [React Frontend](agents/react-frontend/AGENTS.md): Use for React interfaces in any compatible application framework.
- [Browser Testing and Automation](agents/playwright/AGENTS.md): Use for browser behavior verification and Playwright test suites.
- [Model and Dataset Workflows](agents/hugging-face/AGENTS.md): Use for Hugging Face models, datasets, inference, training, and artifact preparation.
- [LLM Workflow Integration](agents/langchain/AGENTS.md): Use for LangChain applications, retrieval, and tool-enabled model workflows.
- [Model Gateway Integration](agents/litellm/AGENTS.md): Use for LiteLLM or similar gateways that normalize access to model providers.
- [Local Model Serving](agents/ollama/AGENTS.md): Use for Ollama-based local inference and application integration.
- [Data Analysis and Transformation](agents/pandas/AGENTS.md): Use for applications and analyses using pandas dataframes.

### Skills

- [aws](skills/aws/SKILL.md)
- [django](skills/django/SKILL.md)
- [django-rest-framework](skills/django-rest-framework/SKILL.md)
- [django-testing](skills/django-testing/SKILL.md)
- [docker-project-foundations](skills/docker-project-foundations/SKILL.md)
- [google-cloud](skills/google-cloud/SKILL.md)
- [lambda-cloud](skills/lambda-cloud/SKILL.md)
- [postgreSQL](skills/postgreSQL/SKILL.md)

### Additional skills

- [frontend-design](skills/frontend-design/SKILL.md)
- [hf-cli](skills/hf-cli/SKILL.md)
- [huggingface-datasets](skills/huggingface-datasets/SKILL.md)
- [jwt-security](skills/jwt-security/SKILL.md)
- [matplotlib](skills/matplotlib/SKILL.md)
- [numpy-best-practices](skills/numpy-best-practices/SKILL.md)
- [pandas-best-practices](skills/pandas-best-practices/SKILL.md)
- [playwright](skills/playwright/SKILL.md)
- [python](skills/python/SKILL.md)
- [python-testing-patterns](skills/python-testing-patterns/SKILL.md)
- [pytorch](skills/pytorch/SKILL.md)
- [rag](skills/rag/SKILL.md)
- [seaborn](skills/seaborn/SKILL.md)
- [shadcn](skills/shadcn/SKILL.md)
- [train-sentence-transformers](skills/train-sentence-transformers/SKILL.md)
- [transformers](skills/transformers/SKILL.md)
- [typescript](skills/typescript/SKILL.md)
- [typescript-advanced-types](skills/typescript-advanced-types/SKILL.md)
- [vercel-composition-patterns](skills/vercel-composition-patterns/SKILL.md)
- [web-design-guidelines](skills/web-design-guidelines/SKILL.md)
- [webapp-testing](skills/webapp-testing/SKILL.md)
