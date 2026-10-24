---
name: lambda-labs
description: On-demand GPU cloud instances for ML training.
version: 1.0.0
author: Orchestra Research
license: MIT
platforms: [linux, macos, windows]
---

# GPU Cloud Workloads

## Using this skill

Read the [shared guide](../../AGENTS.md). Apply this domain guidance with any capable assistant, editor, CLI, SDK, API, or supported UI. Follow installed versions and project conventions; examples do not require adopting their exact stack. Load related guidance only when its subject is part of the task.


## Workflow

- Use this skill for Lambda GPU Cloud workloads; apply its planning principles to another provider only when that provider is selected.
- Inspect workload requirements, model memory, precision, dataset size, runtime, region, and persistence needs.
- Discover current instance availability, pricing, API schema, and storage lifecycle from the chosen provider before provisioning. Do not rely on fixed price or hardware tables.
- Use the available console, CLI, SDK, or HTTP API with scoped credentials. Do not require a specific assistant or third-party client package.
- Estimate cost and use the user's authorized budget and resource scope before launching compute.
- Separate persistent datasets/checkpoints from ephemeral scratch storage; verify restore behavior before terminating resources.
- Check drivers, framework and accelerator compatibility, GPU visibility, distributed networking, and a small representative workload before scaling.
- Record instance identifiers, configuration, checkpoints, logs, and cleanup responsibilities. Terminate or retain resources according to the authorized lifecycle.

Official service documentation: https://docs.lambda.ai

## Related guidance

- [hugging-face](../../agents/hugging-face/AGENTS.md)
- [ollama](../../agents/ollama/AGENTS.md)
- [docker-project-foundations](../docker-project-foundations/SKILL.md)
