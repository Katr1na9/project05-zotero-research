"""Fail-closed single-use import of opaque Claim-ID planner provenance.

This module reuses the frozen controller reference validator without reusing or
modifying the exhausted controller activation.  It returns only the same
read-only reference projection and never inserts Claim-IDs into planner config,
state, action, feature, or scoring inputs.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any
from collections.abc import Mapping, Sequence

from src.compiler.llm import claim_id_control_loop_reference_loader as controller_loader


AUTHORITY_BASE_COMMIT = "2dc26e4647d2c9ef786e12178e84924a8d659732"
AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-planner-import-wiring-"
    "single-execute-authority-design-v0.1-20260725.json"
)
AUTHORITY_DESIGN_SHA256 = (
    "98d1fc3cc3f7c4a72498675433ea36864e32edcba690fe84d6e0af484825be98"
)
AUTHORITY_DESIGN_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-claim-id-planner-import-wiring-"
    "single-execute-authority-design-v0.1-20260725"
)
AUTHORITY_DESIGN_STATUS = (
    "design_only_claim_id_planner_import_wiring_authority_not_activated"
)
ACTIVATION_STATUS = (
    "activated_single_claim_id_planner_import_wiring_execute_authorized"
)
IMPORTER_PATH = "src/compiler/llm/claim_id_planner_reference_importer.py"
PLANNER_ADAPTER_PATH = "09-experiments/scripts/planner_runtime_adapter.py"
PLANNER_RUNTIME_CONTRACT_PATH = (
    "09-experiments/governance/contracts/planner-runtime-contract-v0.1.json"
)
PLANNER_RUNTIME_CONTRACT_SHA256 = (
    "6e8c297e8cdac18b6f5349e6878c567aa524411e37b66187da30409da704c053"
)
CONTROLLER_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-controller-import-wiring-"
    "single-execute-authority-design-v0.1-20260725.json"
)
CONTROLLER_DESIGN_SHA256 = (
    "68dd4deecdd9f980813defeae65c107fff0646b14f0c64211659b2d29a5044b3"
)
CONTROLLER_ACTIVATION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-controller-import-wiring-"
    "single-execute-activation-v0.1-20260725.json"
)
CONTROLLER_ACTIVATION_SHA256 = (
    "9a9b561f5aecdc60f8a605c4918f123309d6117561f0450a654f08b6e622d682"
)
CONTROLLER_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/claim-id-controller-import-wiring/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)
CONTROLLER_RECEIPT_SHA256 = (
    "5b74a22a9dd6b2718a947ff88f7ed252ccc57060ec1b05a9656922870f2af19d"
)
RECEIPT_PATH = (
    "docs/llm-editor/fixtures/claim-id-planner-import-wiring/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)

_ACTIVATION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
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
_EXPECTED_TARGET = {
    "surface_id": controller_loader.SURFACE_ID,
    "package_id": controller_loader.PACKAGE_ID,
    "reference_mode": controller_loader.REFERENCE_MODE,
    "planner_entrypoint": PLANNER_ADAPTER_PATH,
    "planner_attachment_field": "claim_id_mainline_reference",
    "execution_scope": "single_planner_runtime_view_sidecar_import_only",
}
_STATIC_PINS = {
    "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
    "bound_control_loop_reference_sha256": controller_loader.REFERENCE_SHA256,
    "controller_reference_loader_sha256": (
        "3bf033296a4aceb497f8563ef1321998bbe8deb47ad80b41698b9a02017514b9"
    ),
    "controller_import_authority_design_sha256": CONTROLLER_DESIGN_SHA256,
    "exhausted_controller_import_activation_sha256": CONTROLLER_ACTIVATION_SHA256,
    "controller_import_receipt_sha256": CONTROLLER_RECEIPT_SHA256,
    "reference_binder_sha256": controller_loader.REFERENCE_BINDER_SHA256,
    "reference_binder_authority_design_sha256": (
        controller_loader.REFERENCE_BINDER_DESIGN_SHA256
    ),
    "exhausted_reference_binder_activation_sha256": (
        controller_loader.REFERENCE_BINDER_ACTIVATION_SHA256
    ),
    "registration_authority_design_sha256": (
        controller_loader.REGISTRATION_DESIGN_SHA256
    ),
    "registration_executor_sha256": controller_loader.REGISTRATION_EXECUTOR_SHA256,
    "exhausted_registration_activation_sha256": (
        controller_loader.REGISTRATION_ACTIVATION_SHA256
    ),
    "registration_record_sha256": controller_loader.REGISTRATION_RECORD_SHA256,
    "registration_receipt_sha256": controller_loader.REGISTRATION_RECEIPT_SHA256,
    "effective_consumer_contract_sha256": (
        controller_loader.EFFECTIVE_CONSUMER_CONTRACT_SHA256
    ),
    "external_envelope_schema_sha256": controller_loader.EXTERNAL_ENVELOPE_SHA256,
    "planner_runtime_contract_sha256": PLANNER_RUNTIME_CONTRACT_SHA256,
}
_EXPECTED_SELECTED_INPUT = {
    "bound_control_loop_reference": {
        "path": controller_loader.REFERENCE_PATH,
        "sha256": controller_loader.REFERENCE_SHA256,
        "surface_id": controller_loader.SURFACE_ID,
        "package_id": controller_loader.PACKAGE_ID,
        "claim_count": controller_loader.CLAIM_COUNT,
    }
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "single_planner_runtime_view_sidecar_import_only",
    "planner_entrypoint": PLANNER_ADAPTER_PATH,
    "planner_attachment_field": "claim_id_mainline_reference",
    "versioned_receipt_path": RECEIPT_PATH,
    "versioned_receipt_write": True,
    "production_controller_import_wired": True,
    "production_planner_import_wired_after_success": True,
    "planner_or_action_selection_algorithm_change": False,
    "planner_runtime_contract_change": False,
    "claim_lifecycle_mutation": False,
    "kernel_store_write": False,
    "e_case_write": False,
    "certificate_generation": False,
    "certified_stop": False,
}
_EXPECTED_STILL_BLOCKED = {
    "second_planner_import_under_same_activation": True,
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
_PROVENANCE_FIELDS = frozenset(
    {
        "reference_mode",
        "read_only",
        "reference_id",
        "surface_id",
        "package_id",
        "claim_ids",
        "claim_reference",
        "consumer_contract_ref",
        "registration_ref",
        "source_reference_sha256",
    }
)
_IMPORT_SEAL = object()


class ClaimIDPlannerReferenceImportError(ValueError):
    """Raised when planner provenance import fails a closed boundary."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ClaimIDPlannerImport:
    """One authorized immutable planner-sidecar import result."""

    provenance: Mapping[str, Any]
    activation_sha256_before: str
    execute_ledger_after_required: Mapping[str, Any]
    _seal: object = field(repr=False, compare=False)


