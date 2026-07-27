"""Test-only adapter for an audit-log public projection declaration.

The adapter accepts only an already-public, in-memory declaration.  It never
resolves the opaque reference, reads a raw audit record, activates a registry,
mints a Claim-ID, admits evidence, or writes Kernel/E_case state.  A successful
return means only that the declaration matches the accepted A3 RED boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError


SURFACE_ID = "project05_depth2_public"
SOURCE_CLASS = "audit_log_public_projection"
ADAPTER_ID = "m1a_audit_log_projection_v0_1"
ADAPTER_VERSION = "0.1.0"
TEST_AUTHORITY_STATUS = (
    "activated_test_only_in_memory_audit_log_public_projection_authority"
)
ADAPTER_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_audit_log_projection_adapter.py"
)

A3_RED_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-m1-audit-log-evidence-modality-red-owner-acceptance-"
    "v0.1-20260727.json"
)
A3_RED_ACCEPTANCE_SHA256 = (
    "2113590604e86ef82694b5c98632fb8f1132f1c2c88e54398a02a24f9f30b4a5"
)
RED_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-audit-log-evidence-modality-red-design-"
    "v0.1-20260727.json"
)
RED_DESIGN_SHA256 = (
    "6c92dc2440cdc0802ab807789e64a91de56bde39f0278c44802c3db40b17bf85"
)
PROJECTION_CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-audit-log-public-field-projection-"
    "v0.1-20260727.json"
)
PROJECTION_CONTRACT_SHA256 = (
    "93e0d63010eff7e05559d0ca28a00a6b8ab5ce37ed7c469ede09b5c1bf893625"
)
PROJECTION_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-m1-audit-log-public-field-projection-"
    "v0.1-20260727"
)
MAPPING_CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-audit-log-to-claim-ir-mapping-contract-"
    "v0.1-20260727.json"
)
MAPPING_CONTRACT_SHA256 = (
    "7f21af8644a6e686fe26f62f3fabc3a0379e7774cde9613b200ed9025503ece0"
)
RED_FIXTURE_PATH = (
    "docs/llm-editor/fixtures/audit-log-public-projection-red-v0.1/"
    "synthetic-audit-log-public-projection-minimal-v0.1.json"
)
RED_FIXTURE_SHA256 = (
    "3a2e1857e994dddd2fcf9137a106ab05294d5e952924eb2bcf84971f4c32f38a"
)
RED_REVIEW_PACKET_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-kernel-owner-m1-audit-log-evidence-modality-"
    "red-review-packet-v0.1-20260727.json"
)
RED_REVIEW_PACKET_SHA256 = (
    "9659aecfc67a46efa039aff909eca5e382fdba3d7d790bf04685d0a10401c916"
)

EXTERNAL_EVIDENCE_V0_2_PATH = (
    "schemas/claim-ir-external-envelope-evidence-v0.2.schema.json"
)
EXTERNAL_EVIDENCE_V0_2_SHA256 = (
    "e246c44b7513a5bc2f3410a2739a53bd1f40dad3e767036bb1af3158c9e02ac6"
)
KERNEL_ADDITIVE_V0_2_PATH = (
    "schemas/claim-ir-kernel-evidence-additive-v0.2.schema.json"
)
KERNEL_ADDITIVE_V0_2_SHA256 = (
    "ef4aa92e5130286c5da142a4f6780d372fbec2e9bd4f2830222e035e99c3f35f"
)
CONSUMER_V0_3_PATH = (
    "docs/kernel/"
    "kernel-v0.8-shared-claim-ir-consumer-contract-evidence-candidate-"
    "effective-v0.3-20260727.json"
)
CONSUMER_V0_3_SHA256 = (
    "7662762d045381921b8f94a39753d0c491322b3a41d473226cc5fe3f4688457c"
)

_EXPECTED_AUTHORITY_SCOPE = {
    "test_only": True,
    "in_memory_only": True,
    "surface_id": SURFACE_ID,
    "source_class": SOURCE_CLASS,
    "adapter_id": ADAPTER_ID,
    "adapter_version": ADAPTER_VERSION,
    "registry_activation": False,
    "production_execute": False,
    "raw_audit_source_resolution": False,
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "validated_public_declaration_only",
    "file_write": False,
    "raw_source_read": False,
    "raw_source_persist": False,
    "mint": False,
    "admission": False,
    "kernel_write": False,
    "e_case_write": False,
    "certificate": False,
    "certified_stop": False,
    "claim_ceiling": "PUBLIC_AUDIT_DECLARATION_ONLY",
}
_EXPECTED_STILL_BLOCKED = {
    "effective_registry_activation": True,
    "production_execute": True,
    "activation_ledger_write": True,
    "raw_audit_source_download_or_parse": True,
    "claim_id_mint": True,
    "admission": True,
    "kernel_store_write": True,
    "e_case_write": True,
    "a2_sufficiency_catalog_extension": True,
    "certificate_generation": True,
    "certified_stop": True,
    "path_b": True,
    "part_b_elevation": True,
}

_REQUIRED_AUDIT_FIELDS = {
    "entry_id",
    "recorded_at",
    "operation_class",
    "target_class",
    "public_target_ref",
    "reported_outcome",
    "recorded_marker",
}
_OPTIONAL_AUDIT_FIELDS = {
    "public_actor_ref",
    "public_change_ref",
    "public_request_ref",
}
_OPERATION_CLASSES = {
    "create",
    "update",
    "delete",
    "read_access",
    "policy_change",
    "configuration_change",
    "credential_change",
    "role_binding_change",
    "administrative_other",
}
_TARGET_CLASSES = {
    "configuration",
    "policy",
    "account",
    "role_binding",
    "resource",
    "software",
    "data_object",
    "other_public",
}
_OUTCOMES = {"succeeded", "failed", "denied", "unknown"}
_OPAQUE_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_KEYS = {
    "path",
    "filesystem_path",
    "archive_member_path",
    "uri",
    "url",
    "endpoint",
    "raw_source",
    "raw_record",
    "raw_bytes",
    "raw_payload",
    "payload",
    "payload_bytes",
    "full_text",
    "message",
    "diff",
    "before_value",
    "after_value",
    "body",
    "request_body",
    "response_body",
    "authorization_token",
    "token",
    "credential",
    "secret",
    "labels",
    "verdict",
    "ground_truth",
    "oracle",
    "hidden_claim_ids",
    "certificate",
    "certified_stop",
}
_PLANNER_NAMESPACE_KEYS = {
    "source_field",
    "afs",
    "afs_slot",
    "afs_path",
}
_CROSS_MODALITY_BODY_KEYS = {"event", "graph", "report"}


class M1AuditLogProjectionAdapterError(ValueError):
    """Raised when the test-only audit-log adapter fails closed or abstains."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def canonical_json_sha256(value: Any) -> str:
    """Return the deterministic digest used for in-memory declarations."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise M1AuditLogProjectionAdapterError(
            "DENY_NONCANONICAL_JSON",
            "projection is not canonical JSON",
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def verify_adapter_pins(repo_root: Path) -> None:
    """Verify the accepted RED boundary, protected table, and new identities."""

    root = repo_root.resolve()
    direct_pins = {
        A3_RED_ACCEPTANCE_PATH: A3_RED_ACCEPTANCE_SHA256,
        RED_DESIGN_PATH: RED_DESIGN_SHA256,
        PROJECTION_CONTRACT_PATH: PROJECTION_CONTRACT_SHA256,
        MAPPING_CONTRACT_PATH: MAPPING_CONTRACT_SHA256,
        RED_FIXTURE_PATH: RED_FIXTURE_SHA256,
        RED_REVIEW_PACKET_PATH: RED_REVIEW_PACKET_SHA256,
        EXTERNAL_EVIDENCE_V0_2_PATH: EXTERNAL_EVIDENCE_V0_2_SHA256,
        KERNEL_ADDITIVE_V0_2_PATH: KERNEL_ADDITIVE_V0_2_SHA256,
        CONSUMER_V0_3_PATH: CONSUMER_V0_3_SHA256,
    }
    for relative_path, expected_sha in direct_pins.items():
        _verify_pin(root, relative_path, expected_sha)

    review = _load_json(root / RED_REVIEW_PACKET_PATH)
    inherited = review.get("mandatory_pin_table")
    if not isinstance(inherited, list) or len(inherited) != 21:
        raise M1AuditLogProjectionAdapterError(
            "DENY_PROTECTED_PIN_TABLE",
            "A3 RED protected pin table is not the exact 21-entry table",
        )
    for record in inherited:
        if (
            not isinstance(record, Mapping)
            or set(record) != {"role", "path", "sha256"}
            or not isinstance(record["path"], str)
            or not isinstance(record["sha256"], str)
        ):
            raise M1AuditLogProjectionAdapterError(
                "DENY_PROTECTED_PIN_TABLE",
                "A3 RED protected pin record is malformed",
            )
        _verify_pin(root, record["path"], record["sha256"])

    acceptance = _load_json(root / A3_RED_ACCEPTANCE_PATH)
    _require_constant(acceptance.get("decision"), "accept", "acceptance.decision")
    _require_constant(
        acceptance.get("entry_conclusion_accepted"),
        "ENTER_V0_1_CANDIDATE",
        "acceptance.entry_conclusion_accepted",
    )
    _require_constant(
        acceptance.get("effective_state_now"),
        "OUT_OF_V0_1",
        "acceptance.effective_state_now",
    )

    projection_contract = _load_json(root / PROJECTION_CONTRACT_PATH)
    identity = projection_contract.get("projection_identity")
    if not isinstance(identity, Mapping):
        raise M1AuditLogProjectionAdapterError(
            "DENY_PROJECTION_CONTRACT",
            "projection identity is missing",
        )
    for field, expected in (
        ("surface_id", SURFACE_ID),
        ("source_class", SOURCE_CLASS),
        ("future_adapter_id", ADAPTER_ID),
        ("future_adapter_version", ADAPTER_VERSION),
        ("future_mapper_id", "m1m_audit_log_to_claim_ir_v0_1"),
    ):
        _require_constant(
            identity.get(field),
            expected,
            f"projection_contract.identity.{field}",
        )
    _require_constant(
        projection_contract.get("scientific_scope", {}).get("claim_ceiling"),
        "PUBLIC_AUDIT_DECLARATION_ONLY",
        "projection_contract.claim_ceiling",
    )

    mapping_contract = _load_json(root / MAPPING_CONTRACT_PATH)
    mappings = mapping_contract.get("field_to_claim_mapping")
    if (
        not isinstance(mappings, list)
        or len(mappings) != 10
        or [entry.get("ordinal") for entry in mappings] != list(range(1, 11))
        or any(
            not str(entry.get("claim_kind", "")).startswith(
                "evidence.audit_log."
            )
            or not str(entry.get("evidence_field", "")).startswith(
                "evidence.audit_log."
            )
            for entry in mappings
            if isinstance(entry, Mapping)
        )
    ):
        raise M1AuditLogProjectionAdapterError(
            "DENY_MAPPING_CONTRACT",
            "the accepted exact ten-field audit mapping is not pinned",
        )

    consumer = _load_json(root / CONSUMER_V0_3_PATH)
    dispatch = consumer.get("exact_schema_dispatch")
    routes = dispatch.get("routes") if isinstance(dispatch, Mapping) else None
    v0_2_routes = (
        [
            route
            for route in routes
            if isinstance(route, Mapping)
            and route.get("schema_version")
            == "claim-ir-external-evidence-v0.2"
        ]
        if isinstance(routes, list)
        else []
    )
    if (
        not isinstance(dispatch, Mapping)
        or dispatch.get("wildcard_or_fallback") is not False
        or dispatch.get("implicit_default") is not False
        or len(v0_2_routes) != 1
        or v0_2_routes[0].get("new_source_class") != SOURCE_CLASS
    ):
        raise M1AuditLogProjectionAdapterError(
            "DENY_CONSUMER_DISPATCH",
            "consumer v0.3 does not provide one exact audit-log route",
        )

    try:
        Draft202012Validator.check_schema(
            _load_json(root / EXTERNAL_EVIDENCE_V0_2_PATH)
        )
        Draft202012Validator.check_schema(
            _load_json(root / KERNEL_ADDITIVE_V0_2_PATH)
        )
    except (SchemaError, TypeError, ValueError) as exc:
        raise M1AuditLogProjectionAdapterError(
            "DENY_SCHEMA_INVALID",
            "a new A3 schema identity is invalid",
        ) from exc


def adapt_audit_log_public_projection(
    projection: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a canonical validated declaration, never raw audit material."""

    root = repo_root.resolve()
    verify_adapter_pins(root)
    if not isinstance(projection, Mapping):
        raise M1AuditLogProjectionAdapterError(
            "DENY_PROJECTION_TYPE",
            "audit-log projection must be one object",
        )
    _scan_forbidden_input(projection)
    _validate_test_authority(authority, projection, root)
    _validate_projection_declaration(projection)
    return _json_copy(projection)


