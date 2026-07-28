"""Pure SI-002 evaluator-execution capability identity validator.

The module recognizes one exact, hash-bound deterministic Twin/P10 depth-1
candidacy callable as capability identity metadata only.  It never imports or
invokes that callable, the depth-1 planner, a runner, or an evaluator.  A
positive identity record addresses only catalog class 2 and does not establish
execution evidence or execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping

from src.ir.canonical_hash import canonical_document_hash, canonical_value_hash


PRODUCTION_REGISTRATION_ENABLED = False
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
EVALUATOR_CAPABILITY_CLASS = (
    "LOCAL_DETERMINISTIC_FIXED_CASE_MATCHING_EVALUATOR_CAPABILITY"
)
CAPABILITY_PROFILE = "PINNED_TWIN_P10_D1_READONLY_CANDIDACY_NO_TRACE"

CANDIDATE_MODULE_PATH = "src/planner/twin_p10_readonly_wiring.py"
CANDIDATE_ENTRYPOINT = (
    "evaluate_twin_p10_fixed_case_for_depth1_candidacy"
)
CANDIDATE_MODULE_CONTENT_SHA256 = (
    "1e1434e40191469f17f255905f4021fb"
    "273a323672604f0a017afe0384b5b4f9"
)
DETERMINISTIC_DEPENDENCY_MODULE_PATH = "src/planner/deterministic_depth1.py"
DETERMINISTIC_DEPENDENCY_CONTENT_SHA256 = (
    "ada6a8065e71fda58dde7e2b71ca19d7"
    "aded9a39f4cf5f67fb20d6fc5d7e38ff"
)
TWIN_FIXTURE_PATH = (
    "tests/unit/fixtures/kernel_a17_p1e_twin_p10_readonly_wiring_v0.1.json"
)
TWIN_FIXTURE_CONTENT_SHA256 = (
    "1191ba71a41c19131d7368df65ac8d345"
    "d8865af1aec59e300f7435d7536ddee"
)
P1E_FIXTURE_PATH = (
    "tests/unit/fixtures/kernel_a17_p1e_depth1_planner_v0.1.json"
)
P1E_FIXTURE_CONTENT_SHA256 = (
    "1154c5dec1073e0f42efa734212a6658d"
    "9fd9c4492016bbfd484ed7a502d088b"
)
SI002_INVOCATION_FIXTURE_PATH = (
    "tests/unit/fixtures/"
    "part_b_b5_si002_local_bounded_evaluation_harness_runner_invocation/"
    "synthetic-fixed-case-v0.1.json"
)
SI002_INVOCATION_FIXTURE_CONTENT_SHA256 = (
    "5587569a376a087cd648ae8bee00081fc"
    "10a5d48b17c63087407542d4412e086"
)
MATCHING_RULE_PROFILE = (
    "EXACT_TWIN_COUNTEREXAMPLE_001_P1E_DETERMINISTIC_"
    "MATCHING_NO_RANDOM_NO_HIDDEN_GT"
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

REQUEST_KIND = "ASSESS_SI002_EVALUATOR_EXECUTION_CAPABILITY_IDENTITY"
REQUESTED_SCOPE = (
    "LOCAL_EVALUATOR_EXECUTION_CAPABILITY_IDENTITY_"
    "CONTRACT_OR_RECORD_ONLY"
)
RECORD_CLASS = "LOCAL_EVALUATOR_EXECUTION_CAPABILITY_IDENTITY_RECORD"
RECORD_SCOPE = REQUESTED_SCOPE
AUTHORITY_EFFECT = "NONE_IDENTITY_RECORD_ONLY"
SI003_STATE = "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION"
CATALOG_PREREQUISITE = "ACCEPTED_EVALUATOR_EXECUTION_CAPABILITY_IDENTITY"

POSITIVE_DECISION = (
    "LOCAL_EVALUATOR_EXECUTION_CAPABILITY_IDENTITY_"
    "VALID_NO_EXECUTION_NO_FLIP"
)
DENY_UNKNOWN_IMPLEMENTATION = "DENY_UNKNOWN_IMPLEMENTATION"
DENY_UNKNOWN_CAPABILITY_ID = "DENY_UNKNOWN_CAPABILITY_ID"
DENY_LEGACY_IMPLEMENTATION = "DENY_LEGACY_IMPLEMENTATION"
DENY_MISSING_CHAIN_BINDING = "DENY_MISSING_CHAIN_BINDING"
DENY_HASH_MISMATCH = "DENY_HASH_MISMATCH"
DENY_CAPABILITY_SURFACE_MISMATCH = "DENY_CAPABILITY_SURFACE_MISMATCH"
DENY_NONDETERMINISTIC_INPUT = "DENY_NONDETERMINISTIC_INPUT"
DENY_EXECUTION_OR_EVIDENCE_REQUEST = "DENY_EXECUTION_OR_EVIDENCE_REQUEST"
DENY_AUTHORITY_REQUEST = "DENY_AUTHORITY_REQUEST"
DENY_CATALOG_SCOPE_OVERREACH = "DENY_CATALOG_SCOPE_OVERREACH"
DENY_SI003_OR_PART_B_SCOPE = "DENY_SI003_OR_PART_B_SCOPE"
DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT = (
    "DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT"
)

REASON_CODES = {
    POSITIVE_DECISION: "B5-SI002-EVAL-CAP-ID-000-VALID-NO-EXECUTION-NO-FLIP",
    DENY_UNKNOWN_IMPLEMENTATION: "B5-SI002-EVAL-CAP-ID-DENY-UNKNOWN-IMPLEMENTATION",
    DENY_UNKNOWN_CAPABILITY_ID: "B5-SI002-EVAL-CAP-ID-DENY-UNKNOWN-CAPABILITY",
    DENY_LEGACY_IMPLEMENTATION: "B5-SI002-EVAL-CAP-ID-DENY-LEGACY",
    DENY_MISSING_CHAIN_BINDING: "B5-SI002-EVAL-CAP-ID-DENY-MISSING-CHAIN",
    DENY_HASH_MISMATCH: "B5-SI002-EVAL-CAP-ID-DENY-HASH-MISMATCH",
    DENY_CAPABILITY_SURFACE_MISMATCH: "B5-SI002-EVAL-CAP-ID-DENY-SURFACE",
    DENY_NONDETERMINISTIC_INPUT: "B5-SI002-EVAL-CAP-ID-DENY-NONDETERMINISTIC",
    DENY_EXECUTION_OR_EVIDENCE_REQUEST: "B5-SI002-EVAL-CAP-ID-DENY-EXECUTION-EVIDENCE",
    DENY_AUTHORITY_REQUEST: "B5-SI002-EVAL-CAP-ID-DENY-AUTHORITY",
    DENY_CATALOG_SCOPE_OVERREACH: "B5-SI002-EVAL-CAP-ID-DENY-CATALOG-OVERREACH",
    DENY_SI003_OR_PART_B_SCOPE: "B5-SI002-EVAL-CAP-ID-DENY-SI003-PART-B",
    DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT: "B5-SI002-EVAL-CAP-ID-DENY-NON-CONTRACT",
}

IDENTITY_BASIS_FIELDS = (
    "evaluator_capability_id",
    "evaluator_capability_class",
    "capability_profile",
    "candidate_module_path",
    "candidate_entrypoint",
    "candidate_module_content_sha256",
    "deterministic_dependency_module_path",
    "deterministic_dependency_content_sha256",
    "twin_fixture_path",
    "twin_fixture_content_sha256",
    "p1e_fixture_path",
    "p1e_fixture_content_sha256",
    "si002_invocation_fixture_path",
    "si002_invocation_fixture_content_sha256",
    "matching_rule_profile",
    "deterministic_only",
)

IDENTITY_BASIS = {
    "evaluator_capability_id": EVALUATOR_CAPABILITY_ID,
    "evaluator_capability_class": EVALUATOR_CAPABILITY_CLASS,
    "capability_profile": CAPABILITY_PROFILE,
    "candidate_module_path": CANDIDATE_MODULE_PATH,
    "candidate_entrypoint": CANDIDATE_ENTRYPOINT,
    "candidate_module_content_sha256": CANDIDATE_MODULE_CONTENT_SHA256,
    "deterministic_dependency_module_path": DETERMINISTIC_DEPENDENCY_MODULE_PATH,
    "deterministic_dependency_content_sha256": (
        DETERMINISTIC_DEPENDENCY_CONTENT_SHA256
    ),
    "twin_fixture_path": TWIN_FIXTURE_PATH,
    "twin_fixture_content_sha256": TWIN_FIXTURE_CONTENT_SHA256,
    "p1e_fixture_path": P1E_FIXTURE_PATH,
    "p1e_fixture_content_sha256": P1E_FIXTURE_CONTENT_SHA256,
    "si002_invocation_fixture_path": SI002_INVOCATION_FIXTURE_PATH,
    "si002_invocation_fixture_content_sha256": (
        SI002_INVOCATION_FIXTURE_CONTENT_SHA256
    ),
    "matching_rule_profile": MATCHING_RULE_PROFILE,
    "deterministic_only": True,
}

if canonical_value_hash(IDENTITY_BASIS) != EVALUATOR_CAPABILITY_IDENTITY_HASH:
    raise RuntimeError("closed-world evaluator capability identity hash drift")

REQUEST_FIELDS = frozenset(
    {
        "schema_version",
        "request_kind",
        "request_version",
        "requested_scope",
        "implementation_id",
        "evaluator_capability_id",
        "evaluator_capability_identity_hash",
        "evaluator_capability_class",
        "capability_profile",
        "candidate_module_path",
        "candidate_entrypoint",
        "candidate_module_content_sha256",
        "deterministic_dependency_module_path",
        "deterministic_dependency_content_sha256",
        "twin_fixture_path",
        "twin_fixture_content_sha256",
        "p1e_fixture_path",
        "p1e_fixture_content_sha256",
        "si002_invocation_fixture_path",
        "si002_invocation_fixture_content_sha256",
        "matching_rule_profile",
        "deterministic_only",
        "si002_contract_record_hash",
        "si002_contract_record_content_sha256",
        "si002_invocation_record_hash",
        "si002_invocation_record_content_sha256",
        "si002_boundary_record_hash",
        "si002_boundary_record_content_sha256",
        "si002_gap_catalog_record_hash",
        "si002_gap_catalog_record_content_sha256",
        "si002_gap_catalog_acceptance_content_sha256",
        "actual_evaluator_invocation",
        "evaluation_execution_authority",
        "planner_execution_authority",
        "production_registration_enabled",
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
        "evaluator_capability_class",
        "capability_profile",
        "candidate_module_path",
        "candidate_entrypoint",
        "candidate_module_content_sha256",
        "deterministic_dependency_content_sha256",
        "decision",
        "reason_codes",
        "record_scope",
        "authority_effect",
        "capability_identity_contract_valid",
        "catalog_prerequisite_addressed",
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

CHAIN_BINDING_FIELDS = frozenset(
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

NONDETERMINISTIC_REQUEST_FIELDS = frozenset(
    {
        "random_seed",
        "randomized_observation_model",
        "probability_model",
        "learning_model",
        "hidden_ground_truth",
        "oracle_label",
    }
)
EXECUTION_OR_EVIDENCE_REQUEST_FIELDS = frozenset(
    {
        "evaluator_execution_requested",
        "evaluator_evidence_requested",
        "evaluator_execution_evidence",
        "actual_evaluator_invocation_evidence",
        "evaluation_result",
        "runner_execution_requested",
    }
)
AUTHORITY_REQUEST_FIELDS = frozenset(
    {
        "authority_flip_requested",
        "evaluation_authority_requested",
        "planner_authority_requested",
        "explicit_owner_flip_go",
    }
)
CATALOG_SCOPE_OVERREACH_FIELDS = frozenset(
    {
        "owner_flip_go_status",
        "evaluator_execution_evidence_status",
        "actual_evaluator_invocation_evidence_status",
        "evidence_to_authority_binding_status",
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
EXACT_SURFACE_VALUES = {
    "evaluator_capability_class": EVALUATOR_CAPABILITY_CLASS,
    "capability_profile": CAPABILITY_PROFILE,
    "candidate_module_path": CANDIDATE_MODULE_PATH,
    "candidate_entrypoint": CANDIDATE_ENTRYPOINT,
}
EXACT_HASH_BOUND_VALUES = {
    "evaluator_capability_identity_hash": EVALUATOR_CAPABILITY_IDENTITY_HASH,
    "candidate_module_content_sha256": CANDIDATE_MODULE_CONTENT_SHA256,
    "deterministic_dependency_module_path": DETERMINISTIC_DEPENDENCY_MODULE_PATH,
    "deterministic_dependency_content_sha256": (
        DETERMINISTIC_DEPENDENCY_CONTENT_SHA256
    ),
    "twin_fixture_path": TWIN_FIXTURE_PATH,
    "twin_fixture_content_sha256": TWIN_FIXTURE_CONTENT_SHA256,
    "p1e_fixture_path": P1E_FIXTURE_PATH,
    "p1e_fixture_content_sha256": P1E_FIXTURE_CONTENT_SHA256,
    "si002_invocation_fixture_path": SI002_INVOCATION_FIXTURE_PATH,
    "si002_invocation_fixture_content_sha256": (
        SI002_INVOCATION_FIXTURE_CONTENT_SHA256
    ),
}
EXACT_CHAIN_VALUES = {
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
}

AUTHORITY_CEILING = {
    "record_scope": RECORD_SCOPE,
    "authority_effect": AUTHORITY_EFFECT,
    "catalog_prerequisite_addressed": CATALOG_PREREQUISITE,
    "other_catalog_prerequisites_satisfied": False,
    "all_flip_prerequisites_satisfied": False,
    "actual_evaluator_invocation": False,
    "evaluation_execution_authority": False,
    "planner_execution_authority": False,
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
    if extra & EXECUTION_OR_EVIDENCE_REQUEST_FIELDS:
        return DENY_EXECUTION_OR_EVIDENCE_REQUEST
    if extra & NONDETERMINISTIC_REQUEST_FIELDS:
        return DENY_NONDETERMINISTIC_INPUT
    if extra:
        return DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT

    missing = REQUEST_FIELDS - keys
    if missing & CHAIN_BINDING_FIELDS:
        return DENY_MISSING_CHAIN_BINDING
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
        request.get("actual_evaluator_invocation") is not False
    ):
        return DENY_EXECUTION_OR_EVIDENCE_REQUEST
    if (
        request.get("evaluation_execution_authority") is not False
        or request.get("planner_execution_authority") is not False
    ):
        return DENY_AUTHORITY_REQUEST

    if request.get("deterministic_only") is not True:
        return DENY_NONDETERMINISTIC_INPUT
    if request.get("matching_rule_profile") != MATCHING_RULE_PROFILE:
        return DENY_NONDETERMINISTIC_INPUT

    if any(
        request.get(field) != expected
        for field, expected in EXACT_SURFACE_VALUES.items()
    ):
        return DENY_CAPABILITY_SURFACE_MISMATCH

    if any(
        request.get(field) != expected
        for field, expected in EXACT_HASH_BOUND_VALUES.items()
    ):
        return DENY_HASH_MISMATCH

    if any(
        request.get(field) != expected
        for field, expected in EXACT_CHAIN_VALUES.items()
    ):
        return DENY_MISSING_CHAIN_BINDING

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


def evaluate_si002_evaluator_execution_capability_identity(
    identity_request: Mapping[str, object],
) -> dict[str, object]:
    """Return a deterministic identity-only record with no execution or flip."""

    if not isinstance(identity_request, Mapping):
        raise ValueError("identity_request must be a mapping")

    decision = _select_decision(identity_request)
    identity_valid = decision == POSITIVE_DECISION
    record = {
        "schema_version": "0.8.0",
        "record_class": RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": canonical_value_hash(identity_request),
        "implementation_id": IMPLEMENTATION_ID,
        "evaluator_capability_id": EVALUATOR_CAPABILITY_ID,
        "evaluator_capability_identity_hash": (
            EVALUATOR_CAPABILITY_IDENTITY_HASH
        ),
        "evaluator_capability_class": EVALUATOR_CAPABILITY_CLASS,
        "capability_profile": CAPABILITY_PROFILE,
        "candidate_module_path": CANDIDATE_MODULE_PATH,
        "candidate_entrypoint": CANDIDATE_ENTRYPOINT,
        "candidate_module_content_sha256": CANDIDATE_MODULE_CONTENT_SHA256,
        "deterministic_dependency_content_sha256": (
            DETERMINISTIC_DEPENDENCY_CONTENT_SHA256
        ),
        "decision": decision,
        "reason_codes": [REASON_CODES[decision]],
        "record_scope": RECORD_SCOPE,
        "authority_effect": AUTHORITY_EFFECT,
        "capability_identity_contract_valid": identity_valid,
        "catalog_prerequisite_addressed": (
            CATALOG_PREREQUISITE if identity_valid else "NONE"
        ),
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
    "CAPABILITY_PROFILE",
    "CATALOG_PREREQUISITE",
    "CANDIDATE_ENTRYPOINT",
    "CANDIDATE_MODULE_CONTENT_SHA256",
    "CANDIDATE_MODULE_PATH",
    "DENY_AUTHORITY_REQUEST",
    "DENY_CAPABILITY_SURFACE_MISMATCH",
    "DENY_CATALOG_SCOPE_OVERREACH",
    "DENY_EXECUTION_OR_EVIDENCE_REQUEST",
    "DENY_HASH_MISMATCH",
    "DENY_LEGACY_IMPLEMENTATION",
    "DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT",
    "DENY_MISSING_CHAIN_BINDING",
    "DENY_NONDETERMINISTIC_INPUT",
    "DENY_SI003_OR_PART_B_SCOPE",
    "DENY_UNKNOWN_CAPABILITY_ID",
    "DENY_UNKNOWN_IMPLEMENTATION",
    "DETERMINISTIC_DEPENDENCY_CONTENT_SHA256",
    "DETERMINISTIC_DEPENDENCY_MODULE_PATH",
    "EVALUATION_EXECUTION_AUTHORITY",
    "EVALUATOR_CAPABILITY_CLASS",
    "EVALUATOR_CAPABILITY_ID",
    "EVALUATOR_CAPABILITY_IDENTITY_HASH",
    "HARD_BAN",
    "IDENTITY_BASIS",
    "IDENTITY_BASIS_FIELDS",
    "IMPLEMENTATION_ID",
    "LEGACY_IMPLEMENTATION_ID",
    "MATCHING_RULE_PROFILE",
    "P1E_FIXTURE_CONTENT_SHA256",
    "P1E_FIXTURE_PATH",
    "PLANNER_EXECUTION_AUTHORITY",
    "POSITIVE_DECISION",
    "PRODUCTION_REGISTRATION_ENABLED",
    "REASON_CODES",
    "RECORD_CLASS",
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
    "SI002_INVOCATION_FIXTURE_CONTENT_SHA256",
    "SI002_INVOCATION_FIXTURE_PATH",
    "SI002_INVOCATION_RECORD_CONTENT_SHA256",
    "SI002_INVOCATION_RECORD_HASH",
    "SI003_STATE",
    "TWIN_FIXTURE_CONTENT_SHA256",
    "TWIN_FIXTURE_PATH",
    "evaluate_si002_evaluator_execution_capability_identity",
]
