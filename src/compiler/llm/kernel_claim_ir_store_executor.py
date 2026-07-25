"""Fail-closed single-use production Kernel Claim-IR intake store executor.

The executor validates one exact, already-ingested external Claim-IR package
and returns a versioned Kernel intake-store record plus a sanitized receipt.
It has no filesystem write surface: an authorized wrapper must persist the
returned artifacts and the exhausted activation ledger atomically.  The
record is an intake-store record only; it is never an E_case, certificate,
registration, admission, mint, Checker decision, or lifecycle transition.
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


AUTHORITY_BASE_COMMIT = "8aff022870032b1a19bebae3311a4099a6d79ae7"
AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-production-kernel-claim-ir-store-"
    "single-execute-authority-design-v0.1-20260725.json"
)
AUTHORITY_DESIGN_SHA256 = (
    "e12145cc7e996d6435be7570764ea7971393c07745a4f1627bd04069f6fe3e00"
)
AUTHORITY_DESIGN_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-production-kernel-claim-ir-store-single-execute-"
    "authority-design-v0.1-20260725"
)
AUTHORITY_DESIGN_STATUS = (
    "design_only_production_kernel_claim_ir_store_authority_not_activated"
)
ACTIVATION_STATUS = (
    "activated_single_production_kernel_claim_ir_store_execute_authorized"
)
EXECUTOR_PATH = "src/compiler/llm/kernel_claim_ir_store_executor.py"

SURFACE_ID = "project05_depth2_public"
SOURCE_CLASS = "planner_experiment_inputs"
ADAPTER_ID = "m1a_planner_inputs_v0_1"
PACKAGE_ID = "pkg_73d77b55ef6a517a0dc528f7f3a89bd9"
TARGET_STORE_CLASS = "kernel_claim_ir_intake_store"

EFFECTIVE_CONTRACT_PATH = (
    "docs/kernel/kernel-v0.8-shared-claim-ir-consumer-contract-effective-"
    "v0.1-20260725.json"
)
EFFECTIVE_CONTRACT_SHA256 = (
    "a2a176fdeb2b93205a7f5e11c7c096236e2dc582d1c31f8f4a1534866c008d63"
)
EFFECTIVE_CONTRACT_ARTIFACT_ID = (
    "kernel-v0.8-shared-claim-ir-consumer-contract-effective-v0.1-20260725"
)
EFFECTIVE_CONTRACT_STATUS = (
    "effective_consumer_contract_semantics_only_ingestion_not_authorized"
)
ASSISTED_DRAFT_SHA256 = (
    "e2d30697909c2f41e2f6c86178fe198369a35215e937c8129269ea1d68aedfdc"
)
REVISION_PACKET_SHA256 = (
    "5cb0546139bf6b1abc21b5fa22494c80505082c8a43d16241a834b0451b981b3"
)
FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS = frozenset(
    {ASSISTED_DRAFT_SHA256, REVISION_PACKET_SHA256}
)

EXTERNAL_SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
EXTERNAL_SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
KERNEL_SCHEMA_PATH = "schemas/claim-ir-kernel.schema.json"
KERNEL_SCHEMA_SHA256 = (
    "7c6fa2db0b75d69340be5a8843ba0c373e2d5b25b0d37cf8f1d1c416a787865d"
)
INGESTED_FIXTURE_PATH = (
    "docs/llm-editor/fixtures/claim-ir-ingested/"
    "project05-depth2-public-minted-admitted-ingested-v0.1/package.json"
)
INGESTED_FIXTURE_SHA256 = (
    "908becf0c14f0bec756bf0382b85c5eeb100d61e0e19cde8a9375977071bd179"
)
INGESTION_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/claim-ir-ingested/"
    "project05-depth2-public-minted-admitted-ingested-v0.1/"
    "sanitized-receipt.json"
)
INGESTION_RECEIPT_SHA256 = (
    "1a4156704384becf7fc5b70c581c995eefe8d517dca2a6ffd423cb9d292ce2de"
)
IN_MEMORY_INGESTION_EXECUTOR_PATH = (
    "src/compiler/llm/kernel_claim_ir_ingestion_executor.py"
)
IN_MEMORY_INGESTION_EXECUTOR_SHA256 = (
    "da448a03505ac95e9f28bc33573ae453d7f7affc12b1e615a1214704cd8f4ea7"
)

STORE_RECORD_PATH = (
    "docs/llm-editor/fixtures/kernel-claim-ir-intake-store/"
    "project05-depth2-public-v0.1/store-record.json"
)
STORE_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/kernel-claim-ir-intake-store/"
    "project05-depth2-public-v0.1/sanitized-receipt.json"
)
STORE_TARGET_ID = (
    "kernel_claim_ir_intake_store:project05_depth2_public:"
    "pkg_73d77b55ef6a517a0dc528f7f3a89bd9:v0.1"
)
_IDEMPOTENCY_DIGEST = hashlib.sha256(
    "\0".join(
        (
            "kernel-claim-ir-intake-store-v0.1",
            AUTHORITY_DESIGN_SHA256,
            EFFECTIVE_CONTRACT_SHA256,
            INGESTED_FIXTURE_SHA256,
            INGESTION_RECEIPT_SHA256,
            STORE_TARGET_ID,
        )
    ).encode("utf-8")
).hexdigest()
TRANSACTION_ID = f"kcist_{_IDEMPOTENCY_DIGEST[:32]}"
IDEMPOTENCY_KEY = f"kcis_{_IDEMPOTENCY_DIGEST}"

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
        "target",
        "pinned_hashes",
        "selected_input",
        "store_transaction",
        "execute_ledger",
        "output_policy",
        "still_blocked",
        "execution_audit",
    }
)
_EXPECTED_TARGET = {
    "surface_id": SURFACE_ID,
    "source_class": SOURCE_CLASS,
    "adapter_id": ADAPTER_ID,
    "package_id": PACKAGE_ID,
    "target_store_class": TARGET_STORE_CLASS,
    "operation": "persist_exact_ingested_claim_ir_identity_once",
}
_EXPECTED_AUTHORITY_DESIGN_REF = {
    "artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
    "path": AUTHORITY_DESIGN_PATH,
    "sha256": AUTHORITY_DESIGN_SHA256,
    "status": AUTHORITY_DESIGN_STATUS,
}
_EXPECTED_STATIC_PINS = {
    "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
    "effective_consumer_contract_sha256": EFFECTIVE_CONTRACT_SHA256,
    "external_envelope_schema_sha256": EXTERNAL_SCHEMA_SHA256,
    "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
    "ingested_fixture_sha256": INGESTED_FIXTURE_SHA256,
    "sanitized_ingestion_receipt_sha256": INGESTION_RECEIPT_SHA256,
    "in_memory_ingestion_executor_sha256": IN_MEMORY_INGESTION_EXECUTOR_SHA256,
}
_EXPECTED_SELECTED_INPUT = {
    "ingested_package": {
        "path": INGESTED_FIXTURE_PATH,
        "sha256": INGESTED_FIXTURE_SHA256,
        "package_id": PACKAGE_ID,
        "surface_id": SURFACE_ID,
        "claim_id_state": "minted_opaque",
        "admission_state": "admitted_under_separate_authority",
        "kernel_state": "ingested_under_separate_authority",
    },
    "sanitized_ingestion_receipt": {
        "path": INGESTION_RECEIPT_PATH,
        "sha256": INGESTION_RECEIPT_SHA256,
    },
}
_EXPECTED_TRANSACTION = {
    "store_target_id": STORE_TARGET_ID,
    "transaction_id": TRANSACTION_ID,
    "idempotency_key": IDEMPOTENCY_KEY,
    "atomic_all_or_nothing": True,
    "store_target_empty_or_idempotently_equivalent_required": True,
    "partial_claim_store": False,
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "versioned_kernel_claim_ir_intake_store_record",
    "store_record_path": STORE_RECORD_PATH,
    "sanitized_store_receipt_path": STORE_RECEIPT_PATH,
    "file_write": True,
    "kernel_claim_ir_intake_store_write": True,
    "is_kernel_store_record": True,
    "is_e_case": False,
    "e_case_write": False,
    "certificate_generation": False,
    "certified_stop": False,
    "claim_lifecycle_mutation": False,
    "production_registration": False,
}
_EXPECTED_OUTPUT_POLICY_FIELDS = frozenset(_EXPECTED_OUTPUT_POLICY)
_EXPECTED_STILL_BLOCKED = {
    "second_store_execute": True,
    "e_case": True,
    "certificate": True,
    "certified_stop": True,
    "production_registration_execution": True,
    "si_llm_001_closure": True,
    "l2": True,
    "part_b_elevation": True,
    "checker_or_promotion": True,
    "catalog_role_credit": True,
    "m2_fit": True,
    "four_family_llm_finetune": True,
}
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
_ACTIVATION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
_CLAIM_ID_PATTERN = re.compile(r"^clm_[A-Za-z0-9_-]+$")
_MAX_JSON_BYTES = 2 * 1024 * 1024
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


class KernelClaimIRStoreError(ValueError):
    """Raised when the production intake-store gate fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class _DuplicateJSONKey(ValueError):
    pass


