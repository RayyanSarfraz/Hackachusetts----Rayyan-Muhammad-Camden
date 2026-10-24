---
name: train-sentence-transformers
description: Train or fine-tune sentence-transformers models across `SentenceTransformer` (bi-encoder, dense or static embedding model for retrieval, similarity, clustering, classification, paraphrase mining, dedup, multimodal), `CrossEncoder` (reranker, pair scoring for two-stage retrieval / pair classification), `SparseEncoder` (SPLADE, sparse embedding model for learned-sparse retrieval), and `MultiVectorEncoder` (ColBERT / late-interaction, per-token embeddings scored with MaxSim). Covers loss selection, hard-negative mining, evaluators, distillation, LoRA, Matryoshka, and Hugging Face Hub publishing. Use for any sentence-transformers training task.
---

# Train a sentence-transformers Model

## Using this skill

Read the [shared guide](../../AGENTS.md). Use this guidance only when its technical domain fits the task. Follow the target project's installed versions, architecture, and conventions; example tools, paths, and dependencies are options rather than required changes.

**This SKILL.md is a router, not a manual.** It tells you which references and example scripts to load for your task. The actual content (recommended losses, evaluators, training-script structure, model selection, training-arg knobs, troubleshooting) lives in `references/` and `scripts/`.

Inspect the relevant per-type template (`scripts/train_<type>_example.py`) before building a new training workflow. Reuse the project's existing trainer when suitable; adapt the template rather than requiring a wholesale copy. The templates contain load-bearing scaffolding (autocast helper, model-card class, logger silencing list, `force=True`, `seed`, TF32, version-compatible imports, named-evaluator metric handling) that prior agent runs have repeatedly missed when rolling their own from a synthesized snippet.

## 1. Identify the model type

| Tag | Class | What it does | When to pick |
|---|---|---|---|
| **[SentenceTransformer]** | `SentenceTransformer` (bi-encoder) | Maps each input to a fixed-dim dense vector | Retrieval, similarity, clustering, classification, paraphrase mining, dedup |
| **[CrossEncoder]** | `CrossEncoder` (reranker) | Scores `(query, passage)` pairs jointly | Two-stage retrieval (rerank top-100 from bi-encoder), pair classification |
| **[SparseEncoder]** | `SparseEncoder` (SPLADE) | Sparse vectors over the vocabulary | Learned-sparse retrieval, inverted-index backends (Elasticsearch / OpenSearch / Lucene) |
| **[MultiVectorEncoder]** | `MultiVectorEncoder` (ColBERT) | One embedding per token, scored with MaxSim | Late-interaction retrieval, recall gains over bi-encoders at higher storage cost, multimodal (ColPali / ColQwen2) |

Tiebreakers when the request is ambiguous: "embedding model" / "vector search" / "similarity" → **[SentenceTransformer]**. "rerank" / "ranker" / "two-stage" → **[CrossEncoder]**. "SPLADE" / "sparse" / "inverted index" → **[SparseEncoder]**. "ColBERT" / "late interaction" / "multi-vector" / "MaxSim" / "ColPali" / "ColQwen" → **[MultiVectorEncoder]**. If still unclear, ask.

## 2. Required reading

Read the references needed for the selected model type, data format, and training behavior. Unrelated modes do not need to be loaded.

### Per-type: always required

**[SentenceTransformer]**
- `references/losses_sentence_transformer.md`: loss-to-data-shape mapping, `BatchSamplers.NO_DUPLICATES` requirement for MNRL-family, `Cached*` ↔ `gradient_checkpointing` incompatibility.
- `references/evaluators_sentence_transformer.md`: evaluator-to-task mapping, `metric_for_best_model` key construction (named vs unnamed), per-evaluator `primary_metric` values.
- `references/model_architectures.md`: encoder vs decoder vs static vs Router pipelines, pooling rules (mean / cls / lasttoken), auto-mean-pooling behavior for fresh-start MLM bases.
- `scripts/train_sentence_transformer_example.py`: production template. Copy this as your starting point.

