"""Finite, reproducible Part B B2 sampler stub for frozen local fixtures.

This module is deliberately not exported from :mod:`src.executor`.  It cannot
consume real sources, enter the Part A deterministic Executor or formal
ceiling, admit evidence, drive a Planner, access a holdout, issue a
certificate, or emit ``CERTIFIED_STOP``.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from fractions import Fraction
import hashlib

from src.ir.canonical_hash import (
    canonical_json,
    canonical_value_hash,
    has_valid_document_hash,
)


_SOURCE_SCOPE = "FROZEN_B2_FIXTURE_CATALOG_ONLY"
_GENERATOR_ALGORITHM = "SHA256_COUNTER_V1"
_GENERATOR_VERSION = "1.0.0"
_FAILURE_STATUS = {
    "TIMEOUT": "UNKNOWN",
    "RESOURCE_EXHAUSTED": "UNKNOWN",
    "MODEL_INVALID": "UNKNOWN",
    "INFEASIBLE": "INFEASIBLE",
}


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{label} must be an array")
    return value


def _require_local_authority(
    policy: Mapping[str, object],
    fixture: Mapping[str, object],
) -> None:
    if policy.get("execution_scope") != "LOCAL_FIXTURE_ONLY":
        raise ValueError("policy is outside the local fixture scope")
    authority = _mapping(policy.get("authority_boundary"), "authority_boundary")
    if authority.get("local_fixture_sampler") is not True:
        raise ValueError("local fixture sampler authority is absent")
    forbidden = (
        "production_sampling",
        "real_source_access",
        "holdout_release",
        "planner_execution",
        "estimated_model_admission",
        "certificate",
    )
    if any(authority.get(field) is not False for field in forbidden):
        raise ValueError("policy grants authority outside the local stub")
    if authority.get("stop_authority") != "NONE":
        raise ValueError("local sampler stub cannot hold STOP authority")

    if fixture.get("source_scope") != _SOURCE_SCOPE:
        raise ValueError("fixture source scope is not frozen-local-only")
    if fixture.get("real_source_access") is not False:
        raise ValueError("fixture cannot grant real-source access")
    if fixture.get("catalog_ceiling_eligible") is not False:
        raise ValueError("fixture cannot enter the formal catalog ceiling")


def _validate_identity(
    catalog: Mapping[str, object],
    policy: Mapping[str, object],
    fixture: Mapping[str, object],
) -> None:
    if not has_valid_document_hash(catalog):
        raise ValueError("frozen catalog hash does not replay")
    if not has_valid_document_hash(policy):
        raise ValueError("sampler policy hash does not replay")
    if not has_valid_document_hash(fixture):
        raise ValueError("sampler fixture hash does not replay")
    if fixture.get("catalog_hash") != catalog.get("hash"):
        raise ValueError("fixture is not bound to the supplied frozen catalog")


def _find_case(
    fixture: Mapping[str, object],
    action_id: str,
    world_id: str,
) -> None:
    for raw_case in _sequence(fixture.get("allowed_cases"), "allowed_cases"):
        case = _mapping(raw_case, "allowed case")
        if case.get("action_id") != action_id:
            continue
        if case.get("catalog_ceiling_eligible") is not False:
            raise ValueError("fixture case cannot enter the formal catalog ceiling")
        worlds = _sequence(case.get("world_ids"), "case world_ids")
        if world_id not in worlds:
            raise ValueError("world is outside the frozen fixture case")
        return
    raise ValueError("action is outside the frozen fixture catalog")


def _find_distribution(
    catalog: Mapping[str, object],
    action_id: str,
    world_id: str,
) -> tuple[tuple[str, Fraction], ...]:
    for raw_entry in _sequence(catalog.get("entries"), "catalog entries"):
        entry = _mapping(raw_entry, "catalog entry")
        if entry.get("action_id") != action_id:
            continue
        if entry.get("catalog_ceiling_eligible") is not False:
            raise ValueError("catalog entry cannot enter the formal ceiling")
        if entry.get("not_executable") is not True:
            raise ValueError("stub requires the frozen non-executable fixture entry")

        outcomes = tuple(
            str(item)
            for item in _sequence(entry.get("finite_outcomes"), "finite outcomes")
        )
        for raw_row in _sequence(
            entry.get("conditional_distribution"),
            "conditional distribution",
        ):
            row = _mapping(raw_row, "conditional distribution row")
            if row.get("world_id") != world_id:
                continue
            probabilities: dict[str, Fraction] = {}
            for raw_item in _sequence(row.get("probabilities"), "probabilities"):
                item = _mapping(raw_item, "probability item")
                encoded = _mapping(item.get("probability"), "exact probability")
                numerator = encoded.get("numerator")
                denominator = encoded.get("denominator")
                if (
                    not isinstance(numerator, int)
                    or isinstance(numerator, bool)
                    or not isinstance(denominator, int)
                    or isinstance(denominator, bool)
                    or numerator < 0
                    or denominator <= 0
                ):
                    raise ValueError("invalid exact probability")
                probabilities[str(item.get("outcome_id"))] = Fraction(
                    numerator,
                    denominator,
                )
            if set(probabilities) != set(outcomes):
                raise ValueError("probability row does not cover the outcome domain")
            if sum(probabilities.values(), Fraction(0, 1)) != Fraction(1, 1):
                raise ValueError("probability row is not normalized")
            return tuple((outcome, probabilities[outcome]) for outcome in outcomes)
        raise ValueError("world is outside the action distribution")
    raise ValueError("action is outside the frozen catalog")


def _trial_budget(policy: Mapping[str, object], value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("trial_budget must be an integer")
    budget = _mapping(policy.get("trial_budget"), "trial_budget policy")
    minimum = budget.get("minimum")
    maximum = budget.get("maximum")
    if not isinstance(minimum, int) or not isinstance(maximum, int):
        raise ValueError("trial budget policy is invalid")
    if value < minimum or value > maximum:
        raise ValueError("trial_budget is outside the frozen finite range")
    return value


def _generator(policy: Mapping[str, object]) -> dict[str, object]:
    generator = dict(_mapping(policy.get("generator"), "generator"))
    if (
        generator.get("algorithm") != _GENERATOR_ALGORITHM
        or generator.get("version") != _GENERATOR_VERSION
        or generator.get("deterministic_replay") is not True
        or generator.get("counter_origin") != 0
        or generator.get("uniform_mapping") != "UINT256_OVER_2_POW_256"
    ):
        raise ValueError("generator specification is not approved")
    return generator


def _draw(
    request_id: str,
    generator: Mapping[str, object],
    trial_index: int,
) -> Fraction:
    material = canonical_json(
        {
            "request_id": request_id,
            "generator": dict(generator),
            "trial_index": trial_index,
        }
    ).encode("utf-8")
    integer = int.from_bytes(hashlib.sha256(material).digest(), "big")
    return Fraction(integer, 1 << 256)


def _select_outcome(
    distribution: Sequence[tuple[str, Fraction]],
    draw: Fraction,
) -> str:
    cumulative = Fraction(0, 1)
    for outcome, probability in distribution:
        cumulative += probability
        if draw < cumulative:
            return outcome
    raise ValueError("normalized distribution did not select an outcome")


def sample_fixture(
    *,
    catalog: Mapping[str, object],
    policy: Mapping[str, object],
    fixture: Mapping[str, object],
    action_id: str,
    world_id: str,
    seed: int,
    trial_budget: int,
) -> dict[str, object]:
    """Replay a finite stochastic row under the approved local-stub boundary."""

    catalog = _mapping(catalog, "catalog")
    policy = _mapping(policy, "policy")
    fixture = _mapping(fixture, "fixture")
    if not isinstance(action_id, str) or not action_id:
        raise ValueError("action_id must be a non-empty string")
    if not isinstance(world_id, str) or not world_id:
        raise ValueError("world_id must be a non-empty string")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")

    _require_local_authority(policy, fixture)
    _validate_identity(catalog, policy, fixture)
    _find_case(fixture, action_id, world_id)
    distribution = _find_distribution(catalog, action_id, world_id)
    budget = _trial_budget(policy, trial_budget)
    generator = _generator(policy)

    seed_commitment = canonical_value_hash(
        {
            "commitment_algorithm": "SHA256_CANONICAL_JSON",
            "generator": generator,
            "seed": seed,
        }
    )
    request = {
        "source_scope": _SOURCE_SCOPE,
        "catalog_hash": catalog["hash"],
        "policy_hash": policy["hash"],
        "fixture_hash": fixture["hash"],
        "generator": generator,
        "action_id": action_id,
        "world_id": world_id,
        "seed_commitment": seed_commitment,
        "trial_budget": budget,
    }
    request_id = canonical_value_hash(request)
    sequence = [
        _select_outcome(distribution, _draw(request_id, generator, index))
        for index in range(budget)
    ]

    result: dict[str, object] = {
        "schema_version": "0.8.0",
        "status": "COMPLETED",
        "request_id": request_id,
        "source_scope": _SOURCE_SCOPE,
        "simulated": True,
        "admitted_case_evidence": False,
        "catalog_ceiling_eligible": False,
        "action_id": action_id,
        "world_id": world_id,
        "seed_commitment": seed_commitment,
        "trial_budget": budget,
        "catalog_hash": catalog["hash"],
        "policy_hash": policy["hash"],
        "fixture_hash": fixture["hash"],
        "generator": generator,
        "outcome_sequence": sequence,
        "outcome_counts": dict(Counter(sequence)),
        "resource_trace": {
            "status": "COMPLETED",
            "trials_requested": budget,
            "trials_completed": budget,
            "random_draw_count": budget,
            "failure_kind": None,
        },
    }
    result["trace_id"] = canonical_value_hash(result)
    return result


def failure_record(
    *,
    action_id: str,
    world_id: str,
    failure_kind: str,
) -> dict[str, object]:
    """Return a non-sample failure without evidence, UNSAT, or STOP authority."""

    if failure_kind not in _FAILURE_STATUS:
        raise ValueError("failure_kind is outside the frozen failure registry")
    if not isinstance(action_id, str) or not action_id:
        raise ValueError("action_id must be a non-empty string")
    if not isinstance(world_id, str) or not world_id:
        raise ValueError("world_id must be a non-empty string")
    return {
        "action_id": action_id,
        "world_id": world_id,
        "failure_kind": failure_kind,
        "status": _FAILURE_STATUS[failure_kind],
        "sample_emitted": False,
        "unsat": False,
        "catalog_ceiling_eligible": False,
    }


__all__ = ["failure_record", "sample_fixture"]
