"""Model-independent validation and schema projection for constrained decoding."""

from .canonical_validator import (
    CANONICAL_CANDIDATE_CLAIM_IR_SCHEMA,
    CANDIDATE_CLAIM_IR_SCHEMA,
    CandidateClaimIRValidationError,
    validate_candidate_claim_ir,
)
from .schema_projection import (
    build_decoder_compatibility_schema,
    project_decoder_schema,
)

__all__ = [
    "CANONICAL_CANDIDATE_CLAIM_IR_SCHEMA",
    "CANDIDATE_CLAIM_IR_SCHEMA",
    "CandidateClaimIRValidationError",
    "build_decoder_compatibility_schema",
    "project_decoder_schema",
    "validate_candidate_claim_ir",
]
