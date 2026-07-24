"""Fail-closed, in-memory Claim IR admission executor.

The executor recognizes exactly two frozen project05_depth2_public candidate
identities.  It performs no file writes, minting, Kernel/E_case updates,
certificate generation, or catalog/role/credit/L2 changes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any


SURFACE_ID = "project05_depth2_public"
SOURCE_CLASS = "planner_experiment_inputs"
ADAPTER_ID = "m1a_planner_inputs_v0_1"

ADMISSION_CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-ir-admission-contract-design-v0.1-20260724.json"
)
ADMISSION_CONTRACT_SHA256 = (
    "623cc44ce3d07f64e6c3f45b7fa96e11044d727703a0e27ec20578a980053ef3"
)
ADMISSION_AUTHORITY_DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-ir-admission-single-execute-authority-design-"
    "v0.1-20260724.json"
)
ADMISSION_AUTHORITY_DESIGN_SHA256 = (
    "44fc0900852cae0f325d2929cd6fc938949438e8b55cbdf56836532a16bc3d7b"
)
SCHEMA_PATH = "schemas/claim-ir-kernel.schema.json"
SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
PROJECTION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-m0-depth2-public-field-projection-"
    "v0.1-20260724.json"
)
PROJECTION_SHA256 = (
    "4784ff3a29f2c3cb8d04bc187b1f2cd1d95b9ead51c3ad0d7c4da30f4cd557e8"
)
DUAL_PATH_DISPOSITION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-dual-path-single-execute-completion-disposition-"
    "v0.1-20260724.json"
)
DUAL_PATH_DISPOSITION_SHA256 = (
    "101edb00b14dd548d9a579a6ffb9457e4a5b5605a24813e261222ffef8838cf2"
)

ELIGIBLE_CANDIDATES = MappingProxyType(
    {
        "structural_planner_inputs_package": MappingProxyType(
            {
                "candidate_kind": "structural_package",
                "sha256": (
                    "a97dcdd63974cb86afd1cd76de23df41f178fbcedf4657c3345d5253f0e9a650"
                ),
                "claim_id_state": "not_minted",
            }
        ),
        "minted_planner_inputs_package": MappingProxyType(
            {
                "candidate_kind": "minted_package",
                "sha256": (
                    "29a260fe46c3ccf45822e4e2b8d2085cfb6fef0b6a9a0edddfe9a30462cbb1a9"
                ),
                "claim_id_state": "minted_opaque",
            }
        ),
    }
)

_EXPECTED_AUTHORITY_FIELDS = frozenset(
    {
        "status",
        "target",
        "pinned_hashes",
        "selected_candidates",
        "pi_approval_ref",
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
_EXPECTED_LEDGER = {
    "authorized": 1,
    "maximum": 1,
    "started": 0,
    "consumed": 0,
    "remaining": 1,
    "retry": False,
    "resume": False,
    "fallback": False,
}
_EXPECTED_OUTPUT_POLICY = {
    "mode": "in_memory_admission_only",
    "file_write": False,
    "mint": False,
    "claim_id_transition": False,
    "kernel_write": False,
    "certificate_generation": False,
}
_EXPECTED_STILL_BLOCKED = {
    "kernel_write": True,
    "e_case_write": True,
    "certificate_generation": True,
    "catalog_write": True,
    "source_role_assignment": True,
    "lineage_credit": True,
    "quota_credit": True,
    "l2_gate_change": True,
    "m2_fit": True,
    "four_family_llm_finetune": True,
}
_EXPECTED_APPROVAL_FIELDS = frozenset(
    {
        "artifact_id",
        "artifact_type",
        "status",
        "approver_role",
        "target",
        "selected_candidate",
        "pinned_hashes",
    }
)
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
        "random_seed",
        "run_id",
        "raw_path",
        "filesystem_path",
        "archive_member_path",
        "member_path",
        "payload",
        "payload_bytes",
        "raw_payload",
        "private_evidence",
        "hidden_evidence",
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
        "credential",
        "credentials",
    }
)
_CLAIM_ID_PATTERN = re.compile(r"^clm_[A-Za-z0-9_-]+$")
_ARTIFACT_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_MAX_PACKAGE_BYTES = 2 * 1024 * 1024


class ClaimIRAdmissionError(ValueError):
    """Raised when an admission request fails a closed boundary."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def verify_admission_pins(repo_root: Path) -> None:
    """Verify the frozen admission designs and inherited public-surface pins."""

    repo_root = repo_root.resolve()
    for relative_path, expected_sha in (
        (ADMISSION_CONTRACT_PATH, ADMISSION_CONTRACT_SHA256),
        (
            ADMISSION_AUTHORITY_DESIGN_PATH,
            ADMISSION_AUTHORITY_DESIGN_SHA256,
        ),
        (SCHEMA_PATH, SCHEMA_SHA256),
        (PROJECTION_PATH, PROJECTION_SHA256),
        (DUAL_PATH_DISPOSITION_PATH, DUAL_PATH_DISPOSITION_SHA256),
    ):
        _verify_pin(repo_root, relative_path, expected_sha)

    contract = _load_json(repo_root / ADMISSION_CONTRACT_PATH)
    if not isinstance(contract, Mapping):
        raise ClaimIRAdmissionError(
            "contract_shape",
            "admission contract must be an object",
        )
    _require_constant(
        contract.get("status"),
        "design_only_admission_not_authorized",
        "contract.status",
    )
    scope = contract.get("scope")
    _require_target_scope(scope, "contract.scope")
    success = contract.get("future_success_state_design")
    if not isinstance(success, Mapping):
        raise ClaimIRAdmissionError(
            "contract_shape",
            "future success state is missing",
        )
    for field, expected in (
        ("package_admission_state", "admitted_under_separate_authority"),
        ("per_claim_admission_state", "admitted_under_separate_authority"),
        ("claim_id_state_transition_performed", False),
        ("kernel_state", "pending_kernel_schema"),
        ("certificate_surface", "vacant"),
    ):
        _require_constant(success.get(field), expected, f"contract.success.{field}")

    design = _load_json(repo_root / ADMISSION_AUTHORITY_DESIGN_PATH)
    if not isinstance(design, Mapping):
        raise ClaimIRAdmissionError(
            "authority_design_shape",
            "admission authority design must be an object",
        )
    _require_constant(
        design.get("status"),
        "design_only_admission_authority_not_activated",
        "authority_design.status",
    )
    _require_target_scope(design.get("scope"), "authority_design.scope")
    current = design.get("current_authorization_state")
    if not isinstance(current, Mapping):
        raise ClaimIRAdmissionError(
            "authority_design_shape",
            "current authorization state is missing",
        )
    for field, expected in (
        ("activated", False),
        ("admission_execute_authorized_now", 0),
        ("candidate_selected_now", False),
        ("selected_candidate", None),
        ("pi_approval_artifact_present_now", False),
        ("admission_executed", False),
    ):
        _require_constant(
            current.get(field),
            expected,
            f"authority_design.current.{field}",
        )

    candidates = design.get("eligible_candidate_set")
    if not isinstance(candidates, Mapping):
        raise ClaimIRAdmissionError(
            "authority_design_shape",
            "eligible candidate set is missing",
        )
    _require_constant(
        candidates.get("selection_cardinality_at_activation"),
        "exactly_one",
        "authority_design.candidates.selection_cardinality",
    )
    entries = candidates.get("candidates")
    if not isinstance(entries, list) or len(entries) != 2:
        raise ClaimIRAdmissionError(
            "authority_design_candidates",
            "authority design must contain exactly two candidates",
        )
    observed = {
        entry.get("candidate_id"): {
            "candidate_kind": entry.get("candidate_kind"),
            "sha256": entry.get("sha256"),
            "claim_id_state": entry.get("claim_id_state"),
        }
        for entry in entries
        if isinstance(entry, Mapping)
    }
    expected = {
        candidate_id: dict(spec)
        for candidate_id, spec in ELIGIBLE_CANDIDATES.items()
    }
    if observed != expected:
        raise ClaimIRAdmissionError(
            "authority_design_candidates",
            "authority design candidate registry does not match",
        )

    future = design.get("future_activation_shape")
    if not isinstance(future, Mapping):
        raise ClaimIRAdmissionError(
            "authority_design_shape",
            "future activation shape is missing",
        )
    _require_constant(
        future.get("status"),
        "activated_single_admission_execute_authorized",
        "authority_design.future.status",
    )
    _require_typed_mapping(
        future.get("execute_ledger"),
        _EXPECTED_LEDGER,
        "authority_design.future.execute_ledger",
        "authority_design_ledger",
    )
    approval = future.get("pi_approval_requirement")
    if not isinstance(approval, Mapping):
        raise ClaimIRAdmissionError(
            "authority_design_shape",
            "PI approval requirement is missing",
        )
    _require_constant(
        approval.get("approver_role"),
        "PI",
        "authority_design.future.pi_approval.approver_role",
    )
    _require_constant(
        approval.get("this_design_is_pi_approval"),
        False,
        "authority_design.future.pi_approval.this_design_is_pi_approval",
    )


