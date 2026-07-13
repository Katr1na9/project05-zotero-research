#!/usr/bin/env python3
"""Audit and summarize frozen C11 transfers across policy families."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CASE_ID = "C11-otrf-apt29-day1-scranton-nashua"
EXPECTED_TRAIN_CASES = [
    "C01-linux-provenance",
    "C02-freebsd-provenance",
    "C03-windows-host",
    "C04-darpa-e3-fivedirections",
    "C05-darpa-e3-cadets",
    "C06-darpa-e3-cadets-0412",
]
PAIR_KEY = ("case_id", "mask_strategy", "mask_intensity", "seed")
MODEL_LABELS = (
    "label_resolves_critical_gap_node",
    "label_yield_positive",
    "label_reaches_target_after_action",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rows_for_planner(
    rows: list[dict[str, str]], planner: str
) -> list[dict[str, str]]:
    return sorted(
        (row for row in rows if row["planner"] == planner),
        key=lambda row: tuple(row[field] for field in PAIR_KEY),
    )


def assert_shared_rows_match(
    reference_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    planners: tuple[str, ...],
) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    for planner in planners:
        reference = rows_for_planner(reference_rows, planner)
        candidate = rows_for_planner(candidate_rows, planner)
        matches = reference == candidate and len(reference) == 45
        checks[planner] = matches
        if not matches:
            raise ValueError(f"Frozen shared rows changed for {planner}")
    return checks


def paired_against_m2(
    rows: list[dict[str, str]], candidate_planner: str
) -> dict[str, Any]:
    grouped: dict[tuple[str, ...], dict[str, dict[str, str]]] = {}
    for row in rows:
        key = tuple(row[field] for field in PAIR_KEY)
        grouped.setdefault(key, {})[row["planner"]] = row

    wins = ties = losses = repairs = regressions = joint_success = 0
    differences: list[float] = []
    for planners in grouped.values():
        m2 = planners["project05_m2"]
        candidate = planners[candidate_planner]
        m2_success = int(m2["reached_target"])
        candidate_success = int(candidate["reached_target"])
        repairs += int(candidate_success == 1 and m2_success == 0)
        regressions += int(candidate_success == 0 and m2_success == 1)
        if not (m2_success and candidate_success):
            continue
        joint_success += 1
        difference = float(candidate["cost_to_target"]) - float(
            m2["cost_to_target"]
        )
        differences.append(difference)
        wins += int(difference < 0)
        ties += int(difference == 0)
        losses += int(difference > 0)

    return {
        "paired_condition_count": len(grouped),
        "joint_success_count": joint_success,
        "success_repairs_vs_m2": repairs,
        "success_regressions_vs_m2": regressions,
        "cost_wins_vs_m2": wins,
        "cost_ties_vs_m2": ties,
        "cost_losses_vs_m2": losses,
        "mean_cost_difference_vs_m2_on_joint_success": (
            round(sum(differences) / len(differences), 4)
            if differences
            else None
        ),
    }


def compact_result(
    planner: str,
    family: str,
    summary: dict[str, Any],
) -> dict[str, Any]:
    mean_cost = float(summary["mean_cost_to_target"])
    mean_regret = summary.get("mean_cost_regret_vs_oracle")
    if mean_regret is None and float(summary["success_rate"]) == 1.0:
        mean_regret = round(mean_cost - 3.0, 4)
    return {
        "planner": planner,
        "family": family,
        "repeated_run_count": int(
            summary["repeated_run_count"]
            if "repeated_run_count" in summary
            else summary["runs"]
        ),
        "success_rate": float(summary["success_rate"]),
        "mean_cost_to_target": mean_cost,
        "mean_cost_regret_vs_oracle": mean_regret,
        "mean_zero_yield_actions": summary.get("mean_zero_yield_actions"),
        "premature_stop_rate": float(summary["premature_stop_rate"]),
        "ceiling_violation_rate": float(summary.get("ceiling_violation_rate", 0.0)),
    }


def build_summary(results_root: Path) -> dict[str, Any]:
    extended = results_root / "c11_extended_policies_v0.1"
    xgb_dir = extended / "xgboost"
    afa_dir = extended / "afa_voi"
    depth_dir = extended / "depth2"
    frozen_model_dir = results_root / "xgboost_c01_c06_train_c07_c10_test"
    reference_csv = (
        results_root
        / "c11_holdout_v0.1"
        / "c11-otrf-apt29-day1-scranton-nashua_mvp_results.csv"
    )
    reference_summary_path = (
        results_root
        / "c11_holdout_v0.1"
        / "c11-otrf-apt29-day1-scranton-nashua_mvp_summary.json"
    )

    xgb_report = load_json(xgb_dir / "xgboost_experiment_summary.json")
    afa_summary = load_json(afa_dir / "afa_voi_policy_summary.json")
    depth_summary = load_json(depth_dir / "nonmyopic_policy_summary.json")
    reference_summary = load_json(reference_summary_path)
    reference_rows = load_csv(reference_csv)
    xgb_rows = load_csv(xgb_dir / "xgboost_policy_results.csv")
    afa_rows = load_csv(afa_dir / "afa_voi_policy_results.csv")
    depth_rows = load_csv(depth_dir / "nonmyopic_policy_results.csv")

    if xgb_report["train_case_ids"] != EXPECTED_TRAIN_CASES:
        raise ValueError("C11 XGBoost transfer did not preserve C01-C06 training")
    if xgb_report["test_case_ids"] != [CASE_ID]:
        raise ValueError("C11 XGBoost transfer test set is not isolated")

    model_hash_checks: dict[str, dict[str, Any]] = {}
    for label in MODEL_LABELS:
        name = f"xgboost_{label}.json"
        frozen_hash = sha256(frozen_model_dir / name)
        transfer_hash = sha256(xgb_dir / name)
        matches = frozen_hash == transfer_hash
        if not matches:
            raise ValueError(f"Frozen XGBoost model changed for {label}")
        model_hash_checks[label] = {
            "reference_sha256": frozen_hash,
            "c11_transfer_sha256": transfer_hash,
            "identical": matches,
        }

    shared_checks = {
        "xgboost_run": assert_shared_rows_match(
            reference_rows,
            xgb_rows,
            (
                "coverage_greedy",
                "project05_m2",
                "project05_m3a_gap_compat",
                "oracle_optimal",
            ),
        ),
        "afa_run": assert_shared_rows_match(
            reference_rows,
            afa_rows,
            ("project05_m2", "oracle_optimal"),
        ),
        "depth2_run": assert_shared_rows_match(
            reference_rows,
            depth_rows,
            ("project05_m2", "oracle_optimal"),
        ),
    }

    xgb_overall = xgb_report["policy_summary"]["overall_by_planner"]
    afa_overall = afa_summary["overall_by_planner"]
    depth_overall = depth_summary["overall_by_planner"]
    planner_results = [
        compact_result("oracle_optimal", "reference", reference_summary["oracle_optimal"]),
        compact_result(
            "coverage_greedy", "transparent_rule", reference_summary["coverage_greedy"]
        ),
        compact_result("project05_m1", "transparent_rule", reference_summary["project05_m1"]),
        compact_result("project05_m2", "transparent_rule", reference_summary["project05_m2"]),
        compact_result(
            "project05_m3a_gap_compat",
            "transparent_rule",
            reference_summary["project05_m3a_gap_compat"],
        ),
        compact_result(
            "project05_m3b_policy", "logistic_transfer", xgb_overall["project05_m3b_policy"]
        ),
        compact_result(
            "project05_xgboost_policy",
            "xgboost_transfer",
            xgb_overall["project05_xgboost_policy"],
        ),
        compact_result("afa_voi_myopic", "afa_adapter", afa_overall["afa_voi_myopic"]),
        compact_result(
            "afa_voi_rollout_h3", "afa_adapter", afa_overall["afa_voi_rollout_h3"]
        ),
        compact_result(
            "project05_depth2_public",
            "public_lookahead",
            depth_overall["project05_depth2_public"],
        ),
    ]

    paired = {
        "project05_m3b_policy": paired_against_m2(xgb_rows, "project05_m3b_policy"),
        "project05_xgboost_policy": paired_against_m2(
            xgb_rows, "project05_xgboost_policy"
        ),
        "afa_voi_myopic": paired_against_m2(afa_rows, "afa_voi_myopic"),
        "afa_voi_rollout_h3": paired_against_m2(afa_rows, "afa_voi_rollout_h3"),
        "project05_depth2_public": paired_against_m2(
            depth_rows, "project05_depth2_public"
        ),
    }

    source_files = [
        reference_csv,
        reference_summary_path,
        xgb_dir / "xgboost_experiment_summary.json",
        xgb_dir / "xgboost_policy_results.csv",
        afa_dir / "afa_voi_policy_summary.json",
        afa_dir / "afa_voi_policy_results.csv",
        depth_dir / "nonmyopic_policy_summary.json",
        depth_dir / "nonmyopic_policy_results.csv",
    ]
    return {
        "experiment_id": "project05-c11-extended-frozen-policy-transfer-v0.1",
        "case_id": CASE_ID,
        "design": {
            "independent_attack_chain_count": 1,
            "repeated_condition_count_per_planner": 45,
            "target_granularity": "G2_tactic_intent",
            "node_coverage_semantics": "AND",
            "aggregation_rule": "C11 remains separate from C07-C10 G3 means",
        },
        "training_isolation": {
            "train_case_ids": xgb_report["train_case_ids"],
            "test_case_ids": xgb_report["test_case_ids"],
            "c11_used_for_training": CASE_ID in xgb_report["train_case_ids"],
            "model_hash_checks": model_hash_checks,
        },
        "shared_baseline_row_checks": shared_checks,
        "planner_results": planner_results,
        "paired_against_m2": paired,
        "xgboost_offline_primary_label_test": {
            "xgboost": xgb_report["classification"][
                "label_resolves_critical_gap_node"
            ]["xgboost"]["test"],
            "logistic": xgb_report["classification"][
                "label_resolves_critical_gap_node"
            ]["logistic"]["test"],
        },
        "claim_boundary": [
            "C11 is one emulated attack chain with 45 repeated conditions.",
            "Sequential transfer results do not establish cross-scene superiority.",
            "Offline classification and sequential policy utility are reported separately.",
            "No result is actor or campaign attribution accuracy.",
        ],
        "source_sha256": {
            str(path.relative_to(ROOT)): sha256(path) for path in source_files
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit and summarize frozen C11 policy-family transfers."
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=ROOT / "09-experiments" / "results",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            ROOT / "09-experiments" / "results" / "c11_extended_policies_v0.1"
        ),
    )
    args = parser.parse_args()
    summary = build_summary(args.results_root)
    write_json(args.output_dir / "c11_extended_policy_summary.json", summary)
    write_csv(args.output_dir / "c11_extended_policy_table.csv", summary["planner_results"])
    print(json.dumps(summary["paired_against_m2"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
