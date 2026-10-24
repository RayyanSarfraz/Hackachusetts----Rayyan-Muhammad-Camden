"""
Model client.

Thin wrapper around the fine-tuned Qwen model served via vLLM, which exposes an
OpenAI-compatible ``/v1`` endpoint. We talk to it through LangChain's
``ChatOpenAI`` (from ``langchain-openai``).

The model is OPTIONAL. When ``MODEL_API_BASE_URL`` is not configured, the client
reports ``available() == False`` and callers must degrade gracefully — never
fabricate medical facts.
"""
from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class ModelClient:
    """Lazily-constructed chat client for the vLLM-hosted model."""

    def __init__(self) -> None:
        cfg = getattr(settings, "ENGINE", {})
        self._base_url: str = (cfg.get("MODEL_API_BASE_URL") or "").strip()
        self._api_key: str = cfg.get("MODEL_API_KEY") or "not-needed"
        self._model_name: str = cfg.get("MODEL_NAME") or "qwen"
        self._llm = None

    def available(self) -> bool:
        """True only when a model endpoint is configured."""
        return bool(self._base_url)

    def _get_llm(self):
        if self._llm is not None:
            return self._llm
        # Import lazily so the app boots even if langchain-openai is absent.
        from langchain_openai import ChatOpenAI

        self._llm = ChatOpenAI(
            model=self._model_name,
            base_url=self._base_url,
            api_key=self._api_key,
            temperature=0,
            timeout=30,
            max_retries=1,
        )
        return self._llm

    def chat(self, system_prompt: str, user_content: str) -> str | None:
        """
        Send a single-turn prompt and return the raw text response.

        Returns None (and logs) if the model is unavailable or the call fails,
        so callers can fall back to an "unknown/unavailable" result.
        """
        if not self.available():
            return None
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = self._get_llm()
            response = llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_content),
                ]
            )
            return getattr(response, "content", None)
        except Exception:  # noqa: BLE001 - never let model errors crash intake
            logger.exception("Model call failed; treating model as unavailable.")
            return None


_client: ModelClient | None = None


def get_model_client() -> ModelClient:
    """Return a process-wide ModelClient instance."""
    global _client
    if _client is None:
        _client = ModelClient()
    return _client
