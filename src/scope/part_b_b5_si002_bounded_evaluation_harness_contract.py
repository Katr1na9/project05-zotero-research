"""Pure B5 SI-002 bounded-evaluation harness-contract evaluator.

This module validates frozen declarations and returns a deterministic local
contract record.  It never invokes a Planner, evaluator, runner process,
clock, CPU meter, memory meter, connector, production registry, or write
path.  A positive record is contract metadata only and carries no execution,
performance, Part B, certificate, or STOP authority.
"""

from __future__ import annotations

from collections.abc import Mapping
import re

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
)


IMPLEMENTATION_ID = (
    "part_b_b5_m3_kernel_d1_twin_readonly_conformance_v0.1"
)
LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"

IMPLEMENTATION_IDENTITY_HASH = (
    "sha256:25e89d3eef7f13f5b65b839b06895b7"
    "c498753dcf4c955aa4d6c375235a0246d"
)
D1_ADMISSION_EVIDENCE_HASH = (
    "sha256:ff6cc57c5ec974d55a95527aceb90bf7"
    "1f5b58e11d82aafddb9fd06300fc3b3c"
)
D1_ADMISSION_RECORD_HASH = (
    "sha256:a43e7baeaae5f32e14c60694b9cc6cfa"
    "258e46c5315f79d4bfdb83c0b641cc65"
)
BOUNDED_EVALUATION_CONTRACT_HASH = (
    "sha256:9c1cae4643b95f7e2c87b6398cd096db"
    "1836ca3533cca67a1842dd037ec66858"
)
BOUNDED_EVALUATION_CONFIG_CONTENT_SHA256 = (
    "42195a832ee1e88922433aa17d407da7"
    "8825a8b6bafe94cea5bd804c880890c8"
)
BOUNDED_EVALUATION_SCHEMA_CONTENT_SHA256 = (
    "a6e6466f00a34bc469b1fe9264004a14"
    "c8906f5b9bb1b4634f88c5a39f20e44e"
)

REQUEST_KIND = "ASSESS_LOCAL_BOUNDED_EVALUATION_HARNESS_CONTRACT"
RECORD_CLASS = "LOCAL_BOUNDED_EVALUATION_HARNESS_CONTRACT_RECORD"
RECORD_SCOPE = (
    "LOCAL_BOUNDED_EVALUATION_HARNESS_CONTRACT_OR_RECORD_ONLY"
)
POSITIVE_DECISION = "LOCAL_BOUNDED_EVALUATION_HARNESS_CONTRACT_VALID"

SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")

REQUEST_FIELDS = frozenset(
    {
        "schema_version",
        "request_kind",
        "request_version",
        "implementation_id",
        "implementation_identity_hash",
        "d1_admission_record_hash",
        "d1_admission_evidence_hash",
        "bounded_evaluation_contract_hash",
        "bounded_evaluation_config_content_sha256",
        "bounded_evaluation_schema_content_sha256",
        "harness_contract_identity_hash",
        "declared_case_binding_hash",
        "declared_resource_limits_hash",
        "execution_requested",
        "evaluation_execution_authority",
        "planner_execution_authority",
    }
)

IDENTITY_FIELDS = frozenset(
    {
        "schema_version",
        "harness_contract_id",
        "harness_contract_version",
        "implementation_id",
        "implementation_identity_hash",
        "d1_admission_record_hash",
        "bounded_evaluation_contract_hash",
        "bounded_evaluation_config_content_sha256",
        "bounded_evaluation_schema_content_sha256",
        "frozen_resource_caps",
        "frozen_failure_semantics",
        "allowed_contract_metrics",
        "authority_ceiling",
        "hash",
    }
)

POLICY_FIELDS = frozenset(
    {
        "schema_version",
        "policy_id",
        "policy_version",
        "status",
        "authorized_slice",
        "admissible_implementation_ids",
        "wildcards",
        "fallback",
        "expected_harness_contract_identity_hash",
        "expected_d1_admission_evidence_hash",
        "expected_bounded_evaluation_contract_hash",
        "positive_decision",
        "record_scope",
        "reason_codes",
        "failure_semantics",
        "authority_ceiling",
        "hash",
    }
)

