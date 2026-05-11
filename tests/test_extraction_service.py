"""ExtractionService with a stub LLM — the unit-test boundary for the AI workstream."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from app.extraction.llm.client import StructuredOutput
from app.extraction.service import ExtractionRequest, ExtractionService
from app.ingestion.models import Document, DocumentPage
from app.projects.models import Organization, Project, User


class StubLLM:
    def __init__(self, response: dict[str, Any]) -> None:
        self._response = response

    def extract_structured(self, *, prompt: str, schema: dict[str, Any], model: str | None = None):
        return StructuredOutput(self._response), {
            "model": "stub",
            "model_version": "stub-1",
        }


def _seed_doc(db) -> Document:
    org = Organization(name="t")
    db.add(org); db.flush()
    proj = Project(organization_id=org.id, name="p")
    db.add(proj); db.flush()
    user = User(email="u@u", display_name="u", password_hash="x")
    db.add(user); db.flush()
    doc = Document(
        project_id=proj.id,
        uploader_user_id=user.id,
        kind="submittal",
        storage_key="x",
        original_filename="f.pdf",
        current_state="PARSED",
    )
    db.add(doc); db.flush()
    db.add(DocumentPage(
        document_id=doc.id,
        page_number=1,
        text="Submittal Number: 09 30 00-001 by Daltile.",
        tokens=[
            {"text": "Submittal", "bbox": [10, 10, 60, 20]},
            {"text": "Number:", "bbox": [62, 10, 100, 20]},
            {"text": "09", "bbox": [104, 10, 120, 20]},
            {"text": "30", "bbox": [122, 10, 138, 20]},
            {"text": "00-001", "bbox": [140, 10, 180, 20]},
            {"text": "by", "bbox": [184, 10, 200, 20]},
            {"text": "Daltile.", "bbox": [202, 10, 250, 20]},
        ],
    ))
    db.flush()
    return doc


def test_extraction_service_validates_grounds_and_persists(db):
    doc = _seed_doc(db)
    llm = StubLLM(
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
    )
    svc = ExtractionService(llm=llm)
    result = svc.run(db, ExtractionRequest(document_id=doc.id, schema_id="submittal_v1"))
    db.flush()

    assert len(result.fields) == 4
    for f in result.fields:
        assert f.citations, "ADR-003: every field must have at least one citation"


def test_extraction_service_drops_ungroundable_fields(db):
    doc = _seed_doc(db)
    llm = StubLLM(
        {
            "fields": [
                {
                    "field_path": "/submittal_number",
                    "value": "09 30 00-001",
                    "confidence": 0.95,
                    "citations": [{"page": 1, "source_text": "this quote is not on the page"}],
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
    )
    svc = ExtractionService(llm=llm)
    result = svc.run(db, ExtractionRequest(document_id=doc.id, schema_id="submittal_v1"))
    paths = {f.field_path for f in result.fields}
    assert "/submittal_number" not in paths
    assert "/manufacturer" in paths


def test_extraction_service_raises_when_schema_invalid(db):
    doc = _seed_doc(db)
    llm = StubLLM(
        {
            "fields": [
                {
                    "field_path": "/submittal_number",
                    "value": 12345,  # wrong type
                    "confidence": 0.5,
                    "citations": [{"page": 1, "source_text": "09 30 00-001"}],
                }
            ]
        }
    )
    svc = ExtractionService(llm=llm)
    with pytest.raises(Exception):
        svc.run(db, ExtractionRequest(document_id=doc.id, schema_id="submittal_v1"))
