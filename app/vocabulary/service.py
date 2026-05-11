from __future__ import annotations

from sqlalchemy.orm import Session

from app.vocabulary.models import Vocabulary, VocabularyTerm, VocabularyVersion


def latest_version(db: Session, slug: str) -> VocabularyVersion | None:
    vocab = db.query(Vocabulary).filter(Vocabulary.slug == slug).first()
    if vocab is None:
        return None
    return (
        db.query(VocabularyVersion)
        .filter(VocabularyVersion.vocabulary_id == vocab.id)
        .order_by(VocabularyVersion.published_at.desc())
        .first()
    )


def list_terms(db: Session, *, version_id) -> list[VocabularyTerm]:
    return (
        db.query(VocabularyTerm)
        .filter(VocabularyTerm.vocabulary_version_id == version_id)
        .order_by(VocabularyTerm.code)
        .all()
    )
