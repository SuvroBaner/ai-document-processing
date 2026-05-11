from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.extraction.llm.client import StructuredOutput


class OpenAIClient:
    """Default LLMClient. Uses OpenAI structured outputs (response_format=json_object)."""

    def __init__(self, client: OpenAI | None = None) -> None:
        settings = get_settings()
        self._client = client or OpenAI(api_key=settings.openai_api_key)
        self._default_model = settings.llm_model
        self._temperature = settings.llm_temperature

    def extract_structured(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],  # noqa: ARG002 — schema is enforced post-hoc in service.py
        model: str | None = None,
    ) -> tuple[StructuredOutput, dict[str, Any]]:
        used_model = model or self._default_model
        completion = self._client.chat.completions.create(
            model=used_model,
            temperature=self._temperature,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Return only JSON matching the requested shape. Cite verbatim quotes.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = completion.choices[0].message.content or "{}"
        parsed: dict[str, Any] = json.loads(content)
        meta = {
            "model": used_model,
            "model_version": completion.model,
            "usage": completion.usage.model_dump() if completion.usage else None,
            "id": completion.id,
        }
        return StructuredOutput(parsed), meta
