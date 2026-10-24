# MedMatch Model A — coding-agent execution brief

Date: 2026-10-24
Environment: User has **Google Colab Pro** (positive compute units must be checked). User has an **Intel 2019 Mac** as a CLI client, NOT a training GPU. User shared the MedGemma 1.5 model card and has accepted gated model access on the Hugging Face account shown. No access token has been provided and none should be requested in chat.
Goal: Create, validate, and run a reproducible Google Colab GPU-adaptive LoRA/QLoRA SFT pipeline for medical note extraction with `google/medgemma-1.5-4b-it`. This is **Model A only**, not patient-trial eligibility (Model B).

## Your role
Act as senior ML engineer and autonomous coding agent. Implement code, datasets, tests, docs, and a Colab notebook; run all tasks available in your local environment. Do not just propose code. Follow repo instructions (AGENTS.md, README, existing conventions), work in a dedicated feature branch rather than overwriting other team members' work, commit changes, and report the exact commands and verifiable outputs. Do not claim GPU training was run unless it actually was. Ask user only for unavoidable UI credentials/permissions and Colab runtime access.

## Authoritative resources
- MedGemma model: https://huggingface.co/google/medgemma-1.5-4b-it
- MedGemma's official tuning notebook: https://github.com/google-health/medgemma/blob/main/notebooks/fine_tune_with_hugging_face.ipynb
- Google MedGemma documentation: https://developers.google.com/health-ai-developer-foundations/medgemma/get-started
- Dataset 1: https://huggingface.co/datasets/AGBonnet/augmented-clinical-notes
- Dataset 2: https://huggingface.co/datasets/E3-JSI/synthetic-multi-med-notes-ner-v1
- Google Colab limits: https://research.google.com/colaboratory/faq.html
- Google Colab CLI: https://github.com/googlecolab/google-colab-cli

## Requirements — repo files
Create a self-contained `ml/model_a/` directory with:
- `README.md`: one-click Colab / exact execution instructions and architecture limitations
- `colab_finetune_medgemma.ipynb`: install, login, GPU/disk check, Drive mount, dataset prep, baseline inference, training, eval, adapter export and reload demo
- `prepare_data.py`: deterministic HF ingestion, normalization, filtering, de-dup, train/val/test split, manifest
- `train.py`: reusable CLI equivalent of notebook training using Transformers + bitsandbytes + PEFT + TRL (or version-compatible official MedGemma recipe)
- `evaluate.py`: evidence-oriented metrics, baseline and adapter comparison
- `infer.py`: load base + adapter and produce schema-validated JSON
- `config.yaml` or `.json`: model id, seed, maximum sequence length, QLoRA hyperparameters, dataset weights, paths
- `tests/`: unit tests for data converters, offsets, output schema, deterministic splits
- `.gitignore`: model caches, Hugging Face tokens, data exports, training logs and weights; never commit secrets
- `example_inference.json`: representative output clearly labeled as tested model output or example schema, never fictional model predictions.

## Data — DO NOT BLINDLY CONCATENATE
Dataset 1 (AGBonnet; 30K records): fields `idx`, `note`, `full_note`, `conversation`, `summary`. `summary` is GPT-4-generated structured patient information, not clinician-verified ground truth. Start with **full_note -> summary**. Avoid using truncated `note` against a `summary` derived from `full_note` where target facts may be absent. Parse JSON safely. Ensure answer tokens fit context; never silently truncate crucial target fields. Filter and log invalid/empty/overlong examples. Preserve per-example source id. Use language English.
Dataset 2 (E3-JSI; ~3238 total, 9 languages): fields `text`, `language`, `entities` with `text`, `label`, `start`, `end` character offsets; also `gliner_tokenized_text`, `gliner_entities`. Filter to `language == 'english'` case-insensitively for MVP. Verify each annotation: `text[start:end] == entity['text']`. This is **NER supervision**, NOT full patient summary supervision. Use a distinct instruction/task name (`EXTRACT_ENTITIES`) with JSON entities (label + surface text + matching span/evidence; avoid training the LLM to fabricate character offsets; compute offsets in postprocessing when possible). Skip or quarantine invalid annotations and report numbers.
Use distinct chat tasks (`EXTRACT_SUMMARY` and `EXTRACT_ENTITIES`) with the same base MedGemma model. Output contract can be task-specific but both must be valid JSON. Inference pipeline can combine the extracted entities and summary into a normalized patient profile. Do not teach fabricated fields or output from the original notes; handle negations, historical vs active conditions, quantities/units and missing dates.
Split by original case ID, not individual transformed prompt; detect exact and near-duplicates across splits. Fix random seed. Default 80/10/10. Save train/val/test manifest, dataset versions/revisions and quality counts. No leakage. Use a maximum of 500-1000 curated records for initial demo, then expand only if hardware and metrics permit. Don't claim clinical validation.

