"""
Ingest a clinical-trial CSV into PostgreSQL (full records) and ChromaDB
(searchable text + embeddings), keyed by NCT id.

Usage (from api/):
    python manage.py ingest_trials ../data/trials/data.csv
    python manage.py ingest_trials ../data/trials/data.csv --limit 200
    python manage.py ingest_trials ../data/trials/data.csv --skip-vectors

Expected CSV columns (ClinicalTrials.gov Hackachusetts export):
    nct_id, title, phase, conditions, massachusetts_city, status

The command is idempotent: rows are upserted by nct_id in both stores, so it
can be re-run safely. Postgres is written first; vector indexing is best-effort
and, if ChromaDB/embeddings are unavailable, the Postgres data still lands and
the command reports that retrieval will stay unavailable until vectors exist.
"""
from __future__ import annotations

import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.engine.models import Trial
from apps.engine.services.retriever import get_retriever

REQUIRED_COLUMNS = {"nct_id", "title"}
BATCH_SIZE = 200


class Command(BaseCommand):
    help = "Ingest a clinical-trial CSV into PostgreSQL and ChromaDB."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to the trial CSV file.")
        parser.add_argument(
            "--limit", type=int, default=None,
            help="Only ingest the first N rows (useful for testing).",
        )
        parser.add_argument(
            "--skip-vectors", action="store_true",
            help="Load PostgreSQL only; skip ChromaDB embedding/indexing.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        limit = options["limit"]
        skip_vectors = options["skip_vectors"]

        rows = self._read_csv(csv_path, limit)
        if not rows:
            raise CommandError(f"No rows found in {csv_path}.")

        self.stdout.write(f"Read {len(rows)} row(s) from {csv_path}.")

        # 1. PostgreSQL: upsert full records.
        trials = self._upsert_postgres(rows)
        self.stdout.write(self.style.SUCCESS(
            f"PostgreSQL: {len(trials)} trial(s) upserted."
        ))

        # 2. ChromaDB: index searchable text (best-effort).
        if skip_vectors:
            self.stdout.write("Skipping vector indexing (--skip-vectors).")
            return

        indexed = self._index_vectors(trials)
        if indexed is None:
            self.stdout.write(self.style.WARNING(
                "ChromaDB unavailable (not installed or embedding failed). "
                "PostgreSQL data is loaded, but trial retrieval stays "
                "'unavailable' until vectors are indexed."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"ChromaDB: {indexed} document(s) indexed."
            ))

    # ------------------------------------------------------------------ #

    def _read_csv(self, csv_path: str, limit: int | None) -> list[dict]:
        try:
            with open(csv_path, newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
                if missing:
                    raise CommandError(
                        f"CSV is missing required column(s): {sorted(missing)}. "
                        f"Found: {reader.fieldnames}"
                    )
                rows = []
                for i, row in enumerate(reader):
                    if limit is not None and i >= limit:
                        break
                    if (row.get("nct_id") or "").strip():
                        rows.append(row)
                return rows
        except FileNotFoundError as exc:
            raise CommandError(f"File not found: {csv_path}") from exc

    @transaction.atomic
    def _upsert_postgres(self, rows: list[dict]) -> list[Trial]:
        trials: list[Trial] = []
        for row in rows:
            trial, _ = Trial.objects.update_or_create(
                nct_id=row["nct_id"].strip(),
                defaults={
                    "title": (row.get("title") or "").strip(),
                    "phase": (row.get("phase") or "").strip(),
                    "conditions": (row.get("conditions") or "").strip(),
                    "massachusetts_city": (
                        row.get("massachusetts_city") or ""
                    ).strip(),
                    "status": (row.get("status") or "").strip(),
                    "eligibility_criteria": (
                        row.get("eligibility_criteria") or ""
                    ).strip(),
                },
            )
            trials.append(trial)
        return trials

    def _index_vectors(self, trials: list[Trial]) -> int | None:
        retriever = get_retriever()
        total = 0
        try:
            for start in range(0, len(trials), BATCH_SIZE):
                batch = trials[start : start + BATCH_SIZE]
                ids = [t.nct_id for t in batch]
                documents = [t.embedding_text() or t.nct_id for t in batch]
                metadatas = [
                    {
                        "nct_id": t.nct_id,
                        "title": t.title,
                        "phase": t.phase,
                        "status": t.status,
                        "city": t.massachusetts_city,
                    }
                    for t in batch
                ]
                total += retriever.upsert(ids, documents, metadatas)
                self.stdout.write(f"  indexed {total}/{len(trials)}...")
            return total
        except Exception as exc:  # noqa: BLE001 - keep Postgres load intact
            self.stderr.write(f"Vector indexing error: {type(exc).__name__}: {exc}")
            return None
