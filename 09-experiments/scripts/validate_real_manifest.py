#!/usr/bin/env python3
"""Validate a DARPA TC real-data manifest."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("timestamp has no UTC offset")
    return parsed


def validate_manifest(real_data_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = real_data_dir / "manifest.json"
    if not manifest_path.is_file():
        return [f"missing manifest: {manifest_path}"]

    manifest = load_json(manifest_path)
    sources = manifest.get("sources", [])
    source_ids = [source.get("source_id") for source in sources]
    if len(source_ids) != len(set(source_ids)):
        errors.append("source_id values must be unique")
    source_id_set = set(source_ids)

    documents = manifest.get("documents", [])
    document_ids = [document.get("document_id") for document in documents]
    if len(document_ids) != len(set(document_ids)):
        errors.append("document_id values must be unique")
    document_id_set = set(document_ids)
    for document in documents:
        if not SHA256_PATTERN.fullmatch(document.get("sha256", "")):
            errors.append(
                f"invalid SHA-256 for {document.get('document_id')}"
            )

    case_ids: list[str] = []
    for case_ref in manifest.get("cases", []):
        case_id = case_ref.get("case_id")
        case_ids.append(case_id)
        if case_ref.get("source_id") not in source_id_set:
            errors.append(f"{case_id}: unknown source_id")

        relative_path = Path(case_ref.get("ground_truth_file", ""))
        if relative_path.is_absolute() or ".." in relative_path.parts:
            errors.append(f"{case_id}: unsafe ground_truth_file")
            continue
        case_path = real_data_dir / relative_path
        if not case_path.is_file():
            errors.append(f"{case_id}: missing ground truth file")
            continue

        case = load_json(case_path)
        if case.get("case_id") != case_id:
            errors.append(f"{case_id}: case_id mismatch")
        if case.get("source_id") != case_ref.get("source_id"):
            errors.append(f"{case_id}: source_id mismatch")
        if not isinstance(case.get("development_only"), bool):
            errors.append(f"{case_id}: development_only must be a boolean")
        if case.get("ground_truth_document") not in document_id_set:
            errors.append(f"{case_id}: unknown ground_truth_document")
        try:
            start = parse_utc(case["utc_window"]["start"])
            end = parse_utc(case["utc_window"]["end"])
            if start >= end:
                errors.append(f"{case_id}: invalid UTC window order")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{case_id}: invalid UTC window: {exc}")

    if len(case_ids) != len(set(case_ids)):
        errors.append("case_id values must be unique")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--real-data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "real_data"
        / "darpa_tc_e3",
    )
    args = parser.parse_args()
    errors = validate_manifest(args.real_data_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(f"Manifest valid: {args.real_data_dir}")


if __name__ == "__main__":
    main()