## First model experiment — limits
Base model id `google/medgemma-1.5-4b-it`. Request HF access acceptance by the human; use Colab secret `HF_TOKEN`, never print it. Load with a currently compatible AutoProcessor + AutoModelForImageTextToText (or version-compatible class demonstrated by the official MedGemma tuning notebook); do not assume a text-only `AutoModelForCausalLM` works for the multimodal checkpoint. Verify the official fine-tuning notebook and run an actual single mini-batch forward/backward before launching long training. For text-only tasks freeze vision modules. Confirm language model module names and attach LoRA ONLY to suitable decoder projections; avoid matching vision-encoder modules by accident. Use PEFT/TRL API versions that actually work together; document versions. Construct model chat prompts using tokenizer/processor official chat template. Compute loss only on target answer, not prompt, when supported by current trainer. Preserve EOS correctly.
The baseline is 4-bit NF4 QLoRA, fp16 on T4 / bf16 on supported GPUs, LoRA r=16 alpha=32 dropout=.05, batch=1, grad accumulation=8, sequence_len=1024, lr=2e-4, 1 epoch cap, warmup_ratio=.03, checkpointing on, paged_adamw_8bit. **NEW:** If G4 RTX PRO 6000 Blackwell / A100 is actually allocated, prefer the BF16 LoRA profile defined in `medgemma_model_a_training_config.yaml`: do not 4-bit quantize the frozen base on large-memory GPUs. The agent must implement correct BF16 LoRA, not full parameter training. Treat as initial *hypotheses*, measure actual VRAM and adapt if out-of-memory. T4 16GB is a best-effort option, NOT guaranteed fit; try 512-768 context, smaller LoRA targets, offloading or L4 if needed. No flash attention assumptions on T4. Record GPU model, CUDA, free VRAM/disk, max peak memory. Test 10-20 sample smoke run before 500-1000 examples.

## Evaluation acceptance criteria
1. Validate target JSON parsing and that extracted evidence exists in the original note; report field-level precision/recall/F1 where label alignment exists. NER: exact and relaxed span/entity-level P/R/F1 and missed negations; use observed source-matching, not LLM self-evaluation.
2. Evaluate **unchanged base model first**, then **same held-out dataset and decoding parameters after training**. Supply real side-by-side examples, including failure cases.
3. Verify no source-to-label mismatch; track hallucinated facts, omitted entities, incorrect negation, medication dosage and timing mistakes. Keep an untouched test set.
4. Save output adapter (`adapter_model.safetensors`, `adapter_config.json`) plus processor/tokenizer as needed, metrics JSON, training config, seed and dataset manifest to persistent Drive. Save the adapter at least at final completion, and use cautious checkpoint frequency to avoid slow Drive I/O (write checkpoints to /content, copy periodic/final to Drive).
5. Reopen a clean model + adapter and successfully infer on a held-out text example, output valid JSON and record real console result.
6. Production warning: synthetic/research data only; never upload real identifiable patient data to Colab, LlamaCloud or public Hugging Face repos without legal/security approval. App outputs are provisional extraction subject to review.

## Colab Pro — autonomous CLI/SSH execution (UPDATED 2026-10-24)
The user has Colab **Pro**, not free Colab. Google's official FAQ restricts SSH/remote control on **free-of-charge managed runtimes without positive compute-unit balance**, and permits these activities with a paid plan **and positive balance**. Pro does not provide unlimited GPU access or prevent timeouts; monitor usage and persist checkpoints. Do not use public unauthenticated SSH tunnels or expose a notebook endpoint.

**Prefer Google's official Colab CLI** (`google-colab-cli`), which runs on macOS (including user's Intel Mac) and Linux; it provides `colab new`, `colab exec`, `colab console`, `colab ssh`, `colab drivemount`, `colab download`, `colab usage`:
- Repo: https://github.com/googlecolab/google-colab-cli
- Announcement: https://developers.googleblog.com/introducing-the-google-colab-cli/
- SSH details (including runtime capability requirements): https://github.com/googlecolab/google-colab-cli/blob/main/docs/06_ssh_access.md
- Policy: https://research.google.com/colaboratory/faq.html

