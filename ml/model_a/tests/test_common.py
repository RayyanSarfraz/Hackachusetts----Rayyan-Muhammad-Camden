"""Unit tests for pure helpers: config merge, JSON parsing, NER offsets,
deterministic splits, and output schema validation. No ML deps required.

Run from ml/model_a/:  python -m pytest tests/ -q   (or: python -m unittest)
"""

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import common  # noqa: E402
import prepare_data  # noqa: E402
import infer  # noqa: E402
import evaluate as ev  # noqa: E402


class TestConfigMerge(unittest.TestCase):
    def setUp(self):
        self.cfg = common.load_yaml(common.DEFAULT_CONFIG_PATH)

    def test_config_loads(self):
        self.assertEqual(self.cfg["model"]["id"], "google/medgemma-1.5-4b-it")
        self.assertTrue(self.cfg["model"]["load_in_4bit"])  # base default

    def test_g4_profile_overrides_to_bf16_no_4bit(self):
        key = common.resolve_gpu_profile_key("NVIDIA RTX PRO 6000 Blackwell", 96, self.cfg)
        self.assertEqual(key, "g4")
        eff = common.effective_config(self.cfg, key)
        self.assertFalse(eff["effective"]["load_in_4bit"])  # override wins
        self.assertEqual(eff["effective"]["method"], "bf16_lora")
        self.assertEqual(eff["effective"]["precision"], "bf16")
        self.assertEqual(eff["effective"]["max_seq_length"], 2048)
        self.assertEqual(eff["effective"]["per_device_train_batch_size"], 2)

    def test_a100_vram_resolution(self):
        self.assertEqual(common.resolve_gpu_profile_key("NVIDIA A100-SXM4-80GB", 80, self.cfg), "a100_80gb")
        self.assertEqual(common.resolve_gpu_profile_key("NVIDIA A100-SXM4-40GB", 40, self.cfg), "a100_40gb")

    def test_t4_stays_4bit_fp16(self):
        key = common.resolve_gpu_profile_key("Tesla T4", 16, self.cfg)
        eff = common.effective_config(self.cfg, key)
        self.assertTrue(eff["effective"]["load_in_4bit"])
        self.assertEqual(eff["effective"]["precision"], "fp16")

    def test_l4_qlora_bf16(self):
        key = common.resolve_gpu_profile_key("NVIDIA L4", 24, self.cfg)
        eff = common.effective_config(self.cfg, key)
        self.assertTrue(eff["effective"]["load_in_4bit"])
        self.assertEqual(eff["effective"]["precision"], "bf16")

    def test_unknown_gpu_falls_back_to_default(self):
        key = common.resolve_gpu_profile_key("Some Future GPU", 48, self.cfg)
        self.assertEqual(key, self.cfg["gpu_profiles"]["default_profile"])


class TestJsonParsing(unittest.TestCase):
    def test_plain(self):
        v, ok = common.parse_json_safe('{"a": 1}')
        self.assertTrue(ok)
        self.assertEqual(v, {"a": 1})

    def test_fenced(self):
        v, ok = common.parse_json_safe('```json\n{"a": 1}\n```')
        self.assertTrue(ok)
        self.assertEqual(v["a"], 1)

    def test_leading_prose(self):
        v, ok = common.parse_json_safe('Sure! Here it is: {"x": [1,2]} done')
        self.assertTrue(ok)
        self.assertEqual(v, {"x": [1, 2]})

    def test_already_dict(self):
        v, ok = common.parse_json_safe({"a": 1})
        self.assertTrue(ok)

    def test_garbage(self):
        v, ok = common.parse_json_safe("not json at all")
        self.assertFalse(ok)
        self.assertIsNone(v)


class TestNer(unittest.TestCase):
    def test_verify_span_match(self):
        text = "Prescribed metformin for diabetes."
        self.assertTrue(common.verify_entity_span(text, {"text": "metformin", "start": 11, "end": 20}))

    def test_verify_span_mismatch(self):
        text = "Prescribed metformin for diabetes."
        self.assertFalse(common.verify_entity_span(text, {"text": "aspirin", "start": 11, "end": 20}))

    def test_clean_entities_drops_bad(self):
        text = "Prescribed metformin for diabetes."
        stats = common.NerStats()
        kept = common.clean_entities(
            text,
            [
                {"text": "metformin", "label": "MED", "start": 11, "end": 20},
                {"text": "WRONG", "label": "MED", "start": 0, "end": 5},
                {"text": "", "label": "MED", "start": 0, "end": 0},
            ],
            stats,
        )
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["text"], "metformin")
        self.assertEqual(stats.dropped_offset_mismatch, 1)
        self.assertEqual(stats.dropped_empty, 1)
        # kept entities carry NO offsets (not trained on offsets)
        self.assertNotIn("start", kept[0])

    def test_recompute_offsets(self):
        text = "Prescribed metformin for diabetes."
        out = common.recompute_offsets(text, [{"text": "diabetes", "label": "COND"}])
        self.assertEqual(out[0]["start"], text.index("diabetes"))
        self.assertEqual(text[out[0]["start"]:out[0]["end"]], "diabetes")

    def test_recompute_offset_absent(self):
        out = common.recompute_offsets("abc", [{"text": "zzz", "label": "X"}])
        self.assertIsNone(out[0]["start"])


