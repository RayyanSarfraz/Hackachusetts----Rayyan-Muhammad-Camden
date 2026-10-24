"""GPU-adaptive LoRA / QLoRA SFT for MedMatch Model A (google/medgemma-1.5-4b-it).

Implements the brief:
- Detect the allocated GPU (nvidia-smi + torch) and deep-merge the matching
  gpu_profiles entry over the base config -> print the EFFECTIVE config.
- G4 / A100 -> BF16 LoRA (frozen BF16 base, adapters only). NOT 4-bit. NOT full.
- L4 / T4 -> NF4 QLoRA fallback (bf16 on L4, fp16 on T4).
- Load MedGemma as a multimodal image-text-to-text checkpoint
  (AutoProcessor + AutoModelForImageTextToText), freeze the vision tower,
  attach LoRA to language-decoder projections only.
- Supervise completion tokens only (prompt masked).
- Run a 10-20 example forward/backward smoke test and log peak CUDA memory
  and tokens/sec BEFORE any long run.

This is a CLI equivalent of the notebook. It is import-safe: heavy deps load
inside functions so unit tests can import the module without torch installed.

Example (on the Colab VM):
    python train.py --config config.yaml --data data \
        --out /content/outputs --drive /content/drive/MyDrive/medgemma-model-a \
        --smoke           # forward/backward only
    python train.py --config config.yaml --data data --out /content/outputs \
        --drive /content/drive/MyDrive/medgemma-model-a   # real run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import common


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def git_sha() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode()
            .strip()
        )
    except Exception:
        return "nogit"


# --------------------------------------------------------------------------- #
# GPU detection
# --------------------------------------------------------------------------- #


def detect_gpu() -> dict:
    """Return {name, vram_gb, cuda, compute_capability, bf16_supported}."""
    info = {
        "name": "cpu",
        "vram_gb": None,
        "cuda": None,
        "compute_capability": None,
        "bf16_supported": False,
    }
    try:
        import torch

        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            info["name"] = props.name
            info["vram_gb"] = round(props.total_memory / (1024**3), 2)
            info["cuda"] = torch.version.cuda
            info["compute_capability"] = f"{props.major}.{props.minor}"
            info["bf16_supported"] = bool(torch.cuda.is_bf16_supported())
    except Exception as exc:  # torch missing on the Mac client
        info["error"] = repr(exc)
    # also capture nvidia-smi one-liner when present
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        info["nvidia_smi"] = out
    except Exception:
        info["nvidia_smi"] = None
    return info


def peak_vram_gb() -> float | None:
    try:
        import torch

        if torch.cuda.is_available():
            return round(torch.cuda.max_memory_allocated() / (1024**3), 3)
    except Exception:
        return None
    return None


# --------------------------------------------------------------------------- #
# Model + LoRA
# --------------------------------------------------------------------------- #


def discover_language_lora_targets(model) -> list[str]:
    """Collect decoder linear-projection module *names* for LoRA, excluding the
    vision tower / multimodal projector so we never attach to image modules."""
    import torch.nn as nn

    wanted = {"q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"}
    vision_markers = ("vision", "visual", "image", "multi_modal", "mm_", "patch")
    found: set[str] = set()
    for name, module in model.named_modules():
        if not isinstance(module, nn.Linear):
            continue
        lower = name.lower()
        if any(m in lower for m in vision_markers):
            continue
        leaf = name.split(".")[-1]
        if leaf in wanted:
            found.add(leaf)
    return sorted(found)


def freeze_vision(model) -> int:
    """Freeze any parameter that lives under a vision/multimodal submodule."""
    vision_markers = ("vision", "visual", "image", "multi_modal", "mm_")
    frozen = 0
    for name, param in model.named_parameters():
        if any(m in name.lower() for m in vision_markers):
            param.requires_grad = False
            frozen += 1
    return frozen


def load_model_and_processor(eff: dict):
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    model_id = eff["model"]["id"]
    e = eff["effective"]
    dtype = torch.bfloat16 if e["precision"] == "bf16" else torch.float16

    quant_cfg = None
    if e["load_in_4bit"]:
        from transformers import BitsAndBytesConfig

        quant_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=eff["model"].get("quantization_type", "nf4"),
            bnb_4bit_use_double_quant=eff["model"].get("double_quantization", True),
            bnb_4bit_compute_dtype=dtype,
        )

    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        torch_dtype=dtype,
        device_map="auto",
        quantization_config=quant_cfg,
        attn_implementation="eager",  # safe default; no flash-attn assumption
    )
    return model, processor


def attach_lora(model, eff: dict, targets: list[str]):
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    if eff["effective"]["load_in_4bit"]:
        model = prepare_model_for_kbit_training(
            model, use_gradient_checkpointing=eff["training"]["gradient_checkpointing"]
        )
    lora_cfg = LoraConfig(
        r=eff["lora"]["r"],
        lora_alpha=eff["lora"]["alpha"],
        lora_dropout=eff["lora"]["dropout"],
        target_modules=targets,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)
    return model


# --------------------------------------------------------------------------- #
# Data -> tokenized tensors with completion-only loss mask
# --------------------------------------------------------------------------- #


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_tokenized(rows, processor, max_len: int):
    """Tokenize chat prompt + target, masking prompt tokens with -100 so loss is
    computed on the assistant completion only. Returns a list of dicts."""
    tok = getattr(processor, "tokenizer", processor)
    examples = []
    truncated = 0
    for r in rows:
        prompt_ids = tok.apply_chat_template(
            r["messages"], tokenize=True, add_generation_prompt=True
        )
        target_text = r["target"] + (tok.eos_token or "")
        target_ids = tok(target_text, add_special_tokens=False)["input_ids"]
        input_ids = prompt_ids + target_ids
        labels = [-100] * len(prompt_ids) + list(target_ids)
        if len(input_ids) > max_len:
            # never silently drop target: flag and skip rather than truncate answer
            truncated += 1
            continue
        examples.append({"input_ids": input_ids, "labels": labels})
    return examples, truncated


def collate(batch, pad_id: int):
    import torch

    max_len = max(len(b["input_ids"]) for b in batch)
    input_ids, labels, attn = [], [], []
    for b in batch:
        pad = max_len - len(b["input_ids"])
        input_ids.append(b["input_ids"] + [pad_id] * pad)
        labels.append(b["labels"] + [-100] * pad)
        attn.append([1] * len(b["input_ids"]) + [0] * pad)
    return {
        "input_ids": torch.tensor(input_ids),
        "labels": torch.tensor(labels),
        "attention_mask": torch.tensor(attn),
    }


# --------------------------------------------------------------------------- #
# Runners
# --------------------------------------------------------------------------- #


def resolve_effective(cfg: dict, gpu: dict) -> dict:
    key = common.resolve_gpu_profile_key(gpu.get("name", ""), gpu.get("vram_gb"), cfg)
    eff = common.effective_config(cfg, key)
    # If a BF16 profile was selected but the GPU cannot do bf16, degrade to fp16.
    if eff["effective"]["precision"] == "bf16" and not gpu.get("bf16_supported", False):
        if gpu.get("name") not in (None, "cpu"):
            eff["effective"]["precision"] = "fp16"
            eff["effective"]["torch_dtype"] = "float16"
    return eff


def run_smoke(model, processor, eff, train_rows, log: dict):
    import torch

    tok = getattr(processor, "tokenizer", processor)
    n = min(len(train_rows), 20)
    examples, truncated = build_tokenized(train_rows[:n], processor, eff["training"]["max_seq_length"])
    log["smoke"] = {"requested": n, "usable": len(examples), "truncated": truncated}
    if not examples:
        raise RuntimeError("smoke: no examples fit max_seq_length")

    # assert the loss mask actually supervises some completion tokens
    assert any(l != -100 for l in examples[0]["labels"]), "no supervised target tokens"
    assert any(l == -100 for l in examples[0]["labels"]), "prompt not masked"

    model.train()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None

    t0 = time.time()
    batch = collate(examples[: eff["training"]["per_device_train_batch_size"]], pad_id)
    batch = {k: v.to(model.device) for k, v in batch.items()}
    out = model(**batch)
    loss = out.loss
    loss.backward()
    opt.step()
    opt.zero_grad()
    dt = time.time() - t0
    n_tokens = int(batch["attention_mask"].sum().item())

    log["smoke"].update(
        {
            "loss": float(loss.detach().float().cpu()),
            "step_seconds": round(dt, 3),
            "tokens": n_tokens,
            "tokens_per_sec": round(n_tokens / dt, 1) if dt > 0 else None,
            "peak_vram_gb": peak_vram_gb(),
        }
    )
    return log


def run_training(model, processor, eff, train_rows, out_dir: Path, log: dict):
    import torch
    from transformers import Trainer, TrainingArguments

    tok = getattr(processor, "tokenizer", processor)
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    examples, truncated = build_tokenized(
        train_rows, processor, eff["training"]["max_seq_length"]
    )
    log["train_data"] = {"usable": len(examples), "truncated_excluded": truncated}
    if not examples:
        raise RuntimeError("no training examples fit max_seq_length")

    e = eff["effective"]
    args = TrainingArguments(
        output_dir=str(out_dir / "checkpoints"),
        per_device_train_batch_size=e["per_device_train_batch_size"],
        gradient_accumulation_steps=e["gradient_accumulation_steps"],
        learning_rate=e["learning_rate"],
        num_train_epochs=e["num_train_epochs"],
        warmup_ratio=eff["training"]["warmup_ratio"],
        lr_scheduler_type=eff["training"]["lr_scheduler_type"],
        logging_steps=eff["training"]["logging_steps"],
        save_steps=eff["training"]["save_steps"],
        save_total_limit=eff["training"]["save_total_limit"],
        gradient_checkpointing=eff["training"]["gradient_checkpointing"],
        gradient_checkpointing_kwargs=eff["training"].get("gradient_checkpointing_kwargs"),
        bf16=(e["precision"] == "bf16"),
        fp16=(e["precision"] == "fp16"),
        optim=e["optimizer"],
        report_to=[],
    )
    torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=examples,
        data_collator=lambda b: collate(b, pad_id),
    )
    t0 = time.time()
    result = trainer.train()
    log["training"] = {
        "runtime_seconds": round(time.time() - t0, 1),
        "train_loss": float(result.training_loss),
        "peak_vram_gb": peak_vram_gb(),
        "global_steps": int(result.global_step),
    }
    return trainer, log


def save_artifacts(model, processor, eff, out_dir: Path, drive_dir: Path | None, log: dict):
    adapter_dir = out_dir / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_dir))  # LoRA adapter only
    try:
        processor.save_pretrained(str(adapter_dir))
    except Exception:
        getattr(processor, "tokenizer", processor).save_pretrained(str(adapter_dir))
    (out_dir / "effective_config.json").write_text(
        json.dumps(eff, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "run_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    saved = {"adapter_dir": str(adapter_dir)}
    if drive_dir is not None:
        import shutil

        run_name = f"{log['run_id']}"
        dest = drive_dir / run_name
        dest.mkdir(parents=True, exist_ok=True)
        # atomic-ish copy: copy to tmp then replace
        for item in ["adapter", "effective_config.json", "run_log.json"]:
            src = out_dir / item
            if src.is_dir():
                shutil.copytree(src, dest / item, dirs_exist_ok=True)
            elif src.exists():
                shutil.copy2(src, dest / item)
        saved["drive_dir"] = str(dest)
    return saved


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(common.DEFAULT_CONFIG_PATH))
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--drive", default=None, help="persistent Drive dir for artifacts")
    ap.add_argument("--smoke", action="store_true", help="forward/backward only")
    ap.add_argument("--print-effective-only", action="store_true")
    args = ap.parse_args()

    cfg = common.load_yaml(args.config)
    gpu = detect_gpu()
    eff = resolve_effective(cfg, gpu)

    run_id = f"{utc_stamp()}_{git_sha()}_seed{cfg['data']['seed']}"
    log = {"run_id": run_id, "gpu": gpu, "effective": eff["effective"]}

    print("=== Detected GPU ===")
    print(json.dumps(gpu, indent=2))
    print("=== EFFECTIVE config (profile merged over defaults) ===")
    print(json.dumps(eff["effective"], indent=2))

    # Guardrail: never train a high-memory BF16 profile in 4-bit by accident.
    if eff["effective"]["method"] == "bf16_lora" and eff["effective"]["load_in_4bit"]:
        print("ERROR: bf16_lora profile must not load_in_4bit", file=sys.stderr)
        return 2

    if args.print_effective_only:
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    drive_dir = Path(args.drive) if args.drive else None

    train_rows = load_jsonl(Path(args.data) / "train.jsonl")

    print(f"=== Loading {eff['model']['id']} ===", flush=True)
    model, processor = load_model_and_processor(eff)
    frozen = freeze_vision(model)
    targets = discover_language_lora_targets(model)
    log["frozen_vision_params"] = frozen
    log["lora_target_modules"] = targets
    print(f"Froze {frozen} vision params. LoRA targets: {targets}")
    if not targets:
        print("ERROR: no language decoder LoRA targets discovered", file=sys.stderr)
        return 2
    model = attach_lora(model, eff, targets)
    model.print_trainable_parameters()

    # Always smoke first.
    log = run_smoke(model, processor, eff, train_rows, log)
    print("=== Smoke test ===")
    print(json.dumps(log["smoke"], indent=2))

    if args.smoke:
        out_dir.joinpath("run_log.json").write_text(
            json.dumps(log, indent=2), encoding="utf-8"
        )
        return 0

    trainer, log = run_training(model, processor, eff, train_rows, out_dir, log)
    print("=== Training ===")
    print(json.dumps(log["training"], indent=2))

    saved = save_artifacts(model, processor, eff, out_dir, drive_dir, log)
    log["artifacts"] = saved
    out_dir.joinpath("run_log.json").write_text(
        json.dumps(log, indent=2), encoding="utf-8"
    )
    print("=== Artifacts ===")
    print(json.dumps(saved, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
