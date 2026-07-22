"""Guards that keep semantic proposals within the candidate-only boundary."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from .exceptions import CandidateOnlyViolationError


MODEL_CONTROLLED_FIELDS = frozenset(
    {
        "admission_status",
        "certification_authority",
        "promotion_status",
        "binding_status",
        "lifecycle_state",
    }
)
PRODUCER_POINTER_STATES = frozenset({"unbound", "ambiguous"})
ALLOWED_RAW_PROPOSAL_FIELDS = frozenset(
    {"candidate_id", "claim", "pointer_suggestion"}
)
FORBIDDEN_CONTROL_FIELD_PREFIXES = (
    "e_case",
    "checker",
    "gamma",
    "action_catalog",
    "absence_semantics",
)
FORBIDDEN_CONTROL_FIELD_NAMES = frozenset(
    {
        "certify",
        "certified",
        "decision",
        "operation",
        "promote",
        "revoke",
        "sat",
        "stop",
        "unresolvable",
        "unsat",
    }
)


def reject_model_controlled_fields(proposal: Mapping[str, Any]) -> None:
    """Reject model-supplied authority, lifecycle, and modality controls."""

    _reject_unknown_top_level_fields(proposal)
    _reject_control_fields(proposal, ())


def materialize_pointer_suggestion(proposal: Mapping[str, Any]) -> dict[str, Any]:
    """Return a non-binding pointer suggestion limited to producer states."""

    suggestion = proposal.get("pointer_suggestion")
    if suggestion is None:
        return {"status": "unbound"}
    if not isinstance(suggestion, Mapping):
        raise CandidateOnlyViolationError("pointer_suggestion must be a mapping")

    materialized = copy.deepcopy(dict(suggestion))
    status = materialized.get("status", "unbound")
    if status not in PRODUCER_POINTER_STATES:
        raise CandidateOnlyViolationError(
            f"pointer_suggestion status {status!r} is not a producer state"
        )
    materialized["status"] = status
    return materialized


def _reject_control_fields(value: Any, path: tuple[str, ...]) -> None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            field_path = ".".join((*path, str(key)))
            normalized_key = _normalized_control_token(key)
            if normalized_key in MODEL_CONTROLLED_FIELDS:
                raise CandidateOnlyViolationError(
                    f"model proposal contains controlled field {field_path}"
                )
            if normalized_key == "modality":
                raise CandidateOnlyViolationError(
                    f"model proposal contains modality override at {field_path}"
                )
            if (
                normalized_key in FORBIDDEN_CONTROL_FIELD_NAMES
                or normalized_key.startswith(FORBIDDEN_CONTROL_FIELD_PREFIXES)
            ):
                raise CandidateOnlyViolationError(
                    f"model proposal contains forbidden control field {field_path}"
                )
            _reject_control_fields(nested_value, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested_value in enumerate(value):
            _reject_control_fields(nested_value, (*path, str(index)))


def _reject_unknown_top_level_fields(proposal: Mapping[str, Any]) -> None:
    for key in proposal:
        if key not in ALLOWED_RAW_PROPOSAL_FIELDS:
            raise CandidateOnlyViolationError(
                f"model proposal contains unknown top-level field {key}"
            )


def _normalized_control_token(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")
