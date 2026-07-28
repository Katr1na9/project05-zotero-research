"""Pure SI-002 evaluator-execution evidence-record contract validator.

This module validates one exact, hash-bound future evidence-record contract
against the accepted class-2 capability identity and SI-002 chain.  It never
imports or invokes Twin, the depth-1 planner, a runner, or an evaluator.  It
creates contract metadata only: no evidence instance, invocation, execution
authority, authority flip, or evidence-to-authority binding.
"""

from __future__ import annotations

from collections.abc import Mapping

from src.ir.canonical_hash import canonical_document_hash, canonical_value_hash


PRODUCTION_REGISTRATION_ENABLED = False
EVALUATOR_EVIDENCE_INSTANCE_PRESENT = False
ACTUAL_EVALUATOR_INVOCATION = False
EVALUATION_EXECUTION_AUTHORITY = False
PLANNER_EXECUTION_AUTHORITY = False

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
EVIDENCE_RECORD_CLASS = (
    "LOCAL_HASH_BOUND_EVALUATOR_EXECUTION_EVIDENCE_RECORD"
)
EVIDENCE_ORIGIN_MODE = "LOCAL_SYNTHETIC_DECLARATION_BOUND_NO_PRODUCTION"
EVIDENCE_BINDING_PROFILE = (
    "CAPABILITY_ID_ATTEMPT_REQUEST_INPUT_OUTPUT_HASH_BOUND_V0_1"
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
TEST_ONLY_RUNNER_INVOCATION_RECORD_HASH = SI002_INVOCATION_RECORD_HASH

REQUEST_KIND = "ASSESS_SI002_EVALUATOR_EXECUTION_EVIDENCE_RECORD_CONTRACT"
REQUESTED_SCOPE = (
    "LOCAL_EVALUATOR_EXECUTION_EVIDENCE_RECORD_"
    "CONTRACT_OR_RECORD_ONLY"
)
CONTRACT_DECISION_RECORD_CLASS = (
    "LOCAL_EVALUATOR_EXECUTION_EVIDENCE_RECORD_CONTRACT_DECISION"
)
RECORD_SCOPE = REQUESTED_SCOPE
AUTHORITY_EFFECT = "NONE_EVIDENCE_CONTRACT_RECORD_ONLY"
CATALOG_PREREQUISITE = (
    "ACCEPTED_HASH_BOUND_EVALUATOR_EXECUTION_EVIDENCE_OR_RECORD"
)
CLASS_2_STATUS = "ESTABLISHED"
MISSING_STATUS = "MISSING"
SI003_STATE = "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION"

POSITIVE_DECISION = (
    "LOCAL_EVALUATOR_EXECUTION_EVIDENCE_RECORD_CONTRACT_"
    "VALID_NO_INVOCATION_NO_FLIP"
)
DENY_UNKNOWN_IMPLEMENTATION = "DENY_UNKNOWN_IMPLEMENTATION"
DENY_UNKNOWN_CAPABILITY_ID = "DENY_UNKNOWN_CAPABILITY_ID"
DENY_LEGACY_IMPLEMENTATION = "DENY_LEGACY_IMPLEMENTATION"
DENY_MISSING_IDENTITY_BINDING = "DENY_MISSING_IDENTITY_BINDING"
DENY_IDENTITY_HASH_MISMATCH = "DENY_IDENTITY_HASH_MISMATCH"
DENY_EVIDENCE_CONTRACT_SURFACE_MISMATCH = (
    "DENY_EVIDENCE_CONTRACT_SURFACE_MISMATCH"
)
DENY_EVIDENCE_CONTRACT_HASH_MISMATCH = (
    "DENY_EVIDENCE_CONTRACT_HASH_MISMATCH"
)
DENY_EVIDENCE_FIELD_CATALOG_MISMATCH = (
    "DENY_EVIDENCE_FIELD_CATALOG_MISMATCH"
)
DENY_MISSING_SI002_CHAIN_BINDING = "DENY_MISSING_SI002_CHAIN_BINDING"
DENY_SI002_CHAIN_HASH_MISMATCH = "DENY_SI002_CHAIN_HASH_MISMATCH"
DENY_RUNNER_INVOCATION_RECLASSIFICATION = (
    "DENY_RUNNER_INVOCATION_RECLASSIFICATION"
)
DENY_ACTUAL_EVIDENCE_OR_INVOCATION = (
    "DENY_ACTUAL_EVIDENCE_OR_INVOCATION"
)
DENY_AUTHORITY_REQUEST = "DENY_AUTHORITY_REQUEST"
DENY_CATALOG_SCOPE_OVERREACH = "DENY_CATALOG_SCOPE_OVERREACH"
DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT = (
    "DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT"
)
DENY_SI003_OR_PART_B_SCOPE = "DENY_SI003_OR_PART_B_SCOPE"
DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT = (
    "DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT"
)

REASON_CODES = {
    POSITIVE_DECISION: (
        "B5-SI002-EVAL-EVIDENCE-000-CONTRACT-VALID-NO-INVOCATION-NO-FLIP"
    ),
    DENY_UNKNOWN_IMPLEMENTATION: (
        "B5-SI002-EVAL-EVIDENCE-DENY-UNKNOWN-IMPLEMENTATION"
    ),
    DENY_UNKNOWN_CAPABILITY_ID: (
        "B5-SI002-EVAL-EVIDENCE-DENY-UNKNOWN-CAPABILITY"
    ),
    DENY_LEGACY_IMPLEMENTATION: "B5-SI002-EVAL-EVIDENCE-DENY-LEGACY",
    DENY_MISSING_IDENTITY_BINDING: (
        "B5-SI002-EVAL-EVIDENCE-DENY-MISSING-IDENTITY"
    ),
    DENY_IDENTITY_HASH_MISMATCH: (
        "B5-SI002-EVAL-EVIDENCE-DENY-IDENTITY-HASH"
    ),
    DENY_EVIDENCE_CONTRACT_SURFACE_MISMATCH: (
        "B5-SI002-EVAL-EVIDENCE-DENY-CONTRACT-SURFACE"
    ),
    DENY_EVIDENCE_CONTRACT_HASH_MISMATCH: (
        "B5-SI002-EVAL-EVIDENCE-DENY-CONTRACT-HASH"
    ),
    DENY_EVIDENCE_FIELD_CATALOG_MISMATCH: (
        "B5-SI002-EVAL-EVIDENCE-DENY-FIELD-CATALOG"
    ),
    DENY_MISSING_SI002_CHAIN_BINDING: (
        "B5-SI002-EVAL-EVIDENCE-DENY-MISSING-SI002-CHAIN"
    ),
    DENY_SI002_CHAIN_HASH_MISMATCH: (
        "B5-SI002-EVAL-EVIDENCE-DENY-SI002-CHAIN-HASH"
    ),
    DENY_RUNNER_INVOCATION_RECLASSIFICATION: (
        "B5-SI002-EVAL-EVIDENCE-DENY-RUNNER-RECLASSIFICATION"
    ),
    DENY_ACTUAL_EVIDENCE_OR_INVOCATION: (
        "B5-SI002-EVAL-EVIDENCE-DENY-ACTUAL-EVIDENCE-INVOCATION"
    ),
    DENY_AUTHORITY_REQUEST: "B5-SI002-EVAL-EVIDENCE-DENY-AUTHORITY",
    DENY_CATALOG_SCOPE_OVERREACH: (
        "B5-SI002-EVAL-EVIDENCE-DENY-CATALOG-OVERREACH"
    ),
    DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT: (
        "B5-SI002-EVAL-EVIDENCE-DENY-NONDETERMINISTIC-PAYLOAD"
    ),
    DENY_SI003_OR_PART_B_SCOPE: (
        "B5-SI002-EVAL-EVIDENCE-DENY-SI003-PART-B"
    ),
    DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT: (
        "B5-SI002-EVAL-EVIDENCE-DENY-NON-CONTRACT"
    ),
}

EVIDENCE_CONTRACT_IDENTITY_BASIS = {
    "evidence_contract_id": EVIDENCE_CONTRACT_ID,
    "evidence_record_class": EVIDENCE_RECORD_CLASS,
    "evidence_origin_mode": EVIDENCE_ORIGIN_MODE,
    "evidence_binding_profile": EVIDENCE_BINDING_PROFILE,
    "implementation_id": IMPLEMENTATION_ID,
    "evaluator_capability_id": EVALUATOR_CAPABILITY_ID,
    "evaluator_capability_identity_hash": EVALUATOR_CAPABILITY_IDENTITY_HASH,
    "evaluator_capability_identity_record_hash": (
        EVALUATOR_CAPABILITY_IDENTITY_RECORD_HASH
    ),
    "evaluator_capability_identity_acceptance_content_sha256": (
        EVALUATOR_CAPABILITY_IDENTITY_ACCEPTANCE_CONTENT_SHA256
    ),
    "future_evidence_required_fields_hash": (
        FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH
    ),
    "future_evidence_required_field_count": 17,
    "future_evidence_hash_binding_fields_hash": (
        FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH
    ),
    "future_evidence_hash_binding_field_count": 8,
    "test_only_runner_invocation_reclassified_as_evaluator_evidence": False,
}

if (
    canonical_value_hash(list(FUTURE_EVIDENCE_REQUIRED_FIELDS))
    != FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH
):
    raise RuntimeError("future evidence required-field catalog hash drift")
if (
    canonical_value_hash(list(FUTURE_EVIDENCE_HASH_BINDING_FIELDS))
    != FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH
):
    raise RuntimeError("future evidence hash-binding catalog hash drift")
if (
    canonical_value_hash(EVIDENCE_CONTRACT_IDENTITY_BASIS)
    != EVIDENCE_CONTRACT_IDENTITY_HASH
):
    raise RuntimeError("evaluator evidence-contract identity hash drift")

REQUEST_FIELDS = frozenset(
    {
        "schema_version",
        "request_kind",
        "request_version",
        "requested_scope",
        "implementation_id",
        "evaluator_capability_id",
        "evaluator_capability_identity_hash",
        "evaluator_capability_identity_record_hash",
        "evaluator_capability_identity_record_content_sha256",
        "evaluator_capability_identity_acceptance_content_sha256",
        "evidence_contract_id",
        "evidence_contract_identity_hash",
        "evidence_record_class",
        "evidence_origin_mode",
        "evidence_binding_profile",
        "future_evidence_required_fields_hash",
        "future_evidence_required_field_count",
        "future_evidence_hash_binding_fields_hash",
        "future_evidence_hash_binding_field_count",
        "si002_contract_record_hash",
        "si002_contract_record_content_sha256",
        "si002_invocation_record_hash",
        "si002_invocation_record_content_sha256",
        "si002_boundary_record_hash",
        "si002_boundary_record_content_sha256",
        "si002_gap_catalog_record_hash",
        "si002_gap_catalog_record_content_sha256",
        "si002_gap_catalog_acceptance_content_sha256",
        "test_only_runner_invocation_record_hash",
        "test_only_runner_invocation_reclassified_as_evaluator_evidence",
        "evaluator_evidence_instance_present",
        "actual_evaluator_invocation",
        "evaluation_execution_authority",
        "planner_execution_authority",
        "production_registration_enabled",
        "catalog_class_2_status",
        "catalog_class_1_status",
        "catalog_class_4_status",
        "catalog_class_5_status",
        "pb_b5_si_003_state",
    }
)

RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "record_class",
        "record_version",
        "request_hash",
        "implementation_id",
        "evaluator_capability_id",
        "evaluator_capability_identity_hash",
        "evidence_contract_id",
        "evidence_contract_identity_hash",
        "evidence_record_class",
        "evidence_origin_mode",
        "evidence_binding_profile",
        "future_evidence_required_fields_hash",
        "future_evidence_hash_binding_fields_hash",
        "decision",
        "reason_codes",
        "record_scope",
        "authority_effect",
        "evidence_record_contract_valid",
        "evaluator_evidence_instance_present",
        "catalog_prerequisite_addressed",
        "class_2_identity_status",
        "other_catalog_prerequisites_satisfied",
        "all_flip_prerequisites_satisfied",
        "actual_evaluator_invocation",
        "evaluation_execution_authority",
        "planner_execution_authority",
        "production_registration_enabled",
        "pb_b5_si_003_state",
        "stop_authority",
        "hash",
    }
)

