from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from app.db import Base


class WorkflowTransition(Base):
    """Append-only history of every document state transition (ADR-004)."""

    __tablename__ = "workflow_transitions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    from_state = Column(String, nullable=False)
    to_state = Column(String, nullable=False)
    actor_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_name = Column(String, nullable=False)
    event_payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
