"""
Integration orchestrator: combines all components into unified workflow.

This module provides the main entry point for the integration layer:
- combine_trials_and_patient: Main orchestration function
- apply_clarification_answer: Handle answered questions
- update_preferences_only: Re-rank with new preferences (no clinical reassessment)
"""

from typing import Any, Optional

from .clarification import (
    apply_answer_to_profile,
    extract_questions_from_trials,
    find_affected_criteria,
    validate_answer,
)
from .contracts import (
    ClarificationQuestion,
    ComparisonResponse,
    ComparisonResult,
    CriterionStatus,
    PatientPreferences,
    PatientProfile,
    PracticalCompatibility,
    TrialCandidate,
)
from .fixtures import get_synthetic_patient, get_synthetic_trials
from .ranking import rank_trials, rerank_trials


def combine_trials_and_patient(
    trials: list[TrialCandidate],
    patient: PatientProfile,
) -> ComparisonResponse:
    """
    Main orchestration function: combine trial assessments and patient profile.
    
    This is the PRIMARY entry point for the integration layer.
    
    Args:
        trials: Assessed trial candidates (criteria already evaluated)
        patient: Patient profile with preferences
    
    Returns:
        Complete comparison response for frontend consumption
    
    Workflow:
        1. Rank trials by clinical status + practical fit
        2. Extract clarification questions from unknown criteria
        3. Build comparison results
        4. Generate missing data notes and limitations
    """
    # Rank trials (deterministic, no external calls)
    ranked_trials = rank_trials(trials, patient.preferences)
    
    # Extract clarification questions
    questions = extract_questions_from_trials(ranked_trials)
    
    # Build comparison results
    results: list[ComparisonResult] = []
    missing_notes: list[str] = []
    
    for rank, trial in enumerate(ranked_trials, start=1):
        # Check for conflicts and unknowns
        has_conflicts = any(
            c.status == CriterionStatus.CONFLICT for c in trial.criteria
        )
        has_unknowns = any(
            c.status == CriterionStatus.UNKNOWN for c in trial.criteria
        )
        
        # Build result
        result = ComparisonResult(
            trial=trial,
            rank=rank,
            clinical_status=trial.clinical_status or "unknown",
            practical_fit=trial.practical_fit,
            practical_reasons=trial.practical_reasons,
            has_conflicts=has_conflicts,
            has_unknowns=has_unknowns,
            clarification_needed=has_unknowns,
        )
        results.append(result)
        
        # Collect missing data notes
        if trial.nearest_distance_miles is None:
            missing_notes.append(
                f"Trial {trial.nct_id}: Location distance unknown"
            )
    
    # Add general limitations
    limitations = [
        "This is a preliminary assessment, not a definitive eligibility determination.",
        "All clinical criteria require verification by the study team.",
        "Unknown criteria indicate missing information, not ineligibility.",
        "Geographic distance is straight-line, not driving distance.",
        "This demonstration uses fictional patient data for illustration.",
    ]
    
    return ComparisonResponse(
        patient_summary=patient.to_sanitized_dict(),
        results=results,
        questions=questions,
        missing_data_notes=missing_notes,
        limitations=limitations,
    )


def apply_clarification_answer(
    trials: list[TrialCandidate],
    patient: PatientProfile,
    question_id: str,
    answer: Any,
) -> tuple[PatientProfile, list[str], list[str]]:
    """
    Apply an answer to a clarification question.
    
    CRITICAL: This does NOT automatically resolve criteria.
    It returns which criteria need reassessment.
    
    Args:
        trials: Current trial assessments
        patient: Current patient profile
        question_id: ID of the question being answered
        answer: The answer value
    
    Returns:
        (updated_profile, affected_criteria, criteria_requiring_reassessment)
    
    Note:
        The caller is responsible for:
        1. Reassessing affected criteria using clinical assessment logic
        2. Updating trial assessments
        3. Re-running combine_trials_and_patient
    """
    # Find the question
    questions = extract_questions_from_trials(trials)
    question = next((q for q in questions if q.question_id == question_id), None)
    
    if not question:
        raise ValueError(f"Question {question_id} not found")
    
    # Validate answer
    is_valid, error = validate_answer(question, answer)
    if not is_valid:
        raise ValueError(f"Invalid answer: {error}")
    
    # Apply to profile (creates new profile)
    updated_profile = apply_answer_to_profile(patient, question, answer)
    
    # Find affected criteria
    affected = find_affected_criteria(trials, question)
    affected_ids = [f"{tid}:{cid}" for tid, cid in affected]
    
    # All affected criteria need reassessment
    # (We don't automatically resolve them - that's the clinical module's job)
    criteria_requiring_reassessment = affected_ids
    
    return updated_profile, affected_ids, criteria_requiring_reassessment


