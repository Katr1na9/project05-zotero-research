#!/usr/bin/env python3
"""Validate provenance and case coverage for external ground truth."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_SCHEMA = EXP / "data_schema" / "external_ground_truth_bundle.schema.json"
CASE_FILENAMES = ("case_config.json", "evidence_claims.json", "acquisition_actions.json")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_case_dirs(*roots: Path) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        paths.extend(
            path for path in root.iterdir()
            if path.is_dir() and all((path / name).is_file() for name in CASE_FILENAMES)
        )
    return sorted(paths, key=lambda path: path.name)


def expected_case_ids(case_dirs: list[Path]) -> set[str]:
    return {
        str(load_json(case_dir / "case_config.json")["case_id"])
        for case_dir in case_dirs
    }


def validate_bundle(
    bundle_path: Path,
    case_dirs: list[Path],
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    bundle = load_json(bundle_path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_errors = sorted(error.message for error in validator.iter_errors(bundle))
    semantic_errors: list[str] = []
    record_ids: set[str] = set()
    actor_cases: set[str] = set()
    utility_cases: set[str] = set()
    actor_case_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for record in bundle.get("records", []):
        record_id = str(record.get("record_id", ""))
        if record_id in record_ids:
            semantic_errors.append(f"duplicate record_id: {record_id}")
        record_ids.add(record_id)
        case_id = str(record.get("case_id", ""))
        kind = record.get("ground_truth_type")
        if kind == "actor_attribution":
            actor_cases.add(case_id)
            actor_case_counts[case_id] = actor_case_counts.get(case_id, 0) + 1
        elif kind == "analyst_utility":
            utility_cases.add(case_id)
        source = record.get("normalized_source", {})
        source_file = str(source.get("source_file", ""))
        source_counts[source_file] = source_counts.get(source_file, 0) + 1
    duplicate_actor_cases = sorted(
        case_id for case_id, count in actor_case_counts.items() if count > 1
    )
    if duplicate_actor_cases:
        semantic_errors.append(
            f"multiple actor ground truths for cases: {duplicate_actor_cases}"
        )
    declared_counts = {
        str(source.get("path", "")): int(source.get("record_count", -1))
        for source in bundle.get("source_files", [])
    }
    if declared_counts != source_counts:
        semantic_errors.append("source file record counts do not match normalized records")

    expected = expected_case_ids(case_dirs)
    unknown_actor = sorted(actor_cases - expected)
    unknown_utility = sorted(utility_cases - expected)
    if unknown_actor or unknown_utility:
        semantic_errors.append(
            f"unknown case ids: actor={unknown_actor}, utility={unknown_utility}"
        )
    actor_missing = sorted(expected - actor_cases)
    utility_missing = sorted(expected - utility_cases)
    record_count = len(bundle.get("records", []))
    actor_identifiable = not schema_errors and not semantic_errors and not actor_missing
    utility_identifiable = not schema_errors and not semantic_errors and not utility_missing
    blocking_reasons: list[str] = []
    if not record_count:
        blocking_reasons.append("no_external_ground_truth_records")
    if actor_missing:
        blocking_reasons.append("external_actor_ground_truth_incomplete")
    if utility_missing:
        blocking_reasons.append("external_analyst_utility_ground_truth_incomplete")
    if schema_errors or semantic_errors:
        blocking_reasons.append("external_ground_truth_validation_failed")
    return {
        "validation_status": "passed" if not schema_errors and not semantic_errors else "failed",
        "schema_valid": not schema_errors,
        "provenance_valid": not schema_errors and not any("source file" in error for error in semantic_errors),
        "record_count": record_count,
        "expected_case_count": len(expected),
        "actor_case_count": len(actor_cases & expected),
        "analyst_utility_case_count": len(utility_cases & expected),
        "actor_missing_case_ids": actor_missing,
        "analyst_utility_missing_case_ids": utility_missing,
        "external_actor_accuracy": None,
        "external_actor_accuracy_status": (
            "identifiable" if actor_identifiable else "not_identifiable_without_complete_external_actor_ground_truth"
        ),
        "analyst_utility_status": (
            "identifiable" if utility_identifiable else "not_identifiable_without_complete_external_analyst_utility_ground_truth"
        ),
        "schema_errors": schema_errors,
        "semantic_errors": semantic_errors,
        "blocking_reasons": blocking_reasons,
        "bundle_sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
        "all_experiments_complete": False,
        "paper_or_patent_updated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--examples-dir", type=Path, default=EXP / "examples")
    parser.add_argument("--real-cases-dir", type=Path, default=EXP / "real_cases")
    args = parser.parse_args()
    report = validate_bundle(
        args.bundle,
        discover_case_dirs(args.examples_dir, args.real_cases_dir),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["validation_status"] == "passed" else 1)


if __name__ == "__main__":
    main()
