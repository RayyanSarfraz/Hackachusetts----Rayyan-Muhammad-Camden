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
)
from .fixtures import get_synthetic_trials, get_synthetic_patient


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
            ))
        
        return TrialCandidate(
            nct_id=data["nct_id"],
            title=data["title"],
            source_url=data["source_url"],
            recruitment_status=data.get("recruitment_status"),
            locations=locations,
            criteria=criteria,
        )


class AnswerQuestionView(APIView):
    """
    Answer a clarification question.
    
    POST /api/integration/answer/
    
    Request body:
        {
            "question_id": "...",
            "answer": "yes" | "no" | "unknown" | ...
        }
    
    Returns:
        {
            "updated_profile": {...},
            "affected_criteria": [...],
            "requires_reassessment": [...]
        }
    
    Note: This does NOT automatically resolve criteria.
    The clinical assessment module must reevaluate affected criteria.
    """
    
    permission_classes = []  # Public for demo
    
    def post(self, request):
        question_id = request.data.get("question_id")
        answer = request.data.get("answer")
        
        if not question_id or answer is None:
            return Response(
                {"error": "question_id and answer are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # For demo, use synthetic data
        # In production, this would fetch from session/database
        patient = get_synthetic_patient()
        trials = get_synthetic_trials()
        
        try:
            updated_profile, affected, reassess = apply_clarification_answer(
                trials, patient, question_id, answer
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        return Response({
            "updated_profile": updated_profile.to_dict(),
            "affected_criteria": affected,
            "requires_reassessment": reassess,
            "note": "Clinical criteria must be reassessed by the clinical assessment module.",
        })


class UpdatePreferencesView(APIView):
    """
    Update patient preferences and re-rank trials.
    
    POST /api/integration/preferences/
    
    Request body:
        {
            "max_travel_miles": 100.0,
            "avoid_overnight_stays": true,
            "max_visits": 12
        }
    
    Returns:
        Re-ranked trial comparison (no clinical reassessment).
    
    This is the PREFERRED endpoint for preference-only changes.
    It does NOT call any LLM or clinical assessment services.
    """
    
    permission_classes = []  # Public for demo
    
    def post(self, request):
        preferences = PatientPreferences(
            max_travel_miles=request.data.get("max_travel_miles"),
            avoid_overnight_stays=request.data.get("avoid_overnight_stays"),
            max_visits=request.data.get("max_visits"),
        )
        
        # For demo, use synthetic trials
        # In production, would fetch from session/database
        trials = get_synthetic_trials()
        
        # Re-rank (pure function, no external calls)
        updated_trials = update_preferences_only(trials, preferences)
        
        # Build comparison response
        from .orchestrator import combine_trials_and_patient
        patient = get_synthetic_patient()
        patient.preferences = preferences
        response = combine_trials_and_patient(updated_trials, patient)
        
        return Response(response.to_dict())


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
