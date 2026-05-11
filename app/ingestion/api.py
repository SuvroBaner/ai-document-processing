from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.common.auth import CurrentUser, Role, require_role
from app.deps import db_session
from app.extraction.tasks import run_extraction_task
from app.ingestion.service import register_document

router = APIRouter()


@router.post("")
async def upload_document(
    project_id: UUID = Form(...),
    kind: str = Form("submittal"),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role(Role.UPLOADER, Role.ADMIN, Role.REVIEWER)),
    db: Session = Depends(db_session),
) -> dict:
    content = await file.read()
    doc = register_document(
        db,
        project_id=project_id,
        uploader_user_id=user.user_id,
        kind=kind,
        filename=file.filename or "document.pdf",
        content=content,
        content_type=file.content_type or "application/pdf",
    )
    db.commit()

    run_extraction_task.delay(str(doc.id), schema_id="submittal_v1")

    return {"id": str(doc.id), "current_state": doc.current_state}
