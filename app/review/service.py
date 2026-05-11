from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.auth import CurrentUser
from app.common.errors import NotFound
from app.extraction.models import Extraction, ExtractionField
from app.ingestion.models import Document
from app.review.models import FieldEdit, ReviewRevision, ReviewSession
from app.workflow.transitions import approved as approve_doc


def open_or_get_session(db: Session, *, document_id: UUID, user: CurrentUser) -> ReviewSession:
    session = (
        db.query(ReviewSession)
        .filter(ReviewSession.document_id == document_id, ReviewSession.closed_at.is_(None))
        .first()
    )
    if session:
        return session
    session = ReviewSession(document_id=document_id, opened_by_user_id=user.user_id)
    db.add(session)
    db.flush()
    db.add(ReviewRevision(review_session_id=session.id))
    db.flush()
    return session


def edit_field(
    db: Session,
    *,
    document_id: UUID,
    extraction_field_id: UUID,
    new_value: Any,
    reason: str | None,
    user: CurrentUser,
) -> FieldEdit:
    session = open_or_get_session(db, document_id=document_id, user=user)
    revision = (
        db.query(ReviewRevision)
        .filter(ReviewRevision.review_session_id == session.id)
        .order_by(ReviewRevision.created_at.desc())
        .first()
    )
    if revision is None:
        raise NotFound("review revision not found", session_id=str(session.id))

    field = db.get(ExtractionField, extraction_field_id)
    if field is None:
        raise NotFound("extraction_field not found", extraction_field_id=str(extraction_field_id))

    edit = FieldEdit(
        review_revision_id=revision.id,
        extraction_field_id=field.id,
        previous_value=field.value,
        new_value=new_value,
        reason=reason,
    )
    db.add(edit)
    return edit


def approve(db: Session, *, document_id: UUID, user: CurrentUser, reason: str | None = None) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise NotFound("document not found", document_id=str(document_id))
    session = open_or_get_session(db, document_id=document_id, user=user)
    session.outcome = "approved"
    session.closed_at = datetime.now(timezone.utc)
    approve_doc(db, doc, actor=user, reason=reason)
    return doc


def latest_extraction(db: Session, document_id: UUID) -> Extraction | None:
    return (
        db.query(Extraction)
        .filter(Extraction.document_id == document_id)
        .order_by(Extraction.created_at.desc())
        .first()
    )
