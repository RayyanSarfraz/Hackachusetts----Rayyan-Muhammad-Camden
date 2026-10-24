"""
Engine pipeline orchestration.

Two entry points:

- ``run_intake``: validate-stage output -> (extract if model available) ->
  normalize -> return a normalized profile dict. Used by POST /api/engine/intake/.
- ``run_trial_search``: normalized profile -> retrieve from ChromaDB -> (match)
  -> rank. Used by POST /api/engine/trials/.

Every AI/vector dependency is optional. When unavailable, the pipeline returns
honest "unavailable" flags and empty results — it never fabricates medical
facts, trials, or eligibility verdicts.
"""
from __future__ import annotations

from apps.engine.services import ai_matcher, ranker
from apps.engine.services.medical_extractor import extract_medical_entities
from apps.engine.services.patient_processor import normalize_patient
from apps.engine.services.retriever import build_query_text, get_retriever


def run_intake(patient: dict) -> dict:
    """
    Process a validated patient payload into a normalized profile.

    Returns a dict with the normalized profile plus ``model_available``.
    """
    extraction = extract_medical_entities(patient.get("medical_note", ""))
    model_available = extraction["available"]

    profile = normalize_patient(
        patient,
        extracted=extraction["entities"],
        extraction_available=model_available,
    )

    return {
        "profile": profile.as_dict(),
        "model_available": model_available,
    }


def run_trial_search(normalized_profile: dict, n_results: int = 10) -> dict:
    """
    Retrieve and (eventually) match clinical trials for a normalized profile.

    Returns honest availability flags. No fabricated trials or eligibility.
    """
    retriever = get_retriever()
    query_text = build_query_text(normalized_profile)
    retrieval = retriever.retrieve(query_text, n_results=n_results)

    match_result = ai_matcher.match(normalized_profile, retrieval["results"])
    ordered = ranker.rank(retrieval["results"], match_result.get("matches"))

    return {
        "query": query_text,
        "retrieval_available": retrieval["available"],
        "matching_available": match_result["available"],
        "results": ordered,
        "detail": (
            None
            if retrieval["available"]
            else "Trial retrieval is unavailable: no clinical-trial vector "
            "store is configured yet."
        ),
    }
