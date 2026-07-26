"""Authority-gated, fail-closed adapter for a pinned unminted Claim-IR fixture.

The only executable authority supported here is an explicit test-only,
in-memory authority.  The adapter never activates a registry, resolves a
request-supplied path or URI, writes a file, mints a Claim-ID, or advances
admission/Kernel/certificate/STOP state.
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
SOURCE_CLASS = "claim_ir_valid_fixture"
ADAPTER_ID = "m1a_claim_ir_valid_fixture_v0_1"
ADAPTER_VERSION = "0.1.0"
TEST_AUTHORITY_STATUS = "activated_test_only_in_memory_fixture_authority"
FORBIDDEN_MINTED_PACKAGE_ID = "pkg_73d77b55ef6a517a0dc528f7f3a89bd9"

CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-claim-ir-valid-fixture-adapter-contract-"
    "v0.1-20260726.json"
)
CONTRACT_SHA256 = (
    "a889a99b7a2bec340221d8cdc25b2b0cbe5f61525539a58e4db4d8214d0e1ebd"
)
SELECTION_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-dual-adapter-exact-selection-design-v0.1-20260726.json"
)
SELECTION_DESIGN_SHA256 = (
    "ae164d538a0c95a89fafcbd579372332226622d4bbfbe1bf2913529d3cf7694a"
)
RED_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-m1-second-adapter-claim-ir-valid-fixture-red-owner-acceptance-"
    "v0.1-20260726.json"
)
RED_ACCEPTANCE_SHA256 = (
    "0acaa3fb6daaa31f85e24e1f1cd1fdc245de4a4eba6ca56dcf8e30236ab016a3"
)
M1_FRAMEWORK_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-multi-adapter-framework-design-v0.1-20260724.json"
)
M1_FRAMEWORK_SHA256 = (
    "791520b4779f8c0cce12e35cc282bb4c1e7092a9e5d8062c6be67d3a8118cfa2"
)
EXTERNAL_SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
EXTERNAL_SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
EXTERNAL_SCHEMA_ID = "claim-ir-external-v0.1"
EXTERNAL_SCHEMA_DOCUMENT_ID = (
    "https://project05.invalid/schemas/claim-ir-kernel.schema.json"
)
KERNEL_SCHEMA_PATH = "schemas/claim-ir-kernel.schema.json"
KERNEL_SCHEMA_SHA256 = (
    "7c6fa2db0b75d69340be5a8843ba0c373e2d5b25b0d37cf8f1d1c416a787865d"
)
CONSUMER_CONTRACT_PATH = (
    "docs/kernel/"
    "kernel-v0.8-shared-claim-ir-consumer-contract-effective-v0.1-20260725.json"
)
CONSUMER_CONTRACT_SHA256 = (
    "a2a176fdeb2b93205a7f5e11c7c096236e2dc582d1c31f8f4a1534866c008d63"
)
M0_COMPILER_PATH = "src/compiler/llm/m0_rule_compiler.py"
M0_COMPILER_SHA256 = (
    "2a0fd4371b8066ddb453a6ae6edb94c72d6ff2c90a9cf6413404b071fc393e57"
)
PROJECTION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-m0-depth2-public-field-projection-"
    "v0.1-20260724.json"
)
PROJECTION_SHA256 = (
    "4784ff3a29f2c3cb8d04bc187b1f2cd1d95b9ead51c3ad0d7c4da30f4cd557e8"
)
MAPPING_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-source-field-slot-mapping-design-"
    "v0.1-20260724.json"
)
MAPPING_SHA256 = (
    "83d6a685a92dadc8ce0c05ecdd97931a56a207eebaf3c8193201a1daee38c070"
)
PLANNER_IMPLEMENTATION_PATH = "src/compiler/llm/m1_planner_inputs_adapter.py"
PLANNER_IMPLEMENTATION_SHA256 = (
    "ae5c6db06a523ef6a4e384a118e1dcff7f0694d2b3f0e6f87a7dc7b2252d67f0"
)
ADAPTER_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_claim_ir_valid_fixture_adapter.py"
)

_EXPECTED_DESCRIPTOR_FIELDS = frozenset(
    {
        "surface_id",
        "source_class",
        "adapter_id",
        "adapter_version",
        "opaque_fixture_reference",
        "fixture_pin_declaration",
        "declared_claim_ir_fields",
    }
)
_EXPECTED_FIXTURE_PIN_FIELDS = frozenset(
    {
        "fixture_id",
        "fixture_content_sha256",
        "claim_ir_schema_id",
        "claim_ir_schema_sha256",
        "projection_sha256",
        "content_hash",
    }
)
_EXPECTED_DECLARATION_FIELDS = frozenset(
    {
        "schema_version",
        "package_id",
        "surface_id",
        "kernel_state",
        "claim_id_state",
        "admission_state",
        "projection_sha256",
        "claim_count",
        "field_path_set",
        "content_hash",
    }
)
_EXPECTED_REGISTRY_RECORD_FIELDS = frozenset(
    {
        "fixture_id",
        "surface_id",
        "source_class",
        "fixture_content_sha256",
        "claim_ir_schema_sha256",
        "fixture",
        "test_only",
    }
)
_EXPECTED_AUTHORITY_FIELDS = frozenset(
    {
        "status",
        "scope",
        "pinned_hashes",
        "pinned_inputs",
        "output_policy",
        "still_blocked",
    }
)
_EXPECTED_OUTPUT_POLICY = {
    "mode": "in_memory_structural_only",
    "file_write": False,
    "mint": False,
    "kernel_write": False,
    "e_case_write": False,
    "certificate": False,
    "certified_stop": False,
    "admission": False,
}
_EXPECTED_STILL_BLOCKED = {
    "effective_registry_activation": True,
    "production_single_execute": True,
    "claim_id_mint": True,
    "kernel_store_write": True,
    "e_case_write": True,
    "certificate_generation": True,
    "certified_stop": True,
    "durable_attach": True,
    "checker_non_null": True,
    "evidence_sufficiency_non_null": True,
    "production_registration_enablement": True,
    "l2_gate_change": True,
    "part_b_elevation": True,
    "m2": True,
    "four_family_finetune_or_kernel_admission": True,
}
_OPAQUE_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
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
    "uri",
    "http",
)
_FORBIDDEN_DESCRIPTOR_KEYS = frozenset(
    {
        "path",
        "filesystem_path",
        "archive_member_path",
        "uri",
        "url",
        "endpoint",
        "raw_bytes",
        "raw_claim_ir",
        "raw_payload",
        "payload",
        "payload_bytes",
        "label",
        "labels",
        "ground_truth",
        "verdict",
        "realized_outcome",
        "oracle",
        "oracle_path",
        "mask_membership",
        "secret",
        "secrets",
        "credential",
        "credentials",
        "private_key",
        "hidden_claim_ids",
        "recoverable_claim_ids",
    }
)
_FORBIDDEN_AUTHORITY_KEYS = frozenset(
    {
        "execute_ledger",
        "activation_ledger",
        "single_execute_activation",
        "key",
        "key_bytes",
        "key_material",
        "hmac_key",
        "secret",
        "credential",
        "credentials",
    }
)
_FORBIDDEN_FIXTURE_VALUE_TOKENS = (
    "ground_truth",
    "realized_outcome",
    "oracle",
    "mask_membership",
    "hidden_claim",
    "recoverable_claim",
    "private_key",
    "credential",
    "secret",
)


class M1ClaimIRValidFixtureAdapterError(ValueError):
    """Raised when the valid-fixture adapter fails a closed boundary."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def verify_adapter_pins(repo_root: Path) -> None:
    """Verify the RED contract, framework, schemas, and inherited boundaries."""

    root = repo_root.resolve()
    for relative_path, expected_sha in (
        (CONTRACT_PATH, CONTRACT_SHA256),
        (SELECTION_DESIGN_PATH, SELECTION_DESIGN_SHA256),
        (RED_ACCEPTANCE_PATH, RED_ACCEPTANCE_SHA256),
        (M1_FRAMEWORK_PATH, M1_FRAMEWORK_SHA256),
        (EXTERNAL_SCHEMA_PATH, EXTERNAL_SCHEMA_SHA256),
        (KERNEL_SCHEMA_PATH, KERNEL_SCHEMA_SHA256),
        (CONSUMER_CONTRACT_PATH, CONSUMER_CONTRACT_SHA256),
        (M0_COMPILER_PATH, M0_COMPILER_SHA256),
        (PROJECTION_PATH, PROJECTION_SHA256),
        (MAPPING_PATH, MAPPING_SHA256),
        (PLANNER_IMPLEMENTATION_PATH, PLANNER_IMPLEMENTATION_SHA256),
    ):
        _verify_pin(root, relative_path, expected_sha)

    contract = _load_json(root / CONTRACT_PATH)
    if not isinstance(contract, Mapping):
        raise M1ClaimIRValidFixtureAdapterError(
            "contract_shape", "adapter contract must be an object"
        )
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
        raise M1ClaimIRValidFixtureAdapterError(
            "contract_shape", "adapter identity is missing"
        )
    for field, expected in (
        ("adapter_id", ADAPTER_ID),
        ("adapter_version", ADAPTER_VERSION),
        ("source_class", SOURCE_CLASS),
        ("surface_id", SURFACE_ID),
        ("only_surface", True),
        ("certificate_surface", "vacant"),
    ):
        _require_constant(identity.get(field), expected, f"contract.adapter_identity.{field}")

    registry_state = contract.get("registry_state")
    if not isinstance(registry_state, Mapping) or dict(registry_state) != {
        "adapter_registered": False,
        "adapter_implementation_authorized": False,
        "adapter_execution_authorized": False,
        "registry_activation_authorized": False,
        "fixture_registry_active": False,
    }:
        raise M1ClaimIRValidFixtureAdapterError(
            "contract_registry_state", "contract registry state is not inactive"
        )
    inherited = contract.get("inherited_framework_pins")
    if not isinstance(inherited, Mapping):
        raise M1ClaimIRValidFixtureAdapterError(
            "contract_pins", "inherited framework pins are missing"
        )
    for key, expected_path, expected_sha in (
        ("m1_framework_design", M1_FRAMEWORK_PATH, M1_FRAMEWORK_SHA256),
        ("claim_ir_external_schema", EXTERNAL_SCHEMA_PATH, EXTERNAL_SCHEMA_SHA256),
        ("claim_ir_kernel_schema", KERNEL_SCHEMA_PATH, KERNEL_SCHEMA_SHA256),
        ("kernel_consumer_contract", CONSUMER_CONTRACT_PATH, CONSUMER_CONTRACT_SHA256),
        ("m0_rule_compiler", M0_COMPILER_PATH, M0_COMPILER_SHA256),
        ("m0_depth2_public_projection", PROJECTION_PATH, PROJECTION_SHA256),
        ("source_field_slot_mapping", MAPPING_PATH, MAPPING_SHA256),
    ):
        _require_pin_record(
            inherited.get(key),
            expected_path,
            expected_sha,
            f"contract.inherited_framework_pins.{key}",
        )

    input_contract = contract.get("input_contract")
    if (
        not isinstance(input_contract, Mapping)
        or input_contract.get("accepted_surface_id") != SURFACE_ID
        or input_contract.get("accepted_source_class") != SOURCE_CLASS
    ):
        raise M1ClaimIRValidFixtureAdapterError(
            "contract_input", "contract input identity is not frozen"
        )
    output_contract = contract.get("output_contract")
    fixed = (
        output_contract.get("fixed_state_values")
        if isinstance(output_contract, Mapping)
        else None
    )
    if not isinstance(fixed, Mapping) or dict(fixed) != {
        "surface_id": SURFACE_ID,
        "claim_id": None,
        "claim_id_state": "not_minted",
        "admission_state": "not_admitted",
        "kernel_state": "pending_kernel_schema",
    }:
        raise M1ClaimIRValidFixtureAdapterError(
            "contract_output", "structural output states are not frozen"
        )

    framework = _load_json(root / M1_FRAMEWORK_PATH)
    if not isinstance(framework, Mapping):
        raise M1ClaimIRValidFixtureAdapterError(
            "framework_shape", "M1 framework must be an object"
        )
    _require_constant(
        framework.get("status"),
        "design_only_m1_not_authorized",
        "framework.status",
    )
    registry = framework.get("adapter_registry_design")
    candidates = (
        registry.get("candidate_source_classes")
        if isinstance(registry, Mapping)
        else None
    )
    if (
        not isinstance(candidates, Mapping)
        or candidates.get("status") != "reference_only_not_registered"
        or SOURCE_CLASS not in candidates.get("values", [])
        or candidates.get("active_adapter_count") != 0
    ):
        raise M1ClaimIRValidFixtureAdapterError(
            "framework_registry", "fixture source class is not a frozen inactive candidate"
        )

    acceptance = _load_json(root / RED_ACCEPTANCE_PATH)
    if not isinstance(acceptance, Mapping):
        raise M1ClaimIRValidFixtureAdapterError(
            "red_acceptance_shape", "RED acceptance must be an object"
        )
    _require_constant(acceptance.get("decision"), "accept", "red_acceptance.decision")
    _require_constant(
        acceptance.get("status"),
        "red_design_accepted_implementation_execution_registry_and_git_not_authorized",
        "red_acceptance.status",
    )
    scope_note = acceptance.get("scope_note")
    if (
        not isinstance(scope_note, str)
        or "already-minted packages are out" not in scope_note
    ):
        raise M1ClaimIRValidFixtureAdapterError(
            "red_acceptance_boundary", "unminted-only scope is not pinned"
        )

    external_schema = _load_json(root / EXTERNAL_SCHEMA_PATH)
    kernel_schema = _load_json(root / KERNEL_SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(dict(external_schema))
        Draft202012Validator.check_schema(dict(kernel_schema))
    except (SchemaError, TypeError, ValueError) as exc:
        raise M1ClaimIRValidFixtureAdapterError(
            "schema_invalid", "a pinned Claim-IR schema is invalid"
        ) from exc
    _require_constant(
        external_schema.get("$id"),
        EXTERNAL_SCHEMA_DOCUMENT_ID,
        "external_schema.$id",
    )


def adapt_claim_ir_valid_fixture(
    descriptor: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
    fixture_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return one validated unminted structural envelope in memory only."""

    root = repo_root.resolve()
    verify_adapter_pins(root)
    _validate_descriptor(descriptor)
    pin_declaration = descriptor["fixture_pin_declaration"]
    _validate_test_authority(
        authority,
        descriptor=descriptor,
        fixture_sha256=pin_declaration["fixture_content_sha256"],
        repo_root=root,
    )
    fixture = _resolve_fixture(
        fixture_registry,
        descriptor=descriptor,
    )
    _validate_fixture(fixture, root)
    _validate_descriptor_against_fixture(descriptor, fixture)
    return _json_copy(fixture)


def adapt_valid_fixture(
    descriptor: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
    fixture_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compatibility alias for the explicit source-class adapter."""

    return adapt_claim_ir_valid_fixture(
        descriptor,
        repo_root=repo_root,
        authority=authority,
        fixture_registry=fixture_registry,
    )


def canonical_json_sha256(value: Any) -> str:
    """Return the deterministic JSON digest used by the in-memory test registry."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise M1ClaimIRValidFixtureAdapterError(
            "canonical_json", "value is not canonical JSON"
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def _validate_descriptor(descriptor: Mapping[str, Any]) -> None:
    if not isinstance(descriptor, Mapping):
        raise M1ClaimIRValidFixtureAdapterError(
            "descriptor_type", "adapter descriptor must be an object"
        )
    _reject_forbidden_descriptor_material(descriptor)
    if set(descriptor) != _EXPECTED_DESCRIPTOR_FIELDS:
        raise M1ClaimIRValidFixtureAdapterError(
            "descriptor_shape", "descriptor fields do not match the RED contract"
        )
    for field, expected in (
        ("surface_id", SURFACE_ID),
        ("source_class", SOURCE_CLASS),
        ("adapter_id", ADAPTER_ID),
        ("adapter_version", ADAPTER_VERSION),
    ):
        _require_constant(descriptor.get(field), expected, f"descriptor.{field}")

    reference = descriptor.get("opaque_fixture_reference")
    if (
        not isinstance(reference, str)
        or not _OPAQUE_REFERENCE_PATTERN.fullmatch(reference)
        or _contains_forbidden_reference_token(reference)
        or "://" in reference
        or "/" in reference
        or "\\" in reference
    ):
        raise M1ClaimIRValidFixtureAdapterError(
            "opaque_reference",
            "opaque fixture reference is path-like, semantic, or malformed",
        )

    pin = descriptor.get("fixture_pin_declaration")
    if not isinstance(pin, Mapping) or set(pin) != _EXPECTED_FIXTURE_PIN_FIELDS:
        raise M1ClaimIRValidFixtureAdapterError(
            "fixture_pin_shape", "fixture pin declaration is not canonical"
        )
    for field in (
        "fixture_content_sha256",
        "claim_ir_schema_sha256",
        "projection_sha256",
        "content_hash",
    ):
        if (
            not isinstance(pin.get(field), str)
            or not _SHA256_PATTERN.fullmatch(pin[field])
        ):
            raise M1ClaimIRValidFixtureAdapterError(
                "fixture_pin_value", f"{field} must be a lowercase SHA-256"
            )
    _require_constant(
        pin.get("claim_ir_schema_id"),
        EXTERNAL_SCHEMA_ID,
        "descriptor.fixture_pin_declaration.claim_ir_schema_id",
    )
    _require_constant(
        pin.get("claim_ir_schema_sha256"),
        EXTERNAL_SCHEMA_SHA256,
        "descriptor.fixture_pin_declaration.claim_ir_schema_sha256",
    )
    _require_constant(
        pin.get("projection_sha256"),
        PROJECTION_SHA256,
        "descriptor.fixture_pin_declaration.projection_sha256",
    )
    fixture_id = pin.get("fixture_id")
    if (
        not isinstance(fixture_id, str)
        or not _OPAQUE_REFERENCE_PATTERN.fullmatch(fixture_id)
        or _contains_forbidden_reference_token(fixture_id)
    ):
        raise M1ClaimIRValidFixtureAdapterError(
            "fixture_id", "fixture_id must be a safe opaque identifier"
        )

    declared = descriptor.get("declared_claim_ir_fields")
    if not isinstance(declared, Mapping) or set(declared) != _EXPECTED_DECLARATION_FIELDS:
        raise M1ClaimIRValidFixtureAdapterError(
            "declared_fields_shape", "declared Claim-IR fields are not canonical"
        )
    field_path_set = declared.get("field_path_set")
    if (
        not isinstance(field_path_set, list)
        or not field_path_set
        or any(not isinstance(field, str) for field in field_path_set)
        or len(field_path_set) != len(set(field_path_set))
        or field_path_set != sorted(field_path_set)
    ):
        raise M1ClaimIRValidFixtureAdapterError(
            "declared_field_path_set", "field_path_set must be unique and sorted"
        )
    for field, expected in (
        ("surface_id", SURFACE_ID),
        ("kernel_state", "pending_kernel_schema"),
        ("claim_id_state", "not_minted"),
        ("admission_state", "not_admitted"),
        ("projection_sha256", PROJECTION_SHA256),
    ):
        _require_constant(declared.get(field), expected, f"declared_claim_ir_fields.{field}")
    if declared.get("package_id") == FORBIDDEN_MINTED_PACKAGE_ID:
        raise M1ClaimIRValidFixtureAdapterError(
            "minted_package_forbidden",
            "the already-minted package identity is outside this adapter",
        )


def _validate_test_authority(
    authority: Mapping[str, Any] | None,
    *,
    descriptor: Mapping[str, Any],
    fixture_sha256: str,
    repo_root: Path,
) -> None:
    if authority is None:
        raise M1ClaimIRValidFixtureAdapterError(
            "missing_authority",
            "an explicit test-only in-memory authority is required",
        )
    if not isinstance(authority, Mapping):
        raise M1ClaimIRValidFixtureAdapterError(
            "authority_type", "test authority must be an object"
        )
    _reject_forbidden_authority_keys(authority)
    if set(authority) != _EXPECTED_AUTHORITY_FIELDS:
        raise M1ClaimIRValidFixtureAdapterError(
            "authority_shape", "test authority fields are not canonical"
        )
    _require_constant(authority.get("status"), TEST_AUTHORITY_STATUS, "authority.status")
    _require_typed_mapping(
        authority.get("scope"),
        {
            "test_only": True,
            "in_memory_only": True,
            "surface_id": SURFACE_ID,
            "source_class": SOURCE_CLASS,
            "adapter_id": ADAPTER_ID,
            "adapter_version": ADAPTER_VERSION,
            "registry_activation": False,
            "production_execute": False,
        },
        "authority.scope",
        "authority_scope",
    )
    _require_typed_mapping(
        authority.get("pinned_hashes"),
        {
            "red_acceptance_sha256": RED_ACCEPTANCE_SHA256,
            "adapter_contract_sha256": CONTRACT_SHA256,
            "m1_framework_sha256": M1_FRAMEWORK_SHA256,
            "selection_design_sha256": SELECTION_DESIGN_SHA256,
            "external_schema_sha256": EXTERNAL_SCHEMA_SHA256,
            "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
            "consumer_contract_sha256": CONSUMER_CONTRACT_SHA256,
            "adapter_implementation_sha256": _sha256(
                repo_root / ADAPTER_IMPLEMENTATION_PATH
            ),
        },
        "authority.pinned_hashes",
        "authority_pin",
    )
    _require_typed_mapping(
        authority.get("pinned_inputs"),
        {
            "descriptor_sha256": canonical_json_sha256(descriptor),
            "opaque_fixture_reference": descriptor["opaque_fixture_reference"],
            "fixture_content_sha256": fixture_sha256,
        },
        "authority.pinned_inputs",
        "authority_input",
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


def _resolve_fixture(
    fixture_registry: Mapping[str, Mapping[str, Any]] | None,
    *,
    descriptor: Mapping[str, Any],
) -> Mapping[str, Any]:
    if fixture_registry is None:
        raise M1ClaimIRValidFixtureAdapterError(
            "missing_registry", "an ephemeral in-memory fixture registry is required"
        )
    if not isinstance(fixture_registry, Mapping):
        raise M1ClaimIRValidFixtureAdapterError(
            "registry_type", "fixture registry must be an in-memory mapping"
        )
    reference = descriptor["opaque_fixture_reference"]
    if reference not in fixture_registry:
        raise M1ClaimIRValidFixtureAdapterError(
            "unknown_fixture", "opaque fixture reference is not prebound"
        )
    record = fixture_registry[reference]
    if not isinstance(record, Mapping) or set(record) != _EXPECTED_REGISTRY_RECORD_FIELDS:
        raise M1ClaimIRValidFixtureAdapterError(
            "registry_record_shape", "fixture registry record is not canonical"
        )
    if record.get("test_only") is not True:
        raise M1ClaimIRValidFixtureAdapterError(
            "registry_boundary", "only a test-only registry record is accepted"
        )
    for field, expected in (
        ("fixture_id", descriptor["fixture_pin_declaration"]["fixture_id"]),
        ("surface_id", SURFACE_ID),
        ("source_class", SOURCE_CLASS),
        (
            "fixture_content_sha256",
            descriptor["fixture_pin_declaration"]["fixture_content_sha256"],
        ),
        ("claim_ir_schema_sha256", EXTERNAL_SCHEMA_SHA256),
    ):
        _require_constant(record.get(field), expected, f"registry_record.{field}")
    fixture = record.get("fixture")
    if not isinstance(fixture, Mapping):
        raise M1ClaimIRValidFixtureAdapterError(
            "registry_fixture_type", "prebound fixture must be an in-memory object"
        )
    actual_sha = canonical_json_sha256(fixture)
    _require_constant(
        actual_sha,
        record["fixture_content_sha256"],
        "registry_record.fixture_content_sha256",
    )
    return fixture


def _validate_fixture(fixture: Mapping[str, Any], repo_root: Path) -> None:
    schema = _load_json(repo_root / EXTERNAL_SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(dict(schema)).iter_errors(dict(fixture)),
        key=lambda error: list(error.path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "<root>"
        raise M1ClaimIRValidFixtureAdapterError(
            "fixture_schema",
            f"fixture fails external Claim-IR schema at {location}: {first.message}",
        )
    for field, expected in (
        ("schema_version", "claim-ir-external-v0.1"),
        ("surface_id", SURFACE_ID),
        ("kernel_state", "pending_kernel_schema"),
        ("claim_id_state", "not_minted"),
        ("admission_state", "not_admitted"),
    ):
        _require_constant(fixture.get(field), expected, f"fixture.{field}")
    package_id = fixture.get("package_id")
    if package_id == FORBIDDEN_MINTED_PACKAGE_ID:
        raise M1ClaimIRValidFixtureAdapterError(
            "minted_package_forbidden",
            "the already-minted package identity is outside this adapter",
        )
    projection_ref = fixture.get("projection_ref")
    if not isinstance(projection_ref, Mapping) or dict(projection_ref) != {
        "path": PROJECTION_PATH,
        "sha256": PROJECTION_SHA256,
        "surface_id": SURFACE_ID,
    }:
        raise M1ClaimIRValidFixtureAdapterError(
            "fixture_projection", "fixture projection reference is not frozen"
        )
    claims = fixture.get("claims")
    if not isinstance(claims, list) or not claims:
        raise M1ClaimIRValidFixtureAdapterError(
            "fixture_claims", "fixture must contain at least one structural claim"
        )
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise M1ClaimIRValidFixtureAdapterError(
                "fixture_claims", "fixture claim must be an object"
            )
        _require_constant(claim.get("claim_id"), None, "fixture.claim.claim_id")
        _require_constant(
            claim.get("claim_id_state"),
            "not_minted",
            "fixture.claim.claim_id_state",
        )
        _require_constant(
            claim.get("admission_state"),
            "not_admitted",
            "fixture.claim.admission_state",
        )
        _reject_forbidden_fixture_values(claim.get("value"))

    manifest = fixture.get("manifest")
    if not isinstance(manifest, Mapping):
        raise M1ClaimIRValidFixtureAdapterError(
            "fixture_manifest", "fixture manifest is missing"
        )
    _require_constant(
        manifest.get("claim_count"), len(claims), "fixture.manifest.claim_count"
    )
    field_path_set = sorted({claim["source_field"] for claim in claims})
    _require_constant(
        manifest.get("field_path_set"),
        field_path_set,
        "fixture.manifest.field_path_set",
    )
    _require_constant(
        manifest.get("projection_sha256"),
        PROJECTION_SHA256,
        "fixture.manifest.projection_sha256",
    )
    _require_constant(
        manifest.get("content_hash"),
        canonical_json_sha256(claims),
        "fixture.manifest.content_hash",
    )


def _validate_descriptor_against_fixture(
    descriptor: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> None:
    manifest = fixture["manifest"]
    expected_declared = {
        "schema_version": fixture["schema_version"],
        "package_id": fixture["package_id"],
        "surface_id": fixture["surface_id"],
        "kernel_state": fixture["kernel_state"],
        "claim_id_state": fixture["claim_id_state"],
        "admission_state": fixture["admission_state"],
        "projection_sha256": manifest["projection_sha256"],
        "claim_count": manifest["claim_count"],
        "field_path_set": manifest["field_path_set"],
        "content_hash": manifest["content_hash"],
    }
    _require_typed_mapping(
        descriptor.get("declared_claim_ir_fields"),
        expected_declared,
        "descriptor.declared_claim_ir_fields",
        "declared_fixture_mismatch",
    )
    pin = descriptor["fixture_pin_declaration"]
    expected_pin = {
        "fixture_id": pin["fixture_id"],
        "fixture_content_sha256": canonical_json_sha256(fixture),
        "claim_ir_schema_id": EXTERNAL_SCHEMA_ID,
        "claim_ir_schema_sha256": EXTERNAL_SCHEMA_SHA256,
        "projection_sha256": manifest["projection_sha256"],
        "content_hash": manifest["content_hash"],
    }
    _require_typed_mapping(
        pin,
        expected_pin,
        "descriptor.fixture_pin_declaration",
        "fixture_pin_mismatch",
    )


def _reject_forbidden_descriptor_material(
    value: Any,
    path: tuple[str, ...] = (),
) -> None:
    if isinstance(value, (bytes, bytearray)):
        raise M1ClaimIRValidFixtureAdapterError(
            "raw_bytes", f"raw bytes are forbidden at {'.'.join(path) or '<root>'}"
        )
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(nested, (bytes, bytearray)):
                raise M1ClaimIRValidFixtureAdapterError(
                    "raw_bytes",
                    f"raw bytes are forbidden at {'.'.join((*path, str(key)))}",
                )
            normalized = _normalize_key(key)
            if normalized in _FORBIDDEN_DESCRIPTOR_KEYS:
                raise M1ClaimIRValidFixtureAdapterError(
                    "forbidden_descriptor_field",
                    f"forbidden descriptor field: {'.'.join((*path, str(key)))}",
                )
            _reject_forbidden_descriptor_material(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for index, nested in enumerate(value):
            _reject_forbidden_descriptor_material(nested, (*path, str(index)))
    elif isinstance(value, str) and (
        "://" in value
        or "\\" in value
        or value.casefold().startswith(("file:", "http:", "https:"))
    ):
        raise M1ClaimIRValidFixtureAdapterError(
            "path_or_uri", f"path or URI is forbidden at {'.'.join(path) or '<root>'}"
        )


def _reject_forbidden_authority_keys(
    value: Any,
    path: tuple[str, ...] = (),
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            if normalized in _FORBIDDEN_AUTHORITY_KEYS:
                raise M1ClaimIRValidFixtureAdapterError(
                    "forbidden_authority_field",
                    f"forbidden authority field: {'.'.join((*path, str(key)))}",
                )
            _reject_forbidden_authority_keys(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_forbidden_authority_keys(nested, (*path, str(index)))


def _reject_forbidden_fixture_values(value: Any) -> None:
    if isinstance(value, str):
        folded = value.casefold()
        if any(token in folded for token in _FORBIDDEN_FIXTURE_VALUE_TOKENS):
            raise M1ClaimIRValidFixtureAdapterError(
                "forbidden_fixture_value",
                "fixture claim value contains excluded authority or private semantics",
            )
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            _reject_forbidden_fixture_values(nested)


def _contains_forbidden_reference_token(value: str) -> bool:
    folded = value.casefold()
    return any(token in folded for token in _FORBIDDEN_REFERENCE_TOKENS)


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
        raise M1ClaimIRValidFixtureAdapterError(
            "contract_pin", f"{field} does not match the frozen path/SHA"
        )


def _require_typed_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    code: str,
) -> None:
    if not isinstance(value, Mapping) or dict(value) != dict(expected):
        raise M1ClaimIRValidFixtureAdapterError(
            code, f"{field} does not match the required exact mapping"
        )


def _require_constant(value: Any, expected: Any, field: str) -> None:
    if value != expected:
        raise M1ClaimIRValidFixtureAdapterError(
            "constant", f"{field} must equal {expected!r}"
        )


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise M1ClaimIRValidFixtureAdapterError(
            "pin_missing", f"missing pinned artifact: {relative_path}"
        )
    actual = _sha256(path)
    if actual != expected_sha:
        raise M1ClaimIRValidFixtureAdapterError(
            "pin_mismatch", f"pinned artifact SHA mismatch: {relative_path}"
        )


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateJSONKey) as exc:
        raise M1ClaimIRValidFixtureAdapterError(
            "json_load", f"cannot load pinned JSON: {path}"
        ) from exc


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise M1ClaimIRValidFixtureAdapterError(
            "file_read", f"cannot read pinned file: {path}"
        ) from exc


def _json_copy(value: Any) -> Any:
    return json.loads(
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    )


def _normalize_key(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_")


class _DuplicateJSONKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result
