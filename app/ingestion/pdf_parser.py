"""PDF parsing → page text + token bboxes.

The token bboxes feed the citation grounder (app/extraction/llm/citation_grounder.py).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Any

import pdfplumber


@dataclass
class ParsedToken:
    text: str
    bbox: tuple[float, float, float, float]


@dataclass
class ParsedPage:
    page_number: int
    text: str
    tokens: list[ParsedToken]

    def to_db(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text,
            "tokens": [asdict(t) for t in self.tokens],
        }


def parse_pdf(pdf_bytes: bytes) -> list[ParsedPage]:
    pages: list[ParsedPage] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(use_text_flow=True) or []
            tokens = [
                ParsedToken(
                    text=w["text"],
                    bbox=(float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"])),
                )
                for w in words
            ]
            text = page.extract_text() or ""
            pages.append(ParsedPage(page_number=i, text=text, tokens=tokens))
    return pages
