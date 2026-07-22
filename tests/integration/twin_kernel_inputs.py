"""Load auditable Twin inputs without hand-written worlds or predicates."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

import yaml

from src.counterexample.mindiff import PredicateProjectionContract
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
