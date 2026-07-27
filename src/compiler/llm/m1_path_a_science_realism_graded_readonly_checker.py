"""Test-only realism grading for the declared-synthetic Path A catalog.

Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or
unrestricted Part B elevation.

The module has no write, download, registry, mint, admission, or production
Checker capability.  It delegates recognized decision cases to the accepted
Slice-2 read-only helper and locally denies an attempted non-synthetic origin
claim without treating that claim as true.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from compiler.llm import (
    m1_path_a_sufficiency_beyond_synthetic_readonly_checker as slice2,
)


SCOPE_ID = "PATH_A_REALISM_GRADED_SYNTHETIC_DISTORTION_SUITE_V0_1"
SUITE_VERSION = "PATH_A_REALISM_GRADED_SYNTHETIC_DISTORTION_V0_1"
DECLARED_SYNTHETIC_ORIGIN = "SYNTHETIC_DECLARED_SCOPE"
NON_SYNTHETIC_ORIGIN_CLAIM = "NON_SYNTHETIC_ORIGIN_CLAIM"
SURFACE_ID = "project05_depth2_public"
CATALOG_VERSION = "A2_EXACT_SIX_V0_1"
RECORD_CLASS = "path_a_realism_graded_synthetic_readonly_decision_record"
NO_AUTHORITY_ELEVATION = "NO_AUTHORITY_ELEVATION"
HARD_BAN = "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation."

PRODUCTION_REGISTRATION_ENABLED = False

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SAFE_ENUM_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_CASE_FIELDS = {
    "case_id",
    "suite_version",
    "declared_origin",
    "surface_id",
    "catalog_version",
    "realism_grade",
    "distortion_id",
    "ordered_binding_ids",
    "requested_review_scope",
    "authority_request",
    "audit_log_binding_request",
}
_OUTPUT_FIELDS = {
    "record_class",
    "scope_id",
    "case_id",
    "suite_version",
    "declared_origin",
    "realism_grade",
    "distortion_id",
    "delegated_decision_case",
    "sufficiency_decision",
    "checker_decision",
    "basis_codes",
    "partial_result",
    "scientific_ceiling",
    "explicit_non_authorizations",
    "hard_ban",
    "record_hash",
}
_TEST_ONLY_AUTHORITY = {
    "mode": "TEST_ONLY_READONLY",
    "allow_write": False,
    "allow_download": False,
    "allow_registry": False,
    "allow_authority_elevation": False,
}
_CATALOG_IDS = (
    "e2e_anchor_system_log_9",
    "e2e_anchor_provenance_graph_16",
    "e2e_anchor_cti_report_11",
    "a1_coverage_system_log_4",
    "a1_coverage_provenance_graph_48",
    "a1_coverage_cti_report_34",
)
_CASE_ENUMS = {
    "RG0-EXACT-SIX-CONTROL": (
        "RG0_INTACT_SYNTHETIC_CONTROL",
        "NONE_EXACT_SIX_CONTROL",
    ),
    "RG1-MISSING-CRITICAL-MODALITY": (
        "RG1_INCOMPLETE_SYNTHETIC",
        "MISSING_REQUIRED_MODALITY_BINDING",
    ),
    "RG2-AMBIGUOUS-BINDINGS": (
        "RG2_AMBIGUOUS_SYNTHETIC",
        "UNKNOWN_DUPLICATE_OR_REORDERED_BINDING",
    ),
    "RG3-CTI-MODALITY-LAUNDERING": (
        "RG3_INVALID_OR_LAUNDERED_SYNTHETIC",
        "CTI_OBSERVED_OR_DERIVED_LAUNDERING",
    ),
    "RG4-ORIGIN-MISREPRESENTATION": (
        "RG4_ORIGIN_OR_AUTHORITY_MISREPRESENTATION",
        "NON_SYNTHETIC_ORIGIN_MISREPRESENTATION",
    ),
    "RG4-AUTHORITY-ELEVATION": (
        "RG4_ORIGIN_OR_AUTHORITY_MISREPRESENTATION",
        "L2_PART_B_WRITE_CERTIFICATE_OR_STOP_ELEVATION_REQUEST",
    ),
}
_EXPLICIT_NON_AUTHORIZATIONS = {
    "l2_pass": False,
    "part_b_pass": False,
    "unrestricted_part_b_elevation": False,
    "path_b_write": False,
    "production_registration": False,
    "mint": False,
    "admission": False,
    "kernel_or_e_case_write": False,
    "certificate_or_certified_stop": False,
    "production_checker_truth_authority": False,
    "si_006_download": False,
    "raw_audit_download": False,
    "a2_catalog_extension": False,
    "audit_log_as_seventh_a2_package": False,
    "non_synthetic_external_validity": False,
}


class PathARealismGradedError(ValueError):
    """Raised when the test-only authority or case is not closed-world."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def canonical_json_sha256(value: object) -> str:
    """Return SHA-256 over deterministic canonical JSON bytes."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evaluate_realism_graded_synthetic_case(
    case_spec: Mapping[str, Any],
    *,
    test_only_authority: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate one exact declared-synthetic distortion case read-only."""

    _validate_test_only_authority(test_only_authority)
    normalized = _normalize_case(case_spec)

    if (
        normalized["distortion_id"]
        == "NON_SYNTHETIC_ORIGIN_MISREPRESENTATION"
    ):
        delegated_decision_case = (
            "NOT_DELEGATED_ORIGIN_MISREPRESENTATION"
        )
        sufficiency_decision = "DENY_ORIGIN_MISREPRESENTATION"
        checker_decision = "DENY_INVALID_INPUT"
        basis_codes = [
            "DECLARED_SUITE_ORIGIN_IS_SYNTHETIC",
            "NON_SYNTHETIC_ORIGIN_ASSERTION_NOT_ACCEPTED_AS_TRUE",
            "NON_SYNTHETIC_EXTERNAL_VALIDITY_NOT_ESTABLISHED",
            NO_AUTHORITY_ELEVATION,
        ]
    else:
        delegated = (
            slice2
            .evaluate_checker_facing_sufficiency_decision_robustness(
                _slice2_request(normalized),
                repo_root=_REPO_ROOT,
            )
        )
        delegated_decision_case = delegated["decision_case"]
        sufficiency_decision = delegated["sufficiency_decision"]
        checker_decision = delegated["checker_decision"]
        basis_codes = _unique_codes(
            [
                *delegated["basis_codes"],
                "SYNTHETIC_ORIGIN_REMAINS_DECLARED",
                NO_AUTHORITY_ELEVATION,
            ]
        )

    record = {
        "record_class": RECORD_CLASS,
        "scope_id": SCOPE_ID,
        "case_id": normalized["case_id"],
        "suite_version": normalized["suite_version"],
        "declared_origin": normalized["declared_origin"],
        "realism_grade": normalized["realism_grade"],
        "distortion_id": normalized["distortion_id"],
        "delegated_decision_case": delegated_decision_case,
        "sufficiency_decision": sufficiency_decision,
        "checker_decision": checker_decision,
        "basis_codes": _unique_codes(basis_codes),
        "partial_result": False,
        "scientific_ceiling": {
            "ceiling": "SYNTHETIC_DECLARED_SCOPE_ONLY",
            "evidence_origin_remains_synthetic_declared_scope": True,
            "synthetic_distortion_decision_surface_established": True,
            "non_synthetic_external_validity_established": False,
            "recorded_corpus_ingestion_established": False,
            "real_world_content_representativeness_established": False,
            "operation_truth_established": False,
            "actor_authorization_established": False,
            "production_checker_connected": False,
        },
        "explicit_non_authorizations": copy.deepcopy(
            _EXPLICIT_NON_AUTHORIZATIONS
        ),
        "hard_ban": HARD_BAN,
    }
    record["record_hash"] = canonical_json_sha256(record)
    _validate_output(record)
    return copy.deepcopy(record)


