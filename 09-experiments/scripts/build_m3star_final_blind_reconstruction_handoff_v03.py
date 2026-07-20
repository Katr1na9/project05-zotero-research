#!/usr/bin/env python3
"""Build a payload-free handoff for reconstructing the 59 qualified blind cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
IDENTITY_HASH_FIELDS = (
    "source_artifact_sha256",
    "attack_chain_definition_sha256",
    "campaign_execution_sha256",
    "telemetry_capture_sha256",
)
EXPECTED_QUALIFIED_CASES = 59
FIRST_FINAL_CASE_NUMBER = 13
REQUIRED_CASE_FILES = (
    "case_config.json",
    "evidence_claims.json",
    "acquisition_actions.json",
)
CURATOR_SUPPLIED_MANIFEST_FIELDS = (
    "source_record_locator",
    "scenario_family_id",
    "campaign_execution_id",
    "telemetry_capture_id",
    "event_namespace_id",
)


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


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def require_hash(value: Any, field: str) -> str:
    text = require_string(value, field)
    if not SHA256_PATTERN.fullmatch(text):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return text


def identity_commitment(rows: list[tuple[str, ...]]) -> str:
    canonical = json.dumps(sorted(rows), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_handoff(
    report: dict[str, Any],
    *,
    report_path: Path,
    created_utc: str,
) -> dict[str, Any]:
    if report.get("reported_qualified_count") != EXPECTED_QUALIFIED_CASES:
        raise ValueError("Qualification report must contain exactly 59 retained cases")
    if report.get("all_qualified_cases_retained") is not True:
        raise ValueError("Qualification report does not retain every qualified case")
    if report.get("qualification_rules_changed_after_access") is not False:
        raise ValueError("Qualification rules changed after access")
    if report.get("case_selection_used_model_outputs") is not False:
        raise ValueError("Qualification used model outputs")
    if report.get("within_case_conditions_counted_as_independent_cases") is not False:
        raise ValueError("Within-case conditions were counted as independent cases")
    cases = report.get("qualified_cases")
    if not isinstance(cases, list) or len(cases) != EXPECTED_QUALIFIED_CASES:
        raise ValueError("qualified_cases must contain exactly 59 records")

    assignments: list[dict[str, Any]] = []
    identity_rows: list[tuple[str, ...]] = []
    seen_qualification_ids: set[str] = set()
    artifact_groups: dict[str, list[str]] = defaultdict(list)
    release_groups: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"final_case_ids": set(), "source_artifact_sha256": set()}
    )
    source_counts: Counter[str] = Counter()
    source_cluster_counts: Counter[str] = Counter()
    for offset, item in enumerate(cases):
        if not isinstance(item, dict):
            raise ValueError(f"qualified_cases[{offset}] must be an object")
        qualification_case_id = require_string(
            item.get("qualification_case_id"),
            f"qualified_cases[{offset}].qualification_case_id",
        )
        if qualification_case_id in seen_qualification_ids:
            raise ValueError(f"Duplicate qualification case id: {qualification_case_id}")
        seen_qualification_ids.add(qualification_case_id)
        row = tuple(
            require_hash(item.get(field), f"qualified_cases[{offset}].{field}")
            for field in IDENTITY_HASH_FIELDS
        )
        identity_rows.append(row)
        scenario_family_sha256 = require_hash(
            item.get("scenario_family_sha256"),
            f"qualified_cases[{offset}].scenario_family_sha256",
        )
        final_case_id = f"C{FIRST_FINAL_CASE_NUMBER + offset:03d}-final-blind"
        source_id = require_string(item.get("source_id"), f"qualified_cases[{offset}].source_id")
        source_cluster_id = require_string(
            item.get("source_cluster_id"),
            f"qualified_cases[{offset}].source_cluster_id",
        )
        source_release_id = require_string(
            item.get("source_release_id"),
            f"qualified_cases[{offset}].source_release_id",
        )
        source_counts[source_id] += 1
        source_cluster_counts[source_cluster_id] += 1
        artifact_groups[row[0]].append(final_case_id)
        release_group = release_groups[(source_id, source_release_id)]
        release_group["final_case_ids"].add(final_case_id)
        release_group["source_artifact_sha256"].add(row[0])
        assignments.append(
            {
                "reconstruction_index": offset + 1,
                "final_case_id": final_case_id,
                "qualification_case_id": qualification_case_id,
                "source_id": source_id,
                "candidate_key": (
                    str(item["candidate_key"])
                    if item.get("candidate_key") not in (None, "")
                    else None
                ),
                "source_cluster_id": source_cluster_id,
                "source_release_id": source_release_id,
                "source_artifact_sha256": row[0],
                "qualification_only_scenario_family_sha256": scenario_family_sha256,
                "attack_chain_definition_sha256": row[1],
                "campaign_execution_sha256": row[2],
                "telemetry_capture_sha256": row[3],
                "ground_truth_seal_id": require_string(
                    item.get("ground_truth_seal_id"),
                    f"qualified_cases[{offset}].ground_truth_seal_id",
                ),
                "cost_measurement_seal_id": require_string(
                    item.get("cost_measurement_seal_id"),
                    f"qualified_cases[{offset}].cost_measurement_seal_id",
                ),
                "required_case_files": list(REQUIRED_CASE_FILES),
                "required_curator_supplied_manifest_fields": list(
                    CURATOR_SUPPLIED_MANIFEST_FIELDS
                ),
                "reconstruction_status": "pending_isolated_curator_reacquisition",
            }
        )
    if len(set(identity_rows)) != EXPECTED_QUALIFIED_CASES:
        raise ValueError("Qualified identity tuples are not unique")

    artifact_reacquisition_groups = [
        {
            "source_artifact_sha256": artifact_hash,
            "expected_final_case_count": len(case_ids),
            "final_case_ids": case_ids,
            "reacquire_once_then_extract_only_bound_campaigns": True,
        }
        for artifact_hash, case_ids in sorted(artifact_groups.items())
    ]
    source_release_reacquisition_batches = [
        {
            "source_id": source_id,
            "source_release_id": source_release_id,
            "expected_final_case_count": len(group["final_case_ids"]),
            "final_case_ids": sorted(group["final_case_ids"]),
            "bound_source_artifact_sha256": sorted(
                group["source_artifact_sha256"]
            ),
            "prefer_single_authoritative_release_acquisition": True,
        }
        for (source_id, source_release_id), group in sorted(release_groups.items())
    ]
    return {
        "handoff_id": "project05-m3star-final-blind-reconstruction-handoff-v0.3",
        "status": "awaiting_isolated_curator_reconstruction",
        "created_utc": created_utc,
        "qualification_report_path": report_path.as_posix(),
        "qualification_report_sha256": sha256(report_path),
        "qualified_case_count": EXPECTED_QUALIFIED_CASES,
        "final_case_id_first": assignments[0]["final_case_id"],
        "final_case_id_last": assignments[-1]["final_case_id"],
        "identity_hash_fields": list(IDENTITY_HASH_FIELDS),
        "qualified_identity_commitment_sha256": identity_commitment(identity_rows),
        "unique_source_artifact_count": len(artifact_reacquisition_groups),
        "preferred_source_release_batch_count": len(
            source_release_reacquisition_batches
        ),
        "source_case_counts": dict(sorted(source_counts.items())),
        "source_cluster_case_counts": dict(sorted(source_cluster_counts.items())),
        "reacquisition_policy": {
            "download_each_unique_source_artifact_at_most_once": True,
            "prefer_one_download_per_authoritative_source_release": True,
            "verify_source_artifact_sha256_before_extraction": True,
            "extract_only_campaigns_bound_in_case_assignments": True,
            "payload_contents_returned_to_model_development": False,
            "ground_truth_returned_to_model_development_before_one_shot": False,
            "measured_cost_values_returned_to_model_development": False,
            "model_or_baseline_outputs_available_to_curator": False,
        },
        "required_handoff_outputs": [
            "59 complete case directories under 09-experiments/final_blind/cases",
            "dataset-manifest-v0.3.json with exact assignment order and file hashes",
            "sealed ground-truth entities bound to every ground_truth_seal_id",
            "separate measured-cost-profile-v0.3.json covering the exact 59 case_ids",
        ],
        "source_artifact_reacquisition_groups": artifact_reacquisition_groups,
        "source_release_reacquisition_batches": (
            source_release_reacquisition_batches
        ),
        "case_assignments": assignments,
        "ground_truth_opened": False,
        "measured_cost_values_opened": False,
        "model_outputs_opened": False,
        "one_shot_evaluation_consumed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification-report", type=Path, required=True)
    parser.add_argument("--created-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report_path = args.qualification_report.resolve(strict=True)
    handoff = build_handoff(
        load_json(report_path),
        report_path=args.qualification_report,
        created_utc=args.created_utc,
    )
    write_json(args.output, handoff)
    print(
        json.dumps(
            {
                "status": handoff["status"],
                "qualified_case_count": handoff["qualified_case_count"],
                "unique_source_artifact_count": handoff["unique_source_artifact_count"],
                "preferred_source_release_batch_count": handoff[
                    "preferred_source_release_batch_count"
                ],
                "qualified_identity_commitment_sha256": handoff[
                    "qualified_identity_commitment_sha256"
                ],
                "ground_truth_opened": False,
                "measured_cost_values_opened": False,
                "model_outputs_opened": False,
                "one_shot_evaluation_consumed": False,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