def _validate_test_authority(
    authority: Mapping[str, Any] | None,
    projection: Mapping[str, Any],
    root: Path,
) -> None:
    if authority is None:
        raise M1AuditLogProjectionAdapterError(
            "MISSING_TEST_ONLY_AUTHORITY",
            "explicit test-only in-memory authority is required",
        )
    if not isinstance(authority, Mapping):
        raise M1AuditLogProjectionAdapterError(
            "DENY_AUTHORITY_TYPE",
            "authority must be an object",
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
        raise M1AuditLogProjectionAdapterError(
            "DENY_AUTHORITY_SHAPE",
            "authority fields are not exact",
        )
    _require_constant(
        authority.get("status"),
        TEST_AUTHORITY_STATUS,
        "authority.status",
    )
    _require_exact_mapping(
        authority.get("scope"),
        _EXPECTED_AUTHORITY_SCOPE,
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
        "a3_red_acceptance_sha256": A3_RED_ACCEPTANCE_SHA256,
        "projection_contract_sha256": PROJECTION_CONTRACT_SHA256,
        "mapping_contract_sha256": MAPPING_CONTRACT_SHA256,
        "external_evidence_v0_2_sha256": EXTERNAL_EVIDENCE_V0_2_SHA256,
        "kernel_additive_v0_2_sha256": KERNEL_ADDITIVE_V0_2_SHA256,
        "consumer_v0_3_sha256": CONSUMER_V0_3_SHA256,
        "adapter_implementation_sha256": _sha256(
            root / ADAPTER_IMPLEMENTATION_PATH
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
            "projection_contract_sha256": PROJECTION_CONTRACT_SHA256,
            "projection_content_sha256": canonical_json_sha256(projection),
        },
        "authority.pinned_input",
    )


def _validate_projection_declaration(projection: Mapping[str, Any]) -> None:
    if set(projection) & _CROSS_MODALITY_BODY_KEYS:
        raise M1AuditLogProjectionAdapterError(
            "DENY_CROSS_MODALITY_MERGE",
            "audit-log projection cannot carry another modality body",
        )
    _require_exact_keys(
        projection,
        {"descriptor", "audit_entry", "source_metadata"},
        "projection",
    )
    descriptor = projection["descriptor"]
    _require_exact_keys(
        descriptor,
        {
            "surface_id",
            "source_class",
            "opaque_record_reference",
            "projection_pin_declaration",
        },
        "projection.descriptor",
    )
    _require_constant(
        descriptor["surface_id"],
        SURFACE_ID,
        "projection.descriptor.surface_id",
    )
    _require_constant(
        descriptor["source_class"],
        SOURCE_CLASS,
        "projection.descriptor.source_class",
    )
    _require_safe_opaque(
        descriptor["opaque_record_reference"],
        "projection.descriptor.opaque_record_reference",
    )
    _require_exact_mapping(
        descriptor["projection_pin_declaration"],
        {
            "artifact_id": PROJECTION_ARTIFACT_ID,
            "version": "0.1",
            "sha256": PROJECTION_CONTRACT_SHA256,
        },
        "projection.descriptor.projection_pin_declaration",
    )

    entry = projection["audit_entry"]
    if (
        not isinstance(entry, Mapping)
        or not _REQUIRED_AUDIT_FIELDS.issubset(entry)
        or not set(entry).issubset(
            _REQUIRED_AUDIT_FIELDS | _OPTIONAL_AUDIT_FIELDS
        )
    ):
        raise M1AuditLogProjectionAdapterError(
            "DENY_UNKNOWN_OR_MISSING_FIELD",
            "audit_entry fields do not match the closed projection contract",
        )
    _require_safe_opaque(entry["entry_id"], "projection.audit_entry.entry_id")
    _require_rfc3339_utc(
        entry["recorded_at"],
        "projection.audit_entry.recorded_at",
    )
    if entry["operation_class"] not in _OPERATION_CLASSES:
        raise M1AuditLogProjectionAdapterError(
            "DENY_OPERATION_CLASS",
            "operation_class is not allowlisted",
        )
    if entry["target_class"] not in _TARGET_CLASSES:
        raise M1AuditLogProjectionAdapterError(
            "DENY_TARGET_CLASS",
            "target_class is not allowlisted",
        )
    _require_safe_opaque(
        entry["public_target_ref"],
        "projection.audit_entry.public_target_ref",
    )
    if entry["reported_outcome"] not in _OUTCOMES:
        raise M1AuditLogProjectionAdapterError(
            "DENY_REPORTED_OUTCOME",
            "reported_outcome is not allowlisted",
        )
    if entry["recorded_marker"] is not True:
        raise M1AuditLogProjectionAdapterError(
            "DENY_RECORDED_MARKER",
            "recorded_marker must be the declaration const true",
        )
    for field in sorted(_OPTIONAL_AUDIT_FIELDS & set(entry)):
        _require_safe_opaque(entry[field], f"projection.audit_entry.{field}")

    metadata = projection["source_metadata"]
    _require_exact_keys(
        metadata,
        {
            "source_family",
            "epistemic_modality",
            "modality_basis_code",
            "trusted_ingestion_metadata_sha256",
        },
        "projection.source_metadata",
    )
    _require_constant(
        metadata["source_family"],
        "control_plane_audit",
        "projection.source_metadata.source_family",
    )
    modality = metadata["epistemic_modality"]
    if modality in {"observed", "derived"}:
        raise M1AuditLogProjectionAdapterError(
            "DENY_MODALITY_LAUNDERING",
            "audit-log public declarations cannot be observed or derived",
        )
    expected_basis = {
        "reported": "PUBLIC_AUDIT_RECORD_DECLARATION",
        "unknown": "UNRESOLVED_AUDIT_BASIS",
    }.get(modality)
    if expected_basis is None:
        raise M1AuditLogProjectionAdapterError(
            "DENY_UNKNOWN_MODALITY",
            "audit-log modality is not reported or unknown",
        )
    _require_constant(
        metadata["modality_basis_code"],
        expected_basis,
        "projection.source_metadata.modality_basis_code",
    )
    _require_sha(
        metadata["trusted_ingestion_metadata_sha256"],
        "projection.source_metadata.trusted_ingestion_metadata_sha256",
    )
    if modality == "unknown":
        raise M1AuditLogProjectionAdapterError(
            "ABSTAIN_NO_PACKAGE",
            "unknown audit basis abstains before any package or claim emission",
        )


def _scan_forbidden_input(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise M1AuditLogProjectionAdapterError(
            "DENY_RAW_AUDIT_MATERIAL",
            f"raw bytes are forbidden at {'.'.join(path) or '<root>'}",
        )
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().casefold().replace("-", "_")
            if normalized in _PLANNER_NAMESPACE_KEYS:
                raise M1AuditLogProjectionAdapterError(
                    "DENY_PLANNER_NAMESPACE",
                    f"planner namespace is forbidden at {'.'.join((*path, str(key)))}",
                )
            if normalized in _FORBIDDEN_KEYS:
                raise M1AuditLogProjectionAdapterError(
                    "DENY_RAW_AUDIT_MATERIAL",
                    f"forbidden audit material at {'.'.join((*path, str(key)))}",
                )
            _scan_forbidden_input(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for index, nested in enumerate(value):
            _scan_forbidden_input(nested, (*path, str(index)))
    elif isinstance(value, str):
        folded = value.casefold()
        if (
            "://" in value
            or "\\" in value
            or folded.startswith(("file:", "http:", "https:"))
        ):
            raise M1AuditLogProjectionAdapterError(
                "DENY_PATH_OR_URI",
                f"path or URI is forbidden at {'.'.join(path) or '<root>'}",
            )
        if folded.startswith("evidence.system_log."):
            raise M1AuditLogProjectionAdapterError(
                "DENY_NAMESPACE_ALIAS",
                "audit-log input cannot alias evidence.system_log.*",
            )


def _require_exact_keys(
    value: Any,
    expected: set[str],
    location: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise M1AuditLogProjectionAdapterError(
            "DENY_UNKNOWN_OR_MISSING_FIELD",
            f"{location} fields are not exact",
        )


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    location: str,
) -> None:
    if not isinstance(value, Mapping) or dict(value) != dict(expected):
        raise M1AuditLogProjectionAdapterError(
            "DENY_CONSTANT_OR_PIN_MISMATCH",
            f"{location} does not match the exact accepted mapping",
        )


def _require_constant(value: Any, expected: Any, location: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise M1AuditLogProjectionAdapterError(
            "DENY_CONSTANT_OR_PIN_MISMATCH",
            f"{location} does not match the accepted constant",
        )


def _require_safe_opaque(value: Any, location: str) -> None:
    if not isinstance(value, str) or not _OPAQUE_PATTERN.fullmatch(value):
        raise M1AuditLogProjectionAdapterError(
            "DENY_UNSAFE_OPAQUE_REFERENCE",
            f"{location} is not a safe opaque reference",
        )


def _require_sha(value: Any, location: str) -> None:
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise M1AuditLogProjectionAdapterError(
            "DENY_SHA256",
            f"{location} is not a lowercase SHA-256",
        )


def _require_rfc3339_utc(value: Any, location: str) -> None:
    if not isinstance(value, str) or not value.endswith("Z") or len(value) > 64:
        raise M1AuditLogProjectionAdapterError(
            "DENY_RECORDED_AT",
            f"{location} must be bounded RFC3339 UTC text",
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise M1AuditLogProjectionAdapterError(
            "DENY_RECORDED_AT",
            f"{location} is not RFC3339",
        ) from exc
    if parsed.tzinfo is None or parsed.astimezone(timezone.utc).utcoffset():
        raise M1AuditLogProjectionAdapterError(
            "DENY_RECORDED_AT",
            f"{location} is not UTC",
        )


def _verify_pin(root: Path, relative_path: str, expected_sha: str) -> None:
    path = root / relative_path
    if not path.is_file():
        raise M1AuditLogProjectionAdapterError(
            "DENY_MISSING_PIN",
            f"missing pinned artifact: {relative_path}",
        )
    if _sha256(path) != expected_sha:
        raise M1AuditLogProjectionAdapterError(
            "DENY_PIN_MISMATCH",
            f"pinned artifact SHA mismatch: {relative_path}",
        )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise M1AuditLogProjectionAdapterError(
            "DENY_JSON_PIN",
            f"cannot read pinned JSON: {path}",
        ) from exc
    if not isinstance(value, dict):
        raise M1AuditLogProjectionAdapterError(
            "DENY_JSON_PIN",
            f"pinned JSON is not an object: {path}",
        )
    return value


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise M1AuditLogProjectionAdapterError(
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
