#!/usr/bin/env python3
"""Static, outcome-free validation for reconstructed C13+ case bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


CASE_FILENAMES = (
    "case_config.json",
    "evidence_claims.json",
    "acquisition_actions.json",
)
CASE_ID_PATTERN = re.compile(r"^C0*(?:1[3-9]|[2-9][0-9]|[1-9][0-9]{2,})(?:-|$)")
EXPECTED_CONDITION_COUNT = 45
EXPECTED_EFFECT_FIELDS = (
    "expected_granularity_gain",
    "expected_uncertainty_reduction",
    "expected_over_attribution_risk_reduction",
    "expected_conflict_resolution",
    "expected_coverage_delta",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_array(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def require_finite_number(value: Any, field: str, *, positive: bool = False) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"{field} must be a finite number")
    numeric = float(value)
    if positive and numeric <= 0:
        raise ValueError(f"{field} must be positive")
    return numeric


def require_unique_strings(values: Any, field: str, *, nonempty: bool = True) -> list[str]:
    array = require_array(values, field)
    strings = [
        require_nonempty_string(item, f"{field}[{index}]")
        for index, item in enumerate(array)
    ]
    if nonempty and not strings:
        raise ValueError(f"{field} must not be empty")
    if len(strings) != len(set(strings)):
        raise ValueError(f"{field} must contain unique strings")
    return strings


def ensure_acyclic(node_ids: set[str], edges: list[dict[str, Any]]) -> None:
    outgoing = {node_id: set() for node_id in node_ids}
    indegree = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        source = str(edge["source"])
        target = str(edge["target"])
        if target not in outgoing[source]:
            outgoing[source].add(target)
            indegree[target] += 1
    ready = [node_id for node_id, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        current = ready.pop()
        visited += 1
        for target in outgoing[current]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    if visited != len(node_ids):
        raise ValueError("case_config.cti_edges must form an acyclic attack chain")


def validate_case_bundle(
    case_dir: Path,
    expected_case_id: str | None = None,
) -> dict[str, Any]:
    case_dir = case_dir.resolve()
    for filename in CASE_FILENAMES:
        path = case_dir / filename
        if not path.is_file():
            raise ValueError(f"Missing required case file: {path}")

    config = require_object(load_json(case_dir / CASE_FILENAMES[0]), "case_config")
    claims = require_array(load_json(case_dir / CASE_FILENAMES[1]), "evidence_claims")
    actions = require_array(
        load_json(case_dir / CASE_FILENAMES[2]),
        "acquisition_actions",
    )

    case_id = require_nonempty_string(config.get("case_id"), "case_config.case_id")
    if CASE_ID_PATTERN.match(case_id) is None:
        raise ValueError("case_config.case_id must be a C13+ final-blind identifier")
    if expected_case_id is not None and case_id != expected_case_id:
        raise ValueError(
            f"Case id differs from expected assignment: {case_id} != {expected_case_id}"
        )
    if case_dir.name != case_id:
        raise ValueError("Case directory name must exactly match case_config.case_id")
    if config.get("development_only") is not False:
        raise ValueError("Final-blind case_config.development_only must be false")

    mask_intensities = require_array(
        config.get("mask_intensities"),
        "case_config.mask_intensities",
    )
    if not mask_intensities or any(
        not 0 < require_finite_number(
            value,
            f"case_config.mask_intensities[{index}]",
        ) < 1
        for index, value in enumerate(mask_intensities)
    ):
        raise ValueError("Mask intensities must be unique values strictly between 0 and 1")
    if len({float(value) for value in mask_intensities}) != len(mask_intensities):
        raise ValueError("case_config.mask_intensities must be unique")
    mask_strategies = require_unique_strings(
        config.get("mask_strategies"),
        "case_config.mask_strategies",
    )
    random_seeds = require_array(config.get("random_seeds"), "case_config.random_seeds")
    if (
        not random_seeds
        or any(not isinstance(seed, int) or isinstance(seed, bool) for seed in random_seeds)
        or len(random_seeds) != len(set(random_seeds))
    ):
        raise ValueError("case_config.random_seeds must be unique integers")
    condition_count = len(mask_intensities) * len(mask_strategies) * len(random_seeds)
    if condition_count != EXPECTED_CONDITION_COUNT:
        raise ValueError(
            f"Final-blind case must define exactly {EXPECTED_CONDITION_COUNT} "
            f"within-case conditions, observed {condition_count}"
        )
    require_finite_number(config.get("budget_total"), "case_config.budget_total", positive=True)

    claim_ids: list[str] = []
    hideable_claim_count = 0
    for index, raw_claim in enumerate(claims):
        claim = require_object(raw_claim, f"evidence_claims[{index}]")
        claim_id = require_nonempty_string(
            claim.get("claim_id"),
            f"evidence_claims[{index}].claim_id",
        )
        if claim.get("case_id") != case_id:
            raise ValueError(f"Claim {claim_id} case_id mismatch")
        pointer = require_object(
            claim.get("source_pointer"),
            f"evidence_claims[{index}].source_pointer",
        )
        for field in ("artifact_id", "location", "record_id"):
            require_nonempty_string(
                pointer.get(field),
                f"evidence_claims[{index}].source_pointer.{field}",
            )
        require_unique_strings(
            claim.get("mapped_tactic"),
            f"evidence_claims[{index}].mapped_tactic",
        )
        tags = require_unique_strings(
            claim.get("tags"),
            f"evidence_claims[{index}].tags",
        )
        hideable_claim_count += "hideable" in tags
        claim_ids.append(claim_id)
    if not claim_ids:
        raise ValueError("evidence_claims must not be empty")
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("evidence_claims contains duplicate claim_id values")
    if hideable_claim_count == 0:
        raise ValueError("At least one claim must be eligible for evidence masking")
    claim_id_set = set(claim_ids)

    nodes = require_array(config.get("cti_nodes"), "case_config.cti_nodes")
    node_ids: list[str] = []
    referenced_claim_ids: set[str] = set()
    critical_node_count = 0
    for index, raw_node in enumerate(nodes):
        node = require_object(raw_node, f"case_config.cti_nodes[{index}]")
        node_id = require_nonempty_string(
            node.get("node_id"),
            f"case_config.cti_nodes[{index}].node_id",
        )
        require_nonempty_string(
            node.get("stage"),
            f"case_config.cti_nodes[{index}].stage",
        )
        required_claim_ids = require_unique_strings(
            node.get("required_claim_ids"),
            f"case_config.cti_nodes[{index}].required_claim_ids",
            nonempty=False,
        )
        unknown = sorted(set(required_claim_ids) - claim_id_set)
        if unknown:
            raise ValueError(f"CTI node {node_id} references unknown claims: {unknown}")
        referenced_claim_ids.update(required_claim_ids)
        critical_node_count += node.get("critical") is True
        node_ids.append(node_id)
    if not node_ids or len(node_ids) != len(set(node_ids)):
        raise ValueError("case_config.cti_nodes must be non-empty with unique node ids")
    if critical_node_count == 0:
        raise ValueError("At least one CTI node must be marked critical")
    node_id_set = set(node_ids)

    raw_edges = require_array(config.get("cti_edges"), "case_config.cti_edges")
    edges: list[dict[str, Any]] = []
    edge_ids: list[str] = []
    for index, raw_edge in enumerate(raw_edges):
        edge = require_object(raw_edge, f"case_config.cti_edges[{index}]")
        edge_id = require_nonempty_string(
            edge.get("edge_id"),
            f"case_config.cti_edges[{index}].edge_id",
        )
        source = require_nonempty_string(
            edge.get("source"),
            f"case_config.cti_edges[{index}].source",
        )
        target = require_nonempty_string(
            edge.get("target"),
            f"case_config.cti_edges[{index}].target",
        )
        if source not in node_id_set or target not in node_id_set:
            raise ValueError(f"CTI edge {edge_id} references an unknown node")
        if source == target:
            raise ValueError(f"CTI edge {edge_id} is a self-loop")
        edges.append(edge)
        edge_ids.append(edge_id)
    if len(edge_ids) != len(set(edge_ids)):
        raise ValueError("case_config.cti_edges contains duplicate edge ids")
    ensure_acyclic(node_id_set, edges)

    action_ids: list[str] = []
    action_recoverable_claim_ids: set[str] = set()
    action_channels: set[str] = set()
    for index, raw_action in enumerate(actions):
        action = require_object(raw_action, f"acquisition_actions[{index}]")
        action_id = require_nonempty_string(
            action.get("action_id"),
            f"acquisition_actions[{index}].action_id",
        )
        if action.get("case_id") != case_id:
            raise ValueError(f"Action {action_id} case_id mismatch")
        require_nonempty_string(
            action.get("action_type"),
            f"acquisition_actions[{index}].action_type",
        )
        channel = require_nonempty_string(
            action.get("acquisition_channel"),
            f"acquisition_actions[{index}].acquisition_channel",
        )
        action_channels.add(channel)
        require_finite_number(
            action.get("cost"),
            f"acquisition_actions[{index}].cost",
            positive=True,
        )
        recoverable = require_unique_strings(
            action.get("recoverable_claim_ids"),
            f"acquisition_actions[{index}].recoverable_claim_ids",
            nonempty=False,
        )
        unknown_claims = sorted(set(recoverable) - claim_id_set)
        if unknown_claims:
            raise ValueError(
                f"Action {action_id} references unknown recoverable claims: "
                f"{unknown_claims}"
            )
        action_recoverable_claim_ids.update(recoverable)
        intended_nodes = require_unique_strings(
            action.get("intended_cti_node_ids"),
            f"acquisition_actions[{index}].intended_cti_node_ids",
            nonempty=False,
        )
        unknown_nodes = sorted(set(intended_nodes) - node_id_set)
        if unknown_nodes:
            raise ValueError(
                f"Action {action_id} references unknown intended nodes: {unknown_nodes}"
            )
        effects = require_object(
            action.get("expected_effects"),
            f"acquisition_actions[{index}].expected_effects",
        )
        for field in EXPECTED_EFFECT_FIELDS:
            require_finite_number(
                effects.get(field),
                f"acquisition_actions[{index}].expected_effects.{field}",
            )
        target = require_object(
            action.get("target"),
            f"acquisition_actions[{index}].target",
        )
        for field in ("target_type", "target_value"):
            require_nonempty_string(
                target.get(field),
                f"acquisition_actions[{index}].target.{field}",
            )
        require_nonempty_string(
            action.get("natural_language_request"),
            f"acquisition_actions[{index}].natural_language_request",
        )
        action_ids.append(action_id)
    if not action_ids or len(action_ids) != len(set(action_ids)):
        raise ValueError(
            "acquisition_actions must be non-empty with unique action_id values"
        )
    uncovered_claims = sorted(claim_id_set - action_recoverable_claim_ids)
    if uncovered_claims:
        raise ValueError(
            "Every evidence claim must be recoverable by at least one action: "
            f"{uncovered_claims}"
        )
    fixed_order = require_unique_strings(
        config.get("fixed_action_order"),
        "case_config.fixed_action_order",
    )
    if set(fixed_order) != set(action_ids):
        raise ValueError(
            "case_config.fixed_action_order must contain every action exactly once"
        )
    channel_reliability = require_object(
        config.get("channel_reliability"),
        "case_config.channel_reliability",
    )
    if set(channel_reliability) != action_channels:
        raise ValueError(
            "case_config.channel_reliability keys must exactly match action channels"
        )
    for channel, value in channel_reliability.items():
        reliability = require_finite_number(
            value,
            f"case_config.channel_reliability.{channel}",
        )
        if not 0 <= reliability <= 1:
            raise ValueError("Channel reliability values must be between 0 and 1")

    discriminative_claim_ids = require_unique_strings(
        config.get("discriminative_claim_ids"),
        "case_config.discriminative_claim_ids",
        nonempty=False,
    )
    unknown_discriminative = sorted(set(discriminative_claim_ids) - claim_id_set)
    if unknown_discriminative:
        raise ValueError(
            "case_config.discriminative_claim_ids references unknown claims: "
            f"{unknown_discriminative}"
        )
    require_unique_strings(
        config.get("stage_mask_tags"),
        "case_config.stage_mask_tags",
    )

    return {
        "case_id": case_id,
        "condition_count": condition_count,
        "claim_count": len(claim_ids),
        "hideable_claim_count": hideable_claim_count,
        "cti_node_count": len(node_ids),
        "critical_cti_node_count": critical_node_count,
        "cti_edge_count": len(edge_ids),
        "action_count": len(action_ids),
        "claims_referenced_by_required_nodes_count": len(referenced_claim_ids),
        "all_claims_recoverable": True,
        "reference_closure_pass": True,
        "case_files_sha256": {
            filename: sha256(case_dir / filename) for filename in CASE_FILENAMES
        },
        "case_contents_opened_for_structural_validation": True,
        "case_contents_returned_in_report": False,
        "planner_or_model_executed": False,
        "planner_or_model_outputs_opened": False,
        "one_shot_evaluation_consumed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", type=Path, action="append", required=True)
    parser.add_argument("--expected-case-id", action="append")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    expected = args.expected_case_id
    if expected is not None and len(expected) != len(args.case_dir):
        raise ValueError("--expected-case-id count must match --case-dir count")
    case_reports = [
        validate_case_bundle(
            case_dir,
            None if expected is None else expected[index],
        )
        for index, case_dir in enumerate(args.case_dir)
    ]
    report = {
        "status": "final_blind_case_bundle_static_validation_passed",
        "case_count": len(case_reports),
        "case_ids": [item["case_id"] for item in case_reports],
        "cases": case_reports,
        "all_reference_closures_pass": True,
        "case_contents_opened_for_structural_validation": True,
        "case_contents_returned_in_report": False,
        "planner_or_model_executed": False,
        "planner_or_model_outputs_opened": False,
        "one_shot_evaluation_consumed": False,
    }
    if args.output is not None:
        write_json(args.output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
