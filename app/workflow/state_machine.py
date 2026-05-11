"""Document lifecycle state machine (ADR-004).

This is the spine of the platform. Every state change goes through this class.
No other code mutates `documents.current_state`.

Usage:
    lifecycle = DocumentLifecycle(document, actor=current_user)
    lifecycle.parse_started()
    lifecycle.parse_succeeded()
    ...
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from statemachine import State, StateMachine

from app.common.auth import CurrentUser, Role
from app.common.errors import InvalidTransition
from app.common.events import DomainEvent, get_event_bus
from app.ingestion.models import Document
from app.workflow.models import WorkflowTransition


@dataclass(frozen=True)
class TransitionContext:
    actor: CurrentUser | None
    payload: dict[str, Any]


class DocumentLifecycle(StateMachine):
    """All possible states and transitions for a Document.

    The set of allowed roles per transition is enforced by the API layer
    (via require_role); this class enforces that transitions happen in a
    legal order at all.
    """

    UPLOADED = State("UPLOADED", initial=True)
    PARSING = State("PARSING")
    PARSED = State("PARSED")
    PARSE_FAILED = State("PARSE_FAILED", final=True)
    EXTRACTING = State("EXTRACTING")
    EXTRACTED = State("EXTRACTED")
    EXTRACTION_FAILED = State("EXTRACTION_FAILED", final=True)
    IN_REVIEW = State("IN_REVIEW")
    NEEDS_REVISION = State("NEEDS_REVISION")
    APPROVED = State("APPROVED")
    ROUTED = State("ROUTED")
    PLAN_GENERATING = State("PLAN_GENERATING")
    PLAN_READY = State("PLAN_READY")
    PRINTED = State("PRINTED")
    ARCHIVED = State("ARCHIVED", final=True)

    parse_started = UPLOADED.to(PARSING)
    parse_succeeded = PARSING.to(PARSED)
    parse_failed = PARSING.to(PARSE_FAILED)

    extraction_started = PARSED.to(EXTRACTING)
    extraction_succeeded = EXTRACTING.to(EXTRACTED)
    extraction_failed = EXTRACTING.to(EXTRACTION_FAILED)

    review_opened = EXTRACTED.to(IN_REVIEW)
    changes_requested = IN_REVIEW.to(NEEDS_REVISION)
    revisions_submitted = NEEDS_REVISION.to(IN_REVIEW)
    approved = IN_REVIEW.to(APPROVED)

    routed = APPROVED.to(ROUTED)
    plan_generation_started = ROUTED.to(PLAN_GENERATING)
    plan_generation_succeeded = PLAN_GENERATING.to(PLAN_READY)
    printed = PLAN_READY.to(PRINTED)
    archived = PRINTED.to(ARCHIVED)

    # --- Allowed-roles map (the API layer enforces this; documented here) ---
    ALLOWED_ROLES: dict[str, frozenset[Role]] = {
        "parse_started": frozenset({Role.SYSTEM}),
        "parse_succeeded": frozenset({Role.SYSTEM}),
        "parse_failed": frozenset({Role.SYSTEM}),
        "extraction_started": frozenset({Role.SYSTEM}),
        "extraction_succeeded": frozenset({Role.SYSTEM}),
        "extraction_failed": frozenset({Role.SYSTEM}),
        "review_opened": frozenset({Role.SYSTEM, Role.REVIEWER}),
        "changes_requested": frozenset({Role.REVIEWER, Role.APPROVER}),
        "revisions_submitted": frozenset({Role.REVIEWER}),
        "approved": frozenset({Role.APPROVER}),
        "routed": frozenset({Role.SYSTEM}),
        "plan_generation_started": frozenset({Role.SYSTEM}),
        "plan_generation_succeeded": frozenset({Role.SYSTEM}),
        "printed": frozenset({Role.SYSTEM}),
        "archived": frozenset({Role.ADMIN, Role.SYSTEM}),
    }


def perform_transition(
    db: Session,
    document: Document,
    event_name: str,
    actor: CurrentUser | None,
    payload: dict[str, Any] | None = None,
) -> Document:
    """The single entry point for all state changes on a Document.

    1. Checks role guard.
    2. Drives the state machine (which validates legality).
    3. Writes a workflow_transitions row.
    4. Updates the documents.current_state projection.
    5. Publishes a DomainEvent on the bus.
    """
    payload = payload or {}
    allowed = DocumentLifecycle.ALLOWED_ROLES.get(event_name)
    if allowed is None:
        raise InvalidTransition(f"unknown transition: {event_name}")

    actor_roles = actor.roles if actor else frozenset({Role.SYSTEM})
    if not actor_roles.intersection(allowed):
        raise InvalidTransition(
            f"role {[r.value for r in actor_roles]} cannot perform {event_name}",
            allowed=[r.value for r in allowed],
        )

    machine = DocumentLifecycle(start_value=document.current_state)
    from_state = machine.current_state.id
    try:
        machine.send(event_name)
    except Exception as exc:  # statemachine raises generic exception types
        raise InvalidTransition(
            f"cannot {event_name} from {from_state}",
            from_state=from_state,
        ) from exc
    to_state = machine.current_state.id

    actor_id: UUID | None = actor.user_id if actor else None
    db.add(
        WorkflowTransition(
            document_id=document.id,
            from_state=from_state,
            to_state=to_state,
            actor_user_id=actor_id,
            event_name=event_name,
            event_payload=payload,
        )
    )
    document.current_state = to_state
    db.flush()

    get_event_bus().publish(
        DomainEvent(
            name=f"document.{event_name}",
            payload={
                "document_id": str(document.id),
                "from_state": from_state,
                "to_state": to_state,
                **payload,
            },
            actor_user_id=actor_id,
        )
    )
    return document
