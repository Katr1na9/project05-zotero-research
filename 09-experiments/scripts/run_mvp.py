#!/usr/bin/env python3
"""Run the Project05 C01 minimal evidence-acquisition simulator.

The simulator is intentionally small and dependency-free. It validates the
first MVP idea:

complete evidence -> masked evidence -> acquisition action -> recovered claims
-> updated alignment state -> supportable attribution granularity.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from copy import deepcopy
from pathlib import Path
from typing import Any


PLANNERS = [
    "random",
    "fixed_order",
    "coverage_greedy",
    "project05_m1",
    "m1_no_granularity",
    "m1_no_uncertainty",
    "m1_no_risk",
    "m1_no_coverage",
    "m1_no_cost",
    "cmi_proxy",
    "oracle_optimal",
    "full_evidence",
]
M1_ABLATIONS = {
    "m1_no_granularity": {"granularity"},
    "m1_no_uncertainty": {"uncertainty"},
    "m1_no_risk": {"risk"},
    "m1_no_coverage": {"coverage"},
    "m1_no_cost": {"cost"},
}
CASE_FILENAMES = (
    "case_config.json",
    "evidence_claims.json",
    "acquisition_actions.json",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def discover_case_dirs(examples_dir: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in examples_dir.iterdir()
            if path.is_dir()
            and all((path / filename).is_file() for filename in CASE_FILENAMES)
        ),
        key=lambda path: path.name,
    )


def validate_unique_case_ids(case_dirs: list[Path]) -> None:
    seen: dict[str, Path] = {}
    for case_dir in case_dirs:
        case_id = load_json(case_dir / "case_config.json")["case_id"]
        if case_id in seen:
            raise ValueError(
                f"Duplicate case_id {case_id!r}: {seen[case_id]} and {case_dir}"
            )
        seen[case_id] = case_dir


def claim_tags(claim: dict[str, Any]) -> set[str]:
    return set(claim.get("tags", []))


def hideable_claim_ids(claims: list[dict[str, Any]]) -> list[str]:
    return [
        claim["claim_id"]
        for claim in claims
        if "hideable" in claim_tags(claim)
    ]


def build_hidden_claims(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    strategy: str,
    seed: int,
    mask_intensity: float | None = None,
) -> set[str]:
    hideable = hideable_claim_ids(claims)
    intensity = (
        config.get("mask_intensity", 0.4)
        if mask_intensity is None
        else mask_intensity
    )
    k = max(1, math.ceil(intensity * len(hideable)))
    rng = random.Random(seed)

    if strategy == "random":
        return set(rng.sample(hideable, k))

    if strategy == "stage":
        mask_tags = set(config.get("stage_mask_tags", []))
        stage_hidden = [
            claim["claim_id"]
            for claim in claims
            if "hideable" in claim_tags(claim) and claim_tags(claim) & mask_tags
        ]
        if len(stage_hidden) >= k:
            return set(stage_hidden[:k])
        remaining = [
            claim_id for claim_id in hideable if claim_id not in stage_hidden
        ]
        return set(
            stage_hidden + rng.sample(remaining, k - len(stage_hidden))
        )

    if strategy == "discriminative":
        configured = [
            claim_id
            for claim_id in config.get("discriminative_claim_ids", [])
            if claim_id in hideable
        ]
        if len(configured) >= k:
            return set(configured[:k])
        remaining = [claim_id for claim_id in hideable if claim_id not in configured]
        return set(configured + rng.sample(remaining, k - len(configured)))

    raise ValueError(f"Unsupported mask strategy: {strategy}")


def experiment_conditions(
    config: dict[str, Any],
) -> list[tuple[str, float, int]]:
    intensities = config.get(
        "mask_intensities",
        [config.get("mask_intensity", 0.4)],
    )
    return [
        (strategy, float(intensity), int(seed))
        for strategy in config["mask_strategies"]
        for intensity in intensities
        for seed in config["random_seeds"]
    ]


def make_run_id(
    case_id: str,
    mask_strategy: str,
    mask_intensity: float,
    seed: int,
    planner: str,
) -> str:
    intensity_label = f"m{round(mask_intensity * 100):03d}"
    return f"{case_id}-{mask_strategy}-{intensity_label}-{seed}-{planner}"


def granularity_index(config: dict[str, Any], granularity: str) -> int:
    return config["granularity_order"].index(granularity)


def entropy_binary(p: float) -> float:
    p = min(0.999, max(0.001, p))
    q = 1.0 - p
    return -(p * math.log2(p) + q * math.log2(q))


def covered_node_ids(config: dict[str, Any], visible_ids: set[str]) -> set[str]:
    covered = set()
    for node in config["cti_nodes"]:
        required = set(node["required_claim_ids"])
        if required & visible_ids:
            covered.add(node["node_id"])
    return covered


def covered_edge_ids(config: dict[str, Any], covered_nodes: set[str]) -> set[str]:
    covered = set()
    for edge in config["cti_edges"]:
        if edge["source"] in covered_nodes and edge["target"] in covered_nodes:
            covered.add(edge["edge_id"])
    return covered


def supportable_granularity(
    config: dict[str, Any],
    visible_ids: set[str],
) -> str:
    nodes = config["cti_nodes"]
    edges = config["cti_edges"]
    covered_nodes = covered_node_ids(config, visible_ids)
    covered_edges = covered_edge_ids(config, covered_nodes)

    node_cov = len(covered_nodes) / max(1, len(nodes))
    edge_cov = len(covered_edges) / max(1, len(edges))
    stages = {
        node["stage"]
        for node in nodes
        if node["node_id"] in covered_nodes
    }
    critical_nodes = [node for node in nodes if node.get("critical")]
    critical_covered = sum(
        1 for node in critical_nodes if node["node_id"] in covered_nodes
    )

    if node_cov >= 0.75 and edge_cov >= 0.60 and critical_covered == len(critical_nodes):
        structural_granularity = "G3_campaign"
    elif node_cov >= 0.45 and len(stages) >= 2:
        structural_granularity = "G2_tactic_intent"
    elif node_cov >= 0.15:
        structural_granularity = "G1_technique"
    else:
        structural_granularity = "G0_unknown"

    support_ceiling = config.get(
        "support_ceiling",
        config["granularity_order"][-1],
    )
    if (
        granularity_index(config, structural_granularity)
        > granularity_index(config, support_ceiling)
    ):
        return support_ceiling
    return structural_granularity


def build_state(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    run_id: str,
    step_index: int,
    mask_strategy: str,
    mask_intensity: float,
    seed: int,
    visible_ids: set[str],
    hidden_ids: set[str],
    recovered_ids: set[str],
    actions_taken: list[str],
    budget_used: float,
    action_feedback: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    claim_by_id = {claim["claim_id"]: claim for claim in claims}
    nodes = config["cti_nodes"]
    edges = config["cti_edges"]
    covered_nodes = covered_node_ids(config, visible_ids)
    covered_edges = covered_edge_ids(config, covered_nodes)
    unmatched_nodes = [n["node_id"] for n in nodes if n["node_id"] not in covered_nodes]
    unmatched_edges = [e["edge_id"] for e in edges if e["edge_id"] not in covered_edges]

    stage_counts: dict[str, list[int]] = {}
    for node in nodes:
        stage_counts.setdefault(node["stage"], [0, 0])
        stage_counts[node["stage"]][1] += 1
        if node["node_id"] in covered_nodes:
            stage_counts[node["stage"]][0] += 1
    stage_coverage = {
        stage: counts[0] / counts[1] for stage, counts in stage_counts.items()
    }

    hideable = set(hideable_claim_ids(claims))
    evidence_types: dict[str, list[int]] = {}
    for claim in claims:
        if claim["claim_id"] not in hideable:
            continue
        source_type = claim["source_type"]
        evidence_types.setdefault(source_type, [0, 0])
        evidence_types[source_type][1] += 1
        if claim["claim_id"] in visible_ids:
            evidence_types[source_type][0] += 1
    evidence_type_coverage = {
        source_type: counts[0] / counts[1]
        for source_type, counts in evidence_types.items()
    }

    critical_nodes = [node for node in nodes if node.get("critical")]
    critical_gap_count = sum(
        1 for node in critical_nodes if node["node_id"] not in covered_nodes
    )

    unique_visible = [
        claim_id
        for claim_id in visible_ids
        if claim_id in claim_by_id and "unique" in claim_tags(claim_by_id[claim_id])
    ]
    max_unique = max(
        1,
        sum(1 for claim in claims if "unique" in claim_tags(claim)),
    )
    node_cov = len(covered_nodes) / max(1, len(nodes))
    edge_cov = len(covered_edges) / max(1, len(edges))
    alpha_score = min(0.95, max(0.05, 0.35 + 0.40 * node_cov + 0.20 * (len(unique_visible) / max_unique)))
    candidate_entropy = entropy_binary(alpha_score)

    remaining_action_ids = [
        action["action_id"]
        for action in actions
        if action["action_id"] not in actions_taken
    ]
    budget_total = config["budget_total"]
    budget_remaining = max(0.0, budget_total - budget_used)
    granularity = supportable_granularity(config, visible_ids)

    return {
        "state_id": f"{run_id}-S{step_index:02d}",
        "case_id": config["case_id"],
        "run_id": run_id,
        "step_index": step_index,
        "mask_strategy": mask_strategy,
        "mask_intensity": mask_intensity,
        "random_seed": seed,
        "visible_claim_ids": sorted(visible_ids),
        "hidden_claim_ids": sorted(hidden_ids),
        "recovered_claim_ids": sorted(recovered_ids),
        "matched_cti_node_ids": sorted(covered_nodes),
        "unmatched_cti_node_ids": unmatched_nodes,
        "matched_cti_edge_ids": sorted(covered_edges),
        "unmatched_cti_edge_ids": unmatched_edges,
        "coverage": {
            "cti_node_coverage": node_cov,
            "cti_edge_coverage": edge_cov,
            "stage_coverage": stage_coverage,
            "evidence_type_coverage": evidence_type_coverage,
            "critical_gap_count": critical_gap_count,
        },
        "alignment_quality": {
            "alignment_score_mean": round(0.55 + 0.40 * node_cov, 4),
            "alignment_score_min": round(0.35 + 0.40 * edge_cov, 4),
            "conflict_count": 0,
            "unexplained_local_claim_ids": [],
            "conflict_claim_ids": [],
        },
        "candidate_hypotheses": [
            {
                "hypothesis_id": "campaign_alpha",
                "hypothesis_type": "campaign",
                "label": "Campaign Alpha",
                "score": round(alpha_score, 4),
                "supporting_claim_ids": sorted(visible_ids),
                "contradicting_claim_ids": [],
            },
            {
                "hypothesis_id": "unknown",
                "hypothesis_type": "unknown",
                "label": "Unknown / insufficient evidence",
                "score": round(1.0 - alpha_score, 4),
                "supporting_claim_ids": sorted(hidden_ids),
                "contradicting_claim_ids": [],
            },
        ],
        "discriminability": {
            "candidate_entropy": round(candidate_entropy, 4),
            "top2_margin": round(abs(alpha_score - (1.0 - alpha_score)), 4),
            "shared_ttp_ratio": round(max(0.0, 1.0 - (len(unique_visible) / max_unique)), 4),
            "unique_evidence_count": len(unique_visible),
        },
        "supportable_granularity": granularity,
        "granularity_rationale": explain_granularity(granularity, node_cov, edge_cov, critical_gap_count),
        "budget": {
            "budget_total": budget_total,
            "budget_used": budget_used,
            "budget_remaining": budget_remaining,
        },
        "actions_taken": actions_taken[:],
        "action_feedback": deepcopy(action_feedback or []),
        "remaining_action_ids": remaining_action_ids,
        "stop_recommendation": {
            "should_stop": granularity_index(config, granularity) >= granularity_index(config, config["target_granularity"]),
            "reason": "target_granularity_reached"
            if granularity_index(config, granularity) >= granularity_index(config, config["target_granularity"])
            else "continue",
            "explanation": "Stop when the state reaches the configured target granularity.",
        },
    }


def explain_granularity(granularity: str, node_cov: float, edge_cov: float, critical_gap_count: int) -> str:
    if granularity == "G3_campaign":
        return "Enough stage coverage, edge continuity, and critical evidence are visible to support a campaign-level trace."
    if granularity == "G2_tactic_intent":
        return "Multiple stages are visible, but campaign-level continuity or critical evidence is still incomplete."
    if granularity == "G1_technique":
        return "At least one technique is supported, but the observed chain is too sparse for higher-level attribution."
    return "Visible evidence is insufficient for a supported attribution claim."


def recoverable_hidden(action: dict[str, Any], hidden_ids: set[str]) -> set[str]:
    return set(action["recoverable_claim_ids"]) & hidden_ids


def action_by_id(actions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {action["action_id"]: action for action in actions}


def available_actions(
    actions: list[dict[str, Any]],
    actions_taken: list[str],
    budget_remaining: float,
) -> list[dict[str, Any]]:
    taken = set(actions_taken)
    return [
        action
        for action in actions
        if action["action_id"] not in taken and action["cost"] <= budget_remaining
    ]


def expected_effect(
    action: dict[str, Any],
    name: str,
) -> float:
    return float(action.get("expected_effects", {}).get(name, 0.0))


def m1_action_score(
    action: dict[str, Any],
    state: dict[str, Any],
    excluded_components: set[str] | None = None,
) -> float:
    excluded = excluded_components or set()
    has_critical_gap = state["coverage"]["critical_gap_count"] > 0
    components = {
        "granularity": 2.0
        * expected_effect(action, "expected_granularity_gain"),
        "uncertainty": expected_effect(
            action,
            "expected_uncertainty_reduction",
        ),
        "risk": (1.25 if has_critical_gap else 1.0)
        * expected_effect(
            action,
            "expected_over_attribution_risk_reduction",
        ),
        "coverage": (1.5 if has_critical_gap else 1.0)
        * expected_effect(action, "expected_coverage_delta"),
        "cost": -0.35 * float(action["cost"]),
    }
    score = sum(
        value
        for name, value in components.items()
        if name not in excluded
    )
    score += expected_effect(action, "expected_conflict_resolution")
    return score


def select_oracle_optimal_action(
    config: dict[str, Any],
    actions: list[dict[str, Any]],
    visible_ids: set[str],
    hidden_ids: set[str],
    actions_taken: list[str],
    budget_used: float,
) -> dict[str, Any] | None:
    target_idx = granularity_index(config, config["target_granularity"])
    action_map = action_by_id(actions)
    initial_taken = frozenset(actions_taken)
    initial_remaining = float(config["budget_total"]) - budget_used
    memo: dict[
        tuple[frozenset[str], frozenset[str], float],
        tuple[float, tuple[str, ...]],
    ] = {}

    def search(
        current_visible: frozenset[str],
        current_hidden: frozenset[str],
        taken: frozenset[str],
        budget_remaining: float,
    ) -> tuple[float, tuple[str, ...]]:
        if granularity_index(
            config,
            supportable_granularity(config, set(current_visible)),
        ) >= target_idx:
            return 0.0, ()

        key = (current_hidden, taken, round(budget_remaining, 6))
        if key in memo:
            return memo[key]

        best_cost = math.inf
        best_path: tuple[str, ...] = ()
        for action in actions:
            action_id = action["action_id"]
            action_cost = float(action["cost"])
            if action_id in taken or action_cost > budget_remaining:
                continue
            recovered = (
                set(action["recoverable_claim_ids"]) & set(current_hidden)
            )
            if not recovered:
                continue
            tail_cost, tail_path = search(
                frozenset(set(current_visible) | recovered),
                frozenset(set(current_hidden) - recovered),
                taken | {action_id},
                budget_remaining - action_cost,
            )
            total_cost = action_cost + tail_cost
            path = (action_id,) + tail_path
            if (total_cost, path) < (best_cost, best_path):
                best_cost = total_cost
                best_path = path

        memo[key] = (best_cost, best_path)
        return memo[key]

    _, path = search(
        frozenset(visible_ids),
        frozenset(hidden_ids),
        initial_taken,
        initial_remaining,
    )
    if path:
        return action_map[path[0]]

    candidates = available_actions(
        actions,
        actions_taken,
        initial_remaining,
    )
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda action: (
            len(recoverable_hidden(action, hidden_ids))
            / max(0.1, action["cost"]),
            len(recoverable_hidden(action, hidden_ids)),
            -action["cost"],
            action["action_id"],
        ),
    )


def select_action(
    planner: str,
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    state: dict[str, Any],
    visible_ids: set[str],
    hidden_ids: set[str],
    actions_taken: list[str],
    seed: int,
) -> dict[str, Any] | None:
    candidates = available_actions(
        actions,
        actions_taken,
        state["budget"]["budget_remaining"],
    )
    if not candidates:
        return None

    if planner == "random":
        salt = sum(ord(ch) for ch in planner)
        rng = random.Random(seed + 1009 * (len(actions_taken) + 1) + salt)
        return rng.choice(candidates)

    if planner == "fixed_order":
        by_id = action_by_id(candidates)
        for action_id in config.get("fixed_action_order", []):
            if action_id in by_id:
                return by_id[action_id]
        return candidates[0]

    if planner == "coverage_greedy":
        return max(
            candidates,
            key=lambda action: (
                expected_effect(action, "expected_coverage_delta")
                / max(0.1, action["cost"]),
                expected_effect(action, "expected_coverage_delta"),
                -action["cost"],
            ),
        )

    if planner == "project05_m1" or planner in M1_ABLATIONS:
        excluded = M1_ABLATIONS.get(planner, set())
        return max(
            candidates,
            key=lambda action: (
                m1_action_score(action, state, excluded),
                -action["cost"],
                action["action_id"],
            ),
        )

    if planner == "cmi_proxy":
        return max(
            candidates,
            key=lambda action: (
                expected_effect(
                    action,
                    "expected_uncertainty_reduction",
                )
                / max(0.1, action["cost"]),
                expected_effect(
                    action,
                    "expected_uncertainty_reduction",
                ),
                -action["cost"],
                action["action_id"],
            ),
        )

    if planner == "oracle_optimal":
        return select_oracle_optimal_action(
            config,
            actions,
            visible_ids,
            hidden_ids,
            actions_taken,
            state["budget"]["budget_used"],
        )

    raise ValueError(f"Unsupported planner: {planner}")


def run_episode(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    mask_strategy: str,
    mask_intensity: float,
    seed: int,
    planner: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    all_ids = {claim["claim_id"] for claim in claims}
    hidden_ids = build_hidden_claims(
        config,
        claims,
        mask_strategy,
        seed,
        mask_intensity,
    )
    visible_ids = all_ids - hidden_ids
    recovered_ids: set[str] = set()
    actions_taken: list[str] = []
    action_feedback: list[dict[str, Any]] = []
    budget_used = 0.0
    run_id = make_run_id(
        config["case_id"],
        mask_strategy,
        mask_intensity,
        seed,
        planner,
    )

    if planner == "full_evidence":
        hidden_ids = set()
        visible_ids = set(all_ids)

    trace: list[dict[str, Any]] = []
    state = build_state(
        config,
        claims,
        actions,
        run_id,
        0,
        mask_strategy,
        mask_intensity,
        seed,
        visible_ids,
        hidden_ids,
        recovered_ids,
        actions_taken,
        budget_used,
        action_feedback,
    )
    trace.append({"event": "initial_state", "state": deepcopy(state)})

    target_idx = granularity_index(config, config["target_granularity"])
    max_steps = len(actions)

    for step in range(1, max_steps + 1):
        if granularity_index(config, state["supportable_granularity"]) >= target_idx:
            break
        if planner == "full_evidence":
            break

        action = select_action(
            planner,
            config,
            claims,
            actions,
            state,
            visible_ids,
            hidden_ids if planner == "oracle_optimal" else set(),
            actions_taken,
            seed,
        )
        if action is None:
            break

        recovered = recoverable_hidden(action, hidden_ids)
        budget_used += action["cost"]
        actions_taken.append(action["action_id"])
        action_feedback.append(
            {
                "action_id": action["action_id"],
                "action_type": action["action_type"],
                "recovered_count": len(recovered),
            }
        )
        visible_ids |= recovered
        hidden_ids -= recovered
        recovered_ids |= recovered

        state = build_state(
            config,
            claims,
            actions,
            run_id,
            step,
            mask_strategy,
            mask_intensity,
            seed,
            visible_ids,
            hidden_ids,
            recovered_ids,
            actions_taken,
            budget_used,
            action_feedback,
        )
        trace.append(
            {
                "event": "action_taken",
                "action_id": action["action_id"],
                "action_type": action["action_type"],
                "cost": action["cost"],
                "recovered_claim_ids": sorted(recovered),
                "state": deepcopy(state),
            }
        )

    final_state = trace[-1]["state"]
    reached = granularity_index(config, final_state["supportable_granularity"]) >= target_idx
    initial_state = trace[0]["state"]
    support_ceiling = config.get(
        "support_ceiling",
        config["granularity_order"][-1],
    )
    final_idx = granularity_index(
        config,
        final_state["supportable_granularity"],
    )
    ceiling_idx = granularity_index(config, support_ceiling)
    initial_direct_over_attr = (
        granularity_index(config, config["target_granularity"])
        > granularity_index(config, initial_state["supportable_granularity"])
    )
    result = {
        "case_id": config["case_id"],
        "mask_strategy": mask_strategy,
        "mask_intensity": mask_intensity,
        "seed": seed,
        "planner": planner,
        "target_granularity": config["target_granularity"],
        "support_ceiling": support_ceiling,
        "initial_granularity": initial_state["supportable_granularity"],
        "final_granularity": final_state["supportable_granularity"],
        "reached_target": int(reached),
        "correct_stop": int(reached and final_idx <= ceiling_idx),
        "ceiling_violation": int(final_idx > ceiling_idx),
        "cost_to_target": budget_used if reached else "",
        "budget_used": budget_used,
        "steps_to_target": len(actions_taken) if reached else "",
        "steps_taken": len(actions_taken),
        "actions_taken": "|".join(actions_taken),
        "initial_hidden_claims": len(
            build_hidden_claims(
                config,
                claims,
                mask_strategy,
                seed,
                mask_intensity,
            )
        )
        if planner != "full_evidence"
        else 0,
        "recovered_claims": len(recovered_ids),
        "final_node_coverage": round(final_state["coverage"]["cti_node_coverage"], 4),
        "final_edge_coverage": round(final_state["coverage"]["cti_edge_coverage"], 4),
        "final_critical_gap_count": final_state["coverage"]["critical_gap_count"],
        "initial_direct_over_attribution": int(initial_direct_over_attr),
    }
    return result, trace


def execute_case(
    case_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    config = load_json(case_dir / "case_config.json")
    claims = load_json(case_dir / "evidence_claims.json")
    actions = load_json(case_dir / "acquisition_actions.json")

    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for mask_strategy, mask_intensity, seed in experiment_conditions(config):
        for planner in PLANNERS:
            row, trace = run_episode(
                config,
                claims,
                actions,
                mask_strategy,
                mask_intensity,
                seed,
                planner,
            )
            rows.append(row)
            traces.append(
                {
                    "run_id": make_run_id(
                        config["case_id"],
                        mask_strategy,
                        mask_intensity,
                        seed,
                        planner,
                    ),
                    "result": row,
                    "trace": trace,
                }
            )

    return add_oracle_relative_metrics(rows), traces


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty result set")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_all(case_dir: Path, output_dir: Path) -> None:
    rows, traces = execute_case(case_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "c01_mvp_results.csv"
    write_csv(csv_path, rows)

    write_json(output_dir / "c01_mvp_traces.json", traces)
    summary = summarize(rows)
    write_json(output_dir / "c01_mvp_summary.json", summary)

    print(f"Wrote {csv_path}")
    print(f"Wrote {output_dir / 'c01_mvp_traces.json'}")
    print(f"Wrote {output_dir / 'c01_mvp_summary.json'}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def run_cases(
    case_dirs: list[Path],
    output_dir: Path,
    write_traces: bool = True,
) -> list[dict[str, Any]]:
    if not case_dirs:
        raise ValueError("No complete case directories were found")
    validate_unique_case_ids(case_dirs)

    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        case_rows, case_traces = execute_case(case_dir)
        rows.extend(case_rows)
        traces.extend(case_traces)

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "all_cases_results.csv"
    write_csv(csv_path, rows)
    write_json(output_dir / "all_cases_summary.json", summarize_stratified(rows))
    if write_traces:
        write_json(output_dir / "all_cases_traces.json", traces)

    print(f"Wrote {csv_path}")
    print(f"Wrote {output_dir / 'all_cases_summary.json'}")
    if write_traces:
        print(f"Wrote {output_dir / 'all_cases_traces.json'}")
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_planner: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_planner.setdefault(row["planner"], []).append(row)

    summary = {}
    for planner, planner_rows in by_planner.items():
        successes = [row for row in planner_rows if row["reached_target"] == 1]
        costs = [float(row["cost_to_target"]) for row in successes if row["cost_to_target"] != ""]
        steps = [int(row["steps_to_target"]) for row in successes if row["steps_to_target"] != ""]
        summary[planner] = {
            "runs": len(planner_rows),
            "success_rate": round(len(successes) / len(planner_rows), 4),
            "mean_cost_to_target": round(sum(costs) / len(costs), 4) if costs else None,
            "mean_steps_to_target": round(sum(steps) / len(steps), 4) if steps else None,
            "mean_budget_used": round(sum(float(row["budget_used"]) for row in planner_rows) / len(planner_rows), 4),
            "mean_final_node_coverage": round(sum(float(row["final_node_coverage"]) for row in planner_rows) / len(planner_rows), 4),
        }
    return summary


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["reached_target"] == 1]
    costs = [
        float(row["cost_to_target"])
        for row in successes
        if row["cost_to_target"] != ""
    ]
    steps = [
        int(row["steps_to_target"])
        for row in successes
        if row["steps_to_target"] != ""
    ]
    regrets = [
        float(row["cost_regret_vs_oracle"])
        for row in rows
        if row.get("cost_regret_vs_oracle", "") != ""
    ]
    top1_hits = [
        int(row["oracle_top1_action_hit"])
        for row in rows
        if row.get("oracle_top1_action_hit", "") != ""
    ]
    return {
        "independent_case_count": len({row["case_id"] for row in rows}),
        "repeated_run_count": len(rows),
        "success_rate": round(len(successes) / len(rows), 4),
        "mean_cost_to_target": (
            round(sum(costs) / len(costs), 4) if costs else None
        ),
        "mean_steps_to_target": (
            round(sum(steps) / len(steps), 4) if steps else None
        ),
        "mean_budget_used": round(
            sum(float(row["budget_used"]) for row in rows) / len(rows),
            4,
        ),
        "mean_final_node_coverage": round(
            sum(float(row["final_node_coverage"]) for row in rows) / len(rows),
            4,
        ),
        "mean_cost_regret_vs_oracle": (
            round(sum(regrets) / len(regrets), 4) if regrets else None
        ),
        "oracle_top1_action_hit_rate": (
            round(sum(top1_hits) / len(top1_hits), 4)
            if top1_hits
            else None
        ),
    }


def first_action_id(row: dict[str, Any]) -> str:
    actions = str(row.get("actions_taken", ""))
    return actions.split("|", 1)[0] if actions else ""


def add_oracle_relative_metrics(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    condition_keys = (
        "case_id",
        "mask_strategy",
        "mask_intensity",
        "seed",
    )
    oracle_by_condition: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        if row["planner"] != "oracle_optimal":
            continue
        key = tuple(row[field] for field in condition_keys)
        oracle_by_condition[key] = row

    enriched: list[dict[str, Any]] = []
    for row in rows:
        updated = dict(row)
        if row["planner"] == "full_evidence":
            updated["oracle_cost_to_target"] = ""
            updated["cost_regret_vs_oracle"] = ""
            updated["oracle_top1_action_id"] = ""
            updated["oracle_top1_action_hit"] = ""
            enriched.append(updated)
            continue
        key = tuple(row[field] for field in condition_keys)
        oracle = oracle_by_condition.get(key)
        if oracle is None:
            updated["oracle_cost_to_target"] = ""
            updated["cost_regret_vs_oracle"] = ""
            updated["oracle_top1_action_id"] = ""
            updated["oracle_top1_action_hit"] = ""
        else:
            oracle_cost = oracle.get("cost_to_target", "")
            updated["oracle_cost_to_target"] = oracle_cost
            if (
                row.get("cost_to_target", "") != ""
                and oracle_cost != ""
            ):
                updated["cost_regret_vs_oracle"] = round(
                    float(row["cost_to_target"]) - float(oracle_cost),
                    4,
                )
            else:
                updated["cost_regret_vs_oracle"] = ""
            oracle_first = first_action_id(oracle)
            updated["oracle_top1_action_id"] = oracle_first
            updated["oracle_top1_action_hit"] = int(
                bool(oracle_first)
                and first_action_id(row) == oracle_first
            )
        enriched.append(updated)
    return enriched


def group_by(
    rows: list[dict[str, Any]],
    keys: tuple[str, ...],
) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        group_key = tuple(row[key] for key in keys)
        grouped.setdefault(group_key, []).append(row)
    return grouped


def summarize_stratified(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("Cannot summarize an empty result set")

    overall = {
        planner_key[0]: summarize_group(group_rows)
        for planner_key, group_rows in group_by(rows, ("planner",)).items()
    }
    by_case: dict[str, dict[str, Any]] = {}
    for (case_id, planner), group_rows in group_by(
        rows,
        ("case_id", "planner"),
    ).items():
        by_case.setdefault(str(case_id), {})[str(planner)] = summarize_group(
            group_rows
        )

    by_mask_condition: dict[str, dict[str, Any]] = {}
    for (strategy, intensity, planner), group_rows in group_by(
        rows,
        ("mask_strategy", "mask_intensity", "planner"),
    ).items():
        condition = f"{strategy}|{float(intensity):.3f}"
        by_mask_condition.setdefault(condition, {})[str(planner)] = (
            summarize_group(group_rows)
        )

    return {
        "design": {
            "independent_case_count": len(
                {row["case_id"] for row in rows}
            ),
            "repeated_run_count": len(rows),
        },
        "overall_by_planner": overall,
        "by_case_planner": by_case,
        "by_mask_condition_planner": by_mask_condition,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Project05 MVP simulator.")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--case-dir",
        type=Path,
        help="Directory containing case_config.json, evidence_claims.json, and acquisition_actions.json.",
    )
    input_group.add_argument(
        "--examples-dir",
        type=Path,
        help="Directory containing multiple complete case directories.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
        help="Directory for simulator outputs.",
    )
    args = parser.parse_args()
    if args.examples_dir is not None:
        run_cases(discover_case_dirs(args.examples_dir), args.output_dir)
        return
    case_dir = args.case_dir or (
        Path(__file__).resolve().parents[1] / "examples" / "C01"
    )
    run_all(case_dir, args.output_dir)


if __name__ == "__main__":
    main()
