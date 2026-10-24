"""
Patient normalization.

Turns validated intake input (and optional AI-extracted entities) into a
consistent, deduplicated, provenance-preserving profile that downstream
services can consume.

Rules enforced here:
- Every fact carries a ``source``: "user" (typed into the form) or
  "extracted" (pulled from the free-text note by the AI model).
- User-provided values are authoritative. AI-extracted values never silently
  overwrite them; conflicts are flagged for review instead.
- Lists are deduplicated case-insensitively while keeping the first spelling.
- Missing information stays null/empty. Nothing is fabricated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourcedFact:
    """A single medical fact plus where it came from."""

    value: Any
    source: str  # "user" | "extracted"
    evidence: str | None = None

    def as_dict(self) -> dict:
        d = {"value": self.value, "source": self.source}
        if self.evidence is not None:
            d["evidence"] = self.evidence
        return d


@dataclass
class NormalizedPatientProfile:
    """Consistent profile consumed by retrieval/matching services."""

    age: int | None = None
    primary_condition: str = ""
    sex_for_eligibility: str | None = None
    location: dict = field(default_factory=lambda: {"state": "MA", "city": ""})

    conditions: list[SourcedFact] = field(default_factory=list)
    symptoms: list[SourcedFact] = field(default_factory=list)
    medications: list[SourcedFact] = field(default_factory=list)
    previous_treatments: list[SourcedFact] = field(default_factory=list)
    lab_results: list[SourcedFact] = field(default_factory=list)

    medical_note: str = ""
    extraction_conflicts: list[dict] = field(default_factory=list)
    extraction_available: bool = False

    def as_dict(self) -> dict:
        return {
            "age": self.age,
            "primary_condition": self.primary_condition,
            "sex_for_eligibility": self.sex_for_eligibility,
            "location": self.location,
            "conditions": [f.as_dict() for f in self.conditions],
            "symptoms": [f.as_dict() for f in self.symptoms],
            "medications": [f.as_dict() for f in self.medications],
            "previous_treatments": [f.as_dict() for f in self.previous_treatments],
            "lab_results": [f.as_dict() for f in self.lab_results],
            "medical_note": self.medical_note,
            "extraction_conflicts": self.extraction_conflicts,
            "extraction_available": self.extraction_available,
        }


def _norm_key(value: Any) -> str:
    """Canonical comparison key for dedup (case/space-insensitive)."""
    if isinstance(value, dict):
        # Medications and labs: key on the name/test field.
        name = value.get("name") or value.get("test") or ""
        return str(name).strip().lower()
    return str(value).strip().lower()


def _merge_list(
    user_items: list[Any],
    extracted_items: list[dict] | None,
    conflicts: list[dict],
    list_name: str,
) -> list[SourcedFact]:
    """
    Merge a user-provided list with AI-extracted items.

    - User items come first and are authoritative.
    - Extracted items are added only when they don't duplicate a user item.
    - A conflicting extracted item (same key, different detail) is recorded in
      ``conflicts`` and still surfaced as an extracted fact for review — it
      never overwrites the user's value.
    """
    facts: list[SourcedFact] = []
    seen: dict[str, SourcedFact] = {}

    for item in user_items or []:
        key = _norm_key(item)
        if not key or key in seen:
            continue
        fact = SourcedFact(value=item, source="user")
        seen[key] = fact
        facts.append(fact)

    for item in extracted_items or []:
        if not isinstance(item, dict):
            value, evidence = item, None
        else:
            value = item.get("value", item)
            evidence = item.get("evidence")
        key = _norm_key(value)
        if not key:
            continue
        if key in seen:
            existing = seen[key]
            # Same concept already provided by the user. Flag only if the
            # extracted detail genuinely differs; never overwrite the user.
            if existing.source == "user" and existing.value != value:
                conflicts.append(
                    {
                        "field": list_name,
                        "key": key,
                        "user_value": existing.value,
                        "extracted_value": value,
                    }
                )
            continue
        fact = SourcedFact(value=value, source="extracted", evidence=evidence)
        seen[key] = fact
        facts.append(fact)

    return facts


def normalize_patient(
    patient: dict,
    extracted: dict | None = None,
    extraction_available: bool = False,
) -> NormalizedPatientProfile:
    """
    Build a NormalizedPatientProfile from validated form input and optional
    extracted entities.

    ``patient`` is the validated PatientSerializer payload.
    ``extracted`` is the ``entities`` dict from medical_extractor (or None).
    """
    patient = patient or {}
    extracted = extracted or {}
    conflicts: list[dict] = []

    location_in = patient.get("location") or {}
    location = {
        "state": (location_in.get("state") or "MA"),
        "city": (location_in.get("city") or ""),
    }

    # Primary condition: user value authoritative; fall back to extracted.
    primary_condition = (patient.get("primary_condition") or "").strip()
    if not primary_condition and extracted.get("primary_condition"):
        primary_condition = str(extracted["primary_condition"]).strip()

    # Age: user value authoritative; only use extracted when user left it blank.
    age = patient.get("age")
    if age is None and extracted.get("age") is not None:
        try:
            age = int(extracted["age"])
        except (TypeError, ValueError):
            age = None

    profile = NormalizedPatientProfile(
        age=age,
        primary_condition=primary_condition,
        sex_for_eligibility=patient.get("sex_for_eligibility"),
        location=location,
        medical_note=(patient.get("medical_note") or ""),
        extraction_available=extraction_available,
    )

    # Ensure the primary condition is represented in the conditions list.
    user_conditions = list(patient.get("conditions") or [])
    if primary_condition and _norm_key(primary_condition) not in {
        _norm_key(c) for c in user_conditions
    }:
        user_conditions.insert(0, primary_condition)

    profile.conditions = _merge_list(
        user_conditions, extracted.get("conditions"), conflicts, "conditions"
    )
    profile.symptoms = _merge_list(
        patient.get("symptoms"), extracted.get("symptoms"), conflicts, "symptoms"
    )
    profile.medications = _merge_list(
        patient.get("medications"),
        extracted.get("medications"),
        conflicts,
        "medications",
    )
    profile.previous_treatments = _merge_list(
        patient.get("previous_treatments"),
        extracted.get("previous_treatments"),
        conflicts,
        "previous_treatments",
    )
    profile.lab_results = _merge_list(
        patient.get("lab_results"),
        extracted.get("lab_results"),
        conflicts,
        "lab_results",
    )

    profile.extraction_conflicts = conflicts
    return profile
