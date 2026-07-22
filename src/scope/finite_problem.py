"""Compile the frozen v0.8 Twin finite problem from Gamma and case evidence.

This module replaces test-owned world lambdas with one deterministic,
fail-closed compiler. It recognizes only the narrow v0.8 initial-foothold
mechanism profile; it is not a generic rule engine, Planner, or Part B
connector. Hidden/oracle fields are forbidden inputs.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.checker.finite_domain import FiniteDomainProblem


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
class CompiledFiniteProblem:
    """Auditable output of the narrow evidence/Gamma compilation profile."""

    problem: FiniteDomainProblem
    target_variable: str
    mode_variable: str
    possible_lateral_source: str
    destination_host: str
    source_claim_ids: tuple[str, ...]


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
        return CompiledFiniteProblem(
            problem=problem,
            target_variable=target,
            mode_variable=_MODE_VARIABLE,
            possible_lateral_source=possible_lateral_source,
            destination_host=destination_host,
            source_claim_ids=tuple(sorted(source_claim_ids)),
        )

    @staticmethod
    def _single_host(hosts: set[str], predicate: str) -> str:
        if len(hosts) != 1:
            raise ValueError(
                f"{predicate} must bind exactly one admitted evidence host"
            )
        return next(iter(hosts))
