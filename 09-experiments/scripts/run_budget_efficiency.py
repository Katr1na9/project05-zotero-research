#!/usr/bin/env python3
"""Run frozen Oracle-relative budget curves on Project05 holdout cases."""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


MVP_PATH = Path(__file__).with_name("run_mvp.py")
MVP_SPEC = importlib.util.spec_from_file_location("run_mvp", MVP_PATH)
run_mvp = importlib.util.module_from_spec(MVP_SPEC)
assert MVP_SPEC.loader is not None
MVP_SPEC.loader.exec_module(run_mvp)


FROZEN_PLANNERS = [
    "coverage_greedy",
    "cmi_proxy",
    "project05_m1",
    "project05_m2",
    "project05_m3a_gap_compat",
    "oracle_optimal",
]
DEFAULT_CASE_PREFIXES = ("C07-", "C08-", "C09-")


def build_budget_schedule(
    oracle_min_cost: float | None,
    original_budget: float,
) -> list[float]:
    """Return C*, C*+1, C*+2, and the original budget, capped and deduplicated."""

    original = float(original_budget)
    if oracle_min_cost is None:
        return [original]
    tight = [
        min(float(oracle_min_cost) + offset, original)
        for offset in (0.0, 1.0, 2.0)
    ]
    return sorted(set(tight + [original]))


def compute_oracle_min_cost(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    mask_strategy: str,
    mask_intensity: float,
    seed: int,
) -> float | None:
    row, _ = run_mvp.run_episode(
        config,
        claims,
        actions,
        mask_strategy,
        mask_intensity,
        seed,
        "oracle_optimal",
    )
    if int(row["reached_target"]) != 1:
        return None
    return float(row["cost_to_target"])


def execute_budget_curves(
    case_dirs: list[Path],
    planners: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected_planners = planners or FROZEN_PLANNERS
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for case_dir in case_dirs:
        config = run_mvp.load_json(case_dir / "case_config.json")
        claims = run_mvp.load_json(case_dir / "evidence_claims.json")
        actions = run_mvp.load_json(case_dir / "acquisition_actions.json")
        original_budget = float(config["budget_total"])

        for mask_strategy, mask_intensity, seed in run_mvp.experiment_conditions(config):
            oracle_min = compute_oracle_min_cost(
                config,
                claims,
                actions,
                mask_strategy,
                mask_intensity,
                seed,
            )
            schedule = build_budget_schedule(oracle_min, original_budget)
            for budget in schedule:
                budget_config = deepcopy(config)
                budget_config["budget_total"] = budget
                budget_rows: list[dict[str, Any]] = []
                budget_traces: list[dict[str, Any]] = []
                for planner in selected_planners:
                    row, trace = run_mvp.run_episode(
                        budget_config,
                        claims,
                        actions,
                        mask_strategy,
                        mask_intensity,
                        seed,
                        planner,
                    )
                    row.update(
                        {
                            "evaluation_budget": budget,
                            "original_budget": original_budget,
                            "oracle_min_cost_frozen": (
                                "" if oracle_min is None else oracle_min
                            ),
                            "budget_offset": (
                                "" if oracle_min is None else budget - oracle_min
                            ),
                        }
                    )
                    budget_rows.append(row)
                    budget_traces.append(
                        {
                            "evaluation_run_id": (
                                f"{row['case_id']}|{mask_strategy}|"
                                f"{mask_intensity:.3f}|{seed}|b{budget:g}|{planner}"
                            ),
                            "result": row,
                            "trace": trace,
                        }
                    )
                rows.extend(run_mvp.add_oracle_relative_metrics(budget_rows))
                traces.extend(budget_traces)
    return rows, traces


def summarize_budget_curves(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, float], list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("budget_offset", "") == "":
            continue
        key = (str(row["planner"]), float(row["budget_offset"]))
        grouped.setdefault(key, []).append(row)

    curve_points = []
    for (planner, offset), group in sorted(grouped.items()):
        successes = [row for row in group if int(row["reached_target"]) == 1]
        successful_costs = [float(row["cost_to_target"]) for row in successes]
        curve_points.append(
            {
                "planner": planner,
                "budget_offset": offset,
                "condition_count": len(group),
                "independent_case_count": len(
                    {str(row["case_id"]) for row in group}
                ),
                "success_rate": round(len(successes) / len(group), 4),
                "mean_cost_to_target_on_success": (
                    round(sum(successful_costs) / len(successful_costs), 4)
                    if successful_costs
                    else None
                ),
                "mean_budget_used": round(
                    sum(float(row["budget_used"]) for row in group) / len(group),
                    4,
                ),
                "premature_stop_rate": round(
                    sum(int(row.get("premature_stop", 0)) for row in group)
                    / len(group),
                    4,
                ),
                "ceiling_violation_rate": round(
                    sum(int(row.get("ceiling_violation", 0)) for row in group)
                    / len(group),
                    4,
                ),
            }
        )

    return {
        "design": {
            "case_ids": sorted({str(row["case_id"]) for row in rows}),
            "independent_case_count": len(
                {str(row["case_id"]) for row in rows}
            ),
            "paired_condition_count": len(
                {
                    (
                        row["case_id"],
                        row["mask_strategy"],
                        row["mask_intensity"],
                        row["seed"],
                    )
                    for row in rows
                }
            ),
            "planners": sorted({str(row["planner"]) for row in rows}),
            "budget_rule": "min(C* + {0,1,2}, original), plus original; deduplicated",
            "oracle_role": "evaluation lower bound only",
            "m3a_tuning": "none; frozen weights from run_mvp.py",
        },
        "curve_points": curve_points,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen Oracle-relative budget-efficiency curves."
    )
    parser.add_argument("--cases-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    case_dirs = [
        path
        for path in run_mvp.discover_case_dirs(args.cases_root)
        if path.name.startswith(DEFAULT_CASE_PREFIXES)
    ]
    if not case_dirs:
        raise ValueError("No C07-C09 case directories found")
    rows, traces = execute_budget_curves(case_dirs)
    summary = summarize_budget_curves(rows)
    write_csv(args.output_dir / "budget_efficiency_results.csv", rows)
    write_json(args.output_dir / "budget_efficiency_traces.json.gz", traces)
    write_json(args.output_dir / "budget_efficiency_summary.json", summary)
    print(
        f"Wrote {len(rows)} runs across "
        f"{summary['design']['paired_condition_count']} paired conditions."
    )


if __name__ == "__main__":
    main()
