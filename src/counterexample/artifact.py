"""Deterministic P3 assembly of a schema-shaped counterexample artifact.

The assembler combines an existing P1 ``CheckerRun``, its P2
``MinDiffResult``, and explicitly frozen case/Gamma metadata. It performs no
world search, predicate projection, action selection or execution, authority
promotion, and it emits neither a system state nor a STOP decision.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from src.checker.finite_domain import CheckerRun, CheckerStatus, QueryStatus

from .mindiff import MinDiffResult


_SCHEMA_VERSION = "0.8.0"
_GENERATION_BASIS = "kernel_checker"
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def _require_nonempty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _freeze_predicates(
    values: Sequence[str],
    field_name: str,
    *,
    nonempty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a predicate sequence")
    frozen = tuple(values)
    if nonempty and not frozen:
        raise ValueError(f"{field_name} must not be empty")
    if any(not isinstance(value, str) or not value for value in frozen):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(set(frozen)) != len(frozen):
        raise ValueError(f"{field_name} must not contain duplicates")
    return frozen


@dataclass(frozen=True)
class CounterexampleArtifactMetadata:
    """Frozen case/Gamma fields that P1 and P2 do not own or infer."""

    counterexample_id: str
    case_id: str
    gamma_hash: str
    evidence_hash: str
    target_level: str
    result_entity_type: str
    support_world_id: str
    alternative_world_id: str
    support_world_predicates: Sequence[str]
    alternative_world_predicates: Sequence[str]
    shared_predicates: Sequence[str]
    critical_absence_semantics: Sequence[str]

    def __post_init__(self) -> None:
        for field_name in (
            "counterexample_id",
            "case_id",
            "target_level",
            "result_entity_type",
            "support_world_id",
            "alternative_world_id",
        ):
            _require_nonempty_string(getattr(self, field_name), field_name)

        for field_name in ("gamma_hash", "evidence_hash"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
                raise ValueError(
                    f"{field_name} must be a canonical sha256:<64 lowercase hex>"
                )

        if self.support_world_id == self.alternative_world_id:
            raise ValueError("support and alternative world IDs must differ")

        for field_name, nonempty in (
            ("support_world_predicates", True),
            ("alternative_world_predicates", True),
            ("shared_predicates", False),
            ("critical_absence_semantics", False),
        ):
            object.__setattr__(
                self,
                field_name,
                _freeze_predicates(
                    getattr(self, field_name), field_name, nonempty=nonempty
                ),
            )


class CounterexampleArtifactAssembler:
    """Assemble one P1/P2 result pair without assigning system authority."""

    def assemble(
        self,
        checker_run: CheckerRun,
        mindiff: MinDiffResult,
        metadata: CounterexampleArtifactMetadata,
    ) -> dict[str, object]:
        support, alternative = self._validate_sources(
            checker_run, mindiff, metadata.target_level
        )
        support_result = self._target_entity(
            support[metadata.target_level], metadata.result_entity_type, "support"
        )
        alternative_result = self._target_entity(
            alternative[metadata.target_level],
            metadata.result_entity_type,
            "alternative",
        )

        disagreement = dict(mindiff.mindiff_disagreement)
        expected_disagreement = {
            "support_world": support_result["entity_id"],
            "alternative_world": alternative_result["entity_id"],
        }
        if disagreement != expected_disagreement:
            raise ValueError("MinDiff disagreement does not match Checker witnesses")

        distinguishing = _freeze_predicates(
            mindiff.distinguishing_predicates,
            "distinguishing_predicates",
            nonempty=True,
        )
        shared = set(metadata.shared_predicates)
        support_only = tuple(
            predicate
            for predicate in metadata.support_world_predicates
            if predicate not in shared
        )
        alternative_only = tuple(
            predicate
            for predicate in metadata.alternative_world_predicates
            if predicate not in shared
        )
        if set(support_only).intersection(alternative_only):
            raise ValueError(
                "a predicate present in both worlds must be declared shared"
            )

        return {
            "schema_version": _SCHEMA_VERSION,
            "counterexample_id": metadata.counterexample_id,
            "case_id": metadata.case_id,
            "gamma_hash": metadata.gamma_hash,
            "evidence_hash": metadata.evidence_hash,
            "target_level": metadata.target_level,
            "candidate_q": dict(support_result),
            "checker_status": checker_run.checker_status.value,
            "core_query_results": {
                "base": checker_run.base.status.value,
                "support": checker_run.support.status.value,
                "alternative": checker_run.alternative.status.value,
            },
            "support_world": {
                "world_id": metadata.support_world_id,
                "target_result": dict(support_result),
                "predicates": list(metadata.support_world_predicates),
            },
            "alternative_world": {
                "world_id": metadata.alternative_world_id,
                "target_result": dict(alternative_result),
                "predicates": list(metadata.alternative_world_predicates),
            },
            "shared_predicates": list(metadata.shared_predicates),
            "support_only_predicates": list(support_only),
            "alternative_only_predicates": list(alternative_only),
            "distinguishing_predicates": list(distinguishing),
            "critical_absence_semantics": list(
                metadata.critical_absence_semantics
            ),
            "minimization_status": mindiff.minimization_status.value,
            "generation_basis": _GENERATION_BASIS,
        }

    @staticmethod
    def _validate_sources(
        checker_run: CheckerRun,
        mindiff: MinDiffResult,
        target_level: str,
    ) -> tuple[dict[str, object], dict[str, object]]:
        if checker_run.checker_status is not CheckerStatus.COUNTEREXAMPLE_FOUND:
            raise ValueError("artifact assembly requires COUNTEREXAMPLE_FOUND")
        if mindiff.checker_status is not checker_run.checker_status:
            raise ValueError("MinDiff checker status does not match Checker run")
        if any(
            result.status is not QueryStatus.SAT
            for result in (
                checker_run.base,
                checker_run.support,
                checker_run.alternative,
            )
        ):
            raise ValueError("counterexample artifact requires three SAT queries")
        if (
            checker_run.support.witness is None
            or checker_run.alternative.witness is None
        ):
            raise ValueError("counterexample artifact requires materialized witnesses")

        support = dict(checker_run.support.witness)
        alternative = dict(checker_run.alternative.witness)
        if target_level not in support or target_level not in alternative:
            raise ValueError(f"target level {target_level!r} is absent from witnesses")
        if support[target_level] == alternative[target_level]:
            raise ValueError("counterexample witnesses must disagree on the target")
        return support, alternative

    @staticmethod
    def _target_entity(
        value: object,
        entity_type: str,
        world_role: str,
    ) -> dict[str, str]:
        if not isinstance(value, str) or not value:
            raise ValueError(
                f"{world_role} target result must be a non-empty entity ID"
            )
        return {"entity_id": value, "entity_type": entity_type}
