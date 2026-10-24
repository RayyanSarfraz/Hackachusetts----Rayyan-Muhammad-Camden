"""
Clarifying-question generation for the match flow.

Given a normalized engine patient profile (from ``patient_processor``), find the
matcher-relevant facts that are MISSING or UNKNOWN and turn them into clarifying
questions the frontend can render as a form.

This is deliberately profile-gap-driven (not per-trial criteria scraping), so it
works on the current dataset which has no eligibility-criteria text. Questions
are emitted in the same dict shape as integration's ``ClarificationQuestion``
(question_id / required_fact_key / display_question / answer_type / ...), so the
frontend and integration layer see a consistent contract.

No fabrication: a gap only becomes a question; it never becomes an assumed value.
"""
from __future__ import annotations

import hashlib

# Matcher-relevant facts we ask about when missing, in priority order.
# Each: (fact_key, display_question, answer_type)
_GAP_QUESTIONS = [
    ("age", "What is the patient's age?", "number"),
    ("sex_for_eligibility",
     "What is the patient's sex for eligibility screening?", "text"),
    ("primary_condition",
     "What is the patient's primary medical condition?", "text"),
    ("location_state",
     "Which U.S. state is the patient located in?", "text"),
]


def _qid(fact_key: str) -> str:
    """Stable question id per fact (so repeat calls don't churn ids)."""
    return "q_" + hashlib.md5(fact_key.encode("utf-8")).hexdigest()[:10]


def _has_value(profile: dict, key: str) -> bool:
    """True when the profile already carries a usable value for ``key``."""
    if key == "age":
        return profile.get("age") is not None
    if key == "sex_for_eligibility":
        return bool(profile.get("sex_for_eligibility"))
    if key == "primary_condition":
        return bool((profile.get("primary_condition") or "").strip())
    if key == "location_state":
        return bool((profile.get("location") or {}).get("state"))
    return False


def generate_questions(normalized_profile: dict) -> list[dict]:
    """
    Return clarifying questions for matcher-relevant gaps in the profile.

    Each item matches integration's ClarificationQuestion dict shape so the
    frontend renders them uniformly.
    """
    profile = normalized_profile or {}
    questions: list[dict] = []
    for fact_key, prompt, answer_type in _GAP_QUESTIONS:
        if _has_value(profile, fact_key):
            continue
        questions.append(
            {
                "question_id": _qid(fact_key),
                "required_fact_key": fact_key,
                "display_question": prompt,
                "answer_type": answer_type,
                "related_trial_ids": [],
                "source_criterion_ids": [],
            }
        )
    return questions


def apply_answers(patient: dict, answers: dict) -> dict:
    """
    Merge form answers back into a raw patient payload for re-matching.

    ``answers`` maps ``required_fact_key`` -> value (strings/numbers). Only
    known fact keys are applied; "unknown"/blank answers are ignored (they stay
    unknown — never fabricated). Returns a new patient dict; input isn't mutated.
    """
    patient = dict(patient or {})
    answers = answers or {}

    def _blank(v):
        return v is None or (isinstance(v, str) and v.strip().lower() in ("", "unknown"))

    if not _blank(answers.get("age")):
        try:
            patient["age"] = int(answers["age"])
        except (TypeError, ValueError):
            pass
    if not _blank(answers.get("sex_for_eligibility")):
        patient["sex_for_eligibility"] = str(answers["sex_for_eligibility"]).strip().lower()
    if not _blank(answers.get("primary_condition")):
        patient["primary_condition"] = str(answers["primary_condition"]).strip()
    if not _blank(answers.get("location_state")):
        location = dict(patient.get("location") or {})
        location["state"] = str(answers["location_state"]).strip()
        patient["location"] = location

    return patient
