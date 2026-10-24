"""Shared helpers for MedMatch Model A.

Pure-Python utilities with no heavy ML dependencies so they can be imported by
unit tests, data preparation, and the training/eval/infer scripts alike:

- config loading + GPU-profile deep-merge (the "effective config")
- task prompt contracts (EXTRACT_SUMMARY / EXTRACT_ENTITIES)
- robust JSON parsing of model/dataset strings
- NER annotation verification and span-offset recomputation
- deterministic case-level train/val/test splitting
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = HERE / "config.yaml"

# Map the Colab GPU identifier (from `nvidia-smi` / torch device name) to a
# profile key in config.gpu_profiles. A100 resolves to 40gb/80gb by VRAM.
GPU_NAME_PATTERNS = [
    ("g4", re.compile(r"(rtx\s*pro\s*6000|blackwell|\bg4\b)", re.I)),
    ("a100", re.compile(r"a100", re.I)),
    ("l4", re.compile(r"\bl4\b", re.I)),
    ("t4", re.compile(r"\bt4\b", re.I)),
]


def load_yaml(path: str | Path) -> dict:
    """Load YAML. Uses PyYAML if present, else a tiny restricted fallback.

    The fallback only needs to parse our own config.yaml (nested maps, lists,
    scalars). We prefer PyYAML whenever it is installed (always true on Colab).
    """
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except Exception:
        return _mini_yaml(text)


def _coerce_scalar(tok: str) -> Any:
    tok = tok.strip()
    if tok == "" or tok.lower() in {"null", "none", "~"}:
        return None
    if tok.lower() == "true":
        return True
    if tok.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    if re.fullmatch(r"-?\d*\.\d+([eE][-+]?\d+)?", tok) or re.fullmatch(
        r"-?\d+[eE][-+]?\d+", tok
    ):
        return float(tok)
    if tok.startswith("[") and tok.endswith("]"):
        inner = tok[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(x) for x in inner.split(",")]
    return tok.strip().strip("'\"")


def _mini_yaml(text: str) -> dict:
    """Minimal indentation-based YAML for our own config only."""
    root: dict = {}
    # stack of (indent, container)
    stack: list[tuple[int, Any]] = [(-1, root)]
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip() if "#" not in raw.split(":", 1)[0] else raw.rstrip()
        # strip trailing comments only when not inside quotes/brackets (best effort)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if content.startswith("- "):
            val = _coerce_scalar(content[2:])
            if not isinstance(parent, list):
                continue
            parent.append(val)
            continue
        if ":" not in content:
            continue
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            # Peek: decide list vs map lazily -> default to dict, switch to list
            # if the next populated line at deeper indent is a "- " item.
            child: Any = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _coerce_scalar(rest)
    return root


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into a copy of base."""
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def resolve_gpu_profile_key(gpu_name: str, vram_gb: float | None, config: dict) -> str:
    """Pick a gpu_profiles key from the detected GPU name and VRAM."""
    profiles = config.get("gpu_profiles", {})
    family = None
    for key, pat in GPU_NAME_PATTERNS:
        if pat.search(gpu_name or ""):
            family = key
            break
    if family == "a100":
        # choose 80gb vs 40gb by measured VRAM
        if vram_gb is not None and vram_gb >= 60 and "a100_80gb" in profiles:
            return "a100_80gb"
        return "a100_40gb" if "a100_40gb" in profiles else "a100_80gb"
    if family and family in profiles:
        return family
    # fall back to configured default
    return profiles.get("default_profile", "a100_40gb")


def effective_config(config: dict, profile_key: str) -> dict:
    """Deep-merge the chosen gpu profile over model/training and surface the
    key training knobs into a flat `effective` block for logging/assertions.

    Critically: a high-memory profile's load_in_4bit=false overrides the base
    model.load_in_4bit=true. We never silently train a BF16 profile in 4-bit.
    """
    profiles = config.get("gpu_profiles", {})
    profile = profiles.get(profile_key, {})
    merged = copy.deepcopy(config)

    method = profile.get("method")
    load_in_4bit = profile.get("load_in_4bit", config["model"].get("load_in_4bit"))
    precision = profile.get("precision", "bf16")
    max_seq_length = profile.get(
        "max_seq_length", config["training"].get("max_seq_length")
    )
    per_device_bs = profile.get(
        "per_device_train_batch_size",
        config["training"].get("per_device_train_batch_size"),
    )
    grad_accum = profile.get(
        "gradient_accumulation_steps",
        config["training"].get("gradient_accumulation_steps"),
    )
    optimizer = profile.get("optimizer", config["training"].get("optimizer"))

    merged["model"]["load_in_4bit"] = load_in_4bit
    merged["training"]["max_seq_length"] = max_seq_length
    merged["training"]["per_device_train_batch_size"] = per_device_bs
    merged["training"]["gradient_accumulation_steps"] = grad_accum
    merged["training"]["optimizer"] = optimizer

    merged["effective"] = {
        "profile_key": profile_key,
        "method": method,
        "load_in_4bit": load_in_4bit,
        "precision": precision,
        "torch_dtype": "bfloat16" if precision == "bf16" else "float16",
        "max_seq_length": max_seq_length,
        "per_device_train_batch_size": per_device_bs,
        "gradient_accumulation_steps": grad_accum,
        "effective_batch_size": per_device_bs * grad_accum,
        "optimizer": optimizer,
        "learning_rate": config["training"]["learning_rate"],
        "num_train_epochs": config["training"]["num_train_epochs"],
        "lora_r": config["lora"]["r"],
        "lora_alpha": config["lora"]["alpha"],
        "lora_dropout": config["lora"]["dropout"],
    }
    return merged


# --------------------------------------------------------------------------- #
# Task contracts
# --------------------------------------------------------------------------- #

