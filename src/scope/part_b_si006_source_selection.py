"""Deterministic, local-only PB-SI-006 source-selection evaluation.

This module evaluates a caller-supplied abstract source-selection candidate.
It deliberately has no data-plane dependencies: no network, credentials,
retrieval, connector execution, holdout access, planner authority or STOP
authority are available here.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping

from src.ir.canonical_hash import canonical_value_hash


FROZEN_ADAPTER_CONFORMANCE_HASH = (
    "sha256:f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a"
)
RUNTIME_MODULE_STATUS = "SELECTION_CONTRACT_ONLY_DOWNLOAD_DENY"

REQUIRED_FIELDS = frozenset(
    {
        "selection_id",
        "source_pointer",
        "source_status",
        "source_authorization",
        "modality",
        "truth_status",
        "epistemic_role",
        "certification_authority",
        "world_semantics",
        "adapter_conformance",
        "requested_authorities",
    }
)

ALLOWED_FIELDS = REQUIRED_FIELDS
AUTHORITY_FIELDS = (
    "source_authorization",
    "retrieval",
    "download",
    "credential_use",
    "connector_execution",
    "holdout_release",
    "certified_stop",
)
ABSTRACT_ID = re.compile(r"^abstract-[a-z0-9-]+$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def _authority_boundary() -> dict[str, object]:
    return {
        "source_selection_contract_authority": True,
        "local_selection_evaluation_authority": True,
        "source_authorization_authority": False,
        "retrieval_authority": False,
        "download_authority": False,
        "credential_use_authority": False,
        "connector_execution_authority": False,
        "planner_execution_authority": False,
        "holdout_release": "DENY",
        "stop_authority": "NONE",
    }


def _stable_hash(result: Mapping[str, object]) -> str:
    payload = dict(result)
    payload.pop("selection_record_hash", None)
    return canonical_value_hash(payload)


def _result(
    candidate: Mapping[str, object],
    *,
    decision: str,
    reason_code: str,
) -> dict[str, object]:
    source_pointer = candidate.get("source_pointer")
    world_semantics = candidate.get("world_semantics")
    result: dict[str, object] = {
        "selection_id": candidate.get("selection_id"),
        "decision": decision,
        "reason_code": reason_code,
        "source_status": candidate.get("source_status"),
        "source_authorization": "NOT_AUTHORIZED",
        "source_pointer": deepcopy(source_pointer),
        "modality": candidate.get("modality"),
        "truth_status": candidate.get("truth_status"),
        "epistemic_role": candidate.get("epistemic_role"),
        "certification_authority": deepcopy(
            candidate.get("certification_authority")
        ),
        "world_semantics": deepcopy(world_semantics),
        "adapter_conformance": deepcopy(
            candidate.get("adapter_conformance")
        ),
        "authority_boundary": _authority_boundary(),
    }
    result["selection_record_hash"] = _stable_hash(result)
    return result


def _deny(
    candidate: Mapping[str, object],
    reason_code: str,
) -> dict[str, object]:
    return _result(candidate, decision="DENY", reason_code=reason_code)


def _valid_pointer(pointer: object) -> bool:
    if not isinstance(pointer, Mapping):
        return False
    required = {"source_id", "record_id", "content_hash", "range", "range_semantics"}
    if set(pointer) != required:
        return False
    source_id = pointer["source_id"]
    record_id = pointer["record_id"]
    if (
        not isinstance(source_id, str)
        or not source_id
        or not isinstance(record_id, str)
        or not record_id
    ):
        return False
    if not isinstance(pointer["content_hash"], str) or not SHA256.fullmatch(
        pointer["content_hash"]
    ):
        return False
    span = pointer["range"]
    if not isinstance(span, Mapping) or set(span) != {
        "kind",
        "start",
        "end",
        "end_semantics",
    }:
        return False
    if span["kind"] not in {"ROWS", "BYTES"}:
        return False
    if (
        not isinstance(span["start"], int)
        or isinstance(span["start"], bool)
        or span["start"] < 0
        or not isinstance(span["end"], int)
        or isinstance(span["end"], bool)
        or span["end"] <= span["start"]
        or span["end_semantics"] != "EXCLUSIVE"
    ):
        return False
    return pointer["range_semantics"] == f"{span['kind']}_HALF_OPEN"


def _valid_world_semantics(world: object) -> bool:
    if not isinstance(world, Mapping) or set(world) != {
        "mode",
        "zero_hit_semantics",
        "completeness_attestation",
    }:
        return False
    mode = world["mode"]
    if mode == "OPEN_WORLD":
        return (
            world["zero_hit_semantics"] == "UNKNOWN_NOT_ABSENCE"
            and world["completeness_attestation"] is None
        )
    if mode == "CLOSED_BOUNDED":
        return (
            world["zero_hit_semantics"]
            == "ABSENCE_ONLY_WITH_COMPLETE_ATTESTATION"
            and world["completeness_attestation"] is not None
        )
    return False


def _valid_conformance(conformance: object) -> bool:
    return (
        isinstance(conformance, Mapping)
        and set(conformance)
        == {
            "contract_id",
            "contract_hash",
            "decision",
            "pointer_ownership_transferred",
        }
        and conformance["contract_id"] == "part-b-adapter-conformance-v0.8"
        and conformance["contract_hash"] == FROZEN_ADAPTER_CONFORMANCE_HASH
        and conformance["decision"] == "CONFORMANT"
        and conformance["pointer_ownership_transferred"] is False
    )


def _valid_certification_authority(authority: object) -> bool:
    return (
        isinstance(authority, Mapping)
        and set(authority)
        == {"allowed", "levels", "basis_rule_id", "policy_hash"}
        and authority["allowed"] is False
        and authority["levels"] == []
        and authority["basis_rule_id"] is None
        and authority["policy_hash"] is None
    )


def evaluate_source_selection(
    candidate: Mapping[str, Any],
) -> dict[str, object]:
    """Return a deterministic selection-only decision for one candidate.

    The only positive result is ``SELECTED_CONTRACT_ONLY`` for an abstract,
    non-authorized, B1-conformant candidate. Every malformed or authority-
    requesting input is denied with a stable reason code.
    """

    if not isinstance(candidate, Mapping):
        return _deny({}, "SI006-SELECTION-001_MISSING_REQUIRED_FIELD")

    unknown = set(candidate) - ALLOWED_FIELDS
    if unknown:
        return _deny(candidate, "SI006-SELECTION-002_UNKNOWN_FIELD")

    missing = REQUIRED_FIELDS - set(candidate)
    if missing:
        return _deny(candidate, "SI006-SELECTION-001_MISSING_REQUIRED_FIELD")

    requested = candidate["requested_authorities"]
    if (
        not isinstance(requested, Mapping)
        or set(requested) != set(AUTHORITY_FIELDS)
        or any(requested[field] is not False for field in AUTHORITY_FIELDS)
    ):
        return _deny(
            candidate, "SI006-SELECTION-007_AUTHORITY_REQUEST_FORBIDDEN"
        )

    if not _valid_pointer(candidate["source_pointer"]):
        return _deny(candidate, "SI006-SELECTION-003_POINTER_INVALID")

    if not _valid_conformance(candidate["adapter_conformance"]):
        return _deny(
            candidate, "SI006-SELECTION-004_ADAPTER_CONFORMANCE_INVALID"
        )

    source_id = candidate["source_pointer"]["source_id"]
    if (
        not isinstance(source_id, str)
        or not ABSTRACT_ID.fullmatch(source_id)
        or "http://" in source_id.lower()
        or "https://" in source_id.lower()
        or candidate["source_status"]
        != "ABSTRACT_CONTRACT_FIXTURE_NOT_AUTHORIZED"
        or candidate["source_authorization"] != "NOT_AUTHORIZED"
    ):
        return _deny(candidate, "SI006-SELECTION-005_SOURCE_NOT_ABSTRACT")

    if not _valid_certification_authority(
        candidate["certification_authority"]
    ):
        return _deny(
            candidate, "SI006-SELECTION-007_AUTHORITY_REQUEST_FORBIDDEN"
        )

    if not _valid_world_semantics(candidate["world_semantics"]):
        return _deny(
            candidate, "SI006-SELECTION-006_WORLD_SEMANTICS_INVALID"
        )

    return _result(
        candidate,
        decision="SELECTED_CONTRACT_ONLY",
        reason_code="SI006-SELECTION-000_CONTRACT_ONLY",
    )


__all__ = [
    "FROZEN_ADAPTER_CONFORMANCE_HASH",
    "RUNTIME_MODULE_STATUS",
    "evaluate_source_selection",
]
