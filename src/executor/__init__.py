"""P5 deterministic table-driven Executor API.

This package exposes no observation feedback, Checker rerun, Firewall,
promotion, planner, or system-state authority.
"""

from .deterministic import (
    DeterministicObservationExecutor,
    ExecutionBatchResult,
    ExecutionFailure,
    ForbiddenActionError,
    FrozenExecutionTables,
)

__all__ = [
    "DeterministicObservationExecutor",
    "ExecutionBatchResult",
    "ExecutionFailure",
    "ForbiddenActionError",
    "FrozenExecutionTables",
]
