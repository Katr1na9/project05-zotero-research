"""P2/P3 deterministic counterexample post-processing API.

Only finite-witness MinDiff and schema-shaped artifact assembly are exposed.
This package contains no Firewall, promotion, executor, planner, Part B, or
system-state implementation.
"""

from .artifact import (
    CounterexampleArtifactAssembler,
    CounterexampleArtifactMetadata,
)
from .mindiff import (
    FiniteWitnessMinDiff,
    MinDiffResult,
    MinimizationStatus,
    PredicateProjectionContract,
)

__all__ = [
    "CounterexampleArtifactAssembler",
    "CounterexampleArtifactMetadata",
    "FiniteWitnessMinDiff",
    "MinDiffResult",
    "MinimizationStatus",
    "PredicateProjectionContract",
]
