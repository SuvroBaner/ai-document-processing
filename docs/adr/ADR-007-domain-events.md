# ADR-007 — Domain events on every meaningful transition

**Status:** Accepted
**Date:** 2026-05-11

## Context

Audit, analytics, downstream integrations, notifications — all of these need to know "something happened." Polling the DB for changes is the wrong shape. Direct cross-module function calls couple modules together.

## Decision

- Every meaningful business event is a typed `DomainEvent` published to an `EventBus`.
- Subscribers (audit logger, future notifiers, integrations) listen on the bus.
- The bus is **in-process pub/sub today** (a simple synchronous dispatcher in `app/common/events.py`).
- The bus is intentionally swappable for **Redis Streams** when we need cross-process subscribers; the publishing API does not change.

## Consequences

- **Positive:** Modules emit events; they don't know who listens. Pure decoupling.
- **Positive:** Audit log is a subscriber, not a coordinated write. No "I forgot to log this" bugs.
- **Positive:** Adding new integrations (Slack notification, email, webhook) is a new subscriber, zero changes to publishers.
- **Negative:** Synchronous in-proc dispatcher means a slow subscriber can slow the publisher. We mitigate by keeping subscribers thin (write a row, enqueue a task) and by moving to async dispatch when needed.

## Alternatives considered

- **Kafka / NATS from day one.** Rejected: premature.
- **Direct function calls.** Rejected: this is the coupling we're trying to avoid.
