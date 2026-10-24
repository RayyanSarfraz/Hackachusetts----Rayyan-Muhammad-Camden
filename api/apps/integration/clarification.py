"""
Clarification engine: missing-information questions.

This module identifies clinically relevant missing information and generates
focused clarification questions from criterion assessments.

CRITICAL: Questions are derived from source criteria, not invented.
If no safe question is available, the missing requirement remains unresolved.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import hashlib

from .contracts import (
    AnswerType,
    ClarificationQuestion,
    CriterionAssessment,
    CriterionStatus,
    PatientPreferences,
    PatientProfile,
    TrialCandidate,
)


def generate_question_id(fact_key: str, criterion_ids: list[str]) -> str:
    """
    Generate a stable question ID from fact key and criterion IDs.
    
    Uses hash to create deterministic ID from inputs.
    """
    combined = f"{fact_key}:{':'.join(sorted(criterion_ids))}"
    hash_val = hashlib.md5(combined.encode()).hexdigest()[:8]
    return f"q_{hash_val}"


def infer_answer_type(required_fact: str, criterion_text: str) -> AnswerType:
    """
    Infer appropriate answer type from the required fact and criterion.
    
    Simple heuristics:
        - Medical history questions -> yes/no/unknown
        - Count/number questions -> number
        - Specific value questions -> text
    
    For hackathon, default to yes/no/unknown for most medical questions.
    """
    text_lower = (required_fact + " " + criterion_text).lower()
    
    # Count-related questions
    count_indicators = ["how many", "number of", "count"]
    if any(ind in text_lower for ind in count_indicators):
        return AnswerType.NUMBER
    
    # Time/date questions
    time_indicators = ["when", "date", "how long", "duration"]
    if any(ind in text_lower for ind in time_indicators):
        return AnswerType.TEXT
    
    # Default for medical eligibility: yes/no/unknown
    return AnswerType.YES_NO_UNKNOWN


def formulate_question(
    criterion: CriterionAssessment,
    trial_ids: list[str],
) -> Optional[ClarificationQuestion]:
    """
    Formulate a clarification question from an unknown criterion.
    
    Args:
        criterion: Criterion with UNKNOWN status
        trial_ids: IDs of trials this criterion affects
    
    Returns:
        ClarificationQuestion or None if cannot formulate safely
    """
    if criterion.status != CriterionStatus.UNKNOWN:
        return None
    
    if not criterion.question:
        # If no question provided, use criterion text
        # This preserves the original requirement rather than inventing
        display_question = (
            f"Eligibility requirement: {criterion.criterion_text[:200]}..."
            if len(criterion.criterion_text) > 200
            else f"Eligibility requirement: {criterion.criterion_text}"
        )
    else:
        display_question = criterion.question
    
    # Ensure question is patient-friendly
    # For hackathon, we accept clinical language but flag it
    question_id = generate_question_id(
        criterion.required_fact,
        [criterion.criterion_id],
    )
    
    answer_type = infer_answer_type(
        criterion.required_fact,
        criterion.criterion_text,
    )
    
    return ClarificationQuestion(
        question_id=question_id,
        required_fact_key=criterion.required_fact,
        display_question=display_question,
        answer_type=answer_type,
        related_trial_ids=trial_ids,
        source_criterion_ids=[criterion.criterion_id],
        reason=f"Required to assess eligibility for trial(s): {', '.join(trial_ids)}",
    )


def deduplicate_questions(
    questions: list[ClarificationQuestion],
) -> list[ClarificationQuestion]:
    """
    Deduplicate questions about the same missing fact.
    
    When multiple trials have the same unknown requirement, merge into one question.
    
    Args:
        questions: Raw questions from criteria
    
    Returns:
        Deduplicated questions, merging related trial IDs
    """
    # Group by required_fact_key
    by_fact: dict[str, ClarificationQuestion] = {}
    
    for q in questions:
        fact_key = q.required_fact_key
        
        if fact_key in by_fact:
            # Merge: combine trial IDs and criterion IDs
            existing = by_fact[fact_key]
            existing.related_trial_ids = list(set(
                existing.related_trial_ids + q.related_trial_ids
            ))
            existing.source_criterion_ids = list(set(
                existing.source_criterion_ids + q.source_criterion_ids
            ))
            # Update reason to reflect multiple trials
            if len(existing.related_trial_ids) > 1:
                existing.reason = (
                    f"Required to assess eligibility for {len(existing.related_trial_ids)} trial(s)"
                )
        else:
            by_fact[fact_key] = ClarificationQuestion(
                question_id=generate_question_id(fact_key, q.source_criterion_ids),
                required_fact_key=q.required_fact_key,
                display_question=q.display_question,
                answer_type=q.answer_type,
                related_trial_ids=list(q.related_trial_ids),
                source_criterion_ids=list(q.source_criterion_ids),
                reason=q.reason,
            )
    
    return list(by_fact.values())


def prioritize_questions(
    questions: list[ClarificationQuestion],
) -> list[ClarificationQuestion]:
    """
    Prioritize questions by impact.
    
    Higher priority:
        - Questions affecting more trials
        - Questions that might resolve eligibility
    
    Args:
        questions: Deduplicated questions
    
    Returns:
        Questions sorted by priority (highest first)
    """
    def priority_score(q: ClarificationQuestion) -> int:
        """Higher score = higher priority."""
        score = 0
        
        # More trials affected = higher priority
        score += len(q.related_trial_ids) * 10
        
        # Questions with clear yes/no answers preferred
        if q.answer_type in (AnswerType.YES_NO, AnswerType.YES_NO_UNKNOWN):
            score += 5
        
        return score
    
    return sorted(questions, key=priority_score, reverse=True)


def extract_questions_from_trials(
    trials: list[TrialCandidate],
) -> list[ClarificationQuestion]:
    """
    Extract clarification questions from trial assessments.
    
    Args:
        trials: Assessed trial candidates
    
    Returns:
        Prioritized, deduplicated questions
    """
    raw_questions: list[ClarificationQuestion] = []
    
    for trial in trials:
        trial_id = trial.nct_id
        
        for criterion in trial.criteria:
            if criterion.status == CriterionStatus.UNKNOWN:
                question = formulate_question(criterion, [trial_id])
                if question:
                    raw_questions.append(question)
    
    # Deduplicate by required fact
    deduped = deduplicate_questions(raw_questions)
    
    # Prioritize by impact
    return prioritize_questions(deduped)


def validate_answer(
    question: ClarificationQuestion,
    answer: Any,
) -> tuple[bool, Optional[str]]:
    """
    Validate an answer against the expected type.
    
    Args:
        question: The question being answered
        answer: The provided answer
    
    Returns:
        (is_valid, error_message)
    """
    if answer is None:
        return False, "Answer is required"
    
    if question.answer_type == AnswerType.YES_NO:
        if answer not in ("yes", "no"):
            return False, "Answer must be 'yes' or 'no'"
    
    elif question.answer_type == AnswerType.YES_NO_UNKNOWN:
        if answer not in ("yes", "no", "unknown"):
            return False, "Answer must be 'yes', 'no', or 'unknown'"
    
    elif question.answer_type == AnswerType.NUMBER:
        try:
            float(answer)
        except (TypeError, ValueError):
            return False, "Answer must be a number"
    
    elif question.answer_type == AnswerType.TEXT:
        if not isinstance(answer, str) or not answer.strip():
            return False, "Answer must be non-empty text"
    
    return True, None


def apply_answer_to_profile(
    profile: PatientProfile,
    question: ClarificationQuestion,
    answer: Any,
) -> PatientProfile:
    """
    Apply an answer to the patient profile.
    
    Creates a NEW profile with the answer incorporated.
    Does NOT mutate the original profile.
    
    Args:
        profile: Original patient profile
        question: Question being answered
        answer: Validated answer value
    
    Returns:
        Updated profile with the new fact
    """
    # Create a copy
    new_facts = dict(profile.medical_facts)
    
    # Normalize answer
    if question.answer_type == AnswerType.YES_NO_UNKNOWN:
        # For yes/no/unknown, store as boolean or None
        if answer == "yes":
            new_facts[question.required_fact_key] = True
        elif answer == "no":
            new_facts[question.required_fact_key] = False
        else:
            new_facts[question.required_fact_key] = None
    else:
        new_facts[question.required_fact_key] = answer
    
    # Remove from unknowns if present
    new_unknowns = [
        u for u in profile.unknowns
        if u != question.required_fact_key
    ]
    
    return PatientProfile(
        age=profile.age,
        conditions=list(profile.conditions),
        medications=list(profile.medications),
        medical_facts=new_facts,
        location=profile.location,
        location_coords=profile.location_coords,
        preferences=PatientPreferences(
            max_travel_miles=profile.preferences.max_travel_miles,
            avoid_overnight_stays=profile.preferences.avoid_overnight_stays,
            max_visits=profile.preferences.max_visits,
        ),
        unknowns=new_unknowns,
    )


def find_affected_criteria(
    trials: list[TrialCandidate],
    question: ClarificationQuestion,
) -> list[tuple[str, str]]:
    """
    Find criteria that would be affected by answering this question.
    
    Args:
        trials: Current trial assessments
        question: The question being answered
    
    Returns:
        List of (trial_id, criterion_id) tuples for affected criteria
    """
    affected = []
    
    for trial in trials:
        if trial.nct_id in question.related_trial_ids:
            for criterion in trial.criteria:
                if criterion.criterion_id in question.source_criterion_ids:
                    affected.append((trial.nct_id, criterion.criterion_id))
    
    return affected
