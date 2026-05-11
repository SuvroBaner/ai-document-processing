"""Run the extraction pipeline against a local PDF and print the result.

Usage:
    python -m scripts.demo_extract path/to/submittal.pdf

Requires:
- OPENAI_API_KEY in env.
- Postgres + MinIO running (`make dev`).
- `make seed` already run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import UUID

from app.db import SessionLocal
from app.extraction.llm.openai_client import OpenAIClient
from app.extraction.service import ExtractionRequest, ExtractionService
from app.ingestion.service import parse_document, register_document
from app.projects.models import Project, User
from app.workflow.transitions import extraction_started, extraction_succeeded, review_opened


def main(pdf_path: str) -> int:
    path = Path(pdf_path)
    if not path.exists():
        print(f"[demo] file not found: {pdf_path}")
        return 1
    content = path.read_bytes()

    with SessionLocal() as db:
        project = db.query(Project).first()
        uploader = db.query(User).filter(User.email == "uploader@demo").first()
        if project is None or uploader is None:
            print("[demo] run `make seed` first.")
            return 1

        doc = register_document(
            db,
            project_id=project.id,
            uploader_user_id=uploader.id,
            kind="submittal",
            filename=path.name,
            content=content,
        )
        db.commit()
        print(f"[demo] uploaded document_id={doc.id}")

        parse_document(db, UUID(str(doc.id)))
        db.commit()
        print(f"[demo] parsed; state={doc.current_state}")

        extraction_started(db, doc, schema_id="submittal_v1")
        db.commit()

        svc = ExtractionService(llm=OpenAIClient())
        result = svc.run(db, ExtractionRequest(document_id=doc.id, schema_id="submittal_v1"))

        extraction_succeeded(db, doc, extraction_id=str(result.extraction_id))
        review_opened(db, doc)
        db.commit()
        print(json.dumps(result.model_dump(mode="json"), indent=2, default=str))
        return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m scripts.demo_extract <pdf_path>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
