"""Fail-closed Claim-ID mainline handoff payload builder.

The builder emits only a minimal, read-only identity reference for the exact
versioned ``project05_depth2_public`` package that completed the separately
authorized in-memory Kernel ingestion path.  It performs no registration,
state transition, Kernel/E_case write, certificate generation, or L2 change.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


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

HANDOFF_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-mainline-handoff-design-v0.1-20260724.json"
)
HANDOFF_DESIGN_SHA256 = (
    "cc6829709b359e2cac72ad30c00ac78ce7e2989a66f2b2e20d7eac4b98452e80"
)
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
EFFECTIVE_CONSUMER_CONTRACT_VERSION = "0.1"
EFFECTIVE_CONSUMER_CONTRACT_STATUS = (
    "effective_consumer_contract_semantics_only_ingestion_not_authorized"
)
SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
INGESTED_FIXTURE_PATH = (
    "docs/llm-editor/fixtures/claim-ir-ingested/"
    "project05-depth2-public-minted-admitted-ingested-v0.1/package.json"
)
INGESTED_FIXTURE_SHA256 = (
    "908becf0c14f0bec756bf0382b85c5eeb100d61e0e19cde8a9375977071bd179"
)
SANITIZED_RECEIPT_PATH = (
    "docs/llm-editor/fixtures/claim-ir-ingested/"
    "project05-depth2-public-minted-admitted-ingested-v0.1/"
    "sanitized-receipt.json"
)
SANITIZED_RECEIPT_SHA256 = (
    "1a4156704384becf7fc5b70c581c995eefe8d517dca2a6ffd423cb9d292ce2de"
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

PRODUCTION_REGISTRATION_ENABLED = False

_EXPECTED_CONSUMER_CONTRACT_REF = {
    "effective_artifact_id": EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
    "effective_version": EFFECTIVE_CONSUMER_CONTRACT_VERSION,
    "effective_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
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
_EXPECTED_MANIFEST_FIELDS = frozenset(
    {
        "claim_count",
        "field_path_set",
        "projection_sha256",
        "content_hash",
    }
)
_EXPECTED_RECEIPT_FIELDS = frozenset(
    {
        "receipt_version",
        "receipt_id",
        "receipt_scope",
        "decision",
        "effective_consumer_contract",
        "schema",
        "input",
        "authority",
        "transaction",
        "state_transition",
        "identity_preservation",
        "side_effects",
    }
)
_EXPECTED_PAYLOAD_FIELDS = frozenset(
    {
        "surface_id",
        "package_id",
        "claim_reference",
        "claim_id_state",
        "admission_state",
        "kernel_state",
        "consumer_contract_ref",
    }
)
_CLAIM_ID_PATTERN = re.compile(r"^clm_[A-Za-z0-9_-]+$")
_MAX_INPUT_BYTES = 2 * 1024 * 1024


class ClaimIDMainlineHandoffError(ValueError):
    """Raised when a mainline handoff request fails a closed boundary."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def verify_mainline_handoff_pins(repo_root: Path) -> None:
    """Verify every frozen design, contract, schema, package, and receipt pin."""

    repo_root = repo_root.resolve()
    for relative_path, expected_sha in (
        (HANDOFF_DESIGN_PATH, HANDOFF_DESIGN_SHA256),
        (EFFECTIVE_CONSUMER_CONTRACT_PATH, EFFECTIVE_CONSUMER_CONTRACT_SHA256),
        (SCHEMA_PATH, SCHEMA_SHA256),
        (INGESTED_FIXTURE_PATH, INGESTED_FIXTURE_SHA256),
        (SANITIZED_RECEIPT_PATH, SANITIZED_RECEIPT_SHA256),
    ):
        _verify_pin(repo_root, relative_path, expected_sha)

    _validate_handoff_design(_load_json(repo_root / HANDOFF_DESIGN_PATH))
    _validate_effective_contract(
        _load_json(repo_root / EFFECTIVE_CONSUMER_CONTRACT_PATH)
    )


