"""Programmatic conflict annotation without deduplication or synthesis."""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping
from typing import Any

from ..constrained_decoder.canonical_validator import validate_candidate_claim_ir


_POINTER_FIELDS = ("record_id", "source_id", "content_hash")


def preserve_candidate_conflicts(
    candidates: Iterable[Mapping[str, Any]],
    pointer_identities: Mapping[str, Mapping[str, Any]],
    *,
    exclusive_object_predicates: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Retain every candidate and symmetrically annotate source-backed conflicts."""

    outputs = [copy.deepcopy(dict(candidate)) for candidate in candidates]
    for output in outputs:
        validate_candidate_claim_ir(output)
    candidate_ids = [_candidate_id(candidate) for candidate in outputs]
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("candidate_id values must be unique")

    known_ids = set(candidate_ids)
    links = {
        candidate_id: _existing_links(candidate, candidate_id, known_ids)
        for candidate_id, candidate in zip(candidate_ids, outputs, strict=True)
    }
    normalized_pointers = {
        candidate_id: _pointer_identity(pointer_identities[candidate_id])
        for candidate_id in candidate_ids
        if candidate_id in pointer_identities
    }
    exclusive_predicates = frozenset(exclusive_object_predicates)
    if any(not isinstance(predicate, str) or not predicate for predicate in exclusive_predicates):
        raise ValueError("exclusive_object_predicates must contain non-empty strings")

    for candidate_id, existing_links in tuple(links.items()):
        for contradicted_id in tuple(existing_links):
            links[contradicted_id].add(candidate_id)

    for left_index, left in enumerate(outputs):
        for right_index in range(left_index + 1, len(outputs)):
            right = outputs[right_index]
            left_id = candidate_ids[left_index]
            right_id = candidate_ids[right_index]
            if (
                _claims_conflict(left, right, exclusive_predicates)
                and left_id in normalized_pointers
                and right_id in normalized_pointers
                and normalized_pointers[left_id] != normalized_pointers[right_id]
            ):
                links[left_id].add(right_id)
                links[right_id].add(left_id)

    order = {candidate_id: index for index, candidate_id in enumerate(candidate_ids)}
    for candidate_id, output in zip(candidate_ids, outputs, strict=True):
        output["contradict_claim_ids"] = sorted(
            links[candidate_id], key=lambda value: order[value]
        )
        if links[candidate_id]:
            output["truth_status"] = "conflicted"
        validate_candidate_claim_ir(output)
    return outputs


def _candidate_id(candidate: Mapping[str, Any]) -> str:
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ValueError("each candidate requires a non-empty candidate_id")
    return candidate_id


def _existing_links(
    candidate: Mapping[str, Any], candidate_id: str, known_ids: set[str]
) -> set[str]:
    values = candidate.get("contradict_claim_ids", [])
    if (
        not isinstance(values, list)
        or any(not isinstance(value, str) or not value for value in values)
        or len(set(values)) != len(values)
    ):
        raise ValueError("contradict_claim_ids must contain unique candidate IDs")
    invalid = set(values) - known_ids
    if invalid or candidate_id in values:
        raise ValueError("contradict_claim_ids must reference other panel candidates")
    return set(values)


def _pointer_identity(pointer: Mapping[str, Any]) -> tuple[str, str, str]:
    if not isinstance(pointer, Mapping) or set(pointer) != set(_POINTER_FIELDS):
        raise ValueError("pointer identity must contain record_id/source_id/content_hash")
    identity = tuple(pointer[field] for field in _POINTER_FIELDS)
    if any(not isinstance(value, str) or not value for value in identity):
        raise ValueError("pointer identity fields must be non-empty strings")
    return identity  # type: ignore[return-value]


def _claims_conflict(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    exclusive_object_predicates: frozenset[str],
) -> bool:
    left_claim = left.get("claim")
    right_claim = right.get("claim")
    if not isinstance(left_claim, Mapping) or not isinstance(right_claim, Mapping):
        raise ValueError("each candidate requires a claim mapping")
    if (
        left_claim.get("subject") != right_claim.get("subject")
        or left_claim.get("predicate") != right_claim.get("predicate")
    ):
        return False
    object_conflict = (
        left_claim.get("predicate") in exclusive_object_predicates
        and left_claim.get("object") != right_claim.get("object")
    )
    left_polarity = left_claim.get("polarity")
    right_polarity = right_claim.get("polarity")
    polarity_conflict = (
        isinstance(left_polarity, bool)
        and isinstance(right_polarity, bool)
        and left_polarity != right_polarity
    )
    return object_conflict or polarity_conflict
