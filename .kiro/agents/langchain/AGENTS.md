# LLM Workflow Integration

Use for LangChain applications, retrieval, and tool-enabled model workflows.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Inspect installed package versions and existing model, prompt, retriever, and persistence interfaces.
- Keep provider access separate from orchestration so models and serving endpoints can be changed deliberately.
- Define explicit input/output schemas, tool argument validation, timeouts, cancellation, and bounded retries.
- Treat retrieved documents and model output as untrusted data; enforce authorization outside prompts.
- For retrieval, track document provenance, chunking, embedding version, filtering, and evaluation data.
- Bound agent loops and tool access. Tool calls must stay within the user's authorization.
- Test deterministic transformations and failure handling locally; use controlled integration evaluation when provider behavior matters.

## Related guidance

- [Model Gateway Integration](../litellm/AGENTS.md)
- [Local Model Serving](../ollama/AGENTS.md)
- [Model and Dataset Workflows](../hugging-face/AGENTS.md)
- [Data Analysis and Transformation](../pandas/AGENTS.md)
- [Full Stack Architecture](../full-stack-architecture/AGENTS.md)
- [postgreSQL](../../skills/postgreSQL/SKILL.md)
