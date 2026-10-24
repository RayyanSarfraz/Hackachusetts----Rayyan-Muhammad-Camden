---
inclusion: always
---

# Integration Layer

Part of the [unified team agent memory](team-agent-memory.md). Documents the trial comparison, ranking, and clarification engine.

## Overview

The integration layer connects patient profiles, trial assessments, and preferences into a unified recommendation workflow. It is owned by the integration developer (Camden) and must not be modified by other teammates without coordination.

## Data Contracts

All contracts are defined in `api/apps/integration/contracts.py` using Python dataclasses.

### PatientProfile

```python
@dataclass
class PatientProfile:
    age: Optional[int]
    conditions: list[str]
    medications: list[str]
    medical_facts: dict[str, Any]  # Structured clinical facts
    location: Optional[str]
    location_coords: Optional[tuple[float, float]]  # (lat, lng)
    preferences: PatientPreferences
    unknowns: list[str]  # Missing clinical attributes
```

### TrialCandidate

```python
@dataclass
class TrialCandidate:
    nct_id: str
    title: str
    source_url: str
    recruitment_status: Optional[str]
    locations: list[TrialLocation]
    criteria: list[CriterionAssessment]
    clinical_status: Optional[str]  # Derived
    practical_fit: Optional[PracticalCompatibility]  # Derived
    nearest_distance_miles: Optional[float]  # Derived
    unknowns: list[str]
```

### CriterionAssessment

```python
@dataclass
class CriterionAssessment:
    criterion_id: str
    criterion_text: str
    criterion_source: str
    required_fact: str
    status: CriterionStatus  # met | conflict | unknown
    evidence: Optional[str]
    question: Optional[str]
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/integration/compare/` | POST | Compare trials with patient profile |
| `/api/integration/answer/` | POST | Submit clarification answer |
| `/api/integration/preferences/` | POST | Update preferences only (no clinical reassessment) |
| `/api/integration/demo/` | GET | Run synthetic demo |

## Integration Points

### For Muhammad (Patient Extraction)

Feed extracted patient JSON to `/api/integration/compare/`:

```json
{
  "patient": {
    "age": 54,
    "conditions": ["Type 2 Diabetes"],
    "medications": ["Metformin"],
    "medical_facts": {"hba1c_percent": 7.8},
    "location": "Boston, MA",
    "location_coords": [42.3601, -71.0589],
    "preferences": {
      "max_travel_miles": 50,
      "avoid_overnight_stays": true
    }
  }
}
```

### For Clinical Assessment Developer

Feed criterion assessments in trial data:

```json
{
  "trials": [{
    "nct_id": "NCT05615089",
    "title": "Trial Title",
    "source_url": "https://clinicaltrials.gov/study/NCT05615089",
    "criteria": [{
      "criterion_id": "inc-001",
      "criterion_text": "Age >= 18",
      "criterion_source": "https://...",
      "required_fact": "age",
      "status": "met",
      "evidence": "Patient age is 54"
    }]
  }]
}
```

### For Frontend Developer

Consume `/api/integration/compare/` response:

```json
{
  "patient_summary": {
    "age": 54,
    "condition_count": 2,
    "medication_count": 2,
    "location": "Boston, MA"
  },
  "results": [{
    "nct_id": "NCT05615089",
    "title": "Trial Title",
    "rank": 1,
    "clinical_status": "potentially_eligible",
    "practical_fit": "compatible",
    "has_conflicts": false,
    "has_unknowns": true,
    "clarification_needed": true
  }],
  "questions": [{
    "question_id": "q_abc123",
    "display_question": "Have you used insulin?",
    "answer_type": "yes_no_unknown"
  }]
}
```

## Privacy Boundary

- Patient profiles are treated as sensitive
- `to_sanitized_dict()` returns minimal display-safe data
- No real patient data in fixtures or examples
- No logging of raw medical notes
- No patient identifiers in response JSON

## Deterministic Ranking

The ranking algorithm is pure and deterministic:

1. Clinical status takes priority over convenience
2. Potentially eligible > Needs clarification > Conflict
3. Practical compatibility: Compatible > Unknown > Incompatible
4. Re-ranking for preference changes uses no LLM calls

## Three-Valued Uncertainty

Criterion status is ALWAYS one of:
- `met`: Patient satisfies the criterion
- `conflict`: Patient does NOT satisfy the criterion
- `unknown`: Cannot determine from available information

Unknown does NOT mean ineligible. It means more information is needed.

## Testing

Run tests with:

```bash
docker compose run api python manage.py test apps.integration
```

Or locally with Django installed:

```bash
cd api && python manage.py test apps.integration
```
