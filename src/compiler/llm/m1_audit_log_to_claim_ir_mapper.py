"""Test-only A3 mapper for one validated audit-log public declaration.

The mapper emits only an unminted, not-admitted
``claim-ir-external-evidence-v0.2`` package in the
``evidence.audit_log.*`` namespace.  Its output establishes structural
consistency at the public-declaration ceiling; it does not establish operation
truth, actor identity, authorization, scientific sufficiency, or ingestion.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError
from referencing import Registry, Resource

from compiler.llm import m1_audit_log_projection_adapter as adapter


SURFACE_ID = adapter.SURFACE_ID
SOURCE_CLASS = adapter.SOURCE_CLASS
SCHEMA_VERSION = "claim-ir-external-evidence-v0.2"
MAPPER_ID = "m1m_audit_log_to_claim_ir_v0_1"
MAPPER_VERSION = "0.1.0"
TEST_AUTHORITY_STATUS = (
    "activated_test_only_in_memory_audit_log_to_claim_ir_authority"
)
MAPPER_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_audit_log_to_claim_ir_mapper.py"
)
ADAPTER_IMPLEMENTATION_PATH = adapter.ADAPTER_IMPLEMENTATION_PATH
ADAPTER_IMPLEMENTATION_SHA256 = (
    "93934bc6a28eaa1d7b23932bf5d1ca6c44221df2dc7a3c255b8e969cca311704"
)

EXTERNAL_EVIDENCE_V0_2_PATH = adapter.EXTERNAL_EVIDENCE_V0_2_PATH
EXTERNAL_EVIDENCE_V0_2_SHA256 = adapter.EXTERNAL_EVIDENCE_V0_2_SHA256
KERNEL_ADDITIVE_V0_2_PATH = adapter.KERNEL_ADDITIVE_V0_2_PATH
KERNEL_ADDITIVE_V0_2_SHA256 = adapter.KERNEL_ADDITIVE_V0_2_SHA256
CONSUMER_V0_3_PATH = adapter.CONSUMER_V0_3_PATH
CONSUMER_V0_3_SHA256 = adapter.CONSUMER_V0_3_SHA256

EXTERNAL_EVIDENCE_V0_1_PATH = (
    "schemas/claim-ir-external-envelope-evidence-v0.1.schema.json"
)
EXTERNAL_EVIDENCE_V0_1_SHA256 = (
    "9abc23e2258298038e137dbbe38168867d07108fa27719aa68c1c2b752ae2a7c"
)
KERNEL_LEGACY_PATH = "schemas/claim-ir-kernel.schema.json"
KERNEL_LEGACY_SHA256 = (
    "7c6fa2db0b75d69340be5a8843ba0c373e2d5b25b0d37cf8f1d1c416a787865d"
)

_EXPECTED_SCOPE = {
    "test_only": True,
    "in_memory_only": True,
    "surface_id": SURFACE_ID,
    "source_class": SOURCE_CLASS,
    "mapper_id": MAPPER_ID,
    "mapper_version": MAPPER_VERSION,
    "effective_registry_activation": False,
    "production_execute": False,
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "in_memory_nonempty_structural_only",
    "schema_version": SCHEMA_VERSION,
    "claim_ceiling": "PUBLIC_AUDIT_DECLARATION_ONLY",
    "file_write": False,
    "raw_source_read": False,
    "raw_source_persist": False,
    "mint": False,
    "admission": False,
    "kernel_ingestion": False,
    "kernel_write": False,
    "e_case_write": False,
    "certificate": False,
    "certified_stop": False,
}
_EXPECTED_STILL_BLOCKED = {
    "effective_registry_activation": True,
    "production_execute": True,
    "activation_ledger_write": True,
    "raw_audit_source_download_or_parse": True,
    "claim_id_mint": True,
    "admission": True,
    "kernel_ingestion": True,
    "kernel_store_write": True,
    "e_case_write": True,
    "a2_sufficiency_catalog_extension": True,
    "certificate_generation": True,
    "certified_stop": True,
    "path_b": True,
    "part_b_elevation": True,
}
_PLANNER_CLAIM_KINDS = {
    "public_config",
    "public_alignment_state",
    "public_action_declaration",
    "public_prospective_effect",
}
_OCCURRENCE_PATTERN = re.compile(r"^[A-Za-z0-9._:|-]{1,512}$")
_MISSING = object()


class M1AuditLogToClaimIRMapperError(ValueError):
    """Raised when A3 mapping fails closed or abstains."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def canonical_json_sha256(value: Any) -> str:
    """Return the deterministic digest used by package identities."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_NONCANONICAL_JSON",
            "value is not canonical JSON",
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def verify_mapper_pins(repo_root: Path) -> None:
    """Verify the A3 RED contract, adapter, and new exact identities."""

    root = repo_root.resolve()
    adapter.verify_adapter_pins(root)
    pins = {
        ADAPTER_IMPLEMENTATION_PATH: ADAPTER_IMPLEMENTATION_SHA256,
        EXTERNAL_EVIDENCE_V0_2_PATH: EXTERNAL_EVIDENCE_V0_2_SHA256,
        KERNEL_ADDITIVE_V0_2_PATH: KERNEL_ADDITIVE_V0_2_SHA256,
        CONSUMER_V0_3_PATH: CONSUMER_V0_3_SHA256,
        EXTERNAL_EVIDENCE_V0_1_PATH: EXTERNAL_EVIDENCE_V0_1_SHA256,
        KERNEL_LEGACY_PATH: KERNEL_LEGACY_SHA256,
    }
    for relative_path, expected_sha in pins.items():
        _verify_pin(root, relative_path, expected_sha)

    contract = _load_json(root / adapter.MAPPING_CONTRACT_PATH)
    identity = contract.get("identity")
    mappings = contract.get("field_to_claim_mapping")
    if (
        contract.get("status")
        != "design_only_draft_not_executable_pending_kernel_owner_review"
        or not isinstance(identity, Mapping)
        or identity.get("surface_id") != SURFACE_ID
        or identity.get("source_class") != SOURCE_CLASS
        or identity.get("future_mapper_id") != MAPPER_ID
        or not isinstance(mappings, list)
        or len(mappings) != 10
        or [entry.get("ordinal") for entry in mappings] != list(range(1, 11))
    ):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_MAPPING_CONTRACT",
            "accepted A3 ten-field mapping contract is malformed",
        )
    if any(
        not isinstance(entry, Mapping)
        or not str(entry.get("claim_kind", "")).startswith(
            "evidence.audit_log."
        )
        or not str(entry.get("evidence_field", "")).startswith(
            "evidence.audit_log."
        )
        or "source_field" in entry
        or "afs" in entry
        for entry in mappings
    ):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_MAPPING_NAMESPACE",
            "mapping contract escapes evidence.audit_log.*",
        )

    consumer = _load_json(root / CONSUMER_V0_3_PATH)
    dispatch = consumer.get("exact_schema_dispatch")
    routes = dispatch.get("routes") if isinstance(dispatch, Mapping) else None
    versions = (
        [route.get("schema_version") for route in routes]
        if isinstance(routes, list)
        else []
    )
    if (
        versions
        != [
            "claim-ir-external-v0.1",
            "claim-ir-external-evidence-v0.1",
            SCHEMA_VERSION,
        ]
        or dispatch.get("wildcard_or_fallback") is not False
        or dispatch.get("implicit_default") is not False
        or dispatch.get("unknown_schema_version")
        != "DENY_UNKNOWN_SCHEMA_VERSION"
    ):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_CONSUMER_DISPATCH",
            "consumer v0.3 exact dispatch is not closed",
        )

    try:
        Draft202012Validator.check_schema(
            _load_json(root / EXTERNAL_EVIDENCE_V0_2_PATH)
        )
        Draft202012Validator.check_schema(
            _load_json(root / KERNEL_ADDITIVE_V0_2_PATH)
        )
    except (SchemaError, TypeError, ValueError) as exc:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_SCHEMA_INVALID",
            "an A3 schema identity is invalid",
        ) from exc


def map_validated_audit_log_projection_to_claim_ir(
    projection: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Map one reported audit declaration to deterministic nonempty Claim-IR."""

    root = repo_root.resolve()
    verify_mapper_pins(root)
    if isinstance(projection, Sequence) and not isinstance(
        projection, (str, bytes, bytearray)
    ):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_CROSS_MODALITY_MERGE",
            "mapper accepts exactly one audit-log projection",
        )
    if not isinstance(projection, Mapping):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_PROJECTION_TYPE",
            "mapper input must be one object",
        )
    _validate_test_authority(authority, projection, root)
    try:
        adapter._scan_forbidden_input(projection)
        adapter._validate_projection_declaration(projection)
    except adapter.M1AuditLogProjectionAdapterError as exc:
        raise M1AuditLogToClaimIRMapperError(exc.code, str(exc)) from exc

    contract = _load_json(root / adapter.MAPPING_CONTRACT_PATH)
    claims = _emit_claims(
        projection,
        contract["field_to_claim_mapping"],
    )
    if not claims:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_EMPTY_MAPPING",
            "reported A3 mapping must emit nonempty claims",
        )
    digest = canonical_json_sha256(projection)
    package = {
        "schema_version": SCHEMA_VERSION,
        "package_id": f"pkg_audit_evidence_{digest[:32]}",
        "surface_id": SURFACE_ID,
        "kernel_state": "pending_kernel_schema",
        "claim_id_state": "not_minted",
        "admission_state": "not_admitted",
        "projection_ref": {
            "path": adapter.PROJECTION_CONTRACT_PATH,
            "sha256": adapter.PROJECTION_CONTRACT_SHA256,
            "surface_id": SURFACE_ID,
            "source_class": SOURCE_CLASS,
        },
        "claims": claims,
        "manifest": {
            "claim_count": len(claims),
            "field_path_set": [],
            "evidence_field_path_set": sorted(
                {claim["evidence_field"] for claim in claims}
            ),
            "projection_sha256": adapter.PROJECTION_CONTRACT_SHA256,
            "content_hash": canonical_json_sha256(
                {
                    "schema_version": SCHEMA_VERSION,
                    "surface_id": SURFACE_ID,
                    "source_class": SOURCE_CLASS,
                    "projection_sha256": adapter.PROJECTION_CONTRACT_SHA256,
                    "claims": claims,
                }
            ),
        },
    }
    _validate_output(package, root)
    return _json_copy(package)


