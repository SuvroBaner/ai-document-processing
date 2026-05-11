from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.common.auth import CurrentUser, Role, require_role
from app.common.errors import NotFound
from app.common.storage import get_storage
from app.deps import db_session
from app.extraction.models import Citation, ExtractionField
from app.ingestion.models import Document
from app.review.service import approve, edit_field, latest_extraction

router = APIRouter()


@router.get("/queue")
def queue(
    _user: CurrentUser = Depends(require_role(Role.REVIEWER, Role.APPROVER, Role.ADMIN)),
    db: Session = Depends(db_session),
) -> list[dict]:
    docs = (
        db.query(Document)
        .filter(Document.current_state.in_(["IN_REVIEW", "NEEDS_REVISION"]))
        .order_by(Document.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(d.id),
            "filename": d.original_filename,
            "kind": d.kind,
            "state": d.current_state,
        }
        for d in docs
    ]


@router.get("/{document_id}")
def get_review(
    document_id: UUID,
    _user: CurrentUser = Depends(require_role(Role.REVIEWER, Role.APPROVER, Role.ADMIN, Role.VIEWER)),
    db: Session = Depends(db_session),
) -> dict:
    doc = db.get(Document, document_id)
    if doc is None:
        raise NotFound("document not found", document_id=str(document_id))
    extraction = latest_extraction(db, document_id)
    fields_out: list[dict] = []
    if extraction:
        fields = db.query(ExtractionField).filter(ExtractionField.extraction_id == extraction.id).all()
        for f in fields:
            cits = db.query(Citation).filter(Citation.extraction_field_id == f.id).all()
            fields_out.append(
                {
                    "id": str(f.id),
                    "field_path": f.field_path,
                    "value": f.value,
                    "confidence": f.confidence,
                    "citations": [
                        {"page": c.page, "bbox": c.bbox, "source_text": c.source_text}
                        for c in cits
                    ],
                }
            )
    return {
        "document": {
            "id": str(doc.id),
            "filename": doc.original_filename,
            "state": doc.current_state,
            "pdf_url": get_storage().presigned_get(doc.storage_key),
        },
        "extraction": (
            {
                "id": str(extraction.id),
                "schema_id": extraction.schema_id,
                "fields": fields_out,
            }
            if extraction
            else None
        ),
    }


class EditFieldBody(BaseModel):
    new_value: Any
    reason: str | None = None


@router.patch("/{document_id}/fields/{extraction_field_id}")
def patch_field(
    document_id: UUID,
    extraction_field_id: UUID,
    body: EditFieldBody,
    user: CurrentUser = Depends(require_role(Role.REVIEWER, Role.APPROVER)),
    db: Session = Depends(db_session),
) -> dict:
    edit = edit_field(
        db,
        document_id=document_id,
        extraction_field_id=extraction_field_id,
        new_value=body.new_value,
        reason=body.reason,
        user=user,
    )
    db.commit()
    return {"id": str(edit.id), "previous_value": edit.previous_value, "new_value": edit.new_value}


class ApproveBody(BaseModel):
    reason: str | None = None


@router.post("/{document_id}/approve")
def post_approve(
    document_id: UUID,
    body: ApproveBody | None = None,
    user: CurrentUser = Depends(require_role(Role.APPROVER)),
    db: Session = Depends(db_session),
) -> dict:
    doc = approve(db, document_id=document_id, user=user, reason=(body.reason if body else None))
    db.commit()
    return {"id": str(doc.id), "current_state": doc.current_state}