IDENTITY_BINDING_FIELDS = frozenset(
    {
        "evaluator_capability_identity_hash",
        "evaluator_capability_identity_record_hash",
        "evaluator_capability_identity_record_content_sha256",
        "evaluator_capability_identity_acceptance_content_sha256",
    }
)
SI002_CHAIN_BINDING_FIELDS = frozenset(
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
        "test_only_runner_invocation_record_hash",
    }
)

NONDETERMINISTIC_OR_PAYLOAD_FIELDS = frozenset(
    {
        "random_seed",
        "randomized_observation_model",
        "probability_model",
        "learning_model",
        "hidden_ground_truth",
        "oracle_label",
        "evaluator_input",
        "evaluator_output",
        "evaluator_output_payload",
        "raw_evaluator_trace",
    }
)
ACTUAL_EVIDENCE_OR_INVOCATION_FIELDS = frozenset(
    {
        "evaluator_invocation_attempt_id",
        "evaluator_invocation_request_hash",
        "evaluator_input_hash",
        "evaluator_output_hash",
        "evidence_hash",
        "evidence_instance",
        "actual_evaluator_invocation_evidence",
        "evaluation_result",
        "evaluator_execution_requested",
        "runner_execution_requested",
    }
)
AUTHORITY_REQUEST_FIELDS = frozenset(
    {
        "authority_flip_requested",
        "evaluation_authority_requested",
        "planner_authority_requested",
        "explicit_owner_flip_go",
        "evidence_to_authority_binding",
    }
)
CATALOG_SCOPE_OVERREACH_FIELDS = frozenset(
    {
        "catalog_class_3_status",
        "prerequisites_satisfied",
        "all_flip_prerequisites_satisfied",
        "authority_flip_eligible",
    }
)
SI003_OR_PART_B_REQUEST_FIELDS = frozenset(
    {
        "pb_b5_si_003_closed",
        "scalarization",
        "scalar_score",
        "performance_claim",
        "measured_performance",
        "rank",
        "superiority_claim",
        "part_b_pass",
        "full_m3_star",
        "b6_execution_requested",
        "b7_execution_requested",
        "b8_execution_requested",
        "b9_execution_requested",
        "path_b_write",
        "mint",
        "kernel_or_e_case_write",
        "certificate",
        "CERTIFIED_STOP",
        "stop_requested",
    }
)

