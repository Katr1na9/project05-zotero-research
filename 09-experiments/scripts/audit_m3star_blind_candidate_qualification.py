#!/usr/bin/env python3
"""Audit an outcome-free independent-curator qualification of the frozen 102 pool."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
QUALIFICATION_ID_PATTERN = re.compile(r"^QB-[0-9]{3}$")
ALLOWED_RISK_TIERS = {"A", "B"}
ATTRITION_REASONS = {
    "upper_bound_not_instantiated",
    "official_artifact_unavailable",
    "publisher_checksum_mismatch",
    "incomplete_campaign_boundary",
    "incomplete_host_or_sensor_coverage",
    "not_multi_stage",
    "duplicate_scenario_family",
    "duplicate_campaign_execution",
    "duplicate_telemetry_capture",
    "preblind_campaign_overlap",
    "parameter_or_representation_variant",
    "cost_measurement_scope_unsupported",
    "license_or_access_failure",
    "other_documented",
}
REQUIRED_TRUE_CASE_FLAGS = {
    "original_telemetry_present",
    "multi_stage_attack_chain_present",
    "full_campaign_time_window_included",
    "all_in_scope_campaign_hosts_combined",
    "not_a_host_slice",
    "not_a_time_slice",
    "not_a_mask_variant",
    "not_a_parameter_only_variant",
    "not_used_in_model_development",
    "cost_measurement_scope_supported",
    "ground_truth_sealed",
    "cost_values_sealed_from_model_development",
}
CASE_HASH_FIELDS = {
    "source_artifact_sha256",
    "scenario_family_sha256",
    "attack_chain_definition_sha256",
    "campaign_execution_sha256",
    "telemetry_capture_sha256",
}
UNIQUE_CASE_HASH_FIELDS = {
    "scenario_family_sha256",
    "attack_chain_definition_sha256",
    "campaign_execution_sha256",
    "telemetry_capture_sha256",
}


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


def require_nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def require_nonnegative_integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def require_true(value: Any, field: str) -> None:
    if value is not True:
        raise ValueError(f"{field} must be true")


def require_false(value: Any, field: str) -> None:
    if value is not False:
        raise ValueError(f"{field} must be false")


def resolve_repo_file(relative_path: Any, field: str) -> Path:
    value = require_nonempty(relative_path, field)
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{field} must stay within the repository")
    path = (REPO_ROOT / relative).resolve(strict=True)
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{field} resolves outside the repository") from exc
    if not path.is_file():
        raise ValueError(f"{field} must resolve to a file")
    return path


def validate_pool(pool: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if pool.get("status") != "frozen_before_independent_curator_access":
        raise ValueError("Qualification pool must be frozen before curator access")
    if pool.get("source_discovery_status") != "paused_pending_qualification_result":
        raise ValueError("Source discovery must remain paused during qualification")
    require_nonempty(pool.get("pool_id"), "pool_id")
    require_nonempty(pool.get("model_development_team_id"), "model_development_team_id")
    require_true(
        pool.get("all_qualified_cases_must_be_retained"),
        "all_qualified_cases_must_be_retained",
    )
    require_true(
        pool.get("outcome_based_case_selection_forbidden"),
        "outcome_based_case_selection_forbidden",
    )
    require_false(pool.get("ground_truth_opened"), "ground_truth_opened")
    require_false(pool.get("cost_values_opened"), "cost_values_opened")
    require_false(
        pool.get("model_outputs_used_for_qualification"),
        "model_outputs_used_for_qualification",
    )
    require_false(pool.get("qualification_complete"), "qualification_complete")
    if set(pool.get("included_risk_tiers", [])) != ALLOWED_RISK_TIERS:
        raise ValueError("Qualification pool must contain exactly risk tiers A and B")

    matrix_path = resolve_repo_file(
        pool.get("source_candidate_matrix_path"), "source_candidate_matrix_path"
    )
    access_path = resolve_repo_file(
        pool.get("source_access_boundary_path"), "source_access_boundary_path"
    )
    schema_path = resolve_repo_file(
        pool.get("qualification_schema_path"), "qualification_schema_path"
    )
    auditor_path = resolve_repo_file(
        pool.get("qualification_auditor_path"), "qualification_auditor_path"
    )
    if sha256(matrix_path) != str(pool.get("source_candidate_matrix_sha256", "")):
        raise ValueError("Frozen source candidate matrix SHA-256 mismatch")
    if sha256(access_path) != str(pool.get("source_access_boundary_sha256", "")):
        raise ValueError("Frozen source access boundary SHA-256 mismatch")
    if sha256(schema_path) != str(pool.get("qualification_schema_sha256", "")):
        raise ValueError("Frozen qualification schema SHA-256 mismatch")
    if sha256(auditor_path) != str(pool.get("qualification_auditor_sha256", "")):
        raise ValueError("Frozen qualification auditor SHA-256 mismatch")

    quotas = pool.get("source_quotas")
    if not isinstance(quotas, list) or not quotas:
        raise ValueError("source_quotas must be a non-empty array")
    quota_by_source: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(quotas):
        if not isinstance(item, dict):
            raise ValueError(f"source_quotas[{index}] must be an object")
        source_id = require_nonempty(item.get("source_id"), f"source_quotas[{index}].source_id")
        if source_id in quota_by_source:
            raise ValueError(f"Duplicate source quota: {source_id}")
        risk_tier = item.get("risk_tier")
        if risk_tier not in ALLOWED_RISK_TIERS:
            raise ValueError(f"source_quotas[{index}].risk_tier must be A or B")
        count = require_nonnegative_integer(
            item.get("candidate_upper_bound"),
            f"source_quotas[{index}].candidate_upper_bound",
        )
        if count < 1:
            raise ValueError("Every frozen source quota must contribute at least one candidate")
        quota_by_source[source_id] = {"risk_tier": risk_tier, "count": count}

    upper_bound = require_nonnegative_integer(
        pool.get("candidate_upper_bound"), "candidate_upper_bound"
    )
    if sum(item["count"] for item in quota_by_source.values()) != upper_bound:
        raise ValueError("Source quotas do not sum to candidate_upper_bound")
    if upper_bound != 102:
        raise ValueError("Frozen qualification candidate upper bound must be 102")
    if pool.get("minimum_valid_complete_cases_for_frozen_power_design") != 79:
        raise ValueError("Frozen power-design minimum must be 79")
    if pool.get("current_protocol_operational_target") != 96:
        raise ValueError("Current protocol operational target must be 96")

    matrix = load_json(matrix_path)
    matrix_quota = {
        item["source_id"]: {
            "risk_tier": item["candidate_risk_tier"],
            "count": item["conservative_unique_chain_upper_bound"],
        }
        for item in matrix["sources"]
        if item.get("included_in_current_metadata_upper_bound", True)
        and item.get("candidate_risk_tier") in ALLOWED_RISK_TIERS
        and item.get("conservative_unique_chain_upper_bound", 0) > 0
    }
    if matrix_quota != quota_by_source:
        raise ValueError("Frozen pool source quotas do not exactly match matrix A+B candidates")
    return quota_by_source


def validate_roles(report: dict[str, Any], pool: dict[str, Any]) -> None:
    roles = report.get("curation_and_seal_separation")
    if not isinstance(roles, dict):
        raise ValueError("curation_and_seal_separation must be an object")
    curator = require_nonempty(roles.get("curation_team_id"), "curation_team_id")
    model = require_nonempty(
        roles.get("model_development_team_id"), "model_development_team_id"
    )
    custodian = require_nonempty(
        roles.get("ground_truth_custodian_id"), "ground_truth_custodian_id"
    )
    if len({curator, model, custodian}) != 3:
        raise ValueError("Curator, model-development, and custodian identities must be distinct")
    if model != pool["model_development_team_id"]:
        raise ValueError("Qualification report model-development identity does not match pool")
    for field in (
        "teams_are_disjoint",
        "curator_blind_to_model_outputs",
        "model_developers_blind_to_candidate_payloads",
        "ground_truth_custodian_distinct_from_curator_and_model_developer",
    ):
        require_true(roles.get(field), f"curation_and_seal_separation.{field}")


def validate_disclosure_boundary(report: dict[str, Any]) -> None:
    boundary = report.get("non_consuming_disclosure_boundary")
    if not isinstance(boundary, dict):
        raise ValueError("non_consuming_disclosure_boundary must be an object")
    for field in (
        "telemetry_contents_returned_to_model_development",
        "labels_returned_to_model_development",
        "ground_truth_returned_to_model_development",
        "attack_narratives_returned_to_model_development",
        "cost_values_returned_to_model_development",
        "model_outputs_opened_during_qualification",
    ):
        require_false(boundary.get(field), f"non_consuming_disclosure_boundary.{field}")


def validate_qualification_report(
    report: dict[str, Any],
    pool: dict[str, Any],
    pool_path: Path,
) -> dict[str, Any]:
    quota_by_source = validate_pool(pool)
    if report.get("status") != "curator_qualification_complete":
        raise ValueError("Qualification report status must be curator_qualification_complete")
    require_nonempty(report.get("report_id"), "report_id")
    require_nonempty(report.get("report_created_utc"), "report_created_utc")
    if report.get("candidate_pool_id") != pool["pool_id"]:
        raise ValueError("Qualification report candidate_pool_id mismatch")
    if report.get("candidate_pool_sha256") != sha256(pool_path):
        raise ValueError("Qualification report candidate_pool_sha256 mismatch")
    if report.get("candidate_upper_bound_audited") != pool["candidate_upper_bound"]:
        raise ValueError("Qualification report must audit all 102 candidate slots")
    validate_roles(report, pool)
    validate_disclosure_boundary(report)
    require_nonempty(
        report.get("source_artifact_hash_ledger_id"),
        "source_artifact_hash_ledger_id",
    )
    require_true(report.get("all_qualified_cases_retained"), "all_qualified_cases_retained")
    require_false(
        report.get("qualification_rules_changed_after_access"),
        "qualification_rules_changed_after_access",
    )
    require_false(
        report.get("case_selection_used_model_outputs"),
        "case_selection_used_model_outputs",
    )

    source_results = report.get("source_results")
    if not isinstance(source_results, list):
        raise ValueError("source_results must be an array")
    observed_results: dict[str, dict[str, int]] = {}
    for index, item in enumerate(source_results):
        if not isinstance(item, dict):
            raise ValueError(f"source_results[{index}] must be an object")
        source_id = require_nonempty(item.get("source_id"), f"source_results[{index}].source_id")
        if source_id in observed_results:
            raise ValueError(f"Duplicate source result: {source_id}")
        if source_id not in quota_by_source:
            raise ValueError(f"Unexpected source result: {source_id}")
        quota = quota_by_source[source_id]
        if item.get("risk_tier") != quota["risk_tier"]:
            raise ValueError(f"{source_id} risk tier does not match frozen pool")
        if item.get("planned_candidate_upper_bound") != quota["count"]:
            raise ValueError(f"{source_id} candidate upper bound does not match frozen pool")
        qualified = require_nonnegative_integer(
            item.get("qualified_count"), f"{source_id}.qualified_count"
        )
        not_qualified = require_nonnegative_integer(
            item.get("not_qualified_count"), f"{source_id}.not_qualified_count"
        )
        if qualified + not_qualified != quota["count"]:
            raise ValueError(f"{source_id} qualification counts do not exhaust its quota")
        reasons = item.get("attrition_reason_counts")
        if not isinstance(reasons, dict):
            raise ValueError(f"{source_id}.attrition_reason_counts must be an object")
        unexpected_reasons = set(reasons) - ATTRITION_REASONS
        if unexpected_reasons:
            raise ValueError(f"{source_id} has unsupported attrition reasons")
        reason_total = sum(
            require_nonnegative_integer(value, f"{source_id}.{reason}")
            for reason, value in reasons.items()
        )
        if reason_total != not_qualified:
            raise ValueError(f"{source_id} attrition reasons do not sum to not_qualified_count")
        require_true(
            item.get("all_available_official_artifacts_audited"),
            f"{source_id}.all_available_official_artifacts_audited",
        )
        observed_results[source_id] = {
            "qualified": qualified,
            "not_qualified": not_qualified,
        }
    if set(observed_results) != set(quota_by_source):
        raise ValueError("Qualification report must contain every frozen source exactly once")

    reported_qualified = require_nonnegative_integer(
        report.get("reported_qualified_count"), "reported_qualified_count"
    )
    source_qualified = sum(item["qualified"] for item in observed_results.values())
    if reported_qualified != source_qualified:
        raise ValueError("reported_qualified_count does not match source_results")
    cases = report.get("qualified_cases")
    if not isinstance(cases, list) or len(cases) != reported_qualified:
        raise ValueError("qualified_cases length must equal reported_qualified_count")

    ids: set[str] = set()
    unique_hashes: dict[str, set[str]] = {field: set() for field in UNIQUE_CASE_HASH_FIELDS}
    case_counts = Counter()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"qualified_cases[{index}] must be an object")
        prefix = f"qualified_cases[{index}]"
        case_id = require_nonempty(case.get("qualification_case_id"), f"{prefix}.qualification_case_id")
        if not QUALIFICATION_ID_PATTERN.fullmatch(case_id):
            raise ValueError(f"{prefix}.qualification_case_id is malformed")
        if case_id in ids:
            raise ValueError(f"Duplicate qualification_case_id: {case_id}")
        ids.add(case_id)
        source_id = require_nonempty(case.get("source_id"), f"{prefix}.source_id")
        if source_id not in quota_by_source:
            raise ValueError(f"{prefix}.source_id is not in the frozen pool")
        case_counts[source_id] += 1
        require_nonempty(case.get("source_cluster_id"), f"{prefix}.source_cluster_id")
        require_nonempty(case.get("source_release_id"), f"{prefix}.source_release_id")
        require_nonempty(case.get("ground_truth_seal_id"), f"{prefix}.ground_truth_seal_id")
        require_nonempty(case.get("cost_measurement_seal_id"), f"{prefix}.cost_measurement_seal_id")
        for field in CASE_HASH_FIELDS:
            value = str(case.get(field, ""))
            if not SHA256_PATTERN.fullmatch(value):
                raise ValueError(f"{prefix}.{field} must be a lowercase SHA-256")
            if field in UNIQUE_CASE_HASH_FIELDS:
                if value in unique_hashes[field]:
                    raise ValueError(f"Duplicate qualified-case {field}: {value}")
                unique_hashes[field].add(value)
        for field in REQUIRED_TRUE_CASE_FLAGS:
            require_true(case.get(field), f"{prefix}.{field}")
    for source_id, result in observed_results.items():
        if case_counts[source_id] != result["qualified"]:
            raise ValueError(f"{source_id} qualified case records do not match source result")

    minimum = pool["minimum_valid_complete_cases_for_frozen_power_design"]
    target = pool["current_protocol_operational_target"]
    search_required = reported_qualified < minimum
    current_gate_met = reported_qualified >= target
    protocol_amendment_required = minimum <= reported_qualified < target
    return {
        "audit_id": "project05-m3star-blind-candidate-qualification-audit-v0.1",
        "status": "qualification_complete",
        "checked_utc": utc_now(),
        "candidate_pool_id": pool["pool_id"],
        "candidate_pool_sha256": sha256(pool_path),
        "candidate_upper_bound_audited": pool["candidate_upper_bound"],
        "actual_qualified_case_count": reported_qualified,
        "actual_not_qualified_count": pool["candidate_upper_bound"] - reported_qualified,
        "minimum_valid_complete_cases_for_frozen_power_design": minimum,
        "current_protocol_operational_target": target,
        "source_search_required": search_required,
        "additional_qualified_cases_required_to_reach_power_minimum": max(
            minimum - reported_qualified, 0
        ),
        "current_protocol_count_gate_met": current_gate_met,
        "protocol_amendment_required_before_preflight": protocol_amendment_required,
        "all_qualified_cases_to_be_retained": True,
        "decision_basis": (
            "resume_source_discovery_below_79"
            if search_required
            else (
                "stop_search_and_amend_count_gate_use_all_qualified"
                if protocol_amendment_required
                else "stop_search_current_count_gate_met_use_all_qualified"
            )
        ),
        "file_contents_returned_to_model_development": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened_during_qualification": False,
        "one_shot_evaluation_consumed": False,
    }


def build_waiting_report(pool: dict[str, Any], pool_path: Path) -> dict[str, Any]:
    validate_pool(pool)
    return {
        "audit_id": "project05-m3star-blind-candidate-qualification-audit-v0.1",
        "status": "awaiting_independent_curator_report",
        "checked_utc": utc_now(),
        "candidate_pool_id": pool["pool_id"],
        "candidate_pool_sha256": sha256(pool_path),
        "candidate_upper_bound_frozen": pool["candidate_upper_bound"],
        "actual_qualified_case_count": None,
        "actual_not_qualified_count": None,
        "minimum_valid_complete_cases_for_frozen_power_design": pool[
            "minimum_valid_complete_cases_for_frozen_power_design"
        ],
        "current_protocol_operational_target": pool[
            "current_protocol_operational_target"
        ],
        "source_search_required": None,
        "decision_deferred_until_qualification_complete": True,
        "source_discovery_paused": True,
        "file_contents_returned_to_model_development": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened_during_qualification": False,
        "one_shot_evaluation_consumed": False,
        "blocker": "No completed report from a role-separated independent curator is present; 102 is still an upper bound, not an observed qualified-case count."
    }


def build_curator_template(pool: dict[str, Any], pool_path: Path) -> dict[str, Any]:
    quota_by_source = validate_pool(pool)
    return {
        "report_id": "REPLACE-WITH-CURATOR-REPORT-ID",
        "status": "curator_qualification_in_progress",
        "report_created_utc": None,
        "candidate_pool_id": pool["pool_id"],
        "candidate_pool_sha256": sha256(pool_path),
        "candidate_upper_bound_audited": 102,
        "curation_and_seal_separation": {
            "curation_team_id": "REPLACE-WITH-INDEPENDENT-CURATOR-ID",
            "model_development_team_id": pool["model_development_team_id"],
            "ground_truth_custodian_id": "REPLACE-WITH-GROUND-TRUTH-CUSTODIAN-ID",
            "teams_are_disjoint": True,
            "curator_blind_to_model_outputs": True,
            "model_developers_blind_to_candidate_payloads": True,
            "ground_truth_custodian_distinct_from_curator_and_model_developer": True,
        },
        "non_consuming_disclosure_boundary": {
            "telemetry_contents_returned_to_model_development": False,
            "labels_returned_to_model_development": False,
            "ground_truth_returned_to_model_development": False,
            "attack_narratives_returned_to_model_development": False,
            "cost_values_returned_to_model_development": False,
            "model_outputs_opened_during_qualification": False,
        },
        "source_artifact_hash_ledger_id": "REPLACE-WITH-HASH-LEDGER-ID",
        "source_results": [
            {
                "source_id": source_id,
                "risk_tier": item["risk_tier"],
                "planned_candidate_upper_bound": item["count"],
                "qualified_count": None,
                "not_qualified_count": None,
                "attrition_reason_counts": {},
                "all_available_official_artifacts_audited": False,
            }
            for source_id, item in quota_by_source.items()
        ],
        "reported_qualified_count": None,
        "qualified_cases": [],
        "all_qualified_cases_retained": True,
        "qualification_rules_changed_after_access": False,
        "case_selection_used_model_outputs": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--template-output", type=Path)
    args = parser.parse_args()
    pool_path = args.pool.resolve(strict=True)
    pool = load_json(pool_path)
    if args.template_output is not None:
        write_json(args.template_output, build_curator_template(pool, pool_path))
    audit = (
        validate_qualification_report(load_json(args.report), pool, pool_path)
        if args.report is not None
        else build_waiting_report(pool, pool_path)
    )
    if args.output is not None:
        write_json(args.output, audit)
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
