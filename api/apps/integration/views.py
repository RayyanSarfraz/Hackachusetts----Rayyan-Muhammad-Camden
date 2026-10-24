"""
Integration API views.

Provides REST endpoints for:
- Trial comparison
- Clarification question handling
- Preference updates
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .contracts import PatientPreferences, PatientProfile, TrialCandidate
from .orchestrator import (
    apply_clarification_answer,
    combine_trials_and_patient,
    run_synthetic_demo,
    update_preferences_only,
    assess_explicit_boolean_rules,
)
from .fixtures import get_synthetic_trials, get_synthetic_patient
from .frontend_demo import DEMO_PATIENT_NOTES, get_demo_trials, parse_notes


class CompareTrialsView(APIView):
    """
    Main comparison endpoint.
    
    POST /api/integration/compare/
    
    Request body:
        {
            "patient": {...},  // PatientProfile dict
            "trials": [...]    // List of TrialCandidate dicts
        }
    
    Returns:
        ComparisonResponse with ranked trials and questions.
    
    If patient or trials are omitted, uses synthetic demo data.
    """
    
    permission_classes = []  # Public for demo
    
    def post(self, request):
        # Parse patient profile
        patient_data = request.data.get("patient")
        if patient_data:
            try:
                patient = self._parse_patient(patient_data)
            except (KeyError, ValueError) as e:
                return Response(
                    {"error": f"Invalid patient data: {e}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            patient = get_synthetic_patient()
        
        # Parse trials
        trials_data = request.data.get("trials")
        if trials_data:
            try:
                trials = [self._parse_trial(t) for t in trials_data]
            except (KeyError, ValueError) as e:
                return Response(
                    {"error": f"Invalid trial data: {e}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            trials = get_synthetic_trials()
        
        # Run comparison
        response = combine_trials_and_patient(trials, patient)
        
        return Response(response.to_dict())
    
    def _parse_patient(self, data: dict) -> PatientProfile:
        """Parse patient profile from request data."""
        prefs_data = data.get("preferences", {})
        preferences = PatientPreferences(
            max_travel_miles=prefs_data.get("max_travel_miles"),
            avoid_overnight_stays=prefs_data.get("avoid_overnight_stays"),
            max_visits=prefs_data.get("max_visits"),
        )
        
        return PatientProfile(
            age=data.get("age"),
            conditions=data.get("conditions", []),
            medications=data.get("medications", []),
            medical_facts=data.get("medical_facts", {}),
            location=data.get("location"),
            location_coords=tuple(data["location_coords"]) if data.get("location_coords") else None,
            preferences=preferences,
            unknowns=data.get("unknowns", []),
        )
    
    def _parse_trial(self, data: dict) -> TrialCandidate:
        """Parse trial candidate from request data."""
        from .contracts import CriterionAssessment, CriterionStatus, TrialLocation
        
        # Parse locations
        locations = []
        for loc_data in data.get("locations", []):
            locations.append(TrialLocation(
                name=loc_data.get("name", ""),
                city=loc_data.get("city"),
                state=loc_data.get("state"),
                country=loc_data.get("country"),
                coords=tuple(loc_data["coords"]) if loc_data.get("coords") else None,
            ))
        
        # Parse criteria
        criteria = []
        for crit_data in data.get("criteria", []):
            criteria.append(CriterionAssessment(
                criterion_id=crit_data["criterion_id"],
                criterion_text=crit_data["criterion_text"],
                criterion_source=crit_data["criterion_source"],
                required_fact=crit_data["required_fact"],
                status=CriterionStatus(crit_data["status"]),
                evidence=crit_data.get("evidence"),
                question=crit_data.get("question"),
                expected_value=crit_data.get("expected_value"),
            ))
        
        return TrialCandidate(
            nct_id=data["nct_id"],
            title=data["title"],
            source_url=data["source_url"],
            recruitment_status=data.get("recruitment_status"),
            locations=locations,
            criteria=criteria,
        )


def _get_workflow_inputs(request):
    """Stateless workflow: clients must resend the current patient and trials.

    This deliberately avoids using global demo data for patient-specific updates.
    """
    patient_data = request.data.get("patient")
    trials_data = request.data.get("trials")
    if not isinstance(patient_data, dict) or not isinstance(trials_data, list):
        raise ValueError("patient (object) and trials (array) are required")
    parser = CompareTrialsView()
    return parser._parse_patient(patient_data), [parser._parse_trial(t) for t in trials_data]


class AnswerQuestionView(APIView):
    """Answer a question using the exact patient/trials from the client.

    POST {"patient": {...}, "trials": [...], "question_id": "...", "answer": "no"}
    Returns updated *sanitized* profile, updated trials, comparison, and
    remaining criteria that need external clinical reassessment.
    """
    permission_classes = []  # Synthetic demo only; protect before real patient use

    def post(self, request):
        question_id = request.data.get("question_id")
        answer = request.data.get("answer")
        if not question_id or answer is None:
            return Response({"error": "question_id and answer are required"}, status=400)
        try:
            patient, trials = _get_workflow_inputs(request)
            updated_profile, affected, _ = apply_clarification_answer(
                trials, patient, question_id, answer
            )
            updated_trials = assess_explicit_boolean_rules(trials, updated_profile, affected)
            comparison = combine_trials_and_patient(updated_trials, updated_profile)
            remaining = [
                f"{t.nct_id}:{c.criterion_id}" for t in updated_trials
                for c in t.criteria
                if f"{t.nct_id}:{c.criterion_id}" in affected
                and c.status.value == "unknown"
            ]
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            return Response({"error": str(exc)}, status=400)
        return Response({
            "updated_profile": updated_profile.to_sanitized_dict(),
            "affected_criteria": affected,
            "requires_reassessment": remaining,
            "trials": [t.to_dict() for t in updated_trials],
            "comparison": comparison.to_dict(),
            "note": "Only explicit boolean rules are automatically reassessed; other criteria remain unknown.",
        })


class UpdatePreferencesView(APIView):
    """Stateless preference update: POST patient, trials, and preferences."""
    permission_classes = []  # Synthetic demo only

    def post(self, request):
        try:
            patient, trials = _get_workflow_inputs(request)
            prefs_data = request.data.get("preferences")
            if not isinstance(prefs_data, dict):
                raise ValueError("preferences object is required")
            current = patient.preferences
            preferences = PatientPreferences(
                max_travel_miles=prefs_data.get("max_travel_miles", current.max_travel_miles),
                avoid_overnight_stays=prefs_data.get("avoid_overnight_stays", current.avoid_overnight_stays),
                max_visits=prefs_data.get("max_visits", current.max_visits),
            )
            patient.preferences = preferences
            updated_trials = update_preferences_only(trials, preferences, patient.location_coords)
            comparison = combine_trials_and_patient(updated_trials, patient)
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            return Response({"error": str(exc)}, status=400)
        return Response({
            **comparison.to_dict(),
            "trials": [t.to_dict() for t in updated_trials],
        })


class DemoComparisonView(APIView):
    """
    Run the full synthetic demo.
    
    GET /api/integration/demo/
    
    Returns a complete comparison using fictional patient data.
    Useful for testing and demonstration.
    """
    
    permission_classes = []  # Public for demo
    
    def get(self, request):
        response = run_synthetic_demo()
        return Response(response.to_dict())


# =============================================================================
# FRONTEND-FACING SEAM
#
# These two endpoints match the shapes the React client consumes through its
# TrialBridgeApi seam (client/src/types/domain.ts). They let the frontend swap
# its LocalMockApi for an HttpTrialBridgeApi with no change to its own engine:
#
#   GET  /api/trials        -> Trial[]        (unassessed; criteria carry dependsOn)
#   POST /api/extract-facts -> PatientProfile (facts keyed by FactKey; unknown = null)
#
# They are deliberately thin and stateless. All data is fictional.
# =============================================================================


class TrialsView(APIView):
    """
    Return candidate trials in the frontend's `Trial` shape.

    GET /api/trials/

    The frontend's own assessor / ranking / question engine consume these
    unassessed trials; this endpoint intentionally does NOT pre-assess them.
    """

    permission_classes = []  # Public for demo

    def get(self, request):
        return Response(get_demo_trials())


class ExtractFactsView(APIView):
    """
    Extract structured patient facts from free-text notes.

    POST /api/extract-facts/
        { "notes": "<free text>" }

    Returns a PatientProfile in the frontend's shape: facts keyed by FactKey,
    undocumented facts left Unknown (value null). Deterministic, no LLM.
    If `notes` is omitted, the fictional demo note is used.
    """

    permission_classes = []  # Public for demo

    def post(self, request):
        notes = request.data.get("notes")
        if notes is None:
            notes = DEMO_PATIENT_NOTES
        if not isinstance(notes, str):
            return Response(
                {"error": "`notes` must be a string"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(parse_notes(notes))
