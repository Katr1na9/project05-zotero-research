"""Fail-closed durable attachment of read-only Claim-ID provenance.

This module is deliberately parallel to the historical single-execute
controller loader and planner importer.  It never reactivates or invokes those
paths.  A one-time capability activation validates their committed receipts
and exhausted ledgers.  The resulting versioned capability receipt may then
authorize repeatable, read-only attachment without a per-run ledger.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from src.compiler.llm import claim_id_control_loop_reference_loader as reference_loader
from src.compiler.llm import claim_id_mainline_handoff as handoff_module


AUTHORITY_BASE_COMMIT = "28131df8d3a49c6bc1c15c53c1659792117b9737"
AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-durable-replay-attach-"
    "authority-design-v0.1-20260725.json"
)
AUTHORITY_DESIGN_SHA256 = (
    "41a272e66ed30ea5b603fa5daeff9af1938d885786f79db74d6184797d155180"
)
AUTHORITY_DESIGN_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-claim-id-durable-replay-attach-"
    "authority-design-v0.1-20260725"
)
AUTHORITY_DESIGN_STATUS = (
    "design_only_claim_id_durable_replay_attach_authority_not_activated"
)
ACTIVATION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-durable-replay-attach-"
    "activation-v0.1-20260725.json"
)
ACTIVATION_STATUS = (
    "activated_single_claim_id_durable_replay_attach_capability_authorized"
)
ACTIVATION_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-claim-id-durable-replay-attach-"
    "activation-v0.1-20260725"
)
CAPABILITY_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/claim-id-durable-replay-attach/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)
CAPABILITY_RECEIPT_STATUS = "durable_replay_attach_capability_enabled"
ATTACHER_PATH = "src/compiler/llm/claim_id_durable_replay_attacher.py"
EXECUTED_ATTACHER_SHA256 = (
    "eb3a425a59c3d74fcbb451db33c4128f76a7101dc1eda1dcfa06a0c98e294789"
)
CONTROLLER_ENTRYPOINT_PATH = "09-experiments/scripts/run_mvp.py"
PLANNER_ADAPTER_PATH = "09-experiments/scripts/planner_runtime_adapter.py"
CONTROLLER_LOADER_PATH = (
    "src/compiler/llm/claim_id_control_loop_reference_loader.py"
)
CONTROLLER_LOADER_SHA256 = (
    "3bf033296a4aceb497f8563ef1321998bbe8deb47ad80b41698b9a02017514b9"
)
PLANNER_IMPORTER_PATH = "src/compiler/llm/claim_id_planner_reference_importer.py"
PLANNER_IMPORTER_SHA256 = (
    "00454a59223a9c5ba678dbe101b645649c67456b95159661dcf249ba6d0a8db9"
)
COMPLETION_DISPOSITION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-mainline-shortest-path-"
    "completion-disposition-v0.1-20260725.json"
)
COMPLETION_DISPOSITION_SHA256 = (
    "c9030339a7d4fbd29b8f7a9ae69d3b60d4a132e3574d941563cb1be0c3023792"
)
REFERENCE_PATH = reference_loader.REFERENCE_PATH
REFERENCE_SHA256 = reference_loader.REFERENCE_SHA256
CONTROLLER_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/claim-id-controller-import-wiring/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)
CONTROLLER_RECEIPT_SHA256 = (
    "5b74a22a9dd6b2718a947ff88f7ed252ccc57060ec1b05a9656922870f2af19d"
)
PLANNER_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/claim-id-planner-import-wiring/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)
PLANNER_RECEIPT_SHA256 = (
    "0373d53cc56fe8efa8c2d35d74a1ab7949490f9a5fc1bc5e25759ae5351e7b31"
)
CONTROLLER_ACTIVATION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-controller-import-wiring-"
    "single-execute-activation-v0.1-20260725.json"
)
CONTROLLER_ACTIVATION_SHA256 = (
    "9a9b561f5aecdc60f8a605c4918f123309d6117561f0450a654f08b6e622d682"
)
PLANNER_ACTIVATION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-planner-import-wiring-"
    "single-execute-activation-v0.1-20260725.json"
)
PLANNER_ACTIVATION_SHA256 = (
    "336c9ddc4a0d2b5b58bd025adfd9af42debf1d1ca2e5bd62642f8e25e579de58"
)
SURFACE_ID = reference_loader.SURFACE_ID
PACKAGE_ID = reference_loader.PACKAGE_ID
REFERENCE_MODE = reference_loader.REFERENCE_MODE
CLAIM_COUNT = reference_loader.CLAIM_COUNT

_MAX_JSON_BYTES = 2 * 1024 * 1024
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,191}$")
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
        "selected_evidence",
        "execute_ledger",
        "output_policy",
        "still_blocked",
        "execution_audit",
    }
)
_EXPECTED_RECEIPT_FIELDS = frozenset(
    {
        "artifact_id",
        "artifact_type",
        "version",
        "created_date",
        "authority_base_commit",
        "status",
        "capability_id",
        "authority",
        "validated_evidence",
        "runtime_pins",
        "repeatable_attach_proof",
        "terminal_state",
        "post_execution_fail_closed_hardening",
        "side_effects",
        "still_blocked",
    }
)
_EXPECTED_TARGET = {
    "surface_id": SURFACE_ID,
    "package_id": PACKAGE_ID,
    "reference_mode": REFERENCE_MODE,
    "execution_scope": "single_durable_replay_capability_enablement",
    "per_attach_ledger_after_enablement": False,
}
_EXPECTED_SELECTED_EVIDENCE = {
    "bound_reference": {
        "path": REFERENCE_PATH,
        "sha256": REFERENCE_SHA256,
        "claim_count": CLAIM_COUNT,
    },
    "controller_receipt": {
        "path": CONTROLLER_RECEIPT_PATH,
        "sha256": CONTROLLER_RECEIPT_SHA256,
    },
    "planner_receipt": {
        "path": PLANNER_RECEIPT_PATH,
        "sha256": PLANNER_RECEIPT_SHA256,
    },
    "exhausted_controller_activation": {
        "path": CONTROLLER_ACTIVATION_PATH,
        "sha256": CONTROLLER_ACTIVATION_SHA256,
    },
    "exhausted_planner_activation": {
        "path": PLANNER_ACTIVATION_PATH,
        "sha256": PLANNER_ACTIVATION_SHA256,
    },
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "enable_repeatable_read_only_provenance_attach_capability",
    "versioned_receipt_path": CAPABILITY_RECEIPT_PATH,
    "versioned_receipt_write": True,
    "capability_enablement_consumes_ledger_once": True,
    "successful_attach_consumes_per_run_ledger": False,
    "reexecutes_historical_import_wiring": False,
    "reactivates_historical_import_ledgers": False,
    "claim_lifecycle_mutation": False,
    "planner_or_action_selection_algorithm_change": False,
    "kernel_store_write": False,
    "e_case_write": False,
    "certificate_generation": False,
    "certified_stop": False,
}
_EXPECTED_STILL_BLOCKED = {
    "kernel_store": True,
    "e_case": True,
    "certificate": True,
    "certified_stop": True,
    "si_llm_001_closure": True,
    "l2": True,
    "part_b": True,
    "m2": True,
    "four_family_llm_finetune": True,
}
_EXPECTED_SIDE_EFFECTS = {
    "historical_controller_import_reexecuted": False,
    "historical_planner_import_reexecuted": False,
    "historical_activation_ledger_mutated": False,
    "claim_lifecycle_mutation": False,
    "planner_or_action_selection_algorithm_change": False,
    "production_registration_switch_enabled": False,
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
_ATTACHMENT_SEAL = object()
_CAPABILITY_GRANT_SEAL = object()


class ClaimIDDurableReplayAttachError(ValueError):
    """Raised when durable replay evidence fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ClaimIDDurableReplayAttachment:
    """Sealed repeatable attachment validated from a capability receipt."""

    _provenance: Any = field(repr=False)
    capability_receipt_sha256: str
    _repo_root: Path = field(repr=False, compare=False)
    _reference_path: Path = field(repr=False, compare=False)
    _receipt_path: Path = field(repr=False, compare=False)
    _seal: object = field(repr=False, compare=False)

    def to_provenance(self) -> dict[str, Any]:
        """Return a detached JSON-compatible read-only provenance projection."""

        return _thaw(self._provenance)


