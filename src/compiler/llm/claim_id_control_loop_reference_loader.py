"""Fail-closed loader for a controller's read-only Claim-ID provenance import.

The loader accepts only the exact versioned control-loop reference and a
separate, unconsumed single-use import authority.  It returns an immutable
view.  It does not add Claim-IDs to case-local evidence state, invoke planning,
or write Kernel/E_case/certificate/L2 surfaces.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any
from collections.abc import Mapping, Sequence

from src.compiler.llm import claim_id_mainline_handoff as handoff_module


AUTHORITY_BASE_COMMIT = "424ec1305f827d28881498315cba932ea2732dab"
AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-controller-import-wiring-"
    "single-execute-authority-design-v0.1-20260725.json"
)
AUTHORITY_DESIGN_SHA256 = (
    "68dd4deecdd9f980813defeae65c107fff0646b14f0c64211659b2d29a5044b3"
)
AUTHORITY_DESIGN_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-claim-id-controller-import-wiring-"
    "single-execute-authority-design-v0.1-20260725"
)
AUTHORITY_DESIGN_STATUS = (
    "design_only_claim_id_controller_import_wiring_authority_not_activated"
)
ACTIVATION_STATUS = (
    "activated_single_claim_id_controller_import_wiring_execute_authorized"
)
LOADER_PATH = "src/compiler/llm/claim_id_control_loop_reference_loader.py"
CONTROLLER_ENTRYPOINT_PATH = "09-experiments/scripts/run_mvp.py"
REFERENCE_PATH = (
    "docs/llm-editor/fixtures/claim-id-control-loop-reference/"
    "project05-depth2-public-v0.1/reference.json"
)
REFERENCE_SHA256 = (
    "db4343dbc598e3da3bd4a8bfd9e9ddb1a22a71d9bde889f953c0ceb244e8206d"
)
REFERENCE_BINDER_PATH = (
    "src/compiler/llm/claim_id_control_loop_reference_binder.py"
)
REFERENCE_BINDER_SHA256 = (
    "df7e900c48f9d0b7a35e3d9c8b45cf964ff724cfe48bfec4668776b66780533d"
)
REFERENCE_BINDER_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-control-loop-reference-wiring-"
    "single-execute-authority-design-v0.1-20260725.json"
)
REFERENCE_BINDER_DESIGN_SHA256 = (
    "cf4a6fcd9faa6d6dadf3ca6b4caa5da1d80d96d10c6ecdef9a36ed7845ad7856"
)
REFERENCE_BINDER_ACTIVATION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-control-loop-reference-wiring-"
    "single-execute-activation-v0.1-20260725.json"
)
REFERENCE_BINDER_ACTIVATION_SHA256 = (
    "428fc4552768b1d1f98e1336a1a7c74be8f7ad0e16b0eed42f0b1defb89fa4f2"
)
REGISTRATION_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-production-claim-id-mainline-registration-"
    "single-execute-authority-design-v0.1-20260725.json"
)
REGISTRATION_DESIGN_SHA256 = (
    "ad6b95adc6b515649e9dd7886ea9530d33f931559bfff70f97f07576f3d7acda"
)
REGISTRATION_EXECUTOR_PATH = (
    "src/compiler/llm/claim_id_mainline_registration_executor.py"
)
REGISTRATION_EXECUTOR_SHA256 = (
    "1e47013d14f347b15bffc74a8e74746f52ae8ab7345eed77ee0cfd95cfd61182"
)
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
HANDOFF_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-mainline-handoff-design-v0.1-20260724.json"
)
HANDOFF_DESIGN_SHA256 = (
    "cc6829709b359e2cac72ad30c00ac78ce7e2989a66f2b2e20d7eac4b98452e80"
)
EFFECTIVE_CONSUMER_CONTRACT_PATH = (
    "docs/kernel/"
    "kernel-v0.8-shared-claim-ir-consumer-contract-effective-v0.1-20260725.json"
)
EFFECTIVE_CONSUMER_CONTRACT_SHA256 = (
    "a2a176fdeb2b93205a7f5e11c7c096236e2dc582d1c31f8f4a1534866c008d63"
)
EXTERNAL_ENVELOPE_PATH = "schemas/claim-ir-external-envelope.schema.json"
EXTERNAL_ENVELOPE_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
RECEIPT_PATH = (
    "docs/llm-editor/fixtures/claim-id-controller-import-wiring/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)
SURFACE_ID = "project05_depth2_public"
PACKAGE_ID = "pkg_73d77b55ef6a517a0dc528f7f3a89bd9"
REFERENCE_MODE = "opaque_claim_identity_read_only"
REFERENCE_STATUS = "bound_registered_claim_id_reference_read_only"
CLAIM_COUNT = 41
CLAIMS_CONTENT_HASH = (
    "594c0ec4c4533b1fae76ce57579cf52c783e61fc6b191d9807ce9751e5d473f1"
)
CLAIM_ID_LIST_SHA256 = (
    "11ef0f4672d9f43357639e46c19b27474ddcdf40daffb9acb93af9c810d008a4"
)

_ACTIVATION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
_CLAIM_ID_PATTERN = re.compile(r"^clm_[A-Za-z0-9_-]+$")
_MAX_JSON_BYTES = 2 * 1024 * 1024
_LEDGER_BEFORE = {
    "authorized": 1,
    "maximum": 1,
    "started": 0,
    "consumed": 0,
    "remaining": 1,
    "retry": False,
    "resume": False,
    "fallback": False,
}
_LEDGER_AFTER = {
    "authorized": 1,
    "maximum": 1,
    "started": 1,
    "consumed": 1,
    "remaining": 0,
    "retry": False,
    "resume": False,
    "fallback": False,
}
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
_EXPECTED_REFERENCE_FIELDS = frozenset(
    {
        "reference_version",
        "reference_id",
        "status",
        "reference_mode",
        "surface_id",
        "package_id",
        "claim_ids",
        "claim_reference",
        "claim_id_state",
        "admission_state",
        "kernel_state",
        "consumer_contract_ref",
        "registration_ref",
        "runtime_reference_boundary",
        "side_effects",
    }
)
_EXPECTED_TARGET = {
    "surface_id": SURFACE_ID,
    "package_id": PACKAGE_ID,
    "reference_mode": REFERENCE_MODE,
    "controller_entrypoint": CONTROLLER_ENTRYPOINT_PATH,
    "controller_attachment_field": "claim_id_mainline_reference",
    "execution_scope": "single_controller_summary_provenance_import_only",
}
_STATIC_PINS = {
    "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
    "bound_control_loop_reference_sha256": REFERENCE_SHA256,
    "reference_binder_sha256": REFERENCE_BINDER_SHA256,
    "reference_binder_authority_design_sha256": REFERENCE_BINDER_DESIGN_SHA256,
    "exhausted_reference_binder_activation_sha256": (
        REFERENCE_BINDER_ACTIVATION_SHA256
    ),
    "registration_authority_design_sha256": REGISTRATION_DESIGN_SHA256,
    "registration_executor_sha256": REGISTRATION_EXECUTOR_SHA256,
    "registration_record_sha256": REGISTRATION_RECORD_SHA256,
    "registration_receipt_sha256": REGISTRATION_RECEIPT_SHA256,
    "exhausted_registration_activation_sha256": REGISTRATION_ACTIVATION_SHA256,
    "mainline_handoff_design_sha256": HANDOFF_DESIGN_SHA256,
    "effective_consumer_contract_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    "external_envelope_schema_sha256": EXTERNAL_ENVELOPE_SHA256,
}
_EXPECTED_SELECTED_INPUT = {
    "bound_control_loop_reference": {
        "path": REFERENCE_PATH,
        "sha256": REFERENCE_SHA256,
        "surface_id": SURFACE_ID,
        "package_id": PACKAGE_ID,
        "claim_count": CLAIM_COUNT,
    }
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "single_controller_summary_provenance_import_only",
    "controller_entrypoint": CONTROLLER_ENTRYPOINT_PATH,
    "controller_attachment_field": "claim_id_mainline_reference",
    "versioned_receipt_path": RECEIPT_PATH,
    "versioned_receipt_write": True,
    "production_controller_import_wired_after_success": True,
    "production_planner_import_wired": False,
    "planner_or_action_selection_algorithm_change": False,
    "claim_lifecycle_mutation": False,
    "kernel_store_write": False,
    "e_case_write": False,
    "certificate_generation": False,
    "certified_stop": False,
}
_EXPECTED_STILL_BLOCKED = {
    "second_controller_import_under_same_activation": True,
    "production_planner_import_wiring": True,
    "planner_or_action_selection_algorithm_change": True,
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
_EXPECTED_RUNTIME_BOUNDARY = {
    "runtime_control_loop_reference_authorized": True,
    "runtime_planner_reference_authorized": True,
    "read_only_reference_only": True,
    "production_controller_import_wired": False,
    "production_planner_import_wired": False,
    "controller_or_planner_algorithm_changed": False,
    "evidence_sufficiency_asserted": False,
    "certified_stop_asserted": False,
}
_EXPECTED_SIDE_EFFECTS = {
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
_FORBIDDEN_REFERENCE_KEYS = frozenset(
    {
        "value",
        "values",
        "raw_path",
        "raw_paths",
        "payload",
        "payload_bytes",
        "label",
        "labels",
        "outcome",
        "outcomes",
        "oracle",
        "mask",
        "hidden_ids",
        "required_claim_ids",
        "visible_claim_ids",
        "select_action",
        "certificate",
        "e_case",
    }
)


class ClaimIDControlLoopReferenceLoadError(ValueError):
    """Raised when a controller provenance import fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ClaimIDControlLoopReferenceView:
    """Immutable controller-facing view of the opaque Claim-ID reference."""

    reference_id: str
    surface_id: str
    package_id: str
    claim_ids: tuple[str, ...]
    claim_reference: Mapping[str, Any]
    consumer_contract_ref: Mapping[str, Any]
    registration_ref: Mapping[str, Any]
    source_reference_sha256: str

    def to_provenance(self) -> dict[str, Any]:
        """Return the additive JSON projection allowed on result summaries."""

        return {
            "reference_mode": REFERENCE_MODE,
            "read_only": True,
            "reference_id": self.reference_id,
            "surface_id": self.surface_id,
            "package_id": self.package_id,
            "claim_ids": list(self.claim_ids),
            "claim_reference": dict(self.claim_reference),
            "consumer_contract_ref": dict(self.consumer_contract_ref),
            "registration_ref": dict(self.registration_ref),
            "source_reference_sha256": self.source_reference_sha256,
        }