def update_preferences_only(
    trials: list[TrialCandidate],
    new_preferences: PatientPreferences,
) -> list[TrialCandidate]:
    """
    Re-rank trials when only preferences have changed.
    
    This is the PREFERRED path for preference updates:
    - No clinical reassessment
    - No LLM calls
    - Pure deterministic calculation
    
    Args:
        trials: Previously assessed trials
        new_preferences: Updated practical preferences
    
    Returns:
        Re-ranked trials with updated practical_fit
    
    Use this when:
        - User changes max travel distance
        - User changes overnight preference
        - User changes visit frequency preference
    """
    return rerank_trials(trials, new_preferences)


# =============================================================================
# CONVENIENCE FUNCTIONS FOR DEMO
# =============================================================================

def run_synthetic_demo() -> ComparisonResponse:
    """
    Run the complete synthetic demo scenario.
    
    Returns a full comparison response using fictional patient data.
    """
    patient = get_synthetic_patient()
    trials = get_synthetic_trials()
    return combine_trials_and_patient(trials, patient)


def demo_preference_change() -> tuple[ComparisonResponse, ComparisonResponse]:
    """
    Demonstrate preference-only re-ranking.
    
    Returns:
        (before_response, after_response)
    
    Scenario:
        - Initial: max_travel = 50 miles
        - Changed: max_travel = 200 miles
        - Trial NCT05763157 (New Haven, ~130 miles) should move from
          INCOMPATIBLE to COMPATIBLE
    """
    patient = get_synthetic_patient()
    trials = get_synthetic_trials()
    
    # Initial comparison
    before = combine_trials_and_patient(trials, patient)
    
    # Change preference
    new_preferences = PatientPreferences(
        max_travel_miles=200.0,
        avoid_overnight_stays=patient.preferences.avoid_overnight_stays,
        max_visits=patient.preferences.max_visits,
    )
    
    # Re-rank without clinical reassessment
    updated_trials = update_preferences_only(trials, new_preferences)
    
    # New comparison
    patient.preferences = new_preferences
    after = combine_trials_and_patient(updated_trials, patient)
    
    return before, after


def demo_answer_question() -> tuple[ComparisonResponse, ComparisonResponse, str]:
    """
    Demonstrate answering a clarification question.
    
    Returns:
        (before_response, after_response, question_answered)
    
    Scenario:
        - Find first unknown question
        - Answer "no" to insulin_use question
        - Show updated comparison
    """
    patient = get_synthetic_patient()
    trials = get_synthetic_trials()
    
    # Initial comparison
    before = combine_trials_and_patient(trials, patient)
    
    # Find a question to answer
    if not before.questions:
        return before, before, "No questions available"
    
    question = before.questions[0]
    
    # For demo, answer "no" to the first question
    answer = "no"
    
    # Apply answer
    updated_profile, affected, reassess = apply_clarification_answer(
        trials, patient, question.question_id, answer
    )
    
    # For demo purposes, we simulate reassessment by updating criteria
    # In real system, this would call the clinical assessment module
    # For now, we'll just return the updated profile and note what changed
    
    # Build a simple "after" comparison noting the update
    # (Full reassessment would require clinical module integration)
    after = combine_trials_and_patient(trials, updated_profile)
    
    return before, after, f"Answered '{answer}' to: {question.display_question}"
