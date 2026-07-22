"""Deterministic MinDiff for a fixed pair of finite SAT witnesses.

This P2 module runs only after the P1 Checker has returned
``COUNTEREXAMPLE_FOUND`` with support and alternative SAT witnesses. It does
not search for new worlds, generate a counterexample artifact, or emit a
system state. A timeout/resource limit affects only ``minimization_status``;
the Checker's counterexample result is preserved verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping, Sequence

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


_PROJECTION_FACTORY_TOKEN = object()


@dataclass(frozen=True)
class PredicateProjectionContract:
    """Catalog-bound mapping from witness variables to declared predicates.

    Callers choose the variable-to-action bindings. The predicate strings are
    resolved only from those catalog actions' single ``world_dependencies``;
    arbitrary test or runtime strings cannot enter MinDiff.
    """

    schema_version: str
    contract_id: str
    catalog_id: str | None
    catalog_version: str | None
    action_bindings: Mapping[str, str]
    projections: Mapping[str, str]
    witness_variables: tuple[str, ...]
    _factory_token: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._factory_token is not _PROJECTION_FACTORY_TOKEN:
            raise ValueError(
                "PredicateProjectionContract must be built by a contract factory"
            )
        if self.schema_version != "0.8.0":
            raise ValueError("projection contract schema_version must be 0.8.0")
        self._string(self.contract_id, "contract_id")
        variables = self._variables(self.witness_variables)
        bindings = dict(self.action_bindings)
        projections = dict(self.projections)
        if set(bindings) != set(projections):
            raise ValueError("action bindings and projections must share variables")
        if not set(bindings).issubset(variables):
            raise ValueError("projection contains a non-witness variable")
        for variable, action_id in bindings.items():
            self._string(variable, "binding variable")
            self._string(action_id, f"bindings.{variable}")
            self._string(projections[variable], f"projections.{variable}")
        if len(set(projections.values())) != len(projections):
            raise ValueError("projection predicates must be unique across variables")
        if (self.catalog_id is None) != (self.catalog_version is None):
            raise ValueError("catalog_id and catalog_version must be jointly present")
        if bindings and self.catalog_id is None:
            raise ValueError("non-empty projections require a bound catalog")
        if self.catalog_id is not None:
            self._string(self.catalog_id, "catalog_id")
            self._string(self.catalog_version, "catalog_version")
        object.__setattr__(self, "action_bindings", MappingProxyType(bindings))
        object.__setattr__(self, "projections", MappingProxyType(projections))
        object.__setattr__(self, "witness_variables", variables)

    @classmethod
    def from_action_catalog(
        cls,
        contract_document: Mapping[str, object],
        action_catalog: Mapping[str, object],
        *,
        witness_variables: Sequence[str] | Mapping[str, object],
    ) -> "PredicateProjectionContract":
        if not isinstance(contract_document, Mapping):
            raise ValueError("predicate projection contract must be an object")
        if not isinstance(action_catalog, Mapping):
            raise ValueError("action_catalog must be an object")
        if contract_document.get("schema_version") != "0.8.0":
            raise ValueError("projection contract schema_version must be 0.8.0")
        if action_catalog.get("schema_version") != "0.8.0":
            raise ValueError("action catalog schema_version must be 0.8.0")
        contract_id = cls._string(
            contract_document.get("contract_id"), "contract_id"
        )
        catalog_id = cls._string(action_catalog.get("catalog_id"), "catalog_id")
        catalog_version = cls._string(
            action_catalog.get("catalog_version"), "catalog_version"
        )
        if contract_document.get("catalog_id") != catalog_id:
            raise ValueError("projection contract catalog_id mismatch")
        if contract_document.get("catalog_version") != catalog_version:
            raise ValueError("projection contract catalog_version mismatch")

        variables = cls._variables(witness_variables)
        bindings_raw = contract_document.get("bindings")
        if not isinstance(bindings_raw, Mapping):
            raise ValueError("projection contract bindings must be an object")
        action_index = cls._action_index(action_catalog.get("actions"))

        bindings: dict[str, str] = {}
        projections: dict[str, str] = {}
        for variable, raw_action_id in bindings_raw.items():
            variable_name = cls._string(variable, "binding variable")
            if variable_name not in variables:
                raise ValueError(
                    f"projection references unknown variable: {variable_name!r}"
                )
            action_id = cls._string(
                raw_action_id, f"bindings.{variable_name}"
            )
            action = action_index.get(action_id)
            if action is None:
                raise ValueError(
                    f"projection binding references unknown action: {action_id!r}"
                )
            observation_model = action.get("observation_model")
            if not isinstance(observation_model, Mapping):
                raise ValueError(f"action {action_id!r} lacks observation_model")
            dependencies = observation_model.get("world_dependencies")
            if not isinstance(dependencies, Sequence) or isinstance(
                dependencies, (str, bytes)
            ):
                raise ValueError(
                    f"action {action_id!r} world_dependencies must be a sequence"
                )
            frozen_dependencies = tuple(dependencies)
            if (
                len(frozen_dependencies) != 1
                or not isinstance(frozen_dependencies[0], str)
                or not frozen_dependencies[0]
            ):
                raise ValueError(
                    f"action {action_id!r} must declare exactly one predicate dependency"
                )
            bindings[variable_name] = action_id
            projections[variable_name] = frozen_dependencies[0]

        if len(set(projections.values())) != len(projections):
            raise ValueError("projection predicates must be unique across variables")
        return cls(
            schema_version="0.8.0",
            contract_id=contract_id,
            catalog_id=catalog_id,
            catalog_version=catalog_version,
            action_bindings=MappingProxyType(bindings),
            projections=MappingProxyType(projections),
            witness_variables=variables,
            _factory_token=_PROJECTION_FACTORY_TOKEN,
        )

    @classmethod
    def empty(
        cls, witness_variables: Sequence[str] | Mapping[str, object]
    ) -> "PredicateProjectionContract":
        variables = cls._variables(witness_variables)
        return cls(
            schema_version="0.8.0",
            contract_id="empty-projection-contract",
            catalog_id=None,
            catalog_version=None,
            action_bindings=MappingProxyType({}),
            projections=MappingProxyType({}),
            witness_variables=variables,
            _factory_token=_PROJECTION_FACTORY_TOKEN,
        )

    def validate_for_witness(self, witness: Mapping[str, WorldValue]) -> None:
        self.validate_for_variables(witness)

    def validate_for_variables(
        self, variables: Sequence[str] | Mapping[str, object]
    ) -> None:
        variable_names = self._variables(variables)
        if set(variable_names) != set(self.witness_variables):
            raise ValueError("projection contract witness-variable set mismatch")

    @staticmethod
    def _string(value: object, field: str) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field} must be a non-empty string")
        return value

    @classmethod
    def _variables(
        cls, value: Sequence[str] | Mapping[str, object]
    ) -> tuple[str, ...]:
        raw = tuple(value) if isinstance(value, Mapping) else tuple(value)
        if not raw or any(not isinstance(item, str) or not item for item in raw):
            raise ValueError("witness_variables must contain non-empty strings")
        if len(set(raw)) != len(raw):
            raise ValueError("witness_variables must not contain duplicates")
        return raw

    @classmethod
    def _action_index(cls, value: object) -> dict[str, Mapping[str, object]]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            raise ValueError("action_catalog.actions must be a sequence")
        index: dict[str, Mapping[str, object]] = {}
        for position, raw_action in enumerate(value):
            if not isinstance(raw_action, Mapping):
                raise ValueError(f"action_catalog.actions[{position}] must be an object")
            action_id = cls._string(
                raw_action.get("action_id"),
                f"action_catalog.actions[{position}].action_id",
            )
            if action_id in index:
                raise ValueError(f"duplicate action ID: {action_id!r}")
            index[action_id] = raw_action
        return index


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
        predicate_projections: PredicateProjectionContract,
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
        predicate_projections: PredicateProjectionContract,
        witness: Mapping[str, WorldValue],
    ) -> dict[str, str]:
        if not isinstance(predicate_projections, PredicateProjectionContract):
            raise ValueError(
                "predicate_projections must be a PredicateProjectionContract"
            )
        predicate_projections.validate_for_witness(witness)
        return dict(predicate_projections.projections)

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
