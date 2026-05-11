from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)

    schema_id = Column(String, nullable=False)
    schema_version = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    model = Column(String, nullable=False)
    model_version = Column(String, nullable=False)

    raw_response = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    fields = relationship("ExtractionField", back_populates="extraction", cascade="all, delete-orphan")


class ExtractionField(Base):
    __tablename__ = "extraction_fields"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    extraction_id = Column(PG_UUID(as_uuid=True), ForeignKey("extractions.id"), nullable=False, index=True)

    field_path = Column(String, nullable=False)  # JSON pointer, e.g. "/manufacturer"
    value = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)

    extraction = relationship("Extraction", back_populates="fields")
    citations = relationship("Citation", back_populates="field", cascade="all, delete-orphan")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    extraction_field_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("extraction_fields.id"), nullable=False, index=True
    )
    page = Column(Integer, nullable=False)
    bbox = Column(JSON, nullable=False)         # [x0, y0, x1, y1]
    source_text = Column(String, nullable=False)

    field = relationship("ExtractionField", back_populates="citations")
