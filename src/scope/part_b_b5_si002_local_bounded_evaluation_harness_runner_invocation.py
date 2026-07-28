"""Test-only SI-002 local bounded-harness runner invocation record.

The only positive path invokes the pinned Twin/P10 readonly candidacy caller
for one synthetic, declaration-bound fixed case.  The returned record states
that this local test-only runner call occurred; it grants no Planner or
evaluation execution authority and carries no performance, Path B, write,
certificate, or STOP meaning.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
)
from src.planner import twin_p10_readonly_wiring as twin_wiring


PRODUCTION_REGISTRATION_ENABLED = False
EVALUATION_EXECUTION_AUTHORITY = False
PLANNER_EXECUTION_AUTHORITY = False

HARD_BAN = (
    "Path A / Kernel design GREEN must not be inferred as L2 PASS, "
    "Part B PASS, or unrestricted Part B elevation."
)

IMPLEMENTATION_ID = (
    "part_b_b5_m3_kernel_d1_twin_readonly_conformance_v0.1"
)
LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"
IMPLEMENTATION_IDENTITY_HASH = (
    "sha256:25e89d3eef7f13f5b65b839b06895b7"
    "c498753dcf4c955aa4d6c375235a0246d"
)
D1_ADMISSION_RECORD_HASH = (
    "sha256:a43e7baeaae5f32e14c60694b9cc6cfa"
    "258e46c5315f79d4bfdb83c0b641cc65"
)
D1_ADMISSION_EVIDENCE_HASH = (
    "sha256:ff6cc57c5ec974d55a95527aceb90bf7"
    "1f5b58e11d82aafddb9fd06300fc3b3c"
)
HARNESS_CONTRACT_IDENTITY_HASH = (
    "sha256:80794e2a91f271881b902ae386047c608"
    "c53bad9b6ff53acf4af9c9f984bd900"
)
SI002_CONTRACT_RECORD_HASH = (
    "sha256:c3701736df903e9b7f4d4512c9a7e5c8"
    "16b999f5ed8ab59ce4a188235f1403be"
)
SI002_CONTRACT_RECORD_CONTENT_SHA256 = (
    "24c2d212c133f4ba921cb46547be08685"
    "23e4dcda42bb3e59fa3f7a49bf0d421"
)
SI002_POLICY_CONTENT_SHA256 = (
    "4263369a1a5fd6f2bdd39ba58cbff139"
    "2ecbb90678766f23f39ac3954a364035"
)
BOUNDED_EVALUATION_CONTRACT_HASH = (
    "sha256:9c1cae4643b95f7e2c87b6398cd096db"
    "1836ca3533cca67a1842dd037ec66858"
)
DECLARED_RESOURCE_LIMITS_HASH = (
    "sha256:6ad34ed5443dae8244dbf3e4b5ce829e"
    "cb31429f38f7d9dcc27898dcd87f7c81"
)
FAILURE_SEMANTICS_HASH = (
    "sha256:662294e36b8616d6eb94700b1b6f38dc"
    "758205eb4cbb42032ad184510d8e1c3e"
)

OWNER_GO_CONTENT_SHA256 = (
    "82db453eb72cad79e686f274496374a713"
    "e992ec05a7066186267f08d994caef"
)
AUTHORIZED_CELL = (
    "PART_B_B5_SI002_LOCAL_BOUNDED_EVALUATION_"
    "HARNESS_RUNNER_INVOCATION"
)
AUTHORITY_MODE = "TEST_ONLY_LOCAL_READONLY_INVOCATION_RECORD"

REQUEST_KIND = (
    "INVOKE_LOCAL_BOUNDED_EVALUATION_HARNESS_FOR_TEST_ONLY_RECORD"
)
INVOCATION_MODE = "TEST_ONLY_LOCAL_READONLY_FIXED_CASE"
DECLARED_CASE_ID = "TWIN-COUNTEREXAMPLE-001"
DECLARED_CASE_ORIGIN = "SYNTHETIC_LOCAL_DECLARATION_ONLY"
DECLARED_CASE_BINDING_HASH = (
    "sha256:b63a045e1b9ba151a1d1e31ffa3bcedec"
    "09306ff02a66fe09e8d2a7055d3d105"
)
SYNTHETIC_FIXTURE_CONTENT_SHA256 = (
    "5587569a376a087cd648ae8bee00081fc"
    "10a5d48b17c63087407542d4412e086"
)

RECORD_CLASS = (
    "LOCAL_BOUNDED_EVALUATION_HARNESS_RUNNER_INVOCATION_RECORD"
)
RECORD_SCOPE = (
    "LOCAL_BOUNDED_EVALUATION_HARNESS_RUNNER_INVOCATION_"
    "CONTRACT_OR_RECORD_ONLY"
)
POSITIVE_DECISION = (
    "LOCAL_BOUNDED_EVALUATION_HARNESS_RUNNER_INVOCATION_"
    "RECORDED_TEST_ONLY"
)

DECISION_TIMEOUT = "ABSTAIN_TIMEOUT_UNKNOWN_NO_RANK"
DECISION_RESOURCE = "ABSTAIN_RESOURCE_EXHAUSTION_UNKNOWN_NO_RANK"
DECISION_UNKNOWN = "ABSTAIN_UNKNOWN_NO_RANK"
DECISION_INFEASIBLE = "ABSTAIN_INFEASIBLE_SEPARATE_NO_ACTION"
DENY_TEST_AUTHORITY = "DENY_TEST_ONLY_AUTHORITY_MISMATCH"
DENY_UNKNOWN = "DENY_UNKNOWN_IMPLEMENTATION"
DENY_LEGACY = "DENY_LEGACY_IMPLEMENTATION"
DENY_MISSING = "DENY_MISSING_SI002_BINDING"
DENY_MISMATCH = "DENY_HASH_MISMATCH"
DENY_NON_SYNTHETIC = "DENY_NON_SYNTHETIC_OR_PRODUCTION_INPUT"
DENY_AUTHORITY = "DENY_AUTHORITY_REQUEST"
DENY_NON_CONTRACT = "DENY_NON_CONTRACT_INPUT"

REASON_CODES = {
    POSITIVE_DECISION: "B5-SI002-INV-000-RECORDED-TEST-ONLY",
    DECISION_TIMEOUT: "B5-SI002-INV-ABSTAIN-TIMEOUT",
    DECISION_RESOURCE: "B5-SI002-INV-ABSTAIN-RESOURCE",
    DECISION_UNKNOWN: "B5-SI002-INV-ABSTAIN-UNKNOWN",
    DECISION_INFEASIBLE: "B5-SI002-INV-ABSTAIN-INFEASIBLE",
    DENY_TEST_AUTHORITY: "B5-SI002-INV-DENY-TEST-AUTHORITY",
    DENY_UNKNOWN: "B5-SI002-INV-DENY-UNKNOWN-ID",
    DENY_LEGACY: "B5-SI002-INV-DENY-LEGACY-ID",
    DENY_MISSING: "B5-SI002-INV-DENY-MISSING-BINDING",
    DENY_MISMATCH: "B5-SI002-INV-DENY-HASH-MISMATCH",
    DENY_NON_SYNTHETIC: "B5-SI002-INV-DENY-NON-SYNTHETIC",
    DENY_AUTHORITY: "B5-SI002-INV-DENY-AUTHORITY-REQUEST",
    DENY_NON_CONTRACT: "B5-SI002-INV-DENY-NON-CONTRACT",
}

AUTHORITY_FIELDS = frozenset(
    {
        "authority_mode",
        "authorized_cell",
        "owner_go_content_sha256",
        "allowed_implementation_id",
        "synthetic_declaration_only",
        "production_registration_enabled",
        "planner_execution_authority",
        "evaluation_execution_authority",
    }
)

REQUEST_FIELDS = frozenset(
    {
        "schema_version",
        "request_kind",
        "request_version",
        "implementation_id",
        "implementation_identity_hash",
        "d1_admission_record_hash",
        "d1_admission_evidence_hash",
        "harness_contract_identity_hash",
        "si002_contract_record_hash",
        "si002_contract_record_content_sha256",
        "si002_policy_content_sha256",
        "bounded_evaluation_contract_hash",
        "declared_case_id",
        "declared_case_binding_hash",
        "declared_case_origin",
        "synthetic_fixture_content_sha256",
        "declared_resource_limits_hash",
        "failure_semantics_hash",
        "invocation_mode",
        "test_only_runner_invocation_requested",
        "production_evaluation_execution_requested",
        "planner_execution_authority",
        "evaluation_execution_authority",
        "stop_authority",
    }
)

RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "record_class",
        "record_version",
        "request_hash",
        "implementation_id",
        "implementation_identity_hash",
        "d1_admission_record_hash",
        "harness_contract_identity_hash",
        "si002_contract_record_hash",
        "declared_case_id",
        "declared_case_binding_hash",
        "synthetic_fixture_content_sha256",
        "declared_resource_limits_hash",
        "failure_semantics_hash",
        "invocation_mode",
        "decision",
        "reason_codes",
        "invocation_outcome_class",
        "actual_runner_invocation",
        "actual_evaluator_invocation",
        "delegated_decision_record_hash",
        "record_scope",
        "planner_execution_authority",
        "evaluation_execution_authority",
        "stop_authority",
        "hash",
    }
)

POLICY_FIELDS = frozenset(
    {
        "schema_version",
        "policy_id",
        "policy_version",
        "status",
        "authorized_slice",
        "admissible_implementation_ids",
        "wildcards",
        "fallback",
        "expected_implementation_identity_hash",
        "expected_d1_admission_record_hash",
        "expected_d1_admission_evidence_hash",
        "expected_harness_contract_identity_hash",
        "expected_si002_contract_record_hash",
        "expected_si002_contract_record_content_sha256",
        "expected_si002_policy_content_sha256",
        "expected_bounded_evaluation_contract_hash",
        "expected_declared_resource_limits_hash",
        "expected_failure_semantics_hash",
        "synthetic_fixture_registry",
        "positive_decision",
        "record_scope",
        "authority_effect",
        "reason_codes",
        "failure_semantics",
        "authority_ceiling",
        "hard_ban",
        "hash",
    }
)

AUTHORITY_REQUEST_FIELDS = frozenset(
    {
        "path_b_write",
        "mint",
        "kernel_or_e_case_write",
        "certificate",
        "CERTIFIED_STOP",
        "stop_requested",
        "part_b_pass",
        "full_m3_star",
        "b6_execution_requested",
        "b7_execution_requested",
        "b8_execution_requested",
        "b9_execution_requested",
        "scalar_score",
        "rank",
        "performance_claim",
        "superiority_claim",
        "scalarization_requested",
    }
)

NON_SYNTHETIC_OR_PRODUCTION_FIELDS = frozenset(
    {
        "raw_source",
        "raw_path",
        "uri",
        "external_source",
        "production_registry_state",
        "production_registration_enabled",
        "production_execution_requested",
    }
)

FORBIDDEN_NON_CONTRACT_FIELDS = frozenset(
    {
        "oracle_label",
        "hidden_ground_truth",
        "hidden_identifier",
        "actual_world_id",
        "holdout_data",
        "holdout_label",
        "realized_future_outcome",
        "action_payload",
    }
)

AUTHORITY_CEILING = {
    "production_registration_enabled": False,
    "planner_execution_authority": False,
    "evaluation_execution_authority": False,
    "scalarization_authority": False,
    "performance_claim_authority": False,
    "superiority_claim_authority": False,
    "path_b_write_authority": False,
    "mint_authority": False,
    "kernel_or_e_case_write_authority": False,
    "certificate_authority": False,
    "stop_authority": "NONE",
    "part_b_pass": False,
    "full_m3_star": False,
    "pb_b5_si_003_state": "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION",
}

FAILURE_SEMANTICS = {
    "timeout": DECISION_TIMEOUT,
    "resource_exhaustion": DECISION_RESOURCE,
    "infeasible": DECISION_INFEASIBLE,
    "unknown": DECISION_UNKNOWN,
    "missing_measurement": DECISION_UNKNOWN,
    "timeout_as_unsat": False,
    "resource_exhaustion_as_zero_or_loss": False,
    "infeasible_as_high_cost": False,
    "automatic_retry": False,
    "fallback_to_hidden_state": False,
    "scalarization": False,
}

_REPO_ROOT = Path(__file__).resolve().parents[2]
_NEW_POLICY_PATH = (
    "configs/"
    "part-b-b5-si002-local-bounded-evaluation-harness-"
    "runner-invocation-policy-v0.1.yaml"
)
_NEW_FIXTURE_PATH = (
    "tests/unit/fixtures/"
    "part_b_b5_si002_local_bounded_evaluation_harness_runner_invocation/"
    "synthetic-fixed-case-v0.1.json"
)
_TWIN_FIXTURE_PATH = (
    "tests/unit/fixtures/"
    "kernel_a17_p1e_twin_p10_readonly_wiring_v0.1.json"
)
_SI002_IDENTITY_PATH = (
    "configs/part-b-b5-si002-bounded-evaluation-harness-identity-v0.1.yaml"
)
_SI002_POLICY_PATH = (
    "configs/part-b-b5-si002-bounded-evaluation-harness-policy-v0.1.yaml"
)
_SI002_RECORD_PATH = (
    "configs/part-b-b5-si002-bounded-evaluation-harness-record-v0.1.yaml"
)

_EXPECTED_FILE_SHA256 = {
    _NEW_POLICY_PATH: (
        "0536a8a1b69c89af360df850be709bda"
        "1216296704ce872796420e553f9a1a9b"
    ),
    _NEW_FIXTURE_PATH: SYNTHETIC_FIXTURE_CONTENT_SHA256,
    _TWIN_FIXTURE_PATH: (
        "1191ba71a41c19131d7368df65ac8d345"
        "d8865af1aec59e300f7435d7536ddee"
    ),
    _SI002_IDENTITY_PATH: (
        "3c6df2df7dce5b00d26c468d6aea0fc"
        "8991ade19c649aedc3b93188a247ee1b8"
    ),
    _SI002_POLICY_PATH: SI002_POLICY_CONTENT_SHA256,
    _SI002_RECORD_PATH: SI002_CONTRACT_RECORD_CONTENT_SHA256,
    "src/planner/twin_p10_readonly_wiring.py": (
        "1e1434e40191469f17f255905f4021fb"
        "273a323672604f0a017afe0384b5b4f9"
    ),
    (
        "docs/kernel/kernel-v0.8-a17-p1e-twin-p10-readonly-wiring-"
        "owner-go-authorization-v0.1-20260728.json"
    ): (
        "b582178822621c7407e97b847b795db62"
        "e6d5002ddda21024ce9b26173ea18c3"
    ),
}

_EXPECTED_NEW_POLICY_HASH = (
    "sha256:dc8c78bb1cd666b1814b10fac9ca3e25"
    "544a00cb2b0d25977ae7a7ab2ddb2b7f"
)


class _InvocationViolation(ValueError):
    def __init__(self, decision: str):
        super().__init__(decision)
        self.decision = decision


def invoke_local_bounded_evaluation_harness_for_test_only_record(
    invocation_request: Mapping[str, Any] | object,
    *,
    test_only_authority: Mapping[str, Any] | object,
) -> dict[str, object]:
    """Invoke the one pinned local synthetic case and return a record only."""

    if not _valid_test_only_authority(test_only_authority):
        return _record(
            request=invocation_request,
            decision=DENY_TEST_AUTHORITY,
            outcome="NOT_INVOKED_FAIL_CLOSED",
            actual_runner_invocation=False,
            delegated_decision_record_hash=None,
        )

    try:
        request = _validate_request_shape_and_authority(invocation_request)
        policy, synthetic_fixture, twin_fixture = _load_and_verify_bindings()
        _validate_exact_bindings(
            request=request,
            policy=policy,
            synthetic_fixture=synthetic_fixture,
        )
        caller_input, caller_authority = _delegate_inputs(twin_fixture)
    except _InvocationViolation as exc:
        return _record(
            request=invocation_request,
            decision=exc.decision,
            outcome="NOT_INVOKED_FAIL_CLOSED",
            actual_runner_invocation=False,
            delegated_decision_record_hash=None,
        )
    except (KeyError, TypeError, ValueError, OSError, yaml.YAMLError):
        return _record(
            request=invocation_request,
            decision=DENY_MISMATCH,
            outcome="NOT_INVOKED_FAIL_CLOSED",
            actual_runner_invocation=False,
            delegated_decision_record_hash=None,
        )

    try:
        delegated = (
            twin_wiring.evaluate_twin_p10_fixed_case_for_depth1_candidacy(
                deepcopy(caller_input),
                test_only_authority=deepcopy(caller_authority),
            )
        )
    except TimeoutError:
        return _record(
            request=request,
            decision=DECISION_TIMEOUT,
            outcome="TIMEOUT_UNKNOWN_NO_RANK",
            actual_runner_invocation=True,
            delegated_decision_record_hash=None,
        )
    except MemoryError:
        return _record(
            request=request,
            decision=DECISION_RESOURCE,
            outcome="RESOURCE_EXHAUSTION_UNKNOWN_NO_RANK",
            actual_runner_invocation=True,
            delegated_decision_record_hash=None,
        )
    except Exception:
        return _record(
            request=request,
            decision=DECISION_UNKNOWN,
            outcome="UNKNOWN_NO_RANK",
            actual_runner_invocation=True,
            delegated_decision_record_hash=None,
        )

    return _record_from_delegate(request=request, delegated=delegated)


def _valid_test_only_authority(authority: object) -> bool:
    if not isinstance(authority, Mapping) or set(authority) != AUTHORITY_FIELDS:
        return False
    return (
        authority.get("authority_mode") == AUTHORITY_MODE
        and authority.get("authorized_cell") == AUTHORIZED_CELL
        and authority.get("owner_go_content_sha256")
        == OWNER_GO_CONTENT_SHA256
        and authority.get("allowed_implementation_id") == IMPLEMENTATION_ID
        and authority.get("synthetic_declaration_only") is True
        and authority.get("production_registration_enabled") is False
        and authority.get("planner_execution_authority") is False
        and authority.get("evaluation_execution_authority") is False
    )


def _validate_request_shape_and_authority(
    request: object,
) -> Mapping[str, Any]:
    if not isinstance(request, Mapping):
        raise _InvocationViolation(DENY_NON_CONTRACT)

    keys = set(request)
    if keys & AUTHORITY_REQUEST_FIELDS:
        raise _InvocationViolation(DENY_AUTHORITY)
    if keys & NON_SYNTHETIC_OR_PRODUCTION_FIELDS:
        raise _InvocationViolation(DENY_NON_SYNTHETIC)
    if keys & FORBIDDEN_NON_CONTRACT_FIELDS:
        raise _InvocationViolation(DENY_NON_CONTRACT)
    if keys - REQUEST_FIELDS:
        raise _InvocationViolation(DENY_NON_CONTRACT)
    if REQUEST_FIELDS - keys:
        raise _InvocationViolation(DENY_MISSING)

    implementation_id = request.get("implementation_id")
    if implementation_id == LEGACY_IMPLEMENTATION_ID:
        raise _InvocationViolation(DENY_LEGACY)
    if implementation_id != IMPLEMENTATION_ID:
        raise _InvocationViolation(DENY_UNKNOWN)

    if (
        request.get("planner_execution_authority") is not False
        or request.get("evaluation_execution_authority") is not False
        or request.get("stop_authority") != "NONE"
    ):
        raise _InvocationViolation(DENY_AUTHORITY)
    if request.get("production_evaluation_execution_requested") is not False:
        raise _InvocationViolation(DENY_NON_SYNTHETIC)
    if (
        request.get("declared_case_origin") != DECLARED_CASE_ORIGIN
        or request.get("invocation_mode") != INVOCATION_MODE
    ):
        raise _InvocationViolation(DENY_NON_SYNTHETIC)
    if request.get("test_only_runner_invocation_requested") is not True:
        raise _InvocationViolation(DENY_NON_CONTRACT)
    return request


def _load_and_verify_bindings() -> tuple[
    Mapping[str, Any],
    Mapping[str, Any],
    Mapping[str, Any],
]:
    for relative_path, expected in _EXPECTED_FILE_SHA256.items():
        if _file_sha256(relative_path) != expected:
            raise _InvocationViolation(DENY_MISMATCH)

    policy = _load_yaml(_NEW_POLICY_PATH)
    synthetic_fixture = _load_json(_NEW_FIXTURE_PATH)
    twin_fixture = _load_json(_TWIN_FIXTURE_PATH)
    identity = _load_yaml(_SI002_IDENTITY_PATH)
    si002_policy = _load_yaml(_SI002_POLICY_PATH)
    si002_record = _load_yaml(_SI002_RECORD_PATH)

    if (
        set(policy) != POLICY_FIELDS
        or policy.get("hash") != _EXPECTED_NEW_POLICY_HASH
        or canonical_document_hash(policy) != _EXPECTED_NEW_POLICY_HASH
        or identity.get("hash") != HARNESS_CONTRACT_IDENTITY_HASH
        or canonical_document_hash(identity) != HARNESS_CONTRACT_IDENTITY_HASH
        or si002_record.get("hash") != SI002_CONTRACT_RECORD_HASH
        or canonical_document_hash(si002_record) != SI002_CONTRACT_RECORD_HASH
        or canonical_document_hash(si002_policy) != si002_policy.get("hash")
    ):
        raise _InvocationViolation(DENY_MISMATCH)
    if (
        policy.get("reason_codes") != REASON_CODES
        or policy.get("failure_semantics") != FAILURE_SEMANTICS
        or policy.get("authority_ceiling") != AUTHORITY_CEILING
        or policy.get("hard_ban") != HARD_BAN
    ):
        raise _InvocationViolation(DENY_AUTHORITY)
    return policy, synthetic_fixture, twin_fixture


def _validate_exact_bindings(
    *,
    request: Mapping[str, Any],
    policy: Mapping[str, Any],
    synthetic_fixture: Mapping[str, Any],
) -> None:
    exact_values = {
        "schema_version": "0.8.0",
        "request_kind": REQUEST_KIND,
        "request_version": "0.1.0",
        "implementation_identity_hash": IMPLEMENTATION_IDENTITY_HASH,
        "d1_admission_record_hash": D1_ADMISSION_RECORD_HASH,
        "d1_admission_evidence_hash": D1_ADMISSION_EVIDENCE_HASH,
        "harness_contract_identity_hash": HARNESS_CONTRACT_IDENTITY_HASH,
        "si002_contract_record_hash": SI002_CONTRACT_RECORD_HASH,
        "si002_contract_record_content_sha256": (
            SI002_CONTRACT_RECORD_CONTENT_SHA256
        ),
        "si002_policy_content_sha256": SI002_POLICY_CONTENT_SHA256,
        "bounded_evaluation_contract_hash": (
            BOUNDED_EVALUATION_CONTRACT_HASH
        ),
        "declared_case_id": DECLARED_CASE_ID,
        "declared_case_binding_hash": DECLARED_CASE_BINDING_HASH,
        "synthetic_fixture_content_sha256": (
            SYNTHETIC_FIXTURE_CONTENT_SHA256
        ),
        "declared_resource_limits_hash": DECLARED_RESOURCE_LIMITS_HASH,
        "failure_semantics_hash": FAILURE_SEMANTICS_HASH,
    }
    if any(request.get(key) != value for key, value in exact_values.items()):
        raise _InvocationViolation(DENY_MISMATCH)

    policy_values = {
        "admissible_implementation_ids": [IMPLEMENTATION_ID],
        "wildcards": False,
        "fallback": False,
        "expected_implementation_identity_hash": (
            IMPLEMENTATION_IDENTITY_HASH
        ),
        "expected_d1_admission_record_hash": D1_ADMISSION_RECORD_HASH,
        "expected_d1_admission_evidence_hash": D1_ADMISSION_EVIDENCE_HASH,
        "expected_harness_contract_identity_hash": (
            HARNESS_CONTRACT_IDENTITY_HASH
        ),
        "expected_si002_contract_record_hash": SI002_CONTRACT_RECORD_HASH,
        "expected_si002_contract_record_content_sha256": (
            SI002_CONTRACT_RECORD_CONTENT_SHA256
        ),
        "expected_si002_policy_content_sha256": (
            SI002_POLICY_CONTENT_SHA256
        ),
        "expected_bounded_evaluation_contract_hash": (
            BOUNDED_EVALUATION_CONTRACT_HASH
        ),
        "expected_declared_resource_limits_hash": (
            DECLARED_RESOURCE_LIMITS_HASH
        ),
        "expected_failure_semantics_hash": FAILURE_SEMANTICS_HASH,
        "positive_decision": POSITIVE_DECISION,
        "record_scope": RECORD_SCOPE,
        "authority_effect": "NONE_RECORD_ONLY",
    }
    if any(policy.get(key) != value for key, value in policy_values.items()):
        raise _InvocationViolation(DENY_MISMATCH)

    registry = policy.get("synthetic_fixture_registry")
    if not isinstance(registry, list) or len(registry) != 1:
        raise _InvocationViolation(DENY_MISSING)
    registry_entry = registry[0]
    if not isinstance(registry_entry, Mapping):
        raise _InvocationViolation(DENY_MISSING)
    expected_registry = {
        "fixture_id": (
            "part-b-b5-si002-local-bounded-evaluation-harness-"
            "runner-invocation-synthetic-fixed-case-v0.1"
        ),
        "declared_case_id": DECLARED_CASE_ID,
        "fixture_origin": DECLARED_CASE_ORIGIN,
        "fixture_content_sha256": SYNTHETIC_FIXTURE_CONTENT_SHA256,
        "declared_case_binding_hash": DECLARED_CASE_BINDING_HASH,
    }
    if dict(registry_entry) != expected_registry:
        raise _InvocationViolation(DENY_MISMATCH)

    fixture_exact = {
        "schema_version": "0.8.0",
        "fixture_id": expected_registry["fixture_id"],
        "fixture_origin": DECLARED_CASE_ORIGIN,
        "declared_case_id": DECLARED_CASE_ID,
        "delegate_profile": "PINNED_TWIN_P10_D1_READONLY_CANDIDACY_NO_TRACE",
        "expected_delegate_wiring_status": (
            twin_wiring.STATUS_SIDECAR_NO_TRACE
        ),
        "authority_ceiling": AUTHORITY_CEILING,
        "hard_ban": HARD_BAN,
    }
    if set(synthetic_fixture) != {
        *fixture_exact,
        "case_declaration",
    } or any(
        synthetic_fixture.get(key) != value
        for key, value in fixture_exact.items()
    ):
        raise _InvocationViolation(DENY_MISMATCH)
    if (
        canonical_value_hash(synthetic_fixture.get("case_declaration"))
        != DECLARED_CASE_BINDING_HASH
    ):
        raise _InvocationViolation(DENY_MISMATCH)


def _delegate_inputs(
    twin_fixture: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    caller_inputs = twin_fixture.get("caller_inputs")
    authority = twin_fixture.get("test_only_authority")
    if not isinstance(caller_inputs, Mapping) or not isinstance(
        authority, Mapping
    ):
        raise _InvocationViolation(DENY_MISMATCH)
    caller_input = caller_inputs.get("none")
    if not isinstance(caller_input, Mapping):
        raise _InvocationViolation(DENY_MISMATCH)
    if (
        caller_input.get("fixed_case_id") != DECLARED_CASE_ID
        or caller_input.get("resource_trace_binding_mode") != "NONE"
        or caller_input.get("historical_resource_trace_attempt_id")
        is not None
    ):
        raise _InvocationViolation(DENY_MISMATCH)
    return caller_input, authority


def _record_from_delegate(
    *,
    request: Mapping[str, Any],
    delegated: object,
) -> dict[str, object]:
    if not isinstance(delegated, Mapping):
        return _record(
            request=request,
            decision=DECISION_UNKNOWN,
            outcome="UNKNOWN_NO_RANK",
            actual_runner_invocation=True,
            delegated_decision_record_hash=None,
        )

    decision_record = delegated.get("decision_record")
    if (
        delegated.get("wiring_status")
        == twin_wiring.STATUS_SIDECAR_NO_TRACE
        and isinstance(decision_record, Mapping)
        and decision_record.get("decision") == "SELECT_ACTION"
    ):
        return _record(
            request=request,
            decision=POSITIVE_DECISION,
            outcome="COMPLETED_DECLARED_CASE",
            actual_runner_invocation=True,
            delegated_decision_record_hash=canonical_value_hash(
                decision_record
            ),
        )
    if (
        isinstance(decision_record, Mapping)
        and decision_record.get("decision") == "ABSTAIN"
    ):
        return _record(
            request=request,
            decision=DECISION_INFEASIBLE,
            outcome="INFEASIBLE_SEPARATE_NO_ACTION",
            actual_runner_invocation=True,
            delegated_decision_record_hash=canonical_value_hash(
                decision_record
            ),
        )
    return _record(
        request=request,
        decision=DECISION_UNKNOWN,
        outcome="UNKNOWN_NO_RANK",
        actual_runner_invocation=True,
        delegated_decision_record_hash=(
            canonical_value_hash(decision_record)
            if isinstance(decision_record, Mapping)
            else None
        ),
    )


def _record(
    *,
    request: object,
    decision: str,
    outcome: str,
    actual_runner_invocation: bool,
    delegated_decision_record_hash: str | None,
) -> dict[str, object]:
    if decision not in REASON_CODES:
        decision = DENY_NON_CONTRACT
        outcome = "NOT_INVOKED_FAIL_CLOSED"
        actual_runner_invocation = False
        delegated_decision_record_hash = None

    record = {
        "schema_version": "0.8.0",
        "record_class": RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": _safe_request_hash(request),
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_identity_hash": IMPLEMENTATION_IDENTITY_HASH,
        "d1_admission_record_hash": D1_ADMISSION_RECORD_HASH,
        "harness_contract_identity_hash": HARNESS_CONTRACT_IDENTITY_HASH,
        "si002_contract_record_hash": SI002_CONTRACT_RECORD_HASH,
        "declared_case_id": DECLARED_CASE_ID,
        "declared_case_binding_hash": DECLARED_CASE_BINDING_HASH,
        "synthetic_fixture_content_sha256": (
            SYNTHETIC_FIXTURE_CONTENT_SHA256
        ),
        "declared_resource_limits_hash": DECLARED_RESOURCE_LIMITS_HASH,
        "failure_semantics_hash": FAILURE_SEMANTICS_HASH,
        "invocation_mode": INVOCATION_MODE,
        "decision": decision,
        "reason_codes": [REASON_CODES[decision]],
        "invocation_outcome_class": outcome,
        "actual_runner_invocation": actual_runner_invocation,
        "actual_evaluator_invocation": False,
        "delegated_decision_record_hash": (
            delegated_decision_record_hash
        ),
        "record_scope": RECORD_SCOPE,
        "planner_execution_authority": False,
        "evaluation_execution_authority": False,
        "stop_authority": "NONE",
    }
    if set(record) != RECORD_FIELDS - {"hash"} or len(record) != 25:
        raise AssertionError("invocation record shape drift")
    record["hash"] = canonical_document_hash(record)
    return record


def _safe_request_hash(request: object) -> str:
    try:
        return canonical_value_hash(request)
    except (TypeError, ValueError):
        return canonical_value_hash(
            {"invalid_invocation_request_type": type(request).__name__}
        )


def _repo_path(relative_path: str) -> Path:
    path = (_REPO_ROOT / relative_path).resolve()
    try:
        path.relative_to(_REPO_ROOT)
    except ValueError as exc:
        raise _InvocationViolation(DENY_MISMATCH) from exc
    if not path.is_file():
        raise _InvocationViolation(DENY_MISSING)
    return path


def _file_sha256(relative_path: str) -> str:
    return hashlib.sha256(_repo_path(relative_path).read_bytes()).hexdigest()


def _load_json(relative_path: str) -> dict[str, Any]:
    value = json.loads(_repo_path(relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise _InvocationViolation(DENY_MISMATCH)
    return value


def _load_yaml(relative_path: str) -> dict[str, Any]:
    value = yaml.safe_load(
        _repo_path(relative_path).read_text(encoding="utf-8")
    )
    if not isinstance(value, dict):
        raise _InvocationViolation(DENY_MISMATCH)
    return value


__all__ = [
    "AUTHORITY_CEILING",
    "AUTHORITY_FIELDS",
    "AUTHORIZED_CELL",
    "AUTHORITY_MODE",
    "DECLARED_CASE_BINDING_HASH",
    "DECLARED_CASE_ID",
    "DECLARED_CASE_ORIGIN",
    "EVALUATION_EXECUTION_AUTHORITY",
    "FAILURE_SEMANTICS",
    "HARD_BAN",
    "IMPLEMENTATION_ID",
    "INVOCATION_MODE",
    "OWNER_GO_CONTENT_SHA256",
    "PLANNER_EXECUTION_AUTHORITY",
    "POSITIVE_DECISION",
    "PRODUCTION_REGISTRATION_ENABLED",
    "RECORD_FIELDS",
    "RECORD_SCOPE",
    "REQUEST_FIELDS",
    "REQUEST_KIND",
    "SYNTHETIC_FIXTURE_CONTENT_SHA256",
    "invoke_local_bounded_evaluation_harness_for_test_only_record",
]
