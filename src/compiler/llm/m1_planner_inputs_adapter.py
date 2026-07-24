"""Fail-closed structural adapter for planner_experiment_inputs.

The adapter validates one frozen M1 contract and then delegates the public
projection to the existing M0 rule compiler.  It never mints Claim-IDs,
writes files, invokes the mint executor, or changes admission/Kernel state.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from compiler.llm.m0_rule_compiler import (
    M0CompilerError,
    compile_public_projection,
    verify_pins as verify_m0_pins,
)


SURFACE_ID = "project05_depth2_public"
SOURCE_CLASS = "planner_experiment_inputs"
ADAPTER_ID = "m1a_planner_inputs_v0_1"
ADAPTER_VERSION = "0.1.0"

CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-planner-experiment-inputs-adapter-contract-v0.1-20260724.json"
)
CONTRACT_SHA256 = (
    "b9dbbb471bc69932bd6ef81e9824f492fb382125f7c5ef361153c4bf428c4eca"
)
M1_FRAMEWORK_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-multi-adapter-framework-design-v0.1-20260724.json"
)
M1_FRAMEWORK_SHA256 = (
    "a220eafde5eb0c38c381a23ba80e22571edfe932fca401a0e240ec562bb199dc"
)
SCHEMA_PATH = "schemas/claim-ir-kernel.schema.json"
SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
COMPILER_PATH = "src/compiler/llm/m0_rule_compiler.py"
COMPILER_SHA256 = (
    "a132dd140ab13e3fe762f169b8799b4e35886ecf8ea07271e8482a1046c14de1"
)
PROJECTION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-m0-depth2-public-field-projection-v0.1-20260724.json"
)
PROJECTION_SHA256 = (
    "4784ff3a29f2c3cb8d04bc187b1f2cd1d95b9ead51c3ad0d7c4da30f4cd557e8"
)
MAPPING_SHA256 = (
    "c9ed6df54c0f23389a33679abac8d80929eee2dc290885975878f14d92b77799"
)

_EXPECTED_DESCRIPTOR_FIELDS = frozenset(
    {
        "surface_id",
        "source_class",
        "adapter_id",
        "adapter_version",
        "opaque_record_reference",
        "declared_source_fields",
    }
)
_FORBIDDEN_KEYS = frozenset(
    {
        "label",
        "labels",
        "class",
        "attack",
        "technique",
        "verdict",
        "realized_outcome",
        "realized_outcomes",
        "realized_recovery",
        "actual_recovered_claims",
        "recoverable_claim_ids",
        "hidden_claim_ids",
        "required_claim_ids",
        "recovered_claim_ids",
        "oracle",
        "oracle_path",
        "mask_strategy",
        "mask_intensity",
        "mask_membership",
        "random_seed",
        "run_id",
        "actions_taken",
        "action_feedback",
        "recovered_count",
        "private_evidence",
        "hidden_evidence",
        "credentials",
        "credential",
        "secrets",
        "secret",
        "private_key",
        "hmac_key",
        "raw_path",
        "filesystem_path",
        "archive_member_path",
        "member_path",
        "payload",
        "payload_bytes",
        "raw_payload",
    }
)
_OPAQUE_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_ADAPTER_ID_PATTERN = re.compile(r"^m1a_[a-z0-9_-]{1,48}$")
_FORBIDDEN_REFERENCE_TOKENS = (
    "label",
    "verdict",
    "outcome",
    "oracle",
    "mask",
    "payload",
    "secret",
    "credential",
    "private",
    "hidden",
    "recoverable",
    "path",
    "archive",
)


class M1AdapterError(ValueError):
    """Raised when the planner adapter fails a closed boundary."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def verify_adapter_pins(repo_root: Path) -> None:
    """Verify the adapter contract and every inherited M0/M1 pin."""

    repo_root = repo_root.resolve()
    for relative_path, expected_sha in (
        (CONTRACT_PATH, CONTRACT_SHA256),
        (M1_FRAMEWORK_PATH, M1_FRAMEWORK_SHA256),
        (SCHEMA_PATH, SCHEMA_SHA256),
        (COMPILER_PATH, COMPILER_SHA256),
        (PROJECTION_PATH, PROJECTION_SHA256),
    ):
        _verify_pin(repo_root, relative_path, expected_sha)

    try:
        verify_m0_pins(repo_root)
    except M0CompilerError as exc:
        raise M1AdapterError("m0_pin_mismatch", str(exc)) from exc

    contract = _load_json(repo_root / CONTRACT_PATH)
    if not isinstance(contract, Mapping):
        raise M1AdapterError("contract_shape", "adapter contract must be an object")
    _require_constant(
        contract.get("status"),
        "design_only_adapter_not_registered",
        "contract.status",
    )
    _require_constant(
        contract.get("artifact_type"),
        "m1_adapter_contract_design",
        "contract.artifact_type",
    )
    identity = contract.get("adapter_identity")
    if not isinstance(identity, Mapping):
        raise M1AdapterError("contract_shape", "adapter identity is missing")
    for field, expected in (
        ("adapter_id", ADAPTER_ID),
        ("adapter_version", ADAPTER_VERSION),
        ("source_class", SOURCE_CLASS),
        ("surface_id", SURFACE_ID),
    ):
        _require_constant(identity.get(field), expected, f"contract.adapter_identity.{field}")
    _require_constant(identity.get("only_surface"), True, "contract.adapter_identity.only_surface")
    _require_constant(
        identity.get("certificate_surface"),
        "vacant",
        "contract.adapter_identity.certificate_surface",
    )
    if not _ADAPTER_ID_PATTERN.fullmatch(ADAPTER_ID):
        raise M1AdapterError("adapter_id", "adapter ID does not satisfy the frozen pattern")

    registry_state = contract.get("registry_state")
    if not isinstance(registry_state, Mapping) or dict(registry_state) != {
        "adapter_registered": False,
        "adapter_implementation_authorized": False,
        "adapter_execution_authorized": False,
        "registry_activation_authorized": False,
    }:
        raise M1AdapterError("registry_state", "adapter contract is not unregistered and inactive")

    pins = contract.get("inherited_framework_pins")
    if not isinstance(pins, Mapping):
        raise M1AdapterError("contract_pins", "inherited framework pins are missing")
    _require_pin_record(
        pins.get("m1_framework_design"),
        M1_FRAMEWORK_PATH,
        M1_FRAMEWORK_SHA256,
        "contract.inherited_framework_pins.m1_framework_design",
    )
    _require_pin_record(
        pins.get("claim_ir_schema"),
        SCHEMA_PATH,
        SCHEMA_SHA256,
        "contract.inherited_framework_pins.claim_ir_schema",
    )
    _require_pin_record(
        pins.get("m0_rule_compiler"),
        COMPILER_PATH,
        COMPILER_SHA256,
        "contract.inherited_framework_pins.m0_rule_compiler",
    )
    _require_pin_record(
        pins.get("m0_depth2_public_projection"),
        PROJECTION_PATH,
        PROJECTION_SHA256,
        "contract.inherited_framework_pins.m0_depth2_public_projection",
    )
    mapping_record = pins.get("source_field_slot_mapping")
    if (
        not isinstance(mapping_record, Mapping)
        or mapping_record.get("sha256") != MAPPING_SHA256
    ):
        raise M1AdapterError("contract_pins", "source-field mapping pin is not frozen")

    input_contract = contract.get("input_contract")
    if not isinstance(input_contract, Mapping):
        raise M1AdapterError("contract_shape", "input contract is missing")
    _require_constant(
        input_contract.get("accepted_surface_id"),
        SURFACE_ID,
        "contract.input_contract.accepted_surface_id",
    )
    _require_constant(
        input_contract.get("accepted_source_class"),
        SOURCE_CLASS,
        "contract.input_contract.accepted_source_class",
    )
    output_contract = contract.get("output_contract")
    if not isinstance(output_contract, Mapping):
        raise M1AdapterError("contract_shape", "output contract is missing")
    fixed = output_contract.get("fixed_state_values")
    if not isinstance(fixed, Mapping) or dict(fixed) != {
        "surface_id": SURFACE_ID,
        "claim_id": None,
        "claim_id_state": "not_minted",
        "admission_state": "not_admitted",
        "kernel_state": "pending_kernel_schema",
    }:
        raise M1AdapterError("contract_boundary", "structural output states are not frozen")
    handoff = contract.get("m0_handoff_boundary")
    if (
        not isinstance(handoff, Mapping)
        or handoff.get("kernel_ingestion_authorized") is not False
        or handoff.get("mint_authorized") is not False
        or handoff.get("admission_authorized") is not False
    ):
        raise M1AdapterError("contract_boundary", "M0 handoff is not blocked")

    framework = _load_json(repo_root / M1_FRAMEWORK_PATH)
    if not isinstance(framework, Mapping):
        raise M1AdapterError("framework_shape", "M1 framework must be an object")
    _require_constant(
        framework.get("status"),
        "design_only_m1_not_authorized",
        "m1_framework.status",
    )
    scope = framework.get("scope")
    if not isinstance(scope, Mapping) or scope.get("surface_id") != SURFACE_ID:
        raise M1AdapterError("framework_surface", "M1 framework surface is not pinned")
    non_auth = framework.get("explicit_non_authorizations")
    if (
        not isinstance(non_auth, Mapping)
        or non_auth.get("m1_code_implementation") is not False
        or non_auth.get("adapter_execution") is not False
    ):
        raise M1AdapterError("framework_boundary", "M1 framework implementation boundary is not closed")


