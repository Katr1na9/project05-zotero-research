#!/usr/bin/env python3
"""Develop the learning-based, non-myopic Project05 M3* planner.

M3* consumes an allowlisted public evidence-gap graph.  Offline outcome labels
are deliberately kept outside this runtime module's public snapshot.
"""

from __future__ import annotations

import importlib.util
import itertools
import math
from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import numpy as np
import xgboost as xgb


def _load_script(name: str) -> Any:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runtime_adapter = _load_script("planner_runtime_adapter")
run_mvp = _load_script("run_mvp")
CONTRACT_PATH = (
    Path(__file__).resolve().parents[1]
    / "governance"
    / "contracts"
    / "planner-runtime-contract-m3star-v0.2.json"
)
RUNTIME_CONTRACT = runtime_adapter.load_contract(CONTRACT_PATH)
FORBIDDEN_RUNTIME_KEYS = set(
    RUNTIME_CONTRACT["document"]["planner_visibility"]["recursive_forbidden_keys"]
)
GRAPH_FEATURE_COLUMNS = [
    "action_cost_ratio",
    "budget_remaining_ratio",
    "cti_node_coverage",
    "cti_edge_coverage",
    "critical_gap_fraction",
    "action_intended_node_fraction",
    "node_is_critical",
    "node_is_intended",
    "node_stage_expected",
    "node_in_degree_ratio",
    "node_out_degree_ratio",
    "predecessor_covered_ratio",
    "successor_covered_ratio",
    "neighbor_covered_ratio",
    "channel_prior_reliability",
    "channel_feedback_mean",
    "expected_granularity_gain",
    "expected_uncertainty_reduction",
    "expected_over_attribution_risk_reduction",
    "expected_conflict_resolution",
    "expected_coverage_delta",
]
GRAPH_TRANSITION_PARAMS: dict[str, Any] = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "max_depth": 2,
    "eta": 0.1,
    "min_child_weight": 0.0,
    "subsample": 1.0,
    "colsample_bytree": 1.0,
    "lambda": 1.0,
    "alpha": 0.0,
    "seed": 11,
    "nthread": 1,
}
DEFAULT_TARGET_REACH_THRESHOLD = 0.90
ACTION_CONTEXT_FEATURE_COLUMNS = [
    "cost",
    "budget_remaining",
    "cti_node_coverage",
    "cti_edge_coverage",
    "critical_gap_count",
    "intended_node_count",
    "intended_gap_overlap_count",
    "intended_critical_gap_overlap_count",
    "intended_gap_precision",
    "intended_gap_recall",
    "channel_prior_reliability",
    "expected_granularity_gain",
    "expected_uncertainty_reduction",
    "expected_over_attribution_risk_reduction",
    "expected_conflict_resolution",
    "expected_coverage_delta",
]
ACTION_VALUE_GRAPH_FEATURE_COLUMNS = [
    f"{aggregation}_{column}"
    for aggregation in ("mean", "max")
    for column in GRAPH_FEATURE_COLUMNS
]
ACTION_VALUE_FEATURE_COLUMNS = [
    *ACTION_VALUE_GRAPH_FEATURE_COLUMNS,
    *ACTION_CONTEXT_FEATURE_COLUMNS,
]
ACTION_VALUE_PARAMS: dict[str, Any] = {
    **GRAPH_TRANSITION_PARAMS,
    "max_depth": 3,
    "eta": 0.05,
}
ACTION_COST_PARAMS: dict[str, Any] = {
    **ACTION_VALUE_PARAMS,
    "objective": "reg:squarederror",
    "eval_metric": "rmse",
}
DOMINANCE_EFFECT_KEYS = (
    "expected_granularity_gain",
    "expected_uncertainty_reduction",
    "expected_over_attribution_risk_reduction",
    "expected_conflict_resolution",
    "expected_coverage_delta",
)


def forbidden_runtime_key_hits(value: Any) -> list[str]:
    """Return paths to fields that must never reach the M3* runtime."""

    return runtime_adapter.recursive_key_hits(value, FORBIDDEN_RUNTIME_KEYS)


