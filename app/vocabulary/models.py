from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Vocabulary(Base):
    __tablename__ = "vocabularies"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    slug = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=False)

    versions = relationship("VocabularyVersion", back_populates="vocabulary", cascade="all, delete-orphan")


class VocabularyVersion(Base):
    """Immutable snapshot of a vocabulary (ADR-006)."""

    __tablename__ = "vocabulary_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    vocabulary_id = Column(PG_UUID(as_uuid=True), ForeignKey("vocabularies.id"), nullable=False, index=True)
    version_label = Column(String, nullable=False)
    published_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    vocabulary = relationship("Vocabulary", back_populates="versions")
    terms = relationship("VocabularyTerm", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("vocabulary_id", "version_label"),)


class VocabularyTerm(Base):
    """Immutable; a change creates a new VocabularyVersion."""

    __tablename__ = "vocabulary_terms"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    vocabulary_version_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("vocabulary_versions.id"), nullable=False, index=True
    )
    parent_term_id = Column(PG_UUID(as_uuid=True), ForeignKey("vocabulary_terms.id"), nullable=True)
    code = Column(String, nullable=False)
    label = Column(String, nullable=False)

    version = relationship("VocabularyVersion", back_populates="terms")

    __table_args__ = (UniqueConstraint("vocabulary_version_id", "code"),)
