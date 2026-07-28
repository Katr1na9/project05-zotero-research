"""Pure SI-002 evaluation-authority-flip prerequisite-gap catalog validator.

The module recognizes one exact, already accepted D1/SI-002 record chain and
returns a deterministic record describing five prerequisites that remain
missing.  It does not invoke a Planner, Twin, SI-002 runtime, runner,
evaluator, process, meter, registry, or write path.  Catalog validity is not
prerequisite satisfaction and never flips execution authority.
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

IMPLEMENTATION_ID = (
    "part_b_b5_m3_kernel_d1_twin_readonly_conformance_v0.1"
)
LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"
IMPLEMENTATION_IDENTITY_HASH = (
    "sha256:25e89d3eef7f13f5b65b839b06895b7"
    "c498753dcf4c955aa4d6c375235a0246d"
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
SI002_BOUNDARY_ACCEPTANCE_CONTENT_SHA256 = (
    "faf1df2bdd62352690cf9b7871d3c618"
    "d99c36ec84d29425c788a740d9226b8b"
)

REQUEST_KIND = (
    "ASSESS_SI002_EVALUATION_EXECUTION_AUTHORITY_"
    "FLIP_PREREQUISITE_GAP"
)
REQUESTED_SCOPE = (
    "LOCAL_EVALUATION_EXECUTION_AUTHORITY_FLIP_PREREQUISITE_"
    "GAP_CONTRACT_OR_RECORD_ONLY"
)
RECORD_CLASS = (
    "LOCAL_EVALUATION_EXECUTION_AUTHORITY_FLIP_PREREQUISITE_"
    "GAP_CATALOG_RECORD"
)
RECORD_SCOPE = REQUESTED_SCOPE
AUTHORITY_EFFECT = "NONE_GAP_CATALOG_RECORD_ONLY"
SI003_STATE = "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION"

CATALOG_ID = (
    "part-b-b5-si002-evaluation-execution-authority-flip-"
    "prerequisite-gap-catalog-v0.1"
)
PREREQUISITE_CATALOG = (
    {
        "prerequisite_id": "EXPLICIT_LATER_OWNER_FLIP_GO",
        "class": "AUTHORITY",
        "current_status": "MISSING",
        "satisfaction_rule": (
            "Requires a later separate Kernel Owner authorization artifact "
            "whose exact cell explicitly permits "
            "evaluation_execution_authority=true; a request field or "
            "catalog claim cannot self-satisfy it."
        ),
    },
    {
        "prerequisite_id": (
            "ACCEPTED_EVALUATOR_EXECUTION_CAPABILITY_IDENTITY"
        ),
        "class": "CAPABILITY_IDENTITY",
        "current_status": "MISSING",
        "satisfaction_rule": (
            "Requires a separately reviewed and accepted closed-world "
            "evaluator capability identity with exact implementation and "
            "dependency hashes, no wildcard, and no fallback."
        ),
    },
    {
        "prerequisite_id": (
            "ACCEPTED_HASH_BOUND_EVALUATOR_EXECUTION_EVIDENCE_OR_RECORD"
        ),
        "class": "EVIDENCE_RECORD",
        "current_status": "MISSING",
        "satisfaction_rule": (
            "Requires a separately accepted local hash-bound "
            "evaluator-execution evidence or record contract; the existing "
            "test-only runner-invocation record is not a substitute."
        ),
    },
    {
        "prerequisite_id": "ACTUAL_EVALUATOR_INVOCATION_EVIDENCE",
        "class": "OBSERVATION",
        "current_status": "MISSING",
        "satisfaction_rule": (
            "Requires evidence that an accepted evaluator capability was "
            "actually invoked under the separately authorized bounded mode; "
            "current actual_evaluator_invocation=false cannot satisfy it."
        ),
    },
    {
        "prerequisite_id": (
            "CLOSED_WORLD_EVIDENCE_TO_AUTHORITY_DECISION_BINDING"
        ),
        "class": "DECISION_BINDING",
        "current_status": "MISSING",
        "satisfaction_rule": (
            "Requires a separately accepted fail-closed mapping from exact "
            "accepted evidence and Owner authority to an authority decision; "
            "evidence alone and Owner GO alone are each insufficient."
        ),
    },
)
MISSING_PREREQUISITE_IDS = tuple(
    entry["prerequisite_id"] for entry in PREREQUISITE_CATALOG
)
CATALOG_HASH = canonical_value_hash(list(PREREQUISITE_CATALOG))

POSITIVE_DECISION = (
    "LOCAL_EVALUATION_EXECUTION_AUTHORITY_FLIP_PREREQUISITE_"
    "GAP_CATALOG_VALID_NO_FLIP"
)
DENY_UNKNOWN = "DENY_UNKNOWN_IMPLEMENTATION"
DENY_LEGACY = "DENY_LEGACY_IMPLEMENTATION"
DENY_MISSING = "DENY_MISSING_CHAIN_BINDING"
DENY_MISMATCH = "DENY_HASH_MISMATCH"
DENY_CATALOG_SHAPE = "DENY_CATALOG_SHAPE_MISMATCH"
DENY_UNVERIFIED = "DENY_UNVERIFIED_PREREQUISITE_SATISFACTION"
DENY_SILENT_FLIP = "DENY_SILENT_AUTHORITY_FLIP"
DENY_AUTHORITY = "DENY_AUTHORITY_REQUEST"
DENY_NON_CONTRACT = "DENY_NON_CONTRACT_INPUT"
DENY_NON_SUBSTITUTE = "DENY_NON_SUBSTITUTE_NO_AUTHORITY_ELEVATION"
DENY_SI003_OPEN = "DENY_SI003_REMAINS_OPEN"

REASON_CODES = {
    POSITIVE_DECISION: "B5-SI002-FLIP-GAP-000-VALID-NO-FLIP",
    DENY_UNKNOWN: "B5-SI002-FLIP-GAP-DENY-UNKNOWN-ID",
    DENY_LEGACY: "B5-SI002-FLIP-GAP-DENY-LEGACY-ID",
    DENY_MISSING: "B5-SI002-FLIP-GAP-DENY-MISSING-BINDING",
    DENY_MISMATCH: "B5-SI002-FLIP-GAP-DENY-HASH-MISMATCH",
    DENY_CATALOG_SHAPE: "B5-SI002-FLIP-GAP-DENY-CATALOG-SHAPE",
    DENY_UNVERIFIED: "B5-SI002-FLIP-GAP-DENY-UNVERIFIED",
    DENY_SILENT_FLIP: "B5-SI002-FLIP-GAP-DENY-SILENT-FLIP",
    DENY_AUTHORITY: "B5-SI002-FLIP-GAP-DENY-AUTHORITY",
    DENY_NON_CONTRACT: "B5-SI002-FLIP-GAP-DENY-NON-CONTRACT",
    DENY_NON_SUBSTITUTE: "B5-SI002-FLIP-GAP-DENY-NON-SUBSTITUTE",
    DENY_SI003_OPEN: "B5-SI002-FLIP-GAP-DENY-SI003-OPEN",
}

REQUEST_FIELDS = frozenset(
    {
        "schema_version",
        "request_kind",
        "request_version",
        "requested_scope",
        "implementation_id",
        "implementation_identity_hash",
        "si002_contract_record_hash",
        "si002_contract_record_content_sha256",
        "si002_invocation_record_hash",
        "si002_invocation_record_content_sha256",
        "si002_boundary_record_hash",
        "si002_boundary_record_content_sha256",
        "si002_boundary_acceptance_content_sha256",
        "owner_flip_go_status",
        "evaluator_capability_identity_status",
        "evaluator_execution_evidence_status",
        "actual_evaluator_invocation_evidence_status",
        "evidence_to_authority_binding_status",
        "missing_prerequisite_count",
        "actual_runner_invocation_record_fact",
        "actual_evaluator_invocation",
        "evaluation_execution_authority",
        "planner_execution_authority",
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
        "si002_contract_record_hash",
        "si002_invocation_record_hash",
        "si002_boundary_record_hash",
        "decision",
        "reason_codes",
        "record_scope",
        "authority_effect",
        "missing_prerequisite_count",
        "missing_prerequisite_ids",
        "prerequisites_satisfied",
        "actual_runner_invocation_record_fact",
        "actual_evaluator_invocation",
        "evaluation_execution_authority",
        "planner_execution_authority",
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
        "si002_boundary_acceptance_content_sha256",
    }
)

AUTHORITY_REQUEST_FIELDS = frozenset(
    {
        "evaluator_execution_requested",
        "runner_execution_requested",
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
        "prerequisites_satisfied",
        "authority_flip_eligible",
        "path_b_write",
        "mint",
        "kernel_or_e_case_write",
        "certificate",
        "CERTIFIED_STOP",
        "stop_requested",
        "system_state",
    }
)

EXACT_CHAIN_VALUES = {
    "implementation_identity_hash": IMPLEMENTATION_IDENTITY_HASH,
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
    "si002_boundary_acceptance_content_sha256": (
        SI002_BOUNDARY_ACCEPTANCE_CONTENT_SHA256
    ),
}

EXACT_CATALOG_STATUS_VALUES = {
    "owner_flip_go_status": "MISSING",
    "evaluator_capability_identity_status": "MISSING",
    "evaluator_execution_evidence_status": "MISSING",
    "actual_evaluator_invocation_evidence_status": "MISSING",
    "evidence_to_authority_binding_status": "MISSING",
}

EXACT_ENVELOPE_VALUES = {
    "schema_version": "0.8.0",
    "request_kind": REQUEST_KIND,
    "request_version": "0.1.0",
    "requested_scope": REQUESTED_SCOPE,
}

AUTHORITY_CEILING = {
    "record_scope": RECORD_SCOPE,
    "authority_effect": AUTHORITY_EFFECT,
    "missing_prerequisite_count": 5,
    "prerequisites_satisfied": False,
    "actual_runner_invocation_record_fact": True,
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

    if extra & SI003_REQUEST_FIELDS:
        return DENY_SI003_OPEN
    if extra & NON_SUBSTITUTE_REQUEST_FIELDS:
        return DENY_NON_SUBSTITUTE
    if extra & AUTHORITY_REQUEST_FIELDS:
        return DENY_AUTHORITY
    if extra:
        return DENY_NON_CONTRACT

    missing = REQUEST_FIELDS - keys
    if missing & CHAIN_BINDING_FIELDS:
        return DENY_MISSING
    if missing:
        return DENY_CATALOG_SHAPE

    implementation_id = request.get("implementation_id")
    if implementation_id == LEGACY_IMPLEMENTATION_ID:
        return DENY_LEGACY
    if implementation_id != IMPLEMENTATION_ID:
        return DENY_UNKNOWN

    if (
        request.get("actual_evaluator_invocation") is not False
        or request.get("evaluation_execution_authority") is not False
    ):
        return DENY_SILENT_FLIP
    if request.get("planner_execution_authority") is not False:
        return DENY_AUTHORITY

    if any(
        request.get(field) != expected
        for field, expected in EXACT_CHAIN_VALUES.items()
    ):
        return DENY_MISMATCH
    if request.get("actual_runner_invocation_record_fact") is not True:
        return DENY_MISMATCH

    if (
        request.get("actual_evaluator_invocation_evidence_status")
        != "MISSING"
    ):
        return DENY_SILENT_FLIP
    if any(
        request.get(field) != expected
        for field, expected in EXACT_CATALOG_STATUS_VALUES.items()
    ):
        return DENY_UNVERIFIED

    if (
        request.get("missing_prerequisite_count") != 5
        or any(
            request.get(field) != expected
            for field, expected in EXACT_ENVELOPE_VALUES.items()
        )
    ):
        return DENY_CATALOG_SHAPE
    if request.get("pb_b5_si_003_state") != SI003_STATE:
        return DENY_SI003_OPEN

    return POSITIVE_DECISION


def evaluate_si002_evaluation_execution_authority_flip_prerequisite_gap_catalog(
    catalog_request: Mapping[str, object],
) -> dict[str, object]:
    """Return a deterministic missing-prerequisite record with no flip."""

    if not isinstance(catalog_request, Mapping):
        raise ValueError("catalog_request must be a mapping")

    decision = _select_decision(catalog_request)
    record = {
        "schema_version": "0.8.0",
        "record_class": RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": canonical_value_hash(catalog_request),
        "implementation_id": IMPLEMENTATION_ID,
        "si002_contract_record_hash": SI002_CONTRACT_RECORD_HASH,
        "si002_invocation_record_hash": SI002_INVOCATION_RECORD_HASH,
        "si002_boundary_record_hash": SI002_BOUNDARY_RECORD_HASH,
        "decision": decision,
        "reason_codes": [REASON_CODES[decision]],
        "record_scope": RECORD_SCOPE,
        "authority_effect": AUTHORITY_EFFECT,
        "missing_prerequisite_count": 5,
        "missing_prerequisite_ids": list(MISSING_PREREQUISITE_IDS),
        "prerequisites_satisfied": False,
        "actual_runner_invocation_record_fact": True,
        "actual_evaluator_invocation": False,
        "evaluation_execution_authority": False,
        "planner_execution_authority": False,
        "pb_b5_si_003_state": SI003_STATE,
        "stop_authority": "NONE",
    }
    record["hash"] = canonical_document_hash(record)
    return record


__all__ = [
    "ACTUAL_EVALUATOR_INVOCATION",
    "AUTHORITY_CEILING",
    "AUTHORITY_EFFECT",
    "CATALOG_HASH",
    "CATALOG_ID",
    "DENY_AUTHORITY",
    "DENY_CATALOG_SHAPE",
    "DENY_LEGACY",
    "DENY_MISMATCH",
    "DENY_MISSING",
    "DENY_NON_CONTRACT",
    "DENY_NON_SUBSTITUTE",
    "DENY_SI003_OPEN",
    "DENY_SILENT_FLIP",
    "DENY_UNKNOWN",
    "DENY_UNVERIFIED",
    "EVALUATION_EXECUTION_AUTHORITY",
    "HARD_BAN",
    "IMPLEMENTATION_ID",
    "IMPLEMENTATION_IDENTITY_HASH",
    "LEGACY_IMPLEMENTATION_ID",
    "MISSING_PREREQUISITE_IDS",
    "PLANNER_EXECUTION_AUTHORITY",
    "POSITIVE_DECISION",
    "PREREQUISITE_CATALOG",
    "PRODUCTION_REGISTRATION_ENABLED",
    "REASON_CODES",
    "RECORD_CLASS",
    "RECORD_FIELDS",
    "RECORD_SCOPE",
    "REQUEST_FIELDS",
    "REQUEST_KIND",
    "REQUESTED_SCOPE",
    "SI002_BOUNDARY_ACCEPTANCE_CONTENT_SHA256",
    "SI002_BOUNDARY_RECORD_CONTENT_SHA256",
    "SI002_BOUNDARY_RECORD_HASH",
    "SI002_CONTRACT_RECORD_CONTENT_SHA256",
    "SI002_CONTRACT_RECORD_HASH",
    "SI002_INVOCATION_RECORD_CONTENT_SHA256",
    "SI002_INVOCATION_RECORD_HASH",
    "SI003_STATE",
    "evaluate_si002_evaluation_execution_authority_flip_prerequisite_gap_catalog",
]
