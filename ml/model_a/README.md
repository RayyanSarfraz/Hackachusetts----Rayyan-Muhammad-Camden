# MedMatch Model A — MedGemma 1.5 4B extraction fine-tune

GPU-adaptive LoRA / QLoRA supervised fine-tuning of `google/medgemma-1.5-4b-it`
for medical note extraction. Two distinct chat tasks share one base model:

- `EXTRACT_SUMMARY` — `full_note` → structured summary JSON
  (from [AGBonnet/augmented-clinical-notes](https://huggingface.co/datasets/AGBonnet/augmented-clinical-notes))
- `EXTRACT_ENTITIES` — `text` → verified NER entities JSON
  (from [E3-JSI/synthetic-multi-med-notes-ner-v1](https://huggingface.co/datasets/E3-JSI/synthetic-multi-med-notes-ner-v1))

This is **Model A only**. Model B (patient–trial eligibility) is out of scope and
untouched.

> Research / synthetic data only. Outputs are provisional automated extraction,
> subject to clinical review, and **not** clinically validated. Never upload real
> identifiable patient data to Colab, Drive, or public Hugging Face repos.

## Files

| File | Purpose |
| --- | --- |
| `config.yaml` | Model id, seed, LoRA hyperparams, dataset weights, **GPU profiles** |
| `common.py` | Config merge, task prompts, JSON parsing, NER verify, splits |
| `prepare_data.py` | Deterministic ingest → filter → dedup → case split → manifest |
| `train.py` | GPU-adaptive BF16 LoRA / NF4 QLoRA trainer (CLI == notebook) |
| `evaluate.py` | Evidence metrics; **base model first**, then base+adapter |
| `infer.py` | Load base + adapter → schema-validated JSON profile |
| `colab_finetune_medgemma.ipynb` | One-click Colab notebook |
| `colab_bootstrap.py` | Self-contained script for `colab exec -f` / `colab run` |
| `tests/` | Unit tests (30) for converters, offsets, schema, splits, merge |
| `example_inference.json` | Output **schema** example (labeled; not a real prediction) |

## GPU profiles (the key design point)

`config.yaml` ships a 4-bit QLoRA **fallback default**. At allocation the trainer
detects the GPU (`nvidia-smi` + `torch.cuda.get_device_properties`) and
deep-merges the matching `gpu_profiles.<profile>` over the defaults, then prints
the **effective** config:

| GPU | Method | 4-bit | precision | seq_len | micro-bs × accum |
| --- | --- | --- | --- | --- | --- |
| **G4** (RTX PRO 6000, ~96 GB) | BF16 LoRA | no | bf16 | 2048 | 2 × 4 |
| **A100 80 GB** | BF16 LoRA | no | bf16 | 2048 | 2 × 4 |
| **A100 40 GB** | BF16 LoRA | no | bf16 | 2048 | 1 × 8 |
| **L4** (24 GB) | NF4 QLoRA | yes | bf16 | 1024 | 1 × 8 |
| **T4** (16 GB) | NF4 QLoRA | yes | fp16 | 768 | 1 × 8 |

On G4/A100 the base stays frozen in **BF16** and only LoRA adapters train — not
4-bit QLoRA, not full-parameter SFT. The trainer refuses to run a `bf16_lora`
profile with `load_in_4bit=true`.

Vision tower is frozen; LoRA attaches to discovered **language-decoder** linear
projections only (`q/k/v/o/gate/up/down_proj`), never vision/multimodal modules.
Loss is computed on assistant completion tokens only (prompt masked with `-100`).

## Run it — Colab CLI (hands-off)

```bash
python3 -m pip install -U google-colab-cli
colab version && colab usage
colab new -s medgemma-model-a --gpu G4   # falls back to A100 if G4 unavailable
colab status -s medgemma-model-a
# add HF_TOKEN in Colab Secrets (UI) with notebook access, then:
colab exec -s medgemma-model-a -f ml/model_a/colab_bootstrap.py
colab log  -s medgemma-model-a -o medgemma-run-log.md
colab stop -s medgemma-model-a           # after artifacts are in Drive
```

`colab exec -f` sends one file; `colab_bootstrap.py` clones this branch on the VM,
installs deps, verifies the token, and runs the whole pipeline. Set `STAGE=smoke`
(env) to stop after the forward/backward smoke test.

## Run it — Colab notebook (fallback)

Open `colab_finetune_medgemma.ipynb`, set `Runtime → GPU`, add `HF_TOKEN` to
Colab Secrets, and run all cells.

## Run locally (CPU, no model)

```bash
cd ml/model_a
python -m unittest tests.test_common     # 30 unit tests
python prepare_data.py --smoke --out /tmp/smoke   # fixtures, no network/GPU
python train.py --print-effective-only            # show merged config
```

## Experiment stages

20-example smoke → 1000 primary + 150 secondary → evaluate → 5000 + 500 →
evaluate. Expand further only if metrics improve and compute budget allows.
Checkpoints write to `/content`; adapter + metrics + logs are copied to
`/content/drive/MyDrive/medgemma-model-a/<run_id>` where
`run_id = UTC timestamp + git SHA + seed`. The test split is never used for
training.

## Architecture limitations

- Colab Pro does not guarantee a GPU, a specific GPU, or uninterrupted runtime;
  the pipeline persists checkpoints and is resumable.
- `summary` targets are GPT-4-generated, not clinician-verified; treated as a
  starting signal, not clinical ground truth.
- No flash-attention assumption (eager attention by default). T4 has no BF16.
- Entity character offsets are recomputed in postprocessing; the model is not
  trained to emit offsets.