def verify_planner_import_pins(repo_root: Path) -> None:
    """Verify the controller chain and the unchanged planner contract."""

    repo_root = repo_root.resolve()
    controller_loader.verify_controller_import_pins(repo_root)
    for relative_path, expected_sha in (
        (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
        (CONTROLLER_DESIGN_PATH, CONTROLLER_DESIGN_SHA256),
        (CONTROLLER_ACTIVATION_PATH, CONTROLLER_ACTIVATION_SHA256),
        (CONTROLLER_RECEIPT_PATH, CONTROLLER_RECEIPT_SHA256),
        (PLANNER_RUNTIME_CONTRACT_PATH, PLANNER_RUNTIME_CONTRACT_SHA256),
    ):
        _verify_pin(repo_root, relative_path, expected_sha)
    _validate_authority_design(_load_json(repo_root / AUTHORITY_DESIGN_PATH))
    controller_activation = _load_json(repo_root / CONTROLLER_ACTIVATION_PATH)
    _require_exact_mapping(
        controller_activation.get("execute_ledger"),
        _LEDGER_AFTER,
        "controller_activation.execute_ledger",
        "controller_chain",
    )
    controller_receipt = _load_json(repo_root / CONTROLLER_RECEIPT_PATH)
    controller_state = _require_mapping(
        controller_receipt.get("runtime_wiring_state"),
        "controller_receipt.runtime_wiring_state",
        "controller_chain",
    )
    for field, expected in (
        ("production_controller_import_wired", True),
        ("production_planner_import_wired", False),
        ("read_only_reference_only", True),
        ("algorithm_changed", False),
    ):
        _require_constant(
            controller_state.get(field),
            expected,
            f"controller_receipt.runtime_wiring_state.{field}",
            "controller_chain",
        )
    runtime_contract = _load_json(repo_root / PLANNER_RUNTIME_CONTRACT_PATH)
    _require_constant(
        runtime_contract.get("status"),
        "frozen_for_new_runs",
        "planner_runtime_contract.status",
        "planner_contract",
    )


def import_claim_id_planner_reference(
    reference_path: Path | None,
    *,
    repo_root: Path,
    activation_path: Path | None = None,
) -> ClaimIDPlannerImport:
    """Import one exact reference as a planner-view sidecar."""

    if activation_path is None:
        raise ClaimIDPlannerReferenceImportError(
            "missing_activation",
            "an activated single-use planner import authority is required",
        )
    if reference_path is None:
        raise ClaimIDPlannerReferenceImportError(
            "missing_reference", "the bound control-loop reference is required"
        )
    repo_root = repo_root.resolve()
    verify_planner_import_pins(repo_root)
    expected_reference_path = (repo_root / controller_loader.REFERENCE_PATH).resolve()
    if reference_path.resolve() != expected_reference_path:
        raise ClaimIDPlannerReferenceImportError(
            "reference_path", "reference path is not the frozen versioned path"
        )

    activation_bytes = _read_bytes(activation_path, "activation", 256 * 1024)
    activation = _decode_json_bytes(activation_bytes, "activation")
    _validate_activation(
        activation,
        planner_importer_sha256=_sha256(repo_root / IMPORTER_PATH),
        planner_adapter_sha256=_sha256(repo_root / PLANNER_ADAPTER_PATH),
    )
    reference_bytes = _read_bytes(expected_reference_path, "reference")
    if hashlib.sha256(reference_bytes).hexdigest() != controller_loader.REFERENCE_SHA256:
        raise ClaimIDPlannerReferenceImportError(
            "reference_pin", "reference bytes do not match the frozen SHA-256"
        )
    reference = controller_loader._decode_json_bytes(reference_bytes, "reference")
    view = controller_loader._validate_reference(reference)
    provenance = view.to_provenance()
    _validate_provenance(provenance, repo_root)
    return ClaimIDPlannerImport(
        provenance=MappingProxyType(provenance),
        activation_sha256_before=hashlib.sha256(activation_bytes).hexdigest(),
        execute_ledger_after_required=MappingProxyType(dict(_LEDGER_AFTER)),
        _seal=_IMPORT_SEAL,
    )


def validate_authorized_planner_import(
    value: Any,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Reject forged import objects and return an exact copied sidecar."""

    if not isinstance(value, ClaimIDPlannerImport) or value._seal is not _IMPORT_SEAL:
        raise ClaimIDPlannerReferenceImportError(
            "missing_activation",
            "claim_id_mainline_reference requires an authorized planner import",
        )
    if not re.fullmatch(r"[0-9a-f]{64}", value.activation_sha256_before):
        raise ClaimIDPlannerReferenceImportError(
            "activation_pin", "authorized import activation SHA-256 is invalid"
        )
    _require_exact_mapping(
        value.execute_ledger_after_required,
        _LEDGER_AFTER,
        "planner_import.execute_ledger_after_required",
        "activation_ledger",
    )
    return validate_planner_sidecar(value.provenance, repo_root=repo_root)


def validate_planner_sidecar(
    provenance: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Validate and copy the only sidecar shape accepted by the adapter."""

    copied = json.loads(json.dumps(dict(provenance), allow_nan=False))
    _validate_provenance(copied, repo_root.resolve())
    return copied


def _validate_authority_design(value: Any) -> None:
    design = _require_mapping(value, "authority_design", "authority_design")
    for field, expected in (
        ("artifact_id", AUTHORITY_DESIGN_ARTIFACT_ID),
        (
            "artifact_type",
            "claim_id_planner_import_wiring_single_execute_authority_design",
        ),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
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
        ("runtime_planner_reference_import_authorized", False),
        ("production_controller_import_wired", True),
        ("production_planner_import_wired", False),
        ("algorithm_changed", False),
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


def _validate_activation(
    value: Any,
    *,
    planner_importer_sha256: str,
    planner_adapter_sha256: str,
) -> None:
    activation = _require_mapping(value, "activation", "activation_shape")
    _reject_secret_keys(activation)
    if set(activation) != _EXPECTED_ACTIVATION_FIELDS:
        raise ClaimIDPlannerReferenceImportError(
            "activation_shape", "activation fields are not canonical"
        )
    artifact_id = activation.get("artifact_id")
    if not isinstance(artifact_id, str) or not _ACTIVATION_ID_PATTERN.fullmatch(
        artifact_id
    ):
        raise ClaimIDPlannerReferenceImportError(
            "activation_shape", "activation artifact id is invalid"
        )
    for field, expected in (
        ("artifact_type", "claim_id_planner_import_wiring_single_execute_activation"),
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
    expected_pins["planner_reference_importer_sha256"] = planner_importer_sha256
    expected_pins["planner_runtime_adapter_sha256"] = planner_adapter_sha256
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
        raise ClaimIDPlannerReferenceImportError(
            "activation_ledger", "activation already contains execution audit data"
        )


def _validate_provenance(value: Any, repo_root: Path) -> None:
    provenance = _require_mapping(value, "provenance", "provenance_shape")
    if set(provenance) != _PROVENANCE_FIELDS:
        raise ClaimIDPlannerReferenceImportError(
            "provenance_shape", "planner sidecar fields are not canonical"
        )
    _require_constant(
        provenance.get("reference_mode"),
        controller_loader.REFERENCE_MODE,
        "provenance.reference_mode",
        "provenance_state",
    )
    _require_constant(
        provenance.get("read_only"),
        True,
        "provenance.read_only",
        "provenance_state",
    )
    _require_constant(
        provenance.get("surface_id"),
        controller_loader.SURFACE_ID,
        "provenance.surface_id",
        "provenance_state",
    )
    _require_constant(
        provenance.get("package_id"),
        controller_loader.PACKAGE_ID,
        "provenance.package_id",
        "provenance_state",
    )
    _require_constant(
        provenance.get("source_reference_sha256"),
        controller_loader.REFERENCE_SHA256,
        "provenance.source_reference_sha256",
        "provenance_state",
    )
    claim_ids = provenance.get("claim_ids")
    if (
        not isinstance(claim_ids, Sequence)
        or isinstance(claim_ids, (str, bytes, bytearray))
        or len(claim_ids) != controller_loader.CLAIM_COUNT
        or any(not isinstance(item, str) or not item.startswith("clm_") for item in claim_ids)
    ):
        raise ClaimIDPlannerReferenceImportError(
            "provenance_claim_ids", "planner sidecar Claim-IDs are not exact opaque IDs"
        )
    contract = _load_json(repo_root / PLANNER_RUNTIME_CONTRACT_PATH)
    forbidden = set(contract["planner_visibility"]["recursive_forbidden_keys"])
    hits = _recursive_key_hits(provenance, forbidden)
    if hits:
        raise ClaimIDPlannerReferenceImportError(
            "recursive_forbidden_keys",
            f"planner sidecar contains forbidden keys: {hits}",
        )
    reference_bytes = _read_bytes(
        repo_root / controller_loader.REFERENCE_PATH,
        "reference",
    )
    if hashlib.sha256(reference_bytes).hexdigest() != controller_loader.REFERENCE_SHA256:
        raise ClaimIDPlannerReferenceImportError(
            "reference_pin", "reference bytes do not match the frozen SHA-256"
        )
    expected_reference = controller_loader._decode_json_bytes(
        reference_bytes, "reference"
    )
    expected_provenance = controller_loader._validate_reference(
        expected_reference
    ).to_provenance()
    if dict(provenance) != expected_provenance:
        raise ClaimIDPlannerReferenceImportError(
            "provenance_pin",
            "planner sidecar does not match the exact frozen reference projection",
        )


def _recursive_key_hits(value: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []

    def visit(item: Any, path: str) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                child_path = f"{path}.{key}" if path else str(key)
                if key in forbidden:
                    hits.append(child_path)
                visit(child, child_path)
        elif isinstance(item, Sequence) and not isinstance(
            item, (str, bytes, bytearray)
        ):
            for index, child in enumerate(item):
                visit(child, f"{path}[{index}]")

    visit(value, "")
    return hits


def _reject_secret_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).casefold()
            if any(
                token in key_text
                for token in ("secret", "password", "token", "hmac", "key_material")
            ):
                dotted = ".".join((*path, str(key)))
                raise ClaimIDPlannerReferenceImportError(
                    "secret_material", f"secret-bearing field is forbidden: {dotted}"
                )
            _reject_secret_keys(item, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, item in enumerate(value):
            _reject_secret_keys(item, (*path, str(index)))


def _read_bytes(path: Path, kind: str, maximum: int = 2 * 1024 * 1024) -> bytes:
    try:
        value = path.read_bytes()
    except OSError as exc:
        raise ClaimIDPlannerReferenceImportError(
            f"{kind}_unavailable", f"{kind} cannot be read"
        ) from exc
    if not value or len(value) > maximum:
        raise ClaimIDPlannerReferenceImportError(
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
        raise ClaimIDPlannerReferenceImportError(
            f"{kind}_json", f"{kind} must be strict UTF-8 JSON"
        ) from exc
    if not isinstance(decoded, dict):
        raise ClaimIDPlannerReferenceImportError(
            f"{kind}_shape", f"{kind} must be a JSON object"
        )
    return decoded


def _require_mapping(value: Any, field: str, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaimIDPlannerReferenceImportError(code, f"{field} must be an object")
    return value


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    code: str,
) -> None:
    observed = _require_mapping(value, field, code)
    if dict(observed) != dict(expected):
        raise ClaimIDPlannerReferenceImportError(
            code, f"{field} does not match its frozen value"
        )


def _require_constant(observed: Any, expected: Any, field: str, code: str) -> None:
    if observed != expected:
        raise ClaimIDPlannerReferenceImportError(
            code, f"{field} does not match its frozen value"
        )


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = (repo_root / relative_path).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError as exc:
        raise ClaimIDPlannerReferenceImportError(
            "pin_path", f"pinned path escapes repository: {relative_path}"
        ) from exc
    if _sha256(path) != expected_sha:
        raise ClaimIDPlannerReferenceImportError(
            "pin_mismatch", f"pinned file hash mismatch: {relative_path}"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return _decode_json_bytes(_read_bytes(path, "pinned_file"), "pinned_file")


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ClaimIDPlannerReferenceImportError(
            "pin_unavailable", f"pinned file cannot be read: {path}"
        ) from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value
