"""Deterministic, non-executing Part B B5 admission-record evaluator.

This module evaluates frozen identity and evidence mappings.  It does not
load or invoke a Planner, select an action, run an evaluation, inspect a
holdout, calculate performance, issue a certificate, or emit system state.
"""

from __future__ import annotations

from collections.abc import Mapping

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
)


LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"
REQUIRED_EVIDENCE_SLOTS = (
    "dependency",
    "parameter",
    "feature_provenance",
    "runtime_conformance",
)

DECISIONS = {
    "admit": (
        "ADMITTED_CONFORMANCE_ONLY",
        "B5-ADM-000-CONFORMANCE-ONLY",
    ),
    "legacy": (
        "DENY_NOT_ADMITTED_UNVERIFIED",
        "B5-ADM-LEGACY-NOT-ADMITTED",
    ),
    "unknown": (
        "DENY_UNKNOWN_IMPLEMENTATION",
        "B5-ADM-UNKNOWN-ID",
    ),
    "incomplete": (
        "DENY_EVIDENCE_INCOMPLETE",
        "B5-ADM-EVIDENCE-INCOMPLETE",
    ),
    "mismatch": (
        "DENY_EVIDENCE_HASH_MISMATCH",
        "B5-ADM-EVIDENCE-HASH-MISMATCH",
    ),
    "runtime_failed": (
        "DENY_RUNTIME_CONFORMANCE_FAILED",
        "B5-ADM-RUNTIME-CONFORMANCE-FAILED",
    ),
}


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _select_decision(
    *,
    identity: Mapping[str, object],
    evidence: Mapping[str, object],
    policy: Mapping[str, object],
) -> tuple[str, str]:
    implementation_id = identity.get("implementation_id")
    if implementation_id == LEGACY_IMPLEMENTATION_ID:
        return DECISIONS["legacy"]

    admissible_ids = policy.get("admissible_implementation_ids")
    if (
        not isinstance(implementation_id, str)
        or not isinstance(admissible_ids, list)
        or implementation_id not in admissible_ids
    ):
        return DECISIONS["unknown"]

    slots = _mapping(evidence.get("evidence_slots"))
    if (
        evidence.get("implementation_id") != implementation_id
        or set(slots) != set(REQUIRED_EVIDENCE_SLOTS)
    ):
        return DECISIONS["incomplete"]

    identity_hash = identity.get("hash")
    if evidence.get("implementation_identity_hash") != identity_hash:
        return DECISIONS["mismatch"]

    identity_hashes = _mapping(identity.get("identity_hashes"))
    hash_bindings = _mapping(policy.get("evidence_hash_bindings"))
    for slot_name in REQUIRED_EVIDENCE_SLOTS:
        slot = _mapping(slots.get(slot_name))
        identity_hash_field = hash_bindings.get(slot_name)
        if (
            not isinstance(identity_hash_field, str)
            or slot.get("artifact_hash")
            != identity_hashes.get(identity_hash_field)
        ):
            return DECISIONS["mismatch"]

    runtime_slot = _mapping(slots.get("runtime_conformance"))
    if runtime_slot.get("status") != "VERIFIED":
        return DECISIONS["runtime_failed"]

    for slot_name in REQUIRED_EVIDENCE_SLOTS:
        slot = _mapping(slots.get(slot_name))
        if slot.get("status") != "VERIFIED":
            return DECISIONS["incomplete"]

    return DECISIONS["admit"]


def evaluate_admission(
    *,
    identity: Mapping[str, object],
    evidence: Mapping[str, object],
    policy: Mapping[str, object],
) -> dict[str, object]:
    """Return one deterministic evidence-bound admission record."""

    if not all(
        isinstance(value, Mapping)
        for value in (identity, evidence, policy)
    ):
        raise ValueError("identity, evidence and policy must be mappings")

    decision, reason_code = _select_decision(
        identity=identity,
        evidence=evidence,
        policy=policy,
    )
    implementation_id = identity.get("implementation_id")
    if not isinstance(implementation_id, str) or not implementation_id:
        implementation_id = "INVALID_IMPLEMENTATION_ID"

    identity_hash = identity.get("hash")
    if not isinstance(identity_hash, str):
        identity_hash = canonical_value_hash(
            {"invalid_identity": implementation_id}
        )
    evidence_hash = evidence.get("hash")
    if not isinstance(evidence_hash, str):
        evidence_hash = canonical_value_hash(
            {"invalid_evidence_for": implementation_id}
        )
    policy_hash = policy.get("hash")
    if not isinstance(policy_hash, str):
        policy_hash = canonical_value_hash({"invalid_policy": True})

    record_identity = {
        "implementation_id": implementation_id,
        "implementation_identity_hash": identity_hash,
        "admission_evidence_hash": evidence_hash,
        "policy_hash": policy_hash,
        "decision": decision,
        "reason_codes": [reason_code],
        "admission_scope": "INTERFACE_CONFORMANCE_ONLY",
    }
    record = {
        "schema_version": "0.8.0",
        "record_id": canonical_value_hash(record_identity),
        "record_version": "0.8.0",
        **record_identity,
        "planner_execution_authority": False,
        "evaluation_execution_authority": False,
        "holdout_release_authority": False,
        "performance_claim_authority": False,
        "scalarization_authority": False,
        "stop_authority": "NONE",
    }
    record["hash"] = canonical_document_hash(record)
    return record