def _validate_test_authority(
    authority: Mapping[str, Any] | None,
    projection: Mapping[str, Any],
    root: Path,
) -> None:
    if authority is None:
        raise M1AuditLogToClaimIRMapperError(
            "MISSING_TEST_ONLY_AUTHORITY",
            "explicit test-only mapper authority is required",
        )
    if not isinstance(authority, Mapping):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_AUTHORITY_TYPE",
            "mapper authority must be an object",
        )
    if set(authority) != {
        "status",
        "scope",
        "pinned_hashes",
        "pinned_input",
        "output_policy",
        "still_blocked",
    }:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_AUTHORITY_SHAPE",
            "mapper authority fields are not exact",
        )
    _require_constant(
        authority.get("status"),
        TEST_AUTHORITY_STATUS,
        "authority.status",
    )
    _require_exact_mapping(
        authority.get("scope"),
        _EXPECTED_SCOPE,
        "authority.scope",
    )
    _require_exact_mapping(
        authority.get("output_policy"),
        _EXPECTED_OUTPUT_POLICY,
        "authority.output_policy",
    )
    _require_exact_mapping(
        authority.get("still_blocked"),
        _EXPECTED_STILL_BLOCKED,
        "authority.still_blocked",
    )
    expected_hashes = {
        "a3_red_acceptance_sha256": adapter.A3_RED_ACCEPTANCE_SHA256,
        "projection_contract_sha256": adapter.PROJECTION_CONTRACT_SHA256,
        "mapping_contract_sha256": adapter.MAPPING_CONTRACT_SHA256,
        "external_evidence_v0_2_sha256": EXTERNAL_EVIDENCE_V0_2_SHA256,
        "kernel_additive_v0_2_sha256": KERNEL_ADDITIVE_V0_2_SHA256,
        "consumer_v0_3_sha256": CONSUMER_V0_3_SHA256,
        "adapter_implementation_sha256": ADAPTER_IMPLEMENTATION_SHA256,
        "mapper_implementation_sha256": _sha256(
            root / MAPPER_IMPLEMENTATION_PATH
        ),
    }
    _require_exact_mapping(
        authority.get("pinned_hashes"),
        expected_hashes,
        "authority.pinned_hashes",
    )
    _require_exact_mapping(
        authority.get("pinned_input"),
        {
            "source_class": SOURCE_CLASS,
            "projection_sha256": adapter.PROJECTION_CONTRACT_SHA256,
            "projection_content_sha256": canonical_json_sha256(projection),
        },
        "authority.pinned_input",
    )


