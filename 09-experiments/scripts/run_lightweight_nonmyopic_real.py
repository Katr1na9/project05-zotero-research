#!/usr/bin/env python3
"""Evaluate a public-information depth-2 planner on Project05 real cases.

The planner deliberately has no access to hidden or recoverable claim IDs. Its
second step is a public surrogate: an acquisition either produces one positive
feedback event and fills its declared coverage dimensions, or produces a
zero-yield feedback event. Both branches are weighted by the channel prior.
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MVP_PATH = Path(__file__).with_name("run_mvp.py")
PLANNER = "project05_depth2_public"
DISCOUNT = 0.8
FAILURE_COST_WEIGHT = 1.0
BASELINES = ("project05_m2", PLANNER, "oracle_optimal")


def _load_mvp() -> Any:
    spec = importlib.util.spec_from_file_location("project05_run_mvp", MVP_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load simulator from {MVP_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MVP = _load_mvp()


def channel_prior(config: dict[str, Any], action: dict[str, Any]) -> float:
    channel = MVP.acquisition_channel(action)
    reliability = config.get("channel_reliability", {}).get(channel, 1.0)
    return min(1.0, max(0.0, float(reliability)))


def public_surrogate_state(
    state: dict[str, Any],
    action: dict[str, Any],
    success: bool,
) -> dict[str, Any]:
    """Return a copied public-state surrogate after one hypothetical action."""

    updated = deepcopy(state)
    cost = float(action.get("cost", 0.0))
    budget = updated.setdefault("budget", {})
    budget["budget_used"] = float(budget.get("budget_used", 0.0)) + cost
    budget["budget_remaining"] = max(
        0.0,
        float(budget.get("budget_remaining", 0.0)) - cost,
    )
    updated.setdefault("actions_taken", []).append(action["action_id"])
    updated.setdefault("action_feedback", []).append(
        {
            "action_id": action["action_id"],
            "action_type": action.get("action_type", ""),
            "recovered_count": int(success),
        }
    )

    if success:
        coverage = updated.setdefault("coverage", {})
        stage_coverage = coverage.setdefault("stage_coverage", {})
        evidence_coverage = coverage.setdefault("evidence_type_coverage", {})
        for stage in action.get("expected_stages", []):
            stage_coverage[stage] = 1.0
        for evidence_type in action.get("expected_evidence_types", []):
            evidence_coverage[evidence_type] = 1.0

        intended = set(action.get("intended_cti_node_ids", []))
        unmatched = updated.get("unmatched_cti_node_ids")
        if isinstance(unmatched, list):
            updated["unmatched_cti_node_ids"] = [
                node_id for node_id in unmatched if node_id not in intended
            ]
    return updated


def best_second_step_value(
    state: dict[str, Any],
    actions: list[dict[str, Any]],
) -> float:
    candidates = MVP.available_actions(
        actions,
        state.get("actions_taken", []),
        float(state.get("budget", {}).get("budget_remaining", 0.0)),
    )
    return max(
        (MVP.m2_action_score(action, state, actions) for action in candidates),
        default=0.0,
    )


def public_depth2_score(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    action: dict[str, Any],
) -> float:
    if MVP.is_stop_action(action):
        return 0.0

    immediate = MVP.m2_action_score(action, state, actions)
    reliability = channel_prior(config, action)
    success_state = public_surrogate_state(state, action, success=True)
    zero_yield_state = public_surrogate_state(state, action, success=False)
    future = (
        reliability * best_second_step_value(success_state, actions)
        + (1.0 - reliability) * best_second_step_value(zero_yield_state, actions)
    )
    failure_cost = (1.0 - reliability) * float(action.get("cost", 0.0))
    return immediate + DISCOUNT * future - FAILURE_COST_WEIGHT * failure_cost


def select_depth2_public(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Select using only action declarations, public state, and channel priors."""

    candidates = MVP.available_actions(
        actions,
        state.get("actions_taken", []),
        float(state.get("budget", {}).get("budget_remaining", 0.0)),
    )
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda action: (
            public_depth2_score(config, state, actions, action),
            int(MVP.is_stop_action(action)),
            -float(action.get("cost", 0.0)),
            str(action.get("action_id", "")),
        ),
    )


