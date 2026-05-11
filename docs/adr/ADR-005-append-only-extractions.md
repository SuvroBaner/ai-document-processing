# ADR-005 — Extractions are append-only and versioned

**Status:** Accepted
**Date:** 2026-05-11

## Context

Reviewers will edit extracted fields. We need to know what the LLM originally produced — for eval, for audit, and for prompt-improvement signal — separately from what the reviewer ultimately approved.

## Decision

- `extractions`, `extraction_fields`, `citations` are **append-only**.
- Reviewer edits do **not** mutate `extraction_fields`. They create rows in `field_edits`, which roll up under a `review_revision`.
- A document can have multiple `extractions` over time (e.g., re-extraction after a prompt change). Each is identified by `(schema_version, prompt_version, model, model_version)`.

The "current" view of a document's data is a projection: the latest extraction's fields, with reviewer edits overlaid in order.

## Consequences

- **Positive:** We can always recover the raw LLM output. We can compute reviewer edit distance as a quality signal.
- **Positive:** Prompt and model changes are auditable — we know which extraction came from which prompt version.
- **Negative:** Queries for "the current value of field X" go through a projection, not a column. We pay a small query cost. We accept this.

## Alternatives considered

- **Mutate in place.** Rejected: loses the raw LLM signal forever.
- **Soft-delete with `replaced_by` pointers.** Rejected: more complex, no real benefit over append-only.