class TestSplits(unittest.TestCase):
    def test_deterministic(self):
        a = common.assign_split("case-123", 42, 0.8, 0.1)
        b = common.assign_split("case-123", 42, 0.8, 0.1)
        self.assertEqual(a, b)

    def test_distribution_reasonable(self):
        counts = {"train": 0, "validation": 0, "test": 0}
        for i in range(2000):
            counts[common.assign_split(f"c{i}", 42, 0.8, 0.1)] += 1
        self.assertGreater(counts["train"], 1400)  # ~1600
        self.assertGreater(counts["validation"], 100)
        self.assertGreater(counts["test"], 100)

    def test_no_leakage_same_case(self):
        self.assertEqual(
            common.assign_split("X", 7, 0.8, 0.1),
            common.assign_split("X", 7, 0.8, 0.1),
        )


class TestPrepareBuilders(unittest.TestCase):
    def setUp(self):
        self.cfg = common.load_yaml(common.DEFAULT_CONFIG_PATH)

    def test_primary_example(self):
        row = {"idx": "1", "full_note": "note text", "summary": json.dumps({"a": "b"})}
        ex = prepare_data.build_primary_example(row, self.cfg, 10000)
        self.assertEqual(ex["task"], "EXTRACT_SUMMARY")
        self.assertEqual(ex["case_id"], "1")
        self.assertEqual(ex["messages"][0]["role"], "system")
        # target is canonical JSON of the summary
        self.assertEqual(json.loads(ex["target"]), {"a": "b"})

    def test_primary_skips_bad_summary(self):
        row = {"idx": "1", "full_note": "note", "summary": "not json"}
        self.assertIsNone(prepare_data.build_primary_example(row, self.cfg, 10000))

    def test_secondary_filters_language(self):
        stats = common.NerStats()
        row = {"text": "x", "language": "german", "entities": []}
        self.assertIsNone(prepare_data.build_secondary_example(row, self.cfg, stats, 10000))

    def test_secondary_example(self):
        stats = common.NerStats()
        text = "Prescribed metformin for diabetes."
        row = {
            "text": text,
            "language": "English",
            "entities": [{"text": "metformin", "label": "MED", "start": 11, "end": 20}],
        }
        ex = prepare_data.build_secondary_example(row, self.cfg, stats, 10000)
        self.assertEqual(ex["task"], "EXTRACT_ENTITIES")
        self.assertEqual(json.loads(ex["target"])["entities"][0]["text"], "metformin")

    def test_dedupe_and_split_no_leak(self):
        rows = []
        for i in range(50):
            rows.append(
                {
                    "case_id": f"c{i}",
                    "source": "s",
                    "task": "EXTRACT_SUMMARY",
                    "language": "english",
                    "messages": [],
                    "target": "{}",
                    "source_text": f"unique text number {i}",
                    "overlong": False,
                }
            )
        # add an exact duplicate source -> should be dropped
        rows.append(dict(rows[0], case_id="dup"))
        out, counts = prepare_data.dedupe_and_split(rows, self.cfg)
        self.assertEqual(counts["duplicates_dropped"], 1)
        case_splits = {}
        for e in out:
            case_splits.setdefault(e["case_id"], set()).add(e["split"])
        self.assertTrue(all(len(v) == 1 for v in case_splits.values()))


class TestSchemaValidation(unittest.TestCase):
    def test_validate_entities(self):
        clean, problems = infer.validate_entities({"entities": [{"text": "a", "label": "L"}, {"bad": 1}]})
        self.assertEqual(len(clean["entities"]), 1)
        self.assertTrue(problems)

    def test_validate_entities_missing_key(self):
        clean, problems = infer.validate_entities({"foo": 1})
        self.assertEqual(clean, {"entities": []})
        self.assertTrue(problems)

    def test_validate_summary_nulls(self):
        clean, _ = infer.validate_summary({"a": "None", "b": {"c": "unknown"}, "d": "real"})
        self.assertIsNone(clean["a"])
        self.assertIsNone(clean["b"]["c"])
        self.assertEqual(clean["d"], "real")


class TestScoring(unittest.TestCase):
    def test_prf(self):
        r = ev.prf(tp=2, fp=1, fn=1)
        self.assertAlmostEqual(r["precision"], 2 / 3, places=3)
        self.assertAlmostEqual(r["recall"], 2 / 3, places=3)

    def test_score_ner_grounding(self):
        src = "Prescribed metformin for diabetes."
        pred = {"entities": [{"text": "metformin", "label": "MED"}, {"text": "aspirin", "label": "MED"}]}
        gold = [{"text": "metformin", "label": "MED"}, {"text": "diabetes", "label": "COND"}]
        res = ev.score_ner(pred, gold, src)
        self.assertEqual(res["evidence_grounding_rate"], 0.5)  # aspirin not in source
        self.assertEqual(res["relaxed"]["tp"], 1)  # metformin overlaps

    def test_score_summary_coverage(self):
        gold = {"visit": "chest pain", "med": "aspirin", "empty": "None"}
        pred = {"visit": "chest pain", "med": None}
        src = "Patient with chest pain started on aspirin."
        res = ev.score_summary(pred, gold, src)
        self.assertEqual(res["gold_fields"], 2)  # empty 'None' excluded
        self.assertEqual(res["fields_filled"], 1)  # only 'visit' filled
        self.assertEqual(res["coverage"], 0.5)


if __name__ == "__main__":
    unittest.main()
