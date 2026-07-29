"""Pure SI-003 performance/scalarization authority-boundary validator.

This module binds the accepted SI-002 evaluation-authority flip and records
only that SI-003 remains open with no scalarization, performance, superiority,
planner, Part B, Path B, or STOP authority.  It invokes no runtime.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.ir.canonical_hash import canonical_document_hash, canonical_value_hash


PRODUCTION_REGISTRATION_ENABLED = False
EVALUATION_EXECUTION_AUTHORITY = True
PLANNER_EXECUTION_AUTHORITY = False
SCALARIZATION_AUTHORITY = False
PERFORMANCE_CLAIM_AUTHORITY = False
SUPERIORITY_CLAIM_AUTHORITY = False

HARD_BAN = (
    "Path A / Kernel design GREEN must not be inferred as L2 PASS, "
    "Part B PASS, or unrestricted Part B elevation."
)

AUTHORITY_BASE_COMMIT = "2fe4831f81f994ceff6f70ac01b51b980df77fcc"
GREEN_GO_CONTENT_SHA256 = (
    "900603dcaf0276e778e17d6b7bc24114c81d4ef9f3c7356ba9f1316cd686bac7"
)
GREEN_GO_DECISION = (
    "AUTHORIZE_PART_B_B5_SI003_PERFORMANCE_AND_SCALARIZATION_"
    "AUTHORITY_BOUNDARY_GREEN_ONLY"
)
RED_GO_CONTENT_SHA256 = (
    "fa17377fb9934381e5eb66b79db6fd127e98f794aebc6194c8d5c81d83c14aa7"
)
AUTHORITY_KIND = "EXPLICIT_OWNER_SI003_AUTHORITY_BOUNDARY_GREEN_ONLY"
AUTHORIZED_CELL = (
    "PART_B_B5_SI003_PERFORMANCE_AND_SCALARIZATION_AUTHORITY_BOUNDARY_GREEN"
)

IMPLEMENTATION_ID = "part_b_b5_m3_kernel_d1_twin_readonly_conformance_v0.1"
LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"
ISSUE_ID = "PB-B5-SI-003"
SI003_STATE = "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION"
FLIP_CONTRACT_IDENTITY_HASH = (
    "sha256:4ed46d2474cda603bdbd850c288d35193d96760f242ac83b236ae7939d80bdb3"
)
FLIP_RECORD_HASH = (
    "sha256:b4e4cabb30b1d41e389a59606e26efd02a2b3386dea9c90c41a45dfca8839fbf"
)
FLIP_RECORD_CONTENT_SHA256 = (
    "414e710b16c9073ca463d4f23afbc20253eb91d83bf427e1c38c5abfb8cb27f0"
)
FLIP_ACCEPTANCE_CONTENT_SHA256 = (
    "b8a97b460a70d1eaa2a26533ca997956086ee494f0b5ce77f32142abbdfaa4de"
)
EXPLICIT_OWNER_FLIP_GO_CONTENT_SHA256 = (
    "ccb5863d7cd096428365eb7fdb6720e2871928385beb685b73ab38411db55f4c"
)
RESOURCE_VECTOR_MODEL = "EIGHT_DIMENSIONAL_NO_SCALARIZATION"
CONTRACT_CLAIM_CEILING = "CONTRACT_CONSISTENCY_ONLY"
REQUEST_KIND = "ASSESS_SI003_PERFORMANCE_AND_SCALARIZATION_AUTHORITY_BOUNDARY"
REQUESTED_SCOPE = (
    "LOCAL_SI003_PERFORMANCE_AND_SCALARIZATION_AUTHORITY_BOUNDARY_"
    "OR_GAP_RECORD_ONLY"
)
RECORD_CLASS = "LOCAL_SI003_PERFORMANCE_AND_SCALARIZATION_AUTHORITY_BOUNDARY_RECORD"
AUTHORITY_EFFECT = "NONE_BOUNDARY_RECORD_ONLY_SI003_REMAINS_OPEN"

POSITIVE_DECISION = (
    "LOCAL_SI003_PERFORMANCE_AND_SCALARIZATION_AUTHORITY_"
    "BOUNDARY_VALID_NO_CLOSE_NO_CLAIM"
)
DENY_EXPLICIT_OWNER_BOUNDARY_AUTHORITY = "DENY_EXPLICIT_OWNER_BOUNDARY_AUTHORITY"
DENY_UNKNOWN_IMPLEMENTATION = "DENY_UNKNOWN_IMPLEMENTATION"
DENY_WRONG_ISSUE = "DENY_WRONG_ISSUE"
DENY_SI003_STATE = "DENY_SI003_STATE"
DENY_SI003_CLOSE_REQUEST = "DENY_SI003_CLOSE_REQUEST"
DENY_FLIP_BINDING_MISMATCH = "DENY_FLIP_BINDING_MISMATCH"
DENY_POST_FLIP_EVAL_AUTHORITY_MISMATCH = "DENY_POST_FLIP_EVAL_AUTHORITY_MISMATCH"
DENY_PLANNER_SCOPE = "DENY_PLANNER_SCOPE"
DENY_SCALARIZATION_SCOPE = "DENY_SCALARIZATION_SCOPE"
DENY_PERFORMANCE_CLAIM_SCOPE = "DENY_PERFORMANCE_CLAIM_SCOPE"
DENY_SUPERIORITY_SCOPE = "DENY_SUPERIORITY_SCOPE"
DENY_RESOURCE_VECTOR_MODEL = "DENY_RESOURCE_VECTOR_MODEL"
DENY_CLAIM_CEILING = "DENY_CLAIM_CEILING"
DENY_RED_GO_REUSED_AS_CLOSE_GO = "DENY_RED_GO_REUSED_AS_CLOSE_GO"
DENY_SELF_ASSERTED_CLOSE_GO = "DENY_SELF_ASSERTED_CLOSE_GO"
DENY_PART_B_OR_PATH_B_OR_STOP_SCOPE = "DENY_PART_B_OR_PATH_B_OR_STOP_SCOPE"
DENY_B6_B9_SCOPE = "DENY_B6_B9_SCOPE"
DENY_EXTRA_INPUT = "DENY_EXTRA_INPUT"
DENY_PROTECTED_BYTE_MUTATION = "DENY_PROTECTED_BYTE_MUTATION"

DECISION_ENUM = (
    POSITIVE_DECISION,
    DENY_EXPLICIT_OWNER_BOUNDARY_AUTHORITY,
    DENY_UNKNOWN_IMPLEMENTATION,
    DENY_WRONG_ISSUE,
    DENY_SI003_STATE,
    DENY_SI003_CLOSE_REQUEST,
    DENY_FLIP_BINDING_MISMATCH,
    DENY_POST_FLIP_EVAL_AUTHORITY_MISMATCH,
    DENY_PLANNER_SCOPE,
    DENY_SCALARIZATION_SCOPE,
    DENY_PERFORMANCE_CLAIM_SCOPE,
    DENY_SUPERIORITY_SCOPE,
    DENY_RESOURCE_VECTOR_MODEL,
    DENY_CLAIM_CEILING,
    DENY_RED_GO_REUSED_AS_CLOSE_GO,
    DENY_SELF_ASSERTED_CLOSE_GO,
    DENY_PART_B_OR_PATH_B_OR_STOP_SCOPE,
    DENY_B6_B9_SCOPE,
    DENY_EXTRA_INPUT,
    DENY_PROTECTED_BYTE_MUTATION,
)
REASON_CODES = {
    decision: f"B5-SI003-BOUNDARY-{index:03d}"
    for index, decision in enumerate(DECISION_ENUM)
}

AUTHORITY_FIELDS = (
    "schema_version",
    "authority_kind",
    "authorized_cell",
    "authority_base_commit",
    "green_go_content_sha256",
    "green_go_decision",
)
REQUEST_FIELDS = (
    "schema_version",
    "request_kind",
    "request_version",
    "requested_assessment_scope",
    "implementation_id",
    "issue_id",
    "pb_b5_si_003_state",
    "pb_b5_si_003_close_requested",
    "evaluation_execution_authority",
    "planner_execution_authority",
    "scalarization_authority",
    "performance_claim_authority",
    "superiority_claim_authority",
    "flip_contract_identity_hash",
    "flip_record_hash",
    "flip_record_content_sha256",
    "flip_acceptance_content_sha256",
    "explicit_owner_flip_go_content_sha256",
    "resource_vector_model",
    "contract_claim_ceiling",
    "later_separate_owner_si003_close_go_present",
    "this_red_go_reused_as_close_go",
)
RECORD_FIELDS = (
    "schema_version",
    "record_class",
    "record_version",
    "request_hash",
    "implementation_id",
    "issue_id",
    "decision",
    "reason_codes",
    "record_scope",
    "authority_effect",
    "pb_b5_si_003_state",
    "si003_closed",
    "evaluation_execution_authority",
    "planner_execution_authority",
    "scalarization_authority",
    "performance_claim_authority",
    "superiority_claim_authority",
    "resource_vector_model",
    "contract_claim_ceiling",
    "part_b_pass",
    "path_b_write_authority",
    "stop_authority",
    "full_m3_star",
    "hash",
)

AUTHORITY_FIELD_CATALOG_HASH = (
    "sha256:4add2c172bff0796362e0bad03234103ca7dc31cd1134509620e08d52831ea8d"
)
REQUEST_FIELD_CATALOG_HASH = (
    "sha256:6b6d57950aa1827eab837df486efb126a7e1a0f3bb927e76556ea41ee7b84102"
)
RECORD_FIELD_CATALOG_HASH = (
    "sha256:00471cbbc820cf3261a39f02bb15f0f9bd1dd9b0538cb9faa93df0b6fac10d67"
)

EXPECTED_AUTHORITY: dict[str, object] = {
    "schema_version": "0.8.0",
    "authority_kind": AUTHORITY_KIND,
    "authorized_cell": AUTHORIZED_CELL,
    "authority_base_commit": AUTHORITY_BASE_COMMIT,
    "green_go_content_sha256": GREEN_GO_CONTENT_SHA256,
    "green_go_decision": GREEN_GO_DECISION,
}

EXPECTED_REQUEST: dict[str, object] = {
    "schema_version": "0.8.0",
    "request_kind": REQUEST_KIND,
    "request_version": "0.1.0",
    "requested_assessment_scope": REQUESTED_SCOPE,
    "implementation_id": IMPLEMENTATION_ID,
    "issue_id": ISSUE_ID,
    "pb_b5_si_003_state": SI003_STATE,
    "pb_b5_si_003_close_requested": False,
    "evaluation_execution_authority": True,
    "planner_execution_authority": False,
    "scalarization_authority": False,
    "performance_claim_authority": False,
    "superiority_claim_authority": False,
    "flip_contract_identity_hash": FLIP_CONTRACT_IDENTITY_HASH,
    "flip_record_hash": FLIP_RECORD_HASH,
    "flip_record_content_sha256": FLIP_RECORD_CONTENT_SHA256,
    "flip_acceptance_content_sha256": FLIP_ACCEPTANCE_CONTENT_SHA256,
    "explicit_owner_flip_go_content_sha256": EXPLICIT_OWNER_FLIP_GO_CONTENT_SHA256,
    "resource_vector_model": RESOURCE_VECTOR_MODEL,
    "contract_claim_ceiling": CONTRACT_CLAIM_CEILING,
    "later_separate_owner_si003_close_go_present": False,
    "this_red_go_reused_as_close_go": False,
}

FLIP_BINDING_FIELDS = frozenset({
    "flip_contract_identity_hash",
    "flip_record_hash",
    "flip_record_content_sha256",
    "flip_acceptance_content_sha256",
    "explicit_owner_flip_go_content_sha256",
})
PART_B_SCOPE_FIELDS = frozenset({
    "part_b_pass_requested", "path_b_write_requested", "stop_requested",
    "certificate_requested", "full_m3_star_requested",
})
B6_B9_FIELDS = frozenset({
    "b6_execution_requested", "b7_execution_requested",
    "b8_execution_requested", "b9_execution_requested",
})
PROTECTED_MUTATION_FIELDS = frozenset({
    "mutate_protected_bytes", "mutate_si002_class1_class5_bytes",
    "rewrite_flip_record", "rewrite_class5_record",
})


def evaluate_si003_performance_scalarization_authority_boundary(
    boundary_request: Mapping[str, Any] | object,
    *,
    explicit_owner_boundary_authority: Mapping[str, Any] | object,
) -> dict[str, object]:
    """Return the deterministic no-close/no-claim SI-003 boundary record."""

    if not _valid_authority(explicit_owner_boundary_authority):
        return _record(boundary_request, DENY_EXPLICIT_OWNER_BOUNDARY_AUTHORITY)
    if not isinstance(boundary_request, Mapping):
        return _record(boundary_request, DENY_EXTRA_INPUT)
    return _record(boundary_request, _select_decision(boundary_request))


def _valid_authority(authority: object) -> bool:
    return (
        isinstance(authority, Mapping)
        and set(authority) == set(AUTHORITY_FIELDS)
        and dict(authority) == EXPECTED_AUTHORITY
    )


def _select_decision(request: Mapping[str, Any]) -> str:
    keys = set(request)
    expected = set(REQUEST_FIELDS)
    extra = keys - expected
    missing = expected - keys

    if extra & PROTECTED_MUTATION_FIELDS:
        return DENY_PROTECTED_BYTE_MUTATION
    if extra & B6_B9_FIELDS:
        return DENY_B6_B9_SCOPE
    if extra & PART_B_SCOPE_FIELDS:
        return DENY_PART_B_OR_PATH_B_OR_STOP_SCOPE
    if extra or missing:
        return DENY_EXTRA_INPUT

    if request.get("implementation_id") != IMPLEMENTATION_ID:
        return DENY_UNKNOWN_IMPLEMENTATION
    if request.get("issue_id") != ISSUE_ID:
        return DENY_WRONG_ISSUE
    if request.get("pb_b5_si_003_state") != SI003_STATE:
        return DENY_SI003_STATE
    if request.get("pb_b5_si_003_close_requested") is not False:
        return DENY_SI003_CLOSE_REQUEST
    if any(request.get(field) != EXPECTED_REQUEST[field] for field in FLIP_BINDING_FIELDS):
        return DENY_FLIP_BINDING_MISMATCH
    if request.get("evaluation_execution_authority") is not True:
        return DENY_POST_FLIP_EVAL_AUTHORITY_MISMATCH
    if request.get("planner_execution_authority") is not False:
        return DENY_PLANNER_SCOPE
    if request.get("scalarization_authority") is not False:
        return DENY_SCALARIZATION_SCOPE
    if request.get("performance_claim_authority") is not False:
        return DENY_PERFORMANCE_CLAIM_SCOPE
    if request.get("superiority_claim_authority") is not False:
        return DENY_SUPERIORITY_SCOPE
    if request.get("resource_vector_model") != RESOURCE_VECTOR_MODEL:
        return DENY_RESOURCE_VECTOR_MODEL
    if request.get("contract_claim_ceiling") != CONTRACT_CLAIM_CEILING:
        return DENY_CLAIM_CEILING
    if request.get("this_red_go_reused_as_close_go") is not False:
        return DENY_RED_GO_REUSED_AS_CLOSE_GO
    if request.get("later_separate_owner_si003_close_go_present") is not False:
        return DENY_SELF_ASSERTED_CLOSE_GO
    if any(request.get(field) != value for field, value in EXPECTED_REQUEST.items()):
        return DENY_EXTRA_INPUT
    return POSITIVE_DECISION


def _record(request: object, decision: str) -> dict[str, object]:
    source = request if isinstance(request, Mapping) else {}
    result: dict[str, object] = {
        "schema_version": "0.8.0",
        "record_class": RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": _safe_request_hash(request),
        "implementation_id": source.get("implementation_id"),
        "issue_id": ISSUE_ID,
        "decision": decision,
        "reason_codes": [REASON_CODES[decision]],
        "record_scope": REQUESTED_SCOPE,
        "authority_effect": AUTHORITY_EFFECT,
        "pb_b5_si_003_state": SI003_STATE,
        "si003_closed": False,
        "evaluation_execution_authority": True,
        "planner_execution_authority": False,
        "scalarization_authority": False,
        "performance_claim_authority": False,
        "superiority_claim_authority": False,
        "resource_vector_model": RESOURCE_VECTOR_MODEL,
        "contract_claim_ceiling": CONTRACT_CLAIM_CEILING,
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
if set(EXPECTED_REQUEST) != set(REQUEST_FIELDS):
    raise RuntimeError("expected request field drift")
if len(DECISION_ENUM) != len(set(DECISION_ENUM)):
    raise RuntimeError("decision enum duplicates")


__all__ = [
    "AUTHORITY_FIELDS", "AUTHORITY_FIELD_CATALOG_HASH", "DECISION_ENUM",
    "EXPECTED_AUTHORITY", "EXPECTED_REQUEST", "HARD_BAN", "POSITIVE_DECISION",
    "REASON_CODES", "RECORD_FIELDS", "RECORD_FIELD_CATALOG_HASH",
    "REQUEST_FIELDS", "REQUEST_FIELD_CATALOG_HASH",
    "evaluate_si003_performance_scalarization_authority_boundary",
]
