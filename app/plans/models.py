from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from app.db import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)  # transmittal | submittal_package
    status = Column(String, nullable=False, default="pending")
    storage_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