EXACT_ENVELOPE_VALUES = {
    "schema_version": "0.8.0",
    "request_kind": REQUEST_KIND,
    "request_version": "0.1.0",
    "requested_scope": REQUESTED_SCOPE,
}
EXACT_IDENTITY_VALUES = {
    "evaluator_capability_identity_hash": EVALUATOR_CAPABILITY_IDENTITY_HASH,
    "evaluator_capability_identity_record_hash": (
        EVALUATOR_CAPABILITY_IDENTITY_RECORD_HASH
    ),
    "evaluator_capability_identity_record_content_sha256": (
        EVALUATOR_CAPABILITY_IDENTITY_RECORD_CONTENT_SHA256
    ),
    "evaluator_capability_identity_acceptance_content_sha256": (
        EVALUATOR_CAPABILITY_IDENTITY_ACCEPTANCE_CONTENT_SHA256
    ),
}
EXACT_CONTRACT_SURFACE_VALUES = {
    "evidence_contract_id": EVIDENCE_CONTRACT_ID,
    "evidence_record_class": EVIDENCE_RECORD_CLASS,
    "evidence_origin_mode": EVIDENCE_ORIGIN_MODE,
    "evidence_binding_profile": EVIDENCE_BINDING_PROFILE,
}
EXACT_FIELD_CATALOG_VALUES = {
    "future_evidence_required_fields_hash": (
        FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH
    ),
    "future_evidence_required_field_count": 17,
    "future_evidence_hash_binding_fields_hash": (
        FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH
    ),
    "future_evidence_hash_binding_field_count": 8,
}
EXACT_SI002_CHAIN_VALUES = {
    "si002_contract_record_hash": SI002_CONTRACT_RECORD_HASH,
    "si002_contract_record_content_sha256": (
        SI002_CONTRACT_RECORD_CONTENT_SHA256
    ),
    "si002_invocation_record_hash": SI002_INVOCATION_RECORD_HASH,
    "si002_invocation_record_content_sha256": (
        SI002_INVOCATION_RECORD_CONTENT_SHA256
    ),
    "si002_boundary_record_hash": SI002_BOUNDARY_RECORD_HASH,
    "si002_boundary_record_content_sha256": (
        SI002_BOUNDARY_RECORD_CONTENT_SHA256
    ),
    "si002_gap_catalog_record_hash": SI002_GAP_CATALOG_RECORD_HASH,
    "si002_gap_catalog_record_content_sha256": (
        SI002_GAP_CATALOG_RECORD_CONTENT_SHA256
    ),
    "si002_gap_catalog_acceptance_content_sha256": (
        SI002_GAP_CATALOG_ACCEPTANCE_CONTENT_SHA256
    ),
    "test_only_runner_invocation_record_hash": (
        TEST_ONLY_RUNNER_INVOCATION_RECORD_HASH
    ),
}
EXACT_CATALOG_STATUS_VALUES = {
    "catalog_class_2_status": CLASS_2_STATUS,
    "catalog_class_1_status": MISSING_STATUS,
    "catalog_class_4_status": MISSING_STATUS,
    "catalog_class_5_status": MISSING_STATUS,
}

