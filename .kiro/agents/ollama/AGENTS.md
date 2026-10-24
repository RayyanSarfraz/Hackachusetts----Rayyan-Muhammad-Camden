# Local Model Serving

Use for Ollama-based local inference and application integration.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Inspect the installed runtime, available models, hardware, and application endpoint settings.
- Choose model size and quantization based on memory, context, latency, and task quality rather than a fixed GPU assumption.
- Keep model identifiers and endpoint configuration explicit; confirm the requested API capabilities and streaming format.
- Restrict network exposure according to the deployment requirements; use access controls for shared serving.
- Handle model loading, unavailable models, timeouts, cancellation, and resource exhaustion.
- Verify representative inference and application failure paths. Record model/version and hardware when comparing performance.
- Build the model runtime from source only when the task requires it; discover source build commands in that repository.

## Related guidance

- [Model and Dataset Workflows](../hugging-face/AGENTS.md)
- [Model Gateway Integration](../litellm/AGENTS.md)
- [LLM Workflow Integration](../langchain/AGENTS.md)
- [docker-project-foundations](../../skills/docker-project-foundations/SKILL.md)
- [lambda-cloud](../../skills/lambda-cloud/SKILL.md)
