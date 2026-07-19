#!/usr/bin/env python3
"""Case-level analysis for the six-case M3* development evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


CORE = "project05_m3star_h3_dual"
BASELINES = (
    "project05_m2",
    "project05_xgboost_policy",
    "project05_m3b_policy",
)
CONDITION_FIELDS = ("case_id", "mask_strategy", "mask_intensity", "seed")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def condition_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["case_id"]),
        str(row["mask_strategy"]),
        float(row["mask_intensity"]),
        int(row["seed"]),
    )


def index_method(
    rows: list[dict[str, Any]],
    method: str,
) -> dict[tuple[Any, ...], dict[str, Any]]:
    indexed: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        if row["planner"] != method:
            continue
        key = condition_key(row)
        if key in indexed:
            raise ValueError(f"Duplicate {method} condition: {key}")
        indexed[key] = row
    return indexed


def finite_float(row: dict[str, Any], field: str) -> float | None:
    value = row.get(field)
    if value in (None, ""):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def descriptives(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    return {
        "n_cases": int(array.size),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "sd": float(array.std(ddof=1)) if array.size > 1 else None,
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def case_bootstrap(
    values: list[float],
    *,
    seed: int,
    draws: int,
) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    sampled_means = rng.choice(
        array,
        size=(draws, array.size),
        replace=True,
    ).mean(axis=1)
    lower, upper = np.quantile(sampled_means, [0.025, 0.975])
    return {
        "resampling_unit": "case_id",
        "draws": draws,
        "seed": seed,
        "mean_effect": float(array.mean()),
        "percentile_95_interval": [float(lower), float(upper)],
        "bootstrap_fraction_below_zero": float(np.mean(sampled_means < 0.0)),
        "bootstrap_fraction_at_or_below_zero": float(
            np.mean(sampled_means <= 0.0)
        ),
    }


def paired_effects(
    rows: list[dict[str, Any]],
    baseline: str,
    *,
    bootstrap_seed: int,
    bootstrap_draws: int,
) -> dict[str, Any]:
    candidate = index_method(rows, CORE)
    reference = index_method(rows, baseline)
    if set(candidate) != set(reference):
        raise ValueError(f"Condition mismatch for {baseline}")
    case_ids = sorted({key[0] for key in candidate})
    by_case: dict[str, Any] = {}
    for case_id in case_ids:
        keys = [key for key in sorted(candidate) if key[0] == case_id]
        success_losses = 0
        success_gains = 0
        cost_deltas: list[float] = []
        action_deltas: list[float] = []
        all_episode_step_deltas: list[float] = []
        for key in keys:
            core_row = candidate[key]
            base_row = reference[key]
            core_success = int(core_row["reached_target"]) == 1
            base_success = int(base_row["reached_target"]) == 1
            success_losses += int(not core_success and base_success)
            success_gains += int(core_success and not base_success)
            all_episode_step_deltas.append(
                float(core_row["steps_taken"]) - float(base_row["steps_taken"])
            )
            if not (core_success and base_success):
                continue
            core_cost = finite_float(core_row, "cost_to_target")
            base_cost = finite_float(base_row, "cost_to_target")
            core_actions = finite_float(core_row, "steps_to_target")
            base_actions = finite_float(base_row, "steps_to_target")
            assert core_cost is not None and base_cost is not None
            assert core_actions is not None and base_actions is not None
            cost_deltas.append(core_cost - base_cost)
            action_deltas.append(core_actions - base_actions)
        mean_cost_delta = float(np.mean(cost_deltas))
        mean_action_delta = float(np.mean(action_deltas))
        by_case[case_id] = {
            "paired_condition_count": len(keys),
            "success_loss_count": success_losses,
            "success_gain_count": success_gains,
            "both_success_count": len(cost_deltas),
            "mean_cost_delta_on_both_success": mean_cost_delta,
            "mean_actions_to_target_delta_on_both_success": mean_action_delta,
            "mean_steps_taken_delta_all_conditions": float(
                np.mean(all_episode_step_deltas)
            ),
            "cost_noninferior_without_success_loss": bool(
                success_losses == 0 and mean_cost_delta <= 1e-9
            ),
        }
    case_cost_effects = [
        float(by_case[case_id]["mean_cost_delta_on_both_success"])
        for case_id in case_ids
    ]
    case_action_effects = [
        float(by_case[case_id]["mean_actions_to_target_delta_on_both_success"])
        for case_id in case_ids
    ]
    return {
        "candidate": CORE,
        "baseline": baseline,
        "independent_case_count": len(case_ids),
        "within_case_paired_condition_count": len(candidate),
        "success_loss_count": sum(
            int(value["success_loss_count"]) for value in by_case.values()
        ),
        "success_gain_count": sum(
            int(value["success_gain_count"]) for value in by_case.values()
        ),
        "all_cases_pass_directional_pareto_gate": all(
            bool(value["cost_noninferior_without_success_loss"])
            for value in by_case.values()
        ),
        "case_mean_cost_delta_descriptives": descriptives(case_cost_effects),
        "case_mean_cost_delta_bootstrap": case_bootstrap(
            case_cost_effects,
            seed=bootstrap_seed,
            draws=bootstrap_draws,
        ),
        "case_mean_actions_delta_descriptives": descriptives(case_action_effects),
        "case_mean_actions_delta_bootstrap": case_bootstrap(
            case_action_effects,
            seed=bootstrap_seed + 1,
            draws=bootstrap_draws,
        ),
        "by_case": by_case,
    }


def method_descriptives(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    selected = [row for row in rows if row["planner"] == method]
    successes = [row for row in selected if int(row["reached_target"]) == 1]
    return {
        "condition_count": len(selected),
        "success_count": len(successes),
        "success_rate": len(successes) / len(selected),
        "mean_cost_to_target_on_success": float(
            np.mean([float(row["cost_to_target"]) for row in successes])
        ),
        "mean_actions_to_target_on_success": float(
            np.mean([float(row["steps_to_target"]) for row in successes])
        ),
        "mean_steps_taken_all_conditions": float(
            np.mean([float(row["steps_taken"]) for row in selected])
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy-results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-draws", type=int, default=100000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260719)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    rows = load_rows(args.policy_results)
    methods = sorted({str(row["planner"]) for row in rows})
    case_ids = sorted({str(row["case_id"]) for row in rows})
    if len(case_ids) != 6:
        raise ValueError(f"Expected six independent cases, found {case_ids}")
    counts = {
        method: sum(1 for row in rows if row["planner"] == method)
        for method in methods
    }
    if set(counts.values()) != {270}:
        raise ValueError(f"Expected 270 conditions per method, found {counts}")
    frozen_summary = json.loads(args.summary.read_text(encoding="utf-8"))
    output = {
        "analysis_id": "project05-m3star-sixcase-case-level-analysis-v0.1",
        "status": "development_analysis_not_final_blind_confirmation",
        "independent_statistical_unit": "case_id",
        "independent_unit_count": 6,
        "within_case_repeated_condition_count": 45,
        "total_paired_condition_count": 270,
        "pseudoreplication_control": (
            "bootstrap resamples six case-level effects; 270 repeated conditions "
            "are never treated as independent inferential units"
        ),
        "confirmatory_p_value_claim_allowed": False,
        "reason": "reused_method_development_cases_and_small_independent_n",
        "method_descriptives": {
            method: method_descriptives(rows, method)
            for method in (CORE, *BASELINES, "oracle_optimal")
        },
        "paired_case_level_effects": {
            baseline: paired_effects(
                rows,
                baseline,
                bootstrap_seed=args.bootstrap_seed + index * 10,
                bootstrap_draws=args.bootstrap_draws,
            )
            for index, baseline in enumerate(BASELINES)
        },
        "runner_strict_gate": frozen_summary["legacy_debug_gate"],
        "input_sha256": {
            "policy_results": sha256(args.policy_results),
            "summary": sha256(args.summary),
        },
        "analysis_script_sha256": sha256(Path(__file__)),
        "numpy_version": np.__version__,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if not args.quiet:
        print(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
