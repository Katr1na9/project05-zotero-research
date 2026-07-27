"""Test-only Checker-facing robustness over the fixed A2 six-package catalog.

Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or
Part B elevation.

The helper performs no direct file or network I/O.  It delegates package
normalization, pin verification, and sufficiency evaluation to the protected
read-only A2 evaluator.  It adds only the accepted Slice-2 request boundary
and fail-closed decision classification.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from compiler.llm import m1_evidence_sufficiency_evaluator as a2


SCOPE_ID = (
    "CHECKER_FACING_DECISION_ROBUSTNESS_OVER_FIXED_A2_SIX_PACKAGE_CATALOG"
)
SURFACE_ID = "project05_depth2_public"
CATALOG_VERSION = "A2_EXACT_SIX_V0_1"
RECORD_CLASS = "path_a_readonly_checker_facing_sufficiency_record"
HELPER_ID = (
    "m1_path_a_sufficiency_beyond_synthetic_readonly_checker_v0_1"
)
HELPER_VERSION = "0.1.0"
NO_AUTHORITY_ELEVATION = "NO_AUTHORITY_ELEVATION"
HARD_BAN = (
    "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, "
    "or Part B elevation."
)
RED_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-m1-path-a-sufficiency-beyond-synthetic-red-"
    "owner-acceptance-v0.1-20260727.json"
)
RED_ACCEPTANCE_SHA256 = (
    "0a31047daed43654386127308e3f860dfe9fdc3a6d68510d8d97ef343e3bf68a"
)
RED_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-path-a-sufficiency-beyond-synthetic-"
    "red-design-v0.1-20260727.json"
)
RED_DESIGN_SHA256 = (
    "9ddfe28620f6dd7b5e83f3e40f228ab5d53aed6219622312131bb599413c7472"
)
RED_REVIEW_PACKET_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-kernel-owner-m1-path-a-sufficiency-beyond-"
    "synthetic-red-review-packet-v0.1-20260727.json"
)
RED_REVIEW_PACKET_SHA256 = (
    "231129b85425318ee9b994683940e5183c0b943ada4cfcaa81c45d382cee6b2b"
)
A2_EVALUATOR_SHA256 = (
    "ad4e5af8dd9af0012f5174b14822ce9146a6d0f491c07881b5b401d85d62e78f"
)

READONLY_REVIEW_SCOPE = "READONLY_DECLARED_SCOPE_REVIEW"
CTI_OBSERVED_LAUNDERING_SCOPE = "CTI_OBSERVED_LAUNDERING_REVIEW"
CTI_DERIVED_LAUNDERING_SCOPE = "CTI_DERIVED_LAUNDERING_REVIEW"
UNKNOWN_MODALITY_SCOPE = "UNKNOWN_MODALITY_REVIEW"
TEST_ONLY_AUTHORITY_REQUEST = "TEST_ONLY_READONLY_NO_ELEVATION"

_REQUEST_FIELDS = {
    "request_id",
    "surface_id",
    "catalog_version",
    "ordered_binding_ids",
    "requested_review_scope",
    "authority_request",
    "audit_log_binding_request",
}
_KNOWN_REVIEW_SCOPES = {
    READONLY_REVIEW_SCOPE,
    CTI_OBSERVED_LAUNDERING_SCOPE,
    CTI_DERIVED_LAUNDERING_SCOPE,
    UNKNOWN_MODALITY_SCOPE,
}
_ELEVATION_REQUESTS = {
    "L2_PASS",
    "PART_B_PASS",
    "PART_B_ELEVATION",
    "ADMISSION",
    "WRITE",
    "KERNEL_WRITE",
    "E_CASE_WRITE",
    "CERTIFICATE",
    "CERTIFIED_STOP",
    "STOP",
}
_SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_SYNTHETIC_DECLARED_SCOPE_CEILING = (
    "SYNTHETIC_DECLARED_SCOPE_CONDITIONAL_ONLY"
)
_EXPLICIT_NON_AUTHORIZATIONS = {
    "l2_pass": False,
    "part_b_pass": False,
    "part_b_elevation": False,
    "pb_si_008_open": False,
    "path_b_write": False,
    "production_registration": False,
    "mint": False,
    "admission": False,
    "kernel_or_e_case_write": False,
    "certificate": False,
    "certified_stop": False,
    "catalog_extension": False,
    "audit_log_binding": False,
    "real_or_production_checker": False,
    "non_synthetic_external_validity": False,
}


class PathAReadonlyCheckerError(ValueError):
    """Raised when a request is not a closed test-only JSON value."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def evaluate_checker_facing_sufficiency_decision_robustness(
    request: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Return one deterministic, non-authorizing Checker-facing record.

    All catalog and package semantics are delegated to the accepted A2
    evaluator.  This wrapper classifies only Slice-2 request intent.
    """

    normalized = _normalize_request(request)
    catalog = a2.package_binding_catalog(repo_root)
    catalog_by_id = {entry["binding_id"]: entry for entry in catalog}
    catalog_ids = [entry["binding_id"] for entry in catalog]

    unknown_ids = [
        binding_id
        for binding_id in normalized["ordered_binding_ids"]
        if binding_id not in catalog_by_id
    ]
    known_ids = [
        binding_id
        for binding_id in normalized["ordered_binding_ids"]
        if binding_id in catalog_by_id
    ]
    known_in_catalog_order = [
        binding_id for binding_id in catalog_ids if binding_id in known_ids
    ]
    order_mismatch = known_ids != known_in_catalog_order
    duplicate_ids = len(set(normalized["ordered_binding_ids"])) != len(
        normalized["ordered_binding_ids"]
    )

    decision_case: str
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    override: tuple[str, str, list[str]] | None = None

    if normalized["authority_request"] != TEST_ONLY_AUTHORITY_REQUEST:
        decision_case = "authority_elevation_request"
        override = (
            "DENY_AUTHORITY_ELEVATION_REQUEST",
            "DENY_INVALID_AUTHORITY_REQUEST",
            [
                "AUTHORITY_REQUEST_OUTSIDE_TEST_ONLY_READONLY_SCOPE",
                NO_AUTHORITY_ELEVATION,
            ],
        )
    elif normalized["audit_log_binding_request"]:
        decision_case = "audit_log_binding_without_named_sub_authority"
        override = (
            "DENY_UNKNOWN_BINDING",
            "DENY_INVALID_INPUT",
            [
                "AUDIT_LOG_NOT_IN_A2_EXACT_SIX_CATALOG",
                "NO_NAMED_SUB_AUTHORITY",
                NO_AUTHORITY_ELEVATION,
            ],
        )
    elif normalized["requested_review_scope"] in {
        CTI_OBSERVED_LAUNDERING_SCOPE,
        CTI_DERIVED_LAUNDERING_SCOPE,
    }:
        decision_case = "cti_modality_laundering"
        modality = (
            "observed"
            if normalized["requested_review_scope"]
            == CTI_OBSERVED_LAUNDERING_SCOPE
            else "derived"
        )
        rejected = [
            _candidate_for_request(
                normalized,
                source_class="cti_report_public_projection",
                epistemic_modality=modality,
            )
        ]
    elif (
        normalized["requested_review_scope"] not in _KNOWN_REVIEW_SCOPES
        or normalized["requested_review_scope"] == UNKNOWN_MODALITY_SCOPE
        or unknown_ids
        or duplicate_ids
        or order_mismatch
    ):
        decision_case = "unknown_binding_or_unknown_modality"
        rejected = [
            _candidate_for_request(
                normalized,
                source_class="system_log_public_projection",
                epistemic_modality="unknown",
            )
        ]
    else:
        accepted = [
            copy.deepcopy(catalog_by_id[binding_id])
            for binding_id in normalized["ordered_binding_ids"]
        ]
        decision_case = (
            "exact_six_catalog_readonly_review"
            if normalized["ordered_binding_ids"] == catalog_ids
            else "missing_required_binding_or_field_set"
        )

    if override is not None:
        # The protected evaluator is still invoked so pin/catalog semantics are
        # reverified.  Slice-2 then denies the out-of-scope request intent.
        underlying = _call_a2([], [], repo_root)
        sufficiency_decision, checker_decision, basis_codes = override
        partial_result = False
    else:
        underlying = _call_a2(accepted, rejected, repo_root)
        sufficiency_decision = underlying[
            "evidence_sufficiency_decision"
        ]["decision"]
        checker_decision = underlying["checker_decision"]["decision"]
        basis_codes = _unique_codes(
            [
                *underlying["evidence_sufficiency_decision"]["basis_codes"],
                *underlying["checker_decision"]["basis_codes"],
                NO_AUTHORITY_ELEVATION,
            ]
        )
        partial_result = False

    record = {
        "record_class": RECORD_CLASS,
        "scope_id": SCOPE_ID,
        "helper_id": HELPER_ID,
        "helper_version": HELPER_VERSION,
        "surface_id": SURFACE_ID,
        "catalog_version": CATALOG_VERSION,
        "request": copy.deepcopy(normalized),
        "request_sha256": a2.canonical_json_sha256(normalized),
        "decision_case": decision_case,
        "sufficiency_decision": sufficiency_decision,
        "checker_decision": checker_decision,
        "basis_codes": _unique_codes(basis_codes),
        "required_marker": NO_AUTHORITY_ELEVATION,
        "partial_result": partial_result,
        "catalog": {
            "count": len(catalog),
            "extended": False,
            "binding_ids": catalog_ids,
            "audit_log_binding": "DENY_UNKNOWN_BINDING",
        },
        "delegated_a2_evaluation": {
            "called": True,
            "record_sha256": a2.canonical_json_sha256(underlying),
            "sufficiency_decision": underlying[
                "evidence_sufficiency_decision"
            ]["decision"],
            "checker_decision": underlying["checker_decision"]["decision"],
        },
        "scientific_ceiling": {
            "ceiling": _SYNTHETIC_DECLARED_SCOPE_CEILING,
            "evidence_remains_synthetic_declared_scope": True,
            "operation_truth_established": False,
            "actor_authorization_established": False,
            "external_validity_established": False,
            "real_or_production_checker_connected": False,
        },
        "part_b_elevation": "NO_GO",
        "pb_si_008": "NOT_OPENED",
        "production_registration_enabled": False,
        "explicit_non_authorizations": copy.deepcopy(
            _EXPLICIT_NON_AUTHORIZATIONS
        ),
        "hard_ban": HARD_BAN,
    }
    _validate_output(record)
    return copy.deepcopy(record)


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise PathAReadonlyCheckerError(
            "request_type",
            "request must be a JSON object",
        )
    if set(request) != _REQUEST_FIELDS:
        raise PathAReadonlyCheckerError(
            "request_shape",
            "request fields are not exact",
        )
    request_id = request["request_id"]
    if (
        not isinstance(request_id, str)
        or not _SAFE_ID_PATTERN.fullmatch(request_id)
    ):
        raise PathAReadonlyCheckerError(
            "request_id",
            "request_id is not a safe opaque identifier",
        )
    if request["surface_id"] != SURFACE_ID:
        raise PathAReadonlyCheckerError(
            "surface_id",
            "surface_id is outside the accepted test surface",
        )
    if request["catalog_version"] != CATALOG_VERSION:
        raise PathAReadonlyCheckerError(
            "catalog_version",
            "catalog_version is not the exact A2 six-package catalog",
        )
    binding_ids = request["ordered_binding_ids"]
    if not isinstance(binding_ids, Sequence) or isinstance(
        binding_ids,
        (str, bytes, bytearray),
    ):
        raise PathAReadonlyCheckerError(
            "ordered_binding_ids",
            "ordered_binding_ids must be an array",
        )
    normalized_ids: list[str] = []
    for binding_id in binding_ids:
        if (
            not isinstance(binding_id, str)
            or not _SAFE_ID_PATTERN.fullmatch(binding_id)
        ):
            raise PathAReadonlyCheckerError(
                "ordered_binding_ids",
                "binding IDs must be safe opaque identifiers",
            )
        normalized_ids.append(binding_id)
    review_scope = request["requested_review_scope"]
    if (
        not isinstance(review_scope, str)
        or not _SAFE_ID_PATTERN.fullmatch(review_scope)
    ):
        raise PathAReadonlyCheckerError(
            "requested_review_scope",
            "requested_review_scope must be a safe opaque enum",
        )
    authority_request = request["authority_request"]
    if (
        not isinstance(authority_request, str)
        or not _SAFE_ID_PATTERN.fullmatch(authority_request)
    ):
        raise PathAReadonlyCheckerError(
            "authority_request",
            "authority_request must be a safe opaque enum",
        )
    audit_request = request["audit_log_binding_request"]
    if not isinstance(audit_request, bool):
        raise PathAReadonlyCheckerError(
            "audit_log_binding_request",
            "audit_log_binding_request must be boolean",
        )
    return {
        "request_id": request_id,
        "surface_id": request["surface_id"],
        "catalog_version": request["catalog_version"],
        "ordered_binding_ids": normalized_ids,
        "requested_review_scope": review_scope,
        "authority_request": authority_request,
        "audit_log_binding_request": audit_request,
    }


def _candidate_for_request(
    request: Mapping[str, Any],
    *,
    source_class: str,
    epistemic_modality: str,
) -> dict[str, str]:
    return {
        "source_class": source_class,
        "candidate_projection_sha256": a2.canonical_json_sha256(
            {
                "request_id": request["request_id"],
                "requested_review_scope": request[
                    "requested_review_scope"
                ],
                "ordered_binding_ids": request["ordered_binding_ids"],
            }
        ),
        "epistemic_modality": epistemic_modality,
    }


def _call_a2(
    accepted: Sequence[Mapping[str, Any]],
    rejected: Sequence[Mapping[str, Any]],
    repo_root: Path,
) -> dict[str, Any]:
    normalized_accepted = a2._normalize_accepted_bindings(
        accepted,
        repo_root.resolve(),
    )
    normalized_rejected = a2._normalize_rejected_candidates(rejected)
    authority = {
        "status": a2.TEST_AUTHORITY_STATUS,
        "scope": copy.deepcopy(a2._EXPECTED_SCOPE),
        "pinned_hashes": {
            "a2_red_acceptance_sha256": a2.A2_RED_ACCEPTANCE_SHA256,
            "red_design_sha256": a2.RED_DESIGN_SHA256,
            "conditional_example_sha256": a2.RED_EXAMPLE_SHA256S[
                "conditional"
            ],
            "missing_example_sha256": a2.RED_EXAMPLE_SHA256S["missing"],
            "cti_laundering_example_sha256": a2.RED_EXAMPLE_SHA256S[
                "cti_laundering"
            ],
            "external_evidence_schema_sha256": (
                a2.EXTERNAL_EVIDENCE_SCHEMA_SHA256
            ),
            "kernel_additive_schema_sha256": (
                a2.KERNEL_ADDITIVE_SCHEMA_SHA256
            ),
            "consumer_v0_2_sha256": a2.CONSUMER_CONTRACT_SHA256,
            "legacy_external_schema_sha256": (
                a2.LEGACY_EXTERNAL_SCHEMA_SHA256
            ),
            "legacy_kernel_schema_sha256": (
                a2.LEGACY_KERNEL_SCHEMA_SHA256
            ),
            "legacy_consumer_contract_sha256": (
                a2.LEGACY_CONSUMER_CONTRACT_SHA256
            ),
            "green_2_mapper_sha256": a2.GREEN_2_MAPPER_SHA256,
            "system_log_adapter_sha256": a2.SYSTEM_LOG_ADAPTER_SHA256,
            "provenance_graph_adapter_sha256": (
                a2.PROVENANCE_ADAPTER_SHA256
            ),
            "cti_report_adapter_sha256": a2.CTI_ADAPTER_SHA256,
            "evaluator_implementation_sha256": A2_EVALUATOR_SHA256,
        },
        "pinned_input": {
            "accepted_package_bindings_sha256": a2.canonical_json_sha256(
                normalized_accepted
            ),
            "rejected_candidates_sha256": a2.canonical_json_sha256(
                normalized_rejected
            ),
        },
        "output_policy": copy.deepcopy(a2._EXPECTED_OUTPUT_POLICY),
        "still_blocked": copy.deepcopy(a2._EXPECTED_STILL_BLOCKED),
    }
    return a2.evaluate_evidence_sufficiency_for_readonly_review(
        accepted,
        repo_root=repo_root,
        authority=authority,
        rejected_candidates=rejected,
    )


def _unique_codes(codes: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(codes))


def _validate_output(record: Mapping[str, Any]) -> None:
    if (
        record.get("record_class") != RECORD_CLASS
        or record.get("scope_id") != SCOPE_ID
        or not record.get("sufficiency_decision")
        or not record.get("checker_decision")
        or record.get("required_marker") != NO_AUTHORITY_ELEVATION
        or record.get("part_b_elevation") != "NO_GO"
        or record.get("pb_si_008") != "NOT_OPENED"
        or record.get("production_registration_enabled") is not False
        or record.get("partial_result") is not False
        or record.get("catalog", {}).get("count") != 6
        or record.get("catalog", {}).get("extended") is not False
        or record.get("catalog", {}).get("audit_log_binding")
        != "DENY_UNKNOWN_BINDING"
        or record.get("hard_ban") != HARD_BAN
        or any(record.get("explicit_non_authorizations", {}).values())
    ):
        raise PathAReadonlyCheckerError(
            "output_boundary",
            "output record violates the accepted Slice-2 boundary",
        )
