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
    "full_evidence",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


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
) -> set[str]:
    hideable = hideable_claim_ids(claims)
    k = max(1, math.ceil(config.get("mask_intensity", 0.4) * len(hideable)))
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
        return set(stage_hidden[: max(k, len(stage_hidden))])

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
        return "G3_campaign"
    if node_cov >= 0.45 and len(stages) >= 2:
        return "G2_tactic_intent"
    if node_cov >= 0.15:
        return "G1_technique"
    return "G0_unknown"


def build_state(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    run_id: str,
    step_index: int,
    mask_strategy: str,
    seed: int,
    visible_ids: set[str],
    hidden_ids: set[str],
    recovered_ids: set[str],
    actions_taken: list[str],
    budget_used: float,
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
        "mask_intensity": config.get("mask_intensity", 0.4),
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
                len(recoverable_hidden(action, hidden_ids)) / max(0.1, action["cost"]),
                len(recoverable_hidden(action, hidden_ids)),
                -action["cost"],
            ),
        )

    if planner == "project05_m1":
        before_idx = granularity_index(config, state["supportable_granularity"])
        before_cov = state["coverage"]["cti_node_coverage"]
        before_entropy = state["discriminability"]["candidate_entropy"]
        before_critical_gap = state["coverage"]["critical_gap_count"]

        def score(action: dict[str, Any]) -> float:
            recovered = recoverable_hidden(action, hidden_ids)
            after_visible = visible_ids | recovered
            after_state = build_state(
                config,
                claims,
                actions,
                state["run_id"],
                state["step_index"] + 1,
                state["mask_strategy"],
                state["random_seed"],
                after_visible,
                hidden_ids - recovered,
                set(state.get("recovered_claim_ids", [])) | recovered,
                actions_taken + [action["action_id"]],
                state["budget"]["budget_used"] + action["cost"],
            )
            gain = granularity_index(config, after_state["supportable_granularity"]) - before_idx
            coverage_delta = after_state["coverage"]["cti_node_coverage"] - before_cov
            entropy_reduction = max(0.0, before_entropy - after_state["discriminability"]["candidate_entropy"])
            critical_gap_reduction = max(0, before_critical_gap - after_state["coverage"]["critical_gap_count"])
            wasted = 1 if not recovered else 0
            return (
                2.0 * gain
                + 1.5 * coverage_delta
                + 1.0 * entropy_reduction
                + 0.75 * critical_gap_reduction
                - 0.35 * action["cost"]
                - 1.0 * wasted
            )

        return max(candidates, key=lambda action: (score(action), -action["cost"], action["action_id"]))

    raise ValueError(f"Unsupported planner: {planner}")


def run_episode(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    mask_strategy: str,
    seed: int,
    planner: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    all_ids = {claim["claim_id"] for claim in claims}
    hidden_ids = build_hidden_claims(config, claims, mask_strategy, seed)
    visible_ids = all_ids - hidden_ids
    recovered_ids: set[str] = set()
    actions_taken: list[str] = []
    budget_used = 0.0
    run_id = f"{config['case_id']}-{mask_strategy}-{seed}-{planner}"

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
        seed,
        visible_ids,
        hidden_ids,
        recovered_ids,
        actions_taken,
        budget_used,
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
            hidden_ids,
            actions_taken,
            seed,
        )
        if action is None:
            break

        recovered = recoverable_hidden(action, hidden_ids)
        budget_used += action["cost"]
        actions_taken.append(action["action_id"])
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
            seed,
            visible_ids,
            hidden_ids,
            recovered_ids,
            actions_taken,
            budget_used,
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
    initial_direct_over_attr = (
        granularity_index(config, config["target_granularity"])
        > granularity_index(config, initial_state["supportable_granularity"])
    )
    result = {
        "case_id": config["case_id"],
        "mask_strategy": mask_strategy,
        "seed": seed,
        "planner": planner,
        "target_granularity": config["target_granularity"],
        "initial_granularity": initial_state["supportable_granularity"],
        "final_granularity": final_state["supportable_granularity"],
        "reached_target": int(reached),
        "cost_to_target": budget_used if reached else "",
        "budget_used": budget_used,
        "steps_to_target": len(actions_taken) if reached else "",
        "steps_taken": len(actions_taken),
        "actions_taken": "|".join(actions_taken),
        "initial_hidden_claims": len(build_hidden_claims(config, claims, mask_strategy, seed)) if planner != "full_evidence" else 0,
        "recovered_claims": len(recovered_ids),
        "final_node_coverage": round(final_state["coverage"]["cti_node_coverage"], 4),
        "final_edge_coverage": round(final_state["coverage"]["cti_edge_coverage"], 4),
        "final_critical_gap_count": final_state["coverage"]["critical_gap_count"],
        "initial_direct_over_attribution": int(initial_direct_over_attr),
    }
    return result, trace


def run_all(case_dir: Path, output_dir: Path) -> None:
    config = load_json(case_dir / "case_config.json")
    claims = load_json(case_dir / "evidence_claims.json")
    actions = load_json(case_dir / "acquisition_actions.json")

    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for mask_strategy in config["mask_strategies"]:
        for seed in config["random_seeds"]:
            for planner in PLANNERS:
                row, trace = run_episode(config, claims, actions, mask_strategy, seed, planner)
                rows.append(row)
                traces.append(
                    {
                        "run_id": f"{config['case_id']}-{mask_strategy}-{seed}-{planner}",
                        "result": row,
                        "trace": trace,
                    }
                )

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "c01_mvp_results.csv"
    fieldnames = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    write_json(output_dir / "c01_mvp_traces.json", traces)
    summary = summarize(rows)
    write_json(output_dir / "c01_mvp_summary.json", summary)

    print(f"Wrote {csv_path}")
    print(f"Wrote {output_dir / 'c01_mvp_traces.json'}")
    print(f"Wrote {output_dir / 'c01_mvp_summary.json'}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Project05 C01 MVP simulator.")
    parser.add_argument(
        "--case-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "examples" / "C01",
        help="Directory containing case_config.json, evidence_claims.json, and acquisition_actions.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
        help="Directory for simulator outputs.",
    )
    args = parser.parse_args()
    run_all(args.case_dir, args.output_dir)


if __name__ == "__main__":
    main()
