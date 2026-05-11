"""Top-level CSI MasterFormat divisions, 2020 revision.

Source: publicly-known headings of CSI MasterFormat. Sufficient for the slice.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.vocabulary.models import Vocabulary, VocabularyTerm, VocabularyVersion


DIVISIONS_2020 = [
    ("00", "Procurement and Contracting Requirements"),
    ("01", "General Requirements"),
    ("02", "Existing Conditions"),
    ("03", "Concrete"),
    ("04", "Masonry"),
    ("05", "Metals"),
    ("06", "Wood, Plastics, and Composites"),
    ("07", "Thermal and Moisture Protection"),
    ("08", "Openings"),
    ("09", "Finishes"),
    ("10", "Specialties"),
    ("11", "Equipment"),
    ("12", "Furnishings"),
    ("13", "Special Construction"),
    ("14", "Conveying Equipment"),
    ("21", "Fire Suppression"),
    ("22", "Plumbing"),
    ("23", "HVAC"),
    ("26", "Electrical"),
    ("27", "Communications"),
    ("28", "Electronic Safety and Security"),
    ("31", "Earthwork"),
    ("32", "Exterior Improvements"),
    ("33", "Utilities"),
]


def seed(db: Session) -> None:
    existing = db.query(Vocabulary).filter(Vocabulary.slug == "csi_masterformat").first()
    if existing:
        return
    vocab = Vocabulary(slug="csi_masterformat", display_name="CSI MasterFormat")
    db.add(vocab)
    db.flush()
    version = VocabularyVersion(vocabulary_id=vocab.id, version_label="2020")
    db.add(version)
    db.flush()
    for code, label in DIVISIONS_2020:
        db.add(VocabularyTerm(vocabulary_version_id=version.id, code=code, label=label))
