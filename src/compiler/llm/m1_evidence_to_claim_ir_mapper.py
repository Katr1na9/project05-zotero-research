"""Test-only GREEN-2 mapper for public evidence projections.

The mapper consumes one already projected, in-memory declaration and emits a
nonempty ``claim-ir-external-evidence-v0.1`` package.  It has no registry,
download, raw-source, mint, admission, ingestion, Kernel, E_case, certificate,
or STOP capability.  The three existing zero-claim projection adapters remain
byte-identical compatibility paths.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError
from referencing import Registry, Resource


SURFACE_ID = "project05_depth2_public"
SCHEMA_VERSION = "claim-ir-external-evidence-v0.1"
MAPPER_ID = "m1m_evidence_to_claim_ir_green_2_v0_1"
MAPPER_VERSION = "0.1.0"
TEST_AUTHORITY_STATUS = (
    "activated_test_only_in_memory_evidence_to_claim_ir_green_2_authority"
)
MAPPER_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_evidence_to_claim_ir_mapper.py"
)

SCHEMA_GREEN_ACCEPTANCE_PATH = (
    "docs/kernel/"
    "kernel-v0.8-claim-ir-evidence-claim-record-schema-green-owner-acceptance-"
    "v0.1-20260727.json"
)
SCHEMA_GREEN_ACCEPTANCE_SHA256 = (
    "60c31ffef0e4288f031b749ff89807904d13986025b56c769295ef80348ce148"
)
EXTERNAL_EVIDENCE_SCHEMA_PATH = (
    "schemas/claim-ir-external-envelope-evidence-v0.1.schema.json"
)
EXTERNAL_EVIDENCE_SCHEMA_SHA256 = (
    "9abc23e2258298038e137dbbe38168867d07108fa27719aa68c1c2b752ae2a7c"
)
KERNEL_ADDITIVE_SCHEMA_PATH = (
    "schemas/claim-ir-kernel-evidence-additive-v0.1.schema.json"
)
KERNEL_ADDITIVE_SCHEMA_SHA256 = (
    "d8cccbad36c6cca068fdc9d17ecbd8d0db2e08271f986127d0c0236353a79ce5"
)
CONSUMER_CONTRACT_PATH = (
    "docs/kernel/"
    "kernel-v0.8-shared-claim-ir-consumer-contract-evidence-candidate-effective-"
    "v0.2-20260727.json"
)
CONSUMER_CONTRACT_SHA256 = (
    "fe5222b9b4e0ddaf990761b34bdfc5004f45f55d3e2155b09388fb9596a1e504"
)
LEGACY_KERNEL_SCHEMA_PATH = "schemas/claim-ir-kernel.schema.json"
LEGACY_KERNEL_SCHEMA_SHA256 = (
    "7c6fa2db0b75d69340be5a8843ba0c373e2d5b25b0d37cf8f1d1c416a787865d"
)
LEGACY_EXTERNAL_SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
LEGACY_EXTERNAL_SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
LEGACY_CONSUMER_CONTRACT_PATH = (
    "docs/kernel/"
    "kernel-v0.8-shared-claim-ir-consumer-contract-effective-v0.1-20260725.json"
)
LEGACY_CONSUMER_CONTRACT_SHA256 = (
    "a2a176fdeb2b93205a7f5e11c7c096236e2dc582d1c31f8f4a1534866c008d63"
)
MAPPING_FRAMEWORK_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-evidence-to-claim-ir-mapping-framework-design-"
    "v0.1-20260726.json"
)
MAPPING_FRAMEWORK_SHA256 = (
    "796a8ce3b8f3ac154de2aa787635c0b531ce6a179bc22e8906e7623002947fb1"
)

SYSTEM_LOG_ADAPTER_PATH = (
    "src/compiler/llm/m1_system_log_projection_adapter.py"
)
SYSTEM_LOG_ADAPTER_SHA256 = (
    "b7cc4710a2db30eedb353b44671d0f4993a50442c3f5bd2afe06ed5ee33f0116"
)
PROVENANCE_GRAPH_ADAPTER_PATH = (
    "src/compiler/llm/m1_provenance_graph_projection_adapter.py"
)
PROVENANCE_GRAPH_ADAPTER_SHA256 = (
    "9068315019a2980bb43b81d9641537c5a7c69ca63f14c4b9e876a653f8ffeae5"
)
CTI_REPORT_ADAPTER_PATH = (
    "src/compiler/llm/m1_cti_report_projection_adapter.py"
)
CTI_REPORT_ADAPTER_SHA256 = (
    "cc0e04dd15372ecc1e0b5b68777458f07a361cb77ec7ce2c318b1ef42a07be3e"
)

_OPAQUE_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_OCCURRENCE_PATTERN = re.compile(r"^[A-Za-z0-9._:|+-]{1,1024}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_MISSING = object()

_FORBIDDEN_INPUT_KEYS = frozenset(
    {
        "source_field",
        "afs",
        "afs_slot",
        "afs_path",
        "filesystem_path",
        "archive_member_path",
        "path",
        "uri",
        "url",
        "endpoint",
        "raw_source",
        "raw_bytes",
        "raw_payload",
        "payload_bytes",
        "body",
        "excerpt",
        "full_text",
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
        "certificate",
        "certified_stop",
    }
)
_PLANNER_CLAIM_KINDS = frozenset(
    {
        "public_config",
        "public_alignment_state",
        "public_action_declaration",
        "public_prospective_effect",
    }
)
_SOURCE_CLASSES = (
    "cti_report_public_projection",
    "provenance_graph_public_projection",
    "system_log_public_projection",
)


class M1EvidenceToClaimIRMapperError(ValueError):
    """Raised when GREEN-2 mapping fails closed or abstains."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


