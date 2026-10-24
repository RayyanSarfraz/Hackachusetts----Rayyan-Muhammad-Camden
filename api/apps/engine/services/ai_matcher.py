"""
Eligibility matching.

This is where the future fine-tuned eligibility model will score a patient
against each candidate trial's inclusion/exclusion criteria. That model is NOT
available in Phase 1.

Until it exists, matching reports itself unavailable and returns no eligibility
verdicts. We deliberately do NOT invent eligibility results.
"""
from __future__ import annotations


def available() -> bool:
    """No matching model is wired yet."""
    return False


def match(normalized_profile: dict, candidate_trials: list[dict]) -> dict:
    """
    Return ``{"available": bool, "matches": [...]}``.

    Phase 1: always unavailable with an empty matches list. No fabricated
    eligibility determinations.
    """
    return {
        "available": available(),
        "matches": [],
        "detail": "Eligibility matching model is not available yet.",
    }
