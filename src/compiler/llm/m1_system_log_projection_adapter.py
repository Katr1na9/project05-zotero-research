"""Test-only, authority-gated adapter for a system-log public projection.

This module also contains the shared fail-closed plumbing used by the other
two evidence-modality adapter skeletons.  It reads only pinned governance
artifacts and schemas.  Projected source material is supplied in memory; no
request path, URI, raw bytes, registry activation, mint, or write is allowed.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError


SURFACE_ID = "project05_depth2_public"
SOURCE_CLASS = "system_log_public_projection"
ADAPTER_ID = "m1a_system_log_projection_v0_1"
ADAPTER_VERSION = "0.1.0"
TEST_AUTHORITY_STATUS = (
    "activated_test_only_in_memory_system_log_projection_authority"
)

RED_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-m1-evidence-modality-projection-adapters-red-owner-acceptance-"
    "v0.1-20260726.json"
)
RED_ACCEPTANCE_SHA256 = (
    "76d2f9d94d8b165137c9e77a10eab3252feecc5907d80bf3129e7652a34dcf21"
)
FRAMEWORK_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-evidence-modality-projection-adapter-framework-"
    "design-v0.1-20260726.json"
)
FRAMEWORK_SHA256 = (
    "a9a8938908912978d3637ca573cdb2f2b9c3da669eb20351bd1be1daba5c2bee"
)
PROJECTION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-system-log-public-field-projection-"
    "v0.1-20260726.json"
)
PROJECTION_SHA256 = (
    "5c707f5cfa6534d11d04c4f10899ea133396c00961041112353321f47d78f8bb"
)
PROJECTION_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-m1-system-log-public-field-projection-"
    "v0.1-20260726"
)
CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-system-log-projection-adapter-contract-"
    "v0.1-20260726.json"
)
CONTRACT_SHA256 = (
    "e4fc75e2148319ffbc130472807c142460c3092170b659c8776adca65522bedc"
)
EXTERNAL_SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
EXTERNAL_SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
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
M0_PROJECTION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-m0-depth2-public-field-projection-"
    "v0.1-20260724.json"
)
M0_PROJECTION_SHA256 = (
    "4784ff3a29f2c3cb8d04bc187b1f2cd1d95b9ead51c3ad0d7c4da30f4cd557e8"
)
PLANNER_IMPLEMENTATION_PATH = "src/compiler/llm/m1_planner_inputs_adapter.py"
PLANNER_IMPLEMENTATION_SHA256 = (
    "ae5c6db06a523ef6a4e384a118e1dcff7f0694d2b3f0e6f87a7dc7b2252d67f0"
)
VALID_FIXTURE_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_claim_ir_valid_fixture_adapter.py"
)
VALID_FIXTURE_IMPLEMENTATION_SHA256 = (
    "4d69c1a17417c4aad5460608fd217bbdc5d67e1f78b4badfa2427ce33f78670d"
)
ADAPTER_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_system_log_projection_adapter.py"
)

_EXPECTED_DESCRIPTOR_FIELDS = frozenset(
    {
        "surface_id",
        "source_class",
        "adapter_id",
        "adapter_version",
        "opaque_projection_reference",
        "projection_pin_declaration",
        "declared_projected_fields",
    }
)
_EXPECTED_PIN_FIELDS = frozenset(
    {
        "projection_path",
        "projection_sha256",
        "fixture_id",
        "fixture_content_sha256",
    }
)
_EXPECTED_REGISTRY_RECORD_FIELDS = frozenset(
    {
        "fixture_id",
        "surface_id",
        "source_class",
        "fixture_content_sha256",
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
    "raw_source_read": False,
    "raw_source_persist": False,
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
    "activation_ledger_write": True,
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
_OPAQUE_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_KEYS = frozenset(
    {
        "path",
        "filesystem_path",
        "archive_member_path",
        "uri",
        "url",
        "endpoint",
        "raw_source",
        "raw_bytes",
        "raw_payload",
        "payload",
        "payload_bytes",
        "message",
        "full_text",
        "body",
        "excerpt",
        "quoted_text",
        "attachments",
        "raw_stix",
        "raw_json",
        "label",
        "labels",
        "verdict",
        "ground_truth",
        "oracle",
        "oracle_path",
        "mask_membership",
        "secret",
        "secrets",
        "credential",
        "credentials",
        "private_key",
        "hidden_claim_ids",
        "required_claim_ids",
        "recoverable_claim_ids",
        "hostname",
        "ip_address",
        "username",
        "email",
        "process_path",
        "command_line",
        "certificate",
        "certified_stop",
        "ordinary_run_mvp_stop",
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


class M1EvidenceModalityAdapterError(ValueError):
    """Raised when an evidence-modality adapter fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


