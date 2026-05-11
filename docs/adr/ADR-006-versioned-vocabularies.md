# ADR-006 — Controlled vocabularies are versioned and snapshotted at point of use

**Status:** Accepted
**Date:** 2026-05-11

## Context

Construction is governed by controlled vocabularies (CSI MasterFormat, permit-type codes, jurisdiction-specific schedules) that evolve over time. A submittal approved against the 2020 revision of CSI must remain interpretable when the 2024 revision lands — including the case where a code was renamed, moved, or split.

## Decision

- `vocabularies` are versioned. Each version is **immutable**.
- `vocabulary_terms` belong to a specific version; they are never updated.
- When a record references a vocab term, it stores both `term_id` and `vocabulary_version_id`.
- The UI labels vocab values with their version when there is more than one in the system.

Adding or changing a term creates a new version. The previous version remains valid for historical records.

## Consequences

- **Positive:** Historical records remain interpretable regardless of vocab evolution.
- **Positive:** Migrating between versions is an explicit, opt-in operation per record.
- **Negative:** Vocab table grows over time. Acceptable; vocabs are small.

## Alternatives considered

- **Single mutable vocabulary table.** Rejected: silent historical drift.
- **Versioned table with soft-update.** Rejected: harder to reason about than full snapshots.