def _emit_claims(
    projection: Mapping[str, Any],
    mappings: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    metadata = projection["source_metadata"]
    occurrence_key = projection["audit_entry"]["entry_id"]
    if not _OCCURRENCE_PATTERN.fullmatch(occurrence_key):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_OCCURRENCE_KEY",
            "audit entry ID is not an accepted occurrence key",
        )
    claims: list[dict[str, Any]] = []
    for mapping in mappings:
        value = _get_path(projection, mapping["field_path"])
        if value is _MISSING:
            if mapping["presence"] == "optional":
                continue
            raise M1AuditLogToClaimIRMapperError(
                "DENY_MISSING_MAPPING_FIELD",
                f"required mapping field is absent: {mapping['field_path']}",
            )
        if (
            mapping["presence"] == "required_const_true"
            and value is not True
        ):
            raise M1AuditLogToClaimIRMapperError(
                "DENY_RECORDED_MARKER",
                "recorded_marker must remain true",
            )
        _validate_value(mapping["value_type"], value, mapping["field_path"])
        claims.append(
            {
                "record_class": "public_evidence_declaration",
                "claim_id": None,
                "claim_id_state": "not_minted",
                "claim_kind": mapping["claim_kind"],
                "evidence_field": mapping["evidence_field"],
                "occurrence_key": occurrence_key,
                "value_type": mapping["value_type"],
                "value": _json_copy(value),
                "source_class": SOURCE_CLASS,
                "source_record_ref": projection["descriptor"][
                    "opaque_record_reference"
                ],
                "epistemic_modality": metadata["epistemic_modality"],
                "modality_basis_code": metadata["modality_basis_code"],
                "trusted_ingestion_metadata_sha256": metadata[
                    "trusted_ingestion_metadata_sha256"
                ],
                "admission_state": "not_admitted",
            }
        )
    return claims


