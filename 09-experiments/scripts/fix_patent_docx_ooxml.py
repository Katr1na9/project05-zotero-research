from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from docx import Document
from lxml import etree


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKAGE_DIR = ROOT / "08-writing" / "patent-package-v0.4"
ZOOM = b'<w:zoom w:val="bestFit"/>'
FIXED_ZOOM = b'<w:zoom w:val="bestFit" w:percent="100"/>'


def fix_document(path: Path) -> None:
    temporary = path.with_suffix(".fixed.docx")
    with ZipFile(path, "r") as source, ZipFile(temporary, "w", ZIP_DEFLATED) as target:
        for item in source.infolist():
            payload = source.read(item.filename)
            if item.filename == "word/settings.xml":
                if ZOOM not in payload and FIXED_ZOOM not in payload:
                    raise ValueError(f"Unsupported zoom node in {path.name}")
                payload = payload.replace(ZOOM, FIXED_ZOOM)
            if item.filename.endswith(".xml") or item.filename.endswith(".rels"):
                etree.fromstring(payload)
            target.writestr(item, payload)
    temporary.replace(path)
    Document(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize and validate generated patent DOCX packages.")
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE_DIR)
    args = parser.parse_args()
    documents = sorted(args.package_dir.glob("*.docx"))
    if not documents:
        raise FileNotFoundError(f"No DOCX files found in {args.package_dir}")
    for document in documents:
        fix_document(document)
        print(document)


if __name__ == "__main__":
    main()
