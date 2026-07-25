"""Deterministic Part B claims and CERTIFIED_STOP DENY gate.

The classifier consumes only a caller-supplied in-memory mapping. It neither
evaluates empirical performance nor invokes any execution, data, experiment,
certificate, system-state or Part A Kernel path.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
)


SLICE_STATUS = "CLAIMS_STOP_DENY_GATE_ONLY"
CLAIM_CEILING_REMAINDER = "CONTRACT_CONSISTENCY_ONLY"
CERTIFIED_STOP_STATUS = "NOT_AUTHORIZED"

REQUEST_FIELDS = frozenset(
    {
        "request_id",
        "request_kind",
        "promotion_target",
        "basis_kind",
    }
)
ELEVATION_TARGETS = frozenset(
    {
        "SCALARIZED_RANKING",
        "PERFORMANCE_SUPERIORITY",
        "CERTIFICATE_ISSUED",
        "CERTIFIED_STOP",
    }
)
BASIS_KINDS = frozenset(
    {
        "CONTRACT_ONLY",
        "B2_SAMPLER_STUB",
        "B3_CAPTURE_FIXTURE",
        "B5_ADMISSION_RECORD",
    }
)

FROZEN_BOUNDARY = {
    "slice_status": SLICE_STATUS,
    "claim_ceiling_remainder": CLAIM_CEILING_REMAINDER,
    "scalarization_authority": False,
    "scalarization_decision": "DENY",
    "performance_superiority_authority": False,
    "performance_superiority_decision": "DENY",
    "stop_authority": "NONE",
    "certified_stop": CERTIFIED_STOP_STATUS,
    "holdout_release": "DENY",
    "pb_si_006_download": "DENY",
    "pb_si_008": "NOT_OPENED",
    "pb_b5_execution": "NOT_ESTABLISHED",
}

NO_EMISSION_BOUNDARY = {
    "basis_accepted_for_stop": False,
    "certificate_issued": False,
    "scalarization_applied": False,
    "superiority_claim_issued": False,
    "network_io": False,
    "llm_invoked": False,
    "holdout_artifact_accessed": False,
    "part_a_kernel_gamma_changed": False,
    "part_a_certified_stop_semantics_changed": False,
    "kernel_stop_path_invoked": False,
}


def _normalized_request(
    request: Mapping[str, Any],
) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for field in (
        "request_id",
        "request_kind",
        "promotion_target",
        "basis_kind",
    ):
        value = request.get(field)
        normalized[field] = value if isinstance(value, str) else "__INVALID__"
    return normalized


def _record(
    request: Mapping[str, Any],
    *,
    decision: str,
    reason_code: str,
) -> dict[str, object]:
    normalized = _normalized_request(request)
    identity = {
        "request": normalized,
        "decision": decision,
        "reason_code": reason_code,
        "slice_status": SLICE_STATUS,
        "claim_ceiling_remainder": CLAIM_CEILING_REMAINDER,
    }
    record: dict[str, object] = {
        "schema_version": "0.8.0",
        "record_id": canonical_value_hash(identity),
        "record_version": "0.8.0",
        "request": normalized,
        "decision": decision,
        "reason_code": reason_code,
        **FROZEN_BOUNDARY,
        **NO_EMISSION_BOUNDARY,
    }
    record["record_hash"] = canonical_value_hash(record)
    record["hash"] = canonical_document_hash(record)
    return record


def evaluate_claim_authority_request(
    request: Mapping[str, Any],
) -> dict[str, object]:
    """Return a deterministic fail-closed record for one local request."""

    if not isinstance(request, Mapping):
        return _record(
            {},
            decision="DENY",
            reason_code="CLAIMS-STOP-002_REQUEST_INVALID",
        )

    if set(request) - REQUEST_FIELDS:
        return _record(
            request,
            decision="DENY",
            reason_code="CLAIMS-STOP-003_UNKNOWN_FIELD",
        )

    if set(request) != REQUEST_FIELDS or any(
        not isinstance(request.get(field), str)
        or not request.get(field)
        for field in REQUEST_FIELDS
    ):
        return _record(
            request,
            decision="DENY",
            reason_code="CLAIMS-STOP-002_REQUEST_INVALID",
        )

    request_kind = request["request_kind"]
    promotion_target = request["promotion_target"]
    basis_kind = request["basis_kind"]

    if (
        request_kind == "CONTRACT_CONSISTENCY_CHECK"
        and promotion_target == "NONE"
        and basis_kind == "CONTRACT_ONLY"
    ):
        return _record(
            request,
            decision="NO_CLAIM_OR_STOP_AUTHORIZATION_REQUEST",
            reason_code="CLAIMS-STOP-000_NO_ELEVATION_REQUEST",
        )

    if (
        request_kind == "PROMOTE_CLAIM_AUTHORITY"
        and promotion_target in ELEVATION_TARGETS
        and basis_kind in BASIS_KINDS
    ):
        return _record(
            request,
            decision="DENY",
            reason_code="CLAIMS-STOP-001_ELEVATION_DENIED",
        )

    return _record(
        request,
        decision="DENY",
        reason_code="CLAIMS-STOP-002_REQUEST_INVALID",
    )


__all__ = [
    "CERTIFIED_STOP_STATUS",
    "CLAIM_CEILING_REMAINDER",
    "SLICE_STATUS",
    "evaluate_claim_authority_request",
]
