from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.engine.services import model_client
from apps.users.models import PatientProfile

User = get_user_model()

EXAMPLE_PATIENT = {
    "patient": {
        "age": 34,
        "primary_condition": "Alcohol Use Disorder",
        "sex_for_eligibility": None,
        "location": {"state": "MA", "city": "Lowell"},
        "conditions": ["Alcohol Use Disorder"],
        "symptoms": [],
        "medications": [
            {"name": "Naltrexone", "dosage": "50 mg", "status": "current"}
        ],
        "previous_treatments": [],
        "lab_results": [],
        "medical_note": (
            "This fictional patient is 34 years old and has alcohol use "
            "disorder. They currently take naltrexone 50 mg daily."
        ),
    }
}


# Model unconfigured => extraction unavailable, no fabrication.
@override_settings(ENGINE={"MODEL_API_BASE_URL": "", "MODEL_NAME": "qwen",
                           "CHROMA_PERSIST_DIR": "/nonexistent",
                           "CHROMA_COLLECTION": "clinical_trials"})
class IntakeApiTests(APITestCase):
    def setUp(self):
        model_client._client = None
        self.user = User.objects.create_user(
            email="patient@example.com", password="secret123"
        )

    def tearDown(self):
        model_client._client = None

    def test_unauthenticated_request_is_rejected(self):
        resp = self.client.post(reverse("engine:intake"), EXAMPLE_PATIENT,
                                format="json")
        self.assertEqual(resp.status_code, 401)

    def test_authenticated_intake_normalizes_and_persists(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(reverse("engine:intake"), EXAMPLE_PATIENT,
                                format="json")
        self.assertEqual(resp.status_code, 201)
        data = resp.json()

        self.assertIn("profile", data)
        profile = data["profile"]
        self.assertEqual(profile["age"], 34)
        self.assertEqual(profile["primary_condition"], "Alcohol Use Disorder")
        self.assertEqual(profile["location"], {"state": "MA", "city": "Lowell"})
        # User-provided medication, source-tagged.
        self.assertEqual(profile["medications"][0]["source"], "user")
        self.assertEqual(profile["medications"][0]["value"]["name"], "Naltrexone")
        # Model unavailable => no fabricated extraction.
        self.assertFalse(data["model_available"])
        self.assertFalse(profile["extraction_available"])

        # Persisted for the user.
        record = PatientProfile.objects.get(pk=data["profile_id"])
        self.assertEqual(record.user_id, self.user.id)
        self.assertEqual(record.primary_condition, "Alcohol Use Disorder")

    def test_near_empty_payload_accepted(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("engine:intake"),
            {"patient": {"primary_condition": "Hypertension"}},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        profile = resp.json()["profile"]
        self.assertIsNone(profile["age"])
        self.assertEqual(profile["location"]["state"], "MA")

    def test_trials_endpoint_reports_unavailable_without_fabrication(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("engine:trials"),
            {"patient": {"primary_condition": "Alcohol Use Disorder"}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["retrieval_available"])
        self.assertFalse(data["matching_available"])
        self.assertEqual(data["results"], [])
