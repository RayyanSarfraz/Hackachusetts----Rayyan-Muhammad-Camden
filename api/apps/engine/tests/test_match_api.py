from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.engine.services import model_client
from apps.engine.services.clarifier import apply_answers, generate_questions


class ClarifierTests(SimpleTestCase):
    def test_questions_only_for_missing_facts(self):
        profile = {
            "age": 54,
            "primary_condition": "Diabetes",
            "sex_for_eligibility": None,
            "location": {"state": "", "city": ""},
        }
        keys = {q["required_fact_key"] for q in generate_questions(profile)}
        # age + primary_condition present -> not asked; sex + state missing -> asked.
        self.assertNotIn("age", keys)
        self.assertNotIn("primary_condition", keys)
        self.assertIn("sex_for_eligibility", keys)
        self.assertIn("location_state", keys)

    def test_question_shape_matches_contract(self):
        q = generate_questions({})[0]
        for field in ("question_id", "required_fact_key", "display_question",
                      "answer_type", "related_trial_ids", "source_criterion_ids"):
            self.assertIn(field, q)

    def test_apply_answers_merges_known_ignores_unknown(self):
        patient = {"location": {"city": "Boston"}}
        merged = apply_answers(patient, {
            "age": "61",
            "sex_for_eligibility": "female",
            "location_state": "MA",
            "primary_condition": "unknown",  # blank/unknown -> ignored
        })
        self.assertEqual(merged["age"], 61)
        self.assertEqual(merged["sex_for_eligibility"], "female")
        self.assertEqual(merged["location"]["state"], "MA")
        self.assertEqual(merged["location"]["city"], "Boston")  # preserved
        self.assertNotIn("primary_condition", merged)  # unknown not fabricated

    def test_apply_answers_does_not_mutate_input(self):
        patient = {"age": None}
        apply_answers(patient, {"age": "40"})
        self.assertIsNone(patient["age"])


# Model + vector store OFF -> deterministic, graceful-unavailable path.
@override_settings(ENGINE={"MODEL_API_BASE_URL": "", "MODEL_NAME": "medgemma",
                           "CHROMA_PERSIST_DIR": "/nonexistent",
                           "CHROMA_COLLECTION": "clinical_trials"})
class MatchApiTests(APITestCase):
    def setUp(self):
        model_client._client = None

    def tearDown(self):
        model_client._client = None

    def test_match_is_public_and_returns_profile_and_questions(self):
        resp = self.client.post(reverse("engine:match"), {
            "patient": {"medical_note": "patient reports fatigue"}
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("profile", data)
        self.assertIn("results", data)
        self.assertIn("questions", data)
        # No model/vector store -> honest unavailability, no fabrication.
        self.assertFalse(data["model_available"])
        self.assertFalse(data["retrieval_available"])
        self.assertEqual(data["results"], [])
        # Gaps (age, sex, condition, state) surface as questions.
        self.assertTrue(len(data["questions"]) >= 1)

    def test_answers_merge_and_reduce_questions(self):
        first = self.client.post(reverse("engine:match"), {
            "patient": {"medical_note": "fatigue"}
        }, format="json").json()
        asked = {q["required_fact_key"] for q in first["questions"]}
        self.assertIn("age", asked)

        second = self.client.post(reverse("engine:match"), {
            "patient": {"medical_note": "fatigue"},
            "answers": {"age": "61", "primary_condition": "Hypertension",
                        "sex_for_eligibility": "female", "location_state": "MA"},
        }, format="json").json()
        self.assertEqual(second["profile"]["age"], 61)
        # All four gaps answered -> no remaining questions.
        self.assertEqual(second["questions"], [])

    def test_bad_answers_type_rejected(self):
        resp = self.client.post(reverse("engine:match"), {
            "patient": {"medical_note": "x"}, "answers": "notadict"
        }, format="json")
        self.assertEqual(resp.status_code, 400)
