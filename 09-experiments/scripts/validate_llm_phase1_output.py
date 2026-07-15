#!/usr/bin/env python3
"""Dependency-free G0 validation for Project05 LLM Phase 1 outputs."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import unicodedata
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
BUILDER_PATH = SCRIPT_DIR / "build_llm_evaluation_packets.py"
_BUILDER_SPEC = importlib.util.spec_from_file_location(
    "project05_llm_packet_builder_for_validation",
    BUILDER_PATH,
)
_BUILDER = importlib.util.module_from_spec(_BUILDER_SPEC)
assert _BUILDER_SPEC.loader is not None
_BUILDER_SPEC.loader.exec_module(_BUILDER)

canonical_json = _BUILDER.canonical_json
derive_candidate_claim_id = _BUILDER.derive_candidate_claim_id

CANDIDATE_FIELDS = {
    "candidate_claim_id",
    "source_type",
    "subject",
    "predicate",
    "object",
    "source_pointer",
}
ENTITY_FIELDS = {"entity_type", "value"}
POINTER_FIELDS = {"artifact_id", "record_id"}
GAP_CODES = {
    "no_admitted_claim",
    "invalid_pointer",
    "literal_entity_absent",
    "schema_invalid",
}
ERROR_TO_GAP = {
    "candidate_id_mismatch": "schema_invalid",
    "candidate_schema_invalid": "schema_invalid",
    "pointer_not_in_packet": "invalid_pointer",
    "record_sha256_mismatch": "invalid_pointer",
    "literal_entity_not_in_source": "literal_entity_absent",
}


def hash_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest().upper()


def normalize_literal(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(text.strip().split()).casefold()


def iter_scalar_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for item in value.values():
            yield from iter_scalar_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_scalar_values(item)
    elif value is not None and not isinstance(value, (dict, list)):
        yield value


def candidate_schema_valid(candidate: Any) -> bool:
    if not isinstance(candidate, dict) or set(candidate) != CANDIDATE_FIELDS:
        return False
    for field in ("candidate_claim_id", "source_type", "predicate"):
        if not isinstance(candidate.get(field), str) or not candidate[field].strip():
            return False
    for field in ("subject", "object"):
        entity = candidate.get(field)
        if not isinstance(entity, dict) or set(entity) != ENTITY_FIELDS:
            return False
        if any(
            not isinstance(entity.get(name), str) or not entity[name].strip()
            for name in ENTITY_FIELDS
        ):
            return False
    pointer = candidate.get("source_pointer")
    if not isinstance(pointer, dict) or set(pointer) != POINTER_FIELDS:
        return False
    return not any(
        not isinstance(pointer.get(name), str) or not pointer[name].strip()
        for name in POINTER_FIELDS
    )


def validate_candidate(
    candidate,
    packet,
    condition_id,
    attempt_index,
    output_index,
):
    errors: list[str] = []
    if not candidate_schema_valid(candidate):
        errors.append("candidate_schema_invalid")
    if not isinstance(candidate, dict):
        return errors

    expected_id = derive_candidate_claim_id(
        str(packet["request_id"]),
        str(condition_id),
        int(attempt_index),
        int(output_index),
    )
    if candidate.get("candidate_claim_id") != expected_id:
        errors.append("candidate_id_mismatch")

    pointer = candidate.get("source_pointer") or {}
    records = {
        (
            row["source_pointer"]["artifact_id"],
            row["source_pointer"]["record_id"],
        ): row
        for row in packet.get("records", [])
    }
    record = records.get(
        (pointer.get("artifact_id"), pointer.get("record_id"))
    )
    if record is None:
        errors.append("pointer_not_in_packet")
        return sorted(set(errors))

    computed_hash = hashlib.sha256(
        canonical_json(record["source_payload"])
    ).hexdigest().upper()
    if computed_hash != record.get("record_sha256"):
        errors.append("record_sha256_mismatch")

    visible = [
        normalize_literal(value)
        for value in iter_scalar_values(record["source_payload"])
    ]
    for entity in (candidate.get("subject") or {}, candidate.get("object") or {}):
        value = normalize_literal(entity.get("value") or "")
        if not value or not any(value in field for field in visible):
            errors.append("literal_entity_not_in_source")
    return sorted(set(errors))


def admit_candidates(
    result: dict[str, Any],
    packet: dict[str, Any],
) -> dict[str, Any]:
    admitted = []
    rejected = []
    gaps: set[str] = set()
    condition_id = str(result.get("condition_id") or "")
    attempt_index = int(result.get("attempt_index") or 0)
    for output_index, candidate in enumerate(result.get("candidate_claims") or []):
        errors = validate_candidate(
            candidate,
            packet,
            condition_id,
            attempt_index,
            output_index,
        )
        if errors:
            rejected.append(
                {
                    "candidate_claim_id": candidate.get("candidate_claim_id"),
                    "errors": errors,
                }
            )
            gaps.update(
                ERROR_TO_GAP[error]
                for error in errors
                if error in ERROR_TO_GAP
            )
        else:
            admitted.append(candidate)
    if not admitted:
        gaps.add("no_admitted_claim")
    return {
        "request_id": packet["request_id"],
        "condition_id": condition_id,
        "attempt_index": attempt_index,
        "admitted_claims": admitted,
        "rejected": rejected,
        "explicit_gaps": sorted(gaps),
    }


def build_structured_stage2_input(
    admission: dict[str, Any],
    support_ceiling: str,
) -> dict[str, Any]:
    admitted_claims = [
        {key: value for key, value in claim.items() if key in CANDIDATE_FIELDS}
        for claim in admission.get("admitted_claims", [])
        if isinstance(claim, dict)
    ]
    explicit_gaps = sorted(
        {
            str(gap)
            for gap in admission.get("explicit_gaps", [])
            if str(gap) in GAP_CODES
        }
    )
    return {
        "admitted_claims": admitted_claims,
        "explicit_gaps": explicit_gaps,
        "support_ceiling": str(support_ceiling),
    }


def validate_run_manifest(
    manifest,
    config,
    input_manifest,
    prompt_lock,
    model_lock,
):
    errors = []
    if manifest.get("config_sha256") != hash_value(config):
        errors.append("config_sha256_mismatch")
    if manifest.get("input_manifest_sha256") != hash_value(input_manifest):
        errors.append("input_manifest_sha256_mismatch")
    if manifest.get("contract_sha256") != prompt_lock.get("contract_sha256"):
        errors.append("contract_sha256_mismatch")
    if manifest.get("prompt_sha256") != prompt_lock.get("prompt_sha256"):
        errors.append("prompt_sha256_mismatch")
    if canonical_json(manifest.get("model_lock")) != canonical_json(model_lock):
        errors.append("model_lock_mismatch")
    return sorted(errors)


if __name__ == "__main__":
    raise SystemExit(
        "Use run_llm_phase1.py for execution; this module exposes G0 validators."
    )
