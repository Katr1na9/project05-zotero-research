"""Test-only readonly evidence-sufficiency evaluator.

This module implements the accepted Path A2 RED decision contract over the
six exact synthetic evidence-package bindings.  It has no registry,
production Checker, mint, admission, ingestion, Kernel, E_case, certificate,
or STOP capability.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError


SURFACE_ID = "project05_depth2_public"
SCHEMA_VERSION = "m1-evidence-sufficiency-checker-red-v0.1"
RECORD_CLASS = "evidence_sufficiency_checker_decision"
EVALUATOR_ID = "m1_evidence_sufficiency_readonly_green_v0_1"
EVALUATOR_VERSION = "0.1.0"
TEST_AUTHORITY_STATUS = (
    "activated_test_only_in_memory_evidence_sufficiency_authority"
)
EVALUATOR_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_evidence_sufficiency_evaluator.py"
)

A2_RED_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-m1-evidence-sufficiency-checker-non-null-red-"
    "owner-acceptance-v0.1-20260727.json"
)
A2_RED_ACCEPTANCE_SHA256 = (
    "97ff8bceb7c6ff3bd395c8013816d3b5ef1daa9a53d1f623735376ffae1d9481"
)
RED_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-evidence-sufficiency-checker-non-null-"
    "red-design-v0.1-20260727.json"
)
RED_DESIGN_SHA256 = (
    "82afa37e8e027b2c4e0a4d4de7668b0232d905787dd83278a6e41919a756250b"
)
RED_REVIEW_PACKET_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-kernel-owner-m1-evidence-sufficiency-checker-"
    "non-null-red-review-packet-v0.1-20260727.json"
)
RED_REVIEW_PACKET_SHA256 = (
    "d1b8e90495fd99b9d265e97f9ce9cde1e3c8ac65f318388409f2ecd71b0a1441"
)
RED_CONTRACT_TEST_PATH = (
    "tests/compiler_contract/test_m1_evidence_sufficiency_contract.py"
)
RED_CONTRACT_TEST_SHA256 = (
    "acc9878c8fc0d1fc8ad2cfb9e91983712e220311e732842b17066c09e275d435"
)

RED_EXAMPLE_PATHS = {
    "conditional": (
        "docs/llm-editor/fixtures/"
        "evidence-sufficiency-checker-non-null-red-v0.1/"
        "conditional-sufficient-record.json"
    ),
    "missing": (
        "docs/llm-editor/fixtures/"
        "evidence-sufficiency-checker-non-null-red-v0.1/"
        "missing-modalities-fail-record.json"
    ),
    "cti_laundering": (
        "docs/llm-editor/fixtures/"
        "evidence-sufficiency-checker-non-null-red-v0.1/"
        "cti-laundering-deny-record.json"
    ),
}
RED_EXAMPLE_SHA256S = {
    "conditional": (
        "0c31ea39735f3ccc3ad86c4830a5994680a3da10a49f43e5a5ca695da5f75ef1"
    ),
    "missing": (
        "3591ef160d9a6a51c719f02ae34abef6f72806b4c0bf63d2b64cbe326ab24ef9"
    ),
    "cti_laundering": (
        "42fdba3766a9c6e91bab0f6a3a641949a12e06385170a0154b0360db9265a9bc"
    ),
}

PATH_A1_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-m1-evidence-claim-ir-coverage-expansion-"
    "owner-acceptance-v0.1-20260727.json"
)
PATH_A1_ACCEPTANCE_SHA256 = (
    "f4b00bf3fd10cd8d70afa9cdf3ee71b7ed16bd2da694b6caf31b210a7c3443a4"
)
READONLY_E2E_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-m1-evidence-claim-ir-readonly-e2e-"
    "owner-acceptance-v0.1-20260727.json"
)
READONLY_E2E_ACCEPTANCE_SHA256 = (
    "dd264de3f09a385070098969a5a4809c846ffde246e869a7f4382a8fbff4615c"
)
SCHEMA_GREEN_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-claim-ir-evidence-claim-record-schema-green-"
    "owner-acceptance-v0.1-20260727.json"
)
SCHEMA_GREEN_ACCEPTANCE_SHA256 = (
    "60c31ffef0e4288f031b749ff89807904d13986025b56c769295ef80348ce148"
)
GREEN_2_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-m1-evidence-to-claim-ir-mapping-green-2-"
    "owner-acceptance-v0.1-20260727.json"
)
GREEN_2_ACCEPTANCE_SHA256 = (
    "138715778a4a9ecc5cbaef913b56244b3b0c52e11e9f774a50bfc2e0b64a66f4"
)
EXTERNAL_EVIDENCE_SCHEMA_PATH = (
    "schemas/claim-ir-external-envelope-evidence-v0.1.schema.json"
)
EXTERNAL_EVIDENCE_SCHEMA_SHA256 = (
    "9abc23e2258298038e137dbbe38168867d07108fa27719aa68c1c2b752ae2a7c"
)
KERNEL_ADDITIVE_SCHEMA_PATH = (
    "schemas/claim-ir-kernel-evidence-additive-v0.1.schema.json"
)
KERNEL_ADDITIVE_SCHEMA_SHA256 = (
    "d8cccbad36c6cca068fdc9d17ecbd8d0db2e08271f986127d0c0236353a79ce5"
)
CONSUMER_CONTRACT_PATH = (
    "docs/kernel/"
    "kernel-v0.8-shared-claim-ir-consumer-contract-evidence-candidate-"
    "effective-v0.2-20260727.json"
)
CONSUMER_CONTRACT_SHA256 = (
    "fe5222b9b4e0ddaf990761b34bdfc5004f45f55d3e2155b09388fb9596a1e504"
)
LEGACY_EXTERNAL_SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
LEGACY_EXTERNAL_SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
LEGACY_KERNEL_SCHEMA_PATH = "schemas/claim-ir-kernel.schema.json"
LEGACY_KERNEL_SCHEMA_SHA256 = (
    "7c6fa2db0b75d69340be5a8843ba0c373e2d5b25b0d37cf8f1d1c416a787865d"
)
LEGACY_CONSUMER_CONTRACT_PATH = (
    "docs/kernel/"
    "kernel-v0.8-shared-claim-ir-consumer-contract-effective-"
    "v0.1-20260725.json"
)
LEGACY_CONSUMER_CONTRACT_SHA256 = (
    "a2a176fdeb2b93205a7f5e11c7c096236e2dc582d1c31f8f4a1534866c008d63"
)
GREEN_2_MAPPER_PATH = "src/compiler/llm/m1_evidence_to_claim_ir_mapper.py"
GREEN_2_MAPPER_SHA256 = (
    "1dd8f407cc8fe840d90a7bf66c43e2cb11b5131877f2e46f92f2a1ffd372965b"
)

SYSTEM_LOG_ADAPTER_PATH = (
    "src/compiler/llm/m1_system_log_projection_adapter.py"
)
SYSTEM_LOG_ADAPTER_SHA256 = (
    "b7cc4710a2db30eedb353b44671d0f4993a50442c3f5bd2afe06ed5ee33f0116"
)
PROVENANCE_ADAPTER_PATH = (
    "src/compiler/llm/m1_provenance_graph_projection_adapter.py"
)
PROVENANCE_ADAPTER_SHA256 = (
    "9068315019a2980bb43b81d9641537c5a7c69ca63f14c4b9e876a653f8ffeae5"
)
CTI_ADAPTER_PATH = "src/compiler/llm/m1_cti_report_projection_adapter.py"
CTI_ADAPTER_SHA256 = (
    "cc0e04dd15372ecc1e0b5b68777458f07a361cb77ec7ce2c318b1ef42a07be3e"
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_PACKAGE_BINDING_FIELDS = (
    "binding_id",
    "package_role",
    "source_class",
    "epistemic_modality",
    "package_sha256",
    "claim_count",
    "evidence_field_path_set_sha256",
)
_REJECTED_CANDIDATE_INPUT_FIELDS = {
    "source_class",
    "candidate_projection_sha256",
    "epistemic_modality",
}
_SOURCE_CLASSES = (
    "system_log_public_projection",
    "provenance_graph_public_projection",
    "cti_report_public_projection",
)

_EXPECTED_SCOPE = {
    "test_only": True,
    "in_memory_only": True,
    "surface_id": SURFACE_ID,
    "evaluator_id": EVALUATOR_ID,
    "evaluator_version": EVALUATOR_VERSION,
    "registry_activation": False,
    "production_execute": False,
    "checker_runtime_connection": False,
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "assisted_test_only_readonly_decision_record",
    "file_write": False,
    "draft_schema_effective": False,
    "truth_assertion": False,
    "mint": False,
    "admission": False,
    "ingestion": False,
    "kernel_write": False,
    "e_case_write": False,
    "certificate": False,
    "certified_stop": False,
}
_EXPECTED_STILL_BLOCKED = {
    "effective_schema_elevation": True,
    "real_checker_runtime": True,
    "registry_activation": True,
    "production_execute": True,
    "activation_ledger_write": True,
    "claim_id_mint": True,
    "admission": True,
    "kernel_ingestion": True,
    "kernel_or_e_case_write": True,
    "certificate_generation": True,
    "certified_stop": True,
    "a3_audit_log": True,
    "path_b": True,
}
_PINNED_IDENTITIES = {
    "external_evidence_schema_sha256": EXTERNAL_EVIDENCE_SCHEMA_SHA256,
    "kernel_additive_schema_sha256": KERNEL_ADDITIVE_SCHEMA_SHA256,
    "consumer_v0_2_sha256": CONSUMER_CONTRACT_SHA256,
    "green_2_mapper_sha256": GREEN_2_MAPPER_SHA256,
}
_NON_AUTHORIZATIONS = {
    "a3_audit_log": False,
    "registry_activation": False,
    "production_execute": False,
    "claim_id_mint": False,
    "admission": False,
    "kernel_or_e_case_write": False,
    "certificate": False,
    "certified_stop": False,
}


class M1EvidenceSufficiencyEvaluatorError(ValueError):
    """Raised when test-only evaluation fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def canonical_json_sha256(value: Any) -> str:
    """Return the deterministic digest used for authority and record inputs."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise M1EvidenceSufficiencyEvaluatorError(
            "canonical_json",
            "value is not canonical JSON",
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def verify_evaluator_pins(repo_root: Path) -> None:
    """Verify the accepted RED contract and all protected identities."""

    root = repo_root.resolve()
    pins = (
        (A2_RED_ACCEPTANCE_PATH, A2_RED_ACCEPTANCE_SHA256),
        (RED_DESIGN_PATH, RED_DESIGN_SHA256),
        (RED_REVIEW_PACKET_PATH, RED_REVIEW_PACKET_SHA256),
        (RED_CONTRACT_TEST_PATH, RED_CONTRACT_TEST_SHA256),
        *tuple(
            (RED_EXAMPLE_PATHS[name], RED_EXAMPLE_SHA256S[name])
            for name in ("conditional", "missing", "cti_laundering")
        ),
        (PATH_A1_ACCEPTANCE_PATH, PATH_A1_ACCEPTANCE_SHA256),
        (READONLY_E2E_ACCEPTANCE_PATH, READONLY_E2E_ACCEPTANCE_SHA256),
        (SCHEMA_GREEN_ACCEPTANCE_PATH, SCHEMA_GREEN_ACCEPTANCE_SHA256),
        (GREEN_2_ACCEPTANCE_PATH, GREEN_2_ACCEPTANCE_SHA256),
        (EXTERNAL_EVIDENCE_SCHEMA_PATH, EXTERNAL_EVIDENCE_SCHEMA_SHA256),
        (KERNEL_ADDITIVE_SCHEMA_PATH, KERNEL_ADDITIVE_SCHEMA_SHA256),
        (CONSUMER_CONTRACT_PATH, CONSUMER_CONTRACT_SHA256),
        (LEGACY_EXTERNAL_SCHEMA_PATH, LEGACY_EXTERNAL_SCHEMA_SHA256),
        (LEGACY_KERNEL_SCHEMA_PATH, LEGACY_KERNEL_SCHEMA_SHA256),
        (
            LEGACY_CONSUMER_CONTRACT_PATH,
            LEGACY_CONSUMER_CONTRACT_SHA256,
        ),
        (GREEN_2_MAPPER_PATH, GREEN_2_MAPPER_SHA256),
        (SYSTEM_LOG_ADAPTER_PATH, SYSTEM_LOG_ADAPTER_SHA256),
        (PROVENANCE_ADAPTER_PATH, PROVENANCE_ADAPTER_SHA256),
        (CTI_ADAPTER_PATH, CTI_ADAPTER_SHA256),
    )
    for relative_path, expected_sha in pins:
        path = root / relative_path
        if not path.is_file():
            raise M1EvidenceSufficiencyEvaluatorError(
                "missing_pin",
                f"required pin is missing: {relative_path}",
            )
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise M1EvidenceSufficiencyEvaluatorError(
                "pin_mismatch",
                f"required pin mismatch: {relative_path}",
            )

    acceptance = _load_json(root / A2_RED_ACCEPTANCE_PATH)
    if (
        acceptance.get("decision") != "accept"
        or acceptance.get("status")
        != "path_a2_red_contract_accepted_no_green_evaluator_or_path_b"
        or acceptance.get("pinned_red_design", {}).get("content_sha256")
        != RED_DESIGN_SHA256
        or acceptance.get("separate_authority_required_for_a2_green") is not True
    ):
        raise M1EvidenceSufficiencyEvaluatorError(
            "acceptance_contract",
            "A2 RED Owner acceptance is not exact",
        )

    design = _load_json(root / RED_DESIGN_PATH)
    if (
        design.get("status")
        != "assisted_red_design_not_effective_pending_kernel_owner_review"
        or design.get("this_design_is_not_an_effective_schema_or_runtime")
        is not True
        or design.get("input_binding_rules", {}).get("wildcard_or_fallback")
        is not False
    ):
        raise M1EvidenceSufficiencyEvaluatorError(
            "red_design",
            "accepted RED design boundary is not exact",
        )
    try:
        Draft202012Validator.check_schema(design["draft_contract_schema"])
    except (KeyError, SchemaError, TypeError) as exc:
        raise M1EvidenceSufficiencyEvaluatorError(
            "red_schema",
            "embedded RED schema is invalid",
        ) from exc
    validator = Draft202012Validator(design["draft_contract_schema"])
    expected_decisions = {
        "conditional": "CONDITIONAL_SUFFICIENT_DECLARED_SCOPE_ONLY",
        "missing": "FAIL_INSUFFICIENT_EVIDENCE",
        "cti_laundering": "DENY_INVALID_OR_LAUNDERED_INPUT",
    }
    for name, expected_decision in expected_decisions.items():
        example = _load_json(root / RED_EXAMPLE_PATHS[name])
        if list(validator.iter_errors(example)):
            raise M1EvidenceSufficiencyEvaluatorError(
                "red_example_schema",
                f"accepted RED example is invalid: {name}",
            )
        if (
            example["evidence_sufficiency_decision"]["decision"]
            != expected_decision
        ):
            raise M1EvidenceSufficiencyEvaluatorError(
                "red_example_decision",
                f"accepted RED example decision changed: {name}",
            )


def package_binding_catalog(repo_root: Path) -> list[dict[str, Any]]:
    """Return the exact six-package binding catalog from accepted RED."""

    verify_evaluator_pins(repo_root)
    design = _load_json(repo_root.resolve() / RED_DESIGN_PATH)
    return [
        {field: _json_copy(entry[field]) for field in _PACKAGE_BINDING_FIELDS}
        for entry in design["input_binding_catalog"]
    ]


def evaluate_evidence_sufficiency_for_readonly_review(
    accepted_package_bindings: Sequence[Mapping[str, Any]],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
    rejected_candidates: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Evaluate exact synthetic package bindings under the accepted RED rules."""

    root = repo_root.resolve()
    verify_evaluator_pins(root)
    accepted = _normalize_accepted_bindings(accepted_package_bindings, root)
    rejected = _normalize_rejected_candidates(rejected_candidates)
    _validate_test_authority(authority, accepted, rejected, root)
    if accepted and rejected:
        raise M1EvidenceSufficiencyEvaluatorError(
            "mixed_partial_input",
            "accepted packages and rejected candidates cannot be mixed",
        )

    if rejected:
        candidate = rejected[0]
        if candidate["epistemic_modality"] == "unknown":
            record = _build_unknown_record(candidate)
        else:
            record = _build_cti_laundering_record(candidate)
    else:
        catalog = package_binding_catalog(root)
        if [entry["binding_id"] for entry in accepted] == [
            entry["binding_id"] for entry in catalog
        ]:
            record = _build_conditional_record(accepted)
        else:
            record = _build_missing_record(accepted, catalog)

    _validate_output_record(record, root)
    return _json_copy(record)