_SPECS: dict[str, dict[str, Any]] = {
    "system_log_public_projection": {
        "body_key": "event",
        "mapping_contract_path": (
            "docs/llm-editor/"
            "llm-editor-v0.8-l2-m1-system-log-to-claim-ir-mapping-contract-"
            "v0.1-20260726.json"
        ),
        "mapping_contract_sha256": (
            "15bda95021ce21a6016d4f0e2ae96950dd70fdbf433f5cc6e5f47f8ebd1926cb"
        ),
        "mapper_id": "m1m_system_log_to_claim_ir_v0_1",
        "projection_path": (
            "docs/llm-editor/"
            "llm-editor-v0.8-l2-m1-system-log-public-field-projection-"
            "v0.1-20260726.json"
        ),
        "projection_sha256": (
            "5c707f5cfa6534d11d04c4f10899ea133396c00961041112353321f47d78f8bb"
        ),
        "projection_artifact_id": (
            "llm-editor-v0.8-l2-m1-system-log-public-field-projection-"
            "v0.1-20260726"
        ),
        "adapter_path": SYSTEM_LOG_ADAPTER_PATH,
        "adapter_sha256": SYSTEM_LOG_ADAPTER_SHA256,
    },
    "provenance_graph_public_projection": {
        "body_key": "graph",
        "mapping_contract_path": (
            "docs/llm-editor/"
            "llm-editor-v0.8-l2-m1-provenance-graph-to-claim-ir-mapping-contract-"
            "v0.1-20260726.json"
        ),
        "mapping_contract_sha256": (
            "924d44bbdfe7795e3ada260526abfb71cfdc5d26683c6c075b81585c50f82031"
        ),
        "mapper_id": "m1m_provenance_graph_to_claim_ir_v0_1",
        "projection_path": (
            "docs/llm-editor/"
            "llm-editor-v0.8-l2-m1-provenance-graph-public-field-projection-"
            "v0.1-20260726.json"
        ),
        "projection_sha256": (
            "8a210a4eb2d9f48ac35c65f78fb29e2801c6a991b5b28798beaf5980f0c90ad5"
        ),
        "projection_artifact_id": (
            "llm-editor-v0.8-l2-m1-provenance-graph-public-field-projection-"
            "v0.1-20260726"
        ),
        "adapter_path": PROVENANCE_GRAPH_ADAPTER_PATH,
        "adapter_sha256": PROVENANCE_GRAPH_ADAPTER_SHA256,
    },
    "cti_report_public_projection": {
        "body_key": "report",
        "mapping_contract_path": (
            "docs/llm-editor/"
            "llm-editor-v0.8-l2-m1-cti-report-to-claim-ir-mapping-contract-"
            "v0.1-20260726.json"
        ),
        "mapping_contract_sha256": (
            "f13ef69e1fd96ffbf8ea673c840b0291b003aa4a13a752788ae44853ee1b683d"
        ),
        "mapper_id": "m1m_cti_report_to_claim_ir_v0_1",
        "projection_path": (
            "docs/llm-editor/"
            "llm-editor-v0.8-l2-m1-cti-report-public-field-projection-"
            "v0.1-20260726.json"
        ),
        "projection_sha256": (
            "7ec2fc8a04bdb2bd8119edee6b97151ffa9a2faff68cf997b38dd059919b7afb"
        ),
        "projection_artifact_id": (
            "llm-editor-v0.8-l2-m1-cti-report-public-field-projection-"
            "v0.1-20260726"
        ),
        "adapter_path": CTI_REPORT_ADAPTER_PATH,
        "adapter_sha256": CTI_REPORT_ADAPTER_SHA256,
    },
}

_EXPECTED_SCOPE = {
    "test_only": True,
    "in_memory_only": True,
    "surface_id": SURFACE_ID,
    "mapper_id": MAPPER_ID,
    "mapper_version": MAPPER_VERSION,
    "allowed_source_classes": list(_SOURCE_CLASSES),
    "effective_registry_activation": False,
    "production_execute": False,
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "in_memory_nonempty_structural_only",
    "schema_version": SCHEMA_VERSION,
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
    "zero_claim_compatibility_path_unchanged": True,
}
_EXPECTED_STILL_BLOCKED = {
    "effective_registry_activation": True,
    "production_execute": True,
    "activation_ledger_write": True,
    "claim_id_mint": True,
    "admission": True,
    "kernel_ingestion": True,
    "kernel_store_write": True,
    "e_case_write": True,
    "certificate_generation": True,
    "certified_stop": True,
    "checker_non_null": True,
    "evidence_sufficiency_non_null": True,
    "l2_gate_change": True,
    "part_b_elevation": True,
}


