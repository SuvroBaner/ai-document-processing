"""Maps verbatim quotes returned by the LLM back to (page, bbox) coordinates.

The LLM returns `source_text` strings. We need to verify those strings actually
appear on the indexed page tokens captured at parse time, and produce a bounding
box for the UI to highlight (ADR-003).

Strategy:
- Look up the page from the LLM's claimed `page` index.
- Search the page's tokens for the longest contiguous run matching `source_text`.
- If found, compute the union bbox of those tokens.
- If not found within an edit-distance budget, the citation is rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class GroundedCitation:
    page: int
    bbox: tuple[float, float, float, float]
    source_text: str


@dataclass
class PageTokens:
    page_number: int
    tokens: list[dict]  # [{"text": str, "bbox": [x0, y0, x1, y1]}, ...]


def _normalize(s: str) -> str:
    return " ".join(s.split()).lower()


def _union_bbox(boxes: Iterable[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    xs0, ys0, xs1, ys1 = zip(*boxes, strict=False)
    return (min(xs0), min(ys0), max(xs1), max(ys1))


def ground(
    page: PageTokens,
    source_text: str,
    *,
    min_match_ratio: float = 0.8,
) -> GroundedCitation | None:
    """Find `source_text` within `page.tokens` and return its bbox.

    Greedy sliding-window match. Returns None if the matched tokens cover
    less than `min_match_ratio` of the source's word count.
    """
    target_words = _normalize(source_text).split()
    if not target_words:
        return None

    page_words = [(_normalize(t["text"]), tuple(t["bbox"])) for t in page.tokens]
    n = len(page_words)
    t = len(target_words)
    best_score = 0
    best_span: tuple[int, int] | None = None

    for i in range(0, n):
        # Window length grows up to t; we measure exact-match overlap.
        matched = 0
        last_j = i
        for j in range(t):
            if i + j >= n:
                break
            if page_words[i + j][0] == target_words[j]:
                matched += 1
                last_j = i + j
        if matched > best_score:
            best_score = matched
            best_span = (i, last_j)

    if best_span is None:
        return None
    if best_score / t < min_match_ratio:
        return None

    start, end = best_span
    bbox = _union_bbox(page_words[k][1] for k in range(start, end + 1))
    return GroundedCitation(page=page.page_number, bbox=bbox, source_text=source_text)
