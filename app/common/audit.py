"""Append-only audit log writer; subscribes to all domain events."""

from __future__ import annotations

from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from app.common.events import DomainEvent, get_event_bus
from app.db import Base, SessionLocal


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    event_name = Column(String, nullable=False, index=True)
    event_id = Column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    actor_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _persist(event: DomainEvent) -> None:
    with SessionLocal() as session:
        session.add(
            AuditLogEntry(
                event_name=event.name,
                event_id=event.event_id,
                actor_user_id=event.actor_user_id,
                payload=event.payload,
            )
        )
        session.commit()


def register_audit_subscribers() -> None:
    get_event_bus().subscribe_all(_persist)
