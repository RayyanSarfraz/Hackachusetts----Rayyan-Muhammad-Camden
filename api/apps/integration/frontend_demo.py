"""
Frontend-facing demo data + note parser.

This module serves the EXACT shapes the React frontend consumes through its
`TrialBridgeApi` seam (see client/src/types/domain.ts):

  GET  /api/trials        -> Trial[]        (unassessed; criteria carry dependsOn)
  POST /api/extract-facts -> PatientProfile (facts keyed by FactKey; unknown = null)

These are a faithful backend port of the frontend's local mock
(client/src/data/trials.ts + demoPatient.ts) and deterministic parser
(client/src/lib/noteParser.ts), so the UI renders identically whether it runs
on LocalMockApi or HttpTrialBridgeApi.

All data is fictional. Missing information stays Unknown (null) and is never
turned into a negative finding.
"""

from __future__ import annotations

import re
from typing import Optional


# =============================================================================
# FACT CATALOGUE  (mirrors client/src/data/demoPatient.ts FACT_DEFINITIONS)
# =============================================================================

FACT_DEFINITIONS: list[dict[str, str]] = [
    {"key": "age", "label": "Age"},
    {"key": "condition", "label": "Condition"},
    {"key": "location", "label": "Location"},
    {"key": "previousTreatment", "label": "Previous treatment"},
    {"key": "egfrStatus", "label": "EGFR status"},
    {"key": "cancerStage", "label": "Cancer stage"},
    {"key": "ecogStatus", "label": "ECOG performance status"},
]


DEMO_PATIENT_NOTES = """Clinical Note (FICTIONAL — DEMO DATA ONLY)

Patient is a 54-year-old presenting for oncology follow-up.
Diagnosis: non-small cell lung cancer.
Location: Boston, MA.
Treatment history: prior chemotherapy completed.

EGFR mutation testing: not documented in the available record.
Cancer stage: not documented in the available record.
ECOG performance status: not documented in the available record."""


# =============================================================================
# DEMO TRIALS  (faithful port of client/src/data/trials.ts DEMO_TRIALS)
# =============================================================================

def _crit(cid: str, text: str, depends_on: list[str], effort: int, kind: str,
          category: str = "inclusion") -> dict:
    return {
        "id": cid,
        "text": text,
        "category": category,
        "dependsOn": depends_on,
        "estimatedEffort": effort,
        "kind": kind,
    }


DEMO_TRIALS: list[dict] = [
    {
        "id": "DEMO-A",
        "name": "Study A — Targeted Therapy in EGFR+ Advanced NSCLC (Fictional)",
        "location": "Boston, MA",
        "distance": {"miles": 3, "label": "mock"},
        "sourceLabel": "Demo criterion",
        "criteria": [
            _crit("A-condition", "Histologically confirmed non-small cell lung cancer (NSCLC).", ["condition"], 1, "condition"),
            _crit("A-age", "Age between 18 and 75 years, inclusive.", ["age"], 1, "age"),
            _crit("A-egfr", "Documented EGFR activating mutation (EGFR positive) required.", ["egfrStatus"], 2, "egfr"),
            _crit("A-stage", "Stage IV disease required.", ["cancerStage"], 2, "stage"),
            _crit("A-ecog", "ECOG performance status 0 to 1.", ["ecogStatus"], 2, "ecog"),
        ],
    },
    {
        "id": "DEMO-B",
        "name": "Study B — Chemo-Immunotherapy in EGFR-wildtype NSCLC (Fictional)",
        "location": "Cambridge, MA",
        "distance": {"miles": 6, "label": "mock"},
        "sourceLabel": "Demo criterion",
        "criteria": [
            _crit("B-condition", "Histologically confirmed non-small cell lung cancer (NSCLC).", ["condition"], 1, "condition"),
            _crit("B-age", "Age between 18 and 75 years, inclusive.", ["age"], 1, "age"),
            _crit("B-egfr", "EGFR wild-type (EGFR negative) required.", ["egfrStatus"], 2, "egfr"),
            _crit("B-stage", "Stage III or Stage IV disease.", ["cancerStage"], 2, "stage"),
        ],
    },
    {
        "id": "DEMO-C",
        "name": "Study C — Next-Generation TKI in EGFR+ NSCLC (Fictional)",
        "location": "Worcester, MA",
        "distance": {"miles": 48, "label": "mock"},
        "sourceLabel": "Demo criterion",
        "criteria": [
            _crit("C-condition", "Histologically confirmed non-small cell lung cancer (NSCLC).", ["condition"], 1, "condition"),
            _crit("C-age", "Age between 18 and 75 years, inclusive.", ["age"], 1, "age"),
            _crit("C-egfr", "Documented EGFR activating mutation (EGFR positive) required.", ["egfrStatus"], 2, "egfr"),
            _crit("C-ecog", "ECOG performance status 0 to 2.", ["ecogStatus"], 2, "ecog"),
        ],
    },
    {
        "id": "DEMO-D",
        "name": "Study D — Broad-Eligibility NSCLC Platform Study (Fictional)",
        "location": "Springfield, MA",
        "distance": {"miles": 90, "label": "mock"},
        "sourceLabel": "Demo criterion",
        "criteria": [
            _crit("D-condition", "Histologically confirmed non-small cell lung cancer (NSCLC).", ["condition"], 1, "condition"),
            _crit("D-age", "Age between 18 and 75 years, inclusive.", ["age"], 1, "age"),
            _crit("D-stage", "Stage IV disease required. No EGFR restriction.", ["cancerStage"], 2, "stage"),
            _crit("D-ecog", "ECOG performance status 0 to 1.", ["ecogStatus"], 2, "ecog"),
        ],
    },
]


