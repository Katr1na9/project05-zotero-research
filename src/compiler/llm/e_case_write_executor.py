"""Fail-closed, single-use production E_case write executor.

The executor reads the exact immutable Kernel Claim-IR intake record and its
sanitized receipt, constructs one independently typed provenance-only E_case
record, validates it against the Kernel/M3*-issued effective schema, and
returns an in-memory target plus sanitized receipt.  An authorized wrapper is
responsible for atomically persisting those artifacts and the exhausted
activation ledger.  This module never mutates the intake store, writes an
E_case target directly, invokes Checker, emits a certificate, or performs
CERTIFIED_STOP, SI-LLM-001, L2, or Part B effects.
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


AUTHORITY_BASE_COMMIT = "e78b0784b2e5f0fdca87a0bdf278d721ba6c0926"
AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-production-e-case-single-execute-"
    "authority-design-v0.1-20260725.json"
)
AUTHORITY_DESIGN_SHA256 = (
    "154eaa54f4387c0a0bfdbf01dba8130f0542ddb140444358da99d4c67d2ab1ee"
)
AUTHORITY_DESIGN_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-production-e-case-single-execute-authority-design-"
    "v0.1-20260725"
)
AUTHORITY_DESIGN_STATUS = "design_only_production_e_case_authority_not_activated"

EFFECTIVE_SCHEMA_PATH = "schemas/e-case-record-effective-v0.1.schema.json"
EFFECTIVE_SCHEMA_SHA256 = (
    "dbdc0854487fc0d255c4001332ea5fd183c71a248cb04223630ce8af59cd42a1"
)
EFFECTIVE_SCHEMA_ARTIFACT_ID = "e-case-record-effective-v0.1"
EFFECTIVE_SCHEMA_VERSION = "0.1"
EFFECTIVE_SCHEMA_ID = (
    "https://project05.invalid/schemas/e-case-record-effective-v0.1.schema.json"
)
EFFECTIVE_SCHEMA_STATUS = "effective_e_case_target_schema_semantics_only"

EFFECTIVE_WRITE_CONTRACT_PATH = (
    "docs/kernel/kernel-v0.8-e-case-write-contract-effective-v0.1-20260725.json"
)
EFFECTIVE_WRITE_CONTRACT_SHA256 = (
    "eef9a3a2ea805f49b94475c053ebb39b57de84369b34b1fcd0d7b9d198ac0d63"
)
EFFECTIVE_WRITE_CONTRACT_ARTIFACT_ID = (
    "kernel-v0.8-e-case-write-contract-effective-v0.1-20260725"
)
EFFECTIVE_WRITE_CONTRACT_VERSION = "0.1"
EFFECTIVE_WRITE_CONTRACT_STATUS = (
    "effective_e_case_write_contract_semantics_only_write_not_authorized"
)

OWNER_RESPONSE_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-m3-e-case-schema-contract-"
    "review-response-v0.1-20260725.json"
)
OWNER_RESPONSE_SHA256 = (
    "490a308abde413126dcbc5f2ed6c8ed0d19cc32c74fe8d5931f67895b9dc91f0"
)
OWNER_RESPONSE_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-kernel-m3-e-case-schema-contract-review-response-"
    "v0.1-20260725"
)
OWNER_RESPONSE_STATUS = (
    "accept_and_issue_new_effective_schema_and_contract_write_still_blocked"
)

EFFECTIVE_CONSUMER_CONTRACT_PATH = (
    "docs/kernel/kernel-v0.8-shared-claim-ir-consumer-contract-effective-"
    "v0.1-20260725.json"
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

SOURCE_STORE_RECORD_PATH = (
    "docs/llm-editor/fixtures/kernel-claim-ir-intake-store/"
    "project05-depth2-public-v0.1/store-record.json"
)
SOURCE_STORE_RECORD_SHA256 = (
    "06757c1b027866ff1e0aa423aba72bcb035aaba2bc56f4b41fcd7b4ddecc9248"
)
SOURCE_STORE_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/kernel-claim-ir-intake-store/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)
SOURCE_STORE_RECEIPT_SHA256 = (
    "4e3c50ae1f6fb480905f0018a0a1ea4145e85e380bf8aef8724166c47596c565"
)
SOURCE_STORE_RECORD_ID = "kcisr_98aa4efb2a71a8466249148610ff4624"
SOURCE_STORE_TARGET_ID = (
    "kernel_claim_ir_intake_store:project05_depth2_public:"
    "pkg_73d77b55ef6a517a0dc528f7f3a89bd9:v0.1"
)

INGESTED_PACKAGE_PATH = (
    "docs/llm-editor/fixtures/claim-ir-ingested/"
    "project05-depth2-public-minted-admitted-ingested-v0.1/package.json"
)
INGESTED_PACKAGE_SHA256 = (
    "908becf0c14f0bec756bf0382b85c5eeb100d61e0e19cde8a9375977071bd179"
)
EXTERNAL_SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
EXTERNAL_SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
KERNEL_SCHEMA_PATH = "schemas/claim-ir-kernel.schema.json"
KERNEL_SCHEMA_SHA256 = (
    "7c6fa2db0b75d69340be5a8843ba0c373e2d5b25b0d37cf8f1d1c416a787865d"
)

ASSISTED_SCHEMA_SHA256 = (
    "caa29f20c619653e4340822c096b11746d418b205506464bd8f104ad89b792fc"
)
ASSISTED_WRITE_CONTRACT_SHA256 = (
    "faa817a7f33744c4dfc819cc932584659219f6e0e59ff46b1d27d3bfc82b1c8f"
)
REVIEW_PACKET_SHA256 = (
    "8723463f73bc05ebcd473fa2554ba7203b272631c9734d9b4fc9a64433c62f23"
)
FORBIDDEN_NON_EFFECTIVE_SCHEMA_SHAS = frozenset({ASSISTED_SCHEMA_SHA256})
FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS = frozenset(
    {ASSISTED_WRITE_CONTRACT_SHA256, REVIEW_PACKET_SHA256}
)

EXECUTOR_PATH = "src/compiler/llm/e_case_write_executor.py"
ACTIVATION_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-production-e-case-single-execute-"
    "activation-v0.1-20260725.json"
)
ACTIVATION_STATUS = "activated_single_production_e_case_execute_authorized"
SURFACE_ID = "project05_depth2_public"
SOURCE_CLASS = "planner_experiment_inputs"
ADAPTER_ID = "m1a_planner_inputs_v0_1"
PACKAGE_ID = "pkg_73d77b55ef6a517a0dc528f7f3a89bd9"
E_CASE_TARGET_ID = (
    "e_case:project05_depth2_public:pkg_73d77b55ef6a517a0dc528f7f3a89bd9:v0.1"
)
E_CASE_RECORD_PATH = (
    "docs/llm-editor/fixtures/e-case/"
    "project05-depth2-public-v0.1/e-case-record.json"
)
E_CASE_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/e-case/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)

_E_CASE_ID_DIGEST = hashlib.sha256(
    "\0".join(
        (
            EFFECTIVE_WRITE_CONTRACT_SHA256,
            SOURCE_STORE_RECORD_SHA256,
            E_CASE_TARGET_ID,
        )
    ).encode("utf-8")
).hexdigest()
E_CASE_ID = f"ec_{_E_CASE_ID_DIGEST}"
_IDEMPOTENCY_DIGEST = hashlib.sha256(
    "\0".join(
        (
            EFFECTIVE_WRITE_CONTRACT_SHA256,
            EFFECTIVE_SCHEMA_SHA256,
            SOURCE_STORE_RECORD_SHA256,
            SOURCE_STORE_RECEIPT_SHA256,
            E_CASE_TARGET_ID,
        )
    ).encode("utf-8")
).hexdigest()
IDEMPOTENCY_KEY = f"ecase_idem_{_IDEMPOTENCY_DIGEST}"

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
_EXPECTED_ACTIVATION_FIELDS = frozenset(
    {
        "artifact_id",
        "artifact_type",
        "version",
        "created_date",
        "authority_base_commit",
        "status",
        "authority_design",
        "owner_approval",
        "target",
        "pinned_hashes",
        "selected_source",
        "transaction_contract",
        "execute_ledger",
        "output_policy",
        "still_blocked",
        "execution_audit",
    }
)
_EXPECTED_AUTHORITY_DESIGN_REF = {
    "artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
    "path": AUTHORITY_DESIGN_PATH,
    "sha256": AUTHORITY_DESIGN_SHA256,
    "status": AUTHORITY_DESIGN_STATUS,
}
_EXPECTED_OWNER_APPROVAL_REF = {
    "artifact_id": OWNER_RESPONSE_ARTIFACT_ID,
    "path": OWNER_RESPONSE_PATH,
    "sha256": OWNER_RESPONSE_SHA256,
    "status": OWNER_RESPONSE_STATUS,
    "owner": "Kernel/M3*",
    "overall_decision": "accept",
    "e_case_write_authorized_by_response": False,
}
_EXPECTED_TARGET = {
    "surface_id": SURFACE_ID,
    "source_class": SOURCE_CLASS,
    "adapter_id": ADAPTER_ID,
    "package_id": PACKAGE_ID,
    "source_record_class": "kernel_claim_ir_intake_store",
    "target_record_class": "e_case",
    "e_case_target_id": E_CASE_TARGET_ID,
    "operation": "construct_and_write_one_separately_typed_e_case_record",
}
_EXPECTED_STATIC_PINS = {
    "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
    "owner_response_sha256": OWNER_RESPONSE_SHA256,
    "effective_e_case_schema_sha256": EFFECTIVE_SCHEMA_SHA256,
    "effective_e_case_write_contract_sha256": EFFECTIVE_WRITE_CONTRACT_SHA256,
    "effective_consumer_contract_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    "external_envelope_schema_sha256": EXTERNAL_SCHEMA_SHA256,
    "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
    "ingested_package_sha256": INGESTED_PACKAGE_SHA256,
    "source_store_record_sha256": SOURCE_STORE_RECORD_SHA256,
    "source_store_receipt_sha256": SOURCE_STORE_RECEIPT_SHA256,
}
_EXPECTED_SELECTED_SOURCE = {
    "store_record": {
        "path": SOURCE_STORE_RECORD_PATH,
        "sha256": SOURCE_STORE_RECORD_SHA256,
        "store_record_id": SOURCE_STORE_RECORD_ID,
        "store_target_id": SOURCE_STORE_TARGET_ID,
        "package_id": PACKAGE_ID,
        "surface_id": SURFACE_ID,
        "is_kernel_store_record": True,
        "is_e_case": False,
    },
    "sanitized_store_receipt": {
        "path": SOURCE_STORE_RECEIPT_PATH,
        "sha256": SOURCE_STORE_RECEIPT_SHA256,
    },
}
_EXPECTED_TRANSACTION_CONTRACT = {
    "e_case_target_id": E_CASE_TARGET_ID,
    "idempotency_key": IDEMPOTENCY_KEY,
    "transaction_id_derivation": (
        "ecase_txn_ + first_32_hex(sha256(effective_contract_sha256 NUL "
        "source_record_sha256 NUL e_case_target_id NUL activation_sha256_before))"
    ),
    "atomic_all_or_nothing": True,
    "target_empty_or_idempotently_equivalent_required": True,
    "partial_write": False,
}
_EXPECTED_OUTPUT_POLICY_CONSTANTS = {
    "mode": "versioned_e_case_record_and_sanitized_receipt",
    "file_write": True,
    "e_case_write": True,
    "new_separately_typed_target": True,
    "source_store_write": False,
    "source_store_mutation_or_relabel": False,
    "kernel_store_reexecution": False,
    "checker_or_promotion": False,
    "certificate_generation": False,
    "certified_stop": False,
    "si_llm_001_closure": False,
    "l2_or_part_b_change": False,
}
_EXPECTED_OUTPUT_POLICY_FIELDS = frozenset(
    {
        *_EXPECTED_OUTPUT_POLICY_CONSTANTS,
        "e_case_record_path",
        "sanitized_receipt_path",
    }
)
_EXPECTED_STILL_BLOCKED = {
    "second_e_case_execute": True,
    "source_store_mutation_or_relabel": True,
    "kernel_store_reexecution": True,
    "checker_or_promotion": True,
    "certificate": True,
    "certified_stop": True,
    "si_llm_001_closure": True,
    "l2": True,
    "part_b_elevation": True,
    "production_registration_execution": True,
    "catalog_role_credit": True,
    "m2_fit": True,
    "four_family_llm_finetune": True,
}

_ACTIVATION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
_CLAIM_ID_PATTERN = re.compile(r"^clm_[A-Za-z0-9_-]+$")
_SECRET_KEYS = frozenset(
    {
        "secret",
        "secret_key",
        "key_material",
        "hmac_key",
        "password",
        "credential",
        "private_key",
        "token",
    }
)
_MAX_JSON_BYTES = 4 * 1024 * 1024


class ECaseWriteError(ValueError):
    """Raised when an E_case write gate fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class _DuplicateJSONKey(ValueError):
    pass


