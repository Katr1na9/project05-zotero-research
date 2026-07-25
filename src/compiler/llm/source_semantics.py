"""Trusted-source semantics for candidate-only Claim IR projections."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from .exceptions import CandidateOnlyViolationError


MODALITIES = frozenset(
    {"observed", "derived", "reported", "hypothesized", "unknown"}
)
EPISTEMIC_ROLES = frozenset(
    {
        "case_evidence",
        "mechanism_knowledge",
        "background_intelligence",
        "model_hypothesis",
        "analyst_hypothesis",
        "unknown",
    }
)
TRUTH_STATUSES = frozenset(
    {"unassessed", "supported", "contradicted", "conflicted", "retracted"}
)

_DEFAULTS = {
    "epistemic_role": "unknown",
    "truth_status": "unassessed",
}


def preserve_trusted_source_semantics(
    candidate: Mapping[str, Any],
    trusted_source_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Copy trusted semantics into a candidate, rejecting any disagreement."""

    if not isinstance(candidate, Mapping):
        raise TypeError("candidate must be a mapping")
    if not isinstance(trusted_source_metadata, Mapping):
        raise TypeError("trusted_source_metadata must be a mapping")
    if "modality" not in trusted_source_metadata:
        raise ValueError("trusted_source_metadata must contain modality")
    _require_candidate_only_controls(candidate)

    trusted = {
        "modality": _require_member(
            trusted_source_metadata["modality"], MODALITIES, "modality"
        ),
        "epistemic_role": _require_member(
            trusted_source_metadata.get(
                "epistemic_role", _DEFAULTS["epistemic_role"]
            ),
            EPISTEMIC_ROLES,
            "epistemic_role",
        ),
        "truth_status": _require_member(
            trusted_source_metadata.get("truth_status", _DEFAULTS["truth_status"]),
            TRUTH_STATUSES,
            "truth_status",
        ),
    }

    result = copy.deepcopy(dict(candidate))
    for field, trusted_value in trusted.items():
        if field in result and result[field] != trusted_value:
            raise CandidateOnlyViolationError(
                f"candidate {field} disagrees with trusted source metadata"
            )
        result[field] = copy.deepcopy(trusted_value)
    return result


def _require_candidate_only_controls(candidate: Mapping[str, Any]) -> None:
    authority = candidate.get("certification_authority")
    if (
        candidate.get("admission_status") != "candidate"
        or candidate.get("promotion_status") != "none"
        or not isinstance(authority, Mapping)
        or set(authority) != {"allowed", "levels"}
        or authority.get("allowed") is not False
        or not isinstance(authority.get("levels"), list)
        or authority["levels"]
    ):
        raise CandidateOnlyViolationError(
            "source semantics require candidate-only authority and admission controls"
        )


def _require_member(value: Any, allowed: frozenset[str], field: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"trusted {field} is not a canonical value")
    return value
