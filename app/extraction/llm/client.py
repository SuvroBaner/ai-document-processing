"""LLMClient Protocol — the provider-agnostic seam (ADR-008).

Concrete implementations live in sibling modules (openai_client.py).
Tests inject a stub.
"""

from __future__ import annotations

from typing import Any, Protocol


class StructuredOutput(dict[str, Any]):
    """Bag-of-fields JSON returned by the model. Schema validation happens
    in ExtractionService, not here."""


class LLMClient(Protocol):
    def extract_structured(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        model: str | None = None,
    ) -> tuple[StructuredOutput, dict[str, Any]]:
        """Returns (parsed_output, raw_response_metadata).

        The raw metadata is archived verbatim on Extraction.raw_response
        for reproducibility and debugging.
        """
        ...
