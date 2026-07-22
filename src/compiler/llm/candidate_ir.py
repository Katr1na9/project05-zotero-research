"""Local Candidate Claim IR projection pending the shared Kernel schema."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any, Required, TypedDict

from .candidate_only_guard import (
    ALLOWED_RAW_PROPOSAL_FIELDS,
    materialize_pointer_suggestion,
    reject_model_controlled_fields,
)
from .source_semantics import preserve_trusted_source_semantics


class CandidateClaimIRProjection(TypedDict, total=False):
    """A local, candidate-only claim mapping without Kernel-schema authority."""

    modality: Required[Any]
    epistemic_role: Required[str]
    truth_status: Required[str]
    admission_status: Required[str]
    certification_authority: Required[dict[str, Any]]
    promotion_status: Required[str]
    binding_status: Required[str]
    pointer_suggestion: Required[dict[str, Any]]
    compatibility_status: Required[str]


def project_candidate_claim(
    raw_semantic_proposal: Mapping[str, Any],
    trusted_source_metadata: Mapping[str, Any],
) -> CandidateClaimIRProjection:
    """Materialize a local candidate projection from model output and trusted modality."""

    if not isinstance(raw_semantic_proposal, Mapping):
        raise TypeError("raw_semantic_proposal must be a mapping")
    if not isinstance(trusted_source_metadata, Mapping):
        raise TypeError("trusted_source_metadata must be a mapping")
    if "modality" not in trusted_source_metadata:
        raise ValueError("trusted_source_metadata must contain modality")

    reject_model_controlled_fields(raw_semantic_proposal)
    pointer_suggestion = materialize_pointer_suggestion(raw_semantic_proposal)
    projection: CandidateClaimIRProjection = {
        field: copy.deepcopy(raw_semantic_proposal[field])
        for field in ALLOWED_RAW_PROPOSAL_FIELDS
        if field in raw_semantic_proposal
    }
    projection["admission_status"] = "candidate"
    projection["certification_authority"] = {"allowed": False, "levels": []}
    projection["promotion_status"] = "none"
    projection["binding_status"] = pointer_suggestion["status"]
    projection["pointer_suggestion"] = pointer_suggestion
    projection["compatibility_status"] = "pending_kernel_schema"
    return preserve_trusted_source_semantics(
        projection, trusted_source_metadata
    )  # type: ignore[return-value]
