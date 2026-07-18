#!/usr/bin/env python3
"""Import v0.3 JSON/JSONL attempt telemetry into a provenance-locked batch."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_PROTOCOL = (
    EXP
    / "governance"
    / "measurement_v0.3"
    / "operational-cost-measurement-protocol-v0.3.json"
)
VALIDATOR_PATH = Path(__file__).with_name(
    "validate_operational_cost_measurements_v03.py"
)
PROTOCOL_BATCH_KEYS = (
    "protocol_id",
    "ontology_profile",
    "action_executor_registry",
    "execution_readiness",
    "schedule_authorization",
    "experimental_unit",
    "coverage_gate",
    "statistical_sufficiency",
    "randomization",
    "blocking",
    "failure_policy",
    "retry_policy",
    "shared_overhead_policy",
    "scalar_cost_status",
)


def load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("operational_cost_v03_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_reference(value: Any) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_records(path: Path) -> list[dict[str, Any]]:
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
        raise ValueError(f"Measurement source must contain an object array: {path}")
    return records


def normalize_record(
    record: dict[str, Any], source_path: Path, source_hash: str
) -> dict[str, Any]:
    normalized = dict(record)
    normalized["source_file"] = source_path.resolve().as_posix()
    normalized["source_file_sha256"] = source_hash
    normalized["record_sha256"] = canonical_sha256(record)
    return normalized


def measurement_availability_status(records: list[dict[str, Any]]) -> str:
    if not records:
        return "blocked_no_real_measurements"
    capability_pilot_only = all(
        isinstance(row.get("randomization_deviation"), dict)
        and row["randomization_deviation"].get("deviation_type")
        == "unscheduled_capability_pilot"
        for row in records
    )
    if capability_pilot_only:
        return "capability_pilot_only_not_formal_schedule_measurement"
    return "available"


def import_measurements(
    input_dir: Path,
    output_dir: Path,
    protocol_path: Path,
    created_utc: str,
) -> dict[str, Any]:
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise FileExistsError(f"Refusing to overwrite non-empty output: {output_dir}")
    protocol_document = load_json(protocol_path)
    missing_keys = [key for key in PROTOCOL_BATCH_KEYS if key not in protocol_document]
    if missing_keys:
        raise ValueError(f"Protocol omits required batch fields: {missing_keys}")
    schedule = protocol_document.get("schedule")
    if not isinstance(schedule, dict):
        raise ValueError("Protocol does not contain a schedule declaration")
    ontology_meta = protocol_document.get("ontology_profile", {})
    ontology_path = resolve_reference(ontology_meta.get("path", ""))
    if not ontology_path.is_file() or file_sha256(ontology_path) != ontology_meta.get("sha256"):
        raise ValueError("Protocol ontology profile is unavailable or hash-mismatched")
    registry_meta = protocol_document.get("action_executor_registry", {})
    registry_path = resolve_reference(registry_meta.get("path", ""))
    if not registry_path.is_file() or file_sha256(registry_path) != registry_meta.get("sha256"):
        raise ValueError("Protocol action executor registry is unavailable or hash-mismatched")
    schedule_path = resolve_reference(schedule.get("path", ""))
    if not schedule_path.is_file() or file_sha256(schedule_path) != schedule.get("sha256"):
        raise ValueError("Protocol schedule is unavailable or hash-mismatched")

    source_paths = (
        sorted(
            path
            for path in input_dir.iterdir()
            if path.suffix.casefold() in {".json", ".jsonl"}
        )
        if input_dir.is_dir()
        else []
    )
    normalized: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    for source_path in source_paths:
        source_hash = file_sha256(source_path)
        records = read_records(source_path)
        normalized.extend(
            normalize_record(record, source_path, source_hash) for record in records
        )
        source_files.append(
            {
                "path": source_path.resolve().as_posix(),
                "sha256": source_hash,
                "record_count": len(records),
            }
        )
    normalized.sort(
        key=lambda row: (
            int(row.get("scheduled_run_index", 0)),
            row.get("retry_of_attempt_id") is not None,
            str(row.get("execution_attempt_id", "")),
        )
    )
    batch = {
        "batch_id": "project05-operational-cost-measurements-v0.3",
        "version": "0.3.0",
        "created_utc": created_utc,
        "protocol": {key: protocol_document[key] for key in PROTOCOL_BATCH_KEYS},
        "schedule": schedule,
        "records": normalized,
        "source_files": source_files,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_path = output_dir / "operational_cost_measurements_v0.3.json"
    batch_path.write_text(
        json.dumps(batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    report = VALIDATOR.validate_batch(batch_path)
    report_path = output_dir / "measurement_validation_report_v0.3.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    manifest = {
        "infrastructure_status": "implemented_v0.3",
        "real_measurement_status": measurement_availability_status(normalized),
        "capability_pilot_record_count": sum(
            isinstance(row.get("randomization_deviation"), dict)
            and row["randomization_deviation"].get("deviation_type")
            == "unscheduled_capability_pilot"
            for row in normalized
        ),
        "formal_schedule_measurement_record_count": sum(
            row.get("randomization_deviation") is None for row in normalized
        ),
        "measurement_batch_ready": report["measurement_batch_ready"],
        "coverage_gate_passed": report["coverage_gate_passed"],
        "statistical_sufficiency_established": False,
        "formal_measured_cost_profile_ready": False,
        "blocking_reasons": report["blocking_reasons"],
        "output_sha256": {
            batch_path.name: file_sha256(batch_path),
            report_path.name: file_sha256(report_path),
        },
        "paper_or_patent_gate": "closed_until_measurement_statistical_and_transformation_gates_are_satisfied",
        "paper_or_patent_updated": False,
    }
    manifest_path = output_dir / "evaluation_manifest_v0.3.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--created-utc", default="2026-07-18T00:00:00Z")
    args = parser.parse_args()
    manifest = import_measurements(
        args.input_dir, args.output_dir, args.protocol, args.created_utc
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
