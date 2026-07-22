"""Load auditable Twin inputs without hand-written worlds or predicates."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

import yaml

from src.counterexample.mindiff import PredicateProjectionContract
from src.ir.observation_claim import (
    ObservationClaimActionBinding,
    ObservationClaimAdapterContext,
)
from src.scope.finite_problem import (
    CompiledFiniteProblem,
    EvidenceGammaFiniteProblemCompiler,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-COUNTEREXAMPLE-001"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class TwinKernelInputs:
    gamma: Mapping[str, object]
    catalog: Mapping[str, object]
    expected: Mapping[str, object]
    frozen_counterexample: Mapping[str, object]
    case_evidence: tuple[Mapping[str, object], ...]
    compiled: CompiledFiniteProblem
    predicate_projections: PredicateProjectionContract
    observation_rows: tuple[Mapping[str, object], ...]
    resource_rows: tuple[Mapping[str, object], ...]


def load_twin_kernel_inputs() -> TwinKernelInputs:
    gamma = load_yaml(ROOT / "configs" / "gamma-kernel-v0.8.yaml")
    catalog = load_yaml(ROOT / "configs" / "action-catalog-kernel-v0.8.yaml")
    expected = load_yaml(FIXTURE / "expected" / "outcome.yaml")
    frozen_counterexample = load_json(FIXTURE / "expected" / "counterexample.json")
    case_evidence = tuple(load_jsonl(FIXTURE / "claims" / "case_evidence.jsonl"))
    compiled = EvidenceGammaFiniteProblemCompiler().compile(
        gamma,
        case_evidence,
        target_variable=expected["target_level"],
    )
    projection_document = load_yaml(FIXTURE / "predicate_projections.yaml")
    predicate_projections = PredicateProjectionContract.from_action_catalog(
        projection_document,
        catalog,
        witness_variables=compiled.problem.domains,
    )
    return TwinKernelInputs(
        gamma=gamma,
        catalog=catalog,
        expected=expected,
        frozen_counterexample=frozen_counterexample,
        case_evidence=case_evidence,
        compiled=compiled,
        predicate_projections=predicate_projections,
        observation_rows=tuple(
            load_jsonl(FIXTURE / "expected" / "action_observations.jsonl")
        ),
        resource_rows=tuple(
            load_jsonl(FIXTURE / "expected" / "resource_trace.jsonl")
        ),
    )


def twin_observation_adapter_context() -> ObservationClaimAdapterContext:
    """Return explicit non-oracle Claim bindings for all four Twin P5 rows."""

    identity = ObservationClaimActionBinding(
        predicate="action_observation",
        source_family="identity",
        source_schema="kernel.action-observation.v0.8",
        admissible_levels=("initial_foothold",),
    )
    cti = ObservationClaimActionBinding(
        predicate="action_observation",
        source_family="external_intel",
        source_schema="kernel.action-observation.v0.8",
        admissible_levels=("initial_foothold",),
    )
    return ObservationClaimAdapterContext(
        source_id="action_observations.jsonl",
        row_numbers={
            "OBS-001": 1,
            "OBS-002": 2,
            "OBS-003": 3,
            "OBS-004": 4,
        },
        action_bindings={
            "query_logon_origin_H3": identity,
            "query_auth_H1_1000_1015": identity,
            "query_auth_empty_control": identity,
            "analyst_cti_lookup": cti,
        },
        certification_basis_rule_id="A-P5-OBSERVATION",
        certification_policy_hash=(
            "sha256:0eb3cbb8be3cf51dc9952a447e4d1f90"
            "fc89b5dc2c5e2f0edafca32c6805399a"
        ),
        parser_id="p5-observation-adapter",
        parser_version="0.8.0",
        prompt_or_rule_hash=(
            "sha256:3b4bb0ed6f9221c5e71bedc50ce50871"
            "0f693c0e28d84f77af7571ac85f94d3e"
        ),
    )


def twin_observation_admission_config(*, admit_observation_ids=()):
    """Return deterministic P11 admit metadata without certificate authority."""

    from src.cli.kernel_e2e import AdmissionAuditMetadata, ObservationAdmissionConfig

    event_rows = {
        "OBS-001": AdmissionAuditMetadata(
            event_id="TWIN-P11-ADMIT-001",
            rule_id="P7-FW-ADMISSION",
            timestamp="2026-01-01T10:16:00Z",
        ),
        "OBS-002": AdmissionAuditMetadata(
            event_id="TWIN-P11-ADMIT-002",
            rule_id="P7-FW-ADMISSION",
            timestamp="2026-01-01T10:16:01Z",
        ),
        "OBS-003": AdmissionAuditMetadata(
            event_id="TWIN-P11-ADMIT-003",
            rule_id="P7-FW-ADMISSION",
            timestamp="2026-01-01T10:16:02Z",
        ),
        "OBS-004": AdmissionAuditMetadata(
            event_id="TWIN-P11-ADMIT-004",
            rule_id="P7-FW-ADMISSION",
            timestamp="2026-01-01T10:16:03Z",
        ),
    }
    requested = tuple(admit_observation_ids)
    return ObservationAdmissionConfig(
        adapter_context=twin_observation_adapter_context(),
        admit_observation_ids=requested,
        audit_metadata={
            observation_id: event_rows[observation_id]
            for observation_id in requested
        },
        lifecycle_policy_hash=(
            "sha256:0eb3cbb8be3cf51dc9952a447e4d1f90"
            "fc89b5dc2c5e2f0edafca32c6805399a"
        ),
    )