M1SystemLogProjectionAdapterError = M1EvidenceModalityAdapterError


SYSTEM_LOG_SPEC: dict[str, Any] = {
    "surface_id": SURFACE_ID,
    "source_class": SOURCE_CLASS,
    "adapter_id": ADAPTER_ID,
    "adapter_version": ADAPTER_VERSION,
    "authority_status": TEST_AUTHORITY_STATUS,
    "red_acceptance_path": RED_ACCEPTANCE_PATH,
    "red_acceptance_sha256": RED_ACCEPTANCE_SHA256,
    "framework_path": FRAMEWORK_PATH,
    "framework_sha256": FRAMEWORK_SHA256,
    "projection_path": PROJECTION_PATH,
    "projection_sha256": PROJECTION_SHA256,
    "projection_artifact_id": PROJECTION_ARTIFACT_ID,
    "contract_path": CONTRACT_PATH,
    "contract_sha256": CONTRACT_SHA256,
    "external_schema_path": EXTERNAL_SCHEMA_PATH,
    "external_schema_sha256": EXTERNAL_SCHEMA_SHA256,
    "kernel_schema_path": KERNEL_SCHEMA_PATH,
    "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
    "consumer_contract_path": CONSUMER_CONTRACT_PATH,
    "consumer_contract_sha256": CONSUMER_CONTRACT_SHA256,
    "m0_projection_path": M0_PROJECTION_PATH,
    "m0_projection_sha256": M0_PROJECTION_SHA256,
    "implementation_path": ADAPTER_IMPLEMENTATION_PATH,
    "acceptance_artifact_key": "system_log_adapter_contract",
    "acceptance_projection_key": "system_log_public_field_projection",
    "extra_pins": (),
}


def verify_adapter_pins(repo_root: Path) -> None:
    """Verify all system-log adapter pins and accepted RED boundaries."""

    verify_projection_adapter_pins(repo_root, SYSTEM_LOG_SPEC)


