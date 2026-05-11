# ADR-009 — Quality is measured, not hoped for

**Status:** Accepted
**Date:** 2026-05-11

## Context

LLM-driven systems regress silently. A prompt edit "feels better" but degrades a tail case. A model upgrade improves accuracy on common fields but hurts a critical rare one. Without measurement, we will not see this until customers do.

## Decision

The extraction module ships with an **eval harness** in `app/extraction/eval/`:

- **Golden set:** `*.pdf` + `*.expected.json` fixtures, version-controlled.
- **Metrics:** schema validity rate, citation grounding rate, field accuracy, reviewer edit distance.
- **Runner:** invoked via `make eval` and on CI.
- **Reporting:** generates a Markdown report and JSON artifact; the JSON is uploaded as a CI artifact.

Initially, CI reports the result but **does not block merges**. We collect baseline data first. After 4–6 weeks of data, we set thresholds; regressions then block.

## Consequences

- **Positive:** Prompt and model changes have a measurable consequence.
- **Positive:** A reviewer-edit signal closes the loop from production back to eval.
- **Negative:** Maintaining the golden set is real work. We make this part of the AI/ML role (see `hiring-rubric-ai-ml.md`).

## Alternatives considered

- **Vibe-based prompt iteration.** Rejected; that's the failure mode we're guarding against.
- **Third-party eval platform (Braintrust, Promptfoo).** Considered. Acceptable later if it earns its keep; for now, a thin home-grown harness is a few hundred lines and we own it.