def _normalize_accepted_bindings(
    bindings: Sequence[Mapping[str, Any]],
    root: Path,
) -> list[dict[str, Any]]:
    if not isinstance(bindings, Sequence) or isinstance(
        bindings, (str, bytes, bytearray)
    ):
        raise M1EvidenceSufficiencyEvaluatorError(
            "bindings_type",
            "accepted package bindings must be an array",
        )
    catalog = package_binding_catalog(root)
    catalog_by_id = {entry["binding_id"]: entry for entry in catalog}
    order = {
        entry["binding_id"]: index for index, entry in enumerate(catalog)
    }
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, Mapping):
            raise M1EvidenceSufficiencyEvaluatorError(
                "binding_shape",
                "each accepted package binding must be an object",
            )
        if set(binding) != set(_PACKAGE_BINDING_FIELDS):
            raise M1EvidenceSufficiencyEvaluatorError(
                "binding_shape",
                "accepted package binding fields are not exact",
            )
        binding_id = binding.get("binding_id")
        if binding_id not in catalog_by_id:
            raise M1EvidenceSufficiencyEvaluatorError(
                "unknown_binding",
                "accepted package binding is not in the exact RED catalog",
            )
        if binding_id in seen:
            raise M1EvidenceSufficiencyEvaluatorError(
                "duplicate_binding",
                "accepted package binding is duplicated",
            )
        expected = catalog_by_id[binding_id]
        if dict(binding) != expected:
            reason = (
                "evidence_field_set_mismatch"
                if binding.get("evidence_field_path_set_sha256")
                != expected["evidence_field_path_set_sha256"]
                else "package_binding_mismatch"
            )
            raise M1EvidenceSufficiencyEvaluatorError(
                reason,
                f"accepted package binding does not match catalog: {binding_id}",
            )
        seen.add(binding_id)
        normalized.append(_json_copy(expected))
    return sorted(normalized, key=lambda entry: order[entry["binding_id"]])


