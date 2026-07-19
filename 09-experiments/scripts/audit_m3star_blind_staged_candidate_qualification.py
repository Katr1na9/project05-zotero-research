#!/usr/bin/env python3
"""Audit staged, outcome-free qualification of the amended 95-slot blind pool."""

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
EXPECTED_PHASE_1 = [
    ("otrf-security-datasets-compound", None, 9),
    ("splunk-attack-data-apt-simulations", None, 1),
    ("cam-lds", None, 7),
    ("mscad", None, 2),
    ("dapt2020", None, 1),
    ("capd", None, 23),
    ("goose-power-substation-apt", None, 1),
    ("cyber-czech-2019", None, 1),
    ("windows-apt-2025", None, 31),
    ("attackmate-evaluation-data", None, 3),
    ("attackmate-robotdog", None, 1),
    ("ainception-storylines", "SL100", 1),
]
EXPECTED_PHASE_2 = [
    ("ait-log-data-set-v2.1", "russellmitchell", 522084364),
    ("ait-log-data-set-v2.1", "santos", 576734274),
    ("ait-log-data-set-v2.1", "harrison", 667985140),
    ("ait-log-data-set-v2.1", "fox", 688586900),
    ("ait-log-data-set-v2.1", "wheeler", 767673839),
    ("ait-log-data-set-v2.1", "wardbeck", 818462147),
    ("ait-log-data-set-v2.1", "wilson", 1083526183),
    ("ait-log-data-set-v2.1", "shaw", 1319137852),
]
EXPECTED_PHASE_3 = [
    ("apt-sandworm-dataset", "campaign", 1814743122),
    ("locked-shields-partners-run-23", "LSPR23", 1940509448),
    ("ainception-storylines", "SL700", 3358489764),
    ("locked-shields-partners-run-24", "LSPR24", 7973355651),
    ("ainception-storylines", "SL300", 9735245693),
    ("cicapt-iiot", "campaign", None),
]
EXPECTED_PHASE_1_BYTES = 3146302753
EXPECTED_PHASE_2_BYTES = 6444190699
EXPECTED_MINIMUM = 79
EXPECTED_POOL_SIZE = 95
EXPECTED_WITHIN_CASE_CONDITIONS = 45
REPORT_FIELDS = {
    "report_id",
    "status",
    "report_created_utc",
    "amendment_id",
    "amendment_sha256",
    "curation_and_seal_separation",
    "non_consuming_disclosure_boundary",
    "source_artifact_hash_ledger_id",
    "phase_1_source_results",
    "sequential_candidate_results",
    "audited_candidate_count",
    "reported_qualified_count",
    "reported_not_qualified_count",
    "unaudited_reserve_count",
    "qualified_cases",
    "all_qualified_cases_retained",
    "qualification_rules_changed_after_access",
    "case_selection_used_model_outputs",
    "stage_transition_used_only_permitted_fields",
    "within_case_conditions_counted_as_independent_cases",
}
ROLE_FIELDS = {
    "curation_team_id",
    "model_development_team_id",
    "ground_truth_custodian_id",
    "teams_are_disjoint",
    "curator_blind_to_model_outputs",
    "model_developers_blind_to_candidate_payloads",
    "ground_truth_custodian_distinct_from_curator_and_model_developer",
}
DISCLOSURE_FIELDS = {
    "telemetry_contents_returned_to_model_development",
    "labels_returned_to_model_development",
    "ground_truth_returned_to_model_development",
    "attack_narratives_returned_to_model_development",
    "cost_values_returned_to_model_development",
    "model_outputs_opened_during_qualification",
}
PHASE_1_RESULT_FIELDS = {
    "source_id",
    "candidate_key",
    "planned_candidate_slots",
    "qualified_count",
    "not_qualified_count",
    "attrition_reason_counts",
    "all_planned_slots_audited",
}
SEQUENTIAL_RESULT_FIELDS = {
    "phase",
    "phase_candidate_index",
    "source_id",
    "candidate_key",
    "qualification_status",
    "attrition_reason",
}
QUALIFIED_CASE_FIELDS = {
    "qualification_case_id",
    "source_id",
    "candidate_key",
    "source_cluster_id",
    "source_release_id",
    "source_artifact_sha256",
    "scenario_family_sha256",
    "attack_chain_definition_sha256",
    "campaign_execution_sha256",
    "telemetry_capture_sha256",
    *REQUIRED_TRUE_CASE_FLAGS,
    "ground_truth_seal_id",
    "cost_measurement_seal_id",
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


def require_exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    missing = expected - set(value)
    unexpected = set(value) - expected
    if missing or unexpected:
        raise ValueError(
            f"{field} fields differ from the disclosure-safe contract; "
            f"missing={sorted(missing)}, unexpected={sorted(unexpected)}"
        )


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


def allocation_key(item: dict[str, Any]) -> tuple[str, str | None]:
    return (str(item.get("source_id", "")), item.get("candidate_key"))


def validate_amendment(amendment: dict[str, Any]) -> dict[str, Any]:
    if amendment.get("status") != "frozen_before_first_candidate_payload_access":
        raise ValueError("Staged amendment must be frozen before payload access")
    require_nonempty(amendment.get("amendment_id"), "amendment_id")
    for field in (
        "candidate_payload_access_started",
        "ground_truth_opened",
        "cost_values_opened",
        "model_outputs_used_for_ordering",
        "one_shot_evaluation_consumed",
    ):
        require_false(amendment.get(field), field)

    superseded = amendment.get("superseded_pool")
    size_audit = amendment.get("size_audit")
    contract = amendment.get("staged_qualification_contract")
    if not isinstance(superseded, dict) or not isinstance(size_audit, dict):
        raise ValueError("Amendment file anchors must be objects")
    if not isinstance(contract, dict):
        raise ValueError("staged_qualification_contract must be an object")
    for anchor, prefix in ((superseded, "superseded_pool"), (size_audit, "size_audit")):
        path = resolve_repo_file(anchor.get("path"), f"{prefix}.path")
        if sha256(path) != anchor.get("sha256"):
            raise ValueError(f"{prefix} SHA-256 mismatch")
    for name in ("schema", "auditor"):
        path = resolve_repo_file(contract.get(f"{name}_path"), f"{name}_path")
        if sha256(path) != contract.get(f"{name}_sha256"):
            raise ValueError(f"Frozen staged qualification {name} SHA-256 mismatch")

    exclusion = amendment.get("resource_feasibility_exclusion")
    if not isinstance(exclusion, dict):
        raise ValueError("resource_feasibility_exclusion must be an object")
    if (
        exclusion.get("source_id") != "aviator"
        or exclusion.get("candidate_upper_bound_removed") != 7
        or exclusion.get("official_archive_bytes_avoided") != 109261265408
    ):
        raise ValueError("AVIATOR feasibility exclusion drifted from the frozen decision")
    require_true(exclusion.get("exclusion_is_not_a_case_failure"), "exclusion_is_not_a_case_failure")

    amended_pool = amendment.get("amended_pool")
    if not isinstance(amended_pool, dict):
        raise ValueError("amended_pool must be an object")
    if amended_pool.get("candidate_upper_bound") != EXPECTED_POOL_SIZE:
        raise ValueError("Amended pool upper bound must be 95")
    if amended_pool.get("minimum_valid_complete_cases") != EXPECTED_MINIMUM:
        raise ValueError("Frozen power-design minimum must be 79")
    require_true(amended_pool.get("all_qualified_cases_from_every_audited_slot_must_be_retained"), "all_qualified_cases_from_every_audited_slot_must_be_retained")
    require_true(amended_pool.get("unaudited_reserve_slots_are_not_failures"), "unaudited_reserve_slots_are_not_failures")

    within = amendment.get("within_case_conditions")
    if not isinstance(within, dict) or within.get("count") != EXPECTED_WITHIN_CASE_CONDITIONS:
        raise ValueError("Within-case condition count must remain 45")
    if within.get("role") != "paired_repeated_measurements_only":
        raise ValueError("The 45 conditions must remain paired repeated measurements")
    require_true(within.get("never_counted_as_independent_cases"), "never_counted_as_independent_cases")

    rules = amendment.get("stage_rules")
    if not isinstance(rules, dict):
        raise ValueError("stage_rules must be an object")
    require_true(rules.get("ordering_frozen_before_payload_access"), "ordering_frozen_before_payload_access")
    require_true(rules.get("phase_1_must_be_exhausted_before_stopping"), "phase_1_must_be_exhausted_before_stopping")
    require_true(rules.get("phase_2_and_phase_3_are_candidate_sequential"), "phase_2_and_phase_3_are_candidate_sequential")
    require_true(rules.get("stop_immediately_after_qualified_count_reaches_79"), "stop_immediately_after_qualified_count_reaches_79")
    permitted = set(rules.get("stage_transition_may_use_only", []))
    if permitted != {"audited_candidate_count", "qualified_case_count", "documented_nonqualification_reason"}:
        raise ValueError("Stage-transition permitted fields drifted")

    phases = amendment.get("phases")
    if not isinstance(phases, list) or len(phases) != 3:
        raise ValueError("Exactly three frozen acquisition phases are required")
    phase_1 = phases[0]
    actual_phase_1 = [
        (item.get("source_id"), item.get("candidate_key"), item.get("slots"))
        for item in phase_1.get("allocations", [])
    ]
    if actual_phase_1 != EXPECTED_PHASE_1:
        raise ValueError("Phase-1 allocations or order drifted")
    if phase_1.get("planned_candidate_slots") != 81 or phase_1.get("planned_download_bytes") != EXPECTED_PHASE_1_BYTES:
        raise ValueError("Phase-1 frozen totals drifted")
    require_true(phase_1.get("must_complete_entire_phase"), "phase_1.must_complete_entire_phase")

    phase_2 = phases[1]
    actual_phase_2 = [
        (item.get("source_id"), item.get("candidate_key"), item.get("bytes"))
        for item in phase_2.get("candidate_order", [])
    ]
    if actual_phase_2 != EXPECTED_PHASE_2:
        raise ValueError("Phase-2 candidate order or byte ledger drifted")
    if phase_2.get("maximum_additional_slots") != 8 or phase_2.get("maximum_additional_download_bytes") != EXPECTED_PHASE_2_BYTES:
        raise ValueError("Phase-2 frozen totals drifted")
    if sum(item[2] for item in EXPECTED_PHASE_2) != EXPECTED_PHASE_2_BYTES:
        raise ValueError("Internal Phase-2 byte invariant failed")

    phase_3 = phases[2]
    actual_phase_3 = [
        (item.get("source_id"), item.get("candidate_key"), item.get("bytes"))
        for item in phase_3.get("candidate_order", [])
    ]
    if actual_phase_3 != EXPECTED_PHASE_3 or phase_3.get("maximum_additional_slots") != 6:
        raise ValueError("Phase-3 candidate order or slot count drifted")
    return {
        "phase_1": phase_1,
        "sequential_candidates": [
            {"phase": phase, "phase_candidate_index": index, **candidate}
            for phase, items in ((2, phase_2["candidate_order"]), (3, phase_3["candidate_order"]))
            for index, candidate in enumerate(items, start=1)
        ],
    }


def validate_roles(report: dict[str, Any]) -> None:
    roles = report.get("curation_and_seal_separation")
    if not isinstance(roles, dict):
        raise ValueError("curation_and_seal_separation must be an object")
    require_exact_keys(roles, ROLE_FIELDS, "curation_and_seal_separation")
    curator = require_nonempty(roles.get("curation_team_id"), "curation_team_id")
    model = require_nonempty(roles.get("model_development_team_id"), "model_development_team_id")
    custodian = require_nonempty(roles.get("ground_truth_custodian_id"), "ground_truth_custodian_id")
    if len({curator, model, custodian}) != 3:
        raise ValueError("Curator, model-development, and custodian identities must be distinct")
    if model != "project05-model-development":
        raise ValueError("Unexpected model-development identity")
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
    require_exact_keys(boundary, DISCLOSURE_FIELDS, "non_consuming_disclosure_boundary")
    for field in (
        "telemetry_contents_returned_to_model_development",
        "labels_returned_to_model_development",
        "ground_truth_returned_to_model_development",
        "attack_narratives_returned_to_model_development",
        "cost_values_returned_to_model_development",
        "model_outputs_opened_during_qualification",
    ):
        require_false(boundary.get(field), f"non_consuming_disclosure_boundary.{field}")


def validate_attrition_reasons(reasons: Any, expected: int, field: str) -> None:
    if not isinstance(reasons, dict):
        raise ValueError(f"{field} must be an object")
    if set(reasons) - ATTRITION_REASONS:
        raise ValueError(f"{field} contains unsupported reasons")
    total = sum(
        require_nonnegative_integer(value, f"{field}.{reason}")
        for reason, value in reasons.items()
    )
    if total != expected:
        raise ValueError(f"{field} does not sum to not-qualified count")


def validate_qualified_cases(
    cases: Any,
    expected_counts: Counter[tuple[str, str | None]],
) -> None:
    expected_total = sum(expected_counts.values())
    if not isinstance(cases, list) or len(cases) != expected_total:
        raise ValueError("qualified_cases length must equal reported_qualified_count")
    ids: set[str] = set()
    unique_hashes: dict[str, set[str]] = {field: set() for field in UNIQUE_CASE_HASH_FIELDS}
    observed_counts: Counter[tuple[str, str | None]] = Counter()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"qualified_cases[{index}] must be an object")
        prefix = f"qualified_cases[{index}]"
        require_exact_keys(case, QUALIFIED_CASE_FIELDS, prefix)
        case_id = require_nonempty(case.get("qualification_case_id"), f"{prefix}.qualification_case_id")
        if not QUALIFICATION_ID_PATTERN.fullmatch(case_id):
            raise ValueError(f"{prefix}.qualification_case_id is malformed")
        if case_id in ids:
            raise ValueError(f"Duplicate qualification_case_id: {case_id}")
        ids.add(case_id)
        source_id = require_nonempty(case.get("source_id"), f"{prefix}.source_id")
        candidate_key = case.get("candidate_key")
        if candidate_key is not None:
            require_nonempty(candidate_key, f"{prefix}.candidate_key")
        observed_counts[(source_id, candidate_key)] += 1
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
    if observed_counts != expected_counts:
        raise ValueError("Qualified case records do not match audited allocation outcomes")


