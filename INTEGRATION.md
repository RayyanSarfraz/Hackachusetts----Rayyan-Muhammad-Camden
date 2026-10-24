# Integration Layer - Teammate Handoff

## What I Built

A complete integration module for trial comparison, ranking, and clarification questions.

### Files Created

```
api/apps/integration/
├── __init__.py          # Module init
├── apps.py              # Django app config
├── contracts.py         # Data structures (PatientProfile, TrialCandidate, etc.)
├── ranking.py           # Deterministic ranking logic
├── clarification.py     # Question extraction and answer handling
├── orchestrator.py      # Main workflow orchestration
├── fixtures.py          # Synthetic demo data
├── tests.py             # Comprehensive test suite
├── views.py             # REST API endpoints
├── urls.py              # URL routing
├── models.py            # Empty (no DB models needed)
├── serializers.py       # Empty (using dataclasses)
├── admin.py             # Empty
└── migrations/
    └── __init__.py
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/integration/compare/` | POST | Compare trials with patient profile |
| `/api/integration/answer/` | POST | Submit clarification answer |
| `/api/integration/preferences/` | POST | Update preferences only |
| `/api/integration/demo/` | GET | Run synthetic demo |

## For Muhammad (Patient Extraction)

### How to Feed Patient Data

POST to `/api/integration/compare/` with:

```json
{
  "patient": {
    "age": 54,
    "conditions": ["Type 2 Diabetes Mellitus"],
    "medications": ["Metformin 1000mg twice daily"],
    "medical_facts": {
      "hba1c_percent": 7.8,
      "egfr_ml_min": 72,
      "bmi": 31.2
    },
    "location": "Boston, MA",
    "location_coords": [42.3601, -71.0589],
    "preferences": {
      "max_travel_miles": 50.0,
      "avoid_overnight_stays": true,
      "max_visits": 12
    },
    "unknowns": ["insulin_use", "cardiovascular_event_history"]
  }
}
```

### Contract Details

See `api/apps/integration/contracts.py` for full dataclass definitions.

Key points:
- `medical_facts` is a flat dict of clinical attributes
- `unknowns` lists missing clinical facts that need clarification
- `location_coords` is optional but enables distance calculation
- All fields preserve uncertainty - never fabricate missing data

## For Clinical Assessment Developer

### How to Feed Criterion Assessments

Include in the `trials` array:

```json
{
  "trials": [{
    "nct_id": "NCT05615089",
    "title": "A Study of Tirzepatide...",
    "source_url": "https://clinicaltrials.gov/study/NCT05615089",
    "recruitment_status": "Recruiting",
    "locations": [{
      "name": "Massachusetts General Hospital",
      "city": "Boston",
      "state": "MA",
      "country": "USA",
      "coords": [42.3626, -71.0689]
    }],
    "criteria": [{
      "criterion_id": "NCT05615089-inc-001",
      "criterion_text": "Age 18 years or older",
      "criterion_source": "https://clinicaltrials.gov/study/NCT05615089",
      "required_fact": "age",
      "status": "met",
      "evidence": "Patient age is 54 years"
    }, {
      "criterion_id": "NCT05615089-exc-001",
      "criterion_text": "History of severe hypoglycemia",
      "criterion_source": "https://clinicaltrials.gov/study/NCT05615089",
      "required_fact": "severe_hypoglycemia_history",
      "status": "unknown",
      "question": "Have you experienced severe low blood sugar episodes?"
    }]
  }]
}
```

### Criterion Status Values

- `met`: Patient satisfies the criterion
- `conflict`: Patient does NOT satisfy (for inclusion) or DOES satisfy (for exclusion)
- `unknown`: Cannot determine from available information

### What Happens with Unknowns

1. Integration layer extracts questions from `unknown` criteria
2. Questions are deduplicated by `required_fact`
3. Frontend displays questions to user
4. User answers via `/api/integration/answer/`
5. Integration returns affected criteria IDs
6. **Clinical module must reevaluate affected criteria** (not automatic)

## For Frontend Developer

### Demo Endpoint

GET `/api/integration/demo/` returns a complete example response with 3 trials.

### Full Comparison Response

```json
{
  "patient_summary": {
    "age": 54,
    "condition_count": 2,
    "medication_count": 2,
    "location": "Boston, MA",
    "preferences": {
      "max_travel_miles": 50.0,
      "avoid_overnight_stays": true,
      "max_visits": 12
    }
  },
  "results": [
    {
      "nct_id": "NCT05615089",
      "title": "A Study of Tirzepatide...",
      "source_url": "https://clinicaltrials.gov/study/NCT05615089",
      "rank": 1,
      "clinical_status": "potentially_eligible",
      "practical_fit": "compatible",
      "practical_reasons": ["Within 50 mile travel limit (1 miles)"],
      "has_conflicts": false,
      "has_unknowns": true,
      "clarification_needed": true,
      "nearest_distance_miles": 1.2
    }
  ],
  "questions": [
    {
      "question_id": "q_abc123",
      "required_fact_key": "insulin_use",
      "display_question": "Have you ever used insulin?",
      "answer_type": "yes_no_unknown",
      "related_trial_ids": ["NCT05763157"],
      "reason": "Required to assess eligibility"
    }
  ],
  "missing_data_notes": [],
  "limitations": [
    "This is a preliminary assessment, not a definitive eligibility determination.",
    "All clinical criteria require verification by the study team."
  ]
}
```

### Preference-Only Update

POST to `/api/integration/preferences/`:

```json
{
  "max_travel_miles": 150.0,
  "avoid_overnight_stays": false
}
```

Returns re-ranked results with **no clinical reassessment** (pure function, instant).

### Answer Endpoint

POST to `/api/integration/answer/`:

```json
{
  "question_id": "q_abc123",
  "answer": "no"
}
```

Returns updated profile and affected criteria IDs. Clinical reassessment is separate.

## Running Tests

```bash
# Via Docker
docker compose run api python manage.py test apps.integration

# Or locally with Django installed
cd api && python manage.py test apps.integration
```

Test coverage:
- Geographic distance calculation
- Practical constraint evaluation
- Ranking with conflict preservation
- Clarification question extraction
- Answer validation
- Profile updates (no auto-resolution)
- Privacy boundary
- Deterministic behavior
- Empty/edge cases

## Key Design Decisions

1. **Pure functions**: Ranking and clarification have no external dependencies
2. **Three-valued uncertainty**: Unknown ≠ Ineligible
3. **Clinical priority**: Conflicts are never hidden by convenience
4. **Privacy-first**: Sanitized responses, no raw medical notes
5. **No auto-resolution**: Answering a question doesn't automatically resolve criteria

## What's Still Missing

- Database persistence (currently in-memory for demo)
- Session management for multi-step workflows
- Clinical assessment module integration
- Patient extraction module integration
- Frontend UI

## Demo Scenarios

The synthetic fixtures include 3 trials:

1. **NCT05615089**: Potentially eligible, practical match (Boston)
2. **NCT04792886**: Has exclusion conflict
3. **NCT05763157**: Missing insulin_use and cardiovascular history

Run `GET /api/integration/demo/` to see the full workflow.
