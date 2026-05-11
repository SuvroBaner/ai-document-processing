# ADR-003 — Citations are first-class, non-optional

**Status:** Accepted
**Date:** 2026-05-11

## Context

In a regulated industry, extracted data without verifiable provenance is a liability. Reviewers need to see *where* a value came from on the page. Auditors need to be able to ask the question six months later. Quotes that look right but can't be re-grounded to the source page are worse than no quotes at all.

## Decision

Every `ExtractionField` carries a non-empty list of `Citation` objects:

```python
class Citation(BaseModel):
    page: int
    bbox: tuple[float, float, float, float]
    source_text: str
```

- The database FK from `citations` to `extraction_fields` is `NOT NULL`.
- The service layer rejects an `ExtractionField` with zero citations as a schema violation, not a low-confidence warning.
- At extraction time, every returned `source_text` is **grounded** against the indexed page tokens captured during PDF parsing. If grounding fails (edit distance threshold exceeded), the field is retried, then dropped.

The grounding step is what makes citations *verifiable* rather than *plausible*.

## Consequences

- **Positive:** UI can highlight citations on the original PDF with confidence.
- **Positive:** Audit trail is grounded in the document, not the model's recall.
- **Positive:** Reviewer trust compounds: the system is honest about what it knows.
- **Negative:** Some fields will be extracted but not citable (e.g., inferred values). We expose this as a separate `inferred=True` field type for v2; for v1, the extraction simply doesn't return them.

## Alternatives considered

- **Treat citations as "nice to have" with optional fields.** Rejected: in a regulated industry, optional becomes "not there in 30% of records."
- **Store quotes without bboxes.** Rejected: the UI can't render them, and the auditor can't verify.
