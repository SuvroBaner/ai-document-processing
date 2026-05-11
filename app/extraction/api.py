from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.auth import CurrentUser, Role, require_role
from app.common.errors import NotFound
from app.deps import db_session
from app.extraction.models import Citation, Extraction, ExtractionField

router = APIRouter()


@router.get("/{extraction_id}")
def get_extraction(
    extraction_id: UUID,
    _user: CurrentUser = Depends(require_role(Role.REVIEWER, Role.APPROVER, Role.ADMIN, Role.VIEWER)),
    db: Session = Depends(db_session),
) -> dict:
    ext = db.get(Extraction, extraction_id)
    if ext is None:
        raise NotFound("extraction not found", extraction_id=str(extraction_id))

    fields = db.query(ExtractionField).filter(ExtractionField.extraction_id == ext.id).all()
    out_fields = []
    for f in fields:
        citations = db.query(Citation).filter(Citation.extraction_field_id == f.id).all()
        out_fields.append(
            {
                "id": str(f.id),
                "field_path": f.field_path,
                "value": f.value,
                "confidence": f.confidence,
                "citations": [
                    {"page": c.page, "bbox": c.bbox, "source_text": c.source_text}
                    for c in citations
                ],
            }
        )

    return {
        "id": str(ext.id),
        "document_id": str(ext.document_id),
        "schema_id": ext.schema_id,
        "schema_version": ext.schema_version,
        "prompt_version": ext.prompt_version,
        "model": ext.model,
        "model_version": ext.model_version,
        "fields": out_fields,
    }
