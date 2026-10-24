"""
Result ranking.

Orders matched trials for presentation. Full ranking depends on eligibility
scores from ``ai_matcher`` (not available in Phase 1). As a safe interim
behavior, when retrieval is available we preserve the retriever's own distance
ordering; we never invent scores or eligibility.
"""
from __future__ import annotations


def rank(retrieved_results: list[dict], matches: list[dict] | None = None) -> list[dict]:
    """
    Return trials in presentation order.

    - If eligibility matches exist (future), they would drive ordering.
    - Otherwise fall back to the retriever's distance (ascending = closer).
    """
    if matches:
        # Placeholder for future eligibility-driven ordering.
        return matches

    def _distance(item: dict):
        d = item.get("distance")
        return d if isinstance(d, (int, float)) else float("inf")

    return sorted(retrieved_results or [], key=_distance)
