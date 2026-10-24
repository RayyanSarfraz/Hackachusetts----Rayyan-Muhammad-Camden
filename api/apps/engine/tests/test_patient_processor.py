from django.test import SimpleTestCase

from apps.engine.services.patient_processor import normalize_patient


class NormalizePatientTests(SimpleTestCase):
    def test_empty_input_produces_empty_profile(self):
        profile = normalize_patient({}).as_dict()
        self.assertIsNone(profile["age"])
        self.assertEqual(profile["primary_condition"], "")
        self.assertEqual(profile["location"], {"state": "MA", "city": ""})
        self.assertEqual(profile["conditions"], [])
        self.assertEqual(profile["medications"], [])
        self.assertFalse(profile["extraction_available"])
        self.assertEqual(profile["extraction_conflicts"], [])

    def test_primary_condition_added_to_conditions_with_user_source(self):
        profile = normalize_patient(
            {"primary_condition": "Alcohol Use Disorder"}
        ).as_dict()
        conditions = profile["conditions"]
        self.assertEqual(len(conditions), 1)
        self.assertEqual(conditions[0]["value"], "Alcohol Use Disorder")
        self.assertEqual(conditions[0]["source"], "user")

    def test_user_values_are_source_tagged(self):
        profile = normalize_patient(
            {
                "symptoms": ["insomnia"],
                "medications": [{"name": "Naltrexone", "dosage": "50 mg"}],
            }
        ).as_dict()
        self.assertEqual(profile["symptoms"][0]["source"], "user")
        self.assertEqual(profile["medications"][0]["source"], "user")

    def test_dedup_is_case_insensitive(self):
        profile = normalize_patient(
            {"conditions": ["Diabetes", "diabetes", "DIABETES"]}
        ).as_dict()
        self.assertEqual(len(profile["conditions"]), 1)
        self.assertEqual(profile["conditions"][0]["value"], "Diabetes")

    def test_extracted_facts_added_and_tagged(self):
        extracted = {
            "symptoms": [{"value": "tremor", "evidence": "reports tremor"}],
        }
        profile = normalize_patient(
            {"symptoms": ["insomnia"]},
            extracted=extracted,
            extraction_available=True,
        ).as_dict()
        sources = {s["source"] for s in profile["symptoms"]}
        self.assertEqual(sources, {"user", "extracted"})
        self.assertTrue(profile["extraction_available"])

    def test_extracted_does_not_overwrite_user_and_flags_conflict(self):
        extracted = {
            "medications": [
                {"value": {"name": "Naltrexone", "dosage": "100 mg"}}
            ]
        }
        profile = normalize_patient(
            {"medications": [{"name": "Naltrexone", "dosage": "50 mg"}]},
            extracted=extracted,
            extraction_available=True,
        ).as_dict()
        # User value preserved; only one Naltrexone entry (the user's).
        meds = [m for m in profile["medications"]]
        self.assertEqual(len(meds), 1)
        self.assertEqual(meds[0]["source"], "user")
        self.assertEqual(meds[0]["value"]["dosage"], "50 mg")
        # Conflict flagged for review.
        self.assertEqual(len(profile["extraction_conflicts"]), 1)
        self.assertEqual(profile["extraction_conflicts"][0]["field"], "medications")

    def test_age_falls_back_to_extracted_only_when_user_blank(self):
        # User provided -> extracted ignored.
        p1 = normalize_patient({"age": 34}, extracted={"age": 40}).as_dict()
        self.assertEqual(p1["age"], 34)
        # User blank -> extracted used.
        p2 = normalize_patient({}, extracted={"age": 40}).as_dict()
        self.assertEqual(p2["age"], 40)
