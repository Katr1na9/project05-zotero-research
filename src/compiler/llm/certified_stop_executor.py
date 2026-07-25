"""Fail-closed, single-use production CERTIFIED_STOP write executor.

The executor verifies the exact Kernel/Checker effective schema and issue/write
contract, the accepted owner response, and the immutable certificate source chain.
It constructs one independently typed, provenance-only CERTIFIED_STOP record and a
sanitized receipt in memory.  A separately authorized wrapper is responsible
for atomically persisting those artifacts and exhausting the activation.

This module does not invoke Checker, mutate certificate or Kernel intake records,
perform CERTIFIED_STOP, close SI-LLM-001, or change L2 / Part B state.
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


AUTHORITY_BASE_COMMIT = "be965705f5b02392c435c44d59db3e4c9032f4d7"
AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-production-certified-stop-single-execute-"
    "authority-design-v0.1-20260725.json"
)
AUTHORITY_DESIGN_SHA256 = (
    "45260e4552c570307277262bd5701987289584e9f8e021b0c7439664bc2bcc67"
)
AUTHORITY_DESIGN_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-production-certified-stop-single-execute-authority-"
    "design-v0.1-20260725"
)
AUTHORITY_DESIGN_STATUS = (
    "design_only_production_certified_stop_authority_not_activated"
)

EFFECTIVE_SCHEMA_PATH = "schemas/certified-stop-record-effective-v0.1.schema.json"
EFFECTIVE_SCHEMA_SHA256 = (
    "80a63e23b61914a42d9a6e9fc954b210f5321c263a18844a2bcb82c6c1acbd2c"
)
EFFECTIVE_SCHEMA_ARTIFACT_ID = "certified-stop-record-effective-v0.1"
EFFECTIVE_SCHEMA_VERSION = "0.1"
EFFECTIVE_SCHEMA_ID = (
    "https://project05.invalid/schemas/certified-stop-record-effective-v0.1.schema.json"
)
EFFECTIVE_SCHEMA_STATUS = (
    "effective_certified_stop_target_schema_semantics_only_execution_not_authorized"
)

EFFECTIVE_ISSUE_CONTRACT_PATH = (
    "docs/kernel/kernel-v0.8-certified-stop-write-contract-effective-"
    "v0.1-20260725.json"
)
EFFECTIVE_ISSUE_CONTRACT_SHA256 = (
    "75073ab3edbf849cfaf10c799fec53e5ad0084a6b5228283781c4295a67c79cd"
)
EFFECTIVE_ISSUE_CONTRACT_ARTIFACT_ID = (
    "kernel-v0.8-certified-stop-write-contract-effective-v0.1-20260725"
)
EFFECTIVE_ISSUE_CONTRACT_VERSION = "0.1"
EFFECTIVE_ISSUE_CONTRACT_STATUS = (
    "effective_certified_stop_write_contract_semantics_only_execution_not_authorized"
)

OWNER_RESPONSE_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-checker-owner-certified-stop-"
    "schema-contract-review-response-v0.1-20260725.json"
)
OWNER_RESPONSE_SHA256 = (
    "32e8b22de5352c988a3f8fbcd9bfc5f48abe12daa1f0bcf1ee93d9c7f9a1a0ca"
)
OWNER_RESPONSE_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-kernel-checker-owner-certified-stop-schema-contract-"
    "review-response-v0.1-20260725"
)
OWNER_RESPONSE_STATUS = (
    "accept_and_issue_new_effective_schema_and_contract_execution_still_blocked"
)

SOURCE_RECORD_PATH = (
    "docs/llm-editor/fixtures/certificate/project05-depth2-public-v0.1/"
    "certificate-record.json"
)
SOURCE_RECORD_SHA256 = (
    "a7cead6c0315ede6859000db63990f8148c258c2350fba0e99d368ca4a4fa40c"
)
SOURCE_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/certificate/project05-depth2-public-v0.1/"
    "sanitized-receipt.json"
)
SOURCE_RECEIPT_SHA256 = (
    "b1190082b3879fe070eb816c1684354783fcc4b6a0773176b29659e2822f5f64"
)
SOURCE_ID = "cert_2d016caab300bc0a25cd7d973a2ba3d0116dcb74277bc45f0d5ed6b1ef7efd00"

EFFECTIVE_SOURCE_SCHEMA_PATH = "schemas/certificate-record-effective-v0.1.schema.json"
EFFECTIVE_SOURCE_SCHEMA_SHA256 = (
    "a29f5a13944242076973c1d735f33cf82d7e7665c622b4c3e8ac52434d72677d"
)
EFFECTIVE_SOURCE_SCHEMA_ARTIFACT_ID = "certificate-record-effective-v0.1"
EFFECTIVE_SOURCE_SCHEMA_STATUS = "effective_certificate_target_schema_semantics_only_issue_not_authorized"
EFFECTIVE_SOURCE_CONTRACT_PATH = (
    "docs/kernel/kernel-v0.8-certificate-issue-write-contract-effective-v0.1-20260725.json"
)
EFFECTIVE_SOURCE_CONTRACT_SHA256 = (
    "fccfbb9066e3cc0ef2abaff775f34b36c512bc1d13ca23dca675d32f622793dc"
)
EFFECTIVE_SOURCE_CONTRACT_ARTIFACT_ID = (
    "kernel-v0.8-certificate-issue-write-contract-effective-v0.1-20260725"
)
EFFECTIVE_SOURCE_CONTRACT_STATUS = (
    "effective_certificate_issue_write_contract_semantics_only_issue_not_authorized"
)
EXHAUSTED_SOURCE_ACTIVATION_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-production-certificate-single-execute-"
    "activation-v0.1-20260725.json"
)
EXHAUSTED_SOURCE_ACTIVATION_SHA256 = (
    "4800885e72bd9310cbe711b5d01ebfd1912b17636de97cc20b68762c93fad643"
)

EFFECTIVE_CONSUMER_CONTRACT_PATH = (
    "docs/kernel/kernel-v0.8-shared-claim-ir-consumer-contract-effective-"
    "v0.1-20260725.json"
)
EFFECTIVE_CONSUMER_CONTRACT_SHA256 = (
    "a2a176fdeb2b93205a7f5e11c7c096236e2dc582d1c31f8f4a1534866c008d63"
)
EXTERNAL_SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
EXTERNAL_SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
RUN_MVP_PATH = "09-experiments/scripts/run_mvp.py"
RUN_MVP_SHA256 = (
    "0ffb60b2864d8aa35ba7d96ca2667413846c1d6c1c5021f19f7b8a5c9a801d76"
)
KERNEL_SCHEMA_PATH = "schemas/claim-ir-kernel.schema.json"
KERNEL_SCHEMA_SHA256 = (
    "7c6fa2db0b75d69340be5a8843ba0c373e2d5b25b0d37cf8f1d1c416a787865d"
)

ASSISTED_SCHEMA_SHA256 = (
    "238401cd1744864fcb56e2833317922a530a804e4e9ed9469e9b6dffc2254ac8"
)
ASSISTED_CONTRACT_SHA256 = (
    "26ebbef491dd4b17d29c1e75c8626252a2ea09ae234cc3a573faef445c976e2e"
)
CERTIFICATE_SCHEMA_SHA256 = (
    "a29f5a13944242076973c1d735f33cf82d7e7665c622b4c3e8ac52434d72677d"
)
INVENTORY_SCHEMA_SHA256 = (
    "abd394cb950b350c9fbc4a13f6aca5243e59d6ade3a47ef37bde9be4d5b5bfba"
)
PART_B_STOP_DENY_SCHEMA_SHA256S = frozenset(
    {
        "ee9ee762e6fea347b55221c5c3cbabb43aede8a0e00d4f4fd8fce13cb4089dea",
        "ed4e8b1fcaecde0b3c8fb41668ac1b8a4125d0144481d1e51fce8cc2b86872e4",
        "436b4780ab234011610c1c94f39c3853b8f16409ef3da2054efba2892a865620",
    }
)
FORBIDDEN_NON_EFFECTIVE_SCHEMA_SHAS = frozenset(
    {
        ASSISTED_SCHEMA_SHA256,
        CERTIFICATE_SCHEMA_SHA256,
        INVENTORY_SCHEMA_SHA256,
        *PART_B_STOP_DENY_SCHEMA_SHA256S,
    }
)
FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS = frozenset({ASSISTED_CONTRACT_SHA256})

EXECUTOR_PATH = "src/compiler/llm/certified_stop_executor.py"
ACTIVATION_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-production-certified-stop-single-"
    "execute-activation-v0.1-20260725.json"
)
ACTIVATION_STATUS = "activated_single_production_certified_stop_execute_authorized"
SURFACE_ID = "project05_depth2_public"
SOURCE_CLASS = "planner_experiment_inputs"
ADAPTER_ID = "m1a_planner_inputs_v0_1"
PACKAGE_ID = "pkg_73d77b55ef6a517a0dc528f7f3a89bd9"
CLAIM_COUNT = 41
CLAIMS_CONTENT_HASH = (
    "594c0ec4c4533b1fae76ce57579cf52c783e61fc6b191d9807ce9751e5d473f1"
)
CLAIM_ID_LIST_SHA256 = (
    "11ef0f4672d9f43357639e46c19b27474ddcdf40daffb9acb93af9c810d008a4"
)
CERTIFIED_STOP_SCOPE = (
    "terminal_declaration_of_exact_provenance_certificate_identity_only_not_"
    "checker_acceptance_not_evidence_sufficiency_not_run_mvp_ordinary_stop"
)
RECORD_SCOPE = "source_certificate_identity_terminal_declaration_only"
CERTIFIED_STOP_TARGET_ID = (
    "certified-stop:project05_depth2_public:"
    "pkg_73d77b55ef6a517a0dc528f7f3a89bd9:v0.1"
)
CERTIFIED_STOP_RECORD_PATH = (
    "docs/llm-editor/fixtures/certified-stop/project05-depth2-public-v0.1/"
    "certified-stop-record.json"
)
CERTIFIED_STOP_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/certified-stop/project05-depth2-public-v0.1/"
    "sanitized-receipt.json"
)

_CERTIFIED_STOP_ID_DIGEST = hashlib.sha256(
    "\0".join(
        (EFFECTIVE_ISSUE_CONTRACT_SHA256, SOURCE_RECORD_SHA256, CERTIFIED_STOP_TARGET_ID)
    ).encode("utf-8")
).hexdigest()
CERTIFIED_STOP_ID = f"cstop_{_CERTIFIED_STOP_ID_DIGEST}"
_IDEMPOTENCY_DIGEST = hashlib.sha256(
    "\0".join(
        (
            EFFECTIVE_ISSUE_CONTRACT_SHA256,
            EFFECTIVE_SCHEMA_SHA256,
            SOURCE_RECORD_SHA256,
            SOURCE_RECEIPT_SHA256,
            CERTIFIED_STOP_TARGET_ID,
        )
    ).encode("utf-8")
).hexdigest()
IDEMPOTENCY_KEY = f"cstop_idem_{_IDEMPOTENCY_DIGEST}"

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
    "owner": "Kernel/Checker",
    "overall_decision": "accept",
    "certified_stop_execution_authorized_by_response": False,
    "checker_invocation_authorized_by_response": False,
    "evidence_sufficiency_assertion_authorized_by_response": False,
}
_EXPECTED_TARGET = {
    "surface_id": SURFACE_ID,
    "source_class": SOURCE_CLASS,
    "adapter_id": ADAPTER_ID,
    "package_id": PACKAGE_ID,
    "source_record_class": "certificate",
    "target_record_class": "certified_stop",
    "certified_stop_target_id": CERTIFIED_STOP_TARGET_ID,
    "certified_stop_scope": CERTIFIED_STOP_SCOPE,
    "operation": "construct_and_write_one_separately_typed_certified_stop_record",
    "checker_decision_ref": None,
    "evidence_sufficiency_ref": None,
    "ordinary_run_mvp_stop_action_id": "STOP",
    "ordinary_run_mvp_stop_is_certified_stop": False,
}
_EXPECTED_STATIC_PINS = {
    "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
    "owner_response_sha256": OWNER_RESPONSE_SHA256,
    "effective_certified_stop_schema_sha256": EFFECTIVE_SCHEMA_SHA256,
    "effective_certified_stop_write_contract_sha256": EFFECTIVE_ISSUE_CONTRACT_SHA256,
    "source_certificate_record_sha256": SOURCE_RECORD_SHA256,
    "source_certificate_receipt_sha256": SOURCE_RECEIPT_SHA256,
    "effective_certificate_schema_sha256": EFFECTIVE_SOURCE_SCHEMA_SHA256,
    "effective_certificate_issue_write_contract_sha256": EFFECTIVE_SOURCE_CONTRACT_SHA256,
    "exhausted_certificate_activation_sha256": EXHAUSTED_SOURCE_ACTIVATION_SHA256,
    "effective_consumer_contract_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    "external_envelope_schema_sha256": EXTERNAL_SCHEMA_SHA256,
    "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
    "ordinary_run_mvp_sha256": RUN_MVP_SHA256,
}
_EXPECTED_SELECTED_SOURCE = {
    "certificate_record": {
        "path": SOURCE_RECORD_PATH,
        "sha256": SOURCE_RECORD_SHA256,
        "certificate_id": SOURCE_ID,
        "package_id": PACKAGE_ID,
        "surface_id": SURFACE_ID,
        "is_certificate": True,
        "is_e_case": False,
        "is_kernel_store_record": False,
        "is_certified_stop": False,
    },
    "sanitized_certificate_receipt": {
        "path": SOURCE_RECEIPT_PATH,
        "sha256": SOURCE_RECEIPT_SHA256,
    },
}
_EXPECTED_TRANSACTION_CONTRACT = {
    "certified_stop_target_id": CERTIFIED_STOP_TARGET_ID,
    "idempotency_key": IDEMPOTENCY_KEY,
    "transaction_id_derivation": (
        "cstop_txn_ + first_32_hex(sha256(effective_contract_sha256 NUL "
        "source_certificate_sha256 NUL certified_stop_target_id NUL activation_sha256_before))"
    ),
    "atomic_all_or_nothing": True,
    "target_empty_or_idempotently_equivalent_required": True,
    "partial_write": False,
}
_EXPECTED_OUTPUT_POLICY_CONSTANTS = {
    "mode": "versioned_certified_stop_record_and_sanitized_receipt",
    "file_write": True,
    "certified_stop_execution": True,
    "certified_stop_write": True,
    "new_separately_typed_target": True,
    "source_certificate_write_or_mutation": False,
    "source_e_case_write_or_mutation": False,
    "kernel_store_write_or_mutation": False,
    "ordinary_run_mvp_stop_action_change": False,
    "checker_invocation": False,
    "checker_acceptance_or_promotion": False,
    "evidence_sufficiency_assertion": False,
    "si_llm_001_closure": False,
    "l2_or_part_b_change": False,
}
_EXPECTED_OUTPUT_POLICY_FIELDS = frozenset(
    {*_EXPECTED_OUTPUT_POLICY_CONSTANTS, "certified_stop_record_path", "sanitized_receipt_path"}
)
_EXPECTED_STILL_BLOCKED = {
    "second_certified_stop_execute": True,
    "checker_invocation": True,
    "checker_acceptance_or_promotion": True,
    "evidence_sufficiency_assertion": True,
    "ordinary_run_mvp_stop_action_change": True,
    "source_certificate_write_or_mutation": True,
    "source_e_case_write_or_mutation": True,
    "kernel_store_write_or_mutation": True,
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
    {"secret", "secret_key", "key_material", "hmac_key", "password", "credential", "private_key", "token"}
)
_MAX_JSON_BYTES = 4 * 1024 * 1024


class CertifiedStopError(ValueError):
    """Raised when any certified_stop issue gate fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class _DuplicateJSONKey(ValueError):
    pass


