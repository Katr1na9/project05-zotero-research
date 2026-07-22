"""Deterministic MinDiff for a fixed pair of finite SAT witnesses.

This P2 module runs only after the P1 Checker has returned
``COUNTEREXAMPLE_FOUND`` with support and alternative SAT witnesses. It does
not search for new worlds, generate a counterexample artifact, or emit a
system state. A timeout/resource limit affects only ``minimization_status``;
the Checker's counterexample result is preserved verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from src.checker.finite_domain import (
    CheckerRun,
    CheckerStatus,
    QueryStatus,
    WorldValue,
)


class MinimizationStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    BEST_EFFORT = "BEST_EFFORT"
    TIMEOUT = "TIMEOUT"
    NOT_REQUESTED = "NOT_REQUESTED"


@dataclass(frozen=True)
class MinDiffResult:
    checker_status: CheckerStatus
    minimization_status: MinimizationStatus
    mindiff_disagreement: Mapping[str, WorldValue]
    differing_variables: tuple[str, ...]
    distinguishing_predicates: tuple[str, ...]
    unprojected_variables: tuple[str, ...]
    comparisons_examined: int

    def to_outcome_fields(self) -> dict[str, object]:
        """Return MinDiff-owned fields without a system status or STOP claim."""

        return {
            "checker_status": self.checker_status.value,
            "minimization_status": self.minimization_status.value,
            "mindiff_disagreement": dict(self.mindiff_disagreement),
            "distinguishing_predicates": list(self.distinguishing_predicates),
        }


class FiniteWitnessMinDiff:
    """Compare a fixed witness pair in deterministic variable-name order."""

    def __init__(self, max_comparisons: int | None = None) -> None:
        if max_comparisons is not None and (
            isinstance(max_comparisons, bool)
            or not isinstance(max_comparisons, int)
            or max_comparisons <= 0
        ):
            raise ValueError("max_comparisons must be a positive integer or None")
        self._max_comparisons = max_comparisons

    def compare(
        self,
        checker_run: CheckerRun,
        *,
        target_variable: str,
        predicate_projections: Mapping[str, str],
    ) -> MinDiffResult:
        if checker_run.checker_status is not CheckerStatus.COUNTEREXAMPLE_FOUND:
            raise ValueError("MinDiff requires COUNTEREXAMPLE_FOUND")
        if checker_run.support.status is not QueryStatus.SAT:
            raise ValueError("MinDiff requires a support SAT witness")
        if checker_run.alternative.status is not QueryStatus.SAT:
            raise ValueError("MinDiff requires an alternative SAT witness")

        support = checker_run.support.witness
        alternative = checker_run.alternative.witness
        if support is None or alternative is None:
            raise ValueError("MinDiff requires materialized SAT witnesses")
        if set(support) != set(alternative):
            raise ValueError("support and alternative witnesses must share variables")
        if target_variable not in support:
            raise ValueError(f"unknown target variable: {target_variable!r}")
        if support[target_variable] == alternative[target_variable]:
            raise ValueError("counterexample witnesses must disagree on the target")

        projections = self._validate_projections(predicate_projections, support)
        disagreement = MappingProxyType(
            {
                "support_world": support[target_variable],
                "alternative_world": alternative[target_variable],
            }
        )
        differing: list[str] = []
        predicates: list[str] = []
        unprojected: list[str] = []
        comparisons = 0

        for variable in sorted(support):
            if (
                self._max_comparisons is not None
                and comparisons >= self._max_comparisons
            ):
                return self._result(
                    checker_status=checker_run.checker_status,
                    minimization_status=MinimizationStatus.TIMEOUT,
                    disagreement=disagreement,
                    differing=differing,
                    predicates=predicates,
                    unprojected=unprojected,
                    comparisons=comparisons,
                )

            comparisons += 1
            if support[variable] == alternative[variable]:
                continue
            differing.append(variable)
            predicate = projections.get(variable)
            if predicate is None:
                unprojected.append(variable)
            else:
                predicates.append(predicate)

        return self._result(
            checker_status=checker_run.checker_status,
            minimization_status=MinimizationStatus.OPTIMAL,
            disagreement=disagreement,
            differing=differing,
            predicates=predicates,
            unprojected=unprojected,
            comparisons=comparisons,
        )

    @staticmethod
    def _validate_projections(
        predicate_projections: Mapping[str, str],
        witness: Mapping[str, WorldValue],
    ) -> dict[str, str]:
        projections = dict(predicate_projections)
        for variable, predicate in projections.items():
            if variable not in witness:
                raise ValueError(f"projection references unknown variable: {variable!r}")
            if not isinstance(predicate, str) or not predicate:
                raise ValueError("predicate projections must be non-empty strings")
        return projections

    @staticmethod
    def _result(
        *,
        checker_status: CheckerStatus,
        minimization_status: MinimizationStatus,
        disagreement: Mapping[str, WorldValue],
        differing: list[str],
        predicates: list[str],
        unprojected: list[str],
        comparisons: int,
    ) -> MinDiffResult:
        return MinDiffResult(
            checker_status=checker_status,
            minimization_status=minimization_status,
            mindiff_disagreement=disagreement,
            differing_variables=tuple(differing),
            distinguishing_predicates=tuple(sorted(set(predicates))),
            unprojected_variables=tuple(unprojected),
            comparisons_examined=comparisons,
        )
