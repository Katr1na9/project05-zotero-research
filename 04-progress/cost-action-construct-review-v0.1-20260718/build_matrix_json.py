"""Generate a deterministic JSON mirror of the reviewed source CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source-evidence-matrix.csv"
TARGET = ROOT / "source-evidence-matrix.json"


with SOURCE.open(encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))

TARGET.write_text(
    json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(f"wrote {len(rows)} rows to {TARGET}")
