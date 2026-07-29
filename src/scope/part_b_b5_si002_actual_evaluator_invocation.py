"""Test-only SI-002 actual evaluator invocation evidence.

The wrapper admits one local synthetic request, verifies every authority and
content pin before calling the accepted Twin/P10 capability exactly once, and
returns a class-3-conformant evidence instance inside a class-4 decision
record.  It grants no evaluation/planner execution authority, flip, production
registration, Part B status, write authority, certificate, or STOP authority.
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
    has_valid_document_hash,
)
from src.planner import twin_p10_readonly_wiring as twin_wiring


PRODUCTION_REGISTRATION_ENABLED = False
EVALUATION_EXECUTION_AUTHORITY = False
PLANNER_EXECUTION_AUTHORITY = False
AUTHORITY_FLIP_ELIGIBLE = False

HARD_BAN = (
    "Path A / Kernel design GREEN must not be inferred as L2 PASS, "
    "Part B PASS, or unrestricted Part B elevation."
)

IMPLEMENTATION_ID = "part_b_b5_m3_kernel_d1_twin_readonly_conformance_v0.1"
LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"
EVALUATOR_CAPABILITY_ID = (
    "part_b_b5_si002_twin_p10_fixed_case_depth1_"
    "candidacy_evaluator_v0.1"
)
EVALUATOR_CAPABILITY_IDENTITY_HASH = (
    "sha256:7a0a87b85585d2277f1a0ea27d5cb7a3"
    "0a5cbbafb7b7759abf1214a84610da30"
)
EVALUATOR_CAPABILITY_IDENTITY_RECORD_HASH = (
    "sha256:9e56686e8da6a9747f0d438305db72e2"
    "efa0b3cf84ee407e573eb2c182d706d4"
)
EVALUATOR_CAPABILITY_IDENTITY_RECORD_CONTENT_SHA256 = (
    "cc3f169f9b0c365659b6f897ee9ae76d"
    "3941f2fe143e480422fcf4f77b7c4c43"
)
EVALUATOR_CAPABILITY_IDENTITY_ACCEPTANCE_CONTENT_SHA256 = (
    "2f97fffe9a3fc41a7c5243e096b83a83"
    "a31bee8e755572784038ed473ac5ed7d"
)

EVIDENCE_CONTRACT_ID = (
    "part_b_b5_si002_local_hash_bound_evaluator_"
    "execution_evidence_contract_v0.1"
)
EVIDENCE_CONTRACT_IDENTITY_HASH = (
    "sha256:bafdbfe4251bf353d2d7220497e81fbd"
    "9ed955a2bebe566bab39783cb5926be5"
)
EVIDENCE_CONTRACT_RECORD_HASH = (
    "sha256:24f685333264a46bab44a6364d1c636a"
    "65d0f832e2ceb73d28102ab676504864"
)
EVIDENCE_CONTRACT_RECORD_CONTENT_SHA256 = (
    "ac8f979267c83e522d024ac9458ffa345"
    "c6f1565beb516c97ff69b59b81115a4"
)
EVIDENCE_CONTRACT_ACCEPTANCE_CONTENT_SHA256 = (
    "d3e51ff1ab5d94bd3c9b4c5e67bc0bf"
    "a26dd99f4aa3a520968a89f528a010478"
)

FUTURE_EVIDENCE_REQUIRED_FIELDS = (
    "schema_version",
    "evidence_record_class",
    "evidence_record_version",
    "implementation_id",
    "evaluator_capability_id",
    "evaluator_capability_identity_hash",
    "evidence_contract_id",
    "evidence_contract_identity_hash",
    "evaluator_invocation_attempt_id",
    "evaluator_invocation_request_hash",
    "evaluator_input_hash",
    "evaluator_output_hash",
    "invocation_mode",
    "actual_evaluator_invocation",
    "evaluation_execution_authority",
    "production_registration_enabled",
    "evidence_hash",
)
FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH = (
    "sha256:42040c0d8e656899caaf4eff27e46bac"
    "11bdbddbcfe8ab11d9b20a14047566ad"
)
FUTURE_EVIDENCE_HASH_BINDING_FIELDS = (
    "implementation_id",
    "evaluator_capability_id",
    "evaluator_capability_identity_hash",
    "evidence_contract_identity_hash",
    "evaluator_invocation_attempt_id",
    "evaluator_invocation_request_hash",
    "evaluator_input_hash",
    "evaluator_output_hash",
)
FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH = (
    "sha256:f3e4994a2d39e35e4381dd93ad6423cc"
    "d902d70e7a5730f380689abe79f303e7"
)

REQUEST_KIND = "INVOKE_SI002_ACTUAL_EVALUATOR_FOR_TEST_ONLY_EVIDENCE_RECORD"
REQUESTED_SCOPE = (
    "LOCAL_ACTUAL_EVALUATOR_INVOCATION_EVIDENCE_"
    "CONTRACT_OR_RECORD_ONLY"
)
INVOCATION_MODE = (
    "TEST_ONLY_LOCAL_SYNTHETIC_DIRECT_CAPABILITY_"
    "INVOCATION_NO_AUTHORITY"
)
RECORD_CLASS = "LOCAL_ACTUAL_EVALUATOR_INVOCATION_EVIDENCE_DECISION_RECORD"
EVIDENCE_RECORD_CLASS = "LOCAL_HASH_BOUND_EVALUATOR_EXECUTION_EVIDENCE_RECORD"
AUTHORITY_EFFECT = "NONE_TEST_ONLY_EVIDENCE_RECORD_ONLY"
CATALOG_PREREQUISITE = "ACTUAL_EVALUATOR_INVOCATION_EVIDENCE"
CLASS_2_STATUS = "ESTABLISHED"
CLASS_3_STATUS = "ESTABLISHED_CONTRACT_SURFACE_ONLY"
MISSING_STATUS = "MISSING"
SI003_STATE = "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION"

AUTHORITY_KIND = "TEST_ONLY_LOCAL_ACTUAL_EVALUATOR_INVOCATION_EVIDENCE"
AUTHORIZED_CELL = "PART_B_B5_SI002_ACTUAL_EVALUATOR_INVOCATION_GREEN"
AUTHORITY_BASE_COMMIT = "a5bd739b65c71abfbf170ba0225d162da5a03444"
OWNER_GO_CONTENT_SHA256 = (
    "fc3f3c75f5105524d0460d714531e7b7"
    "bf752fdffb7ef623683d6d9c4ff4b99a"
)

POSITIVE_DECISION = (
    "LOCAL_ACTUAL_EVALUATOR_INVOCATION_EVIDENCE_"
    "VALID_NO_AUTHORITY_NO_FLIP"
)
DENY_TEST_ONLY_AUTHORITY = "DENY_TEST_ONLY_AUTHORITY"
DENY_UNKNOWN_IMPLEMENTATION = "DENY_UNKNOWN_IMPLEMENTATION"
DENY_UNKNOWN_CAPABILITY_ID = "DENY_UNKNOWN_CAPABILITY_ID"
DENY_LEGACY_IMPLEMENTATION = "DENY_LEGACY_IMPLEMENTATION"
DENY_MISSING_CLASS2_BINDING = "DENY_MISSING_CLASS2_BINDING"
DENY_CLASS2_HASH_MISMATCH = "DENY_CLASS2_HASH_MISMATCH"
DENY_MISSING_CLASS3_BINDING = "DENY_MISSING_CLASS3_BINDING"
DENY_CLASS3_HASH_MISMATCH = "DENY_CLASS3_HASH_MISMATCH"
DENY_EVIDENCE_FIELD_CATALOG_MISMATCH = (
    "DENY_EVIDENCE_FIELD_CATALOG_MISMATCH"
)
DENY_MISSING_SI002_CHAIN_BINDING = "DENY_MISSING_SI002_CHAIN_BINDING"
DENY_SI002_CHAIN_HASH_MISMATCH = "DENY_SI002_CHAIN_HASH_MISMATCH"
DENY_CALLABLE_IDENTITY_MISMATCH = "DENY_CALLABLE_IDENTITY_MISMATCH"
DENY_FIXTURE_IDENTITY_MISMATCH = "DENY_FIXTURE_IDENTITY_MISMATCH"
DENY_INVOCATION_MODE_OR_PRODUCTION_SCOPE = (
    "DENY_INVOCATION_MODE_OR_PRODUCTION_SCOPE"
)
DENY_RUNNER_INVOCATION_RECLASSIFICATION = (
    "DENY_RUNNER_INVOCATION_RECLASSIFICATION"
)
DENY_EVALUATOR_INVOCATION_FAILURE = "DENY_EVALUATOR_INVOCATION_FAILURE"
DENY_EVALUATOR_OUTPUT_MISMATCH = "DENY_EVALUATOR_OUTPUT_MISMATCH"
DENY_AUTHORITY_OR_BINDING_REQUEST = "DENY_AUTHORITY_OR_BINDING_REQUEST"
DENY_CATALOG_SCOPE_OVERREACH = "DENY_CATALOG_SCOPE_OVERREACH"
DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT = (
    "DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT"
)
DENY_SI003_OR_PART_B_SCOPE = "DENY_SI003_OR_PART_B_SCOPE"
DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT = (
    "DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT"
)

DECISION_ENUM = (
    POSITIVE_DECISION,
    DENY_TEST_ONLY_AUTHORITY,
    DENY_UNKNOWN_IMPLEMENTATION,
    DENY_UNKNOWN_CAPABILITY_ID,
    DENY_LEGACY_IMPLEMENTATION,
    DENY_MISSING_CLASS2_BINDING,
    DENY_CLASS2_HASH_MISMATCH,
    DENY_MISSING_CLASS3_BINDING,
    DENY_CLASS3_HASH_MISMATCH,
    DENY_EVIDENCE_FIELD_CATALOG_MISMATCH,
    DENY_MISSING_SI002_CHAIN_BINDING,
    DENY_SI002_CHAIN_HASH_MISMATCH,
    DENY_CALLABLE_IDENTITY_MISMATCH,
    DENY_FIXTURE_IDENTITY_MISMATCH,
    DENY_INVOCATION_MODE_OR_PRODUCTION_SCOPE,
    DENY_RUNNER_INVOCATION_RECLASSIFICATION,
    DENY_EVALUATOR_INVOCATION_FAILURE,
    DENY_EVALUATOR_OUTPUT_MISMATCH,
    DENY_AUTHORITY_OR_BINDING_REQUEST,
    DENY_CATALOG_SCOPE_OVERREACH,
    DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT,
    DENY_SI003_OR_PART_B_SCOPE,
    DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT,
)

REASON_CODES = {
    POSITIVE_DECISION: "B5-SI002-ACTUAL-EVAL-000-VALID-NO-AUTHORITY-NO-FLIP",
    DENY_TEST_ONLY_AUTHORITY: "B5-SI002-ACTUAL-EVAL-DENY-TEST-AUTHORITY",
    DENY_UNKNOWN_IMPLEMENTATION: "B5-SI002-ACTUAL-EVAL-DENY-IMPLEMENTATION",
    DENY_UNKNOWN_CAPABILITY_ID: "B5-SI002-ACTUAL-EVAL-DENY-CAPABILITY",
    DENY_LEGACY_IMPLEMENTATION: "B5-SI002-ACTUAL-EVAL-DENY-LEGACY",
    DENY_MISSING_CLASS2_BINDING: "B5-SI002-ACTUAL-EVAL-DENY-MISSING-CLASS2",
    DENY_CLASS2_HASH_MISMATCH: "B5-SI002-ACTUAL-EVAL-DENY-CLASS2-HASH",
    DENY_MISSING_CLASS3_BINDING: "B5-SI002-ACTUAL-EVAL-DENY-MISSING-CLASS3",
    DENY_CLASS3_HASH_MISMATCH: "B5-SI002-ACTUAL-EVAL-DENY-CLASS3-HASH",
    DENY_EVIDENCE_FIELD_CATALOG_MISMATCH: "B5-SI002-ACTUAL-EVAL-DENY-EVIDENCE-CATALOG",
    DENY_MISSING_SI002_CHAIN_BINDING: "B5-SI002-ACTUAL-EVAL-DENY-MISSING-SI002",
    DENY_SI002_CHAIN_HASH_MISMATCH: "B5-SI002-ACTUAL-EVAL-DENY-SI002-HASH",
    DENY_CALLABLE_IDENTITY_MISMATCH: "B5-SI002-ACTUAL-EVAL-DENY-CALLABLE",
    DENY_FIXTURE_IDENTITY_MISMATCH: "B5-SI002-ACTUAL-EVAL-DENY-FIXTURE",
    DENY_INVOCATION_MODE_OR_PRODUCTION_SCOPE: "B5-SI002-ACTUAL-EVAL-DENY-MODE",
    DENY_RUNNER_INVOCATION_RECLASSIFICATION: "B5-SI002-ACTUAL-EVAL-DENY-RUNNER-RECLASS",
    DENY_EVALUATOR_INVOCATION_FAILURE: "B5-SI002-ACTUAL-EVAL-DENY-INVOKE-FAILURE",
    DENY_EVALUATOR_OUTPUT_MISMATCH: "B5-SI002-ACTUAL-EVAL-DENY-OUTPUT",
    DENY_AUTHORITY_OR_BINDING_REQUEST: "B5-SI002-ACTUAL-EVAL-DENY-AUTHORITY-BINDING",
    DENY_CATALOG_SCOPE_OVERREACH: "B5-SI002-ACTUAL-EVAL-DENY-CATALOG-SCOPE",
    DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT: "B5-SI002-ACTUAL-EVAL-DENY-NONDETERMINISTIC",
    DENY_SI003_OR_PART_B_SCOPE: "B5-SI002-ACTUAL-EVAL-DENY-SI003-PART-B",
    DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT: "B5-SI002-ACTUAL-EVAL-DENY-NON-CONTRACT",
}

AUTHORITY_FIELDS = frozenset(
    {
        "schema_version",
        "authority_kind",
        "authorized_cell",
        "authority_base_commit",
        "owner_go_content_sha256",
    }
)

REQUEST_FIELDS = frozenset(
    {
        "schema_version", "request_kind", "request_version", "requested_scope",
        "implementation_id", "evaluator_capability_id",
        "evaluator_capability_identity_hash",
        "evaluator_capability_identity_record_hash",
        "evaluator_capability_identity_record_content_sha256",
        "evaluator_capability_identity_acceptance_content_sha256",
        "evidence_contract_id", "evidence_contract_identity_hash",
        "evidence_contract_record_hash",
        "evidence_contract_record_content_sha256",
        "evidence_contract_acceptance_content_sha256",
        "future_evidence_required_fields_hash",
        "future_evidence_required_field_count",
        "future_evidence_hash_binding_fields_hash",
        "future_evidence_hash_binding_field_count",
        "candidate_module_path", "candidate_entrypoint",
        "candidate_module_content_sha256",
        "deterministic_dependency_content_sha256",
        "twin_fixture_path", "twin_fixture_content_sha256",
        "p1e_fixture_path", "p1e_fixture_content_sha256",
        "invocation_fixture_path", "invocation_fixture_content_sha256",
        "declared_case_id", "invocation_mode",
        "expected_evaluator_wiring_status",
        "expected_evaluator_decision_record_hash",
        "si002_contract_record_hash", "si002_contract_record_content_sha256",
        "si002_invocation_record_hash", "si002_invocation_record_content_sha256",
        "si002_boundary_record_hash", "si002_boundary_record_content_sha256",
        "si002_gap_catalog_record_hash",
        "si002_gap_catalog_record_content_sha256",
        "si002_gap_catalog_acceptance_content_sha256",
        "catalog_class_2_status", "catalog_class_3_status",
        "catalog_class_1_status", "catalog_class_5_status",
        "evaluation_execution_authority", "planner_execution_authority",
        "production_registration_enabled", "pb_b5_si_003_state",
        "test_only_runner_invocation_reclassified_as_evaluator_evidence",
        "requested_actual_evaluator_invocation", "authority_flip_requested",
        "evidence_to_authority_binding_requested", "part_b_pass_requested",
        "stop_requested",
    }
)

ATTEMPT_BINDING_FIELDS = (
    "implementation_id", "evaluator_capability_id",
    "evaluator_capability_identity_hash", "evidence_contract_identity_hash",
    "candidate_module_content_sha256",
    "deterministic_dependency_content_sha256",
    "twin_fixture_content_sha256", "p1e_fixture_content_sha256",
    "invocation_fixture_content_sha256", "declared_case_id",
    "invocation_mode", "expected_evaluator_decision_record_hash",
)

POLICY_PATH = "configs/part-b-b5-si002-actual-evaluator-invocation-policy-v0.1.yaml"
POLICY_CONTENT_SHA256 = (
    "2ff0c7bea3999c2ecf56d006fe426421"
    "943aa22af4c225a5c00cd7acece14c29"
)
POLICY_CANONICAL_HASH = (
    "sha256:b7877bf559de120fae0f2105a7a2932a"
    "13dd8692427a54b3d0e609e802b9a440"
)
FIXTURE_PATH = (
    "tests/unit/fixtures/part_b_b5_si002_actual_evaluator_invocation/"
    "synthetic-fixed-case-v0.1.json"
)
FIXTURE_CONTENT_SHA256 = (
    "7fd071be1a2662f7edff7285da0d994d"
    "512c8e4523e2ff76de3c70959e531037"
)
TWIN_FIXTURE_PATH = "tests/unit/fixtures/kernel_a17_p1e_twin_p10_readonly_wiring_v0.1.json"

PINNED_FILES = {
    "docs/kernel/part-b-b5-si002-evaluator-execution-capability-identity-green-owner-acceptance-v0.1-20260728.json": "2f97fffe9a3fc41a7c5243e096b83a83a31bee8e755572784038ed473ac5ed7d",
    "configs/part-b-b5-si002-evaluator-execution-capability-identity-record-v0.1.yaml": "cc3f169f9b0c365659b6f897ee9ae76d3941f2fe143e480422fcf4f77b7c4c43",
    "docs/kernel/part-b-b5-si002-evaluator-execution-evidence-record-green-owner-acceptance-v0.1-20260728.json": "d3e51ff1ab5d94bd3c9b4c5e67bc0bfa26dd99f4aa3a520968a89f528a010478",
    "schemas/part-b-b5-si002-evaluator-execution-evidence-record.schema.json": "fc24f3bea77f9cc0e14653b47669598050a6634f7cd7188354d1c5f7658112c9",
    "configs/part-b-b5-si002-evaluator-execution-evidence-record-policy-v0.1.yaml": "94ab49361faed1a11164fbf95e901786d33af2d06d26d46647a42a7ce007bdb9",
    "configs/part-b-b5-si002-evaluator-execution-evidence-record-v0.1.yaml": "ac8f979267c83e522d024ac9458ffa345c6f1565beb516c97ff69b59b81115a4",
    "configs/part-b-b5-si002-bounded-evaluation-harness-record-v0.1.yaml": "24c2d212c133f4ba921cb46547be0868523e4dcda42bb3e59fa3f7a49bf0d421",
    "configs/part-b-b5-si002-local-bounded-evaluation-harness-runner-invocation-record-v0.1.yaml": "bdbb4a6aea269503eb127bbbc949517ee995f042d09a3810e8af96bfbe30b851",
    "configs/part-b-b5-si002-evaluation-execution-authority-boundary-record-v0.1.yaml": "df8a28daeb194a99019dc348e45a51d0906da8b8db9fda154f4c7a0848b923a5",
    "configs/part-b-b5-si002-evaluation-execution-authority-flip-prerequisite-gap-record-v0.1.yaml": "9066ca092e6d0cf6888e3846a85b3656d574bf590b856da7e993ba69a0d1d5f3",
    "docs/kernel/part-b-b5-si002-evaluation-execution-authority-flip-prerequisite-gap-green-owner-acceptance-v0.1-20260728.json": "69e350764c99ea752675b8848894ac876ce5f1bf4eec791f7850b14dd49802fd",
    "src/planner/deterministic_depth1.py": "ada6a8065e71fda58dde7e2b71ca19d7aded9a39f4cf5f67fb20d6fc5d7e38ff",
    "src/planner/twin_p10_readonly_wiring.py": "1e1434e40191469f17f255905f4021fb273a323672604f0a017afe0384b5b4f9",
    "src/scope/part_b_b5_planner_admission.py": "c6af7e4cbfa9bd98fbc525887456cb2dfaefa19362f4104c5147d1f3943d0be1",
    "src/scope/part_b_b5_si002_bounded_evaluation_harness_contract.py": "6ec634666aaa4fc02ad009abf33a6f3141119f74792e50bb0724dc8a828c947b",
    "src/scope/part_b_b5_si002_local_bounded_evaluation_harness_runner_invocation.py": "35a2cb52d19126d3934cc30e3989bfd1b8028d4542b614fbbaa649373aff863b",
    "src/scope/part_b_b5_si002_evaluation_execution_authority_boundary.py": "a6c60358a935fbbe9cacd5d703f343a8dba6d177b5a26442749a270ebb76e5cf",
    "src/scope/part_b_b5_si002_evaluation_execution_authority_flip_prerequisite_gap.py": "c97d813817c4dbf7a789a187de65aad594ef9f93787280c7cb10a24e52afd793",
    "src/scope/part_b_b5_si002_evaluator_execution_capability_identity.py": "afcf07b5538d1d4f950488411dcbe6a0fe91f8d96f2403aa68157b5e3bf09349",
    "src/scope/part_b_b5_si002_evaluator_execution_evidence_record.py": "7480de3ee3eab25b4a82c7c6cd2f788980ec1a32f196c34a2255d0bac561202e",
    "docs/llm-editor/llm-editor-v0.8-l2-capacity-audit-metadata-only-v0.1-20260722.json": "711080b388af102a2d55fb1cc22853c0ed0cbdb738483d4d7de709f6459f9db6",
    "src/compiler/llm/kernel_readonly_experiment_matrix_runner.py": "1df1cf43c88289c6877b73ce934ccd6e429641c2a91774b1d59d820292522e0e",
    "docs/llm-editor/fixtures/kernel-readonly-experiment-matrix/project05-depth2-public-v0.1/matrix-result.json": "9cdfdb7fc87e9ac41ad58c8975ad6428202fd974ef8c9cf453d9a8e67611ff42",
    TWIN_FIXTURE_PATH: "1191ba71a41c19131d7368df65ac8d345d8865af1aec59e300f7435d7536ddee",
    "tests/unit/fixtures/kernel_a17_p1e_depth1_planner_v0.1.json": "1154c5dec1073e0f42efa734212a6658d9fd9c4492016bbfd484ed7a502d088b",
    "tests/unit/fixtures/part_b_b5_si002_local_bounded_evaluation_harness_runner_invocation/synthetic-fixed-case-v0.1.json": "5587569a376a087cd648ae8bee00081fc10a5d48b17c63087407542d4412e086",
}


class _InvocationViolation(ValueError):
    def __init__(self, decision: str):
        super().__init__(decision)
        self.decision = decision


def invoke_si002_actual_evaluator_for_test_only_evidence_record(
    invocation_request: Mapping[str, Any] | object,
    *,
    test_only_authority: Mapping[str, Any] | object,
) -> dict[str, object]:
    """Invoke one pinned synthetic evaluator capability and return evidence."""

    if not _valid_test_only_authority(test_only_authority):
        return _record(invocation_request, DENY_TEST_ONLY_AUTHORITY)

    try:
        policy, fixture, twin_fixture = _load_and_verify_bindings()
        request = _validate_request(invocation_request, fixture)
        _validate_policy(policy)
        caller_input, caller_authority = _delegate_inputs(twin_fixture)
    except _InvocationViolation as exc:
        return _record(invocation_request, exc.decision)
    except (KeyError, TypeError, ValueError, OSError, yaml.YAMLError):
        return _record(
            invocation_request,
            DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT,
        )

    request_hash = canonical_value_hash(dict(request))
    attempt_id = canonical_value_hash(
        {key: request[key] for key in ATTEMPT_BINDING_FIELDS}
    )
    input_hash = canonical_value_hash(dict(caller_input))

    try:
        delegated = twin_wiring.evaluate_twin_p10_fixed_case_for_depth1_candidacy(
            deepcopy(caller_input),
            test_only_authority=deepcopy(caller_authority),
        )
    except Exception:
        return _record(request, DENY_EVALUATOR_INVOCATION_FAILURE)

    if not isinstance(delegated, Mapping):
        return _record(request, DENY_EVALUATOR_INVOCATION_FAILURE)
    decision_record = delegated.get("decision_record")
    if (
        delegated.get("wiring_status")
        != request["expected_evaluator_wiring_status"]
        or not isinstance(decision_record, Mapping)
        or decision_record.get("decision") != "SELECT_ACTION"
    ):
        return _record(request, DENY_EVALUATOR_OUTPUT_MISMATCH)
    decision_record_hash = canonical_value_hash(dict(decision_record))
    if decision_record_hash != request["expected_evaluator_decision_record_hash"]:
        return _record(request, DENY_EVALUATOR_OUTPUT_MISMATCH)

    output_hash = canonical_value_hash(dict(delegated))
    evidence = _evidence_record(
        request_hash=request_hash,
        attempt_id=attempt_id,
        input_hash=input_hash,
        output_hash=output_hash,
    )
    return _record(
        request,
        POSITIVE_DECISION,
        request_hash=request_hash,
        attempt_id=attempt_id,
        input_hash=input_hash,
        output_hash=output_hash,
        decision_record_hash=decision_record_hash,
        evidence=evidence,
    )


def _valid_test_only_authority(authority: object) -> bool:
    if not isinstance(authority, Mapping) or set(authority) != AUTHORITY_FIELDS:
        return False
    return dict(authority) == {
        "schema_version": "0.8.0",
        "authority_kind": AUTHORITY_KIND,
        "authorized_cell": AUTHORIZED_CELL,
        "authority_base_commit": AUTHORITY_BASE_COMMIT,
        "owner_go_content_sha256": OWNER_GO_CONTENT_SHA256,
    }


def _load_and_verify_bindings() -> tuple[
    Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]
]:
    if _file_sha256(POLICY_PATH) != POLICY_CONTENT_SHA256:
        raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)
    if _file_sha256(FIXTURE_PATH) != FIXTURE_CONTENT_SHA256:
        raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)
    for path, expected in PINNED_FILES.items():
        if _file_sha256(path) != expected:
            if "fixture" in path:
                raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)
            if "twin_p10" in path or "deterministic_depth1" in path:
                raise _InvocationViolation(DENY_CALLABLE_IDENTITY_MISMATCH)
            raise _InvocationViolation(DENY_SI002_CHAIN_HASH_MISMATCH)
    policy = _load_yaml(POLICY_PATH)
    fixture = _load_json(FIXTURE_PATH)
    twin_fixture = _load_json(TWIN_FIXTURE_PATH)
    if not has_valid_document_hash(policy) or policy.get("hash") != POLICY_CANONICAL_HASH:
        raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)
    return policy, fixture, twin_fixture


def _validate_request(
    request: object,
    fixture: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not isinstance(request, Mapping):
        raise _InvocationViolation(DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT)
    nondeterministic_or_payload_fields = {
        "random_seed", "random_uuid", "wall_clock", "process_id",
        "learned_probability", "hidden_ground_truth", "raw_payload",
    }
    if set(request) & nondeterministic_or_payload_fields:
        raise _InvocationViolation(DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT)
    if set(request) != REQUEST_FIELDS:
        raise _InvocationViolation(DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT)
    expected = fixture.get("invocation_request")
    if not isinstance(expected, Mapping) or set(expected) != REQUEST_FIELDS:
        raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)

    if request.get("implementation_id") == LEGACY_IMPLEMENTATION_ID:
        raise _InvocationViolation(DENY_LEGACY_IMPLEMENTATION)
    if request.get("implementation_id") != IMPLEMENTATION_ID:
        raise _InvocationViolation(DENY_UNKNOWN_IMPLEMENTATION)
    if request.get("evaluator_capability_id") != EVALUATOR_CAPABILITY_ID:
        raise _InvocationViolation(DENY_UNKNOWN_CAPABILITY_ID)

    class2 = {
        "evaluator_capability_identity_hash",
        "evaluator_capability_identity_record_hash",
        "evaluator_capability_identity_record_content_sha256",
        "evaluator_capability_identity_acceptance_content_sha256",
    }
    if any(request.get(key) is None for key in class2):
        raise _InvocationViolation(DENY_MISSING_CLASS2_BINDING)
    if any(request.get(key) != expected.get(key) for key in class2):
        raise _InvocationViolation(DENY_CLASS2_HASH_MISMATCH)

    class3 = {
        "evidence_contract_id", "evidence_contract_identity_hash",
        "evidence_contract_record_hash",
        "evidence_contract_record_content_sha256",
        "evidence_contract_acceptance_content_sha256",
    }
    if any(request.get(key) is None for key in class3):
        raise _InvocationViolation(DENY_MISSING_CLASS3_BINDING)
    if any(request.get(key) != expected.get(key) for key in class3):
        raise _InvocationViolation(DENY_CLASS3_HASH_MISMATCH)

    catalogs = {
        "future_evidence_required_fields_hash",
        "future_evidence_required_field_count",
        "future_evidence_hash_binding_fields_hash",
        "future_evidence_hash_binding_field_count",
    }
    if any(request.get(key) != expected.get(key) for key in catalogs):
        raise _InvocationViolation(DENY_EVIDENCE_FIELD_CATALOG_MISMATCH)

    si002 = {
        "si002_contract_record_hash", "si002_contract_record_content_sha256",
        "si002_invocation_record_hash", "si002_invocation_record_content_sha256",
        "si002_boundary_record_hash", "si002_boundary_record_content_sha256",
        "si002_gap_catalog_record_hash",
        "si002_gap_catalog_record_content_sha256",
        "si002_gap_catalog_acceptance_content_sha256",
    }
    if any(request.get(key) is None for key in si002):
        raise _InvocationViolation(DENY_MISSING_SI002_CHAIN_BINDING)
    if any(request.get(key) != expected.get(key) for key in si002):
        raise _InvocationViolation(DENY_SI002_CHAIN_HASH_MISMATCH)

    callable_fields = {
        "candidate_module_path", "candidate_entrypoint",
        "candidate_module_content_sha256",
        "deterministic_dependency_content_sha256",
    }
    if any(request.get(key) != expected.get(key) for key in callable_fields):
        raise _InvocationViolation(DENY_CALLABLE_IDENTITY_MISMATCH)
    fixture_fields = {
        "twin_fixture_path", "twin_fixture_content_sha256",
        "p1e_fixture_path", "p1e_fixture_content_sha256",
        "invocation_fixture_path", "invocation_fixture_content_sha256",
        "declared_case_id",
    }
    if any(request.get(key) != expected.get(key) for key in fixture_fields):
        raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)

    if (
        request.get("invocation_mode") != INVOCATION_MODE
        or request.get("requested_actual_evaluator_invocation") is not True
        or request.get("production_registration_enabled") is not False
    ):
        raise _InvocationViolation(DENY_INVOCATION_MODE_OR_PRODUCTION_SCOPE)
    if request.get(
        "test_only_runner_invocation_reclassified_as_evaluator_evidence"
    ) is not False:
        raise _InvocationViolation(DENY_RUNNER_INVOCATION_RECLASSIFICATION)
    if (
        request.get("evaluation_execution_authority") is not False
        or request.get("planner_execution_authority") is not False
        or request.get("authority_flip_requested") is not False
        or request.get("evidence_to_authority_binding_requested") is not False
    ):
        raise _InvocationViolation(DENY_AUTHORITY_OR_BINDING_REQUEST)
    if (
        request.get("catalog_class_2_status") != CLASS_2_STATUS
        or request.get("catalog_class_3_status") != CLASS_3_STATUS
        or request.get("catalog_class_1_status") != MISSING_STATUS
        or request.get("catalog_class_5_status") != MISSING_STATUS
    ):
        raise _InvocationViolation(DENY_CATALOG_SCOPE_OVERREACH)
    if (
        request.get("pb_b5_si_003_state") != SI003_STATE
        or request.get("part_b_pass_requested") is not False
        or request.get("stop_requested") is not False
    ):
        raise _InvocationViolation(DENY_SI003_OR_PART_B_SCOPE)
    if any(request.get(key) != value for key, value in expected.items()):
        raise _InvocationViolation(DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT)
    return request


def _validate_policy(policy: Mapping[str, Any]) -> None:
    if (
        policy.get("positive_decision") != POSITIVE_DECISION
        or policy.get("record_scope") != REQUESTED_SCOPE
        or policy.get("authority_effect") != AUTHORITY_EFFECT
        or policy.get("hard_ban") != HARD_BAN
        or policy.get("wildcards") is not False
        or policy.get("fallback") is not False
    ):
        raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)
    ceiling = policy.get("positive_authority_ceiling")
    if not isinstance(ceiling, Mapping) or dict(ceiling) != {
        "actual_evaluator_invocation": True,
        "evaluator_evidence_instance_present": True,
        "evaluation_execution_authority": False,
        "planner_execution_authority": False,
        "authority_flip_eligible": False,
        "scalarization_authority": False,
        "performance_claim_authority": False,
        "superiority_claim_authority": False,
        "path_b_write_authority": False,
        "mint_authority": False,
        "kernel_or_e_case_write_authority": False,
        "certificate_authority": False,
        "stop_authority": "NONE",
        "production_registration_enabled": False,
        "pb_b5_si_003_state": SI003_STATE,
        "part_b_pass": False,
        "full_m3_star": False,
    }:
        raise _InvocationViolation(DENY_AUTHORITY_OR_BINDING_REQUEST)


def _delegate_inputs(
    twin_fixture: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    inputs = twin_fixture.get("caller_inputs")
    authority = twin_fixture.get("test_only_authority")
    if not isinstance(inputs, Mapping) or not isinstance(authority, Mapping):
        raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)
    caller_input = inputs.get("none")
    if not isinstance(caller_input, Mapping):
        raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)
    if (
        caller_input.get("fixed_case_id") != "TWIN-COUNTEREXAMPLE-001"
        or caller_input.get("resource_trace_binding_mode") != "NONE"
        or caller_input.get("historical_resource_trace_attempt_id") is not None
    ):
        raise _InvocationViolation(DENY_FIXTURE_IDENTITY_MISMATCH)
    return caller_input, authority


def _evidence_record(
    *, request_hash: str, attempt_id: str, input_hash: str, output_hash: str
) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": "0.8.0",
        "evidence_record_class": EVIDENCE_RECORD_CLASS,
        "evidence_record_version": "0.1.0",
        "implementation_id": IMPLEMENTATION_ID,
        "evaluator_capability_id": EVALUATOR_CAPABILITY_ID,
        "evaluator_capability_identity_hash": EVALUATOR_CAPABILITY_IDENTITY_HASH,
        "evidence_contract_id": EVIDENCE_CONTRACT_ID,
        "evidence_contract_identity_hash": EVIDENCE_CONTRACT_IDENTITY_HASH,
        "evaluator_invocation_attempt_id": attempt_id,
        "evaluator_invocation_request_hash": request_hash,
        "evaluator_input_hash": input_hash,
        "evaluator_output_hash": output_hash,
        "invocation_mode": INVOCATION_MODE,
        "actual_evaluator_invocation": True,
        "evaluation_execution_authority": False,
        "production_registration_enabled": False,
    }
    record["evidence_hash"] = canonical_value_hash(record)
    return record


def _record(
    request: object,
    decision: str,
    *,
    request_hash: str | None = None,
    attempt_id: str | None = None,
    input_hash: str | None = None,
    output_hash: str | None = None,
    decision_record_hash: str | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    positive = decision == POSITIVE_DECISION and evidence is not None
    if not positive:
        request_hash = _safe_request_hash(request)
        attempt_id = input_hash = output_hash = decision_record_hash = None
        evidence = None
    request_mapping = request if isinstance(request, Mapping) else {}
    result: dict[str, object] = {
        "schema_version": "0.8.0",
        "record_class": RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": request_hash,
        "implementation_id": request_mapping.get("implementation_id"),
        "evaluator_capability_id": request_mapping.get("evaluator_capability_id"),
        "evaluator_capability_identity_hash": request_mapping.get(
            "evaluator_capability_identity_hash"
        ),
        "evidence_contract_id": request_mapping.get("evidence_contract_id"),
        "evidence_contract_identity_hash": request_mapping.get(
            "evidence_contract_identity_hash"
        ),
        "decision": decision,
        "reason_codes": [REASON_CODES[decision]],
        "record_scope": REQUESTED_SCOPE,
        "authority_effect": AUTHORITY_EFFECT,
        "invocation_contract_valid": positive,
        "evaluator_invocation_attempt_id": attempt_id,
        "evaluator_invocation_request_hash": request_hash if positive else None,
        "evaluator_input_hash": input_hash,
        "evaluator_output_hash": output_hash,
        "evaluator_decision_record_hash": decision_record_hash,
        "invocation_mode": request_mapping.get("invocation_mode"),
        "invocation_outcome_class": (
            "COMPLETED_MATCHED_HASH_BOUND_TEST_ONLY"
            if positive
            else "NOT_ACCEPTED_FAIL_CLOSED"
        ),
        "actual_evaluator_invocation": positive,
        "evaluator_evidence_instance_present": positive,
        "evidence_record": dict(evidence) if positive else None,
        "evidence_record_hash": (
            evidence.get("evidence_hash") if positive else None
        ),
        "catalog_prerequisite_addressed": (
            CATALOG_PREREQUISITE if positive else "NONE"
        ),
        "class_2_status": CLASS_2_STATUS,
        "class_3_status": CLASS_3_STATUS,
        "class_1_status": MISSING_STATUS,
        "class_5_status": MISSING_STATUS,
        "other_catalog_prerequisites_satisfied": False,
        "all_flip_prerequisites_satisfied": False,
        "authority_flip_eligible": False,
        "evaluation_execution_authority": False,
        "planner_execution_authority": False,
        "production_registration_enabled": False,
        "pb_b5_si_003_state": SI003_STATE,
        "stop_authority": "NONE",
    }
    result["hash"] = canonical_document_hash(result)
    return result


def _safe_request_hash(request: object) -> str:
    try:
        return canonical_value_hash(request)
    except (TypeError, ValueError):
        return canonical_value_hash({"non_canonical_request": True})


def _repo_path(relative_path: str) -> Path:
    return Path(__file__).resolve().parents[2] / relative_path


def _file_sha256(relative_path: str) -> str:
    return hashlib.sha256(_repo_path(relative_path).read_bytes()).hexdigest()


def _load_json(relative_path: str) -> dict[str, Any]:
    value = json.loads(_repo_path(relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("expected JSON object")
    return value


def _load_yaml(relative_path: str) -> dict[str, Any]:
    value = yaml.safe_load(_repo_path(relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("expected YAML object")
    return value


__all__ = [
    "ACTUAL_EVALUATOR_INVOCATION",
    "AUTHORITY_BASE_COMMIT",
    "AUTHORITY_FLIP_ELIGIBLE",
    "AUTHORITY_KIND",
    "AUTHORIZED_CELL",
    "DECISION_ENUM",
    "EVALUATION_EXECUTION_AUTHORITY",
    "FUTURE_EVIDENCE_HASH_BINDING_FIELDS",
    "FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH",
    "FUTURE_EVIDENCE_REQUIRED_FIELDS",
    "FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH",
    "HARD_BAN",
    "OWNER_GO_CONTENT_SHA256",
    "PLANNER_EXECUTION_AUTHORITY",
    "POSITIVE_DECISION",
    "PRODUCTION_REGISTRATION_ENABLED",
    "REQUEST_FIELDS",
    "invoke_si002_actual_evaluator_for_test_only_evidence_record",
]


ACTUAL_EVALUATOR_INVOCATION = True
