"""P10 deterministic thin driver wiring the existing P1--P9 components.

The driver adds no decision policy or algorithm. P4 supplies the action set;
P5 executes that set; callers explicitly name any observation IDs to feed
back through P6. P9 alone derives the system state, and a STOP remains
impossible unless the caller supplies an already-issued level certificate
plus its active evidence hash.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType

from src.actions.selection import ActionSelectionResult, DistinguishingActionSelector
from src.checker.finite_domain import (
    CheckerRun,
    CheckerStatus,
    FiniteDomainChecker,
    FiniteDomainProblem,
    WorldValue,
)
from src.checker.level_certificate import IssuedLevelCertificate
from src.counterexample.artifact import (
    CounterexampleArtifactAssembler,
    CounterexampleArtifactMetadata,
)
from src.counterexample.mindiff import (
    FiniteWitnessMinDiff,
    MinDiffResult,
    PredicateProjectionContract,
)
from src.executor.deterministic import (
    DeterministicObservationExecutor,
    ExecutionBatchResult,
    FrozenExecutionTables,
)
from src.scope.recertify import RecertificationOrchestrator, RecertificationResult
from src.scope.system_state import SystemStateDecision, SystemStateDeriver


def _string_tuple(
    value: object,
    field: str,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be a string sequence")
    items = tuple(value)
    if require_nonempty and not items:
        raise ValueError(f"{field} must not be empty")
    if any(not isinstance(item, str) or not item for item in items):
        raise ValueError(f"{field} must contain non-empty strings")
    if len(set(items)) != len(items):
        raise ValueError(f"{field} must not contain duplicates")
    return items


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


@dataclass(frozen=True)
class KernelE2ERunRequest:
    """Frozen compiled scope and evaluator tables consumed by one P10 run."""

    gamma_contract: Mapping[str, object]
    problem: FiniteDomainProblem
    target_variable: str
    candidate: WorldValue
    predicate_projections: PredicateProjectionContract
    artifact_metadata: CounterexampleArtifactMetadata
    action_catalog: Mapping[str, object]
    execution_tables: FrozenExecutionTables
    feedback_observation_ids: Sequence[str] = ()
    level_certificate: IssuedLevelCertificate | None = None
    active_evidence_hash: str | None = None

    def __post_init__(self) -> None:
        gamma = _mapping(self.gamma_contract, "gamma_contract")
        catalog = _mapping(self.action_catalog, "action_catalog")
        if not isinstance(self.problem, FiniteDomainProblem):
            raise ValueError("problem must be a FiniteDomainProblem")
        if not isinstance(self.target_variable, str) or not self.target_variable:
            raise ValueError("target_variable must be a non-empty string")
        if self.target_variable not in self.problem.domains:
            raise ValueError("target_variable is absent from the finite problem")
        if not isinstance(self.artifact_metadata, CounterexampleArtifactMetadata):
            raise ValueError(
                "artifact_metadata must be CounterexampleArtifactMetadata"
            )
        if self.artifact_metadata.target_level != self.target_variable:
            raise ValueError("artifact metadata target does not match the problem")
        if not isinstance(self.execution_tables, FrozenExecutionTables):
            raise ValueError("execution_tables must be FrozenExecutionTables")
        if self.level_certificate is not None and not isinstance(
            self.level_certificate, IssuedLevelCertificate
        ):
            raise ValueError("level_certificate has the wrong type")
        if self.active_evidence_hash is not None and (
            not isinstance(self.active_evidence_hash, str)
            or not self.active_evidence_hash
        ):
            raise ValueError("active_evidence_hash must be a non-empty string")

        if not isinstance(
            self.predicate_projections, PredicateProjectionContract
        ):
            raise ValueError(
                "predicate_projections must be a PredicateProjectionContract"
            )
        self.predicate_projections.validate_for_variables(self.problem.domains)

        gamma_hash = gamma.get("hash")
        if gamma.get("schema_version") != "0.8.0" or (
            not isinstance(gamma_hash, str) or not gamma_hash
        ):
            raise ValueError("gamma_contract is not a v0.8 frozen contract")
        if gamma_hash != self.artifact_metadata.gamma_hash:
            raise ValueError("Gamma hash does not match artifact metadata")
        result_domains = _mapping(gamma.get("result_domains"), "result_domains")
        target_domain = _mapping(
            result_domains.get(self.target_variable),
            f"result_domains.{self.target_variable}",
        )
        finite_candidates = target_domain.get("finite_candidates")
        if finite_candidates is not None:
            candidates = _string_tuple(
                finite_candidates,
                f"result_domains.{self.target_variable}.finite_candidates",
                require_nonempty=True,
            )
            if tuple(self.problem.domains[self.target_variable]) != candidates:
                raise ValueError(
                    "compiled target domain does not match frozen Gamma candidates"
                )

        feedback = _string_tuple(
            self.feedback_observation_ids, "feedback_observation_ids"
        )
        object.__setattr__(
            self,
            "gamma_contract",
            MappingProxyType(deepcopy(dict(gamma))),
        )
        object.__setattr__(
            self,
            "action_catalog",
            MappingProxyType(deepcopy(dict(catalog))),
        )
        object.__setattr__(self, "feedback_observation_ids", feedback)


@dataclass(frozen=True)
class KernelE2ERunResult:
    checker_run: CheckerRun
    mindiff_result: MinDiffResult
    counterexample_artifact: Mapping[str, object]
    action_selection: ActionSelectionResult
    execution_result: ExecutionBatchResult
    feedback_observation_ids: tuple[str, ...]
    recertification_result: RecertificationResult | None
    system_state: SystemStateDecision

    def to_outcome_fields(self) -> dict[str, object]:
        fields: dict[str, object] = dict(self.checker_run.to_outcome_fields())
        fields.update(
            {
                "counterexample_id": self.counterexample_artifact[
                    "counterexample_id"
                ],
                "minimization_status": self.mindiff_result.minimization_status.value,
                "mindiff_disagreement": dict(
                    self.mindiff_result.mindiff_disagreement
                ),
                "distinguishing_predicates": list(
                    self.mindiff_result.distinguishing_predicates
                ),
                "allowed_actions": list(self.action_selection.allowed_actions),
                "forbidden_actions": list(self.action_selection.forbidden_actions),
                "executed_observation_ids": [
                    row["observation_id"]
                    for row in self.execution_result.observations
                ],
                "feedback_observation_ids": list(self.feedback_observation_ids),
                "recertification_checker_status": (
                    self.recertification_result.checker_run.checker_status.value
                    if self.recertification_result is not None
                    else None
                ),
            }
        )
        fields.update(self.system_state.to_outcome_fields())
        return fields


class DeterministicKernelE2EDriver:
    """Wire P1--P9 in their frozen order without adding a policy layer."""

    def __init__(self) -> None:
        self._checker = FiniteDomainChecker()
        self._mindiff = FiniteWitnessMinDiff()
        self._artifact_assembler = CounterexampleArtifactAssembler()
        self._action_selector = DistinguishingActionSelector()
        self._executor = DeterministicObservationExecutor()
        self._recertifier = RecertificationOrchestrator()
        self._state_deriver = SystemStateDeriver()

    def run(self, request: KernelE2ERunRequest) -> KernelE2ERunResult:
        if not isinstance(request, KernelE2ERunRequest):
            raise ValueError("request must be a KernelE2ERunRequest")

        checker_run = self._checker.check_candidate(
            request.problem,
            target_variable=request.target_variable,
            candidate=request.candidate,
        )
        if checker_run.checker_status is not CheckerStatus.COUNTEREXAMPLE_FOUND:
            raise ValueError(
                "P10 counterexample driver requires initial COUNTEREXAMPLE_FOUND"
            )
        mindiff = self._mindiff.compare(
            checker_run,
            target_variable=request.target_variable,
            predicate_projections=request.predicate_projections,
        )
        artifact = self._artifact_assembler.assemble(
            checker_run, mindiff, request.artifact_metadata
        )
        selection = self._action_selector.select(
            artifact, request.action_catalog
        )
        execution = self._executor.execute(
            selection, request.action_catalog, request.execution_tables
        )

        feedback = self._feedback_rows(
            execution, request.feedback_observation_ids
        )
        recertification = None
        if feedback:
            recertification = self._recertifier.recertify(
                artifact, feedback, request.action_catalog
            )
        system_state = self._state_deriver.derive(
            checker_run,
            recertification_result=recertification,
            action_selection=selection,
            execution_result=execution,
            level_certificate=request.level_certificate,
            active_gamma_hash=request.gamma_contract["hash"],
            active_evidence_hash=request.active_evidence_hash,
        )
        return KernelE2ERunResult(
            checker_run=checker_run,
            mindiff_result=mindiff,
            counterexample_artifact=MappingProxyType(deepcopy(artifact)),
            action_selection=selection,
            execution_result=execution,
            feedback_observation_ids=tuple(
                row["observation_id"] for row in feedback
            ),
            recertification_result=recertification,
            system_state=system_state,
        )

    @staticmethod
    def _feedback_rows(
        execution: ExecutionBatchResult,
        requested_ids: Sequence[str],
    ) -> tuple[Mapping[str, object], ...]:
        if not requested_ids:
            return ()
        observations_by_id: dict[str, Mapping[str, object]] = {}
        for row in execution.observations:
            observation_id = row.get("observation_id")
            if not isinstance(observation_id, str) or not observation_id:
                raise ValueError("executed observation lacks observation_id")
            if observation_id in observations_by_id:
                raise ValueError("executed observations contain duplicate IDs")
            observations_by_id[observation_id] = row

        missing = tuple(
            observation_id
            for observation_id in requested_ids
            if observation_id not in observations_by_id
        )
        if missing:
            raise ValueError(
                "feedback observation was not produced by this run: "
                + ", ".join(missing)
            )
        requested = frozenset(requested_ids)
        return tuple(
            row
            for observation_id, row in observations_by_id.items()
            if observation_id in requested
        )
