"""Load the structurally distinct supply-chain Kernel fixture."""

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
    DeclarativeFiniteWorldCompiler,
)
from tests.unit.policy_test_helpers import approved_policy_authority


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-SUPPLY-CHAIN-002"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class SupplyChainKernelInputs:
    gamma: Mapping[str, object]
    catalog: Mapping[str, object]
    expected: Mapping[str, object]
    expected_counterexample: Mapping[str, object]
    case_evidence: tuple[Mapping[str, object], ...]
    compiled: CompiledFiniteProblem
    predicate_projections: PredicateProjectionContract
    observation_rows: tuple[Mapping[str, object], ...]
    resource_rows: tuple[Mapping[str, object], ...]


def load_supply_chain_kernel_inputs() -> SupplyChainKernelInputs:
    gamma = load_yaml(ROOT / "configs" / "gamma-supply-chain-kernel-v0.8.yaml")
    catalog = load_yaml(
        ROOT / "configs" / "action-catalog-supply-chain-kernel-v0.8.yaml"
    )
    expected = load_yaml(FIXTURE / "expected" / "outcome.yaml")
    expected_counterexample = load_json(
        FIXTURE / "expected" / "counterexample.json"
    )
    evidence = load_jsonl(FIXTURE / "claims" / "case_evidence.jsonl")
    compiled = DeclarativeFiniteWorldCompiler().compile(
        gamma,
        evidence,
        target_variable=expected["target_level"],
    )
    projection = PredicateProjectionContract.from_action_catalog(
        load_yaml(FIXTURE / "predicate_projections.yaml"),
        catalog,
        witness_variables=compiled.problem.domains,
    )
    return SupplyChainKernelInputs(
        gamma=gamma,
        catalog=catalog,
        expected=expected,
        expected_counterexample=expected_counterexample,
        case_evidence=evidence,
        compiled=compiled,
        predicate_projections=projection,
        observation_rows=load_jsonl(
            FIXTURE / "expected" / "action_observations.jsonl"
        ),
        resource_rows=load_jsonl(
            FIXTURE / "expected" / "resource_trace.jsonl"
        ),
    )


def supply_chain_adapter_context() -> ObservationClaimAdapterContext:
    supply = ObservationClaimActionBinding(
        predicate="action_observation",
        source_family="software_supply_chain",
        source_schema="kernel.supply-chain-observation.v0.8",
        admissible_levels=("package_origin",),
        certification_basis_rule_id="A003",
    )
    provenance = ObservationClaimActionBinding(
        predicate="action_observation",
        source_family="system_provenance",
        source_schema="kernel.supply-chain-observation.v0.8",
        admissible_levels=("package_origin",),
        certification_basis_rule_id="A004",
    )
    return ObservationClaimAdapterContext(
        source_id="action_observations.jsonl",
        row_numbers={
            "SC-OBS-001": 1,
            "SC-OBS-002": 2,
            "SC-OBS-003": 3,
        },
        action_bindings={
            "query_registry_attestation_PKG-X": supply,
            "query_mirror_publish_chain_PKG-X": supply,
            "verify_artifact_signature_PKG-X": provenance,
        },
        certification_policy_hash=(
            "sha256:8f34a5e99c2cba3d79304667acd5bb01"
            "0492af74b8b99425352375a796825671"
        ),
        parser_id="supply-chain-observation-adapter",
        parser_version="0.8.0",
        prompt_or_rule_hash=(
            "sha256:9956cf1c64b0c8506a7f931818a12a33"
            "81ab552df67d3c38ff595d500f9f7e6e"
        ),
        claim_id_prefix="SC-P11",
    )


def supply_chain_admission_config():
    from src.cli.kernel_e2e import AdmissionAuditMetadata, ObservationAdmissionConfig

    inputs = load_supply_chain_kernel_inputs()
    authority = approved_policy_authority(inputs.gamma["admission_policy"])
    return ObservationAdmissionConfig(
        adapter_context=supply_chain_adapter_context(),
        admission_policy_authority=authority,
        admit_observation_ids=("SC-OBS-001", "SC-OBS-002", "SC-OBS-003"),
        audit_metadata={
            "SC-OBS-001": AdmissionAuditMetadata(
                "SC-ADMIT-001", "A003", "2026-02-01T09:01:00Z"
            ),
            "SC-OBS-002": AdmissionAuditMetadata(
                "SC-ADMIT-002", "A003", "2026-02-01T09:01:01Z"
            ),
            "SC-OBS-003": AdmissionAuditMetadata(
                "SC-ADMIT-003", "A004", "2026-02-01T09:01:02Z"
            ),
        },
        lifecycle_policy_hash=authority.policy_hash,
    )