def _validate_value(value_type: str, value: Any, location: str) -> None:
    if value_type == "opaque_reference":
        try:
            adapter._require_safe_opaque(value, location)
        except adapter.M1AuditLogProjectionAdapterError as exc:
            raise M1AuditLogToClaimIRMapperError(exc.code, str(exc)) from exc
    elif value_type == "bounded_enum":
        if (
            not isinstance(value, str)
            or not value
            or len(value) > 128
            or not adapter._OPAQUE_PATTERN.fullmatch(value)
        ):
            raise M1AuditLogToClaimIRMapperError(
                "DENY_VALUE_TYPE",
                f"{location} is not a bounded enum",
            )
    elif value_type == "bounded_public_text":
        if not isinstance(value, str) or not value or len(value) > 1024:
            raise M1AuditLogToClaimIRMapperError(
                "DENY_VALUE_TYPE",
                f"{location} is not bounded public text",
            )
    elif value_type == "bounded_boolean":
        if not isinstance(value, bool):
            raise M1AuditLogToClaimIRMapperError(
                "DENY_VALUE_TYPE",
                f"{location} is not a bounded boolean",
            )
    else:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_VALUE_TYPE",
            f"unsupported mapping value type: {value_type}",
        )


def _validate_output(package: Mapping[str, Any], root: Path) -> None:
    external_v0_1 = _load_json(root / EXTERNAL_EVIDENCE_V0_1_PATH)
    external_v0_2 = _load_json(root / EXTERNAL_EVIDENCE_V0_2_PATH)
    legacy_kernel = _load_json(root / KERNEL_LEGACY_PATH)
    kernel_v0_2 = _load_json(root / KERNEL_ADDITIVE_V0_2_PATH)

    registry = Registry()
    for schema in (external_v0_1, external_v0_2, legacy_kernel):
        registry = registry.with_resource(
            schema["$id"],
            Resource.from_contents(schema),
        )
    external_validator = Draft202012Validator(
        external_v0_2,
        registry=registry,
    )
    errors = sorted(
        external_validator.iter_errors(package),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise M1AuditLogToClaimIRMapperError(
            "DENY_OUTPUT_SCHEMA",
            f"external evidence-v0.2 output fails at {location}: {first.message}",
        )

    kernel_validator = Draft202012Validator(
        kernel_v0_2,
        registry=registry,
    )
    for index, claim in enumerate(package["claims"]):
        claim_errors = list(kernel_validator.iter_errors(claim))
        if claim_errors:
            raise M1AuditLogToClaimIRMapperError(
                "DENY_KERNEL_ADDITIVE_SCHEMA",
                f"audit claim {index} fails additive Kernel v0.2 oneOf",
            )

    if package["manifest"]["claim_count"] != len(package["claims"]):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_CONSUMER_INVARIANT",
            "manifest claim_count is not exact",
        )
    expected_fields = sorted(
        {claim["evidence_field"] for claim in package["claims"]}
    )
    if package["manifest"]["evidence_field_path_set"] != expected_fields:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_CONSUMER_INVARIANT",
            "manifest evidence field set is not exact",
        )
    if package["manifest"]["projection_sha256"] != package["projection_ref"][
        "sha256"
    ]:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_CONSUMER_INVARIANT",
            "manifest and projection SHA differ",
        )
    for claim in package["claims"]:
        if (
            claim["source_class"] != SOURCE_CLASS
            or not claim["claim_kind"].startswith("evidence.audit_log.")
            or not claim["evidence_field"].startswith("evidence.audit_log.")
            or claim["claim_kind"] in _PLANNER_CLAIM_KINDS
            or claim["claim_id"] is not None
            or claim["claim_id_state"] != "not_minted"
            or claim["admission_state"] != "not_admitted"
        ):
            raise M1AuditLogToClaimIRMapperError(
                "DENY_CONSUMER_INVARIANT",
                "audit claim violates the structural-only boundary",
            )