def canonical_json_sha256(value: Any) -> str:
    """Return the deterministic SHA-256 used for in-memory declarations."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise M1EvidenceToClaimIRMapperError(
            "canonical_json",
            "value is not canonical JSON",
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def verify_mapper_pins(repo_root: Path) -> None:
    """Verify Owner acceptance, effective identities, contracts, and adapters."""

    root = repo_root.resolve()
    pins = (
        (SCHEMA_GREEN_ACCEPTANCE_PATH, SCHEMA_GREEN_ACCEPTANCE_SHA256),
        (EXTERNAL_EVIDENCE_SCHEMA_PATH, EXTERNAL_EVIDENCE_SCHEMA_SHA256),
        (KERNEL_ADDITIVE_SCHEMA_PATH, KERNEL_ADDITIVE_SCHEMA_SHA256),
        (CONSUMER_CONTRACT_PATH, CONSUMER_CONTRACT_SHA256),
        (LEGACY_KERNEL_SCHEMA_PATH, LEGACY_KERNEL_SCHEMA_SHA256),
        (LEGACY_EXTERNAL_SCHEMA_PATH, LEGACY_EXTERNAL_SCHEMA_SHA256),
        (LEGACY_CONSUMER_CONTRACT_PATH, LEGACY_CONSUMER_CONTRACT_SHA256),
        (MAPPING_FRAMEWORK_PATH, MAPPING_FRAMEWORK_SHA256),
        (SYSTEM_LOG_ADAPTER_PATH, SYSTEM_LOG_ADAPTER_SHA256),
        (PROVENANCE_GRAPH_ADAPTER_PATH, PROVENANCE_GRAPH_ADAPTER_SHA256),
        (CTI_REPORT_ADAPTER_PATH, CTI_REPORT_ADAPTER_SHA256),
        *tuple(
            (
                spec["mapping_contract_path"],
                spec["mapping_contract_sha256"],
            )
            for spec in _SPECS.values()
        ),
    )
    for relative_path, expected_sha in pins:
        path = root / relative_path
        if not path.is_file():
            raise M1EvidenceToClaimIRMapperError(
                "missing_pin",
                f"required pin is missing: {relative_path}",
            )
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected_sha:
            raise M1EvidenceToClaimIRMapperError(
                "pin_mismatch",
                f"required pin mismatch: {relative_path}",
            )

    acceptance = _load_json(root / SCHEMA_GREEN_ACCEPTANCE_PATH)
    _require_constant(acceptance.get("decision"), "accept", "acceptance.decision")
    _require_constant(
        acceptance.get("status"),
        "green_accepted_exact_candidate_bytes_now_effective_for_structural_dispatch_only",
        "acceptance.status",
    )
    identities = acceptance.get("exact_effective_identities_accepted")
    if not isinstance(identities, Mapping):
        raise M1EvidenceToClaimIRMapperError(
            "acceptance_shape",
            "effective identity acceptance table is missing",
        )
    for key, expected_path, expected_sha in (
        (
            "external_evidence_schema",
            EXTERNAL_EVIDENCE_SCHEMA_PATH,
            EXTERNAL_EVIDENCE_SCHEMA_SHA256,
        ),
        (
            "kernel_additive_schema",
            KERNEL_ADDITIVE_SCHEMA_PATH,
            KERNEL_ADDITIVE_SCHEMA_SHA256,
        ),
        (
            "consumer_contract",
            CONSUMER_CONTRACT_PATH,
            CONSUMER_CONTRACT_SHA256,
        ),
    ):
        record = identities.get(key)
        if (
            not isinstance(record, Mapping)
            or record.get("path") != expected_path
            or record.get("content_sha256") != expected_sha
            or record.get("effective") is not True
        ):
            raise M1EvidenceToClaimIRMapperError(
                "acceptance_identity",
                f"Owner acceptance does not pin effective identity {key}",
            )

    consumer = _load_json(root / CONSUMER_CONTRACT_PATH)
    dispatch = consumer.get("exact_schema_dispatch")
    if not isinstance(dispatch, Mapping):
        raise M1EvidenceToClaimIRMapperError(
            "consumer_dispatch",
            "effective consumer exact dispatch table is missing",
        )
    routes = dispatch.get("routes")
    evidence_routes = [
        route
        for route in routes
        if isinstance(route, Mapping)
        and route.get("schema_version") == SCHEMA_VERSION
    ] if isinstance(routes, list) else []
    if (
        dispatch.get("wildcard_or_fallback") is not False
        or dispatch.get("implicit_default") is not False
        or len(evidence_routes) != 1
        or evidence_routes[0].get("decision")
        != "CONSUMABLE_STRUCTURAL_ONLY_NOT_MINTED_NOT_ADMITTED_NO_INGESTION_AUTHORITY"
    ):
        raise M1EvidenceToClaimIRMapperError(
            "consumer_dispatch",
            "effective evidence route is not exact structural-only dispatch",
        )

    for source_class, spec in _SPECS.items():
        contract = _load_json(root / spec["mapping_contract_path"])
        identity = contract.get("identity")
        mappings = contract.get("field_to_claim_mapping")
        if (
            contract.get("status") != "design_only_not_executable"
            or not isinstance(identity, Mapping)
            or identity.get("source_class") != source_class
            or identity.get("surface_id") != SURFACE_ID
            or identity.get("future_mapper_id") != spec["mapper_id"]
            or not isinstance(mappings, list)
            or not mappings
        ):
            raise M1EvidenceToClaimIRMapperError(
                "mapping_contract",
                f"mapping contract is malformed for {source_class}",
            )
        ordinals = [entry.get("ordinal") for entry in mappings]
        if ordinals != list(range(1, len(mappings) + 1)):
            raise M1EvidenceToClaimIRMapperError(
                "mapping_contract",
                f"mapping ordinals are not exact for {source_class}",
            )
        if any(
            not isinstance(entry, Mapping)
            or not str(entry.get("claim_kind", "")).startswith("evidence.")
            or not str(entry.get("evidence_field", "")).startswith("evidence.")
            or "source_field" in entry
            or "afs" in entry
            for entry in mappings
        ):
            raise M1EvidenceToClaimIRMapperError(
                "mapping_contract",
                f"mapping namespace escapes evidence.* for {source_class}",
            )

    try:
        Draft202012Validator.check_schema(
            _load_json(root / EXTERNAL_EVIDENCE_SCHEMA_PATH)
        )
        Draft202012Validator.check_schema(
            _load_json(root / KERNEL_ADDITIVE_SCHEMA_PATH)
        )
    except (SchemaError, TypeError, ValueError) as exc:
        raise M1EvidenceToClaimIRMapperError(
            "schema_invalid",
            "an effective evidence schema is invalid",
        ) from exc


def map_validated_projection_to_claim_ir(
    projection: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Map one validated in-memory public projection to nonempty Claim-IR."""

    root = repo_root.resolve()
    verify_mapper_pins(root)
    if isinstance(projection, Sequence) and not isinstance(
        projection, (str, bytes, bytearray)
    ):
        raise M1EvidenceToClaimIRMapperError(
            "cross_modality_merge",
            "a mapper request must contain exactly one projection",
        )
    if not isinstance(projection, Mapping):
        raise M1EvidenceToClaimIRMapperError(
            "projection_type",
            "projection must be an object",
        )
    _scan_forbidden_input(projection)
    source_class = _source_class(projection)
    spec = _SPECS.get(source_class)
    if spec is None:
        raise M1EvidenceToClaimIRMapperError(
            "unknown_source_class",
            "projection source class is not mapped",
        )
    modality_bodies = set(projection) & {"event", "graph", "report"}
    if modality_bodies != {spec["body_key"]}:
        raise M1EvidenceToClaimIRMapperError(
            "cross_modality_merge",
            "projection body does not match exactly one source class",
        )
    _validate_test_authority(authority, projection, root, source_class, spec)
    _validate_projection(projection, source_class, spec)
    if projection["source_metadata"]["epistemic_modality"] == "unknown":
        raise M1EvidenceToClaimIRMapperError(
            "abstain_unknown_modality",
            "unknown modality abstains before any claim is emitted",
        )

    contract = _load_json(root / spec["mapping_contract_path"])
    claims = _emit_claims(
        projection,
        source_class,
        contract["field_to_claim_mapping"],
    )
    if not claims:
        raise M1EvidenceToClaimIRMapperError(
            "empty_mapping",
            "valid GREEN-2 mapping must be nonempty",
        )
    projection_digest = canonical_json_sha256(projection)
    projection_ref = {
        "path": spec["projection_path"],
        "sha256": spec["projection_sha256"],
        "surface_id": SURFACE_ID,
        "source_class": source_class,
    }
    package = {
        "schema_version": SCHEMA_VERSION,
        "package_id": f"pkg_evidence_{projection_digest[:32]}",
        "surface_id": SURFACE_ID,
        "kernel_state": "pending_kernel_schema",
        "claim_id_state": "not_minted",
        "admission_state": "not_admitted",
        "projection_ref": projection_ref,
        "claims": claims,
        "manifest": {
            "claim_count": len(claims),
            "field_path_set": [],
            "evidence_field_path_set": sorted(
                {claim["evidence_field"] for claim in claims}
            ),
            "projection_sha256": spec["projection_sha256"],
            "content_hash": canonical_json_sha256(
                {
                    "schema_version": SCHEMA_VERSION,
                    "surface_id": SURFACE_ID,
                    "source_class": source_class,
                    "projection_sha256": spec["projection_sha256"],
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
    source_class: str,
    spec: Mapping[str, Any],
) -> None:
    if authority is None:
        raise M1EvidenceToClaimIRMapperError(
            "missing_authority",
            "explicit test-only GREEN-2 authority is required",
        )
    if not isinstance(authority, Mapping):
        raise M1EvidenceToClaimIRMapperError(
            "authority_type",
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
        raise M1EvidenceToClaimIRMapperError(
            "authority_shape",
            "authority fields are not exact",
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
        "schema_green_acceptance_sha256": SCHEMA_GREEN_ACCEPTANCE_SHA256,
        "external_evidence_schema_sha256": EXTERNAL_EVIDENCE_SCHEMA_SHA256,
        "kernel_additive_schema_sha256": KERNEL_ADDITIVE_SCHEMA_SHA256,
        "consumer_contract_sha256": CONSUMER_CONTRACT_SHA256,
        "mapping_framework_sha256": MAPPING_FRAMEWORK_SHA256,
        "system_log_mapping_contract_sha256": _SPECS[
            "system_log_public_projection"
        ]["mapping_contract_sha256"],
        "provenance_graph_mapping_contract_sha256": _SPECS[
            "provenance_graph_public_projection"
        ]["mapping_contract_sha256"],
        "cti_report_mapping_contract_sha256": _SPECS[
            "cti_report_public_projection"
        ]["mapping_contract_sha256"],
        "system_log_adapter_sha256": SYSTEM_LOG_ADAPTER_SHA256,
        "provenance_graph_adapter_sha256": PROVENANCE_GRAPH_ADAPTER_SHA256,
        "cti_report_adapter_sha256": CTI_REPORT_ADAPTER_SHA256,
        "mapper_implementation_sha256": hashlib.sha256(
            (root / MAPPER_IMPLEMENTATION_PATH).read_bytes()
        ).hexdigest(),
    }
    _require_exact_mapping(
        authority.get("pinned_hashes"),
        expected_hashes,
        "authority.pinned_hashes",
    )
    expected_input = {
        "source_class": source_class,
        "projection_sha256": spec["projection_sha256"],
        "projection_content_sha256": canonical_json_sha256(projection),
    }
    _require_exact_mapping(
        authority.get("pinned_input"),
        expected_input,
        "authority.pinned_input",
    )


def _validate_projection(
    projection: Mapping[str, Any],
    source_class: str,
    spec: Mapping[str, Any],
) -> None:
    descriptor = projection.get("descriptor")
    _require_exact_keys(
        descriptor,
        {
            "surface_id",
            "source_class",
            "opaque_record_reference",
            "projection_pin_declaration",
        },
        set(),
        "projection.descriptor",
    )
    _require_constant(
        descriptor["surface_id"],
        SURFACE_ID,
        "projection.descriptor.surface_id",
    )
    _require_constant(
        descriptor["source_class"],
        source_class,
        "projection.descriptor.source_class",
    )
    _require_safe_opaque(
        descriptor["opaque_record_reference"],
        "projection.descriptor.opaque_record_reference",
    )
    _require_exact_mapping(
        descriptor["projection_pin_declaration"],
        {
            "artifact_id": spec["projection_artifact_id"],
            "version": "0.1",
            "sha256": spec["projection_sha256"],
        },
        "projection.descriptor.projection_pin_declaration",
    )
    if source_class == "system_log_public_projection":
        _validate_system_log_projection(projection)
    elif source_class == "provenance_graph_public_projection":
        _validate_provenance_projection(projection)
    else:
        _validate_cti_projection(projection)


def _validate_system_log_projection(projection: Mapping[str, Any]) -> None:
    _require_exact_keys(
        projection,
        {"descriptor", "event", "source_metadata"},
        {"principal"},
        "projection",
    )
    event = projection["event"]
    _require_exact_keys(
        event,
        {"event_id", "event_time", "provider"},
        {"severity", "result_code"},
        "projection.event",
    )
    _require_safe_opaque(event["event_id"], "projection.event.event_id")
    _require_public_text(event["event_time"], "projection.event.event_time")
    _require_safe_opaque(event["provider"], "projection.event.provider")
    for field in ("severity", "result_code"):
        if field in event:
            _require_safe_opaque(event[field], f"projection.event.{field}")
    principal = projection.get("principal")
    if principal is not None:
        _require_exact_keys(
            principal,
            set(),
            {
                "public_host_ref",
                "public_process_ref",
                "public_user_ref",
            },
            "projection.principal",
        )
        for field, value in principal.items():
            _require_safe_opaque(value, f"projection.principal.{field}")

    metadata = projection["source_metadata"]
    _require_exact_keys(
        metadata,
        {
            "transport_source_modality",
            "source_family",
            "epistemic_modality",
            "modality_basis_code",
            "trusted_ingestion_metadata_sha256",
        },
        set(),
        "projection.source_metadata",
    )
    _require_safe_opaque(
        metadata["transport_source_modality"],
        "projection.source_metadata.transport_source_modality",
    )
    _require_constant(
        metadata["source_family"],
        "execution",
        "projection.source_metadata.source_family",
    )
    expected = {
        "DIRECT_SOURCE_ATTESTED_EVENT": "observed",
        "TRANSFORMED_AGGREGATED_OR_ALERT": "derived",
        "UNRESOLVED_BASIS": "unknown",
    }
    if expected.get(metadata["modality_basis_code"]) != metadata[
        "epistemic_modality"
    ]:
        raise M1EvidenceToClaimIRMapperError(
            "modality_mapping",
            "system-log modality and trusted basis do not match",
        )
    _require_sha(
        metadata["trusted_ingestion_metadata_sha256"],
        "projection.source_metadata.trusted_ingestion_metadata_sha256",
    )


def _validate_provenance_projection(projection: Mapping[str, Any]) -> None:
    _require_exact_keys(
        projection,
        {"descriptor", "graph", "source_metadata"},
        set(),
        "projection",
    )
    graph = projection["graph"]
    _require_exact_keys(
        graph,
        {"graph_id", "time_window", "summary"},
        {"nodes", "edges"},
        "projection.graph",
    )
    _require_safe_opaque(graph["graph_id"], "projection.graph.graph_id")
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise M1EvidenceToClaimIRMapperError(
            "graph_arrays",
            "graph nodes and edges must be arrays",
        )
    node_ids: list[str] = []
    for index, node in enumerate(nodes):
        _require_exact_keys(
            node,
            {"node_id", "node_type"},
            set(),
            f"projection.graph.nodes[{index}]",
        )
        _require_safe_opaque(
            node["node_id"],
            f"projection.graph.nodes[{index}].node_id",
        )
        _require_safe_opaque(
            node["node_type"],
            f"projection.graph.nodes[{index}].node_type",
        )
        node_ids.append(node["node_id"])
    if node_ids != sorted(node_ids) or len(node_ids) != len(set(node_ids)):
        raise M1EvidenceToClaimIRMapperError(
            "graph_node_order",
            "node IDs must be unique and canonically sorted",
        )

    edge_ids: list[str] = []
    relationship_types: list[str] = []
    for index, edge in enumerate(edges):
        _require_exact_keys(
            edge,
            {
                "edge_id",
                "from_node_id",
                "to_node_id",
                "relationship_type",
            },
            set(),
            f"projection.graph.edges[{index}]",
        )
        for field in (
            "edge_id",
            "from_node_id",
            "to_node_id",
            "relationship_type",
        ):
            _require_safe_opaque(
                edge[field],
                f"projection.graph.edges[{index}].{field}",
            )
        if (
            edge["from_node_id"] not in node_ids
            or edge["to_node_id"] not in node_ids
        ):
            raise M1EvidenceToClaimIRMapperError(
                "dangling_edge",
                "edge references an undeclared node",
            )
        edge_ids.append(edge["edge_id"])
        relationship_types.append(edge["relationship_type"])
    if edge_ids != sorted(edge_ids) or len(edge_ids) != len(set(edge_ids)):
        raise M1EvidenceToClaimIRMapperError(
            "graph_edge_order",
            "edge IDs must be unique and canonically sorted",
        )

    window = graph["time_window"]
    _require_exact_keys(
        window,
        {"start", "end", "precision"},
        set(),
        "projection.graph.time_window",
    )
    _require_public_text(window["start"], "projection.graph.time_window.start")
    _require_public_text(window["end"], "projection.graph.time_window.end")
    _require_safe_opaque(
        window["precision"],
        "projection.graph.time_window.precision",
    )

    summary = graph["summary"]
    _require_exact_keys(
        summary,
        {"node_count", "edge_count"},
        {"relationship_counts"},
        "projection.graph.summary",
    )
    _require_nonnegative_int(
        summary["node_count"],
        "projection.graph.summary.node_count",
    )
    _require_nonnegative_int(
        summary["edge_count"],
        "projection.graph.summary.edge_count",
    )
    _require_constant(
        summary["node_count"],
        len(nodes),
        "projection.graph.summary.node_count",
    )
    _require_constant(
        summary["edge_count"],
        len(edges),
        "projection.graph.summary.edge_count",
    )
    if "relationship_counts" in summary:
        counts = summary["relationship_counts"]
        if not isinstance(counts, list):
            raise M1EvidenceToClaimIRMapperError(
                "relationship_counts",
                "relationship counts must be an array",
            )
        declared: dict[str, int] = {}
        for index, item in enumerate(counts):
            _require_exact_keys(
                item,
                {"relationship_type", "count"},
                set(),
                f"projection.graph.summary.relationship_counts[{index}]",
            )
            _require_safe_opaque(
                item["relationship_type"],
                f"projection.graph.summary.relationship_counts[{index}].relationship_type",
            )
            _require_nonnegative_int(
                item["count"],
                f"projection.graph.summary.relationship_counts[{index}].count",
            )
            if item["relationship_type"] in declared:
                raise M1EvidenceToClaimIRMapperError(
                    "relationship_counts",
                    "relationship count identities must be unique",
                )
            declared[item["relationship_type"]] = item["count"]
        if list(declared) != sorted(declared):
            raise M1EvidenceToClaimIRMapperError(
                "relationship_count_order",
                "relationship counts must be canonically sorted",
            )
        if declared != dict(Counter(relationship_types)):
            raise M1EvidenceToClaimIRMapperError(
                "relationship_count_mismatch",
                "relationship counts do not match declared edges",
            )

    metadata = projection["source_metadata"]
    _require_exact_keys(
        metadata,
        {
            "source_family",
            "epistemic_modality",
            "materialization_class",
            "modality_basis_code",
            "trusted_ingestion_metadata_sha256",
        },
        set(),
        "projection.source_metadata",
    )
    _require_constant(
        metadata["source_family"],
        "system_provenance",
        "projection.source_metadata.source_family",
    )
    expected = {
        (
            "DIRECT_SOURCE_ATTESTED_GRAPH",
            "ALL_NODES_AND_EDGES_DIRECTLY_ATTESTED",
        ): "observed",
        (
            "TRANSFORMED_OR_INFERRED_GRAPH",
            "ONE_OR_MORE_ELEMENTS_TRANSFORMED_OR_INFERRED",
        ): "derived",
        (
            "MIXED_OR_UNRESOLVED_GRAPH",
            "MIXED_UNSPLIT_OR_UNRESOLVED_BASIS",
        ): "unknown",
    }
    key = (
        metadata["materialization_class"],
        metadata["modality_basis_code"],
    )
    if expected.get(key) != metadata["epistemic_modality"]:
        raise M1EvidenceToClaimIRMapperError(
            "modality_mapping",
            "provenance modality and trusted basis do not match",
        )
    _require_sha(
        metadata["trusted_ingestion_metadata_sha256"],
        "projection.source_metadata.trusted_ingestion_metadata_sha256",
    )


def _validate_cti_projection(projection: Mapping[str, Any]) -> None:
    _require_exact_keys(
        projection,
        {"descriptor", "report", "source_metadata"},
        set(),
        "projection",
    )
    report = projection["report"]
    _require_exact_keys(
        report,
        {"report_id", "publication_window", "reported_marker"},
        {
            "publisher_ref",
            "public_objects",
            "public_techniques",
            "public_relations",
        },
        "projection.report",
    )
    _require_safe_opaque(report["report_id"], "projection.report.report_id")
    if "publisher_ref" in report:
        _require_safe_opaque(
            report["publisher_ref"],
            "projection.report.publisher_ref",
        )
    _require_constant(
        report["reported_marker"],
        True,
        "projection.report.reported_marker",
    )
    window = report["publication_window"]
    _require_exact_keys(
        window,
        {"start", "end"},
        set(),
        "projection.report.publication_window",
    )
    _require_public_text(
        window["start"],
        "projection.report.publication_window.start",
    )
    _require_public_text(
        window["end"],
        "projection.report.publication_window.end",
    )

    objects = report.get("public_objects", [])
    techniques = report.get("public_techniques", [])
    relations = report.get("public_relations", [])
    if not all(isinstance(items, list) for items in (objects, techniques, relations)):
        raise M1EvidenceToClaimIRMapperError(
            "cti_arrays",
            "CTI public objects, techniques, and relations must be arrays",
        )
    object_keys: list[tuple[str, str]] = []
    object_refs: set[str] = set()
    for index, item in enumerate(objects):
        _require_exact_keys(
            item,
            {"object_ref", "object_type"},
            set(),
            f"projection.report.public_objects[{index}]",
        )
        _require_safe_opaque(
            item["object_ref"],
            f"projection.report.public_objects[{index}].object_ref",
        )
        _require_safe_opaque(
            item["object_type"],
            f"projection.report.public_objects[{index}].object_type",
        )
        object_keys.append((item["object_ref"], item["object_type"]))
        object_refs.add(item["object_ref"])
    if object_keys != sorted(object_keys) or len(object_refs) != len(objects):
        raise M1EvidenceToClaimIRMapperError(
            "cti_object_order",
            "CTI objects must be unique and canonically sorted",
        )
    technique_refs: list[str] = []
    for index, item in enumerate(techniques):
        _require_exact_keys(
            item,
            {"technique_ref"},
            set(),
            f"projection.report.public_techniques[{index}]",
        )
        _require_safe_opaque(
            item["technique_ref"],
            f"projection.report.public_techniques[{index}].technique_ref",
        )
        technique_refs.append(item["technique_ref"])
    if technique_refs != sorted(technique_refs) or len(technique_refs) != len(
        set(technique_refs)
    ):
        raise M1EvidenceToClaimIRMapperError(
            "cti_technique_order",
            "CTI techniques must be unique and canonically sorted",
        )
    allowed_refs = object_refs | set(technique_refs)
    relation_keys: list[tuple[str, str, str]] = []
    for index, item in enumerate(relations):
        _require_exact_keys(
            item,
            {"subject_ref", "relation_type", "object_ref"},
            set(),
            f"projection.report.public_relations[{index}]",
        )
        for field in ("subject_ref", "relation_type", "object_ref"):
            _require_safe_opaque(
                item[field],
                f"projection.report.public_relations[{index}].{field}",
            )
        if item["subject_ref"] not in allowed_refs or item["object_ref"] not in allowed_refs:
            raise M1EvidenceToClaimIRMapperError(
                "dangling_cti_relation",
                "CTI relation references an undeclared public object",
            )
        relation_keys.append(
            (item["subject_ref"], item["relation_type"], item["object_ref"])
        )
    if relation_keys != sorted(relation_keys) or len(relation_keys) != len(
        set(relation_keys)
    ):
        raise M1EvidenceToClaimIRMapperError(
            "cti_relation_order",
            "CTI relations must be unique and canonically sorted",
        )

    metadata = projection["source_metadata"]
    _require_exact_keys(
        metadata,
        {
            "source_family",
            "epistemic_modality",
            "modality_basis_code",
            "trusted_ingestion_metadata_sha256",
        },
        set(),
        "projection.source_metadata",
    )
    _require_constant(
        metadata["source_family"],
        "external_intel",
        "projection.source_metadata.source_family",
    )
    if metadata["epistemic_modality"] in {"observed", "derived"}:
        raise M1EvidenceToClaimIRMapperError(
            "modality_laundering",
            "CTI reported material cannot be observed or derived",
        )
    expected = {
        "PUBLIC_CTI_REPORT_DECLARATION": "reported",
        "UNRESOLVED_REPORTING_BASIS": "unknown",
    }
    if expected.get(metadata["modality_basis_code"]) != metadata[
        "epistemic_modality"
    ]:
        raise M1EvidenceToClaimIRMapperError(
            "modality_mapping",
            "CTI modality and trusted basis do not match",
        )
    _require_sha(
        metadata["trusted_ingestion_metadata_sha256"],
        "projection.source_metadata.trusted_ingestion_metadata_sha256",
    )


def _emit_claims(
    projection: Mapping[str, Any],
    source_class: str,
    mappings: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    metadata = projection["source_metadata"]
    source_record_ref = projection["descriptor"]["opaque_record_reference"]
    claims: list[dict[str, Any]] = []
    for entry in mappings:
        field_path = entry["field_path"]
        presence = entry["presence"]
        if "[]" in field_path:
            values = _repeated_values(projection, field_path, source_class)
            for value, occurrence_key in values:
                claims.append(
                    _claim_from_entry(
                        entry,
                        value,
                        occurrence_key,
                        source_class,
                        source_record_ref,
                        metadata,
                    )
                )
            continue

        value = _get_path(projection, field_path)
        if value is _MISSING:
            if presence == "optional":
                continue
            raise M1EvidenceToClaimIRMapperError(
                "missing_required_field",
                f"required mapping field is missing: {field_path}",
            )
        if presence == "required_non_null_for_nonempty_mapping" and value is None:
            raise M1EvidenceToClaimIRMapperError(
                "missing_required_field",
                f"nonempty mapping field is null: {field_path}",
            )
        if presence == "required_const_true" and value is not True:
            raise M1EvidenceToClaimIRMapperError(
                "required_constant",
                f"mapping field must be true: {field_path}",
            )
        occurrence_key = _scalar_occurrence_key(projection, source_class)
        claims.append(
            _claim_from_entry(
                entry,
                value,
                occurrence_key,
                source_class,
                source_record_ref,
                metadata,
            )
        )
    return claims


def _claim_from_entry(
    entry: Mapping[str, Any],
    value: Any,
    occurrence_key: str,
    source_class: str,
    source_record_ref: str,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_claim_value(entry["value_type"], value, entry["field_path"])
    if not isinstance(occurrence_key, str) or not _OCCURRENCE_PATTERN.fullmatch(
        occurrence_key
    ):
        raise M1EvidenceToClaimIRMapperError(
            "occurrence_key",
            f"invalid occurrence key for {entry['field_path']}",
        )
    return {
        "record_class": "public_evidence_declaration",
        "claim_id": None,
        "claim_id_state": "not_minted",
        "claim_kind": entry["claim_kind"],
        "evidence_field": entry["evidence_field"],
        "occurrence_key": occurrence_key,
        "value_type": entry["value_type"],
        "value": _json_copy(value),
        "source_class": source_class,
        "source_record_ref": source_record_ref,
        "epistemic_modality": metadata["epistemic_modality"],
        "modality_basis_code": metadata["modality_basis_code"],
        "trusted_ingestion_metadata_sha256": metadata[
            "trusted_ingestion_metadata_sha256"
        ],
        "admission_state": "not_admitted",
    }


def _repeated_values(
    projection: Mapping[str, Any],
    field_path: str,
    source_class: str,
) -> list[tuple[Any, str]]:
    collection_path, item_path = field_path.split("[]", 1)
    item_path = item_path.lstrip(".")
    collection = _get_path(projection, collection_path)
    if collection is _MISSING:
        return []
    if not isinstance(collection, list):
        raise M1EvidenceToClaimIRMapperError(
            "repeated_field",
            f"repeated mapping collection is not an array: {collection_path}",
        )
    result = []
    for item in collection:
        value = _get_path(item, item_path)
        if value is _MISSING:
            raise M1EvidenceToClaimIRMapperError(
                "missing_repeated_field",
                f"repeated mapping field is missing: {field_path}",
            )
        result.append(
            (
                value,
                _repeated_occurrence_key(source_class, collection_path, item),
            )
        )
    return result


def _repeated_occurrence_key(
    source_class: str,
    collection_path: str,
    item: Mapping[str, Any],
) -> str:
    if source_class == "provenance_graph_public_projection":
        if collection_path == "graph.nodes":
            return item["node_id"]
        if collection_path == "graph.edges":
            return item["edge_id"]
        if collection_path == "graph.summary.relationship_counts":
            return item["relationship_type"]
    if source_class == "cti_report_public_projection":
        if collection_path == "report.public_objects":
            return item["object_ref"]
        if collection_path == "report.public_techniques":
            return item["technique_ref"]
        if collection_path == "report.public_relations":
            return "|".join(
                (
                    item["subject_ref"],
                    item["relation_type"],
                    item["object_ref"],
                )
            )
    raise M1EvidenceToClaimIRMapperError(
        "occurrence_rule",
        f"no accepted occurrence rule for {collection_path}",
    )


def _scalar_occurrence_key(
    projection: Mapping[str, Any],
    source_class: str,
) -> str:
    if source_class == "system_log_public_projection":
        return projection["event"]["event_id"]
    if source_class == "provenance_graph_public_projection":
        return projection["graph"]["graph_id"]
    return projection["report"]["report_id"]


def _validate_claim_value(value_type: str, value: Any, field_path: str) -> None:
    if value_type == "opaque_reference":
        _require_safe_opaque(value, field_path)
    elif value_type == "bounded_enum":
        _require_safe_opaque(value, field_path)
        if len(value) > 128:
            raise M1EvidenceToClaimIRMapperError(
                "value_type",
                f"bounded enum is too long: {field_path}",
            )
    elif value_type == "bounded_public_text":
        _require_public_text(value, field_path)
    elif value_type == "bounded_number":
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not isinstance(value, int)
        ):
            raise M1EvidenceToClaimIRMapperError(
                "value_type",
                f"bounded number is invalid: {field_path}",
            )
    elif value_type == "bounded_boolean":
        if not isinstance(value, bool):
            raise M1EvidenceToClaimIRMapperError(
                "value_type",
                f"bounded boolean is invalid: {field_path}",
            )
    else:
        raise M1EvidenceToClaimIRMapperError(
            "value_type",
            f"unknown mapping value type: {value_type}",
        )


def _validate_output(package: Mapping[str, Any], root: Path) -> None:
    external = _load_json(root / EXTERNAL_EVIDENCE_SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(external).iter_errors(package),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise M1EvidenceToClaimIRMapperError(
            "output_schema",
            f"external evidence output fails at {location}: {first.message}",
        )

    kernel_additive = _load_json(root / KERNEL_ADDITIVE_SCHEMA_PATH)
    legacy_kernel = _load_json(root / LEGACY_KERNEL_SCHEMA_PATH)
    registry = Registry()
    for schema in (legacy_kernel, external):
        registry = registry.with_resource(
            schema["$id"],
            Resource.from_contents(schema),
        )
    validator = Draft202012Validator(kernel_additive, registry=registry)
    for index, claim in enumerate(package["claims"]):
        claim_errors = sorted(
            validator.iter_errors(claim),
            key=lambda error: list(error.absolute_path),
        )
        if claim_errors:
            raise M1EvidenceToClaimIRMapperError(
                "kernel_output_schema",
                f"claim {index} fails additive Kernel oneOf",
            )

    if package["manifest"]["claim_count"] != len(package["claims"]):
        raise M1EvidenceToClaimIRMapperError(
            "consumer_invariant",
            "manifest claim count does not equal claims length",
        )
    expected_fields = sorted(
        {claim["evidence_field"] for claim in package["claims"]}
    )
    if package["manifest"]["evidence_field_path_set"] != expected_fields:
        raise M1EvidenceToClaimIRMapperError(
            "consumer_invariant",
            "manifest evidence field set is not exact",
        )
    if any(
        claim["source_class"] != package["projection_ref"]["source_class"]
        for claim in package["claims"]
    ):
        raise M1EvidenceToClaimIRMapperError(
            "consumer_invariant",
            "claim source class differs from projection source class",
        )


def _source_class(projection: Mapping[str, Any]) -> str:
    descriptor = projection.get("descriptor")
    if not isinstance(descriptor, Mapping):
        raise M1EvidenceToClaimIRMapperError(
            "projection_descriptor",
            "projection descriptor is missing",
        )
    source_class = descriptor.get("source_class")
    if not isinstance(source_class, str):
        raise M1EvidenceToClaimIRMapperError(
            "unknown_source_class",
            "projection source class is missing",
        )
    return source_class


def _scan_forbidden_input(value: Any) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise M1EvidenceToClaimIRMapperError(
            "raw_source",
            "raw bytes are forbidden",
        )
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _FORBIDDEN_INPUT_KEYS:
                raise M1EvidenceToClaimIRMapperError(
                    "forbidden_input_field",
                    f"forbidden input field: {key}",
                )
            if (
                normalized == "claim_kind"
                and isinstance(nested, str)
                and nested in _PLANNER_CLAIM_KINDS
            ):
                raise M1EvidenceToClaimIRMapperError(
                    "forbidden_planner_namespace",
                    "planner claim kinds are forbidden in evidence mapping",
                )
            _scan_forbidden_input(nested)
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for nested in value:
            _scan_forbidden_input(nested)


def _get_path(value: Any, dotted_path: str) -> Any:
    current = value
    if not dotted_path:
        return current
    for part in dotted_path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _require_exact_keys(
    value: Any,
    required: set[str],
    optional: set[str],
    location: str,
) -> None:
    if not isinstance(value, Mapping):
        raise M1EvidenceToClaimIRMapperError(
            "projection_shape",
            f"{location} must be an object",
        )
    keys = set(value)
    if not required.issubset(keys) or not keys.issubset(required | optional):
        raise M1EvidenceToClaimIRMapperError(
            "projection_shape",
            f"{location} fields are not exact",
        )


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    location: str,
) -> None:
    if not isinstance(value, Mapping) or dict(value) != dict(expected):
        raise M1EvidenceToClaimIRMapperError(
            "constant",
            f"{location} does not match the accepted value",
        )


def _require_constant(value: Any, expected: Any, location: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise M1EvidenceToClaimIRMapperError(
            "constant",
            f"{location} does not match the accepted value",
        )


def _require_safe_opaque(value: Any, location: str) -> None:
    if not isinstance(value, str) or not _OPAQUE_PATTERN.fullmatch(value):
        raise M1EvidenceToClaimIRMapperError(
            "unsafe_opaque",
            f"{location} is not a safe opaque value",
        )


def _require_public_text(value: Any, location: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise M1EvidenceToClaimIRMapperError(
            "public_text",
            f"{location} is not bounded public text",
        )


def _require_sha(value: Any, location: str) -> None:
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise M1EvidenceToClaimIRMapperError(
            "sha256",
            f"{location} is not a SHA-256 digest",
        )


def _require_nonnegative_int(value: Any, location: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise M1EvidenceToClaimIRMapperError(
            "number",
            f"{location} is not a nonnegative integer",
        )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise M1EvidenceToClaimIRMapperError(
            "json_pin",
            f"cannot read pinned JSON: {path}",
        ) from exc
    if not isinstance(value, dict):
        raise M1EvidenceToClaimIRMapperError(
            "json_pin",
            f"pinned JSON is not an object: {path}",
        )
    return value


def _json_copy(value: Any) -> Any:
    try:
        return json.loads(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise M1EvidenceToClaimIRMapperError(
            "canonical_json",
            "value is not canonical JSON",
        ) from exc
