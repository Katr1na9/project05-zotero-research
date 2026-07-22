"""Decoder-facing view of the local canonical candidate schema."""

from __future__ import annotations

import copy
from typing import Any

from .canonical_validator import _build_candidate_claim_ir_schema


def build_decoder_compatibility_schema() -> dict[str, Any]:
    """Return a detached view that preserves every canonical restriction."""

    return copy.deepcopy(_build_candidate_claim_ir_schema())


# Short alias for integrations that treat the compatibility view as a projection.
project_decoder_schema = build_decoder_compatibility_schema
