from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from app.db import Base


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True, index=True)
    plan_id = Column(PG_UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True, index=True)
    adapter = Column(String, nullable=False)        # pdf_transmittal | label_zpl
    status = Column(String, nullable=False, default="pending")
    result_storage_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
