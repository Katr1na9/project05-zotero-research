"""Test-only A17-P1e deterministic depth-1 planning contract.

This module classifies one next-action candidate from a frozen finite world
set.  It performs no action execution, observation sampling, system-state
derivation, mint, admission, write, certificate, or STOP operation.

``SELECT_ACTION`` is candidacy metadata only.  It must not be interpreted as
L2 PASS, Part B PASS, unrestricted Part B elevation, or execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
from math import gcd
from pathlib import Path
import re
from typing import Any

import yaml

from src.actions.selection import DistinguishingActionSelector
from src.ir.canonical_hash import canonical_json, canonical_value_hash


PRODUCTION_REGISTRATION_ENABLED = False
ACTION_EXECUTION_ENABLED = False
SYSTEM_STATE_AUTHORITY = False
STOP_AUTHORITY = False

REQUEST_SCHEMA_VERSION = "kernel-a17-p1e-depth1-planner-request-v0.1"
DECISION_SCHEMA_VERSION = "kernel-a17-p1e-depth1-planner-decision-v0.1"
RECEIPT_SCHEMA_VERSION = (
    "kernel-a17-p1e-resource-trace-binding-receipt-v0.1"
)
PLANNER_MODE = "M3-KERNEL-D1"
REQUEST_KIND = "CLASSIFY_NEXT_ACTION_DEPTH_1"
EXECUTION_MODE = "READONLY_DECISION_ONLY_NO_ACTION_EXECUTION"
DECISION_SCOPE = "NEXT_ACTION_CANDIDACY_ONLY_NO_EXECUTE_NO_STOP"
PARTITION_BASIS = "FROZEN_MODEL_PROJECTION_NOT_OBSERVED_TRUTH"
TIE_BREAK_RULE = (
    "MAX_EXACT_WORLD_REDUCTION_THEN_UTF8_ACTION_ID_ASC_V0_1"
)
TRACE_MATCH_POLICY = (
    "EXACT_ATTEMPT_ACTION_DECISION_BUDGET_HASH_MATCH_NO_FALLBACK"
)
HARD_BAN = (
    "Path A / Kernel design GREEN must not be inferred as L2 PASS, "
    "Part B PASS, or unrestricted Part B elevation."
)

SELECT_ACTION = "SELECT_ACTION"
ABSTAIN_NO_ACTION = "ABSTAIN_NO_FORMALLY_ELIGIBLE_ACTION"
ABSTAIN_NO_VALUE = "ABSTAIN_NO_POSITIVE_EXPECTED_REDUCTION"
ABSTAIN_SINGLETON = "ABSTAIN_ALREADY_SINGLETON_NO_ACQUISITION"
ABSTAIN_BUDGET = "ABSTAIN_RESOURCE_BUDGET_EXHAUSTED"
DENY = "DENY_INVALID_OR_UNAUTHORIZED_INPUT"

REQUEST_FIELD_ORDER = (
    "schema_version",
    "request_kind",
    "planner_mode",
    "execution_mode",
    "case_binding",
    "finite_domain_binding",
    "checker_binding",
    "counterexample_binding",
    "action_catalog_binding",
    "p4_selection_binding",
    "deterministic_outcome_partitions",
    "resource_budget_declaration",
    "requested_decision_scope",
    "request_hash",
)
REQUEST_FIELDS = frozenset(REQUEST_FIELD_ORDER)

DECISION_FIELD_ORDER = (
    "schema_version",
    "record_class",
    "planner_mode",
    "decision",
    "reason_codes",
    "request_hash",
    "input_bindings",
    "current_u_summary",
    "eligible_action_ids",
    "action_value_table",
    "selected_action_id",
    "tie_break",
    "resource_trace_binding",
    "authority_ceiling",
    "probability_model",
    "planning_confidence",
    "record_hash",
)
DECISION_FIELDS = frozenset(DECISION_FIELD_ORDER)

TRACE_INPUT_FIELDS = frozenset(
    {
        "attempt_id",
        "action_id",
        "planner_decision_record_hash",
        "resource_budget_hash",
        "status",
        "counts",
        "resources",
    }
)
RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "record_class",
        "planner_decision_record_hash",
        "attempt_id",
        "action_id",
        "resource_budget_hash",
        "trace_row_sha256",
        "match_status",
        "reason_codes",
        "receipt_hash",
    }
)

_CASE_FIELDS = frozenset(
    {"case_id", "gamma_hash", "evidence_hash", "compilation_profile"}
)
_FINITE_FIELDS = frozenset(
    {
        "compiled_legal_world_count",
        "compiled_legal_worlds_hash",
        "compiled_legal_world_ids",
        "current_u_count",
        "current_u_hash",
        "current_u_world_ids",
        "target_variable",
    }
)
_CHECKER_FIELDS = frozenset(
    {
        "checker_run_hash",
        "checker_status",
        "base_status",
        "support_status",
        "alternative_status",
        "support_world_id",
        "alternative_world_id",
    }
)
_COUNTEREXAMPLE_FIELDS = frozenset(
    {
        "counterexample_id",
        "counterexample_hash",
        "target_level",
        "distinguishing_predicates",
        "distinguishing_predicates_hash",
    }
)
_CATALOG_FIELDS = frozenset(
    {
        "schema_version",
        "catalog_id",
        "catalog_version",
        "declared_catalog_hash",
        "catalog_content_sha256",
        "catalog_path",
        "reference_mode",
    }
)
_P4_FIELDS = frozenset(
    {"selection_record_hash", "allowed_action_ids", "forbidden_action_ids"}
)
_PARTITION_FIELDS = frozenset(
    {
        "action_id",
        "observation_model_hash",
        "projection_rule_id",
        "output_domain",
        "partition_basis",
        "world_outcomes",
        "partition_hash",
    }
)
_WORLD_OUTCOME_FIELDS = frozenset({"world_id", "outcome"})
_BUDGET_FIELDS = frozenset(
    {
        "budget_id",
        "budget_hash",
        "as_of_state_hash",
        "budget_policy",
        "hard_limits",
        "consumed",
        "remaining",
        "budget_status",
    }
)
_BUDGET_DIMENSIONS = (
    "wall_seconds",
    "cpu_seconds",
    "records_scanned",
    "bytes_scanned",
    "analyst_seconds",
)
_BUDGET_DIMENSION_SET = frozenset(_BUDGET_DIMENSIONS)

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_PLAIN_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_FORBIDDEN_HIDDEN_KEYS = frozenset(
    {
        "actual_world_id",
        "ground_truth",
        "true_outcome",
        "recoverable_claim_ids",
        "hidden_claim_ids",
        "oracle_effects",
        "posterior",
        "probability",
        "confidence",
        "planning_confidence",
    }
)
_FORBIDDEN_AUTHORITY_KEYS = frozenset(
    {
        "requested_system_state",
        "system_status",
        "stop",
        "stop_authority",
        "certificate",
        "certificate_authority",
        "mint",
        "admission",
        "kernel_write",
        "e_case_write",
        "part_b_pass",
        "execution_authority",
    }
)
_FORBIDDEN_AUTHORITY_VALUES = frozenset(
    {
        "CERTIFIED_STOP",
        "PART_B_PASS",
        "L2_PASS",
        "MINT",
        "ADMIT",
        "EXECUTE",
        "KERNEL_WRITE",
        "E_CASE_WRITE",
    }
)
_REPO_ROOT = Path(__file__).resolve().parents[2]


class _ContractViolation(ValueError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class _ValidatedRequest:
    request: Mapping[str, Any]
    request_hash: str
    case: Mapping[str, Any]
    finite: Mapping[str, Any]
    checker: Mapping[str, Any]
    counterexample: Mapping[str, Any]
    catalog_binding: Mapping[str, Any]
    p4: Mapping[str, Any]
    partitions: tuple[Mapping[str, Any], ...]
    budget: Mapping[str, Any]
    catalog: Mapping[str, Any]
    actions_by_id: Mapping[str, Mapping[str, Any]]
    allowed_action_ids: tuple[str, ...]
    forbidden_action_ids: tuple[str, ...]
    current_u_world_ids: tuple[str, ...]
    required_budget_dimensions: tuple[str, ...]


def canonical_hash_without_field(
    document: Mapping[str, Any], field: str
) -> str:
    """Hash canonical JSON after removing exactly one top-level field."""

    if not isinstance(document, Mapping):
        raise ValueError("document must be an object")
    payload = deepcopy(dict(document))
    payload.pop(field, None)
    return canonical_value_hash(payload)


def evaluate_depth1_planner_request(
    request: Mapping[str, Any] | object,
) -> dict[str, object]:
    """Return an exact seventeen-field decision record without side effects."""

    computed_request_hash = _safe_request_hash(request)
    try:
        validated = _validate_request(request)
        values = _calculate_action_values(validated)
        return _decide(validated, values)
    except _ContractViolation as exc:
        return _decision_record(
            request=request,
            request_hash=computed_request_hash,
            decision=DENY,
            reason_codes=[exc.reason_code],
            input_bindings=_safe_input_bindings(request),
            current_u_summary=_safe_current_u_summary(request),
            eligible_action_ids=[],
            action_value_table=[],
            selected_action_id=None,
            tie_break=None,
            resource_trace_binding=None,
        )
    except (TypeError, ValueError, OSError, yaml.YAMLError):
        return _decision_record(
            request=request,
            request_hash=computed_request_hash,
            decision=DENY,
            reason_codes=["P1E-001_CLOSED_WORLD_REQUEST_SHAPE"],
            input_bindings=_safe_input_bindings(request),
            current_u_summary=_safe_current_u_summary(request),
            eligible_action_ids=[],
            action_value_table=[],
            selected_action_id=None,
            tie_break=None,
            resource_trace_binding=None,
        )


def validate_resource_trace_binding(
    decision_record: Mapping[str, Any] | object,
    trace_row: Mapping[str, Any] | object,
) -> dict[str, object]:
    """Return a pure test-only receipt; never execute or rewrite the trace."""

    reason_codes: list[str] = []
    decision_hash = _safe_record_hash(decision_record)
    expected_attempt: object = None
    expected_action: object = None
    expected_budget: object = None

    if (
        not isinstance(decision_record, Mapping)
        or set(decision_record) != DECISION_FIELDS
        or decision_record.get("decision") != SELECT_ACTION
        or decision_record.get("record_hash") != decision_hash
        or not isinstance(decision_record.get("resource_trace_binding"), Mapping)
    ):
        reason_codes.append(
            "P1E-020_TRACE_DECISION_OR_BUDGET_HASH_MISMATCH"
        )
    else:
        binding = decision_record["resource_trace_binding"]
        expected_attempt = binding.get("attempt_id")
        expected_action = decision_record.get("selected_action_id")
        expected_budget = binding.get("resource_budget_hash")

    trace_hash = _safe_trace_hash(trace_row)
    trace_attempt: object = None
    trace_action: object = None
    trace_decision_hash: object = None
    trace_budget: object = None
    if not isinstance(trace_row, Mapping) or set(trace_row) != TRACE_INPUT_FIELDS:
        reason_codes.append("P1E-018_TRACE_ATTEMPT_ID_MISMATCH")
    else:
        trace_attempt = trace_row.get("attempt_id")
        trace_action = trace_row.get("action_id")
        trace_decision_hash = trace_row.get("planner_decision_record_hash")
        trace_budget = trace_row.get("resource_budget_hash")
        if trace_attempt != expected_attempt:
            reason_codes.append("P1E-018_TRACE_ATTEMPT_ID_MISMATCH")
        if trace_action != expected_action:
            reason_codes.append("P1E-019_TRACE_ACTION_ID_MISMATCH")
        if (
            trace_decision_hash != decision_hash
            or trace_budget != expected_budget
        ):
            reason_codes.append(
                "P1E-020_TRACE_DECISION_OR_BUDGET_HASH_MISMATCH"
            )

    match_status = (
        "MATCH_TEST_ONLY_REPLAY"
        if not reason_codes
        else "DENY_TRACE_BINDING_MISMATCH"
    )
    receipt: dict[str, object] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "record_class": "kernel_a17_p1e_resource_trace_binding_receipt",
        "planner_decision_record_hash": (
            trace_decision_hash
            if isinstance(trace_decision_hash, str)
            else decision_hash
        ),
        "attempt_id": (
            trace_attempt if isinstance(trace_attempt, str) else None
        ),
        "action_id": (
            trace_action if isinstance(trace_action, str) else None
        ),
        "resource_budget_hash": (
            trace_budget if isinstance(trace_budget, str) else None
        ),
        "trace_row_sha256": trace_hash,
        "match_status": match_status,
        "reason_codes": reason_codes,
        "receipt_hash": "",
    }
    receipt["receipt_hash"] = canonical_hash_without_field(
        receipt, "receipt_hash"
    )
    if set(receipt) != RECEIPT_FIELDS:
        raise AssertionError("receipt shape drift")
    return receipt


def _validate_request(
    request: Mapping[str, Any] | object,
) -> _ValidatedRequest:
    if not isinstance(request, Mapping):
        raise _ContractViolation("P1E-001_CLOSED_WORLD_REQUEST_SHAPE")
    if _contains_key(request, _FORBIDDEN_HIDDEN_KEYS):
        raise _ContractViolation("P1E-007_HIDDEN_OR_ORACLE_FIELD")
    if _contains_authority_request(request):
        raise _ContractViolation(
            "P1E-013_AUTHORITY_OR_STOP_REQUEST_FORBIDDEN"
        )
    if set(request) != REQUEST_FIELDS:
        raise _ContractViolation("P1E-001_CLOSED_WORLD_REQUEST_SHAPE")
    if (
        request.get("schema_version") != REQUEST_SCHEMA_VERSION
        or request.get("request_kind") != REQUEST_KIND
        or request.get("planner_mode") != PLANNER_MODE
        or request.get("execution_mode") != EXECUTION_MODE
        or request.get("requested_decision_scope") != DECISION_SCOPE
    ):
        raise _ContractViolation("P1E-002_SCOPE_OR_MODE_MISMATCH")

    request_hash = canonical_hash_without_field(request, "request_hash")
    if request.get("request_hash") != request_hash:
        raise _ContractViolation("P1E-003_STALE_OR_MISMATCHED_HASH")

    case = _exact_mapping(
        request.get("case_binding"),
        _CASE_FIELDS,
        "P1E-001_CLOSED_WORLD_REQUEST_SHAPE",
    )
    for field in ("case_id", "compilation_profile"):
        _nonempty_string(case.get(field), "P1E-001_CLOSED_WORLD_REQUEST_SHAPE")
    for field in ("gamma_hash", "evidence_hash"):
        _canonical_sha(case.get(field), "P1E-003_STALE_OR_MISMATCHED_HASH")

    finite = _validate_finite_binding(request.get("finite_domain_binding"))
    checker = _validate_checker_binding(
        request.get("checker_binding"), finite
    )
    counterexample = _validate_counterexample_binding(
        request.get("counterexample_binding")
    )
    checker_worlds = (
        finite["current_u_world_ids"]
        if finite["current_u_count"] > 1
        else finite["compiled_legal_world_ids"]
    )
    if (
        counterexample["target_level"] != finite["target_variable"]
        or checker["support_world_id"] == checker["alternative_world_id"]
        or checker["support_world_id"] not in checker_worlds
        or checker["alternative_world_id"] not in checker_worlds
    ):
        raise _ContractViolation(
            "P1E-005_CHECKER_COUNTEREXAMPLE_BINDING_INVALID"
        )

    catalog_binding, catalog, actions_by_id = _validate_catalog_binding(
        request.get("action_catalog_binding")
    )
    p4, allowed, forbidden = _validate_p4_binding(
        request.get("p4_selection_binding"),
        counterexample,
        catalog,
    )
    partitions = _validate_partitions(
        request.get("deterministic_outcome_partitions"),
        allowed,
        finite["current_u_world_ids"],
        counterexample["distinguishing_predicates"],
        actions_by_id,
    )
    required_dimensions = _required_budget_dimensions(
        allowed, actions_by_id
    )
    budget = _validate_budget(
        request.get("resource_budget_declaration"),
        required_dimensions,
    )

    return _ValidatedRequest(
        request=request,
        request_hash=request_hash,
        case=case,
        finite=finite,
        checker=checker,
        counterexample=counterexample,
        catalog_binding=catalog_binding,
        p4=p4,
        partitions=partitions,
        budget=budget,
        catalog=catalog,
        actions_by_id=actions_by_id,
        allowed_action_ids=allowed,
        forbidden_action_ids=forbidden,
        current_u_world_ids=tuple(finite["current_u_world_ids"]),
        required_budget_dimensions=required_dimensions,
    )


def _validate_finite_binding(value: object) -> Mapping[str, Any]:
    finite = _exact_mapping(
        value, _FINITE_FIELDS, "P1E-004_FINITE_DOMAIN_BINDING_INVALID"
    )
    compiled = _sorted_unique_strings(
        finite.get("compiled_legal_world_ids"),
        "P1E-004_FINITE_DOMAIN_BINDING_INVALID",
        nonempty=True,
    )
    current = _sorted_unique_strings(
        finite.get("current_u_world_ids"),
        "P1E-004_FINITE_DOMAIN_BINDING_INVALID",
        nonempty=True,
    )
    if not set(current).issubset(compiled):
        raise _ContractViolation(
            "P1E-004_FINITE_DOMAIN_BINDING_INVALID"
        )
    if (
        finite.get("compiled_legal_world_count") != len(compiled)
        or finite.get("current_u_count") != len(current)
        or finite.get("current_u_hash") != canonical_value_hash(list(current))
    ):
        raise _ContractViolation(
            "P1E-004_FINITE_DOMAIN_BINDING_INVALID"
        )
    _canonical_sha(
        finite.get("compiled_legal_worlds_hash"),
        "P1E-003_STALE_OR_MISMATCHED_HASH",
    )
    _nonempty_string(
        finite.get("target_variable"),
        "P1E-004_FINITE_DOMAIN_BINDING_INVALID",
    )
    return finite


def _validate_checker_binding(
    value: object, finite: Mapping[str, Any]
) -> Mapping[str, Any]:
    checker = _exact_mapping(
        value,
        _CHECKER_FIELDS,
        "P1E-005_CHECKER_COUNTEREXAMPLE_BINDING_INVALID",
    )
    _canonical_sha(
        checker.get("checker_run_hash"),
        "P1E-003_STALE_OR_MISMATCHED_HASH",
    )
    if checker.get("checker_run_hash") != canonical_hash_without_field(
        checker, "checker_run_hash"
    ):
        raise _ContractViolation("P1E-003_STALE_OR_MISMATCHED_HASH")
    if (
        checker.get("checker_status") != "COUNTEREXAMPLE_FOUND"
        or checker.get("base_status") != "SAT"
        or checker.get("support_status") != "SAT"
        or checker.get("alternative_status") != "SAT"
    ):
        raise _ContractViolation(
            "P1E-005_CHECKER_COUNTEREXAMPLE_BINDING_INVALID"
        )
    for field in ("support_world_id", "alternative_world_id"):
        _nonempty_string(
            checker.get(field),
            "P1E-005_CHECKER_COUNTEREXAMPLE_BINDING_INVALID",
        )
    return checker


def _validate_counterexample_binding(
    value: object,
) -> Mapping[str, Any]:
    counterexample = _exact_mapping(
        value,
        _COUNTEREXAMPLE_FIELDS,
        "P1E-005_CHECKER_COUNTEREXAMPLE_BINDING_INVALID",
    )
    for field in ("counterexample_id", "target_level"):
        _nonempty_string(
            counterexample.get(field),
            "P1E-005_CHECKER_COUNTEREXAMPLE_BINDING_INVALID",
        )
    _canonical_sha(
        counterexample.get("counterexample_hash"),
        "P1E-003_STALE_OR_MISMATCHED_HASH",
    )
    predicates = _sorted_unique_strings(
        counterexample.get("distinguishing_predicates"),
        "P1E-005_CHECKER_COUNTEREXAMPLE_BINDING_INVALID",
        nonempty=True,
    )
    if counterexample.get(
        "distinguishing_predicates_hash"
    ) != canonical_value_hash(list(predicates)):
        raise _ContractViolation("P1E-003_STALE_OR_MISMATCHED_HASH")
    return counterexample


def _validate_catalog_binding(
    value: object,
) -> tuple[Mapping[str, Any], Mapping[str, Any], dict[str, Mapping[str, Any]]]:
    binding = _exact_mapping(
        value, _CATALOG_FIELDS, "P1E-006_CATALOG_NOT_EXACT"
    )
    if binding.get("reference_mode") != "EXACT_PATH_AND_HASH_NO_WILDCARD":
        raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT")
    relative_path = _nonempty_string(
        binding.get("catalog_path"), "P1E-006_CATALOG_NOT_EXACT"
    )
    if (
        "://" in relative_path
        or any(token in relative_path for token in ("*", "?", "[", "]"))
        or Path(relative_path).is_absolute()
    ):
        raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT")
    path = (_REPO_ROOT / relative_path).resolve()
    try:
        path.relative_to(_REPO_ROOT)
    except ValueError as exc:
        raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT") from exc
    if not path.is_file():
        raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT")
    raw = path.read_bytes()
    content_digest = hashlib.sha256(raw).hexdigest()
    if (
        not isinstance(binding.get("catalog_content_sha256"), str)
        or _PLAIN_SHA256.fullmatch(binding["catalog_content_sha256"]) is None
        or binding["catalog_content_sha256"] != content_digest
    ):
        raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT")
    catalog = yaml.safe_load(raw.decode("utf-8"))
    if not isinstance(catalog, Mapping):
        raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT")
    declared = catalog.get("hash")
    computed = canonical_hash_without_field(catalog, "hash")
    if (
        binding.get("schema_version") != catalog.get("schema_version")
        or binding.get("catalog_id") != catalog.get("catalog_id")
        or binding.get("catalog_version") != catalog.get("catalog_version")
        or binding.get("declared_catalog_hash") != declared
        or declared != computed
    ):
        raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT")
    raw_actions = catalog.get("actions")
    if not isinstance(raw_actions, Sequence) or isinstance(
        raw_actions, (str, bytes)
    ):
        raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT")
    actions: dict[str, Mapping[str, Any]] = {}
    for raw_action in raw_actions:
        if not isinstance(raw_action, Mapping):
            raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT")
        action_id = raw_action.get("action_id")
        if (
            not isinstance(action_id, str)
            or _IDENTIFIER.fullmatch(action_id) is None
            or action_id in actions
        ):
            raise _ContractViolation("P1E-006_CATALOG_NOT_EXACT")
        actions[action_id] = raw_action
    return binding, catalog, actions


def _validate_p4_binding(
    value: object,
    counterexample: Mapping[str, Any],
    catalog: Mapping[str, Any],
) -> tuple[Mapping[str, Any], tuple[str, ...], tuple[str, ...]]:
    p4 = _exact_mapping(
        value, _P4_FIELDS, "P1E-011_P4_SELECTION_BINDING_INVALID"
    )
    allowed = _sorted_unique_strings(
        p4.get("allowed_action_ids"),
        "P1E-011_P4_SELECTION_BINDING_INVALID",
        nonempty=False,
    )
    forbidden = _sorted_unique_strings(
        p4.get("forbidden_action_ids"),
        "P1E-011_P4_SELECTION_BINDING_INVALID",
        nonempty=False,
    )
    if set(allowed).intersection(forbidden):
        raise _ContractViolation(
            "P1E-011_P4_SELECTION_BINDING_INVALID"
        )
    minimal_counterexample = {
        "checker_status": "COUNTEREXAMPLE_FOUND",
        "target_level": counterexample["target_level"],
        "distinguishing_predicates": list(
            counterexample["distinguishing_predicates"]
        ),
    }
    try:
        result = DistinguishingActionSelector().select(
            minimal_counterexample, catalog
        )
    except ValueError as exc:
        raise _ContractViolation(
            "P1E-011_P4_SELECTION_BINDING_INVALID"
        ) from exc
    expected_allowed = tuple(result.allowed_actions)
    expected_forbidden = tuple(sorted(result.forbidden_actions))
    selection_payload = {
        "allowed_actions": list(expected_allowed),
        "forbidden_actions": list(expected_forbidden),
        "catalog_actions_examined": result.catalog_actions_examined,
    }
    if (
        allowed != expected_allowed
        or forbidden != expected_forbidden
        or p4.get("selection_record_hash")
        != canonical_value_hash(selection_payload)
    ):
        raise _ContractViolation(
            "P1E-011_P4_SELECTION_BINDING_INVALID"
        )
    return p4, allowed, forbidden


def _validate_partitions(
    value: object,
    allowed: tuple[str, ...],
    current_worlds: Sequence[str],
    distinguishing_predicates: Sequence[str],
    actions_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise _ContractViolation("P1E-010_OUTCOME_PARTITION_INVALID")
    partitions = tuple(value)
    by_action: dict[str, Mapping[str, Any]] = {}
    for raw_partition in partitions:
        partition = _exact_mapping(
            raw_partition,
            _PARTITION_FIELDS,
            "P1E-010_OUTCOME_PARTITION_INVALID",
        )
        action_id = partition.get("action_id")
        if not isinstance(action_id, str) or action_id in by_action:
            raise _ContractViolation(
                "P1E-010_OUTCOME_PARTITION_INVALID"
            )
        by_action[action_id] = partition
    if set(by_action) != set(allowed):
        raise _ContractViolation("P1E-010_OUTCOME_PARTITION_INVALID")

    validated: list[Mapping[str, Any]] = []
    predicate_set = set(distinguishing_predicates)
    for action_id in allowed:
        action = actions_by_id.get(action_id)
        if action is None:
            raise _ContractViolation(
                "P1E-011_P4_SELECTION_BINDING_INVALID"
            )
        model = action.get("observation_model")
        if not isinstance(model, Mapping):
            raise _ContractViolation("P1E-008_OBSERVATION_MODEL_MISSING")
        if model.get("noise_model") != "deterministic":
            raise _ContractViolation(
                "P1E-009_STOCHASTIC_OBSERVATION_MODEL"
            )
        partition = by_action[action_id]
        if partition.get("partition_basis") != PARTITION_BASIS:
            if "STOCHASTIC" in str(partition.get("partition_basis", "")):
                raise _ContractViolation(
                    "P1E-009_STOCHASTIC_OBSERVATION_MODEL"
                )
            raise _ContractViolation(
                "P1E-010_OUTCOME_PARTITION_INVALID"
            )
        if partition.get("observation_model_hash") != canonical_value_hash(
            model
        ):
            raise _ContractViolation(
                "P1E-003_STALE_OR_MISMATCHED_HASH"
            )
        if partition.get("projection_rule_id") != model.get(
            "projection_rule_id"
        ):
            raise _ContractViolation(
                "P1E-010_OUTCOME_PARTITION_INVALID"
            )
        output_domain = model.get("output_domain")
        if (
            not isinstance(output_domain, Sequence)
            or isinstance(output_domain, (str, bytes))
            or partition.get("output_domain") != list(output_domain)
        ):
            raise _ContractViolation(
                "P1E-010_OUTCOME_PARTITION_INVALID"
            )
        dependencies = model.get("world_dependencies")
        state_effect = action.get("state_effect")
        if (
            not isinstance(dependencies, Sequence)
            or isinstance(dependencies, (str, bytes))
            or not predicate_set.intersection(dependencies)
            or not isinstance(state_effect, Mapping)
            or not state_effect.get("world_elimination_rule_ids")
            or action.get("formal_analysis_eligibility") != "formal"
            or not isinstance(action.get("authority"), Mapping)
            or action["authority"].get("current_status") != "executable"
            or not isinstance(action.get("feasibility"), Mapping)
            or action["feasibility"].get("status") != "executable"
        ):
            raise _ContractViolation(
                "P1E-011_P4_SELECTION_BINDING_INVALID"
            )
        rows = partition.get("world_outcomes")
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise _ContractViolation(
                "P1E-010_OUTCOME_PARTITION_INVALID"
            )
        world_ids: list[str] = []
        for row in rows:
            item = _exact_mapping(
                row,
                _WORLD_OUTCOME_FIELDS,
                "P1E-010_OUTCOME_PARTITION_INVALID",
            )
            world_id = item.get("world_id")
            if not isinstance(world_id, str):
                raise _ContractViolation(
                    "P1E-010_OUTCOME_PARTITION_INVALID"
                )
            world_ids.append(world_id)
            if item.get("outcome") not in output_domain:
                raise _ContractViolation(
                    "P1E-010_OUTCOME_PARTITION_INVALID"
                )
        if world_ids != list(current_worlds) or len(set(world_ids)) != len(
            world_ids
        ):
            raise _ContractViolation(
                "P1E-010_OUTCOME_PARTITION_INVALID"
            )
        if partition.get("partition_hash") != canonical_hash_without_field(
            partition, "partition_hash"
        ):
            raise _ContractViolation("P1E-003_STALE_OR_MISMATCHED_HASH")
        validated.append(partition)
    return tuple(validated)


def _required_budget_dimensions(
    allowed: Sequence[str],
    actions_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    required = {"wall_seconds", "records_scanned", "bytes_scanned"}
    for action_id in allowed:
        instrumentation = actions_by_id[action_id].get(
            "resource_instrumentation"
        )
        if not isinstance(instrumentation, Mapping):
            raise _ContractViolation(
                "P1E-011_P4_SELECTION_BINDING_INVALID"
            )
        for dimension in _BUDGET_DIMENSIONS:
            if instrumentation.get(dimension) is True:
                required.add(dimension)
        if not all(
            instrumentation.get(dimension) is True
            for dimension in ("wall_seconds", "records_scanned", "bytes_scanned")
        ):
            raise _ContractViolation(
                "P1E-011_P4_SELECTION_BINDING_INVALID"
            )
    return tuple(
        dimension for dimension in _BUDGET_DIMENSIONS if dimension in required
    )


def _validate_budget(
    value: object, required_dimensions: Sequence[str]
) -> Mapping[str, Any]:
    budget = _exact_mapping(
        value, _BUDGET_FIELDS, "P1E-012_RESOURCE_BUDGET_INVALID"
    )
    _nonempty_string(
        budget.get("budget_id"), "P1E-012_RESOURCE_BUDGET_INVALID"
    )
    _canonical_sha(
        budget.get("as_of_state_hash"),
        "P1E-012_RESOURCE_BUDGET_INVALID",
    )
    if (
        budget.get("budget_policy")
        != "TRACE_BINDING_ONLY_NO_COST_UTILITY_NO_CHANCE_CONSTRAINT"
    ):
        raise _ContractViolation("P1E-012_RESOURCE_BUDGET_INVALID")
    hard = _exact_mapping(
        budget.get("hard_limits"),
        _BUDGET_DIMENSION_SET,
        "P1E-012_RESOURCE_BUDGET_INVALID",
    )
    consumed = _exact_mapping(
        budget.get("consumed"),
        _BUDGET_DIMENSION_SET,
        "P1E-012_RESOURCE_BUDGET_INVALID",
    )
    remaining = _exact_mapping(
        budget.get("remaining"),
        _BUDGET_DIMENSION_SET,
        "P1E-012_RESOURCE_BUDGET_INVALID",
    )
    exhausted = False
    for dimension in _BUDGET_DIMENSIONS:
        limit = _decimal(hard.get(dimension))
        used = _decimal(consumed.get(dimension))
        left = _decimal(remaining.get(dimension))
        if used > limit or left != limit - used:
            raise _ContractViolation("P1E-012_RESOURCE_BUDGET_INVALID")
        if dimension in required_dimensions and left <= 0:
            exhausted = True
    expected_status = "EXHAUSTED" if exhausted else "AVAILABLE"
    if budget.get("budget_status") != expected_status:
        raise _ContractViolation("P1E-012_RESOURCE_BUDGET_INVALID")
    if budget.get("budget_hash") != canonical_hash_without_field(
        budget, "budget_hash"
    ):
        raise _ContractViolation("P1E-003_STALE_OR_MISMATCHED_HASH")
    return budget


def _calculate_action_values(
    validated: _ValidatedRequest,
) -> tuple[dict[str, object], ...]:
    world_count = len(validated.current_u_world_ids)
    table: list[dict[str, object]] = []
    by_action = {
        str(partition["action_id"]): partition
        for partition in validated.partitions
    }
    for action_id in validated.allowed_action_ids:
        partition = by_action[action_id]
        output_domain = list(partition["output_domain"])
        counts: list[dict[str, object]] = []
        raw_numerator = 0
        for outcome in output_domain:
            count = sum(
                1
                for row in partition["world_outcomes"]
                if row["outcome"] == outcome
            )
            counts.append({"outcome": deepcopy(outcome), "count": count})
            raw_numerator += count * (world_count - count)
        divisor = gcd(raw_numerator, world_count)
        table.append(
            {
                "action_id": action_id,
                "outcome_counts": counts,
                "raw_value_numerator": raw_numerator,
                "raw_value_denominator": world_count,
                "reduced_value_numerator": raw_numerator // divisor,
                "reduced_value_denominator": world_count // divisor,
                "partition_hash": partition["partition_hash"],
            }
        )
    return tuple(table)


def _decide(
    validated: _ValidatedRequest,
    values: tuple[dict[str, object], ...],
) -> dict[str, object]:
    bindings = _input_bindings(validated)
    summary = {
        "world_count": len(validated.current_u_world_ids),
        "world_ids": list(validated.current_u_world_ids),
        "world_ids_hash": validated.finite["current_u_hash"],
    }
    if len(validated.current_u_world_ids) == 1:
        return _decision_record(
            request=validated.request,
            request_hash=validated.request_hash,
            decision=ABSTAIN_SINGLETON,
            reason_codes=["P1E-016_ALREADY_SINGLETON"],
            input_bindings=bindings,
            current_u_summary=summary,
            eligible_action_ids=list(validated.allowed_action_ids),
            action_value_table=list(values),
            selected_action_id=None,
            tie_break=None,
            resource_trace_binding=None,
        )
    if validated.budget["budget_status"] == "EXHAUSTED":
        return _decision_record(
            request=validated.request,
            request_hash=validated.request_hash,
            decision=ABSTAIN_BUDGET,
            reason_codes=["P1E-017_RESOURCE_BUDGET_EXHAUSTED"],
            input_bindings=bindings,
            current_u_summary=summary,
            eligible_action_ids=list(validated.allowed_action_ids),
            action_value_table=list(values),
            selected_action_id=None,
            tie_break=None,
            resource_trace_binding=None,
        )
    if not validated.allowed_action_ids:
        return _decision_record(
            request=validated.request,
            request_hash=validated.request_hash,
            decision=ABSTAIN_NO_ACTION,
            reason_codes=["P1E-014_NO_FORMALLY_ELIGIBLE_ACTION"],
            input_bindings=bindings,
            current_u_summary=summary,
            eligible_action_ids=[],
            action_value_table=[],
            selected_action_id=None,
            tie_break=None,
            resource_trace_binding=None,
        )
    maximum = max(int(row["raw_value_numerator"]) for row in values)
    if maximum <= 0:
        return _decision_record(
            request=validated.request,
            request_hash=validated.request_hash,
            decision=ABSTAIN_NO_VALUE,
            reason_codes=["P1E-015_NO_POSITIVE_EXPECTED_REDUCTION"],
            input_bindings=bindings,
            current_u_summary=summary,
            eligible_action_ids=list(validated.allowed_action_ids),
            action_value_table=list(values),
            selected_action_id=None,
            tie_break=None,
            resource_trace_binding=None,
        )
    tied = sorted(
        str(row["action_id"])
        for row in values
        if row["raw_value_numerator"] == maximum
    )
    selected = tied[0]
    selected_value = next(
        row for row in values if row["action_id"] == selected
    )
    tie_break = {
        "rule_id": TIE_BREAK_RULE,
        "maximum_raw_value_numerator": maximum,
        "tied_action_ids": tied,
        "selected_action_id": selected,
    }
    basis_payload = {
        "request_hash": validated.request_hash,
        "selected_action_id": selected,
        "raw_value_numerator": selected_value["raw_value_numerator"],
        "raw_value_denominator": selected_value["raw_value_denominator"],
        "reduced_value_numerator": selected_value[
            "reduced_value_numerator"
        ],
        "reduced_value_denominator": selected_value[
            "reduced_value_denominator"
        ],
        "tie_break_rule_id": TIE_BREAK_RULE,
        "tied_action_ids": tied,
        "resource_budget_hash": validated.budget["budget_hash"],
    }
    basis_hash = canonical_value_hash(basis_payload)
    instrumentation = validated.actions_by_id[selected][
        "resource_instrumentation"
    ]
    required_trace_dimensions = [
        dimension
        for dimension in _BUDGET_DIMENSIONS
        if instrumentation.get(dimension) is True
    ]
    trace_binding = {
        "decision_basis_hash": basis_hash,
        "attempt_id": f"p1e-attempt:{basis_hash}",
        "selected_action_id": selected,
        "action_catalog_declared_hash": validated.catalog_binding[
            "declared_catalog_hash"
        ],
        "resource_budget_hash": validated.budget["budget_hash"],
        "required_trace_dimensions": required_trace_dimensions,
        "trace_match_policy": TRACE_MATCH_POLICY,
    }
    return _decision_record(
        request=validated.request,
        request_hash=validated.request_hash,
        decision=SELECT_ACTION,
        reason_codes=["P1E-SELECT-001_EXACT_DEPTH1_WORLD_REDUCTION"],
        input_bindings=bindings,
        current_u_summary=summary,
        eligible_action_ids=list(validated.allowed_action_ids),
        action_value_table=list(values),
        selected_action_id=selected,
        tie_break=tie_break,
        resource_trace_binding=trace_binding,
    )


def _decision_record(
    *,
    request: object,
    request_hash: str,
    decision: str,
    reason_codes: Sequence[str],
    input_bindings: Mapping[str, object],
    current_u_summary: Mapping[str, object],
    eligible_action_ids: Sequence[str],
    action_value_table: Sequence[Mapping[str, object]],
    selected_action_id: str | None,
    tie_break: Mapping[str, object] | None,
    resource_trace_binding: Mapping[str, object] | None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "record_class": "kernel_a17_p1e_depth1_planner_decision",
        "planner_mode": PLANNER_MODE,
        "decision": decision,
        "reason_codes": list(reason_codes),
        "request_hash": request_hash,
        "input_bindings": deepcopy(dict(input_bindings)),
        "current_u_summary": deepcopy(dict(current_u_summary)),
        "eligible_action_ids": list(eligible_action_ids),
        "action_value_table": deepcopy(list(action_value_table)),
        "selected_action_id": selected_action_id,
        "tie_break": deepcopy(tie_break),
        "resource_trace_binding": deepcopy(resource_trace_binding),
        "authority_ceiling": {
            "action_execution_authority": False,
            "mint_authority": False,
            "admission_authority": False,
            "kernel_write_authority": False,
            "certificate_authority": False,
            "stop_authority": False,
            "part_b_pass_authority": False,
        },
        "probability_model": None,
        "planning_confidence": None,
        "record_hash": "",
    }
    record["record_hash"] = canonical_hash_without_field(
        record, "record_hash"
    )
    if set(record) != DECISION_FIELDS or len(record) != 17:
        raise AssertionError("decision shape drift")
    return record


def _input_bindings(validated: _ValidatedRequest) -> dict[str, object]:
    return {
        "case_id": validated.case["case_id"],
        "gamma_hash": validated.case["gamma_hash"],
        "evidence_hash": validated.case["evidence_hash"],
        "compiled_legal_worlds_hash": validated.finite[
            "compiled_legal_worlds_hash"
        ],
        "current_u_hash": validated.finite["current_u_hash"],
        "checker_run_hash": validated.checker["checker_run_hash"],
        "counterexample_hash": validated.counterexample[
            "counterexample_hash"
        ],
        "action_catalog_declared_hash": validated.catalog_binding[
            "declared_catalog_hash"
        ],
        "action_catalog_content_sha256": validated.catalog_binding[
            "catalog_content_sha256"
        ],
        "p4_selection_record_hash": validated.p4[
            "selection_record_hash"
        ],
        "outcome_partitions_hash": canonical_value_hash(
            list(validated.partitions)
        ),
        "resource_budget_hash": validated.budget["budget_hash"],
    }


def _safe_input_bindings(request: object) -> dict[str, object]:
    invalid = "__INVALID__"
    result = {
        "case_id": invalid,
        "gamma_hash": invalid,
        "evidence_hash": invalid,
        "compiled_legal_worlds_hash": invalid,
        "current_u_hash": invalid,
        "checker_run_hash": invalid,
        "counterexample_hash": invalid,
        "action_catalog_declared_hash": invalid,
        "action_catalog_content_sha256": invalid,
        "p4_selection_record_hash": invalid,
        "outcome_partitions_hash": invalid,
        "resource_budget_hash": invalid,
    }
    if not isinstance(request, Mapping):
        return result
    sources = {
        "case_id": ("case_binding", "case_id"),
        "gamma_hash": ("case_binding", "gamma_hash"),
        "evidence_hash": ("case_binding", "evidence_hash"),
        "compiled_legal_worlds_hash": (
            "finite_domain_binding",
            "compiled_legal_worlds_hash",
        ),
        "current_u_hash": ("finite_domain_binding", "current_u_hash"),
        "checker_run_hash": ("checker_binding", "checker_run_hash"),
        "counterexample_hash": (
            "counterexample_binding",
            "counterexample_hash",
        ),
        "action_catalog_declared_hash": (
            "action_catalog_binding",
            "declared_catalog_hash",
        ),
        "action_catalog_content_sha256": (
            "action_catalog_binding",
            "catalog_content_sha256",
        ),
        "p4_selection_record_hash": (
            "p4_selection_binding",
            "selection_record_hash",
        ),
        "resource_budget_hash": (
            "resource_budget_declaration",
            "budget_hash",
        ),
    }
    for output, (outer, inner) in sources.items():
        nested = request.get(outer)
        if isinstance(nested, Mapping) and isinstance(
            nested.get(inner), str
        ):
            result[output] = nested[inner]
    partitions = request.get("deterministic_outcome_partitions")
    try:
        result["outcome_partitions_hash"] = canonical_value_hash(partitions)
    except ValueError:
        pass
    return result


def _safe_current_u_summary(request: object) -> dict[str, object]:
    ids: list[str] = []
    if isinstance(request, Mapping):
        finite = request.get("finite_domain_binding")
        if isinstance(finite, Mapping):
            raw_ids = finite.get("current_u_world_ids")
            if (
                isinstance(raw_ids, Sequence)
                and not isinstance(raw_ids, (str, bytes))
                and all(isinstance(item, str) for item in raw_ids)
            ):
                ids = list(raw_ids)
    return {
        "world_count": len(ids),
        "world_ids": ids,
        "world_ids_hash": canonical_value_hash(ids),
    }


def _safe_request_hash(request: object) -> str:
    if isinstance(request, Mapping):
        try:
            return canonical_hash_without_field(request, "request_hash")
        except ValueError:
            pass
    return canonical_value_hash({"invalid_request": True})


def _safe_record_hash(record: object) -> str:
    if isinstance(record, Mapping):
        try:
            return canonical_hash_without_field(record, "record_hash")
        except ValueError:
            pass
    return canonical_value_hash({"invalid_decision_record": True})


def _safe_trace_hash(trace_row: object) -> str:
    try:
        return canonical_value_hash(trace_row)
    except ValueError:
        return canonical_value_hash({"invalid_trace_row": True})


def _exact_mapping(
    value: object, fields: frozenset[str], reason_code: str
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise _ContractViolation(reason_code)
    return value


def _nonempty_string(value: object, reason_code: str) -> str:
    if not isinstance(value, str) or not value:
        raise _ContractViolation(reason_code)
    return value


def _canonical_sha(value: object, reason_code: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise _ContractViolation(reason_code)
    return value


def _sorted_unique_strings(
    value: object, reason_code: str, *, nonempty: bool
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise _ContractViolation(reason_code)
    items = tuple(value)
    if nonempty and not items:
        raise _ContractViolation(reason_code)
    if (
        any(not isinstance(item, str) or not item for item in items)
        or len(set(items)) != len(items)
        or list(items) != sorted(items)
    ):
        raise _ContractViolation(reason_code)
    return items


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise _ContractViolation("P1E-012_RESOURCE_BUDGET_INVALID")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise _ContractViolation(
            "P1E-012_RESOURCE_BUDGET_INVALID"
        ) from exc
    if not number.is_finite() or number < 0:
        raise _ContractViolation("P1E-012_RESOURCE_BUDGET_INVALID")
    return number


def _contains_key(value: object, forbidden: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).lower() in forbidden
            or _contains_key(nested, forbidden)
            for key, nested in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_contains_key(item, forbidden) for item in value)
    return False


def _contains_authority_request(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).lower() in _FORBIDDEN_AUTHORITY_KEYS:
                return True
            if _contains_authority_request(nested):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_contains_authority_request(item) for item in value)
    return isinstance(value, str) and value.upper() in _FORBIDDEN_AUTHORITY_VALUES


__all__ = [
    "ACTION_EXECUTION_ENABLED",
    "DECISION_FIELDS",
    "HARD_BAN",
    "PRODUCTION_REGISTRATION_ENABLED",
    "RECEIPT_FIELDS",
    "REQUEST_FIELDS",
    "SELECT_ACTION",
    "STOP_AUTHORITY",
    "SYSTEM_STATE_AUTHORITY",
    "TRACE_INPUT_FIELDS",
    "canonical_hash_without_field",
    "evaluate_depth1_planner_request",
    "validate_resource_trace_binding",
]
