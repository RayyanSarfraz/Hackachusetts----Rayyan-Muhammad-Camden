import uuid

from django.db import models


class Trial(models.Model):
    """
    A clinical trial record (source of truth in PostgreSQL).

    ChromaDB holds the searchable text + embedding keyed by ``nct_id``; this
    table holds the full structured record. Retrieval returns ``nct_id``s from
    Chroma, which are then joined back to these rows for display.

    The primary key is an internal UUID; ``nct_id`` remains the public business
    key that ChromaDB and the frontend use.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nct_id = models.CharField(max_length=20, unique=True, db_index=True)
    title = models.TextField(blank=True)
    phase = models.CharField(max_length=120, blank=True)
    # Comma/semicolon-separated condition list as stored in the source dataset.
    conditions = models.TextField(blank=True)
    massachusetts_city = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=60, blank=True)

    # Optional richer fields a future fetch could populate (not in the base CSV).
    eligibility_criteria = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nct_id",)
        verbose_name = "trial"
        verbose_name_plural = "trials"

    def __str__(self):
        return f"{self.nct_id}: {self.title[:60]}"

    @property
    def condition_list(self) -> list[str]:
        """Split the stored conditions string into a clean list."""
        raw = self.conditions or ""
        parts = [p.strip() for p in raw.replace(";", ",").split(",")]
        return [p for p in parts if p]

    def embedding_text(self) -> str:
        """Text indexed into ChromaDB for semantic retrieval."""
        pieces = [self.title]
        if self.conditions:
            pieces.append(f"Conditions: {self.conditions}")
        if self.eligibility_criteria:
            pieces.append(f"Eligibility: {self.eligibility_criteria}")
        return ". ".join(p for p in pieces if p)
