"""Auditable formal ceiling verification for frozen finite Kernel domains.

The ceiling is deliberately model-relative: it proves exhaustive enumeration
of a verified finite Gamma/compiled-problem pair and the exact deterministic
formal action/observation subset of a verified catalog.  It does not claim
coverage of unmodeled real-world hypotheses, future actions, or external
connectors.  Requests outside that frozen domain fail closed; resource
exhaustion is UNKNOWN and never UNSAT.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from itertools import product
import json
from math import prod
from types import MappingProxyType

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_json,
    has_valid_document_hash,
)

from .finite_problem import (
    CompiledFiniteProblem,
    compiled_legal_world_documents,
    compiled_legal_worlds_hash,
)


class CeilingStatus(str, Enum):
    VERIFIED = "VERIFIED"
    OUTSIDE_FROZEN_DOMAIN = "OUTSIDE_FROZEN_DOMAIN"
    UNKNOWN_RESOURCE_EXHAUSTED = "UNKNOWN_RESOURCE_EXHAUSTED"
    INVALID_ARTIFACT = "INVALID_ARTIFACT"


_FACTORY_TOKEN = object()
_SUPPORTED_PROFILES = (
    "evidence_bound_initial_foothold_v0.8",
    "explicit_legal_worlds_v0.8:",
)


@dataclass(frozen=True)
class FormalCeilingAssessment:
    """Factory-owned ceiling decision and optional immutable verified report."""

    status: CeilingStatus
    reason_code: str
    report_json: str | None
    _factory_token: object

    def __post_init__(self) -> None:
        if self._factory_token is not _FACTORY_TOKEN:
            raise ValueError("FormalCeilingAssessment must come from the verifier")
        if self.status is CeilingStatus.VERIFIED:
            if self.report_json is None:
                raise ValueError("VERIFIED ceiling requires a report")
            report = json.loads(self.report_json)
            if (
                report.get("status") != "VERIFIED"
                or report.get("hash") != canonical_document_hash(report)
            ):
                raise ValueError("verified ceiling report hash does not replay")
        elif self.report_json is not None:
            raise ValueError("failed ceiling assessment must not expose proof report")

    @property
    def verified(self) -> bool:
        return self.status is CeilingStatus.VERIFIED

    def to_dict(self) -> dict[str, object] | None:
        return json.loads(self.report_json) if self.report_json is not None else None

    @property
    def ceiling_hash(self) -> str | None:
        report = self.to_dict()
        return report["hash"] if report is not None else None

    def binds(
        self,
        *,
        gamma_hash: object,
        catalog_hash: object,
        target_level: object,
        declared_domain_size: object,
        result_candidates: object,
        legal_world_count: object,
        legal_worlds_hash: object,
        cartesian_assignment_bound: object,
    ) -> bool:
        report = self.to_dict()
        return (
            self.verified
            and report is not None
            and report.get("gamma_hash") == gamma_hash
            and report.get("catalog_hash") == catalog_hash
            and report.get("target_level") == target_level
            and len(report.get("result_candidates", ())) == declared_domain_size
            and report.get("result_candidates") == result_candidates
            and report.get("legal_world_count") == legal_world_count
            and report.get("legal_worlds_hash") == legal_worlds_hash
            and report.get("cartesian_assignment_bound")
            == cartesian_assignment_bound
        )


class FormalCeilingVerifier:
    """Verify exact finite model/action coverage or return a fail-closed state."""

    def assess(
        self,
        gamma_contract: Mapping[str, object],
        compiled: CompiledFiniteProblem,
        action_catalog: Mapping[str, object],
        *,
        requested_target: str,
        requested_actions: Sequence[str] | None = None,
        max_assignments: int | None = None,
    ) -> FormalCeilingAssessment:
        try:
            return self._assess(
                gamma_contract,
                compiled,
                action_catalog,
                requested_target=requested_target,
                requested_actions=requested_actions,
                max_assignments=max_assignments,
            )
        except (KeyError, TypeError, ValueError):
            return self._failed(
                CeilingStatus.INVALID_ARTIFACT,
                "CEILING-004_INVALID_OR_UNBOUND_ARTIFACT",
            )

    def _assess(
        self,
        gamma: Mapping[str, object],
        compiled: CompiledFiniteProblem,
        catalog: Mapping[str, object],
        *,
        requested_target: str,
        requested_actions: Sequence[str] | None,
        max_assignments: int | None,
    ) -> FormalCeilingAssessment:
        if not isinstance(gamma, Mapping) or not isinstance(catalog, Mapping):
            raise ValueError("Gamma/catalog must be objects")
        if not isinstance(compiled, CompiledFiniteProblem):
            raise ValueError("compiled problem has the wrong type")
        if not has_valid_document_hash(gamma) or not has_valid_document_hash(catalog):
            raise ValueError("artifact hash mismatch")
        if compiled.gamma_hash != gamma.get("hash"):
            raise ValueError("compiled Gamma hash mismatch")
        if not any(
            compiled.compilation_profile == profile
            or compiled.compilation_profile.startswith(profile)
            for profile in _SUPPORTED_PROFILES
        ):
            raise ValueError("unsupported compilation profile")
        if not isinstance(requested_target, str) or not requested_target:
            raise ValueError("requested_target must be non-empty")
        if requested_target != compiled.target_variable:
            return self._failed(
                CeilingStatus.OUTSIDE_FROZEN_DOMAIN,
                "CEILING-002_TARGET_OUTSIDE_FROZEN_DOMAIN",
            )

        result_domains = gamma.get("result_domains")
        if not isinstance(result_domains, Mapping):
            raise ValueError("Gamma result_domains missing")
        result_domain = result_domains.get(requested_target)
        if not isinstance(result_domain, Mapping):
            return self._failed(
                CeilingStatus.OUTSIDE_FROZEN_DOMAIN,
                "CEILING-002_TARGET_OUTSIDE_FROZEN_DOMAIN",
            )
        candidates = self._strings(
            result_domain.get("finite_candidates"), require_nonempty=True
        )
        if (
            result_domain.get("generator") != "from_finite_candidate_list"
            or result_domain.get("coverage_mode") != "exhaustive"
            or result_domain.get("finiteness_basis")
            != "explicit_finite_candidates"
            or tuple(compiled.problem.domains[requested_target]) != candidates
        ):
            raise ValueError("target domain is not exact exhaustive finite coverage")

        variable_domains = {
            variable: list(values)
            for variable, values in compiled.problem.domains.items()
        }
        assignment_bound = prod(len(values) for values in variable_domains.values())
        if max_assignments is not None and (
            isinstance(max_assignments, bool)
            or not isinstance(max_assignments, int)
            or max_assignments <= 0
        ):
            raise ValueError("max_assignments must be positive or None")
        if max_assignments is not None and max_assignments < assignment_bound:
            return self._failed(
                CeilingStatus.UNKNOWN_RESOURCE_EXHAUSTED,
                "CEILING-003_ENUMERATION_RESOURCE_EXHAUSTED",
            )

        variables = tuple(compiled.problem.domains)
        legal_assignments: list[dict[str, object]] = []
        domains = tuple(compiled.problem.domains[name] for name in variables)
        for values in product(*domains):
            world = MappingProxyType(dict(zip(variables, values)))
            if all(constraint(world) for constraint in compiled.problem.constraints):
                legal_assignments.append(dict(world))
        if not legal_assignments:
            raise ValueError("verified ceiling cannot be empty")
        declared_assignments = [dict(world.assignments) for world in compiled.legal_worlds]
        if canonical_json(legal_assignments) != canonical_json(declared_assignments):
            raise ValueError("compiled legal worlds do not match enumerated constraints")
        if {row[requested_target] for row in legal_assignments} != set(candidates):
            raise ValueError("legal worlds omit target candidates")

        catalog_actions = self._catalog_actions(catalog)
        gamma_catalog = gamma.get("action_catalog")
        if not isinstance(gamma_catalog, Mapping):
            raise ValueError("Gamma action_catalog reference missing")
        gamma_action_ids = self._strings(
            gamma_catalog.get("actions"), require_nonempty=True
        )
        if (
            gamma_catalog.get("version") != catalog.get("catalog_version")
            or set(catalog_actions) != set(gamma_action_ids)
        ):
            raise ValueError("Gamma/catalog action set mismatch")

        formal_action_ids: list[str] = []
        observable_ids: list[str] = []
        excluded: dict[str, str] = {}
        for action_id, action in catalog_actions.items():
            observation = action.get("observation_model")
            eligibility = action.get("formal_analysis_eligibility")
            if observation is None or eligibility == "heuristic_only":
                excluded[action_id] = (
                    "NO_OBSERVATION_MODEL"
                    if observation is None
                    else "HEURISTIC_ONLY"
                )
                continue
            if not isinstance(observation, Mapping):
                raise ValueError("observation_model must be an object")
            dependencies = self._strings(
                observation.get("world_dependencies"), require_nonempty=True
            )
            state_effect = action.get("state_effect")
            if not isinstance(state_effect, Mapping):
                raise ValueError("state_effect missing")
            elimination = self._strings(
                state_effect.get("world_elimination_rule_ids"),
                require_nonempty=False,
            )
            if not elimination:
                excluded[action_id] = "NO_WORLD_ELIMINATION_RULE"
                continue
            if (
                eligibility != "formal"
                or observation.get("noise_model") != "deterministic"
                or len(dependencies) != 1
            ):
                raise ValueError("formal action contract is incomplete")
            formal_action_ids.append(action_id)
            observable_ids.append(self._identifier(observation.get("observable_id")))

        requested = (
            tuple(formal_action_ids)
            if requested_actions is None
            else self._strings(requested_actions, require_nonempty=False)
        )
        if not set(requested).issubset(formal_action_ids):
            return self._failed(
                CeilingStatus.OUTSIDE_FROZEN_DOMAIN,
                "CEILING-001_ACTION_OUTSIDE_FORMAL_DOMAIN",
            )

        legal_world_documents = compiled_legal_world_documents(compiled)
        report: dict[str, object] = {
            "schema_version": "0.8.0",
            "ceiling_id": (
                f"{gamma.get('gamma_id')}:{requested_target}:formal-ceiling-v0.8"
            ),
            "status": "VERIFIED",
            "reason_code": "CEILING-000_EXHAUSTIVE_FINITE_DOMAIN_VERIFIED",
            "gamma_hash": gamma["hash"],
            "catalog_hash": catalog["hash"],
            "compilation_profile": compiled.compilation_profile,
            "target_level": requested_target,
            "result_candidates": list(candidates),
            "variable_domains": variable_domains,
            "cartesian_assignment_bound": assignment_bound,
            "legal_world_count": len(legal_assignments),
            "legal_worlds_hash": compiled_legal_worlds_hash(compiled),
            "formal_action_ids": formal_action_ids,
            "deterministic_observable_ids": list(dict.fromkeys(observable_ids)),
            "excluded_action_reasons": excluded,
            "guarantees": [
                "all declared finite assignments enumerated",
                "all declared result candidates represented by legal worlds",
                "formal actions have deterministic observation models and elimination rules",
                "resource exhaustion and timeout are not UNSAT",
            ],
            "limitations": [
                "model-relative to the exact Gamma hash",
                "does not cover unmodeled real-world hypotheses or future algorithms",
                "does not establish external validity or action-effect correctness",
                "does not itself authorize CERTIFIED_STOP",
            ],
        }
        report["hash"] = canonical_document_hash(report)
        return FormalCeilingAssessment(
            status=CeilingStatus.VERIFIED,
            reason_code=report["reason_code"],
            report_json=canonical_json(report),
            _factory_token=_FACTORY_TOKEN,
        )

    @staticmethod
    def _catalog_actions(
        catalog: Mapping[str, object],
    ) -> dict[str, Mapping[str, object]]:
        raw = catalog.get("actions")
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise ValueError("catalog actions must be a sequence")
        actions: dict[str, Mapping[str, object]] = {}
        for item in raw:
            if not isinstance(item, Mapping):
                raise ValueError("catalog action must be an object")
            action_id = FormalCeilingVerifier._identifier(item.get("action_id"))
            if action_id in actions:
                raise ValueError("duplicate action ID")
            actions[action_id] = item
        return actions

    @staticmethod
    def _identifier(value: object) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError("identifier must be non-empty")
        return value

    @classmethod
    def _strings(
        cls, value: object, *, require_nonempty: bool
    ) -> tuple[str, ...]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            raise ValueError("value must be a string sequence")
        items = tuple(value)
        if require_nonempty and not items:
            raise ValueError("string sequence must not be empty")
        if (
            any(not isinstance(item, str) or not item for item in items)
            or len(set(items)) != len(items)
        ):
            raise ValueError("string sequence must be unique and non-empty")
        return items

    @staticmethod
    def _failed(
        status: CeilingStatus, reason_code: str
    ) -> FormalCeilingAssessment:
        return FormalCeilingAssessment(
            status=status,
            reason_code=reason_code,
            report_json=None,
            _factory_token=_FACTORY_TOKEN,
        )
