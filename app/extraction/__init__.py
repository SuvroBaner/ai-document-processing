"""Public interface for the extraction workstream.

⚠️  This is the contract the AI/ML engineer cannot change without an ADR.
Internal modules may move freely; this surface is durable.

See:
- docs/adr/ADR-002-extraction-workstream.md
- docs/extraction-workstream.md
"""

from app.extraction.service import (
    Citation,
    ExtractionField,
    ExtractionRequest,
    ExtractionResult,
    ExtractionService,
)

__all__ = [
    "Citation",
    "ExtractionField",
    "ExtractionRequest",
    "ExtractionResult",
    "ExtractionService",
]
