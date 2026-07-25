"""Fail-closed binder for an opaque Claim-ID control-loop reference.

The binder accepts only the exact completed registration record and receipt,
then emits a versioned, read-only identity reference.  It does not modify a
controller or planner, wire a production import, mutate Claim IR lifecycle
state, or write Kernel/E_case/certificate/L2 surfaces.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from src.compiler.llm import claim_id_mainline_handoff as handoff_module
from src.compiler.llm.claim_id_mainline_handoff import (
    ADAPTER_ID,
    CLAIMS_CONTENT_HASH,
    CLAIM_COUNT,
    CLAIM_ID_LIST_SHA256,
    EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
    EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    EFFECTIVE_CONSUMER_CONTRACT_VERSION,
    HANDOFF_DESIGN_PATH,
    HANDOFF_DESIGN_SHA256,
    INGESTED_FIXTURE_PATH,
    INGESTED_FIXTURE_SHA256,
    PACKAGE_ID,
    SANITIZED_RECEIPT_PATH as INGESTION_RECEIPT_PATH,
    SANITIZED_RECEIPT_SHA256 as INGESTION_RECEIPT_SHA256,
    SCHEMA_PATH,
    SCHEMA_SHA256,
    SOURCE_CLASS,
    SURFACE_ID,
    build_claim_id_mainline_handoff,
    verify_mainline_handoff_pins,
)


AUTHORITY_BASE_COMMIT = "245f3b7e2bb07480082a943e9cb6e5c75bf6ac08"
AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-control-loop-reference-wiring-"
    "single-execute-authority-design-v0.1-20260725.json"
)
AUTHORITY_DESIGN_SHA256 = (
    "cf4a6fcd9faa6d6dadf3ca6b4caa5da1d80d96d10c6ecdef9a36ed7845ad7856"
)
AUTHORITY_DESIGN_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-claim-id-control-loop-reference-wiring-"
    "single-execute-authority-design-v0.1-20260725"
)
AUTHORITY_DESIGN_STATUS = (
    "design_only_claim_id_control_loop_reference_wiring_authority_not_activated"
)
BINDER_PATH = "src/compiler/llm/claim_id_control_loop_reference_binder.py"
REGISTRATION_RECORD_PATH = (
    "docs/llm-editor/fixtures/claim-id-mainline-registration/"
    "project05-depth2-public-v0.1/registration-record.json"
)
REGISTRATION_RECORD_SHA256 = (
    "7c0e9f5c09774610746c76ec6e2bda92c79ad9a54351cf6e3afc04ebe3f0e875"
)
REGISTRATION_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/claim-id-mainline-registration/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)
REGISTRATION_RECEIPT_SHA256 = (
    "edb1a654ee3b80f8b874b02f8364526e9f28e35120cff2e3f7ef70d74f2d228a"
)
REGISTRATION_ACTIVATION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-production-claim-id-mainline-registration-"
    "single-execute-activation-v0.1-20260725.json"
)
REGISTRATION_ACTIVATION_SHA256 = (
    "8b6c85ae5ab25d144cfb9de15d6ee6e00a24860e6ac78cd698c6840033cd63cd"
)
REGISTRATION_EXECUTOR_PATH = (
    "src/compiler/llm/claim_id_mainline_registration_executor.py"
)
REGISTRATION_EXECUTOR_SHA256 = (
    "1e47013d14f347b15bffc74a8e74746f52ae8ab7345eed77ee0cfd95cfd61182"
)
EFFECTIVE_CONSUMER_CONTRACT_PATH = (
    "docs/kernel/"
    "kernel-v0.8-shared-claim-ir-consumer-contract-effective-v0.1-20260725.json"
)
ACTIVATION_STATUS = "activated_single_claim_id_control_loop_reference_bind_authorized"
REFERENCE_STATUS = "bound_registered_claim_id_reference_read_only"
REFERENCE_MODE = "opaque_claim_identity_read_only"

_ACTIVATION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
_CLAIM_ID_PATTERN = re.compile(r"^clm_[A-Za-z0-9_-]+$")
_MAX_INPUT_BYTES = 2 * 1024 * 1024
_EXPECTED_LEDGER_BEFORE = {
    "authorized": 1,
    "maximum": 1,
    "started": 0,
    "consumed": 0,
    "remaining": 1,
    "retry": False,
    "resume": False,
    "fallback": False,
}
_EXPECTED_LEDGER_AFTER = {
    "authorized": 1,
    "maximum": 1,
    "started": 1,
    "consumed": 1,
    "remaining": 0,
    "retry": False,
    "resume": False,
    "fallback": False,
}
_EXPECTED_REGISTRATION_LEDGER_EXHAUSTED = copy.deepcopy(_EXPECTED_LEDGER_AFTER)
_EXPECTED_ACTIVATION_FIELDS = frozenset(
    {
        "artifact_id",
        "artifact_type",
        "version",
        "created_date",
        "authority_base_commit",
        "status",
        "authority_design",
        "target",
        "pinned_hashes",
        "selected_input",
        "execute_ledger",
        "output_policy",
        "still_blocked",
        "execution_audit",
    }
)
_EXPECTED_TARGET = {
    "surface_id": SURFACE_ID,
    "source_class": SOURCE_CLASS,
    "adapter_id": ADAPTER_ID,
    "package_id": PACKAGE_ID,
    "reference_mode": REFERENCE_MODE,
    "execution_scope": "single_versioned_reference_bind_only",
}
_EXPECTED_STATIC_PINS = {
    "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
    "registration_record_sha256": REGISTRATION_RECORD_SHA256,
    "registration_receipt_sha256": REGISTRATION_RECEIPT_SHA256,
    "exhausted_registration_activation_sha256": REGISTRATION_ACTIVATION_SHA256,
    "registration_executor_sha256": REGISTRATION_EXECUTOR_SHA256,
    "mainline_handoff_design_sha256": HANDOFF_DESIGN_SHA256,
    "effective_consumer_contract_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    "external_envelope_schema_sha256": SCHEMA_SHA256,
    "ingested_fixture_sha256": INGESTED_FIXTURE_SHA256,
    "sanitized_ingestion_receipt_sha256": INGESTION_RECEIPT_SHA256,
}
_EXPECTED_SELECTED_INPUT = {
    "registration_record": {
        "path": REGISTRATION_RECORD_PATH,
        "sha256": REGISTRATION_RECORD_SHA256,
    },
    "registration_receipt": {
        "path": REGISTRATION_RECEIPT_PATH,
        "sha256": REGISTRATION_RECEIPT_SHA256,
    },
    "exhausted_registration_activation": {
        "path": REGISTRATION_ACTIVATION_PATH,
        "sha256": REGISTRATION_ACTIVATION_SHA256,
    },
    "ingested_fixture": {
        "path": INGESTED_FIXTURE_PATH,
        "sha256": INGESTED_FIXTURE_SHA256,
        "package_id": PACKAGE_ID,
    },
}
_EXPECTED_OUTPUT_POLICY_FIELDS = frozenset(
    {
        "mode",
        "reference_artifact_path",
        "reference_artifact_write",
        "production_controller_import_wired",
        "production_planner_import_wired",
        "controller_or_planner_algorithm_change",
        "kernel_store_write",
        "e_case_write",
        "certificate_generation",
        "certified_stop",
        "claim_lifecycle_mutation",
    }
)
_EXPECTED_STILL_BLOCKED = {
    "second_reference_bind": True,
    "production_controller_import_wiring": True,
    "production_planner_import_wiring": True,
    "controller_or_planner_algorithm_change": True,
    "kernel_store_write": True,
    "e_case_write": True,
    "checker_or_promotion": True,
    "certificate_generation": True,
    "certified_stop": True,
    "si_llm_001_closure": True,
    "catalog_role_credit_l2": True,
    "part_b_elevation": True,
    "m2_fit": True,
    "four_family_llm_finetune": True,
}
_EXPECTED_REGISTRATION_SIDE_EFFECTS = {
    "kernel_store_write": False,
    "e_case_write": False,
    "checker_or_promotion": False,
    "certificate_generation": False,
    "certified_stop": False,
    "si_llm_001_closure": False,
    "catalog_role_credit_l2_change": False,
    "m2_fit": False,
    "four_family_llm_finetune": False,
}
_EXPECTED_REFERENCE_SIDE_EFFECTS = {
    "claim_values_copied": False,
    "raw_paths_copied": False,
    "labels_or_outcomes_copied": False,
    "controller_or_planner_algorithm_changed": False,
    "production_controller_import_wired": False,
    "production_planner_import_wired": False,
    "kernel_store_write": False,
    "e_case_write": False,
    "checker_or_promotion": False,
    "certificate_generation": False,
    "certified_stop": False,
    "si_llm_001_closure": False,
    "catalog_role_credit_l2_change": False,
    "part_b_elevation": False,
    "m2_fit": False,
    "four_family_llm_finetune": False,
}


class ClaimIDControlLoopReferenceError(ValueError):
    """Raised when a reference bind request fails a closed boundary."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def verify_control_loop_reference_pins(repo_root: Path) -> None:
    """Verify the design, completed registration, and handoff dependency pins."""

    repo_root = repo_root.resolve()
    for relative_path, expected_sha in (
        (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
        (REGISTRATION_RECORD_PATH, REGISTRATION_RECORD_SHA256),
        (REGISTRATION_RECEIPT_PATH, REGISTRATION_RECEIPT_SHA256),
        (REGISTRATION_ACTIVATION_PATH, REGISTRATION_ACTIVATION_SHA256),
        (REGISTRATION_EXECUTOR_PATH, REGISTRATION_EXECUTOR_SHA256),
        (HANDOFF_DESIGN_PATH, HANDOFF_DESIGN_SHA256),
        (EFFECTIVE_CONSUMER_CONTRACT_PATH, EFFECTIVE_CONSUMER_CONTRACT_SHA256),
        (SCHEMA_PATH, SCHEMA_SHA256),
        (INGESTED_FIXTURE_PATH, INGESTED_FIXTURE_SHA256),
        (INGESTION_RECEIPT_PATH, INGESTION_RECEIPT_SHA256),
    ):
        _verify_pin(repo_root, relative_path, expected_sha)
    _validate_authority_design(_load_json(repo_root / AUTHORITY_DESIGN_PATH))
    _validate_handoff_design_semantics(_load_json(repo_root / HANDOFF_DESIGN_PATH))
    _validate_registration_activation(
        _load_json(repo_root / REGISTRATION_ACTIVATION_PATH)
    )
    verify_mainline_handoff_pins(repo_root)
    _require_registration_switch_disabled()


def bind_claim_id_control_loop_reference(
    registration_record_bytes: bytes | None,
    registration_receipt_bytes: bytes | None,
    *,
    repo_root: Path,
    activation_path: Path | None = None,
) -> dict[str, Any]:
    """Return one versioned opaque Claim-ID reference in memory."""

    if activation_path is None:
        raise ClaimIDControlLoopReferenceError(
            "missing_activation", "an activated single-use reference authority is required"
        )
    repo_root = repo_root.resolve()
    verify_control_loop_reference_pins(repo_root)
    activation_bytes = _read_bytes(activation_path, "activation", 256 * 1024)
    activation = _decode_json_bytes(activation_bytes, "activation")
    activation_sha256 = hashlib.sha256(activation_bytes).hexdigest()
    binder_sha256 = _sha256(repo_root / BINDER_PATH)
    authority = _validate_activation(
        activation,
        repo_root=repo_root,
        binder_sha256=binder_sha256,
    )

    if registration_record_bytes is None:
        raise ClaimIDControlLoopReferenceError(
            "missing_registration", "the exact registration record is required"
        )
    if registration_receipt_bytes is None:
        raise ClaimIDControlLoopReferenceError(
            "missing_registration_receipt", "the exact registration receipt is required"
        )
    _require_bytes_pin(
        registration_record_bytes,
        REGISTRATION_RECORD_SHA256,
        "registration_record_pin",
    )
    _require_bytes_pin(
        registration_receipt_bytes,
        REGISTRATION_RECEIPT_SHA256,
        "registration_receipt_pin",
    )
    record = _decode_json_bytes(registration_record_bytes, "registration_record")
    receipt = _decode_json_bytes(registration_receipt_bytes, "registration_receipt")
    _validate_registration_record(record)
    _validate_registration_receipt(receipt, record)

    package_bytes = (repo_root / INGESTED_FIXTURE_PATH).read_bytes()
    ingestion_receipt_bytes = (repo_root / INGESTION_RECEIPT_PATH).read_bytes()
    expected_handoff = build_claim_id_mainline_handoff(
        package_bytes,
        ingestion_receipt_bytes,
        repo_root=repo_root,
        consumer_contract_ref={
            "effective_artifact_id": EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
            "effective_version": EFFECTIVE_CONSUMER_CONTRACT_VERSION,
            "effective_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
        },
    )
    _require_exact_mapping(
        record.get("handoff_reference"),
        expected_handoff,
        "registration_record.handoff_reference",
        "registration_binding",
    )
    package = _decode_json_bytes(package_bytes, "ingested_fixture")
    claim_ids = _extract_and_validate_claim_ids(package)
    reference = _build_reference(
        claim_ids,
        authority=authority,
        activation_sha256=activation_sha256,
        binder_sha256=binder_sha256,
    )
    _assert_reference_has_no_forbidden_payload(reference)
    return {
        "reference_artifact": reference,
        "activation_sha256_before": activation_sha256,
        "execute_ledger_after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
    }


def _validate_authority_design(value: Any) -> None:
    design = _require_mapping(value, "authority_design", "authority_design")
    for field, expected in (
        ("artifact_id", AUTHORITY_DESIGN_ARTIFACT_ID),
        ("artifact_type", "claim_id_control_loop_reference_wiring_single_execute_authority_design"),
        ("version", "0.1"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", AUTHORITY_DESIGN_STATUS),
    ):
        _require_constant(
            design.get(field), expected, f"authority_design.{field}", "authority_design"
        )
    current = _require_mapping(
        design.get("current_authorization_state"),
        "authority_design.current_authorization_state",
        "authority_design",
    )
    for field, expected in (
        ("activated", False),
        ("authorized", 0),
        ("maximum", 0),
        ("started", 0),
        ("consumed", 0),
        ("remaining", 0),
        ("runtime_control_loop_reference_authorized", False),
        ("runtime_planner_reference_authorized", False),
        ("production_controller_import_wired", False),
        ("production_planner_import_wired", False),
    ):
        _require_constant(
            current.get(field),
            expected,
            f"authority_design.current_authorization_state.{field}",
            "authority_design",
        )
    future = _require_mapping(
        design.get("future_activation_shape"),
        "authority_design.future_activation_shape",
        "authority_design",
    )
    _require_constant(
        future.get("status"),
        ACTIVATION_STATUS,
        "authority_design.future_activation_shape.status",
        "authority_design",
    )
    _require_exact_mapping(
        future.get("execute_ledger"),
        _EXPECTED_LEDGER_BEFORE,
        "authority_design.future_activation_shape.execute_ledger",
        "authority_design",
    )


def _validate_handoff_design_semantics(value: Any) -> None:
    design = _require_mapping(value, "handoff_design", "handoff_design")
    semantics = _require_mapping(
        design.get("control_loop_and_planner_reference_semantics"),
        "handoff_design.control_loop_and_planner_reference_semantics",
        "handoff_design",
    )
    for field, expected in (
        ("reference_mode", REFERENCE_MODE),
        ("claim_payload_copy_into_control_state", False),
        ("claim_id_mint_during_handoff", False),
        ("claim_id_admission_during_handoff", False),
        ("kernel_state_transition_during_handoff", False),
        ("e_case_or_certificate_write_during_handoff", False),
    ):
        _require_constant(
            semantics.get(field),
            expected,
            f"handoff_design.control_loop_and_planner_reference_semantics.{field}",
            "handoff_design",
        )


def _validate_registration_activation(value: Any) -> None:
    activation = _require_mapping(
        value, "registration_activation", "registration_activation"
    )
    _require_exact_mapping(
        activation.get("execute_ledger"),
        _EXPECTED_REGISTRATION_LEDGER_EXHAUSTED,
        "registration_activation.execute_ledger",
        "registration_not_completed",
    )
    audit = _require_mapping(
        activation.get("execution_audit"),
        "registration_activation.execution_audit",
        "registration_not_completed",
    )
    _require_constant(
        audit.get("executor_invocation_count"),
        1,
        "registration_activation.execution_audit.executor_invocation_count",
        "registration_not_completed",
    )
    registration_record = _require_mapping(
        audit.get("registration_record"),
        "registration_activation.execution_audit.registration_record",
        "registration_binding",
    )
    registration_receipt = _require_mapping(
        audit.get("sanitized_receipt"),
        "registration_activation.execution_audit.sanitized_receipt",
        "registration_binding",
    )
    for observed, expected, field in (
        (registration_record.get("sha256"), REGISTRATION_RECORD_SHA256, "registration_record.sha256"),
        (registration_receipt.get("sha256"), REGISTRATION_RECEIPT_SHA256, "sanitized_receipt.sha256"),
    ):
        _require_constant(
            observed,
            expected,
            f"registration_activation.execution_audit.{field}",
            "registration_binding",
        )


def _validate_activation(
    value: Any,
    *,
    repo_root: Path,
    binder_sha256: str,
) -> dict[str, Any]:
    activation = _require_mapping(value, "activation", "activation_shape")
    _reject_secret_keys(activation)
    if set(activation) != _EXPECTED_ACTIVATION_FIELDS:
        raise ClaimIDControlLoopReferenceError(
            "activation_shape", "activation fields are not canonical"
        )
    artifact_id = activation.get("artifact_id")
    if not isinstance(artifact_id, str) or not _ACTIVATION_ID_PATTERN.fullmatch(
        artifact_id
    ):
        raise ClaimIDControlLoopReferenceError(
            "activation_shape", "activation artifact id is invalid"
        )
    for field, expected in (
        ("artifact_type", "claim_id_control_loop_reference_wiring_single_execute_activation"),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", ACTIVATION_STATUS),
    ):
        _require_constant(
            activation.get(field), expected, f"activation.{field}", "not_activated"
        )
    _require_exact_mapping(
        activation.get("authority_design"),
        {
            "artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
            "path": AUTHORITY_DESIGN_PATH,
            "sha256": AUTHORITY_DESIGN_SHA256,
            "status": AUTHORITY_DESIGN_STATUS,
        },
        "activation.authority_design",
        "authority_design_pin",
    )
    _require_exact_mapping(
        activation.get("target"),
        _EXPECTED_TARGET,
        "activation.target",
        "activation_target",
    )
    expected_pins = dict(_EXPECTED_STATIC_PINS)
    expected_pins["reference_binder_sha256"] = binder_sha256
    _require_exact_mapping(
        activation.get("pinned_hashes"),
        expected_pins,
        "activation.pinned_hashes",
        "activation_pin",
    )
    _require_exact_mapping(
        activation.get("selected_input"),
        _EXPECTED_SELECTED_INPUT,
        "activation.selected_input",
        "selected_input",
    )
    _require_exact_mapping(
        activation.get("execute_ledger"),
        _EXPECTED_LEDGER_BEFORE,
        "activation.execute_ledger",
        "activation_ledger",
    )
    if activation.get("execution_audit") is not None:
        raise ClaimIDControlLoopReferenceError(
            "activation_ledger", "activation already contains execution audit data"
        )
    _validate_output_policy(activation.get("output_policy"), repo_root)
    _require_exact_mapping(
        activation.get("still_blocked"),
        _EXPECTED_STILL_BLOCKED,
        "activation.still_blocked",
        "activation_boundary",
    )
    return copy.deepcopy(dict(activation))


def _validate_output_policy(value: Any, repo_root: Path) -> None:
    policy = _require_mapping(value, "activation.output_policy", "output_policy")
    if set(policy) != _EXPECTED_OUTPUT_POLICY_FIELDS:
        raise ClaimIDControlLoopReferenceError(
            "output_policy", "output policy fields are not canonical"
        )
    for field, expected in (
        ("mode", "versioned_reference_contract_only"),
        ("reference_artifact_write", True),
        ("production_controller_import_wired", False),
        ("production_planner_import_wired", False),
        ("controller_or_planner_algorithm_change", False),
        ("kernel_store_write", False),
        ("e_case_write", False),
        ("certificate_generation", False),
        ("certified_stop", False),
        ("claim_lifecycle_mutation", False),
    ):
        _require_constant(
            policy.get(field), expected, f"activation.output_policy.{field}", "output_policy"
        )
    _validate_output_path(policy.get("reference_artifact_path"), repo_root)


def _validate_output_path(value: Any, repo_root: Path) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ClaimIDControlLoopReferenceError(
            "output_policy", "reference artifact path must use POSIX separators"
        )
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ClaimIDControlLoopReferenceError(
            "output_policy", "reference artifact path must remain repository-relative"
        )
    if not (
        value.startswith("docs/llm-editor/fixtures/claim-id-control-loop-reference/")
        or value.startswith(".tmp/compiler-contract/")
    ):
        raise ClaimIDControlLoopReferenceError(
            "output_policy", "reference artifact path is outside allowed audit roots"
        )
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ClaimIDControlLoopReferenceError(
            "output_policy", "reference artifact path escapes the repository"
        ) from exc
    if resolved.exists():
        raise ClaimIDControlLoopReferenceError(
            "output_exists", "reference artifact already exists"
        )
    return resolved


def _validate_registration_record(value: Any) -> None:
    record = _require_mapping(value, "registration_record", "registration_shape")
    for field, expected in (
        ("record_version", "claim-id-mainline-registration-record-v0.1"),
        ("status", "registered_exact_read_only_handoff_reference_under_single_execute_authority"),
        ("registration_scope", "versioned_audit_registration_only_not_control_loop_wiring"),
        ("surface_id", SURFACE_ID),
        ("package_id", PACKAGE_ID),
    ):
        _require_constant(
            record.get(field), expected, f"registration_record.{field}", "registration_not_completed"
        )
    _require_exact_mapping(
        record.get("side_effects"),
        _EXPECTED_REGISTRATION_SIDE_EFFECTS,
        "registration_record.side_effects",
        "registration_side_effect",
    )
    effect = _require_mapping(
        record.get("registration_effect"),
        "registration_record.registration_effect",
        "registration_not_completed",
    )
    for field, expected in (
        ("exact_pinned_handoff_reference_recorded", True),
        ("global_permanent_registration_switch_observed", False),
        ("global_permanent_registration_switch_mutated", False),
        ("production_control_loop_wiring", False),
        ("planner_wiring", False),
    ):
        _require_constant(
            effect.get(field),
            expected,
            f"registration_record.registration_effect.{field}",
            "registration_not_completed",
        )


def _validate_registration_receipt(
    value: Any,
    registration_record: Mapping[str, Any],
) -> None:
    receipt = _require_mapping(value, "registration_receipt", "registration_receipt")
    for field, expected in (
        ("receipt_version", "claim-id-mainline-registration-receipt-v0.1"),
        ("receipt_scope", "sanitized_versioned_audit_registration_only"),
        ("decision", "registered_once_under_single_execute_authority"),
    ):
        _require_constant(
            receipt.get(field), expected, f"registration_receipt.{field}", "registration_receipt"
        )
    _require_exact_mapping(
        receipt.get("side_effects"),
        _EXPECTED_REGISTRATION_SIDE_EFFECTS,
        "registration_receipt.side_effects",
        "registration_side_effect",
    )
    switch = _require_mapping(
        receipt.get("registration_switch_boundary"),
        "registration_receipt.registration_switch_boundary",
        "registration_receipt",
    )
    for field, expected in (
        ("observed_value", False),
        ("mutated_during_execution", False),
        ("permanent_registration_enabled", False),
    ):
        _require_constant(
            switch.get(field),
            expected,
            f"registration_receipt.registration_switch_boundary.{field}",
            "registration_receipt",
        )
    output = _require_mapping(
        receipt.get("output"), "registration_receipt.output", "registration_receipt"
    )
    _require_constant(
        output.get("registration_record_canonical_sha256"),
        _canonical_json_sha256(registration_record),
        "registration_receipt.output.registration_record_canonical_sha256",
        "registration_binding",
    )


def _extract_and_validate_claim_ids(package: Mapping[str, Any]) -> list[str]:
    claims = package.get("claims")
    if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes)):
        raise ClaimIDControlLoopReferenceError(
            "claim_identity", "ingested fixture claims must be an array"
        )
    claim_ids: list[str] = []
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise ClaimIDControlLoopReferenceError(
                "claim_identity", "ingested fixture claim must be an object"
            )
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not _CLAIM_ID_PATTERN.fullmatch(claim_id):
            raise ClaimIDControlLoopReferenceError(
                "claim_identity", "ingested fixture contains an invalid Claim-ID"
            )
        claim_ids.append(claim_id)
    if len(claim_ids) != CLAIM_COUNT or len(set(claim_ids)) != CLAIM_COUNT:
        raise ClaimIDControlLoopReferenceError(
            "claim_identity", "Claim-ID list count or uniqueness is invalid"
        )
    actual_sha = hashlib.sha256(
        json.dumps(
            claim_ids,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    if actual_sha != CLAIM_ID_LIST_SHA256:
        raise ClaimIDControlLoopReferenceError(
            "claim_identity", "Claim-ID list digest does not match the registered handoff"
        )
    return claim_ids


def _build_reference(
    claim_ids: list[str],
    *,
    authority: Mapping[str, Any],
    activation_sha256: str,
    binder_sha256: str,
) -> dict[str, Any]:
    reference_digest = hashlib.sha256(
        "\0".join(
            (
                "claim-id-control-loop-reference-v0.1",
                activation_sha256,
                REGISTRATION_RECORD_SHA256,
                CLAIM_ID_LIST_SHA256,
            )
        ).encode("utf-8")
    ).hexdigest()
    return {
        "reference_version": "claim-id-control-loop-reference-v0.1",
        "reference_id": f"clr_{reference_digest[:32]}",
        "status": REFERENCE_STATUS,
        "reference_mode": REFERENCE_MODE,
        "surface_id": SURFACE_ID,
        "package_id": PACKAGE_ID,
        "claim_ids": list(claim_ids),
        "claim_reference": {
            "claims_content_hash": CLAIMS_CONTENT_HASH,
            "full_claim_id_list_sha256": CLAIM_ID_LIST_SHA256,
            "claim_count": CLAIM_COUNT,
        },
        "claim_id_state": "minted_opaque",
        "admission_state": "admitted_under_separate_authority",
        "kernel_state": "ingested_under_separate_authority",
        "consumer_contract_ref": {
            "effective_artifact_id": EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
            "effective_version": EFFECTIVE_CONSUMER_CONTRACT_VERSION,
            "effective_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
        },
        "registration_ref": {
            "registration_record_sha256": REGISTRATION_RECORD_SHA256,
            "registration_receipt_sha256": REGISTRATION_RECEIPT_SHA256,
            "exhausted_registration_activation_sha256": REGISTRATION_ACTIVATION_SHA256,
            "registration_executor_sha256": REGISTRATION_EXECUTOR_SHA256,
            "wiring_authority_artifact_id": authority["artifact_id"],
            "wiring_activation_sha256": activation_sha256,
            "reference_binder_sha256": binder_sha256,
        },
        "runtime_reference_boundary": {
            "runtime_control_loop_reference_authorized": True,
            "runtime_planner_reference_authorized": True,
            "read_only_reference_only": True,
            "production_controller_import_wired": False,
            "production_planner_import_wired": False,
            "controller_or_planner_algorithm_changed": False,
            "evidence_sufficiency_asserted": False,
            "certified_stop_asserted": False,
        },
        "execute_ledger_after": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
        "side_effects": copy.deepcopy(_EXPECTED_REFERENCE_SIDE_EFFECTS),
    }


def _assert_reference_has_no_forbidden_payload(value: Mapping[str, Any]) -> None:
    forbidden_keys = {
        "value",
        "claim_value",
        "claim_values",
        "raw_path",
        "filesystem_path",
        "archive_member_path",
        "label",
        "labels",
        "outcome",
        "outcomes",
        "oracle",
        "mask",
        "certificate",
        "e_case",
        "truth_status",
    }

    def walk(child: Any) -> None:
        if isinstance(child, Mapping):
            for key, nested in child.items():
                if str(key).lower() in forbidden_keys:
                    raise ClaimIDControlLoopReferenceError(
                        "forbidden_payload", f"forbidden reference field: {key}"
                    )
                walk(nested)
        elif isinstance(child, list):
            for nested in child:
                walk(nested)

    walk(value)


def _require_registration_switch_disabled() -> None:
    if handoff_module.PRODUCTION_REGISTRATION_ENABLED is not False:
        raise ClaimIDControlLoopReferenceError(
            "registration_switch",
            "PRODUCTION_REGISTRATION_ENABLED must remain False",
        )


def _read_bytes(path: Path, kind: str, maximum: int = _MAX_INPUT_BYTES) -> bytes:
    try:
        data = Path(path).read_bytes()
    except (OSError, TypeError) as exc:
        raise ClaimIDControlLoopReferenceError(
            f"{kind}_unavailable", f"{kind} could not be read"
        ) from exc
    if len(data) > maximum:
        raise ClaimIDControlLoopReferenceError(
            f"{kind}_shape", f"{kind} exceeds the size limit"
        )
    return data


def _decode_json_bytes(value: bytes, kind: str) -> dict[str, Any]:
    if not isinstance(value, bytes):
        raise ClaimIDControlLoopReferenceError(
            f"{kind}_type", f"{kind} must be bytes"
        )
    if len(value) > _MAX_INPUT_BYTES:
        raise ClaimIDControlLoopReferenceError(
            f"{kind}_shape", f"{kind} exceeds the size limit"
        )
    try:
        decoded = value.decode("utf-8")
        parsed = json.loads(decoded, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ClaimIDControlLoopReferenceError(
            f"{kind}_json", f"{kind} must be strict UTF-8 JSON"
        ) from exc
    if not isinstance(parsed, dict):
        raise ClaimIDControlLoopReferenceError(
            f"{kind}_shape", f"{kind} must be a JSON object"
        )
    return parsed


def _reject_secret_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")
            parts = set(normalized.split("_"))
            if parts.intersection(
                {"secret", "password", "passwd", "credential", "token", "hmac", "key"}
            ):
                raise ClaimIDControlLoopReferenceError(
                    "secret_field", f"secret-like field is forbidden at {'.'.join(path + (str(key),))}"
                )
            _reject_secret_keys(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_keys(child, path + (str(index),))


def _require_bytes_pin(value: bytes, expected_sha: str, code: str) -> None:
    if not isinstance(value, bytes) or hashlib.sha256(value).hexdigest() != expected_sha:
        raise ClaimIDControlLoopReferenceError(code, "input bytes do not match the frozen pin")


def _require_mapping(value: Any, field: str, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaimIDControlLoopReferenceError(code, f"{field} must be an object")
    return value


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    code: str,
) -> None:
    if not isinstance(value, Mapping) or dict(value) != dict(expected):
        raise ClaimIDControlLoopReferenceError(
            code, f"{field} does not match the frozen shape"
        )


def _require_constant(
    value: Any,
    expected: Any,
    field: str,
    code: str,
) -> None:
    if value != expected or type(value) is not type(expected):
        raise ClaimIDControlLoopReferenceError(code, f"{field} must equal {expected!r}")


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise ClaimIDControlLoopReferenceError(
            "pin_missing", f"pinned artifact is missing: {relative_path}"
        )
    if _sha256(path) != expected_sha:
        raise ClaimIDControlLoopReferenceError(
            "pin_mismatch", f"pinned artifact mismatch: {relative_path}"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return _decode_json_bytes(path.read_bytes(), path.as_posix())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result
