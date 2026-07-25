"""Fail-closed opaque Claim-ID mint executor for one public M0 surface.

The executor has no CLI and performs no file writes.  It defaults to an
unavailable key provider and refuses to mint unless a separately activated,
single-use authority artifact passes every pin and boundary check.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import json
import os
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol


SURFACE_ID = "project05_depth2_public"
MINTING_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-minting-design-v0.1-20260724.json"
)
MINTING_DESIGN_SHA256 = (
    "9f57e9c93cdf5ed2493a428177f434f280859789accdbf50ff01483fef91b21c"
)
MAPPING_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-source-field-slot-mapping-design-v0.1-20260724.json"
)
MAPPING_DESIGN_SHA256 = (
    "83d6a685a92dadc8ce0c05ecdd97931a56a207eebaf3c8193201a1daee38c070"
)
SCHEMA_PATH = "schemas/claim-ir-external-envelope.schema.json"
SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
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
_CASE_REFERENCE_FIELDS = frozenset(
    {"config.case_id", "state.case_id", "action.case_id"}
)
_FORBIDDEN_KEYS = frozenset(
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
        "oracle",
        "oracle_path",
        "mask_strategy",
        "mask_intensity",
        "mask_membership",
        "random_seed",
        "run_id",
        "raw_path",
        "filesystem_path",
        "archive_member_path",
        "member_path",
        "payload",
        "payload_bytes",
        "credentials",
        "credential",
        "secrets",
        "secret",
    }
)
_SECRET_AUTHORITY_KEYS = frozenset(
    {
        "hmac_key",
        "key",
        "key_bytes",
        "key_material",
        "secret",
        "secret_bytes",
    }
)
_SLOT_PATTERN = re.compile(r"^afs_[0-9]{4}$")
_KEY_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_OPAQUE_CASE_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")


class ClaimIDMintError(ValueError):
    """Raised when a mint request fails a closed boundary."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class EphemeralKeyProvider(Protocol):
    """Interface for non-persistent key injection."""

    def get_key(self, key_id: str) -> bytearray | None:
        """Return ephemeral key bytes or None without persisting/logging them."""


class UnavailableKeyProvider:
    """Default provider: no key exists and no environment is read."""

    def get_key(self, key_id: str) -> bytearray | None:
        del key_id
        return None


class EnvironmentKeyProvider:
    """Explicit opt-in environment injection; never enabled by default."""

    def __init__(self, prefix: str = "PROJECT05_M0_MINT_KEY_"):
        self._prefix = prefix

    def get_key(self, key_id: str) -> bytearray | None:
        if not _KEY_ID_PATTERN.fullmatch(key_id):
            return None
        variable = self._prefix + re.sub(r"[^A-Za-z0-9]", "_", key_id).upper()
        value = os.environ.get(variable)
        if value is None:
            return None
        return bytearray(value.encode("utf-8"))


def load_and_validate_slot_mapping(repo_root: Path) -> dict[str, str]:
    """Load pins and return the exact 38-field bijection."""

    repo_root = repo_root.resolve()
    _verify_pin(repo_root, MINTING_DESIGN_PATH, MINTING_DESIGN_SHA256)
    _verify_pin(repo_root, MAPPING_DESIGN_PATH, MAPPING_DESIGN_SHA256)
    _verify_pin(repo_root, SCHEMA_PATH, SCHEMA_SHA256)

    minting_design = _load_json(repo_root / MINTING_DESIGN_PATH)
    mapping_design = _load_json(repo_root / MAPPING_DESIGN_PATH)
    schema = _load_json(repo_root / SCHEMA_PATH)
    if (
        not isinstance(minting_design, Mapping)
        or minting_design.get("status") != "design_only_minting_not_authorized"
        or minting_design.get("scope", {}).get("surface_id") != SURFACE_ID
    ):
        raise ClaimIDMintError("minting_design_mismatch", "minting design is not the pinned surface")
    if (
        not isinstance(mapping_design, Mapping)
        or mapping_design.get("status") != "design_only_mapping_not_implemented"
        or mapping_design.get("scope", {}).get("surface_id") != SURFACE_ID
    ):
        raise ClaimIDMintError("mapping_design_mismatch", "mapping design is not the pinned surface")

    schema_fields = _schema_source_fields(schema)
    entries = mapping_design.get("source_field_to_slot")
    if not isinstance(entries, list) or len(entries) != 38:
        raise ClaimIDMintError("mapping_count", "mapping must contain exactly 38 entries")

    fields: list[str] = []
    slots: list[str] = []
    ordinals: list[int] = []
    mapping: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ClaimIDMintError("mapping_shape", "mapping entry must be an object")
        if set(entry) != {"ordinal", "source_field", "allowlisted_source_slot"}:
            raise ClaimIDMintError("mapping_shape", "mapping entry fields are not canonical")
        ordinal = entry["ordinal"]
        field = entry["source_field"]
        slot = entry["allowlisted_source_slot"]
        if (
            not isinstance(ordinal, int)
            or isinstance(ordinal, bool)
            or not isinstance(field, str)
            or not isinstance(slot, str)
        ):
            raise ClaimIDMintError("mapping_type", "mapping entry types are invalid")
        if not _SLOT_PATTERN.fullmatch(slot):
            raise ClaimIDMintError("slot_format", "allowlisted source slot is not opaque/canonical")
        fields.append(field)
        slots.append(slot)
        ordinals.append(ordinal)
        mapping[field] = slot

    if fields != schema_fields:
        raise ClaimIDMintError("mapping_not_total", "mapping is not the schema-ordered total function")
    if ordinals != list(range(1, 39)):
        raise ClaimIDMintError("mapping_ordinal", "mapping ordinals are not contiguous 1..38")
    if len(set(fields)) != 38 or len(set(slots)) != 38 or len(mapping) != 38:
        raise ClaimIDMintError("mapping_duplicate", "mapping fields or slots are duplicated")
    return mapping


