#!/usr/bin/env python3
"""Import externally sourced actor and analyst-utility ground truth records."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
VALIDATOR_PATH = Path(__file__).with_name("validate_external_ground_truth.py")


def load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("external_gt_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() == ".jsonl":
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        value = json.loads(path.read_text(encoding="utf-8"))
        records = value.get("records", []) if isinstance(value, dict) else value
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError(f"External ground-truth source must contain a record array: {path}")
    return records


def import_ground_truth(
    input_dir: Path,
    output_dir: Path,
    case_dirs: list[Path],
    created_utc: str,
) -> dict[str, Any]:
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise FileExistsError(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    sources = sorted(
        path for path in input_dir.glob("*") if path.suffix.casefold() in {".json", ".jsonl"}
    ) if input_dir.exists() else []
    records: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    for source in sources:
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        raw_records = read_records(source)
        for raw in raw_records:
            record = dict(raw)
            record["normalized_source"] = {
                "source_file": source.resolve().as_posix(),
                "source_file_sha256": source_hash,
                "record_sha256": canonical_sha256(raw),
            }
            records.append(record)
        source_files.append(
            {"path": source.resolve().as_posix(), "sha256": source_hash, "record_count": len(raw_records)}
        )
    records.sort(key=lambda row: (str(row.get("case_id", "")), str(row.get("ground_truth_type", "")), str(row.get("record_id", ""))))
    bundle = {
        "bundle_id": "project05-external-ground-truth-v0.1",
        "version": "0.1.0",
        "created_utc": created_utc,
        "records": records,
        "source_files": source_files,
    }
    bundle_path = output_dir / "external_ground_truth_bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = VALIDATOR.validate_bundle(bundle_path, case_dirs)
    report_path = output_dir / "external_ground_truth_validation.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        "interface_status": "implemented",
        "external_actor_accuracy": None,
        "external_actor_accuracy_status": report["external_actor_accuracy_status"],
        "analyst_utility_status": report["analyst_utility_status"],
        "blocking_reasons": report["blocking_reasons"],
        "output_sha256": {
            bundle_path.name: hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
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
    manifest = import_ground_truth(
        args.input_dir,
        args.output_dir,
        VALIDATOR.discover_case_dirs(args.examples_dir, args.real_cases_dir),
        args.created_utc,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