def _get_path(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    location: str,
) -> None:
    if not isinstance(value, Mapping) or dict(value) != dict(expected):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_CONSTANT_OR_PIN_MISMATCH",
            f"{location} does not match the exact accepted mapping",
        )


def _require_constant(value: Any, expected: Any, location: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_CONSTANT_OR_PIN_MISMATCH",
            f"{location} does not match the accepted constant",
        )


def _verify_pin(root: Path, relative_path: str, expected_sha: str) -> None:
    path = root / relative_path
    if not path.is_file():
        raise M1AuditLogToClaimIRMapperError(
            "DENY_MISSING_PIN",
            f"missing pinned artifact: {relative_path}",
        )
    if _sha256(path) != expected_sha:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_PIN_MISMATCH",
            f"pinned artifact SHA mismatch: {relative_path}",
        )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_JSON_PIN",
            f"cannot read pinned JSON: {path}",
        ) from exc
    if not isinstance(value, dict):
        raise M1AuditLogToClaimIRMapperError(
            "DENY_JSON_PIN",
            f"pinned JSON is not an object: {path}",
        )
    return value


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise M1AuditLogToClaimIRMapperError(
            "DENY_FILE_READ",
            f"cannot read pinned file: {path}",
        ) from exc


def _json_copy(value: Any) -> Any:
    return json.loads(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
