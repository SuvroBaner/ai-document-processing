"""Celery entry point for extraction.

This is the only module other code calls to trigger extraction asynchronously.
The Celery binding is an implementation detail — the durable interface is
ExtractionService.run() in service.py.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from celery import Celery

from app.config import get_settings
from app.db import SessionLocal
from app.extraction.llm.openai_client import OpenAIClient
from app.extraction.service import ExtractionRequest, ExtractionService
from app.ingestion.models import Document
from app.ingestion.service import parse_document
from app.workflow.transitions import (
    extraction_started,
    extraction_succeeded,
    review_opened,
)

logger = structlog.get_logger(__name__)

_settings = get_settings()
celery_app = Celery(
    "aidocs",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
)


@celery_app.task(name="aidocs.run_extraction")
def run_extraction_task(document_id: str, schema_id: str = "submittal_v1") -> dict:
    doc_uuid = UUID(document_id)
    with SessionLocal() as db:
        doc = db.get(Document, doc_uuid)
        if doc is None:
            return {"ok": False, "reason": "document not found"}

        # Parse first if needed (UPLOADED → PARSING → PARSED).
        if doc.current_state == "UPLOADED":
            parse_document(db, doc_uuid)
            db.commit()
            doc = db.get(Document, doc_uuid)

        if doc.current_state != "PARSED":
            return {"ok": False, "reason": f"not in PARSED state (was {doc.current_state})"}

        extraction_started(db, doc, schema_id=schema_id)
        db.commit()

        try:
            svc = ExtractionService(llm=OpenAIClient())
            result = svc.run(db, ExtractionRequest(document_id=doc_uuid, schema_id=schema_id))
        except Exception as exc:
            logger.exception("extraction.failed", document_id=document_id)
            from app.workflow.state_machine import perform_transition
            perform_transition(db, doc, "extraction_failed", actor=None, payload={"error": str(exc)})
            db.commit()
            raise

        extraction_succeeded(db, doc, extraction_id=str(result.extraction_id))
        review_opened(db, doc)
        db.commit()
        return {"ok": True, "extraction_id": str(result.extraction_id)}
