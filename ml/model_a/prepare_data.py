"""Deterministic dataset preparation for MedMatch Model A.

Ingests the two Hugging Face datasets, normalizes them into a single chat SFT
format with distinct tasks (EXTRACT_SUMMARY / EXTRACT_ENTITIES), filters and
de-duplicates, splits by original case id, and writes train/val/test JSONL plus
a manifest with quality counts, dataset revisions, and the random seed.

DO NOT blindly concatenate the two datasets: they are different supervision
signals. Each example records its source id, task, and language.

Usage:
    python prepare_data.py --config config.yaml --out data \
        --primary-n 1000 --secondary-n 150
    python prepare_data.py --smoke            # 20 examples total, no HF download
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import common


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def _canonical_summary(summary_obj) -> str:
    """Stable JSON string for the summary target (sorted keys, compact)."""
    return json.dumps(summary_obj, ensure_ascii=False, sort_keys=True)


def build_primary_example(row: dict, cfg: dict, max_chars: int) -> dict | None:
    """full_note -> summary (EXTRACT_SUMMARY). Returns None if unusable."""
    note = (row.get("full_note") or "").strip()
    summary_raw = row.get("summary")
    if not note:
        return None
    summary_obj, ok = common.parse_json_safe(summary_raw)
    if not ok or summary_obj is None:
        return None
    case_id = str(row.get("idx") or common.content_fingerprint(note))
    target = _canonical_summary(summary_obj)
    # Guard against silently dropping target facts: if the prompt+answer clearly
    # cannot fit, mark overlong so the caller can bucket/exclude it.
    overlong = (len(note) + len(target)) > max_chars
    return {
        "case_id": case_id,
        "source": cfg["data"]["primary_id"],
        "task": cfg["data"]["primary_task"],
        "language": "english",
        "messages": common.build_summary_messages(note),
        "target": target,
        "source_text": note,
        "overlong": overlong,
    }


def build_secondary_example(
    row: dict, cfg: dict, stats: common.NerStats, max_chars: int
) -> dict | None:
    """text -> entities (EXTRACT_ENTITIES), english only, verified offsets."""
    lang = (row.get("language") or "").strip().lower()
    if lang != "english":
        return None
    text = (row.get("text") or "").strip()
    if not text:
        return None
    kept = common.clean_entities(text, row.get("entities") or [], stats)
    if not kept:
        return None
    case_id = common.content_fingerprint(text)
    target = json.dumps({"entities": kept}, ensure_ascii=False, sort_keys=True)
    overlong = (len(text) + len(target)) > max_chars
    return {
        "case_id": case_id,
        "source": cfg["data"]["secondary_id"],
        "task": cfg["data"]["secondary_task"],
        "language": "english",
        "messages": common.build_entities_messages(text),
        "target": target,
        "source_text": text,
        "overlong": overlong,
    }


def dedupe_and_split(examples: list[dict], cfg: dict) -> tuple[list[dict], dict]:
    """Assign splits by case id; drop exact/near-duplicate source text, keeping
    the first occurrence. Prevents the same case leaking across splits."""
    seed = cfg["data"]["seed"]
    train = cfg["data"]["split_train"]
    val = cfg["data"]["split_validation"]
    seen_fp: dict[str, str] = {}
    seen_case: dict[str, str] = {}
    dup_dropped = 0
    out = []
    for ex in examples:
        fp = common.content_fingerprint(ex["source_text"])
        if fp in seen_fp:
            dup_dropped += 1
            continue
        # keep case->split stable even if the same case appears twice
        if ex["case_id"] in seen_case:
            split = seen_case[ex["case_id"]]
        else:
            split = common.assign_split(ex["case_id"], seed, train, val)
            seen_case[ex["case_id"]] = split
        seen_fp[fp] = split
        ex = dict(ex)
        ex["split"] = split
        out.append(ex)
    counts = {"duplicates_dropped": dup_dropped}
    return out, counts


def load_hf(dataset_id: str):
    from datasets import load_dataset  # lazy import

    return load_dataset(dataset_id, split="train")


def smoke_rows() -> tuple[list[dict], list[dict]]:
    """Tiny built-in fixtures so the pipeline is testable with no network/GPU."""
    primary = [
        {
            "idx": f"smoke-p-{i}",
            "full_note": (
                f"Patient {i}: 54-year-old presenting with chest pain. "
                "Started on aspirin 81 mg daily. No known drug allergies. "
                "Discharged home with cardiology follow-up."
            ),
            "summary": json.dumps(
                {
                    "visit_motivation": "chest pain",
                    "treatments": [
                        {"name": "aspirin", "dosage": "81 mg", "frequency": "daily"}
                    ],
                    "discharge": {"follow up": "cardiology"},
                }
            ),
        }
        for i in range(12)
    ]
    secondary = [
        {
            "text": f"Prescribed metformin for diabetes in patient {i}.",
            "language": "english",
            "entities": [
                {"text": "metformin", "label": "MEDICATION", "start": 11, "end": 20},
                {"text": "diabetes", "label": "CONDITION", "start": 25, "end": 33},
            ],
        }
        for i in range(8)
    ]
    return primary, secondary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(common.DEFAULT_CONFIG_PATH))
    ap.add_argument("--out", default="data")
    ap.add_argument("--primary-n", type=int, default=None)
    ap.add_argument("--secondary-n", type=int, default=None)
    ap.add_argument("--smoke", action="store_true", help="use built-in fixtures")
    args = ap.parse_args()

    cfg = common.load_yaml(args.config)
    out_dir = Path(args.out)
    # ~4 chars/token heuristic for the fit guard at max_seq_length.
    max_chars = cfg["training"]["max_seq_length"] * 4

    primary_n = args.primary_n or cfg["data"]["target_primary_examples"]
    secondary_n = args.secondary_n or cfg["data"]["target_secondary_examples"]

    ner_stats = common.NerStats()
    rev = {"primary": None, "secondary": None}

    if args.smoke:
        p_rows, s_rows = smoke_rows()
        primary_n = min(primary_n, len(p_rows))
        secondary_n = min(secondary_n, len(s_rows))
    else:
        print(f"[prepare] loading {cfg['data']['primary_id']} ...", flush=True)
        p_ds = load_hf(cfg["data"]["primary_id"])
        s_ds = load_hf(cfg["data"]["secondary_id"])
        rev["primary"] = str(getattr(p_ds, "_fingerprint", None))
        rev["secondary"] = str(getattr(s_ds, "_fingerprint", None))
        p_rows = p_ds
        s_rows = s_ds

    primary_examples: list[dict] = []
    for row in p_rows:
        ex = build_primary_example(dict(row), cfg, max_chars)
        if ex:
            primary_examples.append(ex)
        if len(primary_examples) >= primary_n:
            break

    secondary_examples: list[dict] = []
    for row in s_rows:
        ex = build_secondary_example(dict(row), cfg, ner_stats, max_chars)
        if ex:
            secondary_examples.append(ex)
        if len(secondary_examples) >= secondary_n:
            break

    all_examples = primary_examples + secondary_examples
    split_examples, dup_counts = dedupe_and_split(all_examples, cfg)

    overlong = sum(1 for e in split_examples if e.get("overlong"))

    by_split: dict[str, list[dict]] = {"train": [], "validation": [], "test": []}
    for ex in split_examples:
        by_split[ex["split"]].append(ex)

    for split, rows in by_split.items():
        _write_jsonl(out_dir / f"{split}.jsonl", rows)

    def _counts(rows):
        by_task, by_lang = {}, {}
        for r in rows:
            by_task[r["task"]] = by_task.get(r["task"], 0) + 1
            by_lang[r["language"]] = by_lang.get(r["language"], 0) + 1
        return {"total": len(rows), "by_task": by_task, "by_language": by_lang}

    manifest = {
        "created_utc": _utc(),
        "seed": cfg["data"]["seed"],
        "smoke": args.smoke,
        "datasets": {
            "primary": {"id": cfg["data"]["primary_id"], "revision": rev["primary"]},
            "secondary": {
                "id": cfg["data"]["secondary_id"],
                "revision": rev["secondary"],
            },
        },
        "requested": {"primary_n": primary_n, "secondary_n": secondary_n},
        "quality": {
            "ner": vars(ner_stats),
            "duplicates_dropped": dup_counts["duplicates_dropped"],
            "overlong_flagged": overlong,
        },
        "splits": {
            "train": _counts(by_split["train"]),
            "validation": _counts(by_split["validation"]),
            "test": _counts(by_split["test"]),
        },
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(manifest["splits"], indent=2))
    print(f"[prepare] NER verification: {vars(ner_stats)}")
    print(f"[prepare] wrote splits + manifest to {out_dir}/")
    # leakage assertion: no case id in more than one split
    case_to_splits: dict[str, set] = {}
    for ex in split_examples:
        case_to_splits.setdefault(ex["case_id"], set()).add(ex["split"])
    leaks = {c: s for c, s in case_to_splits.items() if len(s) > 1}
    if leaks:
        print(f"[prepare] ERROR: {len(leaks)} case(s) leaked across splits", flush=True)
        return 1
    print("[prepare] no case-level leakage detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