@dataclass(frozen=True)
class ClaimIDDurableReplayCapabilityGrant:
    """One validated capability enablement and its non-consuming attach view."""

    activation_sha256_before: str
    runtime_pins: Mapping[str, str]
    _provenance: Any = field(repr=False)
    _seal: object = field(repr=False, compare=False)

    def attach_for_enablement_proof(self) -> ClaimIDDurableReplayAttachment:
        """Produce a proof attachment without consuming another ledger unit."""

        if self._seal is not _CAPABILITY_GRANT_SEAL:
            raise ClaimIDDurableReplayAttachError(
                "capability_seal", "capability grant is not module-authorized"
            )
        return ClaimIDDurableReplayAttachment(
            _provenance=self._provenance,
            capability_receipt_sha256="",
            _repo_root=Path(),
            _reference_path=Path(),
            _receipt_path=Path(),
            _seal=_ATTACHMENT_SEAL,
        )


def verify_durable_replay_static_pins(repo_root: Path) -> None:
    """Verify the frozen historical evidence without invoking old loaders."""

    root = repo_root.resolve()
    for relative_path, expected_sha in (
        (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
        (COMPLETION_DISPOSITION_PATH, COMPLETION_DISPOSITION_SHA256),
        (REFERENCE_PATH, REFERENCE_SHA256),
        (CONTROLLER_RECEIPT_PATH, CONTROLLER_RECEIPT_SHA256),
        (PLANNER_RECEIPT_PATH, PLANNER_RECEIPT_SHA256),
        (CONTROLLER_ACTIVATION_PATH, CONTROLLER_ACTIVATION_SHA256),
        (PLANNER_ACTIVATION_PATH, PLANNER_ACTIVATION_SHA256),
        (CONTROLLER_LOADER_PATH, CONTROLLER_LOADER_SHA256),
        (PLANNER_IMPORTER_PATH, PLANNER_IMPORTER_SHA256),
    ):
        _verify_pin(root, relative_path, expected_sha)
    _validate_authority_design(_load_json(root / AUTHORITY_DESIGN_PATH))
    _validate_historical_receipt(
        _load_json(root / CONTROLLER_RECEIPT_PATH), "controller"
    )
    _validate_historical_receipt(
        _load_json(root / PLANNER_RECEIPT_PATH), "planner"
    )
    _validate_historical_activation(
        _load_json(root / CONTROLLER_ACTIVATION_PATH), "controller"
    )
    _validate_historical_activation(
        _load_json(root / PLANNER_ACTIVATION_PATH), "planner"
    )
    if handoff_module.PRODUCTION_REGISTRATION_ENABLED is not False:
        raise ClaimIDDurableReplayAttachError(
            "registration_switch",
            "PRODUCTION_REGISTRATION_ENABLED must remain False",
        )


def enable_durable_replay_attach_capability(
    activation_path: Path | None,
    *,
    repo_root: Path,
) -> ClaimIDDurableReplayCapabilityGrant:
    """Consume the single capability-enablement authority in wrapper audit."""

    if activation_path is None:
        raise ClaimIDDurableReplayAttachError(
            "missing_activation", "capability activation is required"
        )
    root = repo_root.resolve()
    verify_durable_replay_static_pins(root)
    activation_pins = _activation_runtime_pins(root)
    activation_bytes = _read_bytes(
        activation_path.resolve(), "activation", 512 * 1024
    )
    activation = _decode_json_bytes(activation_bytes, "activation")
    _validate_activation(
        activation,
        runtime_pins=activation_pins,
        expected_ledger=_LEDGER_BEFORE,
        expected_receipt_sha256=None,
    )
    provenance = _load_reference_provenance(root / REFERENCE_PATH)
    return ClaimIDDurableReplayCapabilityGrant(
        activation_sha256_before=hashlib.sha256(activation_bytes).hexdigest(),
        runtime_pins=MappingProxyType(dict(_runtime_pins(root))),
        _provenance=_freeze(provenance),
        _seal=_CAPABILITY_GRANT_SEAL,
    )


def build_capability_receipt(
    grant: ClaimIDDurableReplayCapabilityGrant,
    provenance_sha256s: Sequence[str],
) -> dict[str, Any]:
    """Build the sanitized receipt after at least two stable proof attaches."""

    if not isinstance(grant, ClaimIDDurableReplayCapabilityGrant) or (
        grant._seal is not _CAPABILITY_GRANT_SEAL
    ):
        raise ClaimIDDurableReplayAttachError(
            "capability_seal", "capability grant is not module-authorized"
        )
    hashes = list(provenance_sha256s)
    if len(hashes) < 2 or any(not _is_sha256(value) for value in hashes):
        raise ClaimIDDurableReplayAttachError(
            "repeatable_attach_proof",
            "at least two valid provenance hashes are required",
        )
    if len(set(hashes)) != 1:
        raise ClaimIDDurableReplayAttachError(
            "repeatable_attach_proof", "repeatable provenance is not stable"
        )
    return {
        "artifact_id": (
            "llm-editor-v0.8-l2-claim-id-durable-replay-attach-"
            "sanitized-receipt-v0.1-20260725"
        ),
        "artifact_type": "claim_id_durable_replay_attach_sanitized_receipt",
        "version": "0.1",
        "created_date": "2026-07-25",
        "authority_base_commit": AUTHORITY_BASE_COMMIT,
        "status": CAPABILITY_RECEIPT_STATUS,
        "capability_id": "claim_id_durable_replay_attach_v0_1",
        "authority": {
            "design": {
                "artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
                "path": AUTHORITY_DESIGN_PATH,
                "sha256": AUTHORITY_DESIGN_SHA256,
                "status": AUTHORITY_DESIGN_STATUS,
            },
            "activation": {
                "artifact_id": ACTIVATION_ARTIFACT_ID,
                "path": ACTIVATION_PATH,
                "sha256_before": grant.activation_sha256_before,
                "execute_ledger_before": dict(_LEDGER_BEFORE),
                "execute_ledger_after": dict(_LEDGER_AFTER),
            },
        },
        "validated_evidence": _expected_selected_evidence_with_states(),
        "runtime_pins": dict(grant.runtime_pins),
        "repeatable_attach_proof": {
            "attach_call_count": len(hashes),
            "first_provenance_sha256": hashes[0],
            "second_provenance_sha256": hashes[1],
            "all_provenance_sha256_equal": True,
            "successful_attach_consumes_per_run_ledger": False,
        },
        "terminal_state": {
            "durable_replay_attach_authorized": True,
            "production_controller_import_wired": True,
            "production_planner_import_wired": True,
            "read_only_reference_only": True,
            "algorithm_changed": False,
            "historical_import_activations_remain_exhausted": True,
            "production_registration_enabled": False,
        },
        "post_execution_fail_closed_hardening": {
            "second_capability_activation_execution_performed": False,
            "capability_ledger_remained_exhausted": True,
            "executed_durable_replay_attacher_sha256": (
                EXECUTED_ATTACHER_SHA256
            ),
            "current_durable_replay_attacher_sha256": grant.runtime_pins[
                "durable_replay_attacher_sha256"
            ],
            "receipt_activation_cross_binding_added": True,
            "complete_receipt_revalidated_on_every_attachment": True,
        },
        "side_effects": dict(_EXPECTED_SIDE_EFFECTS),
        "still_blocked": dict(_EXPECTED_STILL_BLOCKED),
    }


def load_claim_id_durable_replay_attachment(
    reference_path: Path | None,
    capability_receipt_path: Path | None,
    capability_receipt_sha256: str | None,
    *,
    repo_root: Path,
) -> ClaimIDDurableReplayAttachment:
    """Load one repeatable attachment from committed exhausted-state evidence."""

    if reference_path is None:
        raise ClaimIDDurableReplayAttachError(
            "missing_reference", "bound reference path is required"
        )
    if capability_receipt_path is None:
        raise ClaimIDDurableReplayAttachError(
            "missing_receipt", "durable replay capability receipt is required"
        )
    if not isinstance(capability_receipt_sha256, str) or not _is_sha256(
        capability_receipt_sha256
    ):
        raise ClaimIDDurableReplayAttachError(
            "missing_receipt_pin", "exact capability receipt SHA-256 is required"
        )
    root = repo_root.resolve()
    expected_reference = (root / REFERENCE_PATH).resolve()
    expected_receipt = (root / CAPABILITY_RECEIPT_PATH).resolve()
    if reference_path.resolve() != expected_reference:
        raise ClaimIDDurableReplayAttachError(
            "reference_path", "reference path is not the frozen versioned path"
        )
    if capability_receipt_path.resolve() != expected_receipt:
        raise ClaimIDDurableReplayAttachError(
            "receipt_path", "capability receipt path is not versioned path"
        )
    provenance = _validate_durable_inputs(
        root,
        expected_reference,
        expected_receipt,
        capability_receipt_sha256,
    )
    return ClaimIDDurableReplayAttachment(
        _provenance=_freeze(provenance),
        capability_receipt_sha256=capability_receipt_sha256,
        _repo_root=root,
        _reference_path=expected_reference,
        _receipt_path=expected_receipt,
        _seal=_ATTACHMENT_SEAL,
    )


def validate_durable_replay_attachment(
    value: Any,
) -> dict[str, Any]:
    """Revalidate complete receipt/reference evidence on every attachment."""

    if not isinstance(value, ClaimIDDurableReplayAttachment) or (
        value._seal is not _ATTACHMENT_SEAL
    ):
        raise ClaimIDDurableReplayAttachError(
            "attachment_seal", "durable replay attachment is not authorized"
        )
    if not value.capability_receipt_sha256:
        raise ClaimIDDurableReplayAttachError(
            "proof_only_attachment",
            "capability-enablement proof is not a runtime attachment",
        )
    observed = _validate_durable_inputs(
        value._repo_root,
        value._reference_path,
        value._receipt_path,
        value.capability_receipt_sha256,
    )
    if observed != value.to_provenance():
        raise ClaimIDDurableReplayAttachError(
            "attachment_tamper", "attachment projection changed after validation"
        )
    return observed


def canonical_json_sha256(value: Any) -> str:
    """Return the canonical SHA-256 used for repeatability evidence."""

    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_durable_inputs(
    root: Path,
    reference_path: Path,
    receipt_path: Path,
    receipt_sha256: str,
) -> dict[str, Any]:
    verify_durable_replay_static_pins(root)
    runtime_pins = _runtime_pins(root)
    activation_pins = _activation_runtime_pins(root)
    receipt_bytes = _read_bytes(receipt_path, "capability_receipt", 512 * 1024)
    _require_sha256(receipt_bytes, receipt_sha256, "capability_receipt_pin")
    receipt = _decode_json_bytes(receipt_bytes, "capability_receipt")
    _validate_capability_receipt(receipt, runtime_pins=runtime_pins)
    activation = _load_json(root / ACTIVATION_PATH)
    _validate_activation(
        activation,
        runtime_pins=activation_pins,
        expected_ledger=_LEDGER_AFTER,
        expected_receipt_sha256=receipt_sha256,
    )
    _validate_receipt_activation_cross_binding(
        receipt,
        activation,
        receipt_sha256=receipt_sha256,
        current_runtime_pins=runtime_pins,
    )
    return _load_reference_provenance(reference_path)


def _runtime_pins(root: Path) -> dict[str, str]:
    return {
        "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
        "completion_disposition_sha256": COMPLETION_DISPOSITION_SHA256,
        "bound_reference_sha256": REFERENCE_SHA256,
        "controller_sanitized_receipt_sha256": CONTROLLER_RECEIPT_SHA256,
        "planner_sanitized_receipt_sha256": PLANNER_RECEIPT_SHA256,
        "exhausted_controller_activation_sha256": CONTROLLER_ACTIVATION_SHA256,
        "exhausted_planner_activation_sha256": PLANNER_ACTIVATION_SHA256,
        "controller_reference_loader_sha256": CONTROLLER_LOADER_SHA256,
        "planner_reference_importer_sha256": PLANNER_IMPORTER_SHA256,
        "durable_replay_attacher_sha256": _sha256(root / ATTACHER_PATH),
        "controller_entrypoint_sha256": _sha256(
            root / CONTROLLER_ENTRYPOINT_PATH
        ),
        "planner_runtime_adapter_sha256": _sha256(root / PLANNER_ADAPTER_PATH),
    }


def _activation_runtime_pins(root: Path) -> dict[str, str]:
    pins = _runtime_pins(root)
    pins["durable_replay_attacher_sha256"] = EXECUTED_ATTACHER_SHA256
    return pins


def _validate_authority_design(value: Any) -> None:
    design = _require_mapping(value, "authority_design", "authority_design")
    for field_name, expected in (
        ("artifact_id", AUTHORITY_DESIGN_ARTIFACT_ID),
        ("artifact_type", "claim_id_durable_replay_attach_authority_design"),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", AUTHORITY_DESIGN_STATUS),
        ("surface_id", SURFACE_ID),
    ):
        _require_constant(
            design.get(field_name),
            expected,
            f"authority_design.{field_name}",
            "authority_design",
        )
    current = _require_mapping(
        design.get("current_authorization_state"),
        "authority_design.current_authorization_state",
        "authority_design",
    )
    for field_name, expected in (
        ("activated", False),
        ("authorized", 0),
        ("maximum", 0),
        ("started", 0),
        ("consumed", 0),
        ("remaining", 0),
        ("durable_replay_attach_authorized", False),
        ("per_run_replay_authorized", False),
    ):
        _require_constant(
            current.get(field_name),
            expected,
            f"authority_design.current_authorization_state.{field_name}",
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


def _validate_historical_receipt(value: Any, kind: str) -> None:
    receipt = _require_mapping(value, f"{kind}_receipt", "historical_receipt")
    expected_status = {
        "controller": "production_controller_import_wired_read_only_reference",
        "planner": "production_planner_import_wired_read_only_reference",
    }[kind]
    _require_constant(
        receipt.get("status"),
        expected_status,
        f"{kind}_receipt.status",
        "historical_receipt",
    )
    runtime = _require_mapping(
        receipt.get("runtime_wiring_state"),
        f"{kind}_receipt.runtime_wiring_state",
        "historical_receipt",
    )
    for field_name, expected in (
        ("production_controller_import_wired", True),
        ("production_planner_import_wired", kind == "planner"),
        ("read_only_reference_only", True),
        ("algorithm_changed", False),
        ("evidence_sufficiency_asserted", False),
        ("certified_stop_asserted", False),
    ):
        _require_constant(
            runtime.get(field_name),
            expected,
            f"{kind}_receipt.runtime_wiring_state.{field_name}",
            "historical_receipt",
        )
    side_effects = _require_mapping(
        receipt.get("side_effects"),
        f"{kind}_receipt.side_effects",
        "historical_receipt",
    )
    if not side_effects or any(value is not False for value in side_effects.values()):
        raise ClaimIDDurableReplayAttachError(
            "historical_receipt",
            f"{kind} receipt contains a non-false side effect",
        )


def _validate_historical_activation(value: Any, kind: str) -> None:
    activation = _require_mapping(
        value, f"{kind}_activation", "historical_activation"
    )
    _require_exact_mapping(
        activation.get("execute_ledger"),
        _LEDGER_AFTER,
        f"{kind}_activation.execute_ledger",
        "historical_activation",
    )
    audit = _require_mapping(
        activation.get("execution_audit"),
        f"{kind}_activation.execution_audit",
        "historical_activation",
    )
    count_field = {
        "controller": "loader_invocation_count",
        "planner": "planner_importer_invocation_count",
    }[kind]
    _require_constant(
        audit.get(count_field),
        1,
        f"{kind}_activation.execution_audit.{count_field}",
        "historical_activation",
    )
    expected_receipt_sha = {
        "controller": CONTROLLER_RECEIPT_SHA256,
        "planner": PLANNER_RECEIPT_SHA256,
    }[kind]
    audit_receipt = _require_mapping(
        audit.get("sanitized_receipt"),
        f"{kind}_activation.execution_audit.sanitized_receipt",
        "historical_activation",
    )
    _require_constant(
        audit_receipt.get("sha256"),
        expected_receipt_sha,
        f"{kind}_activation.execution_audit.sanitized_receipt.sha256",
        "historical_activation",
    )


def _validate_activation(
    value: Any,
    *,
    runtime_pins: Mapping[str, str],
    expected_ledger: Mapping[str, Any],
    expected_receipt_sha256: str | None,
) -> None:
    activation = _require_mapping(value, "activation", "activation_shape")
    _reject_secret_keys(activation)
    if set(activation) != _EXPECTED_ACTIVATION_FIELDS:
        raise ClaimIDDurableReplayAttachError(
            "activation_shape", "activation fields are not canonical"
        )
    for field_name, expected in (
        ("artifact_id", ACTIVATION_ARTIFACT_ID),
        ("artifact_type", "claim_id_durable_replay_attach_activation"),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", ACTIVATION_STATUS),
    ):
        _require_constant(
            activation.get(field_name),
            expected,
            f"activation.{field_name}",
            "not_activated",
        )
    if not _ARTIFACT_ID_PATTERN.fullmatch(str(activation.get("artifact_id"))):
        raise ClaimIDDurableReplayAttachError(
            "activation_shape", "activation artifact id is invalid"
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
    _require_exact_mapping(
        activation.get("pinned_hashes"),
        runtime_pins,
        "activation.pinned_hashes",
        "activation_pin",
    )
    _require_exact_mapping(
        activation.get("selected_evidence"),
        _EXPECTED_SELECTED_EVIDENCE,
        "activation.selected_evidence",
        "selected_evidence",
    )
    _require_exact_mapping(
        activation.get("execute_ledger"),
        expected_ledger,
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
    audit = activation.get("execution_audit")
    if expected_receipt_sha256 is None:
        if audit is not None:
            raise ClaimIDDurableReplayAttachError(
                "activation_ledger", "unconsumed activation contains audit data"
            )
        return
    audit_mapping = _require_mapping(
        audit, "activation.execution_audit", "activation_audit"
    )
    _validate_execution_audit(
        audit_mapping,
        runtime_pins=runtime_pins,
        expected_receipt_sha256=expected_receipt_sha256,
    )


def _validate_execution_audit(
    audit: Mapping[str, Any],
    *,
    runtime_pins: Mapping[str, str],
    expected_receipt_sha256: str,
) -> None:
    expected_fields = {
        "decision",
        "attacher_invocation_count",
        "grant_attach_proof_count",
        "activation_sha256_before",
        "runtime_pins",
        "execute_ledger_before",
        "execute_ledger_after",
        "sanitized_receipt",
        "repeatable_attach_proof",
        "historical_import_activations_remained_exhausted",
        "post_execution_fail_closed_hardening",
        "forbidden_side_effects",
    }
    if set(audit) != expected_fields:
        raise ClaimIDDurableReplayAttachError(
            "activation_audit", "activation audit fields are not canonical"
        )
    for field_name, expected in (
        ("decision", "enabled_durable_replay_attach_capability_once"),
        ("attacher_invocation_count", 1),
        ("grant_attach_proof_count", 2),
        ("historical_import_activations_remained_exhausted", True),
    ):
        _require_constant(
            audit.get(field_name),
            expected,
            f"activation.execution_audit.{field_name}",
            "activation_audit",
        )
    if not _is_sha256(audit.get("activation_sha256_before")):
        raise ClaimIDDurableReplayAttachError(
            "activation_audit", "activation before SHA-256 is invalid"
        )
    _require_exact_mapping(
        audit.get("runtime_pins"),
        runtime_pins,
        "activation.execution_audit.runtime_pins",
        "activation_audit",
    )
    _require_exact_mapping(
        audit.get("execute_ledger_before"),
        _LEDGER_BEFORE,
        "activation.execution_audit.execute_ledger_before",
        "activation_audit",
    )
    _require_exact_mapping(
        audit.get("execute_ledger_after"),
        _LEDGER_AFTER,
        "activation.execution_audit.execute_ledger_after",
        "activation_audit",
    )
    _require_exact_mapping(
        audit.get("sanitized_receipt"),
        {
            "path": CAPABILITY_RECEIPT_PATH,
            "sha256": expected_receipt_sha256,
            "status": CAPABILITY_RECEIPT_STATUS,
        },
        "activation.execution_audit.sanitized_receipt",
        "activation_audit",
    )
    proof = _require_mapping(
        audit.get("repeatable_attach_proof"),
        "activation.execution_audit.repeatable_attach_proof",
        "activation_audit",
    )
    if proof.get("attach_call_count") != 2 or (
        proof.get("first_provenance_sha256")
        != proof.get("second_provenance_sha256")
    ):
        raise ClaimIDDurableReplayAttachError(
            "activation_audit", "activation attach proof is not stable"
        )
    _require_exact_mapping(
        audit.get("forbidden_side_effects"),
        _EXPECTED_SIDE_EFFECTS,
        "activation.execution_audit.forbidden_side_effects",
        "activation_audit",
    )
    hardening = _require_mapping(
        audit.get("post_execution_fail_closed_hardening"),
        "activation.execution_audit.post_execution_fail_closed_hardening",
        "activation_audit",
    )
    for field_name, expected in (
        ("second_capability_activation_execution_performed", False),
        ("capability_ledger_remained_exhausted", True),
        ("executed_durable_replay_attacher_sha256", EXECUTED_ATTACHER_SHA256),
        ("receipt_activation_cross_binding_added", True),
        ("complete_receipt_revalidated_on_every_attachment", True),
    ):
        _require_constant(
            hardening.get(field_name),
            expected,
            (
                "activation.execution_audit."
                f"post_execution_fail_closed_hardening.{field_name}"
            ),
            "activation_audit",
        )
    if not _is_sha256(hardening.get("current_durable_replay_attacher_sha256")):
        raise ClaimIDDurableReplayAttachError(
            "activation_audit", "current hardened attacher SHA-256 is invalid"
        )
    if not _is_sha256(hardening.get("current_capability_receipt_sha256")):
        raise ClaimIDDurableReplayAttachError(
            "activation_audit", "current capability receipt SHA-256 is invalid"
        )


def _validate_capability_receipt(
    value: Any,
    *,
    runtime_pins: Mapping[str, str],
) -> None:
    receipt = _require_mapping(
        value, "capability_receipt", "capability_receipt_shape"
    )
    _reject_secret_keys(receipt)
    if set(receipt) != _EXPECTED_RECEIPT_FIELDS:
        raise ClaimIDDurableReplayAttachError(
            "capability_receipt_shape", "receipt fields are not canonical"
        )
    for field_name, expected in (
        (
            "artifact_id",
            "llm-editor-v0.8-l2-claim-id-durable-replay-attach-"
            "sanitized-receipt-v0.1-20260725",
        ),
        ("artifact_type", "claim_id_durable_replay_attach_sanitized_receipt"),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", CAPABILITY_RECEIPT_STATUS),
        ("capability_id", "claim_id_durable_replay_attach_v0_1"),
    ):
        _require_constant(
            receipt.get(field_name),
            expected,
            f"capability_receipt.{field_name}",
            "capability_receipt",
        )
    authority = _require_mapping(
        receipt.get("authority"),
        "capability_receipt.authority",
        "capability_receipt",
    )
    _require_exact_mapping(
        authority.get("design"),
        {
            "artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
            "path": AUTHORITY_DESIGN_PATH,
            "sha256": AUTHORITY_DESIGN_SHA256,
            "status": AUTHORITY_DESIGN_STATUS,
        },
        "capability_receipt.authority.design",
        "capability_receipt",
    )
    activation_ref = _require_mapping(
        authority.get("activation"),
        "capability_receipt.authority.activation",
        "capability_receipt",
    )
    for field_name, expected in (
        ("artifact_id", ACTIVATION_ARTIFACT_ID),
        ("path", ACTIVATION_PATH),
    ):
        _require_constant(
            activation_ref.get(field_name),
            expected,
            f"capability_receipt.authority.activation.{field_name}",
            "capability_receipt",
        )
    if not _is_sha256(activation_ref.get("sha256_before")):
        raise ClaimIDDurableReplayAttachError(
            "capability_receipt", "activation before SHA-256 is invalid"
        )
    _require_exact_mapping(
        activation_ref.get("execute_ledger_before"),
        _LEDGER_BEFORE,
        "capability_receipt.authority.activation.execute_ledger_before",
        "capability_receipt",
    )
    _require_exact_mapping(
        activation_ref.get("execute_ledger_after"),
        _LEDGER_AFTER,
        "capability_receipt.authority.activation.execute_ledger_after",
        "capability_receipt",
    )
    _require_exact_mapping(
        receipt.get("validated_evidence"),
        _expected_selected_evidence_with_states(),
        "capability_receipt.validated_evidence",
        "capability_receipt",
    )
    _require_exact_mapping(
        receipt.get("runtime_pins"),
        runtime_pins,
        "capability_receipt.runtime_pins",
        "capability_receipt",
    )
    proof = _require_mapping(
        receipt.get("repeatable_attach_proof"),
        "capability_receipt.repeatable_attach_proof",
        "capability_receipt",
    )
    if (
        not isinstance(proof.get("attach_call_count"), int)
        or proof.get("attach_call_count") < 2
        or not _is_sha256(proof.get("first_provenance_sha256"))
        or proof.get("first_provenance_sha256")
        != proof.get("second_provenance_sha256")
        or proof.get("all_provenance_sha256_equal") is not True
        or proof.get("successful_attach_consumes_per_run_ledger") is not False
    ):
        raise ClaimIDDurableReplayAttachError(
            "repeatable_attach_proof", "receipt attach proof is invalid"
        )
    _require_exact_mapping(
        receipt.get("terminal_state"),
        {
            "durable_replay_attach_authorized": True,
            "production_controller_import_wired": True,
            "production_planner_import_wired": True,
            "read_only_reference_only": True,
            "algorithm_changed": False,
            "historical_import_activations_remain_exhausted": True,
            "production_registration_enabled": False,
        },
        "capability_receipt.terminal_state",
        "capability_receipt",
    )
    _require_exact_mapping(
        receipt.get("post_execution_fail_closed_hardening"),
        {
            "second_capability_activation_execution_performed": False,
            "capability_ledger_remained_exhausted": True,
            "executed_durable_replay_attacher_sha256": (
                EXECUTED_ATTACHER_SHA256
            ),
            "current_durable_replay_attacher_sha256": runtime_pins[
                "durable_replay_attacher_sha256"
            ],
            "receipt_activation_cross_binding_added": True,
            "complete_receipt_revalidated_on_every_attachment": True,
        },
        "capability_receipt.post_execution_fail_closed_hardening",
        "capability_receipt",
    )
    _require_exact_mapping(
        receipt.get("side_effects"),
        _EXPECTED_SIDE_EFFECTS,
        "capability_receipt.side_effects",
        "capability_receipt",
    )
    _require_exact_mapping(
        receipt.get("still_blocked"),
        _EXPECTED_STILL_BLOCKED,
        "capability_receipt.still_blocked",
        "capability_receipt",
    )


def _validate_receipt_activation_cross_binding(
    receipt: Mapping[str, Any],
    activation: Mapping[str, Any],
    *,
    receipt_sha256: str,
    current_runtime_pins: Mapping[str, str],
) -> None:
    receipt_authority = _require_mapping(
        receipt.get("authority"),
        "capability_receipt.authority",
        "cross_binding",
    )
    receipt_activation = _require_mapping(
        receipt_authority.get("activation"),
        "capability_receipt.authority.activation",
        "cross_binding",
    )
    audit = _require_mapping(
        activation.get("execution_audit"),
        "activation.execution_audit",
        "cross_binding",
    )
    _require_constant(
        audit.get("activation_sha256_before"),
        receipt_activation.get("sha256_before"),
        "receipt_activation.activation_sha256_before",
        "cross_binding",
    )
    _require_exact_mapping(
        audit.get("repeatable_attach_proof"),
        _require_mapping(
            receipt.get("repeatable_attach_proof"),
            "capability_receipt.repeatable_attach_proof",
            "cross_binding",
        ),
        "receipt_activation.repeatable_attach_proof",
        "cross_binding",
    )
    audit_receipt = _require_mapping(
        audit.get("sanitized_receipt"),
        "activation.execution_audit.sanitized_receipt",
        "cross_binding",
    )
    _require_constant(
        audit_receipt.get("sha256"),
        receipt_sha256,
        "receipt_activation.receipt_sha256",
        "cross_binding",
    )
    audit_hardening = _require_mapping(
        audit.get("post_execution_fail_closed_hardening"),
        "activation.execution_audit.post_execution_fail_closed_hardening",
        "cross_binding",
    )
    receipt_hardening = _require_mapping(
        receipt.get("post_execution_fail_closed_hardening"),
        "capability_receipt.post_execution_fail_closed_hardening",
        "cross_binding",
    )
    current_attacher_sha = current_runtime_pins[
        "durable_replay_attacher_sha256"
    ]
    for observed in (
        audit_hardening.get("current_durable_replay_attacher_sha256"),
        receipt_hardening.get("current_durable_replay_attacher_sha256"),
    ):
        _require_constant(
            observed,
            current_attacher_sha,
            "receipt_activation.current_durable_replay_attacher_sha256",
            "cross_binding",
        )
    _require_constant(
        audit_hardening.get("current_capability_receipt_sha256"),
        receipt_sha256,
        "receipt_activation.current_capability_receipt_sha256",
        "cross_binding",
    )


def _expected_selected_evidence_with_states() -> dict[str, Any]:
    return {
        **_EXPECTED_SELECTED_EVIDENCE,
        "controller_terminal_state": {
            "production_controller_import_wired": True,
            "production_planner_import_wired": False,
            "algorithm_changed": False,
        },
        "planner_terminal_state": {
            "production_controller_import_wired": True,
            "production_planner_import_wired": True,
            "algorithm_changed": False,
        },
    }


def _load_reference_provenance(path: Path) -> dict[str, Any]:
    reference_bytes = _read_bytes(path, "reference")
    _require_sha256(reference_bytes, REFERENCE_SHA256, "reference_pin")
    reference = _decode_json_bytes(reference_bytes, "reference")
    try:
        view = reference_loader._validate_reference(reference)
    except reference_loader.ClaimIDControlLoopReferenceLoadError as exc:
        raise ClaimIDDurableReplayAttachError(
            "reference_validation", "bound reference failed frozen validation"
        ) from exc
    provenance = view.to_provenance()
    if canonical_json_sha256(provenance) != canonical_json_sha256(
        view.to_provenance()
    ):
        raise ClaimIDDurableReplayAttachError(
            "reference_validation", "reference projection is unstable"
        )
    return provenance


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _reject_secret_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).casefold()
            if any(
                token in key_text
                for token in ("secret", "password", "hmac", "key_material")
            ):
                dotted = ".".join((*path, str(key)))
                raise ClaimIDDurableReplayAttachError(
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
        raise ClaimIDDurableReplayAttachError(
            f"{kind}_unavailable", f"{kind} cannot be read"
        ) from exc
    if not value or len(value) > maximum:
        raise ClaimIDDurableReplayAttachError(
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
        raise ClaimIDDurableReplayAttachError(
            f"{kind}_json", f"{kind} must be strict UTF-8 JSON"
        ) from exc
    if not isinstance(decoded, dict):
        raise ClaimIDDurableReplayAttachError(
            f"{kind}_shape", f"{kind} must be a JSON object"
        )
    return decoded


def _require_mapping(value: Any, field_name: str, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaimIDDurableReplayAttachError(
            code, f"{field_name} must be an object"
        )
    return value


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field_name: str,
    code: str,
) -> None:
    observed = _require_mapping(value, field_name, code)
    if dict(observed) != dict(expected):
        raise ClaimIDDurableReplayAttachError(
            code, f"{field_name} does not match its frozen value"
        )


def _require_constant(
    observed: Any,
    expected: Any,
    field_name: str,
    code: str,
) -> None:
    if observed != expected:
        raise ClaimIDDurableReplayAttachError(
            code, f"{field_name} does not match its frozen value"
        )


def _verify_pin(root: Path, relative_path: str, expected_sha: str) -> None:
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ClaimIDDurableReplayAttachError(
            "pin_path", f"pinned path escapes repository: {relative_path}"
        ) from exc
    if _sha256(path) != expected_sha:
        raise ClaimIDDurableReplayAttachError(
            "pin_mismatch", f"pinned file hash mismatch: {relative_path}"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return _decode_json_bytes(_read_bytes(path, "pinned_file"), "pinned_file")


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ClaimIDDurableReplayAttachError(
            "pin_unavailable", f"pinned file cannot be read: {path}"
        ) from exc


def _require_sha256(value: bytes, expected: str, code: str) -> None:
    if hashlib.sha256(value).hexdigest() != expected:
        raise ClaimIDDurableReplayAttachError(
            code, "input bytes do not match the frozen SHA-256"
        )


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_PATTERN.fullmatch(value))


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value
