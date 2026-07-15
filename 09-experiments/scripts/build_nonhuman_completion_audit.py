#!/usr/bin/env python3
"""Build a hash-anchored audit of all executable non-human Project05 work."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
RESULTS = EXP / "results"


def load_script(name: str) -> Any:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"completion_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_audit_manifest(path: Path) -> dict[str, Any]:
    manifest = load_json(path / "audit_manifest.json")
    for filename, expected in manifest["outputs"].items():
        if sha256_file(path / filename) != expected:
            raise ValueError(f"Audit output SHA-256 mismatch: {path / filename}")
    return {
        "validation_status": "passed",
        "audit_id": manifest["audit_id"],
        "output_count": len(manifest["outputs"]),
        "output_sha256_verified": True,
    }


def collect_validations() -> dict[str, Any]:
    parameter = load_script("validate_parameter_governance_output")
    afa = load_script("validate_afa_endpoint_output")
    depth = load_script("validate_depth2_output")
    xgboost = load_script("validate_xgboost_output")
    measured = load_script("validate_operational_cost_measurements")
    external = load_script("validate_external_ground_truth")
    case_dirs = measured.discover_case_dirs(EXP / "examples", EXP / "real_cases")
    matrix: dict[str, Any] = {
        "parameter_governance_v0.1": parameter.validate(
            RESULTS / "parameter_governance_v0.1"
        ),
        "parameter_governance_w6_v0.2": parameter.validate(
            RESULTS / "parameter_governance_w6_v0.2"
        ),
        "policy_prior_sensitivity_audit_v0.2": verify_audit_manifest(
            RESULTS / "policy_prior_sensitivity_audit_v0.2"
        ),
    }
    for name in (
        "afa_endpoint_c07_c12_v0.1",
        "afa_endpoint_c07_c12_prior_x0.75_v0.1",
        "afa_endpoint_c07_c12_prior_x1.25_v0.1",
        "afa_endpoint_c07_c12_uniform_v0.2",
    ):
        matrix[name] = afa.validate(RESULTS / name)
    for name in (
        "depth2_endpoint_c07_c12_v0.3",
        "depth2_endpoint_c07_c12_prior_x0.75_v0.3",
        "depth2_endpoint_c07_c12_prior_x1.25_v0.3",
        "depth2_endpoint_c07_c12_uniform_v0.3",
    ):
        matrix[name] = depth.validate(RESULTS / name)
    for name in (
        "xgboost_c07_c12_v0.3",
        "xgboost_c07_c12_uniform_v0.3",
    ):
        matrix[name] = xgboost.validate(RESULTS / name)
    matrix["measured_cost_infrastructure_v0.1"] = measured.validate_batch(
        RESULTS / "measured_cost_infrastructure_v0.1" / "operational_cost_measurements.json",
        case_dirs,
    )
    matrix["external_ground_truth_interface_v0.1"] = external.validate_bundle(
        RESULTS / "external_ground_truth_interface_v0.1" / "external_ground_truth_bundle.json",
        case_dirs,
    )
    return matrix


def git_branch_state() -> dict[str, Any]:
    result = subprocess.run(
        ["git", "branch", "--format=%(refname:short)"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    branches = sorted(line.strip() for line in result.stdout.splitlines() if line.strip())
    return {
        "local_branches": branches,
        "independent_feature_branches_available": len(branches) > 1,
        "git_merge_performed": False,
        "integration_method": (
            "git_merge_not_applicable_single_local_branch; runners_contracts_validators_and_new-version-results_integrated_in_worktree"
        ),
    }


def build_manifest(
    validations: dict[str, Any],
    test_passed: int,
    test_skipped: int,
) -> dict[str, Any]:
    failures = {
        name: report.get("validation_status")
        for name, report in validations.items()
        if report.get("validation_status") not in {
            "passed",
            "passed_with_runtime_allowlist",
        }
    }
    if failures:
        raise ValueError(f"Completion audit contains failed validations: {failures}")
    measured = validations["measured_cost_infrastructure_v0.1"]
    external = validations["external_ground_truth_interface_v0.1"]
    return {
        "audit_id": "project05-nonhuman-completion-audit-v0.1",
        "scope": "all_executable_work_except_human_annotation_and_paper_patent_writing",
        "status": "automatable_scope_complete_with_external_evidence_gates_open",
        "automatable_implementation_complete": True,
        "formal_outputs_validated": len(validations),
        "methodology_items": {
            "cost": {
                "legacy_and_uniform_execution": "complete",
                "rubric": "blocked_pending_independent_human_ratings_and_freeze",
                "measured_infrastructure": "complete",
                "measured_values": "blocked_pending_real_operational_measurements",
            },
            "W1_threshold_grid": "complete",
            "W7_corroboration_k_of_n": "complete",
            "W2_m2_weight_and_alpha_sensitivity": "complete",
            "W6_expected_effect_and_channel_prior_sensitivity": "complete_with_measured_substitution_external_gate_open",
            "W3_human_annotation_round2": "excluded_by_user_instruction",
            "W4_evidence_limited_endpoints": "implemented; external actor accuracy remains not_identifiable",
            "W5_afa_endpoint_contract": "complete",
            "W9_runtime_information_boundaries": "complete_for_afa_depth2_xgboost_logistic",
        },
        "external_evidence_gates": {
            "operational_measurement_records": measured["record_count"],
            "operational_actions_missing": measured["missing_action_count"],
            "formal_measured_cost_profile_ready": measured["formal_measured_cost_profile_ready"],
            "external_ground_truth_records": external["record_count"],
            "external_actor_accuracy": external["external_actor_accuracy"],
            "external_actor_accuracy_status": external["external_actor_accuracy_status"],
            "analyst_utility_status": external["analyst_utility_status"],
        },
        "human_dependent_gates": {
            "round2_annotation": "not_started",
            "rubric_component_ratings_pending": 360,
        },
        "test_verification": {
            "passed": int(test_passed),
            "skipped": int(test_skipped),
            "failed": 0,
        },
        "branch_integration": git_branch_state(),
        "all_experiments_complete": False,
        "paper_or_patent_gate": "closed_until_human_and_operational_gates_are_satisfied",
        "paper_or_patent_updated": False,
    }


def write_audit(
    output_dir: Path,
    test_passed: int,
    test_skipped: int,
) -> dict[str, Any]:
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise FileExistsError(f"Completion audit output must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    validations = collect_validations()
    validation_path = output_dir / "validation_matrix.json"
    validation_path.write_text(
        json.dumps(validations, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    manifest = build_manifest(validations, test_passed, test_skipped)
    manifest["validation_matrix_sha256"] = sha256_file(validation_path)
    manifest["source_manifest_sha256"] = {
        path.relative_to(ROOT).as_posix(): sha256_file(path)
        for path in sorted(RESULTS.glob("*/evaluation_manifest.json"))
        if path.parent.name in validations
    }
    manifest_path = output_dir / "completion_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULTS / "nonhuman_completion_audit_v0.1",
    )
    parser.add_argument("--test-passed", type=int, required=True)
    parser.add_argument("--test-skipped", type=int, required=True)
    args = parser.parse_args()
    manifest = write_audit(args.output_dir, args.test_passed, args.test_skipped)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