FROZEN_RESOURCE_CAPS = {
    "max_public_state_bytes": 1048576,
    "max_feasible_action_ids": 4096,
    "max_decision_wall_ms": 2000,
    "max_decision_cpu_ms": 1000,
    "max_memory_bytes": 536870912,
    "max_decisions_per_case": 256,
}

FROZEN_FAILURE_SEMANTICS = {
    "timeout": "UNKNOWN_NO_RANK",
    "resource_exhaustion": "UNKNOWN_NO_RANK",
    "infeasible": "SEPARATE_NO_ACTION",
    "unknown": "FAIL_CLOSED_NO_RANK",
    "missing_measurement": "UNKNOWN_NOT_ZERO",
    "infeasible_as_high_cost": False,
    "timeout_as_unsat": False,
    "resource_exhaustion_as_zero_or_loss": False,
    "automatic_retry": False,
    "fallback_to_hidden_state": False,
}

ALLOWED_CONTRACT_METRICS = [
    "INTERFACE_CONFORMANCE",
    "FAILURE_CHANNEL_COUNTS",
    "UNSCALARIZED_RESOURCE_VECTOR_SHAPE",
]

AUTHORITY_CEILING = {
    "record_scope": RECORD_SCOPE,
    "execution_requested": False,
    "actual_runner_or_evaluator_invocation": False,
    "planner_execution_authority": False,
    "evaluation_execution_authority": False,
    "scalarization_authority": False,
    "performance_claim_authority": False,
    "superiority_claim_authority": False,
    "path_b_write_authority": False,
    "mint_authority": False,
    "kernel_or_e_case_write_authority": False,
    "certificate_authority": False,
    "stop_authority": "NONE",
    "full_m3_star": False,
    "part_b_pass": False,
    "production_registration_enabled": False,
    "pb_b5_si_002_state": (
        "CONTRACT_PATH_ESTABLISHED_EXECUTION_NOT_ESTABLISHED"
    ),
    "pb_b5_si_003_state": (
        "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION"
    ),
}

DECISIONS = {
    "valid": (
        POSITIVE_DECISION,
        "B5-SI002-000-CONTRACT-VALID",
    ),
    "unknown": (
        "DENY_UNKNOWN_IMPLEMENTATION",
        "B5-SI002-DENY-UNKNOWN-ID",
    ),
    "legacy": (
        "DENY_LEGACY_IMPLEMENTATION",
        "B5-SI002-DENY-LEGACY-ID",
    ),
    "missing": (
        "DENY_MISSING_EVIDENCE",
        "B5-SI002-DENY-MISSING-EVIDENCE",
    ),
    "mismatch": (
        "DENY_HASH_MISMATCH",
        "B5-SI002-DENY-HASH-MISMATCH",
    ),
    "limits": (
        "DENY_INVALID_RESOURCE_LIMITS",
        "B5-SI002-DENY-INVALID-RESOURCE-LIMITS",
    ),
    "authority": (
        "DENY_AUTHORITY_REQUEST",
        "B5-SI002-DENY-AUTHORITY-REQUEST",
    ),
    "non_contract": (
        "DENY_NON_CONTRACT_INPUT",
        "B5-SI002-DENY-NON-CONTRACT-INPUT",
    ),
}

POLICY_REASON_CODES = {
    decision: reason_code for decision, reason_code in DECISIONS.values()
}


AUTHORITY_REQUEST_FIELDS = frozenset(
    {
        "action_payload",
        "actual_runner_invocation",
        "evaluator_invocation",
        "b6_execution_requested",
        "b7_execution_requested",
        "b8_execution_requested",
        "b9_execution_requested",
        "path_b_write",
        "mint",
        "kernel_or_e_case_write",
        "certificate",
        "CERTIFIED_STOP",
        "stop_requested",
        "part_b_pass",
        "full_m3_star",
    }
)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


