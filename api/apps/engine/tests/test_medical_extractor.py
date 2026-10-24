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


@override_settings(ENGINE={"MODEL_API_BASE_URL": "", "MODEL_NAME": "medgemma"})
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
    def test_parses_plain_json(self):
        raw = '{"conditions": [{"value": "x"}]}'
        parsed = medical_extractor._parse_model_json(raw)
        self.assertEqual(parsed["conditions"][0]["value"], "x")

    def test_parses_fenced_json(self):
        raw = '```json\n{"conditions": [{"value": "x"}]}\n```'
        parsed = medical_extractor._parse_model_json(raw)
        self.assertEqual(parsed["conditions"][0]["value"], "x")

    def test_returns_none_for_garbage(self):
        self.assertIsNone(medical_extractor._parse_model_json("not json at all"))

    def test_returns_none_for_empty(self):
        self.assertIsNone(medical_extractor._parse_model_json(""))

    def test_parses_reasoning_model_output(self):
        """
        MedGemma (Gemma 3) emits a <unused94>thought ...<unused95> block, often
        containing an illustrative JSON snippet, BEFORE the real fenced answer.
        The parser must skip the thinking block and take the final JSON.
        """
        raw = (
            "<unused94>thought\n"
            "I should extract entities. Example of what NOT to return:\n"
            '```json\n{"conditions": [{"value": "WRONG"}]}\n```\n'
            "Now the real answer.<unused95>"
            '```json\n'
            '{"conditions": [{"value": "alcohol use disorder", '
            '"evidence": "alcohol use disorder"}], "symptoms": [], '
            '"medications": [], "previous_treatments": [], '
            '"lab_results": [], "dates": []}\n'
            "```"
        )
        parsed = medical_extractor._parse_model_json(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(
            parsed["conditions"][0]["value"], "alcohol use disorder"
        )

    def test_salvages_trailing_json_object_without_fence(self):
        raw = (
            "<unused94>thought\nreasoning here<unused95>"
            '{"conditions": [{"value": "hypertension"}], "symptoms": []}'
        )
        parsed = medical_extractor._parse_model_json(raw)
        self.assertEqual(parsed["conditions"][0]["value"], "hypertension")

    def test_extract_filters_unknown_keys_and_nonlists(self):
        """Only known entity keys that are lists survive; no fabrication."""
        raw = (
            '{"conditions": [{"value": "x"}], "bogus": [{"value": "y"}], '
            '"symptoms": "not-a-list"}'
        )
        parsed = medical_extractor._parse_model_json(raw)
        entities = medical_extractor.empty_entities()
        for key in medical_extractor.ENTITY_KEYS:
            value = parsed.get(key)
            if isinstance(value, list):
                entities[key] = value
        self.assertEqual(entities["conditions"], [{"value": "x"}])
        self.assertEqual(entities["symptoms"], [])  # non-list dropped
        self.assertNotIn("bogus", entities)

    def test_salvages_object_with_unbalanced_brace_in_string(self):
        """
        A clinical evidence snippet can contain a lone '{' or '}'. With
        surrounding prose (so whole-text parse fails) and no code fence, the
        salvage scan must stay JSON-string-aware and still recover the object.
        """
        raw = (
            "Here is the result:\n"
            '{"conditions": [{"value": "edema", '
            '"evidence": "noted {2+} pitting edema, BP high }"}], '
            '"symptoms": []}\n'
            "I hope this helps!"
        )
        parsed = medical_extractor._parse_model_json(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["conditions"][0]["value"], "edema")
        self.assertEqual(
            parsed["conditions"][0]["evidence"],
            "noted {2+} pitting edema, BP high }",
        )

    def test_marker_token_inside_json_string_does_not_drop_answer(self):
        """
        A thinking-marker-looking token (e.g. '</think>') appearing inside a
        JSON string value must not cause the answer to be truncated/dropped.
        """
        raw = (
            "answer: "
            '{"conditions": [{"value": "x", '
            '"evidence": "patient said </think> jokingly"}], "symptoms": []} '
            "end"
        )
        parsed = medical_extractor._parse_model_json(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["conditions"][0]["value"], "x")
        self.assertIn("</think>", parsed["conditions"][0]["evidence"])

    def test_returns_none_for_top_level_array(self):
        """A top-level JSON array is not the expected object shape -> None."""
        self.assertIsNone(
            medical_extractor._parse_model_json('[{"value": "x"}]')
        )

    def test_prefers_final_object_over_thinking_snippet_without_fence(self):
        """
        When the thinking block contains an illustrative bare object and the
        real answer is a later bare object, the final one must win.
        """
        raw = (
            "<unused94>thought\n"
            'Example of what NOT to return: {"conditions": [{"value": "WRONG"}]}\n'
            "Now the real answer.<unused95>\n"
            '{"conditions": [{"value": "RIGHT"}], "symptoms": []}'
        )
        parsed = medical_extractor._parse_model_json(raw)
        self.assertEqual(parsed["conditions"][0]["value"], "RIGHT")
