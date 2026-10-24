"""
Clinical-trial retrieval from ChromaDB.

Uses ChromaDB in LOCAL persistent-client mode (not the networked server, which
has a known multi-tenant authorization CVE). The collection is populated by a
separate ingestion step (out of scope for Phase 1), so when the persist dir or
collection is absent, retrieval reports itself unavailable and returns no
results — it never fabricates trials.
"""
from __future__ import annotations

import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


class TrialRetriever:
    """Semantic retrieval over a local ChromaDB collection."""

    def __init__(self) -> None:
        cfg = getattr(settings, "ENGINE", {})
        self._persist_dir: str = cfg.get("CHROMA_PERSIST_DIR") or ".chroma"
        self._collection_name: str = cfg.get("CHROMA_COLLECTION") or "clinical_trials"
        self._collection = None
        self._checked = False

    def _load_collection(self):
        """Attempt to open the persisted collection; cache the result."""
        if self._checked:
            return self._collection
        self._checked = True

        # Only attempt if a persisted store actually exists on disk.
        if not os.path.isdir(self._persist_dir):
            logger.info("Chroma persist dir %s absent; retrieval unavailable.",
                        self._persist_dir)
            return None
        try:
            import chromadb

            client = chromadb.PersistentClient(path=self._persist_dir)
            self._collection = client.get_collection(self._collection_name)
        except Exception:  # noqa: BLE001 - missing collection => unavailable
            logger.info("Chroma collection '%s' not available.",
                        self._collection_name)
            self._collection = None
        return self._collection

    def available(self) -> bool:
        return self._load_collection() is not None

    def retrieve(self, query_text: str, n_results: int = 10) -> dict:
        """
        Return ``{"available": bool, "results": [...]}``.

        Results are raw trial references (ids + metadata) for the matching
        stage; full trial info is later joined from PostgreSQL. When the store
        is absent, results is empty and available is False.
        """
        collection = self._load_collection()
        if collection is None or not (query_text or "").strip():
            return {"available": False, "results": []}
        try:
            raw = collection.query(query_texts=[query_text], n_results=n_results)
        except Exception:  # noqa: BLE001
            logger.exception("Chroma query failed; returning no results.")
            return {"available": False, "results": []}

        ids = (raw.get("ids") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        results = [
            {
                "trial_id": ids[i] if i < len(ids) else None,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
            }
            for i in range(len(ids))
        ]
        return {"available": True, "results": results}


_retriever: TrialRetriever | None = None


def get_retriever() -> TrialRetriever:
    global _retriever
    if _retriever is None:
        _retriever = TrialRetriever()
    return _retriever


def build_query_text(normalized_profile: dict) -> str:
    """Compose a retrieval query string from a normalized profile."""
    parts: list[str] = []
    if normalized_profile.get("primary_condition"):
        parts.append(normalized_profile["primary_condition"])
    for fact in normalized_profile.get("conditions", []):
        value = fact.get("value") if isinstance(fact, dict) else fact
        if value:
            parts.append(str(value))
    for fact in normalized_profile.get("symptoms", []):
        value = fact.get("value") if isinstance(fact, dict) else fact
        if value:
            parts.append(str(value))
    # De-dupe while preserving order.
    seen: set[str] = set()
    ordered = []
    for p in parts:
        k = p.strip().lower()
        if k and k not in seen:
            seen.add(k)
            ordered.append(p)
    return ", ".join(ordered)
