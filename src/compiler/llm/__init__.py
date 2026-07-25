"""Candidate-only, model-independent LLM compiler projections."""

from .candidate_ir import CandidateClaimIRProjection, project_candidate_claim
from .exceptions import CandidateOnlyViolationError

__all__ = [
    "CandidateClaimIRProjection",
    "CandidateOnlyViolationError",
    "project_candidate_claim",
]
