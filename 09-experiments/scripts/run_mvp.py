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
import hashlib
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
    "project05_m2",
    "project05_m3a_gap_compat",
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
STOP_ACTION_ID = "STOP"
PLANNER_ACTION_FIELDS = frozenset(
    {
        "action_id",
        "case_id",
        "action_type",
        "acquisition_channel",
        "target",
        "cost",
        "cost_breakdown",
        "preconditions",
        "intended_cti_node_ids",
        "expected_evidence_types",
        "expected_stages",
        "expected_effects",
        "status",
        "natural_language_request",
    }
)
PLANNER_STATE_FIELDS = frozenset(
    {
        "case_id",
        "step_index",
        "visible_claim_ids",
        "recovered_claim_ids",
        "matched_cti_node_ids",
        "unmatched_cti_node_ids",
        "matched_cti_edge_ids",
        "unmatched_cti_edge_ids",
        "coverage",
        "alignment_quality",
        "candidate_hypotheses",
        "discriminability",
        "supportable_granularity",
        "granularity_rationale",
        "budget",
        "actions_taken",
        "action_feedback",
        "remaining_action_ids",
        "stop_recommendation",
    }
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
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
    semantics = str(config.get("node_coverage_semantics", "OR")).upper()
    if semantics not in {"OR", "AND"}:
        raise ValueError(f"Unsupported node coverage semantics: {semantics}")
    covered = set()
    for node in config["cti_nodes"]:
        required = set(node["required_claim_ids"])
        is_covered = (
            bool(required & visible_ids)
            if semantics == "OR"
            else bool(required) and required <= visible_ids
        )
        if is_covered:
            covered.add(node["node_id"])
    return covered


def or_covered_node_ids(
    config: dict[str, Any],
    claim_ids: set[str] | list[str],
) -> set[str]:
    """CTI nodes covered under OR semantics by a claim set (e.g. recoverable ids)."""

    visible = set(claim_ids)
    return {
        node["node_id"]
        for node in config["cti_nodes"]
        if set(node["required_claim_ids"]) & visible
    }


def intended_equals_recoverable_or(
    config: dict[str, Any],
    action: dict[str, Any],
) -> bool:
    """True when public intent is an exact answer key for recoverable OR-coverage.

    Empty intent with empty recoverable coverage (noise / STOP-like actions) is
    not treated as a leak. STOP actions are never flagged.
    """

    if is_stop_action(action):
        return False
    intended = set(action.get("intended_cti_node_ids", []))
    covered = or_covered_node_ids(
        config,
        action.get("recoverable_claim_ids", []),
    )
    if not intended and not covered:
        return False
    return intended == covered


def covered_edge_ids(config: dict[str, Any], covered_nodes: set[str]) -> set[str]:
    covered = set()
    for edge in config["cti_edges"]:
        if edge["source"] in covered_nodes and edge["target"] in covered_nodes:
            covered.add(edge["edge_id"])
    return covered


def granularity_thresholds(config: dict[str, Any]) -> dict[str, float]:
    configured = config.get("granularity_thresholds", {})
    thresholds = {
        "g3_node_coverage": float(configured.get("g3_node_coverage", 0.75)),
        "g3_edge_coverage": float(configured.get("g3_edge_coverage", 0.60)),
        "g2_node_coverage": float(configured.get("g2_node_coverage", 0.45)),
        "g2_min_stages": float(configured.get("g2_min_stages", 2)),
        "g1_node_coverage": float(configured.get("g1_node_coverage", 0.15)),
    }
    coverage_keys = (
        "g3_node_coverage",
        "g3_edge_coverage",
        "g2_node_coverage",
        "g1_node_coverage",
    )
    for key in coverage_keys:
        if not 0.0 <= thresholds[key] <= 1.0:
            raise ValueError(f"Granularity threshold {key} must be in [0, 1]")
    if not (
        thresholds["g3_node_coverage"]
        >= thresholds["g2_node_coverage"]
        >= thresholds["g1_node_coverage"]
    ):
        raise ValueError(
            "Node coverage thresholds must satisfy G3 >= G2 >= G1"
        )
    min_stages = thresholds["g2_min_stages"]
    if min_stages < 0 or not min_stages.is_integer():
        raise ValueError("g2_min_stages must be a nonnegative integer")
    return thresholds


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
    thresholds = granularity_thresholds(config)

    if (
        node_cov >= thresholds["g3_node_coverage"]
        and edge_cov >= thresholds["g3_edge_coverage"]
        and critical_covered == len(critical_nodes)
    ):
        structural_granularity = "G3_campaign"
    elif (
        node_cov >= thresholds["g2_node_coverage"]
        and len(stages) >= int(thresholds["g2_min_stages"])
    ):
        structural_granularity = "G2_tactic_intent"
    elif node_cov >= thresholds["g1_node_coverage"]:
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


# Public mapping from acquisition action type to the collection channel / data
# source that fulfils it. The channel is what carries a (documented, pre-
# registered) reliability profile: some channels occasionally return nothing
# even when the underlying evidence exists. This decouples an action's public
# *declared* target (intended_cti_node_ids) from its *realised* recovery, so
# that a planner cannot treat the declaration as a ground-truth answer key.
ACTION_TYPE_CHANNELS: dict[str, str] = {
    "extend_log_window": "log_retention",
    "query_host_subgraph": "host_forensics",
    "recover_network_summary": "network_telemetry",
    "ioc_enrichment": "threat_intel",
    "infrastructure_history": "threat_intel",
    "cti_report_lookup": "threat_intel",
    "malware_analysis": "sample_lab",
    "ttp_local_probe": "host_probe",
    "human_review": "analyst",
    "stop": "decision",
    "other": "other",
}


def is_stop_action(action: dict[str, Any]) -> bool:
    return (
        action.get("action_id") == STOP_ACTION_ID
        or action.get("action_type") == "stop"
    )


def make_stop_action(case_id: str) -> dict[str, Any]:
    """Public zero-cost action that ends acquisition and accepts current granularity."""

    return {
        "action_id": STOP_ACTION_ID,
        "case_id": case_id,
        "action_type": "stop",
        "acquisition_channel": "decision",
        "target": {"target_type": "case", "target_value": case_id},
        "cost": 0,
        "recoverable_claim_ids": [],
        "intended_cti_node_ids": [],
        "expected_evidence_types": [],
        "expected_stages": [],
        "expected_effects": {
            "expected_granularity_gain": 0,
            "expected_uncertainty_reduction": 0,
            "expected_over_attribution_risk_reduction": 0,
            "expected_conflict_resolution": 0,
            "expected_coverage_delta": 0,
        },
        "status": "available",
        "natural_language_request": (
            "Stop acquisition and accept the currently supportable "
            "attribution granularity."
        ),
        "notes": (
            "Public stop/degrade action: ends the episode without recovering "
            "claims. Planners should choose it when continuing is not worth "
            "the remaining budget."
        ),
    }


def ensure_stop_action(
    config: dict[str, Any],
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if any(is_stop_action(action) for action in actions):
        return actions
    return list(actions) + [make_stop_action(config["case_id"])]


def planner_action_view(action: dict[str, Any]) -> dict[str, Any]:
    """Return the allowlisted request-side fields visible to a planner.

    Execution-only fields such as ``recoverable_claim_ids`` and free-form
    implementation notes are deliberately absent. The executor resolves the
    selected action id back to the full action object after planning.
    """

    return {
        key: deepcopy(value)
        for key, value in action.items()
        if key in PLANNER_ACTION_FIELDS
    }


def planner_action_views(
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [planner_action_view(action) for action in actions]


def planner_state_view(state: dict[str, Any]) -> dict[str, Any]:
    """Return the observable state supplied to non-oracle planners.

    Simulator-only fields such as hidden claim ids, mask settings, random
    seeds, and run ids are omitted. Claim references nested under public
    hypotheses or alignment diagnostics are restricted to visible claims.
    """

    public = {
        key: deepcopy(value)
        for key, value in state.items()
        if key in PLANNER_STATE_FIELDS
    }
    visible = set(public.get("visible_claim_ids", []))

    alignment = public.get("alignment_quality")
    if isinstance(alignment, dict):
        for field in ("unexplained_local_claim_ids", "conflict_claim_ids"):
            if field in alignment:
                alignment[field] = [
                    claim_id
                    for claim_id in alignment[field]
                    if claim_id in visible
                ]

    hypotheses = public.get("candidate_hypotheses")
    if isinstance(hypotheses, list):
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                continue
            for field in ("supporting_claim_ids", "contradicting_claim_ids"):
                if field in hypothesis:
                    hypothesis[field] = [
                        claim_id
                        for claim_id in hypothesis[field]
                        if claim_id in visible
                    ]
    return public


def acquisition_channel(action: dict[str, Any]) -> str:
    explicit = action.get("acquisition_channel")
    if explicit:
        return str(explicit)
    return ACTION_TYPE_CHANNELS.get(action.get("action_type", "other"), "other")


def channel_reliability(config: dict[str, Any], channel: str) -> float:
    profile = config.get("channel_reliability", {}) or {}
    return float(profile.get(channel, 1.0))


def channel_is_up(config: dict[str, Any], channel: str, seed: int) -> bool:
    """Deterministically decide whether ``channel`` is online for this episode.

    Reliability ``p`` is the pre-registered probability that the channel
    delivers. Whether it is online in a given episode is a reproducible
    Bernoulli(p) draw keyed on (case_id, channel, seed) so that every planner
    (including the oracle) observes the same realised channel state and results
    stay reproducible across runs and platforms.
    """

    p = channel_reliability(config, channel)
    if p >= 1.0:
        return True
    if p <= 0.0:
        return False
    key = f"{config.get('case_id', '')}|{channel}|{int(seed)}".encode("utf-8")
    draw = int.from_bytes(hashlib.sha256(key).digest()[:8], "big") / float(1 << 64)
    return draw < p


def realized_recovery(
    config: dict[str, Any],
    action: dict[str, Any],
    hidden_ids: set[str],
    seed: int,
) -> set[str]:
    """Claims actually recovered by ``action`` this episode.

    Equal to the hidden claims the action can recover, but only if the action's
    channel is online; a down channel yields nothing even though the evidence
    exists. Backward compatible: when the case declares no ``channel_reliability``
    every channel has p=1.0 and this equals :func:`recoverable_hidden`.
    """

    if not channel_is_up(config, acquisition_channel(action), seed):
        return set()
    return recoverable_hidden(action, hidden_ids)


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


def action_signature(action: dict[str, Any]) -> set[str]:
    target = action.get("target", {})
    signature = {
        f"action_type:{action.get('action_type', '')}",
        f"target_type:{target.get('target_type', '')}",
        f"target_value:{target.get('target_value', '')}",
    }
    signature.update(
        f"evidence_type:{evidence_type}"
        for evidence_type in action.get("expected_evidence_types", [])
    )
    signature.update(
        f"stage:{stage}"
        for stage in action.get("expected_stages", [])
    )
    return signature


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def overlap_waste_cost(
    actions: list[dict[str, Any]],
    actions_taken: list[str],
) -> float:
    action_map = action_by_id(actions)
    prior_signatures: list[set[str]] = []
    waste = 0.0
    for action_id in actions_taken:
        action = action_map[action_id]
        signature = action_signature(action)
        max_overlap = max(
            (
                jaccard(signature, prior_signature)
                for prior_signature in prior_signatures
            ),
            default=0.0,
        )
        waste += float(action["cost"]) * max_overlap
        prior_signatures.append(signature)
    return round(waste, 4)


def m2_action_score(
    action: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
) -> float:
    coverage = state.get("coverage", {})
    stage_coverage = coverage.get("stage_coverage", {})
    evidence_coverage = coverage.get("evidence_type_coverage", {})
    expected_stages = action.get("expected_stages", [])
    expected_evidence_types = action.get("expected_evidence_types", [])

    stage_gap = (
        sum(1.0 - float(stage_coverage.get(stage, 0.0)) for stage in expected_stages)
        / len(expected_stages)
        if expected_stages
        else 0.0
    )
    evidence_gap = (
        sum(
            1.0 - float(evidence_coverage.get(evidence_type, 0.0))
            for evidence_type in expected_evidence_types
        )
        / len(expected_evidence_types)
        if expected_evidence_types
        else 0.0
    )

    action_map = action_by_id(actions)
    candidate_signature = action_signature(action)
    overlap = max(
        (
            jaccard(
                candidate_signature,
                action_signature(action_map[action_id]),
            )
            for action_id in state.get("actions_taken", [])
            if action_id in action_map
        ),
        default=0.0,
    )

    same_type_feedback = [
        feedback
        for feedback in state.get("action_feedback", [])
        if feedback.get("action_type") == action.get("action_type")
    ]
    no_yield_risk = (
        sum(
            1
            for feedback in same_type_feedback
            if int(feedback.get("recovered_count", 0)) == 0
        )
        / len(same_type_feedback)
        if same_type_feedback
        else 0.0
    )
    cost_ratio = float(action["cost"]) / max(
        0.1,
        float(state["budget"]["budget_remaining"]),
    )

    return (
        2.00 * expected_effect(action, "expected_granularity_gain")
        + 1.50 * expected_effect(action, "expected_uncertainty_reduction")
        + 1.50
        * expected_effect(
            action,
            "expected_over_attribution_risk_reduction",
        )
        + 1.50 * stage_gap
        + 1.00 * evidence_gap
        - 1.50 * overlap
        - 1.00 * no_yield_risk
        - 0.75 * cost_ratio
    )


def critical_cti_node_ids(config: dict[str, Any]) -> set[str]:
    return {
        node["node_id"]
        for node in config.get("cti_nodes", [])
        if node.get("critical")
    }


def m3a_gap_compat_score(
    action: dict[str, Any],
    state: dict[str, Any],
    config: dict[str, Any],
) -> float:
    # Break-even utility: continue only when some acquisition action scores > 0.
    if is_stop_action(action):
        return 0.0
    intended_nodes = set(action.get("intended_cti_node_ids", []))
    unmatched_nodes = set(state.get("unmatched_cti_node_ids", []))
    if not intended_nodes or not unmatched_nodes:
        return -float(action["cost"])

    targeted_gaps = intended_nodes & unmatched_nodes
    critical_targets = targeted_gaps & critical_cti_node_ids(config)
    precision = len(targeted_gaps) / max(1, len(intended_nodes))
    recall = len(targeted_gaps) / max(1, len(unmatched_nodes))
    cost = max(0.1, float(action["cost"]))

    return (
        8.0 * len(critical_targets)
        + 3.0 * len(targeted_gaps)
        + 2.0 * precision
        + recall
        - 0.5 * cost
    ) / cost


def oracle_optimal_plan(
    config: dict[str, Any],
    actions: list[dict[str, Any]],
    visible_ids: set[str],
    hidden_ids: set[str],
    seed: int,
    budget_remaining: float,
    actions_taken: list[str] | None = None,
) -> tuple[float, tuple[str, ...]]:
    """Exact min-cost acquisition plan under realised channel states.

    Returns ``(cost, action_id_path)``. Cost is ``math.inf`` when unreachable
    within ``budget_remaining``. Stop actions are ignored (they recover nothing).
    """

    target_idx = granularity_index(config, config["target_granularity"])
    initial_taken = frozenset(actions_taken or [])
    memo: dict[
        tuple[frozenset[str], frozenset[str], float],
        tuple[float, tuple[str, ...]],
    ] = {}

    def search(
        current_visible: frozenset[str],
        current_hidden: frozenset[str],
        taken: frozenset[str],
        remaining: float,
    ) -> tuple[float, tuple[str, ...]]:
        if granularity_index(
            config,
            supportable_granularity(config, set(current_visible)),
        ) >= target_idx:
            return 0.0, ()

        key = (current_hidden, taken, round(remaining, 6))
        if key in memo:
            return memo[key]

        best_cost = math.inf
        best_path: tuple[str, ...] = ()
        for action in actions:
            if is_stop_action(action):
                continue
            action_id = action["action_id"]
            action_cost = float(action["cost"])
            if action_id in taken or action_cost > remaining:
                continue
            if channel_is_up(config, acquisition_channel(action), seed):
                recovered = (
                    set(action["recoverable_claim_ids"]) & set(current_hidden)
                )
            else:
                recovered = set()
            if not recovered:
                continue
            tail_cost, tail_path = search(
                frozenset(set(current_visible) | recovered),
                frozenset(set(current_hidden) - recovered),
                taken | {action_id},
                remaining - action_cost,
            )
            total_cost = action_cost + tail_cost
            path = (action_id,) + tail_path
            if (total_cost, path) < (best_cost, best_path):
                best_cost = total_cost
                best_path = path

        memo[key] = (best_cost, best_path)
        return memo[key]

    return search(
        frozenset(visible_ids),
        frozenset(hidden_ids),
        initial_taken,
        float(budget_remaining),
    )


def select_oracle_optimal_action(
    config: dict[str, Any],
    actions: list[dict[str, Any]],
    visible_ids: set[str],
    hidden_ids: set[str],
    actions_taken: list[str],
    budget_used: float,
    seed: int,
) -> dict[str, Any] | None:
    action_map = action_by_id(actions)
    initial_remaining = float(config["budget_total"]) - budget_used
    _, path = oracle_optimal_plan(
        config,
        actions,
        visible_ids,
        hidden_ids,
        seed,
        initial_remaining,
        actions_taken=actions_taken,
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
    stop = next((action for action in candidates if is_stop_action(action)), None)
    productive = [
        action
        for action in candidates
        if not is_stop_action(action)
        and realized_recovery(config, action, hidden_ids, seed)
    ]
    # No remaining productive recovery under realised channel state: stop.
    if stop is not None and not productive:
        return stop
    if not productive:
        return candidates[0]
    return max(
        productive,
        key=lambda action: (
            len(realized_recovery(config, action, hidden_ids, seed))
            / max(0.1, action["cost"]),
            len(realized_recovery(config, action, hidden_ids, seed)),
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
    if planner != "oracle_optimal":
        actions = planner_action_views(actions)
        state = planner_state_view(state)
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
                int(is_stop_action(action)),
                -action["cost"],
                action["action_id"],
            ),
        )

    if planner == "project05_m1" or planner in M1_ABLATIONS:
        excluded = M1_ABLATIONS.get(planner, set())
        return max(
            candidates,
            key=lambda action: (
                m1_action_score(action, state, excluded),
                int(is_stop_action(action)),
                -action["cost"],
                action["action_id"],
            ),
        )

    if planner == "project05_m2":
        return min(
            candidates,
            key=lambda action: (
                -m2_action_score(action, state, actions),
                -int(is_stop_action(action)),
                action["cost"],
                -len(action.get("expected_stages", [])),
                action["action_id"],
            ),
        )

    if planner == "project05_m3a_gap_compat":
        return max(
            candidates,
            key=lambda action: (
                m3a_gap_compat_score(action, state, config),
                int(is_stop_action(action)),
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
                int(is_stop_action(action)),
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
            seed,
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
    action_selector: Any | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actions = ensure_stop_action(config, actions)
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

        planner_actions = (
            actions
            if planner == "oracle_optimal"
            else planner_action_views(actions)
        )
        planner_state = (
            state
            if planner == "oracle_optimal"
            else planner_state_view(state)
        )
        if action_selector is None:
            selected_action = select_action(
                planner,
                config,
                claims,
                planner_actions,
                planner_state,
                visible_ids,
                hidden_ids if planner == "oracle_optimal" else set(),
                actions_taken,
                seed,
            )
        else:
            selected_action = action_selector(
                config,
                planner_state,
                planner_actions,
            )
        if selected_action is None:
            break
        selected_action_id = selected_action.get("action_id")
        full_action = action_by_id(actions).get(selected_action_id)
        if full_action is None:
            raise ValueError(
                "Planner selected an unknown action_id: "
                f"{selected_action_id!r}"
            )
        action = full_action

        if is_stop_action(action):
            budget_used += float(action["cost"])
            actions_taken.append(action["action_id"])
            action_feedback.append(
                {
                    "action_id": action["action_id"],
                    "action_type": action["action_type"],
                    "recovered_count": 0,
                }
            )
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
                    "acquisition_channel": acquisition_channel(action),
                    "channel_up": 1,
                    "cost": action["cost"],
                    "recovered_claim_ids": [],
                    "explicit_stop": 1,
                    "state": deepcopy(state),
                }
            )
            break

        channel = acquisition_channel(action)
        channel_online = channel_is_up(config, channel, seed)
        recovered = recoverable_hidden(action, hidden_ids) if channel_online else set()
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
                "acquisition_channel": channel,
                "channel_up": int(channel_online),
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
    explicit_stop = int(any(action_id == STOP_ACTION_ID for action_id in actions_taken))
    # Target success, or an explicit stop that stays within the support ceiling
    # (accepting a lower granularity instead of burning budget). Premature stops
    # relative to the oracle are flagged later in add_oracle_relative_metrics.
    correct_target_stop = int(reached and final_idx <= ceiling_idx)
    correct_degrade_stop = int(
        explicit_stop and not reached and final_idx <= ceiling_idx
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
        "explicit_stop": explicit_stop,
        "correct_target_stop": correct_target_stop,
        "correct_degrade_stop": correct_degrade_stop,
        "correct_stop": int(correct_target_stop or correct_degrade_stop),
        "ceiling_violation": int(final_idx > ceiling_idx),
        "cost_to_target": budget_used if reached else "",
        "budget_used": budget_used,
        "steps_to_target": len(actions_taken) if reached else "",
        "steps_taken": len(actions_taken),
        "actions_taken": "|".join(actions_taken),
        "zero_yield_actions": sum(
            feedback["recovered_count"] == 0
            for feedback in action_feedback
            if feedback["action_id"] != STOP_ACTION_ID
        ),
        "overlap_waste_cost": overlap_waste_cost(
            actions,
            [action_id for action_id in actions_taken if action_id != STOP_ACTION_ID],
        ),
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
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def single_case_output_paths(output_dir: Path, case_id: str) -> dict[str, Path]:
    """Return case-specific output paths while retaining the C01 legacy names."""

    prefix = case_id.casefold()
    return {
        "results": output_dir / f"{prefix}_mvp_results.csv",
        "traces": output_dir / f"{prefix}_mvp_traces.json",
        "summary": output_dir / f"{prefix}_mvp_summary.json",
    }


def run_all(case_dir: Path, output_dir: Path) -> None:
    rows, traces = execute_case(case_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    case_id = load_json(case_dir / "case_config.json")["case_id"]
    output_paths = single_case_output_paths(output_dir, case_id)
    write_csv(output_paths["results"], rows)

    write_json(output_paths["traces"], traces)
    summary = summarize(rows)
    write_json(output_paths["summary"], summary)

    print(f"Wrote {output_paths['results']}")
    print(f"Wrote {output_paths['traces']}")
    print(f"Wrote {output_paths['summary']}")
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
            "correct_stop_rate": round(
                sum(int(row.get("correct_stop", 0)) for row in planner_rows)
                / len(planner_rows),
                4,
            ),
            "explicit_stop_rate": round(
                sum(int(row.get("explicit_stop", 0)) for row in planner_rows)
                / len(planner_rows),
                4,
            ),
            "premature_stop_rate": round(
                sum(int(row.get("premature_stop", 0)) for row in planner_rows)
                / len(planner_rows),
                4,
            ),
            "justified_degrade_stop_rate": round(
                sum(int(row.get("justified_degrade_stop", 0)) for row in planner_rows)
                / len(planner_rows),
                4,
            ),
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
        "mean_zero_yield_actions": round(
            sum(float(row.get("zero_yield_actions", 0)) for row in rows)
            / len(rows),
            4,
        ),
        "mean_overlap_waste_cost": round(
            sum(float(row.get("overlap_waste_cost", 0)) for row in rows)
            / len(rows),
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
        "correct_stop_rate": round(
            sum(int(row.get("correct_stop", 0)) for row in rows) / len(rows),
            4,
        ),
        "explicit_stop_rate": round(
            sum(int(row.get("explicit_stop", 0)) for row in rows) / len(rows),
            4,
        ),
        "premature_stop_rate": round(
            sum(int(row.get("premature_stop", 0)) for row in rows) / len(rows),
            4,
        ),
        "justified_degrade_stop_rate": round(
            sum(int(row.get("justified_degrade_stop", 0)) for row in rows)
            / len(rows),
            4,
        ),
        "ceiling_violation_rate": round(
            sum(int(row.get("ceiling_violation", 0)) for row in rows) / len(rows),
            4,
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
            oracle_reached = int(oracle.get("reached_target", 0))
            explicit_stop = int(row.get("explicit_stop", 0))
            reached = int(row.get("reached_target", 0))
            # Stopped short while the oracle still reached the target under the
            # same realised channel state: premature abstention.
            updated["premature_stop"] = int(
                explicit_stop and not reached and oracle_reached == 1
            )
            # Explicit stop when the oracle also failed: justified degrade/abstain.
            updated["justified_degrade_stop"] = int(
                explicit_stop and not reached and oracle_reached == 0
            )
            # Recompute correct_stop with oracle-aware premature filter.
            ceiling_ok = int(row.get("ceiling_violation", 0)) == 0
            updated["correct_degrade_stop"] = int(
                explicit_stop and not reached and ceiling_ok and oracle_reached == 0
            )
            updated["correct_stop"] = int(
                (reached and ceiling_ok)
                or updated["correct_degrade_stop"]
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
