# ADR-004 — Document lifecycle is an explicit state machine

**Status:** Accepted
**Date:** 2026-05-11

## Context

The document lifecycle is the most complex moving part of the platform: many states, many actors (System, Reviewer, Approver), many transitions, regulated audit needs. Modeling this as `status` strings or `is_*` booleans scattered across handlers is the single most common way platforms in this shape become unmaintainable.

## Decision

The document lifecycle is a **first-class state machine**:

- Implemented with [`python-statemachine`](https://github.com/fgmacedo/python-statemachine).
- One `DocumentLifecycle` class. States and transitions are enumerated and explicit.
- Every transition has a **role guard** — `Reviewer`, `Approver`, or `System`.
- Every transition emits a typed `DomainEvent` on the `EventBus`.
- Every transition writes a row to `workflow_transitions` (append-only).
- The denormalized `documents.current_state` column is the projection of the latest transition. It is updated only by the state machine.

No code outside the state machine sets `current_state`. There is no path where `current_state` can disagree with the `workflow_transitions` log.

## Consequences

- **Positive:** Every state change is observable, audited, and tested.
- **Positive:** Adding a state or transition is a localized change — one file, one test.
- **Positive:** Forbidden transitions raise typed errors at the call site.
- **Negative:** Adds a dependency. Mitigated by the library being small and stable.

## Alternatives considered

- **Status strings + business logic in handlers.** Rejected: this is what we're trying to avoid.
- **Workflow engine (Temporal, Airflow, Camunda).** Rejected for now: heavyweight for our scale. The state machine pattern is enough; we can promote to Temporal if and when long-running, externally-coordinated workflows become a thing.

## Related

- `app/workflow/state_machine.py` — the implementation.
- `tests/test_state_machine.py` — exhaustive transition coverage.
