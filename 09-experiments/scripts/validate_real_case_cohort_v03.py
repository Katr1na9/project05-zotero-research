#!/usr/bin/env python3
"""Validate the real-only canonical cohort and its source alias chain."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_SCHEMA = EXP / "data_schema" / "real_case_cohort.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_reference(value: Any) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def validate_cohort(
    cohort_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    verify_artifact_bytes: bool = False,
) -> dict[str, Any]:
    cohort = load_json(cohort_path)
    validator = Draft202012Validator(
        load_json(schema_path), format_checker=FormatChecker()
    )
    schema_errors = [
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(cohort), key=lambda item: list(item.path))
    ]
    semantic_errors: list[str] = []
    cases = cohort.get("cases", [])
    canonical_ids = [row.get("canonical_case_id") for row in cases]
    source_ids = [row.get("source_case_id") for row in cases]
    if canonical_ids != [f"C{number:02d}" for number in range(1, 10)]:
        semantic_errors.append("canonical case IDs must be ordered exactly C01-C09")
    if len(source_ids) != len(set(source_ids)):
        semantic_errors.append("source case IDs are not unique")
    verified_artifacts = 0
    declared_artifacts = 0
    for row in cases:
        canonical_id = str(row.get("canonical_case_id"))
        case_dir = resolve_reference(row.get("source_case_path"))
        config_path = case_dir / "case_config.json"
        if not config_path.is_file():
            semantic_errors.append(f"source case config unavailable: {canonical_id}")
        else:
            config = load_json(config_path)
            if config.get("case_id") != row.get("source_case_id"):
                semantic_errors.append(f"source case ID mismatch: {canonical_id}")
            if file_sha256(config_path) != row.get("source_case_config_sha256"):
                semantic_errors.append(f"source case config hash mismatch: {canonical_id}")
        expected_phase = "calibration" if canonical_id in {"C01", "C02", "C03"} else "development"
        if row.get("phase") != expected_phase:
            semantic_errors.append(f"phase mismatch: {canonical_id}")
        for replay in row.get("replay_artifacts", []):
            declared_artifacts += 1
            path = resolve_reference(replay.get("path"))
            if not path.is_file():
                semantic_errors.append(f"replay artifact unavailable: {canonical_id}/{path}")
                continue
            if path.stat().st_size != replay.get("size_bytes"):
                semantic_errors.append(f"replay artifact size mismatch: {canonical_id}/{path}")
            digest_source = replay.get("declared_digest_source", {})
            digest_path = resolve_reference(digest_source.get("path"))
            if not digest_path.is_file():
                semantic_errors.append(f"declared digest source unavailable: {canonical_id}/{digest_path}")
            elif file_sha256(digest_path) != digest_source.get("sha256"):
                semantic_errors.append(f"declared digest source hash mismatch: {canonical_id}/{digest_path}")
            if verify_artifact_bytes:
                if file_sha256(path) != replay.get("sha256"):
                    semantic_errors.append(f"replay artifact hash mismatch: {canonical_id}/{path}")
                else:
                    verified_artifacts += 1
    toy_ids: list[str] = []
    for row in cohort.get("toy_exclusions", []):
        case_dir = resolve_reference(row.get("source_case_path"))
        config_path = case_dir / "case_config.json"
        if not config_path.is_file():
            semantic_errors.append(f"toy source config unavailable: {case_dir}")
            continue
        config = load_json(config_path)
        toy_ids.append(str(config.get("case_id")))
        if config.get("case_id") != row.get("source_case_id"):
            semantic_errors.append(f"toy source case ID mismatch: {case_dir}")
        if file_sha256(config_path) != row.get("source_case_config_sha256"):
            semantic_errors.append(f"toy source config hash mismatch: {case_dir}")
    if len(toy_ids) != 3 or any(not value.startswith(("C01", "C02", "C03")) for value in toy_ids):
        semantic_errors.append("toy exclusion set does not exactly represent source C01-C03")
    return {
        "cohort_path": str(cohort_path.resolve()),
        "schema_valid": not schema_errors,
        "source_alias_valid": not semantic_errors,
        "canonical_case_count": len(cases),
        "toy_exclusion_count": len(cohort.get("toy_exclusions", [])),
        "calibration_case_count": sum(row.get("phase") == "calibration" for row in cases),
        "development_case_count": sum(row.get("phase") == "development" for row in cases),
        "declared_replay_artifact_count": declared_artifacts,
        "artifact_byte_verification_requested": verify_artifact_bytes,
        "artifact_byte_verified_count": verified_artifacts,
        "formal_ready": not schema_errors and not semantic_errors and cohort.get("status") == "frozen",
        "errors": schema_errors + semantic_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cohort", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--verify-artifact-bytes", action="store_true")
    args = parser.parse_args()
    report = validate_cohort(
        args.cohort, args.schema, args.verify_artifact_bytes
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if not report["errors"] else 1)


if __name__ == "__main__":
    main()