The coding agent MUST:
1. Detect whether CLI is installed locally; if not, provide `python3 -m pip install -U google-colab-cli` and verify `colab version`. Follow CLI's documented sign-in/authentication; have the user complete any Google OAuth flow. Never handle passwords or ask for access tokens in chat.
2. Check `colab usage` and `colab status`/`sessions` before allocating. Recommend **G4 (RTX PRO 6000 Blackwell 96GB)** when actually selectable/allocated, **A100 80/40GB** as next choice, **L4 (24GB)** or **T4 (16GB)** as fallback with smaller seq length. On T4 BF16 support is unavailable; use FP16. Record allocation and actual VRAM.
3. Provision an isolated named session, e.g. `colab new -s medgemma-model-a --gpu G4` only after confirming the current CLI supports that GPU identifier; if allocation fails, check `colab new --help`, user's availability and select T4/A100 appropriately rather than assuming entitlement.
4. For hands-off execution, use `colab exec -s medgemma-model-a -f <self-contained-bootstrap.py-or-notebook.ipynb>` or `colab console`. Use `colab ssh -s medgemma-model-a` when SSH server feature is exposed. `colab ssh` can return 404 when SSH isn't enabled on an existing runtime; don't treat this as success. If the SSH pathway fails, use official `colab exec`/`console` instead. On macOS, use SSH-over-WebSocket with the official CLI, NOT arbitrary ngrok tunnels or public forwarding services. Do not assume VS Code Remote SSH works without a proven successful connection.
5. Keep scripts and configs in GitHub and run them on the allocated VM. `colab exec -f` sends ONE local script or notebook to the remote kernel; when code relies on sibling files, explicitly synchronize the project (authenticated git clone/pull on VM or single self-contained bootstrap that installs/checks out repo). Do not assume local files are automatically mounted remotely.
6. Authenticate model downloads inside Colab securely. User's model-card screenshot states **gated access granted**, but download will still need an **HF_TOKEN** stored in Colab Secrets/secure credential store and permissioned for the repo. No actual token was supplied. Test the token with a small metadata call before downloading multi-GB weights. Do not output token, put in command line, log, GitHub, or exported notebook.
7. Keep caches and training working data in `/content` local disk. Mount Drive (`colab drivemount -s medgemma-model-a` or `drive.mount`) for snapshots and final adapter. Copy checkpoints atomically from `/content` to `/content/drive/MyDrive/medgemma-model-a/` periodically and at end; verify files and readable adapter. Prefer storing only adapter, not full base model.
8. Begin with GPU inventory + 10-20 record smoke test, baseline eval, 500-1000 record run, and held-out eval; scale context and dataset ONLY if resource limits allow. Save actual run logs, config, dataset manifest, git SHA, versions, random seed, before/after metrics and two evidence-grounded examples.
9. Record compute spend/usage and **stop the VM** via `colab stop -s medgemma-model-a` after persisting everything. Do not assert indefinite background operation or uptime; runtimes may terminate.
10. Provide a Colab notebook fallback (user launches `Runtime -> Change runtime type -> GPU`, authorizes Drive and HF token, runs all) if CLI authentication, feature availability, or environment prevents remote execution. The autonomous task can write code without user clicks, but cannot perform account authorizations without the user.

