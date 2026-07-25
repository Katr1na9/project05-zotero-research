"""Compile the frozen v0.8 Twin finite problem from Gamma and case evidence.

This module replaces test-owned world lambdas with one deterministic,
fail-closed compiler. It recognizes only the narrow v0.8 initial-foothold
mechanism profile; it is not a generic rule engine, Planner, or Part B
connector. Hidden/oracle fields are forbidden inputs.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from src.checker.finite_domain import FiniteDomainProblem
from src.ir.canonical_hash import canonical_value_hash, has_valid_document_hash


_MODE_VARIABLE = "authentication_mode"
_MODE_DOMAIN = ("lateral", "direct")
_REQUIRED_MECHANISM_RULES = frozenset(
    {
        "credential_login_implies_authentication",
        "lateral_movement_requires_prior_compromise",
    }
)
_ORACLE_FIELDS = frozenset(
    {
        "ground_truth",
        "recoverable_claim_ids",
        "oracle_effects",
        "hidden_claim_ids",
        "true_outcome",
    }
)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _string_sequence(
    value: object,
    field: str,
    *,
    require_nonempty: bool = True,
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be a string sequence")
    frozen = tuple(value)
    if require_nonempty and not frozen:
        raise ValueError(f"{field} must not be empty")
    if any(not isinstance(item, str) or not item for item in frozen):
        raise ValueError(f"{field} must contain non-empty strings")
    if len(set(frozen)) != len(frozen):
        raise ValueError(f"{field} must not contain duplicates")
    return frozen


def _contains_oracle_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            key in _ORACLE_FIELDS or _contains_oracle_field(nested)
            for key, nested in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_contains_oracle_field(item) for item in value)
    return False


def _is_admitted_case_evidence(claim: Mapping[str, object]) -> bool:
    authority = claim.get("certification_authority")
    return (
        claim.get("modality") == "observed"
        and claim.get("truth_status") == "supported"
        and claim.get("epistemic_role") == "case_evidence"
        and claim.get("binding_status") == "bound"
        and claim.get("admission_status") == "admitted"
        and claim.get("lifecycle_state") == "admitted"
        and isinstance(authority, Mapping)
        and authority.get("allowed") is True
    )


@dataclass(frozen=True)
class CompiledLegalWorld:
    """One Gamma-declared legal world with auditable observation predicates."""

    world_id: str
    assignments: Mapping[str, str]
    predicates: tuple[str, ...]


@dataclass(frozen=True)
class CompiledFiniteProblem:
    """Auditable output of the narrow evidence/Gamma compilation profile."""

    problem: FiniteDomainProblem
    target_variable: str
    mode_variable: str
    possible_lateral_source: str | None
    destination_host: str | None
    source_claim_ids: tuple[str, ...]
    gamma_hash: str
    compilation_profile: str
    legal_worlds: tuple[CompiledLegalWorld, ...]


def compiled_legal_world_documents(
    compiled: CompiledFiniteProblem,
) -> tuple[dict[str, object], ...]:
    """Return the canonical, auditable legal-world projection for bindings."""

    if not isinstance(compiled, CompiledFiniteProblem):
        raise ValueError("compiled must be a CompiledFiniteProblem")
    return tuple(
        {
            "world_id": world.world_id,
            "assignments": dict(world.assignments),
            "predicates": list(world.predicates),
        }
        for world in compiled.legal_worlds
    )


def compiled_legal_worlds_hash(compiled: CompiledFiniteProblem) -> str:
    """Hash the exact ordered legal-world table used by Checker/recertification."""

    return canonical_value_hash(compiled_legal_world_documents(compiled))


class EvidenceGammaFiniteProblemCompiler:
    """Compile the deterministic two-mechanism v0.8 finite problem."""

    def compile(
        self,
        gamma_contract: Mapping[str, object],
        case_evidence: Sequence[Mapping[str, object]],
        *,
        target_variable: str,
    ) -> CompiledFiniteProblem:
        gamma = _mapping(gamma_contract, "gamma_contract")
        target = _string(target_variable, "target_variable")
        if _contains_oracle_field(gamma):
            raise ValueError("Gamma must not contain oracle or hidden fields")
        if gamma.get("schema_version") != "0.8.0":
            raise ValueError("Gamma schema_version must be 0.8.0")
        if not has_valid_document_hash(gamma):
            raise ValueError("Gamma canonical hash does not replay")

        attribution_levels = _string_sequence(
            gamma.get("attribution_levels"), "Gamma.attribution_levels"
        )
        if target not in attribution_levels:
            raise ValueError("target_variable is outside Gamma attribution_levels")

        result_domains = _mapping(
            gamma.get("result_domains"), "Gamma.result_domains"
        )
        result_domain = _mapping(
            result_domains.get(target), f"Gamma.result_domains.{target}"
        )
        if result_domain.get("generator") != "from_finite_candidate_list":
            raise ValueError("target result domain is not an explicit finite list")
        if result_domain.get("finiteness_basis") != "explicit_finite_candidates":
            raise ValueError("target result domain lacks explicit finiteness basis")
        if result_domain.get("coverage_mode") != "exhaustive":
            raise ValueError("Twin compilation requires exhaustive target coverage")
        candidates = _string_sequence(
            result_domain.get("finite_candidates"),
            f"Gamma.result_domains.{target}.finite_candidates",
        )

        mechanism_rules = frozenset(
            _string_sequence(gamma.get("mechanism_rules"), "Gamma.mechanism_rules")
        )
        missing_rules = tuple(sorted(_REQUIRED_MECHANISM_RULES - mechanism_rules))
        if missing_rules:
            raise ValueError(
                "Gamma lacks required finite-problem mechanism rules: "
                + ", ".join(missing_rules)
            )

        if not isinstance(case_evidence, Sequence) or isinstance(
            case_evidence, (str, bytes)
        ):
            raise ValueError("case_evidence must be a claim sequence")

        hosts_by_predicate: dict[str, set[str]] = {
            "authenticated_account": set(),
            "executed_process": set(),
        }
        source_claim_ids: list[str] = []
        for index, raw_claim in enumerate(case_evidence):
            claim = _mapping(raw_claim, f"case_evidence[{index}]")
            if _contains_oracle_field(claim):
                raise ValueError("case evidence must not contain oracle or hidden fields")
            if not _is_admitted_case_evidence(claim):
                continue
            predicate = claim.get("predicate")
            if predicate not in hosts_by_predicate:
                continue
            subject = _mapping(
                claim.get("subject"), f"case_evidence[{index}].subject"
            )
            if subject.get("entity_type") != "host":
                raise ValueError(f"{predicate} subject must be a host")
            host = _string(
                subject.get("entity_id"),
                f"case_evidence[{index}].subject.entity_id",
            )
            hosts_by_predicate[predicate].add(host)
            source_claim_ids.append(
                _string(claim.get("claim_id"), f"case_evidence[{index}].claim_id")
            )

        destination_host = self._single_host(
            hosts_by_predicate["authenticated_account"], "authenticated_account"
        )
        possible_lateral_source = self._single_host(
            hosts_by_predicate["executed_process"], "executed_process"
        )
        if destination_host == possible_lateral_source:
            raise ValueError("source and destination evidence hosts must be distinct")
        for role, host in (
            ("destination", destination_host),
            ("possible lateral source", possible_lateral_source),
        ):
            if host not in candidates:
                raise ValueError(f"{role} host is outside the frozen target domain")

        def mechanism_constraint(
            world: Mapping[str, object],
            *,
            target_name: str = target,
            mode_name: str = _MODE_VARIABLE,
            source: str = possible_lateral_source,
            destination: str = destination_host,
        ) -> bool:
            return (
                world[target_name] == source and world[mode_name] == "lateral"
            ) or (
                world[target_name] == destination and world[mode_name] == "direct"
            )

        problem = FiniteDomainProblem(
            domains={target: candidates, _MODE_VARIABLE: _MODE_DOMAIN},
            constraints=(mechanism_constraint,),
        )
        legal_worlds = (
            CompiledLegalWorld(
                world_id=f"W-SUPPORT-{possible_lateral_source}",
                assignments=MappingProxyType(
                    {target: possible_lateral_source, _MODE_VARIABLE: "lateral"}
                ),
                predicates=(
                    f"credential_activity:{possible_lateral_source}",
                    f"authentication_origin:{destination_host}={possible_lateral_source}",
                    f"compromised:{destination_host}",
                ),
            ),
            CompiledLegalWorld(
                world_id=f"W-ALTERNATIVE-{destination_host}",
                assignments=MappingProxyType(
                    {target: destination_host, _MODE_VARIABLE: "direct"}
                ),
                predicates=(
                    f"external_credential_login:{destination_host}",
                    f"authentication_origin:{destination_host}=EXTERNAL",
                    f"compromised:{destination_host}",
                ),
            ),
        )
        return CompiledFiniteProblem(
            problem=problem,
            target_variable=target,
            mode_variable=_MODE_VARIABLE,
            possible_lateral_source=possible_lateral_source,
            destination_host=destination_host,
            source_claim_ids=tuple(sorted(source_claim_ids)),
            gamma_hash=gamma["hash"],
            compilation_profile="evidence_bound_initial_foothold_v0.8",
            legal_worlds=legal_worlds,
        )

    @staticmethod
    def _single_host(hosts: set[str], predicate: str) -> str:
        if len(hosts) != 1:
            raise ValueError(
                f"{predicate} must bind exactly one admitted evidence host"
            )
        return next(iter(hosts))


class DeclarativeFiniteWorldCompiler:
    """Compile a Gamma ``explicit_legal_worlds_v0.8`` model fail closed."""

    def compile(
        self,
        gamma_contract: Mapping[str, object],
        case_evidence: Sequence[Mapping[str, object]],
        *,
        target_variable: str,
    ) -> CompiledFiniteProblem:
        gamma = _mapping(gamma_contract, "gamma_contract")
        target = _string(target_variable, "target_variable")
        if _contains_oracle_field(gamma):
            raise ValueError("Gamma must not contain oracle or hidden fields")
        if gamma.get("schema_version") != "0.8.0" or not has_valid_document_hash(
            gamma
        ):
            raise ValueError("Gamma schema/hash is not a verified v0.8 contract")

        result_domains = _mapping(gamma.get("result_domains"), "result_domains")
        result_domain = _mapping(
            result_domains.get(target), f"result_domains.{target}"
        )
        if (
            result_domain.get("generator") != "from_finite_candidate_list"
            or result_domain.get("coverage_mode") != "exhaustive"
            or result_domain.get("finiteness_basis")
            != "explicit_finite_candidates"
        ):
            raise ValueError("declarative target must be an exhaustive finite list")
        candidates = _string_sequence(
            result_domain.get("finite_candidates"),
            f"result_domains.{target}.finite_candidates",
        )

        model = _mapping(gamma.get("formal_model"), "formal_model")
        if (
            model.get("profile") != "explicit_legal_worlds_v0.8"
            or model.get("target_variable") != target
        ):
            raise ValueError("formal_model profile/target mismatch")
        model_id = _string(model.get("model_id"), "formal_model.model_id")
        raw_auxiliary = _mapping(
            model.get("auxiliary_domains"), "formal_model.auxiliary_domains"
        )
        if target in raw_auxiliary:
            raise ValueError("target must not be repeated as an auxiliary domain")
        domains: dict[str, tuple[str, ...]] = {target: candidates}
        for variable, raw_domain in raw_auxiliary.items():
            variable_name = _string(variable, "auxiliary domain name")
            domains[variable_name] = _string_sequence(
                raw_domain, f"formal_model.auxiliary_domains.{variable_name}"
            )

        evidence = self._admitted_evidence(case_evidence)
        source_claim_ids = self._check_evidence_requirements(
            model.get("evidence_requirements"), evidence
        )
        legal_worlds = self._legal_worlds(model.get("legal_worlds"), domains)
        represented_targets = {world.assignments[target] for world in legal_worlds}
        if represented_targets != set(candidates):
            raise ValueError("legal worlds must represent every target candidate")

        legal_assignments = frozenset(
            tuple(world.assignments[variable] for variable in domains)
            for world in legal_worlds
        )

        def legal_world_constraint(
            world: Mapping[str, object],
            *,
            variables: tuple[str, ...] = tuple(domains),
            legal: frozenset[tuple[str, ...]] = legal_assignments,
        ) -> bool:
            return tuple(world[variable] for variable in variables) in legal

        problem = FiniteDomainProblem(
            domains=domains,
            constraints=(legal_world_constraint,),
        )
        return CompiledFiniteProblem(
            problem=problem,
            target_variable=target,
            mode_variable=next(iter(raw_auxiliary)),
            possible_lateral_source=None,
            destination_host=None,
            source_claim_ids=source_claim_ids,
            gamma_hash=gamma["hash"],
            compilation_profile=f"explicit_legal_worlds_v0.8:{model_id}",
            legal_worlds=legal_worlds,
        )

    @staticmethod
    def _admitted_evidence(
        case_evidence: Sequence[Mapping[str, object]],
    ) -> tuple[Mapping[str, object], ...]:
        if not isinstance(case_evidence, Sequence) or isinstance(
            case_evidence, (str, bytes)
        ):
            raise ValueError("case_evidence must be a claim sequence")
        admitted = []
        for index, raw_claim in enumerate(case_evidence):
            claim = _mapping(raw_claim, f"case_evidence[{index}]")
            if _contains_oracle_field(claim):
                raise ValueError("case evidence must not contain oracle fields")
            if _is_admitted_case_evidence(claim):
                admitted.append(claim)
        return tuple(admitted)

    @staticmethod
    def _check_evidence_requirements(
        raw_requirements: object,
        evidence: Sequence[Mapping[str, object]],
    ) -> tuple[str, ...]:
        if not isinstance(raw_requirements, Sequence) or isinstance(
            raw_requirements, (str, bytes)
        ):
            raise ValueError("evidence_requirements must be a sequence")
        matched_claim_ids: set[str] = set()
        seen_requirement_ids: set[str] = set()
        for index, raw_requirement in enumerate(raw_requirements):
            requirement = _mapping(
                raw_requirement, f"evidence_requirements[{index}]"
            )
            requirement_id = _string(
                requirement.get("requirement_id"),
                f"evidence_requirements[{index}].requirement_id",
            )
            if requirement_id in seen_requirement_ids:
                raise ValueError("duplicate evidence requirement ID")
            seen_requirement_ids.add(requirement_id)
            predicate = _string(
                requirement.get("predicate"),
                f"evidence_requirements[{index}].predicate",
            )
            families = frozenset(
                _string_sequence(
                    requirement.get("source_families"),
                    f"evidence_requirements[{index}].source_families",
                )
            )
            minimum = requirement.get("minimum_count")
            if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
                raise ValueError("minimum_count must be a positive integer")
            matches = tuple(
                claim
                for claim in evidence
                if claim.get("predicate") == predicate
                and claim.get("source_family") in families
            )
            if len(matches) < minimum:
                raise ValueError(
                    f"evidence requirement {requirement_id!r} is not satisfied"
                )
            matched_claim_ids.update(
                _string(claim.get("claim_id"), "case evidence claim_id")
                for claim in matches
            )
        return tuple(sorted(matched_claim_ids))

    @staticmethod
    def _legal_worlds(
        raw_worlds: object,
        domains: Mapping[str, Sequence[str]],
    ) -> tuple[CompiledLegalWorld, ...]:
        if not isinstance(raw_worlds, Sequence) or isinstance(
            raw_worlds, (str, bytes)
        ):
            raise ValueError("legal_worlds must be a sequence")
        worlds: list[CompiledLegalWorld] = []
        world_ids: set[str] = set()
        assignments_seen: set[tuple[str, ...]] = set()
        variables = tuple(domains)
        for index, raw_world in enumerate(raw_worlds):
            world = _mapping(raw_world, f"legal_worlds[{index}]")
            world_id = _string(world.get("world_id"), f"legal_worlds[{index}].world_id")
            if world_id in world_ids:
                raise ValueError("duplicate legal world ID")
            world_ids.add(world_id)
            assignments = _mapping(
                world.get("assignments"), f"legal_worlds[{index}].assignments"
            )
            if set(assignments) != set(variables):
                raise ValueError("legal world assignments must cover every variable")
            frozen_assignment: dict[str, str] = {}
            for variable in variables:
                value = _string(
                    assignments.get(variable),
                    f"legal_worlds[{index}].assignments.{variable}",
                )
                if value not in domains[variable]:
                    raise ValueError("legal world value is outside its domain")
                frozen_assignment[variable] = value
            assignment_key = tuple(frozen_assignment[variable] for variable in variables)
            if assignment_key in assignments_seen:
                raise ValueError("duplicate legal world assignment")
            assignments_seen.add(assignment_key)
            predicates = _string_sequence(
                world.get("predicates"), f"legal_worlds[{index}].predicates"
            )
            worlds.append(
                CompiledLegalWorld(
                    world_id=world_id,
                    assignments=MappingProxyType(frozen_assignment),
                    predicates=predicates,
                )
            )
        if len(worlds) < 2:
            raise ValueError("at least two legal worlds are required")
        return tuple(worlds)
