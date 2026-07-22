"""Canonical local validation for candidate-only Claim IR projections."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar


Document = TypeVar("Document", bound=Mapping[str, Any])

_TOP_LEVEL_FIELDS = frozenset(
    {
        "candidate_id",
        "claim",
        "modality",
        "admission_status",
        "certification_authority",
        "promotion_status",
        "binding_status",
        "pointer_suggestion",
        "compatibility_status",
    }
)
_CLAIM_FIELDS = frozenset(
    {"subject", "predicate", "object", "polarity", "literal", "quote"}
)
_REQUIRED_CLAIM_FIELDS = frozenset({"subject", "predicate", "object"})
_MODALITIES = ("observed", "derived", "reported", "hypothesized", "unknown")

def _build_candidate_claim_ir_schema() -> dict[str, Any]:
    """Build the contract from immutable literals, never an exported schema dict."""

    def string_schema() -> dict[str, Any]:
        return {"type": "string", "minLength": 1}

    unbound_pointer: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["status"],
        "properties": {"status": {"const": "unbound"}},
    }
    ambiguous_pointer: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "candidates"],
        "properties": {
            "status": {"const": "ambiguous"},
            "candidates": {
                "type": "array",
                "items": string_schema(),
                "minItems": 2,
                "uniqueItems": True,
            },
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:project05:local:candidate-claim-ir:pending-kernel-schema",
        "title": "Local Candidate Claim IR Projection",
        "type": "object",
        "additionalProperties": False,
        "required": sorted(_TOP_LEVEL_FIELDS),
        "properties": {
            "candidate_id": string_schema(),
            "claim": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(_REQUIRED_CLAIM_FIELDS),
                "properties": {
                    "subject": string_schema(),
                    "predicate": string_schema(),
                    "object": string_schema(),
                    "polarity": {"type": "boolean"},
                    "literal": {"type": "string"},
                    "quote": {"type": "string"},
                },
            },
            "modality": {"type": "string", "enum": list(_MODALITIES)},
            "admission_status": {"const": "candidate"},
            "certification_authority": {
                "type": "object",
                "additionalProperties": False,
                "required": ["allowed", "levels"],
                "properties": {
                    "allowed": {"const": False},
                    "levels": {"type": "array", "maxItems": 0},
                },
            },
            "promotion_status": {"const": "none"},
            "binding_status": {"enum": ["unbound", "ambiguous"]},
            "pointer_suggestion": {
                "oneOf": [unbound_pointer, ambiguous_pointer]
            },
            "compatibility_status": {"const": "pending_kernel_schema"},
        },
        "allOf": [
            {
                "if": {
                    "properties": {"binding_status": {"const": "unbound"}},
                    "required": ["binding_status"],
                },
                "then": {"properties": {"pointer_suggestion": unbound_pointer}},
                "else": {
                    "properties": {"pointer_suggestion": ambiguous_pointer}
                },
            }
        ],
    }


CANDIDATE_CLAIM_IR_SCHEMA = _build_candidate_claim_ir_schema()

# Descriptive alias for callers that prefer an explicit canonical name.
CANONICAL_CANDIDATE_CLAIM_IR_SCHEMA = CANDIDATE_CLAIM_IR_SCHEMA


class CandidateClaimIRValidationError(ValueError):
    """Raised when a local candidate projection violates the canonical contract."""


def validate_candidate_claim_ir(document: Document) -> Document:
    """Fail closed on documents outside the local candidate-only projection."""

    if not isinstance(document, Mapping):
        raise CandidateClaimIRValidationError("candidate document must be an object")

    fields = set(document)
    unknown = fields - _TOP_LEVEL_FIELDS
    if unknown:
        raise CandidateClaimIRValidationError(
            f"unknown top-level field(s): {', '.join(sorted(map(str, unknown)))}"
        )
    missing = _TOP_LEVEL_FIELDS - fields
    if missing:
        raise CandidateClaimIRValidationError(
            f"missing required field(s): {', '.join(sorted(missing))}"
        )

    _require_nonempty_string(document["candidate_id"], "candidate_id")
    _validate_claim(document["claim"])
    _require_member(document["modality"], _MODALITIES, "modality")
    _require_constant(document["admission_status"], "candidate", "admission_status")
    _validate_authority(document["certification_authority"])
    _require_constant(document["promotion_status"], "none", "promotion_status")
    _require_constant(
        document["compatibility_status"],
        "pending_kernel_schema",
        "compatibility_status",
    )
    pointer_status = _validate_pointer_suggestion(document["pointer_suggestion"])
    _require_member(
        document["binding_status"], ("unbound", "ambiguous"), "binding_status"
    )
    if document["binding_status"] != pointer_status:
        raise CandidateClaimIRValidationError(
            "binding_status must equal pointer_suggestion.status"
        )
    return document


def _validate_claim(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise CandidateClaimIRValidationError("claim must be an object")
    fields = set(value)
    unknown = fields - _CLAIM_FIELDS
    if unknown:
        raise CandidateClaimIRValidationError(
            f"claim has unknown field(s): {', '.join(sorted(map(str, unknown)))}"
        )
    missing = _REQUIRED_CLAIM_FIELDS - fields
    if missing:
        raise CandidateClaimIRValidationError(
            f"claim missing required field(s): {', '.join(sorted(missing))}"
        )
    for field in ("subject", "predicate", "object"):
        _require_nonempty_string(value[field], f"claim.{field}")
    for field in ("literal", "quote"):
        if field in value and not isinstance(value[field], str):
            raise CandidateClaimIRValidationError(f"claim.{field} must be a string")
    if "polarity" in value and not isinstance(value["polarity"], bool):
        raise CandidateClaimIRValidationError("claim.polarity must be a boolean")


def _validate_authority(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise CandidateClaimIRValidationError(
            "certification_authority must be an object"
        )
    if set(value) != {"allowed", "levels"}:
        raise CandidateClaimIRValidationError(
            "certification_authority must contain only allowed and levels"
        )
    if (
        value["allowed"] is not False
        or not isinstance(value["levels"], list)
        or value["levels"]
    ):
        raise CandidateClaimIRValidationError(
            "certification_authority must equal {'allowed': false, 'levels': []}"
        )


def _validate_pointer_suggestion(value: Any) -> str:
    if not isinstance(value, Mapping):
        raise CandidateClaimIRValidationError("pointer_suggestion must be an object")
    status = value.get("status")
    if status == "unbound":
        if set(value) != {"status"}:
            raise CandidateClaimIRValidationError(
                "unbound pointer_suggestion must contain only status"
            )
        return status
    if status == "ambiguous":
        if set(value) != {"status", "candidates"}:
            raise CandidateClaimIRValidationError(
                "ambiguous pointer_suggestion requires only status and candidates"
            )
        candidates = value["candidates"]
        if (
            not isinstance(candidates, list)
            or len(candidates) < 2
            or any(
                not isinstance(candidate, str) or not candidate
                for candidate in candidates
            )
            or len(set(candidates)) != len(candidates)
        ):
            raise CandidateClaimIRValidationError(
                "ambiguous pointer_suggestion requires at least two unique "
                "non-empty string candidates"
            )
        return status
    raise CandidateClaimIRValidationError(
        "pointer_suggestion.status must be unbound or ambiguous"
    )


def _require_nonempty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise CandidateClaimIRValidationError(f"{field} must be a non-empty string")


def _require_constant(value: Any, expected: Any, field: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise CandidateClaimIRValidationError(f"{field} must equal {expected!r}")


def _require_member(value: Any, allowed: tuple[str, ...], field: str) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise CandidateClaimIRValidationError(
            f"{field} must be one of {', '.join(allowed)}"
        )
