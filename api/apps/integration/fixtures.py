"""
Synthetic demo fixtures for Hackachusetts demonstration.

All patient data is FICTIONAL and clearly labeled.
Trial data references real NCT IDs but uses synthesized criteria for demo.
"""

from .contracts import (
    AnswerType,
    ClarificationQuestion,
    CriterionAssessment,
    CriterionStatus,
    PatientPreferences,
    PatientProfile,
    PracticalCompatibility,
    TrialCandidate,
    TrialLocation,
)


# =============================================================================
# SYNTHETIC PATIENT PROFILE
# =============================================================================

SYNTHETIC_PATIENT = PatientProfile(
    age=54,
    conditions=["Type 2 Diabetes Mellitus", "Hypertension"],
    medications=["Metformin 1000mg twice daily", "Lisinopril 10mg daily"],
    medical_facts={
        "diabetes_type_2": True,
        "hypertension": True,
        "metformin_use": True,
        "hba1c_percent": 7.8,
        "egfr_ml_min": 72,  # Kidney function
        "bmi": 31.2,
    },
    location="Boston, MA",
    location_coords=(42.3601, -71.0589),
    preferences=PatientPreferences(
        max_travel_miles=50.0,
        avoid_overnight_stays=True,
        max_visits=12,
    ),
    unknowns=[
        "insulin_use",  # Has patient ever used insulin?
        "cardiovascular_event_history",  # Any prior heart attack/stroke?
    ],
)

# =============================================================================
# SYNTHETIC TRIAL CANDIDATES
# =============================================================================

# Trial A: Potentially eligible, practically compatible
# Real NCT for diabetes trial (simplified for demo)
TRIAL_MATCH = TrialCandidate(
    nct_id="NCT05615089",  # Real NCT ID for a diabetes study
    title="A Study of Tirzepatide in Participants With Type 2 Diabetes",
    source_url="https://clinicaltrials.gov/study/NCT05615089",
    recruitment_status="Recruiting",
    locations=[
        TrialLocation(
            name="Massachusetts General Hospital",
            city="Boston",
            state="MA",
            country="USA",
            coords=(42.3626, -71.0689),
        ),
        TrialLocation(
            name="Brigham and Women's Hospital",
            city="Boston",
            state="MA",
            country="USA",
            coords=(42.3359, -71.1057),
        ),
    ],
    criteria=[
        CriterionAssessment(
            criterion_id="NCT05615089-inc-001",
            criterion_text="Age 18 years or older",
            criterion_source="https://clinicaltrials.gov/study/NCT05615089",
            required_fact="age",
            status=CriterionStatus.MET,
            evidence="Patient age is 54 years",
        ),
        CriterionAssessment(
            criterion_id="NCT05615089-inc-002",
            criterion_text="Diagnosis of Type 2 Diabetes Mellitus",
            criterion_source="https://clinicaltrials.gov/study/NCT05615089",
            required_fact="diabetes_type_2",
            status=CriterionStatus.MET,
            evidence="Patient has Type 2 Diabetes diagnosis",
        ),
        CriterionAssessment(
            criterion_id="NCT05615089-inc-003",
            criterion_text="HbA1c between 7.0% and 10.0%",
            criterion_source="https://clinicaltrials.gov/study/NCT05615089",
            required_fact="hba1c_percent",
            status=CriterionStatus.MET,
            evidence="Patient HbA1c is 7.8%",
        ),
        CriterionAssessment(
            criterion_id="NCT05615089-exc-001",
            criterion_text="History of severe hypoglycemia in the past 6 months",
            criterion_source="https://clinicaltrials.gov/study/NCT05615089",
            required_fact="severe_hypoglycemia_history",
            status=CriterionStatus.MET,
            evidence="Patient record documents no severe hypoglycemia episodes in the past 6 months",
        ),
    ],
    clinical_status=None,  # Will be derived
    practical_fit=None,  # Will be derived
    nearest_distance_miles=None,  # Will be computed
)

# Trial B: Clinical conflict (exclusion applies)
TRIAL_CONFLICT = TrialCandidate(
    nct_id="NCT04792886",  # Real NCT ID for a diabetes/cardiovascular study
    title="Effect of Dapagliflozin on Cardiorenal Outcomes in Type 2 Diabetes",
    source_url="https://clinicaltrials.gov/study/NCT04792886",
    recruitment_status="Recruiting",
    locations=[
        TrialLocation(
            name="Brigham and Women's Hospital",
            city="Boston",
            state="MA",
            country="USA",
            coords=(42.3359, -71.1057),
        ),
    ],
    criteria=[
        CriterionAssessment(
            criterion_id="NCT04792886-inc-001",
            criterion_text="Age 40 years or older with Type 2 Diabetes",
            criterion_source="https://clinicaltrials.gov/study/NCT04792886",
            required_fact="age",
            status=CriterionStatus.MET,
            evidence="Patient age is 54 years with Type 2 Diabetes",
        ),
        CriterionAssessment(
            criterion_id="NCT04792886-exc-001",
            criterion_text="eGFR less than 60 mL/min/1.73m²",
            criterion_source="https://clinicaltrials.gov/study/NCT04792886",
            required_fact="egfr_ml_min",
            status=CriterionStatus.CONFLICT,
            evidence="Patient eGFR is 72 mL/min, above exclusion threshold of 60",
        ),
        CriterionAssessment(
            criterion_id="NCT04792886-exc-002",
            criterion_text="Current use of SGLT2 inhibitor within 30 days",
            criterion_source="https://clinicaltrials.gov/study/NCT04792886",
            required_fact="sglt2_inhibitor_use",
            status=CriterionStatus.UNKNOWN,
            question="Are you currently taking an SGLT2 inhibitor medication (such as empagliflozin, canagliflozin, or dapagliflozin)?",
        ),
    ],
    clinical_status=None,
    practical_fit=None,
    nearest_distance_miles=None,
)

