from django.test import SimpleTestCase, override_settings

from apps.engine.services import medical_extractor, model_client
from apps.engine.services.medical_extractor import (
    ENTITY_KEYS,
    empty_entities,
    extract_medical_entities,
)


def _reset_client():
    """Clear the cached ModelClient so settings overrides take effect."""
    model_client._client = None


@override_settings(ENGINE={"MODEL_API_BASE_URL": "", "MODEL_NAME": "qwen"})
class MedicalExtractorUnavailableTests(SimpleTestCase):
    def setUp(self):
        _reset_client()

    def tearDown(self):
        _reset_client()

    def test_returns_unavailable_when_model_not_configured(self):
        result = extract_medical_entities("Patient has a cough.")
        self.assertFalse(result["available"])
        self.assertEqual(result["entities"], empty_entities())

    def test_empty_note_returns_unavailable_without_fabrication(self):
        result = extract_medical_entities("")
        self.assertFalse(result["available"])
        for key in ENTITY_KEYS:
            self.assertEqual(result["entities"][key], [])

    def test_empty_entities_shape_is_consistent(self):
        entities = empty_entities()
        self.assertEqual(set(entities.keys()), set(ENTITY_KEYS))
        self.assertTrue(all(v == [] for v in entities.values()))


class ParseModelJsonTests(SimpleTestCase):
    def test_parses_fenced_json(self):
        raw = '```json\n{"conditions": [{"value": "x"}]}\n```'
        parsed = medical_extractor._parse_model_json(raw)
        self.assertEqual(parsed["conditions"][0]["value"], "x")

    def test_returns_none_for_garbage(self):
        self.assertIsNone(medical_extractor._parse_model_json("not json at all"))