def validate_qualification_report(
    report: dict[str, Any],
    amendment: dict[str, Any],
    amendment_path: Path,
) -> dict[str, Any]:
    plan = validate_amendment(amendment)
    require_exact_keys(report, REPORT_FIELDS, "qualification report")
    if report.get("status") != "curator_staged_qualification_checkpoint":
        raise ValueError("Report status must be curator_staged_qualification_checkpoint")
    require_nonempty(report.get("report_id"), "report_id")
    require_nonempty(report.get("report_created_utc"), "report_created_utc")
    if report.get("amendment_id") != amendment["amendment_id"]:
        raise ValueError("Qualification report amendment_id mismatch")
    if report.get("amendment_sha256") != sha256(amendment_path):
        raise ValueError("Qualification report amendment_sha256 mismatch")
    validate_roles(report)
    validate_disclosure_boundary(report)
    require_nonempty(report.get("source_artifact_hash_ledger_id"), "source_artifact_hash_ledger_id")
    for field in (
        "all_qualified_cases_retained",
        "stage_transition_used_only_permitted_fields",
    ):
        require_true(report.get(field), field)
    for field in (
        "qualification_rules_changed_after_access",
        "case_selection_used_model_outputs",
        "within_case_conditions_counted_as_independent_cases",
    ):
        require_false(report.get(field), field)

    phase_1_results = report.get("phase_1_source_results")
    if not isinstance(phase_1_results, list) or len(phase_1_results) != len(EXPECTED_PHASE_1):
        raise ValueError("Phase-1 report must contain every frozen allocation exactly once")
    expected_counts: Counter[tuple[str, str | None]] = Counter()
    phase_1_qualified = 0
    phase_1_not_qualified = 0
    for index, (result, allocation) in enumerate(zip(phase_1_results, plan["phase_1"]["allocations"])):
        if not isinstance(result, dict):
            raise ValueError(f"phase_1_source_results[{index}] must be an object")
        require_exact_keys(result, PHASE_1_RESULT_FIELDS, f"phase_1_source_results[{index}]")
        key = allocation_key(allocation)
        if allocation_key(result) != key:
            raise ValueError("Phase-1 source results must preserve the frozen allocation order")
        planned = allocation["slots"]
        if result.get("planned_candidate_slots") != planned:
            raise ValueError(f"Phase-1 planned slots mismatch for {key}")
        qualified = require_nonnegative_integer(result.get("qualified_count"), f"phase_1_source_results[{index}].qualified_count")
        not_qualified = require_nonnegative_integer(result.get("not_qualified_count"), f"phase_1_source_results[{index}].not_qualified_count")
        if qualified + not_qualified != planned:
            raise ValueError(f"Phase-1 counts do not exhaust allocation {key}")
        validate_attrition_reasons(result.get("attrition_reason_counts"), not_qualified, f"phase_1_source_results[{index}].attrition_reason_counts")
        require_true(result.get("all_planned_slots_audited"), f"phase_1_source_results[{index}].all_planned_slots_audited")
        expected_counts[key] += qualified
        phase_1_qualified += qualified
        phase_1_not_qualified += not_qualified

    sequential_results = report.get("sequential_candidate_results")
    if not isinstance(sequential_results, list):
        raise ValueError("sequential_candidate_results must be an array")
    frozen_sequence = plan["sequential_candidates"]
    if len(sequential_results) > len(frozen_sequence):
        raise ValueError("Sequential results exceed the frozen reserve")
    sequential_qualified = 0
    sequential_not_qualified = 0
    cumulative_qualified = phase_1_qualified
    for index, (result, expected) in enumerate(zip(sequential_results, frozen_sequence)):
        if not isinstance(result, dict):
            raise ValueError(f"sequential_candidate_results[{index}] must be an object")
        require_exact_keys(result, SEQUENTIAL_RESULT_FIELDS, f"sequential_candidate_results[{index}]")
        for field in ("phase", "phase_candidate_index", "source_id", "candidate_key"):
            if result.get(field) != expected.get(field):
                raise ValueError("Sequential candidate results are not the exact frozen-order prefix")
        status = result.get("qualification_status")
        reason = result.get("attrition_reason")
        if status == "qualified":
            if reason is not None:
                raise ValueError("Qualified sequential candidates must not have an attrition reason")
            sequential_qualified += 1
            cumulative_qualified += 1
            expected_counts[allocation_key(expected)] += 1
        elif status == "not_qualified":
            if reason not in ATTRITION_REASONS:
                raise ValueError("Not-qualified sequential candidates require a supported attrition reason")
            sequential_not_qualified += 1
        else:
            raise ValueError("Sequential qualification_status must be qualified or not_qualified")
        if cumulative_qualified >= EXPECTED_MINIMUM and index != len(sequential_results) - 1:
            raise ValueError("Sequential acquisition continued after the 79-case stopping boundary")

    audited_count = 81 + len(sequential_results)
    qualified_count = phase_1_qualified + sequential_qualified
    not_qualified_count = phase_1_not_qualified + sequential_not_qualified
    unaudited_count = EXPECTED_POOL_SIZE - audited_count
    reported = {
        "audited_candidate_count": audited_count,
        "reported_qualified_count": qualified_count,
        "reported_not_qualified_count": not_qualified_count,
        "unaudited_reserve_count": unaudited_count,
    }
    for field, expected in reported.items():
        if report.get(field) != expected:
            raise ValueError(f"{field} does not match the audited frozen prefix")
    if audited_count != qualified_count + not_qualified_count:
        raise ValueError("Audited slots must be exactly qualified plus not-qualified")
    if audited_count + unaudited_count != EXPECTED_POOL_SIZE:
        raise ValueError("Audited and unaudited slots must exhaust the amended pool")
    validate_qualified_cases(report.get("qualified_cases"), expected_counts)

    if phase_1_qualified >= EXPECTED_MINIMUM:
        if sequential_results:
            raise ValueError("No reserve candidate may be audited after Phase 1 reaches 79")
        acquisition_complete = True
        source_search_required: bool | None = False
        decision_basis = "stop_after_phase_1_minimum_reached"
        next_candidate = None
    elif qualified_count >= EXPECTED_MINIMUM:
        acquisition_complete = True
        source_search_required = False
        decision_basis = "stop_at_first_sequential_candidate_reaching_79"
        next_candidate = None
    elif audited_count == EXPECTED_POOL_SIZE:
        acquisition_complete = True
        source_search_required = True
        decision_basis = "resume_metadata_only_source_discovery_after_95_below_79"
        next_candidate = None
    else:
        acquisition_complete = False
        source_search_required = None
        decision_basis = "continue_with_next_frozen_candidate"
        next_candidate = frozen_sequence[len(sequential_results)]

    return {
        "audit_id": "project05-m3star-blind-staged-candidate-qualification-audit-v0.2",
        "status": "qualification_complete" if acquisition_complete else "qualification_checkpoint_continue_acquisition",
        "checked_utc": utc_now(),
        "amendment_id": amendment["amendment_id"],
        "amendment_sha256": sha256(amendment_path),
        "candidate_upper_bound": EXPECTED_POOL_SIZE,
        "audited_candidate_count": audited_count,
        "actual_qualified_case_count": qualified_count,
        "actual_not_qualified_count": not_qualified_count,
        "unaudited_reserve_count": unaudited_count,
        "unaudited_reserve_slots_counted_as_failures": False,
        "minimum_valid_complete_cases_for_frozen_power_design": EXPECTED_MINIMUM,
        "acquisition_complete": acquisition_complete,
        "source_search_required": source_search_required,
        "additional_qualified_cases_required_to_reach_power_minimum": max(EXPECTED_MINIMUM - qualified_count, 0),
        "decision_basis": decision_basis,
        "next_frozen_candidate": next_candidate,
        "all_qualified_cases_to_be_retained": True,
        "independent_case_count": qualified_count,
        "within_case_repeated_conditions": EXPECTED_WITHIN_CASE_CONDITIONS,
        "within_case_conditions_inflate_independent_n": False,
        "file_contents_returned_to_model_development": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened_during_qualification": False,
        "one_shot_evaluation_consumed": False,
    }


