#!/usr/bin/env python3
"""Bind staged-qualified opaque case identities to the final blind manifest."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
IDENTITY_HASH_FIELDS = (
    "source_artifact_sha256",
    "attack_chain_definition_sha256",
    "campaign_execution_sha256",
    "telemetry_capture_sha256",
)
MINIMUM_VALID_CASES = 79
MAXIMUM_STAGED_SLOTS = 95


def load_staged_auditor() -> Any:
    path = Path(__file__).with_name(
        "audit_m3star_blind_staged_candidate_qualification.py"
    )
    spec = importlib.util.spec_from_file_location("staged_qualification_auditor", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


staged = load_staged_auditor()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def require_true(value: Any, field: str) -> None:
    if value is not True:
        raise ValueError(f"{field} must be true")


def require_false(value: Any, field: str) -> None:
    if value is not False:
        raise ValueError(f"{field} must be false")


def identity_rows(items: Any, field: str) -> list[tuple[str, ...]]:
    if not isinstance(items, list):
        raise ValueError(f"{field} must be an array")
    rows: list[tuple[str, ...]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"{field}[{index}] must be an object")
        row = tuple(str(item.get(name, "")) for name in IDENTITY_HASH_FIELDS)
        if any(not SHA256_PATTERN.fullmatch(value) for value in row):
            raise ValueError(f"{field}[{index}] has a malformed identity SHA-256")
        rows.append(row)
    if len(rows) != len(set(rows)):
        raise ValueError(f"{field} contains a duplicate case identity")
    return sorted(rows)


def identity_commitment(rows: list[tuple[str, ...]]) -> str:
    canonical = json.dumps(rows, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_binding(
    amendment_path: Path,
    qualification_report_path: Path,
    qualification_readiness_path: Path,
    dataset_manifest_path: Path,
) -> dict[str, Any]:
    amendment = load_json(amendment_path)
    report = load_json(qualification_report_path)
    readiness = load_json(qualification_readiness_path)
    manifest = load_json(dataset_manifest_path)
    staged_audit = staged.validate_qualification_report(
        report,
        amendment,
        amendment_path,
    )
    if staged_audit.get("status") != "qualification_complete":
        raise ValueError("Staged qualification is not complete")
    if readiness.get("status") != "qualification_complete":
        raise ValueError("Qualification readiness status is not complete")
    require_true(readiness.get("acquisition_complete"), "acquisition_complete")
    if readiness.get("source_search_required") is not False:
        raise ValueError("Qualification still requires source discovery")
    require_true(
        readiness.get("all_qualified_cases_to_be_retained"),
        "all_qualified_cases_to_be_retained",
    )
    require_false(
        readiness.get("unaudited_reserve_slots_counted_as_failures"),
        "unaudited_reserve_slots_counted_as_failures",
    )
    for field in (
        "file_contents_returned_to_model_development",
        "ground_truth_opened",
        "cost_values_opened",
        "model_outputs_opened_during_qualification",
        "one_shot_evaluation_consumed",
    ):
        require_false(readiness.get(field), field)
    for field in (
        "amendment_id",
        "amendment_sha256",
        "audited_candidate_count",
        "actual_qualified_case_count",
        "actual_not_qualified_count",
        "unaudited_reserve_count",
        "decision_basis",
    ):
        if readiness.get(field) != staged_audit.get(field):
            raise ValueError(f"Qualification readiness {field} does not match report audit")
    qualified_count = readiness.get("actual_qualified_case_count")
    if (
        not isinstance(qualified_count, int)
        or isinstance(qualified_count, bool)
        or not MINIMUM_VALID_CASES <= qualified_count <= MAXIMUM_STAGED_SLOTS
    ):
        raise ValueError("Qualified independent-case count must be between 79 and 95")

    if manifest.get("status") != "frozen":
        raise ValueError("Final blind manifest must be frozen")
    for field in (
        "curation_blind_to_model_development",
        "ground_truth_sealed_until_execution",
        "all_cases_new_and_unseen",
        "source_and_attack_chain_deduplication_complete",
    ):
        require_true(manifest.get(field), field)
    case_ids = manifest.get("case_ids")
    if not isinstance(case_ids, list) or len(case_ids) != qualified_count:
        raise ValueError("Final manifest case_ids must contain every qualified case")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("Final manifest has duplicate case_ids")
    if manifest.get("case_count") != qualified_count:
        raise ValueError("Final manifest case_count must equal qualified count")

    qualified_rows = identity_rows(report.get("qualified_cases"), "qualified_cases")
    manifest_rows = identity_rows(manifest.get("case_provenance"), "case_provenance")
    if len(qualified_rows) != qualified_count or len(manifest_rows) != qualified_count:
        raise ValueError("Identity row counts must equal the qualified count")
    if qualified_rows != manifest_rows:
        raise ValueError("Final manifest identity set differs from qualified case set")
    commitment = identity_commitment(qualified_rows)
    return {
        "audit_id": "project05-m3star-blind-qualification-manifest-binding-v0.2",
        "status": "qualification_manifest_binding_complete",
        "checked_utc": utc_now(),
        "staged_amendment_id": amendment["amendment_id"],
        "staged_amendment_sha256": sha256(amendment_path),
        "qualification_report_sha256": sha256(qualification_report_path),
        "qualification_readiness_sha256": sha256(qualification_readiness_path),
        "dataset_manifest_sha256": sha256(dataset_manifest_path),
        "qualified_case_count": qualified_count,
        "final_manifest_case_count": manifest["case_count"],
        "qualified_case_identity_commitment_sha256": commitment,
        "manifest_case_identity_commitment_sha256": commitment,
        "identity_sets_match_exactly": True,
        "all_qualified_cases_retained": True,
        "unaudited_reserve_slots_counted_as_failures": False,
        "telemetry_contents_opened_by_binding_audit": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened": False,
        "one_shot_evaluation_consumed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--qualification-report", type=Path, required=True)
    parser.add_argument("--qualification-readiness", type=Path, required=True)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    audit = validate_binding(
        args.amendment.resolve(strict=True),
        args.qualification_report.resolve(strict=True),
        args.qualification_readiness.resolve(strict=True),
        args.dataset_manifest.resolve(strict=True),
    )
    if args.output is not None:
        write_json(args.output, audit)
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