SUMMARY_SYSTEM = (
    "You are a clinical information extraction assistant. Read the clinical "
    "note and extract structured facts. Output ONLY a single JSON object. "
    "Use null for any field not stated in the note. Never invent facts, "
    "dosages, dates, or negations that are not supported by the text."
)

SUMMARY_INSTRUCTION = (
    "Task: EXTRACT_SUMMARY\n"
    "From the clinical note below, extract a JSON object with keys: "
    "visit_motivation, patient_information, medical_conditions (list), "
    "treatments (list of {{name, dosage, frequency, duration, reason}}), "
    "and discharge. Use null where the note does not state a value.\n\n"
    "Clinical note:\n{note}"
)

ENTITIES_SYSTEM = (
    "You are a medical named-entity extraction assistant. Extract entities "
    "that appear verbatim in the text. Output ONLY a single JSON object. "
    "Copy entity surface text exactly as it appears; do not paraphrase and do "
    "not fabricate character offsets."
)

ENTITIES_INSTRUCTION = (
    "Task: EXTRACT_ENTITIES\n"
    "From the medical text below, extract a JSON object of the form "
    '{{"entities": [{{"text": <verbatim surface string>, "label": <type>}}]}}. '
    "Only include spans that occur exactly in the text.\n\n"
    "Text:\n{text}"
)


def build_summary_messages(note: str) -> list[dict]:
    return [
        {"role": "system", "content": SUMMARY_SYSTEM},
        {"role": "user", "content": SUMMARY_INSTRUCTION.format(note=note)},
    ]


def build_entities_messages(text: str) -> list[dict]:
    return [
        {"role": "system", "content": ENTITIES_SYSTEM},
        {"role": "user", "content": ENTITIES_INSTRUCTION.format(text=text)},
    ]


# --------------------------------------------------------------------------- #
# JSON parsing
# --------------------------------------------------------------------------- #


def parse_json_safe(raw: Any) -> tuple[dict | list | None, bool]:
    """Best-effort parse of a JSON string.

    Returns (value, ok). Handles the common cases seen in these datasets and in
    model output: raw already a dict/list, fenced ```json blocks, and leading
    prose before the first `{`.
    """
    if raw is None:
        return None, False
    if isinstance(raw, (dict, list)):
        return raw, True
    if not isinstance(raw, str):
        return None, False
    s = raw.strip()
    if not s:
        return None, False
    # strip code fences
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", s, re.S | re.I)
    if fence:
        s = fence.group(1).strip()
    try:
        return json.loads(s), True
    except Exception:
        pass
    # fall back to first balanced {...} or [...]
    start = min(
        [i for i in (s.find("{"), s.find("[")) if i != -1] or [-1]
    )
    if start == -1:
        return None, False
    opener = s[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(s[start : i + 1]), True
                except Exception:
                    return None, False
    return None, False


# --------------------------------------------------------------------------- #
# NER verification
# --------------------------------------------------------------------------- #


@dataclass
class NerStats:
    total: int = 0
    kept: int = 0
    dropped_offset_mismatch: int = 0
    dropped_empty: int = 0


def verify_entity_span(text: str, entity: dict) -> bool:
    """True iff text[start:end] == entity['text'] exactly."""
    try:
        start = int(entity["start"])
        end = int(entity["end"])
        surface = entity["text"]
    except (KeyError, TypeError, ValueError):
        return False
    if start < 0 or end > len(text) or start >= end:
        return False
    return text[start:end] == surface


def clean_entities(text: str, entities: Iterable[dict], stats: NerStats) -> list[dict]:
    """Keep only entities whose offsets verify against the source text.

    Output entities carry only label + verbatim surface text; we deliberately
    do NOT train on character offsets (recomputed in postprocessing instead).
    """
    kept: list[dict] = []
    for ent in entities or []:
        stats.total += 1
        surface = (ent or {}).get("text") or ""
        if not surface.strip():
            stats.dropped_empty += 1
            continue
        if not verify_entity_span(text, ent):
            stats.dropped_offset_mismatch += 1
            continue
        kept.append({"text": surface, "label": ent.get("label", "")})
        stats.kept += 1
    return kept


def recompute_offsets(text: str, entities: Iterable[dict]) -> list[dict]:
    """Postprocessing: locate each verbatim entity surface in text to supply
    character offsets the model was never asked to fabricate."""
    out = []
    for ent in entities or []:
        surface = (ent or {}).get("text") or ""
        label = (ent or {}).get("label", "")
        idx = text.find(surface) if surface else -1
        if idx == -1:
            out.append({"text": surface, "label": label, "start": None, "end": None})
        else:
            out.append(
                {"text": surface, "label": label, "start": idx, "end": idx + len(surface)}
            )
    return out


# --------------------------------------------------------------------------- #
# Deterministic case-level splitting + dedup
# --------------------------------------------------------------------------- #


def _case_bucket(case_id: str, seed: int) -> float:
    """Stable hash in [0,1) keyed on (seed, case_id). Same input -> same bucket
    across runs and machines (unlike Python's salted hash())."""
    h = hashlib.sha256(f"{seed}:{case_id}".encode("utf-8")).hexdigest()
    return int(h[:16], 16) / float(1 << 64)


def assign_split(case_id: str, seed: int, train: float, val: float) -> str:
    """Assign a case to train/validation/test by its stable bucket.

    Splitting is by original case id (not per transformed prompt) so all prompts
    from one case land in the same split -> no leakage.
    """
    b = _case_bucket(str(case_id), seed)
    if b < train:
        return "train"
    if b < train + val:
        return "validation"
    return "test"


def content_fingerprint(text: str) -> str:
    """Normalized fingerprint for near-duplicate detection across splits."""
    norm = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()
