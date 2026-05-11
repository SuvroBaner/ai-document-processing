"""ExtractionService — the workstream's orchestrator.

This is the implementation behind the public interface exposed in
`app/extraction/__init__.py`. The AI/ML engineer owns this file and the
modules it imports; the rest of the platform sees only the public types.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

import jsonschema
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.common.errors import ValidationFailed
from app.extraction.llm.citation_grounder import PageTokens, ground
from app.extraction.llm.client import LLMClient
from app.extraction.models import Citation as CitationRow
from app.extraction.models import Extraction, ExtractionField as ExtractionFieldRow
from app.ingestion.models import Document, DocumentPage

SCHEMA_DIR = Path(__file__).parent / "schemas"
PROMPT_DIR = Path(__file__).parent / "prompts"
SCHEMA_VERSION = "v1"
PROMPT_VERSION = "v1"


_jinja = Environment(loader=FileSystemLoader(str(PROMPT_DIR)), autoescape=select_autoescape())


# ---------- Public types (the interface) ----------

class Citation(BaseModel):
    page: int = Field(ge=1)
    bbox: tuple[float, float, float, float]
    source_text: str = Field(min_length=1)


class ExtractionField(BaseModel):
    field_path: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[Citation] = Field(min_length=1)  # non-empty (ADR-003)

    @field_validator("field_path")
    @classmethod
    def must_be_json_pointer(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError("field_path must be a JSON Pointer (starts with /)")
        return v


class ExtractionRequest(BaseModel):
    document_id: UUID
    schema_id: str
    page_range: tuple[int, int] | None = None
    prompt_version: str | None = None


class ExtractionResult(BaseModel):
    extraction_id: UUID
    schema_id: str
    schema_version: str
    model: str
    model_version: str
    prompt_version: str
    fields: list[ExtractionField]
    raw_response: dict[str, Any]


# ---------- Service ----------

class ExtractionService:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, db: Session, req: ExtractionRequest) -> ExtractionResult:
        document = db.get(Document, req.document_id)
        if document is None:
            raise ValidationFailed("document not found", document_id=str(req.document_id))

        schema = _load_schema(req.schema_id)
        pages = _load_pages(db, document, req.page_range)
        prompt = _render_prompt(schema, pages)

        raw_output, meta = self._llm.extract_structured(prompt=prompt, schema=schema)

        validated_fields = _validate_and_ground(raw_output, schema, pages)

        extraction = Extraction(
            document_id=document.id,
            schema_id=req.schema_id,
            schema_version=SCHEMA_VERSION,
            prompt_version=req.prompt_version or PROMPT_VERSION,
            model=meta.get("model", "unknown"),
            model_version=meta.get("model_version", "unknown"),
            raw_response={"output": dict(raw_output), "meta": meta},
        )
        db.add(extraction)
        db.flush()

        result_fields: list[ExtractionField] = []
        for field in validated_fields:
            row = ExtractionFieldRow(
                extraction_id=extraction.id,
                field_path=field.field_path,
                value=field.value,
                confidence=field.confidence,
            )
            db.add(row)
            db.flush()
            for cit in field.citations:
                db.add(
                    CitationRow(
                        extraction_field_id=row.id,
                        page=cit.page,
                        bbox=list(cit.bbox),
                        source_text=cit.source_text,
                    )
                )
            result_fields.append(field)

        return ExtractionResult(
            extraction_id=extraction.id,
            schema_id=req.schema_id,
            schema_version=SCHEMA_VERSION,
            model=extraction.model,
            model_version=extraction.model_version,
            prompt_version=extraction.prompt_version,
            fields=result_fields,
            raw_response=extraction.raw_response,
        )


# ---------- Helpers ----------

def _load_schema(schema_id: str) -> dict[str, Any]:
    path = SCHEMA_DIR / f"{schema_id}.json"
    if not path.exists():
        raise ValidationFailed("unknown schema_id", schema_id=schema_id)
    return json.loads(path.read_text())


def _load_pages(
    db: Session,
    document: Document,
    page_range: tuple[int, int] | None,
) -> list[DocumentPage]:
    q = db.query(DocumentPage).filter(DocumentPage.document_id == document.id).order_by(DocumentPage.page_number)
    pages = q.all()
    if page_range:
        lo, hi = page_range
        pages = [p for p in pages if lo <= p.page_number <= hi]
    return pages


def _render_prompt(schema: dict[str, Any], pages: list[DocumentPage]) -> str:
    template = _jinja.get_template("submittal_v1.jinja")
    return template.render(
        schema_json=json.dumps(schema, indent=2),
        pages=[{"page_number": p.page_number, "text": p.text} for p in pages],
    )


def _validate_and_ground(
    raw_output: dict[str, Any],
    schema: dict[str, Any],
    pages: list[DocumentPage],
) -> list[ExtractionField]:
    """Validate the LLM output and ground every citation to actual page tokens."""
    field_dicts = raw_output.get("fields", [])
    if not isinstance(field_dicts, list):
        raise ValidationFailed("llm response missing 'fields' list", raw=raw_output)

    # Build a flat dict of values for schema validation.
    values: dict[str, Any] = {}
    for f in field_dicts:
        path = f.get("field_path", "")
        if path.startswith("/"):
            values[path[1:]] = f.get("value")
    jsonschema.validate(instance=values, schema=schema)  # raises on violation

    page_tokens = {p.page_number: PageTokens(page_number=p.page_number, tokens=p.tokens) for p in pages}
    grounded_fields: list[ExtractionField] = []

    for f in field_dicts:
        grounded_cits: list[Citation] = []
        for c in f.get("citations", []):
            page_num = c.get("page")
            text = c.get("source_text", "")
            page = page_tokens.get(page_num)
            if page is None:
                continue
            res = ground(page, text)
            if res is None:
                continue
            grounded_cits.append(Citation(page=res.page, bbox=res.bbox, source_text=res.source_text))

        if not grounded_cits:
            # ADR-003: drop fields whose citations did not ground.
            continue

        grounded_fields.append(
            ExtractionField(
                field_path=f["field_path"],
                value=f["value"],
                confidence=float(f.get("confidence", 0.5)),
                citations=grounded_cits,
            )
        )

    if not grounded_fields:
        raise ValidationFailed("no fields had grounded citations", raw=raw_output)

    return grounded_fields
