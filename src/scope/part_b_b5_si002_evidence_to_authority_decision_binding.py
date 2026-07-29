"""Pure SI-002 class-5 evidence-to-authority decision binding validator.

This module validates one exact metadata-only binding from the accepted
class-4 test-only evaluator evidence record to a decision that keeps
evaluation execution authority false pending a separate explicit Owner flip
GO.  It imports and invokes no planner, Twin wiring, evaluator, runner, or
prior SI-002 runtime.  A valid binding is not an authority flip.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.ir.canonical_hash import canonical_document_hash, canonical_value_hash


PRODUCTION_REGISTRATION_ENABLED = False
EVALUATION_EXECUTION_AUTHORITY = False
PLANNER_EXECUTION_AUTHORITY = False
AUTHORITY_FLIP_ELIGIBLE = False
EXPLICIT_LATER_OWNER_FLIP_GO_PRESENT = False

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
CLASS2_ACCEPTANCE_CONTENT_SHA256 = (
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
CLASS3_ACCEPTANCE_CONTENT_SHA256 = (
    "d3e51ff1ab5d94bd3c9b4c5e67bc0bf"
    "a26dd99f4aa3a520968a89f528a010478"
)

CLASS4_POSITIVE_DECISION = (
    "LOCAL_ACTUAL_EVALUATOR_INVOCATION_EVIDENCE_"
    "VALID_NO_AUTHORITY_NO_FLIP"
)
CLASS4_RECORD_HASH = (
    "sha256:c25472f6ba5a73c5943b06595e1776e7"
    "d53c681cc2502f8475d43aa3f57d766a"
)
CLASS4_RECORD_CONTENT_SHA256 = (
    "09cdda105a76cf465cf7e7d36f992e43"
    "dfdea692491538ab92261993d1ee631f"
)
CLASS4_ACCEPTANCE_CONTENT_SHA256 = (
    "a24c93b164fd454418e538091dd90be99"
    "70b7fc48ae199b6fd063c220e796c61"
)
CLASS4_EVIDENCE_HASH = (
    "sha256:384917e7250f29cc83bbc46ce8c603d1"
    "13aaccc9b52d3669f2be7a656540b0be"
)

SI002_CONTRACT_RECORD_HASH = (
    "sha256:c3701736df903e9b7f4d4512c9a7e5c8"
    "16b999f5ed8ab59ce4a188235f1403be"
)
SI002_CONTRACT_RECORD_CONTENT_SHA256 = (
    "24c2d212c133f4ba921cb46547be08685"
    "23e4dcda42bb3e59fa3f7a49bf0d421"
)
SI002_INVOCATION_RECORD_HASH = (
    "sha256:1ebee7beb9621d90f87b4f192c19c650"
    "a3db4bb4a1c4558546f2e5168e52860c"
)
SI002_INVOCATION_RECORD_CONTENT_SHA256 = (
    "bdbb4a6aea269503eb127bbbc949517ee"
    "995f042d09a3810e8af96bfbe30b851"
)
SI002_BOUNDARY_RECORD_HASH = (
    "sha256:440ebcc9489c3a6a850e541f78331be9"
    "92e6ffede4f9c468676de66aad344afe"
)
SI002_BOUNDARY_RECORD_CONTENT_SHA256 = (
    "df8a28daeb194a99019dc348e45a51d0"
    "906da8b8db9fda154f4c7a0848b923a5"
)
SI002_GAP_CATALOG_RECORD_HASH = (
    "sha256:520cac2587d29fb2fe569f17300d2ac28"
    "c8184e1f2a62f129136e6b738e0b092"
)
SI002_GAP_CATALOG_RECORD_CONTENT_SHA256 = (
    "9066ca092e6d0cf6888e3846a85b3656"
    "d574bf590b856da7e993ba69a0d1d5f3"
)
SI002_GAP_CATALOG_ACCEPTANCE_CONTENT_SHA256 = (
    "69e350764c99ea752675b8848894ac876"
    "ce5f1bf4eec791f7850b14dd49802fd"
)

BINDING_CONTRACT_ID = (
    "part_b_b5_si002_closed_world_evidence_to_"
    "authority_decision_binding_v0.1"
)
BINDING_CONTRACT_IDENTITY_HASH = (
    "sha256:524af6a553b9d41313b4b8463a939357"
    "da70ee8ade9f6e33d0369d5d737d8325"
)
BINDING_MODE = (
    "CLOSED_WORLD_HASH_BOUND_EVIDENCE_TO_KEEP_"
    "AUTHORITY_FALSE_DECISION"
)
BOUND_AUTHORITY_DECISION = (
    "KEEP_EVALUATION_EXECUTION_AUTHORITY_FALSE_"
    "PENDING_EXPLICIT_LATER_OWNER_FLIP_GO"
)
CATALOG_PREREQUISITE = (
    "CLOSED_WORLD_EVIDENCE_TO_AUTHORITY_DECISION_BINDING"
)
REQUEST_KIND = "EVALUATE_SI002_EVIDENCE_TO_AUTHORITY_DECISION_BINDING"
REQUESTED_SCOPE = (
    "LOCAL_EVIDENCE_TO_AUTHORITY_DECISION_"
    "BINDING_CONTRACT_OR_RECORD_ONLY"
)
RECORD_CLASS = "LOCAL_EVIDENCE_TO_AUTHORITY_DECISION_BINDING_RECORD"
AUTHORITY_EFFECT = "NONE_BINDING_RECORD_ONLY_KEEP_AUTHORITY_FALSE"
SI003_STATE = "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION"
CLASS2_STATUS = "ESTABLISHED"
CLASS3_STATUS = "ESTABLISHED_CONTRACT_SURFACE_ONLY"
CLASS4_STATUS = "ESTABLISHED_TEST_ONLY_EVIDENCE"
CLASS5_ESTABLISHED_STATUS = "ESTABLISHED_BINDING_SURFACE_ONLY"
MISSING_STATUS = "MISSING"

AUTHORITY_KIND = "TEST_ONLY_LOCAL_EVIDENCE_TO_AUTHORITY_DECISION_BINDING"
AUTHORIZED_CELL = (
    "PART_B_B5_SI002_EVIDENCE_TO_AUTHORITY_DECISION_BINDING_GREEN"
)
AUTHORITY_BASE_COMMIT = "3e2f6b011e0bc4770e68dd601d3e5a99015ba671"
OWNER_GO_CONTENT_SHA256 = (
    "0b1a2b2823c946a15eca0f2abbb7fadd"
    "142b6a2cbf9bd6d846c73e6e710b204a"
)

POSITIVE_DECISION = (
    "LOCAL_EVIDENCE_TO_AUTHORITY_DECISION_BINDING_"
    "VALID_NO_AUTHORITY_NO_FLIP"
)
DENY_TEST_ONLY_AUTHORITY = "DENY_TEST_ONLY_AUTHORITY"
DENY_UNKNOWN_IMPLEMENTATION = "DENY_UNKNOWN_IMPLEMENTATION"
DENY_LEGACY_IMPLEMENTATION = "DENY_LEGACY_IMPLEMENTATION"
DENY_UNKNOWN_CAPABILITY_ID = "DENY_UNKNOWN_CAPABILITY_ID"
DENY_MISSING_CLASS2_BINDING = "DENY_MISSING_CLASS2_BINDING"
DENY_CLASS2_HASH_MISMATCH = "DENY_CLASS2_HASH_MISMATCH"
DENY_MISSING_CLASS3_BINDING = "DENY_MISSING_CLASS3_BINDING"
DENY_CLASS3_HASH_MISMATCH = "DENY_CLASS3_HASH_MISMATCH"
DENY_MISSING_CLASS4_BINDING = "DENY_MISSING_CLASS4_BINDING"
DENY_CLASS4_HASH_OR_DECISION_MISMATCH = (
    "DENY_CLASS4_HASH_OR_DECISION_MISMATCH"
)
DENY_CLASS4_EVIDENCE_NOT_ACTUAL = "DENY_CLASS4_EVIDENCE_NOT_ACTUAL"
DENY_CLASS4_EVIDENCE_AUTHORITY_DRIFT = (
    "DENY_CLASS4_EVIDENCE_AUTHORITY_DRIFT"
)
DENY_MISSING_SI002_CHAIN_BINDING = "DENY_MISSING_SI002_CHAIN_BINDING"
DENY_SI002_CHAIN_HASH_MISMATCH = "DENY_SI002_CHAIN_HASH_MISMATCH"
DENY_BINDING_CONTRACT_IDENTITY_MISMATCH = (
    "DENY_BINDING_CONTRACT_IDENTITY_MISMATCH"
)
DENY_BINDING_MODE_MISMATCH = "DENY_BINDING_MODE_MISMATCH"
DENY_CLASS1_OWNER_FLIP_GO_PRESENT_OR_REQUESTED = (
    "DENY_CLASS1_OWNER_FLIP_GO_PRESENT_OR_REQUESTED"
)
DENY_AUTHORITY_TRUE_OR_FLIP_ELIGIBLE = (
    "DENY_AUTHORITY_TRUE_OR_FLIP_ELIGIBLE"
)
DENY_PRODUCTION_SCOPE = "DENY_PRODUCTION_SCOPE"
DENY_CATALOG_SCOPE_OVERREACH = "DENY_CATALOG_SCOPE_OVERREACH"
DENY_RUNNER_RECLASSIFICATION = "DENY_RUNNER_RECLASSIFICATION"
DENY_SI003_OR_PART_B_SCOPE = "DENY_SI003_OR_PART_B_SCOPE"
DENY_NONDETERMINISTIC_OR_HIDDEN_INPUT = (
    "DENY_NONDETERMINISTIC_OR_HIDDEN_INPUT"
)
DENY_NON_CONTRACT_INPUT = "DENY_NON_CONTRACT_INPUT"

DECISION_ENUM = (
    POSITIVE_DECISION,
    DENY_TEST_ONLY_AUTHORITY,
    DENY_UNKNOWN_IMPLEMENTATION,
    DENY_LEGACY_IMPLEMENTATION,
    DENY_UNKNOWN_CAPABILITY_ID,
    DENY_MISSING_CLASS2_BINDING,
    DENY_CLASS2_HASH_MISMATCH,
    DENY_MISSING_CLASS3_BINDING,
    DENY_CLASS3_HASH_MISMATCH,
    DENY_MISSING_CLASS4_BINDING,
    DENY_CLASS4_HASH_OR_DECISION_MISMATCH,
    DENY_CLASS4_EVIDENCE_NOT_ACTUAL,
    DENY_CLASS4_EVIDENCE_AUTHORITY_DRIFT,
    DENY_MISSING_SI002_CHAIN_BINDING,
    DENY_SI002_CHAIN_HASH_MISMATCH,
    DENY_BINDING_CONTRACT_IDENTITY_MISMATCH,
    DENY_BINDING_MODE_MISMATCH,
    DENY_CLASS1_OWNER_FLIP_GO_PRESENT_OR_REQUESTED,
    DENY_AUTHORITY_TRUE_OR_FLIP_ELIGIBLE,
    DENY_PRODUCTION_SCOPE,
    DENY_CATALOG_SCOPE_OVERREACH,
    DENY_RUNNER_RECLASSIFICATION,
    DENY_SI003_OR_PART_B_SCOPE,
    DENY_NONDETERMINISTIC_OR_HIDDEN_INPUT,
    DENY_NON_CONTRACT_INPUT,
)

REASON_CODES = {
    POSITIVE_DECISION: "B5-SI002-E2A-000-BINDING-VALID-KEEP-AUTHORITY-FALSE",
    DENY_TEST_ONLY_AUTHORITY: "B5-SI002-E2A-DENY-TEST-AUTHORITY",
    DENY_UNKNOWN_IMPLEMENTATION: "B5-SI002-E2A-DENY-IMPLEMENTATION",
    DENY_LEGACY_IMPLEMENTATION: "B5-SI002-E2A-DENY-LEGACY",
    DENY_UNKNOWN_CAPABILITY_ID: "B5-SI002-E2A-DENY-CAPABILITY",
    DENY_MISSING_CLASS2_BINDING: "B5-SI002-E2A-DENY-MISSING-CLASS2",
    DENY_CLASS2_HASH_MISMATCH: "B5-SI002-E2A-DENY-CLASS2-HASH",
    DENY_MISSING_CLASS3_BINDING: "B5-SI002-E2A-DENY-MISSING-CLASS3",
    DENY_CLASS3_HASH_MISMATCH: "B5-SI002-E2A-DENY-CLASS3-HASH",
    DENY_MISSING_CLASS4_BINDING: "B5-SI002-E2A-DENY-MISSING-CLASS4",
    DENY_CLASS4_HASH_OR_DECISION_MISMATCH: "B5-SI002-E2A-DENY-CLASS4-HASH",
    DENY_CLASS4_EVIDENCE_NOT_ACTUAL: "B5-SI002-E2A-DENY-CLASS4-NOT-ACTUAL",
    DENY_CLASS4_EVIDENCE_AUTHORITY_DRIFT: "B5-SI002-E2A-DENY-CLASS4-AUTHORITY",
    DENY_MISSING_SI002_CHAIN_BINDING: "B5-SI002-E2A-DENY-MISSING-SI002",
    DENY_SI002_CHAIN_HASH_MISMATCH: "B5-SI002-E2A-DENY-SI002-HASH",
    DENY_BINDING_CONTRACT_IDENTITY_MISMATCH: "B5-SI002-E2A-DENY-BINDING-ID",
    DENY_BINDING_MODE_MISMATCH: "B5-SI002-E2A-DENY-BINDING-MODE",
    DENY_CLASS1_OWNER_FLIP_GO_PRESENT_OR_REQUESTED: "B5-SI002-E2A-DENY-CLASS1-GO",
    DENY_AUTHORITY_TRUE_OR_FLIP_ELIGIBLE: "B5-SI002-E2A-DENY-AUTHORITY-TRUE",
    DENY_PRODUCTION_SCOPE: "B5-SI002-E2A-DENY-PRODUCTION",
    DENY_CATALOG_SCOPE_OVERREACH: "B5-SI002-E2A-DENY-CATALOG-SCOPE",
    DENY_RUNNER_RECLASSIFICATION: "B5-SI002-E2A-DENY-RUNNER-RECLASS",
    DENY_SI003_OR_PART_B_SCOPE: "B5-SI002-E2A-DENY-SI003-PART-B",
    DENY_NONDETERMINISTIC_OR_HIDDEN_INPUT: "B5-SI002-E2A-DENY-HIDDEN-INPUT",
    DENY_NON_CONTRACT_INPUT: "B5-SI002-E2A-DENY-NON-CONTRACT",
}

AUTHORITY_FIELDS = (
    "schema_version",
    "authority_kind",
    "authorized_cell",
    "authority_base_commit",
    "owner_go_content_sha256",
)
REQUEST_FIELDS = (
    "schema_version",
    "request_kind",
    "request_version",
    "requested_scope",
    "implementation_id",
    "evaluator_capability_id",
    "evaluator_capability_identity_hash",
    "class_2_identity_acceptance_content_sha256",
    "evidence_contract_id",
    "evidence_contract_identity_hash",
    "class_3_contract_acceptance_content_sha256",
    "class_4_positive_decision",
    "class_4_record_hash",
    "class_4_record_content_sha256",
    "class_4_acceptance_content_sha256",
    "class_4_evidence_hash",
    "class_4_actual_evaluator_invocation",
    "class_4_evaluation_execution_authority",
    "class_4_planner_execution_authority",
    "class_4_authority_flip_eligible",
    "si002_contract_record_hash",
    "si002_contract_record_content_sha256",
    "si002_invocation_record_hash",
    "si002_invocation_record_content_sha256",
    "si002_boundary_record_hash",
    "si002_boundary_record_content_sha256",
    "si002_gap_catalog_record_hash",
    "si002_gap_catalog_record_content_sha256",
    "si002_gap_catalog_acceptance_content_sha256",
    "binding_contract_id",
    "binding_contract_identity_hash",
    "catalog_prerequisite_id",
    "catalog_class_number",
    "class_2_status",
    "class_3_status",
    "class_4_status",
    "class_1_status",
    "class_5_status_before",
    "binding_mode",
    "requested_binding_decision",
    "evidence_to_authority_binding_requested",
    "test_only_runner_invocation_reclassified_as_class_4_or_5",
    "actual_evaluator_invocation",
    "evaluator_evidence_instance_present",
    "explicit_later_owner_flip_go_present",
    "evaluation_execution_authority",
    "planner_execution_authority",
    "authority_flip_eligible",
    "production_registration_enabled",
    "pb_b5_si_003_state",
    "part_b_pass_requested",
    "stop_requested",
)
RECORD_FIELDS = (
    "schema_version",
    "record_class",
    "record_version",
    "request_hash",
    "implementation_id",
    "binding_contract_id",
    "binding_contract_identity_hash",
    "evaluator_capability_id",
    "evaluator_capability_identity_hash",
    "evidence_contract_id",
    "evidence_contract_identity_hash",
    "class_4_record_hash",
    "class_4_evidence_hash",
    "decision",
    "reason_codes",
    "record_scope",
    "authority_effect",
    "binding_contract_valid",
    "evidence_to_authority_decision_binding_established",
    "bound_evidence_decision",
    "bound_authority_decision",
    "catalog_prerequisite_addressed",
    "class_2_status",
    "class_3_status",
    "class_4_status",
    "class_5_status",
    "class_1_status",
    "other_catalog_prerequisites_satisfied",
    "all_flip_prerequisites_satisfied",
    "actual_evaluator_invocation",
    "evaluator_evidence_instance_present",
    "evaluation_execution_authority",
    "planner_execution_authority",
    "authority_flip_eligible",
    "production_registration_enabled",
    "pb_b5_si_003_state",
    "stop_authority",
    "hash",
)

AUTHORITY_FIELD_CATALOG_HASH = (
    "sha256:240cf31cf39b095c37a4a044aad792c9d"
    "a0620b1629817932ce63685ff39f95d"
)
REQUEST_FIELD_CATALOG_HASH = (
    "sha256:515736d6c50c7dc30740800fc01a11004"
    "0d63fad46dd41e3c86c91a3ae9649f6"
)
RECORD_FIELD_CATALOG_HASH = (
    "sha256:8d2c7645286c4dc9f61817579430519f"
    "b3f1704578a23f86e263586c9e155f26"
)

BINDING_IDENTITY_COMPONENTS = {
    "implementation_id": IMPLEMENTATION_ID,
    "evaluator_capability_id": EVALUATOR_CAPABILITY_ID,
    "evaluator_capability_identity_hash": EVALUATOR_CAPABILITY_IDENTITY_HASH,
    "evidence_contract_id": EVIDENCE_CONTRACT_ID,
    "evidence_contract_identity_hash": EVIDENCE_CONTRACT_IDENTITY_HASH,
    "class_4_positive_decision": CLASS4_POSITIVE_DECISION,
    "class_4_record_hash": CLASS4_RECORD_HASH,
    "class_4_evidence_hash": CLASS4_EVIDENCE_HASH,
    "catalog_prerequisite_id": CATALOG_PREREQUISITE,
    "binding_mode": BINDING_MODE,
    "bound_authority_decision": BOUND_AUTHORITY_DECISION,
}

EXPECTED_AUTHORITY: dict[str, object] = {
    "schema_version": "0.8.0",
    "authority_kind": AUTHORITY_KIND,
    "authorized_cell": AUTHORIZED_CELL,
    "authority_base_commit": AUTHORITY_BASE_COMMIT,
    "owner_go_content_sha256": OWNER_GO_CONTENT_SHA256,
}

EXPECTED_REQUEST: dict[str, object] = {
    "schema_version": "0.8.0",
    "request_kind": REQUEST_KIND,
    "request_version": "0.1.0",
    "requested_scope": REQUESTED_SCOPE,
    "implementation_id": IMPLEMENTATION_ID,
    "evaluator_capability_id": EVALUATOR_CAPABILITY_ID,
    "evaluator_capability_identity_hash": EVALUATOR_CAPABILITY_IDENTITY_HASH,
    "class_2_identity_acceptance_content_sha256": CLASS2_ACCEPTANCE_CONTENT_SHA256,
    "evidence_contract_id": EVIDENCE_CONTRACT_ID,
    "evidence_contract_identity_hash": EVIDENCE_CONTRACT_IDENTITY_HASH,
    "class_3_contract_acceptance_content_sha256": CLASS3_ACCEPTANCE_CONTENT_SHA256,
    "class_4_positive_decision": CLASS4_POSITIVE_DECISION,
    "class_4_record_hash": CLASS4_RECORD_HASH,
    "class_4_record_content_sha256": CLASS4_RECORD_CONTENT_SHA256,
    "class_4_acceptance_content_sha256": CLASS4_ACCEPTANCE_CONTENT_SHA256,
    "class_4_evidence_hash": CLASS4_EVIDENCE_HASH,
    "class_4_actual_evaluator_invocation": True,
    "class_4_evaluation_execution_authority": False,
    "class_4_planner_execution_authority": False,
    "class_4_authority_flip_eligible": False,
    "si002_contract_record_hash": SI002_CONTRACT_RECORD_HASH,
    "si002_contract_record_content_sha256": SI002_CONTRACT_RECORD_CONTENT_SHA256,
    "si002_invocation_record_hash": SI002_INVOCATION_RECORD_HASH,
    "si002_invocation_record_content_sha256": SI002_INVOCATION_RECORD_CONTENT_SHA256,
    "si002_boundary_record_hash": SI002_BOUNDARY_RECORD_HASH,
    "si002_boundary_record_content_sha256": SI002_BOUNDARY_RECORD_CONTENT_SHA256,
    "si002_gap_catalog_record_hash": SI002_GAP_CATALOG_RECORD_HASH,
    "si002_gap_catalog_record_content_sha256": SI002_GAP_CATALOG_RECORD_CONTENT_SHA256,
    "si002_gap_catalog_acceptance_content_sha256": SI002_GAP_CATALOG_ACCEPTANCE_CONTENT_SHA256,
    "binding_contract_id": BINDING_CONTRACT_ID,
    "binding_contract_identity_hash": BINDING_CONTRACT_IDENTITY_HASH,
    "catalog_prerequisite_id": CATALOG_PREREQUISITE,
    "catalog_class_number": 5,
    "class_2_status": CLASS2_STATUS,
    "class_3_status": CLASS3_STATUS,
    "class_4_status": CLASS4_STATUS,
    "class_1_status": MISSING_STATUS,
    "class_5_status_before": MISSING_STATUS,
    "binding_mode": BINDING_MODE,
    "requested_binding_decision": BOUND_AUTHORITY_DECISION,
    "evidence_to_authority_binding_requested": True,
    "test_only_runner_invocation_reclassified_as_class_4_or_5": False,
    "actual_evaluator_invocation": True,
    "evaluator_evidence_instance_present": True,
    "explicit_later_owner_flip_go_present": False,
    "evaluation_execution_authority": False,
    "planner_execution_authority": False,
    "authority_flip_eligible": False,
    "production_registration_enabled": False,
    "pb_b5_si_003_state": SI003_STATE,
    "part_b_pass_requested": False,
    "stop_requested": False,
}

CLASS2_FIELDS = frozenset(
    {
        "evaluator_capability_identity_hash",
        "class_2_identity_acceptance_content_sha256",
    }
)
CLASS3_FIELDS = frozenset(
    {
        "evidence_contract_id",
        "evidence_contract_identity_hash",
        "class_3_contract_acceptance_content_sha256",
    }
)
CLASS4_FIELDS = frozenset(
    {
        "class_4_positive_decision",
        "class_4_record_hash",
        "class_4_record_content_sha256",
        "class_4_acceptance_content_sha256",
        "class_4_evidence_hash",
        "class_4_actual_evaluator_invocation",
        "class_4_evaluation_execution_authority",
        "class_4_planner_execution_authority",
        "class_4_authority_flip_eligible",
    }
)
SI002_CHAIN_FIELDS = frozenset(
    {
        "si002_contract_record_hash",
        "si002_contract_record_content_sha256",
        "si002_invocation_record_hash",
        "si002_invocation_record_content_sha256",
        "si002_boundary_record_hash",
        "si002_boundary_record_content_sha256",
        "si002_gap_catalog_record_hash",
        "si002_gap_catalog_record_content_sha256",
        "si002_gap_catalog_acceptance_content_sha256",
    }
)
NONDETERMINISTIC_OR_HIDDEN_FIELDS = frozenset(
    {
        "random_seed",
        "random_uuid",
        "wall_clock",
        "process_id",
        "learned_probability",
        "hidden_ground_truth",
        "oracle_label",
        "raw_payload",
        "raw_evidence",
        "evaluator_input",
        "evaluator_output",
    }
)
CLASS1_REQUEST_FIELDS = frozenset(
    {
        "authority_flip_requested",
        "explicit_later_owner_flip_go",
        "owner_flip_go",
    }
)


def evaluate_si002_evidence_to_authority_decision_binding(
    binding_request: Mapping[str, Any] | object,
    *,
    test_only_authority: Mapping[str, Any] | object,
) -> dict[str, object]:
    """Validate the exact class-5 binding request without invoking anything."""

    if not _valid_test_only_authority(test_only_authority):
        return _record(binding_request, DENY_TEST_ONLY_AUTHORITY)
    if not isinstance(binding_request, Mapping):
        return _record(binding_request, DENY_NON_CONTRACT_INPUT)
    decision = _select_decision(binding_request)
    return _record(binding_request, decision)


def _valid_test_only_authority(authority: object) -> bool:
    return (
        isinstance(authority, Mapping)
        and set(authority) == set(AUTHORITY_FIELDS)
        and dict(authority) == EXPECTED_AUTHORITY
    )


def _select_decision(request: Mapping[str, Any]) -> str:
    keys = set(request)
    expected_keys = set(REQUEST_FIELDS)
    extra = keys - expected_keys
    missing = expected_keys - keys

    if extra & NONDETERMINISTIC_OR_HIDDEN_FIELDS:
        return DENY_NONDETERMINISTIC_OR_HIDDEN_INPUT
    if extra & CLASS1_REQUEST_FIELDS:
        return DENY_CLASS1_OWNER_FLIP_GO_PRESENT_OR_REQUESTED
    if extra:
        return DENY_NON_CONTRACT_INPUT

    if missing & CLASS2_FIELDS:
        return DENY_MISSING_CLASS2_BINDING
    if missing & CLASS3_FIELDS:
        return DENY_MISSING_CLASS3_BINDING
    if missing & CLASS4_FIELDS:
        return DENY_MISSING_CLASS4_BINDING
    if missing & SI002_CHAIN_FIELDS:
        return DENY_MISSING_SI002_CHAIN_BINDING
    if missing:
        return DENY_NON_CONTRACT_INPUT

    implementation_id = request.get("implementation_id")
    if implementation_id == LEGACY_IMPLEMENTATION_ID:
        return DENY_LEGACY_IMPLEMENTATION
    if implementation_id != IMPLEMENTATION_ID:
        return DENY_UNKNOWN_IMPLEMENTATION
    if request.get("evaluator_capability_id") != EVALUATOR_CAPABILITY_ID:
        return DENY_UNKNOWN_CAPABILITY_ID

    if any(request.get(key) != EXPECTED_REQUEST[key] for key in CLASS2_FIELDS):
        return DENY_CLASS2_HASH_MISMATCH
    if any(request.get(key) != EXPECTED_REQUEST[key] for key in CLASS3_FIELDS):
        return DENY_CLASS3_HASH_MISMATCH

    class4_hash_fields = CLASS4_FIELDS - {
        "class_4_actual_evaluator_invocation",
        "class_4_evaluation_execution_authority",
        "class_4_planner_execution_authority",
        "class_4_authority_flip_eligible",
    }
    if any(
        request.get(key) != EXPECTED_REQUEST[key]
        for key in class4_hash_fields
    ):
        return DENY_CLASS4_HASH_OR_DECISION_MISMATCH
    if request.get("class_4_actual_evaluator_invocation") is not True:
        return DENY_CLASS4_EVIDENCE_NOT_ACTUAL
    if (
        request.get("class_4_evaluation_execution_authority") is not False
        or request.get("class_4_planner_execution_authority") is not False
        or request.get("class_4_authority_flip_eligible") is not False
    ):
        return DENY_CLASS4_EVIDENCE_AUTHORITY_DRIFT

    if any(
        request.get(key) != EXPECTED_REQUEST[key] for key in SI002_CHAIN_FIELDS
    ):
        return DENY_SI002_CHAIN_HASH_MISMATCH

    if (
        request.get("binding_contract_id") != BINDING_CONTRACT_ID
        or request.get("binding_contract_identity_hash")
        != BINDING_CONTRACT_IDENTITY_HASH
        or request.get("catalog_prerequisite_id") != CATALOG_PREREQUISITE
        or request.get("catalog_class_number") != 5
    ):
        return DENY_BINDING_CONTRACT_IDENTITY_MISMATCH
    if (
        request.get("binding_mode") != BINDING_MODE
        or request.get("requested_binding_decision")
        != BOUND_AUTHORITY_DECISION
        or request.get("evidence_to_authority_binding_requested") is not True
    ):
        return DENY_BINDING_MODE_MISMATCH

    if (
        request.get("explicit_later_owner_flip_go_present") is not False
    ):
        return DENY_CLASS1_OWNER_FLIP_GO_PRESENT_OR_REQUESTED
    if (
        request.get("evaluation_execution_authority") is not False
        or request.get("planner_execution_authority") is not False
        or request.get("authority_flip_eligible") is not False
    ):
        return DENY_AUTHORITY_TRUE_OR_FLIP_ELIGIBLE
    if request.get("production_registration_enabled") is not False:
        return DENY_PRODUCTION_SCOPE
    if (
        request.get("class_2_status") != CLASS2_STATUS
        or request.get("class_3_status") != CLASS3_STATUS
        or request.get("class_4_status") != CLASS4_STATUS
        or request.get("class_1_status") != MISSING_STATUS
        or request.get("class_5_status_before") != MISSING_STATUS
    ):
        return DENY_CATALOG_SCOPE_OVERREACH
    if request.get(
        "test_only_runner_invocation_reclassified_as_class_4_or_5"
    ) is not False:
        return DENY_RUNNER_RECLASSIFICATION
    if (
        request.get("pb_b5_si_003_state") != SI003_STATE
        or request.get("part_b_pass_requested") is not False
        or request.get("stop_requested") is not False
    ):
        return DENY_SI003_OR_PART_B_SCOPE
    if (
        request.get("actual_evaluator_invocation") is not True
        or request.get("evaluator_evidence_instance_present") is not True
    ):
        return DENY_CLASS4_EVIDENCE_NOT_ACTUAL

    if any(request.get(key) != value for key, value in EXPECTED_REQUEST.items()):
        return DENY_NON_CONTRACT_INPUT
    return POSITIVE_DECISION


def _record(request: object, decision: str) -> dict[str, object]:
    positive = decision == POSITIVE_DECISION
    request_mapping = request if isinstance(request, Mapping) else {}
    request_hash = _safe_request_hash(request)
    result: dict[str, object] = {
        "schema_version": "0.8.0",
        "record_class": RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": request_hash,
        "implementation_id": request_mapping.get("implementation_id"),
        "binding_contract_id": request_mapping.get("binding_contract_id"),
        "binding_contract_identity_hash": request_mapping.get(
            "binding_contract_identity_hash"
        ),
        "evaluator_capability_id": request_mapping.get(
            "evaluator_capability_id"
        ),
        "evaluator_capability_identity_hash": request_mapping.get(
            "evaluator_capability_identity_hash"
        ),
        "evidence_contract_id": request_mapping.get("evidence_contract_id"),
        "evidence_contract_identity_hash": request_mapping.get(
            "evidence_contract_identity_hash"
        ),
        "class_4_record_hash": request_mapping.get("class_4_record_hash"),
        "class_4_evidence_hash": request_mapping.get("class_4_evidence_hash"),
        "decision": decision,
        "reason_codes": [REASON_CODES[decision]],
        "record_scope": REQUESTED_SCOPE,
        "authority_effect": AUTHORITY_EFFECT,
        "binding_contract_valid": positive,
        "evidence_to_authority_decision_binding_established": positive,
        "bound_evidence_decision": CLASS4_POSITIVE_DECISION if positive else None,
        "bound_authority_decision": BOUND_AUTHORITY_DECISION if positive else None,
        "catalog_prerequisite_addressed": CATALOG_PREREQUISITE if positive else "NONE",
        "class_2_status": CLASS2_STATUS,
        "class_3_status": CLASS3_STATUS,
        "class_4_status": CLASS4_STATUS,
        "class_5_status": CLASS5_ESTABLISHED_STATUS if positive else MISSING_STATUS,
        "class_1_status": MISSING_STATUS,
        "other_catalog_prerequisites_satisfied": False,
        "all_flip_prerequisites_satisfied": False,
        "actual_evaluator_invocation": positive,
        "evaluator_evidence_instance_present": positive,
        "evaluation_execution_authority": False,
        "planner_execution_authority": False,
        "authority_flip_eligible": False,
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


if canonical_value_hash(list(AUTHORITY_FIELDS)) != AUTHORITY_FIELD_CATALOG_HASH:
    raise RuntimeError("authority field catalog hash drift")
if canonical_value_hash(list(REQUEST_FIELDS)) != REQUEST_FIELD_CATALOG_HASH:
    raise RuntimeError("request field catalog hash drift")
if canonical_value_hash(list(RECORD_FIELDS)) != RECORD_FIELD_CATALOG_HASH:
    raise RuntimeError("record field catalog hash drift")
if canonical_value_hash(BINDING_IDENTITY_COMPONENTS) != BINDING_CONTRACT_IDENTITY_HASH:
    raise RuntimeError("binding contract identity hash drift")
if set(EXPECTED_REQUEST) != set(REQUEST_FIELDS):
    raise RuntimeError("expected request field drift")
if len(DECISION_ENUM) != len(set(DECISION_ENUM)):
    raise RuntimeError("decision enum contains duplicates")


__all__ = [
    "AUTHORITY_BASE_COMMIT",
    "AUTHORITY_EFFECT",
    "AUTHORITY_FIELD_CATALOG_HASH",
    "AUTHORITY_FLIP_ELIGIBLE",
    "AUTHORITY_KIND",
    "AUTHORIZED_CELL",
    "BINDING_CONTRACT_ID",
    "BINDING_CONTRACT_IDENTITY_HASH",
    "BOUND_AUTHORITY_DECISION",
    "DECISION_ENUM",
    "EVALUATION_EXECUTION_AUTHORITY",
    "EXPECTED_AUTHORITY",
    "EXPECTED_REQUEST",
    "EXPLICIT_LATER_OWNER_FLIP_GO_PRESENT",
    "HARD_BAN",
    "OWNER_GO_CONTENT_SHA256",
    "PLANNER_EXECUTION_AUTHORITY",
    "POSITIVE_DECISION",
    "PRODUCTION_REGISTRATION_ENABLED",
    "RECORD_FIELDS",
    "RECORD_FIELD_CATALOG_HASH",
    "REQUEST_FIELDS",
    "REQUEST_FIELD_CATALOG_HASH",
    "evaluate_si002_evidence_to_authority_decision_binding",
]