def admit_claim_ir_package(
    package_bytes: bytes,
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
    pi_approval: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Admit one exact candidate in memory after every authority gate passes."""

    verify_admission_pins(repo_root)
    selected = _validate_authority(authority)
    _validate_pi_approval(pi_approval, authority, selected)
    package = _load_candidate_package(package_bytes, selected)
    return _admit_in_memory(package)


def _validate_authority(
    authority: Mapping[str, Any] | None,
) -> dict[str, str]:
    if authority is None:
        raise ClaimIRAdmissionError(
            "missing_authority",
            "activated admission authority is required",
        )
    if not isinstance(authority, Mapping):
        raise ClaimIRAdmissionError(
            "authority_type",
            "admission authority must be an object",
        )
    _reject_secret_keys(authority)
    if set(authority) != _EXPECTED_AUTHORITY_FIELDS:
        raise ClaimIRAdmissionError(
            "authority_shape",
            "admission authority fields are not canonical",
        )
    if authority.get("status") != "activated_single_admission_execute_authorized":
        raise ClaimIRAdmissionError(
            "not_activated",
            "admission authority is not activated",
        )
    _require_typed_mapping(
        authority.get("target"),
        {
            "surface_id": SURFACE_ID,
            "source_class": SOURCE_CLASS,
            "adapter_id": ADAPTER_ID,
            "only_target": True,
        },
        "authority.target",
        "authority_target",
    )
    _require_typed_mapping(
        authority.get("pinned_hashes"),
        {
            "admission_contract_sha256": ADMISSION_CONTRACT_SHA256,
            "admission_authority_design_sha256": (
                ADMISSION_AUTHORITY_DESIGN_SHA256
            ),
            "schema_sha256": SCHEMA_SHA256,
            "projection_sha256": PROJECTION_SHA256,
            "dual_path_disposition_sha256": DUAL_PATH_DISPOSITION_SHA256,
        },
        "authority.pinned_hashes",
        "authority_pin",
    )

    selected_candidates = authority.get("selected_candidates")
    if not isinstance(selected_candidates, list) or len(selected_candidates) != 1:
        raise ClaimIRAdmissionError(
            "candidate_selection",
            "authority must select exactly one candidate",
        )
    selected = selected_candidates[0]
    if not isinstance(selected, Mapping) or set(selected) != {
        "candidate_id",
        "candidate_kind",
        "sha256",
    }:
        raise ClaimIRAdmissionError(
            "candidate_selection",
            "selected candidate fields are not canonical",
        )
    candidate_id = selected.get("candidate_id")
    spec = ELIGIBLE_CANDIDATES.get(candidate_id)
    if (
        not isinstance(candidate_id, str)
        or spec is None
        or selected.get("candidate_kind") != spec["candidate_kind"]
        or selected.get("sha256") != spec["sha256"]
    ):
        raise ClaimIRAdmissionError(
            "candidate_pin",
            "selected candidate is not one exact eligible identity",
        )

    _require_typed_mapping(
        authority.get("execute_ledger"),
        _EXPECTED_LEDGER,
        "authority.execute_ledger",
        "authority_ledger",
    )
    _require_typed_mapping(
        authority.get("output_policy"),
        _EXPECTED_OUTPUT_POLICY,
        "authority.output_policy",
        "authority_boundary",
    )
    _require_typed_mapping(
        authority.get("still_blocked"),
        _EXPECTED_STILL_BLOCKED,
        "authority.still_blocked",
        "authority_boundary",
    )
    return {
        "candidate_id": candidate_id,
        "candidate_kind": spec["candidate_kind"],
        "sha256": spec["sha256"],
        "claim_id_state": spec["claim_id_state"],
    }


def _validate_pi_approval(
    pi_approval: Mapping[str, Any] | None,
    authority: Mapping[str, Any],
    selected: Mapping[str, str],
) -> None:
    if pi_approval is None:
        raise ClaimIRAdmissionError(
            "missing_pi_approval",
            "separate PI approval artifact is required",
        )
    if not isinstance(pi_approval, Mapping):
        raise ClaimIRAdmissionError(
            "pi_approval",
            "PI approval artifact must be an object",
        )
    _reject_secret_keys(pi_approval)
    if set(pi_approval) != _EXPECTED_APPROVAL_FIELDS:
        raise ClaimIRAdmissionError(
            "pi_approval",
            "PI approval fields are not canonical",
        )
    artifact_id = pi_approval.get("artifact_id")
    if not isinstance(artifact_id, str) or not _ARTIFACT_ID_PATTERN.fullmatch(
        artifact_id
    ):
        raise ClaimIRAdmissionError(
            "pi_approval",
            "PI approval artifact ID is invalid",
        )
    for field, expected in (
        ("artifact_type", "claim_ir_admission_pi_approval"),
        ("status", "approved_single_admission_candidate"),
        ("approver_role", "PI"),
    ):
        _require_constant(
            pi_approval.get(field),
            expected,
            f"pi_approval.{field}",
            error_code="pi_approval",
        )
    _require_typed_mapping(
        pi_approval.get("target"),
        {
            "surface_id": SURFACE_ID,
            "source_class": SOURCE_CLASS,
            "adapter_id": ADAPTER_ID,
        },
        "pi_approval.target",
        "pi_approval",
    )
    _require_typed_mapping(
        pi_approval.get("selected_candidate"),
        {
            "candidate_id": selected["candidate_id"],
            "candidate_kind": selected["candidate_kind"],
            "sha256": selected["sha256"],
        },
        "pi_approval.selected_candidate",
        "pi_approval",
    )
    _require_typed_mapping(
        pi_approval.get("pinned_hashes"),
        {
            "admission_contract_sha256": ADMISSION_CONTRACT_SHA256,
            "admission_authority_design_sha256": (
                ADMISSION_AUTHORITY_DESIGN_SHA256
            ),
            "schema_sha256": SCHEMA_SHA256,
        },
        "pi_approval.pinned_hashes",
        "pi_approval",
    )

    approval_ref = authority.get("pi_approval_ref")
    _require_typed_mapping(
        approval_ref,
        {
            "artifact_id": artifact_id,
            "sha256": _canonical_json_sha256(pi_approval),
            "approver_role": "PI",
        },
        "authority.pi_approval_ref",
        "pi_approval",
    )


def _load_candidate_package(
    package_bytes: bytes,
    selected: Mapping[str, str],
) -> dict[str, Any]:
    if not isinstance(package_bytes, bytes):
        raise ClaimIRAdmissionError(
            "package_type",
            "candidate package must be provided as immutable bytes",
        )
    if not package_bytes or len(package_bytes) > _MAX_PACKAGE_BYTES:
        raise ClaimIRAdmissionError(
            "package_size",
            "candidate package byte length is empty or exceeds the bound",
        )
    if hashlib.sha256(package_bytes).hexdigest() != selected["sha256"]:
        raise ClaimIRAdmissionError(
            "candidate_pin",
            "candidate package bytes do not match the selected SHA",
        )
    try:
        package = json.loads(package_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClaimIRAdmissionError(
            "package_json",
            "candidate package is not valid UTF-8 JSON",
        ) from exc
    if not isinstance(package, dict):
        raise ClaimIRAdmissionError(
            "package_shape",
            "candidate package must decode to an object",
        )
    _reject_forbidden_package_keys(package)
    _validate_candidate_package(package, selected)
    return package


def _validate_candidate_package(
    package: Mapping[str, Any],
    selected: Mapping[str, str],
) -> None:
    if set(package) != _EXPECTED_PACKAGE_FIELDS:
        raise ClaimIRAdmissionError(
            "package_shape",
            "candidate package fields are not canonical",
        )
    for field, expected in (
        ("schema_version", "claim-ir-external-v0.1"),
        ("surface_id", SURFACE_ID),
        ("kernel_state", "pending_kernel_schema"),
        ("claim_id_state", selected["claim_id_state"]),
        ("admission_state", "not_admitted"),
    ):
        _require_constant(
            package.get(field),
            expected,
            f"package.{field}",
            error_code="package_state",
        )
    projection = package.get("projection_ref")
    if (
        not isinstance(projection, Mapping)
        or projection.get("path") != PROJECTION_PATH
        or projection.get("sha256") != PROJECTION_SHA256
        or projection.get("surface_id") != SURFACE_ID
    ):
        raise ClaimIRAdmissionError(
            "package_projection",
            "candidate package projection pin is invalid",
        )
    claims = package.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ClaimIRAdmissionError(
            "package_claims",
            "candidate package must contain claims",
        )
    identifiers: set[str] = set()
    for claim in claims:
        if not isinstance(claim, Mapping) or set(claim) != _EXPECTED_CLAIM_FIELDS:
            raise ClaimIRAdmissionError(
                "claim_shape",
                "candidate claim fields are not canonical",
            )
        _require_constant(
            claim.get("claim_id_state"),
            selected["claim_id_state"],
            "claim.claim_id_state",
            error_code="package_state",
        )
        _require_constant(
            claim.get("admission_state"),
            "not_admitted",
            "claim.admission_state",
            error_code="package_state",
        )
        identifier = claim.get("claim_id")
        if selected["claim_id_state"] == "not_minted":
            _require_constant(
                identifier,
                None,
                "claim.claim_id",
                error_code="package_state",
            )
        elif (
            not isinstance(identifier, str)
            or not _CLAIM_ID_PATTERN.fullmatch(identifier)
            or identifier in identifiers
        ):
            raise ClaimIRAdmissionError(
                "package_claim_id",
                "minted candidate Claim-IDs must be opaque and unique",
            )
        else:
            identifiers.add(identifier)


def _admit_in_memory(package: Mapping[str, Any]) -> dict[str, Any]:
    admitted = copy.deepcopy(dict(package))
    admitted["admission_state"] = "admitted_under_separate_authority"
    for claim in admitted["claims"]:
        claim["admission_state"] = "admitted_under_separate_authority"
    admitted["manifest"]["content_hash"] = hashlib.sha256(
        json.dumps(
            admitted["claims"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    admitted["kernel_state"] = "pending_kernel_schema"
    return admitted


def _require_target_scope(value: Any, field: str) -> None:
    if not isinstance(value, Mapping):
        raise ClaimIRAdmissionError(
            "scope_shape",
            f"{field} must be an object",
        )
    for key, expected in (
        ("surface_id", SURFACE_ID),
        ("source_class", SOURCE_CLASS),
        ("adapter_id", ADAPTER_ID),
        ("certificate_surface", "vacant"),
    ):
        _require_constant(value.get(key), expected, f"{field}.{key}")


def _require_typed_mapping(
    value: Any,
    expected: Mapping[str, Any],
    field: str,
    error_code: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise ClaimIRAdmissionError(
            error_code,
            f"{field} does not match the frozen shape",
        )
    for key, expected_value in expected.items():
        actual_value = value.get(key)
        if actual_value != expected_value or type(actual_value) is not type(
            expected_value
        ):
            raise ClaimIRAdmissionError(
                error_code,
                f"{field}.{key} does not match the frozen value",
            )


def _require_constant(
    value: Any,
    expected: Any,
    field: str,
    *,
    error_code: str = "state_mismatch",
) -> None:
    if value != expected or type(value) is not type(expected):
        raise ClaimIRAdmissionError(
            error_code,
            f"{field} must equal {expected!r}",
        )


def _reject_forbidden_package_keys(
    value: Any,
    path: tuple[str, ...] = (),
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            field_path = ".".join((*path, str(key)))
            if normalized in _FORBIDDEN_PACKAGE_KEYS:
                raise ClaimIRAdmissionError(
                    "forbidden_field",
                    f"forbidden candidate field: {field_path}",
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
            field_path = ".".join((*path, str(key)))
            if normalized in _SECRET_AUTHORITY_KEYS:
                raise ClaimIRAdmissionError(
                    "secret_in_authority",
                    f"secret field is forbidden: {field_path}",
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
        raise ClaimIRAdmissionError(
            "pi_approval",
            "PI approval is not canonical JSON",
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def _verify_pin(repo_root: Path, relative_path: str, expected_sha: str) -> None:
    path = repo_root / relative_path
    if not path.is_file():
        raise ClaimIRAdmissionError(
            "pin_missing",
            f"pinned file missing: {relative_path}",
        )
    if _sha256(path) != expected_sha:
        raise ClaimIRAdmissionError(
            "pin_mismatch",
            f"pinned SHA mismatch: {relative_path}",
        )


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClaimIRAdmissionError(
            "json_read",
            f"cannot read JSON artifact: {path.name}",
        ) from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ClaimIRAdmissionError(
            "pin_read",
            f"cannot read pinned artifact: {path.name}",
        ) from exc
    return digest.hexdigest()


def _normalize_key(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")