def _normalize_rejected_candidates(
    candidates: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(candidates, Sequence) or isinstance(
        candidates, (str, bytes, bytearray)
    ):
        raise M1EvidenceSufficiencyEvaluatorError(
            "candidates_type",
            "rejected candidates must be an array",
        )
    if len(candidates) > 1:
        raise M1EvidenceSufficiencyEvaluatorError(
            "candidate_count",
            "one fail-closed candidate is permitted per readonly decision",
        )
    normalized = []
    for candidate in candidates:
        if (
            not isinstance(candidate, Mapping)
            or set(candidate) != _REJECTED_CANDIDATE_INPUT_FIELDS
        ):
            raise M1EvidenceSufficiencyEvaluatorError(
                "candidate_shape",
                "rejected candidate fields are not exact",
            )
        source_class = candidate["source_class"]
        digest = candidate["candidate_projection_sha256"]
        modality = candidate["epistemic_modality"]
        if source_class not in _SOURCE_CLASSES:
            raise M1EvidenceSufficiencyEvaluatorError(
                "unknown_source_class",
                "rejected candidate source class is unknown",
            )
        if not isinstance(digest, str) or not _SHA256_PATTERN.fullmatch(digest):
            raise M1EvidenceSufficiencyEvaluatorError(
                "candidate_sha256",
                "rejected candidate digest is invalid",
            )
        if modality == "unknown":
            reason_code = "UNKNOWN_MODALITY_NO_PACKAGE"
        elif (
            source_class == "cti_report_public_projection"
            and modality in {"observed", "derived"}
        ):
            reason_code = "CTI_MODALITY_LAUNDERING_NO_PACKAGE"
        else:
            raise M1EvidenceSufficiencyEvaluatorError(
                "candidate_semantics",
                "candidate is neither unknown nor CTI laundering",
            )
        normalized.append(
            {
                "candidate_kind": "projection_declaration_without_package",
                "source_class": source_class,
                "candidate_projection_sha256": digest,
                "epistemic_modality": modality,
                "reason_code": reason_code,
                "package_emitted": False,
            }
        )
    return normalized


def _validate_test_authority(
    authority: Mapping[str, Any] | None,
    accepted: Sequence[Mapping[str, Any]],
    rejected: Sequence[Mapping[str, Any]],
    root: Path,
) -> None:
    if not isinstance(authority, Mapping):
        raise M1EvidenceSufficiencyEvaluatorError(
            "missing_authority",
            "explicit test-only authority is required",
        )
    expected_fields = {
        "status",
        "scope",
        "pinned_hashes",
        "pinned_input",
        "output_policy",
        "still_blocked",
    }
    if set(authority) != expected_fields:
        raise M1EvidenceSufficiencyEvaluatorError(
            "authority_shape",
            "test authority fields are not exact",
        )
    if authority["status"] != TEST_AUTHORITY_STATUS:
        raise M1EvidenceSufficiencyEvaluatorError(
            "authority_status",
            "test authority status is not accepted",
        )
    if authority["scope"] != _EXPECTED_SCOPE:
        raise M1EvidenceSufficiencyEvaluatorError(
            "authority_scope",
            "test authority scope is not exact",
        )
    evaluator_sha = hashlib.sha256(
        (root / EVALUATOR_IMPLEMENTATION_PATH).read_bytes()
    ).hexdigest()
    expected_hashes = {
        "a2_red_acceptance_sha256": A2_RED_ACCEPTANCE_SHA256,
        "red_design_sha256": RED_DESIGN_SHA256,
        "conditional_example_sha256": RED_EXAMPLE_SHA256S["conditional"],
        "missing_example_sha256": RED_EXAMPLE_SHA256S["missing"],
        "cti_laundering_example_sha256": RED_EXAMPLE_SHA256S[
            "cti_laundering"
        ],
        "external_evidence_schema_sha256": EXTERNAL_EVIDENCE_SCHEMA_SHA256,
        "kernel_additive_schema_sha256": KERNEL_ADDITIVE_SCHEMA_SHA256,
        "consumer_v0_2_sha256": CONSUMER_CONTRACT_SHA256,
        "legacy_external_schema_sha256": LEGACY_EXTERNAL_SCHEMA_SHA256,
        "legacy_kernel_schema_sha256": LEGACY_KERNEL_SCHEMA_SHA256,
        "legacy_consumer_contract_sha256": LEGACY_CONSUMER_CONTRACT_SHA256,
        "green_2_mapper_sha256": GREEN_2_MAPPER_SHA256,
        "system_log_adapter_sha256": SYSTEM_LOG_ADAPTER_SHA256,
        "provenance_graph_adapter_sha256": PROVENANCE_ADAPTER_SHA256,
        "cti_report_adapter_sha256": CTI_ADAPTER_SHA256,
        "evaluator_implementation_sha256": evaluator_sha,
    }
    if authority["pinned_hashes"] != expected_hashes:
        raise M1EvidenceSufficiencyEvaluatorError(
            "authority_pins",
            "test authority pins are not exact",
        )
    expected_input = {
        "accepted_package_bindings_sha256": canonical_json_sha256(accepted),
        "rejected_candidates_sha256": canonical_json_sha256(rejected),
    }
    if authority["pinned_input"] != expected_input:
        raise M1EvidenceSufficiencyEvaluatorError(
            "authority_input",
            "test authority input digest is not exact",
        )
    if authority["output_policy"] != _EXPECTED_OUTPUT_POLICY:
        raise M1EvidenceSufficiencyEvaluatorError(
            "authority_output",
            "test authority output policy is not exact",
        )
    if authority["still_blocked"] != _EXPECTED_STILL_BLOCKED:
        raise M1EvidenceSufficiencyEvaluatorError(
            "authority_blocked",
            "test authority blocked set is not exact",
        )


def _base_record(
    record_id: str,
    accepted: Sequence[Mapping[str, Any]],
    rejected: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_class": RECORD_CLASS,
        "record_id": record_id,
        "status": "assisted_red_example_not_effective",
        "surface_id": SURFACE_ID,
        "input_binding": {
            "accepted_packages": _json_copy(accepted),
            "rejected_candidates": _json_copy(rejected),
            "schema_validity_layer": "PASS_FOR_ACCEPTED_PACKAGES_ONLY",
            "consumer_structural_layer": (
                "PASS_STRUCTURAL_ONLY_NO_INGESTION_AUTHORITY"
            ),
        },
        "explicit_non_authorizations": _json_copy(_NON_AUTHORIZATIONS),
    }


def _sufficiency_decision(
    decision_id: str,
    decision: str,
    basis_codes: Sequence[str],
    fail_closed_reasons: Sequence[str],
    accepted: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "decision_id": decision_id,
        "decision": decision,
        "basis_codes": list(basis_codes),
        "fail_closed_reasons": list(fail_closed_reasons),
        "pinned_package_sha256s": [
            entry["package_sha256"] for entry in accepted
        ],
        "pinned_identities": _json_copy(_PINNED_IDENTITIES),
        "scope": "DECLARED_SYNTHETIC_READONLY_REVIEW_ONLY",
        "truth_asserted": False,
        "admission_authority": False,
        "ingestion_authority": False,
        "stop_authority": "NONE",
    }


def _checker_decision(
    decision_id: str,
    decision: str,
    sufficiency_ref: str,
    basis_codes: Sequence[str],
) -> dict[str, Any]:
    return {
        "decision_id": decision_id,
        "decision": decision,
        "sufficiency_decision_ref": sufficiency_ref,
        "checker_decision_non_null": True,
        "basis_codes": list(basis_codes),
        "truth_asserted": False,
        "admission_authority": False,
        "kernel_write_authority": False,
        "certificate_authority": False,
        "stop_authority": "NONE",
    }


def _build_conditional_record(
    accepted: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    record = _base_record(
        "sufficiency_checker_conditional_001",
        accepted,
        (),
    )
    decision_id = "sufficiency_conditional_001"
    record["evidence_sufficiency_decision"] = _sufficiency_decision(
        decision_id,
        "CONDITIONAL_SUFFICIENT_DECLARED_SCOPE_ONLY",
        (
            "EXACT_PACKAGE_PINS_VERIFIED",
            "EXACT_EVIDENCE_FIELD_SETS_VERIFIED",
            "E2E_ANCHOR_SET_PRESENT",
            "A1_COVERAGE_SET_PRESENT",
            "THREE_MODALITIES_PRESENT",
            "STRUCTURAL_VALIDITY_SEPARATE_FROM_SUFFICIENCY",
            "DECLARED_SYNTHETIC_SCOPE_ONLY",
            "CTI_REPORTED_ONLY",
            "NO_AUTHORITY_ELEVATION",
        ),
        (),
        accepted,
    )
    record["checker_decision"] = _checker_decision(
        "checker_conditional_001",
        "ACCEPT_CONDITIONAL_FOR_READONLY_REVIEW_ONLY",
        decision_id,
        (
            "CHECKER_OBJECT_SCHEMA_VALID",
            "STRUCTURAL_VALIDITY_SEPARATE_FROM_SUFFICIENCY",
            "DECLARED_SYNTHETIC_SCOPE_ONLY",
            "NO_AUTHORITY_ELEVATION",
        ),
    )
    return record


def _build_missing_record(
    accepted: Sequence[Mapping[str, Any]],
    catalog: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    exact_example_ids = {
        "e2e_anchor_system_log_9",
        "a1_coverage_system_log_4",
    }
    accepted_ids = {entry["binding_id"] for entry in accepted}
    if accepted_ids == exact_example_ids:
        suffix = "modalities_001"
    else:
        suffix = canonical_json_sha256(accepted)[:16]
    record = _base_record(
        f"sufficiency_checker_missing_{suffix}",
        accepted,
        (),
    )
    source_classes = {entry["source_class"] for entry in accepted}
    reasons = []
    for source_class, reason in (
        ("system_log_public_projection", "MISSING_SYSTEM_LOG_EVIDENCE"),
        (
            "provenance_graph_public_projection",
            "MISSING_PROVENANCE_GRAPH_EVIDENCE",
        ),
        ("cti_report_public_projection", "MISSING_CTI_REPORT_EVIDENCE"),
    ):
        if source_class not in source_classes:
            reasons.append(reason)
    if not reasons or len(accepted_ids) != len(catalog):
        if "MISSING_REQUIRED_EVIDENCE_FIELD_SET" not in reasons:
            reasons.append("MISSING_REQUIRED_EVIDENCE_FIELD_SET")
    if accepted_ids == exact_example_ids:
        reasons = [
            "MISSING_PROVENANCE_GRAPH_EVIDENCE",
            "MISSING_CTI_REPORT_EVIDENCE",
        ]
        sufficiency_id = "sufficiency_missing_modalities_001"
        checker_id = "checker_missing_modalities_001"
    else:
        sufficiency_id = f"sufficiency_missing_{suffix}"
        checker_id = f"checker_missing_{suffix}"
    record["evidence_sufficiency_decision"] = _sufficiency_decision(
        sufficiency_id,
        "FAIL_INSUFFICIENT_EVIDENCE",
        (
            "EXACT_PACKAGE_PINS_VERIFIED",
            "EXACT_EVIDENCE_FIELD_SETS_VERIFIED",
            "STRUCTURAL_VALIDITY_SEPARATE_FROM_SUFFICIENCY",
            "REQUIRED_MODALITY_MISSING",
            "DECLARED_SYNTHETIC_SCOPE_ONLY",
            "NO_AUTHORITY_ELEVATION",
        ),
        reasons,
        accepted,
    )
    record["checker_decision"] = _checker_decision(
        checker_id,
        "REJECT_FAIL_CLOSED",
        sufficiency_id,
        (
            "CHECKER_OBJECT_SCHEMA_VALID",
            "STRUCTURAL_VALIDITY_SEPARATE_FROM_SUFFICIENCY",
            "REQUIRED_MODALITY_MISSING",
            "NO_AUTHORITY_ELEVATION",
        ),
    )
    return record


def _build_cti_laundering_record(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    digest = candidate["candidate_projection_sha256"]
    exact_red = (
        candidate["epistemic_modality"] == "observed"
        and digest
        == "2869145b445195c780164fa9bce8721fa909ca68a9f4e41c4c85a1933c43d860"
    )
    suffix = "001" if exact_red else digest[:16]
    record = _base_record(
        f"sufficiency_checker_cti_laundering_{suffix}",
        (),
        (candidate,),
    )
    sufficiency_id = f"sufficiency_cti_laundering_{suffix}"
    checker_id = f"checker_cti_laundering_{suffix}"
    reason = (
        "CTI_OBSERVED_LAUNDERING"
        if candidate["epistemic_modality"] == "observed"
        else "CTI_DERIVED_LAUNDERING"
    )
    record["evidence_sufficiency_decision"] = _sufficiency_decision(
        sufficiency_id,
        "DENY_INVALID_OR_LAUNDERED_INPUT",
        (
            "CTI_MODALITY_LAUNDERING",
            "STRUCTURAL_VALIDITY_SEPARATE_FROM_SUFFICIENCY",
            "DECLARED_SYNTHETIC_SCOPE_ONLY",
            "NO_AUTHORITY_ELEVATION",
        ),
        (reason,),
        (),
    )
    record["checker_decision"] = _checker_decision(
        checker_id,
        "DENY_INVALID_INPUT",
        sufficiency_id,
        (
            "CHECKER_OBJECT_SCHEMA_VALID",
            "CTI_MODALITY_LAUNDERING",
            "NO_AUTHORITY_ELEVATION",
        ),
    )
    return record


def _build_unknown_record(candidate: Mapping[str, Any]) -> dict[str, Any]:
    suffix = candidate["candidate_projection_sha256"][:16]
    record = _base_record(
        f"sufficiency_checker_unknown_{suffix}",
        (),
        (candidate,),
    )
    sufficiency_id = f"sufficiency_unknown_{suffix}"
    record["evidence_sufficiency_decision"] = _sufficiency_decision(
        sufficiency_id,
        "ABSTAIN_UNRESOLVED_EVIDENCE",
        (
            "UNKNOWN_MODALITY_NO_PACKAGE",
            "STRUCTURAL_VALIDITY_SEPARATE_FROM_SUFFICIENCY",
            "DECLARED_SYNTHETIC_SCOPE_ONLY",
            "NO_AUTHORITY_ELEVATION",
        ),
        ("UNKNOWN_MODALITY_NO_PACKAGE",),
        (),
    )
    record["checker_decision"] = _checker_decision(
        f"checker_unknown_{suffix}",
        "ABSTAIN_FAIL_CLOSED",
        sufficiency_id,
        (
            "CHECKER_OBJECT_SCHEMA_VALID",
            "UNKNOWN_MODALITY_NO_PACKAGE",
            "NO_AUTHORITY_ELEVATION",
        ),
    )
    return record


def _validate_output_record(record: Mapping[str, Any], root: Path) -> None:
    design = _load_json(root / RED_DESIGN_PATH)
    errors = sorted(
        Draft202012Validator(design["draft_contract_schema"]).iter_errors(
            record
        ),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise M1EvidenceSufficiencyEvaluatorError(
            "output_schema",
            f"output fails accepted RED schema: {errors[0].message}",
        )
    sufficiency = record["evidence_sufficiency_decision"]
    checker = record["checker_decision"]
    accepted = record["input_binding"]["accepted_packages"]
    if checker["sufficiency_decision_ref"] != sufficiency["decision_id"]:
        raise M1EvidenceSufficiencyEvaluatorError(
            "checker_reference",
            "Checker decision does not reference sufficiency decision",
        )
    if sufficiency["pinned_package_sha256s"] != [
        entry["package_sha256"] for entry in accepted
    ]:
        raise M1EvidenceSufficiencyEvaluatorError(
            "package_pin_output",
            "output package pins do not match accepted bindings",
        )
    if (
        "NO_AUTHORITY_ELEVATION" not in sufficiency["basis_codes"]
        or "NO_AUTHORITY_ELEVATION" not in checker["basis_codes"]
    ):
        raise M1EvidenceSufficiencyEvaluatorError(
            "authority_marker",
            "output lacks explicit no-elevation basis",
        )
    if (
        sufficiency["truth_asserted"]
        or sufficiency["admission_authority"]
        or sufficiency["ingestion_authority"]
        or sufficiency["stop_authority"] != "NONE"
        or checker["truth_asserted"]
        or checker["admission_authority"]
        or checker["kernel_write_authority"]
        or checker["certificate_authority"]
        or checker["stop_authority"] != "NONE"
        or any(record["explicit_non_authorizations"].values())
    ):
        raise M1EvidenceSufficiencyEvaluatorError(
            "authority_elevation",
            "output attempts an authority transition",
        )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise M1EvidenceSufficiencyEvaluatorError(
            "json_pin",
            f"cannot read pinned JSON: {path}",
        ) from exc
    if not isinstance(value, dict):
        raise M1EvidenceSufficiencyEvaluatorError(
            "json_pin",
            f"pinned JSON is not an object: {path}",
        )
    return value


def _json_copy(value: Any) -> Any:
    try:
        return json.loads(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise M1EvidenceSufficiencyEvaluatorError(
            "json_value",
            "value is not JSON serializable",
        ) from exc