def public_graph_snapshot(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the complete public graph-and-action view consumed by M3*."""

    view = runtime_adapter.build_runtime_view(
        config,
        state,
        actions,
        RUNTIME_CONTRACT,
    )
    public_config = view["config"]
    public_state = view["state"]
    unmatched = set(public_state.get("unmatched_cti_node_ids", []))
    matched = set(public_state.get("matched_cti_node_ids", []))
    if not matched:
        matched = {
            node["node_id"]
            for node in public_config.get("cti_nodes", [])
            if node["node_id"] not in unmatched
        }
    granularity_order = list(public_config.get("granularity_order", []))
    support_ceiling = public_config.get("support_ceiling") or (
        granularity_order[-1] if granularity_order else None
    )
    snapshot = {
        "contract": view["contract"],
        "case_id": public_config.get("case_id"),
        "target_granularity": public_config.get("target_granularity"),
        "support_ceiling": support_ceiling,
        "granularity_order": granularity_order,
        "granularity_thresholds": dict(
            public_config.get("granularity_thresholds", {})
        ),
        "nodes": list(public_config.get("cti_nodes", [])),
        "edges": list(public_config.get("cti_edges", [])),
        "covered_node_ids": sorted(matched),
        "unmatched_node_ids": sorted(unmatched),
        "coverage": dict(public_state.get("coverage", {})),
        "budget": dict(public_state.get("budget", {})),
        "actions_taken": list(public_state.get("actions_taken", [])),
        "action_feedback": list(public_state.get("action_feedback", [])),
        "actions": list(view["actions"]),
        "channel_reliability": dict(
            public_config.get("channel_reliability", {})
        ),
    }
    hits = forbidden_runtime_key_hits(snapshot)
    if hits:
        raise ValueError(f"M3* public graph snapshot leaked forbidden keys: {hits}")
    return snapshot


def _action_channel(action: dict[str, Any]) -> str:
    return run_mvp.acquisition_channel(action)


def _channel_feedback_mean(
    snapshot: dict[str, Any],
    action: dict[str, Any],
) -> float:
    channel = _action_channel(action)
    alpha = 1.0
    beta = 1.0
    for feedback in snapshot.get("action_feedback", []):
        feedback_channel = _action_channel(
            {"action_type": feedback.get("action_type", "other")}
        )
        if feedback_channel != channel:
            continue
        if int(feedback.get("recovered_count", 0)) > 0:
            alpha += 1.0
        else:
            beta += 1.0
    return alpha / (alpha + beta)


def _action_context_features(
    snapshot: dict[str, Any],
    action: dict[str, Any],
) -> dict[str, float]:
    """Build the frozen 16-dimensional public state-action context."""

    coverage = snapshot["coverage"]
    intended_nodes = set(action.get("intended_cti_node_ids", []))
    unmatched_nodes = set(snapshot.get("unmatched_node_ids", []))
    critical_nodes = {
        node["node_id"]
        for node in snapshot["nodes"]
        if bool(node.get("critical"))
    }
    intended_gap_overlap = intended_nodes & unmatched_nodes
    intended_critical_gap_overlap = intended_gap_overlap & critical_nodes
    effects = action.get("expected_effects", {})
    channel = _action_channel(action)
    features = {
        "cost": float(action["cost"]),
        "budget_remaining": float(snapshot["budget"]["budget_remaining"]),
        "cti_node_coverage": float(coverage.get("cti_node_coverage", 0.0)),
        "cti_edge_coverage": float(coverage.get("cti_edge_coverage", 0.0)),
        "critical_gap_count": float(coverage.get("critical_gap_count", 0.0)),
        "intended_node_count": float(len(intended_nodes)),
        "intended_gap_overlap_count": float(len(intended_gap_overlap)),
        "intended_critical_gap_overlap_count": float(
            len(intended_critical_gap_overlap)
        ),
        "intended_gap_precision": float(
            len(intended_gap_overlap) / max(1, len(intended_nodes))
        ),
        "intended_gap_recall": float(
            len(intended_gap_overlap) / max(1, len(unmatched_nodes))
        ),
        "channel_prior_reliability": float(
            snapshot.get("channel_reliability", {}).get(channel, 1.0)
        ),
        "expected_granularity_gain": float(
            effects.get("expected_granularity_gain", 0.0)
        ),
        "expected_uncertainty_reduction": float(
            effects.get("expected_uncertainty_reduction", 0.0)
        ),
        "expected_over_attribution_risk_reduction": float(
            effects.get("expected_over_attribution_risk_reduction", 0.0)
        ),
        "expected_conflict_resolution": float(
            effects.get("expected_conflict_resolution", 0.0)
        ),
        "expected_coverage_delta": float(
            effects.get("expected_coverage_delta", 0.0)
        ),
    }
    if list(features) != ACTION_CONTEXT_FEATURE_COLUMNS:
        raise AssertionError("M3* action-context feature order does not match contract")
    if any(not math.isfinite(value) for value in features.values()):
        raise ValueError("M3* action-context features must be finite")
    return features


def _node_transition_features(
    snapshot: dict[str, Any],
    action: dict[str, Any],
    node: dict[str, Any],
) -> dict[str, float]:
    node_id = node["node_id"]
    node_ids = {item["node_id"] for item in snapshot["nodes"]}
    covered = set(snapshot["covered_node_ids"])
    predecessors = {
        edge["source"]
        for edge in snapshot["edges"]
        if edge["target"] == node_id
    }
    successors = {
        edge["target"]
        for edge in snapshot["edges"]
        if edge["source"] == node_id
    }
    neighbours = predecessors | successors
    intended = set(action.get("intended_cti_node_ids", []))
    expected_stages = set(action.get("expected_stages", []))
    coverage = snapshot["coverage"]
    budget = snapshot["budget"]
    total_budget = max(0.1, float(budget.get("budget_total", 0.0)))
    remaining_budget = max(0.0, float(budget.get("budget_remaining", 0.0)))
    critical_count = sum(bool(item.get("critical")) for item in snapshot["nodes"])
    effects = action.get("expected_effects", {})
    channel = _action_channel(action)

    features = {
        "action_cost_ratio": float(action["cost"]) / max(0.1, remaining_budget),
        "budget_remaining_ratio": remaining_budget / total_budget,
        "cti_node_coverage": float(coverage.get("cti_node_coverage", 0.0)),
        "cti_edge_coverage": float(coverage.get("cti_edge_coverage", 0.0)),
        "critical_gap_fraction": float(coverage.get("critical_gap_count", 0.0))
        / max(1, critical_count),
        "action_intended_node_fraction": len(intended & node_ids) / max(1, len(node_ids)),
        "node_is_critical": float(bool(node.get("critical"))),
        "node_is_intended": float(node_id in intended),
        "node_stage_expected": float(node.get("stage") in expected_stages),
        "node_in_degree_ratio": len(predecessors) / max(1, len(node_ids) - 1),
        "node_out_degree_ratio": len(successors) / max(1, len(node_ids) - 1),
        "predecessor_covered_ratio": len(predecessors & covered)
        / max(1, len(predecessors)),
        "successor_covered_ratio": len(successors & covered)
        / max(1, len(successors)),
        "neighbor_covered_ratio": len(neighbours & covered)
        / max(1, len(neighbours)),
        "channel_prior_reliability": float(
            snapshot.get("channel_reliability", {}).get(channel, 1.0)
        ),
        "channel_feedback_mean": _channel_feedback_mean(snapshot, action),
        "expected_granularity_gain": float(
            effects.get("expected_granularity_gain", 0.0)
        ),
        "expected_uncertainty_reduction": float(
            effects.get("expected_uncertainty_reduction", 0.0)
        ),
        "expected_over_attribution_risk_reduction": float(
            effects.get("expected_over_attribution_risk_reduction", 0.0)
        ),
        "expected_conflict_resolution": float(
            effects.get("expected_conflict_resolution", 0.0)
        ),
        "expected_coverage_delta": float(
            effects.get("expected_coverage_delta", 0.0)
        ),
    }
    if list(features) != GRAPH_FEATURE_COLUMNS:
        raise AssertionError("M3* graph feature order does not match its contract")
    if any(not math.isfinite(value) for value in features.values()):
        raise ValueError("M3* graph transition features must be finite")
    return features


def node_transition_feature_rows(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return one public graph-conditioned feature row per action-gap pair."""

    snapshot = public_graph_snapshot(config, state, actions)
    nodes = {node["node_id"]: node for node in snapshot["nodes"]}
    rows: list[dict[str, Any]] = []
    for action in snapshot["actions"]:
        if action.get("action_type") == "stop":
            continue
        for node_id in snapshot["unmatched_node_ids"]:
            rows.append(
                {
                    "action_id": action["action_id"],
                    "node_id": node_id,
                    **_node_transition_features(snapshot, action, nodes[node_id]),
                    **_action_context_features(snapshot, action),
                }
            )
    return rows


def build_node_transition_rows_for_state(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    *,
    visible_ids: set[str],
    hidden_ids: set[str],
    seed: int,
    actions_taken: list[str] | None = None,
    budget_used: float = 0.0,
    action_feedback: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Join offline transition labels to an already-sanitised public feature set."""

    taken = list(actions_taken or [])
    feedback = list(action_feedback or [])
    state = run_mvp.build_state(
        config,
        claims,
        actions,
        f"{config['case_id']}|m3star-offline",
        len(taken),
        "offline_training",
        0.0,
        int(seed),
        set(visible_ids),
        set(hidden_ids),
        set(),
        taken,
        float(budget_used),
        feedback,
    )
    available = run_mvp.available_actions(
        actions,
        taken,
        float(state["budget"]["budget_remaining"]),
    )
    public_rows = node_transition_feature_rows(config, state, available)
    action_map = run_mvp.action_by_id(available)
    before_nodes = run_mvp.covered_node_ids(config, set(visible_ids))
    target_index = run_mvp.granularity_index(
        config,
        config["target_granularity"],
    )
    labels_by_action: dict[str, dict[str, Any]] = {}
    for action_id, action in action_map.items():
        recovered = run_mvp.realized_recovery(
            config,
            action,
            set(hidden_ids),
            int(seed),
        )
        after_visible = set(visible_ids) | recovered
        after_nodes = run_mvp.covered_node_ids(config, after_visible)
        labels_by_action[action_id] = {
            "resolved_node_ids": after_nodes - before_nodes,
            "label_yield_positive": int(bool(recovered)),
            "label_reaches_target_after_action": int(
                run_mvp.granularity_index(
                    config,
                    run_mvp.supportable_granularity(config, after_visible),
                )
                >= target_index
            ),
        }

    rows: list[dict[str, Any]] = []
    for public_row in public_rows:
        labels = labels_by_action[public_row["action_id"]]
        rows.append(
            {
                "case_id": config["case_id"],
                **public_row,
                "label_node_resolved": int(
                    public_row["node_id"] in labels["resolved_node_ids"]
                ),
                "label_yield_positive": labels["label_yield_positive"],
                "label_reaches_target_after_action": labels[
                    "label_reaches_target_after_action"
                ],
            }
        )
    return rows


def _oracle_action_cost_labels(
    config: dict[str, Any],
    actions: list[dict[str, Any]],
    available: list[dict[str, Any]],
    *,
    visible_ids: set[str],
    hidden_ids: set[str],
    seed: int,
    budget_remaining: float,
    actions_taken: list[str],
) -> dict[str, dict[str, Any]]:
    target_index = run_mvp.granularity_index(
        config,
        config["target_granularity"],
    )
    costs: dict[str, float] = {}
    for action in available:
        recovered = run_mvp.realized_recovery(
            config,
            action,
            set(hidden_ids),
            seed,
        )
        after_visible = set(visible_ids) | recovered
        after_hidden = set(hidden_ids) - recovered
        action_cost = float(action["cost"])
        if run_mvp.granularity_index(
            config,
            run_mvp.supportable_granularity(config, after_visible),
        ) >= target_index:
            costs[action["action_id"]] = action_cost
            continue
        future_cost, _ = run_mvp.oracle_optimal_plan(
            config,
            actions,
            after_visible,
            after_hidden,
            seed,
            float(budget_remaining) - action_cost,
            [*actions_taken, action["action_id"]],
        )
        costs[action["action_id"]] = (
            action_cost + float(future_cost)
            if math.isfinite(float(future_cost))
            else math.inf
        )
    finite_costs = [cost for cost in costs.values() if math.isfinite(cost)]
    minimum = min(finite_costs) if finite_costs else math.inf
    return {
        action_id: {
            "label_oracle_optimal_action": int(
                math.isfinite(cost)
                and math.isclose(cost, minimum, rel_tol=1e-9, abs_tol=1e-9)
            ),
            "label_oracle_cost_via_action": cost if math.isfinite(cost) else "",
            "label_oracle_reachable_via_action": int(math.isfinite(cost)),
        }
        for action_id, cost in costs.items()
    }


def build_reachable_transition_rows(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    *,
    max_depth: int = 3,
) -> list[dict[str, Any]]:
    """Breadth-first label all actions at decision states up to depth three."""

    if (
        not isinstance(max_depth, int)
        or isinstance(max_depth, bool)
        or not 1 <= max_depth <= 3
    ):
        raise ValueError("M3* reachable-state max_depth must be an integer in [1, 3]")

    all_claim_ids = {claim["claim_id"] for claim in claims}
    target_index = run_mvp.granularity_index(
        config,
        config["target_granularity"],
    )
    rows: list[dict[str, Any]] = []

    for mask_strategy, mask_intensity, seed in run_mvp.experiment_conditions(config):
        hidden_ids = run_mvp.build_hidden_claims(
            config,
            claims,
            mask_strategy,
            seed,
            mask_intensity,
        )
        visible_ids = all_claim_ids - hidden_ids
        condition_id = (
            f"{config['case_id']}|{mask_strategy}|"
            f"m{round(mask_intensity * 100):03d}|{seed}"
        )
        queue = deque(
            [
                (
                    0,
                    tuple(),
                    visible_ids,
                    hidden_ids,
                    tuple(),
                    0.0,
                    tuple(),
                )
            ]
        )
        visited: set[tuple[Any, ...]] = set()

        while queue:
            (
                depth,
                action_path,
                current_visible,
                current_hidden,
                actions_taken,
                budget_used,
                action_feedback,
            ) = queue.popleft()
            state_key = (
                depth,
                frozenset(current_visible),
                frozenset(current_hidden),
                frozenset(actions_taken),
                round(float(budget_used), 9),
                tuple(
                    sorted(
                        (
                            feedback["action_id"],
                            feedback["action_type"],
                            int(feedback["recovered_count"]),
                        )
                        for feedback in action_feedback
                    )
                ),
            )
            if state_key in visited:
                continue
            visited.add(state_key)

            if run_mvp.granularity_index(
                config,
                run_mvp.supportable_granularity(config, set(current_visible)),
            ) >= target_index:
                continue

            state = run_mvp.build_state(
                config,
                claims,
                actions,
                f"{condition_id}|m3star-bfs|d{depth}",
                depth,
                mask_strategy,
                mask_intensity,
                seed,
                set(current_visible),
                set(current_hidden),
                all_claim_ids - set(current_hidden) - visible_ids,
                list(actions_taken),
                float(budget_used),
                list(action_feedback),
            )
            available = [
                action
                for action in run_mvp.available_actions(
                    actions,
                    list(actions_taken),
                    float(state["budget"]["budget_remaining"]),
                )
                if not run_mvp.is_stop_action(action)
            ]
            if not available:
                continue

            path_label = ">".join(action_path) if action_path else "root"
            state_id = f"{condition_id}|d{depth}|{path_label}"
            state_rows = build_node_transition_rows_for_state(
                config,
                claims,
                actions,
                visible_ids=set(current_visible),
                hidden_ids=set(current_hidden),
                seed=seed,
                actions_taken=list(actions_taken),
                budget_used=float(budget_used),
                action_feedback=list(action_feedback),
            )
            oracle_labels = _oracle_action_cost_labels(
                config,
                actions,
                available,
                visible_ids=set(current_visible),
                hidden_ids=set(current_hidden),
                seed=seed,
                budget_remaining=float(state["budget"]["budget_remaining"]),
                actions_taken=list(actions_taken),
            )
            rows.extend(
                {
                    **row,
                    **oracle_labels[row["action_id"]],
                    "condition_id": condition_id,
                    "mask_strategy": mask_strategy,
                    "mask_intensity": mask_intensity,
                    "seed": seed,
                    "state_id": state_id,
                    "state_depth": depth,
                    "action_path": list(action_path),
                }
                for row in state_rows
            )

            if depth + 1 >= max_depth:
                continue
            for action in sorted(available, key=lambda item: item["action_id"]):
                recovered = run_mvp.realized_recovery(
                    config,
                    action,
                    set(current_hidden),
                    seed,
                )
                queue.append(
                    (
                        depth + 1,
                        (*action_path, action["action_id"]),
                        set(current_visible) | recovered,
                        set(current_hidden) - recovered,
                        (*actions_taken, action["action_id"]),
                        float(budget_used) + float(action["cost"]),
                        (
                            *action_feedback,
                            {
                                "action_id": action["action_id"],
                                "action_type": action.get("action_type", "other"),
                                "recovered_count": len(recovered),
                            },
                        ),
                    )
                )

    return rows


def build_case_partitioned_transition_rows(
    cases: list[
        tuple[
            dict[str, Any],
            list[dict[str, Any]],
            list[dict[str, Any]],
        ]
    ],
    *,
    train_case_ids: set[str] | list[str] | tuple[str, ...],
    validation_case_ids: set[str] | list[str] | tuple[str, ...],
    max_depth: int = 3,
) -> dict[str, Any]:
    """Split raw cases first, then generate masks and reachable states."""

    train_ids = set(train_case_ids)
    validation_ids = set(validation_case_ids)
    overlap = train_ids & validation_ids
    if overlap:
        raise ValueError(
            "M3* training and validation case_id sets must be disjoint; "
            f"overlap={sorted(overlap)}"
        )
    by_case_id = {
        config["case_id"]: (config, claims, actions)
        for config, claims, actions in cases
    }

    def generate(partition: str, case_ids: set[str]) -> list[dict[str, Any]]:
        partition_rows: list[dict[str, Any]] = []
        for case_id in sorted(case_ids):
            config, claims, actions = by_case_id[case_id]
            partition_rows.extend(
                {
                    **row,
                    "dataset_partition": partition,
                }
                for row in build_reachable_transition_rows(
                    config,
                    claims,
                    actions,
                    max_depth=max_depth,
                )
            )
        return partition_rows

    return {
        "train_rows": generate("train", train_ids),
        "validation_rows": generate("validation", validation_ids),
        "split_manifest": {
            "split_unit": "case_id",
            "train_case_ids": sorted(train_ids),
            "validation_case_ids": sorted(validation_ids),
            "case_overlap": [],
            "generation_order": [
                "case_split",
                "mask_generation",
                "bfs_state_expansion",
            ],
            "mask_generated_after_case_split": True,
            "max_depth": max_depth,
        },
    }


def _graph_matrix(
    rows: list[dict[str, Any]],
    *,
    label_column: str | None = None,
) -> xgb.DMatrix:
    values = np.asarray(
        [
            [float(row[column]) for column in GRAPH_FEATURE_COLUMNS]
            for row in rows
        ],
        dtype=np.float32,
    )
    labels = None
    if label_column is not None:
        labels = np.asarray(
            [int(row[label_column]) for row in rows],
            dtype=np.float32,
        )
    return xgb.DMatrix(
        values,
        label=labels,
        feature_names=GRAPH_FEATURE_COLUMNS,
    )


def train_graph_transition_model(
    rows: list[dict[str, Any]],
    *,
    boost_rounds: int = 150,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fit the replaceable first M3* node-transition probability head."""

    if not rows:
        raise ValueError("Cannot train M3* on an empty transition dataset")
    labels = {int(row["label_node_resolved"]) for row in rows}
    if labels != {0, 1}:
        raise ValueError(
            "M3* node-resolution training requires both classes; "
            f"found {sorted(labels)}"
        )
    if not isinstance(boost_rounds, int) or isinstance(boost_rounds, bool) or boost_rounds < 1:
        raise ValueError("M3* boost_rounds must be a positive integer")
    frozen_params = dict(GRAPH_TRANSITION_PARAMS if params is None else params)
    booster = xgb.train(
        frozen_params,
        _graph_matrix(rows, label_column="label_node_resolved"),
        num_boost_round=boost_rounds,
    )
    return {
        "model_family": "m3star_graph_transition_xgboost_v0.1",
        "booster": booster,
        "feature_columns": list(GRAPH_FEATURE_COLUMNS),
        "label_column": "label_node_resolved",
        "params": frozen_params,
        "boost_rounds": boost_rounds,
        "training_case_ids": sorted(
            {str(row["case_id"]) for row in rows if row.get("case_id")}
        ),
    }


def aggregate_action_value_rows(
    node_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collapse node-level rows to one public feature vector per state-action."""

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in node_rows:
        key = (
            str(row["case_id"]),
            str(row["state_id"]),
            str(row["action_id"]),
        )
        grouped.setdefault(key, []).append(row)

    action_rows: list[dict[str, Any]] = []
    label_columns = (
        "label_oracle_optimal_action",
        "label_oracle_cost_via_action",
        "label_oracle_reachable_via_action",
    )
    for (case_id, state_id, action_id), rows in sorted(grouped.items()):
        labels: dict[str, Any] = {}
        for column in label_columns:
            values = {row[column] for row in rows}
            if len(values) != 1:
                raise ValueError(
                    f"M3* action-value label {column} is inconsistent within "
                    f"state-action {(state_id, action_id)}"
                )
            labels[column] = next(iter(values))
        context: dict[str, float] = {}
        for column in ACTION_CONTEXT_FEATURE_COLUMNS:
            values = {float(row[column]) for row in rows}
            if len(values) != 1:
                raise ValueError(
                    f"M3* action-context feature {column} is inconsistent within "
                    f"state-action {(state_id, action_id)}"
                )
            context[column] = next(iter(values))
        features = {
            **{
                f"mean_{column}": sum(float(row[column]) for row in rows)
                / len(rows)
                for column in GRAPH_FEATURE_COLUMNS
            },
            **{
                f"max_{column}": max(float(row[column]) for row in rows)
                for column in GRAPH_FEATURE_COLUMNS
            },
            **context,
        }
        action_rows.append(
            {
                "case_id": case_id,
                "state_id": state_id,
                "action_id": action_id,
                **features,
                **labels,
            }
        )
    return action_rows


def _action_value_matrix(
    rows: list[dict[str, Any]],
    *,
    label_column: str | None = None,
) -> xgb.DMatrix:
    values = np.asarray(
        [
            [float(row[column]) for column in ACTION_VALUE_FEATURE_COLUMNS]
            for row in rows
        ],
        dtype=np.float32,
    )
    labels = None
    if label_column is not None:
        labels = np.asarray(
            [float(row[label_column]) for row in rows],
            dtype=np.float32,
        )
    return xgb.DMatrix(
        values,
        label=labels,
        feature_names=ACTION_VALUE_FEATURE_COLUMNS,
    )


def train_graph_action_value_model(
    rows: list[dict[str, Any]],
    *,
    boost_rounds: int = 150,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Learn which public state-action lies on a minimum-cost reachable path."""

    if not rows:
        raise ValueError("Cannot train M3* action value on an empty dataset")
    labels = {int(row["label_oracle_optimal_action"]) for row in rows}
    if labels != {0, 1}:
        raise ValueError(
            "M3* action-value training requires both classes; "
            f"found {sorted(labels)}"
        )
    if not isinstance(boost_rounds, int) or isinstance(boost_rounds, bool) or boost_rounds < 1:
        raise ValueError("M3* action-value boost_rounds must be a positive integer")
    frozen_params = dict(ACTION_VALUE_PARAMS if params is None else params)
    booster = xgb.train(
        frozen_params,
        _action_value_matrix(
            rows,
            label_column="label_oracle_optimal_action",
        ),
        num_boost_round=boost_rounds,
    )
    reachability_labels = {
        int(row["label_oracle_reachable_via_action"])
        for row in rows
    }
    if reachability_labels != {0, 1}:
        raise ValueError(
            "M3* action-reachability training requires both classes; "
            f"found {sorted(reachability_labels)}"
        )
    reachability_booster = xgb.train(
        frozen_params,
        _action_value_matrix(
            rows,
            label_column="label_oracle_reachable_via_action",
        ),
        num_boost_round=boost_rounds,
    )
    cost_rows = [
        row
        for row in rows
        if row.get("label_oracle_cost_via_action") not in (None, "")
        and math.isfinite(float(row["label_oracle_cost_via_action"]))
        and float(row["label_oracle_cost_via_action"]) >= 0.0
    ]
    if not cost_rows:
        raise ValueError(
            "M3* action-cost training requires at least one finite reachable target"
        )
    cost_params = dict(ACTION_COST_PARAMS)
    cost_booster = xgb.train(
        cost_params,
        _action_value_matrix(
            cost_rows,
            label_column="label_oracle_cost_via_action",
        ),
        num_boost_round=boost_rounds,
    )
    return {
        "model_family": "m3star_graph_action_value_xgboost_v0.3",
        "booster": booster,
        "reachability_booster": reachability_booster,
        "cost_booster": cost_booster,
        "feature_columns": list(ACTION_VALUE_FEATURE_COLUMNS),
        "label_column": "label_oracle_optimal_action",
        "reachability_label_column": (
            "label_oracle_reachable_via_action"
        ),
        "cost_label_column": "label_oracle_cost_via_action",
        "params": frozen_params,
        "cost_params": cost_params,
        "boost_rounds": boost_rounds,
        "training_case_ids": sorted(
            {str(row["case_id"]) for row in rows if row.get("case_id")}
        ),
    }


def predict_action_optimal_probabilities(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[float]:
    if list(model.get("feature_columns", [])) != ACTION_VALUE_FEATURE_COLUMNS:
        raise ValueError("M3* action-value feature contract does not match runtime")
    if not rows:
        return []
    predictions = model["booster"].predict(_action_value_matrix(rows))
    return [float(value) for value in predictions]


def predict_action_reachability_probabilities(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[float]:
    if list(model.get("feature_columns", [])) != ACTION_VALUE_FEATURE_COLUMNS:
        raise ValueError("M3* action-reachability feature contract does not match runtime")
    if "reachability_booster" not in model:
        raise ValueError("M3* action-value bundle is missing its reachability head")
    if not rows:
        return []
    predictions = model["reachability_booster"].predict(
        _action_value_matrix(rows)
    )
    return [float(value) for value in predictions]


def predict_action_costs(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[float]:
    if list(model.get("feature_columns", [])) != ACTION_VALUE_FEATURE_COLUMNS:
        raise ValueError("M3* action-cost feature contract does not match runtime")
    if "cost_booster" not in model:
        raise ValueError("M3* action-value bundle is missing its cost head")
    if not rows:
        return []
    predictions = model["cost_booster"].predict(_action_value_matrix(rows))
    costs: list[float] = []
    for prediction in predictions:
        value = float(prediction)
        if not math.isfinite(value):
            raise ValueError("M3* action-cost predictions must be finite")
        costs.append(max(0.0, value))
    return costs


def action_value_feature_rows(
    snapshot: dict[str, Any],
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the runtime 42-column action graph summary from public fields."""

    nodes = {node["node_id"]: node for node in snapshot["nodes"]}
    rows: list[dict[str, Any]] = []
    for action in actions:
        node_rows = [
            _node_transition_features(
                snapshot,
                action,
                nodes[node_id],
            )
            for node_id in snapshot["unmatched_node_ids"]
        ]
        if not node_rows:
            continue
        features = {
            **{
                f"mean_{column}": sum(float(row[column]) for row in node_rows)
                / len(node_rows)
                for column in GRAPH_FEATURE_COLUMNS
            },
            **{
                f"max_{column}": max(float(row[column]) for row in node_rows)
                for column in GRAPH_FEATURE_COLUMNS
            },
            **_action_context_features(snapshot, action),
        }
        rows.append(
            {
                "action_id": action["action_id"],
                **features,
            }
        )
    return rows


def model_action_value_predictor(
    model: dict[str, Any],
) -> ActionValuePredictor:
    def predict(
        snapshot: dict[str, Any],
        actions: list[dict[str, Any]],
    ) -> dict[str, float]:
        rows = action_value_feature_rows(snapshot, actions)
        probabilities = predict_action_optimal_probabilities(model, rows)
        return {
            row["action_id"]: probability
            for row, probability in zip(rows, probabilities)
        }

    return predict


def model_action_reachability_predictor(
    model: dict[str, Any],
) -> ActionReachabilityPredictor:
    def predict(
        snapshot: dict[str, Any],
        actions: list[dict[str, Any]],
    ) -> dict[str, float]:
        rows = action_value_feature_rows(snapshot, actions)
        probabilities = predict_action_reachability_probabilities(model, rows)
        return {
            row["action_id"]: probability
            for row, probability in zip(rows, probabilities)
        }

    return predict


def model_action_cost_predictor(
    model: dict[str, Any],
) -> ActionCostPredictor:
    def predict(
        snapshot: dict[str, Any],
        actions: list[dict[str, Any]],
    ) -> dict[str, float]:
        rows = action_value_feature_rows(snapshot, actions)
        costs = predict_action_costs(model, rows)
        return {
            row["action_id"]: cost
            for row, cost in zip(rows, costs)
        }

    return predict


def predict_node_resolution_probabilities(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[float]:
    if list(model.get("feature_columns", [])) != GRAPH_FEATURE_COLUMNS:
        raise ValueError("M3* model feature contract does not match runtime features")
    if not rows:
        return []
    predictions = model["booster"].predict(_graph_matrix(rows))
    return [float(value) for value in predictions]


def factorized_node_transition_outcomes(
    node_probabilities: list[tuple[str, float]],
    *,
    max_explicit_outcomes: int | None = None,
) -> list[dict[str, Any]]:
    """Expand Bernoulli node heads and conservatively aggregate pruned mass."""

    if max_explicit_outcomes is not None and (
        not isinstance(max_explicit_outcomes, int)
        or isinstance(max_explicit_outcomes, bool)
        or max_explicit_outcomes < 1
    ):
        raise ValueError("M3* max_explicit_outcomes must be a positive integer")
    node_ids = [str(node_id) for node_id, _ in node_probabilities]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("M3* factorized transition node ids must be unique")
    bounded: list[tuple[str, float]] = []
    for node_id, probability in node_probabilities:
        value = float(probability)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError("M3* node transition probability must be in [0, 1]")
        bounded.append((str(node_id), value))

    outcomes: list[dict[str, Any]] = []
    for resolved_flags in itertools.product((False, True), repeat=len(bounded)):
        probability = 1.0
        resolved: list[str] = []
        for flag, (node_id, node_probability) in zip(resolved_flags, bounded):
            probability *= node_probability if flag else 1.0 - node_probability
            if flag:
                resolved.append(node_id)
        if probability <= 0.0:
            continue
        outcomes.append(
            {
                "probability": probability,
                "resolved_node_ids": sorted(resolved),
            }
        )
    ranked = sorted(
        outcomes,
        key=lambda outcome: (
            -float(outcome["probability"]),
            tuple(outcome["resolved_node_ids"]),
        ),
    )
    if max_explicit_outcomes is None or len(ranked) <= max_explicit_outcomes:
        return ranked or [{"probability": 1.0, "resolved_node_ids": []}]

    explicit = ranked[:max_explicit_outcomes]
    omitted = ranked[max_explicit_outcomes:]
    residual_probability = sum(float(row["probability"]) for row in omitted)
    no_resolution = next(
        (row for row in explicit if not row["resolved_node_ids"]),
        None,
    )
    if no_resolution is None:
        explicit.append(
            {
                "probability": residual_probability,
                "resolved_node_ids": [],
                "residual_aggregation": True,
                "aggregated_probability_mass": residual_probability,
                "aggregated_outcome_count": len(omitted),
            }
        )
    else:
        no_resolution["probability"] = (
            float(no_resolution["probability"]) + residual_probability
        )
        no_resolution["residual_aggregation"] = True
        no_resolution["aggregated_probability_mass"] = residual_probability
        no_resolution["aggregated_outcome_count"] = len(omitted)
    total = sum(float(row["probability"]) for row in explicit)
    if not math.isclose(total, 1.0, rel_tol=1e-12, abs_tol=1e-12):
        for row in explicit:
            row["probability"] = float(row["probability"]) / total
    return explicit


def model_transition_outcomes(
    model: dict[str, Any],
    snapshot: dict[str, Any],
    action: dict[str, Any],
    *,
    max_outcome_nodes: int = 8,
    max_explicit_outcomes: int | None = None,
) -> list[dict[str, Any]]:
    """Expand learned per-node probabilities into an auditable outcome distribution."""

    if max_outcome_nodes < 1:
        raise ValueError("M3* max_outcome_nodes must be positive")
    nodes = {node["node_id"]: node for node in snapshot["nodes"]}
    feature_rows = [
        {
            "action_id": action["action_id"],
            "node_id": node_id,
            **_node_transition_features(snapshot, action, nodes[node_id]),
        }
        for node_id in snapshot["unmatched_node_ids"]
    ]
    if not feature_rows:
        return [{"probability": 1.0, "resolved_node_ids": []}]
    probabilities = predict_node_resolution_probabilities(model, feature_rows)
    return _node_predictions_to_outcomes(
        action,
        feature_rows,
        probabilities,
        max_outcome_nodes=max_outcome_nodes,
        max_explicit_outcomes=max_explicit_outcomes,
    )


def _node_predictions_to_outcomes(
    action: dict[str, Any],
    feature_rows: list[dict[str, Any]],
    probabilities: list[float],
    *,
    max_outcome_nodes: int,
    max_explicit_outcomes: int | None,
) -> list[dict[str, Any]]:
    if len(feature_rows) != len(probabilities):
        raise ValueError("M3* node feature and probability counts do not match")
    ranked = sorted(
        zip(feature_rows, probabilities),
        key=lambda item: (-item[1], item[0]["node_id"]),
    )
    if len(ranked) > max_outcome_nodes:
        intended = set(action.get("intended_cti_node_ids", []))
        ranked = sorted(
            ranked,
            key=lambda item: (
                item[0]["node_id"] not in intended,
                -item[1],
                item[0]["node_id"],
            ),
        )[:max_outcome_nodes]

    return factorized_node_transition_outcomes(
        [
            (row["node_id"], min(1.0, max(0.0, float(node_probability))))
            for row, node_probability in ranked
        ],
        max_explicit_outcomes=max_explicit_outcomes,
    )


class GraphModelTransitionPredictor:
    def __init__(
        self,
        model: dict[str, Any],
        *,
        max_outcome_nodes: int,
        max_explicit_outcomes: int | None,
    ) -> None:
        self.model = model
        self.max_outcome_nodes = max_outcome_nodes
        self.max_explicit_outcomes = max_explicit_outcomes

    def __call__(
        self,
        snapshot: dict[str, Any],
        action: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return model_transition_outcomes(
            self.model,
            snapshot,
            action,
            max_outcome_nodes=self.max_outcome_nodes,
            max_explicit_outcomes=self.max_explicit_outcomes,
        )

    def predict_many(
        self,
        snapshot: dict[str, Any],
        actions: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        nodes = {node["node_id"]: node for node in snapshot["nodes"]}
        all_rows: list[dict[str, Any]] = []
        ranges: dict[str, tuple[int, int]] = {}
        for action in actions:
            start = len(all_rows)
            all_rows.extend(
                {
                    "action_id": action["action_id"],
                    "node_id": node_id,
                    **_node_transition_features(
                        snapshot,
                        action,
                        nodes[node_id],
                    ),
                }
                for node_id in snapshot["unmatched_node_ids"]
            )
            ranges[action["action_id"]] = (start, len(all_rows))
        all_probabilities = predict_node_resolution_probabilities(
            self.model,
            all_rows,
        )
        outcomes_by_action: dict[str, list[dict[str, Any]]] = {}
        for action in actions:
            start, end = ranges[action["action_id"]]
            action_rows = all_rows[start:end]
            if not action_rows:
                outcomes_by_action[action["action_id"]] = [
                    {"probability": 1.0, "resolved_node_ids": []}
                ]
                continue
            outcomes_by_action[action["action_id"]] = (
                _node_predictions_to_outcomes(
                    action,
                    action_rows,
                    all_probabilities[start:end],
                    max_outcome_nodes=self.max_outcome_nodes,
                    max_explicit_outcomes=self.max_explicit_outcomes,
                )
            )
        return outcomes_by_action


def model_transition_predictor(
    model: dict[str, Any],
    *,
    max_outcome_nodes: int = 8,
    max_explicit_outcomes: int | None = None,
) -> TransitionPredictor:
    return GraphModelTransitionPredictor(
        model,
        max_outcome_nodes=max_outcome_nodes,
        max_explicit_outcomes=max_explicit_outcomes,
    )


TransitionPredictor = Callable[
    [dict[str, Any], dict[str, Any]],
    list[dict[str, Any]],
]
ActionValuePredictor = Callable[
    [dict[str, Any], list[dict[str, Any]]],
    dict[str, float],
]
ActionReachabilityPredictor = Callable[
    [dict[str, Any], list[dict[str, Any]]],
    dict[str, float],
]
ActionCostPredictor = Callable[
    [dict[str, Any], list[dict[str, Any]]],
    dict[str, float],
]


def _granularity_index(snapshot: dict[str, Any], name: str) -> int:
    order = snapshot["granularity_order"]
    if name not in order:
        raise ValueError(f"Unknown granularity {name!r}")
    return order.index(name)


def _granularity_thresholds(snapshot: dict[str, Any]) -> dict[str, float]:
    configured = snapshot.get("granularity_thresholds", {})
    return {
        "g3_node_coverage": float(configured.get("g3_node_coverage", 0.75)),
        "g3_edge_coverage": float(configured.get("g3_edge_coverage", 0.60)),
        "g2_node_coverage": float(configured.get("g2_node_coverage", 0.45)),
        "g2_min_stages": float(configured.get("g2_min_stages", 2)),
        "g1_node_coverage": float(configured.get("g1_node_coverage", 0.15)),
    }


def _covered_edges(
    snapshot: dict[str, Any],
    covered_nodes: set[str],
) -> set[str]:
    return {
        edge["edge_id"]
        for edge in snapshot["edges"]
        if edge["source"] in covered_nodes and edge["target"] in covered_nodes
    }


def supportable_granularity_from_nodes(
    snapshot: dict[str, Any],
    covered_node_ids: set[str] | list[str],
) -> str:
    """Evaluate the public structural gate for a predicted node state."""

    covered = set(covered_node_ids)
    nodes = snapshot["nodes"]
    edges = snapshot["edges"]
    node_ids = {node["node_id"] for node in nodes}
    unknown = covered - node_ids
    if unknown:
        raise ValueError(f"Predicted state contains unknown CTI nodes: {sorted(unknown)}")
    covered_edges = _covered_edges(snapshot, covered)
    node_coverage = len(covered) / max(1, len(nodes))
    edge_coverage = len(covered_edges) / max(1, len(edges))
    stages = {
        node["stage"] for node in nodes if node["node_id"] in covered
    }
    critical_ids = {
        node["node_id"] for node in nodes if bool(node.get("critical"))
    }
    thresholds = _granularity_thresholds(snapshot)

    if (
        node_coverage >= thresholds["g3_node_coverage"]
        and edge_coverage >= thresholds["g3_edge_coverage"]
        and critical_ids <= covered
    ):
        structural = "G3_campaign"
    elif (
        node_coverage >= thresholds["g2_node_coverage"]
        and len(stages) >= int(thresholds["g2_min_stages"])
    ):
        structural = "G2_tactic_intent"
    elif node_coverage >= thresholds["g1_node_coverage"]:
        structural = "G1_technique"
    else:
        structural = "G0_unknown"

    ceiling = snapshot.get("support_ceiling") or snapshot["granularity_order"][-1]
    if _granularity_index(snapshot, structural) > _granularity_index(snapshot, ceiling):
        return ceiling
    return structural


def _target_reached(snapshot: dict[str, Any]) -> bool:
    current = supportable_granularity_from_nodes(
        snapshot,
        snapshot["covered_node_ids"],
    )
    return _granularity_index(snapshot, current) >= _granularity_index(
        snapshot,
        snapshot["target_granularity"],
    )


def _normalised_outcomes(
    snapshot: dict[str, Any],
    outcomes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not outcomes:
        raise ValueError("M3* transition predictor returned no outcomes")
    node_ids = {node["node_id"] for node in snapshot["nodes"]}
    normalised: list[dict[str, Any]] = []
    probability_sum = 0.0
    for outcome in outcomes:
        probability = float(outcome.get("probability", -1.0))
        if not math.isfinite(probability) or probability < 0.0:
            raise ValueError("M3* transition probability must be finite and nonnegative")
        resolved = set(outcome.get("resolved_node_ids", []))
        unknown = resolved - node_ids
        if unknown:
            raise ValueError(
                f"M3* transition predicted unknown CTI nodes: {sorted(unknown)}"
            )
        probability_sum += probability
        normalised.append(
            {
                "probability": probability,
                "resolved_node_ids": sorted(resolved),
            }
        )
    if not math.isclose(probability_sum, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(
            f"M3* transition probabilities must sum to 1; found {probability_sum}"
        )
    return normalised


def _project_snapshot(
    snapshot: dict[str, Any],
    action: dict[str, Any],
    resolved_node_ids: list[str],
) -> dict[str, Any]:
    projected = deepcopy(snapshot)
    covered = set(projected["covered_node_ids"]) | set(resolved_node_ids)
    all_nodes = {node["node_id"] for node in projected["nodes"]}
    covered_edges = _covered_edges(projected, covered)
    stages: dict[str, list[int]] = {}
    for node in projected["nodes"]:
        stages.setdefault(node["stage"], [0, 0])
        stages[node["stage"]][1] += 1
        if node["node_id"] in covered:
            stages[node["stage"]][0] += 1
    critical_ids = {
        node["node_id"] for node in projected["nodes"] if node.get("critical")
    }
    projected["covered_node_ids"] = sorted(covered)
    projected["unmatched_node_ids"] = sorted(all_nodes - covered)
    projected["coverage"] = {
        **projected.get("coverage", {}),
        "cti_node_coverage": len(covered) / max(1, len(all_nodes)),
        "cti_edge_coverage": len(covered_edges) / max(1, len(projected["edges"])),
        "critical_gap_count": len(critical_ids - covered),
        "stage_coverage": {
            stage: counts[0] / counts[1] for stage, counts in stages.items()
        },
    }
    cost = float(action["cost"])
    projected["budget"] = {
        **projected["budget"],
        "budget_used": float(projected["budget"].get("budget_used", 0.0)) + cost,
        "budget_remaining": float(projected["budget"]["budget_remaining"]) - cost,
    }
    projected["actions_taken"] = [
        *projected.get("actions_taken", []),
        action["action_id"],
    ]
    projected["action_feedback"] = [
        *projected.get("action_feedback", []),
        {
            "action_id": action["action_id"],
            "action_type": action.get("action_type", "other"),
            "recovered_count": len(resolved_node_ids),
        },
    ]
    return projected


def _candidate_actions(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    taken = set(snapshot.get("actions_taken", []))
    remaining_budget = float(snapshot["budget"]["budget_remaining"])
    return [
        action
        for action in snapshot["actions"]
        if action["action_id"] not in taken
        and float(action["cost"]) <= remaining_budget
        and action.get("action_type") != "stop"
    ]


def _stochastically_dominating_equivalent_action(
    snapshot: dict[str, Any],
    selected_action_id: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Find a strictly more reliable, functionally equivalent public action."""

    by_id = {action["action_id"]: action for action in candidates}
    selected = by_id.get(selected_action_id)
    if selected is None:
        return None
    intended = set(selected.get("intended_cti_node_ids", []))
    if not intended:
        return None
    selected_channel = _action_channel(selected)
    selected_reliability = float(
        snapshot.get("channel_reliability", {}).get(selected_channel, 1.0)
    )
    selected_cost = float(selected["cost"])
    selected_effects = selected.get("expected_effects", {})
    risk_adjusted_selected_cost = selected_cost / max(0.05, selected_reliability)
    eligible: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    for alternative in candidates:
        if alternative["action_id"] == selected_action_id:
            continue
        if set(alternative.get("intended_cti_node_ids", [])) != intended:
            continue
        alternative_channel = _action_channel(alternative)
        alternative_reliability = float(
            snapshot.get("channel_reliability", {}).get(
                alternative_channel,
                1.0,
            )
        )
        if alternative_reliability <= selected_reliability:
            continue
        alternative_cost = float(alternative["cost"])
        if alternative_cost > risk_adjusted_selected_cost + 1e-9:
            continue
        alternative_effects = alternative.get("expected_effects", {})
        if any(
            float(alternative_effects.get(key, 0.0))
            < float(selected_effects.get(key, 0.0)) - 1e-9
            for key in DOMINANCE_EFFECT_KEYS
        ):
            continue
        metadata = {
            "source_action_id": selected_action_id,
            "target_action_id": alternative["action_id"],
            "source_reliability": selected_reliability,
            "target_reliability": alternative_reliability,
            "source_cost": selected_cost,
            "target_cost": alternative_cost,
            "source_risk_adjusted_cost": risk_adjusted_selected_cost,
        }
        key = (
            alternative_cost / max(0.05, alternative_reliability),
            alternative_cost,
            -alternative_reliability,
            str(alternative["action_id"]),
        )
        eligible.append((key, metadata))
    return min(eligible, key=lambda item: item[0])[1] if eligible else None


def _dominance_audit_fields(
    selected_action_id: str | None,
    selection_reason: str,
) -> dict[str, Any]:
    return {
        "pre_dominance_action_id": selected_action_id,
        "dominance_substitution_applied": 0,
        "dominance_selection_reason": selection_reason,
        "dominance_source_action_id": None,
        "dominance_target_action_id": None,
        "dominance_source_reliability": None,
        "dominance_target_reliability": None,
        "dominance_source_cost": None,
        "dominance_target_cost": None,
        "dominance_source_risk_adjusted_cost": None,
    }


def _apply_post_selection_stochastic_dominance(
    snapshot: dict[str, Any],
    plans: list[dict[str, Any]],
    selected: dict[str, Any],
) -> dict[str, Any]:
    default_audit = _dominance_audit_fields(
        selected.get("action_id"),
        "not_applied",
    )
    selected_action_id = selected.get("action_id")
    if selected_action_id is None:
        return {**selected, **default_audit}
    candidates = _candidate_actions(snapshot)
    replacement = _stochastically_dominating_equivalent_action(
        snapshot,
        str(selected_action_id),
        candidates,
    )
    if replacement is None:
        return {**selected, **default_audit}
    by_action_id = {str(plan["action_id"]): plan for plan in plans}
    target = by_action_id.get(str(replacement["target_action_id"]))
    if target is None:
        return {**selected, **default_audit}
    return {
        **target,
        **default_audit,
        "dominance_substitution_applied": 1,
        "dominance_selection_reason": (
            "strict_equivalent_action_stochastic_dominance"
        ),
        "dominance_source_action_id": replacement["source_action_id"],
        "dominance_target_action_id": replacement["target_action_id"],
        "dominance_source_reliability": replacement["source_reliability"],
        "dominance_target_reliability": replacement["target_reliability"],
        "dominance_source_cost": replacement["source_cost"],
        "dominance_target_cost": replacement["target_cost"],
        "dominance_source_risk_adjusted_cost": replacement[
            "source_risk_adjusted_cost"
        ],
    }


def _empty_plan() -> dict[str, Any]:
    return {
        "action_id": None,
        "planned_action_ids": [],
        "target_reach_probability": 0.0,
        "expected_total_cost": 0.0,
        "action_value_probability": 0.0,
        "action_value_cost_index": 0.0,
        "action_reachability_probability": 0.0,
        "action_cost_to_go": 0.0,
        **_dominance_audit_fields(None, "not_applied"),
    }


def _horizon_diagnostics(
    myopic: dict[str, Any] | None,
    nonmyopic: dict[str, Any] | None,
    reason: str,
    myopic_rollout: dict[str, Any] | None = None,
) -> dict[str, Any]:
    def value(plan: dict[str, Any] | None, key: str) -> Any:
        return None if plan is None else plan.get(key)

    probability_delta = None
    cost_delta = None
    if myopic_rollout is not None and nonmyopic is not None:
        probability_delta = float(
            nonmyopic["target_reach_probability"]
        ) - float(myopic_rollout["target_reach_probability"])
        cost_delta = float(nonmyopic["expected_total_cost"]) - float(
            myopic_rollout["expected_total_cost"]
        )
    return {
        "myopic_action_id": value(myopic, "action_id"),
        "myopic_target_reach_probability": value(
            myopic,
            "target_reach_probability",
        ),
        "myopic_expected_total_cost": value(myopic, "expected_total_cost"),
        "myopic_action_value_probability": value(
            myopic,
            "action_value_probability",
        ),
        "myopic_action_value_cost_index": value(
            myopic,
            "action_value_cost_index",
        ),
        "myopic_action_reachability_probability": value(
            myopic,
            "action_reachability_probability",
        ),
        "myopic_action_cost_to_go": value(myopic, "action_cost_to_go"),
        "nonmyopic_action_id": value(nonmyopic, "action_id"),
        "nonmyopic_target_reach_probability": value(
            nonmyopic,
            "target_reach_probability",
        ),
        "nonmyopic_expected_total_cost": value(
            nonmyopic,
            "expected_total_cost",
        ),
        "nonmyopic_action_value_probability": value(
            nonmyopic,
            "action_value_probability",
        ),
        "nonmyopic_action_value_cost_index": value(
            nonmyopic,
            "action_value_cost_index",
        ),
        "nonmyopic_action_reachability_probability": value(
            nonmyopic,
            "action_reachability_probability",
        ),
        "nonmyopic_action_cost_to_go": value(
            nonmyopic,
            "action_cost_to_go",
        ),
        "myopic_rollout_action_id": value(myopic_rollout, "action_id"),
        "myopic_rollout_planned_action_ids": value(
            myopic_rollout,
            "planned_action_ids",
        ),
        "myopic_rollout_target_reach_probability": value(
            myopic_rollout,
            "target_reach_probability",
        ),
        "myopic_rollout_expected_total_cost": value(
            myopic_rollout,
            "expected_total_cost",
        ),
        "myopic_rollout_action_value_probability": value(
            myopic_rollout,
            "action_value_probability",
        ),
        "myopic_rollout_action_value_cost_index": value(
            myopic_rollout,
            "action_value_cost_index",
        ),
        "myopic_rollout_action_reachability_probability": value(
            myopic_rollout,
            "action_reachability_probability",
        ),
        "myopic_rollout_action_cost_to_go": value(
            myopic_rollout,
            "action_cost_to_go",
        ),
        "counterfactual_probability_delta": probability_delta,
        "counterfactual_cost_delta": cost_delta,
        "horizon_selection_reason": reason,
    }


def _plan_pareto_dominates(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    tolerance: float = 1e-9,
) -> bool:
    candidate_probability = float(candidate["target_reach_probability"])
    baseline_probability = float(baseline["target_reach_probability"])
    candidate_cost = float(candidate["expected_total_cost"])
    baseline_cost = float(baseline["expected_total_cost"])
    probability_noninferior = candidate_probability >= (
        baseline_probability - tolerance
    )
    cost_noninferior = candidate_cost <= baseline_cost + tolerance
    strictly_better = (
        candidate_probability > baseline_probability + tolerance
        or candidate_cost < baseline_cost - tolerance
    )
    return probability_noninferior and cost_noninferior and strictly_better


def _planning_state_key(
    snapshot: dict[str, Any],
    depth: int,
) -> tuple[Any, ...]:
    feedback = tuple(
        sorted(
            (
                str(item.get("action_id", "")),
                str(item.get("action_type", "other")),
                int(item.get("recovered_count", 0)),
            )
            for item in snapshot.get("action_feedback", [])
        )
    )
    return (
        depth,
        tuple(sorted(snapshot["covered_node_ids"])),
        tuple(sorted(snapshot.get("actions_taken", []))),
        round(float(snapshot["budget"]["budget_remaining"]), 9),
        feedback,
    )


def _best_plan(
    snapshot: dict[str, Any],
    transition_predictor: TransitionPredictor,
    depth: int,
    target_reach_threshold: float,
    memo: dict[tuple[Any, ...], dict[str, Any]],
    transition_cache: dict[
        tuple[Any, ...],
        dict[str, list[dict[str, Any]]],
    ],
    action_value_predictor: ActionValuePredictor | None,
    action_value_cache: dict[tuple[Any, ...], dict[str, float]],
    action_reachability_predictor: ActionReachabilityPredictor | None = None,
    action_reachability_cache: (
        dict[tuple[Any, ...], dict[str, float]] | None
    ) = None,
    action_cost_predictor: ActionCostPredictor | None = None,
    action_cost_cache: (
        dict[tuple[Any, ...], dict[str, float]] | None
    ) = None,
    required_action_id: str | None = None,
    apply_post_selection_dominance: bool = False,
) -> dict[str, Any]:
    if action_reachability_cache is None:
        action_reachability_cache = {}
    if action_cost_cache is None:
        action_cost_cache = {}
    state_key = (
        *_planning_state_key(snapshot, depth),
        required_action_id,
    )
    if state_key in memo:
        return memo[state_key]
    if _target_reached(snapshot):
        result = {
            **_empty_plan(),
            "target_reach_probability": 1.0,
        }
        memo[state_key] = result
        return result
    if depth <= 0:
        result = _empty_plan()
        memo[state_key] = result
        return result

    plans: list[dict[str, Any]] = []
    candidates = _candidate_actions(snapshot)
    if required_action_id is not None:
        candidates = [
            action
            for action in candidates
            if action["action_id"] == required_action_id
        ]
    transition_key = _planning_state_key(snapshot, 0)[1:]
    batched_outcomes = transition_cache.get(transition_key)
    if batched_outcomes is None:
        predict_many = getattr(transition_predictor, "predict_many", None)
        if callable(predict_many):
            batched_outcomes = predict_many(snapshot, candidates)
        else:
            batched_outcomes = {
                action["action_id"]: transition_predictor(snapshot, action)
                for action in candidates
            }
        transition_cache[transition_key] = batched_outcomes
    action_values = action_value_cache.get(transition_key)
    if action_values is None:
        action_values = (
            action_value_predictor(snapshot, candidates)
            if action_value_predictor is not None
            else {action["action_id"]: 0.0 for action in candidates}
        )
        for action in candidates:
            action_id = action["action_id"]
            if action_id not in action_values:
                raise ValueError(
                    f"M3* action-value predictor omitted action {action_id!r}"
                )
            value = float(action_values[action_id])
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(
                    "M3* action-value probabilities must be finite and in [0, 1]"
                )
            action_values[action_id] = value
        action_value_cache[transition_key] = action_values
    action_reachabilities = action_reachability_cache.get(transition_key)
    if action_reachabilities is None:
        action_reachabilities = (
            action_reachability_predictor(snapshot, candidates)
            if action_reachability_predictor is not None
            else {action["action_id"]: 0.0 for action in candidates}
        )
        for action in candidates:
            action_id = action["action_id"]
            if action_id not in action_reachabilities:
                raise ValueError(
                    "M3* action-reachability predictor omitted action "
                    f"{action_id!r}"
                )
            probability = float(action_reachabilities[action_id])
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                raise ValueError(
                    "M3* action-reachability probabilities must be finite "
                    "and in [0, 1]"
                )
            action_reachabilities[action_id] = probability
        action_reachability_cache[transition_key] = action_reachabilities
    action_costs = action_cost_cache.get(transition_key)
    if action_costs is None and action_cost_predictor is not None:
        action_costs = action_cost_predictor(snapshot, candidates)
        for action in candidates:
            action_id = action["action_id"]
            if action_id not in action_costs:
                raise ValueError(
                    f"M3* action-cost predictor omitted action {action_id!r}"
                )
            value = float(action_costs[action_id])
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(
                    "M3* action-cost predictions must be finite and nonnegative"
                )
            action_costs[action_id] = value
        action_cost_cache[transition_key] = action_costs
    for action in candidates:
        predicted_outcomes = batched_outcomes[action["action_id"]]
        outcomes = _normalised_outcomes(
            snapshot,
            predicted_outcomes,
        )
        reach_probability = 0.0
        expected_future_cost = 0.0
        representative: tuple[tuple[Any, ...], dict[str, Any]] | None = None
        for outcome in outcomes:
            next_snapshot = _project_snapshot(
                snapshot,
                action,
                outcome["resolved_node_ids"],
            )
            child = _best_plan(
                next_snapshot,
                transition_predictor,
                depth - 1,
                target_reach_threshold,
                memo,
                transition_cache,
                action_value_predictor,
                action_value_cache,
                action_reachability_predictor,
                action_reachability_cache,
                action_cost_predictor,
                action_cost_cache,
            )
            probability = float(outcome["probability"])
            reach_probability += probability * float(
                child["target_reach_probability"]
            )
            expected_future_cost += probability * float(child["expected_total_cost"])
            branch_key = (
                probability * float(child["target_reach_probability"]),
                probability,
                -float(child["expected_total_cost"]),
                tuple(child["planned_action_ids"]),
            )
            if representative is None or branch_key > representative[0]:
                representative = (branch_key, child)
        representative_child = representative[1] if representative else _empty_plan()
        expected_total_cost = float(action["cost"]) + expected_future_cost
        action_value_probability = float(
            action_values[action["action_id"]]
        )
        action_reachability_probability = float(
            action_reachabilities[action["action_id"]]
        )
        action_cost_to_go = (
            max(float(action["cost"]), float(action_costs[action["action_id"]]))
            if action_costs is not None
            else expected_total_cost
        )
        plans.append(
            {
                "action_id": action["action_id"],
                "planned_action_ids": [
                    action["action_id"],
                    *representative_child["planned_action_ids"],
                ],
                "target_reach_probability": reach_probability,
                "expected_total_cost": expected_total_cost,
                "action_value_probability": action_value_probability,
                "action_reachability_probability": (
                    action_reachability_probability
                ),
                "action_cost_to_go": action_cost_to_go,
                "action_value_cost_index": (
                    action_value_probability / expected_total_cost
                    if expected_total_cost > 0.0
                    else action_value_probability
                ),
            }
        )

    if not plans:
        result = _empty_plan()
        memo[state_key] = result
        return result
    threshold_plans = [
        plan
        for plan in plans
        if float(plan["target_reach_probability"]) >= target_reach_threshold
    ]
    if threshold_plans:
        best = min(
            threshold_plans,
            key=lambda plan: (
                float(plan["action_cost_to_go"]),
                float(plan["expected_total_cost"]),
                -float(plan["action_value_probability"]),
                -float(plan["action_reachability_probability"]),
                -float(plan["target_reach_probability"]),
                -float(plan["action_value_cost_index"]),
                str(plan["action_id"]),
            ),
        )
        if apply_post_selection_dominance:
            best = _apply_post_selection_stochastic_dominance(
                snapshot,
                plans,
                best,
            )
        else:
            best = {
                **best,
                **_dominance_audit_fields(best.get("action_id"), "disabled"),
            }
        memo[state_key] = best
        return best
    best = min(
        plans,
        key=lambda plan: (
            -float(plan["target_reach_probability"]),
            float(plan["action_cost_to_go"]),
            float(plan["expected_total_cost"]),
            -float(plan["action_value_probability"]),
            -float(plan["action_reachability_probability"]),
            -float(plan["action_value_cost_index"]),
            str(plan["action_id"]),
        ),
    )
    if float(best["target_reach_probability"]) <= 0.0:
        result = _empty_plan()
        memo[state_key] = result
        return result
    if apply_post_selection_dominance:
        best = _apply_post_selection_stochastic_dominance(
            snapshot,
            plans,
            best,
        )
    else:
        best = {
            **best,
            **_dominance_audit_fields(best.get("action_id"), "disabled"),
        }
    memo[state_key] = best
    return best


def plan_m3star_action(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    transition_predictor: TransitionPredictor,
    *,
    horizon: int = 3,
    target_reach_threshold: float = DEFAULT_TARGET_REACH_THRESHOLD,
    action_value_predictor: ActionValuePredictor | None = None,
    action_reachability_predictor: ActionReachabilityPredictor | None = None,
    action_cost_predictor: ActionCostPredictor | None = None,
    myopic_safety_shield: bool = True,
    stochastic_dominance_shield: bool = True,
) -> dict[str, Any]:
    """Choose the first action of the best learned finite-horizon plan."""

    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("M3* planning horizon must be a positive integer")
    if not isinstance(myopic_safety_shield, bool):
        raise ValueError("M3* myopic_safety_shield must be a boolean")
    if not isinstance(stochastic_dominance_shield, bool):
        raise ValueError("M3* stochastic_dominance_shield must be a boolean")
    if (
        isinstance(target_reach_threshold, bool)
        or not isinstance(target_reach_threshold, (int, float))
        or not math.isfinite(float(target_reach_threshold))
        or not 0.0 <= float(target_reach_threshold) <= 1.0
    ):
        raise ValueError("M3* target_reach_threshold must be finite and in [0, 1]")
    snapshot = public_graph_snapshot(config, state, actions)
    if _granularity_index(snapshot, snapshot["target_granularity"]) > _granularity_index(
        snapshot,
        snapshot["support_ceiling"],
    ):
        return {
            **_empty_plan(),
            "requested_horizon": horizon,
            "effective_horizon": 0,
            **_horizon_diagnostics(None, None, "target_above_support_ceiling"),
        }
    if _target_reached(snapshot):
        return {
            **_empty_plan(),
            "target_reach_probability": 1.0,
            "requested_horizon": horizon,
            "effective_horizon": 0,
            **_horizon_diagnostics(None, None, "target_already_reached"),
        }

    transition_cache: dict[
        tuple[Any, ...],
        dict[str, list[dict[str, Any]]],
    ] = {}
    action_value_cache: dict[tuple[Any, ...], dict[str, float]] = {}
    action_reachability_cache: dict[
        tuple[Any, ...],
        dict[str, float],
    ] = {}
    action_cost_cache: dict[tuple[Any, ...], dict[str, float]] = {}
    one_step = _best_plan(
        snapshot,
        transition_predictor,
        1,
        float(target_reach_threshold),
        {},
        transition_cache,
        action_value_predictor,
        action_value_cache,
        action_reachability_predictor,
        action_reachability_cache,
        action_cost_predictor,
        action_cost_cache,
        apply_post_selection_dominance=stochastic_dominance_shield,
    )
    if (
        one_step["action_id"] is not None
        and float(one_step["target_reach_probability"])
        >= float(target_reach_threshold)
    ):
        return {
            **one_step,
            "requested_horizon": horizon,
            "effective_horizon": 1,
            **_horizon_diagnostics(
                one_step,
                None,
                "myopic_threshold_sufficient",
            ),
        }
    if horizon == 1:
        return {
            **one_step,
            "requested_horizon": 1,
            "effective_horizon": 1,
            **_horizon_diagnostics(
                one_step,
                None,
                "myopic_horizon_requested",
            ),
        }
    nonmyopic_memo: dict[tuple[Any, ...], dict[str, Any]] = {}
    plan = _best_plan(
        snapshot,
        transition_predictor,
        horizon,
        float(target_reach_threshold),
        nonmyopic_memo,
        transition_cache,
        action_value_predictor,
        action_value_cache,
        action_reachability_predictor,
        action_reachability_cache,
        action_cost_predictor,
        action_cost_cache,
        apply_post_selection_dominance=stochastic_dominance_shield,
    )
    myopic_rollout = None
    if (
        myopic_safety_shield
        and one_step["action_id"] is not None
        and plan["action_id"] is not None
    ):
        if one_step["action_id"] == plan["action_id"]:
            myopic_rollout = plan
        else:
            myopic_rollout = _best_plan(
                snapshot,
                transition_predictor,
                horizon,
                float(target_reach_threshold),
                nonmyopic_memo,
                transition_cache,
                action_value_predictor,
                action_value_cache,
                action_reachability_predictor,
                action_reachability_cache,
                action_cost_predictor,
                action_cost_cache,
                required_action_id=str(one_step["action_id"]),
            )
    if myopic_safety_shield and one_step["action_id"] is not None:
        nonmyopic_dominates = (
            plan["action_id"] is not None
            and myopic_rollout is not None
            and _plan_pareto_dominates(plan, myopic_rollout)
        )
        if nonmyopic_dominates:
            return {
                **plan,
                "requested_horizon": horizon,
                "effective_horizon": horizon,
                **_horizon_diagnostics(
                    one_step,
                    plan,
                    "counterfactual_rollout_dominance",
                    myopic_rollout,
                ),
            }
        return {
            **one_step,
            "requested_horizon": horizon,
            "effective_horizon": 1,
            **_horizon_diagnostics(
                one_step,
                plan,
                "counterfactual_rollout_shield",
                myopic_rollout,
            ),
        }
    return {
        **plan,
        "requested_horizon": horizon,
        "effective_horizon": horizon,
        **_horizon_diagnostics(
            one_step,
            plan,
            (
                "nonmyopic_plan_selected"
                if plan["action_id"] is not None
                else "nonmyopic_no_positive_plan"
            ),
            myopic_rollout,
        ),
    }


def run_m3star_episode(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    mask_strategy: str,
    mask_intensity: float,
    seed: int,
    transition_predictor: TransitionPredictor,
    *,
    horizon: int = 3,
    target_reach_threshold: float = DEFAULT_TARGET_REACH_THRESHOLD,
    action_value_predictor: ActionValuePredictor | None = None,
    action_reachability_predictor: ActionReachabilityPredictor | None = None,
    action_cost_predictor: ActionCostPredictor | None = None,
    myopic_safety_shield: bool = True,
    stochastic_dominance_shield: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Execute M3* as an auditable receding-horizon learned controller."""

    episode_actions = run_mvp.ensure_stop_action(config, actions)
    decisions: list[dict[str, Any]] = []

    def select_action(
        episode_config: dict[str, Any],
        state: dict[str, Any],
        public_actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        plan = plan_m3star_action(
            episode_config,
            state,
            public_actions,
            transition_predictor,
            horizon=horizon,
            target_reach_threshold=target_reach_threshold,
            action_value_predictor=action_value_predictor,
            action_reachability_predictor=action_reachability_predictor,
            action_cost_predictor=action_cost_predictor,
            myopic_safety_shield=myopic_safety_shield,
            stochastic_dominance_shield=stochastic_dominance_shield,
        )
        selected_action_id = plan["action_id"] or run_mvp.STOP_ACTION_ID
        by_id = run_mvp.action_by_id(public_actions)
        if selected_action_id not in by_id:
            raise ValueError(
                "M3* selected an action that is absent from its public action set: "
                f"{selected_action_id!r}"
            )
        selected_action = by_id[selected_action_id]
        snapshot = public_graph_snapshot(
            episode_config,
            state,
            public_actions,
        )
        decision = {
                "selected_action_id": selected_action_id,
                "planned_action_ids": list(plan["planned_action_ids"]),
                "target_reach_probability": float(
                    plan["target_reach_probability"]
                ),
                "expected_total_cost": float(plan["expected_total_cost"]),
                "action_value_probability": float(
                    plan["action_value_probability"]
                ),
                "action_value_cost_index": float(
                    plan["action_value_cost_index"]
                ),
                "action_reachability_probability": float(
                    plan["action_reachability_probability"]
                ),
                "action_cost_to_go": float(plan["action_cost_to_go"]),
                "pre_dominance_action_id": plan[
                    "pre_dominance_action_id"
                ],
                "dominance_substitution_applied": int(
                    plan["dominance_substitution_applied"]
                ),
                "dominance_selection_reason": plan[
                    "dominance_selection_reason"
                ],
                "dominance_source_action_id": plan[
                    "dominance_source_action_id"
                ],
                "dominance_target_action_id": plan[
                    "dominance_target_action_id"
                ],
                "dominance_source_reliability": plan[
                    "dominance_source_reliability"
                ],
                "dominance_target_reliability": plan[
                    "dominance_target_reliability"
                ],
                "dominance_source_cost": plan["dominance_source_cost"],
                "dominance_target_cost": plan["dominance_target_cost"],
                "dominance_source_risk_adjusted_cost": plan[
                    "dominance_source_risk_adjusted_cost"
                ],
                "myopic_action_id": plan["myopic_action_id"],
                "myopic_target_reach_probability": plan[
                    "myopic_target_reach_probability"
                ],
                "myopic_expected_total_cost": plan[
                    "myopic_expected_total_cost"
                ],
                "myopic_action_value_probability": plan[
                    "myopic_action_value_probability"
                ],
                "myopic_action_value_cost_index": plan[
                    "myopic_action_value_cost_index"
                ],
                "myopic_action_reachability_probability": plan[
                    "myopic_action_reachability_probability"
                ],
                "myopic_action_cost_to_go": plan[
                    "myopic_action_cost_to_go"
                ],
                "nonmyopic_action_id": plan["nonmyopic_action_id"],
                "nonmyopic_target_reach_probability": plan[
                    "nonmyopic_target_reach_probability"
                ],
                "nonmyopic_expected_total_cost": plan[
                    "nonmyopic_expected_total_cost"
                ],
                "nonmyopic_action_value_probability": plan[
                    "nonmyopic_action_value_probability"
                ],
                "nonmyopic_action_value_cost_index": plan[
                    "nonmyopic_action_value_cost_index"
                ],
                "nonmyopic_action_reachability_probability": plan[
                    "nonmyopic_action_reachability_probability"
                ],
                "nonmyopic_action_cost_to_go": plan[
                    "nonmyopic_action_cost_to_go"
                ],
                "myopic_rollout_action_id": plan[
                    "myopic_rollout_action_id"
                ],
                "myopic_rollout_planned_action_ids": plan[
                    "myopic_rollout_planned_action_ids"
                ],
                "myopic_rollout_target_reach_probability": plan[
                    "myopic_rollout_target_reach_probability"
                ],
                "myopic_rollout_expected_total_cost": plan[
                    "myopic_rollout_expected_total_cost"
                ],
                "myopic_rollout_action_value_probability": plan[
                    "myopic_rollout_action_value_probability"
                ],
                "myopic_rollout_action_value_cost_index": plan[
                    "myopic_rollout_action_value_cost_index"
                ],
                "myopic_rollout_action_reachability_probability": plan[
                    "myopic_rollout_action_reachability_probability"
                ],
                "myopic_rollout_action_cost_to_go": plan[
                    "myopic_rollout_action_cost_to_go"
                ],
                "counterfactual_probability_delta": plan[
                    "counterfactual_probability_delta"
                ],
                "counterfactual_cost_delta": plan[
                    "counterfactual_cost_delta"
                ],
                "horizon_selection_reason": plan[
                    "horizon_selection_reason"
                ],
                "myopic_safety_shield": int(myopic_safety_shield),
                "stochastic_dominance_shield": int(
                    stochastic_dominance_shield
                ),
                "planning_horizon": horizon,
                "effective_horizon": int(plan["effective_horizon"]),
                "target_reach_threshold": float(target_reach_threshold),
                "supportable_granularity_before": (
                    state.get("supportable_granularity")
                ),
                "budget_remaining_before": float(
                    state["budget"]["budget_remaining"]
                ),
                "feedback_channel": _action_channel(selected_action),
                "feedback_mean_before": _channel_feedback_mean(
                    snapshot,
                    selected_action,
                ),
            }
        if plan["action_id"] is None:
            decision["stop_reason"] = "no_positive_target_reach_plan"
        decisions.append(decision)
        return selected_action

    result, trace = run_mvp.run_episode(
        config,
        claims,
        episode_actions,
        mask_strategy,
        mask_intensity,
        seed,
        "project05_m3star",
        action_selector=select_action,
    )
    action_events = [
        event for event in trace if event.get("event") == "action_taken"
    ]
    if len(action_events) != len(decisions):
        raise AssertionError(
            "M3* audit decision count does not match executed action count"
        )
    result["stochastic_dominance_shield"] = int(stochastic_dominance_shield)
    result["dominance_substitution_count"] = sum(
        int(decision["dominance_substitution_applied"])
        for decision in decisions
    )
    public_episode_actions = run_mvp.planner_action_views(episode_actions)
    public_actions_by_id = run_mvp.action_by_id(public_episode_actions)
    for decision, event in zip(decisions, action_events):
        selected_action = public_actions_by_id[decision["selected_action_id"]]
        after_snapshot = public_graph_snapshot(
            config,
            event["state"],
            public_episode_actions,
        )
        event["m3star_decision"] = {
            key: value
            for key, value in decision.items()
            if key not in {"feedback_channel", "feedback_mean_before"}
        }
        event["m3star_decision"]["feedback_update"] = {
            "channel": decision["feedback_channel"],
            "mean_before": decision["feedback_mean_before"],
            "mean_after": _channel_feedback_mean(
                after_snapshot,
                selected_action,
            ),
            "observation_positive": int(bool(event["recovered_claim_ids"])),
        }
    return result, trace


def run_m3star_model_episode(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    mask_strategy: str,
    mask_intensity: float,
    seed: int,
    model: dict[str, Any],
    *,
    action_value_model: dict[str, Any] | None = None,
    horizon: int = 3,
    max_outcome_nodes: int = 8,
    max_explicit_outcomes: int | None = None,
    target_reach_threshold: float = DEFAULT_TARGET_REACH_THRESHOLD,
    myopic_safety_shield: bool = True,
    stochastic_dominance_shield: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Connect fitted transition/value heads to the M3* controller."""

    result, trace = run_m3star_episode(
        config,
        claims,
        actions,
        mask_strategy,
        mask_intensity,
        seed,
        model_transition_predictor(
            model,
            max_outcome_nodes=max_outcome_nodes,
            max_explicit_outcomes=max_explicit_outcomes,
        ),
        horizon=horizon,
        target_reach_threshold=target_reach_threshold,
        action_value_predictor=(
            model_action_value_predictor(action_value_model)
            if action_value_model is not None
            else None
        ),
        action_reachability_predictor=(
            model_action_reachability_predictor(action_value_model)
            if action_value_model is not None
            and "reachability_booster" in action_value_model
            else None
        ),
        action_cost_predictor=(
            model_action_cost_predictor(action_value_model)
            if action_value_model is not None
            and "cost_booster" in action_value_model
            else None
        ),
        myopic_safety_shield=myopic_safety_shield,
        stochastic_dominance_shield=stochastic_dominance_shield,
    )
    model_family = str(model.get("model_family", "unknown"))
    action_value_model_family = (
        str(action_value_model.get("model_family", "unknown"))
        if action_value_model is not None
        else "none"
    )
    action_reachability_model_family = (
        action_value_model_family
        if action_value_model is not None
        and "reachability_booster" in action_value_model
        else "none"
    )
    action_cost_model_family = (
        action_value_model_family
        if action_value_model is not None
        and "cost_booster" in action_value_model
        else "none"
    )
    runtime_contract = runtime_adapter.contract_metadata(RUNTIME_CONTRACT)
    result["transition_model_family"] = model_family
    result["action_value_model_family"] = action_value_model_family
    result["action_reachability_model_family"] = (
        action_reachability_model_family
    )
    result["action_cost_model_family"] = action_cost_model_family
    result["runtime_contract_id"] = runtime_contract["contract_id"]
    result["runtime_contract_version"] = runtime_contract["version"]
    result["runtime_contract_sha256"] = runtime_contract["sha256"]
    result["myopic_safety_shield"] = int(myopic_safety_shield)
    result["stochastic_dominance_shield"] = int(
        stochastic_dominance_shield
    )
    result["max_outcome_nodes"] = max_outcome_nodes
    result["max_explicit_outcomes"] = (
        "" if max_explicit_outcomes is None else max_explicit_outcomes
    )
    for event in trace:
        if event.get("event") != "action_taken":
            continue
        event["m3star_decision"]["transition_model_family"] = model_family
        event["m3star_decision"][
            "action_value_model_family"
        ] = action_value_model_family
        event["m3star_decision"][
            "action_reachability_model_family"
        ] = action_reachability_model_family
        event["m3star_decision"][
            "action_cost_model_family"
        ] = action_cost_model_family
        event["m3star_decision"]["runtime_contract_id"] = runtime_contract[
            "contract_id"
        ]
        event["m3star_decision"]["runtime_contract_version"] = runtime_contract[
            "version"
        ]
        event["m3star_decision"]["runtime_contract_sha256"] = runtime_contract[
            "sha256"
        ]
        event["m3star_decision"]["max_outcome_nodes"] = max_outcome_nodes
        event["m3star_decision"]["max_explicit_outcomes"] = (
            None if max_explicit_outcomes is None else max_explicit_outcomes
        )
    return result, trace