**Documented terminal sequence (after user authorizes Google/HF access; commands are executed locally on user's Mac):**
```bash
python3 -m pip install -U google-colab-cli
colab version
colab usage
colab new -s medgemma-model-a --gpu G4  # if allocation fails use A100, then L4
colab status -s medgemma-model-a
colab ssh -s medgemma-model-a            # optional, only if supported by runtime
# Alternative, agent-run command (the script must bootstrap its dependencies):
colab exec -s medgemma-model-a -f ml/model_a/colab_finetune_medgemma.ipynb
colab log -s medgemma-model-a -o medgemma-run-log.md
colab stop -s medgemma-model-a           # after exporting adapter and results
```

**Training config is included both in this instruction text and as a standalone file** `medgemma_model_a_training_config.yaml` (attached alongside this brief; copy into `ml/model_a/config.yaml` when generating the project). These are proposed starting settings, NOT executed measurements; agent must adapt and report changes. On L4 start with the same settings as T4 while validating the model, then consider max_seq_length 1536/2048 if resources and data length justify it. Use 1 epoch at first; increase only when metrics support improvement.

**Model-card-specific corrections:** MedGemma 1.5 4B is a **multimodal Gemma 3** checkpoint; its card's baseline inference uses `AutoModelForImageTextToText` and `AutoProcessor`, not necessarily `AutoModelForCausalLM`. Select a supported and version-compatible class/trainer for text-only QLoRA. Max *supported model* context (128K) is NOT a training budget recommendation. The pasted page includes inference code, **not a hosted model inference API key**; this experiment downloads model weights from Hugging Face and fine-tunes locally on Colab. License is Health AI Developer Foundations; honor terms, and keep patient data synthetic / non-identifiable.


## Output you must return
- Status of each task: implemented, tested, not run and why
- Paths of created files, git branch and commit if permitted
- Training dataset counts split by source, task, and language
- Actual GPU name / VRAM, peak VRAM, run time and checkpoint location if executed
- Base vs tuned metrics based only on executions
- 2+ actual before/after predictions with source evidence, or an explicit blocker
- Single launch command / Colab link.

Scope discipline: Model B and clinical trial matching are explicitly excluded. No PDF OCR fine-tuning in this iteration because both selected datasets are text; PDF parsing is a separate upstream integration. Do not overbuild a full healthcare app.

## 2026-10-24 GPU update — G4/A100 priority (user screenshot)
The user's Colab screenshot displays G4, A100, L4, T4 as seemingly selectable options; H100 is visibly greyed out. Do not assume H100 entitlement. Google Colab GPU offerings change over time; inspect actual allocation via `nvidia-smi` and `torch.cuda.get_device_properties(0)` and verify CLI enum with `colab new --help`. G4 refers to RTX PRO 6000 Blackwell (up to 96GB GPU VRAM). A100 might be 40GB or 80GB. Do not assert that a selectable option will always allocate.

The companion config now contains **gpu_profiles**. Implement GPU auto-detection and profile selection. For G4 or A100, run BF16 base + PEFT LoRA, frozen main weights, language decoder LoRA only; **NOT** 4-bit QLoRA and **NOT** full-parameter SFT. BF16 LoRA generally simplifies implementation when GPU memory is ample; quality advantage over QLoRA is a testable hypothesis, not guaranteed. For L4/T4, retain NF4 QLoRA fallback. Follow a 20-example forward/backward smoke test on real model and log peak CUDA memory and tokens/sec.

On G4 start seq_len=2048, micro-batch 2, accumulation 4; evaluate increasing seq_len to 4096 and/or micro-batch up to 4 ONLY after verifying input+target token length distribution and stable VRAM. On A100 40GB start seq_len=2048, batch 1, accumulation 8. Use BF16 when supported; a suitable torch fused AdamW optimizer when available. Keep baseline r=16 alpha=32 dropout=.05 and lr=2e-4, verify LoRA training correctness with loss decrease, and adjust learning rate only after observing validation results. Preserve loss masking to assistant completions and source evidence. Do not truncate target summary JSON silently; dynamically bucket/drop overlong records and record exclusions.

To balance the user's prepaid compute units, run 20-example smoke -> 1,000 primary + 150 secondary -> evaluate -> 5,000 primary + 500 secondary -> evaluate. Only then attempt a larger, quality-filtered subset of the ~30k primary dataset; record speed, current balance and projected credit consumption before a longer run. GPU power alone does not justify increasing training dataset size or epochs if labels are noisy. Save checkpoints locally then copy adapters/metrics persistently to Drive, and terminate GPU session at the end.

## Mandatory run-state checks and artifact naming
- Before proceeding beyond the smoke test, confirm the model's **answer-only loss mask** works for multimodal tokenization; a training batch must have supervised output tokens and ignored input/prompt tokens.
- Explicitly merge the selected `gpu_profiles` override into defaults and print the *effective* config, including `load_in_4bit`, dtype, optimizer, batch size, accumulation and max length. Never silently train the high-memory BF16 profile in 4-bit because the base YAML contains a 4-bit fallback default.
- Make the main training run idempotent and resumable: checkpoints and manifests are keyed by UTC timestamp + git SHA + dataset revision + seed. Never overwrite the previous successful adapter.
- Start with G4 if available, or A100; use L4/T4 only if allocation or memory makes it necessary. Measure actual VRAM with `nvidia-smi`, not estimates.
- For medical negation, history and dates, missing evidence must be represented as `unknown`/`null`, never imputed.
- Verify source text before using automatically generated supervised labels. Keep Synthea records and any real medical documents out of public model repos.