@dataclass(frozen=True)
class ClaimIDControllerImport:
    """One authorized in-memory import result and its required ledger terminal."""

    view: ClaimIDControlLoopReferenceView
    activation_sha256_before: str
    execute_ledger_after_required: Mapping[str, Any]


def verify_controller_import_pins(repo_root: Path) -> None:
    """Verify every frozen dependency without enabling production registration."""

    repo_root = repo_root.resolve()
    for relative_path, expected_sha in (
        (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
        (REFERENCE_PATH, REFERENCE_SHA256),
        (REFERENCE_BINDER_PATH, REFERENCE_BINDER_SHA256),
        (REFERENCE_BINDER_DESIGN_PATH, REFERENCE_BINDER_DESIGN_SHA256),
        (REFERENCE_BINDER_ACTIVATION_PATH, REFERENCE_BINDER_ACTIVATION_SHA256),
        (REGISTRATION_DESIGN_PATH, REGISTRATION_DESIGN_SHA256),
        (REGISTRATION_EXECUTOR_PATH, REGISTRATION_EXECUTOR_SHA256),
        (REGISTRATION_RECORD_PATH, REGISTRATION_RECORD_SHA256),
        (REGISTRATION_RECEIPT_PATH, REGISTRATION_RECEIPT_SHA256),
        (REGISTRATION_ACTIVATION_PATH, REGISTRATION_ACTIVATION_SHA256),
        (HANDOFF_DESIGN_PATH, HANDOFF_DESIGN_SHA256),
        (EFFECTIVE_CONSUMER_CONTRACT_PATH, EFFECTIVE_CONSUMER_CONTRACT_SHA256),
        (EXTERNAL_ENVELOPE_PATH, EXTERNAL_ENVELOPE_SHA256),
    ):
        _verify_pin(repo_root, relative_path, expected_sha)
    _validate_authority_design(_load_json(repo_root / AUTHORITY_DESIGN_PATH))
    _validate_exhausted_activation(
        _load_json(repo_root / REFERENCE_BINDER_ACTIVATION_PATH),
        "reference_binder_activation",
    )
    _validate_exhausted_activation(
        _load_json(repo_root / REGISTRATION_ACTIVATION_PATH),
        "registration_activation",
    )
    if handoff_module.PRODUCTION_REGISTRATION_ENABLED is not False:
        raise ClaimIDControlLoopReferenceLoadError(
            "registration_switch",
            "PRODUCTION_REGISTRATION_ENABLED must remain False",
        )


def load_claim_id_control_loop_reference(
    reference_path: Path | None,
    *,
    repo_root: Path,
    activation_path: Path | None = None,
) -> ClaimIDControllerImport:
    """Load the exact pinned reference once under a separate import authority."""

    if activation_path is None:
        raise ClaimIDControlLoopReferenceLoadError(
            "missing_activation",
            "an activated single-use controller import authority is required",
        )
    if reference_path is None:
        raise ClaimIDControlLoopReferenceLoadError(
            "missing_reference", "the bound control-loop reference is required"
        )
    repo_root = repo_root.resolve()
    verify_controller_import_pins(repo_root)
    expected_reference_path = (repo_root / REFERENCE_PATH).resolve()
    if reference_path.resolve() != expected_reference_path:
        raise ClaimIDControlLoopReferenceLoadError(
            "reference_path", "reference path is not the frozen versioned path"
        )

    activation_bytes = _read_bytes(activation_path, "activation", 256 * 1024)
    activation = _decode_json_bytes(activation_bytes, "activation")
    loader_sha256 = _sha256(repo_root / LOADER_PATH)
    controller_entrypoint_sha256 = _sha256(
        repo_root / CONTROLLER_ENTRYPOINT_PATH
    )
    _validate_activation(
        activation,
        loader_sha256=loader_sha256,
        controller_entrypoint_sha256=controller_entrypoint_sha256,
    )

    reference_bytes = _read_bytes(expected_reference_path, "reference")
    _require_sha256(reference_bytes, REFERENCE_SHA256, "reference_pin")
    reference = _decode_json_bytes(reference_bytes, "reference")
    view = _validate_reference(reference)
    return ClaimIDControllerImport(
        view=view,
        activation_sha256_before=hashlib.sha256(activation_bytes).hexdigest(),
        execute_ledger_after_required=MappingProxyType(dict(_LEDGER_AFTER)),
    )


def _validate_authority_design(value: Any) -> None:
    design = _require_mapping(value, "authority_design", "authority_design")
    for field, expected in (
        ("artifact_id", AUTHORITY_DESIGN_ARTIFACT_ID),
        (
            "artifact_type",
            "claim_id_controller_import_wiring_single_execute_authority_design",
        ),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", AUTHORITY_DESIGN_STATUS),
    ):
        _require_constant(
            design.get(field),
            expected,
            f"authority_design.{field}",
            "authority_design",
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
        ("runtime_controller_reference_import_authorized", False),
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
        _LEDGER_BEFORE,
        "authority_design.future_activation_shape.execute_ledger",
        "authority_design",
    )


def _validate_exhausted_activation(value: Any, field: str) -> None:
    activation = _require_mapping(value, field, "dependency_activation")
    _require_exact_mapping(
        activation.get("execute_ledger"),
        _LEDGER_AFTER,
        f"{field}.execute_ledger",
        "dependency_activation",
    )
    audit = _require_mapping(
        activation.get("execution_audit"),
        f"{field}.execution_audit",
        "dependency_activation",
    )
    invocation_fields = (
        "binder_invocation_count",
        "executor_invocation_count",
    )
    if not any(audit.get(name) == 1 for name in invocation_fields):
        raise ClaimIDControlLoopReferenceLoadError(
            "dependency_activation",
            f"{field} does not record exactly one dependency execution",
        )


def _validate_activation(
    value: Any,
    *,
    loader_sha256: str,
    controller_entrypoint_sha256: str,
) -> None:
    activation = _require_mapping(value, "activation", "activation_shape")
    _reject_secret_keys(activation)
    if set(activation) != _EXPECTED_ACTIVATION_FIELDS:
        raise ClaimIDControlLoopReferenceLoadError(
            "activation_shape", "activation fields are not canonical"
        )
    artifact_id = activation.get("artifact_id")
    if not isinstance(artifact_id, str) or not _ACTIVATION_ID_PATTERN.fullmatch(
        artifact_id
    ):
        raise ClaimIDControlLoopReferenceLoadError(
            "activation_shape", "activation artifact id is invalid"
        )
    for field, expected in (
        (
            "artifact_type",
            "claim_id_controller_import_wiring_single_execute_activation",
        ),
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
    expected_pins = dict(_STATIC_PINS)
    expected_pins["reference_loader_sha256"] = loader_sha256
    expected_pins["controller_entrypoint_sha256"] = (
        controller_entrypoint_sha256
    )
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
        _LEDGER_BEFORE,
        "activation.execute_ledger",
        "activation_ledger",
    )
    _require_exact_mapping(
        activation.get("output_policy"),
        _EXPECTED_OUTPUT_POLICY,
        "activation.output_policy",
        "output_policy",
    )
    _require_exact_mapping(
        activation.get("still_blocked"),
        _EXPECTED_STILL_BLOCKED,
        "activation.still_blocked",
        "activation_boundary",
    )
    if activation.get("execution_audit") is not None:
        raise ClaimIDControlLoopReferenceLoadError(
            "activation_ledger", "activation already contains execution audit data"
        )


def _validate_reference(value: Any) -> ClaimIDControlLoopReferenceView:
    reference = _require_mapping(value, "reference", "reference_shape")
    _reject_forbidden_reference_keys(reference)
    if set(reference) != _EXPECTED_REFERENCE_FIELDS:
        raise ClaimIDControlLoopReferenceLoadError(
            "reference_shape", "reference fields are not canonical"
        )
    for field, expected in (
        ("reference_version", "claim-id-control-loop-reference-v0.1"),
        ("status", REFERENCE_STATUS),
        ("reference_mode", REFERENCE_MODE),
        ("surface_id", SURFACE_ID),
        ("package_id", PACKAGE_ID),
        ("claim_id_state", "minted_opaque"),
        ("admission_state", "admitted_under_separate_authority"),
        ("kernel_state", "ingested_under_separate_authority"),
    ):
        _require_constant(
            reference.get(field), expected, f"reference.{field}", "reference_state"
        )
    reference_id = reference.get("reference_id")
    if not isinstance(reference_id, str) or not reference_id.startswith("clr_"):
        raise ClaimIDControlLoopReferenceLoadError(
            "reference_shape", "reference id is invalid"
        )
    claim_ids_value = reference.get("claim_ids")
    if (
        not isinstance(claim_ids_value, Sequence)
        or isinstance(claim_ids_value, (str, bytes, bytearray))
        or len(claim_ids_value) != CLAIM_COUNT
    ):
        raise ClaimIDControlLoopReferenceLoadError(
            "claim_ids", "reference must contain exactly 41 opaque Claim-IDs"
        )
    claim_ids: list[str] = []
    for claim_id in claim_ids_value:
        if not isinstance(claim_id, str) or not _CLAIM_ID_PATTERN.fullmatch(
            claim_id
        ):
            raise ClaimIDControlLoopReferenceLoadError(
                "claim_ids", "reference contains an invalid opaque Claim-ID"
            )
        claim_ids.append(claim_id)
    if len(set(claim_ids)) != CLAIM_COUNT:
        raise ClaimIDControlLoopReferenceLoadError(
            "claim_ids", "reference Claim-IDs must be unique"
        )
    if _canonical_json_sha256(claim_ids) != CLAIM_ID_LIST_SHA256:
        raise ClaimIDControlLoopReferenceLoadError(
            "claim_ids", "complete ordered Claim-ID list hash is not pinned"
        )
    claim_reference = _require_mapping(
        reference.get("claim_reference"),
        "reference.claim_reference",
        "reference_pin",
    )
    _require_exact_mapping(
        claim_reference,
        {
            "claims_content_hash": CLAIMS_CONTENT_HASH,
            "full_claim_id_list_sha256": CLAIM_ID_LIST_SHA256,
            "claim_count": CLAIM_COUNT,
        },
        "reference.claim_reference",
        "reference_pin",
    )
    consumer_contract_ref = _require_mapping(
        reference.get("consumer_contract_ref"),
        "reference.consumer_contract_ref",
        "reference_pin",
    )
    _require_exact_mapping(
        consumer_contract_ref,
        {
            "effective_artifact_id": (
                "kernel-v0.8-shared-claim-ir-consumer-contract-"
                "effective-v0.1-20260725"
            ),
            "effective_version": "0.1",
            "effective_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
        },
        "reference.consumer_contract_ref",
        "reference_pin",
    )
    registration_ref = _require_mapping(
        reference.get("registration_ref"),
        "reference.registration_ref",
        "reference_pin",
    )
    _require_exact_mapping(
        registration_ref,
        {
            "registration_record_sha256": REGISTRATION_RECORD_SHA256,
            "registration_receipt_sha256": REGISTRATION_RECEIPT_SHA256,
            "exhausted_registration_activation_sha256": (
                REGISTRATION_ACTIVATION_SHA256
            ),
            "registration_executor_sha256": REGISTRATION_EXECUTOR_SHA256,
            "wiring_authority_artifact_id": (
                "claim_id_control_loop_reference_wiring_"
                "single_execute_activation_v0_1_20260725"
            ),
            "wiring_activation_sha256": (
                "eb46658973027e00d089c8d619243bc03bcaf88e507cca28bbc0f8f9056b3457"
            ),
            "reference_binder_sha256": REFERENCE_BINDER_SHA256,
        },
        "reference.registration_ref",
        "reference_pin",
    )
    _require_exact_mapping(
        reference.get("runtime_reference_boundary"),
        _EXPECTED_RUNTIME_BOUNDARY,
        "reference.runtime_reference_boundary",
        "runtime_reference_boundary",
    )
    _require_exact_mapping(
        reference.get("side_effects"),
        _EXPECTED_SIDE_EFFECTS,
        "reference.side_effects",
        "reference_side_effect",
    )
    return ClaimIDControlLoopReferenceView(
        reference_id=reference_id,
        surface_id=SURFACE_ID,
        package_id=PACKAGE_ID,
        claim_ids=tuple(claim_ids),
        claim_reference=MappingProxyType(dict(claim_reference)),
        consumer_contract_ref=MappingProxyType(dict(consumer_contract_ref)),
        registration_ref=MappingProxyType(dict(registration_ref)),
        source_reference_sha256=REFERENCE_SHA256,
    )


def _reject_forbidden_reference_keys(
    value: Any, path: tuple[str, ...] = ()
) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).casefold()
            if key_text in _FORBIDDEN_REFERENCE_KEYS:
                dotted = ".".join((*path, str(key)))
                raise ClaimIDControlLoopReferenceLoadError(
                    "forbidden_reference_payload",
                    f"forbidden reference field: {dotted}",
                )
            _reject_forbidden_reference_keys(item, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, item in enumerate(value):
            _reject_forbidden_reference_keys(item, (*path, str(index)))


def _reject_secret_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).casefold()
            if any(
                token in key_text
                for token in ("secret", "password", "token", "hmac", "key_material")
            ):
                dotted = ".".join((*path, str(key)))
                raise ClaimIDControlLoopReferenceLoadError(
                    "secret_material", f"secret-bearing field is forbidden: {dotted}"
                )
            _reject_secret_keys(item, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, item in enumerate(value):
            _reject_secret_keys(item, (*path, str(index)))


def _read_bytes(path: Path, kind: str, maximum: int = _MAX_JSON_BYTES) -> bytes:
    try:
        value = path.read_bytes()
    except OSError as exc:
        raise ClaimIDControlLoopReferenceLoadError(
            f"{kind}_unavailable", f"{kind} cannot be read"
        ) from exc
    if not value or len(value) > maximum:
        raise ClaimIDControlLoopReferenceLoadError(
            f"{kind}_shape", f"{kind} size is outside the allowed range"
        )
    return value


def _decode_json_bytes(value: bytes, kind: str) -> dict[str, Any]:
    try:
        decoded = json.loads(
            value.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON constant: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ClaimIDControlLoopReferenceLoadError(
            f"{kind}_json", f"{kind} must be strict UTF-8 JSON"
        ) from exc
    if not isinstance(decoded, dict):
        raise ClaimIDControlLoopReferenceLoadError(
            f"{kind}_shape", f"{kind} must be a JSON object"
        )
    return decoded


def _require_mapping(
    value: Any, field: str, code: str
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaimIDControlLoopReferenceLoadError(
            code, f"{field} must be an object"
        )
    return value


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    code: str,
) -> None:
    observed = _require_mapping(value, field, code)
    if dict(observed) != dict(expected):
        raise ClaimIDControlLoopReferenceLoadError(
            code, f"{field} does not match its frozen value"
        )


def _require_constant(
    observed: Any, expected: Any, field: str, code: str
) -> None:
    if observed != expected:
        raise ClaimIDControlLoopReferenceLoadError(
            code, f"{field} does not match its frozen value"
        )


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = (repo_root / relative_path).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError as exc:
        raise ClaimIDControlLoopReferenceLoadError(
            "pin_path", f"pinned path escapes repository: {relative_path}"
        ) from exc
    if _sha256(path) != expected_sha:
        raise ClaimIDControlLoopReferenceLoadError(
            "pin_mismatch", f"pinned file hash mismatch: {relative_path}"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return _decode_json_bytes(_read_bytes(path, "pinned_file"), "pinned_file")


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ClaimIDControlLoopReferenceLoadError(
            "pin_unavailable", f"pinned file cannot be read: {path}"
        ) from exc


def _require_sha256(value: bytes, expected: str, code: str) -> None:
    if hashlib.sha256(value).hexdigest() != expected:
        raise ClaimIDControlLoopReferenceLoadError(
            code, "input bytes do not match the frozen SHA-256"
        )


def _canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value