AUTHORITY_CEILING = {
    "record_scope": RECORD_SCOPE,
    "authority_effect": AUTHORITY_EFFECT,
    "evaluator_evidence_instance_present": False,
    "catalog_prerequisite_addressed": CATALOG_PREREQUISITE,
    "class_2_identity_status": CLASS_2_STATUS,
    "other_catalog_prerequisites_satisfied": False,
    "all_flip_prerequisites_satisfied": False,
    "actual_evaluator_invocation": False,
    "evaluation_execution_authority": False,
    "planner_execution_authority": False,
    "evidence_to_authority_binding_present": False,
    "scalarization_authority": False,
    "performance_claim_authority": False,
    "path_b_write_authority": False,
    "mint_authority": False,
    "kernel_or_e_case_write_authority": False,
    "certificate_authority": False,
    "stop_authority": "NONE",
    "production_registration_enabled": False,
    "pb_b5_si_003_state": SI003_STATE,
    "part_b_pass": False,
    "full_m3_star": False,
}


def _select_decision(request: Mapping[str, object]) -> str:
    keys = set(request)
    extra = keys - REQUEST_FIELDS

    if extra & SI003_OR_PART_B_REQUEST_FIELDS:
        return DENY_SI003_OR_PART_B_SCOPE
    if extra & CATALOG_SCOPE_OVERREACH_FIELDS:
        return DENY_CATALOG_SCOPE_OVERREACH
    if extra & AUTHORITY_REQUEST_FIELDS:
        return DENY_AUTHORITY_REQUEST
    if extra & ACTUAL_EVIDENCE_OR_INVOCATION_FIELDS:
        return DENY_ACTUAL_EVIDENCE_OR_INVOCATION
    if extra & NONDETERMINISTIC_OR_PAYLOAD_FIELDS:
        return DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT
    if extra:
        return DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT

    missing = REQUEST_FIELDS - keys
    if missing & IDENTITY_BINDING_FIELDS:
        return DENY_MISSING_IDENTITY_BINDING
    if missing & SI002_CHAIN_BINDING_FIELDS:
        return DENY_MISSING_SI002_CHAIN_BINDING
    if missing:
        return DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT

    implementation_id = request.get("implementation_id")
    if implementation_id == LEGACY_IMPLEMENTATION_ID:
        return DENY_LEGACY_IMPLEMENTATION
    if implementation_id != IMPLEMENTATION_ID:
        return DENY_UNKNOWN_IMPLEMENTATION

    if request.get("evaluator_capability_id") != EVALUATOR_CAPABILITY_ID:
        return DENY_UNKNOWN_CAPABILITY_ID

    if (
        request.get(
            "test_only_runner_invocation_reclassified_as_evaluator_evidence"
        )
        is not False
    ):
        return DENY_RUNNER_INVOCATION_RECLASSIFICATION

    if (
        request.get("evaluator_evidence_instance_present") is not False
        or request.get("actual_evaluator_invocation") is not False
    ):
        return DENY_ACTUAL_EVIDENCE_OR_INVOCATION

    if (
        request.get("evaluation_execution_authority") is not False
        or request.get("planner_execution_authority") is not False
    ):
        return DENY_AUTHORITY_REQUEST

    if any(
        request.get(field) != expected
        for field, expected in EXACT_CATALOG_STATUS_VALUES.items()
    ):
        return DENY_CATALOG_SCOPE_OVERREACH

    if any(
        request.get(field) != expected
        for field, expected in EXACT_IDENTITY_VALUES.items()
    ):
        return DENY_IDENTITY_HASH_MISMATCH

    if any(
        request.get(field) != expected
        for field, expected in EXACT_CONTRACT_SURFACE_VALUES.items()
    ):
        return DENY_EVIDENCE_CONTRACT_SURFACE_MISMATCH

    if (
        request.get("evidence_contract_identity_hash")
        != EVIDENCE_CONTRACT_IDENTITY_HASH
    ):
        return DENY_EVIDENCE_CONTRACT_HASH_MISMATCH

    if any(
        request.get(field) != expected
        for field, expected in EXACT_FIELD_CATALOG_VALUES.items()
    ):
        return DENY_EVIDENCE_FIELD_CATALOG_MISMATCH

    if any(
        request.get(field) != expected
        for field, expected in EXACT_SI002_CHAIN_VALUES.items()
    ):
        return DENY_SI002_CHAIN_HASH_MISMATCH

    if request.get("pb_b5_si_003_state") != SI003_STATE:
        return DENY_SI003_OR_PART_B_SCOPE

    if request.get("production_registration_enabled") is not False:
        return DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT

    if any(
        request.get(field) != expected
        for field, expected in EXACT_ENVELOPE_VALUES.items()
    ):
        return DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT

    return POSITIVE_DECISION


