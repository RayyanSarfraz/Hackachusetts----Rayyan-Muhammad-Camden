import io
import os
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.engine.models import Trial
from apps.engine.services.retriever import TrialRetriever

HEADER = "nct_id,title,phase,conditions,massachusetts_city,status\n"


def _write_csv(text: str) -> str:
    fh = tempfile.NamedTemporaryFile(
        "w", suffix=".csv", delete=False, encoding="utf-8", newline=""
    )
    fh.write(text)
    fh.close()
    return fh.name


class IngestTrialsCommandTests(TestCase):
    def setUp(self):
        self.paths = []

    def tearDown(self):
        for path in self.paths:
            os.unlink(path)

    def _csv(self, text: str) -> str:
        path = _write_csv(text)
        self.paths.append(path)
        return path

    def _ingest(self, path: str):
        call_command("ingest_trials", path, "--skip-vectors", stdout=io.StringIO())

    def test_rerun_upserts_by_nct_id_instead_of_duplicating(self):
        first = self._csv(
            HEADER
            + 'NCT00000001,Old title,PHASE2,"Diabetes, Obesity",,RECRUITING\n'
            + "NCT00000002,Second,,Asthma,,RECRUITING\n"
        )
        self._ingest(first)
        second = self._csv(
            HEADER + 'NCT00000001,New title,PHASE3,"Diabetes, Obesity",,RECRUITING\n'
        )
        self._ingest(second)

        self.assertEqual(Trial.objects.count(), 2)
        trial = Trial.objects.get(nct_id="NCT00000001")
        self.assertEqual(trial.title, "New title")
        self.assertEqual(trial.phase, "PHASE3")
        self.assertEqual(trial.condition_list, ["Diabetes", "Obesity"])

    def test_rows_without_nct_id_are_skipped(self):
        path = self._csv(
            HEADER + ",No id,,Asthma,,RECRUITING\nNCT00000003,Has id,,,,RECRUITING\n"
        )
        self._ingest(path)
        self.assertEqual(
            list(Trial.objects.values_list("nct_id", flat=True)), ["NCT00000003"]
        )

    def test_missing_required_column_fails_without_writing(self):
        path = self._csv("title,status\nSomething,RECRUITING\n")
        with self.assertRaises(CommandError):
            self._ingest(path)
        self.assertEqual(Trial.objects.count(), 0)


class _StubCollection:
    def __init__(self, ids):
        self.ids = ids

    def query(self, query_texts, n_results):
        return {
            "ids": [self.ids],
            "metadatas": [[{"nct_id": i} for i in self.ids]],
            "distances": [[0.1 * n for n in range(len(self.ids))]],
        }


class RetrieverJoinTests(TestCase):
    def test_hits_are_joined_to_postgres_and_unknown_ids_stay_unjoined(self):
        Trial.objects.create(
            nct_id="NCT00000010", title="Insulin pump study",
            conditions="Type 1 Diabetes; Hypoglycemia", status="RECRUITING",
        )
        retriever = TrialRetriever()
        retriever._collection = _StubCollection(["NCT00000010", "NCT09999999"])
        retriever._checked = True

        result = retriever.retrieve("type 1 diabetes", n_results=2)

        self.assertTrue(result["available"])
        joined, missing = result["results"]
        self.assertEqual(joined["trial"]["title"], "Insulin pump study")
        self.assertEqual(
            joined["trial"]["conditions"], ["Type 1 Diabetes", "Hypoglycemia"]
        )
        self.assertEqual(missing["trial_id"], "NCT09999999")
        self.assertIsNone(missing["trial"])
