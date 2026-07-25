"""Fail-closed single-use Claim-ID mainline reference registration.

The executor registers only the exact read-only handoff reference frozen by
the reviewed authority design and an activated single-use authority.  It
returns an in-memory registration record and sanitized receipt; a separately
authorized wrapper is responsible for writing those audit artifacts and for
persisting the exhausted ledger.  It never writes a Kernel store, E_case,
certificate, control-loop wiring, or lifecycle state.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.compiler.llm import claim_id_mainline_handoff as handoff_module
from src.compiler.llm.claim_id_mainline_handoff import (
    ADAPTER_ID,
    CLAIMS_CONTENT_HASH,
    CLAIM_COUNT,
    CLAIM_ID_LIST_SHA256,
    EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
    EFFECTIVE_CONSUMER_CONTRACT_PATH,
    EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    EFFECTIVE_CONSUMER_CONTRACT_VERSION,
    HANDOFF_DESIGN_PATH,
    HANDOFF_DESIGN_SHA256,
    INGESTED_FIXTURE_PATH,
    INGESTED_FIXTURE_SHA256,
    PACKAGE_ID,
    SANITIZED_RECEIPT_PATH,
    SANITIZED_RECEIPT_SHA256,
    SCHEMA_PATH,
    SCHEMA_SHA256,
    SOURCE_CLASS,
    SURFACE_ID,
    build_claim_id_mainline_handoff,
    verify_mainline_handoff_pins,
)


AUTHORITY_BASE_COMMIT = "3371974b04ac645e0cf9ede6439e253b88b2fe2b"
AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-production-claim-id-mainline-registration-"
    "single-execute-authority-design-v0.1-20260725.json"
)
AUTHORITY_DESIGN_SHA256 = (
    "ad6b95adc6b515649e9dd7886ea9530d33f931559bfff70f97f07576f3d7acda"
)
AUTHORITY_DESIGN_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-production-claim-id-mainline-registration-"
    "single-execute-authority-design-v0.1-20260725"
)
AUTHORITY_DESIGN_STATUS = (
    "design_only_production_registration_authority_not_activated"
)
EXECUTOR_PATH = "src/compiler/llm/claim_id_mainline_registration_executor.py"
HANDOFF_IMPLEMENTATION_PATH = "src/compiler/llm/claim_id_mainline_handoff.py"
HANDOFF_IMPLEMENTATION_SHA256 = (
    "304000b03ad273a26d864e2567c4b3f20ce06bdc5199387d57d46bc64152c35a"
)
MERGE_READINESS_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-mainline-handoff-merge-readiness-"
    "disposition-v0.1-20260725.json"
)
MERGE_READINESS_SHA256 = (
    "b1d9f2cf54132685f072d9cb84619f1e73b9da331bd37d683342ec7444b8ad94"
)
ACTIVATION_STATUS = "activated_single_production_registration_execute_authorized"
RECORD_STATUS = (
    "registered_exact_read_only_handoff_reference_under_single_execute_authority"
)

_ACTIVATION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
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
        "execute_ledger",
        "output_policy",
        "still_blocked",
        "execution_audit",
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
_EXPECTED_TARGET = {
    "surface_id": SURFACE_ID,
    "source_class": SOURCE_CLASS,
    "adapter_id": ADAPTER_ID,
    "package_id": PACKAGE_ID,
    "registration_target": "claim_id_mainline_read_only_reference",
    "execution_scope": "single_versioned_audit_registration_only",
}
_EXPECTED_STATIC_PINS = {
    "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
    "mainline_handoff_implementation_sha256": HANDOFF_IMPLEMENTATION_SHA256,
    "mainline_handoff_design_sha256": HANDOFF_DESIGN_SHA256,
    "merge_readiness_disposition_sha256": MERGE_READINESS_SHA256,
    "effective_consumer_contract_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    "external_envelope_schema_sha256": SCHEMA_SHA256,
    "ingested_fixture_sha256": INGESTED_FIXTURE_SHA256,
    "sanitized_ingestion_receipt_sha256": SANITIZED_RECEIPT_SHA256,
}
_EXPECTED_SELECTED_INPUT = {
    "package": {
        "path": INGESTED_FIXTURE_PATH,
        "sha256": INGESTED_FIXTURE_SHA256,
        "package_id": PACKAGE_ID,
    },
    "ingestion_receipt": {
        "path": SANITIZED_RECEIPT_PATH,
        "sha256": SANITIZED_RECEIPT_SHA256,
    },
    "handoff_reference": {
        "surface_id": SURFACE_ID,
        "package_id": PACKAGE_ID,
        "effective_consumer_contract_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    },
}
_EXPECTED_OUTPUT_POLICY_FIELDS = frozenset(
    {
        "mode",
        "registration_record_path",
        "sanitized_receipt_path",
        "registration_record_write",
        "sanitized_receipt_write",
        "kernel_store_write",
        "e_case_write",
        "certificate_generation",
        "certified_stop",
        "production_control_loop_wiring",
        "planner_wiring",
        "claim_lifecycle_mutation",
    }
)
_EXPECTED_STILL_BLOCKED = {
    "second_registration_execute": True,
    "permanent_registration_switch": True,
    "production_control_loop_wiring": True,
    "planner_wiring": True,
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
_EXPECTED_AUTHORITY_DESIGN_REF = {
    "artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
    "path": AUTHORITY_DESIGN_PATH,
    "sha256": AUTHORITY_DESIGN_SHA256,
    "status": AUTHORITY_DESIGN_STATUS,
}
_MAX_ACTIVATION_BYTES = 256 * 1024


class ClaimIDMainlineRegistrationError(ValueError):
    """Raised when a registration attempt fails a closed boundary."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def verify_registration_pins(repo_root: Path) -> None:
    """Verify the complete frozen design and handoff dependency chain."""

    repo_root = repo_root.resolve()
    for relative_path, expected_sha in (
        (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
        (HANDOFF_IMPLEMENTATION_PATH, HANDOFF_IMPLEMENTATION_SHA256),
        (HANDOFF_DESIGN_PATH, HANDOFF_DESIGN_SHA256),
        (MERGE_READINESS_PATH, MERGE_READINESS_SHA256),
        (EFFECTIVE_CONSUMER_CONTRACT_PATH, EFFECTIVE_CONSUMER_CONTRACT_SHA256),
        (SCHEMA_PATH, SCHEMA_SHA256),
        (INGESTED_FIXTURE_PATH, INGESTED_FIXTURE_SHA256),
        (SANITIZED_RECEIPT_PATH, SANITIZED_RECEIPT_SHA256),
    ):
        _verify_pin(repo_root, relative_path, expected_sha)

    _validate_authority_design(_load_json(repo_root / AUTHORITY_DESIGN_PATH))
    verify_mainline_handoff_pins(repo_root)
    _require_global_switch_disabled()


def execute_claim_id_mainline_registration(
    *,
    repo_root: Path,
    activation_path: Path | None = None,
) -> dict[str, Any]:
    """Register the exact pinned handoff reference once in memory.

    This function has no filesystem write surface.  It returns the exact
    record, sanitized receipt, and exhausted ledger that the authorized
    wrapper must persist.
    """

    if activation_path is None:
        raise ClaimIDMainlineRegistrationError(
            "missing_activation",
            "a distinct activated single-use registration authority is required",
        )

    repo_root = repo_root.resolve()
    verify_registration_pins(repo_root)
    activation_bytes = _read_activation_bytes(activation_path)
    activation = _decode_json_bytes(activation_bytes, "activation")
    activation_sha256 = hashlib.sha256(activation_bytes).hexdigest()
    executor_sha256 = _sha256(repo_root / EXECUTOR_PATH)
    authority = _validate_activation(
        activation,
        repo_root=repo_root,
        executor_sha256=executor_sha256,
    )

    package_bytes = (repo_root / INGESTED_FIXTURE_PATH).read_bytes()
    ingestion_receipt_bytes = (repo_root / SANITIZED_RECEIPT_PATH).read_bytes()
    handoff_payload = build_claim_id_mainline_handoff(
        package_bytes,
        ingestion_receipt_bytes,
        repo_root=repo_root,
        consumer_contract_ref={
            "effective_artifact_id": EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
            "effective_version": EFFECTIVE_CONSUMER_CONTRACT_VERSION,
            "effective_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
        },
    )

    record = _build_registration_record(
        handoff_payload,
        authority=authority,
        activation_sha256=activation_sha256,
        executor_sha256=executor_sha256,
    )
    receipt = _build_sanitized_registration_receipt(
        record,
        authority=authority,
        activation_sha256=activation_sha256,
        executor_sha256=executor_sha256,
    )
    return {
        "registration_record": record,
        "sanitized_receipt": receipt,
        "activation_sha256_before": activation_sha256,
        "execute_ledger_after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
    }


def _validate_authority_design(value: Any) -> None:
    design = _require_mapping(value, "authority_design", "authority_design")
    for field, expected in (
        ("artifact_id", AUTHORITY_DESIGN_ARTIFACT_ID),
        ("artifact_type", "production_claim_id_mainline_registration_single_execute_authority_design"),
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
        ("production_registration_enabled", False),
        ("production_registration_performed", False),
    ):
        _require_constant(
            current.get(field),
            expected,
            f"authority_design.current_authorization_state.{field}",
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
        "authority_design.future_activation_shape.status",
        "authority_design",
    )
    _require_exact_mapping(
        future.get("execute_ledger"),
        _EXPECTED_LEDGER_BEFORE,
        "authority_design.future_activation_shape.execute_ledger",
        "authority_design",
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
        raise ClaimIDMainlineRegistrationError(
            "activation_shape", "activation fields are not canonical"
        )
    artifact_id = activation.get("artifact_id")
    if not isinstance(artifact_id, str) or not _ACTIVATION_ID_PATTERN.fullmatch(
        artifact_id
    ):
        raise ClaimIDMainlineRegistrationError(
            "activation_shape", "activation artifact id is invalid"
        )
    for field, expected in (
        ("artifact_type", "production_claim_id_mainline_registration_single_execute_activation"),
        ("version", "0.1"),
        ("created_date", "2026-07-25"),
        ("authority_base_commit", AUTHORITY_BASE_COMMIT),
        ("status", ACTIVATION_STATUS),
    ):
        _require_constant(
            activation.get(field), expected, f"activation.{field}", "not_activated"
        )
    _require_exact_mapping(
        activation.get("authority_design"),
        _EXPECTED_AUTHORITY_DESIGN_REF,
        "activation.authority_design",
        "authority_design_pin",
    )
    _require_exact_mapping(
        activation.get("target"),
        _EXPECTED_TARGET,
        "activation.target",
        "activation_target",
    )
    expected_pins = dict(_EXPECTED_STATIC_PINS)
    expected_pins["registration_executor_sha256"] = executor_sha256
    _require_exact_mapping(
        activation.get("pinned_hashes"),
        expected_pins,
        "activation.pinned_hashes",
        "activation_pin",
    )
    _require_exact_mapping(
        activation.get("selected_input"),
        _EXPECTED_SELECTED_INPUT,
        "activation.selected_input",
        "selected_input",
    )
    _require_exact_mapping(
        activation.get("execute_ledger"),
        _EXPECTED_LEDGER_BEFORE,
        "activation.execute_ledger",
        "activation_ledger",
    )
    if activation.get("execution_audit") is not None:
        raise ClaimIDMainlineRegistrationError(
            "activation_ledger", "activation already contains execution audit data"
        )
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
        raise ClaimIDMainlineRegistrationError(
            "output_policy", "activation output policy fields are not canonical"
        )
    for field, expected in (
        ("mode", "versioned_audit_registration_only"),
        ("registration_record_write", True),
        ("sanitized_receipt_write", True),
        ("kernel_store_write", False),
        ("e_case_write", False),
        ("certificate_generation", False),
        ("certified_stop", False),
        ("production_control_loop_wiring", False),
        ("planner_wiring", False),
        ("claim_lifecycle_mutation", False),
    ):
        _require_constant(
            policy.get(field), expected, f"activation.output_policy.{field}", "output_policy"
        )
    record_path = _validate_output_path(
        policy.get("registration_record_path"),
        repo_root,
        "activation.output_policy.registration_record_path",
    )
    receipt_path = _validate_output_path(
        policy.get("sanitized_receipt_path"),
        repo_root,
        "activation.output_policy.sanitized_receipt_path",
    )
    if record_path == receipt_path:
        raise ClaimIDMainlineRegistrationError(
            "output_policy", "record and receipt paths must be distinct"
        )


def _validate_output_path(value: Any, repo_root: Path, field: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ClaimIDMainlineRegistrationError(
            "output_policy", f"{field} must be a non-empty POSIX-style path"
        )
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ClaimIDMainlineRegistrationError(
            "output_policy", f"{field} must remain repository-relative"
        )
    if not (
        value.startswith(
            "docs/llm-editor/fixtures/claim-id-mainline-registration/"
        )
        or value.startswith(".tmp/compiler-contract/")
    ):
        raise ClaimIDMainlineRegistrationError(
            "output_policy", f"{field} is outside the allowed audit roots"
        )
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ClaimIDMainlineRegistrationError(
            "output_policy", f"{field} escapes the repository"
        ) from exc
    if resolved.exists():
        raise ClaimIDMainlineRegistrationError(
            "output_exists", f"{field} already exists"
        )
    return resolved


def _build_registration_record(
    handoff_payload: Mapping[str, Any],
    *,
    authority: Mapping[str, Any],
    activation_sha256: str,
    executor_sha256: str,
) -> dict[str, Any]:
    record_digest = hashlib.sha256(
        "\0".join(
            (
                "claim-id-mainline-registration-record-v0.1",
                activation_sha256,
                executor_sha256,
                INGESTED_FIXTURE_SHA256,
                SANITIZED_RECEIPT_SHA256,
            )
        ).encode("utf-8")
    ).hexdigest()
    return {
        "record_version": "claim-id-mainline-registration-record-v0.1",
        "record_id": f"cir_{record_digest[:32]}",
        "status": RECORD_STATUS,
        "registration_scope": "versioned_audit_registration_only_not_control_loop_wiring",
        "surface_id": SURFACE_ID,
        "package_id": PACKAGE_ID,
        "handoff_reference": copy.deepcopy(dict(handoff_payload)),
        "authority": {
            "artifact_id": authority["artifact_id"],
            "activation_sha256": activation_sha256,
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "registration_executor_sha256": executor_sha256,
            "execute_ledger_before": copy.deepcopy(_EXPECTED_LEDGER_BEFORE),
            "execute_ledger_after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
        },
        "input_pins": {
            "effective_consumer_contract_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
            "external_envelope_schema_sha256": SCHEMA_SHA256,
            "ingested_fixture_sha256": INGESTED_FIXTURE_SHA256,
            "sanitized_ingestion_receipt_sha256": SANITIZED_RECEIPT_SHA256,
        },
        "identity_preservation": {
            "package_id_unchanged": True,
            "claim_ids_unchanged": True,
            "claim_id_state_unchanged": True,
            "admission_state_unchanged": True,
            "kernel_state_unchanged": True,
            "claim_content_unchanged": True,
        },
        "registration_effect": {
            "exact_pinned_handoff_reference_recorded": True,
            "activation_scoped_single_execute_exception": True,
            "global_permanent_registration_switch_observed": False,
            "global_permanent_registration_switch_mutated": False,
            "production_control_loop_wiring": False,
            "planner_wiring": False,
        },
        "side_effects": {
            "kernel_store_write": False,
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


def _build_sanitized_registration_receipt(
    record: Mapping[str, Any],
    *,
    authority: Mapping[str, Any],
    activation_sha256: str,
    executor_sha256: str,
) -> dict[str, Any]:
    record_sha256 = _canonical_json_sha256(record)
    receipt_digest = hashlib.sha256(
        f"{record_sha256}\0{activation_sha256}\0{executor_sha256}".encode("utf-8")
    ).hexdigest()
    output_policy = authority["output_policy"]
    return {
        "receipt_version": "claim-id-mainline-registration-receipt-v0.1",
        "receipt_id": f"cirr_{receipt_digest[:32]}",
        "receipt_scope": "sanitized_versioned_audit_registration_only",
        "decision": "registered_once_under_single_execute_authority",
        "authority": {
            "artifact_id": authority["artifact_id"],
            "activation_sha256": activation_sha256,
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "registration_executor_sha256": executor_sha256,
        },
        "input": {
            "surface_id": SURFACE_ID,
            "package_id": PACKAGE_ID,
            "ingested_fixture_sha256": INGESTED_FIXTURE_SHA256,
            "sanitized_ingestion_receipt_sha256": SANITIZED_RECEIPT_SHA256,
            "claim_count": CLAIM_COUNT,
            "claims_content_hash": CLAIMS_CONTENT_HASH,
            "claim_id_list_sha256": CLAIM_ID_LIST_SHA256,
        },
        "output": {
            "registration_record_path": output_policy["registration_record_path"],
            "registration_record_canonical_sha256": record_sha256,
            "sanitized_receipt_path": output_policy["sanitized_receipt_path"],
        },
        "execute_ledger_before": copy.deepcopy(_EXPECTED_LEDGER_BEFORE),
        "execute_ledger_after_required": copy.deepcopy(_EXPECTED_LEDGER_AFTER),
        "registration_switch_boundary": {
            "symbol": "PRODUCTION_REGISTRATION_ENABLED",
            "observed_value": False,
            "mutated_during_execution": False,
            "activation_scoped_single_execute_exception": True,
            "permanent_registration_enabled": False,
        },
        "wrapper_audit_boundary": {
            "executor_file_write": False,
            "versioned_registration_record_write_authorized": True,
            "versioned_sanitized_receipt_write_authorized": True,
            "activation_ledger_exhaustion_write_required": True,
        },
        "side_effects": copy.deepcopy(record["side_effects"]),
    }


def _require_global_switch_disabled() -> None:
    if handoff_module.PRODUCTION_REGISTRATION_ENABLED is not False:
        raise ClaimIDMainlineRegistrationError(
            "global_kill_switch",
            "PRODUCTION_REGISTRATION_ENABLED must remain False; activation is the only single-use exception",
        )


def _read_activation_bytes(path: Path) -> bytes:
    try:
        data = Path(path).read_bytes()
    except (OSError, TypeError) as exc:
        raise ClaimIDMainlineRegistrationError(
            "activation_unavailable", "activation artifact could not be read"
        ) from exc
    if len(data) > _MAX_ACTIVATION_BYTES:
        raise ClaimIDMainlineRegistrationError(
            "activation_shape", "activation artifact exceeds the size limit"
        )
    return data


def _decode_json_bytes(value: bytes, kind: str) -> dict[str, Any]:
    try:
        decoded = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ClaimIDMainlineRegistrationError(
            f"{kind}_encoding", f"{kind} must be UTF-8"
        ) from exc
    try:
        parsed = json.loads(decoded, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ClaimIDMainlineRegistrationError(
            f"{kind}_json", f"{kind} must be strict JSON without duplicate keys"
        ) from exc
    if not isinstance(parsed, dict):
        raise ClaimIDMainlineRegistrationError(
            f"{kind}_shape", f"{kind} must be a JSON object"
        )
    return parsed


def _reject_secret_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")
            parts = set(normalized.split("_"))
            if parts.intersection(
                {"secret", "password", "passwd", "credential", "token", "hmac", "key"}
            ):
                raise ClaimIDMainlineRegistrationError(
                    "secret_field", f"secret-like field is forbidden at {'.'.join(path + (str(key),))}"
                )
            _reject_secret_keys(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_keys(child, path + (str(index),))


def _require_mapping(value: Any, field: str, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaimIDMainlineRegistrationError(code, f"{field} must be an object")
    return value


def _require_exact_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    code: str,
) -> None:
    if not isinstance(value, Mapping) or dict(value) != dict(expected):
        raise ClaimIDMainlineRegistrationError(
            code, f"{field} does not match the frozen shape"
        )


def _require_constant(
    value: Any,
    expected: Any,
    field: str,
    code: str,
) -> None:
    if value != expected or type(value) is not type(expected):
        raise ClaimIDMainlineRegistrationError(
            code, f"{field} must equal {expected!r}"
        )


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise ClaimIDMainlineRegistrationError(
            "pin_missing", f"pinned artifact is missing: {relative_path}"
        )
    actual = _sha256(path)
    if actual != expected_sha:
        raise ClaimIDMainlineRegistrationError(
            "pin_mismatch", f"pinned artifact mismatch: {relative_path}"
        )


def _load_json(path: Path) -> dict[str, Any]:
    return _decode_json_bytes(path.read_bytes(), path.as_posix())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result
