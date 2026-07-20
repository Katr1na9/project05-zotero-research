#!/usr/bin/env python3
"""Outcome-agnostic action-construction gate for CAM-LDS final-blind cases.

The public inventory is a fixed eight-slot interface.  Only
``recoverable_claim_ids`` is bound after the public inventory has been sealed.
No command, archive member, record locator, or ATT&CK mapping is permitted in a
planner-visible action field.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE_PATH = Path(
    "04-progress/m3star-final-blind-data-intake-v0.1-20260719/"
    "cam-lds-action-construction-contract-v0.3.json"
)
CONTRACT_ID = "project05-cam-lds-action-construction-contract-v0.3"
PENDING_RELIABILITY_STATUS = "pending_independent_executor_calibration"
FROZEN_RELIABILITY_STATUS = "frozen_independent_executor_calibration"
EXPECTED_EFFECTS_RULE_ID = "outcome_agnostic_neutral_zero_v1"
EXPECTED_EFFECT_FIELDS = (
    "expected_granularity_gain",
    "expected_uncertainty_reduction",
    "expected_over_attribution_risk_reduction",
    "expected_conflict_resolution",
    "expected_coverage_delta",
)
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
OUTCOME_BINDING_FIELDS = ("recoverable_claim_ids",)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def planner_action_view(action: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in action.items()
        if key in PLANNER_ACTION_FIELDS
    }


def planner_inventory(actions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [planner_action_view(action) for action in actions]


def planner_inventory_sha256(actions: Sequence[Mapping[str, Any]]) -> str:
    return canonical_sha256(planner_inventory(actions))


def instantiate_public_actions(
    case_id: str,
    public_cti_node_ids: Sequence[str],
) -> list[dict[str, Any]]:
    """Instantiate the fixed public rows without accepting any outcome input."""

    contract, _path, _digest = load_contract()
    if case_id not in contract["case_scope"]["eligible_case_ids"]:
        raise ValueError(f"Case {case_id} is outside the CAM-LDS contract scope")
    node_ids = sorted(str(value) for value in public_cti_node_ids)
    if not node_ids or any(not value for value in node_ids):
        raise ValueError("public_cti_node_ids must contain non-empty values")
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("public_cti_node_ids must be unique")
    neutral_effects = {field: 0.0 for field in EXPECTED_EFFECT_FIELDS}
    actions: list[dict[str, Any]] = []
    for index, slot in enumerate(contract["fixed_public_slot_templates"], start=1):
        actions.append(
            {
                "action_id": f"{case_id}-AA-{index:03d}",
                "case_id": case_id,
                "action_type": slot["action_type"],
                "acquisition_channel": slot["acquisition_channel"],
                "target": {
                    "target_type": "case",
                    "target_value": f"{case_id}:scope:{index:02d}",
                },
                "cost": None,
                "intended_cti_node_ids": node_ids,
                "expected_evidence_types": list(slot["expected_evidence_types"]),
                "expected_effects": deepcopy(neutral_effects),
                "status": "available",
                "natural_language_request": slot["natural_language_request"],
            }
        )
    return actions


def make_construction_metadata(
    public_actions: Sequence[Mapping[str, Any]],
    private_executor_map_sha256: str,
) -> dict[str, Any]:
    """Create the public seal metadata; the private map remains undisclosed."""

    _contract, _path, contract_sha256 = load_contract()
    _require_sha256(private_executor_map_sha256, "private_executor_map_sha256")
    return {
        "contract_id": CONTRACT_ID,
        "contract_sha256": contract_sha256,
        "expected_effects_rule_id": EXPECTED_EFFECTS_RULE_ID,
        "public_inventory_sealed_before_outcome_binding": True,
        "outcome_binding_fields": list(OUTCOME_BINDING_FIELDS),
        "private_executor_map_sha256": private_executor_map_sha256,
        "planner_visible_inventory_sha256": planner_inventory_sha256(public_actions),
    }


def bind_recoverable_claims(
    public_actions: Sequence[Mapping[str, Any]],
    recoverable_by_action: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Bind hidden outcomes without permitting public-row changes."""

    before = planner_inventory_sha256(public_actions)
    bound: list[dict[str, Any]] = []
    observed_ids: set[str] = set()
    for raw_action in public_actions:
        action = deepcopy(dict(raw_action))
        action_id = str(action.get("action_id", ""))
        if not action_id or action_id in observed_ids:
            raise ValueError("Public actions must have unique non-empty action ids")
        observed_ids.add(action_id)
        claims = recoverable_by_action.get(action_id)
        if claims is None:
            raise ValueError(f"Missing recoverable-claim binding for {action_id}")
        normalized = [str(value) for value in claims]
        if any(not value for value in normalized) or len(normalized) != len(
            set(normalized)
        ):
            raise ValueError(f"Invalid recoverable-claim binding for {action_id}")
        action["recoverable_claim_ids"] = normalized
        bound.append(action)
    unknown = sorted(set(recoverable_by_action) - observed_ids)
    if unknown:
        raise ValueError(f"Bindings reference unknown action ids: {unknown}")
    if planner_inventory_sha256(bound) != before:
        raise AssertionError("Outcome binding changed the planner-visible inventory")
    return bound