def _select_decision(
    *,
    request: Mapping[str, object],
    identity: Mapping[str, object],
    policy: Mapping[str, object],
) -> tuple[str, str]:
    request_keys = set(request)
    if request_keys & AUTHORITY_REQUEST_FIELDS:
        return DECISIONS["authority"]
    if request_keys - REQUEST_FIELDS:
        return DECISIONS["non_contract"]
    if REQUEST_FIELDS - request_keys:
        return DECISIONS["missing"]

    implementation_id = request.get("implementation_id")
    if implementation_id == LEGACY_IMPLEMENTATION_ID:
        return DECISIONS["legacy"]
    if implementation_id != IMPLEMENTATION_ID:
        return DECISIONS["unknown"]

    if (
        request.get("execution_requested") is not False
        or request.get("evaluation_execution_authority") is not False
        or request.get("planner_execution_authority") is not False
    ):
        return DECISIONS["authority"]

    if set(identity) != IDENTITY_FIELDS or set(policy) != POLICY_FIELDS:
        return DECISIONS["non_contract"]
    if (
        identity.get("implementation_id") != IMPLEMENTATION_ID
        or policy.get("admissible_implementation_ids")
        != [IMPLEMENTATION_ID]
        or policy.get("wildcards") is not False
        or policy.get("fallback") is not False
    ):
        return DECISIONS["unknown"]

    policy_exact_values = {
        "schema_version": "0.8.0",
        "policy_id": "part-b-b5-si002-bounded-evaluation-harness-policy-v0.1",
        "policy_version": "0.1.0",
        "status": "LOCAL_CONTRACT_RECORD_ONLY_NO_EXECUTION",
        "authorized_slice": "PART_B_B5_SI002_BOUNDED_EVALUATION_RUNNER_CONTRACT_RECORD_ONLY",
    }
    if any(
        policy.get(field) != expected
        for field, expected in policy_exact_values.items()
    ) or policy.get("reason_codes") != POLICY_REASON_CODES:
        return DECISIONS["non_contract"]

    identity_hash = identity.get("hash")
    policy_hash = policy.get("hash")
    if (
        not _valid_sha256(identity_hash)
        or identity_hash != canonical_document_hash(identity)
        or not _valid_sha256(policy_hash)
        or policy_hash != canonical_document_hash(policy)
    ):
        return DECISIONS["mismatch"]

    if _mapping(identity.get("frozen_resource_caps")) != FROZEN_RESOURCE_CAPS:
        return DECISIONS["limits"]
    if (
        _mapping(identity.get("frozen_failure_semantics"))
        != FROZEN_FAILURE_SEMANTICS
        or identity.get("allowed_contract_metrics")
        != ALLOWED_CONTRACT_METRICS
    ):
        return DECISIONS["non_contract"]
    if _mapping(identity.get("authority_ceiling")) != AUTHORITY_CEILING:
        return DECISIONS["authority"]
    if _mapping(policy.get("authority_ceiling")) != AUTHORITY_CEILING:
        return DECISIONS["authority"]
    if policy.get("failure_semantics") != FROZEN_FAILURE_SEMANTICS:
        return DECISIONS["non_contract"]

    exact_request_values = {
        "schema_version": "0.8.0",
        "request_kind": REQUEST_KIND,
        "request_version": "0.1.0",
        "implementation_identity_hash": IMPLEMENTATION_IDENTITY_HASH,
        "d1_admission_record_hash": D1_ADMISSION_RECORD_HASH,
        "d1_admission_evidence_hash": D1_ADMISSION_EVIDENCE_HASH,
        "bounded_evaluation_contract_hash": (
            BOUNDED_EVALUATION_CONTRACT_HASH
        ),
        "bounded_evaluation_config_content_sha256": (
            BOUNDED_EVALUATION_CONFIG_CONTENT_SHA256
        ),
        "bounded_evaluation_schema_content_sha256": (
            BOUNDED_EVALUATION_SCHEMA_CONTENT_SHA256
        ),
    }
    if any(
        request.get(field) != expected
        for field, expected in exact_request_values.items()
    ):
        return DECISIONS["mismatch"]

    identity_exact_values = {
        "schema_version": "0.8.0",
        "harness_contract_id": (
            "part-b-b5-si002-local-bounded-evaluation-"
            "harness-contract-v0.1"
        ),
        "harness_contract_version": "0.1.0",
        "implementation_identity_hash": IMPLEMENTATION_IDENTITY_HASH,
        "d1_admission_record_hash": D1_ADMISSION_RECORD_HASH,
        "bounded_evaluation_contract_hash": (
            BOUNDED_EVALUATION_CONTRACT_HASH
        ),
        "bounded_evaluation_config_content_sha256": (
            BOUNDED_EVALUATION_CONFIG_CONTENT_SHA256
        ),
        "bounded_evaluation_schema_content_sha256": (
            BOUNDED_EVALUATION_SCHEMA_CONTENT_SHA256
        ),
    }
    if any(
        identity.get(field) != expected
        for field, expected in identity_exact_values.items()
    ):
        return DECISIONS["mismatch"]

    if (
        request.get("harness_contract_identity_hash") != identity_hash
        or policy.get("expected_harness_contract_identity_hash")
        != identity_hash
        or policy.get("expected_d1_admission_evidence_hash")
        != D1_ADMISSION_EVIDENCE_HASH
        or policy.get("expected_bounded_evaluation_contract_hash")
        != BOUNDED_EVALUATION_CONTRACT_HASH
        or policy.get("positive_decision") != POSITIVE_DECISION
        or policy.get("record_scope") != RECORD_SCOPE
    ):
        return DECISIONS["mismatch"]

    expected_limits_hash = canonical_value_hash(FROZEN_RESOURCE_CAPS)
    if request.get("declared_resource_limits_hash") != expected_limits_hash:
        return DECISIONS["limits"]
    if not _valid_sha256(request.get("declared_case_binding_hash")):
        return DECISIONS["missing"]

    return DECISIONS["valid"]