def adapt_planner_projection(
    descriptor: Mapping[str, Any],
    projection: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Validate one planner descriptor and compile its public projection.

    The returned object is exactly the existing M0 structural package.  No
    adapter metadata is appended because the published Claim IR schema is
    closed to additional package properties.
    """

    verify_adapter_pins(repo_root)
    source_fields = _schema_source_fields(repo_root / SCHEMA_PATH)
    _validate_descriptor(descriptor, source_fields)
    _reject_forbidden_keys(projection)
    _reject_forbidden_values(projection)
    try:
        package = compile_public_projection(projection, repo_root=repo_root)
    except M0CompilerError as exc:
        raise M1AdapterError(exc.code, str(exc)) from exc

    actual_fields = {
        claim["source_field"] for claim in package["claims"]
    }
    declared_fields = descriptor["declared_source_fields"]
    if set(declared_fields) != actual_fields:
        raise M1AdapterError(
            "declared_fields_mismatch",
            "declared_source_fields must match the projection's allowlisted fields",
        )
    _require_structural_states(package)
    return package


def compile_planner_projection(
    descriptor: Mapping[str, Any],
    projection: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Compatibility alias for callers that name the adapter handoff compile."""

    return adapt_planner_projection(descriptor, projection, repo_root=repo_root)


def _validate_descriptor(
    descriptor: Mapping[str, Any],
    source_fields: tuple[str, ...],
) -> None:
    if not isinstance(descriptor, Mapping):
        raise M1AdapterError("descriptor_type", "adapter descriptor must be an object")
    if set(descriptor) != _EXPECTED_DESCRIPTOR_FIELDS:
        raise M1AdapterError(
            "descriptor_shape",
            "descriptor fields must match the frozen contract exactly",
        )
    for field, expected in (
        ("surface_id", SURFACE_ID),
        ("source_class", SOURCE_CLASS),
        ("adapter_id", ADAPTER_ID),
        ("adapter_version", ADAPTER_VERSION),
    ):
        _require_constant(descriptor.get(field), expected, f"descriptor.{field}")

    reference = descriptor.get("opaque_record_reference")
    if (
        not isinstance(reference, str)
        or not _OPAQUE_REFERENCE_PATTERN.fullmatch(reference)
        or _contains_forbidden_reference_token(reference)
    ):
        raise M1AdapterError(
            "opaque_reference",
            "opaque_record_reference is not a safe non-semantic reference",
        )

    declared = descriptor.get("declared_source_fields")
    if not isinstance(declared, list) or not declared:
        raise M1AdapterError(
            "declared_fields_shape",
            "declared_source_fields must be a non-empty array",
        )
    if any(not isinstance(field, str) or field not in source_fields for field in declared):
        raise M1AdapterError(
            "unknown_source_field",
            "declared_source_fields contains an unknown or unmapped field",
        )
    if len(declared) > len(source_fields) or len(set(declared)) != len(declared):
        raise M1AdapterError(
            "declared_fields_duplicate",
            "declared_source_fields must be unique and bounded",
        )
    source_order = {field: index for index, field in enumerate(source_fields)}
    if declared != sorted(declared, key=source_order.__getitem__):
        raise M1AdapterError(
            "declared_fields_order",
            "declared_source_fields must use the pinned schema order",
        )


def _require_structural_states(package: Mapping[str, Any]) -> None:
    for field, expected in (
        ("surface_id", SURFACE_ID),
        ("claim_id_state", "not_minted"),
        ("admission_state", "not_admitted"),
        ("kernel_state", "pending_kernel_schema"),
    ):
        _require_constant(package.get(field), expected, f"package.{field}")
    claims = package.get("claims")
    if not isinstance(claims, list) or not claims:
        raise M1AdapterError("package_shape", "M0 output contains no claims")
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise M1AdapterError("package_shape", "M0 output claim is not an object")
        _require_constant(claim.get("claim_id"), None, "claim.claim_id")
        _require_constant(claim.get("claim_id_state"), "not_minted", "claim.claim_id_state")
        _require_constant(claim.get("admission_state"), "not_admitted", "claim.admission_state")


def _schema_source_fields(schema_path: Path) -> tuple[str, ...]:
    schema = _load_json(schema_path)
    try:
        fields = schema["$defs"]["source_field"]["enum"]
    except (KeyError, TypeError) as exc:
        raise M1AdapterError("schema_shape", "source_field enum is unavailable") from exc
    if (
        not isinstance(fields, list)
        or len(fields) != 38
        or any(not isinstance(field, str) for field in fields)
        or len(set(fields)) != 38
    ):
        raise M1AdapterError("schema_shape", "source_field enum must contain 38 unique strings")
    return tuple(fields)


def _reject_forbidden_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            field_path = ".".join((*path, str(key)))
            if normalized in _FORBIDDEN_KEYS:
                raise M1AdapterError("forbidden_field", f"forbidden field: {field_path}")
            _reject_forbidden_keys(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_forbidden_keys(nested, (*path, str(index)))


def _reject_forbidden_values(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, (bytes, bytearray)):
        raise M1AdapterError(
            "raw_payload",
            f"raw payload bytes are forbidden at {'.'.join(path) or '<root>'}",
        )
    if isinstance(value, str):
        if "/" in value or "\\" in value or value.casefold().startswith("file:"):
            raise M1AdapterError(
                "raw_path",
                f"path-like value is forbidden at {'.'.join(path) or '<root>'}",
            )
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _reject_forbidden_values(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_forbidden_values(nested, (*path, str(index)))


def _contains_forbidden_reference_token(value: str) -> bool:
    lowered = value.casefold()
    return any(token in lowered for token in _FORBIDDEN_REFERENCE_TOKENS)


def _require_pin_record(
    value: Any,
    expected_path: str,
    expected_sha: str,
    field: str,
) -> None:
    if (
        not isinstance(value, Mapping)
        or value.get("path") != expected_path
        or value.get("sha256") != expected_sha
    ):
        raise M1AdapterError("contract_pins", f"{field} does not match the frozen pin")


def _require_constant(value: Any, expected: Any, field: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise M1AdapterError("state_mismatch", f"{field} must equal {expected!r}")


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise M1AdapterError("pin_missing", f"pinned file missing: {relative_path}")
    if _sha256(path) != expected_sha:
        raise M1AdapterError("pin_mismatch", f"pinned SHA mismatch: {relative_path}")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise M1AdapterError("json_read", f"cannot read JSON artifact: {path.name}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise M1AdapterError("pin_read", f"cannot read pinned artifact: {path.name}") from exc
    return digest.hexdigest()


def _normalize_key(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")
