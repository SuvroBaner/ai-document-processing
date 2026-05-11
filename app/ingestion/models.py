from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    uploader_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    kind = Column(String, nullable=False)        # submittal | rfi | spec | drawing | contract
    storage_key = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)

    # Denormalized projection of the latest workflow_transitions.to_state.
    # Only the state machine writes to this column (ADR-004).
    current_state = Column(String, nullable=False, default="UPLOADED")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    text = Column(String, nullable=False, default="")
    # tokens: [{"text": "...", "bbox": [x0, y0, x1, y1]}, ...]
    tokens = Column(JSON, nullable=False, default=list)

    document = relationship("Document", back_populates="pages")

    __table_args__ = (UniqueConstraint("document_id", "page_number"),)
