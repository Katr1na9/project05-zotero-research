"""Authority-gated fail-closed adapter for planner_experiment_inputs.

The adapter requires an in-memory, activated, single-use execute authority,
validates one frozen M1 contract, and then delegates the public projection to
the existing M0 rule compiler.  It never mints Claim-IDs, writes files,
invokes the mint executor, or changes admission/Kernel state.
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
    "a0627ff3bb4b339336ba0aa1347c90a58a46526cdb84359d03a8e515546c7d98"
)
M1_FRAMEWORK_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-multi-adapter-framework-design-v0.1-20260724.json"
)
M1_FRAMEWORK_SHA256 = (
    "791520b4779f8c0cce12e35cc282bb4c1e7092a9e5d8062c6be67d3a8118cfa2"
)
SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
COMPILER_PATH = "src/compiler/llm/m0_rule_compiler.py"
COMPILER_SHA256 = (
    "2a0fd4371b8066ddb453a6ae6edb94c72d6ff2c90a9cf6413404b071fc393e57"
)
PROJECTION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-m0-depth2-public-field-projection-v0.1-20260724.json"
)
PROJECTION_SHA256 = (
    "4784ff3a29f2c3cb8d04bc187b1f2cd1d95b9ead51c3ad0d7c4da30f4cd557e8"
)
MAPPING_SHA256 = (
    "83d6a685a92dadc8ce0c05ecdd97931a56a207eebaf3c8193201a1daee38c070"
)
AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-planner-inputs-single-execute-authority-design-v0.1-20260724.json"
)
AUTHORITY_DESIGN_SHA256 = (
    "e09b51e4aa01758cbe481c6ecf7e6c14aa0c683f209f9a04f61d1890f4a15e37"
)
ADAPTER_DISPOSITION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-planner-inputs-adapter-implementation-disposition-v0.1-20260724.json"
)
ADAPTER_DISPOSITION_SHA256 = (
    "a891fd1f7b015a4ad50f198864543ae5d0eea2fcd2ade56728e19e33c1c6f700"
)
ADAPTER_IMPLEMENTATION_PATH = "src/compiler/llm/m1_planner_inputs_adapter.py"

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
_EXPECTED_AUTHORITY_FIELDS = frozenset(
    {
        "status",
        "target",
        "pinned_hashes",
        "pinned_inputs",
        "reserved_result_path",
        "execute_ledger",
        "output_policy",
        "still_blocked",
    }
)
_EXPECTED_EXECUTE_LEDGER = {
    "authorized": 1,
    "maximum": 1,
    "started": 0,
    "consumed": 0,
    "remaining": 1,
    "retry": False,
    "resume": False,
    "fallback": False,
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "in_memory_structural_only",
    "file_write": False,
    "mint": False,
    "kernel_write": False,
    "admission": False,
}
_EXPECTED_STILL_BLOCKED = {
    "production_claim_id_mint": True,
    "kernel_write": True,
    "e_case_write": True,
    "certificate_generation": True,
    "admission": True,
    "catalog_write": True,
    "source_role_assignment": True,
    "lineage_credit": True,
    "quota_credit": True,
    "l2_gate_change": True,
    "m2_implementation_or_fit": True,
    "four_family_llm_finetune": True,
    "registry_permanent_effect": True,
}
_FORBIDDEN_AUTHORITY_KEYS = frozenset(
    {
        "key",
        "key_bytes",
        "key_material",
        "hmac_key",
        "secret",
        "secret_bytes",
        "credential",
        "credentials",
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
        (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
        (ADAPTER_DISPOSITION_PATH, ADAPTER_DISPOSITION_SHA256),
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

    _validate_authority_design(repo_root)
    _validate_adapter_disposition(repo_root)


def adapt_planner_projection(
    descriptor: Mapping[str, Any],
    projection: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Authorize, validate, and compile one planner public projection.

    The returned object is exactly the existing M0 structural package.  No
    adapter metadata is appended because the published Claim IR schema is
    closed to additional package properties.
    """

    verify_adapter_pins(repo_root)
    _validate_execute_authority(
        authority,
        descriptor=descriptor,
        projection=projection,
        repo_root=repo_root,
    )
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
    authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compatibility alias for callers that name the adapter handoff compile."""

    return adapt_planner_projection(
        descriptor,
        projection,
        repo_root=repo_root,
        authority=authority,
    )


def _validate_authority_design(repo_root: Path) -> None:
    design = _load_json(repo_root / AUTHORITY_DESIGN_PATH)
    if not isinstance(design, Mapping):
        raise M1AdapterError("authority_design_shape", "authority design must be an object")
    _require_constant(
        design.get("status"),
        "design_only_execute_authority_not_activated",
        "authority_design.status",
    )
    _require_constant(
        design.get("artifact_type"),
        "m1_planner_inputs_single_execute_authority_design",
        "authority_design.artifact_type",
    )

    scope = design.get("scope")
    if not isinstance(scope, Mapping):
        raise M1AdapterError("authority_design_shape", "authority design scope is missing")
    for field, expected in (
        ("surface_id", SURFACE_ID),
        ("only_input_surface", True),
        ("adapter_id", ADAPTER_ID),
        ("source_class", SOURCE_CLASS),
        ("certificate_surface", "vacant"),
        ("permanent_registry_effect", False),
    ):
        _require_constant(scope.get(field), expected, f"authority_design.scope.{field}")

    chain = design.get("pinned_authority_chain")
    if not isinstance(chain, Mapping):
        raise M1AdapterError("authority_design_pins", "authority design chain is missing")
    for key, expected_path, expected_sha in (
        ("m1_framework", M1_FRAMEWORK_PATH, M1_FRAMEWORK_SHA256),
        ("planner_adapter_contract", CONTRACT_PATH, CONTRACT_SHA256),
        (
            "planner_adapter_disposition",
            ADAPTER_DISPOSITION_PATH,
            ADAPTER_DISPOSITION_SHA256,
        ),
        ("claim_ir_schema", SCHEMA_PATH, SCHEMA_SHA256),
        ("m0_rule_compiler", COMPILER_PATH, COMPILER_SHA256),
        ("m0_projection", PROJECTION_PATH, PROJECTION_SHA256),
    ):
        _require_pin_record(
            chain.get(key),
            expected_path,
            expected_sha,
            f"authority_design.pinned_authority_chain.{key}",
        )
    implementation = chain.get("planner_adapter_implementation")
    if (
        not isinstance(implementation, Mapping)
        or implementation.get("path") != ADAPTER_IMPLEMENTATION_PATH
        or implementation.get("sha256")
        != "40b68761fa56c01327427b1e096b05785a58b545f8dc6e53df25a2100f6cf8fb"
    ):
        raise M1AdapterError(
            "authority_design_pins",
            "authority design does not pin the pre-gate adapter lineage",
        )

    current = design.get("current_authorization_state")
    expected_current = {
        "authority_activated": False,
        "adapter_execute_authorized_now": 0,
        "adapter_execute_started": 0,
        "adapter_execute_consumed": 0,
        "adapter_execute_remaining": 0,
        "registry_activated": False,
        "adapter_registered_effective": False,
        "execution_performed": False,
    }
    if not isinstance(current, Mapping):
        raise M1AdapterError("authority_design_state", "current authorization state is missing")
    for field, expected in expected_current.items():
        _require_constant(
            current.get(field),
            expected,
            f"authority_design.current_authorization_state.{field}",
        )

    future = design.get("future_activation_shape")
    if not isinstance(future, Mapping):
        raise M1AdapterError("authority_design_shape", "future activation shape is missing")
    _require_constant(
        future.get("status"),
        "activated_single_adapter_execute_authorized",
        "authority_design.future_activation_shape.status",
    )
    _require_typed_mapping(
        future.get("target"),
        {
            "surface_id": SURFACE_ID,
            "adapter_id": ADAPTER_ID,
            "source_class": SOURCE_CLASS,
            "only_target": True,
        },
        "authority_design.future_activation_shape.target",
        "authority_design_shape",
    )
    _require_typed_mapping(
        future.get("execute_ledger"),
        _EXPECTED_EXECUTE_LEDGER,
        "authority_design.future_activation_shape.execute_ledger",
        "authority_design_state",
    )
    _require_constant(
        future.get("activation_created_now"),
        False,
        "authority_design.future_activation_shape.activation_created_now",
    )
    _require_constant(
        future.get("execute_authorized_now_by_this_design"),
        False,
        "authority_design.future_activation_shape.execute_authorized_now_by_this_design",
    )

    integrity = design.get("activation_integrity_rules")
    if not isinstance(integrity, Mapping):
        raise M1AdapterError("authority_design_shape", "activation integrity rules are missing")
    _require_constant(
        integrity.get("adapter_contract_status_must_remain"),
        "design_only_adapter_not_registered",
        "authority_design.activation_integrity_rules.adapter_contract_status_must_remain",
    )
    for field in (
        "editing_adapter_contract_status_to_simulate_activation",
        "editing_m1_framework_status_to_simulate_activation",
        "in_place_activation_of_this_design",
        "registry_permanence_from_single_execute",
        "adapter_effective_registration_from_single_execute",
        "activation_without_authority_artifact",
    ):
        _require_constant(
            integrity.get(field),
            False,
            f"authority_design.activation_integrity_rules.{field}",
        )

    gate = design.get("required_future_adapter_authority_gate")
    if not isinstance(gate, Mapping):
        raise M1AdapterError("authority_design_shape", "future authority gate is missing")
    for field, expected in (
        ("code_change_required_before_any_execute", True),
        ("current_adapter_must_not_be_executed_under_this_design", True),
        ("fail_closed_before_m0_handoff", True),
        ("no_authority_no_execution", True),
        ("code_implementation_authorized_by_this_design", False),
    ):
        _require_constant(
            gate.get(field),
            expected,
            f"authority_design.required_future_adapter_authority_gate.{field}",
        )


def _validate_adapter_disposition(repo_root: Path) -> None:
    disposition = _load_json(repo_root / ADAPTER_DISPOSITION_PATH)
    if not isinstance(disposition, Mapping):
        raise M1AdapterError("disposition_shape", "adapter disposition must be an object")
    _require_constant(
        disposition.get("status"),
        "draft_disposition_not_effective",
        "adapter_disposition.status",
    )
    scope = disposition.get("scope")
    if not isinstance(scope, Mapping):
        raise M1AdapterError("disposition_shape", "adapter disposition scope is missing")
    for field, expected in (
        ("surface_id", SURFACE_ID),
        ("only_input_surface", True),
        ("adapter_id", ADAPTER_ID),
        ("source_class", SOURCE_CLASS),
        ("certificate_surface", "vacant"),
    ):
        _require_constant(scope.get(field), expected, f"adapter_disposition.scope.{field}")
    registry = disposition.get("registry_and_effective_status")
    if not isinstance(registry, Mapping):
        raise M1AdapterError("disposition_shape", "registry disposition is missing")
    for field, expected in (
        ("registry_activated", False),
        ("adapter_registered_effective", False),
        ("adapter_contract_effective", False),
        ("adapter_execution_authorized", False),
        ("contract_status_remains", "design_only_adapter_not_registered"),
        ("contract_is_frozen_pin_not_execution_authority", True),
    ):
        _require_constant(
            registry.get(field),
            expected,
            f"adapter_disposition.registry_and_effective_status.{field}",
        )


def _validate_execute_authority(
    authority: Mapping[str, Any] | None,
    *,
    descriptor: Mapping[str, Any],
    projection: Mapping[str, Any],
    repo_root: Path,
) -> None:
    if authority is None:
        raise M1AdapterError(
            "missing_authority",
            "an activated single-use adapter execute authority is required",
        )
    if not isinstance(authority, Mapping):
        raise M1AdapterError("authority_type", "adapter execute authority must be an object")
    _reject_forbidden_authority_keys(authority)
    if set(authority) != _EXPECTED_AUTHORITY_FIELDS:
        raise M1AdapterError(
            "authority_shape",
            "adapter execute authority fields are not canonical",
        )
    if authority.get("status") != "activated_single_adapter_execute_authorized":
        raise M1AdapterError("not_activated", "adapter execute authority is not activated")

    _require_typed_mapping(
        authority.get("target"),
        {
            "surface_id": SURFACE_ID,
            "adapter_id": ADAPTER_ID,
            "source_class": SOURCE_CLASS,
            "only_target": True,
        },
        "authority.target",
        "authority_target",
    )
    expected_pins = {
        "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
        "m1_framework_sha256": M1_FRAMEWORK_SHA256,
        "adapter_contract_sha256": CONTRACT_SHA256,
        "adapter_implementation_sha256": _sha256(repo_root / ADAPTER_IMPLEMENTATION_PATH),
        "adapter_disposition_sha256": ADAPTER_DISPOSITION_SHA256,
        "schema_sha256": SCHEMA_SHA256,
        "m0_compiler_sha256": COMPILER_SHA256,
        "projection_sha256": PROJECTION_SHA256,
    }
    _require_typed_mapping(
        authority.get("pinned_hashes"),
        expected_pins,
        "authority.pinned_hashes",
        "authority_pin",
    )
    expected_inputs = {
        "descriptor_sha256": _canonical_json_sha256(descriptor),
        "public_projection_sha256": _canonical_json_sha256(projection),
    }
    _require_typed_mapping(
        authority.get("pinned_inputs"),
        expected_inputs,
        "authority.pinned_inputs",
        "authority_input",
    )
    _validate_reserved_result_path(authority.get("reserved_result_path"), repo_root)
    _require_typed_mapping(
        authority.get("execute_ledger"),
        _EXPECTED_EXECUTE_LEDGER,
        "authority.execute_ledger",
        "authority_ledger",
    )
    _require_typed_mapping(
        authority.get("output_policy"),
        _EXPECTED_OUTPUT_POLICY,
        "authority.output_policy",
        "authority_boundary",
    )
    _require_typed_mapping(
        authority.get("still_blocked"),
        _EXPECTED_STILL_BLOCKED,
        "authority.still_blocked",
        "authority_boundary",
    )


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


def _reject_forbidden_authority_keys(
    value: Any,
    path: tuple[str, ...] = (),
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            field_path = ".".join((*path, str(key)))
            if normalized in _FORBIDDEN_AUTHORITY_KEYS:
                raise M1AdapterError(
                    "secret_in_authority",
                    f"secret or credential field is forbidden: {field_path}",
                )
            _reject_forbidden_authority_keys(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_forbidden_authority_keys(nested, (*path, str(index)))


def _validate_reserved_result_path(value: Any, repo_root: Path) -> None:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or "\x00" in value
    ):
        raise M1AdapterError(
            "authority_result_path",
            "reserved result path must be a non-empty repository-relative POSIX path",
        )
    relative = Path(value)
    if (
        relative.is_absolute()
        or relative.drive
        or relative.suffix.casefold() != ".json"
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise M1AdapterError(
            "authority_result_path",
            "reserved result path is not a safe JSON path",
        )
    resolved_root = repo_root.resolve()
    resolved = (resolved_root / relative).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise M1AdapterError(
            "authority_result_path",
            "reserved result path escapes the repository",
        ) from exc
    if resolved.exists():
        raise M1AdapterError(
            "result_exists",
            "the authority's unique structural result path already exists",
        )


def _canonical_json_sha256(value: Any) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise M1AdapterError(
            "authority_input",
            "authority-pinned input is not canonical JSON",
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def _require_typed_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    error_code: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise M1AdapterError(error_code, f"{field} does not match the frozen shape")
    for key, expected_value in expected.items():
        actual_value = value.get(key)
        if actual_value != expected_value or type(actual_value) is not type(expected_value):
            raise M1AdapterError(
                error_code,
                f"{field}.{key} does not match the frozen value",
            )


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
