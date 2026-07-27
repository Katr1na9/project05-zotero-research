"""Test-only Path A caller for the additive PB-SI-008 named-open gate.

Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.scope.part_b_si008_named_open_path_a_evidence_candidacy import (
    evaluate_si008_named_open_request,
)


PRODUCTION_REGISTRATION_ENABLED = False
HARD_BAN = "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation."

TEST_ONLY_AUTHORITY_FIELDS = frozenset(
    {
        "authority_id",
        "authorization_sha256",
        "mode",
        "allow_write",
        "allow_dereference",
    }
)
CALLER_INPUT_FIELDS = frozenset(
    {
        "request_id",
        "promotion_target",
        "reference_kind",
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
    }
)
GATE_REQUEST_FIELDS = frozenset(
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

_EXPECTED_TEST_ONLY_AUTHORITY = {
    "authority_id": "PB-SI008-PATH-A-CALLER-WIRING-TEST-ONLY-V0_1",
    "authorization_sha256": (
        "1d7c72cfb67c48537609c529e52e672e"
        "036001a6f99c27d3f8543dcbb13ac067"
    ),
    "mode": "TEST_ONLY_NO_PRODUCTION_REGISTRATION",
    "allow_write": False,
    "allow_dereference": False,
}
_FIXED_REQUEST_FIELDS = {
    "request_kind": "PROMOTE_TO_PART_B_NAMED_TARGET",
    "named_target_id": (
        "PATH_A_EVIDENCE_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1"
    ),
    "requested_authority_scope": (
        "EVIDENCE_STRUCTURAL_CANDIDACY_ONLY"
    ),
    "reference_access_mode": (
        "CLASSIFY_DECLARED_REFERENCE_ONLY_NO_DEREFERENCE"
    ),
}
_REQUIRED_NONEMPTY_INPUT_FIELDS = CALLER_INPUT_FIELDS - {"claim_id"}


class PathACallerWiringDenied(ValueError):
    """Fail-closed caller rejection before the named-open gate is invoked."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def evaluate_path_a_structural_binding_for_named_open(
    caller_input: Mapping[str, Any],
    *,
    test_only_authority: Mapping[str, Any],
) -> dict[str, object]:
    """Build the exact request and return the gate record without wrapping it."""

    _require_test_only_authority(test_only_authority)
    _require_closed_world_caller_input(caller_input)

    request = {
        "request_id": caller_input["request_id"],
        "request_kind": _FIXED_REQUEST_FIELDS["request_kind"],
        "promotion_target": caller_input["promotion_target"],
        "reference_kind": caller_input["reference_kind"],
        "named_target_id": _FIXED_REQUEST_FIELDS["named_target_id"],
        "source_schema_version": caller_input["source_schema_version"],
        "source_schema_sha256": caller_input["source_schema_sha256"],
        "consumer_contract_id": caller_input["consumer_contract_id"],
        "consumer_contract_sha256": caller_input[
            "consumer_contract_sha256"
        ],
        "package_sha256": caller_input["package_sha256"],
        "structural_validation_receipt_sha256": caller_input[
            "structural_validation_receipt_sha256"
        ],
        "record_class": caller_input["record_class"],
        "claim_id": caller_input["claim_id"],
        "claim_id_state": caller_input["claim_id_state"],
        "admission_state": caller_input["admission_state"],
        "structural_validation_status": caller_input[
            "structural_validation_status"
        ],
        "requested_authority_scope": _FIXED_REQUEST_FIELDS[
            "requested_authority_scope"
        ],
        "reference_access_mode": _FIXED_REQUEST_FIELDS[
            "reference_access_mode"
        ],
    }
    if set(request) != GATE_REQUEST_FIELDS:
        raise AssertionError("caller failed to build the exact gate request")
    return evaluate_si008_named_open_request(request)


def _require_test_only_authority(
    authority: Mapping[str, Any],
) -> None:
    if (
        not isinstance(authority, Mapping)
        or set(authority) != TEST_ONLY_AUTHORITY_FIELDS
        or any(
            authority.get(field) != expected
            for field, expected in _EXPECTED_TEST_ONLY_AUTHORITY.items()
        )
    ):
        raise PathACallerWiringDenied(
            "CALLER-WIRING-001_TEST_ONLY_AUTHORITY_REQUIRED"
        )


def _require_closed_world_caller_input(
    caller_input: Mapping[str, Any],
) -> None:
    if (
        not isinstance(caller_input, Mapping)
        or set(caller_input) != CALLER_INPUT_FIELDS
        or any(
            not isinstance(caller_input.get(field), str)
            or not caller_input.get(field)
            for field in _REQUIRED_NONEMPTY_INPUT_FIELDS
        )
    ):
        raise PathACallerWiringDenied(
            "CALLER-WIRING-002_CLOSED_WORLD_INPUT_REQUIRED"
        )


__all__ = [
    "CALLER_INPUT_FIELDS",
    "GATE_REQUEST_FIELDS",
    "HARD_BAN",
    "PRODUCTION_REGISTRATION_ENABLED",
    "PathACallerWiringDenied",
    "TEST_ONLY_AUTHORITY_FIELDS",
    "evaluate_path_a_structural_binding_for_named_open",
]
