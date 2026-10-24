"""
DRF serializers for the engine intake API.

These validate the incoming patient payload. Every medical field is optional;
missing information stays null/empty and is never fabricated. The serializers
only validate and structure input — normalization happens in
``services/patient_processor.py``.
"""
from rest_framework import serializers


class LocationSerializer(serializers.Serializer):
    state = serializers.CharField(max_length=64, required=False, default="MA")
    city = serializers.CharField(
        max_length=120, required=False, allow_blank=True, allow_null=True
    )


class MedicationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    dosage = serializers.CharField(
        max_length=120, required=False, allow_blank=True, allow_null=True
    )
    status = serializers.CharField(
        max_length=60, required=False, allow_blank=True, allow_null=True
    )


class PatientSerializer(serializers.Serializer):
    """Incoming patient object. All medical fields are optional."""

    SEX_CHOICES = ("female", "male", "intersex", "unknown")

    age = serializers.IntegerField(
        required=False, allow_null=True, min_value=0, max_value=150
    )
    primary_condition = serializers.CharField(
        max_length=255, required=False, allow_blank=True, allow_null=True
    )
    sex_for_eligibility = serializers.ChoiceField(
        choices=SEX_CHOICES, required=False, allow_null=True
    )
    location = LocationSerializer(required=False)

    conditions = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False, default=list
    )
    symptoms = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False, default=list
    )
    medications = MedicationSerializer(many=True, required=False, default=list)
    previous_treatments = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False, default=list
    )
    lab_results = serializers.ListField(
        child=serializers.JSONField(), required=False, default=list
    )

    medical_note = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )


class IntakeRequestSerializer(serializers.Serializer):
    """Top-level request body: ``{"patient": {...}}``."""

    patient = PatientSerializer()


# --- Response serializers (shape only; values come from the processor) -------


class SourcedFactSerializer(serializers.Serializer):
    """A medical fact tagged with its provenance."""

    value = serializers.JSONField()
    source = serializers.ChoiceField(choices=("user", "extracted"))
    evidence = serializers.CharField(required=False, allow_null=True)


class NormalizedProfileSerializer(serializers.Serializer):
    """Shape of the normalized profile returned to the frontend."""

    age = serializers.IntegerField(allow_null=True)
    primary_condition = serializers.CharField(allow_blank=True)
    sex_for_eligibility = serializers.CharField(allow_null=True)
    location = LocationSerializer()

    conditions = SourcedFactSerializer(many=True)
    symptoms = SourcedFactSerializer(many=True)
    medications = SourcedFactSerializer(many=True)
    previous_treatments = SourcedFactSerializer(many=True)
    lab_results = SourcedFactSerializer(many=True)

    medical_note = serializers.CharField(allow_blank=True)
    extraction_conflicts = serializers.ListField(child=serializers.JSONField())
    extraction_available = serializers.BooleanField()
