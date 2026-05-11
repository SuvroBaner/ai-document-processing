from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import db_session
from app.vocabulary.service import latest_version, list_terms

router = APIRouter()


@router.get("/{slug}/latest")
def latest(slug: str, db: Session = Depends(db_session)) -> dict:
    v = latest_version(db, slug)
    if v is None:
        raise HTTPException(status_code=404, detail=f"vocabulary '{slug}' not found")
    return {
        "vocabulary_slug": slug,
        "version_id": str(v.id),
        "version_label": v.version_label,
        "terms": [{"code": t.code, "label": t.label} for t in list_terms(db, version_id=v.id)],
    }