def adapt_system_log_projection(
    descriptor: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
    fixture_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate one declared system-log projection and return an M0 envelope."""

    return adapt_projection_with_spec(
        descriptor,
        repo_root=repo_root,
        authority=authority,
        fixture_registry=fixture_registry,
        spec=SYSTEM_LOG_SPEC,
        fixture_validator=_validate_system_log_fixture,
    )


def verify_projection_adapter_pins(
    repo_root: Path,
    spec: Mapping[str, Any],
) -> None:
    """Shared exact pin verification for the three test-only skeletons."""

    root = repo_root.resolve()
    pinned = (
        (spec["red_acceptance_path"], spec["red_acceptance_sha256"]),
        (spec["framework_path"], spec["framework_sha256"]),
        (spec["projection_path"], spec["projection_sha256"]),
        (spec["contract_path"], spec["contract_sha256"]),
        (spec["external_schema_path"], spec["external_schema_sha256"]),
        (spec["kernel_schema_path"], spec["kernel_schema_sha256"]),
        (spec["consumer_contract_path"], spec["consumer_contract_sha256"]),
        (spec["m0_projection_path"], spec["m0_projection_sha256"]),
        (PLANNER_IMPLEMENTATION_PATH, PLANNER_IMPLEMENTATION_SHA256),
        (VALID_FIXTURE_IMPLEMENTATION_PATH, VALID_FIXTURE_IMPLEMENTATION_SHA256),
        *tuple(spec.get("extra_pins", ())),
    )
    for relative_path, expected_sha in pinned:
        _verify_pin(root, relative_path, expected_sha)

    contract = _load_json(root / spec["contract_path"])
    _require_mapping(contract, "contract_shape", "adapter contract")
    _require_constant(
        contract.get("status"),
        "design_only_adapter_not_registered",
        "contract.status",
    )
    identity = contract.get("adapter_identity")
    _require_mapping(identity, "contract_shape", "adapter identity")
    for field, expected in (
        ("adapter_id", spec["adapter_id"]),
        ("adapter_version", spec["adapter_version"]),
        ("source_class", spec["source_class"]),
        ("surface_id", spec["surface_id"]),
        ("only_surface", True),
        ("certificate_surface", "vacant"),
    ):
        _require_constant(identity.get(field), expected, f"contract.identity.{field}")
    _require_exact_mapping(
        contract.get("registry_state"),
        {
            "adapter_registered": False,
            "adapter_implementation_authorized": False,
            "adapter_execution_authorized": False,
            "registry_activation_authorized": False,
            "production_registration_enabled": False,
        },
        "contract.registry_state",
        "contract_registry",
    )
    exact_identity = (
        contract.get("input_contract", {}).get("exact_identity")
        if isinstance(contract.get("input_contract"), Mapping)
        else None
    )
    _require_exact_mapping(
        exact_identity,
        {
            "surface_id": spec["surface_id"],
            "source_class": spec["source_class"],
            "adapter_id": spec["adapter_id"],
            "adapter_version": spec["adapter_version"],
        },
        "contract.input_contract.exact_identity",
        "contract_input",
    )
    _require_constant(
        contract.get("normalization_contract", {}).get("normalization_status"),
        "design_only_not_executable",
        "contract.normalization_status",
    )
    _require_exact_mapping(
        contract.get("output_contract", {}).get("fixed_state_values"),
        {
            "surface_id": spec["surface_id"],
            "claim_id": None,
            "claim_id_state": "not_minted",
            "admission_state": "not_admitted",
            "kernel_state": "pending_kernel_schema",
        },
        "contract.output_contract.fixed_state_values",
        "contract_output",
    )

    projection = _load_json(root / spec["projection_path"])
    _require_mapping(projection, "projection_shape", "field projection")
    _require_constant(
        projection.get("status"),
        "design_only_public_projection_not_authorized",
        "projection.status",
    )
    projection_identity = projection.get("projection_identity")
    _require_mapping(
        projection_identity,
        "projection_shape",
        "projection identity",
    )
    for field, expected in (
        ("source_class", spec["source_class"]),
        ("surface_id", spec["surface_id"]),
        ("future_adapter_id", spec["adapter_id"]),
        ("future_adapter_version", spec["adapter_version"]),
    ):
        _require_constant(
            projection_identity.get(field),
            expected,
            f"projection.identity.{field}",
        )
    allowlist = projection.get("allowlisted_field_paths")
    if (
        not isinstance(allowlist, list)
        or not allowlist
        or any(
            not isinstance(item, Mapping)
            or not isinstance(item.get("field_path"), str)
            for item in allowlist
        )
        or len({item["field_path"] for item in allowlist}) != len(allowlist)
    ):
        raise M1EvidenceModalityAdapterError(
            "projection_allowlist",
            "projection allowlisted field paths are missing or ambiguous",
        )

    framework = _load_json(root / spec["framework_path"])
    _require_mapping(framework, "framework_shape", "framework")
    _require_constant(
        framework.get("status"),
        "design_only_not_authorized",
        "framework.status",
    )
    source_plan = framework.get("source_class_plan")
    if (
        not isinstance(source_plan, Mapping)
        or spec["source_class"] not in source_plan
        or source_plan.get("audit_log_public_projection", {}).get("status")
        != "OUT_OF_V0_1"
    ):
        raise M1EvidenceModalityAdapterError(
            "framework_source_class",
            "source class or audit-log boundary is not frozen",
        )

    acceptance = _load_json(root / spec["red_acceptance_path"])
    _require_mapping(acceptance, "red_acceptance_shape", "RED acceptance")
    _require_constant(acceptance.get("decision"), "accept", "acceptance.decision")
    _require_constant(
        acceptance.get("status"),
        "red_design_accepted_implementation_execution_download_and_git_not_authorized",
        "acceptance.status",
    )
    accepted_contract = acceptance.get("pinned_red_artifacts", {}).get(
        spec["acceptance_artifact_key"]
    )
    accepted_projection = acceptance.get("pinned_red_artifacts", {}).get(
        spec["acceptance_projection_key"]
    )
    _require_pin_record(
        accepted_contract,
        spec["contract_path"],
        spec["contract_sha256"],
        "acceptance.contract",
    )
    _require_pin_record(
        accepted_projection,
        spec["projection_path"],
        spec["projection_sha256"],
        "acceptance.projection",
    )
    guidance = acceptance.get("orq04_guidance")
    if (
        not isinstance(guidance, str)
        or "directly to the existing M0 Claim-IR structural boundary"
        not in guidance
    ):
        raise M1EvidenceModalityAdapterError(
            "red_acceptance_guidance",
            "direct-to-M0 GREEN guidance is not pinned",
        )

    try:
        Draft202012Validator.check_schema(
            dict(_load_json(root / spec["external_schema_path"]))
        )
        Draft202012Validator.check_schema(
            dict(_load_json(root / spec["kernel_schema_path"]))
        )
    except (SchemaError, TypeError, ValueError) as exc:
        raise M1EvidenceModalityAdapterError(
            "schema_invalid",
            "a pinned Claim-IR schema is invalid",
        ) from exc


def adapt_projection_with_spec(
    descriptor: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None,
    fixture_registry: Mapping[str, Mapping[str, Any]] | None,
    spec: Mapping[str, Any],
    fixture_validator: Callable[[Mapping[str, Any], Mapping[str, Any]], None],
) -> dict[str, Any]:
    """Shared in-memory validation and structural-envelope construction."""

    root = repo_root.resolve()
    verify_projection_adapter_pins(root, spec)
    _validate_adapter_descriptor(descriptor, spec)
    _validate_test_authority(authority, descriptor, root, spec)
    fixture = _resolve_fixture(fixture_registry, descriptor, spec)
    fixture_validator(fixture, spec)
    if fixture.get("descriptor", {}).get("opaque_record_reference") != descriptor.get(
        "opaque_projection_reference"
    ):
        raise M1EvidenceModalityAdapterError(
            "fixture_reference_mismatch",
            "fixture and adapter opaque references differ",
        )
    _require_exact_mapping(
        descriptor.get("declared_projected_fields"),
        fixture,
        "descriptor.declared_projected_fields",
        "declared_fixture_mismatch",
    )
    envelope = _build_structural_envelope(descriptor, spec)
    schema = _load_json(root / spec["external_schema_path"])
    errors = sorted(
        Draft202012Validator(dict(schema)).iter_errors(envelope),
        key=lambda error: list(error.path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "<root>"
        raise M1EvidenceModalityAdapterError(
            "output_schema",
            f"structural output fails M0 schema at {location}: {first.message}",
        )
    return _json_copy(envelope)


def canonical_json_sha256(value: Any) -> str:
    """Return the deterministic digest used by ephemeral test registries."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise M1EvidenceModalityAdapterError(
            "canonical_json",
            "value is not canonical JSON",
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def _validate_adapter_descriptor(
    descriptor: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> None:
    if not isinstance(descriptor, Mapping):
        raise M1EvidenceModalityAdapterError(
            "descriptor_type",
            "adapter descriptor must be an object",
        )
    if set(descriptor) != _EXPECTED_DESCRIPTOR_FIELDS:
        extra = set(descriptor) - _EXPECTED_DESCRIPTOR_FIELDS
        if any(_normalize_key(key) in _FORBIDDEN_KEYS for key in extra):
            raise M1EvidenceModalityAdapterError(
                "forbidden_descriptor_field",
                "adapter descriptor contains forbidden source material",
            )
        raise M1EvidenceModalityAdapterError(
            "descriptor_shape",
            "adapter descriptor fields are not exact",
        )
    for field, expected in (
        ("surface_id", spec["surface_id"]),
        ("source_class", spec["source_class"]),
        ("adapter_id", spec["adapter_id"]),
        ("adapter_version", spec["adapter_version"]),
    ):
        _require_constant(descriptor.get(field), expected, f"descriptor.{field}")
    _require_safe_opaque(
        descriptor.get("opaque_projection_reference"),
        "descriptor.opaque_projection_reference",
    )
    pin = descriptor.get("projection_pin_declaration")
    if not isinstance(pin, Mapping) or set(pin) != _EXPECTED_PIN_FIELDS:
        raise M1EvidenceModalityAdapterError(
            "projection_pin_shape",
            "projection pin declaration is not exact",
        )
    for field, expected in (
        ("projection_path", spec["projection_path"]),
        ("projection_sha256", spec["projection_sha256"]),
    ):
        _require_constant(pin.get(field), expected, f"descriptor.pin.{field}")
    _require_safe_opaque(pin.get("fixture_id"), "descriptor.pin.fixture_id")
    _require_sha(
        pin.get("fixture_content_sha256"),
        "descriptor.pin.fixture_content_sha256",
    )
    declared = descriptor.get("declared_projected_fields")
    if not isinstance(declared, Mapping):
        raise M1EvidenceModalityAdapterError(
            "declared_fields_type",
            "declared projected fields must be an object",
        )
    _reject_forbidden_declared_material(declared)


def _validate_test_authority(
    authority: Mapping[str, Any] | None,
    descriptor: Mapping[str, Any],
    repo_root: Path,
    spec: Mapping[str, Any],
) -> None:
    if authority is None:
        raise M1EvidenceModalityAdapterError(
            "missing_authority",
            "explicit test-only in-memory authority is required",
        )
    if not isinstance(authority, Mapping):
        raise M1EvidenceModalityAdapterError(
            "authority_type",
            "authority must be an object",
        )
    _reject_forbidden_authority_material(authority)
    if set(authority) != _EXPECTED_AUTHORITY_FIELDS:
        raise M1EvidenceModalityAdapterError(
            "authority_shape",
            "authority fields are not exact",
        )
    _require_constant(
        authority.get("status"),
        spec["authority_status"],
        "authority.status",
    )
    _require_exact_mapping(
        authority.get("scope"),
        {
            "test_only": True,
            "in_memory_only": True,
            "surface_id": spec["surface_id"],
            "source_class": spec["source_class"],
            "adapter_id": spec["adapter_id"],
            "adapter_version": spec["adapter_version"],
            "registry_activation": False,
            "production_execute": False,
        },
        "authority.scope",
        "authority_scope",
    )
    expected_hashes = {
        "red_acceptance_sha256": spec["red_acceptance_sha256"],
        "framework_sha256": spec["framework_sha256"],
        "projection_sha256": spec["projection_sha256"],
        "adapter_contract_sha256": spec["contract_sha256"],
        "external_schema_sha256": spec["external_schema_sha256"],
        "kernel_schema_sha256": spec["kernel_schema_sha256"],
        "consumer_contract_sha256": spec["consumer_contract_sha256"],
        "m0_projection_sha256": spec["m0_projection_sha256"],
        "adapter_implementation_sha256": _sha256(
            repo_root / spec["implementation_path"]
        ),
    }
    if spec.get("support_implementation_path"):
        expected_hashes["support_implementation_sha256"] = spec[
            "support_implementation_sha256"
        ]
    _require_exact_mapping(
        authority.get("pinned_hashes"),
        expected_hashes,
        "authority.pinned_hashes",
        "authority_pin",
    )
    pin = descriptor["projection_pin_declaration"]
    _require_exact_mapping(
        authority.get("pinned_inputs"),
        {
            "descriptor_sha256": canonical_json_sha256(descriptor),
            "opaque_projection_reference": descriptor[
                "opaque_projection_reference"
            ],
            "fixture_content_sha256": pin["fixture_content_sha256"],
        },
        "authority.pinned_inputs",
        "authority_input",
    )
    _require_exact_mapping(
        authority.get("output_policy"),
        _EXPECTED_OUTPUT_POLICY,
        "authority.output_policy",
        "authority_boundary",
    )
    _require_exact_mapping(
        authority.get("still_blocked"),
        _EXPECTED_STILL_BLOCKED,
        "authority.still_blocked",
        "authority_boundary",
    )


def _resolve_fixture(
    registry: Mapping[str, Mapping[str, Any]] | None,
    descriptor: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not isinstance(registry, Mapping):
        raise M1EvidenceModalityAdapterError(
            "missing_registry",
            "an ephemeral in-memory fixture registry is required",
        )
    reference = descriptor["opaque_projection_reference"]
    if reference not in registry:
        raise M1EvidenceModalityAdapterError(
            "unknown_fixture",
            "opaque projection reference is not prebound",
        )
    record = registry[reference]
    if not isinstance(record, Mapping) or set(record) != _EXPECTED_REGISTRY_RECORD_FIELDS:
        raise M1EvidenceModalityAdapterError(
            "registry_record_shape",
            "fixture registry record is not exact",
        )
    if record.get("test_only") is not True:
        raise M1EvidenceModalityAdapterError(
            "registry_boundary",
            "only a test-only registry record is accepted",
        )
    pin = descriptor["projection_pin_declaration"]
    for field, expected in (
        ("fixture_id", pin["fixture_id"]),
        ("surface_id", spec["surface_id"]),
        ("source_class", spec["source_class"]),
        ("fixture_content_sha256", pin["fixture_content_sha256"]),
    ):
        _require_constant(record.get(field), expected, f"registry.{field}")
    fixture = record.get("fixture")
    if not isinstance(fixture, Mapping):
        raise M1EvidenceModalityAdapterError(
            "registry_fixture_type",
            "prebound fixture must be an in-memory object",
        )
    _require_constant(
        canonical_json_sha256(fixture),
        record["fixture_content_sha256"],
        "registry.fixture_content_sha256",
    )
    return fixture


def _build_structural_envelope(
    descriptor: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    claims: list[dict[str, Any]] = []
    descriptor_digest = canonical_json_sha256(descriptor)
    return {
        "schema_version": "claim-ir-external-v0.1",
        "package_id": f"pkg_m1ev_{descriptor_digest[:32]}",
        "surface_id": spec["surface_id"],
        "kernel_state": "pending_kernel_schema",
        "claim_id_state": "not_minted",
        "admission_state": "not_admitted",
        "projection_ref": {
            "path": spec["m0_projection_path"],
            "sha256": spec["m0_projection_sha256"],
            "surface_id": spec["surface_id"],
        },
        "claims": claims,
        "manifest": {
            "claim_count": 0,
            "field_path_set": [],
            "projection_sha256": spec["projection_sha256"],
            "content_hash": canonical_json_sha256(claims),
        },
    }


def _validate_system_log_fixture(
    fixture: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> None:
    _require_exact_keys(
        fixture,
        {"descriptor", "event", "principal", "source_metadata"},
        "fixture",
    )
    descriptor = fixture["descriptor"]
    _require_exact_keys(
        descriptor,
        {
            "surface_id",
            "source_class",
            "opaque_record_reference",
            "projection_pin_declaration",
        },
        "fixture.descriptor",
    )
    _require_constant(
        descriptor["surface_id"],
        spec["surface_id"],
        "fixture.descriptor.surface_id",
    )
    _require_constant(
        descriptor["source_class"],
        spec["source_class"],
        "fixture.descriptor.source_class",
    )
    _require_safe_opaque(
        descriptor["opaque_record_reference"],
        "fixture.descriptor.opaque_record_reference",
    )
    _require_exact_mapping(
        descriptor["projection_pin_declaration"],
        {
            "artifact_id": spec["projection_artifact_id"],
            "version": "0.1",
            "sha256": spec["projection_sha256"],
        },
        "fixture.descriptor.projection_pin_declaration",
        "fixture_projection_pin",
    )

    event = fixture["event"]
    _require_exact_keys(
        event,
        {"event_id", "event_time", "provider", "severity", "result_code"},
        "fixture.event",
    )
    for field in ("event_id", "provider", "result_code"):
        _require_safe_opaque(event[field], f"fixture.event.{field}")
    if not isinstance(event["event_time"], str) or not event["event_time"].endswith("Z"):
        raise M1EvidenceModalityAdapterError(
            "event_time",
            "system-log event_time must be an RFC3339 UTC declaration",
        )
    if event["severity"] not in {
        "informational",
        "low",
        "medium",
        "high",
        "critical",
        "unknown",
    }:
        raise M1EvidenceModalityAdapterError(
            "event_severity",
            "system-log severity is not allowlisted",
        )

    principal = fixture["principal"]
    _require_exact_keys(
        principal,
        {"public_host_ref", "public_process_ref", "public_user_ref"},
        "fixture.principal",
    )
    for field, value in principal.items():
        _require_safe_opaque(value, f"fixture.principal.{field}")

    metadata = fixture["source_metadata"]
    _require_exact_keys(
        metadata,
        {
            "transport_source_modality",
            "source_family",
            "epistemic_modality",
            "modality_basis_code",
            "trusted_ingestion_metadata_sha256",
        },
        "fixture.source_metadata",
    )
    if metadata["transport_source_modality"] not in {
        "endpoint_event",
        "network_event",
        "security_text",
        "other_public_transport",
    }:
        raise M1EvidenceModalityAdapterError(
            "transport_modality",
            "transport modality is not allowlisted",
        )
    if metadata["source_family"] not in {
        "execution",
        "identity",
        "communication",
        "data_access",
        "control_plane",
        "system_provenance",
        "software_supply_chain",
    }:
        raise M1EvidenceModalityAdapterError(
            "source_family",
            "system-log source family is not allowlisted",
        )
    expected_pairs = {
        "DIRECT_SOURCE_ATTESTED_EVENT": "observed",
        "TRANSFORMED_AGGREGATED_OR_ALERT": "derived",
        "UNRESOLVED_BASIS": "unknown",
    }
    modality = expected_pairs.get(metadata["modality_basis_code"])
    if modality != metadata["epistemic_modality"]:
        raise M1EvidenceModalityAdapterError(
            "modality_mapping",
            "system-log modality and trusted basis do not match",
        )
    _require_sha(
        metadata["trusted_ingestion_metadata_sha256"],
        "fixture.source_metadata.trusted_ingestion_metadata_sha256",
    )


def _reject_forbidden_declared_material(
    value: Any,
    path: tuple[str, ...] = (),
) -> None:
    if isinstance(value, (bytes, bytearray)):
        raise M1EvidenceModalityAdapterError(
            "raw_bytes",
            f"raw bytes are forbidden at {'.'.join(path) or '<root>'}",
        )
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            if normalized == "claim_id" and nested is not None:
                raise M1EvidenceModalityAdapterError(
                    "authority_elevation",
                    "non-null claim_id is forbidden",
                )
            if normalized == "claim_id_state" and nested != "not_minted":
                raise M1EvidenceModalityAdapterError(
                    "authority_elevation",
                    "claim_id_state elevation is forbidden",
                )
            if normalized == "admission_state" and nested != "not_admitted":
                raise M1EvidenceModalityAdapterError(
                    "authority_elevation",
                    "admission elevation is forbidden",
                )
            if normalized == "kernel_state" and nested != "pending_kernel_schema":
                raise M1EvidenceModalityAdapterError(
                    "authority_elevation",
                    "Kernel-state elevation is forbidden",
                )
            if normalized in _FORBIDDEN_KEYS:
                raise M1EvidenceModalityAdapterError(
                    "forbidden_descriptor_field",
                    f"forbidden field at {'.'.join((*path, str(key)))}",
                )
            _reject_forbidden_declared_material(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        for index, nested in enumerate(value):
            _reject_forbidden_declared_material(nested, (*path, str(index)))
    elif isinstance(value, str) and (
        "://" in value
        or "\\" in value
        or value.casefold().startswith(("file:", "http:", "https:"))
    ):
        raise M1EvidenceModalityAdapterError(
            "path_or_uri",
            f"path or URI is forbidden at {'.'.join(path) or '<root>'}",
        )


def _reject_forbidden_authority_material(
    value: Any,
    path: tuple[str, ...] = (),
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _normalize_key(key) in _FORBIDDEN_AUTHORITY_KEYS:
                raise M1EvidenceModalityAdapterError(
                    "forbidden_authority_field",
                    f"forbidden authority field at {'.'.join((*path, str(key)))}",
                )
            _reject_forbidden_authority_material(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        for index, nested in enumerate(value):
            _reject_forbidden_authority_material(nested, (*path, str(index)))


def _require_exact_keys(
    value: Any,
    expected: set[str],
    field: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise M1EvidenceModalityAdapterError(
            "unknown_field",
            f"{field} fields do not match the projection allowlist",
        )


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    code: str,
) -> None:
    if not isinstance(value, Mapping) or dict(value) != dict(expected):
        raise M1EvidenceModalityAdapterError(
            code,
            f"{field} does not match the exact required mapping",
        )


def _require_mapping(value: Any, code: str, field: str) -> None:
    if not isinstance(value, Mapping):
        raise M1EvidenceModalityAdapterError(code, f"{field} must be an object")


def _require_constant(value: Any, expected: Any, field: str) -> None:
    if value != expected:
        raise M1EvidenceModalityAdapterError(
            "constant",
            f"{field} must equal {expected!r}",
        )


def _require_safe_opaque(value: Any, field: str) -> None:
    if (
        not isinstance(value, str)
        or not _OPAQUE_PATTERN.fullmatch(value)
        or "/" in value
        or "\\" in value
        or "://" in value
    ):
        raise M1EvidenceModalityAdapterError(
            "opaque_reference",
            f"{field} must be a safe opaque reference",
        )


def _require_sha(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise M1EvidenceModalityAdapterError(
            "sha256",
            f"{field} must be a lowercase SHA-256",
        )


def _require_pin_record(
    value: Any,
    expected_path: str,
    expected_sha: str,
    field: str,
) -> None:
    if (
        not isinstance(value, Mapping)
        or value.get("path") != expected_path
        or value.get("content_sha256") != expected_sha
    ):
        raise M1EvidenceModalityAdapterError(
            "acceptance_pin",
            f"{field} does not match the accepted path/SHA",
        )


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise M1EvidenceModalityAdapterError(
            "pin_missing",
            f"missing pinned artifact: {relative_path}",
        )
    if _sha256(path) != expected_sha:
        raise M1EvidenceModalityAdapterError(
            "pin_mismatch",
            f"pinned artifact SHA mismatch: {relative_path}",
        )


def _load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateJSONKey) as exc:
        raise M1EvidenceModalityAdapterError(
            "json_load",
            f"cannot load pinned JSON: {path}",
        ) from exc


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise M1EvidenceModalityAdapterError(
            "file_read",
            f"cannot read pinned file: {path}",
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