def build_claim_id_mainline_handoff(
    package_bytes: bytes,
    receipt_bytes: bytes,
    *,
    repo_root: Path,
    consumer_contract_ref: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return a minimal read-only Claim-ID handoff payload.

    The exact ingested fixture and its exact sanitized receipt are required.
    This function has no persistent write or lifecycle-state mutation surface.
    """

    repo_root = repo_root.resolve()
    verify_mainline_handoff_pins(repo_root)
    contract_ref = _validate_consumer_contract_ref(consumer_contract_ref)

    package = _decode_json_bytes(package_bytes, "package")
    _validate_ingested_package(package)
    _require_bytes_pin(
        package_bytes,
        INGESTED_FIXTURE_SHA256,
        "fixture_pin",
        "ingested package bytes do not match the versioned fixture",
    )

    receipt = _decode_json_bytes(receipt_bytes, "receipt")
    _validate_sanitized_receipt(receipt)
    _require_bytes_pin(
        receipt_bytes,
        SANITIZED_RECEIPT_SHA256,
        "receipt_pin",
        "sanitized receipt bytes do not match the versioned fixture",
    )

    claim_ids = [claim["claim_id"] for claim in package["claims"]]
    claim_id_list_sha = hashlib.sha256(
        json.dumps(
            claim_ids,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    _require_constant(
        claim_id_list_sha,
        CLAIM_ID_LIST_SHA256,
        "package.claim_id_list_sha256",
        "claim_identity",
    )

    payload = {
        "surface_id": package["surface_id"],
        "package_id": package["package_id"],
        "claim_reference": {
            "claims_content_hash": package["manifest"]["content_hash"],
            "full_claim_id_list_sha256": claim_id_list_sha,
            "claim_count": len(claim_ids),
        },
        "claim_id_state": package["claim_id_state"],
        "admission_state": package["admission_state"],
        "kernel_state": package["kernel_state"],
        "consumer_contract_ref": contract_ref,
    }
    if set(payload) != _EXPECTED_PAYLOAD_FIELDS:
        raise ClaimIDMainlineHandoffError(
            "payload_shape",
            "mainline handoff payload is not the frozen minimal shape",
        )
    return payload


def _validate_handoff_design(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ClaimIDMainlineHandoffError(
            "design_shape", "mainline handoff design must be an object"
        )
    for field, expected in (
        ("artifact_type", "claim_id_mainline_handoff_design"),
        ("status", "design_only_mainline_handoff_not_authorized"),
    ):
        _require_constant(
            value.get(field), expected, f"design.{field}", "design_shape"
        )
    scope = _require_mapping(value.get("scope"), "design.scope", "design_shape")
    _require_constant(
        scope.get("surface_id"), SURFACE_ID, "design.scope.surface_id", "design_shape"
    )
    minimal = _require_mapping(
        value.get("minimal_handoff_payload_design"),
        "design.minimal_handoff_payload_design",
        "design_shape",
    )
    _require_constant(
        minimal.get("payload_type"),
        "claim_id_mainline_reference_v0.1",
        "design.payload_type",
        "design_shape",
    )
    _require_constant(
        minimal.get("additional_fields_allowed"),
        False,
        "design.additional_fields_allowed",
        "design_shape",
    )
    required = minimal.get("required_fields")
    if not isinstance(required, list) or set(required) != _EXPECTED_PAYLOAD_FIELDS:
        raise ClaimIDMainlineHandoffError(
            "design_shape", "design required payload fields are not frozen"
        )


def _validate_effective_contract(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ClaimIDMainlineHandoffError(
            "contract_shape", "effective consumer contract must be an object"
        )
    for field, expected in (
        ("artifact_id", EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID),
        ("artifact_type", "kernel_m3_shared_claim_ir_consumer_contract_effective"),
        ("version", EFFECTIVE_CONSUMER_CONTRACT_VERSION),
        ("owner", "Kernel/M3*"),
        ("status", EFFECTIVE_CONSUMER_CONTRACT_STATUS),
    ):
        _require_constant(
            value.get(field), expected, f"contract.{field}", "contract_shape"
        )
    ownership = _require_mapping(
        value.get("ownership"), "contract.ownership", "contract_shape"
    )
    _require_constant(
        ownership.get("effective"),
        True,
        "contract.ownership.effective",
        "contract_shape",
    )
    schema = _require_mapping(
        value.get("accepted_external_claim_ir_schema"),
        "contract.accepted_external_claim_ir_schema",
        "contract_shape",
    )
    _require_constant(
        schema.get("content_sha256"),
        SCHEMA_SHA256,
        "contract.schema.content_sha256",
        "contract_shape",
    )
    target = _require_mapping(
        value.get("target_token_consumption_semantics"),
        "contract.target_token_consumption_semantics",
        "contract_shape",
    )
    _require_constant(
        target.get("token"),
        "ingested_under_separate_authority",
        "contract.target_token",
        "contract_shape",
    )


def _validate_consumer_contract_ref(
    value: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if value is None:
        raise ClaimIDMainlineHandoffError(
            "missing_consumer_contract",
            "a bound effective consumer contract reference is required",
        )
    if not isinstance(value, Mapping):
        raise ClaimIDMainlineHandoffError(
            "consumer_contract_shape",
            "consumer contract reference must be an object",
        )
    effective_sha = value.get("effective_sha256")
    if effective_sha is None:
        raise ClaimIDMainlineHandoffError(
            "unbound_consumer_contract",
            "consumer contract reference is unbound",
        )
    if effective_sha in FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS:
        raise ClaimIDMainlineHandoffError(
            "non_effective_contract_identity",
            "draft or revision packet SHA cannot identify the effective contract",
        )
    if set(value) != set(_EXPECTED_CONSUMER_CONTRACT_REF):
        raise ClaimIDMainlineHandoffError(
            "consumer_contract_shape",
            "consumer contract reference fields are not canonical",
        )
    if effective_sha != EFFECTIVE_CONSUMER_CONTRACT_SHA256:
        raise ClaimIDMainlineHandoffError(
            "consumer_contract_pin",
            "consumer contract effective SHA does not match the frozen contract",
        )
    for field, expected in _EXPECTED_CONSUMER_CONTRACT_REF.items():
        _require_constant(
            value.get(field),
            expected,
            f"consumer_contract_ref.{field}",
            "consumer_contract_ref",
        )
    return dict(value)


def _validate_ingested_package(value: Any) -> None:
    if not isinstance(value, Mapping) or set(value) != _EXPECTED_PACKAGE_FIELDS:
        raise ClaimIDMainlineHandoffError(
            "package_shape", "ingested package fields are not canonical"
        )
    for field, expected in (
        ("schema_version", "claim-ir-external-v0.1"),
        ("package_id", PACKAGE_ID),
        ("surface_id", SURFACE_ID),
    ):
        _require_constant(
            value.get(field), expected, f"package.{field}", "package_identity"
        )
    for field, expected in (
        ("kernel_state", "ingested_under_separate_authority"),
        ("claim_id_state", "minted_opaque"),
        ("admission_state", "admitted_under_separate_authority"),
    ):
        _require_constant(
            value.get(field), expected, f"package.{field}", "package_state"
        )

    claims = value.get("claims")
    if not isinstance(claims, list) or len(claims) != CLAIM_COUNT:
        raise ClaimIDMainlineHandoffError(
            "package_claims", "ingested package claim count is not frozen"
        )
    claim_ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, Mapping) or set(claim) != _EXPECTED_CLAIM_FIELDS:
            raise ClaimIDMainlineHandoffError(
                "claim_shape", "ingested claim fields are not canonical"
            )
        for field, expected in (
            ("claim_id_state", "minted_opaque"),
            ("admission_state", "admitted_under_separate_authority"),
        ):
            _require_constant(
                claim.get(field), expected, f"claim.{field}", "package_state"
            )
        claim_id = claim.get("claim_id")
        if (
            not isinstance(claim_id, str)
            or not _CLAIM_ID_PATTERN.fullmatch(claim_id)
            or claim_id in claim_ids
        ):
            raise ClaimIDMainlineHandoffError(
                "claim_identity", "Claim-IDs must remain opaque and unique"
            )
        claim_ids.add(claim_id)

    manifest = value.get("manifest")
    if not isinstance(manifest, Mapping) or set(manifest) != _EXPECTED_MANIFEST_FIELDS:
        raise ClaimIDMainlineHandoffError(
            "manifest_shape", "ingested package manifest is not canonical"
        )
    for field, expected in (
        ("claim_count", CLAIM_COUNT),
        ("content_hash", CLAIMS_CONTENT_HASH),
    ):
        _require_constant(
            manifest.get(field),
            expected,
            f"package.manifest.{field}",
            "manifest_identity",
        )


def _validate_sanitized_receipt(value: Any) -> None:
    if not isinstance(value, Mapping) or set(value) != _EXPECTED_RECEIPT_FIELDS:
        raise ClaimIDMainlineHandoffError(
            "receipt_shape", "sanitized ingestion receipt is not canonical"
        )
    for field, expected in (
        ("receipt_version", "kernel-claim-ir-ingestion-receipt-v0.1"),
        ("receipt_scope", "sanitized_in_memory_test_only"),
        ("decision", "in_memory_ingestion_contract_test_passed"),
    ):
        _require_constant(
            value.get(field), expected, f"receipt.{field}", "receipt_shape"
        )
    contract = _require_mapping(
        value.get("effective_consumer_contract"),
        "receipt.effective_consumer_contract",
        "receipt_binding",
    )
    for field, expected in (
        ("artifact_id", EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID),
        ("version", EFFECTIVE_CONSUMER_CONTRACT_VERSION),
        ("sha256", EFFECTIVE_CONSUMER_CONTRACT_SHA256),
    ):
        _require_constant(
            contract.get(field),
            expected,
            f"receipt.contract.{field}",
            "receipt_binding",
        )
    receipt_input = _require_mapping(
        value.get("input"), "receipt.input", "receipt_binding"
    )
    for field, expected in (
        ("package_id", PACKAGE_ID),
        ("surface_id", SURFACE_ID),
        ("claim_count", CLAIM_COUNT),
        ("claim_id_list_sha256", CLAIM_ID_LIST_SHA256),
        ("claims_content_hash", CLAIMS_CONTENT_HASH),
    ):
        _require_constant(
            receipt_input.get(field),
            expected,
            f"receipt.input.{field}",
            "receipt_binding",
        )
    transition = _require_mapping(
        value.get("state_transition"), "receipt.state_transition", "receipt_binding"
    )
    for field, expected in (
        ("field", "package.kernel_state"),
        ("before", "pending_kernel_schema"),
        ("after", "ingested_under_separate_authority"),
    ):
        _require_constant(
            transition.get(field),
            expected,
            f"receipt.transition.{field}",
            "receipt_binding",
        )
    side_effects = _require_mapping(
        value.get("side_effects"), "receipt.side_effects", "receipt_boundary"
    )
    for field in (
        "production_kernel_store_write",
        "e_case_write",
        "checker_or_promotion",
        "certificate_generation",
        "certified_stop",
        "si_llm_001_closure",
        "catalog_role_credit_l2_change",
        "m2_fit",
        "four_family_llm_finetune",
    ):
        _require_constant(
            side_effects.get(field),
            False,
            f"receipt.side_effects.{field}",
            "receipt_boundary",
        )


def _decode_json_bytes(value: bytes, kind: str) -> dict[str, Any]:
    if not isinstance(value, bytes):
        raise ClaimIDMainlineHandoffError(
            f"{kind}_type", f"{kind} must be provided as immutable bytes"
        )
    if not value or len(value) > _MAX_INPUT_BYTES:
        raise ClaimIDMainlineHandoffError(
            f"{kind}_size", f"{kind} byte length is empty or exceeds the bound"
        )
    try:
        decoded = value.decode("utf-8")
        result = json.loads(decoded, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateJSONKey) as exc:
        raise ClaimIDMainlineHandoffError(
            f"{kind}_json", f"{kind} is not canonical UTF-8 JSON"
        ) from exc
    if not isinstance(result, dict):
        raise ClaimIDMainlineHandoffError(
            f"{kind}_shape", f"{kind} must decode to an object"
        )
    return result


def _require_mapping(value: Any, field: str, error_code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaimIDMainlineHandoffError(error_code, f"{field} must be an object")
    return value


def _require_constant(
    value: Any,
    expected: Any,
    field: str,
    error_code: str,
) -> None:
    if value != expected or type(value) is not type(expected):
        raise ClaimIDMainlineHandoffError(
            error_code, f"{field} does not match the frozen value"
        )


def _require_bytes_pin(
    value: bytes,
    expected_sha: str,
    error_code: str,
    message: str,
) -> None:
    if hashlib.sha256(value).hexdigest() != expected_sha:
        raise ClaimIDMainlineHandoffError(error_code, message)


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise ClaimIDMainlineHandoffError(
            "pin_missing", f"pinned file missing: {relative_path}"
        )
    if _sha256(path) != expected_sha:
        raise ClaimIDMainlineHandoffError(
            "pin_mismatch", f"pinned SHA mismatch: {relative_path}"
        )


def _load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        _DuplicateJSONKey,
    ) as exc:
        raise ClaimIDMainlineHandoffError(
            "json_read", f"cannot read canonical JSON artifact: {path.name}"
        ) from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ClaimIDMainlineHandoffError(
            "pin_read", f"cannot read pinned artifact: {path.name}"
        ) from exc
    return digest.hexdigest()


class _DuplicateJSONKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(key)
        result[key] = value
    return result
