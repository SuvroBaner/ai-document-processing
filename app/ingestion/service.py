from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.common.errors import NotFound
from app.common.storage import get_storage
from app.ingestion.models import Document, DocumentPage
from app.ingestion.pdf_parser import parse_pdf
from app.workflow.transitions import parse_started, parse_succeeded


def register_document(
    db: Session,
    *,
    project_id: UUID,
    uploader_user_id: UUID,
    kind: str,
    filename: str,
    content: bytes,
    content_type: str = "application/pdf",
) -> Document:
    storage_key = f"documents/{uuid4()}/{filename}"
    get_storage().put(storage_key, content, content_type=content_type)
    doc = Document(
        project_id=project_id,
        uploader_user_id=uploader_user_id,
        kind=kind,
        storage_key=storage_key,
        original_filename=filename,
        current_state="UPLOADED",
    )
    db.add(doc)
    db.flush()
    return doc


def parse_document(db: Session, document_id: UUID) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise NotFound("document not found", document_id=str(document_id))
    parse_started(db, doc)
    pdf_bytes = get_storage().get(doc.storage_key)
    parsed = parse_pdf(pdf_bytes)
    for page in parsed:
        db.add(DocumentPage(document_id=doc.id, **page.to_db()))
    parse_succeeded(db, doc, page_count=len(parsed))
    return doc
