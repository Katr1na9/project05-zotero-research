"""Additive PB-SI-008 gate for one named Path A CLAIM target.

Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or
unrestricted Part B elevation.

Legacy exact-four-field requests and existing exact EVIDENCE requests are
returned from the protected evidence gate without modification.  New CLAIM
requests are classified from their declarations only; package and structural
validation receipt references are never dereferenced.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
)
from src.scope.part_b_si008_dual_track_deny import (
    REQUEST_FIELDS as LEGACY_REQUEST_FIELDS,
)
from src.scope.part_b_si008_named_open_path_a_evidence_candidacy import (
    NAMED_REQUEST_FIELDS as EVIDENCE_NAMED_REQUEST_FIELDS,
    NAMED_TARGET_ID as EVIDENCE_NAMED_TARGET_ID,
    evaluate_si008_named_open_request,
)


PB_SI_008_STATUS = "OPENED_FOR_NAMED_TARGET_ONLY_EVIDENCE_AND_CLAIM"
PART_B_STATUS = (
    "NAMED_TARGET_CLAIM_CANDIDACY_ONLY_NO_MINT_NO_ADMISSION"
)
EXPERIMENT_TRACK_STATUS = "MAY_PROCEED_UNDER_SEPARATE_AUTHORITY"
EXPERIMENT_TRACK_DECISION = (
    "NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED"
)
NAMED_TARGET_ID = "PATH_A_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1"
ALLOW_DECISION = "ALLOW_NAMED_CLAIM_CANDIDACY_ONLY"
HARD_BAN = "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation."
PRODUCTION_REGISTRATION_ENABLED = False

NAMED_REQUEST_FIELDS = frozenset(
    {
        "request_id",
        "request_kind",
        "promotion_target",
        "reference_kind",
        "named_target_id",
        "source_schema_version",
        "source_schema_sha256",
        "consumer_contract_id",
        "consumer_contract_sha256",
        "package_sha256",
        "structural_validation_receipt_sha256",
        "record_class",
        "claim_id",
        "claim_id_state",
        "admission_state",
        "structural_validation_status",
        "requested_authority_scope",
        "reference_access_mode",
    }
)
_NAMED_REQUEST_FIELD_ORDER = (
    "request_id",
    "request_kind",
    "promotion_target",
    "reference_kind",
    "named_target_id",
    "source_schema_version",
    "source_schema_sha256",
    "consumer_contract_id",
    "consumer_contract_sha256",
    "package_sha256",
    "structural_validation_receipt_sha256",
    "record_class",
    "claim_id",
    "claim_id_state",
    "admission_state",
    "structural_validation_status",
    "requested_authority_scope",
    "reference_access_mode",
)
DENIED_PROMOTION_TARGETS = frozenset({"AUTHORITY", "PASS_CONDITION"})
CLAIM_REFERENCE_PAIRS = {
    "PATH_A_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE": {
        "source_schema_version": "claim-ir-external-evidence-v0.1",
        "source_schema_sha256": (
            "9abc23e2258298038e137dbbe38168867"
            "d07108fa27719aa68c1c2b752ae2a7c"
        ),
        "consumer_contract_id": (
            "shared-claim-ir-consumer-contract-evidence-candidate-"
            "effective-v0.2"
        ),
        "consumer_contract_sha256": (
            "fe5222b9b4e0ddaf990761b34bdfc500"
            "4f45f55d3e2155b09388fb9596a1e504"
        ),
    },
    "PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE": {
        "source_schema_version": "claim-ir-external-evidence-v0.2",
        "source_schema_sha256": (
            "e246c44b7513a5bc2f3410a2739a53bd"
            "1f40dad3e767036bb1af3158c9e02ac6"
        ),
        "consumer_contract_id": (
            "shared-claim-ir-consumer-contract-evidence-candidate-"
            "effective-v0.3"
        ),
        "consumer_contract_sha256": (
            "7662762d045381921b8f94a39753d0c4"
            "91322b3a41d473226cc5fe3f4688457c"
        ),
    },
}

_EXACT_CLAIM_VALUES = {
    "request_kind": "PROMOTE_TO_PART_B_NAMED_TARGET",
    "promotion_target": "CLAIM",
    "named_target_id": NAMED_TARGET_ID,
    "record_class": "public_evidence_declaration",
    "claim_id": None,
    "claim_id_state": "not_minted",
    "admission_state": "not_admitted",
    "structural_validation_status": (
        "PASS_STRUCTURAL_ONLY_NO_INGESTION_AUTHORITY"
    ),
    "requested_authority_scope": "CLAIM_STRUCTURAL_CANDIDACY_ONLY",
    "reference_access_mode": (
        "CLASSIFY_DECLARED_REFERENCE_ONLY_NO_DEREFERENCE"
    ),
}
_DIGEST_FIELDS = (
    "source_schema_sha256",
    "consumer_contract_sha256",
    "package_sha256",
    "structural_validation_receipt_sha256",
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

AUTHORITY_BOUNDARY = {
    "allow_is_mint": False,
    "allow_is_admission": False,
    "allow_is_part_b_pass": False,
    "allow_is_write_authority": False,
    "part_b_evidence_authority": False,
    "part_b_claim_authority": False,
    "part_b_authority_grant": False,
    "part_b_pass_condition_authority": False,
    "path_b_write_authority": False,
    "production_registration_authority": False,
    "mint_authority": False,
    "admission_authority": False,
    "kernel_or_e_case_write_authority": False,
    "certificate_authority": False,
    "named_claim_candidacy_classification_authority": False,
}
ADJACENT_GATES = {
    "holdout_release": "DENY",
    "pb_si_006_download": "DENY",
    "pb_b5_execution": "NOT_ESTABLISHED",
    "stop_authority": "NONE",
    "certified_stop": "NOT_AUTHORIZED",
}


def evaluate_si008_named_open_claim_request(
    request: Mapping[str, Any] | object,
) -> dict[str, object]:
    """Classify one legacy, EVIDENCE, or CLAIM request without I/O."""

    if isinstance(request, Mapping) and set(request) == LEGACY_REQUEST_FIELDS:
        return evaluate_si008_named_open_request(request)

    if (
        isinstance(request, Mapping)
        and set(request) == EVIDENCE_NAMED_REQUEST_FIELDS
        and request.get("promotion_target") == "EVIDENCE"
        and request.get("named_target_id") == EVIDENCE_NAMED_TARGET_ID
    ):
        return evaluate_si008_named_open_request(request)

    if not isinstance(request, Mapping):
        return _claim_record(
            {},
            decision="DENY",
            reason_code="SI008-NAMED-CLAIM-003_REQUEST_NOT_QUALIFIED",
            qualified=False,
        )

    if set(request) != NAMED_REQUEST_FIELDS:
        return _claim_record(
            request,
            decision="DENY",
            reason_code="SI008-NAMED-CLAIM-003_REQUEST_NOT_QUALIFIED",
            qualified=False,
        )

    if not _has_exact_claim_types(request):
        return _claim_record(
            request,
            decision="DENY",
            reason_code="SI008-NAMED-CLAIM-003_REQUEST_NOT_QUALIFIED",
            qualified=False,
        )

    if request["promotion_target"] in DENIED_PROMOTION_TARGETS:
        return _claim_record(
            request,
            decision="DENY",
            reason_code=(
                "SI008-NAMED-CLAIM-002_PROMOTION_TARGET_NOT_AUTHORIZED"
            ),
            qualified=False,
        )

    if not _qualifies_for_named_claim_candidacy(request):
        return _claim_record(
            request,
            decision="DENY",
            reason_code="SI008-NAMED-CLAIM-003_REQUEST_NOT_QUALIFIED",
            qualified=False,
        )

    return _claim_record(
        request,
        decision=ALLOW_DECISION,
        reason_code=(
            "SI008-NAMED-CLAIM-001_EXACT_TARGET_CLAIM_CANDIDACY"
        ),
        qualified=True,
    )


def _has_exact_claim_types(request: Mapping[str, Any]) -> bool:
    for field in NAMED_REQUEST_FIELDS - {"claim_id"}:
        value = request.get(field)
        if not isinstance(value, str) or not value:
            return False
    return request.get("claim_id") is None


def _qualifies_for_named_claim_candidacy(
    request: Mapping[str, Any],
) -> bool:
    for field, expected in _EXACT_CLAIM_VALUES.items():
        if request.get(field) != expected:
            return False
    if any(
        not _SHA256_PATTERN.fullmatch(str(request.get(field, "")))
        for field in _DIGEST_FIELDS
    ):
        return False
    pair = CLAIM_REFERENCE_PAIRS.get(str(request.get("reference_kind")))
    if pair is None:
        return False
    return all(
        request.get(field) == expected
        for field, expected in pair.items()
    )


def _normalized_claim_request(
    request: Mapping[str, Any],
) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for field in _NAMED_REQUEST_FIELD_ORDER:
        value = request.get(field)
        if field == "claim_id":
            normalized[field] = None if value is None else "__INVALID__"
        else:
            normalized[field] = (
                value if isinstance(value, str) else "__INVALID__"
            )
    return normalized


def _claim_record(
    request: Mapping[str, Any],
    *,
    decision: str,
    reason_code: str,
    qualified: bool,
) -> dict[str, object]:
    normalized = _normalized_claim_request(request)
    identity = {
        "request": normalized,
        "pb_si_008_status": PB_SI_008_STATUS,
        "part_b_status": PART_B_STATUS,
        "decision": decision,
        "reason_code": reason_code,
        "named_target_id": NAMED_TARGET_ID,
    }
    authority_boundary = dict(AUTHORITY_BOUNDARY)
    authority_boundary[
        "named_claim_candidacy_classification_authority"
    ] = qualified
    record: dict[str, object] = {
        "schema_version": "0.8.0",
        "record_id": canonical_value_hash(identity),
        "record_version": "0.8.0",
        "request": normalized,
        "pb_si_008_status": PB_SI_008_STATUS,
        "part_b_status": PART_B_STATUS,
        "experiment_track_status": EXPERIMENT_TRACK_STATUS,
        "decision": decision,
        "part_b_decision": decision,
        "experiment_track_decision": EXPERIMENT_TRACK_DECISION,
        "reason_code": reason_code,
        "named_target_id": NAMED_TARGET_ID,
        "allowed_promotion_targets": ["EVIDENCE", "CLAIM"],
        "allowed_promotion_target": "CLAIM",
        "reference_qualified": qualified,
        "package_dereferenced": False,
        "validation_receipt_dereferenced": False,
        "experiment_artifact_accessed": False,
        "llm_invoked": False,
        "hard_ban": HARD_BAN,
        **ADJACENT_GATES,
        **authority_boundary,
    }
    record["record_hash"] = canonical_value_hash(record)
    record["hash"] = canonical_document_hash(record)
    return record


__all__ = [
    "ALLOW_DECISION",
    "CLAIM_REFERENCE_PAIRS",
    "HARD_BAN",
    "NAMED_REQUEST_FIELDS",
    "NAMED_TARGET_ID",
    "PART_B_STATUS",
    "PB_SI_008_STATUS",
    "PRODUCTION_REGISTRATION_ENABLED",
    "evaluate_si008_named_open_claim_request",
]
