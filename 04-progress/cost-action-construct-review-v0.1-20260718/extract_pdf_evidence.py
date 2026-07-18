"""Locate review-relevant passages in local PDFs without writing extracted text.

Usage:
    python extract_pdf_evidence.py FILE.pdf REGEX [REGEX ...]

The script prints the one-based PDF page number and a bounded context window for
each matching regular expression. It is deliberately read-only so that the
evidence review can retain the source PDF as the auditable record.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

from pypdf import PdfReader


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("patterns", nargs="+")
    parser.add_argument("--context", type=int, default=350)
    parser.add_argument("--max-per-pattern", type=int, default=8)
    args = parser.parse_args()

    reader = PdfReader(args.pdf)
    print(f"FILE={args.pdf} PAGES={len(reader.pages)}")
    compiled = [(raw, re.compile(raw, re.IGNORECASE)) for raw in args.patterns]
    counts = {raw: 0 for raw, _ in compiled}

    for page_no, page in enumerate(reader.pages, start=1):
        text = compact(page.extract_text() or "")
        for raw, pattern in compiled:
            if counts[raw] >= args.max_per_pattern:
                continue
            match = pattern.search(text)
            if not match:
                continue
            start = max(0, match.start() - args.context)
            end = min(len(text), match.end() + args.context)
            print(f"\nPATTERN={raw!r} PDF_PAGE={page_no}")
            print(text[start:end])
            counts[raw] += 1

    print("\nMATCH_COUNTS")
    for raw, _ in compiled:
        print(f"{raw}\t{counts[raw]}")


if __name__ == "__main__":
    main()
