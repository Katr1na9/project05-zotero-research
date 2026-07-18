#!/usr/bin/env python3
"""Validate operational cost telemetry without inventing measured costs."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_SCHEMA = EXP / "data_schema" / "operational_cost_measurement_batch.schema.json"
CASE_FILENAMES = ("case_config.json", "evidence_claims.json", "acquisition_actions.json")
DEFAULT_MINIMUM_COMPLETED_ATTEMPTS = 3


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_case_dirs(*roots: Path) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        found.extend(
            path
            for path in root.iterdir()
            if path.is_dir() and all((path / name).is_file() for name in CASE_FILENAMES)
        )
    return sorted(found, key=lambda path: path.name)


def expected_actions(case_dirs: list[Path]) -> set[tuple[str, str]]:
    expected: set[tuple[str, str]] = set()
    for case_dir in case_dirs:
        config = load_json(case_dir / "case_config.json")
        for action in load_json(case_dir / "acquisition_actions.json"):
            if action.get("action_id") == "STOP" or action.get("action_type") == "stop":
                continue
            expected.add((str(config["case_id"]), str(action["action_id"])))
    return expected


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_source_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() == ".jsonl":
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        value = load_json(path)
        records = value.get("records", []) if isinstance(value, dict) else value
    if not isinstance(records, list) or not all(
        isinstance(record, dict) for record in records
    ):
        raise ValueError("source does not contain an object record array")
    return records


def validate_batch(
    batch_path: Path,
    case_dirs: list[Path],
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    batch = load_json(batch_path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_errors = sorted(
        error.message for error in validator.iter_errors(batch)
    )
    semantic_errors: list[str] = []
    seen_measurements: set[str] = set()
    seen_attempts: set[tuple[str, str, str]] = set()
    observed: set[tuple[str, str]] = set()
    completed_attempts: Counter[tuple[str, str]] = Counter()
    for record in batch.get("records", []):
        measurement_id = str(record.get("measurement_id", ""))
        if measurement_id in seen_measurements:
            semantic_errors.append(f"duplicate measurement_id: {measurement_id}")
        seen_measurements.add(measurement_id)
        key = (
            str(record.get("case_id", "")),
            str(record.get("action_id", "")),
            str(record.get("attempt_id", "")),
        )
        if key in seen_attempts:
            semantic_errors.append(f"duplicate action attempt: {'/'.join(key)}")
        seen_attempts.add(key)
        observed.add(key[:2])
        if record.get("execution_status") == "completed":
            completed_attempts[key[:2]] += 1
        try:
            started = datetime.fromisoformat(str(record["started_utc"]).replace("Z", "+00:00"))
            ended = datetime.fromisoformat(str(record["ended_utc"]).replace("Z", "+00:00"))
            if ended < started:
                semantic_errors.append(f"ended_utc precedes started_utc: {measurement_id}")
        except (KeyError, ValueError):
            pass
        authorization = record.get("authorization", {})
        if authorization.get("required") and not authorization.get("approval_reference"):
            semantic_errors.append(
                f"authorization approval_reference missing: {measurement_id}"
            )
        if not authorization.get("required") and authorization.get("boundary") != "none":
            semantic_errors.append(
                f"non-required authorization must use boundary=none: {measurement_id}"
            )

    expected = expected_actions(case_dirs)
    protocol = batch.get("measurement_protocol", {})
    minimum_completed_attempts = protocol.get(
        "minimum_completed_attempts_per_action",
        DEFAULT_MINIMUM_COMPLETED_ATTEMPTS,
    )
    if not isinstance(minimum_completed_attempts, int) or isinstance(
        minimum_completed_attempts, bool
    ):
        minimum_completed_attempts = DEFAULT_MINIMUM_COMPLETED_ATTEMPTS
    covered = {
        key
        for key, count in completed_attempts.items()
        if count >= minimum_completed_attempts
    }
    unknown = sorted(observed - expected)
    missing = sorted(expected - covered)
    if unknown:
        semantic_errors.append(f"unknown case/action measurements: {unknown}")
    source_declarations = batch.get("source_files", [])
    source_paths = [str(source.get("path")) for source in source_declarations]
    if len(source_paths) != len(set(source_paths)):
        semantic_errors.append("provenance: duplicate source file declaration")
    source_counts = {
        str(source.get("path")): int(source.get("record_count", -1))
        for source in source_declarations
    }
    actual_source_counts: dict[str, int] = {}
    for record in batch.get("records", []):
        path = str(record.get("source_file", ""))
        actual_source_counts[path] = actual_source_counts.get(path, 0) + 1
    if source_counts != actual_source_counts:
        semantic_errors.append(
            "provenance: source file record counts do not match normalized records"
        )
    records_by_source: dict[str, list[dict[str, Any]]] = {}
    for record in batch.get("records", []):
        records_by_source.setdefault(str(record.get("source_file", "")), []).append(
            record
        )
    for source in source_declarations:
        source_path_text = str(source.get("path", ""))
        source_path = Path(source_path_text)
        if not source_path.is_file():
            semantic_errors.append(
                f"provenance: source file unavailable: {source_path_text}"
            )
            continue
        actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        declared_hash = str(source.get("sha256", ""))
        if actual_hash != declared_hash:
            semantic_errors.append(
                f"provenance: source file sha256 mismatch: {source_path_text}"
            )
        normalized_records = records_by_source.get(source_path_text, [])
        if any(
            str(record.get("source_file_sha256", "")) != declared_hash
            for record in normalized_records
        ):
            semantic_errors.append(
                f"provenance: normalized source hash mismatch: {source_path_text}"
            )
        try:
            raw_records = read_source_records(source_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            semantic_errors.append(
                f"provenance: source file replay failed: {source_path_text}: {exc}"
            )
            continue
        raw_hashes = Counter(canonical_sha256(record) for record in raw_records)
        normalized_hashes = Counter(
            str(record.get("record_sha256", "")) for record in normalized_records
        )
        if raw_hashes != normalized_hashes:
            semantic_errors.append(
                f"provenance: source record hashes do not replay: {source_path_text}"
            )

    record_count = len(batch.get("records", []))
    schema_valid = not schema_errors
    provenance_valid = not any(
        error.startswith("provenance:") for error in semantic_errors
    )
    measurement_batch_ready = (
        schema_valid
        and not semantic_errors
        and record_count > 0
        and not missing
        and provenance_valid
    )
    blocking_reasons: list[str] = []
    if record_count == 0:
        blocking_reasons.append("no_real_operational_measurement_records")
    if missing:
        blocking_reasons.append("incomplete_action_measurement_coverage")
    if record_count > 0 and missing:
        blocking_reasons.append("insufficient_completed_attempt_replication")
    if schema_errors or semantic_errors:
        blocking_reasons.append("measurement_validation_failed")
    blocking_reasons.append("measured_cost_transformation_and_profile_not_frozen")
    return {
        "validation_status": "passed" if schema_valid and not semantic_errors else "failed",
        "schema_valid": schema_valid,
        "provenance_valid": provenance_valid,
        "record_count": record_count,
        "completed_attempt_count": sum(completed_attempts.values()),
        "minimum_completed_attempts_per_action": minimum_completed_attempts,
        "expected_action_count": len(expected),
        "covered_action_count": len(covered & expected),
        "missing_action_count": len(missing),
        "missing_actions": [f"{case_id}/{action_id}" for case_id, action_id in missing],
        "unknown_actions": [f"{case_id}/{action_id}" for case_id, action_id in unknown],
        "schema_errors": schema_errors,
        "semantic_errors": semantic_errors,
        "measurement_batch_ready": measurement_batch_ready,
        "formal_measured_cost_profile_ready": False,
        "blocking_reasons": blocking_reasons,
        "batch_sha256": hashlib.sha256(batch_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    parser.add_argument("--examples-dir", type=Path, default=EXP / "examples")
    parser.add_argument("--real-cases-dir", type=Path, default=EXP / "real_cases")
    args = parser.parse_args()
    report = validate_batch(
        args.batch,
        discover_case_dirs(args.examples_dir, args.real_cases_dir),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["validation_status"] == "passed" else 1)


if __name__ == "__main__":
    main()
