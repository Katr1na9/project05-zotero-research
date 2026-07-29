"""Pure SI-002 class-1 explicit Owner evaluation-authority flip validator.

The validator records one closed-world metadata transition from evaluation
execution authority false to true.  It invokes no planner, Twin wiring,
evaluator, runner, or prior SI-002 runtime.  Planner authority, production,
SI-003, Part B, Path B, full M3*, certificates, and STOP remain closed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.ir.canonical_hash import canonical_document_hash, canonical_value_hash


PRODUCTION_REGISTRATION_ENABLED = False
PLANNER_EXECUTION_AUTHORITY = False
PB_B5_SI_003_STATE = "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION"

HARD_BAN = (
    "Path A / Kernel design GREEN must not be inferred as L2 PASS, "
    "Part B PASS, or unrestricted Part B elevation."
)

AUTHORITY_BASE_COMMIT = "508919e0f07da3b13f95cae115c098fdee49a617"
RED_GO_CONTENT_SHA256 = (
    "e5b8febc62fb314772133d5a0edccaa6c704e8ebcb0c95259ecb2c4f0d5cc302"
)
EXPLICIT_OWNER_FLIP_GO_ARTIFACT_ID = (
    "part-b-b5-si002-explicit-owner-evaluation-execution-authority-"
    "flip-green-authorization-v0.1-20260729"
)
EXPLICIT_OWNER_FLIP_GO_CONTENT_SHA256 = (
    "ccb5863d7cd096428365eb7fdb6720e2871928385beb685b73ab38411db55f4c"
)
EXPLICIT_OWNER_FLIP_GO_DECISION = (
    "AUTHORIZE_LOCAL_EXPLICIT_OWNER_EVALUATION_EXECUTION_AUTHORITY_"
    "FALSE_TO_TRUE_FLIP_RECORD_GREEN_ONLY"
)
AUTHORITY_KIND = "EXPLICIT_OWNER_EVALUATION_EXECUTION_AUTHORITY_FLIP_GREEN_ONLY"
AUTHORIZED_CELL = "PART_B_B5_SI002_EXPLICIT_OWNER_FLIP_GO_GREEN"

IMPLEMENTATION_ID = "part_b_b5_m3_kernel_d1_twin_readonly_conformance_v0.1"
LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"
EVALUATOR_CAPABILITY_ID = (
    "part_b_b5_si002_twin_p10_fixed_case_depth1_candidacy_evaluator_v0.1"
)
EVALUATOR_CAPABILITY_IDENTITY_HASH = (
    "sha256:7a0a87b85585d2277f1a0ea27d5cb7a30a5cbbafb7b7759abf1214a84610da30"
)
CLASS2_ACCEPTANCE_CONTENT_SHA256 = (
    "2f97fffe9a3fc41a7c5243e096b83a83a31bee8e755572784038ed473ac5ed7d"
)
EVIDENCE_CONTRACT_ID = (
    "part_b_b5_si002_local_hash_bound_evaluator_execution_evidence_contract_v0.1"
)
EVIDENCE_CONTRACT_IDENTITY_HASH = (
    "sha256:bafdbfe4251bf353d2d7220497e81fbd9ed955a2bebe566bab39783cb5926be5"
)
CLASS3_ACCEPTANCE_CONTENT_SHA256 = (
    "d3e51ff1ab5d94bd3c9b4c5e67bc0bfa26dd99f4aa3a520968a89f528a010478"
)
CLASS4_POSITIVE_DECISION = (
    "LOCAL_ACTUAL_EVALUATOR_INVOCATION_EVIDENCE_VALID_NO_AUTHORITY_NO_FLIP"
)
CLASS4_RECORD_HASH = (
    "sha256:c25472f6ba5a73c5943b06595e1776e7d53c681cc2502f8475d43aa3f57d766a"
)
CLASS4_RECORD_CONTENT_SHA256 = (
    "09cdda105a76cf465cf7e7d36f992e43dfdea692491538ab92261993d1ee631f"
)
CLASS4_ACCEPTANCE_CONTENT_SHA256 = (
    "a24c93b164fd454418e538091dd90be9970b7fc48ae199b6fd063c220e796c61"
)
CLASS4_EVIDENCE_HASH = (
    "sha256:384917e7250f29cc83bbc46ce8c603d113aaccc9b52d3669f2be7a656540b0be"
)
CLASS5_POSITIVE_DECISION = (
    "LOCAL_EVIDENCE_TO_AUTHORITY_DECISION_BINDING_VALID_NO_AUTHORITY_NO_FLIP"
)
CLASS5_BINDING_CONTRACT_ID = (
    "part_b_b5_si002_closed_world_evidence_to_authority_decision_binding_v0.1"
)
CLASS5_BINDING_CONTRACT_IDENTITY_HASH = (
    "sha256:524af6a553b9d41313b4b8463a939357da70ee8ade9f6e33d0369d5d737d8325"
)
CLASS5_RECORD_HASH = (
    "sha256:3b770d5d41fc8620643fc6b65a9827e97f0167dd9c49d6de39a63730fe0768b9"
)
CLASS5_RECORD_CONTENT_SHA256 = (
    "024710ac2c26a5601654059913bac4d7bc57c0ff07fb43450373677acf57278a"
)
CLASS5_ACCEPTANCE_CONTENT_SHA256 = (
    "54348bf13cfa367e58a0224080da00e2f6301e1443e6a06ea4fda6dd9801ddbd"
)
PRE_FLIP_BOUND_AUTHORITY_DECISION = (
    "KEEP_EVALUATION_EXECUTION_AUTHORITY_FALSE_PENDING_EXPLICIT_LATER_OWNER_FLIP_GO"
)

SI002_CONTRACT_RECORD_HASH = (
    "sha256:c3701736df903e9b7f4d4512c9a7e5c816b999f5ed8ab59ce4a188235f1403be"
)
SI002_CONTRACT_RECORD_CONTENT_SHA256 = (
    "24c2d212c133f4ba921cb46547be0868523e4dcda42bb3e59fa3f7a49bf0d421"
)
SI002_INVOCATION_RECORD_HASH = (
    "sha256:1ebee7beb9621d90f87b4f192c19c650a3db4bb4a1c4558546f2e5168e52860c"
)
SI002_INVOCATION_RECORD_CONTENT_SHA256 = (
    "bdbb4a6aea269503eb127bbbc949517ee995f042d09a3810e8af96bfbe30b851"
)
SI002_BOUNDARY_RECORD_HASH = (
    "sha256:440ebcc9489c3a6a850e541f78331be992e6ffede4f9c468676de66aad344afe"
)
SI002_BOUNDARY_RECORD_CONTENT_SHA256 = (
    "df8a28daeb194a99019dc348e45a51d0906da8b8db9fda154f4c7a0848b923a5"
)
SI002_GAP_CATALOG_RECORD_HASH = (
    "sha256:520cac2587d29fb2fe569f17300d2ac28c8184e1f2a62f129136e6b738e0b092"
)
SI002_GAP_CATALOG_RECORD_CONTENT_SHA256 = (
    "9066ca092e6d0cf6888e3846a85b3656d574bf590b856da7e993ba69a0d1d5f3"
)
SI002_GAP_CATALOG_ACCEPTANCE_CONTENT_SHA256 = (
    "69e350764c99ea752675b8848894ac876ce5f1bf4eec791f7850b14dd49802fd"
)

FLIP_CONTRACT_ID = (
    "part_b_b5_si002_explicit_owner_evaluation_execution_authority_flip_v0.1"
)
FLIP_CONTRACT_IDENTITY_HASH = (
    "sha256:4ed46d2474cda603bdbd850c288d35193d96760f242ac83b236ae7939d80bdb3"
)
CATALOG_PREREQUISITE_ID = "EXPLICIT_LATER_OWNER_FLIP_GO"
AUTHORITY_TRANSITION = "EVALUATION_EXECUTION_AUTHORITY_FALSE_TO_TRUE"
REQUEST_KIND = "EVALUATE_SI002_EXPLICIT_OWNER_EVALUATION_EXECUTION_AUTHORITY_FLIP"
REQUESTED_SCOPE = (
    "LOCAL_EXPLICIT_OWNER_EVALUATION_EXECUTION_AUTHORITY_FLIP_GO_OR_RECORD_ONLY"
)
RECORD_CLASS = "LOCAL_EXPLICIT_OWNER_EVALUATION_EXECUTION_AUTHORITY_FLIP_RECORD"
POSITIVE_AUTHORITY_EFFECT = (
    "EVALUATION_EXECUTION_AUTHORITY_FALSE_TO_TRUE_RECORD_ONLY_NO_PLANNER_NO_PART_B"
)

CLASS1_BEFORE_STATUS = "MISSING"
CLASS1_AFTER_STATUS = "ESTABLISHED_BY_EXPLICIT_OWNER_FLIP_GO"
CLASS2_STATUS = "ESTABLISHED"
CLASS3_STATUS = "ESTABLISHED_CONTRACT_SURFACE_ONLY"
CLASS4_STATUS = "ESTABLISHED_TEST_ONLY_EVIDENCE"
CLASS5_STATUS = "ESTABLISHED_BINDING_SURFACE_ONLY"

POSITIVE_DECISION = (
    "LOCAL_EXPLICIT_OWNER_EVALUATION_EXECUTION_AUTHORITY_FLIP_"
    "RECORDED_NO_PLANNER_NO_PART_B"
)
DENY_EXPLICIT_OWNER_FLIP_AUTHORITY = "DENY_EXPLICIT_OWNER_FLIP_AUTHORITY"
DENY_UNKNOWN_IMPLEMENTATION = "DENY_UNKNOWN_IMPLEMENTATION"
DENY_MISSING_CLASS2_BINDING = "DENY_MISSING_CLASS2_BINDING"
DENY_CLASS2_HASH_MISMATCH = "DENY_CLASS2_HASH_MISMATCH"
DENY_MISSING_CLASS3_BINDING = "DENY_MISSING_CLASS3_BINDING"
DENY_CLASS3_HASH_MISMATCH = "DENY_CLASS3_HASH_MISMATCH"
DENY_MISSING_CLASS4_BINDING = "DENY_MISSING_CLASS4_BINDING"
DENY_CLASS4_HASH_OR_STATE_MISMATCH = "DENY_CLASS4_HASH_OR_STATE_MISMATCH"
DENY_MISSING_CLASS5_BINDING = "DENY_MISSING_CLASS5_BINDING"
DENY_CLASS5_HASH_OR_KEEP_FALSE_BINDING_MISMATCH = (
    "DENY_CLASS5_HASH_OR_KEEP_FALSE_BINDING_MISMATCH"
)
DENY_MISSING_SI002_CHAIN_BINDING = "DENY_MISSING_SI002_CHAIN_BINDING"
DENY_SI002_CHAIN_HASH_MISMATCH = "DENY_SI002_CHAIN_HASH_MISMATCH"
DENY_MISSING_EXPLICIT_OWNER_FLIP_GO = "DENY_MISSING_EXPLICIT_OWNER_FLIP_GO"
DENY_EXPLICIT_OWNER_FLIP_GO_HASH_OR_DECISION_MISMATCH = (
    "DENY_EXPLICIT_OWNER_FLIP_GO_HASH_OR_DECISION_MISMATCH"
)
DENY_RED_GO_REUSED_AS_FLIP_GO = "DENY_RED_GO_REUSED_AS_FLIP_GO"
DENY_PRE_FLIP_BINDING_NOT_SATISFIED = "DENY_PRE_FLIP_BINDING_NOT_SATISFIED"
DENY_PRE_FLIP_AUTHORITY_NOT_FALSE = "DENY_PRE_FLIP_AUTHORITY_NOT_FALSE"
DENY_FLIP_TRANSITION_MISMATCH = "DENY_FLIP_TRANSITION_MISMATCH"
DENY_PLANNER_EXECUTION_AUTHORITY_REQUEST = (
    "DENY_PLANNER_EXECUTION_AUTHORITY_REQUEST"
)
DENY_PRODUCTION_SCOPE = "DENY_PRODUCTION_SCOPE"
DENY_SI003_SCOPE = "DENY_SI003_SCOPE"
DENY_PART_B_PATH_B_OR_FULL_M3_SCOPE = "DENY_PART_B_PATH_B_OR_FULL_M3_SCOPE"
DENY_STOP_OR_CERTIFICATE_SCOPE = "DENY_STOP_OR_CERTIFICATE_SCOPE"
DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT = (
    "DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT"
)

DECISION_ENUM = (
    POSITIVE_DECISION,
    DENY_EXPLICIT_OWNER_FLIP_AUTHORITY,
    DENY_UNKNOWN_IMPLEMENTATION,
    DENY_MISSING_CLASS2_BINDING,
    DENY_CLASS2_HASH_MISMATCH,
    DENY_MISSING_CLASS3_BINDING,
    DENY_CLASS3_HASH_MISMATCH,
    DENY_MISSING_CLASS4_BINDING,
    DENY_CLASS4_HASH_OR_STATE_MISMATCH,
    DENY_MISSING_CLASS5_BINDING,
    DENY_CLASS5_HASH_OR_KEEP_FALSE_BINDING_MISMATCH,
    DENY_MISSING_SI002_CHAIN_BINDING,
    DENY_SI002_CHAIN_HASH_MISMATCH,
    DENY_MISSING_EXPLICIT_OWNER_FLIP_GO,
    DENY_EXPLICIT_OWNER_FLIP_GO_HASH_OR_DECISION_MISMATCH,
    DENY_RED_GO_REUSED_AS_FLIP_GO,
    DENY_PRE_FLIP_BINDING_NOT_SATISFIED,
    DENY_PRE_FLIP_AUTHORITY_NOT_FALSE,
    DENY_FLIP_TRANSITION_MISMATCH,
    DENY_PLANNER_EXECUTION_AUTHORITY_REQUEST,
    DENY_PRODUCTION_SCOPE,
    DENY_SI003_SCOPE,
    DENY_PART_B_PATH_B_OR_FULL_M3_SCOPE,
    DENY_STOP_OR_CERTIFICATE_SCOPE,
    DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT,
)

REASON_CODES = {
    decision: f"B5-SI002-FLIP-{index:03d}"
    for index, decision in enumerate(DECISION_ENUM)
}

AUTHORITY_FIELDS = (
    "schema_version",
    "authority_kind",
    "authorized_cell",
    "authority_base_commit",
    "explicit_owner_flip_go_artifact_id",
    "explicit_owner_flip_go_content_sha256",
    "explicit_owner_flip_go_decision",
)
REQUEST_FIELDS = (
    "schema_version",
    "request_kind",
    "request_version",
    "requested_scope",
    "implementation_id",
    "evaluator_capability_id",
    "evaluator_capability_identity_hash",
    "class_2_acceptance_content_sha256",
    "evidence_contract_id",
    "evidence_contract_identity_hash",
    "class_3_acceptance_content_sha256",
    "class_4_positive_decision",
    "class_4_record_hash",
    "class_4_record_content_sha256",
    "class_4_acceptance_content_sha256",
    "class_4_evidence_hash",
    "class_4_actual_evaluator_invocation",
    "class_4_evaluation_execution_authority",
    "class_4_planner_execution_authority",
    "class_5_positive_decision",
    "class_5_binding_contract_id",
    "class_5_binding_contract_identity_hash",
    "class_5_record_hash",
    "class_5_record_content_sha256",
    "class_5_acceptance_content_sha256",
    "class_5_bound_authority_decision",
    "class_5_binding_established",
    "class_5_evaluation_execution_authority",
    "class_5_planner_execution_authority",
    "class_5_authority_flip_eligible",
    "si002_contract_record_hash",
    "si002_contract_record_content_sha256",
    "si002_invocation_record_hash",
    "si002_invocation_record_content_sha256",
    "si002_boundary_record_hash",
    "si002_boundary_record_content_sha256",
    "si002_gap_catalog_record_hash",
    "si002_gap_catalog_record_content_sha256",
    "si002_gap_catalog_acceptance_content_sha256",
    "flip_contract_id",
    "flip_contract_identity_hash",
    "catalog_prerequisite_id",
    "catalog_class_number",
    "class_2_status",
    "class_3_status",
    "class_4_status",
    "class_5_status",
    "class_1_status_before",
    "pre_flip_binding_satisfied",
    "pre_flip_evaluation_execution_authority",
    "requested_post_flip_evaluation_execution_authority",
    "requested_post_flip_planner_execution_authority",
    "requested_transition",
    "explicit_owner_flip_go_artifact_id",
    "explicit_owner_flip_go_content_sha256",
    "explicit_owner_flip_go_decision",
    "explicit_owner_flip_go_authority_base_commit",
    "flip_go_is_separate_from_red_go",
    "production_registration_enabled",
    "pb_b5_si_003_state",
    "pb_b5_si_003_close_requested",
    "part_b_pass_requested",
    "path_b_write_requested",
    "stop_requested",
    "full_m3_star_requested",
)
RECORD_FIELDS = (
    "schema_version",
    "record_class",
    "record_version",
    "request_hash",
    "implementation_id",
    "flip_contract_id",
    "flip_contract_identity_hash",
    "explicit_owner_flip_go_artifact_id",
    "explicit_owner_flip_go_content_sha256",
    "explicit_owner_flip_go_decision",
    "evaluator_capability_identity_hash",
    "evidence_contract_identity_hash",
    "class_4_record_hash",
    "class_4_evidence_hash",
    "class_5_binding_contract_identity_hash",
    "class_5_record_hash",
    "decision",
    "reason_codes",
    "record_scope",
    "authority_effect",
    "flip_contract_valid",
    "explicit_owner_flip_go_valid",
    "pre_flip_binding_satisfied",
    "pre_flip_bound_authority_decision",
    "flip_performed",
    "authority_transition",
    "pre_flip_evaluation_execution_authority",
    "post_flip_evaluation_execution_authority",
    "planner_execution_authority",
    "class_1_status",
    "class_2_status",
    "class_3_status",
    "class_4_status",
    "class_5_status",
    "all_flip_prerequisites_satisfied",
    "authority_flip_eligible_before",
    "authority_flip_eligible_after",
    "production_registration_enabled",
    "pb_b5_si_003_state",
    "part_b_pass",
    "path_b_write_authority",
    "stop_authority",
    "full_m3_star",
    "hash",
)

AUTHORITY_FIELD_CATALOG_HASH = (
    "sha256:543590d0dc2486f4b174489b418eb9e58ffb2fc6a02a1ab355a5edff7161ee56"
)
REQUEST_FIELD_CATALOG_HASH = (
    "sha256:dbaee3c9131b182f62b65658f774dfb3c775b51b57a711b7bc23c25366f65d48"
)
RECORD_FIELD_CATALOG_HASH = (
    "sha256:a297671e93d9e52aa30da66cdaf5ec74d75072161a05069c418d7ad9cddd09b7"
)

FLIP_IDENTITY_COMPONENTS = {
    "implementation_id": IMPLEMENTATION_ID,
    "evaluator_capability_identity_hash": EVALUATOR_CAPABILITY_IDENTITY_HASH,
    "evidence_contract_identity_hash": EVIDENCE_CONTRACT_IDENTITY_HASH,
    "class_4_record_hash": CLASS4_RECORD_HASH,
    "class_4_evidence_hash": CLASS4_EVIDENCE_HASH,
    "class_5_binding_contract_identity_hash": CLASS5_BINDING_CONTRACT_IDENTITY_HASH,
    "class_5_record_hash": CLASS5_RECORD_HASH,
    "pre_flip_bound_authority_decision": PRE_FLIP_BOUND_AUTHORITY_DECISION,
    "catalog_prerequisite_id": CATALOG_PREREQUISITE_ID,
    "authority_transition": AUTHORITY_TRANSITION,
    "post_flip_evaluation_execution_authority": True,
    "planner_execution_authority": False,
    "pb_b5_si_003_state": PB_B5_SI_003_STATE,
}

EXPECTED_AUTHORITY: dict[str, object] = {
    "schema_version": "0.8.0",
    "authority_kind": AUTHORITY_KIND,
    "authorized_cell": AUTHORIZED_CELL,
    "authority_base_commit": AUTHORITY_BASE_COMMIT,
    "explicit_owner_flip_go_artifact_id": EXPLICIT_OWNER_FLIP_GO_ARTIFACT_ID,
    "explicit_owner_flip_go_content_sha256": EXPLICIT_OWNER_FLIP_GO_CONTENT_SHA256,
    "explicit_owner_flip_go_decision": EXPLICIT_OWNER_FLIP_GO_DECISION,
}

EXPECTED_REQUEST: dict[str, object] = {
    "schema_version": "0.8.0",
    "request_kind": REQUEST_KIND,
    "request_version": "0.1.0",
    "requested_scope": REQUESTED_SCOPE,
    "implementation_id": IMPLEMENTATION_ID,
    "evaluator_capability_id": EVALUATOR_CAPABILITY_ID,
    "evaluator_capability_identity_hash": EVALUATOR_CAPABILITY_IDENTITY_HASH,
    "class_2_acceptance_content_sha256": CLASS2_ACCEPTANCE_CONTENT_SHA256,
    "evidence_contract_id": EVIDENCE_CONTRACT_ID,
    "evidence_contract_identity_hash": EVIDENCE_CONTRACT_IDENTITY_HASH,
    "class_3_acceptance_content_sha256": CLASS3_ACCEPTANCE_CONTENT_SHA256,
    "class_4_positive_decision": CLASS4_POSITIVE_DECISION,
    "class_4_record_hash": CLASS4_RECORD_HASH,
    "class_4_record_content_sha256": CLASS4_RECORD_CONTENT_SHA256,
    "class_4_acceptance_content_sha256": CLASS4_ACCEPTANCE_CONTENT_SHA256,
    "class_4_evidence_hash": CLASS4_EVIDENCE_HASH,
    "class_4_actual_evaluator_invocation": True,
    "class_4_evaluation_execution_authority": False,
    "class_4_planner_execution_authority": False,
    "class_5_positive_decision": CLASS5_POSITIVE_DECISION,
    "class_5_binding_contract_id": CLASS5_BINDING_CONTRACT_ID,
    "class_5_binding_contract_identity_hash": CLASS5_BINDING_CONTRACT_IDENTITY_HASH,
    "class_5_record_hash": CLASS5_RECORD_HASH,
    "class_5_record_content_sha256": CLASS5_RECORD_CONTENT_SHA256,
    "class_5_acceptance_content_sha256": CLASS5_ACCEPTANCE_CONTENT_SHA256,
    "class_5_bound_authority_decision": PRE_FLIP_BOUND_AUTHORITY_DECISION,
    "class_5_binding_established": True,
    "class_5_evaluation_execution_authority": False,
    "class_5_planner_execution_authority": False,
    "class_5_authority_flip_eligible": False,
    "si002_contract_record_hash": SI002_CONTRACT_RECORD_HASH,
    "si002_contract_record_content_sha256": SI002_CONTRACT_RECORD_CONTENT_SHA256,
    "si002_invocation_record_hash": SI002_INVOCATION_RECORD_HASH,
    "si002_invocation_record_content_sha256": SI002_INVOCATION_RECORD_CONTENT_SHA256,
    "si002_boundary_record_hash": SI002_BOUNDARY_RECORD_HASH,
    "si002_boundary_record_content_sha256": SI002_BOUNDARY_RECORD_CONTENT_SHA256,
    "si002_gap_catalog_record_hash": SI002_GAP_CATALOG_RECORD_HASH,
    "si002_gap_catalog_record_content_sha256": SI002_GAP_CATALOG_RECORD_CONTENT_SHA256,
    "si002_gap_catalog_acceptance_content_sha256": SI002_GAP_CATALOG_ACCEPTANCE_CONTENT_SHA256,
    "flip_contract_id": FLIP_CONTRACT_ID,
    "flip_contract_identity_hash": FLIP_CONTRACT_IDENTITY_HASH,
    "catalog_prerequisite_id": CATALOG_PREREQUISITE_ID,
    "catalog_class_number": 1,
    "class_2_status": CLASS2_STATUS,
    "class_3_status": CLASS3_STATUS,
    "class_4_status": CLASS4_STATUS,
    "class_5_status": CLASS5_STATUS,
    "class_1_status_before": CLASS1_BEFORE_STATUS,
    "pre_flip_binding_satisfied": True,
    "pre_flip_evaluation_execution_authority": False,
    "requested_post_flip_evaluation_execution_authority": True,
    "requested_post_flip_planner_execution_authority": False,
    "requested_transition": AUTHORITY_TRANSITION,
    "explicit_owner_flip_go_artifact_id": EXPLICIT_OWNER_FLIP_GO_ARTIFACT_ID,
    "explicit_owner_flip_go_content_sha256": EXPLICIT_OWNER_FLIP_GO_CONTENT_SHA256,
    "explicit_owner_flip_go_decision": EXPLICIT_OWNER_FLIP_GO_DECISION,
    "explicit_owner_flip_go_authority_base_commit": AUTHORITY_BASE_COMMIT,
    "flip_go_is_separate_from_red_go": True,
    "production_registration_enabled": False,
    "pb_b5_si_003_state": PB_B5_SI_003_STATE,
    "pb_b5_si_003_close_requested": False,
    "part_b_pass_requested": False,
    "path_b_write_requested": False,
    "stop_requested": False,
    "full_m3_star_requested": False,
}

CLASS2_FIELDS = frozenset({
    "evaluator_capability_id", "evaluator_capability_identity_hash",
    "class_2_acceptance_content_sha256", "class_2_status",
})
CLASS3_FIELDS = frozenset({
    "evidence_contract_id", "evidence_contract_identity_hash",
    "class_3_acceptance_content_sha256", "class_3_status",
})
CLASS4_FIELDS = frozenset({
    "class_4_positive_decision", "class_4_record_hash",
    "class_4_record_content_sha256", "class_4_acceptance_content_sha256",
    "class_4_evidence_hash", "class_4_actual_evaluator_invocation",
    "class_4_evaluation_execution_authority", "class_4_planner_execution_authority",
    "class_4_status",
})
CLASS5_FIELDS = frozenset({
    "class_5_positive_decision", "class_5_binding_contract_id",
    "class_5_binding_contract_identity_hash", "class_5_record_hash",
    "class_5_record_content_sha256", "class_5_acceptance_content_sha256",
    "class_5_bound_authority_decision", "class_5_binding_established",
    "class_5_evaluation_execution_authority", "class_5_planner_execution_authority",
    "class_5_authority_flip_eligible", "class_5_status",
})
SI002_CHAIN_FIELDS = frozenset({
    "si002_contract_record_hash", "si002_contract_record_content_sha256",
    "si002_invocation_record_hash", "si002_invocation_record_content_sha256",
    "si002_boundary_record_hash", "si002_boundary_record_content_sha256",
    "si002_gap_catalog_record_hash", "si002_gap_catalog_record_content_sha256",
    "si002_gap_catalog_acceptance_content_sha256",
})
OWNER_GO_FIELDS = frozenset({
    "explicit_owner_flip_go_artifact_id", "explicit_owner_flip_go_content_sha256",
    "explicit_owner_flip_go_decision", "explicit_owner_flip_go_authority_base_commit",
    "flip_go_is_separate_from_red_go",
})
NON_CONTRACT_FIELDS = frozenset({
    "random_seed", "random_uuid", "wall_clock", "process_id",
    "learned_probability", "hidden_ground_truth", "oracle_label",
    "raw_payload", "raw_evidence", "evaluator_input", "evaluator_output",
    "certificate_requested",
})
CERTIFICATE_REQUEST_FIELDS = frozenset({
    "certificate_requested", "certificate_authority_requested",
})


def evaluate_si002_explicit_owner_evaluation_execution_authority_flip(
    flip_request: Mapping[str, Any] | object,
    *,
    explicit_owner_flip_authority: Mapping[str, Any] | object,
) -> dict[str, object]:
    """Validate and record the one exact Owner-authorized metadata flip."""

    if (
        isinstance(explicit_owner_flip_authority, Mapping)
        and explicit_owner_flip_authority.get("explicit_owner_flip_go_content_sha256") == RED_GO_CONTENT_SHA256
    ):
        return _record(flip_request, DENY_RED_GO_REUSED_AS_FLIP_GO)
    if not _valid_explicit_owner_flip_authority(explicit_owner_flip_authority):
        return _record(flip_request, DENY_EXPLICIT_OWNER_FLIP_AUTHORITY)
    if not isinstance(flip_request, Mapping):
        return _record(flip_request, DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT)
    return _record(flip_request, _select_decision(flip_request))


def _valid_explicit_owner_flip_authority(authority: object) -> bool:
    return (
        isinstance(authority, Mapping)
        and set(authority) == set(AUTHORITY_FIELDS)
        and dict(authority) == EXPECTED_AUTHORITY
        and authority.get("explicit_owner_flip_go_content_sha256") != RED_GO_CONTENT_SHA256
    )


def _select_decision(request: Mapping[str, Any]) -> str:
    keys = set(request)
    expected_keys = set(REQUEST_FIELDS)
    extra = keys - expected_keys
    missing = expected_keys - keys

    if extra & CERTIFICATE_REQUEST_FIELDS:
        return DENY_STOP_OR_CERTIFICATE_SCOPE
    if extra:
        return DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT
    if missing & CLASS2_FIELDS:
        return DENY_MISSING_CLASS2_BINDING
    if missing & CLASS3_FIELDS:
        return DENY_MISSING_CLASS3_BINDING
    if missing & CLASS4_FIELDS:
        return DENY_MISSING_CLASS4_BINDING
    if missing & CLASS5_FIELDS:
        return DENY_MISSING_CLASS5_BINDING
    if missing & SI002_CHAIN_FIELDS:
        return DENY_MISSING_SI002_CHAIN_BINDING
    if missing & OWNER_GO_FIELDS:
        return DENY_MISSING_EXPLICIT_OWNER_FLIP_GO
    if missing:
        return DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT

    if request.get("implementation_id") != IMPLEMENTATION_ID:
        return DENY_UNKNOWN_IMPLEMENTATION
    if any(request.get(key) != EXPECTED_REQUEST[key] for key in CLASS2_FIELDS):
        return DENY_CLASS2_HASH_MISMATCH
    if any(request.get(key) != EXPECTED_REQUEST[key] for key in CLASS3_FIELDS):
        return DENY_CLASS3_HASH_MISMATCH
    if any(request.get(key) != EXPECTED_REQUEST[key] for key in CLASS4_FIELDS):
        return DENY_CLASS4_HASH_OR_STATE_MISMATCH
    if any(request.get(key) != EXPECTED_REQUEST[key] for key in CLASS5_FIELDS):
        return DENY_CLASS5_HASH_OR_KEEP_FALSE_BINDING_MISMATCH
    if any(request.get(key) != EXPECTED_REQUEST[key] for key in SI002_CHAIN_FIELDS):
        return DENY_SI002_CHAIN_HASH_MISMATCH

    if request.get("explicit_owner_flip_go_content_sha256") == RED_GO_CONTENT_SHA256:
        return DENY_RED_GO_REUSED_AS_FLIP_GO
    if any(request.get(key) != EXPECTED_REQUEST[key] for key in OWNER_GO_FIELDS):
        return DENY_EXPLICIT_OWNER_FLIP_GO_HASH_OR_DECISION_MISMATCH
    if request.get("pre_flip_binding_satisfied") is not True:
        return DENY_PRE_FLIP_BINDING_NOT_SATISFIED
    if request.get("pre_flip_evaluation_execution_authority") is not False:
        return DENY_PRE_FLIP_AUTHORITY_NOT_FALSE
    if (
        request.get("requested_transition") != AUTHORITY_TRANSITION
        or request.get("requested_post_flip_evaluation_execution_authority") is not True
    ):
        return DENY_FLIP_TRANSITION_MISMATCH
    if request.get("requested_post_flip_planner_execution_authority") is not False:
        return DENY_PLANNER_EXECUTION_AUTHORITY_REQUEST
    if request.get("production_registration_enabled") is not False:
        return DENY_PRODUCTION_SCOPE
    if (
        request.get("pb_b5_si_003_state") != PB_B5_SI_003_STATE
        or request.get("pb_b5_si_003_close_requested") is not False
    ):
        return DENY_SI003_SCOPE
    if (
        request.get("part_b_pass_requested") is not False
        or request.get("path_b_write_requested") is not False
        or request.get("full_m3_star_requested") is not False
    ):
        return DENY_PART_B_PATH_B_OR_FULL_M3_SCOPE
    if request.get("stop_requested") is not False:
        return DENY_STOP_OR_CERTIFICATE_SCOPE
    if (
        request.get("class_1_status_before") != CLASS1_BEFORE_STATUS
        or request.get("catalog_prerequisite_id") != CATALOG_PREREQUISITE_ID
        or request.get("catalog_class_number") != 1
        or request.get("flip_contract_id") != FLIP_CONTRACT_ID
        or request.get("flip_contract_identity_hash") != FLIP_CONTRACT_IDENTITY_HASH
        or request.get("requested_scope") != REQUESTED_SCOPE
        or request.get("request_kind") != REQUEST_KIND
        or request.get("flip_go_is_separate_from_red_go") is not True
    ):
        return DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT
    if any(request.get(key) != value for key, value in EXPECTED_REQUEST.items()):
        return DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT
    return POSITIVE_DECISION


def _record(request: object, decision: str) -> dict[str, object]:
    positive = decision == POSITIVE_DECISION
    source = request if isinstance(request, Mapping) else {}
    result: dict[str, object] = {
        "schema_version": "0.8.0",
        "record_class": RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": _safe_request_hash(request),
        "implementation_id": source.get("implementation_id"),
        "flip_contract_id": source.get("flip_contract_id"),
        "flip_contract_identity_hash": source.get("flip_contract_identity_hash"),
        "explicit_owner_flip_go_artifact_id": source.get("explicit_owner_flip_go_artifact_id"),
        "explicit_owner_flip_go_content_sha256": source.get("explicit_owner_flip_go_content_sha256"),
        "explicit_owner_flip_go_decision": source.get("explicit_owner_flip_go_decision"),
        "evaluator_capability_identity_hash": source.get("evaluator_capability_identity_hash"),
        "evidence_contract_identity_hash": source.get("evidence_contract_identity_hash"),
        "class_4_record_hash": source.get("class_4_record_hash"),
        "class_4_evidence_hash": source.get("class_4_evidence_hash"),
        "class_5_binding_contract_identity_hash": source.get("class_5_binding_contract_identity_hash"),
        "class_5_record_hash": source.get("class_5_record_hash"),
        "decision": decision,
        "reason_codes": [REASON_CODES[decision]],
        "record_scope": REQUESTED_SCOPE,
        "authority_effect": POSITIVE_AUTHORITY_EFFECT if positive else "NONE_DENIED",
        "flip_contract_valid": positive,
        "explicit_owner_flip_go_valid": positive,
        "pre_flip_binding_satisfied": positive,
        "pre_flip_bound_authority_decision": PRE_FLIP_BOUND_AUTHORITY_DECISION if positive else None,
        "flip_performed": positive,
        "authority_transition": AUTHORITY_TRANSITION if positive else "NONE",
        "pre_flip_evaluation_execution_authority": False,
        "post_flip_evaluation_execution_authority": positive,
        "planner_execution_authority": False,
        "class_1_status": CLASS1_AFTER_STATUS if positive else CLASS1_BEFORE_STATUS,
        "class_2_status": CLASS2_STATUS if positive else "UNVERIFIED",
        "class_3_status": CLASS3_STATUS if positive else "UNVERIFIED",
        "class_4_status": CLASS4_STATUS if positive else "UNVERIFIED",
        "class_5_status": CLASS5_STATUS if positive else "UNVERIFIED",
        "all_flip_prerequisites_satisfied": positive,
        "authority_flip_eligible_before": positive,
        "authority_flip_eligible_after": False,
        "production_registration_enabled": False,
        "pb_b5_si_003_state": PB_B5_SI_003_STATE,
        "part_b_pass": False,
        "path_b_write_authority": False,
        "stop_authority": "NONE",
        "full_m3_star": False,
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
if canonical_value_hash(FLIP_IDENTITY_COMPONENTS) != FLIP_CONTRACT_IDENTITY_HASH:
    raise RuntimeError("flip contract identity hash drift")
if set(EXPECTED_REQUEST) != set(REQUEST_FIELDS):
    raise RuntimeError("expected request field drift")
if len(DECISION_ENUM) != len(set(DECISION_ENUM)):
    raise RuntimeError("decision enum contains duplicates")


__all__ = [
    "AUTHORITY_FIELDS", "AUTHORITY_FIELD_CATALOG_HASH", "DECISION_ENUM",
    "EXPECTED_AUTHORITY", "EXPECTED_REQUEST", "EXPLICIT_OWNER_FLIP_GO_CONTENT_SHA256",
    "FLIP_CONTRACT_IDENTITY_HASH", "FLIP_IDENTITY_COMPONENTS", "HARD_BAN",
    "POSITIVE_DECISION", "PRODUCTION_REGISTRATION_ENABLED", "REASON_CODES",
    "RECORD_FIELDS", "RECORD_FIELD_CATALOG_HASH", "RED_GO_CONTENT_SHA256",
    "REQUEST_FIELDS", "REQUEST_FIELD_CATALOG_HASH",
    "evaluate_si002_explicit_owner_evaluation_execution_authority_flip",
]