# Trial C: Missing important eligibility fact
TRIAL_UNKNOWN = TrialCandidate(
    nct_id="NCT05763157",  # Real NCT ID for diabetes/insulin study
    title="Study Comparing Once-Weekly Insulin Icodec to Daily Insulin Glargine",
    source_url="https://clinicaltrials.gov/study/NCT05763157",
    recruitment_status="Recruiting",
    locations=[
        TrialLocation(
            name="Yale School of Medicine",
            city="New Haven",
            state="CT",
            country="USA",
            coords=(41.3033, -72.9318),
        ),
        TrialLocation(
            name="Columbia University Medical Center",
            city="New York",
            state="NY",
            country="USA",
            coords=(40.8406, -73.9417),
        ),
    ],
    criteria=[
        CriterionAssessment(
            criterion_id="NCT05763157-inc-001",
            criterion_text="Age 18 years or older",
            criterion_source="https://clinicaltrials.gov/study/NCT05763157",
            required_fact="age",
            status=CriterionStatus.MET,
            evidence="Patient age is 54 years",
        ),
        CriterionAssessment(
            criterion_id="NCT05763157-inc-002",
            criterion_text="Type 2 Diabetes treated with insulin or eligible for insulin therapy",
            criterion_source="https://clinicaltrials.gov/study/NCT05763157",
            required_fact="insulin_use",
            status=CriterionStatus.UNKNOWN,
            question="Have you ever used insulin to manage your diabetes?",
        ),
        CriterionAssessment(
            criterion_id="NCT05763157-inc-003",
            criterion_text="HbA1c between 7.0% and 11.0%",
            criterion_source="https://clinicaltrials.gov/study/NCT05763157",
            required_fact="hba1c_percent",
            status=CriterionStatus.MET,
            evidence="Patient HbA1c is 7.8%",
        ),
        CriterionAssessment(
            criterion_id="NCT05763157-exc-001",
            criterion_text="History of cardiovascular event (myocardial infarction, stroke) within 90 days",
            criterion_source="https://clinicaltrials.gov/study/NCT05763157",
            required_fact="cardiovascular_event_history",
            status=CriterionStatus.UNKNOWN,
            question="Have you had a heart attack or stroke within the past 3 months?",
        ),
    ],
    clinical_status=None,
    practical_fit=None,
    nearest_distance_miles=None,
)


def get_synthetic_trials() -> list[TrialCandidate]:
    """Get synthetic trial fixtures for demonstration."""
    return [TRIAL_MATCH, TRIAL_CONFLICT, TRIAL_UNKNOWN]


def get_synthetic_patient() -> PatientProfile:
    """Get synthetic patient profile for demonstration."""
    return SYNTHETIC_PATIENT


# =============================================================================
# EXAMPLE DEMONSTRATION SCENARIOS
# =============================================================================

SCENARIO_A_UNKNOWN_INFO = """
SCENARIO A: Missing Information
================================
Patient: 54-year-old with Type 2 Diabetes, HbA1c 7.8%
Trial: NCT05763157 (insulin study)

Missing facts:
- insulin_use: Has patient ever used insulin?
- cardiovascular_event_history: Any recent heart attack/stroke?

Result: Trial shows "needs_clarification" status.
System generates two targeted questions.
"""

SCENARIO_B_ANSWER = """
SCENARIO B: Answering the Question
===================================
Question: "Have you ever used insulin to manage your diabetes?"
Answer: "no"

Result:
- Patient profile updated: insulin_use = False
- Criterion NCT05763157-inc-002 reassessed -> MET
- Trial status updated
- Remaining unknown: cardiovascular_event_history
"""

SCENARIO_C_PREFERENCE_CHANGE = """
SCENARIO C: Preference Changes
===============================
Initial preference: max_travel_miles = 50
Trial NCT05763157 nearest site: New Haven, CT (~130 miles)
Result: Trial marked INCOMPATIBLE for travel

User changes preference: max_travel_miles = 150
Result:
- Re-ranking triggered (pure function, no LLM call)
- Trial now COMPATIBLE for travel
- Clinical status unchanged (still needs_clarification)
"""

SCENARIO_D_PRIVACY = """
SCENARIO D: Privacy
====================
Frontend display shows:
- Patient age: 54
- Conditions count: 2 (not specific conditions)
- Medications count: 2 (not specific medications)
- Location: Boston, MA (public)

NOT shown in public comparison:
- Full medication list
- HbA1c value
- eGFR value
- Specific medical facts
"""

SCENARIO_E_CONFLICT = """
SCENARIO E: Clinical Conflict
==============================
Trial: NCT04792886
Criterion: "eGFR less than 60 mL/min" (exclusion)
Patient eGFR: 72 mL/min

Result: CRITERION STATUS = CONFLICT (patient does NOT meet exclusion)
Overall clinical status: CONFLICT (for different reason - SGLT2 inhibitor use unknown)

Key point: Even though this trial is in Boston (practically convenient),
the clinical conflict is clearly displayed. Convenience does NOT hide conflicts.
"""
