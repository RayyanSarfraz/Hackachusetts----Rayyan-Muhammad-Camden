"""Evidence-oriented evaluation for MedMatch Model A.

Metrics are computed against the held-out test split, with the SAME decoding
parameters for base and tuned models (greedy / do_sample=false). We evaluate the
UNCHANGED base model first, then the base+adapter, and report side by side.

Metrics (no LLM self-evaluation):
- json_parse_rate: fraction of outputs that parse as a single JSON object
- evidence_grounding_rate (NER): fraction of predicted entity surfaces that
  occur verbatim in the source text (guards against hallucinated spans)
- ner exact P/R/F1: on (surface, label) pairs vs verified gold
- ner relaxed P/R/F1: on surface text only (label-agnostic)
- summary field coverage: fraction of gold non-null keys the prediction fills
  with a value also supported by the source (substring evidence check)

The scoring functions are pure and unit-tested; model generation is isolated in
generate_predictions so evaluate's math can run without a GPU.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import common


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# --------------------------------------------------------------------------- #
# Scoring (pure)
# --------------------------------------------------------------------------- #


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4), "tp": tp, "fp": fp, "fn": fn}


def _norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def score_ner(pred_obj, gold_entities: list[dict], source: str) -> dict:
    """Exact (surface,label) and relaxed (surface) P/R/F1 + grounding rate."""
    pred_entities = []
    if isinstance(pred_obj, dict):
        pred_entities = pred_obj.get("entities") or []
    pred_pairs_exact = {(_norm(e.get("text", "")), _norm(e.get("label", ""))) for e in pred_entities if isinstance(e, dict)}
    pred_surfaces = {_norm(e.get("text", "")) for e in pred_entities if isinstance(e, dict)}
    gold_pairs_exact = {(_norm(e["text"]), _norm(e.get("label", ""))) for e in gold_entities}
    gold_surfaces = {_norm(e["text"]) for e in gold_entities}

    exact = prf(
        tp=len(pred_pairs_exact & gold_pairs_exact),
        fp=len(pred_pairs_exact - gold_pairs_exact),
        fn=len(gold_pairs_exact - pred_pairs_exact),
    )
    relaxed = prf(
        tp=len(pred_surfaces & gold_surfaces),
        fp=len(pred_surfaces - gold_surfaces),
        fn=len(gold_surfaces - pred_surfaces),
    )
    src_norm = _norm(source)
    grounded = sum(1 for s in pred_surfaces if s and s in src_norm)
    grounding = grounded / len(pred_surfaces) if pred_surfaces else 1.0
    return {"exact": exact, "relaxed": relaxed, "evidence_grounding_rate": round(grounding, 4)}


def _flatten(obj, prefix="") -> dict:
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(_flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def _is_null(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip().lower() in {"", "none", "null", "unknown"})


def score_summary(pred_obj, gold_obj, source: str) -> dict:
    """Coverage of gold non-null leaf values, with source-evidence check on the
    predicted value (hallucination guard)."""
    gold_flat = {k: v for k, v in _flatten(gold_obj).items() if not _is_null(v)}
    pred_flat = _flatten(pred_obj) if isinstance(pred_obj, (dict, list)) else {}
    src_norm = _norm(source)
    filled = 0
    grounded = 0
    for k in gold_flat:
        pv = pred_flat.get(k)
        if not _is_null(pv):
            filled += 1
            if _norm(str(pv)) in src_norm:
                grounded += 1
    n = len(gold_flat)
    return {
        "gold_fields": n,
        "fields_filled": filled,
        "coverage": round(filled / n, 4) if n else 0.0,
        "value_grounding_rate": round(grounded / filled, 4) if filled else 1.0,
    }


def aggregate(per_example: list[dict]) -> dict:
    n = len(per_example)
    if not n:
        return {}
    parse_ok = sum(1 for e in per_example if e["parsed"])
    agg = {"n": n, "json_parse_rate": round(parse_ok / n, 4)}

    ner = [e for e in per_example if e["task"] == "EXTRACT_ENTITIES"]
    summ = [e for e in per_example if e["task"] == "EXTRACT_SUMMARY"]
    if ner:
        def micro(key):
            tp = sum(e["ner"][key]["tp"] for e in ner if e.get("ner"))
            fp = sum(e["ner"][key]["fp"] for e in ner if e.get("ner"))
            fn = sum(e["ner"][key]["fn"] for e in ner if e.get("ner"))
            return prf(tp, fp, fn)
        ground = [e["ner"]["evidence_grounding_rate"] for e in ner if e.get("ner")]
        agg["ner"] = {
            "n": len(ner),
            "exact_micro": micro("exact"),
            "relaxed_micro": micro("relaxed"),
            "mean_evidence_grounding_rate": round(sum(ground) / len(ground), 4) if ground else 0.0,
        }
    if summ:
        cov = [e["summary"]["coverage"] for e in summ if e.get("summary")]
        vg = [e["summary"]["value_grounding_rate"] for e in summ if e.get("summary")]
        agg["summary"] = {
            "n": len(summ),
            "mean_coverage": round(sum(cov) / len(cov), 4) if cov else 0.0,
            "mean_value_grounding_rate": round(sum(vg) / len(vg), 4) if vg else 0.0,
        }
    return agg


def score_example(row: dict, prediction_text: str) -> dict:
    pred_obj, parsed = common.parse_json_safe(prediction_text)
    gold_obj, _ = common.parse_json_safe(row["target"])
    rec = {"task": row["task"], "parsed": parsed, "prediction": prediction_text}
    if row["task"] == "EXTRACT_ENTITIES":
        gold_entities = (gold_obj or {}).get("entities", []) if isinstance(gold_obj, dict) else []
        rec["ner"] = score_ner(pred_obj, gold_entities, row["source_text"])
    else:
        rec["summary"] = score_summary(pred_obj, gold_obj, row["source_text"])
    return rec


# --------------------------------------------------------------------------- #
# Generation (GPU)
# --------------------------------------------------------------------------- #


def generate_predictions(rows, model, processor, max_new_tokens=512) -> list[str]:
    import torch

    tok = getattr(processor, "tokenizer", processor)
    preds = []
    model.eval()
    for r in rows:
        ids = tok.apply_chat_template(
            r["messages"], tokenize=True, add_generation_prompt=True, return_tensors="pt"
        ).to(model.device)
        with torch.no_grad():
            out = model.generate(
                ids, max_new_tokens=max_new_tokens, do_sample=False, num_beams=1
            )
        text = tok.decode(out[0][ids.shape[-1]:], skip_special_tokens=True)
        preds.append(text.strip())
    return preds


def load_base(eff: dict):
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    dtype = torch.bfloat16 if eff["effective"]["precision"] == "bf16" else torch.float16
    processor = AutoProcessor.from_pretrained(eff["model"]["id"])
    model = AutoModelForImageTextToText.from_pretrained(
        eff["model"]["id"], torch_dtype=dtype, device_map="auto", attn_implementation="eager"
    )
    return model, processor


def load_with_adapter(eff: dict, adapter_dir: str):
    from peft import PeftModel

    model, processor = load_base(eff)
    model = PeftModel.from_pretrained(model, adapter_dir)
    return model, processor


def evaluate_model(rows, model, processor, max_new_tokens=512) -> tuple[dict, list[dict]]:
    preds = generate_predictions(rows, model, processor, max_new_tokens)
    per_example = [score_example(r, p) for r, p in zip(rows, preds)]
    return aggregate(per_example), per_example


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(common.DEFAULT_CONFIG_PATH))
    ap.add_argument("--data", default="data")
    ap.add_argument("--adapter", default="outputs/adapter")
    ap.add_argument("--out", default="outputs/metrics")
    ap.add_argument("--limit", type=int, default=None, help="cap test examples")
    ap.add_argument("--max-new-tokens", type=int, default=512)
    args = ap.parse_args()

    cfg = common.load_yaml(args.config)
    from train import detect_gpu, resolve_effective  # reuse detection

    eff = resolve_effective(cfg, detect_gpu())
    rows = load_jsonl(Path(args.data) / "test.jsonl")
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("no test rows", file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Baseline (unchanged base) on {len(rows)} held-out examples ===")
    base_model, processor = load_base(eff)
    base_agg, base_ex = evaluate_model(rows, base_model, processor, args.max_new_tokens)
    print(json.dumps(base_agg, indent=2))

    del base_model
    try:
        import torch

        torch.cuda.empty_cache()
    except Exception:
        pass

    print("=== Tuned (base + LoRA adapter), same decoding ===")
    tuned_model, processor = load_with_adapter(eff, args.adapter)
    tuned_agg, tuned_ex = evaluate_model(rows, tuned_model, processor, args.max_new_tokens)
    print(json.dumps(tuned_agg, indent=2))

    report = {
        "n_test": len(rows),
        "decoding": {"do_sample": False, "num_beams": 1, "max_new_tokens": args.max_new_tokens},
        "baseline": base_agg,
        "tuned": tuned_agg,
    }
    (out_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "baseline_examples.json").write_text(json.dumps(base_ex, indent=2), encoding="utf-8")
    (out_dir / "tuned_examples.json").write_text(json.dumps(tuned_ex, indent=2), encoding="utf-8")
    print(f"=== wrote metrics + per-example predictions to {out_dir}/ ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
