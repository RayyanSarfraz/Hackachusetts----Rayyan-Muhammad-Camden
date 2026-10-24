# Model Gateway Integration

Use for LiteLLM or similar gateways that normalize access to model providers.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Inspect the existing provider configuration, SDK/proxy version, endpoint contract, and deployment topology.
- Preserve provider-specific capabilities explicitly, including streaming, tool calls, embeddings, usage, and error formats.
- Keep keys in the configured secret mechanism; redact logs and enforce tenant-level authorization and quotas where required.
- Configure bounded timeouts, retries, fallbacks, and budgets; account for duplicate requests and billing.
- Verify routing, authentication, rate limits, streaming termination, and failure handling with controlled tests.
- Use live provider calls only when authorized and necessary; report cost-bearing checks and any untested provider behavior.
- Follow the current repository's contribution conventions rather than a copied upstream branch or attribution policy.

## Related guidance

- [LLM Workflow Integration](../langchain/AGENTS.md)
- [Local Model Serving](../ollama/AGENTS.md)
- [Model and Dataset Workflows](../hugging-face/AGENTS.md)
- [Full Stack Architecture](../full-stack-architecture/AGENTS.md)
- [docker-project-foundations](../../skills/docker-project-foundations/SKILL.md)
