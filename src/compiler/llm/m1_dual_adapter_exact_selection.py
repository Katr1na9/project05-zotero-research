"""Fail-closed design-level selector for the two frozen M1 adapter contracts.

This module is an executable conformance harness, not an effective registry.
It resolves an exact four-field design record and never imports or invokes an
adapter implementation.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


SURFACE_ID = "project05_depth2_public"
PLANNER_SOURCE_CLASS = "planner_experiment_inputs"
PLANNER_ADAPTER_ID = "m1a_planner_inputs_v0_1"
PLANNER_ADAPTER_VERSION = "0.1.0"
FIXTURE_SOURCE_CLASS = "claim_ir_valid_fixture"
FIXTURE_ADAPTER_ID = "m1a_claim_ir_valid_fixture_v0_1"
FIXTURE_ADAPTER_VERSION = "0.1.0"
INVALID_FIXTURE_SOURCE_CLASS = "claim_ir_authority_leak_or_invalid_fixture"
CERTIFICATE_SOURCE_CLASS = "certificate_experiment_inputs"
SUCCESS_OUTCOME = "OK_DESIGN_LEVEL_SELECTED_ONLY"
DENY_OUTCOME = "FAIL_CLOSED_DENY"

SELECTION_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-dual-adapter-exact-selection-design-v0.1-20260726.json"
)
SELECTION_DESIGN_SHA256 = (
    "ae164d538a0c95a89fafcbd579372332226622d4bbfbe1bf2913529d3cf7694a"
)
RED_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-m1-second-adapter-claim-ir-valid-fixture-red-owner-acceptance-"
    "v0.1-20260726.json"
)
RED_ACCEPTANCE_SHA256 = (
    "0acaa3fb6daaa31f85e24e1f1cd1fdc245de4a4eba6ca56dcf8e30236ab016a3"
)
M1_FRAMEWORK_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-multi-adapter-framework-design-v0.1-20260724.json"
)
M1_FRAMEWORK_SHA256 = (
    "791520b4779f8c0cce12e35cc282bb4c1e7092a9e5d8062c6be67d3a8118cfa2"
)
PLANNER_CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-planner-experiment-inputs-adapter-contract-"
    "v0.1-20260724.json"
)
PLANNER_CONTRACT_SHA256 = (
    "a0627ff3bb4b339336ba0aa1347c90a58a46526cdb84359d03a8e515546c7d98"
)
PLANNER_IMPLEMENTATION_PATH = "src/compiler/llm/m1_planner_inputs_adapter.py"
PLANNER_IMPLEMENTATION_SHA256 = (
    "ae5c6db06a523ef6a4e384a118e1dcff7f0694d2b3f0e6f87a7dc7b2252d67f0"
)
FIXTURE_CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-claim-ir-valid-fixture-adapter-contract-"
    "v0.1-20260726.json"
)
FIXTURE_CONTRACT_SHA256 = (
    "a889a99b7a2bec340221d8cdc25b2b0cbe5f61525539a58e4db4d8214d0e1ebd"
)

_REQUEST_FIELDS = frozenset(
    {"surface_id", "source_class", "adapter_id", "adapter_version"}
)
_EXACT_KEY = ("surface_id", "source_class", "adapter_id", "adapter_version")
_REQUIRED_CASE_IDS = frozenset(
    {
        "SEL-PLANNER-EXACT",
        "SEL-CLAIM-IR-VALID-FIXTURE-EXACT",
        "SEL-WRONG-CLASS-FOR-PLANNER-ID",
        "SEL-WRONG-VERSION",
        "SEL-AMBIGUOUS-DUPLICATE-RECORDS",
        "SEL-IMPLICIT-DEFAULT",
        "SEL-WILDCARD",
        "SEL-CROSS-SURFACE",
        "SEL-CERTIFICATE-CLASS-OUT-OF-SCOPE",
        "SEL-AUTHORITY-LEAK-OR-INVALID-FIXTURE",
    }
)
_WILDCARD_VALUES = frozenset({"*", "any", "default", "latest"})


class M1DualAdapterSelectionError(ValueError):
    """Raised when an exact design-level adapter selection fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.decision = DENY_OUTCOME


