"""AI-assisted plan generation. Stubbed for the vertical slice."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.plans.models import Plan


def create_transmittal(db: Session, document_id: UUID) -> Plan:
    plan = Plan(document_id=document_id, kind="transmittal", status="ready")
    db.add(plan)
    db.flush()
    return plan
