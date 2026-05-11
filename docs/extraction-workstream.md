# The AI Extraction Workstream

This is the standalone scoping document for the AI/ML engineer who will own extraction. It defines the interface they cannot break, the surface area they own, the deployment options as the workstream scales, and the quality bar.

## 1. Mission

> Given a parsed document and a target schema, return structured fields with grounded citations, at a measurable quality bar, within a versioned and reproducible system.

## 2. Interface (the contract)

The platform calls extraction through exactly one entry point:

```python
# app/extraction/__init__.py
from app.extraction.service import (
    ExtractionService,
    ExtractionRequest,
    ExtractionResult,
    ExtractionField,
    Citation,
)
```

```python
class ExtractionRequest(BaseModel):
    document_id: UUID
    schema_id: str                      # registered schema, e.g. "submittal_v1"
    page_range: tuple[int, int] | None  # optional sub-range
    prompt_version: str | None          # pin for reproducibility; default = latest


class Citation(BaseModel):
    page: int
    bbox: tuple[float, float, float, float]
    source_text: str


class ExtractionField(BaseModel):
    field_path: str          # JSON pointer, e.g. "/manufacturer"
    value: Any
    confidence: float        # 0..1
    citations: list[Citation]  # MUST be non-empty


class ExtractionResult(BaseModel):
    extraction_id: UUID
    schema_id: str
    schema_version: str
    model: str
    model_version: str
    prompt_version: str
    fields: list[ExtractionField]
    raw_response: dict       # archived verbatim
```

**The AI/ML engineer can change anything inside the module.** They cannot change the shape of `ExtractionRequest` or `ExtractionResult` without an ADR.

## 3. Owned surface area

| Path | What lives here |
|---|---|
| `app/extraction/schemas/` | JSON Schemas per document type. Versioned filenames (`submittal_v1.json`). |
| `app/extraction/prompts/` | Jinja2 templates. Filename is the version (`submittal_v1.jinja`). |
| `app/extraction/llm/` | `LLMClient` Protocol + concrete clients (OpenAI today). |
| `app/extraction/llm/citation_grounder.py` | Maps verbatim quotes back to page+bbox. |
| `app/extraction/service.py` | Orchestrates: schema load → prompt render → LLM call → validate → ground → persist. |
| `app/extraction/tasks.py` | Celery entry point. |
| `app/extraction/eval/` | Golden-set runner, metrics, fixtures. |

Nothing else. The AI/ML engineer does not need to touch the API layer, the data model, the UI, or the workflow state machine to do their job.

## 4. Deployment posture

A slider, not a one-way door. Same code, different runtime.

| Stage | Trigger | Runtime |
|---|---|---|
| **Stage 1 — In-proc worker** *(today)* | Volumes low; ops cost matters most | Celery worker in the same container family |
| **Stage 2 — Dedicated pool** | Extraction CPU/latency dominates the worker tier | Separate Celery queue + dedicated worker pool; same image |
| **Stage 3 — Standalone service** | Need different release cadence, GPU, or different scaling profile | gRPC / FastAPI service in its own image. Callsites unchanged — they still call `ExtractionService.run(req)`; only the binding is swapped. |

The interface is the same at every stage. We will not refactor application code to ship Stage 3.

## 5. Quality measurement — non-negotiable

The eval harness lives in `app/extraction/eval/`. It runs on every PR (non-blocking initially) and on a nightly schedule (blocking).

### Metrics

| Metric | Definition | Target (initial) |
|---|---|---|
| Schema validity | % of LLM responses that pass JSON Schema validation on first attempt | ≥ 95% |
| Citation grounding | % of returned `source_text` quotes that match indexed page tokens with edit distance ≤ 3 | ≥ 90% |
| Field accuracy (golden set) | Per-field equality against `*.expected.json` | ≥ 90% on top-10 fields |
| Reviewer edit distance | Median number of fields edited in `review_revisions` per approved document | ≤ 2 |

### Golden set lifecycle

- New samples are added to `app/extraction/eval/golden/` as PRs from operators or customer-facing PMs.
- Each sample is `{name}.pdf` + `{name}.expected.json`.
- Removing a sample requires an ADR (or at minimum a recorded reason in the PR description).

## 6. What the AI/ML engineer is *not* responsible for

- The UI's display of confidence or citations.
- The state machine that decides when extraction is invoked.
- Auth and tenancy.
- The data model outside `app/extraction/models.py`.
- Picking the cloud provider.

Bringing this clarity to the role is what separates a productive AI engineering hire from a productive AI engineering hire who is constantly blocked on cross-team coordination.

## 7. Reproducibility

Every `ExtractionResult` is keyed by `(schema_version, prompt_version, model, model_version)`. Re-running an extraction with the same key on the same document must produce the same result modulo LLM nondeterminism (which is why temperature defaults to `0.0`). The `raw_response` field is archived so debugging can re-examine the model output without re-paying for the call.

## 8. Future extensions where an agent harness enters

See [ADR-010](./adr/ADR-010-no-agent-framework.md). Briefly: RFI response drafting, multi-document submittal package assembly, drawing/spec cross-referencing, permit-package preflight against AHJ rules. Each is a new sub-module, not a refactor of `ExtractionService`.