def verify_selection_pins(repo_root: Path) -> None:
    """Verify the accepted RED design and every selection dependency."""

    root = repo_root.resolve()
    for relative_path, expected_sha in (
        (SELECTION_DESIGN_PATH, SELECTION_DESIGN_SHA256),
        (RED_ACCEPTANCE_PATH, RED_ACCEPTANCE_SHA256),
        (M1_FRAMEWORK_PATH, M1_FRAMEWORK_SHA256),
        (PLANNER_CONTRACT_PATH, PLANNER_CONTRACT_SHA256),
        (PLANNER_IMPLEMENTATION_PATH, PLANNER_IMPLEMENTATION_SHA256),
        (FIXTURE_CONTRACT_PATH, FIXTURE_CONTRACT_SHA256),
    ):
        _verify_pin(root, relative_path, expected_sha)

    design = _load_json(root / SELECTION_DESIGN_PATH)
    if not isinstance(design, Mapping):
        raise M1DualAdapterSelectionError(
            "selection_design_shape", "selection design must be an object"
        )
    _require_constant(
        design.get("status"),
        "design_only_dual_adapter_registry_not_activated",
        "selection_design.status",
    )
    scope = design.get("scope")
    if (
        not isinstance(scope, Mapping)
        or scope.get("surface_id") != SURFACE_ID
        or scope.get("registry_activation_authorized") is not False
        or scope.get("adapter_execution_authorized") is not False
        or scope.get("planner_single_execute_replay_authorized") is not False
    ):
        raise M1DualAdapterSelectionError(
            "selection_design_boundary",
            "selection scope is not design-only and inactive",
        )

    registry = design.get("design_level_registry")
    if not isinstance(registry, Mapping):
        raise M1DualAdapterSelectionError(
            "selection_design_shape", "design-level registry is missing"
        )
    if (
        registry.get("registry_status") != "DESIGN_ONLY_NOT_ACTIVE"
        or registry.get("registry_activation_authorized") is not False
        or registry.get("active_adapter_count") != 0
        or registry.get("design_record_count") != 2
        or tuple(registry.get("exact_selection_key", ())) != _EXACT_KEY
    ):
        raise M1DualAdapterSelectionError(
            "selection_design_boundary",
            "design-level registry identity or inactive state is not frozen",
        )
    records = registry.get("records")
    if not isinstance(records, list) or len(records) != 2:
        raise M1DualAdapterSelectionError(
            "selection_design_records", "exactly two design records are required"
        )
    _validate_frozen_records(records)

    cases = design.get("selection_cases")
    if not isinstance(cases, list):
        raise M1DualAdapterSelectionError(
            "selection_design_cases", "selection case table is missing"
        )
    case_ids = {
        case.get("case_id")
        for case in cases
        if isinstance(case, Mapping)
    }
    if case_ids != _REQUIRED_CASE_IDS:
        raise M1DualAdapterSelectionError(
            "selection_design_cases", "selection case table is incomplete"
        )
    for case in cases:
        if (
            not isinstance(case, Mapping)
            or case.get("adapter_executed") is not False
            or case.get("expected_outcome")
            not in {SUCCESS_OUTCOME, DENY_OUTCOME}
        ):
            raise M1DualAdapterSelectionError(
                "selection_design_cases",
                "selection cases must be non-executing and fail closed",
            )

    acceptance = _load_json(root / RED_ACCEPTANCE_PATH)
    if not isinstance(acceptance, Mapping):
        raise M1DualAdapterSelectionError(
            "red_acceptance_shape", "RED acceptance must be an object"
        )
    _require_constant(acceptance.get("decision"), "accept", "red_acceptance.decision")
    _require_constant(
        acceptance.get("status"),
        "red_design_accepted_implementation_execution_registry_and_git_not_authorized",
        "red_acceptance.status",
    )
    constraints = acceptance.get("green_constraints_if_later_authorized")
    if not isinstance(constraints, list) or len(constraints) < 7:
        raise M1DualAdapterSelectionError(
            "red_acceptance_boundary", "GREEN constraints are unavailable"
        )


def design_registry_records(repo_root: Path) -> tuple[dict[str, Any], ...]:
    """Return copies of the two frozen design records after pin verification."""

    verify_selection_pins(repo_root)
    design = _load_json(repo_root.resolve() / SELECTION_DESIGN_PATH)
    records = design["design_level_registry"]["records"]
    return tuple(_json_copy(record) for record in records)


