#!/usr/bin/env python3
"""Runtime allowlist and provenance adapter for Project05 AFA policies."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_PATH = (
    ROOT
    / "09-experiments"
    / "governance"
    / "contracts"
    / "afa-endpoint-contract-v0.1.json"
)
PROFILE_FIELDS = ("profile_id", "version", "sha256", "provenance")


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_contract(path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    raw = path.read_bytes()
    document = json.loads(raw.decode("utf-8"))
    if not isinstance(document, dict):
        raise ValueError("AFA endpoint contract must be a JSON object")
    if document.get("status") != "frozen_for_new_runs":
        raise ValueError("AFA endpoint contract must be frozen_for_new_runs")
    for field in ("contract_id", "version", "planner_visibility"):
        if field not in document:
            raise ValueError(f"AFA endpoint contract is missing {field}")
    return {
        "document": document,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_path": str(path.resolve()),
    }


def _project_mapping(value: Any, fields: list[str]) -> Any:
    allowed = set(fields)
    if isinstance(value, dict):
        return {
            key: copy.deepcopy(item)
            for key, item in value.items()
            if key in allowed
        }
    if isinstance(value, list):
        return [
            _project_mapping(item, fields) if isinstance(item, dict) else copy.deepcopy(item)
            for item in value
        ]
    return copy.deepcopy(value)


def project_section(
    value: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any]:
    allowed = set(spec["top_level_fields"])
    projected = {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key in allowed
    }
    for field, nested_fields in spec.get("nested_fields", {}).items():
        if field in projected:
            projected[field] = _project_mapping(projected[field], nested_fields)
    return projected


def recursive_key_hits(value: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []

    def visit(item: Any, path: str) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                child_path = f"{path}.{key}" if path else str(key)
                if key in forbidden:
                    hits.append(child_path)
                visit(child, child_path)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                visit(child, f"{path}[{index}]")

    visit(value, "")
    return hits


def _validate_profile_identity(identity: dict[str, Any], name: str) -> None:
    if set(identity) != set(PROFILE_FIELDS):
        raise ValueError(
            f"{name} profile identity must contain exactly {PROFILE_FIELDS}"
        )
    for field in ("profile_id", "version", "provenance"):
        if not isinstance(identity[field], str) or not identity[field]:
            raise ValueError(f"{name} profile identity has invalid {field}")
    digest = identity["sha256"]
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(f"{name} profile identity has invalid sha256")


def embedded_profile_identity(
    config: dict[str, Any],
    actions: list[dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, dict[str, str]]:
    cost_basis = [
        {
            "action_id": str(action.get("action_id", "")),
            "cost": float(action.get("cost", 0.0)),
        }
        for action in actions
        if str(action.get("action_id", "")) != "STOP"
        and str(action.get("action_type", "")) != "stop"
    ]
    cost_basis.sort(key=lambda row: row["action_id"])
    prior_basis = {
        "channel_reliability": {
            str(key): float(value)
            for key, value in sorted(
                (config.get("channel_reliability", {}) or {}).items()
            )
        }
    }
    requirements = contract["profile_identity"]
    case_id = str(config.get("case_id", "unknown-case"))
    identities = {
        "cost": {
            "profile_id": f"{case_id}-embedded-legacy-cost",
            "version": "1.0.0",
            "sha256": canonical_sha256(cost_basis),
            "provenance": requirements["cost"]["default_provenance"],
        },
        "prior": {
            "profile_id": f"{case_id}-embedded-channel-prior",
            "version": "1.0.0",
            "sha256": canonical_sha256(prior_basis),
            "provenance": requirements["prior"]["default_provenance"],
        },
    }
    for name, identity in identities.items():
        _validate_profile_identity(identity, name)
        allowed = set(
            contract["profile_identity"][name]["allowed_provenance"]
        )
        if identity["provenance"] not in allowed:
            raise ValueError(
                f"{name} profile provenance is not allowed by the endpoint "
                f"contract: {identity['provenance']!r}"
            )
    return identities


def build_endpoint_view(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    contract_bundle: dict[str, Any] | None = None,
    profile_identity: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    bundle = contract_bundle or load_contract()
    contract = bundle["document"]
    visibility = contract["planner_visibility"]
    projected_config = project_section(config, visibility["config"])
    projected_state = project_section(state, visibility["state"])
    projected_actions = [
        project_section(action, visibility["action"]) for action in actions
    ]
    identities = profile_identity or embedded_profile_identity(
        projected_config,
        projected_actions,
        contract,
    )
    if set(identities) != {"cost", "prior"}:
        raise ValueError("AFA endpoint requires cost and prior profile identities")
    for name, identity in identities.items():
        _validate_profile_identity(identity, name)
        allowed = set(
            contract["profile_identity"][name]["allowed_provenance"]
        )
        if identity["provenance"] not in allowed:
            raise ValueError(
                f"{name} profile provenance is not allowed by the endpoint "
                f"contract: {identity['provenance']!r}"
            )

    view = {
        "contract": {
            "contract_id": contract["contract_id"],
            "version": contract["version"],
            "sha256": bundle["sha256"],
        },
        "profile_identity": copy.deepcopy(identities),
        "config": projected_config,
        "state": projected_state,
        "actions": projected_actions,
    }
    forbidden = set(visibility["recursive_forbidden_keys"])
    hits = recursive_key_hits(view, forbidden)
    if hits:
        raise ValueError(f"AFA endpoint allowlist leaked forbidden keys: {hits}")

    node_ids = {
        str(node.get("node_id", ""))
        for node in projected_config.get("cti_nodes", [])
    }
    for action in projected_actions:
        intended = set(action.get("intended_cti_node_ids", []))
        unknown = sorted(str(node) for node in intended - node_ids)
        if unknown:
            raise ValueError(
                f"Action {action.get('action_id')} declares unknown CTI nodes: {unknown}"
            )
    return view


def case_endpoint_metadata(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    contract_bundle: dict[str, Any] | None = None,
    profile_identity: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    bundle = contract_bundle or load_contract()
    contract = bundle["document"]
    hideable_count = sum(
        "hideable" in set(claim.get("tags", [])) for claim in claims
    )
    identities = profile_identity or embedded_profile_identity(config, actions, contract)
    for name, identity in identities.items():
        _validate_profile_identity(identity, name)
        allowed = set(contract["profile_identity"][name]["allowed_provenance"])
        if identity["provenance"] not in allowed:
            raise ValueError(
                f"{name} profile provenance is not allowed by the endpoint "
                f"contract: {identity['provenance']!r}"
            )
    return {
        "endpoint_contract": {
            "contract_id": contract["contract_id"],
            "version": contract["version"],
            "sha256": bundle["sha256"],
        },
        "profile_identity": identities,
        "missingness": {
            "native_missing": {
                "representation": "not_materialized_as_claim_ids",
                "enumerated_claim_count": None,
                "support_ceiling": config.get("support_ceiling"),
            },
            "experimentally_masked": {
                "eligible_hideable_claim_count": int(hideable_count),
                "mask_strategies": list(config.get("mask_strategies", [])),
                "mask_intensities": list(
                    config.get(
                        "mask_intensities",
                        [config.get("mask_intensity", 0.4)],
                    )
                ),
                "seeds": list(config.get("random_seeds", [])),
                "membership_visible_to_planner": False,
            },
        },
    }
