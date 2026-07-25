"""Explicit, non-entity abstentions for local candidate processing."""

from __future__ import annotations

from enum import Enum


class AbstentionReason(str, Enum):
    """Stable reason codes for intentionally absent pointer output."""

    NO_POINTER_CANDIDATES = "no_pointer_candidates"
    INCOMPLETE_POINTER_IDENTITY = "incomplete_pointer_identity"


def create_abstention(reason: AbstentionReason) -> dict[str, str]:
    """Return an explicit abstention without choosing or naming an entity."""

    if not isinstance(reason, AbstentionReason):
        raise TypeError("reason must be an AbstentionReason")
    return {"status": "abstained", "reason_code": reason.value}
