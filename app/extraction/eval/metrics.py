"""Eval metrics for the extraction module (ADR-009)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EvalRow:
    sample: str
    schema_valid: bool
    grounding_rate: float
    field_accuracy: dict[str, bool]


def field_accuracy(predicted: dict[str, Any], expected: dict[str, Any]) -> dict[str, bool]:
    """Per-field equality. Missing predicted fields count as wrong."""
    return {k: (predicted.get(k) == v) for k, v in expected.items()}


def grounding_rate(num_fields: int, num_grounded: int) -> float:
    return (num_grounded / num_fields) if num_fields else 0.0


def summarize(rows: list[EvalRow]) -> dict[str, Any]:
    if not rows:
        return {"samples": 0}
    schema_valid_pct = sum(1 for r in rows if r.schema_valid) / len(rows)
    grounding_avg = sum(r.grounding_rate for r in rows) / len(rows)
    field_totals: dict[str, list[bool]] = {}
    for r in rows:
        for k, v in r.field_accuracy.items():
            field_totals.setdefault(k, []).append(v)
    field_acc = {k: sum(v) / len(v) for k, v in field_totals.items()}
    return {
        "samples": len(rows),
        "schema_valid_rate": schema_valid_pct,
        "grounding_rate_avg": grounding_avg,
        "field_accuracy": field_acc,
    }
