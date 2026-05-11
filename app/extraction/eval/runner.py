"""Golden-set eval runner.

Run with:  make eval
Or:        python -m app.extraction.eval.runner
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.extraction.eval.metrics import EvalRow, summarize

GOLDEN_DIR = Path(__file__).parent / "golden"


def discover_samples() -> list[Path]:
    return sorted(GOLDEN_DIR.glob("*.expected.json"))


def main() -> int:
    samples = discover_samples()
    if not samples:
        print("[eval] no golden samples found in", GOLDEN_DIR)
        print("[eval] add <name>.pdf and <name>.expected.json pairs to populate the golden set")
        return 0

    rows: list[EvalRow] = []
    for expected_path in samples:
        name = expected_path.stem.replace(".expected", "")
        # Actual extraction wiring (run extraction against the PDF) is intentionally
        # omitted here — the AI/ML hire will fill this in alongside their first PR.
        rows.append(
            EvalRow(
                sample=name,
                schema_valid=False,
                grounding_rate=0.0,
                field_accuracy={},
            )
        )

    summary = summarize(rows)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
