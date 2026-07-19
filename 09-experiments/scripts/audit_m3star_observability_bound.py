#!/usr/bin/env python3
"""Lower-bound deterministic public-policy regret under hidden-state aliasing."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_script(name: str) -> Any:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


regret_audit = load_script("audit_m3star_oracle_regret")
run_m3star = regret_audit.run_m3star
run_mvp = regret_audit.run_mvp


def observation_snapshot(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    decision: dict[str, Any],
) -> dict[str, Any]:
    episode_actions = run_mvp.ensure_stop_action(config, actions)
    state = run_mvp.build_state(
        config,
        claims,
        episode_actions,
        "observability-bound",
        int(decision["state_depth"]),
        decision["mask_strategy"],
        decision["mask_intensity"],
        int(decision["seed"]),
        set(decision["visible_ids"]),
        set(decision["hidden_ids"]),
        set(decision["recovered_ids"]),
        list(decision["actions_taken"]),
        float(decision["budget_used"]),
        list(decision["action_feedback"]),
    )
    return run_m3star.public_graph_snapshot(
        config,
        run_mvp.planner_state_view(state),
        run_mvp.planner_action_views(episode_actions),
    )


def observation_sha256(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def minimax_first_action_regret(
    oracle_costs: list[float],
    costs_via_action: dict[str, list[float]],
    tolerance: float = 1e-9,
) -> dict[str, Any]:
    """Best public first action under worst hidden state and Oracle tails.

    Each via-action cost already includes the first action.  Allowing a
    clairvoyant optimal tail after it makes this an optimistic lower bound for
    every implementable deterministic public policy.
    """

    if not oracle_costs or any(not math.isfinite(value) for value in oracle_costs):
        raise ValueError("Every aliased state must be Oracle-reachable")
    worst_by_action: dict[str, float] = {}
    for action_id, costs in costs_via_action.items():
        if len(costs) != len(oracle_costs):
            raise ValueError(f"Incomplete via-action vector for {action_id}")
        regrets = [
            via - oracle
            for oracle, via in zip(oracle_costs, costs)
        ]
        if any(not math.isfinite(value) for value in regrets):
            worst_by_action[action_id] = math.inf
            continue
        if any(value < -tolerance for value in regrets):
            raise ValueError(f"Oracle cost violation through {action_id}")
        worst_by_action[action_id] = max(0.0, max(regrets))
    finite = {
        action_id: value
        for action_id, value in worst_by_action.items()
        if math.isfinite(value)
    }
    if not finite:
        return {
            "lower_bound": math.inf,
            "minimax_action_ids": [],
            "worst_regret_by_action": worst_by_action,
        }
    lower_bound = min(finite.values())
    return {
        "lower_bound": lower_bound,
        "minimax_action_ids": sorted(
            action_id
            for action_id, value in finite.items()
            if math.isclose(value, lower_bound, rel_tol=0.0, abs_tol=tolerance)
        ),
        "worst_regret_by_action": worst_by_action,
    }


def load_regret_rows(path: Path) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            state_id = str(row["state_id"])
            if state_id in indexed:
                raise ValueError(f"Duplicate regret row: {state_id}")
            indexed[state_id] = row
    return indexed


def finite_or_none(value: float) -> float | None:
    return value if math.isfinite(value) else None


def evaluate_observation_group(
    config: dict[str, Any],
    actions: list[dict[str, Any]],
    members: list[dict[str, Any]],
    observed_rows: dict[str, dict[str, Any]],
    signature: str,
) -> dict[str, Any]:
    oracle_costs: list[float] = []
    oracle_paths: list[tuple[str, ...]] = []
    available_ids = {
        str(action["action_id"])
        for action in members[0]["available_actions"]
    }
    costs_via: dict[str, list[float]] = {
        action_id: [] for action_id in sorted(available_ids)
    }
    for decision in members:
        member_available = {
            str(action["action_id"])
            for action in decision["available_actions"]
        }
        if member_available != available_ids:
            raise ValueError("Identical observations exposed different actions")
        oracle_cost, oracle_path = run_mvp.oracle_optimal_plan(
            config,
            actions,
            decision["visible_ids"],
            decision["hidden_ids"],
            int(decision["seed"]),
            float(decision["state"]["budget"]["budget_remaining"]),
            actions_taken=decision["actions_taken"],
        )
        if not math.isfinite(oracle_cost):
            raise ValueError(f"Oracle-unreachable state: {decision['state_id']}")
        oracle_costs.append(float(oracle_cost))
        oracle_paths.append(oracle_path)
        labels = run_m3star._oracle_action_cost_labels(
            config,
            actions,
            decision["available_actions"],
            visible_ids=decision["visible_ids"],
            hidden_ids=decision["hidden_ids"],
            seed=int(decision["seed"]),
            budget_remaining=float(
                decision["state"]["budget"]["budget_remaining"]
            ),
            actions_taken=decision["actions_taken"],
        )
        for action_id in costs_via:
            value = labels[action_id]["label_oracle_cost_via_action"]
            costs_via[action_id].append(
                math.inf if value in (None, "") else float(value)
            )

    minimax = minimax_first_action_regret(oracle_costs, costs_via)
    observed = [observed_rows[str(member["state_id"])] for member in members]
    observed_regrets = [
        float(row["absolute_regret"])
        for row in observed
        if row["absolute_regret"] not in (None, "")
    ]
    first_actions = sorted({path[0] for path in oracle_paths if path})
    state_ids = [str(member["state_id"]) for member in members]
    return {
        "case_id": config["case_id"],
        "observation_sha256": signature,
        "state_count": len(members),
        "state_depth": int(members[0]["state_depth"]),
        "state_ids": state_ids,
        "distinct_oracle_first_action_ids": first_actions,
        "oracle_first_action_conflict": int(len(first_actions) > 1),
        "deterministic_public_policy_lower_bound": finite_or_none(
            float(minimax["lower_bound"])
        ),
        "minimax_first_action_ids": minimax["minimax_action_ids"],
        "worst_regret_by_first_action": {
            action_id: finite_or_none(float(value))
            for action_id, value in minimax["worst_regret_by_action"].items()
        },
        "observed_m3star_max_regret": max(observed_regrets),
        "observed_m3star_action_paths": sorted(
            {str(row["m3star_action_path"]) for row in observed}
        ),
    }


def summarize_groups(groups: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[str, dict[str, Any]] = {}
    for case_id in sorted({str(group["case_id"]) for group in groups}):
        case_groups = [group for group in groups if group["case_id"] == case_id]
        positive = [
            group
            for group in case_groups
            if float(group["deterministic_public_policy_lower_bound"] or 0.0) > 0.0
        ]
        by_case[case_id] = {
            "observation_group_count": len(case_groups),
            "aliased_state_count": sum(
                int(group["state_count"])
                for group in case_groups
                if int(group["state_count"]) > 1
            ),
            "oracle_first_action_conflict_group_count": sum(
                int(group["oracle_first_action_conflict"])
                for group in case_groups
            ),
            "positive_lower_bound_group_count": len(positive),
            "max_deterministic_public_policy_lower_bound": max(
                float(group["deterministic_public_policy_lower_bound"] or 0.0)
                for group in case_groups
            ),
            "observed_m3star_max_regret": max(
                float(group["observed_m3star_max_regret"])
                for group in case_groups
            ),
        }
    global_lower_bound = max(
        float(group["deterministic_public_policy_lower_bound"] or 0.0)
        for group in groups
    )
    observed_max = max(float(group["observed_m3star_max_regret"]) for group in groups)
    worst = sorted(
        groups,
        key=lambda group: (
            float(group["deterministic_public_policy_lower_bound"] or 0.0),
            float(group["observed_m3star_max_regret"]),
            str(group["observation_sha256"]),
        ),
        reverse=True,
    )[:20]
    return {
        "overall": {
            "observation_group_count": len(groups),
            "state_count": sum(int(group["state_count"]) for group in groups),
            "oracle_first_action_conflict_group_count": sum(
                int(group["oracle_first_action_conflict"]) for group in groups
            ),
            "positive_lower_bound_group_count": sum(
                float(group["deterministic_public_policy_lower_bound"] or 0.0) > 0.0
                for group in groups
            ),
            "deterministic_public_policy_worst_regret_lower_bound": (
                global_lower_bound
            ),
            "observed_m3star_worst_regret": observed_max,
            "observed_excess_above_information_lower_bound": (
                observed_max - global_lower_bound
            ),
            "zero_worst_regret_information_theoretically_impossible": (
                global_lower_bound > 0.0
            ),
        },
        "by_case": by_case,
        "worst_observation_groups": worst,
    }


def write_group_csv(path: Path, groups: list[dict[str, Any]]) -> None:
    fields = (
        "case_id",
        "observation_sha256",
        "state_count",
        "state_depth",
        "oracle_first_action_conflict",
        "deterministic_public_policy_lower_bound",
        "observed_m3star_max_regret",
        "distinct_oracle_first_action_ids",
        "minimax_first_action_ids",
        "observed_m3star_action_paths",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for group in groups:
            writer.writerow(
                {
                    field: (
                        json.dumps(group[field], ensure_ascii=False)
                        if isinstance(group[field], list)
                        else group[field]
                    )
                    for field in fields
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regret-result-dir", type=Path, required=True)
    parser.add_argument("--frozen-experiment-dir", type=Path, required=True)
    parser.add_argument("--cases-root", type=Path, required=True)
    parser.add_argument("--cost-profile", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    experiment = regret_audit.load_json(
        args.frozen_experiment_dir / "experiment_report.json"
    )
    cost_profile = run_mvp.load_cost_profile(args.cost_profile)
    if cost_profile["sha256"] != experiment["cost_profile_identity"]["sha256"]:
        raise ValueError("Cost profile differs from frozen experiment")
    case_ids = [str(value) for value in experiment["evaluation_case_ids"]]
    cases = regret_audit.load_frozen_cases(
        args.cases_root,
        case_ids,
        cost_profile,
    )
    observed = load_regret_rows(
        args.regret_result_dir / "state_oracle_regret.csv"
    )
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    case_payloads: dict[str, tuple[Any, Any, Any]] = {}
    max_depth = int(experiment["configuration"]["max_depth"])
    for config, claims, actions in cases:
        case_payloads[str(config["case_id"])] = (config, claims, actions)
        decisions = run_m3star.enumerate_reachable_decision_states(
            config,
            claims,
            actions,
            max_depth=max_depth,
        )
        for decision in decisions:
            snapshot = observation_snapshot(
                config,
                claims,
                actions,
                decision,
            )
            signature = observation_sha256(snapshot)
            grouped[f"{config['case_id']}|{signature}"].append(decision)

    groups: list[dict[str, Any]] = []
    for group_key, members in sorted(grouped.items()):
        case_id, signature = group_key.split("|", 1)
        config, _, actions = case_payloads[case_id]
        groups.append(
            evaluate_observation_group(
                config,
                actions,
                members,
                observed,
                signature,
            )
        )
    if sum(int(group["state_count"]) for group in groups) != len(observed):
        raise ValueError("Observation groups do not cover every regret row")

    summary = summarize_groups(groups)
    csv_path = args.output_dir / "observation_groups.csv"
    write_group_csv(csv_path, groups)
    report = {
        "audit_id": "project05-m3star-observability-regret-lower-bound-v0.1",
        "status": "frozen_model_internal_method_development_audit",
        "paper_or_patent_updated": False,
        "formal_external_claim_allowed": False,
        "policy_class": "deterministic_public_state_policies",
        "bound_construction": (
            "minimise over common public first actions; maximise regret over "
            "aliased hidden states; allow exact clairvoyant Oracle continuation"
        ),
        "why_lower_bound": (
            "Oracle continuation after the common first action is at least as "
            "powerful as any implementable public continuation policy"
        ),
        "summary": summary,
        "frozen_inputs": {
            "experiment_report_sha256": regret_audit.sha256(
                args.frozen_experiment_dir / "experiment_report.json"
            ),
            "state_oracle_regret_sha256": regret_audit.sha256(
                args.regret_result_dir / "state_oracle_regret.csv"
            ),
            "cost_profile_sha256": cost_profile["sha256"],
            "runtime_contract": experiment["runtime_contract"],
            "audit_runner_sha256": regret_audit.sha256(Path(__file__)),
        },
        "observation_group_csv": csv_path.name,
        "observation_group_csv_sha256": regret_audit.sha256(csv_path),
    }
    (args.output_dir / "observability_bound.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary["overall"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
