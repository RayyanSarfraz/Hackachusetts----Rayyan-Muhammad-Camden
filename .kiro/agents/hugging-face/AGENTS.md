# Model and Dataset Workflows

Use for Hugging Face models, datasets, inference, training, and artifact preparation.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Identify the task, model/dataset revision, license, access requirements, and available compute.
- Use the installed SDK, CLI, API, or console appropriate to the task; do not require unavailable skill packages.
- Inspect model and dataset cards. Pin revisions for reproducibility and treat remote code as executable code requiring review.
- Separate training, validation, and test data; check leakage, preprocessing, tokenizer compatibility, and evaluation metrics.
- Estimate memory and runtime from the workload; verify precision and quantization compatibility on the target hardware.
- Keep tokens out of source and logs. Preserve artifact provenance, checkpoints, configuration, and evaluation evidence.
- Publish artifacts or provision paid compute only within the user's authorized scope.

## Related guidance

- [Data Analysis and Transformation](../pandas/AGENTS.md)
- [Local Model Serving](../ollama/AGENTS.md)
- [LLM Workflow Integration](../langchain/AGENTS.md)
- [Model Gateway Integration](../litellm/AGENTS.md)
- [lambda-cloud](../../skills/lambda-cloud/SKILL.md)
- [aws](../../skills/aws/SKILL.md)
- [docker-project-foundations](../../skills/docker-project-foundations/SKILL.md)
