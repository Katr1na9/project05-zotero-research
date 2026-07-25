"""Deterministic local-only B8 holdout DENY-audit evaluation.

The module reads only frozen contract/configuration documents.  It never
opens a holdout payload, label, result, network endpoint, connector or
statistical runtime.  Every request produces a DENY record with a stable
reason code and reproducible hashes.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"

FROZEN_B8_PATHS = {
    "holdout_analysis_policy_hash": (
        CONFIG_DIR / "part-b-holdout-analysis-policy-v0.8.yaml"
    ),
    "holdout_preregistration_hash": (
        CONFIG_DIR / "part-b-holdout-preregistration-v0.8.yaml"
    ),
    "holdout_analysis_envelope_hash": (
        CONFIG_DIR / "part-b-holdout-analysis-envelope-example-v0.8.yaml"
    ),
    "b8_manifest_hash": CONFIG_DIR / "part-b-b8-manifest-v0.8.yaml",
}

FALLBACK_BINDINGS = {
    "holdout_analysis_policy_hash": (
        "sha256:542ed51380c7dc3e5ba1553d3c80b1a55e5ca5b008cb38d3df831fdee828b603"
    ),
    "holdout_preregistration_hash": (
        "sha256:6af52503f38ff70fc640d8e1313ce8d7f02cf6f79bf23f5cc2a8b3bf5ba38342"
    ),
    "holdout_analysis_envelope_hash": (
        "sha256:6126bd2145b1a05c91bf53aa81c599992a787d0dd6a43847f5a67f0bb07a07ed"
    ),
    "b8_manifest_hash": (
        "sha256:4e6e4ec552d3a9c20c8c68e76766205cb1b2ecdf6dfbfe95866085e0b56c593b"
    ),
}

REQUEST_FIELDS = frozenset(
    {"operation", "requested_decision", "case_id", "bindings"}
)
DENY_REASONS = {
    "release_holdout": "B8-DENY-001_RELEASE_NOT_AUTHORIZED",
    "read_holdout_labels": "B8-DENY-002_LABEL_ACCESS_DENIED",
    "read_holdout_results": "B8-DENY-003_RESULT_ACCESS_DENIED",
    "read_holdout_data": "B8-DENY-004_DATA_ACCESS_DENIED",
    "run_statistical_analysis": (
        "B8-DENY-005_STATISTICAL_EXECUTION_DENIED"
    ),
}

ACCESS_BOUNDARY = {
    "holdout_data_loaded": False,
    "holdout_labels_loaded": False,
    "holdout_results_loaded": False,
    "statistics_computed": False,
}

AUTHORITY_BOUNDARY = {
    "holdout_data_access_authority": False,
    "holdout_label_access_authority": False,
    "holdout_result_access_authority": False,
    "statistical_analysis_execution_authority": False,
    "release_authority": False,
    "performance_claim_authority": False,
    "stop_authority": "NONE",
}


def _read_frozen_bindings() -> dict[str, str]:
    """Replay the declared hashes of the four frozen B8 inputs."""

    bindings: dict[str, str] = {}
    for binding_name, path in FROZEN_B8_PATHS.items():
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        declared = document.get("hash")
        if declared != canonical_document_hash(document):
            raise ValueError(f"frozen B8 hash mismatch: {path.name}")
        bindings[binding_name] = declared
    return bindings


def _normalized_request(request: Mapping[str, Any]) -> dict[str, object]:
    operation = request.get("operation")
    normalized: dict[str, object] = {
        "operation": operation if isinstance(operation, str) else "__INVALID__",
        "requested_decision": request.get("requested_decision"),
    }
    case_id = request.get("case_id")
    if case_id is not None:
        normalized["case_id"] = (
            case_id if isinstance(case_id, str) else "__INVALID__"
        )
    return normalized


def _record(
    request: Mapping[str, Any],
    *,
    reason_code: str,
    bindings: Mapping[str, str],
) -> dict[str, object]:
    normalized = _normalized_request(request)
    identity = {
        "request": normalized,
        "decision": "DENY",
        "reason_code": reason_code,
        "bindings": dict(bindings),
    }
    record: dict[str, object] = {
        "schema_version": "0.8.0",
        "record_id": canonical_value_hash(identity),
        "record_version": "0.8.0",
        "request": normalized,
        "decision": "DENY",
        "reason_code": reason_code,
        "audit_scope": "HOLDOUT_DENY_AUDIT_ONLY",
        "release_decision": "DENY",
        "bindings": dict(bindings),
        "access_boundary": deepcopy(ACCESS_BOUNDARY),
        "authority_boundary": deepcopy(AUTHORITY_BOUNDARY),
        **deepcopy(AUTHORITY_BOUNDARY),
    }
    audit_payload = deepcopy(record)
    record["audit_hash"] = canonical_value_hash(audit_payload)
    record["hash"] = canonical_document_hash(record)
    return record


def evaluate_holdout_request(
    request: Mapping[str, Any],
) -> dict[str, object]:
    """Return one deterministic DENY-only audit record.

    No input can grant release, read labels/results/data, execute statistics,
    emit a claim, or change the frozen B8 bindings.
    """

    try:
        frozen_bindings = _read_frozen_bindings()
        binding_failure = False
    except (OSError, TypeError, ValueError, yaml.YAMLError):
        frozen_bindings = dict(FALLBACK_BINDINGS)
        binding_failure = True

    if not isinstance(request, Mapping):
        return _record(
            {},
            reason_code="B8-DENY-006_REQUEST_INVALID",
            bindings=frozen_bindings,
        )

    unknown = set(request) - REQUEST_FIELDS
    if unknown:
        return _record(
            request,
            reason_code="B8-DENY-007_UNKNOWN_FIELD",
            bindings=frozen_bindings,
        )

    supplied_bindings = request.get("bindings")
    if supplied_bindings is not None and (
        not isinstance(supplied_bindings, Mapping)
        or dict(supplied_bindings) != frozen_bindings
    ):
        return _record(
            request,
            reason_code="B8-DENY-008_BINDING_MISMATCH",
            bindings=frozen_bindings,
        )
    if binding_failure:
        return _record(
            request,
            reason_code="B8-DENY-008_BINDING_MISMATCH",
            bindings=frozen_bindings,
        )

    operation = request.get("operation")
    if not isinstance(operation, str) or not operation:
        return _record(
            request,
            reason_code="B8-DENY-006_REQUEST_INVALID",
            bindings=frozen_bindings,
        )

    reason_code = DENY_REASONS.get(
        operation,
        "B8-DENY-006_REQUEST_INVALID",
    )
    return _record(
        request,
        reason_code=reason_code,
        bindings=frozen_bindings,
    )


__all__ = ["evaluate_holdout_request"]
