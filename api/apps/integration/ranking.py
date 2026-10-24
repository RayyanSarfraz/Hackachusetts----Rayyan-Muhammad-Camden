"""
Deterministic practical matching and ranking.

This module contains pure functions for:
- Geographic distance calculation
- Practical constraint evaluation
- Trial ranking (clinical + practical)
- Re-ranking when only preferences change (no LLM calls)

All functions are testable without external dependencies.
"""

import math
from typing import Optional

from .contracts import (
    CriterionStatus,
    PatientPreferences,
    PatientProfile,
    PracticalCompatibility,
    TrialCandidate,
    TrialLocation,
)


def haversine_distance(
    coord1: tuple[float, float],
    coord2: tuple[float, float],
) -> float:
    """
    Calculate geographic distance in miles using haversine formula.
    
    Args:
        coord1: (latitude, longitude) of first point
        coord2: (latitude, longitude) of second point
    
    Returns:
        Distance in miles
    
    Note:
        This is straight-line distance, NOT driving distance.
        Labels as "geographic" in display to avoid confusion.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Earth radius in miles
    R = 3959.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def find_nearest_location(
    patient_coords: Optional[tuple[float, float]],
    locations: list[TrialLocation],
) -> tuple[Optional[TrialLocation], Optional[float]]:
    """
    Find the nearest trial location to the patient.
    
    Args:
        patient_coords: Patient (lat, lng) or None if unknown
        locations: List of trial locations
    
    Returns:
        (nearest_location, distance_miles) or (None, None) if cannot determine
    """
    if patient_coords is None:
        return None, None
    
    nearest: Optional[TrialLocation] = None
    nearest_distance: Optional[float] = None
    
    for location in locations:
        if location.coords is None:
            continue
        
        distance = haversine_distance(patient_coords, location.coords)
        
        if nearest_distance is None or distance < nearest_distance:
            nearest = location
            nearest_distance = distance
    
    return nearest, nearest_distance


def evaluate_travel_constraint(
    max_travel_miles: Optional[float],
    nearest_distance_miles: Optional[float],
) -> tuple[PracticalCompatibility, str]:
    """
    Evaluate whether the nearest trial location is within travel preference.
    
    Returns:
        (compatibility_status, reason_message)
    """
    if max_travel_miles is None:
        return PracticalCompatibility.UNKNOWN, "Travel preference not specified"
    
    if nearest_distance_miles is None:
        return PracticalCompatibility.UNKNOWN, "Trial location distance unknown"
    
    if nearest_distance_miles <= max_travel_miles:
        return (
            PracticalCompatibility.COMPATIBLE,
            f"Within {max_travel_miles} mile travel limit ({nearest_distance_miles:.0f} miles to nearest site)",
        )
    else:
        return (
            PracticalCompatibility.INCOMPATIBLE,
            f"Exceeds {max_travel_miles} mile travel limit ({nearest_distance_miles:.0f} miles to nearest site)",
        )


def evaluate_overnight_constraint(
    avoid_overnight: Optional[bool],
    nearest_distance_miles: Optional[float],
    threshold_miles: float = 100.0,
) -> tuple[PracticalCompatibility, str]:
    """
    Evaluate overnight stay compatibility.
    
    Uses simple distance heuristic: beyond threshold, overnight likely needed.
    
    Note: If actual overnight requirements are in trial data, that takes
    precedence. This is a fallback for when that data is unavailable.
    """
    if avoid_overnight is None or not avoid_overnight:
        return PracticalCompatibility.COMPATIBLE, "No overnight preference specified or acceptable"
    
    if nearest_distance_miles is None:
        return PracticalCompatibility.UNKNOWN, "Distance unknown; cannot assess overnight requirement"
    
    if nearest_distance_miles > threshold_miles:
        return (
            PracticalCompatibility.INCOMPATIBLE,
            f"Trial {nearest_distance_miles:.0f} miles away; likely requires overnight stay",
        )
    
    return (
        PracticalCompatibility.COMPATIBLE,
        f"Within day-trip range ({nearest_distance_miles:.0f} miles)",
    )


def evaluate_practical_fit(
    trial: TrialCandidate,
    preferences: PatientPreferences,
) -> tuple[PracticalCompatibility, list[str]]:
    """
    Evaluate all practical constraints for a trial.
    
    Args:
        trial: Trial candidate with location info
        preferences: User's practical preferences
    
    Returns:
        (overall_compatibility, list_of_reasons)
    
    Rules:
        - If ANY constraint is INCOMPATIBLE, overall is INCOMPATIBLE
        - If any constraint is UNKNOWN and none are INCOMPATIBLE, overall is UNKNOWN
        - Otherwise COMPATIBLE
    """
    reasons: list[str] = []
    
    # Find nearest location
    nearest, nearest_distance = find_nearest_location(
        None,  # Will use trial's computed distance if available
        trial.locations,
    )
    
    # Use trial's precomputed distance if available, otherwise calculate
    distance_to_use = trial.nearest_distance_miles or nearest_distance
    
    # Evaluate travel
    travel_status, travel_reason = evaluate_travel_constraint(
        preferences.max_travel_miles,
        distance_to_use,
    )
    reasons.append(travel_reason)
    
    # Evaluate overnight
    overnight_status, overnight_reason = evaluate_overnight_constraint(
        preferences.avoid_overnight_stays,
        distance_to_use,
    )
    reasons.append(overnight_reason)
    
    # Aggregate: INCOMPATIBLE takes precedence
    all_statuses = [travel_status, overnight_status]
    
    if PracticalCompatibility.INCOMPATIBLE in all_statuses:
        return PracticalCompatibility.INCOMPATIBLE, reasons
    
    if PracticalCompatibility.UNKNOWN in all_statuses:
        return PracticalCompatibility.UNKNOWN, reasons
    
    return PracticalCompatibility.COMPATIBLE, reasons


def derive_clinical_status(trial: TrialCandidate) -> str:
    """
    Derive overall clinical status from criterion assessments.
    
    Rules:
        - If any criterion has CONFLICT status: "conflict"
        - If any criterion has UNKNOWN status (and no conflicts): "needs_clarification"
        - Otherwise: "potentially_eligible"
    
    Note: This is preliminary assessment, NOT a definitive eligibility determination.
    """
    has_conflict = False
    has_unknown = False
    
    for criterion in trial.criteria:
        if criterion.status == CriterionStatus.CONFLICT:
            has_conflict = True
        elif criterion.status == CriterionStatus.UNKNOWN:
            has_unknown = True
    
    if has_conflict:
        return "conflict"
    
    if has_unknown:
        return "needs_clarification"
    
    return "potentially_eligible"


def rank_trials(
    trials: list[TrialCandidate],
    preferences: PatientPreferences,
) -> list[TrialCandidate]:
    """
    Rank trials by clinical status and practical fit.
    
    This is a PURE FUNCTION - no side effects, no external calls.
    
    Ranking priority (highest to lowest):
        1. Potentially eligible + practically compatible
        2. Potentially eligible + unknown practical fit
        3. Needs clarification (clinical unknowns)
        4. Clinical conflict (even if practically convenient)
    
    Clinical conflicts are NEVER hidden by strong practical convenience.
    
    Args:
        trials: List of assessed trial candidates
        preferences: User's practical preferences
    
    Returns:
        Same trials with clinical_status, practical_fit, and nearest_distance populated
    """
    # Evaluate each trial
    for trial in trials:
        # Derive clinical status
        trial.clinical_status = derive_clinical_status(trial)
        
        # Evaluate practical fit
        trial.practical_fit, trial.practical_reasons = evaluate_practical_fit(
            trial, preferences
        )
        
        # Compute nearest distance if not already set
        if trial.nearest_distance_miles is None and trial.locations:
            _, distance = find_nearest_location(None, trial.locations)
            trial.nearest_distance_miles = distance
    
    # Sort by ranking priority
    # Lower score = higher priority
    def ranking_score(trial: TrialCandidate) -> tuple[int, int, float]:
        """
        Compute ranking score for sorting.
        
        Returns:
            (clinical_priority, practical_priority, distance)
        
            clinical_priority:
                0 = potentially_eligible
                1 = needs_clarification
                2 = conflict
            
            practical_priority:
                0 = compatible
                1 = unknown
                2 = incompatible
            
            distance: lower is better (use max distance as fallback for unknowns)
        """
        # Clinical priority
        clinical_priority = {
            "potentially_eligible": 0,
            "needs_clarification": 1,
            "conflict": 2,
        }.get(trial.clinical_status or "needs_clarification", 1)
        
        # Practical priority
        practical_priority = {
            PracticalCompatibility.COMPATIBLE: 0,
            PracticalCompatibility.UNKNOWN: 1,
            PracticalCompatibility.INCOMPATIBLE: 2,
        }.get(trial.practical_fit, 1)
        
        # Distance (max distance as fallback for unknowns, so they sort after known)
        distance = trial.nearest_distance_miles or float("inf")
        
        return (clinical_priority, practical_priority, distance)
    
    return sorted(trials, key=ranking_score)


def rerank_trials(
    trials: list[TrialCandidate],
    preferences: PatientPreferences,
) -> list[TrialCandidate]:
    """
    Re-rank trials when only preferences have changed.
    
    This is the PREFERRED function when re-ranking due to preference changes:
    - No clinical reassessment needed
    - No LLM calls
    - Pure deterministic calculation
    
    Args:
        trials: Previously assessed trials (criteria already evaluated)
        preferences: Updated practical preferences
    
    Returns:
        Re-ranked trials with updated practical_fit
    """
    # Simply delegate to rank_trials - it's already pure
    return rank_trials(trials, preferences)
