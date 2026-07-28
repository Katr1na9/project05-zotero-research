"""Test-only Twin/P10 to A17-P1e readonly caller wiring.

The caller maps the single pinned ``TWIN-COUNTEREXAMPLE-001`` public fixture
into the accepted fourteen-field depth-1 planner request.  It returns only a
next-action candidacy sidecar.  It does not import or call the P10 driver,
execute an action, derive system state, register a production surface, mutate
a trace, mint, admit, write, certify, or STOP.

Historical Twin resource-trace rows are legacy five-field rows.  They are
passed unmodified to the accepted P1e validator and must fail closed; this
module never fabricates a matching P1e trace row.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from src.actions.selection import DistinguishingActionSelector
from src.ir.canonical_hash import canonical_value_hash
from src.planner import deterministic_depth1 as depth1
from src.scope.finite_problem import (
    EvidenceGammaFiniteProblemCompiler,
    compiled_legal_world_documents,
    compiled_legal_worlds_hash,
)


PRODUCTION_REGISTRATION_ENABLED = False
ACTION_EXECUTION_ENABLED = False
SYSTEM_STATE_AUTHORITY = False
STOP_AUTHORITY = False

HARD_BAN = (
    "Path A / Kernel design GREEN must not be inferred as L2 PASS, "
    "Part B PASS, or unrestricted Part B elevation."
)

CALLER_INPUT_SCHEMA_VERSION = (
    "kernel-a17-p1e-twin-p10-readonly-wiring-input-v0.1"
)
CALLER_RESULT_SCHEMA_VERSION = (
    "kernel-a17-p1e-twin-p10-readonly-wiring-result-v0.1"
)
CALLER_REQUEST_KIND = (
    "CLASSIFY_TWIN_FIXED_CASE_NEXT_ACTION_CANDIDACY_SIDECAR"
)
CALLER_CLASS = "TEST_ONLY_NO_PRODUCTION_REGISTRATION"
AUTHORIZED_SCOPE = (
    "TWIN_FIXED_CASE_TO_P1E_NEXT_ACTION_CANDIDACY_SIDECAR_ONLY"
)
FIXED_CASE_ID = "TWIN-COUNTEREXAMPLE-001"
TWIN_INPUT_PROFILE = "PINNED_TWIN_COUNTEREXAMPLE_001_PUBLIC_INPUTS"
P1E_REQUEST_PROFILE = "EXACT_A17_P1E_REQUEST_V0_1"
CURRENT_U_POLICY = "FULL_COMPILED_LEGAL_WORLD_SET_NO_EXPANSION"
RESOURCE_BUDGET_PROFILE = "PINNED_P1E_TEST_ONLY_BUDGET_TWIN_001"
RESULT_SCOPE = "NEXT_ACTION_CANDIDACY_SIDECAR_ONLY_NO_EXECUTE_NO_STOP"
RESULT_CLASS = "NEXT_ACTION_CANDIDACY_SIDECAR_ONLY"

NO_TRACE_BINDING = "NONE"
VALIDATE_HISTORICAL_TRACE = (
    "VALIDATE_EXACT_HISTORICAL_TWIN_ROW_FAIL_CLOSED"
)
TRACE_BINDING_MODES = frozenset(
    {NO_TRACE_BINDING, VALIDATE_HISTORICAL_TRACE}
)
HISTORICAL_ATTEMPT_IDS = frozenset(
    {"ATTEMPT-001", "ATTEMPT-002", "ATTEMPT-003"}
)

STATUS_SIDECAR_NO_TRACE = (
    "CANDIDACY_SIDECAR_EMITTED_NO_TRACE_BINDING"
)
STATUS_SIDECAR_TRACE_DENIED = (
    "CANDIDACY_SIDECAR_EMITTED_TRACE_BINDING_DENIED"
)
STATUS_D1_NONSELECT = "D1_NONSELECT_DECISION_RETURNED_FAIL_CLOSED"
STATUS_DENY_AUTHORITY = "DENY_CALLER_AUTHORITY"
STATUS_DENY_INPUT = "DENY_CALLER_INPUT"

REASON_AUTHORITY = "P1E-TWIN-WIRING-001_TEST_ONLY_AUTHORITY_REQUIRED"
REASON_INPUT = "P1E-TWIN-WIRING-002_CLOSED_WORLD_INPUT_OR_PIN_MISMATCH"

OWNER_GO_PATH = (
    "docs/kernel/"
    "kernel-v0.8-a17-p1e-twin-p10-readonly-wiring-"
    "owner-go-authorization-v0.1-20260728.json"
)
OWNER_GO_SHA256 = (
    "b582178822621c7407e97b847b795db62e6d5002ddda21024ce9b26173ea18c3"
)

AUTHORITY_FIELDS = frozenset(
    {
        "authority_class",
        "authorized_scope",
        "owner_go_path",
        "owner_go_sha256",
        "production_registration_enabled",
    }
)
CALLER_INPUT_FIELDS = frozenset(
    {
        "schema_version",
        "request_kind",
        "caller_class",
        "fixed_case_id",
        "twin_input_profile",
        "p1e_request_profile",
        "current_u_policy",
        "resource_budget_profile",
        "resource_trace_binding_mode",
        "historical_resource_trace_attempt_id",
        "requested_result_scope",
        "caller_input_hash",
    }
)
RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "record_class",
        "result_class",
        "wiring_status",
        "reason_codes",
        "decision_record",
        "resource_trace_binding_receipt",
        "authority_ceiling",
    }
)
HISTORICAL_TRACE_FIELDS = frozenset(
    {"attempt_id", "action_id", "status", "counts", "resources"}
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GAMMA_PATH = "configs/gamma-kernel-v0.8.yaml"
_CATALOG_PATH = "configs/action-catalog-kernel-v0.8.yaml"
_CASE_EVIDENCE_PATH = (
    "tests/fixtures/TWIN-COUNTEREXAMPLE-001/claims/case_evidence.jsonl"
)
_COUNTEREXAMPLE_PATH = (
    "tests/fixtures/TWIN-COUNTEREXAMPLE-001/expected/counterexample.json"
)
_OUTCOME_PATH = (
    "tests/fixtures/TWIN-COUNTEREXAMPLE-001/expected/outcome.yaml"
)
_HISTORICAL_TRACE_PATH = (
    "tests/fixtures/TWIN-COUNTEREXAMPLE-001/expected/resource_trace.jsonl"
)
_P1E_FIXTURE_PATH = (
    "tests/unit/fixtures/kernel_a17_p1e_depth1_planner_v0.1.json"
)

_EXPECTED_COMPILED_WORLD_HASH = (
    "sha256:6d4bbedd4bf705be0e6a0dce9cc5440948be163e496cf96c55ba2d33fd0a080c"
)
_EXPECTED_WORLD_IDS = ("W-ALTERNATIVE-H3", "W-SUPPORT-H1")
_EXPECTED_ALLOWED_ACTION_IDS = (
    "query_auth_H1_1000_1015",
    "query_logon_origin_H3",
)
_EXPECTED_FORBIDDEN_ACTION_IDS = (
    "oracle_reveal_true_initial_foothold",
    "use_hidden_recoverable_claim_ids",
)

# These are replayed before any call into the P1e gate.  The observation file
# is hashed as a protected P10 boundary but is deliberately never parsed into
# a D1 partition.
_EXPECTED_FILE_SHA256: dict[str, str] = {
    OWNER_GO_PATH: OWNER_GO_SHA256,
    (
        "docs/kernel/"
        "kernel-v0.8-a17-p1e-twin-p10-readonly-wiring-"
        "red-design-v0.1-20260728.json"
    ): "0848ddf4b1cf5c495082d0e4d05c62eeff0542fb1c9840ab1c537c59fd0f75c4",
    (
        "docs/llm-editor/"
        "llm-editor-v0.8-l2-kernel-owner-a17-p1e-twin-p10-"
        "readonly-wiring-red-review-packet-v0.1-20260728.json"
    ): "f94bcfcfe1621142bb2a5a16ef01b55038cac79da8d50c830202521ece277865",
    (
        "docs/kernel/"
        "kernel-v0.8-a16-current-tip-replay-green-owner-"
        "acceptance-v0.1-20260728.json"
    ): "cf956a00a80c66bdbd97b076dac1f1814143a973950e1b24de5c2f854560dd06",
    (
        "docs/kernel/"
        "kernel-v0.8-a17-p1e-deterministic-depth1-planner-"
        "resource-trace-binding-green-owner-acceptance-v0.1-20260728.json"
    ): "84a3a2b402aa4355604410812f435d8142eba4042d53b5512f2833365a2c6d06",
    "src/planner/deterministic_depth1.py": (
        "ada6a8065e71fda58dde7e2b71ca19d7aded9a39f4cf5f67fb20d6fc5d7e38ff"
    ),
    _P1E_FIXTURE_PATH: (
        "1154c5dec1073e0f42efa734212a6658d9fd9c4492016bbfd484ed7a502d088b"
    ),
    "src/actions/selection.py": (
        "16f26fa8ca5fa0fe39a9b901b8b13a099f5527ed0c21f77718fd57763f847a83"
    ),
    "src/executor/deterministic.py": (
        "4e5ec71edc536bfef70fe19f86a723ac57b4ab5370bc845fa074ad2d107ba32a"
    ),
    "src/cli/kernel_e2e.py": (
        "8a7807c32d70e98ac5a36bda3a56f2279ebffbe23e0d2c6a11286bdba9208d60"
    ),
    "tests/integration/test_twin_kernel_e2e_p10.py": (
        "a332cbce5f8bdc9b0fd4467fbc09d0255d6099716c0405ffc5b47a13cdd26254"
    ),
    "tests/integration/twin_kernel_inputs.py": (
        "16323f3c415e903eeb2e72bdb94e116338c1770d8212bbf3f5917d48b4c4bdf3"
    ),
    _HISTORICAL_TRACE_PATH: (
        "2c3e5da8692070fb44e594666e337bcca6c4d3d09ad8662eabcbd1ee45c92318"
    ),
    (
        "tests/fixtures/TWIN-SUPPLY-CHAIN-002/expected/"
        "resource_trace.jsonl"
    ): "102f43c3210208101f393580b6d4afe7573f9be0e081edabb97d28f19b9efee5",
    _GAMMA_PATH: (
        "6477d93af84295e9affa3f6c1fbf1639c1dda29a45ba810d672e4d9a8a350966"
    ),
    _CATALOG_PATH: (
        "6442c1099fd0e0a43f081b5e912b516c8feec3d2dbdd604b9a59020ee43c066b"
    ),
    _CASE_EVIDENCE_PATH: (
        "600d7c56319a3aec24b16660484428d713c5584a4e0a2d7513e314b2de2bff04"
    ),
    _COUNTEREXAMPLE_PATH: (
        "2540921303ee383718858f03e87c3a7de899a70a3a782373f20d7d35bbc24d2c"
    ),
    _OUTCOME_PATH: (
        "7df3a24e7ee9cb1e16672517434b982e6ace4c42d92af537ccf055612ab0ade9"
    ),
    (
        "tests/fixtures/TWIN-COUNTEREXAMPLE-001/"
        "predicate_projections.yaml"
    ): "827f5d94d3d58edfe6522e9d52f5f77549eb3652c5f47eca2a6770ae718054a5",
    (
        "tests/fixtures/TWIN-COUNTEREXAMPLE-001/expected/"
        "action_observations.jsonl"
    ): "7c096524ef05789283430ede53f6cf907ccc7d614b227873c28cbb5432cad981",
}

_AUTHORITY_CEILING = {
    "action_execution_authority": False,
    "system_state_authority": False,
    "production_registration_authority": False,
    "mint_authority": False,
    "admission_authority": False,
    "kernel_or_e_case_write_authority": False,
    "certificate_authority": False,
    "stop_authority": False,
    "part_b_or_path_b_authority": False,
}


class _WiringViolation(ValueError):
    pass


def evaluate_twin_p10_fixed_case_for_depth1_candidacy(
    caller_input: Mapping[str, Any] | object,
    *,
    test_only_authority: Mapping[str, Any] | object,
) -> dict[str, object]:
    """Return an exact readonly candidacy sidecar for the fixed Twin case."""

    if not _valid_test_only_authority(test_only_authority):
        return _result(
            wiring_status=STATUS_DENY_AUTHORITY,
            reason_codes=[REASON_AUTHORITY],
            decision_record=None,
            receipt=None,
        )

    try:
        validated_input = _validate_caller_input(caller_input)
        _verify_all_pins()
        request = _build_p1e_request()
    except (
        _WiringViolation,
        KeyError,
        TypeError,
        ValueError,
        OSError,
        yaml.YAMLError,
    ):
        return _result(
            wiring_status=STATUS_DENY_INPUT,
            reason_codes=[REASON_INPUT],
            decision_record=None,
            receipt=None,
        )

    decision = depth1.evaluate_depth1_planner_request(request)
    if decision.get("decision") != depth1.SELECT_ACTION:
        reason_codes = decision.get("reason_codes")
        return _result(
            wiring_status=STATUS_D1_NONSELECT,
            reason_codes=(
                list(reason_codes)
                if isinstance(reason_codes, list)
                else [REASON_INPUT]
            ),
            decision_record=decision,
            receipt=None,
        )

    if validated_input["resource_trace_binding_mode"] == NO_TRACE_BINDING:
        return _result(
            wiring_status=STATUS_SIDECAR_NO_TRACE,
            reason_codes=[],
            decision_record=decision,
            receipt=None,
        )

    try:
        trace_row = _select_exact_historical_trace_row(
            validated_input["historical_resource_trace_attempt_id"]
        )
    except (
        _WiringViolation,
        KeyError,
        TypeError,
        ValueError,
        OSError,
    ):
        return _result(
            wiring_status=STATUS_DENY_INPUT,
            reason_codes=[REASON_INPUT],
            decision_record=None,
            receipt=None,
        )

    trace_before = deepcopy(trace_row)
    receipt = depth1.validate_resource_trace_binding(decision, trace_row)
    if trace_row != trace_before:
        return _result(
            wiring_status=STATUS_DENY_INPUT,
            reason_codes=[REASON_INPUT],
            decision_record=None,
            receipt=None,
        )
    if receipt.get("match_status") != "DENY_TRACE_BINDING_MISMATCH":
        return _result(
            wiring_status=STATUS_DENY_INPUT,
            reason_codes=[REASON_INPUT],
            decision_record=None,
            receipt=None,
        )
    receipt_reasons = receipt.get("reason_codes")
    return _result(
        wiring_status=STATUS_SIDECAR_TRACE_DENIED,
        reason_codes=(
            list(receipt_reasons)
            if isinstance(receipt_reasons, list)
            else [REASON_INPUT]
        ),
        decision_record=decision,
        receipt=receipt,
    )


def _valid_test_only_authority(authority: object) -> bool:
    if not isinstance(authority, Mapping) or set(authority) != AUTHORITY_FIELDS:
        return False
    return (
        authority.get("authority_class") == CALLER_CLASS
        and authority.get("authorized_scope") == AUTHORIZED_SCOPE
        and authority.get("owner_go_path") == OWNER_GO_PATH
        and authority.get("owner_go_sha256") == OWNER_GO_SHA256
        and type(authority.get("production_registration_enabled")) is bool
        and authority.get("production_registration_enabled") is False
    )


def _validate_caller_input(caller_input: object) -> Mapping[str, Any]:
    if not isinstance(caller_input, Mapping):
        raise _WiringViolation(REASON_INPUT)
    if set(caller_input) != CALLER_INPUT_FIELDS:
        raise _WiringViolation(REASON_INPUT)
    expected_values = {
        "schema_version": CALLER_INPUT_SCHEMA_VERSION,
        "request_kind": CALLER_REQUEST_KIND,
        "caller_class": CALLER_CLASS,
        "fixed_case_id": FIXED_CASE_ID,
        "twin_input_profile": TWIN_INPUT_PROFILE,
        "p1e_request_profile": P1E_REQUEST_PROFILE,
        "current_u_policy": CURRENT_U_POLICY,
        "resource_budget_profile": RESOURCE_BUDGET_PROFILE,
        "requested_result_scope": RESULT_SCOPE,
    }
    if any(caller_input.get(key) != value for key, value in expected_values.items()):
        raise _WiringViolation(REASON_INPUT)

    mode = caller_input.get("resource_trace_binding_mode")
    attempt_id = caller_input.get("historical_resource_trace_attempt_id")
    if mode not in TRACE_BINDING_MODES:
        raise _WiringViolation(REASON_INPUT)
    if mode == NO_TRACE_BINDING and attempt_id is not None:
        raise _WiringViolation(REASON_INPUT)
    if mode == VALIDATE_HISTORICAL_TRACE and attempt_id not in HISTORICAL_ATTEMPT_IDS:
        raise _WiringViolation(REASON_INPUT)
    if caller_input.get("caller_input_hash") != depth1.canonical_hash_without_field(
        caller_input, "caller_input_hash"
    ):
        raise _WiringViolation(REASON_INPUT)
    return caller_input


def _verify_all_pins() -> None:
    for relative_path, expected in _EXPECTED_FILE_SHA256.items():
        path = _repo_path(relative_path)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise _WiringViolation(REASON_INPUT)


def _build_p1e_request() -> dict[str, object]:
    gamma = _load_yaml(_GAMMA_PATH)
    catalog = _load_yaml(_CATALOG_PATH)
    expected = _load_yaml(_OUTCOME_PATH)
    counterexample = _load_json(_COUNTEREXAMPLE_PATH)
    case_evidence = _load_jsonl(_CASE_EVIDENCE_PATH)
    p1e_fixture = _load_json(_P1E_FIXTURE_PATH)

    if (
        expected.get("case_id") != FIXED_CASE_ID
        or counterexample.get("case_id") != FIXED_CASE_ID
        or gamma.get("hash") != counterexample.get("gamma_hash")
        or expected.get("target_level") != counterexample.get("target_level")
    ):
        raise _WiringViolation(REASON_INPUT)

    compiled = EvidenceGammaFiniteProblemCompiler().compile(
        gamma,
        case_evidence,
        target_variable=expected["target_level"],
    )
    world_documents = compiled_legal_world_documents(compiled)
    world_hash = compiled_legal_worlds_hash(compiled)
    world_ids = tuple(sorted(world["world_id"] for world in world_documents))
    if (
        compiled.gamma_hash != gamma["hash"]
        or compiled.target_variable != expected["target_level"]
        or world_hash != _EXPECTED_COMPILED_WORLD_HASH
        or world_ids != _EXPECTED_WORLD_IDS
        or len(world_documents) != 2
    ):
        raise _WiringViolation(REASON_INPUT)

    core = counterexample.get("core_query_results")
    support_world = counterexample.get("support_world")
    alternative_world = counterexample.get("alternative_world")
    if not all(
        isinstance(value, Mapping)
        for value in (core, support_world, alternative_world)
    ):
        raise _WiringViolation(REASON_INPUT)
    checker_seed: dict[str, object] = {
        "checker_status": expected.get("checker_status"),
        "base_status": expected.get("base"),
        "support_status": expected.get("support"),
        "alternative_status": expected.get("alternative"),
        "support_world_id": support_world.get("world_id"),
        "alternative_world_id": alternative_world.get("world_id"),
    }
    if (
        checker_seed["checker_status"] != counterexample.get("checker_status")
        or checker_seed["base_status"] != core.get("base")
        or checker_seed["support_status"] != core.get("support")
        or checker_seed["alternative_status"] != core.get("alternative")
        or checker_seed["checker_status"] != "COUNTEREXAMPLE_FOUND"
        or any(
            checker_seed[key] != "SAT"
            for key in ("base_status", "support_status", "alternative_status")
        )
        or set(
            (
                checker_seed["support_world_id"],
                checker_seed["alternative_world_id"],
            )
        )
        != set(world_ids)
    ):
        raise _WiringViolation(REASON_INPUT)
    checker_binding = dict(checker_seed)
    checker_binding["checker_run_hash"] = canonical_value_hash(checker_binding)

    predicates = counterexample.get("distinguishing_predicates")
    if (
        not isinstance(predicates, Sequence)
        or isinstance(predicates, (str, bytes))
        or any(not isinstance(item, str) or not item for item in predicates)
    ):
        raise _WiringViolation(REASON_INPUT)
    sorted_predicates = sorted(predicates)
    if len(set(sorted_predicates)) != len(sorted_predicates):
        raise _WiringViolation(REASON_INPUT)
    counterexample_binding = {
        "counterexample_id": counterexample.get("counterexample_id"),
        "counterexample_hash": canonical_value_hash(counterexample),
        "target_level": counterexample.get("target_level"),
        "distinguishing_predicates": sorted_predicates,
        "distinguishing_predicates_hash": canonical_value_hash(
            sorted_predicates
        ),
    }

    selection = DistinguishingActionSelector().select(counterexample, catalog)
    allowed = tuple(selection.allowed_actions)
    forbidden = tuple(sorted(selection.forbidden_actions))
    if (
        allowed != _EXPECTED_ALLOWED_ACTION_IDS
        or forbidden != _EXPECTED_FORBIDDEN_ACTION_IDS
    ):
        raise _WiringViolation(REASON_INPUT)
    selection_payload = {
        "allowed_actions": list(allowed),
        "forbidden_actions": list(forbidden),
        "catalog_actions_examined": selection.catalog_actions_examined,
    }
    p4_binding = {
        "selection_record_hash": canonical_value_hash(selection_payload),
        "allowed_action_ids": list(allowed),
        "forbidden_action_ids": list(forbidden),
    }

    catalog_hash = depth1.canonical_hash_without_field(catalog, "hash")
    if (
        catalog.get("schema_version") != "0.8.0"
        or catalog.get("catalog_id") != "action-catalog-kernel-v0.8"
        or catalog.get("catalog_version") != "0.8.0"
        or catalog.get("hash") != catalog_hash
    ):
        raise _WiringViolation(REASON_INPUT)
    catalog_binding = {
        "schema_version": catalog["schema_version"],
        "catalog_id": catalog["catalog_id"],
        "catalog_version": catalog["catalog_version"],
        "declared_catalog_hash": catalog["hash"],
        "catalog_content_sha256": _EXPECTED_FILE_SHA256[_CATALOG_PATH],
        "catalog_path": _CATALOG_PATH,
        "reference_mode": "EXACT_PATH_AND_HASH_NO_WILDCARD",
    }

    partitions = _build_partitions(
        gamma=gamma,
        catalog=catalog,
        allowed_action_ids=allowed,
        world_documents=world_documents,
    )

    request_seed = p1e_fixture.get("request_seed")
    if not isinstance(request_seed, Mapping):
        raise _WiringViolation(REASON_INPUT)
    budget_seed = request_seed.get("resource_budget_seed")
    if not isinstance(budget_seed, Mapping):
        raise _WiringViolation(REASON_INPUT)
    budget = deepcopy(dict(budget_seed))
    budget["budget_hash"] = ""
    budget["budget_hash"] = depth1.canonical_hash_without_field(
        budget, "budget_hash"
    )

    request: dict[str, object] = {
        "schema_version": depth1.REQUEST_SCHEMA_VERSION,
        "request_kind": depth1.REQUEST_KIND,
        "planner_mode": depth1.PLANNER_MODE,
        "execution_mode": depth1.EXECUTION_MODE,
        "case_binding": {
            "case_id": FIXED_CASE_ID,
            "gamma_hash": gamma["hash"],
            "evidence_hash": counterexample["evidence_hash"],
            "compilation_profile": compiled.compilation_profile,
        },
        "finite_domain_binding": {
            "compiled_legal_world_count": len(world_ids),
            "compiled_legal_worlds_hash": world_hash,
            "compiled_legal_world_ids": list(world_ids),
            "current_u_count": len(world_ids),
            "current_u_hash": canonical_value_hash(list(world_ids)),
            "current_u_world_ids": list(world_ids),
            "target_variable": compiled.target_variable,
        },
        "checker_binding": checker_binding,
        "counterexample_binding": counterexample_binding,
        "action_catalog_binding": catalog_binding,
        "p4_selection_binding": p4_binding,
        "deterministic_outcome_partitions": partitions,
        "resource_budget_declaration": budget,
        "requested_decision_scope": depth1.DECISION_SCOPE,
        "request_hash": "",
    }
    request["request_hash"] = depth1.canonical_hash_without_field(
        request, "request_hash"
    )
    if set(request) != depth1.REQUEST_FIELDS or len(request) != 14:
        raise _WiringViolation(REASON_INPUT)
    return request


def _build_partitions(
    *,
    gamma: Mapping[str, Any],
    catalog: Mapping[str, Any],
    allowed_action_ids: Sequence[str],
    world_documents: Sequence[Mapping[str, Any]],
) -> list[dict[str, object]]:
    raw_actions = catalog.get("actions")
    if not isinstance(raw_actions, Sequence) or isinstance(
        raw_actions, (str, bytes)
    ):
        raise _WiringViolation(REASON_INPUT)
    actions = {
        action.get("action_id"): action
        for action in raw_actions
        if isinstance(action, Mapping)
        and isinstance(action.get("action_id"), str)
    }
    if len(actions) != len(raw_actions):
        raise _WiringViolation(REASON_INPUT)

    raw_coverage = gamma.get("sensor_coverage")
    if not isinstance(raw_coverage, Sequence) or isinstance(
        raw_coverage, (str, bytes)
    ):
        raise _WiringViolation(REASON_INPUT)
    coverage = {
        row.get("sensor_id"): row
        for row in raw_coverage
        if isinstance(row, Mapping)
        and isinstance(row.get("sensor_id"), str)
    }
    auth_coverage = coverage.get("auth-H1")
    if (
        not isinstance(auth_coverage, Mapping)
        or auth_coverage.get("absence_semantics")
        not in {"bounded_completeness", "closed_world"}
    ):
        raise _WiringViolation(REASON_INPUT)

    worlds = sorted(world_documents, key=lambda item: str(item.get("world_id")))
    partitions: list[dict[str, object]] = []
    for action_id in allowed_action_ids:
        action = actions.get(action_id)
        if not isinstance(action, Mapping):
            raise _WiringViolation(REASON_INPUT)
        model = action.get("observation_model")
        if not isinstance(model, Mapping) or model.get("noise_model") != "deterministic":
            raise _WiringViolation(REASON_INPUT)
        output_domain = model.get("output_domain")
        if not isinstance(output_domain, Sequence) or isinstance(
            output_domain, (str, bytes)
        ):
            raise _WiringViolation(REASON_INPUT)

        rows: list[dict[str, object]] = []
        for world in worlds:
            world_id = world.get("world_id")
            predicates = world.get("predicates")
            if (
                not isinstance(world_id, str)
                or not isinstance(predicates, Sequence)
                or isinstance(predicates, (str, bytes))
                or any(not isinstance(item, str) for item in predicates)
            ):
                raise _WiringViolation(REASON_INPUT)
            outcome = _project_world_outcome(
                action_id=action_id,
                model=model,
                predicates=tuple(predicates),
            )
            if outcome not in output_domain:
                raise _WiringViolation(REASON_INPUT)
            rows.append({"world_id": world_id, "outcome": outcome})

        partition: dict[str, object] = {
            "action_id": action_id,
            "observation_model_hash": canonical_value_hash(model),
            "projection_rule_id": model.get("projection_rule_id"),
            "output_domain": list(output_domain),
            "partition_basis": depth1.PARTITION_BASIS,
            "world_outcomes": rows,
            "partition_hash": "",
        }
        partition["partition_hash"] = depth1.canonical_hash_without_field(
            partition, "partition_hash"
        )
        partitions.append(partition)
    return partitions


def _project_world_outcome(
    *,
    action_id: str,
    model: Mapping[str, Any],
    predicates: Sequence[str],
) -> str:
    if action_id == "query_auth_H1_1000_1015":
        if (
            model.get("projection_rule_id") != "auth-presence-by-origin-v1"
            or model.get("world_dependencies") != ["credential_activity:H1"]
        ):
            raise _WiringViolation(REASON_INPUT)
        return (
            "present"
            if "credential_activity:H1" in predicates
            else "absent"
        )
    if action_id == "query_logon_origin_H3":
        if (
            model.get("projection_rule_id") != "frozen-logon-origin-v1"
            or model.get("world_dependencies")
            != ["authentication_origin:H3"]
        ):
            raise _WiringViolation(REASON_INPUT)
        prefix = "authentication_origin:H3="
        matches = [
            predicate[len(prefix) :]
            for predicate in predicates
            if predicate.startswith(prefix)
        ]
        if len(matches) != 1:
            raise _WiringViolation(REASON_INPUT)
        return matches[0]
    raise _WiringViolation(REASON_INPUT)


def _select_exact_historical_trace_row(attempt_id: object) -> dict[str, object]:
    if attempt_id not in HISTORICAL_ATTEMPT_IDS:
        raise _WiringViolation(REASON_INPUT)
    rows = _load_jsonl(_HISTORICAL_TRACE_PATH)
    matches = [row for row in rows if row.get("attempt_id") == attempt_id]
    if len(matches) != 1 or set(matches[0]) != HISTORICAL_TRACE_FIELDS:
        raise _WiringViolation(REASON_INPUT)
    return matches[0]


def _result(
    *,
    wiring_status: str,
    reason_codes: list[str],
    decision_record: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": CALLER_RESULT_SCHEMA_VERSION,
        "record_class": "kernel_a17_p1e_twin_p10_readonly_wiring_result",
        "result_class": RESULT_CLASS,
        "wiring_status": wiring_status,
        "reason_codes": deepcopy(reason_codes),
        "decision_record": decision_record,
        "resource_trace_binding_receipt": receipt,
        "authority_ceiling": deepcopy(_AUTHORITY_CEILING),
    }
    if set(result) != RESULT_FIELDS or len(result) != 8:
        raise AssertionError("caller result shape drift")
    return result


def _repo_path(relative_path: str) -> Path:
    path = (_REPO_ROOT / relative_path).resolve()
    try:
        path.relative_to(_REPO_ROOT)
    except ValueError as exc:
        raise _WiringViolation(REASON_INPUT) from exc
    if not path.is_file():
        raise _WiringViolation(REASON_INPUT)
    return path


def _load_json(relative_path: str) -> dict[str, Any]:
    value = json.loads(_repo_path(relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise _WiringViolation(REASON_INPUT)
    return value


def _load_jsonl(relative_path: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for line in _repo_path(relative_path).read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise _WiringViolation(REASON_INPUT)
        values.append(value)
    if not values:
        raise _WiringViolation(REASON_INPUT)
    return values


def _load_yaml(relative_path: str) -> dict[str, Any]:
    value = yaml.safe_load(_repo_path(relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise _WiringViolation(REASON_INPUT)
    return value


__all__ = [
    "ACTION_EXECUTION_ENABLED",
    "AUTHORITY_FIELDS",
    "CALLER_INPUT_FIELDS",
    "HARD_BAN",
    "PRODUCTION_REGISTRATION_ENABLED",
    "RESULT_FIELDS",
    "STOP_AUTHORITY",
    "SYSTEM_STATE_AUTHORITY",
    "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
]
