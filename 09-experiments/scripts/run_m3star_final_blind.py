#!/usr/bin/env python3
"""One-shot, persistent-gate runner for the sealed M3* external evaluation."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scipy.stats import t


def load_script(name: str) -> Any:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


m3_runner = load_script("run_m3star_experiment")
afa_runner = load_script("run_afa_voi_baselines")
depth_runner = load_script("run_lightweight_nonmyopic_real")
run_mvp = m3_runner.run_mvp

CONFIRMATION_PHRASE = "EXECUTE_PROJECT05_M3STAR_FINAL_BLIND_ONCE"
REPO_ROOT = Path(__file__).resolve().parents[2]
POWER_DESIGN_RELATIVE_PATH = Path(
    "09-experiments/results/m3star_final_blind_power_design_v0.1/power_design.json"
)
CONSUMPTION_LEDGER_RELATIVE_PATH = Path(
    "09-experiments/governance/locks/m3star-final-blind-consumed-v0.1.json"
)
MINIMUM_VALID_COMPLETE_CASES = 79
OPERATIONAL_RECRUITMENT_TARGET = 96
MINIMUM_JOINT_SUCCESS_CONDITIONS_PER_CASE = 30
PRIMARY_BASELINES = (
    "project05_m2",
    "project05_xgboost_policy",
    "project05_m3b_policy",
    afa_runner.MYOPIC,
    afa_runner.ROLLOUT,
    depth_runner.PLANNER,
)
M3_METHOD_IDS = (
    m3_runner.CORE_METHOD,
    "project05_xgboost_policy",
    "project05_m3b_policy",
    "project05_m2",
    "oracle_optimal",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def case_number(case_id: str) -> int | None:
    match = re.match(r"^C(\d+)(?:-|$)", case_id)
    return int(match.group(1)) if match else None


def resolve_repo_relative_path(value: str, field: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise ValueError(f"{field} must be repository-relative")
    resolved = (REPO_ROOT / path).resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"{field} escapes the repository root") from exc
    return resolved


def discover_final_case_dirs(cases_root: Path) -> list[Path]:
    final: list[tuple[int, str, Path]] = []
    for case_dir in run_mvp.discover_case_dirs(cases_root):
        config = load_json(case_dir / "case_config.json")
        case_id = str(config["case_id"])
        number = case_number(case_id)
        if number is not None and number >= 13:
            final.append((number, case_id, case_dir))
    final.sort()
    return [item[2] for item in final]


def validate_dataset_manifest(
    manifest_path: Path,
    case_dirs: list[Path],
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    if manifest.get("status") != "frozen":
        raise ValueError("Final-blind dataset manifest is not frozen")
    if manifest.get("curation_blind_to_model_development") is not True:
        raise ValueError("Dataset curation independence is not certified")
    if manifest.get("ground_truth_sealed_until_execution") is not True:
        raise ValueError("Ground truth was not sealed until execution")
    if manifest.get("all_cases_new_and_unseen") is not True:
        raise ValueError("Final-blind cases are not certified new and unseen")
    if manifest.get("source_and_attack_chain_deduplication_complete") is not True:
        raise ValueError("Final-blind source/attack-chain deduplication is incomplete")
    case_ids = [
        str(load_json(case_dir / "case_config.json")["case_id"])
        for case_dir in case_dirs
    ]
    if manifest.get("case_ids") != case_ids:
        raise ValueError("Dataset manifest case order/identity mismatch")
    if manifest.get("case_count") != len(case_ids):
        raise ValueError("Dataset manifest case count mismatch")
    file_hashes = manifest.get("case_files_sha256", {})
    for case_id, case_dir in zip(case_ids, case_dirs):
        expected = file_hashes.get(case_id)
        if not isinstance(expected, dict):
            raise ValueError(f"Missing dataset hashes for {case_id}")
        for filename in run_mvp.CASE_FILENAMES:
            path = case_dir / filename
            if expected.get(filename) != sha256(path):
                raise ValueError(f"Dataset file hash mismatch: {case_id}/{filename}")
    return manifest


def validate_protocol_document(protocol: dict[str, Any]) -> None:
    if protocol.get("status") != "frozen_before_final_blind_data_access":
        raise ValueError("Final-blind protocol is not frozen")
    if protocol.get("independent_statistical_unit") != "attack_chain_case_id":
        raise ValueError("Final-blind independent unit must be the attack-chain case")
    within_case = protocol.get("within_case_conditions", {})
    if within_case.get("count") != 45 or within_case.get("role") != (
        "paired_repeated_measurements_only"
    ):
        raise ValueError("The 45 within-case conditions must remain repeated measurements")
    if within_case.get("never_counted_as_independent_n") is not True:
        raise ValueError("Within-case conditions cannot be counted as independent cases")
    if protocol.get("primary_baselines") != list(PRIMARY_BASELINES):
        raise ValueError("Final-blind primary baselines differ from the frozen six")
    if protocol.get("oracle_role") != "ceiling_reference_not_a_baseline_to_outperform":
        raise ValueError("Oracle role differs from the frozen ceiling-reference role")

    sample_size = protocol.get("sample_size", {})
    if sample_size.get("minimum_valid_complete_cases") != MINIMUM_VALID_COMPLETE_CASES:
        raise ValueError("Minimum valid independent-case count differs from 79")
    if sample_size.get("operational_recruitment_target") != OPERATIONAL_RECRUITMENT_TARGET:
        raise ValueError("Operational recruitment target differs from 96")
    analysis_gate = protocol.get("analysis_gate", {})
    if analysis_gate.get("minimum_joint_success_conditions_per_case") != (
        MINIMUM_JOINT_SUCCESS_CONDITIONS_PER_CASE
    ):
        raise ValueError("Minimum joint-success repeated conditions differ from 30")
    if analysis_gate.get("all_primary_baselines_must_pass") is not True:
        raise ValueError("Intersection-union baseline gate is not enabled")
    if analysis_gate.get("case_mean_cost_uses_only_frozen_joint_success_conditions") is not True:
        raise ValueError("Case-mean cost rule differs from the frozen rule")

    data_seal = protocol.get("data_seal", {})
    for field in (
        "c13_plus_only",
        "all_cases_new_and_unseen",
        "curation_blind_to_model_development",
        "source_and_attack_chain_deduplication_required",
        "ground_truth_sealed_until_one_shot_execution",
    ):
        if data_seal.get(field) is not True:
            raise ValueError(f"Final-blind data seal is missing {field}")
    cost_seal = protocol.get("cost_seal", {})
    for field in (
        "training_and_evaluation_profiles_must_be_distinct",
        "evaluation_profile_frozen_before_execution",
        "evaluation_profile_scope_exactly_matches_final_cases",
        "evaluation_costs_measured_without_model_output_access",
    ):
        if cost_seal.get(field) is not True:
            raise ValueError(f"Final-blind cost seal is missing {field}")

    design = protocol.get("frozen_design", {})
    design_path = resolve_repo_relative_path(
        str(design.get("power_design_path", "")),
        "frozen_design.power_design_path",
    )
    if design_path != (REPO_ROOT / POWER_DESIGN_RELATIVE_PATH).resolve():
        raise ValueError("Final-blind power-design path differs from the frozen path")
    if not design_path.is_file() or design.get("power_design_sha256") != sha256(design_path):
        raise ValueError("Final-blind power-design hash differs from the protocol")

    one_shot = protocol.get("one_shot_gate", {})
    ledger_path = resolve_repo_relative_path(
        str(one_shot.get("consumption_ledger_path", "")),
        "one_shot_gate.consumption_ledger_path",
    )
    expected_ledger = (REPO_ROOT / CONSUMPTION_LEDGER_RELATIVE_PATH).resolve()
    if ledger_path != expected_ledger:
        raise ValueError("Consumption ledger path differs from the frozen path")
    if one_shot.get("confirmation_phrase_sha256") != hashlib.sha256(
        CONFIRMATION_PHRASE.encode("utf-8")
    ).hexdigest():
        raise ValueError("One-shot confirmation phrase hash differs from the runner")
    if one_shot.get("failed_execution_is_consumed") is not True:
        raise ValueError("Failed final-blind execution must remain consumed")


def static_protocol_checks(
    protocol_path: Path,
    frozen_model_result_dir: Path,
    training_cost_profile_path: Path,
) -> dict[str, Any]:
    protocol = load_json(protocol_path)
    validate_protocol_document(protocol)
    frozen = protocol["frozen_implementation"]
    current_contract = m3_runner.runtime_contract_metadata()
    if frozen["runtime_contract_sha256"] != current_contract["sha256"]:
        raise ValueError("Runtime contract hash differs from blind protocol")
    if frozen["final_blind_runner_sha256"] != sha256(Path(__file__)):
        raise ValueError("Final-blind runner hash differs from protocol")
    source = m3_runner.frozen_model_source_metadata(frozen_model_result_dir)
    for field in (
        "experiment_report_sha256",
        "evaluation_manifest_sha256",
        "training_dataset_summary_sha256",
        "model_metadata_sha256",
    ):
        if source[field] != frozen[field]:
            raise ValueError(f"Frozen model source mismatch for {field}")
    training_profile = run_mvp.load_cost_profile(training_cost_profile_path)
    if training_profile["sha256"] != frozen["training_cost_profile_sha256"]:
        raise ValueError("Training cost profile hash differs from blind protocol")
    return {"protocol": protocol, "model_source": source}


def preflight(
    protocol_path: Path,
    cases_root: Path,
    dataset_manifest_path: Path,
    training_cost_profile_path: Path,
    evaluation_cost_profile_path: Path,
    frozen_model_result_dir: Path,
    output_dir: Path,
    consumption_ledger: Path,
) -> dict[str, Any]:
    static = static_protocol_checks(
        protocol_path,
        frozen_model_result_dir,
        training_cost_profile_path,
    )
    protocol = static["protocol"]
    if training_cost_profile_path.resolve() == evaluation_cost_profile_path.resolve():
        raise ValueError("Training and final-blind evaluation cost profiles must differ")
    if consumption_ledger.exists():
        raise ValueError(
            f"Final-blind evaluation has already been consumed: {consumption_ledger}"
        )
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Final-blind output directory is not empty: {output_dir}")
    case_dirs = discover_final_case_dirs(cases_root)
    target = int(protocol["sample_size"]["operational_recruitment_target"])
    if len(case_dirs) < target:
        raise ValueError(
            f"Final-blind cohort has {len(case_dirs)} cases; {target} are required"
        )
    case_ids = [
        str(load_json(case_dir / "case_config.json")["case_id"])
        for case_dir in case_dirs
    ]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("Duplicate final-blind case ids")
    if any((case_number(case_id) or 0) < 13 for case_id in case_ids):
        raise ValueError("Final-blind cohort contains a pre-C13 case")
    dataset_manifest = validate_dataset_manifest(dataset_manifest_path, case_dirs)
    evaluation_profile = run_mvp.load_cost_profile(evaluation_cost_profile_path)
    if evaluation_profile["document"].get("status") != "frozen":
        raise ValueError("Final-blind evaluation cost profile is not frozen")
    if evaluation_profile["document"].get("regime") != "measured":
        raise ValueError("Final-blind evaluation cost profile must use measured cost")
    if evaluation_profile["sha256"] == static["protocol"]["frozen_implementation"][
        "training_cost_profile_sha256"
    ]:
        raise ValueError("Training and final-blind evaluation cost hashes must differ")
    evaluation_case_ids = evaluation_profile["document"].get("scope", {}).get(
        "case_ids"
    )
    if evaluation_case_ids != case_ids:
        raise ValueError("Evaluation cost-profile scope must exactly match final cases")
    for case_dir in case_dirs:
        config = load_json(case_dir / "case_config.json")
        actions = load_json(case_dir / "acquisition_actions.json")
        run_mvp.apply_cost_regime(
            actions,
            config["case_id"],
            "measured",
            evaluation_profile,
        )
    return {
        "status": "ready_for_one_shot_execution",
        "checked_utc": utc_now(),
        "protocol_sha256": sha256(protocol_path),
        "dataset_manifest_sha256": sha256(dataset_manifest_path),
        "training_cost_profile_sha256": static["protocol"][
            "frozen_implementation"
        ]["training_cost_profile_sha256"],
        "evaluation_cost_profile_sha256": evaluation_profile["sha256"],
        "case_count": len(case_dirs),
        "case_ids": case_ids,
        "case_dirs": case_dirs,
        "dataset_manifest": dataset_manifest,
    }


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Cannot write empty final-blind results")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def condition_key(row: dict[str, Any]) -> tuple[str, str, float, int]:
    return (
        str(row["case_id"]),
        str(row["mask_strategy"]),
        float(row["mask_intensity"]),
        int(row["seed"]),
    )


def merge_primary_rows(
    m3_rows: list[dict[str, Any]],
    afa_rows: list[dict[str, Any]],
    depth_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    keep = {m3_runner.CORE_METHOD, *PRIMARY_BASELINES, "oracle_optimal"}
    combined = [row for row in m3_rows if row["planner"] in keep]
    combined.extend(
        row for row in afa_rows if row["planner"] in {afa_runner.MYOPIC, afa_runner.ROLLOUT}
    )
    combined.extend(
        row for row in depth_rows if row["planner"] == depth_runner.PLANNER
    )
    seen: set[tuple[Any, ...]] = set()
    for row in combined:
        key = (*condition_key(row), str(row["planner"]))
        if key in seen:
            raise ValueError(f"Duplicate merged final-blind result: {key}")
        seen.add(key)
    return combined


def one_sided_upper_mean(values: list[float], alpha: float = 0.05) -> float:
    if len(values) < 2:
        raise ValueError("At least two independent case effects are required")
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    standard_error = math.sqrt(variance / len(values))
    return mean + float(t.ppf(1.0 - alpha, len(values) - 1)) * standard_error


def analyze_final_rows(
    rows: list[dict[str, Any]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    indexed = {
        (*condition_key(row), str(row["planner"])): row
        for row in rows
    }
    case_ids = sorted({str(row["case_id"]) for row in rows})
    minimum_valid = int(protocol["sample_size"]["minimum_valid_complete_cases"])
    minimum_joint = int(
        protocol["analysis_gate"]["minimum_joint_success_conditions_per_case"]
    )
    comparisons: dict[str, Any] = {}
    for baseline in PRIMARY_BASELINES:
        case_effects: list[float] = []
        success_loss_cases: list[str] = []
        invalid_cases: list[str] = []
        for case_id in case_ids:
            keys = sorted(
                {
                    key[:4]
                    for key in indexed
                    if key[0] == case_id
                    and key[4] in {m3_runner.CORE_METHOD, baseline}
                }
            )
            candidate_rows = [
                indexed[(*key, m3_runner.CORE_METHOD)] for key in keys
            ]
            baseline_rows = [indexed[(*key, baseline)] for key in keys]
            candidate_success = sum(int(row["reached_target"]) for row in candidate_rows)
            baseline_success = sum(int(row["reached_target"]) for row in baseline_rows)
            if candidate_success < baseline_success:
                success_loss_cases.append(case_id)
            deltas = [
                float(candidate["cost_to_target"]) - float(control["cost_to_target"])
                for candidate, control in zip(candidate_rows, baseline_rows)
                if int(candidate["reached_target"]) and int(control["reached_target"])
            ]
            if len(deltas) < minimum_joint:
                invalid_cases.append(case_id)
            else:
                case_effects.append(sum(deltas) / len(deltas))
        upper = (
            one_sided_upper_mean(case_effects)
            if len(case_effects) >= 2
            else None
        )
        mean = sum(case_effects) / len(case_effects) if case_effects else None
        comparisons[baseline] = {
            "valid_independent_case_count": len(case_effects),
            "invalid_case_ids": invalid_cases,
            "case_success_loss_count": len(success_loss_cases),
            "case_success_loss_ids": success_loss_cases,
            "mean_case_cost_delta_m3star_minus_baseline": mean,
            "one_sided_95_percent_upper_mean_delta": upper,
            "success_gate_pass": len(success_loss_cases) == 0,
            "sample_size_gate_pass": len(case_effects) >= minimum_valid,
            "cost_superiority_gate_pass": upper is not None and upper < 0.0,
        }
        comparisons[baseline]["all_gates_pass"] = all(
            comparisons[baseline][field]
            for field in (
                "success_gate_pass",
                "sample_size_gate_pass",
                "cost_superiority_gate_pass",
            )
        )
    candidate_rows = [
        row for row in rows if row["planner"] == m3_runner.CORE_METHOD
    ]
    safety_violations = sum(
        int(row.get("ceiling_violation", 0) or 0) for row in candidate_rows
    )
    budget_violations = sum(
        float(row["budget_used"]) > float(row["budget_total"]) + 1e-9
        for row in candidate_rows
    )
    global_pass = (
        all(result["all_gates_pass"] for result in comparisons.values())
        and safety_violations == 0
        and budget_violations == 0
    )
    return {
        "independent_case_count": len(case_ids),
        "within_case_conditions_are_repeated_measurements": True,
        "multiplicity_structure": "intersection_union_all_baselines_must_pass",
        "per_comparison_one_sided_alpha": 0.05,
        "comparisons": comparisons,
        "safety_violation_count": safety_violations,
        "budget_violation_count": budget_violations,
        "global_confirmatory_gate_pass": global_pass,
        "formal_external_superiority_claim_allowed": global_pass,
    }


def output_hashes(output_dir: Path) -> dict[str, str]:
    return {
        str(path.relative_to(output_dir)).replace("\\", "/"): sha256(path)
        for path in sorted(output_dir.rglob("*"))
        if path.is_file()
    }


def execute_once(args: argparse.Namespace, checked: dict[str, Any]) -> dict[str, Any]:
    protocol = load_json(args.protocol)
    ledger = resolve_repo_relative_path(
        protocol["one_shot_gate"]["consumption_ledger_path"],
        "one_shot_gate.consumption_ledger_path",
    )
    ledger.parent.mkdir(parents=True, exist_ok=True)
    started = {
        "status": "consumed_execution_started",
        "started_utc": utc_now(),
        "protocol_sha256": checked["protocol_sha256"],
        "dataset_manifest_sha256": checked["dataset_manifest_sha256"],
        "evaluation_cost_profile_sha256": checked[
            "evaluation_cost_profile_sha256"
        ],
        "case_count": checked["case_count"],
    }
    with ledger.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(started, indent=2, ensure_ascii=False) + "\n")
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        training_profile = run_mvp.load_cost_profile(args.training_cost_profile)
        evaluation_profile = run_mvp.load_cost_profile(args.evaluation_cost_profile)
        prefixes = tuple(path.name for path in checked["case_dirs"])
        m3_dir = args.output_dir / "m3star_core"
        m3_runner.run_experiment(
            args.examples_root,
            args.cases_root,
            m3_dir,
            evaluation_prefixes=prefixes,
            evaluation_role="final_blind",
            confirm_final_test_once=True,
            partitions=("development",),
            cost_regime="measured",
            cost_profile=training_profile,
            evaluation_cost_profile=evaluation_profile,
            training_scope="real_only_three",
            max_depth=3,
            boost_rounds=150,
            target_reach_threshold=0.9,
            max_outcome_nodes=8,
            method_ids=M3_METHOD_IDS,
            frozen_model_result_dir=args.frozen_model_result_dir,
        )
        afa_rows, afa_traces = afa_runner.execute_cases(
            checked["case_dirs"],
            channel_prior_multiplier=1.0,
            cost_regime="measured",
            cost_profile=evaluation_profile,
        )
        depth_rows, depth_traces = depth_runner.execute_cases(
            checked["case_dirs"],
            channel_prior_multiplier=1.0,
            cost_regime="measured",
            cost_profile=evaluation_profile,
        )
        m3_rows = read_csv(m3_dir / "development_policy_results.csv")
        merged = merge_primary_rows(m3_rows, afa_rows, depth_rows)
        write_csv(args.output_dir / "final_blind_primary_results.csv", merged)
        with gzip.open(
            args.output_dir / "external_baseline_traces.json.gz",
            "wt",
            encoding="utf-8",
        ) as handle:
            json.dump(
                {"afa": afa_traces, "depth2": depth_traces},
                handle,
                ensure_ascii=False,
                allow_nan=False,
            )
        analysis = analyze_final_rows(merged, protocol)
        report = {
            "evaluation_id": "project05-m3star-final-blind-v0.1",
            "status": "one_shot_final_blind_complete",
            "completed_utc": utc_now(),
            "protocol_sha256": checked["protocol_sha256"],
            "dataset_manifest_sha256": checked["dataset_manifest_sha256"],
            "evaluation_cost_profile_sha256": checked[
                "evaluation_cost_profile_sha256"
            ],
            "analysis": analysis,
        }
        write_json(args.output_dir / "final_blind_analysis.json", report)
        completed = {
            **started,
            "status": "consumed_execution_complete",
            "completed_utc": utc_now(),
            "global_confirmatory_gate_pass": analysis[
                "global_confirmatory_gate_pass"
            ],
            "output_sha256": output_hashes(args.output_dir),
        }
        write_json(ledger, completed)
        return report
    except BaseException as exc:
        write_json(
            ledger,
            {
                **started,
                "status": "consumed_execution_failed_no_rerun_allowed",
                "failed_utc": utc_now(),
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--examples-root", type=Path, required=True)
    parser.add_argument("--cases-root", type=Path, required=True)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--training-cost-profile", type=Path, required=True)
    parser.add_argument("--evaluation-cost-profile", type=Path, required=True)
    parser.add_argument("--frozen-model-result-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--execute-final-blind", action="store_true")
    parser.add_argument("--confirmation-phrase")
    args = parser.parse_args()
    protocol = load_json(args.protocol)
    ledger = resolve_repo_relative_path(
        protocol["one_shot_gate"]["consumption_ledger_path"],
        "one_shot_gate.consumption_ledger_path",
    )
    checked = preflight(
        args.protocol,
        args.cases_root,
        args.dataset_manifest,
        args.training_cost_profile,
        args.evaluation_cost_profile,
        args.frozen_model_result_dir,
        args.output_dir,
        ledger,
    )
    public_preflight = {
        key: value
        for key, value in checked.items()
        if key not in {"case_dirs", "dataset_manifest"}
    }
    if args.preflight_only:
        write_json(args.output_dir / "preflight_report.json", public_preflight)
        print(json.dumps(public_preflight, indent=2, ensure_ascii=False))
        return
    if not args.execute_final_blind:
        parser.error("Use --preflight-only or explicitly use --execute-final-blind")
    if args.confirmation_phrase != CONFIRMATION_PHRASE:
        parser.error("Exact one-shot confirmation phrase is required")
    report = execute_once(args, checked)
    print(json.dumps(report["analysis"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