def evaluate_si002_evaluator_execution_evidence_record_contract(
    contract_request: Mapping[str, object],
) -> dict[str, object]:
    """Return a deterministic contract record with no evidence or invocation."""

    if not isinstance(contract_request, Mapping):
        raise ValueError("contract_request must be a mapping")

    decision = _select_decision(contract_request)
    contract_valid = decision == POSITIVE_DECISION
    record = {
        "schema_version": "0.8.0",
        "record_class": CONTRACT_DECISION_RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": canonical_value_hash(contract_request),
        "implementation_id": IMPLEMENTATION_ID,
        "evaluator_capability_id": EVALUATOR_CAPABILITY_ID,
        "evaluator_capability_identity_hash": (
            EVALUATOR_CAPABILITY_IDENTITY_HASH
        ),
        "evidence_contract_id": EVIDENCE_CONTRACT_ID,
        "evidence_contract_identity_hash": EVIDENCE_CONTRACT_IDENTITY_HASH,
        "evidence_record_class": EVIDENCE_RECORD_CLASS,
        "evidence_origin_mode": EVIDENCE_ORIGIN_MODE,
        "evidence_binding_profile": EVIDENCE_BINDING_PROFILE,
        "future_evidence_required_fields_hash": (
            FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH
        ),
        "future_evidence_hash_binding_fields_hash": (
            FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH
        ),
        "decision": decision,
        "reason_codes": [REASON_CODES[decision]],
        "record_scope": RECORD_SCOPE,
        "authority_effect": AUTHORITY_EFFECT,
        "evidence_record_contract_valid": contract_valid,
        "evaluator_evidence_instance_present": False,
        "catalog_prerequisite_addressed": (
            CATALOG_PREREQUISITE if contract_valid else "NONE"
        ),
        "class_2_identity_status": CLASS_2_STATUS,
        "other_catalog_prerequisites_satisfied": False,
        "all_flip_prerequisites_satisfied": False,
        "actual_evaluator_invocation": False,
        "evaluation_execution_authority": False,
        "planner_execution_authority": False,
        "production_registration_enabled": False,
        "pb_b5_si_003_state": SI003_STATE,
        "stop_authority": "NONE",
    }
    record["hash"] = canonical_document_hash(record)
    return record