def mint_claim_ids(
    package: Mapping[str, Any],
    *,
    repo_root: Path,
    authority_path: Path | None = None,
    key_provider: EphemeralKeyProvider | None = None,
) -> dict[str, Any]:
    """Mint only after all pins, authority, and ephemeral-key gates pass."""

    mapping = load_and_validate_slot_mapping(repo_root)
    _reject_forbidden_keys(package)
    case_reference = _validate_structural_package(package, mapping)
    if authority_path is None:
        raise ClaimIDMintError("missing_authority", "activated execute authority artifact is required")

    authority = _load_json(authority_path)
    key_id = _validate_authority(authority)
    provider = key_provider if key_provider is not None else UnavailableKeyProvider()
    key = provider.get_key(key_id)
    if key is None:
        raise ClaimIDMintError("key_unavailable", "external ephemeral key is unavailable")
    if not isinstance(key, bytearray) or len(key) < 32:
        _zeroize(key)
        raise ClaimIDMintError("key_attestation", "ephemeral key does not satisfy the minimum boundary")

    try:
        return _mint_in_memory(package, mapping, case_reference, key)
    finally:
        _zeroize(key)


def _validate_structural_package(
    package: Mapping[str, Any],
    mapping: Mapping[str, str],
) -> str:
    if not isinstance(package, Mapping):
        raise ClaimIDMintError("package_type", "package must be an object")
    if set(package) != _EXPECTED_PACKAGE_FIELDS:
        raise ClaimIDMintError("package_shape", "package fields are not canonical")
    _require_constant(package["schema_version"], "claim-ir-external-v0.1", "schema_version")
    _require_constant(package["surface_id"], SURFACE_ID, "surface_id")
    _require_constant(package["claim_id_state"], "not_minted", "claim_id_state")
    _require_constant(package["admission_state"], "not_admitted", "admission_state")
    _require_constant(package["kernel_state"], "pending_kernel_schema", "kernel_state")

    claims = package["claims"]
    if not isinstance(claims, list) or not claims:
        raise ClaimIDMintError("claims_shape", "claims must be a non-empty array")
    case_references: set[str] = set()
    for claim in claims:
        if not isinstance(claim, Mapping) or set(claim) != _EXPECTED_CLAIM_FIELDS:
            raise ClaimIDMintError("claim_shape", "claim fields are not canonical")
        if claim["claim_id"] is not None:
            raise ClaimIDMintError("already_minted", "claim_id must be null before mint")
        _require_constant(claim["claim_id_state"], "not_minted", "claim.claim_id_state")
        _require_constant(claim["admission_state"], "not_admitted", "claim.admission_state")
        source_field = claim["source_field"]
        if not isinstance(source_field, str) or source_field not in mapping:
            raise ClaimIDMintError("unmapped_source_field", "claim source_field is not mapped")
        if source_field in _CASE_REFERENCE_FIELDS:
            case_value = claim["value"]
            if not isinstance(case_value, str) or not _OPAQUE_CASE_PATTERN.fullmatch(case_value):
                raise ClaimIDMintError("case_reference", "case reference is not opaque/canonical")
            case_references.add(case_value)
    if len(case_references) != 1:
        raise ClaimIDMintError("case_reference", "package must contain one consistent opaque case reference")
    return next(iter(case_references))


