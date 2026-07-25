#!/usr/bin/env python3
"""Runtime allowlist adapter for Project05 Depth-2 and ML planners."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_PATH = (
    ROOT
    / "09-experiments"
    / "governance"
    / "contracts"
    / "planner-runtime-contract-v0.1.json"
)


def load_contract(path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    raw = path.read_bytes()
    document = json.loads(raw.decode("utf-8"))
    if not isinstance(document, dict):
        raise ValueError("Planner runtime contract must be a JSON object")
    if document.get("status") != "frozen_for_new_runs":
        raise ValueError("Planner runtime contract must be frozen_for_new_runs")
    for field in ("contract_id", "version", "planner_visibility", "ml_feature_contract"):
        if field not in document:
            raise ValueError(f"Planner runtime contract is missing {field}")
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


def project_section(value: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
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


def load_claim_id_mainline_reference(
    reference_path: Path,
    activation_path: Path,
) -> Any:
    """Load one authorized opaque Claim-ID planner-sidecar import."""

    root_text = str(ROOT)
    inserted_root = root_text not in sys.path
    if inserted_root:
        sys.path.insert(0, root_text)
    try:
        from src.compiler.llm.claim_id_planner_reference_importer import (
            import_claim_id_planner_reference,
        )

        return import_claim_id_planner_reference(
            reference_path,
            repo_root=ROOT,
            activation_path=activation_path,
        )
    finally:
        if inserted_root:
            sys.path.remove(root_text)


def _attach_claim_id_mainline_reference(
    view: dict[str, Any],
    claim_id_reference_import: Any,
    forbidden: set[str],
) -> dict[str, Any]:
    """Attach a validated sidecar outside config/state/action planning inputs."""

    from src.compiler.llm.claim_id_planner_reference_importer import (
        ClaimIDPlannerReferenceImportError,
        validate_authorized_planner_import,
    )

    try:
        provenance = validate_authorized_planner_import(
            claim_id_reference_import,
            repo_root=ROOT,
        )
    except ClaimIDPlannerReferenceImportError as exc:
        raise ValueError(
            "claim_id_mainline_reference requires an authorized planner import"
        ) from exc
    hits = recursive_key_hits(provenance, forbidden)
    if hits:
        raise ValueError(
            f"Claim-ID planner sidecar leaked forbidden keys: {hits}"
        )
    attached = copy.deepcopy(view)
    attached["claim_id_mainline_reference"] = provenance
    return attached


def build_runtime_view(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    contract_bundle: dict[str, Any] | None = None,
    claim_id_reference_import: Any | None = None,
) -> dict[str, Any]:
    bundle = contract_bundle or load_contract()
    contract = bundle["document"]
    visibility = contract["planner_visibility"]
    view = {
        "contract": {
            "contract_id": contract["contract_id"],
            "version": contract["version"],
            "sha256": bundle["sha256"],
        },
        "config": project_section(config, visibility["config"]),
        "state": project_section(state, visibility["state"]),
        "actions": [
            project_section(action, visibility["action"])
            for action in actions
        ],
    }
    forbidden = set(visibility["recursive_forbidden_keys"])
    hits = recursive_key_hits(view, forbidden)
    if hits:
        raise ValueError(f"Planner runtime allowlist leaked forbidden keys: {hits}")
    if claim_id_reference_import is not None:
        view = _attach_claim_id_mainline_reference(
            view,
            claim_id_reference_import,
            forbidden,
        )
    return view


def build_ml_feature_row(
    config: dict[str, Any],
    state: dict[str, Any],
    action: dict[str, Any],
    feature_builder: Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], dict[str, Any]],
    feature_columns: list[str],
    contract_bundle: dict[str, Any] | None = None,
    claim_id_reference_import: Any | None = None,
) -> dict[str, float]:
    bundle = contract_bundle or load_contract()
    frozen_columns = list(bundle["document"]["ml_feature_contract"]["columns"])
    if list(feature_columns) != frozen_columns:
        raise ValueError("ML feature columns do not match the frozen runtime contract")
    view = build_runtime_view(
        config,
        state,
        [action],
        bundle,
        claim_id_reference_import,
    )
    features = feature_builder(view["config"], view["state"], view["actions"][0])
    if set(features) != set(frozen_columns):
        raise ValueError("Runtime feature builder returned fields outside the frozen contract")
    output = {column: float(features[column]) for column in frozen_columns}
    if any(not math.isfinite(value) for value in output.values()):
        raise ValueError("Runtime feature row contains non-finite values")
    return output


def contract_metadata(
    contract_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = contract_bundle or load_contract()
    document = bundle["document"]
    return {
        "contract_id": document["contract_id"],
        "version": document["version"],
        "sha256": bundle["sha256"],
        "runtime_allowlist_enforced": True,
    }
