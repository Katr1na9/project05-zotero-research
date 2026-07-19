#!/usr/bin/env python3
"""Validate C13+ final-blind provenance without opening labels or ground truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CASE_ID_PATTERN = re.compile(r"^C(\d+)(?:-|$)")
INTAKE_CONTRACT_VERSION = "0.1.0"
INDEPENDENT_UNIT = "whole_campaign_execution"
INDEPENDENCE_BASIS = "unique_attack_chain_definition_and_execution"


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


def require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def require_sha256(value: Any, field: str) -> str:
    text = require_nonempty_string(value, field).lower()
    if not SHA256_PATTERN.fullmatch(text):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return text


def require_true(value: Any, field: str) -> None:
    if value is not True:
        raise ValueError(f"{field} must be true")


def require_null(value: Any, field: str) -> None:
    if value is not None:
        raise ValueError(f"{field} must be null")


def require_unique(
    records: list[dict[str, Any]],
    field: str,
    *,
    description: str,
) -> None:
    values = [record[field] for record in records]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(
            f"Duplicate {description}; repeated cases are pseudoreplication: "
            + ", ".join(str(value) for value in duplicates[:5])
        )


def validate_used_campaign_registry(registry: dict[str, Any]) -> set[str]:
    if registry.get("status") != "frozen_before_c13_plus_intake":
        raise ValueError("Used-campaign registry is not frozen")
    if registry.get("independent_unit") != INDEPENDENT_UNIT:
        raise ValueError("Used-campaign registry has the wrong independent unit")
    campaigns = registry.get("used_campaigns")
    if not isinstance(campaigns, list) or not campaigns:
        raise ValueError("Used-campaign registry has no prior campaigns")
    identifiers: list[str] = []
    for index, record in enumerate(campaigns):
        if not isinstance(record, dict):
            raise ValueError(f"used_campaigns[{index}] must be an object")
        identifiers.append(
            require_nonempty_string(
                record.get("campaign_execution_id"),
                f"used_campaigns[{index}].campaign_execution_id",
            )
        )
        prior_case_ids = record.get("prior_case_ids")
        if not isinstance(prior_case_ids, list) or not prior_case_ids:
            raise ValueError(f"used_campaigns[{index}].prior_case_ids is empty")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Used-campaign registry contains duplicate identifiers")
    return set(identifiers)


def validate_separation(manifest: dict[str, Any]) -> None:
    separation = manifest.get("curation_and_seal_separation")
    if not isinstance(separation, dict):
        raise ValueError("Missing curation_and_seal_separation")
    curation_team = require_nonempty_string(
        separation.get("curation_team_id"),
        "curation_and_seal_separation.curation_team_id",
    )
    model_team = require_nonempty_string(
        separation.get("model_development_team_id"),
        "curation_and_seal_separation.model_development_team_id",
    )
    custodian = require_nonempty_string(
        separation.get("ground_truth_custodian_id"),
        "curation_and_seal_separation.ground_truth_custodian_id",
    )
    if len({curation_team, model_team, custodian}) != 3:
        raise ValueError(
            "Curation, model-development, and ground-truth-custodian identities "
            "must be distinct"
        )
    for field in (
        "teams_are_disjoint",
        "curators_blind_to_model_outputs",
        "model_developers_blind_to_c13_plus_contents",
        "ground_truth_custodian_not_a_model_developer",
        "cost_measurement_completed_without_model_output_access",
    ):
        require_true(
            separation.get(field),
            f"curation_and_seal_separation.{field}",
        )


def validate_case_record(record: dict[str, Any], index: int) -> None:
    prefix = f"case_provenance[{index}]"
    case_id = require_nonempty_string(record.get("case_id"), f"{prefix}.case_id")
    match = CASE_ID_PATTERN.match(case_id)
    if match is None or int(match.group(1)) < 13:
        raise ValueError(f"{prefix}.case_id must be a canonical C13+ id")
    for field in (
        "source_cluster_id",
        "source_release_id",
        "source_record_locator",
        "scenario_family_id",
        "campaign_execution_id",
        "telemetry_capture_id",
        "event_namespace_id",
        "ground_truth_seal_id",
        "cost_measurement_seal_id",
    ):
        require_nonempty_string(record.get(field), f"{prefix}.{field}")
    for field in (
        "source_artifact_sha256",
        "attack_chain_definition_sha256",
        "campaign_execution_sha256",
        "telemetry_capture_sha256",
    ):
        require_sha256(record.get(field), f"{prefix}.{field}")
    if record.get("independent_unit") != INDEPENDENT_UNIT:
        raise ValueError(f"{prefix}.independent_unit must be {INDEPENDENT_UNIT}")
    if record.get("independence_basis") != INDEPENDENCE_BASIS:
        raise ValueError(
            f"{prefix}.independence_basis must be {INDEPENDENCE_BASIS}"
        )
    for field in (
        "original_telemetry_present",
        "multi_stage_attack_chain_present",
        "full_campaign_time_window_included",
        "all_in_scope_campaign_hosts_combined",
        "not_a_host_slice",
        "not_a_time_slice",
        "not_a_mask_variant",
        "not_a_parameter_only_variant",
        "not_used_in_model_development",
        "ground_truth_sealed",
        "cost_values_sealed_from_model_development",
    ):
        require_true(record.get(field), f"{prefix}.{field}")
    for field in (
        "parent_campaign_execution_id",
        "derived_from_case_id",
        "mask_variant_of_case_id",
        "parameter_variant_of_scenario_family_id",
    ):
        require_null(record.get(field), f"{prefix}.{field}")


def validate_manifest(
    manifest: dict[str, Any],
    expected_case_ids: list[str],
    used_campaign_registry_path: Path,
) -> dict[str, Any]:
    """Return a label-free audit report or raise on leakage/pseudoreplication."""
    if manifest.get("intake_contract_version") != INTAKE_CONTRACT_VERSION:
        raise ValueError("Final-blind intake contract version mismatch")
    validate_separation(manifest)

    review = manifest.get("independence_review")
    if not isinstance(review, dict):
        raise ValueError("Missing independence_review")
    for field in (
        "whole_campaign_execution_is_the_counting_unit",
        "host_time_mask_and_parameter_slices_forbidden",
        "same_scenario_family_counted_once",
        "prior_campaign_overlap_review_complete",
        "source_cluster_recorded_for_sensitivity_analysis",
    ):
        require_true(review.get(field), f"independence_review.{field}")
    expected_registry_sha256 = require_sha256(
        review.get("used_campaign_registry_sha256"),
        "independence_review.used_campaign_registry_sha256",
    )
    observed_registry_sha256 = sha256(used_campaign_registry_path)
    if expected_registry_sha256 != observed_registry_sha256:
        raise ValueError("Used-campaign registry hash mismatch")
    used_campaign_ids = validate_used_campaign_registry(
        load_json(used_campaign_registry_path)
    )

    records = manifest.get("case_provenance")
    if not isinstance(records, list):
        raise ValueError("case_provenance must be an array")
    if len(records) != len(expected_case_ids):
        raise ValueError("case_provenance count differs from the final case count")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"case_provenance[{index}] must be an object")
        validate_case_record(record, index)
    observed_case_ids = [str(record["case_id"]) for record in records]
    if observed_case_ids != expected_case_ids:
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
        require_unique(records, field, description=description)

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
        source_cluster_counts[source_cluster] = (
            source_cluster_counts.get(source_cluster, 0) + 1
        )
    return {
        "status": "intake_identity_and_separation_checks_passed",
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "case_count": len(records),
        "unique_scenario_family_count": len(
            {record["scenario_family_id"] for record in records}
        ),
        "unique_campaign_execution_count": len(
            {record["campaign_execution_id"] for record in records}
        ),
        "unique_telemetry_capture_count": len(
            {record["telemetry_capture_id"] for record in records}
        ),
        "source_cluster_count": len(source_cluster_counts),
        "source_cluster_case_counts": dict(sorted(source_cluster_counts.items())),
        "prior_campaign_overlap_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--used-campaign-registry", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = load_json(args.manifest)
    case_ids = [str(case_id) for case_id in manifest.get("case_ids", [])]
    report = validate_manifest(
        manifest,
        case_ids,
        args.used_campaign_registry,
    )
    if args.output is not None:
        write_json(args.output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