def _validate_test_only_authority(
    authority: Mapping[str, Any],
) -> None:
    if not isinstance(authority, Mapping) or set(authority) != set(
        _TEST_ONLY_AUTHORITY
    ):
        raise PathARealismGradedError(
            "test_only_authority",
            "exact test-only authority is required",
        )
    if authority["mode"] != _TEST_ONLY_AUTHORITY["mode"] or any(
        authority[field] is not False
        for field in (
            "allow_write",
            "allow_download",
            "allow_registry",
            "allow_authority_elevation",
        )
    ):
        raise PathARealismGradedError(
            "test_only_authority",
            "authority cannot enable write, download, registry, or elevation",
        )


def _normalize_case(
    case_spec: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(case_spec, Mapping):
        raise PathARealismGradedError(
            "case_type",
            "case_spec must be a JSON object",
        )
    if set(case_spec) != _CASE_FIELDS:
        raise PathARealismGradedError(
            "case_shape",
            "case_spec fields are not exact",
        )
    for field in (
        "case_id",
        "suite_version",
        "declared_origin",
        "surface_id",
        "catalog_version",
        "realism_grade",
        "distortion_id",
        "requested_review_scope",
        "authority_request",
    ):
        value = case_spec[field]
        if (
            not isinstance(value, str)
            or not _SAFE_ENUM_PATTERN.fullmatch(value)
        ):
            raise PathARealismGradedError(
                (
                    "case_enum"
                    if field
                    in {"case_id", "realism_grade", "distortion_id"}
                    else "case_value"
                ),
                f"{field} must be a safe opaque enum",
            )

    case_id = case_spec["case_id"]
    expected_enums = _CASE_ENUMS.get(case_id)
    if expected_enums is None or expected_enums != (
        case_spec["realism_grade"],
        case_spec["distortion_id"],
    ):
        raise PathARealismGradedError(
            "case_enum",
            "case ID, realism grade, or distortion is not allowlisted",
        )
    if case_spec["suite_version"] != SUITE_VERSION:
        raise PathARealismGradedError(
            "case_value",
            "suite_version is not exact",
        )
    if case_spec["surface_id"] != SURFACE_ID:
        raise PathARealismGradedError(
            "case_value",
            "surface_id is not exact",
        )
    if case_spec["catalog_version"] != CATALOG_VERSION:
        raise PathARealismGradedError(
            "case_value",
            "catalog_version is not exact",
        )
    if case_spec["audit_log_binding_request"] is not False:
        raise PathARealismGradedError(
            "case_value",
            "audit_log cannot become a seventh A2 package",
        )

    binding_ids = case_spec["ordered_binding_ids"]
    if not isinstance(binding_ids, Sequence) or isinstance(
        binding_ids,
        (str, bytes, bytearray),
    ):
        raise PathARealismGradedError(
            "case_value",
            "ordered_binding_ids must be an array",
        )
    normalized_ids: list[str] = []
    for binding_id in binding_ids:
        if (
            not isinstance(binding_id, str)
            or not _SAFE_ENUM_PATTERN.fullmatch(binding_id)
        ):
            raise PathARealismGradedError(
                "case_value",
                "binding IDs must be safe opaque identifiers",
            )
        normalized_ids.append(binding_id)

    normalized = {
        field: copy.deepcopy(case_spec[field])
        for field in _CASE_FIELDS
    }
    normalized["ordered_binding_ids"] = normalized_ids
    _validate_case_values(normalized)
    return normalized


def _validate_case_values(case_spec: Mapping[str, Any]) -> None:
    case_id = case_spec["case_id"]
    exact_ids = list(_CATALOG_IDS)
    expected_ids: list[str]
    expected_scopes: set[str]
    expected_authorities: set[str]
    expected_origin = DECLARED_SYNTHETIC_ORIGIN

    if case_id == "RG0-EXACT-SIX-CONTROL":
        expected_ids = exact_ids
        expected_scopes = {slice2.READONLY_REVIEW_SCOPE}
        expected_authorities = {slice2.TEST_ONLY_AUTHORITY_REQUEST}
    elif case_id == "RG1-MISSING-CRITICAL-MODALITY":
        expected_ids = exact_ids[:-1]
        expected_scopes = {slice2.READONLY_REVIEW_SCOPE}
        expected_authorities = {slice2.TEST_ONLY_AUTHORITY_REQUEST}
    elif case_id == "RG2-AMBIGUOUS-BINDINGS":
        expected_ids = list(reversed(exact_ids))
        expected_scopes = {slice2.READONLY_REVIEW_SCOPE}
        expected_authorities = {slice2.TEST_ONLY_AUTHORITY_REQUEST}
    elif case_id == "RG3-CTI-MODALITY-LAUNDERING":
        expected_ids = []
        expected_scopes = {
            slice2.CTI_OBSERVED_LAUNDERING_SCOPE,
            slice2.CTI_DERIVED_LAUNDERING_SCOPE,
        }
        expected_authorities = {slice2.TEST_ONLY_AUTHORITY_REQUEST}
    elif case_id == "RG4-ORIGIN-MISREPRESENTATION":
        expected_ids = exact_ids
        expected_scopes = {slice2.READONLY_REVIEW_SCOPE}
        expected_authorities = {slice2.TEST_ONLY_AUTHORITY_REQUEST}
        expected_origin = NON_SYNTHETIC_ORIGIN_CLAIM
    else:
        expected_ids = exact_ids
        expected_scopes = {slice2.READONLY_REVIEW_SCOPE}
        expected_authorities = set(slice2._ELEVATION_REQUESTS)

    if (
        case_spec["ordered_binding_ids"] != expected_ids
        or case_spec["requested_review_scope"] not in expected_scopes
        or case_spec["authority_request"] not in expected_authorities
        or case_spec["declared_origin"] != expected_origin
    ):
        raise PathARealismGradedError(
            "case_value",
            "case values do not match the closed distortion definition",
        )


def _slice2_request(case_spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "request_id": case_spec["case_id"],
        "surface_id": case_spec["surface_id"],
        "catalog_version": case_spec["catalog_version"],
        "ordered_binding_ids": copy.deepcopy(
            case_spec["ordered_binding_ids"]
        ),
        "requested_review_scope": case_spec["requested_review_scope"],
        "authority_request": case_spec["authority_request"],
        "audit_log_binding_request": False,
    }


def _unique_codes(codes: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(codes))


def _validate_output(record: Mapping[str, Any]) -> None:
    payload = {
        key: value
        for key, value in record.items()
        if key != "record_hash"
    }
    if (
        set(record) != _OUTPUT_FIELDS
        or record.get("record_class") != RECORD_CLASS
        or record.get("scope_id") != SCOPE_ID
        or not record.get("sufficiency_decision")
        or not record.get("checker_decision")
        or NO_AUTHORITY_ELEVATION not in record.get("basis_codes", [])
        or record.get("partial_result") is not False
        or record.get("hard_ban") != HARD_BAN
        or any(record.get("explicit_non_authorizations", {}).values())
        or record.get("scientific_ceiling", {}).get(
            "evidence_origin_remains_synthetic_declared_scope"
        )
        is not True
        or record.get("scientific_ceiling", {}).get(
            "non_synthetic_external_validity_established"
        )
        is not False
        or record.get("record_hash") != canonical_json_sha256(payload)
    ):
        raise PathARealismGradedError(
            "output_boundary",
            "record violates the accepted science GREEN boundary",
        )