**[CrossEncoder]**
- `references/losses_cross_encoder.md`: pointwise / pairwise / listwise / distillation, `pos_weight` derivation, `activation_fn=Identity()` mandatory for non-BCE losses (silent eval-rank collapse otherwise).
- `references/evaluators_cross_encoder.md`: `CrossEncoderRerankingEvaluator` recipe, named-evaluator key format `eval_{name}_{primary_metric}`.
- `scripts/train_cross_encoder_example.py`: production template. Copy this as your starting point.

**[SparseEncoder]**
- `references/losses_sparse_encoder.md`: `SpladeLoss` wrapper requirement, FLOPS regularizer weights, smoke-test active-dim ramp behavior.
- `references/evaluators_sparse_encoder.md`: `SparseNanoBEIREvaluator` (English-only) and the in-domain alternative, `eval_{name}_{primary_metric}` key format.
- `scripts/train_sparse_encoder_example.py`: production template. Copy this as your starting point.

**[MultiVectorEncoder]**
- `references/losses_multi_vector_encoder.md`: MaxSim scoring, scale choice per scoring mode (`scale=1.0` for MaxSim, roughly the average query length for MeanMaxSim), MNRL / CachedMNRL / MarginMSE / DistillKLDiv, XTR-vs-ColBERT scoring, CachedMNRL ↔ `gradient_checkpointing` incompatibility.
- `references/evaluators_multi_vector_encoder.md`: `MultiVectorNanoBEIREvaluator` (English-only) and the in-domain alternative, `eval_NanoBEIR_mean_maxsim_ndcg@10` key format, distillation-eval spearman variant.
- `scripts/train_multi_vector_encoder_example.py`: production template. Copy this as your starting point.

### Cross-cutting: select for the task

- `references/training_args.md`: `TrainingArguments` knobs, precision rules (load fp32 + autocast bf16/fp16, never `torch_dtype=bfloat16`), `warmup_steps` (float) vs deprecated `warmup_ratio`, `save_steps` must be a multiple of `eval_steps` for `load_best_model_at_end`, schedulers, HPO, tracker, resume, hub-push variants.
- `references/dataset_formats.md`: column-matching rules (label name auto-detection, column-order-not-name), reshaping recipes, hard-negative mining options.
- `references/base_model_selection.md`: discovery commands, per-type model namespaces, ModernBERT-family `max_seq_length=8192` trap, `datasets >= 4` script-loader rejection, non-English starting-point shortcuts.
- `references/troubleshooting.md`: symptom-indexed failure recipes. Consult the relevant symptoms when diagnosing a problem. The "Metrics don't improve" and "Hub push fails" entries cover bugs that bite frequently and are cheaper to recognize before they fire than to debug after.

### Cross-cutting: load when applicable

- `references/hardware_guide.md`: VRAM sizing, multi-GPU, FSDP / DeepSpeed, HF Jobs flavors. Required for >24GB models, multi-GPU, or HF Jobs runs.
- `references/hf_jobs_execution.md`: required when running on HF Jobs.
- `references/prompts_and_instructions.md`: required when using prompt-tuned bases (E5, BGE, GTE, Qwen3-Embedding, Instructor, Nomic, etc.) or adding `query: ` / `passage: ` style prefixes.

### Variant scripts (open when the task matches)
- **[SentenceTransformer]** `scripts/train_sentence_transformer_<matryoshka|multi_dataset|with_lora|distillation|make_multilingual|static_embedding>_example.py`.
- **[CrossEncoder]** `scripts/train_cross_encoder_<distillation|listwise>_example.py`.
- **[SparseEncoder]** `scripts/train_sparse_encoder_distillation_example.py`.
- Hard-negative mining CLI: `scripts/mine_hard_negatives.py`.

## 3. Defaults