def verify_issue_pins(repo_root: Path) -> None:
    """Verify every immutable design, owner, effective, source, and STOP pin."""

    root = repo_root.resolve()
    for relative_path, expected_sha in (
        (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
        (EFFECTIVE_SCHEMA_PATH, EFFECTIVE_SCHEMA_SHA256),
        (EFFECTIVE_ISSUE_CONTRACT_PATH, EFFECTIVE_ISSUE_CONTRACT_SHA256),
        (OWNER_RESPONSE_PATH, OWNER_RESPONSE_SHA256),
        (SOURCE_RECORD_PATH, SOURCE_RECORD_SHA256),
        (SOURCE_RECEIPT_PATH, SOURCE_RECEIPT_SHA256),
        (EFFECTIVE_SOURCE_SCHEMA_PATH, EFFECTIVE_SOURCE_SCHEMA_SHA256),
        (EFFECTIVE_SOURCE_CONTRACT_PATH, EFFECTIVE_SOURCE_CONTRACT_SHA256),
        (EXHAUSTED_SOURCE_ACTIVATION_PATH, EXHAUSTED_SOURCE_ACTIVATION_SHA256),
        (EFFECTIVE_CONSUMER_CONTRACT_PATH, EFFECTIVE_CONSUMER_CONTRACT_SHA256),
        (EXTERNAL_SCHEMA_PATH, EXTERNAL_SCHEMA_SHA256),
        (KERNEL_SCHEMA_PATH, KERNEL_SCHEMA_SHA256),
        (RUN_MVP_PATH, RUN_MVP_SHA256),
        ("schemas/part-b-claims-stop-deny-policy.schema.json", "ee9ee762e6fea347b55221c5c3cbabb43aede8a0e00d4f4fd8fce13cb4089dea"),
        ("schemas/part-b-claims-stop-deny-manifest.schema.json", "ed4e8b1fcaecde0b3c8fb41668ac1b8a4125d0144481d1e51fce8cc2b86872e4"),
        ("schemas/part-b-claims-stop-deny-record.schema.json", "436b4780ab234011610c1c94f39c3853b8f16409ef3da2054efba2892a865620"),
    ):
        _verify_pin(root, relative_path, expected_sha)

    _validate_authority_design(_load_json(root / AUTHORITY_DESIGN_PATH))
    target_schema = _load_json(root / EFFECTIVE_SCHEMA_PATH)
    _validate_effective_schema(target_schema)
    _validate_effective_contract(_load_json(root / EFFECTIVE_ISSUE_CONTRACT_PATH))
    _validate_owner_response(_load_json(root / OWNER_RESPONSE_PATH))
    source_activation = _load_json(root / EXHAUSTED_SOURCE_ACTIVATION_PATH)
    _require_exact_mapping(
        source_activation.get("execute_ledger"),
        _EXPECTED_LEDGER_AFTER,
        "source_activation.execute_ledger",
        "source_activation",
    )
    audit = _require_mapping(
        source_activation.get("execution_audit"),
        "source_activation.execution_audit",
        "source_activation",
    )
    _require_constant(audit.get("executor_invocation_count"), 1, "source_activation.invocation_count", "source_activation")
    source_schema = _load_json(root / EFFECTIVE_SOURCE_SCHEMA_PATH)
    validate_source_bytes(
        (root / SOURCE_RECORD_PATH).read_bytes(),
        (root / SOURCE_RECEIPT_PATH).read_bytes(),
        source_schema=source_schema,
        target_schema=target_schema,
    )

def validate_source_bytes(
    source_record_bytes: bytes,
    source_receipt_bytes: bytes,
    *,
    source_schema: Mapping[str, Any] | None = None,
    target_schema: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate exact immutable source bytes and return the decoded record."""

    if hashlib.sha256(source_record_bytes).hexdigest() != SOURCE_RECORD_SHA256:
        raise CertifiedStopError("source_record_pin", "source certificate record bytes changed")
    if hashlib.sha256(source_receipt_bytes).hexdigest() != SOURCE_RECEIPT_SHA256:
        raise CertifiedStopError("source_receipt_pin", "source certificate receipt bytes changed")
    record = _decode_json_bytes(source_record_bytes, "source_record")
    receipt = _decode_json_bytes(source_receipt_bytes, "source_receipt")
    _validate_source_record(record)
    _validate_source_receipt(receipt)
    if source_schema is not None:
        errors = sorted(
            Draft202012Validator(dict(source_schema)).iter_errors(record),
            key=lambda error: list(error.path),
        )
        if errors:
            raise CertifiedStopError("source_schema", errors[0].message)
    if target_schema is not None and not list(
        Draft202012Validator(dict(target_schema)).iter_errors(record)
    ):
        raise CertifiedStopError(
            "source_type_separation", "source record must not validate as a certified_stop"
        )
    return record


def execute_certified_stop(
    *,
    repo_root: Path,
    activation_path: Path | None = None,
    source_record_bytes: bytes | None = None,
    source_receipt_bytes: bytes | None = None,
    checker_decision_ref: Any = None,
    evidence_sufficiency_ref: Any = None,
    ordinary_run_mvp_stop: bool = False,
) -> dict[str, Any]:
    """Construct one CERTIFIED_STOP record in memory under a single-use activation."""

    if activation_path is None:
        raise CertifiedStopError(
            "missing_activation", "a distinct activated single-use CERTIFIED_STOP authority is required"
        )
    if checker_decision_ref is not None:
        raise CertifiedStopError(
            "non_null_checker_decision_ref",
            "the effective owner policy permits only null checker_decision_ref",
        )
    if evidence_sufficiency_ref is not None:
        raise CertifiedStopError(
            "non_null_evidence_sufficiency_ref",
            "the effective owner policy permits only null evidence_sufficiency_ref",
        )
    if ordinary_run_mvp_stop is not False:
        raise CertifiedStopError(
            "ordinary_stop_confusion",
            "ordinary run_mvp STOP cannot be reinterpreted as CERTIFIED_STOP",
        )
    root = repo_root.resolve()
    verify_issue_pins(root)
    activation_bytes = _read_bounded_bytes(Path(activation_path), "activation")
    activation = _decode_json_bytes(activation_bytes, "activation")
    activation_sha256 = hashlib.sha256(activation_bytes).hexdigest()
    executor_sha256 = _sha256(root / EXECUTOR_PATH)
    authority = _validate_activation(
        activation,
        repo_root=root,
        executor_sha256=executor_sha256,
    )

    frozen_record_bytes = (root / SOURCE_RECORD_PATH).read_bytes()
    frozen_receipt_bytes = (root / SOURCE_RECEIPT_PATH).read_bytes()
    record_bytes = frozen_record_bytes if source_record_bytes is None else source_record_bytes
    receipt_bytes = frozen_receipt_bytes if source_receipt_bytes is None else source_receipt_bytes
    source_schema = _load_json(root / EFFECTIVE_SOURCE_SCHEMA_PATH)
    target_schema = _load_json(root / EFFECTIVE_SCHEMA_PATH)
    source = validate_source_bytes(
        record_bytes,
        receipt_bytes,
        source_schema=source_schema,
        target_schema=target_schema,
    )
    transaction_id = _derive_transaction_id(activation_sha256)
    target = _build_target_record(
        source,
        authority=authority,
        activation_sha256=activation_sha256,
        executor_sha256=executor_sha256,
        transaction_id=transaction_id,
    )
    _validate_target_record(target, target_schema)
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
        "certified_stop_record": target,
        "sanitized_receipt": receipt,
        "activation_sha256_before": activation_sha256,
        "execute_ledger_after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
        "write_required": write_required,
    }

def _validate_authority_design(value: Any) -> None:
    design = _require_mapping(value, "authority_design", "authority_design")
    for field, expected in (
        ("artifact_id", AUTHORITY_DESIGN_ARTIFACT_ID),
        ("artifact_type", "production_certified_stop_single_execute_authority_design"),
        ("version", "0.1"),
        ("status", AUTHORITY_DESIGN_STATUS),
    ):
        _require_constant(design.get(field), expected, f"authority_design.{field}", "authority_design")
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
        ("certified_stop_execution_authorized", False),
        ("certified_stop_executed", False),
        ("certified_stop_record_written", False),
        ("checker_invocation_authorized", False),
        ("checker_acceptance_or_promotion_authorized", False),
        ("evidence_sufficiency_assertion_authorized", False),
        ("ordinary_planner_stop_action_change_authorized", False),
    ):
        _require_constant(current.get(field), expected, f"authority_design.current.{field}", "authority_design")
    future = _require_mapping(
        design.get("future_activation_shape"),
        "authority_design.future_activation_shape",
        "authority_design",
    )
    _require_constant(future.get("status"), ACTIVATION_STATUS, "authority_design.future.status", "authority_design")
    _require_exact_mapping(
        future.get("execute_ledger"),
        _EXPECTED_LEDGER_BEFORE,
        "authority_design.future.execute_ledger",
        "authority_design",
    )
    for field, expected in (
        ("activation_must_be_distinct_artifact", True),
        ("activation_must_not_reuse_exhausted_certificate_activation", True),
        ("activation_must_not_modify_run_mvp_stop_action", True),
        ("certified_stop_authorized_now_by_this_design", False),
    ):
        _require_constant(future.get(field), expected, f"authority_design.future.{field}", "authority_design")

def _validate_effective_schema(value: Any) -> None:
    schema = _require_mapping(value, "effective_schema", "effective_schema")
    for field, expected in (
        ("$id", EFFECTIVE_SCHEMA_ID),
        ("type", "object"),
        ("additionalProperties", False),
    ):
        _require_constant(schema.get(field), expected, f"effective_schema.{field}", "effective_schema")
    metadata = _require_mapping(
        schema.get("x-project05-artifact"), "effective_schema.metadata", "effective_schema"
    )
    for field, expected in (
        ("artifact_id", EFFECTIVE_SCHEMA_ARTIFACT_ID),
        ("version", EFFECTIVE_SCHEMA_VERSION),
        ("status", EFFECTIVE_SCHEMA_STATUS),
        ("owner", "Kernel/Checker"),
        ("effective", True),
        ("certificate_schema_is_certified_stop_schema", False),
        ("ordinary_run_mvp_stop_is_certified_stop", False),
        ("certificate_is_certified_stop", False),
    ):
        _require_constant(metadata.get(field), expected, f"effective_schema.metadata.{field}", "effective_schema")
    properties = _require_mapping(schema.get("properties"), "effective_schema.properties", "effective_schema")
    for name, expected in (
        ("is_certified_stop", True),
        ("is_certificate", False),
        ("is_e_case", False),
        ("is_kernel_store_record", False),
        ("is_ordinary_run_mvp_stop", False),
        ("record_scope", RECORD_SCOPE),
    ):
        _require_constant(
            _require_mapping(properties.get(name), f"schema.{name}", "effective_schema").get("const"),
            expected,
            f"schema.{name}.const",
            "effective_schema",
        )
    for name in ("checker_decision_ref", "evidence_sufficiency_ref"):
        _require_constant(
            _require_mapping(properties.get(name), f"schema.{name}", "effective_schema").get("type"),
            "null",
            f"schema.{name}.type",
            "effective_schema",
        )
    prohibited = schema.get("x-project05-prohibited-top-level-fields")
    if not isinstance(prohibited, list) or not {
        "checker_decision",
        "checker_accepted",
        "promotion",
        "evidence_sufficiency",
        "evidence_sufficiency_passed",
        "stop_recommendation",
        "si_llm_001_closed",
        "l2_passed",
        "part_b_elevated",
    }.issubset(set(prohibited)):
        raise CertifiedStopError("effective_schema", "schema prohibition list is incomplete")
    try:
        Draft202012Validator.check_schema(dict(schema))
    except Exception as exc:  # pragma: no cover
        raise CertifiedStopError("effective_schema", "effective schema is invalid") from exc

def _validate_effective_contract(value: Any) -> None:
    contract = _require_mapping(value, "effective_contract", "effective_contract")
    for field, expected in (
        ("artifact_id", EFFECTIVE_ISSUE_CONTRACT_ARTIFACT_ID),
        ("artifact_type", "kernel_checker_certified_stop_write_contract_effective"),
        ("version", EFFECTIVE_ISSUE_CONTRACT_VERSION),
        ("owner", "Kernel/Checker"),
        ("status", EFFECTIVE_ISSUE_CONTRACT_STATUS),
    ):
        _require_constant(contract.get(field), expected, f"effective_contract.{field}", "effective_contract")
    accepted_schema = _require_mapping(
        contract.get("accepted_effective_certified_stop_schema"),
        "effective_contract.accepted_schema",
        "effective_contract",
    )
    for field, expected in (
        ("artifact_id", EFFECTIVE_SCHEMA_ARTIFACT_ID),
        ("path", EFFECTIVE_SCHEMA_PATH),
        ("content_sha256", EFFECTIVE_SCHEMA_SHA256),
        ("status", EFFECTIVE_SCHEMA_STATUS),
        ("owner", "Kernel/Checker"),
        ("part_b_stop_deny_schemas_are_effective_pin", False),
    ):
        _require_constant(accepted_schema.get(field), expected, f"effective_contract.schema.{field}", "effective_contract")
    source = _require_mapping(contract.get("accepted_source_identity"), "effective_contract.source", "effective_contract")
    for field, expected in (
        ("source_record_path", SOURCE_RECORD_PATH),
        ("source_record_sha256", SOURCE_RECORD_SHA256),
        ("source_receipt_path", SOURCE_RECEIPT_PATH),
        ("source_receipt_sha256", SOURCE_RECEIPT_SHA256),
        ("certificate_id", SOURCE_ID),
        ("claim_id_list_sha256", CLAIM_ID_LIST_SHA256),
        ("source_record_must_have_is_certificate_true", True),
        ("source_record_must_have_is_e_case_false", True),
        ("source_record_must_have_is_kernel_store_record_false", True),
        ("source_record_may_be_mutated", False),
        ("source_receipt_may_be_mutated", False),
        ("certificate_presence_implies_certified_stop", False),
    ):
        _require_constant(source.get(field), expected, f"effective_contract.source.{field}", "effective_contract")
    semantics = _require_mapping(
        contract.get("certified_stop_scope_and_terminal_semantics"),
        "effective_contract.scope",
        "effective_contract",
    )
    for field, expected in (
        ("certified_stop_scope", CERTIFIED_STOP_SCOPE),
        ("record_scope", RECORD_SCOPE),
        ("subject_kind", "provenance_certificate"),
        ("certificate_presence_defaults_to_certified_stop", False),
        ("certificate_presence_defaults_to_checker_acceptance", False),
        ("certificate_presence_defaults_to_checker_promotion", False),
        ("certificate_presence_defaults_to_evidence_sufficiency", False),
        ("ordinary_run_mvp_stop_defaults_to_certified_stop", False),
    ):
        _require_constant(semantics.get(field), expected, f"effective_contract.scope.{field}", "effective_contract")
    policy = _require_mapping(
        contract.get("checker_and_sufficiency_input_policy"),
        "effective_contract.decision_policy",
        "effective_contract",
    )
    for field, expected in (
        ("allowed_form_under_this_scope", "null_only"),
        ("checker_decision_ref_value", None),
        ("evidence_sufficiency_ref_value", None),
        ("non_null_checker_decision_ref_rejected_fail_closed", True),
        ("non_null_evidence_sufficiency_ref_rejected_fail_closed", True),
        ("certified_stop_writer_may_invoke_checker", False),
        ("certified_stop_writer_may_assert_evidence_sufficiency", False),
        ("this_policy_authorizes_checker_invocation", False),
        ("this_policy_authorizes_evidence_sufficiency_assertion", False),
    ):
        _require_constant(policy.get(field), expected, f"effective_contract.policy.{field}", "effective_contract")
    mapping = _require_mapping(contract.get("source_to_certified_stop_mapping"), "effective_contract.mapping", "effective_contract")
    for field, expected in (
        ("target_must_be_new_separately_typed_object", True),
        ("claim_identity_only", True),
        ("claim_values_copied_to_certified_stop", False),
        ("silent_schema_authority_checker_sufficiency_or_stop_escalation", False),
        ("certified_stop_scope_value", CERTIFIED_STOP_SCOPE),
        ("record_scope_value", RECORD_SCOPE),
        ("claim_id_list_sha256_value", CLAIM_ID_LIST_SHA256),
        ("checker_decision_ref_value", None),
        ("evidence_sufficiency_ref_value", None),
    ):
        _require_constant(mapping.get(field), expected, f"effective_contract.mapping.{field}", "effective_contract")
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
    ):
        _require_constant(transaction.get(field), expected, f"effective_contract.transaction.{field}", "effective_contract")
    execution = _require_mapping(
        contract.get("execution_authorization_state"),
        "effective_contract.execution_authorization_state",
        "effective_contract",
    )
    for field, expected in (
        ("effective_schema_issued", True),
        ("effective_write_contract_issued", True),
        ("executor_implementation_authorized", False),
        ("activation_authorized", False),
        ("certified_stop_execution_authorized", False),
        ("checker_invocation_authorized", False),
        ("checker_acceptance_or_promotion_authorized", False),
        ("evidence_sufficiency_assertion_authorized", False),
        ("run_mvp_stop_action_change_authorized", False),
        ("separate_executor_review_and_single_use_activation_required", True),
    ):
        _require_constant(execution.get(field), expected, f"effective_contract.execution.{field}", "effective_contract")

def _validate_owner_response(value: Any) -> None:
    response = _require_mapping(value, "owner_response", "owner_response")
    for field, expected in (
        ("artifact_id", OWNER_RESPONSE_ARTIFACT_ID),
        ("artifact_type", "kernel_checker_owner_certified_stop_schema_contract_review_response_and_approval_record"),
        ("version", "0.1"),
        ("owner", "Kernel/Checker"),
        ("status", OWNER_RESPONSE_STATUS),
        ("overall_decision", "accept"),
    ):
        _require_constant(response.get(field), expected, f"owner_response.{field}", "owner_response")
    schema = _require_mapping(response.get("effective_certified_stop_schema_identity"), "owner_response.schema", "owner_response")
    for field, expected in (
        ("artifact_id", EFFECTIVE_SCHEMA_ARTIFACT_ID),
        ("path", EFFECTIVE_SCHEMA_PATH),
        ("sha256", EFFECTIVE_SCHEMA_SHA256),
        ("status", EFFECTIVE_SCHEMA_STATUS),
        ("owner", "Kernel/Checker"),
        ("assisted_schema_sha256", ASSISTED_SCHEMA_SHA256),
    ):
        _require_constant(schema.get(field), expected, f"owner_response.schema.{field}", "owner_response")
    contract = _require_mapping(
        response.get("effective_certified_stop_write_contract_identity"),
        "owner_response.contract",
        "owner_response",
    )
    for field, expected in (
        ("artifact_id", EFFECTIVE_ISSUE_CONTRACT_ARTIFACT_ID),
        ("path", EFFECTIVE_ISSUE_CONTRACT_PATH),
        ("sha256", EFFECTIVE_ISSUE_CONTRACT_SHA256),
        ("status", EFFECTIVE_ISSUE_CONTRACT_STATUS),
        ("owner", "Kernel/Checker"),
        ("assisted_contract_sha256", ASSISTED_CONTRACT_SHA256),
    ):
        _require_constant(contract.get(field), expected, f"owner_response.contract.{field}", "owner_response")
    policy = _require_mapping(response.get("checker_and_sufficiency_input_policy"), "owner_response.policy", "owner_response")
    for field, expected in (
        ("allowed_form_under_this_scope", "null_only"),
        ("non_null_refs_rejected_fail_closed", True),
        ("certificate_presence_may_substitute", False),
        ("ordinary_run_mvp_stop_may_substitute", False),
        ("certified_stop_writer_may_invoke_checker", False),
        ("certified_stop_writer_may_assert_evidence_sufficiency", False),
        ("this_policy_authorizes_checker_invocation", False),
        ("this_policy_authorizes_evidence_sufficiency_assertion", False),
    ):
        _require_constant(policy.get(field), expected, f"owner_response.policy.{field}", "owner_response")
    authority = _require_mapping(response.get("execution_authority"), "owner_response.execution_authority", "owner_response")
    for field in (
        "certified_stop_execution_authorized",
        "executor_implementation_authorized",
        "activation_authorized",
        "checker_invocation_authorized",
        "evidence_sufficiency_assertion_authorized",
        "run_mvp_stop_action_change_authorized",
    ):
        _require_constant(authority.get(field), False, f"owner_response.execution_authority.{field}", "owner_response")

def _validate_source_record(record: Mapping[str, Any]) -> None:
    for field, expected in (
        ("certificate_version", "certificate-record-v0.1"),
        ("certificate_id", SOURCE_ID),
        ("record_scope", "source_e_case_provenance_attestation_only"),
        ("surface_id", SURFACE_ID),
        ("package_id", PACKAGE_ID),
        ("is_certificate", True),
        ("is_e_case", False),
        ("is_kernel_store_record", False),
        ("checker_decision_ref", None),
    ):
        _require_constant(record.get(field), expected, f"source_record.{field}", "source_identity")
    state = _require_mapping(record.get("source_package_state"), "source_record.state", "source_identity")
    for field, expected in (
        ("claim_id_state", "minted_opaque"),
        ("admission_state", "admitted_under_separate_authority"),
        ("kernel_state", "ingested_under_separate_authority"),
        ("claim_count", CLAIM_COUNT),
        ("claims_content_hash", CLAIMS_CONTENT_HASH),
    ):
        _require_constant(state.get(field), expected, f"source_record.state.{field}", "source_identity")
    identities = _require_mapping(
        record.get("claim_identity_summary"), "source_record.claim_identity_summary", "source_identity"
    )
    for field, expected in (
        ("claim_count", CLAIM_COUNT),
        ("claim_id_list_sha256", CLAIM_ID_LIST_SHA256),
        ("claim_values_copied", False),
    ):
        _require_constant(identities.get(field), expected, f"source_record.identity.{field}", "source_identity")
    subject = _require_mapping(record.get("certificate_subject"), "source_record.subject", "source_identity")
    for field, expected in (
        ("subject_kind", "e_case"),
        ("certificate_scope", "provenance_attestation_of_exact_e_case_identity_only_not_evidence_sufficiency_not_checker_acceptance_not_certified_stop"),
    ):
        _require_constant(subject.get(field), expected, f"source_record.subject.{field}", "source_identity")
    separation = _require_mapping(record.get("separation_assertions"), "source_record.separation", "source_identity")
    for field, expected in (
        ("source_e_case_unchanged", True),
        ("source_is_certificate", False),
        ("certificate_is_e_case", False),
        ("certificate_is_kernel_store_record", False),
        ("checker_invoked_by_certificate_writer", False),
        ("checker_acceptance_or_promotion_implied", False),
        ("evidence_sufficiency_defaulted", False),
        ("certified_stop_authorized", False),
        ("certified_stop_declared", False),
        ("si_llm_001_closed", False),
        ("l2_or_part_b_gate_passed", False),
    ):
        _require_constant(separation.get(field), expected, f"source_record.separation.{field}", "source_identity")

def _validate_source_receipt(receipt: Mapping[str, Any]) -> None:
    for field, expected in (
        ("certificate_receipt_version", "certificate-issue-receipt-v0.1"),
        ("receipt_scope", "sanitized_versioned_certificate_issue_only"),
        ("decision", "certificate_issued_once_under_single_execute_authority"),
    ):
        _require_constant(receipt.get(field), expected, f"source_receipt.{field}", "source_receipt")
    target = _require_mapping(receipt.get("target"), "source_receipt.target", "source_receipt")
    for field, expected in (
        ("certificate_record_path", SOURCE_RECORD_PATH),
        ("certificate_id", SOURCE_ID),
        ("record_file_sha256", SOURCE_RECORD_SHA256),
        ("is_certificate", True),
        ("is_e_case", False),
        ("is_kernel_store_record", False),
    ):
        _require_constant(target.get(field), expected, f"source_receipt.target.{field}", "source_receipt")
    source = _require_mapping(receipt.get("source"), "source_receipt.source", "source_receipt")
    for field, expected in (
        ("surface_id", SURFACE_ID),
        ("package_id", PACKAGE_ID),
        ("claim_count", CLAIM_COUNT),
        ("claims_content_hash", CLAIMS_CONTENT_HASH),
        ("claim_id_list_sha256", CLAIM_ID_LIST_SHA256),
    ):
        _require_constant(source.get(field), expected, f"source_receipt.source.{field}", "source_receipt")
    effects = _require_mapping(receipt.get("side_effect_assertions"), "source_receipt.effects", "source_receipt")
    for field, value in effects.items():
        expected = field in {"certificate_generation", "certificate_write"}
        _require_constant(value, expected, f"source_receipt.effects.{field}", "source_receipt")

def _validate_activation(value: Any, *, repo_root: Path, executor_sha256: str) -> dict[str, Any]:
    activation = _require_mapping(value, "activation", "activation_shape")
    _reject_secret_keys(activation)
    if set(activation) != _EXPECTED_ACTIVATION_FIELDS:
        raise CertifiedStopError("activation_shape", "activation fields are not canonical")
    artifact_id = activation.get("artifact_id")
    if not isinstance(artifact_id, str) or not _ACTIVATION_ID_PATTERN.fullmatch(artifact_id):
        raise CertifiedStopError("activation_shape", "activation artifact id is invalid")
    for field, expected in (
        ("artifact_type", "production_certified_stop_single_execute_activation"),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", ACTIVATION_STATUS),
    ):
        _require_constant(activation.get(field), expected, f"activation.{field}", "not_activated")
    _require_exact_mapping(activation.get("authority_design"), _EXPECTED_AUTHORITY_DESIGN_REF, "activation.authority_design", "authority_design_pin")
    _require_exact_mapping(activation.get("owner_approval"), _EXPECTED_OWNER_APPROVAL_REF, "activation.owner_approval", "owner_approval_pin")
    _require_exact_mapping(activation.get("target"), _EXPECTED_TARGET, "activation.target", "activation_target")
    pins = _require_mapping(activation.get("pinned_hashes"), "activation.pins", "activation_pin")
    schema_pin = pins.get("effective_certified_stop_schema_sha256")
    contract_pin = pins.get("effective_certified_stop_write_contract_sha256")
    if schema_pin in FORBIDDEN_NON_EFFECTIVE_SCHEMA_SHAS:
        raise CertifiedStopError("non_effective_schema_identity", "assisted or inventory schema SHA is not effective")
    if contract_pin in FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS:
        raise CertifiedStopError("non_effective_contract_identity", "assisted contract SHA is not effective")
    expected_pins = dict(_EXPECTED_STATIC_PINS)
    expected_pins["certified_stop_executor_sha256"] = executor_sha256
    _require_exact_mapping(pins, expected_pins, "activation.pinned_hashes", "activation_pin")
    _require_exact_mapping(activation.get("selected_source"), _EXPECTED_SELECTED_SOURCE, "activation.selected_source", "selected_source")
    _require_exact_mapping(activation.get("transaction_contract"), _EXPECTED_TRANSACTION_CONTRACT, "activation.transaction_contract", "transaction_contract")
    _require_exact_mapping(activation.get("execute_ledger"), _EXPECTED_LEDGER_BEFORE, "activation.execute_ledger", "activation_ledger")
    if activation.get("execution_audit") is not None:
        raise CertifiedStopError("activation_ledger", "activation already contains execution audit")
    _validate_output_policy(activation.get("output_policy"), repo_root)
    _require_exact_mapping(activation.get("still_blocked"), _EXPECTED_STILL_BLOCKED, "activation.still_blocked", "activation_boundary")
    return copy.deepcopy(dict(activation))


def _validate_output_policy(value: Any, repo_root: Path) -> None:
    policy = _require_mapping(value, "activation.output_policy", "output_policy")
    if set(policy) != _EXPECTED_OUTPUT_POLICY_FIELDS:
        raise CertifiedStopError("output_policy", "output policy fields are not canonical")
    for field, expected in _EXPECTED_OUTPUT_POLICY_CONSTANTS.items():
        _require_constant(policy.get(field), expected, f"output_policy.{field}", "output_policy")
    record_path = _validate_output_path(policy.get("certified_stop_record_path"), repo_root)
    receipt_path = _validate_output_path(policy.get("sanitized_receipt_path"), repo_root)
    if record_path == receipt_path:
        raise CertifiedStopError("output_policy", "record and receipt paths must differ")


def _build_target_record(
    source: Mapping[str, Any],
    *,
    authority: Mapping[str, Any],
    activation_sha256: str,
    executor_sha256: str,
    transaction_id: str,
) -> dict[str, Any]:
    state = source["source_package_state"]
    return {
        "certified_stop_version": "certified-stop-record-v0.1",
        "certified_stop_id": CERTIFIED_STOP_ID,
        "record_scope": RECORD_SCOPE,
        "surface_id": SURFACE_ID,
        "package_id": PACKAGE_ID,
        "is_certified_stop": True,
        "is_certificate": False,
        "is_e_case": False,
        "is_kernel_store_record": False,
        "is_ordinary_run_mvp_stop": False,
        "source_certificate": {
            "record_path": SOURCE_RECORD_PATH,
            "record_sha256": SOURCE_RECORD_SHA256,
            "receipt_path": SOURCE_RECEIPT_PATH,
            "receipt_sha256": SOURCE_RECEIPT_SHA256,
            "certificate_id": SOURCE_ID,
            "source_is_certificate": True,
            "source_is_e_case": False,
            "source_is_kernel_store_record": False,
            "source_is_certified_stop": False,
            "source_is_ordinary_run_mvp_stop": False,
        },
        "source_package_state": {
            "claim_id_state": state["claim_id_state"],
            "admission_state": state["admission_state"],
            "kernel_state": state["kernel_state"],
            "claim_count": state["claim_count"],
            "claims_content_hash": state["claims_content_hash"],
        },
        "claim_identity_summary": {
            "claim_count": CLAIM_COUNT,
            "claim_id_list_sha256": CLAIM_ID_LIST_SHA256,
            "claim_values_copied": False,
        },
        "certified_stop_subject": {
            "subject_kind": "provenance_certificate",
            "certificate_id": SOURCE_ID,
            "certified_stop_scope": CERTIFIED_STOP_SCOPE,
        },
        "provenance": {
            "effective_certificate_schema": {
                "artifact_id": EFFECTIVE_SOURCE_SCHEMA_ARTIFACT_ID,
                "version": "0.1",
                "path": EFFECTIVE_SOURCE_SCHEMA_PATH,
                "sha256": EFFECTIVE_SOURCE_SCHEMA_SHA256,
                "status": EFFECTIVE_SOURCE_SCHEMA_STATUS,
                "owner": "Kernel/Checker",
            },
            "effective_certificate_issue_write_contract": {
                "artifact_id": EFFECTIVE_SOURCE_CONTRACT_ARTIFACT_ID,
                "version": "0.1",
                "path": EFFECTIVE_SOURCE_CONTRACT_PATH,
                "sha256": EFFECTIVE_SOURCE_CONTRACT_SHA256,
                "status": EFFECTIVE_SOURCE_CONTRACT_STATUS,
                "owner": "Kernel/Checker",
            },
            "effective_certified_stop_schema": {
                "artifact_id": EFFECTIVE_SCHEMA_ARTIFACT_ID,
                "version": EFFECTIVE_SCHEMA_VERSION,
                "path": EFFECTIVE_SCHEMA_PATH,
                "sha256": EFFECTIVE_SCHEMA_SHA256,
                "status": EFFECTIVE_SCHEMA_STATUS,
                "owner": "Kernel/Checker",
            },
            "effective_certified_stop_write_contract": {
                "artifact_id": EFFECTIVE_ISSUE_CONTRACT_ARTIFACT_ID,
                "version": EFFECTIVE_ISSUE_CONTRACT_VERSION,
                "path": EFFECTIVE_ISSUE_CONTRACT_PATH,
                "sha256": EFFECTIVE_ISSUE_CONTRACT_SHA256,
                "status": EFFECTIVE_ISSUE_CONTRACT_STATUS,
                "owner": "Kernel/Checker",
            },
        },
        "checker_decision_ref": None,
        "evidence_sufficiency_ref": None,
        "issue_authority": {
            "activation_artifact_id": authority["artifact_id"],
            "activation_path": ACTIVATION_PATH,
            "activation_sha256_before": activation_sha256,
            "executor_path": EXECUTOR_PATH,
            "executor_sha256": executor_sha256,
            "single_use": True,
        },
        "transaction": {
            "certified_stop_target_id": CERTIFIED_STOP_TARGET_ID,
            "transaction_id": transaction_id,
            "idempotency_key": IDEMPOTENCY_KEY,
            "atomic_all_or_nothing": True,
            "partial_write": False,
            "retry": False,
            "resume": False,
            "fallback": False,
        },
        "separation_assertions": {
            "source_certificate_unchanged": True,
            "source_is_certified_stop": False,
            "certified_stop_is_certificate": False,
            "certified_stop_is_e_case": False,
            "certified_stop_is_kernel_store_record": False,
            "certified_stop_is_ordinary_run_mvp_stop": False,
            "checker_invoked_by_certified_stop_writer": False,
            "checker_acceptance_or_promotion_implied": False,
            "evidence_sufficiency_defaulted": False,
            "si_llm_001_closed": False,
            "l2_or_part_b_gate_passed": False,
        },
    }

def _validate_target_record(record: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    if record.get("checker_decision_ref") is not None:
        raise CertifiedStopError("non_null_checker_decision_ref", "checker_decision_ref must be null")
    if record.get("evidence_sufficiency_ref") is not None:
        raise CertifiedStopError("non_null_evidence_sufficiency_ref", "evidence_sufficiency_ref must be null")
    for field, expected in (
        ("is_certified_stop", True),
        ("is_certificate", False),
        ("is_e_case", False),
        ("is_kernel_store_record", False),
        ("is_ordinary_run_mvp_stop", False),
    ):
        _require_constant(record.get(field), expected, f"target.{field}", "target_type")
    errors = sorted(
        Draft202012Validator(dict(schema)).iter_errors(record),
        key=lambda error: list(error.path),
    )
    if errors:
        raise CertifiedStopError("target_schema", errors[0].message)
    serialized = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    for forbidden in (
        '"claim_identity_refs"',
        '"claim_values"',
        '"labels"',
        '"realized_outcomes"',
        '"oracle"',
        '"action_id"',
        '"action_type"',
        '"checker_decision"',
        '"checker_accepted"',
        '"evidence_sufficiency"',
        '"promotion"',
        '"stop_recommendation"',
    ):
        if forbidden in serialized:
            raise CertifiedStopError("target_payload", "CERTIFIED_STOP contains a forbidden field")

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
    receipt_digest = hashlib.sha256(
        f"{record_sha256}\0{activation_sha256}\0{executor_sha256}".encode("utf-8")
    ).hexdigest()
    return {
        "certified_stop_receipt_version": "certified-stop-write-receipt-v0.1",
        "certified_stop_receipt_id": f"csor_{receipt_digest[:32]}",
        "receipt_scope": "sanitized_versioned_certified_stop_write_only",
        "decision": "certified_stop_written_once_under_single_execute_authority",
        "effective_artifacts": {
            "schema": {
                "artifact_id": EFFECTIVE_SCHEMA_ARTIFACT_ID,
                "path": EFFECTIVE_SCHEMA_PATH,
                "sha256": EFFECTIVE_SCHEMA_SHA256,
                "status": EFFECTIVE_SCHEMA_STATUS,
                "owner": "Kernel/Checker",
            },
            "write_contract": {
                "artifact_id": EFFECTIVE_ISSUE_CONTRACT_ARTIFACT_ID,
                "path": EFFECTIVE_ISSUE_CONTRACT_PATH,
                "sha256": EFFECTIVE_ISSUE_CONTRACT_SHA256,
                "status": EFFECTIVE_ISSUE_CONTRACT_STATUS,
                "owner": "Kernel/Checker",
            },
            "owner_response": {
                "artifact_id": OWNER_RESPONSE_ARTIFACT_ID,
                "path": OWNER_RESPONSE_PATH,
                "sha256": OWNER_RESPONSE_SHA256,
                "status": OWNER_RESPONSE_STATUS,
                "owner": "Kernel/Checker",
            },
        },
        "source": {
            "record_path": SOURCE_RECORD_PATH,
            "record_sha256": SOURCE_RECORD_SHA256,
            "receipt_path": SOURCE_RECEIPT_PATH,
            "receipt_sha256": SOURCE_RECEIPT_SHA256,
            "certificate_id": SOURCE_ID,
            "surface_id": SURFACE_ID,
            "package_id": PACKAGE_ID,
            "claim_count": CLAIM_COUNT,
            "claims_content_hash": CLAIMS_CONTENT_HASH,
            "claim_id_list_sha256": CLAIM_ID_LIST_SHA256,
            "source_is_certificate": True,
            "source_is_e_case": False,
            "source_is_kernel_store_record": False,
            "source_is_certified_stop": False,
            "source_is_ordinary_run_mvp_stop": False,
        },
        "target": {
            "certified_stop_record_path": authority["output_policy"]["certified_stop_record_path"],
            "certified_stop_id": CERTIFIED_STOP_ID,
            "certified_stop_target_id": CERTIFIED_STOP_TARGET_ID,
            "certified_stop_scope": CERTIFIED_STOP_SCOPE,
            "record_canonical_sha256": record_sha256,
            "record_file_sha256": record_file_sha256,
            "is_certified_stop": True,
            "is_certificate": False,
            "is_e_case": False,
            "is_kernel_store_record": False,
            "is_ordinary_run_mvp_stop": False,
        },
        "authority": {
            "activation_artifact_id": authority["artifact_id"],
            "activation_path": ACTIVATION_PATH,
            "activation_sha256_before": activation_sha256,
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "executor_path": EXECUTOR_PATH,
            "executor_sha256": executor_sha256,
        },
        "external_decision_input_policy": {
            "allowed_form": "null_only",
            "checker_decision_ref": None,
            "evidence_sufficiency_ref": None,
            "writer_invoked_checker": False,
            "writer_asserted_evidence_sufficiency": False,
            "checker_acceptance_or_promotion": False,
        },
        "ordinary_stop_separation": {
            "run_mvp_path": RUN_MVP_PATH,
            "run_mvp_sha256": RUN_MVP_SHA256,
            "ordinary_stop_action_id": "STOP",
            "ordinary_stop_action_is_certified_stop": False,
            "planner_stop_semantics_changed": False,
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
            "source_certificate_record_bytes_unchanged": True,
            "source_certificate_receipt_bytes_unchanged": True,
            "source_certificate_is_certificate_remains_true": True,
            "source_certificate_is_e_case_remains_false": True,
            "source_certificate_is_kernel_store_record_remains_false": True,
            "source_certificate_certified_stop_authorized_remains_false": True,
            "source_certificate_certified_stop_declared_remains_false": True,
            "source_package_id_unchanged": True,
            "source_claim_identity_count_unchanged": True,
            "source_claim_identity_hash_unchanged": True,
            "source_claim_id_state_unchanged": True,
            "source_admission_state_unchanged": True,
            "source_kernel_state_unchanged": True,
            "direct_rename_relabel_alias_copy_or_in_place_conversion": False,
        },
        "side_effect_assertions": {
            "certified_stop_execution": True,
            "certified_stop_write": True,
            "source_certificate_write_or_mutation": False,
            "source_e_case_write_or_mutation": False,
            "kernel_store_write_or_mutation": False,
            "ordinary_run_mvp_stop_action_change": False,
            "checker_invocation": False,
            "checker_acceptance_or_promotion": False,
            "evidence_sufficiency_assertion": False,
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
                EFFECTIVE_ISSUE_CONTRACT_SHA256,
                SOURCE_RECORD_SHA256,
                CERTIFIED_STOP_TARGET_ID,
                activation_sha256,
            )
        ).encode("utf-8")
    ).hexdigest()
    return f"cstop_txn_{digest[:32]}"


def _assert_source_still_unchanged(
    repo_root: Path,
    record_bytes_before: bytes,
    receipt_bytes_before: bytes,
) -> None:
    if (repo_root / SOURCE_RECORD_PATH).read_bytes() != record_bytes_before:
        raise CertifiedStopError("source_mutation", "source certificate record changed during execution")
    if (repo_root / SOURCE_RECEIPT_PATH).read_bytes() != receipt_bytes_before:
        raise CertifiedStopError("source_mutation", "source certificate receipt changed during execution")


def _validate_target_state(
    repo_root: Path,
    *,
    record: Mapping[str, Any],
    receipt: Mapping[str, Any],
    output_policy: Mapping[str, Any],
) -> bool:
    record_path = repo_root / output_policy["certified_stop_record_path"]
    receipt_path = repo_root / output_policy["sanitized_receipt_path"]
    record_exists = record_path.exists()
    receipt_exists = receipt_path.exists()
    if record_exists != receipt_exists:
        raise CertifiedStopError("target_collision", "certified_stop target is partially occupied")
    if not record_exists:
        return True
    if _load_json(record_path) != record or _load_json(receipt_path) != receipt:
        raise CertifiedStopError("target_collision", "existing certified_stop target is not idempotently equivalent")
    return False


def _validate_output_path(value: Any, repo_root: Path) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise CertifiedStopError("output_policy", "output path must use POSIX separators")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise CertifiedStopError("output_policy", "output path must remain repository-relative")
    if not (
        value.startswith("docs/llm-editor/fixtures/certified-stop/")
        or value.startswith(".tmp/compiler-contract/certified-stop/")
    ):
        raise CertifiedStopError("output_policy", "output path is outside allowed certified_stop roots")
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise CertifiedStopError("output_policy", "output path escapes repository") from exc
    return resolved


def _reject_secret_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().casefold().replace("-", "_").replace(" ", "_")
            if normalized in _SECRET_KEYS:
                raise CertifiedStopError("secret_in_activation", "activation contains a secret field")
            _reject_secret_keys(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            _reject_secret_keys(nested)


def _require_mapping(value: Any, field: str, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CertifiedStopError(code, f"{field} must be an object")
    return value


def _require_exact_mapping(value: Any, expected: Mapping[str, Any], field: str, code: str) -> None:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise CertifiedStopError(code, f"{field} does not match the frozen shape")
    for key, expected_value in expected.items():
        actual = value.get(key)
        if actual != expected_value or type(actual) is not type(expected_value):
            raise CertifiedStopError(code, f"{field}.{key} does not match the frozen value")


def _require_constant(value: Any, expected: Any, field: str, code: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise CertifiedStopError(code, f"{field} does not match the frozen value")


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise CertifiedStopError("pin_missing", f"pinned file missing: {relative_path}")
    if _sha256(path) != expected_sha:
        raise CertifiedStopError("pin_mismatch", f"pinned SHA mismatch: {relative_path}")


def _read_bounded_bytes(path: Path, kind: str) -> bytes:
    try:
        data = path.read_bytes()
    except (OSError, TypeError) as exc:
        raise CertifiedStopError(f"{kind}_read", f"cannot read {kind}") from exc
    if not data or len(data) > _MAX_JSON_BYTES:
        raise CertifiedStopError(f"{kind}_read", f"{kind} size is invalid")
    return data


def _decode_json_bytes(data: bytes, kind: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateJSONKey) as exc:
        raise CertifiedStopError(f"{kind}_json", f"{kind} is not canonical JSON") from exc
    if not isinstance(value, dict):
        raise CertifiedStopError(f"{kind}_json", f"{kind} must be an object")
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
        raise CertifiedStopError("pin_read", f"cannot read pinned artifact: {path.name}") from exc
    return digest.hexdigest()


def _claim_id_list_sha256(claim_ids: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(claim_ids, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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
        raise CertifiedStopError("canonical_json", "artifact is not canonical JSON") from exc
    return hashlib.sha256(data).hexdigest()


def _pretty_json_bytes(value: Any) -> bytes:
    """Return the exact versioned-fixture serialization used by the wrapper."""

    try:
        return (
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False, allow_nan=False)
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CertifiedStopError("pretty_json", "artifact is not serializable JSON") from exc


verify_certified_stop_pins = verify_issue_pins
validate_certified_stop_source_bytes = validate_source_bytes
