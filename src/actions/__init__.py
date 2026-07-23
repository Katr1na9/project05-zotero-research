"""P4 catalog-only distinguishing-action selection API.

No executor, observation replay, planner, promotion, or system-state authority
is exposed from this package.
"""

from .selection import (
    ActionSelectionResult,
    DistinguishingActionSelector,
)

__all__ = ["ActionSelectionResult", "DistinguishingActionSelector"]