def load_contract() -> tuple[dict[str, Any], Path, str]:
    path = REPO_ROOT / CONTRACT_RELATIVE_PATH
    document = json.loads(path.read_text(encoding="utf-8"))
    digest = sha256_file(path)
    if document.get("contract_id") != CONTRACT_ID:
        raise ValueError("CAM-LDS action-construction contract id mismatch")
    if document.get("status") != "frozen_before_case_reconstruction":
        raise ValueError("CAM-LDS action-construction contract is not frozen")
    pinned_scripts = document.get("pinned_scripts")
    if not isinstance(pinned_scripts, list) or not pinned_scripts:
        raise ValueError("CAM-LDS action-construction contract pins no scripts")
    for index, entry in enumerate(pinned_scripts):
        if not isinstance(entry, dict):
            raise ValueError(f"pinned_scripts[{index}] must be an object")
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"pinned_scripts[{index}].path is invalid")
        pinned_path = (REPO_ROOT / relative).resolve()
        try:
            pinned_path.relative_to(REPO_ROOT)
        except ValueError as exc:
            raise ValueError(f"pinned_scripts[{index}].path escapes the repository") from exc
        if not pinned_path.is_file() or expected != sha256_file(pinned_path):
            raise ValueError(f"Pinned action-construction script hash mismatch: {relative}")
    return document, path, digest


def _require_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 value")
    return value


def _require_unique_strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValueError(f"{field} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} must contain unique strings")
    return list(value)


def _claim_to_nodes(
    config: Mapping[str, Any],
    claim_ids: set[str],
) -> dict[str, set[str]]:
    result = {claim_id: set() for claim_id in claim_ids}
    nodes = config.get("cti_nodes")
    if not isinstance(nodes, list):
        raise ValueError("case_config.cti_nodes must be an array")
    for index, raw_node in enumerate(nodes):
        if not isinstance(raw_node, dict):
            raise ValueError(f"case_config.cti_nodes[{index}] must be an object")
        node_id = raw_node.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            raise ValueError(f"case_config.cti_nodes[{index}].node_id is invalid")
        required = _require_unique_strings(
            raw_node.get("required_claim_ids"),
            f"case_config.cti_nodes[{index}].required_claim_ids",
        )
        for claim_id in required:
            if claim_id in result:
                result[claim_id].add(node_id)
    return result