def get_demo_trials() -> list[dict]:
    """Return the frontend-shaped demo trials (deep-copied to avoid mutation)."""
    import copy
    return copy.deepcopy(DEMO_TRIALS)


# =============================================================================
# NOTE PARSER  (faithful port of client/src/lib/noteParser.ts)
# =============================================================================

def _parse_age(notes: str) -> Optional[dict]:
    patterns = [
        r"(\d{1,3})[\s-]*year[\s-]*old",
        r"\bage[:\s]+(\d{1,3})\b",
        r"\b(\d{1,3})\s*(?:yo|y/o|yrs?)\b",
    ]
    for pat in patterns:
        m = re.search(pat, notes, re.IGNORECASE)
        if m:
            age = int(m.group(1))
            if 0 < age < 120:
                return {"value": age, "evidence": m.group(0).strip()}
    return None


def _parse_condition(notes: str) -> Optional[dict]:
    m = re.search(r"non[\s-]?small[\s-]?cell lung cancer|\bNSCLC\b", notes, re.IGNORECASE)
    if m:
        return {"value": "Non-small cell lung cancer", "evidence": m.group(0).strip()}
    return None


def _parse_location(notes: str) -> Optional[dict]:
    labeled = re.search(r"location[:\s]+([A-Za-z.\s]+,\s*[A-Z]{2})\b", notes, re.IGNORECASE)
    if labeled:
        return {"value": labeled.group(1).strip(), "evidence": labeled.group(0).strip()}
    bare = re.search(r"\b([A-Z][a-zA-Z.]+(?:\s[A-Z][a-zA-Z.]+)*,\s*[A-Z]{2})\b", notes)
    if bare:
        return {"value": bare.group(1).strip(), "evidence": bare.group(1).strip()}
    return None


def _parse_previous_treatment(notes: str) -> Optional[dict]:
    m = re.search(r"\b(chemotherapy|chemo|radiation|radiotherapy|immunotherapy|surgery|resection)\b", notes, re.IGNORECASE)
    if not m:
        return None
    token = m.group(1).lower()
    normalized = "Chemotherapy" if token == "chemo" else token[0].upper() + token[1:]
    return {"value": normalized, "evidence": m.group(0).strip()}


def _parse_egfr(notes: str) -> Optional[dict]:
    if re.search(r"egfr[^.\n]*\b(not documented|unknown|pending|not available|no result)\b", notes, re.IGNORECASE):
        return None
    m = re.search(r"egfr[^.\n]*\b(positive|mutation|mutant|detected|activating)\b", notes, re.IGNORECASE)
    if m:
        return {"value": "positive", "evidence": m.group(0).strip()}
    m = re.search(r"egfr[^.\n]*\b(negative|wild[\s-]?type|not detected|wildtype)\b", notes, re.IGNORECASE)
    if m:
        return {"value": "negative", "evidence": m.group(0).strip()}
    return None


def _normalize_stage(raw: str) -> str:
    mapping = {"1": "I", "2": "II", "3": "III", "4": "IV"}
    upper = raw.upper()
    return mapping.get(upper, upper)


def _parse_stage(notes: str) -> Optional[dict]:
    if re.search(r"stage[^.\n]*\b(not documented|unknown|pending|not available)\b", notes, re.IGNORECASE):
        return None
    m = re.search(r"\bstage\s+(IV|III|II|I|4|3|2|1)\b", notes, re.IGNORECASE)
    if m:
        return {"value": _normalize_stage(m.group(1)), "evidence": m.group(0).strip()}
    return None


def _parse_ecog(notes: str) -> Optional[dict]:
    if re.search(r"ecog[^.\n]*\b(not documented|unknown|pending|not available)\b", notes, re.IGNORECASE):
        return None
    m = re.search(r"ecog[^.\n]*?\b([0-4])\b", notes, re.IGNORECASE)
    if m:
        return {"value": int(m.group(1)), "evidence": m.group(0).strip()}
    return None


_PARSERS = {
    "age": _parse_age,
    "condition": _parse_condition,
    "location": _parse_location,
    "previousTreatment": _parse_previous_treatment,
    "egfrStatus": _parse_egfr,
    "cancerStage": _parse_stage,
    "ecogStatus": _parse_ecog,
}


def parse_notes(notes: str, patient_id: str = "patient-http") -> dict:
    """
    Parse free-text notes into the frontend's PatientProfile shape.

    Deterministic and local: no LLM, no network. Undocumented facts stay
    Unknown (value null, known false). Mirrors client/src/lib/noteParser.ts.
    """
    facts: dict[str, dict] = {}
    for definition in FACT_DEFINITIONS:
        key = definition["key"]
        label = definition["label"]
        base = {"key": key, "label": label, "value": None, "known": False, "source": "parsed"}
        result = _PARSERS[key](notes)
        if result:
            base["value"] = result["value"]
            base["known"] = True
            base["evidence"] = result["evidence"]
        facts[key] = base
    return {"id": patient_id, "facts": facts, "rawNotes": notes}
