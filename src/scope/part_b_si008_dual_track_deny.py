"""Deterministic PB-SI-008 Part B / experiment dual-track gate.

This module classifies caller-supplied references without dereferencing
them. It neither invokes an LLM nor inspects experiment artifacts. Its DENY
decision applies only to attempted promotion into the Part B evidence,
claim, authority or pass-condition track.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
)


PART_B_STATUS = "OUTSIDE_AUTHORIZED_TRACK_DENY"
EXPERIMENT_TRACK_STATUS = "MAY_PROCEED_UNDER_SEPARATE_AUTHORITY"
PB_SI_008_STATUS = "NOT_OPENED"
EXPERIMENT_TRACK_DECISION = (
    "NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED"
)

REQUEST_FIELDS = frozenset(
    {
        "request_id",
        "request_kind",
        "promotion_target",
        "reference_kind",
    }
)
PROMOTION_TARGETS = frozenset(
    {"EVIDENCE", "CLAIM", "AUTHORITY", "PASS_CONDITION"}
)
REFERENCE_KINDS = frozenset(
    {
        "ABSTRACT_EXPERIMENT_REFERENCE",
        "LLM_OUTPUT_REFERENCE",
        "EXPERIMENT_PATH_REFERENCE",
    }
)

AUTHORITY_BOUNDARY = {
    "part_b_evidence_authority": False,
    "part_b_claim_authority": False,
    "part_b_authority_grant": False,
    "part_b_pass_condition_authority": False,
    "llm_execution_authority": False,
    "experiment_artifact_access_authority": False,
}

ADJACENT_GATES = {
    "holdout_release": "DENY",
    "pb_si_006_download": "DENY",
    "pb_b5_execution": "NOT_ESTABLISHED",
    "pb_b8_si_004": "OPEN",
    "stop_authority": "NONE",
}


def _normalized_request(
    request: Mapping[str, Any],
) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for field in (
        "request_id",
        "request_kind",
        "promotion_target",
        "reference_kind",
    ):
        value = request.get(field)
        normalized[field] = value if isinstance(value, str) else "__INVALID__"
    return normalized


def _record(
    request: Mapping[str, Any],
    *,
    part_b_decision: str,
    reason_code: str,
) -> dict[str, object]:
    normalized = _normalized_request(request)
    identity = {
        "request": normalized,
        "part_b_decision": part_b_decision,
        "reason_code": reason_code,
        "part_b_status": PART_B_STATUS,
        "experiment_track_status": EXPERIMENT_TRACK_STATUS,
        "pb_si_008_status": PB_SI_008_STATUS,
    }
    record: dict[str, object] = {
        "schema_version": "0.8.0",
        "record_id": canonical_value_hash(identity),
        "record_version": "0.8.0",
        "request": normalized,
        "part_b_status": PART_B_STATUS,
        "experiment_track_status": EXPERIMENT_TRACK_STATUS,
        "pb_si_008_status": PB_SI_008_STATUS,
        "part_b_decision": part_b_decision,
        "experiment_track_decision": EXPERIMENT_TRACK_DECISION,
        "reason_code": reason_code,
        "experiment_artifact_accessed": False,
        "llm_invoked": False,
        **ADJACENT_GATES,
        **AUTHORITY_BOUNDARY,
    }
    record["record_hash"] = canonical_value_hash(record)
    record["hash"] = canonical_document_hash(record)
    return record


def evaluate_dual_track_request(
    request: Mapping[str, Any],
) -> dict[str, object]:
    """Classify one request without touching either external track.

    An experiment-only notice is outside Part B admission and receives a
    non-interference record. An attempted elevation into Part B is denied.
    Invalid or widened requests fail closed while the independent experiment
    track remains unevaluated and subject to its own authority.
    """

    if not isinstance(request, Mapping):
        return _record(
            {},
            part_b_decision="DENY",
            reason_code="SI008-DUAL-002_REQUEST_INVALID",
        )

    if set(request) - REQUEST_FIELDS:
        return _record(
            request,
            part_b_decision="DENY",
            reason_code="SI008-DUAL-003_UNKNOWN_FIELD",
        )

    if set(request) != REQUEST_FIELDS or any(
        not isinstance(request.get(field), str)
        or not request.get(field)
        for field in REQUEST_FIELDS
    ):
        return _record(
            request,
            part_b_decision="DENY",
            reason_code="SI008-DUAL-002_REQUEST_INVALID",
        )

    request_kind = request["request_kind"]
    promotion_target = request["promotion_target"]
    reference_kind = request["reference_kind"]
    if reference_kind not in REFERENCE_KINDS:
        return _record(
            request,
            part_b_decision="DENY",
            reason_code="SI008-DUAL-002_REQUEST_INVALID",
        )

    if (
        request_kind == "EXPERIMENT_TRACK_ONLY"
        and promotion_target == "NONE"
        and reference_kind == "ABSTRACT_EXPERIMENT_REFERENCE"
    ):
        return _record(
            request,
            part_b_decision="NO_PART_B_ADMISSION_REQUEST",
            reason_code="SI008-DUAL-000_NO_PART_B_ADMISSION_REQUEST",
        )

    if (
        request_kind == "PROMOTE_TO_PART_B"
        and promotion_target in PROMOTION_TARGETS
    ):
        return _record(
            request,
            part_b_decision="DENY",
            reason_code="SI008-DUAL-001_PART_B_ELEVATION_DENIED",
        )

    return _record(
        request,
        part_b_decision="DENY",
        reason_code="SI008-DUAL-002_REQUEST_INVALID",
    )


__all__ = [
    "EXPERIMENT_TRACK_STATUS",
    "PART_B_STATUS",
    "PB_SI_008_STATUS",
    "evaluate_dual_track_request",
]