def evaluate_bounded_evaluation_harness_contract(
    request: Mapping[str, object],
    *,
    identity: Mapping[str, object],
    policy: Mapping[str, object],
) -> dict[str, object]:
    """Return one deterministic local contract record without execution."""

    if not all(
        isinstance(value, Mapping)
        for value in (request, identity, policy)
    ):
        raise ValueError("request, identity and policy must be mappings")

    decision, reason_code = _select_decision(
        request=request,
        identity=identity,
        policy=policy,
    )

    request_hash = canonical_value_hash(request)
    identity_hash = identity.get("hash")
    if not _valid_sha256(identity_hash):
        identity_hash = canonical_value_hash(
            {"invalid_harness_contract_identity": True}
        )

    record_implementation_id = request.get("implementation_id")
    if not isinstance(
        record_implementation_id, str
    ) or not record_implementation_id:
        record_implementation_id = "INVALID_IMPLEMENTATION_ID"

    record = {
        "schema_version": "0.8.0",
        "record_class": RECORD_CLASS,
        "record_version": "0.1.0",
        "request_hash": request_hash,
        "harness_contract_identity_hash": identity_hash,
        "implementation_id": record_implementation_id,
        "implementation_identity_hash": IMPLEMENTATION_IDENTITY_HASH,
        "d1_admission_record_hash": D1_ADMISSION_RECORD_HASH,
        "bounded_evaluation_contract_hash": (
            BOUNDED_EVALUATION_CONTRACT_HASH
        ),
        "decision": decision,
        "reason_codes": [reason_code],
        "record_scope": RECORD_SCOPE,
        "declared_resource_limits_hash": canonical_value_hash(
            FROZEN_RESOURCE_CAPS
        ),
        "failure_semantics_hash": canonical_value_hash(
            FROZEN_FAILURE_SEMANTICS
        ),
        "planner_execution_authority": False,
        "evaluation_execution_authority": False,
        "stop_authority": "NONE",
    }
    record["hash"] = canonical_document_hash(record)
    return record


__all__ = [
    "ALLOWED_CONTRACT_METRICS",
    "AUTHORITY_CEILING",
    "BOUNDED_EVALUATION_CONFIG_CONTENT_SHA256",
    "BOUNDED_EVALUATION_CONTRACT_HASH",
    "BOUNDED_EVALUATION_SCHEMA_CONTENT_SHA256",
    "D1_ADMISSION_EVIDENCE_HASH",
    "D1_ADMISSION_RECORD_HASH",
    "FROZEN_FAILURE_SEMANTICS",
    "FROZEN_RESOURCE_CAPS",
    "IMPLEMENTATION_ID",
    "IMPLEMENTATION_IDENTITY_HASH",
    "POSITIVE_DECISION",
    "RECORD_CLASS",
    "RECORD_SCOPE",
    "REQUEST_FIELDS",
    "REQUEST_KIND",
    "evaluate_bounded_evaluation_harness_contract",
]
