#!/usr/bin/env python3
"""Import JSON/JSONL operational telemetry into a provenance-locked batch."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
VALIDATOR_PATH = Path(__file__).with_name("validate_operational_cost_measurements.py")


def load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("operational_cost_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


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
        value = json.loads(path.read_text(encoding="utf-8"))
        records = value.get("records", []) if isinstance(value, dict) else value
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError(f"Measurement source must contain a record array: {path}")
    return records


def normalize_record(record: dict[str, Any], source: Path, source_hash: str) -> dict[str, Any]:
    normalized = dict(record)
    normalized["source_file"] = source.resolve().as_posix()
    normalized["source_file_sha256"] = source_hash
    normalized["record_sha256"] = canonical_sha256(record)
    return normalized


def import_measurements(
    input_dir: Path,
    output_dir: Path,
    case_dirs: list[Path],
    created_utc: str,
) -> dict[str, Any]:
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise FileExistsError(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    source_paths = sorted(
        path for path in input_dir.glob("*") if path.suffix.casefold() in {".json", ".jsonl"}
    ) if input_dir.exists() else []
    normalized: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    for path in source_paths:
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        records = read_records(path)
        normalized.extend(normalize_record(record, path, source_hash) for record in records)
        source_files.append(
            {"path": path.resolve().as_posix(), "sha256": source_hash, "record_count": len(records)}
        )
    normalized.sort(key=lambda row: (str(row.get("case_id", "")), str(row.get("action_id", "")), str(row.get("attempt_id", "")), str(row.get("measurement_id", ""))))
    batch = {
        "batch_id": "project05-operational-cost-measurements-v0.1",
        "version": "0.1.0",
        "created_utc": created_utc,
        "records": normalized,
        "source_files": source_files,
    }
    batch_path = output_dir / "operational_cost_measurements.json"
    batch_path.write_text(
        json.dumps(batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    report = VALIDATOR.validate_batch(batch_path, case_dirs)
    report_path = output_dir / "measurement_validation_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    manifest = {
        "infrastructure_status": "implemented",
        "real_measurement_status": (
            "available" if report["record_count"] else "blocked_no_real_measurements"
        ),
        "measurement_batch_ready": report["measurement_batch_ready"],
        "formal_measured_cost_profile_ready": False,
        "blocking_reasons": report["blocking_reasons"],
        "output_sha256": {
            batch_path.name: hashlib.sha256(batch_path.read_bytes()).hexdigest(),
            report_path.name: hashlib.sha256(report_path.read_bytes()).hexdigest(),
        },
        "all_experiments_complete": False,
        "paper_or_patent_gate": "closed_until_human_and_operational_gates_are_satisfied",
        "paper_or_patent_updated": False,
    }
    (output_dir / "evaluation_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--examples-dir", type=Path, default=EXP / "examples")
    parser.add_argument("--real-cases-dir", type=Path, default=EXP / "real_cases")
    parser.add_argument("--created-utc", default="2026-07-14T08:00:00Z")
    args = parser.parse_args()
    case_dirs = VALIDATOR.discover_case_dirs(args.examples_dir, args.real_cases_dir)
    manifest = import_measurements(
        args.input_dir, args.output_dir, case_dirs, args.created_utc
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
