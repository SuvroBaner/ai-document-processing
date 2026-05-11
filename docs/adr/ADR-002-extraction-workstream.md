# ADR-002 — Extraction is a separable workstream

**Status:** Accepted
**Date:** 2026-05-11

## Context

The AI extraction module has a different release cadence, a different quality measurement story, and a different specialist owner (the AI/ML hire). If it's entangled with the rest of the codebase, ownership becomes ambiguous and changes ripple across team boundaries.

## Decision

The extraction module has a **single Python interface** that the rest of the system depends on:

```python
class ExtractionService:
    def run(self, req: ExtractionRequest) -> ExtractionResult: ...
```

Inside the module, the AI/ML engineer owns schemas, prompts, the `LLMClient`, citation grounding, and the eval harness. **Outside the module, nothing knows how extraction works.**

The module is deployable today as a Celery worker in the same process family. The same code can be moved to a dedicated worker pool, then to a standalone service (gRPC), without callsite changes.

## Consequences

- **Positive:** AI/ML engineer has a clean lane. PR ownership is unambiguous.
- **Positive:** Implementation can change drastically (different model, different provider, different chunking strategy) without coordination.
- **Positive:** The deployment posture is a slider, not a one-way door.
- **Negative:** The interface needs to be designed carefully; changing it later is expensive.

## Alternatives considered

- **Embed LLM calls anywhere they're needed.** Rejected: explodes the surface area of prompt/model changes.
- **Microservice from day one.** Rejected: deferred to Stage 3 in `docs/extraction-workstream.md`. The interface is the durable artifact, not the deployment shape.

## Related

- [`docs/extraction-workstream.md`](../extraction-workstream.md) — the full scoping document.
- [`docs/hiring-rubric-ai-ml.md`](../hiring-rubric-ai-ml.md) — how to hire for this seat.
