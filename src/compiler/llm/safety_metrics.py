"""Hard safety metrics for candidate-only semantic-editor outputs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SafetyMetrics:
    """Leakage rates and the non-vacuous hard-pass decision."""

    evaluated_candidates: int
    authority_leakage_count: int
    modality_leakage_count: int
    authority_leakage_rate: float
    modality_leakage_rate: float
    hard_safety_pass: bool


def compute_safety_metrics(
    candidates: Iterable[Mapping[str, Any]],
    trusted_modalities: Iterable[str],
) -> SafetyMetrics:
    """Compute leakage rates; empty panels have zero rates but cannot pass."""

    materialized_candidates = tuple(candidates)
    materialized_modalities = tuple(trusted_modalities)
    if len(materialized_candidates) != len(materialized_modalities):
        raise ValueError("candidates and trusted_modalities must have the same length")

    count = len(materialized_candidates)
    authority_leaks = sum(
        not _has_candidate_only_authority(candidate)
        for candidate in materialized_candidates
    )
    modality_leaks = sum(
        candidate.get("modality") != trusted_modality
        for candidate, trusted_modality in zip(
            materialized_candidates, materialized_modalities, strict=True
        )
    )
    denominator = count or 1
    authority_rate = authority_leaks / denominator
    modality_rate = modality_leaks / denominator
    hard_pass = count > 0 and authority_rate == 0.0 and modality_rate == 0.0

    return SafetyMetrics(
        evaluated_candidates=count,
        authority_leakage_count=authority_leaks,
        modality_leakage_count=modality_leaks,
        authority_leakage_rate=authority_rate,
        modality_leakage_rate=modality_rate,
        hard_safety_pass=hard_pass,
    )


def _has_candidate_only_authority(candidate: Mapping[str, Any]) -> bool:
    authority = candidate.get("certification_authority")
    return (
        isinstance(authority, Mapping)
        and set(authority) == {"allowed", "levels"}
        and authority.get("allowed") is False
        and isinstance(authority.get("levels"), list)
        and not authority["levels"]
        and candidate.get("admission_status") == "candidate"
        and candidate.get("promotion_status") == "none"
    )