def verify_write_pins(repo_root: Path) -> None:
    """Verify all frozen owner, schema, contract, and source pins."""

    root = repo_root.resolve()
    for relative_path, expected_sha in (
        (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
        (EFFECTIVE_SCHEMA_PATH, EFFECTIVE_SCHEMA_SHA256),
        (EFFECTIVE_WRITE_CONTRACT_PATH, EFFECTIVE_WRITE_CONTRACT_SHA256),
        (OWNER_RESPONSE_PATH, OWNER_RESPONSE_SHA256),
        (EFFECTIVE_CONSUMER_CONTRACT_PATH, EFFECTIVE_CONSUMER_CONTRACT_SHA256),
        (EXTERNAL_SCHEMA_PATH, EXTERNAL_SCHEMA_SHA256),
        (KERNEL_SCHEMA_PATH, KERNEL_SCHEMA_SHA256),
        (INGESTED_PACKAGE_PATH, INGESTED_PACKAGE_SHA256),
        (SOURCE_STORE_RECORD_PATH, SOURCE_STORE_RECORD_SHA256),
        (SOURCE_STORE_RECEIPT_PATH, SOURCE_STORE_RECEIPT_SHA256),
    ):
        _verify_pin(root, relative_path, expected_sha)

    _validate_authority_design(_load_json(root / AUTHORITY_DESIGN_PATH))
    schema = _load_json(root / EFFECTIVE_SCHEMA_PATH)
    _validate_effective_schema(schema)
    _validate_effective_contract(_load_json(root / EFFECTIVE_WRITE_CONTRACT_PATH))
    _validate_owner_response(_load_json(root / OWNER_RESPONSE_PATH))
    record_bytes = (root / SOURCE_STORE_RECORD_PATH).read_bytes()
    receipt_bytes = (root / SOURCE_STORE_RECEIPT_PATH).read_bytes()
    validate_source_bytes(record_bytes, receipt_bytes, schema=schema)


def validate_source_bytes(
    source_record_bytes: bytes,
    source_receipt_bytes: bytes,
    *,
    schema: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate exact immutable source bytes and return the decoded record."""

    if hashlib.sha256(source_record_bytes).hexdigest() != SOURCE_STORE_RECORD_SHA256:
        raise ECaseWriteError("source_record_pin", "source store record bytes changed")
    if hashlib.sha256(source_receipt_bytes).hexdigest() != SOURCE_STORE_RECEIPT_SHA256:
        raise ECaseWriteError("source_receipt_pin", "source store receipt bytes changed")
    record = _decode_json_bytes(source_record_bytes, "source_record")
    receipt = _decode_json_bytes(source_receipt_bytes, "source_receipt")
    _validate_source_record(record)
    _validate_source_receipt(receipt)
    if schema is not None:
        errors = list(Draft202012Validator(dict(schema)).iter_errors(record))
        if not errors:
            raise ECaseWriteError(
                "source_type_separation",
                "Kernel intake record must not validate as an E_case target",
            )
    return record


def execute_e_case_write(
    *,
    repo_root: Path,
    activation_path: Path | None = None,
    source_record_bytes: bytes | None = None,
    source_receipt_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Construct one E_case target in memory under a single-use activation."""

    if activation_path is None:
        raise ECaseWriteError(
            "missing_activation",
            "a distinct activated single-use production E_case authority is required",
        )
    root = repo_root.resolve()
    verify_write_pins(root)
    activation_bytes = _read_bounded_bytes(Path(activation_path), "activation")
    activation = _decode_json_bytes(activation_bytes, "activation")
    activation_sha256 = hashlib.sha256(activation_bytes).hexdigest()
    executor_sha256 = _sha256(root / EXECUTOR_PATH)
    authority = _validate_activation(
        activation,
        repo_root=root,
        executor_sha256=executor_sha256,
    )

    frozen_record_bytes = (root / SOURCE_STORE_RECORD_PATH).read_bytes()
    frozen_receipt_bytes = (root / SOURCE_STORE_RECEIPT_PATH).read_bytes()
    record_bytes = frozen_record_bytes if source_record_bytes is None else source_record_bytes
    receipt_bytes = (
        frozen_receipt_bytes if source_receipt_bytes is None else source_receipt_bytes
    )
    schema = _load_json(root / EFFECTIVE_SCHEMA_PATH)
    source = validate_source_bytes(record_bytes, receipt_bytes, schema=schema)
    transaction_id = _derive_transaction_id(activation_sha256)
    target = _build_target_record(
        source,
        authority=authority,
        activation_sha256=activation_sha256,
        executor_sha256=executor_sha256,
        transaction_id=transaction_id,
    )
    errors = sorted(
        Draft202012Validator(dict(schema)).iter_errors(target),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ECaseWriteError("target_schema", errors[0].message)
    _assert_source_still_unchanged(root, frozen_record_bytes, frozen_receipt_bytes)
    receipt = _build_sanitized_receipt(
        target,
        authority=authority,
        activation_sha256=activation_sha256,
        executor_sha256=executor_sha256,
        transaction_id=transaction_id,
    )
    write_required = _validate_target_state(
        root,
        record=target,
        receipt=receipt,
        output_policy=authority["output_policy"],
    )
    return {
        "e_case_record": target,
        "sanitized_receipt": receipt,
        "activation_sha256_before": activation_sha256,
        "execute_ledger_after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
        "write_required": write_required,
    }


def _validate_authority_design(value: Any) -> None:
    design = _require_mapping(value, "authority_design", "authority_design")
    for field, expected in (
        ("artifact_id", AUTHORITY_DESIGN_ARTIFACT_ID),
        ("artifact_type", "production_e_case_single_execute_authority_design"),
        ("version", "0.1"),
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
        ("production_e_case_write_authorized", False),
        ("production_e_case_write_performed", False),
    ):
        _require_constant(
            current.get(field),
            expected,
            f"authority_design.current.{field}",
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
        "authority_design.future.status",
        "authority_design",
    )
    _require_exact_mapping(
        future.get("execute_ledger"),
        _EXPECTED_LEDGER_BEFORE,
        "authority_design.future.execute_ledger",
        "authority_design",
    )


def _validate_effective_schema(value: Any) -> None:
    schema = _require_mapping(value, "effective_schema", "effective_schema")
    for field, expected in (
        ("$id", EFFECTIVE_SCHEMA_ID),
        ("type", "object"),
        ("additionalProperties", False),
    ):
        _require_constant(
            schema.get(field), expected, f"effective_schema.{field}", "effective_schema"
        )
    properties = _require_mapping(
        schema.get("properties"), "effective_schema.properties", "effective_schema"
    )
    _require_constant(
        _require_mapping(
            properties.get("is_e_case"), "schema.is_e_case", "effective_schema"
        ).get("const"),
        True,
        "schema.is_e_case.const",
        "effective_schema",
    )
    _require_constant(
        _require_mapping(
            properties.get("is_kernel_store_record"),
            "schema.is_kernel_store_record",
            "effective_schema",
        ).get("const"),
        False,
        "schema.is_kernel_store_record.const",
        "effective_schema",
    )
    prohibited = schema.get("x-project05-prohibited-top-level-fields")
    if not isinstance(prohibited, list) or not {
        "stored_claim_ir_package",
        "certificate",
        "checker_decision",
        "certified_stop",
        "claim_values",
        "labels",
        "realized_outcomes",
        "oracle",
    }.issubset(set(prohibited)):
        raise ECaseWriteError("effective_schema", "schema prohibition list is incomplete")
    try:
        Draft202012Validator.check_schema(dict(schema))
    except Exception as exc:  # pragma: no cover
        raise ECaseWriteError("effective_schema", "effective schema is invalid") from exc


def _validate_effective_contract(value: Any) -> None:
    contract = _require_mapping(value, "effective_contract", "effective_contract")
    for field, expected in (
        ("artifact_id", EFFECTIVE_WRITE_CONTRACT_ARTIFACT_ID),
        ("artifact_type", "kernel_m3_e_case_write_contract_effective"),
        ("version", EFFECTIVE_WRITE_CONTRACT_VERSION),
        ("owner", "Kernel/M3*"),
        ("status", EFFECTIVE_WRITE_CONTRACT_STATUS),
        ("identity_pin_method", "sha256_of_file_bytes_external"),
    ):
        _require_constant(
            contract.get(field), expected, f"effective_contract.{field}", "effective_contract"
        )
    ownership = _require_mapping(
        contract.get("ownership_and_effectivity"),
        "effective_contract.ownership",
        "effective_contract",
    )
    for field, expected in (
        ("owned_by", "Kernel/M3*"),
        ("effective", True),
        ("assisted_draft_sha_forbidden_as_this_identity", ASSISTED_WRITE_CONTRACT_SHA256),
        ("assisted_schema_sha_forbidden_as_effective_schema_identity", ASSISTED_SCHEMA_SHA256),
        ("review_packet_sha_forbidden_as_effective_identity", REVIEW_PACKET_SHA256),
    ):
        _require_constant(
            ownership.get(field), expected, f"effective_contract.ownership.{field}", "effective_contract"
        )
    schema = _require_mapping(
        contract.get("accepted_effective_e_case_schema"),
        "effective_contract.accepted_schema",
        "effective_contract",
    )
    for field, expected in (
        ("artifact_id", EFFECTIVE_SCHEMA_ARTIFACT_ID),
        ("version", EFFECTIVE_SCHEMA_VERSION),
        ("path", EFFECTIVE_SCHEMA_PATH),
        ("content_sha256", EFFECTIVE_SCHEMA_SHA256),
        ("schema_id", EFFECTIVE_SCHEMA_ID),
        ("assisted_basis_may_occupy_effective_schema_sha256", False),
    ):
        _require_constant(
            schema.get(field), expected, f"effective_contract.accepted_schema.{field}", "effective_contract"
        )
    source = _require_mapping(
        contract.get("accepted_source_identity"),
        "effective_contract.accepted_source",
        "effective_contract",
    )
    for field, expected in (
        ("decision", "accept_exact_source_identity"),
        ("source_record_path", SOURCE_STORE_RECORD_PATH),
        ("source_record_sha256", SOURCE_STORE_RECORD_SHA256),
        ("source_receipt_path", SOURCE_STORE_RECEIPT_PATH),
        ("source_receipt_sha256", SOURCE_STORE_RECEIPT_SHA256),
        ("source_record_must_have_is_kernel_store_record_true", True),
        ("source_record_must_have_is_e_case_false", True),
        ("source_record_may_be_mutated", False),
        ("source_receipt_may_be_mutated", False),
    ):
        _require_constant(
            source.get(field), expected, f"effective_contract.source.{field}", "effective_contract"
        )
    mapping = _require_mapping(
        contract.get("source_to_e_case_mapping"),
        "effective_contract.mapping",
        "effective_contract",
    )
    for field, expected in (
        ("mapping_mode", "construct_new_provenance_only_target_from_exact_source_identity"),
        ("target_must_be_new_separately_typed_object", True),
        ("claim_order_preserved", True),
        ("claim_identity_only", True),
        ("claim_values_copied_to_e_case", False),
        ("silent_schema_or_authority_escalation", False),
        ("owner_decision", "accepted"),
        ("target_must_pin_this_effective_e_case_write_contract", True),
    ):
        _require_constant(
            mapping.get(field), expected, f"effective_contract.mapping.{field}", "effective_contract"
        )
    transaction = _require_mapping(
        contract.get("transaction_and_idempotency_contract"),
        "effective_contract.transaction",
        "effective_contract",
    )
    for field, expected in (
        ("validation_before_any_target_mutation", True),
        ("atomic_all_or_nothing", True),
        ("partial_write", False),
        ("process_start_consumes_single_attempt", True),
        ("success_or_failure_exhausts_attempt", True),
        ("automatic_retry", False),
        ("resume", False),
        ("fallback", False),
        ("target_must_be_empty_or_idempotently_equivalent_before_start", True),
        ("existing_non_idempotent_target_fails_closed", True),
        ("owner_decision", "accepted"),
        ("authorized_now", False),
    ):
        _require_constant(
            transaction.get(field), expected, f"effective_contract.transaction.{field}", "effective_contract"
        )
    boundary = _require_mapping(
        contract.get("checker_certificate_and_certified_stop_boundary"),
        "effective_contract.boundary",
        "effective_contract",
    )
    if boundary.get("confirmed_by_owner") is not True:
        raise ECaseWriteError("effective_contract", "owner boundary confirmation is missing")
    for field in (
        "e_case_write_is_checker_decision",
        "e_case_write_is_checker_acceptance",
        "e_case_write_is_evidence_sufficiency",
        "e_case_write_is_truth_assertion",
        "e_case_write_is_promotion",
        "e_case_write_is_certificate",
        "e_case_write_is_certified_stop",
        "e_case_write_closes_si_llm_001",
        "e_case_write_passes_l2_or_part_b",
    ):
        _require_constant(
            boundary.get(field), False, f"effective_contract.boundary.{field}", "effective_contract"
        )


def _validate_owner_response(value: Any) -> None:
    response = _require_mapping(value, "owner_response", "owner_response")
    for field, expected in (
        ("artifact_id", OWNER_RESPONSE_ARTIFACT_ID),
        ("artifact_type", "kernel_m3_e_case_schema_contract_review_response"),
        ("version", "0.1"),
        ("owner", "Kernel/M3*"),
        ("status", OWNER_RESPONSE_STATUS),
        ("overall_decision", "accept"),
        ("overall_contract_decision", "accept_and_issue_new_effective_schema_and_contract"),
        ("source_identity_decision", "accept_exact_source_identity"),
    ):
        _require_constant(
            response.get(field), expected, f"owner_response.{field}", "owner_response"
        )
    schema = _require_mapping(
        response.get("effective_schema_identity"),
        "owner_response.effective_schema",
        "owner_response",
    )
    for field, expected in (
        ("artifact_id", EFFECTIVE_SCHEMA_ARTIFACT_ID),
        ("path", EFFECTIVE_SCHEMA_PATH),
        ("sha256", EFFECTIVE_SCHEMA_SHA256),
        ("status", EFFECTIVE_SCHEMA_STATUS),
        ("owner", "Kernel/M3*"),
        ("assisted_schema_sha256", ASSISTED_SCHEMA_SHA256),
    ):
        _require_constant(
            schema.get(field), expected, f"owner_response.schema.{field}", "owner_response"
        )
    contract = _require_mapping(
        response.get("effective_write_contract_identity"),
        "owner_response.effective_contract",
        "owner_response",
    )
    for field, expected in (
        ("artifact_id", EFFECTIVE_WRITE_CONTRACT_ARTIFACT_ID),
        ("path", EFFECTIVE_WRITE_CONTRACT_PATH),
        ("sha256", EFFECTIVE_WRITE_CONTRACT_SHA256),
        ("status", EFFECTIVE_WRITE_CONTRACT_STATUS),
        ("owner", "Kernel/M3*"),
        ("assisted_contract_sha256", ASSISTED_WRITE_CONTRACT_SHA256),
    ):
        _require_constant(
            contract.get(field), expected, f"owner_response.contract.{field}", "owner_response"
        )
    write = _require_mapping(
        response.get("write_authority"),
        "owner_response.write_authority",
        "owner_response",
    )
    for field in (
        "e_case_write_authorized",
        "executor_implementation_authorized",
        "activation_authorized",
    ):
        _require_constant(
            write.get(field), False, f"owner_response.write_authority.{field}", "owner_response"
        )


def _validate_source_record(value: Any) -> None:
    record = _require_mapping(value, "source_record", "source_record")
    for field, expected in (
        ("store_record_version", "kernel-claim-ir-intake-store-record-v0.1"),
        ("store_record_id", SOURCE_STORE_RECORD_ID),
        ("status", "stored_exact_ingested_claim_ir_under_single_execute_authority"),
        ("store_target_class", "kernel_claim_ir_intake_store"),
        ("store_target_id", SOURCE_STORE_TARGET_ID),
        ("is_kernel_store_record", True),
        ("is_e_case", False),
        ("surface_id", SURFACE_ID),
        ("package_id", PACKAGE_ID),
    ):
        _require_constant(record.get(field), expected, f"source_record.{field}", "source_record")
    package = _require_mapping(
        record.get("stored_claim_ir_package"), "source_record.package", "source_record"
    )
    for field, expected in (
        ("package_id", PACKAGE_ID),
        ("surface_id", SURFACE_ID),
        ("claim_id_state", "minted_opaque"),
        ("admission_state", "admitted_under_separate_authority"),
        ("kernel_state", "ingested_under_separate_authority"),
    ):
        _require_constant(package.get(field), expected, f"source_package.{field}", "source_record")
    claims = package.get("claims")
    if not isinstance(claims, list) or len(claims) != 41:
        raise ECaseWriteError("source_record", "source package must contain 41 claims")
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        claim_map = _require_mapping(claim, f"source_claim[{index}]", "source_record")
        claim_id = claim_map.get("claim_id")
        if not isinstance(claim_id, str) or not _CLAIM_ID_PATTERN.fullmatch(claim_id):
            raise ECaseWriteError("source_record", "source claim_id is invalid")
        if claim_id in seen:
            raise ECaseWriteError("source_record", "source claim_id is duplicated")
        seen.add(claim_id)
        _require_constant(
            claim_map.get("claim_id_state"), "minted_opaque", "source_claim.state", "source_record"
        )
        _require_constant(
            claim_map.get("admission_state"),
            "admitted_under_separate_authority",
            "source_claim.admission_state",
            "source_record",
        )
    manifest = _require_mapping(package.get("manifest"), "source_manifest", "source_record")
    _require_constant(manifest.get("claim_count"), 41, "source_manifest.claim_count", "source_record")
    _require_constant(
        manifest.get("content_hash"),
        "594c0ec4c4533b1fae76ce57579cf52c783e61fc6b191d9807ce9751e5d473f1",
        "source_manifest.content_hash",
        "source_record",
    )


def _validate_source_receipt(value: Any) -> None:
    receipt = _require_mapping(value, "source_receipt", "source_receipt")
    for field, expected in (
        ("store_receipt_version", "kernel-claim-ir-intake-store-receipt-v0.1"),
        ("store_receipt_id", "kcisrr_3a9a6174763f5b2ece6a3156fb665fff"),
        ("receipt_scope", "sanitized_versioned_kernel_claim_ir_intake_store_only"),
        ("decision", "stored_once_under_single_execute_authority"),
        ("store_target_id", SOURCE_STORE_TARGET_ID),
    ):
        _require_constant(receipt.get(field), expected, f"source_receipt.{field}", "source_receipt")
    side_effects = _require_mapping(
        receipt.get("side_effect_assertions"), "source_receipt.side_effects", "source_receipt"
    )
    _require_constant(
        side_effects.get("kernel_claim_ir_intake_store_write"),
        True,
        "source_receipt.side_effects.kernel_write",
        "source_receipt",
    )
    for field in (
        "e_case_write",
        "checker_or_promotion",
        "certificate_generation",
        "certified_stop",
        "production_registration",
        "claim_lifecycle_mutation",
        "si_llm_001_closure",
        "catalog_role_credit_l2_change",
        "m2_fit",
        "four_family_llm_finetune",
    ):
        _require_constant(
            side_effects.get(field), False, f"source_receipt.side_effects.{field}", "source_receipt"
        )


def _validate_activation(
    value: Any,
    *,
    repo_root: Path,
    executor_sha256: str,
) -> dict[str, Any]:
    activation = _require_mapping(value, "activation", "activation_shape")
    _reject_secret_keys(activation)
    if set(activation) != _EXPECTED_ACTIVATION_FIELDS:
        raise ECaseWriteError("activation_shape", "activation fields are not canonical")
    artifact_id = activation.get("artifact_id")
    if not isinstance(artifact_id, str) or not _ACTIVATION_ID_PATTERN.fullmatch(artifact_id):
        raise ECaseWriteError("activation_shape", "activation artifact id is invalid")
    for field, expected in (
        ("artifact_type", "production_e_case_single_execute_activation"),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", ACTIVATION_STATUS),
    ):
        _require_constant(activation.get(field), expected, f"activation.{field}", "not_activated")
    _require_exact_mapping(
        activation.get("authority_design"),
        _EXPECTED_AUTHORITY_DESIGN_REF,
        "activation.authority_design",
        "authority_design_pin",
    )
    _require_exact_mapping(
        activation.get("owner_approval"),
        _EXPECTED_OWNER_APPROVAL_REF,
        "activation.owner_approval",
        "owner_approval_pin",
    )
    _require_exact_mapping(
        activation.get("target"), _EXPECTED_TARGET, "activation.target", "activation_target"
    )
    pins = _require_mapping(activation.get("pinned_hashes"), "activation.pins", "activation_pin")
    schema_pin = pins.get("effective_e_case_schema_sha256")
    contract_pin = pins.get("effective_e_case_write_contract_sha256")
    if schema_pin in FORBIDDEN_NON_EFFECTIVE_SCHEMA_SHAS:
        raise ECaseWriteError("non_effective_schema_identity", "assisted schema SHA is not effective")
    if contract_pin in FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS:
        raise ECaseWriteError("non_effective_contract_identity", "assisted or packet SHA is not effective")
    expected_pins = dict(_EXPECTED_STATIC_PINS)
    expected_pins["e_case_write_executor_sha256"] = executor_sha256
    _require_exact_mapping(pins, expected_pins, "activation.pinned_hashes", "activation_pin")
    _require_exact_mapping(
        activation.get("selected_source"),
        _EXPECTED_SELECTED_SOURCE,
        "activation.selected_source",
        "selected_source",
    )
    _require_exact_mapping(
        activation.get("transaction_contract"),
        _EXPECTED_TRANSACTION_CONTRACT,
        "activation.transaction_contract",
        "transaction_contract",
    )
    _require_exact_mapping(
        activation.get("execute_ledger"),
        _EXPECTED_LEDGER_BEFORE,
        "activation.execute_ledger",
        "activation_ledger",
    )
    if activation.get("execution_audit") is not None:
        raise ECaseWriteError("activation_ledger", "activation already contains execution audit")
    _validate_output_policy(activation.get("output_policy"), repo_root)
    _require_exact_mapping(
        activation.get("still_blocked"),
        _EXPECTED_STILL_BLOCKED,
        "activation.still_blocked",
        "activation_boundary",
    )
    return copy.deepcopy(dict(activation))


def _validate_output_policy(value: Any, repo_root: Path) -> None:
    policy = _require_mapping(value, "activation.output_policy", "output_policy")
    if set(policy) != _EXPECTED_OUTPUT_POLICY_FIELDS:
        raise ECaseWriteError("output_policy", "output policy fields are not canonical")
    for field, expected in _EXPECTED_OUTPUT_POLICY_CONSTANTS.items():
        _require_constant(policy.get(field), expected, f"output_policy.{field}", "output_policy")
    record_path = _validate_output_path(policy.get("e_case_record_path"), repo_root)
    receipt_path = _validate_output_path(policy.get("sanitized_receipt_path"), repo_root)
    if record_path == receipt_path:
        raise ECaseWriteError("output_policy", "record and receipt paths must differ")


def _build_target_record(
    source: Mapping[str, Any],
    *,
    authority: Mapping[str, Any],
    activation_sha256: str,
    executor_sha256: str,
    transaction_id: str,
) -> dict[str, Any]:
    package = source["stored_claim_ir_package"]
    claims = package["claims"]
    return {
        "e_case_version": "e-case-record-v0.1",
        "e_case_id": E_CASE_ID,
        "record_scope": "opaque_claim_identity_provenance_only",
        "surface_id": SURFACE_ID,
        "package_id": PACKAGE_ID,
        "is_e_case": True,
        "is_kernel_store_record": False,
        "source_store": {
            "record_path": SOURCE_STORE_RECORD_PATH,
            "record_sha256": SOURCE_STORE_RECORD_SHA256,
            "receipt_path": SOURCE_STORE_RECEIPT_PATH,
            "receipt_sha256": SOURCE_STORE_RECEIPT_SHA256,
            "store_record_id": SOURCE_STORE_RECORD_ID,
            "store_target_id": SOURCE_STORE_TARGET_ID,
            "source_is_kernel_store_record": True,
            "source_is_e_case": False,
        },
        "source_package_state": {
            "claim_id_state": package["claim_id_state"],
            "admission_state": package["admission_state"],
            "kernel_state": package["kernel_state"],
            "claim_count": package["manifest"]["claim_count"],
            "claims_content_hash": package["manifest"]["content_hash"],
        },
        "claim_identity_refs": [
            {
                "claim_id": claim["claim_id"],
                "source_claim_index": index,
                "source_claim_id_state": claim["claim_id_state"],
                "source_admission_state": claim["admission_state"],
            }
            for index, claim in enumerate(claims)
        ],
        "provenance": {
            "effective_consumer_contract": {
                "artifact_id": EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
                "version": "0.1",
                "path": EFFECTIVE_CONSUMER_CONTRACT_PATH,
                "sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
                "status": EFFECTIVE_CONSUMER_CONTRACT_STATUS,
            },
            "effective_e_case_target_schema": {
                "artifact_id": EFFECTIVE_SCHEMA_ARTIFACT_ID,
                "version": EFFECTIVE_SCHEMA_VERSION,
                "path": EFFECTIVE_SCHEMA_PATH,
                "sha256": EFFECTIVE_SCHEMA_SHA256,
                "status": EFFECTIVE_SCHEMA_STATUS,
            },
            "effective_e_case_write_contract": {
                "artifact_id": EFFECTIVE_WRITE_CONTRACT_ARTIFACT_ID,
                "version": EFFECTIVE_WRITE_CONTRACT_VERSION,
                "path": EFFECTIVE_WRITE_CONTRACT_PATH,
                "sha256": EFFECTIVE_WRITE_CONTRACT_SHA256,
                "status": EFFECTIVE_WRITE_CONTRACT_STATUS,
            },
        },
        "write_authority": {
            "activation_artifact_id": authority["artifact_id"],
            "activation_path": ACTIVATION_PATH,
            "activation_sha256_before": activation_sha256,
            "executor_path": EXECUTOR_PATH,
            "executor_sha256": executor_sha256,
            "single_use": True,
        },
        "transaction": {
            "e_case_target_id": E_CASE_TARGET_ID,
            "transaction_id": transaction_id,
            "idempotency_key": IDEMPOTENCY_KEY,
            "atomic_all_or_nothing": True,
            "partial_write": False,
            "retry": False,
            "resume": False,
            "fallback": False,
        },
        "separation_assertions": {
            "source_store_record_unchanged": True,
            "source_store_record_is_e_case": False,
            "checker_decision_present": False,
            "promotion_performed": False,
            "certificate_generated": False,
            "certified_stop": False,
            "si_llm_001_closed": False,
            "l2_or_part_b_gate_passed": False,
        },
    }


def _build_sanitized_receipt(
    record: Mapping[str, Any],
    *,
    authority: Mapping[str, Any],
    activation_sha256: str,
    executor_sha256: str,
    transaction_id: str,
) -> dict[str, Any]:
    record_sha256 = _canonical_json_sha256(record)
    record_file_sha256 = hashlib.sha256(_pretty_json_bytes(record)).hexdigest()
    claim_ids = [item["claim_id"] for item in record["claim_identity_refs"]]
    claim_id_list_sha256 = hashlib.sha256(
        json.dumps(claim_ids, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    receipt_digest = hashlib.sha256(
        f"{record_sha256}\0{activation_sha256}\0{executor_sha256}".encode("utf-8")
    ).hexdigest()
    return {
        "e_case_receipt_version": "e-case-write-receipt-v0.1",
        "e_case_receipt_id": f"ecr_{receipt_digest[:32]}",
        "receipt_scope": "sanitized_versioned_e_case_write_only",
        "decision": "e_case_written_once_under_single_execute_authority",
        "effective_artifacts": {
            "schema": {
                "artifact_id": EFFECTIVE_SCHEMA_ARTIFACT_ID,
                "path": EFFECTIVE_SCHEMA_PATH,
                "sha256": EFFECTIVE_SCHEMA_SHA256,
                "status": EFFECTIVE_SCHEMA_STATUS,
            },
            "write_contract": {
                "artifact_id": EFFECTIVE_WRITE_CONTRACT_ARTIFACT_ID,
                "path": EFFECTIVE_WRITE_CONTRACT_PATH,
                "sha256": EFFECTIVE_WRITE_CONTRACT_SHA256,
                "status": EFFECTIVE_WRITE_CONTRACT_STATUS,
            },
            "owner_response": {
                "artifact_id": OWNER_RESPONSE_ARTIFACT_ID,
                "path": OWNER_RESPONSE_PATH,
                "sha256": OWNER_RESPONSE_SHA256,
                "status": OWNER_RESPONSE_STATUS,
            },
        },
        "source": {
            "record_path": SOURCE_STORE_RECORD_PATH,
            "record_sha256": SOURCE_STORE_RECORD_SHA256,
            "receipt_path": SOURCE_STORE_RECEIPT_PATH,
            "receipt_sha256": SOURCE_STORE_RECEIPT_SHA256,
            "surface_id": SURFACE_ID,
            "package_id": PACKAGE_ID,
            "claim_count": 41,
            "claims_content_hash": "594c0ec4c4533b1fae76ce57579cf52c783e61fc6b191d9807ce9751e5d473f1",
            "claim_id_list_sha256": claim_id_list_sha256,
        },
        "target": {
            "e_case_record_path": authority["output_policy"]["e_case_record_path"],
            "e_case_id": E_CASE_ID,
            "e_case_target_id": E_CASE_TARGET_ID,
            "record_canonical_sha256": record_sha256,
            "record_file_sha256": record_file_sha256,
            "is_e_case": True,
            "is_kernel_store_record": False,
        },
        "authority": {
            "activation_artifact_id": authority["artifact_id"],
            "activation_path": ACTIVATION_PATH,
            "activation_sha256_before": activation_sha256,
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "executor_path": EXECUTOR_PATH,
            "executor_sha256": executor_sha256,
        },
        "transaction": {
            "transaction_id": transaction_id,
            "idempotency_key": IDEMPOTENCY_KEY,
            "atomic_all_or_nothing": True,
            "partial_write": False,
            "retry": False,
            "resume": False,
            "fallback": False,
        },
        "ledger_before_and_after": {
            "before": copy.deepcopy(_EXPECTED_LEDGER_BEFORE),
            "after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
            "success_or_failure_exhausts_attempt": True,
        },
        "source_preservation": {
            "source_store_record_bytes_unchanged": True,
            "source_store_receipt_bytes_unchanged": True,
            "source_store_record_is_kernel_store_record_remains_true": True,
            "source_store_record_is_e_case_remains_false": True,
            "source_package_id_unchanged": True,
            "source_claim_ids_unchanged": True,
            "source_claim_order_unchanged": True,
            "source_claim_id_state_unchanged": True,
            "source_admission_state_unchanged": True,
            "source_kernel_state_unchanged": True,
            "source_claim_content_unchanged": True,
            "direct_rename_relabel_alias_or_in_place_conversion": False,
        },
        "side_effect_assertions": {
            "e_case_write": True,
            "source_store_write": False,
            "source_store_mutation_or_relabel": False,
            "kernel_store_reexecution": False,
            "checker_or_promotion": False,
            "certificate_generation": False,
            "certified_stop": False,
            "production_registration": False,
            "si_llm_001_closure": False,
            "catalog_role_credit_l2_change": False,
            "part_b_elevation": False,
            "m2_fit": False,
            "four_family_llm_finetune": False,
        },
    }


def _derive_transaction_id(activation_sha256: str) -> str:
    digest = hashlib.sha256(
        "\0".join(
            (
                EFFECTIVE_WRITE_CONTRACT_SHA256,
                SOURCE_STORE_RECORD_SHA256,
                E_CASE_TARGET_ID,
                activation_sha256,
            )
        ).encode("utf-8")
    ).hexdigest()
    return f"ecase_txn_{digest[:32]}"


def _assert_source_still_unchanged(
    repo_root: Path,
    record_bytes_before: bytes,
    receipt_bytes_before: bytes,
) -> None:
    if (repo_root / SOURCE_STORE_RECORD_PATH).read_bytes() != record_bytes_before:
        raise ECaseWriteError("source_mutation", "source store record changed during execution")
    if (repo_root / SOURCE_STORE_RECEIPT_PATH).read_bytes() != receipt_bytes_before:
        raise ECaseWriteError("source_mutation", "source store receipt changed during execution")


def _validate_target_state(
    repo_root: Path,
    *,
    record: Mapping[str, Any],
    receipt: Mapping[str, Any],
    output_policy: Mapping[str, Any],
) -> bool:
    record_path = repo_root / output_policy["e_case_record_path"]
    receipt_path = repo_root / output_policy["sanitized_receipt_path"]
    record_exists = record_path.exists()
    receipt_exists = receipt_path.exists()
    if record_exists != receipt_exists:
        raise ECaseWriteError("target_collision", "E_case target is partially occupied")
    if not record_exists:
        return True
    if _load_json(record_path) != record or _load_json(receipt_path) != receipt:
        raise ECaseWriteError("target_collision", "existing E_case target is not idempotently equivalent")
    return False


def _validate_output_path(value: Any, repo_root: Path) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ECaseWriteError("output_policy", "output path must use POSIX separators")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ECaseWriteError("output_policy", "output path must remain repository-relative")
    if not (
        value.startswith("docs/llm-editor/fixtures/e-case/")
        or value.startswith(".tmp/compiler-contract/e-case/")
    ):
        raise ECaseWriteError("output_policy", "output path is outside allowed E_case roots")
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ECaseWriteError("output_policy", "output path escapes repository") from exc
    return resolved


def _reject_secret_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().casefold().replace("-", "_").replace(" ", "_")
            if normalized in _SECRET_KEYS:
                raise ECaseWriteError("secret_in_activation", "activation contains a secret field")
            _reject_secret_keys(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            _reject_secret_keys(nested)


def _require_mapping(value: Any, field: str, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ECaseWriteError(code, f"{field} must be an object")
    return value


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    code: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise ECaseWriteError(code, f"{field} does not match the frozen shape")
    for key, expected_value in expected.items():
        actual = value.get(key)
        if actual != expected_value or type(actual) is not type(expected_value):
            raise ECaseWriteError(code, f"{field}.{key} does not match the frozen value")


def _require_constant(value: Any, expected: Any, field: str, code: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise ECaseWriteError(code, f"{field} does not match the frozen value")


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise ECaseWriteError("pin_missing", f"pinned file missing: {relative_path}")
    if _sha256(path) != expected_sha:
        raise ECaseWriteError("pin_mismatch", f"pinned SHA mismatch: {relative_path}")


def _read_bounded_bytes(path: Path, kind: str) -> bytes:
    try:
        data = path.read_bytes()
    except (OSError, TypeError) as exc:
        raise ECaseWriteError(f"{kind}_read", f"cannot read {kind}") from exc
    if not data or len(data) > _MAX_JSON_BYTES:
        raise ECaseWriteError(f"{kind}_read", f"{kind} size is invalid")
    return data


def _decode_json_bytes(data: bytes, kind: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateJSONKey) as exc:
        raise ECaseWriteError(f"{kind}_json", f"{kind} is not canonical JSON") from exc
    if not isinstance(value, dict):
        raise ECaseWriteError(f"{kind}_json", f"{kind} must be an object")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    return _decode_json_bytes(_read_bounded_bytes(path, "artifact"), "artifact")


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
        raise ECaseWriteError("pin_read", f"cannot read pinned artifact: {path.name}") from exc
    return digest.hexdigest()


def _canonical_json_sha256(value: Any) -> str:
    try:
        data = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ECaseWriteError("canonical_json", "artifact is not canonical JSON") from exc
    return hashlib.sha256(data).hexdigest()


def _pretty_json_bytes(value: Any) -> bytes:
    """Return the exact versioned-fixture serialization used by the wrapper."""

    try:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                sort_keys=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ECaseWriteError(
            "pretty_json", "artifact is not serializable JSON"
        ) from exc


# Public compatibility aliases; the L1 implementation calls only neutral helpers.
verify_e_case_write_pins = verify_write_pins
validate_e_case_source_bytes = validate_source_bytes