def select_adapter(
    request: Mapping[str, Any],
    *,
    repo_root: Path,
    registry_records: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Select exactly one design record without importing or invoking adapters."""

    verify_selection_pins(repo_root)
    _validate_request(request)
    if registry_records is None:
        records: Sequence[Mapping[str, Any]] = design_registry_records(repo_root)
    else:
        if isinstance(registry_records, (str, bytes, bytearray)) or not isinstance(
            registry_records, Sequence
        ):
            raise M1DualAdapterSelectionError(
                "registry_shape", "ephemeral design records must be a sequence"
            )
        records = registry_records

    normalized_records = [_validate_ephemeral_record(record) for record in records]
    matches = [
        record
        for record in normalized_records
        if all(record[field] == request[field] for field in _EXACT_KEY)
    ]
    if len(matches) > 1:
        raise M1DualAdapterSelectionError(
            "ambiguous_selection", "more than one exact design record matched"
        )
    if not matches:
        same_adapter = [
            record for record in normalized_records
            if record["adapter_id"] == request["adapter_id"]
        ]
        if same_adapter and all(
            record["source_class"] != request["source_class"]
            for record in same_adapter
        ):
            code = "wrong_class"
        elif any(
            record["source_class"] == request["source_class"]
            and record["adapter_id"] == request["adapter_id"]
            for record in normalized_records
        ):
            code = "wrong_version"
        else:
            code = "no_exact_match"
        raise M1DualAdapterSelectionError(
            code, "no exact four-field design record matched"
        )

    selected = matches[0]
    return {
        "decision": SUCCESS_OUTCOME,
        "matched_record_id": selected["record_id"],
        "surface_id": request["surface_id"],
        "source_class": request["source_class"],
        "adapter_id": request["adapter_id"],
        "adapter_version": request["adapter_version"],
        "contract_sha256": selected["contract_sha256"],
        "adapter_executed": False,
        "registry_activated": False,
    }


def _validate_request(request: Mapping[str, Any]) -> None:
    if not isinstance(request, Mapping):
        raise M1DualAdapterSelectionError(
            "request_type", "selection request must be an object"
        )
    fields = set(request)
    missing = _REQUEST_FIELDS - fields
    if missing or any(request.get(field) in {None, ""} for field in _REQUEST_FIELDS):
        raise M1DualAdapterSelectionError(
            "implicit_default", "all four exact selection fields are required"
        )
    if fields != _REQUEST_FIELDS:
        raise M1DualAdapterSelectionError(
            "request_shape", "selection request contains unknown fields"
        )
    for field in _EXACT_KEY:
        value = request[field]
        if not isinstance(value, str):
            raise M1DualAdapterSelectionError(
                "request_type", f"{field} must be a string"
            )
        folded = value.casefold()
        if (
            folded in _WILDCARD_VALUES
            or "*" in value
            or "?" in value
            or field == "adapter_version" and any(token in value for token in "<>^~")
        ):
            raise M1DualAdapterSelectionError(
                "wildcard_forbidden", "wildcard, range, latest, and default are forbidden"
            )
    if request["surface_id"] != SURFACE_ID:
        raise M1DualAdapterSelectionError(
            "cross_surface", "only project05_depth2_public is selectable"
        )
    if request["source_class"] == INVALID_FIXTURE_SOURCE_CLASS:
        raise M1DualAdapterSelectionError(
            "authority_leak_deny",
            "authority-leak or invalid fixtures never select a positive adapter",
        )
    if request["source_class"] == CERTIFICATE_SOURCE_CLASS:
        raise M1DualAdapterSelectionError(
            "certificate_out_of_scope",
            "certificate_experiment_inputs is outside this dual design",
        )
    if request["source_class"] not in {
        PLANNER_SOURCE_CLASS,
        FIXTURE_SOURCE_CLASS,
    }:
        raise M1DualAdapterSelectionError(
            "wrong_class", "source class is not present in the dual design"
        )


def _validate_frozen_records(records: Sequence[Mapping[str, Any]]) -> None:
    expected = {
        (
            SURFACE_ID,
            PLANNER_SOURCE_CLASS,
            PLANNER_ADAPTER_ID,
            PLANNER_ADAPTER_VERSION,
            PLANNER_CONTRACT_SHA256,
        ),
        (
            SURFACE_ID,
            FIXTURE_SOURCE_CLASS,
            FIXTURE_ADAPTER_ID,
            FIXTURE_ADAPTER_VERSION,
            FIXTURE_CONTRACT_SHA256,
        ),
    }
    actual = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise M1DualAdapterSelectionError(
                "selection_design_records", "design record must be an object"
            )
        actual.add(
            (
                record.get("surface_id"),
                record.get("source_class"),
                record.get("adapter_id"),
                record.get("adapter_version"),
                record.get("contract_sha256"),
            )
        )
        if record.get("execution_authorized_by_this_design") is not False:
            raise M1DualAdapterSelectionError(
                "selection_design_boundary", "design record grants execution"
            )
    if actual != expected:
        raise M1DualAdapterSelectionError(
            "selection_design_records", "frozen design records do not match contracts"
        )


def _validate_ephemeral_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise M1DualAdapterSelectionError(
            "registry_record_type", "ephemeral record must be an object"
        )
    required = {
        "record_id",
        "surface_id",
        "source_class",
        "adapter_id",
        "adapter_version",
        "contract_sha256",
    }
    if not required.issubset(record):
        raise M1DualAdapterSelectionError(
            "registry_record_shape", "ephemeral record is missing selection fields"
        )
    result = {field: record[field] for field in required}
    if any(not isinstance(result[field], str) for field in required):
        raise M1DualAdapterSelectionError(
            "registry_record_type", "ephemeral record fields must be strings"
        )
    return result


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise M1DualAdapterSelectionError(
            "pin_missing", f"missing pinned artifact: {relative_path}"
        )
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha:
        raise M1DualAdapterSelectionError(
            "pin_mismatch", f"pinned artifact SHA mismatch: {relative_path}"
        )


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise M1DualAdapterSelectionError(
            "json_load", f"cannot load pinned JSON: {path}"
        ) from exc


def _require_constant(value: Any, expected: Any, field: str) -> None:
    if value != expected:
        raise M1DualAdapterSelectionError(
            "pin_contract", f"{field} does not match the accepted design"
        )


def _json_copy(value: Any) -> Any:
    return json.loads(
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    )


class _DuplicateJSONKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result
