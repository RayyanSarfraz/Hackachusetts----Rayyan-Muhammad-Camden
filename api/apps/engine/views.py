"""Engine API views: status, patient intake, and trial search."""
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.engine.serializers import IntakeRequestSerializer, PatientSerializer
from apps.engine.services import pipeline
from apps.users.models import PatientProfile


class EngineStatusView(APIView):
    """Lightweight status endpoint for the engine module."""

    permission_classes = [AllowAny]

    def get(self, _request):
        return Response({"module": "engine", "status": "ok"})


class IntakeView(APIView):
    """
    POST /api/engine/intake/

    Validate -> normalize -> (extract if model available) -> persist a
    PatientProfile for the authenticated user -> return the normalized profile.
    Preserves user-vs-extracted provenance and reports model availability.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = IntakeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = serializer.validated_data["patient"]

        result = pipeline.run_intake(patient)
        profile = result["profile"]

        # Persist. Store the sourced-fact lists as-is to preserve provenance.
        record = PatientProfile.objects.create(
            user=request.user,
            age=profile["age"],
            primary_condition=profile["primary_condition"],
            city=profile["location"].get("city", ""),
            state=profile["location"].get("state", "MA"),
            sex_for_eligibility=profile["sex_for_eligibility"],
            medical_note=profile["medical_note"],
            conditions=profile["conditions"],
            symptoms=profile["symptoms"],
            medications=profile["medications"],
            previous_treatments=profile["previous_treatments"],
            lab_results=profile["lab_results"],
            extraction_conflicts=profile["extraction_conflicts"],
            extraction_available=profile["extraction_available"],
        )

        return Response(
            {
                "profile_id": record.id,
                "profile": profile,
                "model_available": result["model_available"],
            },
            status=status.HTTP_201_CREATED,
        )


class TrialSearchView(APIView):
    """
    POST /api/engine/trials/

    Accepts a normalized profile (as returned by intake) and runs the trial
    retrieval workflow. Returns honest availability flags; never fabricates
    trials or eligibility results when services are unavailable.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.data.get("profile")
        if not isinstance(profile, dict):
            # Allow passing a raw patient object too; normalize it first.
            patient_serializer = PatientSerializer(data=request.data.get("patient", {}))
            patient_serializer.is_valid(raise_exception=True)
            profile = pipeline.run_intake(patient_serializer.validated_data)["profile"]

        result = pipeline.run_trial_search(profile)
        return Response(result, status=status.HTTP_200_OK)


class MatchView(APIView):
    """
    POST /api/engine/match/

    Unified match + clarify flow in one call. Validates the patient, runs the
    engine (extract + normalize + retrieve/match the real dataset), and returns
    matched trials plus clarifying questions for matcher-relevant gaps.

    Accepts optional ``answers`` (a map of required_fact_key -> value from a
    previously-generated form) which are merged into the profile before
    re-matching, enabling a fill-form -> refine loop.

    Public for the demo (like the integration + frontend-seam endpoints).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PatientSerializer(data=request.data.get("patient", {}))
        serializer.is_valid(raise_exception=True)

        answers = request.data.get("answers") or {}
        if not isinstance(answers, dict):
            return Response(
                {"error": "`answers` must be an object of fact_key -> value."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = pipeline.run_match(serializer.validated_data, answers=answers)
        return Response(result, status=status.HTTP_200_OK)
