"""Fail-closed, in-memory Kernel Claim IR ingestion transition.

This module validates one exact admitted ``project05_depth2_public`` package
against the Kernel/M3*-owned effective consumer contract.  It never writes a
Kernel store, E_case, a certificate, or an activation artifact.  A successful
call returns an in-memory state transition, a sanitized receipt, and the
single-use ledger state that an external authorized wrapper would have to
persist.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SURFACE_ID = "project05_depth2_public"
SOURCE_CLASS = "planner_experiment_inputs"
ADAPTER_ID = "m1a_planner_inputs_v0_1"
PACKAGE_ID = "pkg_73d77b55ef6a517a0dc528f7f3a89bd9"

EFFECTIVE_CONSUMER_CONTRACT_PATH = (
    "docs/kernel/"
    "kernel-v0.8-shared-claim-ir-consumer-contract-effective-v0.1-20260725.json"
)
EFFECTIVE_CONSUMER_CONTRACT_SHA256 = (
    "a2a176fdeb2b93205a7f5e11c7c096236e2dc582d1c31f8f4a1534866c008d63"
)
EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID = (
    "kernel-v0.8-shared-claim-ir-consumer-contract-effective-v0.1-20260725"
)
EFFECTIVE_CONSUMER_CONTRACT_STATUS = (
    "effective_consumer_contract_semantics_only_ingestion_not_authorized"
)

ADMITTED_FIXTURE_PATH = (
    "docs/llm-editor/fixtures/claim-ir-admitted/"
    "project05-depth2-public-minted-admitted-v0.1/package.json"
)
ADMITTED_FIXTURE_SHA256 = (
    "f553b0d5f5f29b4e7045cc745cd380414dcdeca2569d9e5a65bbf92208d8eb32"
)
SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
SCHEMA_ID = "https://project05.invalid/schemas/claim-ir-kernel.schema.json"
SCHEMA_VERSION = "claim-ir-external-v0.1"

ASSISTED_DRAFT_SHA256 = (
    "e2d30697909c2f41e2f6c86178fe198369a35215e937c8129269ea1d68aedfdc"
)
REVISION_PACKET_SHA256 = (
    "5cb0546139bf6b1abc21b5fa22494c80505082c8a43d16241a834b0451b981b3"
)
FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS = frozenset(
    {ASSISTED_DRAFT_SHA256, REVISION_PACKET_SHA256}
)

_EXPECTED_AUTHORITY_FIELDS = frozenset(
    {
        "artifact_id",
        "status",
        "target",
        "pinned_hashes",
        "selected_input",
        "execute_ledger",
        "output_policy",
        "still_blocked",
    }
)
_EXPECTED_PACKAGE_FIELDS = frozenset(
    {
        "schema_version",
        "package_id",
        "surface_id",
        "kernel_state",
        "claim_id_state",
        "admission_state",
        "projection_ref",
        "claims",
        "manifest",
    }
)
_EXPECTED_CLAIM_FIELDS = frozenset(
    {
        "claim_id",
        "claim_id_state",
        "claim_kind",
        "source_field",
        "value_type",
        "value",
        "admission_state",
    }
)
_EXPECTED_MANIFEST_FIELDS = frozenset(
    {
        "claim_count",
        "field_path_set",
        "projection_sha256",
        "content_hash",
    }
)
_EXPECTED_LEDGER_BEFORE = {
    "authorized": 1,
    "maximum": 1,
    "started": 0,
    "consumed": 0,
    "remaining": 1,
    "retry": False,
    "resume": False,
    "fallback": False,
}
_EXPECTED_LEDGER_AFTER = {
    "authorized": 1,
    "maximum": 1,
    "started": 1,
    "consumed": 1,
    "remaining": 0,
    "retry": False,
    "resume": False,
    "fallback": False,
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "in_memory_test_only",
    "file_write": False,
    "kernel_store_write": False,
    "e_case_write": False,
    "certificate_generation": False,
    "certified_stop": False,
    "sanitized_receipt": True,
}
_EXPECTED_STILL_BLOCKED = {
    "production_kernel_ingestion": True,
    "kernel_store_write": True,
    "e_case_write": True,
    "checker_or_promotion": True,
    "certificate_generation": True,
    "certified_stop": True,
    "si_llm_001_closure": True,
    "catalog_role_credit_l2": True,
    "m2_fit": True,
    "four_family_llm_finetune": True,
}
_EXPECTED_SELECTED_INPUT = {
    "path": ADMITTED_FIXTURE_PATH,
    "sha256": ADMITTED_FIXTURE_SHA256,
    "package_id": PACKAGE_ID,
}
_FORBIDDEN_PACKAGE_KEYS = frozenset(
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
        "raw_path",
        "filesystem_path",
        "archive_member_path",
        "member_path",
        "payload",
        "payload_bytes",
        "raw_payload",
        "private_evidence",
        "certificate",
        "certified_stop",
        "e_case",
    }
)
_SECRET_AUTHORITY_KEYS = frozenset(
    {
        "secret",
        "secret_key",
        "key",
        "key_bytes",
        "key_material",
        "hmac_key",
        "token",
        "password",
        "credential",
        "private_key",
    }
)
_CLAIM_ID_PATTERN = re.compile(r"^clm_[A-Za-z0-9_-]+$")
_AUTHORITY_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_MAX_PACKAGE_BYTES = 2 * 1024 * 1024


class KernelClaimIRIngestionError(ValueError):
    """Raised when a Kernel Claim IR ingestion gate fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class _DuplicateJSONKey(ValueError):
    pass


