"""Pure SI-002 evaluation-execution-authority boundary evaluator.

The module recognizes one exact, already accepted D1/SI-002 record chain and
returns a deterministic boundary record.  It never invokes a Planner, Twin
runner, evaluator, process, meter, registry, or write path.  The sole positive
decision validates a no-flip boundary; it does not grant execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping

from src.ir.canonical_hash import canonical_document_hash, canonical_value_hash


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
SI002_CONTRACT_POLICY_CONTENT_SHA256 = (
    "4263369a1a5fd6f2bdd39ba58cbff139"
    "2ecbb90678766f23f39ac3954a364035"
)
SI002_INVOCATION_RECORD_HASH = (
    "sha256:1ebee7beb9621d90f87b4f192c19c650"
    "a3db4bb4a1c4558546f2e5168e52860c"
)
SI002_INVOCATION_RECORD_CONTENT_SHA256 = (
    "bdbb4a6aea269503eb127bbbc949517ee"
    "995f042d09a3810e8af96bfbe30b851"
)
SI002_INVOCATION_POLICY_CONTENT_SHA256 = (
    "0536a8a1b69c89af360df850be709bda"
    "1216296704ce872796420e553f9a1a9b"
)
INVOCATION_DECISION = (
    "LOCAL_BOUNDED_EVALUATION_HARNESS_RUNNER_INVOCATION_"
    "RECORDED_TEST_ONLY"
)

REQUEST_KIND = "ASSESS_SI002_EVALUATION_EXECUTION_AUTHORITY_BOUNDARY"
REQUESTED_ASSESSMENT_SCOPE = (
    "LOCAL_EVALUATION_EXECUTION_AUTHORITY_BOUNDARY_"
    "CONTRACT_OR_RECORD_ONLY"
)
RECORD_CLASS = "LOCAL_EVALUATION_EXECUTION_AUTHORITY_BOUNDARY_RECORD"
RECORD_SCOPE = REQUESTED_ASSESSMENT_SCOPE
AUTHORITY_EFFECT = "NONE_BOUNDARY_RECORD_ONLY"
SI003_STATE = "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION"

POSITIVE_DECISION = (
    "LOCAL_EVALUATION_EXECUTION_AUTHORITY_BOUNDARY_VALID_NO_FLIP"
)
DENY_UNKNOWN = "DENY_UNKNOWN_IMPLEMENTATION"
DENY_LEGACY = "DENY_LEGACY_IMPLEMENTATION"
DENY_MISSING = "DENY_MISSING_SI002_BINDING"
DENY_MISMATCH = "DENY_HASH_MISMATCH"
DENY_SILENT_FLIP = "DENY_SILENT_AUTHORITY_FLIP"
DENY_AUTHORITY = "DENY_AUTHORITY_REQUEST"
DENY_NON_CONTRACT = "DENY_NON_CONTRACT_INPUT"
DENY_NON_SUBSTITUTE = "DENY_NON_SUBSTITUTE_NO_AUTHORITY_ELEVATION"
DENY_SI003_OPEN = "DENY_SI003_REMAINS_OPEN"

REASON_CODES = {
    POSITIVE_DECISION: "B5-SI002-AUTH-BOUNDARY-000-VALID-NO-FLIP",
    DENY_UNKNOWN: "B5-SI002-AUTH-BOUNDARY-DENY-UNKNOWN-ID",
    DENY_LEGACY: "B5-SI002-AUTH-BOUNDARY-DENY-LEGACY-ID",
    DENY_MISSING: "B5-SI002-AUTH-BOUNDARY-DENY-MISSING-BINDING",
    DENY_MISMATCH: "B5-SI002-AUTH-BOUNDARY-DENY-HASH-MISMATCH",
    DENY_SILENT_FLIP: "B5-SI002-AUTH-BOUNDARY-DENY-SILENT-FLIP",
    DENY_AUTHORITY: "B5-SI002-AUTH-BOUNDARY-DENY-AUTHORITY",
    DENY_NON_CONTRACT: "B5-SI002-AUTH-BOUNDARY-DENY-NON-CONTRACT",
    DENY_NON_SUBSTITUTE: (
        "B5-SI002-AUTH-BOUNDARY-DENY-NON-SUBSTITUTE"
    ),
    DENY_SI003_OPEN: "B5-SI002-AUTH-BOUNDARY-DENY-SI003-OPEN",
}

REQUEST_FIELDS = frozenset(
    {
        "schema_version",
        "request_kind",
        "request_version",
        "requested_assessment_scope",
        "implementation_id",
        "implementation_identity_hash",
        "harness_contract_identity_hash",
        "si002_contract_record_hash",
        "si002_contract_record_content_sha256",
        "si002_contract_policy_content_sha256",
        "si002_invocation_record_hash",
        "si002_invocation_record_content_sha256",
        "si002_invocation_policy_content_sha256",
        "invocation_decision",
        "actual_runner_invocation",
        "actual_evaluator_invocation",
        "evaluation_execution_authority",
        "planner_execution_authority",
        "later_separate_owner_authority_flip_go_present",
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
        "harness_contract_identity_hash",
        "si002_contract_record_hash",
        "si002_invocation_record_hash",
        "decision",
        "reason_codes",
        "record_scope",
        "authority_effect",
        "actual_runner_invocation",
        "actual_evaluator_invocation",
        "evaluation_execution_authority",
        "planner_execution_authority",
        "pb_b5_si_003_state",
        "stop_authority",
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
        "system_state",
        "b6_execution_requested",
        "b7_execution_requested",
        "b8_execution_requested",
        "b9_execution_requested",
        "production_registration_enabled",
        "action_payload",
        "evaluation_result",
    }
)

SI003_REQUEST_FIELDS = frozenset(
    {
        "pb_b5_si_003_closed",
        "scalarization",
        "scalar_score",
        "performance_claim",
        "measured_performance",
        "rank",
        "superiority_claim",
    }
)

NON_SUBSTITUTE_REQUEST_FIELDS = frozenset(
    {
        "part_b_pass",
        "full_m3_star",
        "authority_elevation",
    }
)

EXACT_REQUEST_VALUES = {
    "schema_version": "0.8.0",
    "request_kind": REQUEST_KIND,
    "request_version": "0.1.0",
    "requested_assessment_scope": REQUESTED_ASSESSMENT_SCOPE,
    "implementation_identity_hash": IMPLEMENTATION_IDENTITY_HASH,
    "harness_contract_identity_hash": HARNESS_CONTRACT_IDENTITY_HASH,
    "si002_contract_record_hash": SI002_CONTRACT_RECORD_HASH,
    "si002_contract_record_content_sha256": (
        SI002_CONTRACT_RECORD_CONTENT_SHA256
    ),
    "si002_contract_policy_content_sha256": (
        SI002_CONTRACT_POLICY_CONTENT_SHA256
    ),
    "si002_invocation_record_hash": SI002_INVOCATION_RECORD_HASH,
    "si002_invocation_record_content_sha256": (
        SI002_INVOCATION_RECORD_CONTENT_SHA256
    ),
    "si002_invocation_policy_content_sha256": (
        SI002_INVOCATION_POLICY_CONTENT_SHA256
    ),
    "invocation_decision": INVOCATION_DECISION,
}

AUTHORITY_CEILING = {
    "record_scope": RECORD_SCOPE,
    "authority_effect": AUTHORITY_EFFECT,
    "actual_runner_invocation_record_fact": True,
    "actual_evaluator_invocation": False,
    "evaluation_execution_authority": False,
    (
        "evaluation_execution_authority_in_future_boundary_green_"
        "without_later_explicit_owner_flip_go"
    ): False,
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

    if extra & SI003_REQUEST_FIELDS:
        return DENY_SI003_OPEN
    if extra & NON_SUBSTITUTE_REQUEST_FIELDS:
        return DENY_NON_SUBSTITUTE
    if extra & AUTHORITY_REQUEST_FIELDS:
        return DENY_AUTHORITY
    if extra:
        return DENY_NON_CONTRACT
    if REQUEST_FIELDS - keys:
        return DENY_MISSING

    implementation_id = request.get("implementation_id")
    if implementation_id == LEGACY_IMPLEMENTATION_ID:
        return DENY_LEGACY
    if implementation_id != IMPLEMENTATION_ID:
        return DENY_UNKNOWN

    if (
        request.get("actual_evaluator_invocation") is not False
        or request.get("evaluation_execution_authority") is not False
        or request.get("later_separate_owner_authority_flip_go_present")
        is not False
    ):
        return DENY_SILENT_FLIP
    if request.get("planner_execution_authority") is not False:
        return DENY_AUTHORITY

    if any(
        request.get(field) != expected
        for field, expected in EXACT_REQUEST_VALUES.items()
    ):
        return DENY_MISMATCH
    if request.get("actual_runner_invocation") is not True:
        return DENY_MISMATCH

    return POSITIVE_DECISION


def evaluate_si002_evaluation_execution_authority_boundary(
    boundary_request: Mapping[str, object],
) -> dict[str, object]:
    """Return one deterministic boundary record without invoking execution."""

    if not isinstance(boundary_request, Mapping):
        raise ValueError("boundary_request must be a mapping")

    decision = _select_decision(boundary_request)
    record = {
        "schema_version": "0.8.0",
        "record_class": RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": canonical_value_hash(boundary_request),
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_identity_hash": IMPLEMENTATION_IDENTITY_HASH,
        "harness_contract_identity_hash": HARNESS_CONTRACT_IDENTITY_HASH,
        "si002_contract_record_hash": SI002_CONTRACT_RECORD_HASH,
        "si002_invocation_record_hash": SI002_INVOCATION_RECORD_HASH,
        "decision": decision,
        "reason_codes": [REASON_CODES[decision]],
        "record_scope": RECORD_SCOPE,
        "authority_effect": AUTHORITY_EFFECT,
        "actual_runner_invocation": True,
        "actual_evaluator_invocation": False,
        "evaluation_execution_authority": False,
        "planner_execution_authority": False,
        "pb_b5_si_003_state": SI003_STATE,
        "stop_authority": "NONE",
    }
    record["hash"] = canonical_document_hash(record)
    return record


__all__ = [
    "AUTHORITY_CEILING",
    "AUTHORITY_EFFECT",
    "DENY_AUTHORITY",
    "DENY_LEGACY",
    "DENY_MISMATCH",
    "DENY_MISSING",
    "DENY_NON_CONTRACT",
    "DENY_NON_SUBSTITUTE",
    "DENY_SI003_OPEN",
    "DENY_SILENT_FLIP",
    "DENY_UNKNOWN",
    "EVALUATION_EXECUTION_AUTHORITY",
    "HARD_BAN",
    "HARNESS_CONTRACT_IDENTITY_HASH",
    "IMPLEMENTATION_ID",
    "IMPLEMENTATION_IDENTITY_HASH",
    "INVOCATION_DECISION",
    "LEGACY_IMPLEMENTATION_ID",
    "PLANNER_EXECUTION_AUTHORITY",
    "POSITIVE_DECISION",
    "PRODUCTION_REGISTRATION_ENABLED",
    "REASON_CODES",
    "RECORD_CLASS",
    "RECORD_FIELDS",
    "RECORD_SCOPE",
    "REQUEST_FIELDS",
    "REQUEST_KIND",
    "REQUESTED_ASSESSMENT_SCOPE",
    "SI002_CONTRACT_POLICY_CONTENT_SHA256",
    "SI002_CONTRACT_RECORD_CONTENT_SHA256",
    "SI002_CONTRACT_RECORD_HASH",
    "SI002_INVOCATION_POLICY_CONTENT_SHA256",
    "SI002_INVOCATION_RECORD_CONTENT_SHA256",
    "SI002_INVOCATION_RECORD_HASH",
    "SI003_STATE",
    "evaluate_si002_evaluation_execution_authority_boundary",
]