Override only if the user specifies otherwise:
- **Local execution.** Pitch HF Jobs only if local hardware can't fit the job.
- **Single run.** After it completes, propose experimentation if the user would benefit (weak/marginal verdict, "see how high you can push it" framing, etc.). Iteration rules in `references/training_args.md` (Experimentation section).
- **Save artifacts locally by default.** Hub uploads and cloud jobs apply only when requested or otherwise authorized. Choose the repository and visibility explicitly; private is the default for new uploaded artifacts. For ephemeral jobs, arrange an authorized persistent destination before starting.

## 4. Constraints the produced script must satisfy

Preserve applicable numerical and data-shape requirements. Logging format, tracker, directory layout, and monitor integration are examples to adapt to the project.

- Capture the pre-training evaluator score as `baseline_eval` **before** `trainer.train()`.
- Emit a single end-of-run line: `VERDICT: WIN|MARGINAL|REGRESSION | score=... | baseline=... | delta=...`. Use this format only when useful or required by the project's monitor.
- Silence `httpx`, `httpcore`, `huggingface_hub`, `urllib3`, `filelock`, `fsspec` to WARNING (otherwise HF download URLs flood the agent's context).
- Tee logs to `logs/{RUN_NAME}.log`.
- Save the final model locally. Enable optional Hub upload only for an authorized destination; the bundled templates require `PUSH_TO_HUB=1` and create private repos by default.
- Smoke-test before any long run (`max_steps=1` + tiny dataset slice). The production templates show one common pattern (`SMOKE_TEST` env var).
- **[CrossEncoder]** Include `EarlyStoppingCallback(patience>=3)`. CE rerankers often peak mid-training and regress.
- **[SparseEncoder]** Log `query_active_dims` / `corpus_active_dims` on the verdict line. High nDCG with collapsed sparsity is not a win. The keys come back name-prefixed (e.g. `..._query_active_dims`). Use suffix matching to pluck them. See the SPARSE production template for the exact pattern.
- **[MultiVectorEncoder]** Match `scale` to the scoring mode on any MNRL-family loss: near `1.0` for unnormalized MaxSim (do not copy `scale=20.0` from bi-encoder MNRL), roughly the average query length with length-normalized MeanMaxSim, since each score is divided by its query's token count. `XTRScores` is a train-only `similarity_fct`: the evaluators reject it, so evaluation always scores with MaxSim, including for XTR-trained models.

## 5. Workflow

1. Identify the model type (§1). Ask if ambiguous.
2. Load the §2 required-reading files for that type.
3. Inspect the matching template and adapt its relevant pieces to the existing training workflow.
4. Replace `MODEL_NAME`, `DATASET_NAME`, `RUN_NAME`, the loss, and the evaluator with the user's task. Cross-check loss/data-shape match against `references/losses_<type>.md`. Cross-check the `metric_for_best_model` key against `references/evaluators_<type>.md` (named evaluators format the key as `eval_{name}_{primary_metric}`).
5. Smoke-test (`max_steps=1`).
6. Run.
7. After the run, append to `logs/experiments.md` and propose iteration if the verdict is weak/marginal.

## Prerequisites

```bash
pip install "sentence-transformers[train]>=5.0"        # add [train,image] / [audio] / [video] for [SentenceTransformer] multimodal
                                                       # [MultiVectorEncoder] requires >=6.0
pip install trackio                                    # optional tracker (or wandb / tensorboard / mlflow)
hf auth login                                          # only when needed; write scope only for authorized uploads
```

Choose hardware and precision from model size, runtime budget, and supported operations. CPU can suit small runs; GPU acceleration may be necessary for practical larger training.

## Related guidance

- [transformers](../transformers/SKILL.md)
- [huggingface-datasets](../huggingface-datasets/SKILL.md)
- [lambda-cloud](../lambda-cloud/SKILL.md)
- [rag](../rag/SKILL.md)
