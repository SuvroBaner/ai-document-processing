from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class ReviewSession(Base):
    __tablename__ = "review_sessions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    opened_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(String, nullable=True)  # approved | rejected | needs_revision

    revisions = relationship("ReviewRevision", back_populates="session", cascade="all, delete-orphan")


class ReviewRevision(Base):
    __tablename__ = "review_revisions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    review_session_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("review_sessions.id"), nullable=False, index=True
    )
    parent_revision_id = Column(PG_UUID(as_uuid=True), ForeignKey("review_revisions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("ReviewSession", back_populates="revisions")
    edits = relationship("FieldEdit", back_populates="revision", cascade="all, delete-orphan")


class FieldEdit(Base):
    __tablename__ = "field_edits"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    review_revision_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("review_revisions.id"), nullable=False, index=True
    )
    extraction_field_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("extraction_fields.id"), nullable=False, index=True
    )
    previous_value = Column(JSON, nullable=False)
    new_value = Column(JSON, nullable=False)
    reason = Column(String, nullable=True)

    revision = relationship("ReviewRevision", back_populates="edits")
