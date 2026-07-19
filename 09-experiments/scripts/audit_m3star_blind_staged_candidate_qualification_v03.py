#!/usr/bin/env python3
"""Audit the v0.3 outcome-free sample-size/stopping overlay.

The v0.2 auditor remains the authority for candidate order, eligibility,
deduplication, role separation, and the disclosure boundary.  This module adds
only the pre-outcome stopping amendment: the first checkpoint reaching 59
qualified independent cases is complete and no later candidate may be audited.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


def load_legacy_auditor() -> Any:
    path = Path(__file__).with_name(
        "audit_m3star_blind_staged_candidate_qualification.py"
    )
    spec = importlib.util.spec_from_file_location(
        "audit_m3star_blind_staged_candidate_qualification_v02", path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


legacy = load_legacy_auditor()
REPO_ROOT = Path(__file__).resolve().parents[2]
EFFECTIVE_MINIMUM = 59
NINETY_PERCENT_REFERENCE = 79
EXPECTED_POOL_SIZE = 95
EXPECTED_WITHIN_CASE_CONDITIONS = 45
EXPECTED_STOPPING_AMENDMENT_ID = (
    "project05-m3star-final-blind-sample-size-and-stopping-amendment-v0.3"
)


load_json = legacy.load_json
write_json = legacy.write_json
sha256 = legacy.sha256
utc_now = legacy.utc_now


def require_false(value: Any, field: str) -> None:
    if value is not False:
        raise ValueError(f"{field} must be false")


def require_true(value: Any, field: str) -> None:
    if value is not True:
        raise ValueError(f"{field} must be true")


def resolve_anchor(anchor: dict[str, Any], path_field: str, hash_field: str) -> Path:
    path = legacy.resolve_repo_file(anchor.get(path_field), path_field)
    if sha256(path) != anchor.get(hash_field):
        raise ValueError(f"{hash_field} mismatch")
    return path


def validate_stopping_amendment(
    stopping: dict[str, Any],
    stopping_path: Path,
) -> dict[str, Any]:
    if stopping.get("amendment_id") != EXPECTED_STOPPING_AMENDMENT_ID:
        raise ValueError("Unexpected v0.3 stopping amendment identity")
    if stopping.get("status") != "frozen_before_next_candidate_payload_access":
        raise ValueError("Stopping amendment was not frozen before the next payload")
    if stopping.get("scope") != "sample_size_and_stopping_threshold_only":
        raise ValueError("Stopping amendment scope is broader than sample size/stopping")
    if not stopping_path.is_file() or stopping_path.resolve().parent != (
        REPO_ROOT
        / "04-progress"
        / "m3star-final-blind-data-intake-v0.1-20260719"
    ).resolve():
        raise ValueError("Stopping amendment is outside the frozen governance location")

    base = stopping.get("base_staged_acquisition_amendment")
    review = stopping.get("outcome_free_sample_size_review")
    checkpoint = stopping.get("pre_amendment_checkpoint")
    if not all(isinstance(item, dict) for item in (base, review, checkpoint)):
        raise ValueError("Stopping amendment anchors must be objects")
    base_path = resolve_anchor(base, "path", "sha256")
    review_path = resolve_anchor(review, "path", "sha256")
    report_path = resolve_anchor(
        checkpoint,
        "qualification_report_path",
        "qualification_report_sha256",
    )
    audit_path = resolve_anchor(
        checkpoint,
        "qualification_audit_path",
        "qualification_audit_sha256",
    )

    base_document = load_json(base_path)
    legacy.validate_amendment(base_document)
    review_document = load_json(review_path)
    if review_document.get("final_blind_outcomes_opened") is not False:
        raise ValueError("Sample-size review was not outcome-free")
    checks = review_document.get("independent_checks", {})
    if (
        checks.get("cost_n_at_80_percent_power") != 58
        or checks.get(
            "zero_success_loss_n_for_one_sided_95_percent_upper_at_most_5_percent"
        )
        != EFFECTIVE_MINIMUM
        or checks.get("combined_n_at_80_percent_power") != EFFECTIVE_MINIMUM
        or checks.get("combined_n_at_90_percent_power") != NINETY_PERCENT_REFERENCE
    ):
        raise ValueError("Sample-size review does not support the v0.3 thresholds")

    checkpoint_report = load_json(report_path)
    recalculated_checkpoint = legacy.validate_qualification_report(
        checkpoint_report, base_document, base_path
    )
    checkpoint_audit = load_json(audit_path)
    for field, expected in (
        ("audited_candidate_count", 86),
        ("actual_qualified_case_count", 52),
        ("actual_not_qualified_count", 34),
        ("unaudited_reserve_count", 9),
    ):
        if recalculated_checkpoint.get(field) != expected:
            raise ValueError(f"Recalculated checkpoint {field} drifted")
        if checkpoint_audit.get(field) != expected:
            raise ValueError(f"Frozen checkpoint audit {field} drifted")
    expected_next = checkpoint.get("next_frozen_candidate")
    if (
        not isinstance(expected_next, dict)
        or expected_next.get("candidate_key") != "wardbeck"
        or recalculated_checkpoint.get("next_frozen_candidate") != expected_next
        or checkpoint_audit.get("next_frozen_candidate") != expected_next
    ):
        raise ValueError("The next frozen candidate is not wardbeck")

    for field in (
        "candidate_payloads_after_checkpoint_opened",
        "final_blind_model_outputs_opened",
        "baseline_outputs_opened",
        "ground_truth_opened",
        "cost_values_opened",
        "success_or_failure_results_opened",
        "action_sequences_opened",
        "one_shot_evaluation_consumed",
    ):
        require_false(stopping.get("blinding_attestation", {}).get(field), field)

    design = stopping.get("effective_design", {})
    if (
        design.get("combined_minimum_valid_complete_independent_cases")
        != EFFECTIVE_MINIMUM
        or design.get("cost_power_minimum_independent_cases") != 58
        or design.get("zero_success_loss_precision_minimum_independent_cases")
        != EFFECTIVE_MINIMUM
        or design.get("ninety_percent_power_reference_independent_cases")
        != NINETY_PERCENT_REFERENCE
    ):
        raise ValueError("Effective v0.3 design thresholds drifted")
    require_true(
        design.get("within_case_conditions_are_paired_repeated_measurements_only"),
        "within_case_conditions_are_paired_repeated_measurements_only",
    )
    require_true(
        design.get("ninety_percent_reference_is_not_an_active_acquisition_target"),
        "ninety_percent_reference_is_not_an_active_acquisition_target",
    )

    rule = stopping.get("effective_stopping_rule", {})
    for field in (
        "resume_from_exact_frozen_candidate_prefix",
        "stop_immediately_when_qualified_count_reaches_59",
        "auditing_any_later_candidate_after_first_reaching_59_is_forbidden",
        "retain_every_qualified_case_from_every_audited_slot",
        "no_sample_size_reestimation_using_unblinded_outcomes",
    ):
        require_true(rule.get(field), field)
    if rule.get("next_candidate_must_be") != "wardbeck":
        raise ValueError("v0.3 stopping rule must resume with wardbeck")

    unchanged = stopping.get("unchanged_frozen_components", {})
    for field in (
        "candidate_identity_and_order",
        "qualification_eligibility_rules",
        "curator_model_developer_and_ground_truth_role_separation",
        "payload_disclosure_boundary",
        "all_qualified_cases_retained",
        "primary_baselines",
        "cost_unit_and_sesoi",
        "success_safety_and_budget_gate_definitions",
        "one_shot_final_blind_execution",
    ):
        require_true(unchanged.get(field), f"unchanged_frozen_components.{field}")
    return {
        "base_path": base_path,
        "base_document": base_document,
        "review_path": review_path,
        "checkpoint_report_path": report_path,
        "checkpoint_audit_path": audit_path,
    }


def validate_qualification_report(
    report: dict[str, Any],
    base_amendment: dict[str, Any],
    base_amendment_path: Path,
    stopping_amendment: dict[str, Any],
    stopping_amendment_path: Path,
) -> dict[str, Any]:
    overlay = validate_stopping_amendment(
        stopping_amendment, stopping_amendment_path
    )
    if base_amendment_path.resolve() != overlay["base_path"].resolve():
        raise ValueError("Supplied base amendment differs from the v0.3 anchor")
    if sha256(base_amendment_path) != sha256(overlay["base_path"]):
        raise ValueError("Supplied base amendment hash differs from the v0.3 anchor")
    if base_amendment != overlay["base_document"]:
        raise ValueError("Supplied base amendment content differs from the v0.3 anchor")

    base_audit = legacy.validate_qualification_report(
        report, base_amendment, base_amendment_path
    )
    phase_1_qualified = sum(
        int(item["qualified_count"]) for item in report["phase_1_source_results"]
    )
    sequential = report["sequential_candidate_results"]
    cumulative = phase_1_qualified
    if cumulative >= EFFECTIVE_MINIMUM and sequential:
        raise ValueError("Sequential acquisition continued after the 59-case boundary")
    for index, item in enumerate(sequential):
        if item["qualification_status"] == "qualified":
            cumulative += 1
        if cumulative >= EFFECTIVE_MINIMUM and index != len(sequential) - 1:
            raise ValueError("Sequential acquisition continued after the 59-case boundary")

    qualified_count = int(base_audit["actual_qualified_case_count"])
    audited_count = int(base_audit["audited_candidate_count"])
    if qualified_count >= EFFECTIVE_MINIMUM:
        acquisition_complete = True
        source_search_required: bool | None = False
        decision_basis = (
            "stop_after_phase_1_effective_minimum_reached"
            if not sequential
            else "stop_at_first_sequential_candidate_reaching_59"
        )
        next_candidate = None
    elif audited_count == EXPECTED_POOL_SIZE:
        acquisition_complete = True
        source_search_required = True
        decision_basis = "resume_metadata_only_source_discovery_after_95_below_59"
        next_candidate = None
    else:
        acquisition_complete = False
        source_search_required = None
        decision_basis = "continue_with_next_frozen_candidate_under_v0.3"
        next_candidate = base_audit["next_frozen_candidate"]

    return {
        **base_audit,
        "audit_id": "project05-m3star-blind-staged-candidate-qualification-audit-v0.3",
        "status": (
            "qualification_complete"
            if acquisition_complete
            else "qualification_checkpoint_continue_acquisition"
        ),
        "checked_utc": utc_now(),
        "stopping_amendment_id": stopping_amendment["amendment_id"],
        "stopping_amendment_sha256": sha256(stopping_amendment_path),
        "minimum_valid_complete_cases_for_effective_power_design": EFFECTIVE_MINIMUM,
        "ninety_percent_power_reference_cases": NINETY_PERCENT_REFERENCE,
        "ninety_percent_reference_is_not_an_active_acquisition_target": True,
        "acquisition_complete": acquisition_complete,
        "source_search_required": source_search_required,
        "additional_qualified_cases_required_to_reach_power_minimum": max(
            EFFECTIVE_MINIMUM - qualified_count, 0
        ),
        "decision_basis": decision_basis,
        "next_frozen_candidate": next_candidate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-amendment", type=Path, required=True)
    parser.add_argument("--stopping-amendment", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    base_path = args.base_amendment.resolve(strict=True)
    stopping_path = args.stopping_amendment.resolve(strict=True)
    audit = validate_qualification_report(
        load_json(args.report.resolve(strict=True)),
        load_json(base_path),
        base_path,
        load_json(stopping_path),
        stopping_path,
    )
    if args.output is not None:
        write_json(args.output, audit)
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
