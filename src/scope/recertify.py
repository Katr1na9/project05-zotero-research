"""P6 deterministic world elimination and candidate recertification.

Eligible P5 observations filter the complete legal-world table emitted by the
frozen Gamma/evidence compiler.  The counterexample support/alternative pair
is only an auditable witness projection; it is never treated as exhaustive.
The surviving assignments constrain the original ``FiniteDomainProblem`` and
the existing P1 Checker is run again. If ambiguity remains, the existing P2
MinDiff is rerun without inventing predicate projections. This module issues
no certificate, changes no admission or authority, and emits no system state
or STOP decision.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.checker.finite_domain import (
    CheckerRun,
    CheckerStatus,
    FiniteDomainChecker,
    FiniteDomainProblem,
)
from src.counterexample.mindiff import (
    FiniteWitnessMinDiff,
    MinDiffResult,
    PredicateProjectionContract,
)
from src.scope.finite_problem import (
    CompiledFiniteProblem,
    compiled_legal_worlds_hash,
)


def _required_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _string_sequence(
    value: object,
    field_name: str,
    *,
    nonempty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a string sequence")
    frozen = tuple(value)
    if nonempty and not frozen:
        raise ValueError(f"{field_name} must not be empty")
    if any(not isinstance(item, str) or not item for item in frozen):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(set(frozen)) != len(frozen):
        raise ValueError(f"{field_name} must not contain duplicates")
    return frozen


@dataclass(frozen=True)
class FiniteArtifactWorld:
    world_id: str
    target_result: str
    assignments: Mapping[str, object]
    predicates: frozenset[str]


@dataclass(frozen=True)
class IgnoredObservation:
    observation_id: str
    action_id: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "observation_id": self.observation_id,
            "action_id": self.action_id,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class WorldEliminationResult:
    all_worlds: tuple[FiniteArtifactWorld, ...]
    surviving_worlds: tuple[FiniteArtifactWorld, ...]
    eliminated_worlds: tuple[FiniteArtifactWorld, ...]
    applied_observation_ids: tuple[str, ...]
    ignored_observations: tuple[IgnoredObservation, ...]


@dataclass(frozen=True)
class RecertificationResult:
    checker_run: CheckerRun
    mindiff_result: MinDiffResult | None
    surviving_world_ids: tuple[str, ...]
    eliminated_world_ids: tuple[str, ...]
    applied_observation_ids: tuple[str, ...]
    ignored_observations: tuple[IgnoredObservation, ...]
    legal_world_count: int
    legal_worlds_hash: str

    def to_outcome_fields(self) -> dict[str, object]:
        """Return recertification fields without certificate or system state."""

        fields: dict[str, object] = dict(self.checker_run.to_outcome_fields())
        fields.update(
            {
                "surviving_world_ids": list(self.surviving_world_ids),
                "eliminated_world_ids": list(self.eliminated_world_ids),
                "applied_observation_ids": list(self.applied_observation_ids),
                "ignored_observations": [
                    observation.to_dict()
                    for observation in self.ignored_observations
                ],
                "legal_world_count": self.legal_world_count,
                "legal_worlds_hash": self.legal_worlds_hash,
            }
        )
        if self.mindiff_result is not None:
            fields["minimization_status"] = (
                self.mindiff_result.minimization_status.value
            )
            fields["distinguishing_predicates"] = list(
                self.mindiff_result.distinguishing_predicates
            )
            fields["unprojected_variables"] = list(
                self.mindiff_result.unprojected_variables
            )
        return fields


class DeterministicWorldEliminator:
    """Filter every compiler-declared legal world using eligible observations."""

    def eliminate(
        self,
        counterexample_artifact: Mapping[str, object],
        observations: Sequence[Mapping[str, object]],
        action_catalog: Mapping[str, object],
        compiled_problem: CompiledFiniteProblem,
    ) -> WorldEliminationResult:
        artifact = _required_mapping(counterexample_artifact, "counterexample")
        if artifact.get("checker_status") != "COUNTEREXAMPLE_FOUND":
            raise ValueError("world elimination requires COUNTEREXAMPLE_FOUND")
        worlds = self._compiled_worlds(artifact, compiled_problem)
        actions = self._catalog_actions(action_catalog)
        critical_absence = frozenset(
            _string_sequence(
                artifact.get("critical_absence_semantics", ()),
                "counterexample.critical_absence_semantics",
            )
        )

        if not isinstance(observations, Sequence) or isinstance(
            observations, (str, bytes)
        ):
            raise ValueError("observations must be a row sequence")

        surviving = list(worlds)
        eliminated: list[FiniteArtifactWorld] = []
        applied: list[str] = []
        ignored: list[IgnoredObservation] = []
        seen_observations: set[str] = set()
        for index, raw_observation in enumerate(observations):
            observation = _required_mapping(
                raw_observation, f"observations[{index}]"
            )
            observation_id = _required_string(
                observation.get("observation_id"),
                f"observations[{index}].observation_id",
            )
            action_id = _required_string(
                observation.get("action_id"),
                f"observations[{index}].action_id",
            )
            if observation_id in seen_observations:
                raise ValueError(f"duplicate observation ID: {observation_id!r}")
            seen_observations.add(observation_id)

            used = observation.get("used_for_world_elimination")
            complete = observation.get("completeness_conditions_satisfied")
            if not isinstance(used, bool) or not isinstance(complete, bool):
                raise ValueError(
                    f"observation {observation_id!r} eligibility flags must be boolean"
                )
            if not used:
                ignored.append(
                    IgnoredObservation(
                        observation_id, action_id, "NOT_MARKED_FOR_ELIMINATION"
                    )
                )
                continue
            if not complete:
                ignored.append(
                    IgnoredObservation(
                        observation_id, action_id, "COMPLETENESS_NOT_SATISFIED"
                    )
                )
                continue

            action = actions.get(action_id)
            if action is None:
                ignored.append(
                    IgnoredObservation(
                        observation_id, action_id, "UNKNOWN_CATALOG_ACTION"
                    )
                )
                continue
            if action.get("formal_analysis_eligibility") != "formal":
                ignored.append(
                    IgnoredObservation(
                        observation_id, action_id, "HEURISTIC_ONLY"
                    )
                )
                continue

            state_effect = _required_mapping(
                action.get("state_effect"), f"action {action_id!r}.state_effect"
            )
            elimination_rules = _string_sequence(
                state_effect.get("world_elimination_rule_ids"),
                f"action {action_id!r}.world_elimination_rule_ids",
            )
            if not elimination_rules:
                ignored.append(
                    IgnoredObservation(
                        observation_id, action_id, "NO_WORLD_ELIMINATION_RULE"
                    )
                )
                continue

            observation_model = action.get("observation_model")
            if observation_model is None:
                ignored.append(
                    IgnoredObservation(
                        observation_id, action_id, "OBSERVATION_MODEL_MISSING"
                    )
                )
                continue
            model = _required_mapping(
                observation_model, f"action {action_id!r}.observation_model"
            )
            if model.get("noise_model") != "deterministic":
                raise ValueError(
                    f"action {action_id!r} has a non-deterministic observation model"
                )
            dependencies = _string_sequence(
                model.get("world_dependencies"),
                f"action {action_id!r}.world_dependencies",
                nonempty=True,
            )
            if len(dependencies) != 1:
                raise ValueError(
                    f"action {action_id!r} requires one finite-world dependency"
                )
            output_domain = model.get("output_domain")
            if not isinstance(output_domain, Sequence) or isinstance(
                output_domain, (str, bytes)
            ):
                raise ValueError(f"action {action_id!r}.output_domain is invalid")
            observed_value = observation.get("observed_value")
            if observed_value not in output_domain:
                raise ValueError(
                    f"observation {observation_id!r} is outside output_domain"
                )

            if observed_value == "absent":
                absence_ref = _required_string(
                    model.get("absence_semantics_ref"),
                    f"action {action_id!r}.absence_semantics_ref",
                )
                legal_absence = {
                    f"{absence_ref}:bounded_completeness",
                    f"{absence_ref}:closed_world",
                }
                if critical_absence.isdisjoint(legal_absence):
                    ignored.append(
                        IgnoredObservation(
                            observation_id,
                            action_id,
                            "ABSENCE_SEMANTICS_UNVERIFIED",
                        )
                    )
                    continue

            dependency = dependencies[0]
            compatible: list[FiniteArtifactWorld] = []
            for world in surviving:
                predicted = self._predict_observation(
                    world, dependency, output_domain
                )
                if predicted == observed_value:
                    compatible.append(world)
                else:
                    eliminated.append(world)
            surviving = compatible
            applied.append(observation_id)

        return WorldEliminationResult(
            all_worlds=worlds,
            surviving_worlds=tuple(surviving),
            eliminated_worlds=tuple(eliminated),
            applied_observation_ids=tuple(applied),
            ignored_observations=tuple(ignored),
        )

    @staticmethod
    def _predict_observation(
        world: FiniteArtifactWorld,
        dependency: str,
        output_domain: Sequence[object],
    ) -> object:
        assignment_prefix = dependency + "="
        assignments = tuple(
            predicate[len(assignment_prefix) :]
            for predicate in world.predicates
            if predicate.startswith(assignment_prefix)
        )
        if len(assignments) > 1:
            raise ValueError(
                f"world {world.world_id!r} has conflicting {dependency!r} values"
            )
        presence_domain = "present" in output_domain and "absent" in output_domain
        if presence_domain:
            if dependency in world.predicates or assignments:
                return "present"
            return "absent"
        if assignments:
            return assignments[0]
        if dependency in world.predicates and "present" in output_domain:
            return "present"
        return "absent"

    @staticmethod
    def _compiled_worlds(
        artifact: Mapping[str, object],
        compiled: CompiledFiniteProblem,
    ) -> tuple[FiniteArtifactWorld, ...]:
        if not isinstance(compiled, CompiledFiniteProblem):
            raise ValueError("compiled_problem must be a CompiledFiniteProblem")
        target_level = _required_string(
            artifact.get("target_level"), "counterexample.target_level"
        )
        if (
            compiled.target_variable != target_level
            or compiled.gamma_hash != artifact.get("gamma_hash")
        ):
            raise ValueError("compiled problem does not bind counterexample scope")

        artifact_worlds: dict[str, tuple[str, frozenset[str]]] = {}
        for role in ("support_world", "alternative_world"):
            raw_world = _required_mapping(
                artifact.get(role), f"counterexample.{role}"
            )
            world_id = _required_string(
                raw_world.get("world_id"), f"counterexample.{role}.world_id"
            )
            target_result = _required_mapping(
                raw_world.get("target_result"),
                f"counterexample.{role}.target_result",
            )
            target_id = _required_string(
                target_result.get("entity_id"),
                f"counterexample.{role}.target_result.entity_id",
            )
            predicates = frozenset(
                _string_sequence(
                    raw_world.get("predicates"),
                    f"counterexample.{role}.predicates",
                    nonempty=True,
                )
            )
            if world_id in artifact_worlds:
                raise ValueError(f"duplicate artifact world ID: {world_id!r}")
            artifact_worlds[world_id] = (target_id, predicates)

        worlds: list[FiniteArtifactWorld] = []
        world_ids: set[str] = set()
        variables = tuple(compiled.problem.domains)
        for declared in compiled.legal_worlds:
            world_id = _required_string(declared.world_id, "compiled world_id")
            if world_id in world_ids:
                raise ValueError(f"duplicate compiled world ID: {world_id!r}")
            world_ids.add(world_id)
            target_id = _required_string(
                declared.assignments.get(target_level),
                f"compiled world {world_id!r}.{target_level}",
            )
            if set(declared.assignments) != set(variables):
                raise ValueError("compiled world assignments are incomplete")
            predicates = frozenset(
                _string_sequence(
                    declared.predicates,
                    f"compiled world {world_id!r}.predicates",
                    nonempty=False,
                )
            )
            worlds.append(
                FiniteArtifactWorld(
                    world_id,
                    target_id,
                    declared.assignments,
                    predicates,
                )
            )
        for world_id, (target_id, predicates) in artifact_worlds.items():
            matches = tuple(world for world in worlds if world.world_id == world_id)
            if len(matches) != 1:
                raise ValueError(
                    f"artifact witness {world_id!r} is absent from compiled worlds"
                )
            compiled_world = matches[0]
            if (
                compiled_world.target_result != target_id
                or not predicates.issubset(compiled_world.predicates)
            ):
                raise ValueError(
                    f"artifact witness {world_id!r} disagrees with compiled world"
                )
        return tuple(worlds)

    @staticmethod
    def _catalog_actions(
        action_catalog: Mapping[str, object],
    ) -> dict[str, Mapping[str, object]]:
        catalog = _required_mapping(action_catalog, "action_catalog")
        raw_actions = catalog.get("actions")
        if not isinstance(raw_actions, Sequence) or isinstance(
            raw_actions, (str, bytes)
        ):
            raise ValueError("action_catalog.actions must be an action sequence")
        actions: dict[str, Mapping[str, object]] = {}
        for index, raw_action in enumerate(raw_actions):
            action = _required_mapping(
                raw_action, f"action_catalog.actions[{index}]"
            )
            action_id = _required_string(
                action.get("action_id"),
                f"action_catalog.actions[{index}].action_id",
            )
            if action_id in actions:
                raise ValueError(f"duplicate catalog action ID: {action_id!r}")
            actions[action_id] = action
        return actions


class RecertificationOrchestrator:
    """Eliminate worlds, rebuild the finite target problem, and rerun P1/P2."""

    def __init__(self) -> None:
        self._eliminator = DeterministicWorldEliminator()

    def recertify(
        self,
        counterexample_artifact: Mapping[str, object],
        observations: Sequence[Mapping[str, object]],
        action_catalog: Mapping[str, object],
        compiled_problem: CompiledFiniteProblem,
        *,
        predicate_projections: PredicateProjectionContract | None = None,
    ) -> RecertificationResult:
        artifact = _required_mapping(counterexample_artifact, "counterexample")
        elimination = self._eliminator.eliminate(
            artifact, observations, action_catalog, compiled_problem
        )
        target_level = _required_string(
            artifact.get("target_level"), "counterexample.target_level"
        )
        candidate_ref = _required_mapping(
            artifact.get("candidate_q"), "counterexample.candidate_q"
        )
        candidate = _required_string(
            candidate_ref.get("entity_id"), "counterexample.candidate_q.entity_id"
        )

        variables = tuple(compiled_problem.problem.domains)
        surviving_assignments = frozenset(
            tuple(world.assignments[variable] for variable in variables)
            for world in elimination.surviving_worlds
        )

        def survived(world: Mapping[str, object]) -> bool:
            return tuple(world[variable] for variable in variables) in surviving_assignments

        problem = FiniteDomainProblem(
            domains=compiled_problem.problem.domains,
            constraints=compiled_problem.problem.constraints + (survived,),
        )
        checker_run = FiniteDomainChecker().check_candidate(
            problem,
            target_variable=target_level,
            candidate=candidate,
        )
        mindiff_result = None
        if checker_run.checker_status is CheckerStatus.COUNTEREXAMPLE_FOUND:
            projections = predicate_projections
            if projections is None:
                projections = PredicateProjectionContract.empty(problem.domains)
            else:
                projections.validate_for_variables(problem.domains)
            mindiff_result = FiniteWitnessMinDiff().compare(
                checker_run,
                target_variable=target_level,
                predicate_projections=projections,
            )

        return RecertificationResult(
            checker_run=checker_run,
            mindiff_result=mindiff_result,
            surviving_world_ids=tuple(
                world.world_id for world in elimination.surviving_worlds
            ),
            eliminated_world_ids=tuple(
                world.world_id for world in elimination.eliminated_worlds
            ),
            applied_observation_ids=elimination.applied_observation_ids,
            ignored_observations=elimination.ignored_observations,
            legal_world_count=len(compiled_problem.legal_worlds),
            legal_worlds_hash=compiled_legal_worlds_hash(compiled_problem),
        )
