"""P2 counterexample post-processing API.

Only deterministic finite-witness MinDiff is exposed. This package contains no
Firewall, promotion, executor, planner, Part B, or system-state implementation.
"""

from .mindiff import FiniteWitnessMinDiff, MinDiffResult, MinimizationStatus

__all__ = ["FiniteWitnessMinDiff", "MinDiffResult", "MinimizationStatus"]
