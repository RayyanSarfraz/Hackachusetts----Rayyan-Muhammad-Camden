"""
Integration contracts: data structures for trial comparison workflow.

These are the shared interfaces between:
- Patient extraction (Muhammad's component)
- Trial retrieval and clinical assessment (other teammate)
- Deterministic ranking and clarification (this module)
- Frontend display (frontend teammate)

All fields preserve uncertainty explicitly. Never fabricate missing data.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class CriterionStatus(str, Enum):
    """Three-valued eligibility status for a single criterion."""
    MET = "met"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"


class PracticalCompatibility(str, Enum):
    """Practical/logistical compatibility status."""
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


class AnswerType(str, Enum):
    """Supported question answer types."""
    YES_NO = "yes_no"
    YES_NO_UNKNOWN = "yes_no_unknown"
    TEXT = "text"
    NUMBER = "number"


@dataclass
class PatientPreferences:
    """
    User-specified practical constraints.
    
    These can change without triggering clinical reassessment.
    """
    max_travel_miles: Optional[float] = None
    avoid_overnight_stays: Optional[bool] = None
    max_visits: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "max_travel_miles": self.max_travel_miles,
            "avoid_overnight_stays": self.avoid_overnight_stays,
            "max_visits": self.max_visits,
        }


@dataclass
class PatientProfile:
    """
    Structured patient profile extracted from medical summary.
    
    CRITICAL: Unknown information must remain unknown.
    Never fabricate or infer missing medical facts.
    """
    age: Optional[int] = None
    conditions: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    medical_facts: dict[str, Any] = field(default_factory=dict)
    location: Optional[str] = None
    location_coords: Optional[tuple[float, float]] = None  # (lat, lng) if available
    preferences: PatientPreferences = field(default_factory=PatientPreferences)
    unknowns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "age": self.age,
            "conditions": self.conditions,
            "medications": self.medications,
            "medical_facts": self.medical_facts,
            "location": self.location,
            "location_coords": self.location_coords,
            "preferences": self.preferences.to_dict(),
            "unknowns": self.unknowns,
        }

    def to_sanitized_dict(self) -> dict:
        """
        Return profile for frontend display.
        
        Sanitize to minimal, non-sensitive representation.
        """
        return {
            "age": self.age,
            "condition_count": len(self.conditions),
            "medication_count": len(self.medications),
            "location": self.location,
            "preferences": self.preferences.to_dict(),
        }


@dataclass
class TrialLocation:
    """A study site with optional coordinates."""
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    coords: Optional[tuple[float, float]] = None  # (lat, lng)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "coords": self.coords,
        }


@dataclass
class CriterionAssessment:
    """
    Assessment of a single eligibility criterion against patient profile.
    
    CRITICAL: If evaluation cannot be reliably performed, status MUST be UNKNOWN.
    Never silently discard complex criteria.
    """
    criterion_id: str
    criterion_text: str
    criterion_source: str
    required_fact: str
    status: CriterionStatus
    evidence: Optional[str] = None
    question: Optional[str] = None
    # Only explicitly supplied boolean rules may be automatically reassessed.
    expected_value: Optional[bool] = None
    def to_dict(self) -> dict:
        return {
            "criterion_id": self.criterion_id,
            "criterion_text": self.criterion_text,
            "criterion_source": self.criterion_source,
            "required_fact": self.required_fact,
            "status": self.status.value,
            "evidence": self.evidence,
            "question": self.question,
            "expected_value": self.expected_value,
        }


@dataclass
class TrialCandidate:
    """
    A clinical trial candidate with assessed criteria.
    
    clinical_status is derived from criterion assessments.
    practical_fit is derived from preferences and logistics.
    These are computed separately and must never be conflated.
    """
    nct_id: str
    title: str
    source_url: str
    recruitment_status: Optional[str] = None
    locations: list[TrialLocation] = field(default_factory=list)
    criteria: list[CriterionAssessment] = field(default_factory=list)
    clinical_status: Optional[str] = None  # Derived: "potentially_eligible", "conflict", "needs_clarification"
    practical_fit: Optional[PracticalCompatibility] = None
    practical_reasons: list[str] = field(default_factory=list)
    nearest_distance_miles: Optional[float] = None
    unknowns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nct_id": self.nct_id,
            "title": self.title,
            "source_url": self.source_url,
            "recruitment_status": self.recruitment_status,
            "locations": [loc.to_dict() for loc in self.locations],
            "criteria": [c.to_dict() for c in self.criteria],
            "clinical_status": self.clinical_status,
            "practical_fit": self.practical_fit.value if self.practical_fit else None,
            "practical_reasons": self.practical_reasons,
            "nearest_distance_miles": self.nearest_distance_miles,
            "unknowns": self.unknowns,
        }


@dataclass
class ClarificationQuestion:
    """
    A targeted question about missing eligibility information.
    
    Questions are generated from criterion assessments with UNKNOWN status.
    Each question references the source criteria and affected trials.
    """
    question_id: str
    required_fact_key: str
    display_question: str
    answer_type: AnswerType
    related_trial_ids: list[str]
    source_criterion_ids: list[str]
    reason: str

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "required_fact_key": self.required_fact_key,
            "display_question": self.display_question,
            "answer_type": self.answer_type.value,
            "related_trial_ids": self.related_trial_ids,
            "source_criterion_ids": self.source_criterion_ids,
            "reason": self.reason,
        }


@dataclass
class ComparisonResult:
    """
    Single trial's comparison result for display.
    
    Combines clinical status, practical fit, and ranking info.
    """
    trial: TrialCandidate
    rank: int
    clinical_status: str
    practical_fit: Optional[PracticalCompatibility]
    practical_reasons: list[str]
    has_conflicts: bool
    has_unknowns: bool
    clarification_needed: bool

    def to_dict(self) -> dict:
        return {
            "nct_id": self.trial.nct_id,
            "title": self.trial.title,
            "source_url": self.trial.source_url,
            "rank": self.rank,
            "clinical_status": self.clinical_status,
            "practical_fit": self.practical_fit.value if self.practical_fit else None,
            "practical_reasons": self.practical_reasons,
            "has_conflicts": self.has_conflicts,
            "has_unknowns": self.has_unknowns,
            "clarification_needed": self.clarification_needed,
            "nearest_distance_miles": self.trial.nearest_distance_miles,
            "criteria": [c.to_dict() for c in self.trial.criteria],
            "locations": [loc.to_dict() for loc in self.trial.locations],
        }


@dataclass
class ComparisonResponse:
    """
    Complete comparison response for frontend consumption.
    
    This is the unified output of the integration layer.
    """
    patient_summary: dict
    results: list[ComparisonResult]
    questions: list[ClarificationQuestion]
    missing_data_notes: list[str]
    limitations: list[str]

    def to_dict(self) -> dict:
        return {
            "patient_summary": self.patient_summary,
            "results": [r.to_dict() for r in self.results],
            "questions": [q.to_dict() for q in self.questions],
            "missing_data_notes": self.missing_data_notes,
            "limitations": self.limitations,
        }
