"""Stamps an approved submittal and emits a transmittal cover page.

For the slice, this is a stub that records the intent. Real implementation
would invoke a PDF stamper (e.g., pypdfium2 + reportlab).
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


def stamp_and_emit(document_id: str) -> str:
    """Returns a storage key that *would* hold the stamped artifact."""
    storage_key = f"output/transmittals/{document_id}/stamped.pdf"
    logger.info("output.pdf_transmittal.stamped", document_id=document_id, storage_key=storage_key)
    return storage_key
