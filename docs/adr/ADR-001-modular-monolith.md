# ADR-001 — Modular monolith, not microservices

**Status:** Accepted
**Date:** 2026-05-11

## Context

The platform has a small team, an early-stage product, and tight feedback loops with design partners. We need to ship features and iterate on data model and lifecycle without a distribution tax.

## Decision

We ship as a **modular monolith**: one FastAPI process, one deployment unit, one database. Internal modules (`app.ingestion`, `app.extraction`, etc.) have **strict boundaries enforced by `import-linter`** — no direct imports between domain modules.

## Consequences

- **Positive:** No service discovery, no inter-service auth, no per-service deploy pipelines. Refactors are atomic. New developers onboard in hours, not weeks.
- **Positive:** Module boundaries are real (`import-linter` is in CI), so the monolith can be peeled apart later without a rewrite.
- **Negative:** Single deploy footprint scales as one. We accept this until measured pressure says otherwise.
- **Negative:** A poorly disciplined team can erode internal boundaries; we mitigate with the linter.

## Alternatives considered

- **Microservices from day one.** Rejected: at this team size and traffic, the operational cost outweighs any theoretical scaling benefit.
- **Single flat package, no enforced boundaries.** Rejected: this is how monoliths become unmaintainable. The discipline is cheap; the regret is expensive.