def _validate_neutral_effects(action: Mapping[str, Any], action_id: str) -> None:
    effects = action.get("expected_effects")
    if not isinstance(effects, dict) or set(effects) != set(EXPECTED_EFFECT_FIELDS):
        raise ValueError(
            f"Action {action_id} expected_effects must exactly match the frozen fields"
        )
    for field in EXPECTED_EFFECT_FIELDS:
        value = effects[field]
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
            or float(value) != 0.0
        ):
            raise ValueError(
                f"Action {action_id} {field} must be zero under the neutral prior"
            )


def validate_cam_lds_action_construction(
    config: Mapping[str, Any],
    claims: Sequence[Mapping[str, Any]],
    actions: Sequence[Mapping[str, Any]],
    *,
    require_frozen_action_calibration: bool = False,
) -> dict[str, Any]:
    contract, _contract_path, contract_sha256 = load_contract()
    case_id = config.get("case_id")
    eligible = contract.get("case_scope", {}).get("eligible_case_ids", [])
    if case_id not in eligible:
        raise ValueError(f"Case {case_id} is outside the frozen CAM-LDS contract scope")

    construction = config.get("action_construction")
    if not isinstance(construction, dict):
        raise ValueError("case_config.action_construction must be an object")
    if construction.get("contract_id") != CONTRACT_ID:
        raise ValueError("case_config action-construction contract id mismatch")
    if construction.get("contract_sha256") != contract_sha256:
        raise ValueError("case_config action-construction contract SHA-256 mismatch")
    if construction.get("expected_effects_rule_id") != EXPECTED_EFFECTS_RULE_ID:
        raise ValueError("case_config expected-effects rule differs from the contract")
    if construction.get("public_inventory_sealed_before_outcome_binding") is not True:
        raise ValueError("Public action inventory was not sealed before outcome binding")
    if construction.get("outcome_binding_fields") != list(OUTCOME_BINDING_FIELDS):
        raise ValueError("Only recoverable_claim_ids may be bound after public sealing")
    _require_sha256(
        construction.get("private_executor_map_sha256"),
        "case_config.action_construction.private_executor_map_sha256",
    )

    slots = contract.get("fixed_public_slot_templates")
    if not isinstance(slots, list) or len(actions) != len(slots):
        raise ValueError(
            f"CAM-LDS action inventory must contain exactly {len(slots or [])} slots"
        )
    node_ids = _require_unique_strings(
        [node.get("node_id") for node in config.get("cti_nodes", [])],
        "case_config.cti node ids",
    )
    all_node_ids = sorted(node_ids)
    claim_ids = {
        str(claim.get("claim_id"))
        for claim in claims
        if isinstance(claim, dict) and claim.get("claim_id")
    }
    claim_to_nodes = _claim_to_nodes(config, claim_ids)

    positive_action_count = 0
    zero_yield_action_count = 0
    covered_claim_ids: set[str] = set()
    for index, (raw_action, slot) in enumerate(zip(actions, slots)):
        if not isinstance(raw_action, dict) or not isinstance(slot, dict):
            raise ValueError(f"Action slot {index} is malformed")
        action = raw_action
        slot_number = index + 1
        expected_action_id = f"{case_id}-AA-{slot_number:03d}"
        action_id = action.get("action_id")
        if action_id != expected_action_id:
            raise ValueError(
                f"CAM-LDS slot {slot_number} action id must be {expected_action_id}"
            )
        expected_target = {
            "target_type": "case",
            "target_value": f"{case_id}:scope:{slot_number:02d}",
        }
        exact_public_fields = {
            "action_id": expected_action_id,
            "case_id": case_id,
            "action_type": slot.get("action_type"),
            "acquisition_channel": slot.get("acquisition_channel"),
            "target": expected_target,
            "cost": None,
            "intended_cti_node_ids": all_node_ids,
            "expected_evidence_types": slot.get("expected_evidence_types"),
            "expected_effects": {field: 0.0 for field in EXPECTED_EFFECT_FIELDS},
            "status": "available",
            "natural_language_request": slot.get("natural_language_request"),
        }
        if planner_action_view(action) != exact_public_fields:
            raise ValueError(
                f"Action {action_id} planner-visible row differs from its frozen slot template"
            )
        _validate_neutral_effects(action, str(action_id))
        recoverable = set(
            _require_unique_strings(
                action.get("recoverable_claim_ids"),
                f"Action {action_id} recoverable_claim_ids",
            )
        )
        unknown = sorted(recoverable - claim_ids)
        if unknown:
            raise ValueError(f"Action {action_id} has unknown recoverable claims: {unknown}")
        covered_claim_ids.update(recoverable)
        recovered_nodes: set[str] = set()
        for claim_id in recoverable:
            recovered_nodes.update(claim_to_nodes.get(claim_id, set()))
        if recoverable:
            positive_action_count += 1
        else:
            zero_yield_action_count += 1
        if set(all_node_ids) == recovered_nodes:
            raise ValueError(
                f"Action {action_id} declared intent equals its hidden recovered-node set"
            )

    if covered_claim_ids != claim_ids:
        missing = sorted(claim_ids - covered_claim_ids)
        raise ValueError(f"CAM-LDS action inventory leaves claims uncovered: {missing}")
    minimum_zero = int(contract["outcome_binding_gates"]["minimum_zero_yield_actions"])
    minimum_positive = int(contract["outcome_binding_gates"]["minimum_positive_actions"])
    if zero_yield_action_count < minimum_zero:
        raise ValueError(
            f"CAM-LDS inventory requires at least {minimum_zero} zero-yield actions"
        )
    if positive_action_count < minimum_positive:
        raise ValueError(
            f"CAM-LDS inventory requires at least {minimum_positive} positive actions"
        )

    observed_inventory_sha256 = planner_inventory_sha256(actions)
    if construction.get("planner_visible_inventory_sha256") != observed_inventory_sha256:
        raise ValueError("Planner-visible action inventory differs from its prebinding seal")

    expected_channels = {
        str(slot["acquisition_channel"]) for slot in slots if isinstance(slot, dict)
    }
    reliability = config.get("channel_reliability")
    if not isinstance(reliability, dict) or set(reliability) != expected_channels:
        raise ValueError("case_config.channel_reliability keys differ from action channels")
    reliability_status = config.get("channel_reliability_status")
    calibration_frozen = reliability_status == FROZEN_RELIABILITY_STATUS
    if reliability_status == PENDING_RELIABILITY_STATUS:
        if any(value is not None for value in reliability.values()):
            raise ValueError("Pending channel reliability values must remain null")
    elif calibration_frozen:
        for channel, value in reliability.items():
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(float(value))
                or not 0.0 <= float(value) <= 1.0
            ):
                raise ValueError(f"Frozen reliability for {channel} is invalid")
        _require_sha256(
            config.get("channel_reliability_profile_sha256"),
            "case_config.channel_reliability_profile_sha256",
        )
    else:
        raise ValueError("Unknown channel_reliability_status")
    if require_frozen_action_calibration and not calibration_frozen:
        raise ValueError("Final-blind action-channel calibration is still pending")

    return {
        "action_construction_contract_id": CONTRACT_ID,
        "action_construction_contract_sha256": contract_sha256,
        "planner_visible_inventory_sha256": observed_inventory_sha256,
        "planner_visible_inventory_matches_prebinding_seal": True,
        "outcome_binding_changes_public_rows": False,
        "positive_action_count": positive_action_count,
        "zero_yield_action_count": zero_yield_action_count,
        "action_inventory_contains_only_successes": False,
        "intended_nodes_equal_recovered_nodes_count": 0,
        "expected_effects_rule_id": EXPECTED_EFFECTS_RULE_ID,
        "legacy_expert_prior_used": False,
        "channel_reliability_status": reliability_status,
        "channel_reliability_calibration_frozen": calibration_frozen,
        "action_calibration_required_by_this_run": require_frozen_action_calibration,
    }
