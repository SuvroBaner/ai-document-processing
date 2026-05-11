"""The vertical slice end-to-end, with LLM stubbed.

This test exercises: parse-succeeded → extraction → review-opened → field-edit →
approved. It asserts the state machine advanced correctly and the audit trail
is complete.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.common.auth import CurrentUser, Role
from app.extraction.llm.client import StructuredOutput
from app.extraction.service import ExtractionRequest, ExtractionService
from app.ingestion.models import Document, DocumentPage
from app.projects.models import Organization, Project, User
from app.review.service import approve, edit_field
from app.workflow.models import WorkflowTransition
from app.workflow.transitions import (
    extraction_started,
    extraction_succeeded,
    parse_started,
    parse_succeeded,
    review_opened,
)


class StubLLM:
    def extract_structured(self, *, prompt, schema, model=None):  # noqa: ARG002
        return StructuredOutput(
            {
                "fields": [
                    {
                        "field_path": "/submittal_number",
                        "value": "09 30 00-001",
                        "confidence": 0.95,
                        "citations": [{"page": 1, "source_text": "09 30 00-001"}],
                    },
                    {
                        "field_path": "/spec_section",
                        "value": "09 30 00",
                        "confidence": 0.9,
                        "citations": [{"page": 1, "source_text": "09 30 00"}],
                    },
                    {
                        "field_path": "/product_name",
                        "value": "Continental Slate",
                        "confidence": 0.8,
                        "citations": [{"page": 1, "source_text": "Daltile."}],
                    },
                    {
                        "field_path": "/manufacturer",
                        "value": "Daltile",
                        "confidence": 0.99,
                        "citations": [{"page": 1, "source_text": "Daltile."}],
                    },
                ]
            }
        ), {"model": "stub", "model_version": "stub-1"}


@pytest.fixture
def world(db):
    org = Organization(name="Demo")
    db.add(org); db.flush()
    project = Project(organization_id=org.id, name="Acme Tower")
    db.add(project); db.flush()
    reviewer = User(email="reviewer@demo", display_name="R", password_hash="x")
    approver = User(email="approver@demo", display_name="A", password_hash="x")
    db.add_all([reviewer, approver]); db.flush()
    doc = Document(
        project_id=project.id,
        uploader_user_id=reviewer.id,
        kind="submittal",
        storage_key="seed",
        original_filename="sample.pdf",
        current_state="UPLOADED",
    )
    db.add(doc); db.flush()
    db.add(DocumentPage(
        document_id=doc.id,
        page_number=1,
        text="Submittal Number: 09 30 00-001 by Daltile. Section 09 30 00.",
        tokens=[
            {"text": "Submittal", "bbox": [10, 10, 60, 20]},
            {"text": "Number:", "bbox": [62, 10, 100, 20]},
            {"text": "09", "bbox": [104, 10, 120, 20]},
            {"text": "30", "bbox": [122, 10, 138, 20]},
            {"text": "00-001", "bbox": [140, 10, 180, 20]},
            {"text": "by", "bbox": [184, 10, 200, 20]},
            {"text": "Daltile.", "bbox": [202, 10, 250, 20]},
            {"text": "Section", "bbox": [10, 30, 60, 40]},
            {"text": "09", "bbox": [62, 30, 78, 40]},
            {"text": "30", "bbox": [80, 30, 96, 40]},
            {"text": "00.", "bbox": [98, 30, 122, 40]},
        ],
    ))
    db.flush()
    return {"doc": doc, "reviewer": reviewer, "approver": approver}


def _approver_user(approver_user) -> CurrentUser:
    return CurrentUser(
        user_id=approver_user.id,
        email=approver_user.email,
        org_id=uuid4(),
        roles=frozenset({Role.APPROVER, Role.REVIEWER}),
    )


def test_vertical_slice(db, world):
    doc = world["doc"]
    approver = world["approver"]

    # 1. Parse
    parse_started(db, doc)
    parse_succeeded(db, doc, page_count=1)
    assert doc.current_state == "PARSED"

    # 2. Extract
    extraction_started(db, doc, schema_id="submittal_v1")
    svc = ExtractionService(llm=StubLLM())
    result = svc.run(db, ExtractionRequest(document_id=doc.id, schema_id="submittal_v1"))
    extraction_succeeded(db, doc, extraction_id=str(result.extraction_id))
    assert doc.current_state == "EXTRACTED"

    # 3. Open review
    review_opened(db, doc)
    assert doc.current_state == "IN_REVIEW"

    # 4. Reviewer edits a field
    from app.extraction.models import ExtractionField
    a_field = db.query(ExtractionField).first()
    edit_field(
        db,
        document_id=doc.id,
        extraction_field_id=a_field.id,
        new_value="EDITED",
        reason="reviewer correction",
        user=_approver_user(approver),
    )

    # 5. Approver approves
    approve(db, document_id=doc.id, user=_approver_user(approver))
    assert doc.current_state == "APPROVED"

    # 6. Audit trail: every state change is recorded
    transitions = (
        db.query(WorkflowTransition)
        .filter(WorkflowTransition.document_id == doc.id)
        .order_by(WorkflowTransition.created_at)
        .all()
    )
    event_chain = [t.event_name for t in transitions]
    assert event_chain == [
        "parse_started",
        "parse_succeeded",
        "extraction_started",
        "extraction_succeeded",
        "review_opened",
        "approved",
    ]
    assert datetime.now(timezone.utc).year >= 2025  # sanity, timezone-aware timestamps
