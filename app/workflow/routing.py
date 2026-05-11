"""Post-approval routing.

Subscribes to `document.approved` events; for the slice, logs the would-be
destination and emits `document.routed`. Real routing rules live here.
"""

from __future__ import annotations

import structlog

from app.common.events import DomainEvent, get_event_bus
from app.db import SessionLocal
from app.ingestion.models import Document
from app.workflow.transitions import routed

logger = structlog.get_logger(__name__)


def _on_approved(event: DomainEvent) -> None:
    document_id = event.payload["document_id"]
    logger.info("routing.approved_document", document_id=document_id, destination="printing")
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if doc is None:
            return
        routed(db, doc, destination="printing")
        db.commit()


def register_routing_subscribers() -> None:
    get_event_bus().subscribe("document.approved", _on_approved)