def build_waiting_report(amendment: dict[str, Any], amendment_path: Path) -> dict[str, Any]:
    validate_amendment(amendment)
    return {
        "audit_id": "project05-m3star-blind-staged-candidate-qualification-audit-v0.2",
        "status": "awaiting_independent_curator_phase_1_report",
        "checked_utc": utc_now(),
        "amendment_id": amendment["amendment_id"],
        "amendment_sha256": sha256(amendment_path),
        "candidate_upper_bound": EXPECTED_POOL_SIZE,
        "audited_candidate_count": 0,
        "actual_qualified_case_count": None,
        "actual_not_qualified_count": None,
        "unaudited_reserve_count": EXPECTED_POOL_SIZE,
        "source_search_required": None,
        "source_discovery_paused": True,
        "next_action": "Independent curator must exhaust the frozen 81-slot Phase 1 before returning a checkpoint report.",
        "file_contents_returned_to_model_development": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened_during_qualification": False,
        "one_shot_evaluation_consumed": False,
    }


def build_curator_template(amendment: dict[str, Any], amendment_path: Path) -> dict[str, Any]:
    plan = validate_amendment(amendment)
    return {
        "report_id": "REPLACE-WITH-CURATOR-CHECKPOINT-ID",
        "status": "curator_staged_qualification_checkpoint",
        "report_created_utc": None,
        "amendment_id": amendment["amendment_id"],
        "amendment_sha256": sha256(amendment_path),
        "curation_and_seal_separation": {
            "curation_team_id": "REPLACE-WITH-INDEPENDENT-CURATOR-ID",
            "model_development_team_id": "project05-model-development",
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
        "phase_1_source_results": [
            {
                "source_id": allocation["source_id"],
                "candidate_key": allocation.get("candidate_key"),
                "planned_candidate_slots": allocation["slots"],
                "qualified_count": None,
                "not_qualified_count": None,
                "attrition_reason_counts": {},
                "all_planned_slots_audited": False,
            }
            for allocation in plan["phase_1"]["allocations"]
        ],
        "sequential_candidate_results": [],
        "audited_candidate_count": None,
        "reported_qualified_count": None,
        "reported_not_qualified_count": None,
        "unaudited_reserve_count": None,
        "qualified_cases": [],
        "all_qualified_cases_retained": True,
        "qualification_rules_changed_after_access": False,
        "case_selection_used_model_outputs": False,
        "stage_transition_used_only_permitted_fields": True,
        "within_case_conditions_counted_as_independent_cases": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--template-output", type=Path)
    args = parser.parse_args()
    amendment_path = args.amendment.resolve(strict=True)
    amendment = load_json(amendment_path)
    if args.template_output is not None:
        write_json(args.template_output, build_curator_template(amendment, amendment_path))
    audit = (
        validate_qualification_report(load_json(args.report), amendment, amendment_path)
        if args.report is not None
        else build_waiting_report(amendment, amendment_path)
    )
    if args.output is not None:
        write_json(args.output, audit)
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
