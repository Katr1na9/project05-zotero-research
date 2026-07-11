#!/usr/bin/env python3
"""Run the frozen two-level non-myopic and DQN necessity gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import statistics
import time
from functools import lru_cache
from itertools import product
from pathlib import Path
from typing import Any, Iterable, NamedTuple


MVP_PATH = Path(__file__).with_name("run_mvp.py")
MVP_SPEC = importlib.util.spec_from_file_location("run_mvp_nonmyopic", MVP_PATH)
run_mvp = importlib.util.module_from_spec(MVP_SPEC)
assert MVP_SPEC.loader is not None
MVP_SPEC.loader.exec_module(run_mvp)


PLANNERS = (
    "one_step_gain_cost",
    "project05_m2",
    "depth2_m2",
    "dp_oracle",
)
UNLOCK_DEPTHS = (1, 2, 3, 4)
BUDGET_SLACKS = (0, 1)
DISTRACTOR_COUNTS = (1, 3, 6, 10)
DISTRACTOR_GAINS = (0.5, 1.0, 2.0)
CHAIN_RELIABILITIES = (1.0, 0.8)
FROZEN_SEEDS = (11, 23, 37, 41, 53, 67, 79, 83, 97, 101)
TARGET_REWARD = 10.0
COST_PENALTY = 0.1


class Scenario(NamedTuple):
    scenario_id: str
    unlock_depth: int
    budget_slack: int
    distractor_count: int
    distractor_gain: float
    chain_reliability: float

    @property
    def budget_total(self) -> int:
        return self.unlock_depth + 1 + self.budget_slack


class State(NamedTuple):
    budget_remaining: int
    chain_index: int = 0
    target_reached: bool = False
    chain_blocked: bool = False
    taken: frozenset[str] = frozenset()
    feedback: tuple[tuple[str, int], ...] = ()
    local_gain: float = 0.0


def scenario_grid() -> list[Scenario]:
    scenarios: list[Scenario] = []
    for depth, slack, count, gain, reliability in product(
        UNLOCK_DEPTHS,
        BUDGET_SLACKS,
        DISTRACTOR_COUNTS,
        DISTRACTOR_GAINS,
        CHAIN_RELIABILITIES,
    ):
        scenario_id = (
            f"NM-d{depth}-s{slack}-n{count:02d}-"
            f"g{int(gain * 100):03d}-r{int(reliability * 100):03d}"
        )
        scenarios.append(
            Scenario(
                scenario_id=scenario_id,
                unlock_depth=depth,
                budget_slack=slack,
                distractor_count=count,
                distractor_gain=gain,
                chain_reliability=reliability,
            )
        )
    return scenarios


def expected_effects(
    granularity: float = 0.0,
    uncertainty: float = 0.0,
    risk: float = 0.0,
    coverage: float = 0.0,
) -> dict[str, float]:
    return {
        "expected_granularity_gain": granularity,
        "expected_uncertainty_reduction": uncertainty,
        "expected_over_attribution_risk_reduction": risk,
        "expected_conflict_resolution": 0.0,
        "expected_coverage_delta": coverage,
    }


def action_catalog(scenario: Scenario) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    distractor_uncertainty = min(1.0, 0.4 + 0.2 * scenario.distractor_gain)
    for index in range(1, scenario.distractor_count + 1):
        actions.append(
            {
                "action_id": f"DISTRACTOR_{index:02d}",
                "action_type": "local_context_review",
                "kind": "distractor",
                "index": index,
                "cost": 1,
                "immediate_gain": scenario.distractor_gain,
                "success_probability": 1.0,
                "target": {
                    "target_type": "local_context",
                    "target_value": f"supporting-clue-{index:02d}",
                },
                "expected_stages": ["local_context"],
                "expected_evidence_types": ["supporting_context"],
                "expected_effects": expected_effects(
                    uncertainty=distractor_uncertainty,
                    risk=0.2,
                    coverage=0.25,
                ),
            }
        )
    for index in range(1, scenario.unlock_depth + 1):
        actions.append(
            {
                "action_id": f"SETUP_{index:02d}",
                "action_type": "unlock_prerequisite",
                "kind": "setup",
                "index": index,
                "cost": 1,
                "immediate_gain": 0.0,
                "success_probability": scenario.chain_reliability,
                "target": {
                    "target_type": "critical_path",
                    "target_value": f"unlock-step-{index:02d}",
                },
                "expected_stages": ["critical_path"],
                "expected_evidence_types": ["host_forensics"],
                "expected_effects": expected_effects(),
            }
        )
    actions.append(
        {
            "action_id": "PAYOFF",
            "action_type": "resolve_critical_gap",
            "kind": "payoff",
            "index": scenario.unlock_depth + 1,
            "cost": 1,
            "immediate_gain": 0.0,
            "success_probability": scenario.chain_reliability,
            "target": {
                "target_type": "critical_gap",
                "target_value": "target-granularity",
            },
            "expected_stages": ["critical_path"],
            "expected_evidence_types": ["host_forensics"],
            "expected_effects": expected_effects(
                granularity=1.0,
                uncertainty=1.0,
                risk=1.0,
                coverage=1.0,
            ),
        }
    )
    stop = run_mvp.make_stop_action(scenario.scenario_id)
    stop.update({"kind": "stop", "index": 0, "immediate_gain": 0.0})
    actions.append(stop)
    return actions


def initial_state(scenario: Scenario) -> State:
    return State(budget_remaining=scenario.budget_total)


def available_actions(
    scenario: Scenario,
    state: State,
    catalog: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    available: list[dict[str, Any]] = []
    for action in catalog:
        action_id = str(action["action_id"])
        kind = str(action["kind"])
        if kind == "stop":
            available.append(action)
            continue
        if action_id in state.taken or int(action["cost"]) > state.budget_remaining:
            continue
        if kind == "distractor":
            available.append(action)
        elif kind == "setup":
            if not state.chain_blocked and int(action["index"]) == state.chain_index + 1:
                available.append(action)
        elif kind == "payoff":
            if not state.chain_blocked and state.chain_index == scenario.unlock_depth:
                available.append(action)
    return available


def apply_outcome(
    scenario: Scenario,
    state: State,
    action: dict[str, Any],
    success: bool,
) -> State:
    kind = str(action["kind"])
    if kind == "stop":
        return state
    action_id = str(action["action_id"])
    cost = int(action["cost"])
    taken = state.taken | {action_id}
    action_type = str(action["action_type"])

    if kind == "distractor":
        return State(
            budget_remaining=state.budget_remaining - cost,
            chain_index=state.chain_index,
            target_reached=state.target_reached,
            chain_blocked=state.chain_blocked,
            taken=taken,
            feedback=state.feedback + ((action_type, 1),),
            local_gain=state.local_gain + float(action["immediate_gain"]),
        )

    if kind == "setup":
        return State(
            budget_remaining=state.budget_remaining - cost,
            chain_index=state.chain_index + int(success),
            target_reached=False,
            chain_blocked=not success,
            taken=taken,
            feedback=state.feedback + ((action_type, int(success)),),
            local_gain=state.local_gain,
        )

    if kind == "payoff":
        return State(
            budget_remaining=state.budget_remaining - cost,
            chain_index=state.chain_index,
            target_reached=bool(success),
            chain_blocked=not success,
            taken=taken,
            feedback=state.feedback + ((action_type, int(success)),),
            local_gain=state.local_gain,
        )
    raise ValueError(f"unknown action kind: {kind}")


def outcome_branches(
    scenario: Scenario,
    state: State,
    action: dict[str, Any],
) -> list[tuple[float, State]]:
    if action["kind"] == "stop":
        return [(1.0, state)]
    probability = float(action.get("success_probability", 1.0))
    if probability >= 1.0:
        return [(1.0, apply_outcome(scenario, state, action, True))]
    if probability <= 0.0:
        return [(1.0, apply_outcome(scenario, state, action, False))]
    return [
        (probability, apply_outcome(scenario, state, action, True)),
        (1.0 - probability, apply_outcome(scenario, state, action, False)),
    ]


def hash_draw(scenario_id: str, seed: int, action_id: str) -> float:
    payload = f"{scenario_id}|{seed}|{action_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)


def realized_success(scenario: Scenario, seed: int, action: dict[str, Any]) -> bool:
    probability = float(action.get("success_probability", 1.0))
    return hash_draw(scenario.scenario_id, seed, str(action["action_id"])) < probability


def m2_public_state(scenario: Scenario, state: State) -> dict[str, Any]:
    used_distractor = any(action_id.startswith("DISTRACTOR_") for action_id in state.taken)
    chain_fraction = state.chain_index / max(1, scenario.unlock_depth)
    return {
        "coverage": {
            "stage_coverage": {
                "local_context": float(used_distractor),
                "critical_path": chain_fraction,
            },
            "evidence_type_coverage": {
                "supporting_context": float(used_distractor),
                "host_forensics": chain_fraction,
            },
        },
        "budget": {"budget_remaining": state.budget_remaining},
        "actions_taken": list(state.taken),
        "action_feedback": [
            {"action_type": action_type, "recovered_count": recovered_count}
            for action_type, recovered_count in state.feedback
        ],
    }


def select_m2(
    scenario: Scenario,
    state: State,
    catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    candidates = available_actions(scenario, state, catalog)
    public_state = m2_public_state(scenario, state)
    return min(
        candidates,
        key=lambda action: (
            -run_mvp.m2_action_score(action, public_state, catalog),
            -int(run_mvp.is_stop_action(action)),
            action["cost"],
            -len(action.get("expected_stages", [])),
            action["action_id"],
        ),
    )


def one_step_value(action: dict[str, Any]) -> float:
    kind = str(action["kind"])
    cost = float(action["cost"])
    if kind == "stop":
        return 0.0
    if kind == "payoff":
        return float(action["success_probability"]) * TARGET_REWARD - COST_PENALTY * cost
    return float(action["immediate_gain"]) - COST_PENALTY * cost


def select_one_step(
    scenario: Scenario,
    state: State,
    catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    return max(
        available_actions(scenario, state, catalog),
        key=lambda action: (
            one_step_value(action),
            int(action["kind"] == "stop"),
            -float(action["cost"]),
            str(action["action_id"]),
        ),
    )


def bounded_reach_value(
    scenario: Scenario,
    state: State,
    catalog: list[dict[str, Any]],
    horizon: int,
) -> tuple[float, float, int]:
    expanded = 0

    @lru_cache(maxsize=None)
    def value(current: State, remaining_horizon: int) -> tuple[float, float]:
        nonlocal expanded
        expanded += 1
        if current.target_reached:
            return 1.0, 0.0
        if remaining_horizon <= 0:
            return 0.0, 0.0
        best = (0.0, 0.0)
        for action in available_actions(scenario, current, catalog):
            if action["kind"] == "stop":
                candidate = (0.0, 0.0)
            else:
                probability = 0.0
                tail_cost = 0.0
                for branch_probability, next_state in outcome_branches(
                    scenario, current, action
                ):
                    branch_reach, branch_cost = value(
                        next_state, remaining_horizon - 1
                    )
                    probability += branch_probability * branch_reach
                    tail_cost += branch_probability * branch_cost
                candidate = (probability, float(action["cost"]) + tail_cost)
            if (candidate[0], -candidate[1]) > (best[0], -best[1]):
                best = candidate
        return best

    reach, cost = value(state, horizon)
    return reach, cost, expanded


def select_depth2(
    scenario: Scenario,
    state: State,
    catalog: list[dict[str, Any]],
) -> tuple[dict[str, Any], int]:
    candidates = available_actions(scenario, state, catalog)
    ranked: list[tuple[float, float, str, dict[str, Any], int]] = []
    for action in candidates:
        if action["kind"] == "stop":
            ranked.append((0.0, 0.0, str(action["action_id"]), action, 0))
            continue
        probability = 0.0
        expected_cost = float(action["cost"])
        expanded = 0
        for branch_probability, next_state in outcome_branches(scenario, state, action):
            branch_reach, branch_cost, branch_expanded = bounded_reach_value(
                scenario,
                next_state,
                catalog,
                horizon=1,
            )
            probability += branch_probability * branch_reach
            expected_cost += branch_probability * branch_cost
            expanded += branch_expanded
        ranked.append(
            (probability, -expected_cost, str(action["action_id"]), action, expanded)
        )
    best = max(ranked, key=lambda item: (item[0], item[1], item[2]))
    if best[0] > 0.0:
        return best[3], sum(item[4] for item in ranked)
    return select_m2(scenario, state, catalog), sum(item[4] for item in ranked)


class DPPolicy:
    def __init__(self, scenario: Scenario, catalog: list[dict[str, Any]]):
        self.scenario = scenario
        self.catalog = catalog
        self.expanded_states = 0

    @lru_cache(maxsize=None)
    def value(self, state: State) -> tuple[float, float]:
        self.expanded_states += 1
        if state.target_reached:
            return 1.0, 0.0
        best_probability = 0.0
        best_cost = 0.0
        for action in available_actions(self.scenario, state, self.catalog):
            if action["kind"] == "stop":
                probability, expected_cost = 0.0, 0.0
            else:
                probability = 0.0
                tail_cost = 0.0
                for branch_probability, next_state in outcome_branches(
                    self.scenario, state, action
                ):
                    branch_reach, branch_cost = self.value(next_state)
                    probability += branch_probability * branch_reach
                    tail_cost += branch_probability * branch_cost
                expected_cost = float(action["cost"]) + tail_cost
            if (probability, -expected_cost) > (
                best_probability,
                -best_cost,
            ):
                best_probability = probability
                best_cost = expected_cost
        return best_probability, best_cost

    def select(self, state: State) -> dict[str, Any]:
        ranked: list[tuple[float, float, str, dict[str, Any]]] = []
        for action in available_actions(self.scenario, state, self.catalog):
            if action["kind"] == "stop":
                probability, expected_cost = 0.0, 0.0
            else:
                probability = 0.0
                tail_cost = 0.0
                for branch_probability, next_state in outcome_branches(
                    self.scenario, state, action
                ):
                    branch_reach, branch_cost = self.value(next_state)
                    probability += branch_probability * branch_reach
                    tail_cost += branch_probability * branch_cost
                expected_cost = float(action["cost"]) + tail_cost
            ranked.append(
                (
                    probability,
                    -expected_cost,
                    str(action["action_id"]),
                    action,
                )
            )
        return max(ranked, key=lambda item: (item[0], item[1], item[2]))[3]


def benchmark_dp(scenario: Scenario) -> dict[str, Any]:
    catalog = action_catalog(scenario)
    policy = DPPolicy(scenario, catalog)
    state = initial_state(scenario)
    started = time.perf_counter()
    action = policy.select(state)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    probability, expected_cost = policy.value(state)
    return {
        "scenario_id": scenario.scenario_id,
        "initial_action": action["action_id"],
        "success_probability": probability,
        "expected_cost": expected_cost,
        "elapsed_ms": elapsed_ms,
        "expanded_states": policy.expanded_states,
    }


def run_episode(
    scenario: Scenario,
    seed: int,
    planner: str,
    catalog: list[dict[str, Any]] | None = None,
    dp_policy: DPPolicy | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actions = catalog or action_catalog(scenario)
    oracle = dp_policy or DPPolicy(scenario, actions)
    state = initial_state(scenario)
    initial_budget = state.budget_remaining
    trace: list[dict[str, Any]] = []
    action_ids: list[str] = []
    explicit_stop = False
    premature_stop = False
    depth2_expanded = 0
    failed_chain_actions = 0

    while not state.target_reached:
        if planner == "one_step_gain_cost":
            action = select_one_step(scenario, state, actions)
        elif planner == "project05_m2":
            action = select_m2(scenario, state, actions)
        elif planner == "depth2_m2":
            action, expanded = select_depth2(scenario, state, actions)
            depth2_expanded += expanded
        elif planner == "dp_oracle":
            action = oracle.select(state)
        else:
            raise ValueError(f"unsupported planner: {planner}")

        if action["kind"] == "stop":
            explicit_stop = True
            premature_stop = oracle.value(state)[0] > 0.0
            trace.append(
                {
                    "state": state_to_dict(state),
                    "action_id": action["action_id"],
                    "outcome": "stop",
                }
            )
            break

        success = realized_success(scenario, seed, action)
        next_state = apply_outcome(scenario, state, action, success)
        if action["kind"] in {"setup", "payoff"} and not success:
            failed_chain_actions += 1
        action_ids.append(str(action["action_id"]))
        trace.append(
            {
                "state": state_to_dict(state),
                "action_id": action["action_id"],
                "outcome": "success" if success else "failure",
                "next_state": state_to_dict(next_state),
            }
        )
        state = next_state

    budget_used = initial_budget - state.budget_remaining
    result = {
        "scenario_id": scenario.scenario_id,
        "unlock_depth": scenario.unlock_depth,
        "budget_slack": scenario.budget_slack,
        "distractor_count": scenario.distractor_count,
        "distractor_gain": scenario.distractor_gain,
        "chain_reliability": scenario.chain_reliability,
        "seed": seed,
        "planner": planner,
        "reached_target": int(state.target_reached),
        "cost_to_target": budget_used if state.target_reached else "",
        "budget_used": budget_used,
        "steps": len(action_ids),
        "local_gain": state.local_gain,
        "actions_taken": "|".join(action_ids),
        "first_action": action_ids[0] if action_ids else "STOP",
        "explicit_stop": int(explicit_stop),
        "premature_stop": int(premature_stop),
        "failed_chain_actions": failed_chain_actions,
        "depth2_expanded_states": depth2_expanded,
    }
    return result, trace


def state_to_dict(state: State) -> dict[str, Any]:
    return {
        "budget_remaining": state.budget_remaining,
        "chain_index": state.chain_index,
        "target_reached": state.target_reached,
        "chain_blocked": state.chain_blocked,
        "taken": sorted(state.taken),
        "local_gain": state.local_gain,
    }


def mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def percentile(values: Iterable[float], quantile: float) -> float:
    items = sorted(values)
    if not items:
        return 0.0
    position = (len(items) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(items) - 1)
    fraction = position - lower
    return items[lower] * (1.0 - fraction) + items[upper] * fraction


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "episodes": 0,
            "independent_scenarios": 0,
            "success_rate": 0.0,
            "mean_cost_on_success": None,
            "mean_budget_used": 0.0,
            "premature_stop_rate": 0.0,
            "mean_local_gain": 0.0,
        }
    successes = [row for row in rows if int(row["reached_target"]) == 1]
    return {
        "episodes": len(rows),
        "independent_scenarios": len({row["scenario_id"] for row in rows}),
        "success_rate": round(len(successes) / len(rows), 4),
        "mean_cost_on_success": (
            round(mean(float(row["cost_to_target"]) for row in successes), 4)
            if successes
            else None
        ),
        "mean_budget_used": round(mean(float(row["budget_used"]) for row in rows), 4),
        "premature_stop_rate": round(
            mean(float(row["premature_stop"]) for row in rows), 4
        ),
        "mean_local_gain": round(mean(float(row["local_gain"]) for row in rows), 4),
    }


def scenario_planner_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["scenario_id"], row["planner"]), []).append(row)
    output: list[dict[str, Any]] = []
    for (scenario_id, planner), group in sorted(grouped.items()):
        first = group[0]
        summary = summarize_group(group)
        output.append(
            {
                "scenario_id": scenario_id,
                "planner": planner,
                "unlock_depth": first["unlock_depth"],
                "budget_slack": first["budget_slack"],
                "distractor_count": first["distractor_count"],
                "distractor_gain": first["distractor_gain"],
                "chain_reliability": first["chain_reliability"],
                **summary,
            }
        )
    return output


def gate_summary(
    episode_rows: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    benchmarks: list[dict[str, Any]],
) -> dict[str, Any]:
    overall = {
        planner: summarize_group(
            [row for row in episode_rows if row["planner"] == planner]
        )
        for planner in PLANNERS
    }
    by_depth = {
        str(depth): {
            planner: summarize_group(
                [
                    row
                    for row in episode_rows
                    if row["planner"] == planner and row["unlock_depth"] == depth
                ]
            )
            for planner in PLANNERS
        }
        for depth in UNLOCK_DEPTHS
    }

    scenario_index = {
        (row["scenario_id"], row["planner"]): row for row in scenario_rows
    }
    reachable_ids = {
        row["scenario_id"] for row in benchmarks if row["success_probability"] > 0
    }
    dp_minus_m2 = mean(
        scenario_index[(scenario_id, "dp_oracle")]["success_rate"]
        - scenario_index[(scenario_id, "project05_m2")]["success_rate"]
        for scenario_id in reachable_ids
    )
    depth1_ids = {
        row["scenario_id"]
        for row in scenario_rows
        if row["unlock_depth"] == 1
    }
    depth2_repair_d1 = mean(
        scenario_index[(scenario_id, "depth2_m2")]["success_rate"]
        - scenario_index[(scenario_id, "project05_m2")]["success_rate"]
        for scenario_id in depth1_ids
    )
    conflict_ids = {
        scenario_id
        for scenario_id in reachable_ids
        if scenario_index[(scenario_id, "dp_oracle")]["success_rate"]
        - scenario_index[(scenario_id, "project05_m2")]["success_rate"]
        >= 0.1
    }
    conflict_rows = [
        row
        for row in scenario_rows
        if row["scenario_id"] in conflict_ids and row["planner"] == "dp_oracle"
    ]
    conflict_counts = {row["distractor_count"] for row in conflict_rows}
    conflict_gains = {row["distractor_gain"] for row in conflict_rows}
    gate_a_checks = {
        "reachable_scenarios_at_least_24": len(reachable_ids) >= 24,
        "dp_minus_m2_success_at_least_0_20": dp_minus_m2 >= 0.20,
        "depth2_repairs_depth1": depth2_repair_d1 > 0.0,
        "conflicts_cover_two_counts_and_gains": (
            len(conflict_counts) >= 2 and len(conflict_gains) >= 2
        ),
    }

    dp_minus_depth2 = overall["dp_oracle"]["success_rate"] - overall[
        "depth2_m2"
    ]["success_rate"]
    depth_gaps = {
        depth: by_depth[str(depth)]["dp_oracle"]["success_rate"]
        - by_depth[str(depth)]["depth2_m2"]["success_rate"]
        for depth in UNLOCK_DEPTHS
    }
    depths_with_gap = [depth for depth, gap in depth_gaps.items() if gap >= 0.10]
    p95_ms = percentile((row["elapsed_ms"] for row in benchmarks), 0.95)
    max_expanded = max(row["expanded_states"] for row in benchmarks)
    gate_b_checks = {
        "dp_minus_depth2_success_at_least_0_10": dp_minus_depth2 >= 0.10,
        "dp_complexity_exceeds_threshold": p95_ms > 100.0 or max_expanded > 100000,
        "gap_covers_two_depths": len(depths_with_gap) >= 2,
    }

    return {
        "design": {
            "independent_scenario_count": len(
                {row["scenario_id"] for row in episode_rows}
            ),
            "seed_count": len({row["seed"] for row in episode_rows}),
            "episode_count": len(episode_rows),
            "planners": list(PLANNERS),
            "grid": {
                "unlock_depth": list(UNLOCK_DEPTHS),
                "budget_slack": list(BUDGET_SLACKS),
                "distractor_count": list(DISTRACTOR_COUNTS),
                "distractor_gain": list(DISTRACTOR_GAINS),
                "chain_reliability": list(CHAIN_RELIABILITIES),
                "seeds": list(FROZEN_SEEDS),
            },
        },
        "overall_by_planner": overall,
        "by_depth_planner": by_depth,
        "gate_a_nonmyopic_necessity": {
            "passed": all(gate_a_checks.values()),
            "checks": gate_a_checks,
            "reachable_scenario_count": len(reachable_ids),
            "conflict_scenario_count": len(conflict_ids),
            "mean_success_advantage_dp_vs_m2": round(dp_minus_m2, 4),
            "mean_depth2_repair_at_depth1": round(depth2_repair_d1, 4),
            "conflict_distractor_counts": sorted(conflict_counts),
            "conflict_distractor_gains": sorted(conflict_gains),
        },
        "gate_b_dqn_necessity": {
            "passed": all(gate_b_checks.values()),
            "checks": gate_b_checks,
            "success_advantage_dp_vs_depth2": round(dp_minus_depth2, 4),
            "depth_success_gaps": {
                str(depth): round(gap, 4) for depth, gap in depth_gaps.items()
            },
            "depths_with_gap_at_least_0_10": depths_with_gap,
            "dp_cold_start_p95_ms": round(p95_ms, 4),
            "dp_cold_start_median_ms": round(
                statistics.median(row["elapsed_ms"] for row in benchmarks), 4
            ),
            "dp_max_expanded_states": max_expanded,
        },
        "decision": (
            "approve_dqn"
            if all(gate_a_checks.values()) and all(gate_b_checks.values())
            else (
                "use_lightweight_nonmyopic_planning_no_dqn"
                if all(gate_a_checks.values())
                else "close_nonmyopic_rl_branch"
            )
        ),
    }


def representative_scenario(
    scenarios: list[Scenario], depth: int
) -> Scenario:
    return next(
        scenario
        for scenario in scenarios
        if scenario.unlock_depth == depth
        and scenario.budget_slack == 0
        and scenario.distractor_count == 3
        and scenario.distractor_gain == 1.0
        and scenario.chain_reliability == 1.0
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def run_experiment(
    output_dir: Path,
    scenarios: list[Scenario] | None = None,
    seeds: tuple[int, ...] = FROZEN_SEEDS,
) -> dict[str, Any]:
    selected = scenarios or scenario_grid()
    episode_rows: list[dict[str, Any]] = []
    benchmarks: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    representative_ids = {
        representative_scenario(selected, depth).scenario_id
        for depth in (1, 3)
        if any(scenario.unlock_depth == depth for scenario in selected)
    } if scenarios is None else set()

    for scenario in selected:
        catalog = action_catalog(scenario)
        benchmarks.append(benchmark_dp(scenario))
        shared_dp_policy = DPPolicy(scenario, catalog)
        for seed in seeds:
            for planner in PLANNERS:
                row, trace = run_episode(
                    scenario,
                    seed,
                    planner,
                    catalog=catalog,
                    dp_policy=shared_dp_policy,
                )
                episode_rows.append(row)
                if scenario.scenario_id in representative_ids and seed == seeds[0]:
                    traces.append(
                        {
                            "scenario_id": scenario.scenario_id,
                            "seed": seed,
                            "planner": planner,
                            "result": row,
                            "trace": trace,
                        }
                    )

    scenario_rows = scenario_planner_summary(episode_rows)
    summary = gate_summary(episode_rows, scenario_rows, benchmarks)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "nonmyopic_gate_episodes.csv", episode_rows)
    write_csv(output_dir / "nonmyopic_gate_scenario_summary.csv", scenario_rows)
    write_csv(output_dir / "nonmyopic_gate_dp_benchmarks.csv", benchmarks)
    write_json(output_dir / "nonmyopic_gate_representative_traces.json", traces)
    write_json(output_dir / "nonmyopic_gate_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen Project05 non-myopic and DQN necessity gate."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = run_experiment(args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
