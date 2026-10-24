"""Inference for MedMatch Model A: load base + LoRA adapter, produce
schema-validated JSON for a single clinical text.

Combines the two task outputs into a normalized patient profile when both are
requested. Entity character offsets are recomputed in postprocessing (the model
is never asked to emit offsets). Missing evidence stays null/unknown.

Usage (on a GPU VM with the adapter present):
    python infer.py --adapter outputs/adapter --task summary --text-file note.txt
    python infer.py --adapter outputs/adapter --task entities --text "..."
    python infer.py --adapter outputs/adapter --task both --text "..."
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import common


# --------------------------------------------------------------------------- #
# Schema validation (pure; unit-tested)
# --------------------------------------------------------------------------- #


def validate_entities(obj) -> tuple[dict, list[str]]:
    """Coerce to {'entities':[{text,label}]}; return (clean, problems)."""
    problems = []
    if not isinstance(obj, dict) or "entities" not in obj:
        return {"entities": []}, ["missing 'entities' key"]
    clean = []
    for i, ent in enumerate(obj.get("entities") or []):
        if not isinstance(ent, dict) or "text" not in ent:
            problems.append(f"entity[{i}] malformed")
            continue
        clean.append({"text": str(ent.get("text", "")), "label": str(ent.get("label", ""))})
    return {"entities": clean}, problems


def validate_summary(obj) -> tuple[dict, list[str]]:
    """Ensure a JSON object; normalize 'None'/'' leaves to null."""
    problems = []
    if not isinstance(obj, dict):
        return {}, ["summary is not a JSON object"]

    def norm(v):
        if isinstance(v, dict):
            return {k: norm(x) for k, x in v.items()}
        if isinstance(v, list):
            return [norm(x) for x in v]
        if isinstance(v, str) and v.strip().lower() in {"", "none", "null", "unknown"}:
            return None
        return v

    return norm(obj), problems


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #


def load_model(adapter_dir: str, model_id: str, precision: str):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForImageTextToText, AutoProcessor

    dtype = torch.bfloat16 if precision == "bf16" else torch.float16
    processor = AutoProcessor.from_pretrained(model_id)
    base = AutoModelForImageTextToText.from_pretrained(
        model_id, torch_dtype=dtype, device_map="auto", attn_implementation="eager"
    )
    model = PeftModel.from_pretrained(base, adapter_dir)
    model.eval()
    return model, processor


def generate(model, processor, messages, max_new_tokens=512) -> str:
    import torch

    tok = getattr(processor, "tokenizer", processor)
    ids = tok.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
    ).to(model.device)
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=max_new_tokens, do_sample=False, num_beams=1)
    return tok.decode(out[0][ids.shape[-1]:], skip_special_tokens=True).strip()


def infer_summary(model, processor, text: str) -> dict:
    raw = generate(model, processor, common.build_summary_messages(text))
    obj, ok = common.parse_json_safe(raw)
    clean, problems = validate_summary(obj if ok else {})
    return {"raw": raw, "valid_json": ok, "schema_problems": problems, "summary": clean}


def infer_entities(model, processor, text: str) -> dict:
    raw = generate(model, processor, common.build_entities_messages(text))
    obj, ok = common.parse_json_safe(raw)
    clean, problems = validate_entities(obj if ok else {})
    # recompute offsets in postprocessing against the source text
    clean["entities"] = common.recompute_offsets(text, clean["entities"])
    return {"raw": raw, "valid_json": ok, "schema_problems": problems, "entities": clean["entities"]}


def normalized_profile(summary_res: dict, entities_res: dict) -> dict:
    return {
        "patient_summary": summary_res.get("summary"),
        "entities": entities_res.get("entities"),
        "provenance": {
            "summary_valid_json": summary_res.get("valid_json"),
            "entities_valid_json": entities_res.get("valid_json"),
        },
        "disclaimer": "Provisional automated extraction from synthetic/research text. Subject to clinical review; not validated for clinical use.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(common.DEFAULT_CONFIG_PATH))
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--task", choices=["summary", "entities", "both"], default="both")
    ap.add_argument("--text", default=None)
    ap.add_argument("--text-file", default=None)
    ap.add_argument("--precision", default="bf16", choices=["bf16", "fp16"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        print("provide --text or --text-file", file=sys.stderr)
        return 2

    cfg = common.load_yaml(args.config)
    model, processor = load_model(args.adapter, cfg["model"]["id"], args.precision)

    result = {}
    summary_res = infer_summary(model, processor, text) if args.task in ("summary", "both") else {}
    entities_res = infer_entities(model, processor, text) if args.task in ("entities", "both") else {}
    if args.task == "summary":
        result = summary_res
    elif args.task == "entities":
        result = entities_res
    else:
        result = normalized_profile(summary_res, entities_res)

    out_text = json.dumps(result, indent=2, ensure_ascii=False)
    print(out_text)
    if args.out:
        Path(args.out).write_text(out_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