__all__ = [
    "ACTUAL_EVALUATOR_INVOCATION",
    "AUTHORITY_CEILING",
    "AUTHORITY_EFFECT",
    "CATALOG_PREREQUISITE",
    "CLASS_2_STATUS",
    "CONTRACT_DECISION_RECORD_CLASS",
    "DENY_ACTUAL_EVIDENCE_OR_INVOCATION",
    "DENY_AUTHORITY_REQUEST",
    "DENY_CATALOG_SCOPE_OVERREACH",
    "DENY_EVIDENCE_CONTRACT_HASH_MISMATCH",
    "DENY_EVIDENCE_CONTRACT_SURFACE_MISMATCH",
    "DENY_EVIDENCE_FIELD_CATALOG_MISMATCH",
    "DENY_IDENTITY_HASH_MISMATCH",
    "DENY_LEGACY_IMPLEMENTATION",
    "DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT",
    "DENY_MISSING_IDENTITY_BINDING",
    "DENY_MISSING_SI002_CHAIN_BINDING",
    "DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT",
    "DENY_RUNNER_INVOCATION_RECLASSIFICATION",
    "DENY_SI002_CHAIN_HASH_MISMATCH",
    "DENY_SI003_OR_PART_B_SCOPE",
    "DENY_UNKNOWN_CAPABILITY_ID",
    "DENY_UNKNOWN_IMPLEMENTATION",
    "EVALUATION_EXECUTION_AUTHORITY",
    "EVALUATOR_CAPABILITY_ID",
    "EVALUATOR_CAPABILITY_IDENTITY_ACCEPTANCE_CONTENT_SHA256",
    "EVALUATOR_CAPABILITY_IDENTITY_HASH",
    "EVALUATOR_CAPABILITY_IDENTITY_RECORD_CONTENT_SHA256",
    "EVALUATOR_CAPABILITY_IDENTITY_RECORD_HASH",
    "EVALUATOR_EVIDENCE_INSTANCE_PRESENT",
    "EVIDENCE_BINDING_PROFILE",
    "EVIDENCE_CONTRACT_ID",
    "EVIDENCE_CONTRACT_IDENTITY_BASIS",
    "EVIDENCE_CONTRACT_IDENTITY_HASH",
    "EVIDENCE_ORIGIN_MODE",
    "EVIDENCE_RECORD_CLASS",
    "FUTURE_EVIDENCE_HASH_BINDING_FIELDS",
    "FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH",
    "FUTURE_EVIDENCE_REQUIRED_FIELDS",
    "FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH",
    "HARD_BAN",
    "IMPLEMENTATION_ID",
    "LEGACY_IMPLEMENTATION_ID",
    "MISSING_STATUS",
    "PLANNER_EXECUTION_AUTHORITY",
    "POSITIVE_DECISION",
    "PRODUCTION_REGISTRATION_ENABLED",
    "REASON_CODES",
    "RECORD_FIELDS",
    "RECORD_SCOPE",
    "REQUEST_FIELDS",
    "REQUEST_KIND",
    "REQUESTED_SCOPE",
    "SI002_BOUNDARY_RECORD_CONTENT_SHA256",
    "SI002_BOUNDARY_RECORD_HASH",
    "SI002_CONTRACT_RECORD_CONTENT_SHA256",
    "SI002_CONTRACT_RECORD_HASH",
    "SI002_GAP_CATALOG_ACCEPTANCE_CONTENT_SHA256",
    "SI002_GAP_CATALOG_RECORD_CONTENT_SHA256",
    "SI002_GAP_CATALOG_RECORD_HASH",
    "SI002_INVOCATION_RECORD_CONTENT_SHA256",
    "SI002_INVOCATION_RECORD_HASH",
    "SI003_STATE",
    "TEST_ONLY_RUNNER_INVOCATION_RECORD_HASH",
    "evaluate_si002_evaluator_execution_evidence_record_contract",
]
