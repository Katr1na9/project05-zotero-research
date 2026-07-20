#!/usr/bin/env python3
"""Validate the outcome-free v0.3 C13+ final-blind intake contract."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def load_legacy_validator() -> Any:
    path = Path(__file__).with_name("validate_m3star_final_blind_intake.py")
    spec = importlib.util.spec_from_file_location("legacy_final_blind_intake", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


legacy = load_legacy_validator()
INTAKE_CONTRACT_VERSION = "0.3.0"
INDEPENDENT_UNIT = legacy.INDEPENDENT_UNIT
INDEPENDENCE_BASIS = legacy.INDEPENDENCE_BASIS
MINIMUM_VALID_CASES = 59
MAXIMUM_STAGED_CASES = 95
DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data_schema"
    / "m3star_final_blind_intake_manifest_v03.schema.json"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    legacy.write_json(path, value)


def validate_schema(manifest: dict[str, Any], schema_path: Path) -> None:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "<root>"
        raise ValueError(f"v0.3 intake schema violation at {location}: {error.message}")


def validate_manifest(
    manifest: dict[str, Any],
    expected_case_ids: list[str],
    used_campaign_registry_path: Path,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Return a label-free v0.3 intake audit or raise on contract drift."""
    validate_schema(manifest, schema_path)
    if manifest.get("intake_contract_version") != INTAKE_CONTRACT_VERSION:
        raise ValueError("Final-blind intake contract version mismatch")
    case_count = manifest.get("case_count")
    if not isinstance(case_count, int) or isinstance(case_count, bool):
        raise ValueError("case_count must be an integer")
    if not MINIMUM_VALID_CASES <= case_count <= MAXIMUM_STAGED_CASES:
        raise ValueError("case_count must be between 59 and 95 independent cases")
    case_ids = manifest.get("case_ids")
    if case_ids != expected_case_ids:
        raise ValueError("case_ids order/identity differs from observed final cases")
    if case_count != len(case_ids):
        raise ValueError("case_count differs from case_ids length")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("case_ids contains duplicate independent cases")
    file_hashes = manifest.get("case_files_sha256")
    if not isinstance(file_hashes, dict) or set(file_hashes) != set(case_ids):
        raise ValueError("case_files_sha256 keys must exactly match case_ids")

    legacy.validate_separation(manifest)
    review = manifest.get("independence_review")
    assert isinstance(review, dict)
    for field in (
        "whole_campaign_execution_is_the_counting_unit",
        "host_time_mask_and_parameter_slices_forbidden",
        "same_scenario_family_counted_once",
        "prior_campaign_overlap_review_complete",
        "source_cluster_recorded_for_sensitivity_analysis",
    ):
        legacy.require_true(review.get(field), f"independence_review.{field}")
    expected_registry_sha256 = legacy.require_sha256(
        review.get("used_campaign_registry_sha256"),
        "independence_review.used_campaign_registry_sha256",
    )
    if expected_registry_sha256 != legacy.sha256(used_campaign_registry_path):
        raise ValueError("Used-campaign registry hash mismatch")
    used_campaign_ids = legacy.validate_used_campaign_registry(
        load_json(used_campaign_registry_path)
    )

    records = manifest.get("case_provenance")
    assert isinstance(records, list)
    if len(records) != case_count:
        raise ValueError("case_provenance count differs from case_count")
    for index, record in enumerate(records):
        legacy.validate_case_record(record, index)
    observed_case_ids = [str(record["case_id"]) for record in records]
    if observed_case_ids != case_ids:
        raise ValueError("case_provenance order/identity differs from case_ids")
    for field, description in (
        ("case_id", "case id"),
        ("scenario_family_id", "scenario family"),
        ("campaign_execution_id", "campaign execution"),
        ("campaign_execution_sha256", "campaign execution fingerprint"),
        ("telemetry_capture_id", "telemetry capture"),
        ("telemetry_capture_sha256", "telemetry capture fingerprint"),
        ("event_namespace_id", "event namespace"),
        ("attack_chain_definition_sha256", "attack-chain definition"),
        ("ground_truth_seal_id", "ground-truth seal"),
        ("cost_measurement_seal_id", "cost-measurement seal"),
    ):
        legacy.require_unique(records, field, description=description)
    overlap = sorted(
        {
            str(record["campaign_execution_id"])
            for record in records
            if record["campaign_execution_id"] in used_campaign_ids
        }
    )
    if overlap:
        raise ValueError(
            "C13+ intake overlaps a campaign used in model development: "
            + ", ".join(overlap)
        )
    source_cluster_counts: dict[str, int] = {}
    for record in records:
        source_cluster = str(record["source_cluster_id"])
        source_cluster_counts[source_cluster] = source_cluster_counts.get(source_cluster, 0) + 1
    return {
        "status": "intake_identity_and_separation_checks_passed",
        "intake_contract_version": INTAKE_CONTRACT_VERSION,
        "minimum_valid_cases": MINIMUM_VALID_CASES,
        "maximum_staged_cases": MAXIMUM_STAGED_CASES,
        "schema_sha256": legacy.sha256(schema_path),
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "case_count": case_count,
        "unique_scenario_family_count": len({record["scenario_family_id"] for record in records}),
        "unique_campaign_execution_count": len({record["campaign_execution_id"] for record in records}),
        "unique_telemetry_capture_count": len({record["telemetry_capture_id"] for record in records}),
        "source_cluster_count": len(source_cluster_counts),
        "source_cluster_case_counts": dict(sorted(source_cluster_counts.items())),
        "prior_campaign_overlap_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--used-campaign-registry", type=Path, required=True)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = load_json(args.manifest)
    report = validate_manifest(
        manifest,
        [str(case_id) for case_id in manifest.get("case_ids", [])],
        args.used_campaign_registry,
        args.schema,
    )
    if args.output is not None:
        write_json(args.output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
