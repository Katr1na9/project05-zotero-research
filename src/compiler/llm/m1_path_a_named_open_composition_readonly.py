"""Test-only composition of Path A science and named-open classifications.

Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or
unrestricted Part B elevation.

The two accepted dependency records remain independent and unmodified.  This
module has no direct gate, Slice-2, filesystem, network, registry, write,
mint, admission, or production-registration capability.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from compiler.llm import (
    m1_path_a_science_realism_graded_readonly_checker as realism,
)
from src.scope import (
    part_b_si008_path_a_named_open_caller_wiring as caller,
)


COMPOSITION_CONTRACT_VERSION = "PATH_A_NAMED_OPEN_COMPOSITION_V0_1"
REQUESTED_OUTPUT_MODE = (
    "RETURN_BOTH_RECORDS_UNMODIFIED_NO_AMALGAMATION"
)
RECORD_CLASS = "path_a_science_named_open_composition_readonly_record"
HARD_BAN = (
    "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, "
    "or unrestricted Part B elevation."
)
PRODUCTION_REGISTRATION_ENABLED = False

_SAFE_ENUM_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_AUTHORITY_FIELDS = {
    "authority_id",
    "authorization_sha256",
    "mode",
    "allow_write",
    "allow_download",
    "allow_registry",
    "allow_dereference",
    "allow_authority_elevation",
}
_EXPECTED_AUTHORITY = {
    "authority_id": "PATH-A-NAMED-OPEN-COMPOSITION-TEST-ONLY-V0_1",
    "authorization_sha256": (
        "87e6a798c6c9dfb7f05a468daa99fb24"
        "8d0d75a3a57fed0d8a2f8a115b194858"
    ),
    "mode": "TEST_ONLY_READONLY_NO_PRODUCTION_REGISTRATION",
    "allow_write": False,
    "allow_download": False,
    "allow_registry": False,
    "allow_dereference": False,
    "allow_authority_elevation": False,
}
_INPUT_FIELDS = {
    "composition_case_id",
    "composition_contract_version",
    "realism_fixture_id",
    "realism_fixture_sha256",
    "realism_case_id",
    "realism_case_spec",
    "realism_case_spec_sha256",
    "named_open_fixture_id",
    "named_open_fixture_sha256",
    "caller_input_variant",
    "caller_input",
    "caller_input_sha256",
    "requested_output_mode",
}
_REALISM_CASE_FIELDS = {
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
    "composition_contract_version",
    "composition_case_id",
    "science_record",
    "named_open_gate_record",
    "science_branch_classification",
    "named_open_branch_classification",
    "composition_disposition",
    "records_amalgamated",
    "part_b_pass",
    "admission",
    "write_authority",
    "explicit_non_authorizations",
    "hard_ban",
    "record_hash",
}
_REALISM_FIXTURE_ID = "m1_path_a_science_realism_graded_fixture_v0_1"
_REALISM_FIXTURE_SHA256 = (
    "4f9eebb25fb9d520223b8d6d4a9579e96263af7392310570270e2b7c80aedd62"
)
_REALISM_AUTHORITY = {
    "mode": "TEST_ONLY_READONLY",
    "allow_write": False,
    "allow_download": False,
    "allow_registry": False,
    "allow_authority_elevation": False,
}
_CALLER_AUTHORITY = {
    "authority_id": "PB-SI008-PATH-A-CALLER-WIRING-TEST-ONLY-V0_1",
    "authorization_sha256": (
        "1d7c72cfb67c48537609c529e52e672e"
        "036001a6f99c27d3f8543dcbb13ac067"
    ),
    "mode": "TEST_ONLY_NO_PRODUCTION_REGISTRATION",
    "allow_write": False,
    "allow_dereference": False,
}
_EXPLICIT_NON_AUTHORIZATIONS = {
    "claim_named_open": False,
    "claim_promotion": False,
    "authority_promotion": False,
    "pass_condition_promotion": False,
    "l2_pass": False,
    "part_b_pass": False,
    "unrestricted_part_b_elevation": False,
    "path_b_write": False,
    "production_registration": False,
    "mint": False,
    "admission": False,
    "kernel_or_e_case_write": False,
    "certificate_or_certified_stop": False,
    "holdout_or_si006_or_b5": False,
    "non_synthetic_external_validity": False,
}

_CASE_REGISTRY = {
    "COMP-RG0-V01-EXACT": {
        "realism_case_id": "RG0-EXACT-SIX-CONTROL",
        "realism_case_spec_sha256": (
            "17691cf3e3e1d4dff1ed0aa9a212d84"
            "f63029469b43797f2422496add28f7a00"
        ),
        "named_open_fixture_id": (
            "PB_SI008_CALLER_EVIDENCE_V0_1_SYSTEM_LOG"
        ),
        "named_open_fixture_sha256": (
            "afb695d5730affe057e178be3e6b009b"
            "2cb641726e4e8610c67dffb9dc37e135"
        ),
        "caller_input_variant": "EXACT",
        "caller_input_sha256": (
            "7393ecd304b1d86e1650a8f2555f5479"
            "c4e949a25a5444a18893c2c6b683b0b8"
        ),
        "science_branch_classification": (
            "CONDITIONAL_DECLARED_SCOPE_ONLY"
        ),
        "named_open_branch_classification": (
            "ALLOW_NAMED_EVIDENCE_CANDIDACY_ONLY"
        ),
        "composition_disposition": (
            "DUAL_RECORDS_RETURNED_NO_AMALGAMATION"
        ),
    },
    "COMP-RG0-V02-EXACT": {
        "realism_case_id": "RG0-EXACT-SIX-CONTROL",
        "realism_case_spec_sha256": (
            "17691cf3e3e1d4dff1ed0aa9a212d84"
            "f63029469b43797f2422496add28f7a00"
        ),
        "named_open_fixture_id": (
            "PB_SI008_CALLER_EVIDENCE_V0_2_AUDIT_LOG"
        ),
        "named_open_fixture_sha256": (
            "46937b764485b8410b7e11e5e45e31a"
            "4068941a0ebf29d792f15a447a987ad54"
        ),
        "caller_input_variant": "EXACT",
        "caller_input_sha256": (
            "16d7f83c5e1a4aa4dec294c88ee1810e"
            "3d8c2039644e7292ad13e3cd3ccfd4e6"
        ),
        "science_branch_classification": (
            "CONDITIONAL_DECLARED_SCOPE_ONLY"
        ),
        "named_open_branch_classification": (
            "ALLOW_NAMED_EVIDENCE_CANDIDACY_ONLY"
        ),
        "composition_disposition": (
            "DUAL_RECORDS_RETURNED_NO_AMALGAMATION"
        ),
    },
    "COMP-RG3-V01-SCIENCE-DENY": {
        "realism_case_id": "RG3-CTI-MODALITY-LAUNDERING",
        "realism_case_spec_sha256": (
            "fb5542fca2974f92162521c9def42e57"
            "27a7af2ec4e001f1ef8b29b78db230b5"
        ),
        "named_open_fixture_id": (
            "PB_SI008_CALLER_EVIDENCE_V0_1_SYSTEM_LOG"
        ),
        "named_open_fixture_sha256": (
            "afb695d5730affe057e178be3e6b009b"
            "2cb641726e4e8610c67dffb9dc37e135"
        ),
        "caller_input_variant": "EXACT",
        "caller_input_sha256": (
            "7393ecd304b1d86e1650a8f2555f5479"
            "c4e949a25a5444a18893c2c6b683b0b8"
        ),
        "science_branch_classification": (
            "DENY_INVALID_OR_LAUNDERED_INPUT"
        ),
        "named_open_branch_classification": (
            "ALLOW_NAMED_EVIDENCE_CANDIDACY_ONLY"
        ),
        "composition_disposition": (
            "FAIL_CLOSED_SCIENCE_NONQUALIFYING"
        ),
    },
    "COMP-RG0-V01-NAMED-DENY": {
        "realism_case_id": "RG0-EXACT-SIX-CONTROL",
        "realism_case_spec_sha256": (
            "17691cf3e3e1d4dff1ed0aa9a212d84"
            "f63029469b43797f2422496add28f7a00"
        ),
        "named_open_fixture_id": (
            "PB_SI008_CALLER_EVIDENCE_V0_1_SYSTEM_LOG"
        ),
        "named_open_fixture_sha256": (
            "afb695d5730affe057e178be3e6b009b"
            "2cb641726e4e8610c67dffb9dc37e135"
        ),
        "caller_input_variant": "PROMOTION_TARGET_CLAIM",
        "caller_input_sha256": (
            "9cfbfeece627dec2bef47fccbdff232f3"
            "d3df492e8ec24022571b7817df12f67"
        ),
        "science_branch_classification": (
            "CONDITIONAL_DECLARED_SCOPE_ONLY"
        ),
        "named_open_branch_classification": (
            "DENY_SI008_NAMED_002_PROMOTION_TARGET_NOT_AUTHORIZED"
        ),
        "composition_disposition": "FAIL_CLOSED_NAMED_OPEN_DENY",
    },
    "COMP-RG3-V02-BOTH-DENY": {
        "realism_case_id": "RG3-CTI-MODALITY-LAUNDERING",
        "realism_case_spec_sha256": (
            "fb5542fca2974f92162521c9def42e57"
            "27a7af2ec4e001f1ef8b29b78db230b5"
        ),
        "named_open_fixture_id": (
            "PB_SI008_CALLER_EVIDENCE_V0_2_AUDIT_LOG"
        ),
        "named_open_fixture_sha256": (
            "46937b764485b8410b7e11e5e45e31a"
            "4068941a0ebf29d792f15a447a987ad54"
        ),
        "caller_input_variant": "PROMOTION_TARGET_CLAIM",
        "caller_input_sha256": (
            "0e70fddf475ddbcc264d0993d491069d"
            "5b03f0a04647cece3e4822d2e5637ec7"
        ),
        "science_branch_classification": (
            "DENY_INVALID_OR_LAUNDERED_INPUT"
        ),
        "named_open_branch_classification": (
            "DENY_SI008_NAMED_002_PROMOTION_TARGET_NOT_AUTHORIZED"
        ),
        "composition_disposition": (
            "FAIL_CLOSED_BOTH_BRANCHES_NONQUALIFYING"
        ),
    },
    "COMP-RG0-V01-MIXED-PAIR-DENY": {
        "realism_case_id": "RG0-EXACT-SIX-CONTROL",
        "realism_case_spec_sha256": (
            "17691cf3e3e1d4dff1ed0aa9a212d84"
            "f63029469b43797f2422496add28f7a00"
        ),
        "named_open_fixture_id": (
            "PB_SI008_CALLER_EVIDENCE_V0_1_SYSTEM_LOG"
        ),
        "named_open_fixture_sha256": (
            "afb695d5730affe057e178be3e6b009b"
            "2cb641726e4e8610c67dffb9dc37e135"
        ),
        "caller_input_variant": (
            "MIXED_V01_REFERENCE_WITH_V02_SCHEMA_CONSUMER"
        ),
        "caller_input_sha256": (
            "ce8d564a1fa0ea64188f79ed24e9ab3"
            "c661633af281202953ce770a704e87058"
        ),
        "science_branch_classification": (
            "CONDITIONAL_DECLARED_SCOPE_ONLY"
        ),
        "named_open_branch_classification": (
            "DENY_SI008_NAMED_003_REQUEST_NOT_QUALIFIED"
        ),
        "composition_disposition": (
            "FAIL_CLOSED_MIXED_REFERENCE_PAIR"
        ),
    },
}


class PathANamedOpenCompositionDenied(ValueError):
    """Fail-closed composition rejection with a stable code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def canonical_json_sha256(value: object) -> str:
    """Return a deterministic SHA-256 over canonical JSON bytes."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compose_path_a_science_and_named_open_evidence_candidacy(
    composition_input: Mapping[str, Any],
    *,
    test_only_authority: Mapping[str, Any],
) -> dict[str, Any]:
    """Return two accepted records under a non-amalgamation envelope."""

    _require_test_only_authority(test_only_authority)
    normalized, expected = _require_closed_world_input(composition_input)

    try:
        science_record = realism.evaluate_realism_graded_synthetic_case(
            copy.deepcopy(normalized["realism_case_spec"]),
            test_only_authority=copy.deepcopy(_REALISM_AUTHORITY),
        )
    except realism.PathARealismGradedError as exc:
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-005_SCIENCE_BRANCH_REJECTED"
        ) from exc

    science_classification = _science_classification(science_record)
    if (
        science_classification
        != expected["science_branch_classification"]
    ):
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-005_SCIENCE_BRANCH_REJECTED"
        )

    try:
        named_record = (
            caller.evaluate_path_a_structural_binding_for_named_open(
                copy.deepcopy(normalized["caller_input"]),
                test_only_authority=copy.deepcopy(_CALLER_AUTHORITY),
            )
        )
    except caller.PathACallerWiringDenied as exc:
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-006_NAMED_OPEN_CALLER_REJECTED"
        ) from exc

    named_classification = _named_open_classification(named_record)
    if (
        named_classification
        != expected["named_open_branch_classification"]
    ):
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-006_NAMED_OPEN_CALLER_REJECTED"
        )

    record = {
        "record_class": RECORD_CLASS,
        "composition_contract_version": COMPOSITION_CONTRACT_VERSION,
        "composition_case_id": normalized["composition_case_id"],
        "science_record": copy.deepcopy(science_record),
        "named_open_gate_record": copy.deepcopy(named_record),
        "science_branch_classification": science_classification,
        "named_open_branch_classification": named_classification,
        "composition_disposition": expected[
            "composition_disposition"
        ],
        "records_amalgamated": False,
        "part_b_pass": False,
        "admission": False,
        "write_authority": False,
        "explicit_non_authorizations": copy.deepcopy(
            _EXPLICIT_NON_AUTHORIZATIONS
        ),
        "hard_ban": HARD_BAN,
    }
    record["record_hash"] = canonical_json_sha256(record)
    _validate_output(record)
    return copy.deepcopy(record)


def _require_test_only_authority(
    authority: Mapping[str, Any],
) -> None:
    if (
        not isinstance(authority, Mapping)
        or set(authority) != _AUTHORITY_FIELDS
    ):
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-001_TEST_ONLY_AUTHORITY_REQUIRED"
        )
    for field, expected in _EXPECTED_AUTHORITY.items():
        actual = authority.get(field)
        if isinstance(expected, bool):
            if actual is not expected:
                raise PathANamedOpenCompositionDenied(
                    "COMPOSITION-001_TEST_ONLY_AUTHORITY_REQUIRED"
                )
        elif actual != expected:
            raise PathANamedOpenCompositionDenied(
                "COMPOSITION-001_TEST_ONLY_AUTHORITY_REQUIRED"
            )


def _require_closed_world_input(
    value: Mapping[str, Any],
) -> tuple[dict[str, Any], Mapping[str, str]]:
    if not isinstance(value, Mapping) or set(value) != _INPUT_FIELDS:
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-002_CLOSED_WORLD_INPUT_REQUIRED"
        )

    string_fields = (
        "composition_case_id",
        "composition_contract_version",
        "realism_fixture_id",
        "realism_fixture_sha256",
        "realism_case_id",
        "realism_case_spec_sha256",
        "named_open_fixture_id",
        "named_open_fixture_sha256",
        "caller_input_variant",
        "caller_input_sha256",
        "requested_output_mode",
    )
    if any(
        not isinstance(value.get(field), str)
        or not _SAFE_ENUM_PATTERN.fullmatch(value[field])
        for field in string_fields
    ):
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-002_CLOSED_WORLD_INPUT_REQUIRED"
        )
    if (
        value["composition_contract_version"]
        != COMPOSITION_CONTRACT_VERSION
        or value["requested_output_mode"] != REQUESTED_OUTPUT_MODE
        or not isinstance(value["realism_case_spec"], Mapping)
        or set(value["realism_case_spec"]) != _REALISM_CASE_FIELDS
        or not isinstance(value["caller_input"], Mapping)
        or set(value["caller_input"]) != set(caller.CALLER_INPUT_FIELDS)
    ):
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-002_CLOSED_WORLD_INPUT_REQUIRED"
        )

    expected = _CASE_REGISTRY.get(value["composition_case_id"])
    if expected is None:
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-003_EXACT_PAIR_NOT_ALLOWLISTED"
        )
    if (
        value["realism_fixture_id"] != _REALISM_FIXTURE_ID
        or value["realism_case_id"] != expected["realism_case_id"]
        or value["realism_case_spec"].get("case_id")
        != expected["realism_case_id"]
        or value["named_open_fixture_id"]
        != expected["named_open_fixture_id"]
        or value["caller_input_variant"]
        != expected["caller_input_variant"]
    ):
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-003_EXACT_PAIR_NOT_ALLOWLISTED"
        )

    digest_fields = (
        "realism_fixture_sha256",
        "realism_case_spec_sha256",
        "named_open_fixture_sha256",
        "caller_input_sha256",
    )
    if any(
        not _SHA256_PATTERN.fullmatch(value[field])
        for field in digest_fields
    ):
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-004_PIN_OR_CANONICAL_DIGEST_MISMATCH"
        )
    if (
        value["realism_fixture_sha256"] != _REALISM_FIXTURE_SHA256
        or value["realism_case_spec_sha256"]
        != expected["realism_case_spec_sha256"]
        or value["named_open_fixture_sha256"]
        != expected["named_open_fixture_sha256"]
        or value["caller_input_sha256"]
        != expected["caller_input_sha256"]
        or canonical_json_sha256(value["realism_case_spec"])
        != value["realism_case_spec_sha256"]
        or canonical_json_sha256(value["caller_input"])
        != value["caller_input_sha256"]
    ):
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-004_PIN_OR_CANONICAL_DIGEST_MISMATCH"
        )

    return copy.deepcopy(dict(value)), expected


def _science_classification(record: Mapping[str, Any]) -> str:
    if (
        record.get("sufficiency_decision")
        == "CONDITIONAL_SUFFICIENT_DECLARED_SCOPE_ONLY"
        and record.get("checker_decision")
        == "ACCEPT_CONDITIONAL_FOR_READONLY_REVIEW_ONLY"
    ):
        return "CONDITIONAL_DECLARED_SCOPE_ONLY"
    decision = record.get("sufficiency_decision")
    if isinstance(decision, str) and decision:
        return decision
    raise PathANamedOpenCompositionDenied(
        "COMPOSITION-005_SCIENCE_BRANCH_REJECTED"
    )


def _named_open_classification(record: Mapping[str, Any]) -> str:
    decision = record.get("decision")
    if decision == "ALLOW_NAMED_EVIDENCE_CANDIDACY_ONLY":
        return decision
    reason_code = record.get("reason_code")
    if decision == "DENY" and isinstance(reason_code, str) and reason_code:
        return "DENY_" + reason_code.replace("-", "_")
    raise PathANamedOpenCompositionDenied(
        "COMPOSITION-006_NAMED_OPEN_CALLER_REJECTED"
    )


def _validate_output(record: Mapping[str, Any]) -> None:
    payload = {
        key: value
        for key, value in record.items()
        if key != "record_hash"
    }
    if (
        set(record) != _OUTPUT_FIELDS
        or record.get("record_class") != RECORD_CLASS
        or record.get("composition_contract_version")
        != COMPOSITION_CONTRACT_VERSION
        or record.get("records_amalgamated") is not False
        or record.get("part_b_pass") is not False
        or record.get("admission") is not False
        or record.get("write_authority") is not False
        or record.get("hard_ban") != HARD_BAN
        or any(record.get("explicit_non_authorizations", {}).values())
        or record.get("record_hash") != canonical_json_sha256(payload)
    ):
        raise PathANamedOpenCompositionDenied(
            "COMPOSITION-007_OUTPUT_BOUNDARY_VIOLATION"
        )


__all__ = [
    "COMPOSITION_CONTRACT_VERSION",
    "HARD_BAN",
    "PRODUCTION_REGISTRATION_ENABLED",
    "PathANamedOpenCompositionDenied",
    "canonical_json_sha256",
    "compose_path_a_science_and_named_open_evidence_candidacy",
]