def verify_kernel_ingestion_pins(repo_root: Path) -> None:
    """Verify the effective contract, schema, and exact admitted fixture."""

    repo_root = repo_root.resolve()
    for relative_path, expected_sha in (
        (
            EFFECTIVE_CONSUMER_CONTRACT_PATH,
            EFFECTIVE_CONSUMER_CONTRACT_SHA256,
        ),
        (SCHEMA_PATH, SCHEMA_SHA256),
        (ADMITTED_FIXTURE_PATH, ADMITTED_FIXTURE_SHA256),
    ):
        _verify_pin(repo_root, relative_path, expected_sha)

    contract = _load_json(repo_root / EFFECTIVE_CONSUMER_CONTRACT_PATH)
    _validate_effective_contract(contract)

    schema = _load_json(repo_root / SCHEMA_PATH)
    _validate_schema_identity(schema)

    fixture_bytes = (repo_root / ADMITTED_FIXTURE_PATH).read_bytes()
    fixture = _decode_package(fixture_bytes)
    _validate_package(fixture, schema)
    _require_fixture_bytes(fixture_bytes)


def ingest_claim_ir_package(
    package_bytes: bytes,
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and transition the exact admitted package in memory only."""

    repo_root = repo_root.resolve()
    verify_kernel_ingestion_pins(repo_root)
    authority_copy = _validate_authority(authority)
    schema = _load_json(repo_root / SCHEMA_PATH)
    package = _decode_package(package_bytes)
    _validate_package(package, schema)
    _require_fixture_bytes(package_bytes)

    transitioned = copy.deepcopy(package)
    transitioned["kernel_state"] = "ingested_under_separate_authority"
    _validate_schema_instance(transitioned, schema, "transition_schema")
    _assert_only_kernel_state_changed(package, transitioned)

    receipt = _build_sanitized_receipt(package, authority_copy)
    return {
        "ingested_package": transitioned,
        "receipt": receipt,
        "execute_ledger_after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
    }


def _validate_effective_contract(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise KernelClaimIRIngestionError(
            "effective_contract_shape",
            "effective consumer contract must be an object",
        )
    for field, expected in (
        ("artifact_id", EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID),
        ("artifact_type", "kernel_m3_shared_claim_ir_consumer_contract_effective"),
        ("version", "0.1"),
        ("owner", "Kernel/M3*"),
        ("status", EFFECTIVE_CONSUMER_CONTRACT_STATUS),
        ("authority_base_commit", "24e515d32ba8ed98d973d8fb3ea836587646368e"),
        ("identity_pin_method", "sha256_of_file_bytes_external"),
    ):
        _require_constant(
            value.get(field),
            expected,
            f"effective_contract.{field}",
            "effective_contract_shape",
        )

    ownership = _require_mapping(value.get("ownership"), "contract.ownership")
    for field, expected in (
        ("owned_by", "Kernel/M3*"),
        ("assisted_draft_is_not_this_artifact", True),
        ("assisted_draft_sha_forbidden_as_this_identity", ASSISTED_DRAFT_SHA256),
        ("revision_packet_sha_forbidden_as_this_identity", REVISION_PACKET_SHA256),
        ("effective", True),
    ):
        _require_constant(
            ownership.get(field),
            expected,
            f"contract.ownership.{field}",
            "effective_contract_shape",
        )
    not_effective_for = ownership.get("not_effective_for")
    if not isinstance(not_effective_for, list) or not {
        "ingestion_implementation",
        "ingestion_activation",
        "ingestion_execute",
        "kernel_write",
        "e_case_write",
        "certificate_generation",
        "certified_stop",
        "si_llm_001_closure",
    }.issubset(set(not_effective_for)):
        raise KernelClaimIRIngestionError(
            "effective_contract_boundary",
            "effective contract non-authorization boundary is incomplete",
        )

    accepted_schema = _require_mapping(
        value.get("accepted_external_claim_ir_schema"),
        "contract.accepted_schema",
    )
    for field, expected in (
        ("decision", "accept_exact_identity"),
        ("path", SCHEMA_PATH),
        ("schema_id", SCHEMA_ID),
        ("schema_version", SCHEMA_VERSION),
        ("content_sha256", SCHEMA_SHA256),
        ("schema_validation_alone_authorizes_ingestion", False),
    ):
        _require_constant(
            accepted_schema.get(field),
            expected,
            f"contract.accepted_schema.{field}",
            "effective_contract_schema",
        )

    accepted_package = _require_mapping(
        value.get("accepted_admitted_package_identity"),
        "contract.accepted_package",
    )
    for field, expected in (
        ("decision", "accept_exact_package_identity"),
        ("path", ADMITTED_FIXTURE_PATH),
        ("content_sha256", ADMITTED_FIXTURE_SHA256),
        ("package_id", PACKAGE_ID),
        ("surface_id", SURFACE_ID),
        ("claim_count", 41),
        ("claim_id_state", "minted_opaque"),
        ("admission_state", "admitted_under_separate_authority"),
        ("kernel_state_required_before_ingestion", "pending_kernel_schema"),
        ("is_kernel_record", False),
        ("is_e_case_record", False),
        ("is_certificate", False),
    ):
        _require_constant(
            accepted_package.get(field),
            expected,
            f"contract.accepted_package.{field}",
            "effective_contract_package",
        )

    semantics = _require_mapping(
        value.get("target_token_consumption_semantics"),
        "contract.target_token_semantics",
    )
    _require_constant(
        semantics.get("token"),
        "ingested_under_separate_authority",
        "contract.target_token_semantics.token",
        "effective_contract_semantics",
    )
    _require_constant(
        semantics.get("owner_decision"),
        "approve_for_inclusion_in_this_effective_contract",
        "contract.target_token_semantics.owner_decision",
        "effective_contract_semantics",
    )
    transition = _require_mapping(
        semantics.get("state_transition_scope"),
        "contract.target_token_semantics.state_transition_scope",
    )
    for field, expected in (
        ("only_mutable_field", "package.kernel_state"),
        ("before", "pending_kernel_schema"),
        ("after", "ingested_under_separate_authority"),
        ("claim_id", "unchanged"),
        ("claim_id_state", "minted_opaque_unchanged"),
        ("admission_state", "admitted_under_separate_authority_unchanged"),
        ("e_case_write", False),
        ("certificate_generation", False),
    ):
        _require_constant(
            transition.get(field),
            expected,
            f"contract.transition.{field}",
            "effective_contract_semantics",
        )
    receipt_constraints = _require_mapping(
        semantics.get("receipt_constraints"),
        "contract.receipt_constraints",
    )
    for field, expected in (
        ("aggregate_and_governance_only", True),
        ("immutable_after_commit", True),
        ("raw_claim_payload_allowed", False),
        ("labels_or_realized_outcomes_allowed", False),
        ("oracle_mask_hidden_or_required_ids_allowed", False),
        ("key_secret_or_hmac_material_allowed", False),
        ("receipt_is_e_case", False),
        ("receipt_is_certificate", False),
    ):
        _require_constant(
            receipt_constraints.get(field),
            expected,
            f"contract.receipt_constraints.{field}",
            "effective_contract_semantics",
        )

    boundary = _require_mapping(
        value.get("kernel_intake_versus_e_case_boundary"),
        "contract.kernel_e_case_boundary",
    )
    for field, expected in (
        ("confirmed_by_owner", True),
        ("kernel_intake_is_e_case", False),
        ("kernel_intake_implies_claim_truth", False),
        ("kernel_intake_implies_promotion", False),
        ("kernel_intake_implies_checker_acceptance", False),
        ("e_case_requires_separate_contract_executor_and_authority", True),
    ):
        _require_constant(
            boundary.get(field),
            expected,
            f"contract.kernel_e_case_boundary.{field}",
            "effective_contract_boundary",
        )

    transaction = _require_mapping(
        value.get("ingestion_transaction_semantics_declared_but_not_authorized"),
        "contract.ingestion_transaction",
    )
    for field, expected in (
        ("validation_before_any_kernel_mutation", True),
        ("atomic_all_or_nothing", True),
        ("partial_claim_ingestion", False),
        ("implicit_retry_resume_or_fallback", False),
        ("authorized_now", False),
        ("implementation_authorized_now", False),
        ("activation_authorized_now", False),
        ("execute_authorized_now", False),
    ):
        _require_constant(
            transaction.get(field),
            expected,
            f"contract.ingestion_transaction.{field}",
            "effective_contract_boundary",
        )

    explicit = _require_mapping(
        value.get("explicit_non_authorizations"),
        "contract.explicit_non_authorizations",
    )
    if not explicit or any(item is not False for item in explicit.values()):
        raise KernelClaimIRIngestionError(
            "effective_contract_boundary",
            "effective contract non-authorizations must remain false",
        )


def _validate_schema_identity(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise KernelClaimIRIngestionError(
            "schema_shape",
            "Claim IR schema must be an object",
        )
    for field, expected in (
        ("$id", SCHEMA_ID),
        ("type", "object"),
        ("additionalProperties", False),
    ):
        _require_constant(
            value.get(field),
            expected,
            f"schema.{field}",
            "schema_shape",
        )
    properties = _require_mapping(value.get("properties"), "schema.properties")
    schema_version = _require_mapping(
        properties.get("schema_version"),
        "schema.properties.schema_version",
    )
    _require_constant(
        schema_version.get("const"),
        SCHEMA_VERSION,
        "schema.properties.schema_version.const",
        "schema_shape",
    )
    surface = _require_mapping(
        properties.get("surface_id"),
        "schema.properties.surface_id",
    )
    _require_constant(
        surface.get("const"),
        SURFACE_ID,
        "schema.properties.surface_id.const",
        "schema_shape",
    )
    definitions = _require_mapping(value.get("$defs"), "schema.$defs")
    kernel_state = _require_mapping(
        definitions.get("kernel_state"),
        "schema.$defs.kernel_state",
    )
    _require_constant(
        kernel_state.get("enum"),
        [
            "pending_kernel_schema",
            "ingested_under_separate_authority",
            "rejected",
        ],
        "schema.$defs.kernel_state.enum",
        "schema_shape",
    )
    try:
        Draft202012Validator.check_schema(dict(value))
    except Exception as exc:  # pragma: no cover - dependency supplies subclasses
        raise KernelClaimIRIngestionError(
            "schema_invalid",
            "Claim IR schema is not a valid Draft 2020-12 schema",
        ) from exc


def _validate_authority(
    authority: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if authority is None:
        raise KernelClaimIRIngestionError(
            "missing_authority",
            "activated single-use Kernel ingestion authority is required",
        )
    if not isinstance(authority, Mapping):
        raise KernelClaimIRIngestionError(
            "authority_type",
            "Kernel ingestion authority must be an object",
        )
    _reject_secret_keys(authority)
    if set(authority) != _EXPECTED_AUTHORITY_FIELDS:
        raise KernelClaimIRIngestionError(
            "authority_shape",
            "Kernel ingestion authority fields are not canonical",
        )
    artifact_id = authority.get("artifact_id")
    if not isinstance(artifact_id, str) or not _AUTHORITY_ID_PATTERN.fullmatch(
        artifact_id
    ):
        raise KernelClaimIRIngestionError(
            "authority_shape",
            "Kernel ingestion authority artifact id is invalid",
        )
    _require_constant(
        authority.get("status"),
        "activated_single_kernel_ingestion_execute_authorized",
        "authority.status",
        "not_activated",
    )
    _require_exact_mapping(
        authority.get("target"),
        {
            "surface_id": SURFACE_ID,
            "source_class": SOURCE_CLASS,
            "adapter_id": ADAPTER_ID,
            "package_id": PACKAGE_ID,
            "target_token": "ingested_under_separate_authority",
            "execution_scope": "in_memory_test_only",
        },
        "authority.target",
        "authority_target",
    )

    pins = authority.get("pinned_hashes")
    if not isinstance(pins, Mapping):
        raise KernelClaimIRIngestionError(
            "authority_pin",
            "authority pinned_hashes must be an object",
        )
    effective_pin = pins.get("effective_consumer_contract_sha256")
    if effective_pin in FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS:
        raise KernelClaimIRIngestionError(
            "non_effective_contract_identity",
            "draft or revision packet SHA cannot identify the effective contract",
        )
    _require_exact_mapping(
        pins,
        {
            "effective_consumer_contract_sha256": (
                EFFECTIVE_CONSUMER_CONTRACT_SHA256
            ),
            "schema_sha256": SCHEMA_SHA256,
            "admitted_fixture_sha256": ADMITTED_FIXTURE_SHA256,
        },
        "authority.pinned_hashes",
        "effective_contract_pin",
    )
    _require_exact_mapping(
        authority.get("selected_input"),
        _EXPECTED_SELECTED_INPUT,
        "authority.selected_input",
        "fixture_pin",
    )
    _require_exact_mapping(
        authority.get("execute_ledger"),
        _EXPECTED_LEDGER_BEFORE,
        "authority.execute_ledger",
        "authority_ledger",
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
    return copy.deepcopy(dict(authority))


def _decode_package(package_bytes: bytes) -> dict[str, Any]:
    if not isinstance(package_bytes, bytes):
        raise KernelClaimIRIngestionError(
            "package_type",
            "admitted package must be provided as immutable bytes",
        )
    if not package_bytes or len(package_bytes) > _MAX_PACKAGE_BYTES:
        raise KernelClaimIRIngestionError(
            "package_size",
            "admitted package byte length is empty or exceeds the bound",
        )
    try:
        decoded = package_bytes.decode("utf-8")
        package = json.loads(decoded, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateJSONKey) as exc:
        raise KernelClaimIRIngestionError(
            "package_json",
            "admitted package is not canonical UTF-8 JSON",
        ) from exc
    if not isinstance(package, dict):
        raise KernelClaimIRIngestionError(
            "package_shape",
            "admitted package must decode to an object",
        )
    _reject_forbidden_package_keys(package)
    return package


def _validate_package(package: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    if set(package) != _EXPECTED_PACKAGE_FIELDS:
        raise KernelClaimIRIngestionError(
            "package_shape",
            "admitted package fields are not canonical",
        )
    for field, expected in (
        ("schema_version", SCHEMA_VERSION),
        ("package_id", PACKAGE_ID),
        ("surface_id", SURFACE_ID),
        ("kernel_state", "pending_kernel_schema"),
        ("claim_id_state", "minted_opaque"),
        ("admission_state", "admitted_under_separate_authority"),
    ):
        _require_constant(
            package.get(field),
            expected,
            f"package.{field}",
            "package_state" if field.endswith("state") else "package_identity",
        )

    claims = package.get("claims")
    if not isinstance(claims, list) or len(claims) != 41:
        raise KernelClaimIRIngestionError(
            "package_claims",
            "admitted package must contain the exact bounded claim count",
        )
    identifiers: set[str] = set()
    for claim in claims:
        if not isinstance(claim, Mapping) or set(claim) != _EXPECTED_CLAIM_FIELDS:
            raise KernelClaimIRIngestionError(
                "claim_shape",
                "admitted claim fields are not canonical",
            )
        for field, expected in (
            ("claim_id_state", "minted_opaque"),
            ("admission_state", "admitted_under_separate_authority"),
        ):
            _require_constant(
                claim.get(field),
                expected,
                f"claim.{field}",
                "package_state",
            )
        claim_id = claim.get("claim_id")
        if (
            not isinstance(claim_id, str)
            or not _CLAIM_ID_PATTERN.fullmatch(claim_id)
            or claim_id in identifiers
        ):
            raise KernelClaimIRIngestionError(
                "package_claim_id",
                "admitted Claim-IDs must be opaque and unique",
            )
        identifiers.add(claim_id)

    manifest = package.get("manifest")
    if not isinstance(manifest, Mapping) or set(manifest) != _EXPECTED_MANIFEST_FIELDS:
        raise KernelClaimIRIngestionError(
            "manifest_shape",
            "admitted package manifest fields are not canonical",
        )
    _require_constant(
        manifest.get("claim_count"),
        41,
        "package.manifest.claim_count",
        "manifest_identity",
    )
    expected_content_hash = hashlib.sha256(
        json.dumps(
            claims,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    _require_constant(
        manifest.get("content_hash"),
        expected_content_hash,
        "package.manifest.content_hash",
        "manifest_identity",
    )
    _validate_schema_instance(package, schema, "schema_validation")


def _validate_schema_instance(
    package: Mapping[str, Any],
    schema: Mapping[str, Any],
    error_code: str,
) -> None:
    errors = list(Draft202012Validator(dict(schema)).iter_errors(dict(package)))
    if errors:
        raise KernelClaimIRIngestionError(
            error_code,
            "Claim IR package failed the pinned Draft 2020-12 schema",
        )


def _require_fixture_bytes(package_bytes: bytes) -> None:
    if hashlib.sha256(package_bytes).hexdigest() != ADMITTED_FIXTURE_SHA256:
        raise KernelClaimIRIngestionError(
            "fixture_pin",
            "admitted package bytes do not match the accepted fixture SHA",
        )


def _assert_only_kernel_state_changed(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> None:
    expected = copy.deepcopy(dict(before))
    expected["kernel_state"] = "ingested_under_separate_authority"
    if after != expected:
        raise KernelClaimIRIngestionError(
            "identity_preservation",
            "in-memory ingestion changed fields beyond package.kernel_state",
        )


def _build_sanitized_receipt(
    package: Mapping[str, Any],
    authority: Mapping[str, Any],
) -> dict[str, Any]:
    authority_sha = _canonical_json_sha256(authority)
    claim_ids = [claim["claim_id"] for claim in package["claims"]]
    claim_id_list_sha = hashlib.sha256(
        json.dumps(
            claim_ids,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    idempotency_digest = hashlib.sha256(
        "\0".join(
            (
                "project05-shared-kernel-intake-v0.1",
                EFFECTIVE_CONSUMER_CONTRACT_SHA256,
                SCHEMA_SHA256,
                ADMITTED_FIXTURE_SHA256,
            )
        ).encode("utf-8")
    ).hexdigest()
    receipt_digest = hashlib.sha256(
        f"{idempotency_digest}\0{authority_sha}".encode("utf-8")
    ).hexdigest()
    return {
        "receipt_version": "kernel-claim-ir-ingestion-receipt-v0.1",
        "receipt_id": f"kir_{receipt_digest[:32]}",
        "receipt_scope": "sanitized_in_memory_test_only",
        "decision": "in_memory_ingestion_contract_test_passed",
        "effective_consumer_contract": {
            "artifact_id": EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
            "version": "0.1",
            "path": EFFECTIVE_CONSUMER_CONTRACT_PATH,
            "sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
        },
        "schema": {
            "id": SCHEMA_ID,
            "version": SCHEMA_VERSION,
            "path": SCHEMA_PATH,
            "sha256": SCHEMA_SHA256,
        },
        "input": {
            "path": ADMITTED_FIXTURE_PATH,
            "sha256": ADMITTED_FIXTURE_SHA256,
            "package_id": PACKAGE_ID,
            "surface_id": SURFACE_ID,
            "claim_count": 41,
            "claim_id_list_sha256": claim_id_list_sha,
            "claims_content_hash": package["manifest"]["content_hash"],
        },
        "authority": {
            "artifact_id": authority["artifact_id"],
            "canonical_sha256": authority_sha,
            "execution_scope": "in_memory_test_only",
            "execute_ledger_before": copy.deepcopy(_EXPECTED_LEDGER_BEFORE),
            "execute_ledger_after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
        },
        "transaction": {
            "idempotency_key": f"kii_{idempotency_digest}",
            "atomic_all_or_nothing": True,
            "partial_claim_ingestion": False,
            "retry": False,
            "resume": False,
            "fallback": False,
            "kernel_intake_committed_in_memory_test_double": True,
            "production_kernel_store_write": False,
        },
        "state_transition": {
            "field": "package.kernel_state",
            "before": "pending_kernel_schema",
            "after": "ingested_under_separate_authority",
        },
        "identity_preservation": {
            "package_id_unchanged": True,
            "claim_order_unchanged": True,
            "claim_ids_unchanged": True,
            "claim_id_state_unchanged": True,
            "admission_state_unchanged": True,
            "claim_records_unchanged": True,
            "projection_ref_unchanged": True,
        },
        "side_effects": {
            "file_write": False,
            "production_kernel_store_write": False,
            "e_case_write": False,
            "checker_or_promotion": False,
            "certificate_generation": False,
            "certified_stop": False,
            "si_llm_001_closure": False,
            "catalog_role_credit_l2_change": False,
            "m2_fit": False,
            "four_family_llm_finetune": False,
        },
    }


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KernelClaimIRIngestionError(
            "contract_shape",
            f"{field} must be an object",
        )
    return value


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    error_code: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise KernelClaimIRIngestionError(
            error_code,
            f"{field} does not match the frozen shape",
        )
    for key, expected_value in expected.items():
        actual = value.get(key)
        if actual != expected_value or type(actual) is not type(expected_value):
            raise KernelClaimIRIngestionError(
                error_code,
                f"{field}.{key} does not match the frozen value",
            )


def _require_constant(
    value: Any,
    expected: Any,
    field: str,
    error_code: str,
) -> None:
    if value != expected or type(value) is not type(expected):
        raise KernelClaimIRIngestionError(
            error_code,
            f"{field} does not match the frozen value",
        )


def _reject_forbidden_package_keys(
    value: Any,
    path: tuple[str, ...] = (),
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            if normalized in _FORBIDDEN_PACKAGE_KEYS:
                raise KernelClaimIRIngestionError(
                    "forbidden_field",
                    "admitted package contains a forbidden authority field",
                )
            _reject_forbidden_package_keys(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        for index, nested in enumerate(value):
            _reject_forbidden_package_keys(nested, (*path, str(index)))


def _reject_secret_keys(
    value: Any,
    path: tuple[str, ...] = (),
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            if normalized in _SECRET_AUTHORITY_KEYS:
                raise KernelClaimIRIngestionError(
                    "secret_in_authority",
                    "Kernel ingestion authority contains a forbidden secret field",
                )
            _reject_secret_keys(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        for index, nested in enumerate(value):
            _reject_secret_keys(nested, (*path, str(index)))


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
        raise KernelClaimIRIngestionError(
            "authority_json",
            "Kernel ingestion authority is not canonical JSON",
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise KernelClaimIRIngestionError(
            "pin_missing",
            f"pinned file missing: {relative_path}",
        )
    if _sha256(path) != expected_sha:
        raise KernelClaimIRIngestionError(
            "pin_mismatch",
            f"pinned SHA mismatch: {relative_path}",
        )


def _load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text, object_pairs_hook=_unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, _DuplicateJSONKey) as exc:
        raise KernelClaimIRIngestionError(
            "json_read",
            f"cannot read canonical JSON artifact: {path.name}",
        ) from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(key)
        result[key] = value
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise KernelClaimIRIngestionError(
            "pin_read",
            f"cannot read pinned artifact: {path.name}",
        ) from exc
    return digest.hexdigest()


def _normalize_key(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")
