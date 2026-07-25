#!/usr/bin/env python3
"""Validate v0.3 raw cost telemetry, schedule compliance, and coverage gates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_SCHEMA = EXP / "data_schema" / "operational_cost_measurement_batch_v0.3.schema.json"
RESOURCE_PATHS = (
    ("compute", "wall_seconds"),
    ("compute", "cpu_seconds"),
    ("compute", "memory_byte_seconds"),
    ("data_access", "bytes_scanned"),
    ("data_access", "records_scanned"),
    ("direct_currency", "amount"),
    ("direct_currency", "currency"),
    ("authorization_wait_seconds",),
    ("shared_overhead", "setup_seconds"),
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def resolve_reference(value: Any) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


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
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise ValueError("source does not contain an object record array")
    return records


def value_at_path(value: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = value
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def incomplete_resource_paths(record: dict[str, Any]) -> list[str]:
    trace = record.get("resource_trace", {})
    missing = [
        "resource_trace/" + "/".join(path)
        for path in RESOURCE_PATHS
        if value_at_path(trace, path) is None
    ]
    for index, role in enumerate(trace.get("analyst_time_by_role", [])):
        if role.get("seconds") is None:
            missing.append(f"resource_trace/analyst_time_by_role/{index}/seconds")
    observation = record.get("observation_summary", {})
    if observation.get("downtime_seconds") is None:
        missing.append("observation_summary/downtime_seconds")
    return missing


def load_schedule(batch: dict[str, Any]) -> tuple[Path | None, list[dict[str, str]], list[str]]:
    errors: list[str] = []
    schedule_meta = batch.get("schedule", {})
    path = resolve_reference(schedule_meta.get("path", ""))
    if not path.is_file():
        return None, [], [f"schedule unavailable: {path}"]
    if file_sha256(path) != schedule_meta.get("sha256"):
        errors.append(f"schedule sha256 mismatch: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != schedule_meta.get("scheduled_primary_attempt_count"):
        errors.append("schedule row count does not match scheduled_primary_attempt_count")
    return path, rows, errors


def validate_provenance(batch: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    declarations = batch.get("source_files", [])
    declared_paths = [str(row.get("path", "")) for row in declarations]
    if len(declared_paths) != len(set(declared_paths)):
        errors.append("provenance: duplicate source file declaration")
    normalized_by_source: dict[str, list[dict[str, Any]]] = {}
    for record in batch.get("records", []):
        normalized_by_source.setdefault(str(record.get("source_file", "")), []).append(record)
    declared_counts = {
        str(row.get("path", "")): row.get("record_count") for row in declarations
    }
    actual_counts = {path: len(rows) for path, rows in normalized_by_source.items()}
    if declared_counts != actual_counts:
        errors.append("provenance: source record counts do not match normalized records")
    for source in declarations:
        source_text = str(source.get("path", ""))
        source_path = Path(source_text)
        if not source_path.is_file():
            errors.append(f"provenance: source file unavailable: {source_text}")
            continue
        declared_hash = str(source.get("sha256", ""))
        if file_sha256(source_path) != declared_hash:
            errors.append(f"provenance: source file sha256 mismatch: {source_text}")
        normalized = normalized_by_source.get(source_text, [])
        if any(row.get("source_file_sha256") != declared_hash for row in normalized):
            errors.append(f"provenance: normalized source hash mismatch: {source_text}")
        try:
            raw_records = read_source_records(source_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"provenance: source replay failed: {source_text}: {exc}")
            continue
        raw_hashes = Counter(canonical_sha256(row) for row in raw_records)
        normalized_hashes = Counter(str(row.get("record_sha256", "")) for row in normalized)
        if raw_hashes != normalized_hashes:
            errors.append(f"provenance: source record hashes do not replay: {source_text}")
    return errors


def validate_batch(
    batch_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    batch = load_json(batch_path)
    validator = Draft202012Validator(
        load_json(schema_path), format_checker=FormatChecker()
    )
    schema_errors = [
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(batch), key=lambda item: list(item.path))
    ]
    semantic_errors: list[str] = []
    warnings: list[str] = []
    protocol = batch.get("protocol", {})
    registry_meta = protocol.get("action_executor_registry", {})
    registry_path = resolve_reference(registry_meta.get("path", ""))
    registry_integrity_valid = (
        registry_path.is_file()
        and file_sha256(registry_path) == registry_meta.get("sha256")
    )
    if not registry_integrity_valid:
        semantic_errors.append(
            f"action executor registry unavailable or hash-mismatched: {registry_path}"
        )
    execution_authorized = (
        protocol.get("execution_readiness") == "authorized_action_adapters_frozen"
        and protocol.get("schedule_authorization") == "execution_authorized"
        and registry_integrity_valid
    )
    _, schedule_rows, schedule_errors = load_schedule(batch)
    semantic_errors.extend(schedule_errors)
    schedule_by_index: dict[int, dict[str, str]] = {}
    for row in schedule_rows:
        try:
            index = int(row["scheduled_run_index"])
        except (KeyError, ValueError):
            semantic_errors.append("schedule contains an invalid scheduled_run_index")
            continue
        if index in schedule_by_index:
            semantic_errors.append(f"duplicate schedule run index: {index}")
        schedule_by_index[index] = row

    seen_measurements: set[str] = set()
    attempts_by_id: dict[str, dict[str, Any]] = {}
    primary_by_schedule: dict[int, dict[str, Any]] = {}
    resource_missing: dict[str, list[str]] = {}
    randomization_deviations: list[str] = []
    for record in batch.get("records", []):
        measurement_id = str(record.get("measurement_id", ""))
        if measurement_id in seen_measurements:
            semantic_errors.append(f"duplicate measurement_id: {measurement_id}")
        seen_measurements.add(measurement_id)
        attempt_id = str(record.get("execution_attempt_id", ""))
        if attempt_id in attempts_by_id:
            semantic_errors.append(f"duplicate execution_attempt_id: {attempt_id}")
        attempts_by_id[attempt_id] = record
        missing = incomplete_resource_paths(record)
        if missing:
            resource_missing[attempt_id] = missing
        try:
            started = datetime.fromisoformat(str(record["started_utc"]).replace("Z", "+00:00"))
            ended = datetime.fromisoformat(str(record["ended_utc"]).replace("Z", "+00:00"))
            if ended < started:
                semantic_errors.append(f"ended_utc precedes started_utc: {attempt_id}")
        except (KeyError, ValueError):
            pass
        authorization = record.get("context_covariates", {}).get("authorization", {})
        if authorization.get("required") and not authorization.get("approval_reference"):
            semantic_errors.append(f"required authorization lacks approval_reference: {attempt_id}")
        if not authorization.get("required") and authorization.get("boundary") != "none":
            semantic_errors.append(f"non-required authorization must use boundary=none: {attempt_id}")
        constraints = record.get("hard_constraints", {})
        if constraints.get("violations") and all(
            constraints.get(field)
            for field in ("authorization_satisfied", "data_available", "safety_gate_passed")
        ):
            semantic_errors.append(f"hard-constraint violations conflict with satisfied flags: {attempt_id}")
        run_index = record.get("scheduled_run_index")
        scheduled = schedule_by_index.get(run_index) if isinstance(run_index, int) else None
        if scheduled is None:
            semantic_errors.append(f"attempt references unknown scheduled_run_index: {attempt_id}")
        else:
            expected_pairs = {
                "case_id": record.get("case_id"),
                "action_id": record.get("action_id"),
                "phase": record.get("phase"),
                "attempt_round": str(record.get("attempt_round")),
                "block_id": record.get("block_id"),
            }
            for field, actual in expected_pairs.items():
                if str(scheduled.get(field)) != str(actual):
                    semantic_errors.append(f"schedule mismatch for {attempt_id}: {field}")
        if record.get("randomization_deviation") is not None:
            randomization_deviations.append(attempt_id)
        if record.get("retry_of_attempt_id") is None:
            if isinstance(run_index, int) and run_index in primary_by_schedule:
                semantic_errors.append(f"multiple primary attempts for schedule index: {run_index}")
            elif isinstance(run_index, int):
                primary_by_schedule[run_index] = record

    for attempt_id, record in attempts_by_id.items():
        parent_id = record.get("retry_of_attempt_id")
        if parent_id is None:
            continue
        parent = attempts_by_id.get(str(parent_id))
        if parent is None:
            semantic_errors.append(f"retry parent is absent: {attempt_id} -> {parent_id}")
            continue
        for field in ("case_id", "action_id", "phase", "planner_decision_id", "scheduled_run_index"):
            if record.get(field) != parent.get(field):
                semantic_errors.append(f"retry linkage mismatch for {attempt_id}: {field}")

    provenance_errors = validate_provenance(batch)
    semantic_errors.extend(provenance_errors)
    completed_primary: Counter[tuple[str, str]] = Counter()
    for record in primary_by_schedule.values():
        attempt_id = str(record.get("execution_attempt_id", ""))
        constraints = record.get("hard_constraints", {})
        coverage_eligible = (
            record.get("execution_status") == "completed"
            and record.get("context_covariates", {}).get("initial_state_reset") is True
            and record.get("randomization_deviation") is None
            and not resource_missing.get(attempt_id)
            and all(
                constraints.get(field) is True
                for field in ("authorization_satisfied", "data_available", "safety_gate_passed")
            )
            and not constraints.get("violations")
        )
        if coverage_eligible:
            completed_primary[(str(record.get("case_id")), str(record.get("action_id")))] += 1

    expected_actions = {
        (row["case_id"], row["action_id"]) for row in schedule_rows
    }
    minimum = batch.get("protocol", {}).get("coverage_gate", {}).get(
        "minimum_completed_primary_attempts_per_action", 3
    )
    covered = {key for key, count in completed_primary.items() if count >= minimum}
    missing_actions = sorted(expected_actions - covered)
    missing_schedule_indices = sorted(set(schedule_by_index) - set(primary_by_schedule))
    if randomization_deviations:
        warnings.append(
            f"{len(randomization_deviations)} attempts declare randomization deviations requiring adjudication"
        )
    if resource_missing:
        warnings.append(
            f"{len(resource_missing)} attempts have incomplete unit-bearing resource traces"
        )

    schema_valid = not schema_errors
    provenance_valid = not provenance_errors
    schedule_compliant = not schedule_errors and not any(
        error.startswith(("schedule mismatch", "attempt references unknown", "multiple primary", "duplicate schedule"))
        for error in semantic_errors
    ) and not randomization_deviations
    coverage_gate_passed = bool(expected_actions) and not missing_actions
    resource_trace_complete = not resource_missing
    measurement_batch_ready = (
        schema_valid
        and not semantic_errors
        and provenance_valid
        and schedule_compliant
        and coverage_gate_passed
        and resource_trace_complete
        and not missing_schedule_indices
        and execution_authorized
    )
    blocking_reasons: list[str] = []
    if not batch.get("records"):
        blocking_reasons.append("no_real_operational_measurement_records")
    if missing_schedule_indices:
        blocking_reasons.append("scheduled_primary_attempts_missing")
    if not coverage_gate_passed:
        blocking_reasons.append("coverage_smoke_gate_incomplete")
    if not resource_trace_complete:
        blocking_reasons.append("unit_bearing_resource_trace_incomplete")
    if not schedule_compliant:
        blocking_reasons.append("randomization_or_schedule_noncompliance")
    if schema_errors or semantic_errors:
        blocking_reasons.append("measurement_validation_failed")
    if not execution_authorized:
        blocking_reasons.append("action_executor_registry_not_frozen_or_execution_authorized")
    blocking_reasons.extend(
        [
            "statistical_sufficiency_not_established_by_coverage_gate",
            "scalar_cost_transformation_model_not_calibrated_or_frozen",
        ]
    )
    return {
        "validation_status": "passed" if schema_valid and not semantic_errors else "failed",
        "schema_valid": schema_valid,
        "provenance_valid": provenance_valid,
        "schedule_compliant": schedule_compliant,
        "resource_trace_complete": resource_trace_complete,
        "action_executor_registry_integrity_valid": registry_integrity_valid,
        "execution_authorized": execution_authorized,
        "record_count": len(batch.get("records", [])),
        "planner_decision_count": len(
            {str(row.get("planner_decision_id")) for row in batch.get("records", [])}
        ),
        "execution_attempt_count": len(attempts_by_id),
        "primitive_operation_count": sum(
            row.get("primitive_operation_count", 0)
            for row in batch.get("records", [])
            if isinstance(row.get("primitive_operation_count"), int)
        ),
        "retry_attempt_count": sum(
            row.get("retry_of_attempt_id") is not None for row in batch.get("records", [])
        ),
        "scheduled_primary_attempt_count": len(schedule_rows),
        "observed_primary_attempt_count": len(primary_by_schedule),
        "missing_scheduled_primary_attempt_count": len(missing_schedule_indices),
        "expected_action_count": len(expected_actions),
        "covered_action_count": len(covered & expected_actions),
        "missing_action_count": len(missing_actions),
        "missing_actions": [f"{case_id}/{action_id}" for case_id, action_id in missing_actions],
        "resource_incomplete_attempts": resource_missing,
        "randomization_deviation_attempts": randomization_deviations,
        "coverage_gate_passed": coverage_gate_passed,
        "statistical_sufficiency_established": False,
        "measurement_batch_ready": measurement_batch_ready,
        "formal_measured_cost_profile_ready": False,
        "schema_errors": schema_errors,
        "semantic_errors": semantic_errors,
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
        "batch_sha256": file_sha256(batch_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    report = validate_batch(args.batch, args.schema)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["validation_status"] == "passed" else 1)


if __name__ == "__main__":
    main()
