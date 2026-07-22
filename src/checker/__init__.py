"""P1 finite-domain Checker API.

This package intentionally exposes no MinDiff, Firewall, acquisition, planner,
executor, or system-STOP implementation.
"""

from .finite_domain import (
    CheckerRun,
    CheckerStatus,
    FiniteDomainChecker,
    FiniteDomainEnumerator,
    FiniteDomainProblem,
    QueryResult,
    QueryStatus,
    classify_query_results,
)

__all__ = [
    "CheckerRun",
    "CheckerStatus",
    "FiniteDomainChecker",
    "FiniteDomainEnumerator",
    "FiniteDomainProblem",
    "QueryResult",
    "QueryStatus",
    "classify_query_results",
]