def execute_cases(case_dirs: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        config = MVP.load_json(case_dir / "case_config.json")
        claims = MVP.load_json(case_dir / "evidence_claims.json")
        actions = MVP.load_json(case_dir / "acquisition_actions.json")
        for strategy, intensity, seed in MVP.experiment_conditions(config):
            for planner in BASELINES:
                selector = select_depth2_public if planner == PLANNER else None
                result, trace = MVP.run_episode(
                    config,
                    claims,
                    actions,
                    strategy,
                    intensity,
                    seed,
                    planner,
                    action_selector=selector,
                )
                rows.append(result)
                traces.append(
                    {
                        "run_id": MVP.make_run_id(
                            config["case_id"], strategy, intensity, seed, planner
                        ),
                        "result": result,
                        "trace": trace,
                    }
                )
    return MVP.add_oracle_relative_metrics(rows), traces


def paired_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    key_fields = ("case_id", "mask_strategy", "mask_intensity", "seed")
    paired: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        paired.setdefault(key, {})[row["planner"]] = row

    wins = ties = losses = both_success = repairs = regressions = 0
    cost_differences: list[float] = []
    by_case: dict[str, list[float]] = {}
    for key, planners in paired.items():
        m2 = planners.get("project05_m2")
        depth2 = planners.get(PLANNER)
        if m2 is None or depth2 is None:
            continue
        m2_success = int(m2["reached_target"])
        depth2_success = int(depth2["reached_target"])
        repairs += int(depth2_success == 1 and m2_success == 0)
        regressions += int(depth2_success == 0 and m2_success == 1)
        if not (m2_success and depth2_success):
            continue
        both_success += 1
        difference = float(depth2["cost_to_target"]) - float(m2["cost_to_target"])
        cost_differences.append(difference)
        by_case.setdefault(str(key[0]), []).append(difference)
        wins += int(difference < 0)
        ties += int(difference == 0)
        losses += int(difference > 0)

    return {
        "paired_condition_count": len(paired),
        "both_success_count": both_success,
        "depth2_success_repairs": repairs,
        "depth2_success_regressions": regressions,
        "depth2_cost_wins": wins,
        "cost_ties": ties,
        "depth2_cost_losses": losses,
        "mean_cost_difference_depth2_minus_m2": (
            round(sum(cost_differences) / len(cost_differences), 4)
            if cost_differences
            else None
        ),
        "by_case_mean_cost_difference": {
            case_id: round(sum(values) / len(values), 4)
            for case_id, values in sorted(by_case.items())
        },
    }


def write_traces(path: Path, traces: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(traces, ensure_ascii=False).encode("utf-8")
    path.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))


def resolve_case_dirs(cases_root: Path) -> list[Path]:
    resolved: list[Path] = []
    for case_id in ("C07", "C08", "C09", "C10"):
        matches = sorted(
            path
            for path in cases_root.glob(f"{case_id}*")
            if path.is_dir()
            and all((path / filename).is_file() for filename in MVP.CASE_FILENAMES)
        )
        if len(matches) != 1:
            raise FileNotFoundError(
                f"Expected one complete {case_id} directory under {cases_root}, "
                f"found {matches}"
            )
        resolved.append(matches[0])
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen public depth-2 planner on C07-C10."
    )
    parser.add_argument(
        "--cases-root",
        type=Path,
        default=ROOT / "09-experiments" / "real_cases",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "09-experiments" / "results" / "nonmyopic_real_v0.1",
    )
    args = parser.parse_args()

    case_dirs = resolve_case_dirs(args.cases_root)

    rows, traces = execute_cases(case_dirs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    MVP.write_csv(args.output_dir / "nonmyopic_policy_results.csv", rows)
    MVP.write_json(
        args.output_dir / "nonmyopic_policy_summary.json",
        MVP.summarize_stratified(rows),
    )
    MVP.write_json(
        args.output_dir / "nonmyopic_paired_summary.json",
        paired_summary(rows),
    )
    write_traces(args.output_dir / "nonmyopic_policy_traces.json.gz", traces)
    print(f"Wrote frozen evaluation to {args.output_dir}")


if __name__ == "__main__":
    main()