def _validate_authority(authority: Any) -> str:
    if not isinstance(authority, Mapping):
        raise ClaimIDMintError("authority_type", "execute authority must be an object")
    _reject_secret_authority_keys(authority)
    _require_constant(
        authority.get("status"),
        "activated_single_mint_execute_authorized",
        "authority.status",
    )
    _require_constant(authority.get("surface_id"), SURFACE_ID, "authority.surface_id")

    pins = authority.get("pinned_hashes")
    if not isinstance(pins, Mapping) or dict(pins) != {
        "minting_design_sha256": MINTING_DESIGN_SHA256,
        "mapping_design_sha256": MAPPING_DESIGN_SHA256,
        "schema_sha256": SCHEMA_SHA256,
    }:
        raise ClaimIDMintError("authority_pin", "execute authority pins do not match")

    ledger = authority.get("execute_ledger")
    if not isinstance(ledger, Mapping) or dict(ledger) != {
        "authorized": 1,
        "maximum": 1,
        "started": 0,
        "consumed": 0,
        "remaining": 1,
        "retry": False,
        "resume": False,
        "fallback": False,
    }:
        raise ClaimIDMintError("authority_ledger", "execute authority is not an unused single attempt")

    attestation = authority.get("namespace_key_attestation")
    if not isinstance(attestation, Mapping):
        raise ClaimIDMintError("key_attestation", "namespace key attestation is missing")
    key_id = attestation.get("key_id")
    if (
        not isinstance(key_id, str)
        or not _KEY_ID_PATTERN.fullmatch(key_id)
        or attestation.get("key_material_external") is not True
        or attestation.get("key_material_not_logged") is not True
        or attestation.get("key_material_not_committed") is not True
    ):
        raise ClaimIDMintError("key_attestation", "namespace key attestation is invalid")

    boundaries = authority.get("still_blocked")
    required_boundaries = {
        "admission": True,
        "kernel_ingestion": True,
        "certificate": True,
        "catalog": True,
        "source_role": True,
        "lineage_credit": True,
        "quota_credit": True,
        "l2_gate": True,
    }
    if not isinstance(boundaries, Mapping) or dict(boundaries) != required_boundaries:
        raise ClaimIDMintError("authority_boundary", "post-mint boundaries are not fully blocked")
    return key_id


def _mint_in_memory(
    package: Mapping[str, Any],
    mapping: Mapping[str, str],
    case_reference: str,
    key: bytearray,
) -> dict[str, Any]:
    minted = copy.deepcopy(dict(package))
    identifiers: set[str] = set()
    for ordinal, claim in enumerate(minted["claims"], start=1):
        slot = mapping[claim["source_field"]]
        message = "\x00".join(
            (
                "claim-id-mint-v0.1",
                SURFACE_ID,
                slot,
                case_reference,
                str(ordinal),
            )
        ).encode("utf-8")
        digest = hmac.new(bytes(key), message, hashlib.sha256).digest()
        identifier = "clm_" + base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        if identifier in identifiers:
            raise ClaimIDMintError("claim_id_collision", "opaque Claim-ID collision")
        identifiers.add(identifier)
        claim["claim_id"] = identifier
        claim["claim_id_state"] = "minted_opaque"
        claim["admission_state"] = "not_admitted"

    minted["claim_id_state"] = "minted_opaque"
    minted["admission_state"] = "not_admitted"
    minted["kernel_state"] = "pending_kernel_schema"
    minted["manifest"]["content_hash"] = hashlib.sha256(
        json.dumps(
            minted["claims"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return minted


def _schema_source_fields(schema: Any) -> list[str]:
    try:
        fields = schema["$defs"]["source_field"]["enum"]
    except (KeyError, TypeError) as exc:
        raise ClaimIDMintError("schema_shape", "schema source_field enum is unavailable") from exc
    if (
        not isinstance(fields, list)
        or len(fields) != 38
        or any(not isinstance(field, str) for field in fields)
        or len(set(fields)) != 38
    ):
        raise ClaimIDMintError("schema_shape", "schema source_field enum is not 38 unique strings")
    return fields


def _reject_forbidden_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            field_path = ".".join((*path, str(key)))
            if normalized in _FORBIDDEN_KEYS:
                raise ClaimIDMintError("forbidden_field", f"forbidden field: {field_path}")
            _reject_forbidden_keys(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_forbidden_keys(nested, (*path, str(index)))


def _reject_secret_authority_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            if normalized in _SECRET_AUTHORITY_KEYS:
                field_path = ".".join((*path, str(key)))
                raise ClaimIDMintError("secret_in_authority", f"secret field is forbidden: {field_path}")
            _reject_secret_authority_keys(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_secret_authority_keys(nested, (*path, str(index)))


def _require_constant(value: Any, expected: Any, field: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise ClaimIDMintError("state_mismatch", f"{field} must equal {expected!r}")


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise ClaimIDMintError("pin_missing", f"pinned file missing: {relative_path}")
    if _sha256(path) != expected_sha:
        raise ClaimIDMintError("pin_mismatch", f"pinned SHA mismatch: {relative_path}")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClaimIDMintError("json_read", f"cannot read JSON artifact: {path.name}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_key(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


def _zeroize(value: Any) -> None:
    if isinstance(value, bytearray):
        for index in range(len(value)):
            value[index] = 0
