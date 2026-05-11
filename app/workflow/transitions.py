"""Named transition helpers used by API and tasks.

Each function is the *only* sanctioned way to perform that transition from
calling code. They wrap perform_transition() to provide typed args.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.auth import CurrentUser
from app.ingestion.models import Document
from app.workflow.state_machine import perform_transition


def parse_started(db: Session, doc: Document) -> Document:
    return perform_transition(db, doc, "parse_started", actor=None)


def parse_succeeded(db: Session, doc: Document, page_count: int) -> Document:
    return perform_transition(db, doc, "parse_succeeded", actor=None, payload={"page_count": page_count})


def extraction_started(db: Session, doc: Document, schema_id: str) -> Document:
    return perform_transition(db, doc, "extraction_started", actor=None, payload={"schema_id": schema_id})


def extraction_succeeded(db: Session, doc: Document, extraction_id: str) -> Document:
    return perform_transition(
        db, doc, "extraction_succeeded", actor=None, payload={"extraction_id": extraction_id}
    )


def review_opened(db: Session, doc: Document) -> Document:
    return perform_transition(db, doc, "review_opened", actor=None)


def approved(db: Session, doc: Document, actor: CurrentUser, reason: str | None = None) -> Document:
    payload: dict[str, Any] = {}
    if reason:
        payload["reason"] = reason
    return perform_transition(db, doc, "approved", actor=actor, payload=payload)


def routed(db: Session, doc: Document, destination: str) -> Document:
    return perform_transition(db, doc, "routed", actor=None, payload={"destination": destination})
