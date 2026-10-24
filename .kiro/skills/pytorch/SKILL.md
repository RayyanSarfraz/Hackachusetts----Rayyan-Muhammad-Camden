---
name: pytorch
description: PyTorch deep learning development with transformers, diffusion models, and GPU optimization.
metadata:
  maintainer: Mindrally
  source: https://github.com/Mindrally/skills
---

# PyTorch Development

## Using this skill

Read the [shared guide](../../AGENTS.md). Use this guidance only when its technical domain fits the task. Follow the target project's installed versions, architecture, and conventions; example tools, paths, and dependencies are options rather than required changes.

You are an expert in deep learning with PyTorch, transformers, and diffusion models.

## Core Principles

- Write concise, technical code with accurate examples
- Prioritize clarity and efficiency in deep learning workflows
- Use object-oriented programming for model architectures
- Select CPU/GPU execution and precision from supported hardware and workload needs

## Model Development

### Custom Modules
- Implement custom `nn.Module` classes for architectures
- Use `forward` method for forward pass logic
- Initialize weights properly in `__init__`
- Register buffers for non-parameter tensors

### Autograd
- Leverage automatic differentiation
- Use `torch.no_grad()` for inference
- Implement custom autograd functions when needed
- Handle gradient accumulation properly

## Transformers Integration

- Use the existing compatible model library; Hugging Face Transformers is an option for supported pretrained models
- Implement attention mechanisms correctly
- Apply efficient fine-tuning (LoRA, P-tuning)
- Handle tokenization and sequences properly

## Diffusion Models

- Use Diffusers when compatible with the selected diffusion workflow
- Implement forward/reverse diffusion processes
- Utilize appropriate noise schedulers
- Understand pipeline variants (SDXL, etc.)

## Training Best Practices

### Data Loading
- Implement efficient DataLoaders
- Use proper train/validation/test splits
- Apply data augmentation appropriately
- Handle large datasets with streaming

### Optimization
- Apply learning rate scheduling
- Implement early stopping
- Use gradient clipping for stability
- Handle NaN/Inf values properly

## Performance Optimization

- Use the project-compatible distributed strategy when multiple GPUs are required
- Implement gradient accumulation for large batches
- Use the installed PyTorch version's supported automatic mixed precision API when hardware and numerical requirements permit it
- Profile code to identify bottlenecks

## Gradio Integration

- Create an interactive demo only when the requested output calls for one
- Build user-friendly interfaces
- Handle errors gracefully in demos

## Related guidance

- [transformers](../transformers/SKILL.md)
- [train-sentence-transformers](../train-sentence-transformers/SKILL.md)
- [lambda-cloud](../lambda-cloud/SKILL.md)
