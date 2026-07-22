"""Deterministic finite-domain base/support/alternative Checker.

The caller supplies a compiled finite problem whose domains and constraints
come from frozen Gamma and admitted case evidence. Hidden ground truth and
oracle fields are forbidden inputs by contract. This P1 module determines
query satisfiability only; it does not generate counterexample artifacts,
minimize differences, perform promotion, or emit a system STOP state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product
from math import isfinite
from types import MappingProxyType
from typing import Callable, Mapping, Sequence


WorldValue = str | int | float | bool | None
World = Mapping[str, WorldValue]
Constraint = Callable[[World], bool]


class QueryStatus(str, Enum):
    SAT = "SAT"
    UNSAT = "UNSAT"
    TIMEOUT = "TIMEOUT"
    NOT_RUN = "NOT_RUN"


class CheckerStatus(str, Enum):
    SCOPE_MISMATCH_SUSPECTED = "SCOPE_MISMATCH_SUSPECTED"
    REJECT_CANDIDATE = "REJECT_CANDIDATE"
    COUNTEREXAMPLE_FOUND = "COUNTEREXAMPLE_FOUND"
    CANDIDATE_CERTIFIED = "CANDIDATE_CERTIFIED"
    UNKNOWN = "UNKNOWN"


_TRUTH_TABLE = {
    (
        QueryStatus.UNSAT,
        QueryStatus.NOT_RUN,
        QueryStatus.NOT_RUN,
    ): CheckerStatus.SCOPE_MISMATCH_SUSPECTED,
    (
        QueryStatus.SAT,
        QueryStatus.UNSAT,
        QueryStatus.NOT_RUN,
    ): CheckerStatus.REJECT_CANDIDATE,
    (
        QueryStatus.SAT,
        QueryStatus.SAT,
        QueryStatus.SAT,
    ): CheckerStatus.COUNTEREXAMPLE_FOUND,
    (
        QueryStatus.SAT,
        QueryStatus.SAT,
        QueryStatus.UNSAT,
    ): CheckerStatus.CANDIDATE_CERTIFIED,
    (
        QueryStatus.SAT,
        QueryStatus.TIMEOUT,
        QueryStatus.NOT_RUN,
    ): CheckerStatus.UNKNOWN,
    (
        QueryStatus.SAT,
        QueryStatus.SAT,
        QueryStatus.TIMEOUT,
    ): CheckerStatus.UNKNOWN,
    (
        QueryStatus.TIMEOUT,
        QueryStatus.NOT_RUN,
        QueryStatus.NOT_RUN,
    ): CheckerStatus.UNKNOWN,
}


def classify_query_results(
    base: QueryStatus,
    support: QueryStatus,
    alternative: QueryStatus,
) -> CheckerStatus:
    """Map one valid query sequence through the approved seven-row table."""

    try:
        return _TRUTH_TABLE[(base, support, alternative)]
    except KeyError as error:
        raise ValueError(
            "invalid base/support/alternative query sequence: "
            f"{base.value}/{support.value}/{alternative.value}"
        ) from error


def _validate_world_value(value: object, variable: str) -> WorldValue:
    if not isinstance(value, (str, int, float, bool, type(None))):
        raise ValueError(f"domain {variable!r} contains a non-scalar value")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError(f"domain {variable!r} contains a non-finite number")
    return value


@dataclass(frozen=True)
class FiniteDomainProblem:
    """A compiled finite CSP over JSON-scalar domains and pure constraints."""

    domains: Mapping[str, Sequence[WorldValue]]
    constraints: Sequence[Constraint] = ()

    def __post_init__(self) -> None:
        if not self.domains:
            raise ValueError("at least one finite domain is required")

        frozen_domains: dict[str, tuple[WorldValue, ...]] = {}
        for variable, domain in self.domains.items():
            if not isinstance(variable, str) or not variable:
                raise ValueError("domain variable names must be non-empty strings")
            if isinstance(domain, (str, bytes)):
                raise ValueError(f"domain {variable!r} must be a finite sequence")

            values = tuple(_validate_world_value(value, variable) for value in domain)
            if not values:
                raise ValueError(f"domain {variable!r} must not be empty")
            if any(
                value == earlier
                for index, value in enumerate(values)
                for earlier in values[:index]
            ):
                raise ValueError(f"domain {variable!r} contains duplicate values")
            frozen_domains[variable] = values

        frozen_constraints = tuple(self.constraints)
        if any(not callable(constraint) for constraint in frozen_constraints):
            raise ValueError("every finite-domain constraint must be callable")

        object.__setattr__(self, "domains", MappingProxyType(frozen_domains))
        object.__setattr__(self, "constraints", frozen_constraints)


@dataclass(frozen=True)
class QueryResult:
    status: QueryStatus
    assignments_examined: int = 0
    witness: World | None = None

    @classmethod
    def not_run(cls) -> "QueryResult":
        return cls(status=QueryStatus.NOT_RUN)


@dataclass(frozen=True)
class CheckerRun:
    base: QueryResult
    support: QueryResult
    alternative: QueryResult
    checker_status: CheckerStatus

    def to_outcome_fields(self) -> dict[str, str]:
        """Return only P1 Checker-owned fields, never a system state."""

        return {
            "base": self.base.status.value,
            "support": self.support.status.value,
            "alternative": self.alternative.status.value,
            "checker_status": self.checker_status.value,
        }


class FiniteDomainEnumerator:
    """Enumerate a finite Cartesian product in stable insertion/domain order."""

    def __init__(self, max_assignments: int | None = None) -> None:
        if max_assignments is not None and (
            isinstance(max_assignments, bool)
            or not isinstance(max_assignments, int)
            or max_assignments <= 0
        ):
            raise ValueError("max_assignments must be a positive integer or None")
        self._max_assignments = max_assignments

    def solve(
        self,
        problem: FiniteDomainProblem,
        query_constraint: Constraint | None = None,
    ) -> QueryResult:
        variables = tuple(problem.domains)
        domains = tuple(problem.domains[variable] for variable in variables)
        examined = 0

        for assignment in product(*domains):
            if self._max_assignments is not None and examined >= self._max_assignments:
                return QueryResult(
                    status=QueryStatus.TIMEOUT,
                    assignments_examined=examined,
                )

            examined += 1
            mutable_world = dict(zip(variables, assignment))
            world: World = MappingProxyType(mutable_world)
            if not all(constraint(world) for constraint in problem.constraints):
                continue
            if query_constraint is not None and not query_constraint(world):
                continue
            return QueryResult(
                status=QueryStatus.SAT,
                assignments_examined=examined,
                witness=world,
            )

        return QueryResult(
            status=QueryStatus.UNSAT,
            assignments_examined=examined,
        )


class FiniteDomainChecker:
    """Run base, support, and alternative queries in the normative order."""

    def __init__(self, max_assignments: int | None = None) -> None:
        self._enumerator = FiniteDomainEnumerator(max_assignments=max_assignments)

    def check_candidate(
        self,
        problem: FiniteDomainProblem,
        *,
        target_variable: str,
        candidate: WorldValue,
    ) -> CheckerRun:
        if target_variable not in problem.domains:
            raise ValueError(f"unknown target variable: {target_variable!r}")

        support = QueryResult.not_run()
        alternative = QueryResult.not_run()
        base = self._enumerator.solve(problem)

        if base.status is QueryStatus.SAT:
            support = self._enumerator.solve(
                problem,
                query_constraint=lambda world: world[target_variable] == candidate,
            )

            if support.status is QueryStatus.SAT:
                alternative = self._enumerator.solve(
                    problem,
                    query_constraint=lambda world: world[target_variable] != candidate,
                )

        checker_status = classify_query_results(
            base.status,
            support.status,
            alternative.status,
        )
        return CheckerRun(
            base=base,
            support=support,
            alternative=alternative,
            checker_status=checker_status,
        )