def verify_kernel_claim_ir_store_pins(repo_root: Path) -> None:
    """Verify the frozen design, contract, schemas, input, and receipt pins."""

    root = repo_root.resolve()
    for relative_path, expected_sha in (
        (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
        (EFFECTIVE_CONTRACT_PATH, EFFECTIVE_CONTRACT_SHA256),
        (EXTERNAL_SCHEMA_PATH, EXTERNAL_SCHEMA_SHA256),
        (KERNEL_SCHEMA_PATH, KERNEL_SCHEMA_SHA256),
        (INGESTED_FIXTURE_PATH, INGESTED_FIXTURE_SHA256),
        (INGESTION_RECEIPT_PATH, INGESTION_RECEIPT_SHA256),
        (IN_MEMORY_INGESTION_EXECUTOR_PATH, IN_MEMORY_INGESTION_EXECUTOR_SHA256),
    ):
        _verify_pin(root, relative_path, expected_sha)

    _validate_authority_design(_load_json(root / AUTHORITY_DESIGN_PATH))
    _validate_effective_contract(_load_json(root / EFFECTIVE_CONTRACT_PATH))
    schema = _load_json(root / EXTERNAL_SCHEMA_PATH)
    _validate_external_schema(schema)
    package_bytes = (root / INGESTED_FIXTURE_PATH).read_bytes()
    package = _decode_json_bytes(package_bytes, "ingested_package")
    _validate_ingested_package(package, schema)
    _validate_ingestion_receipt(_load_json(root / INGESTION_RECEIPT_PATH))


def execute_kernel_claim_ir_store(
    *,
    repo_root: Path,
    activation_path: Path | None = None,
) -> dict[str, Any]:
    """Return the exact store record and sanitized receipt for one attempt.

    The caller must persist both artifacts and the returned exhausted ledger
    atomically.  A committed exhausted activation cannot call this function
    again because the canonical BEFORE ledger is required.
    """

    if activation_path is None:
        raise KernelClaimIRStoreError(
            "missing_activation",
            "a distinct activated single-use production store authority is required",
        )
    root = repo_root.resolve()
    verify_kernel_claim_ir_store_pins(root)
    activation_bytes = _read_bounded_bytes(Path(activation_path), "activation")
    activation = _decode_json_bytes(activation_bytes, "activation")
    activation_sha256 = hashlib.sha256(activation_bytes).hexdigest()
    executor_sha256 = _sha256(root / EXECUTOR_PATH)
    authority = _validate_activation(
        activation,
        repo_root=root,
        executor_sha256=executor_sha256,
    )
    package_bytes = (root / INGESTED_FIXTURE_PATH).read_bytes()
    package = _decode_json_bytes(package_bytes, "ingested_package")

    record = _build_store_record(
        package,
        authority=authority,
        activation_sha256=activation_sha256,
        executor_sha256=executor_sha256,
    )
    receipt = _build_sanitized_store_receipt(
        record,
        authority=authority,
        activation_sha256=activation_sha256,
        executor_sha256=executor_sha256,
    )
    write_required = _validate_target_state(
        root,
        record=record,
        receipt=receipt,
        output_policy=authority["output_policy"],
    )
    _assert_exact_package_preserved(package, record["stored_claim_ir_package"])
    return {
        "store_record": record,
        "sanitized_store_receipt": receipt,
        "activation_sha256_before": activation_sha256,
        "execute_ledger_after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
        "store_write_required": write_required,
    }


def _validate_authority_design(value: Any) -> None:
    design = _require_mapping(value, "authority_design", "authority_design")
    for field, expected in (
        ("artifact_id", AUTHORITY_DESIGN_ARTIFACT_ID),
        (
            "artifact_type",
            "production_kernel_claim_ir_store_single_execute_authority_design",
        ),
        ("version", "0.1"),
        ("status", AUTHORITY_DESIGN_STATUS),
    ):
        _require_constant(
            design.get(field), expected, f"authority_design.{field}", "authority_design"
        )
    scope = _require_mapping(design.get("scope"), "design.scope", "authority_design")
    for field, expected in (
        ("surface_id", SURFACE_ID),
        ("package_id", PACKAGE_ID),
        ("target_store_class", TARGET_STORE_CLASS),
        ("activation_included", False),
        ("execution_included", False),
        ("e_case_write_included", False),
        ("certificate_generation_included", False),
    ):
        _require_constant(
            scope.get(field), expected, f"design.scope.{field}", "authority_design"
        )
    current = _require_mapping(
        design.get("current_authorization_state"),
        "design.current_authorization_state",
        "authority_design",
    )
    for field, expected in (
        ("activated", False),
        ("authorized", 0),
        ("maximum", 0),
        ("started", 0),
        ("consumed", 0),
        ("remaining", 0),
        ("production_kernel_store_write_authorized", False),
        ("production_kernel_store_write_performed", False),
    ):
        _require_constant(
            current.get(field),
            expected,
            f"design.current_authorization_state.{field}",
            "authority_design",
        )
    future = _require_mapping(
        design.get("future_activation_shape"),
        "design.future_activation_shape",
        "authority_design",
    )
    _require_constant(
        future.get("status"),
        ACTIVATION_STATUS,
        "design.future_activation_shape.status",
        "authority_design",
    )
    _require_exact_mapping(
        future.get("execute_ledger"),
        _EXPECTED_LEDGER_BEFORE,
        "design.future_activation_shape.execute_ledger",
        "authority_design",
    )
    preconditions = _require_mapping(
        future.get("required_future_preconditions"),
        "design.future_activation_shape.required_future_preconditions",
        "authority_design",
    )
    if not preconditions or any(value is not True for value in preconditions.values()):
        raise KernelClaimIRStoreError(
            "authority_design", "future production-store preconditions are incomplete"
        )


def _validate_effective_contract(value: Any) -> None:
    contract = _require_mapping(value, "effective_contract", "effective_contract")
    for field, expected in (
        ("artifact_id", EFFECTIVE_CONTRACT_ARTIFACT_ID),
        ("artifact_type", "kernel_m3_shared_claim_ir_consumer_contract_effective"),
        ("owner", "Kernel/M3*"),
        ("status", EFFECTIVE_CONTRACT_STATUS),
    ):
        _require_constant(
            contract.get(field), expected, f"effective_contract.{field}", "effective_contract"
        )
    ownership = _require_mapping(
        contract.get("ownership"), "effective_contract.ownership", "effective_contract"
    )
    _require_constant(
        ownership.get("effective"), True, "effective_contract.ownership.effective", "effective_contract"
    )
    accepted = _require_mapping(
        contract.get("accepted_external_claim_ir_schema"),
        "effective_contract.accepted_schema",
        "effective_contract",
    )
    for field, expected in (
        ("path", EXTERNAL_SCHEMA_PATH),
        ("content_sha256", EXTERNAL_SCHEMA_SHA256),
        ("decision", "accept_exact_identity"),
    ):
        _require_constant(
            accepted.get(field), expected, f"effective_contract.schema.{field}", "effective_contract"
        )
    semantics = _require_mapping(
        contract.get("target_token_consumption_semantics"),
        "effective_contract.target_token",
        "effective_contract",
    )
    _require_constant(
        semantics.get("token"),
        "ingested_under_separate_authority",
        "effective_contract.target_token.token",
        "effective_contract",
    )
    boundary = _require_mapping(
        contract.get("kernel_intake_versus_e_case_boundary"),
        "effective_contract.kernel_intake_boundary",
        "effective_contract",
    )
    for field, expected in (
        ("confirmed_by_owner", True),
        ("kernel_intake_is_e_case", False),
        ("kernel_intake_implies_claim_truth", False),
        ("kernel_intake_implies_promotion", False),
        ("kernel_intake_implies_checker_acceptance", False),
    ):
        _require_constant(
            boundary.get(field), expected, f"effective_contract.boundary.{field}", "effective_contract"
        )


def _validate_external_schema(value: Any) -> None:
    schema = _require_mapping(value, "external_schema", "schema")
    for field, expected in (
        ("$id", "https://project05.invalid/schemas/claim-ir-kernel.schema.json"),
        ("type", "object"),
        ("additionalProperties", False),
    ):
        _require_constant(schema.get(field), expected, f"external_schema.{field}", "schema")
    try:
        Draft202012Validator.check_schema(dict(schema))
    except Exception as exc:  # pragma: no cover
        raise KernelClaimIRStoreError("schema", "external schema is invalid") from exc


def _validate_ingested_package(value: Any, schema: Mapping[str, Any]) -> None:
    package = _require_mapping(value, "ingested_package", "package")
    if set(package) != _EXPECTED_PACKAGE_FIELDS:
        raise KernelClaimIRStoreError("package_shape", "package fields are not canonical")
    for field, expected in (
        ("schema_version", "claim-ir-external-v0.1"),
        ("package_id", PACKAGE_ID),
        ("surface_id", SURFACE_ID),
        ("claim_id_state", "minted_opaque"),
        ("admission_state", "admitted_under_separate_authority"),
        ("kernel_state", "ingested_under_separate_authority"),
    ):
        _require_constant(package.get(field), expected, f"package.{field}", "package_state")
    claims = package.get("claims")
    if not isinstance(claims, list) or len(claims) != 41:
        raise KernelClaimIRStoreError("package_shape", "package must contain exactly 41 claims")
    seen: set[str] = set()
    for claim in claims:
        if not isinstance(claim, Mapping) or set(claim) != _EXPECTED_CLAIM_FIELDS:
            raise KernelClaimIRStoreError("package_shape", "claim fields are not canonical")
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not _CLAIM_ID_PATTERN.fullmatch(claim_id):
            raise KernelClaimIRStoreError("package_identity", "claim_id is invalid")
        if claim_id in seen:
            raise KernelClaimIRStoreError("package_identity", "claim_id must be unique")
        seen.add(claim_id)
        _require_constant(
            claim.get("claim_id_state"), "minted_opaque", "claim.claim_id_state", "package_state"
        )
        _require_constant(
            claim.get("admission_state"),
            "admitted_under_separate_authority",
            "claim.admission_state",
            "package_state",
        )
    manifest = _require_mapping(package.get("manifest"), "package.manifest", "package_shape")
    _require_constant(manifest.get("claim_count"), 41, "package.manifest.claim_count", "package_shape")
    _require_constant(
        manifest.get("content_hash"),
        "594c0ec4c4533b1fae76ce57579cf52c783e61fc6b191d9807ce9751e5d473f1",
        "package.manifest.content_hash",
        "package_identity",
    )
    errors = sorted(Draft202012Validator(dict(schema)).iter_errors(dict(package)), key=lambda e: list(e.path))
    if errors:
        raise KernelClaimIRStoreError("package_schema", errors[0].message)


def _validate_ingestion_receipt(value: Any) -> None:
    receipt = _require_mapping(value, "ingestion_receipt", "ingestion_receipt")
    for field, expected in (
        ("receipt_version", "kernel-claim-ir-ingestion-receipt-v0.1"),
        ("receipt_scope", "sanitized_in_memory_test_only"),
        ("decision", "in_memory_ingestion_contract_test_passed"),
    ):
        _require_constant(receipt.get(field), expected, f"ingestion_receipt.{field}", "ingestion_receipt")
    effective = _require_mapping(
        receipt.get("effective_consumer_contract"), "receipt.contract", "ingestion_receipt"
    )
    _require_constant(
        effective.get("sha256"), EFFECTIVE_CONTRACT_SHA256, "receipt.contract.sha256", "ingestion_receipt"
    )
    schema = _require_mapping(receipt.get("schema"), "receipt.schema", "ingestion_receipt")
    _require_constant(schema.get("path"), EXTERNAL_SCHEMA_PATH, "receipt.schema.path", "ingestion_receipt")
    _require_constant(schema.get("sha256"), EXTERNAL_SCHEMA_SHA256, "receipt.schema.sha256", "ingestion_receipt")
    transition = _require_mapping(
        receipt.get("state_transition"), "receipt.state_transition", "ingestion_receipt"
    )
    _require_constant(
        transition.get("after"), "ingested_under_separate_authority", "receipt.transition.after", "ingestion_receipt"
    )
    preservation = _require_mapping(
        receipt.get("identity_preservation"), "receipt.identity_preservation", "ingestion_receipt"
    )
    if not preservation or any(item is not True for item in preservation.values()):
        raise KernelClaimIRStoreError("ingestion_receipt", "ingestion identity was not preserved")
    side_effects = _require_mapping(
        receipt.get("side_effects"), "receipt.side_effects", "ingestion_receipt"
    )
    if not side_effects or any(item is not False for item in side_effects.values()):
        raise KernelClaimIRStoreError("ingestion_receipt", "ingestion receipt has forbidden side effects")


def _validate_activation(
    value: Any,
    *,
    repo_root: Path,
    executor_sha256: str,
) -> dict[str, Any]:
    activation = _require_mapping(value, "activation", "activation_shape")
    _reject_secret_keys(activation)
    if set(activation) != _EXPECTED_ACTIVATION_FIELDS:
        raise KernelClaimIRStoreError("activation_shape", "activation fields are not canonical")
    artifact_id = activation.get("artifact_id")
    if not isinstance(artifact_id, str) or not _ACTIVATION_ID_PATTERN.fullmatch(artifact_id):
        raise KernelClaimIRStoreError("activation_shape", "activation artifact id is invalid")
    for field, expected in (
        ("artifact_type", "production_kernel_claim_ir_store_single_execute_activation"),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", ACTIVATION_STATUS),
    ):
        _require_constant(activation.get(field), expected, f"activation.{field}", "not_activated")
    _require_exact_mapping(
        activation.get("authority_design"), _EXPECTED_AUTHORITY_DESIGN_REF, "activation.authority_design", "design_pin"
    )
    _require_exact_mapping(activation.get("target"), _EXPECTED_TARGET, "activation.target", "activation_target")
    pins = _require_mapping(activation.get("pinned_hashes"), "activation.pinned_hashes", "activation_pin")
    effective_pin = pins.get("effective_consumer_contract_sha256")
    if effective_pin in FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS:
        raise KernelClaimIRStoreError(
            "non_effective_contract_identity", "draft or revision SHA cannot identify the effective contract"
        )
    expected_pins = dict(_EXPECTED_STATIC_PINS)
    expected_pins["production_store_executor_sha256"] = executor_sha256
    _require_exact_mapping(pins, expected_pins, "activation.pinned_hashes", "activation_pin")
    _require_exact_mapping(
        activation.get("selected_input"), _EXPECTED_SELECTED_INPUT, "activation.selected_input", "selected_input"
    )
    _require_exact_mapping(
        activation.get("store_transaction"), _EXPECTED_TRANSACTION, "activation.store_transaction", "store_transaction"
    )
    _require_exact_mapping(
        activation.get("execute_ledger"), _EXPECTED_LEDGER_BEFORE, "activation.execute_ledger", "activation_ledger"
    )
    if activation.get("execution_audit") is not None:
        raise KernelClaimIRStoreError("activation_ledger", "activation already contains execution audit data")
    _validate_output_policy(activation.get("output_policy"), repo_root)
    _require_exact_mapping(
        activation.get("still_blocked"), _EXPECTED_STILL_BLOCKED, "activation.still_blocked", "activation_boundary"
    )
    return copy.deepcopy(dict(activation))


def _validate_output_policy(value: Any, repo_root: Path) -> None:
    policy = _require_mapping(value, "activation.output_policy", "output_policy")
    if set(policy) != _EXPECTED_OUTPUT_POLICY_FIELDS:
        raise KernelClaimIRStoreError("output_policy", "output policy fields are not canonical")
    for field, expected in _EXPECTED_OUTPUT_POLICY.items():
        if field in {"store_record_path", "sanitized_store_receipt_path"}:
            continue
        _require_constant(
            policy.get(field), expected, f"activation.output_policy.{field}", "output_policy"
        )
    record_path = _validate_output_path(policy.get("store_record_path"), repo_root)
    receipt_path = _validate_output_path(
        policy.get("sanitized_store_receipt_path"), repo_root
    )
    if record_path == receipt_path:
        raise KernelClaimIRStoreError("output_policy", "record and receipt paths must be distinct")


def _build_store_record(
    package: Mapping[str, Any],
    *,
    authority: Mapping[str, Any],
    activation_sha256: str,
    executor_sha256: str,
) -> dict[str, Any]:
    digest = hashlib.sha256(
        "\0".join(
            (
                "kernel-claim-ir-intake-store-record-v0.1",
                STORE_TARGET_ID,
                TRANSACTION_ID,
                IDEMPOTENCY_KEY,
                activation_sha256,
                INGESTED_FIXTURE_SHA256,
            )
        ).encode("utf-8")
    ).hexdigest()
    return {
        "store_record_version": "kernel-claim-ir-intake-store-record-v0.1",
        "store_record_id": f"kcisr_{digest[:32]}",
        "status": "stored_exact_ingested_claim_ir_under_single_execute_authority",
        "store_target_class": TARGET_STORE_CLASS,
        "store_target_id": STORE_TARGET_ID,
        "transaction_id": TRANSACTION_ID,
        "idempotency_key": IDEMPOTENCY_KEY,
        "is_kernel_store_record": True,
        "is_e_case": False,
        "surface_id": SURFACE_ID,
        "package_id": PACKAGE_ID,
        "authority": {
            "artifact_id": authority["artifact_id"],
            "activation_sha256": activation_sha256,
            "authority_design_artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "production_store_executor_sha256": executor_sha256,
        },
        "input_pins": {
            "effective_consumer_contract_sha256": EFFECTIVE_CONTRACT_SHA256,
            "external_envelope_schema_sha256": EXTERNAL_SCHEMA_SHA256,
            "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
            "ingested_fixture_sha256": INGESTED_FIXTURE_SHA256,
            "sanitized_ingestion_receipt_sha256": INGESTION_RECEIPT_SHA256,
        },
        "stored_claim_ir_package": copy.deepcopy(dict(package)),
        "identity_preservation": {
            "package_id_unchanged": True,
            "claim_ids_unchanged": True,
            "claim_id_state_unchanged": True,
            "admission_state_unchanged": True,
            "kernel_state_unchanged": True,
            "claim_content_unchanged": True,
            "silent_schema_conversion": False,
        },
        "side_effects": {
            "kernel_claim_ir_intake_store_write": True,
            "e_case_write": False,
            "checker_or_promotion": False,
            "certificate_generation": False,
            "certified_stop": False,
            "production_registration": False,
            "claim_lifecycle_mutation": False,
            "si_llm_001_closure": False,
            "catalog_role_credit_l2_change": False,
            "m2_fit": False,
            "four_family_llm_finetune": False,
        },
    }


def _build_sanitized_store_receipt(
    record: Mapping[str, Any],
    *,
    authority: Mapping[str, Any],
    activation_sha256: str,
    executor_sha256: str,
) -> dict[str, Any]:
    record_sha256 = _canonical_json_sha256(record)
    digest = hashlib.sha256(
        f"{record_sha256}\0{activation_sha256}\0{executor_sha256}".encode("utf-8")
    ).hexdigest()
    return {
        "store_receipt_version": "kernel-claim-ir-intake-store-receipt-v0.1",
        "store_receipt_id": f"kcisrr_{digest[:32]}",
        "receipt_scope": "sanitized_versioned_kernel_claim_ir_intake_store_only",
        "decision": "stored_once_under_single_execute_authority",
        "authority_artifact_id_and_sha256": {
            "artifact_id": authority["artifact_id"],
            "activation_sha256": activation_sha256,
            "authority_design_artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "production_store_executor_sha256": executor_sha256,
        },
        "effective_consumer_contract_sha256": EFFECTIVE_CONTRACT_SHA256,
        "external_and_kernel_schema_sha256": {
            "external_envelope_schema_sha256": EXTERNAL_SCHEMA_SHA256,
            "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
            "silent_schema_conversion": False,
        },
        "package_id_and_input_sha256": {
            "surface_id": SURFACE_ID,
            "package_id": PACKAGE_ID,
            "input_sha256": INGESTED_FIXTURE_SHA256,
            "ingestion_receipt_sha256": INGESTION_RECEIPT_SHA256,
            "claim_count": 41,
            "claims_content_hash": "594c0ec4c4533b1fae76ce57579cf52c783e61fc6b191d9807ce9751e5d473f1",
        },
        "store_target_id": STORE_TARGET_ID,
        "transaction_id_and_idempotency_key": {
            "transaction_id": TRANSACTION_ID,
            "idempotency_key": IDEMPOTENCY_KEY,
            "atomic_all_or_nothing": True,
            "partial_claim_store": False,
        },
        "output": {
            "store_record_path": authority["output_policy"]["store_record_path"],
            "store_record_canonical_sha256": record_sha256,
            "sanitized_store_receipt_path": authority["output_policy"]["sanitized_store_receipt_path"],
        },
        "ledger_before_and_after": {
            "before": copy.deepcopy(_EXPECTED_LEDGER_BEFORE),
            "after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
            "success_or_failure_exhausts_attempt": True,
        },
        "identity_preservation": copy.deepcopy(record["identity_preservation"]),
        "side_effect_assertions": copy.deepcopy(record["side_effects"]),
    }


def _validate_target_state(
    repo_root: Path,
    *,
    record: Mapping[str, Any],
    receipt: Mapping[str, Any],
    output_policy: Mapping[str, Any],
) -> bool:
    record_path = repo_root / output_policy["store_record_path"]
    receipt_path = repo_root / output_policy["sanitized_store_receipt_path"]
    record_exists = record_path.exists()
    receipt_exists = receipt_path.exists()
    if record_exists != receipt_exists:
        raise KernelClaimIRStoreError(
            "store_target_collision", "store target is partially occupied"
        )
    if not record_exists:
        return True
    existing_record = _load_json(record_path)
    existing_receipt = _load_json(receipt_path)
    if existing_record != record or existing_receipt != receipt:
        raise KernelClaimIRStoreError(
            "store_target_collision", "existing store target is not idempotently equivalent"
        )
    return False


def _assert_exact_package_preserved(before: Mapping[str, Any], after: Any) -> None:
    if not isinstance(after, Mapping) or dict(before) != dict(after):
        raise KernelClaimIRStoreError(
            "identity_preservation", "stored package is not the exact ingested identity"
        )


def _validate_output_path(value: Any, repo_root: Path) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise KernelClaimIRStoreError("output_policy", "output path must use POSIX separators")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise KernelClaimIRStoreError("output_policy", "output path must remain repository-relative")
    if not (
        value.startswith("docs/llm-editor/fixtures/kernel-claim-ir-intake-store/")
        or value.startswith(".tmp/compiler-contract/")
    ):
        raise KernelClaimIRStoreError("output_policy", "output path is outside allowed store roots")
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise KernelClaimIRStoreError("output_policy", "output path escapes repository") from exc
    return resolved


def _reject_secret_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().casefold().replace("-", "_").replace(" ", "_")
            if normalized in _SECRET_KEYS:
                raise KernelClaimIRStoreError("secret_in_activation", "activation contains a secret field")
            _reject_secret_keys(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            _reject_secret_keys(nested)


def _require_mapping(value: Any, field: str, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KernelClaimIRStoreError(code, f"{field} must be an object")
    return value


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    code: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise KernelClaimIRStoreError(code, f"{field} does not match the frozen shape")
    for key, expected_value in expected.items():
        actual = value.get(key)
        if actual != expected_value or type(actual) is not type(expected_value):
            raise KernelClaimIRStoreError(code, f"{field}.{key} does not match the frozen value")


def _require_constant(value: Any, expected: Any, field: str, code: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise KernelClaimIRStoreError(code, f"{field} does not match the frozen value")


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise KernelClaimIRStoreError("pin_missing", f"pinned file missing: {relative_path}")
    if _sha256(path) != expected_sha:
        raise KernelClaimIRStoreError("pin_mismatch", f"pinned SHA mismatch: {relative_path}")


def _read_bounded_bytes(path: Path, kind: str) -> bytes:
    try:
        data = path.read_bytes()
    except (OSError, TypeError) as exc:
        raise KernelClaimIRStoreError(f"{kind}_read", f"cannot read {kind}") from exc
    if not data or len(data) > _MAX_JSON_BYTES:
        raise KernelClaimIRStoreError(f"{kind}_read", f"{kind} size is invalid")
    return data


def _decode_json_bytes(data: bytes, kind: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateJSONKey) as exc:
        raise KernelClaimIRStoreError(f"{kind}_json", f"{kind} is not canonical JSON") from exc
    if not isinstance(value, dict):
        raise KernelClaimIRStoreError(f"{kind}_json", f"{kind} must be an object")
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
        raise KernelClaimIRStoreError("pin_read", f"cannot read pinned artifact: {path.name}") from exc
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
        raise KernelClaimIRStoreError("canonical_json", "artifact is not canonical JSON") from exc
    return hashlib.sha256(data).hexdigest()
