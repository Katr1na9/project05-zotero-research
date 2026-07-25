#!/usr/bin/env python3
"""Build the v0.3 cost/action governance contract from hashed local artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
ONTOLOGY = (
    EXP
    / "governance"
    / "profiles"
    / "action-ontology-v0.3-real-only-draft.json"
)
REGISTRY = EXP / "governance" / "measurement_v0.3" / "action-executor-registry-v0.1-draft.json"
PROTOCOL = EXP / "governance" / "measurement_v0.3" / "operational-cost-measurement-protocol-v0.3.json"
SCHEDULE = EXP / "governance" / "measurement_v0.3" / "minimum-coverage-schedule-v0.3.csv"
MEASUREMENT_SCHEMA = EXP / "data_schema" / "operational_cost_measurement_batch_v0.3.schema.json"
ONTOLOGY_SCHEMA = EXP / "data_schema" / "action_ontology_profile.schema.json"
REGISTRY_SCHEMA = EXP / "data_schema" / "action_executor_registry.schema.json"
CONSTRUCT_SYNTHESIS = ROOT / "04-progress" / "cost-action-construct-review-v0.1-20260718" / "construct-synthesis.md"
DEFAULT_OUTPUT = EXP / "governance" / "contracts" / "cost-pipeline-contract-v0.3.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def artifact(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise FileNotFoundError(f"Governance artifact is missing: {path}")
    return {"path": relative_path(path), "sha256": file_sha256(path)}


def build_contract() -> dict[str, Any]:
    ontology = load_json(ONTOLOGY)
    registry = load_json(REGISTRY)
    protocol = load_json(PROTOCOL)
    with SCHEDULE.open("r", encoding="utf-8", newline="") as handle:
        schedule_rows = list(csv.DictReader(handle))
    adapters = registry.get("adapters", [])
    implemented = [row for row in adapters if row.get("status") == "implemented"]
    eligible = [
        row for row in adapters if row.get("operational_cost_measurement_eligible") is True
    ]
    execution_authorized = (
        protocol.get("execution_readiness") == "authorized_action_adapters_frozen"
        and protocol.get("schedule_authorization") == "execution_authorized"
    )
    return {
        "contract_id": "project05-cost-pipeline-contract-v0.3",
        "version": "0.3.0",
        "status": "draft_blocked_no_real_action_executor",
        "authority": {
            "new_cost_measurement_design": "v0.3_normative",
            "legacy_replay": "v0.2_and_case_embedded_costs_compatibility_only",
            "paper_or_patent_writing": "closed_until_full_experimental_validation",
        },
        "evidence_basis": artifact(CONSTRUCT_SYNTHESIS),
        "canonical_pipeline": {
            "action_ontology_schema": artifact(ONTOLOGY_SCHEMA),
            "action_ontology_profile": artifact(ONTOLOGY),
            "action_executor_registry_schema": artifact(REGISTRY_SCHEMA),
            "action_executor_registry": artifact(REGISTRY),
            "measurement_schema": artifact(MEASUREMENT_SCHEMA),
            "measurement_protocol": artifact(PROTOCOL),
            "minimum_coverage_schedule": artifact(SCHEDULE),
            "measurement_importer": artifact(
                EXP / "scripts" / "import_operational_cost_measurements_v03.py"
            ),
            "measurement_validator": artifact(
                EXP / "scripts" / "validate_operational_cost_measurements_v03.py"
            ),
        },
        "construct_semantics": {
            "acquisition_burden": "unit_bearing_raw_resource_vector",
            "utility_or_evidence_value": "separate_outcome_construct",
            "volatility_or_delay_loss": "separate_time_dependent_loss_construct",
            "operational_risk_or_impact": "separate_event_and_downtime_construct",
            "hard_constraints": "separate_feasibility_gate",
            "scalar_cost": "undefined_until_transformation_model_is_calibrated_validated_and_frozen",
        },
        "counting_semantics": {
            "status": ontology["counting_semantics"]["status"],
            "planner_decision_count": "distinct_from_execution_and_primitive_counts",
            "execution_attempt_count": "includes_failures_cancellations_and_each_retry",
            "primitive_operation_count": "instrumented_only_never_implicit_one",
            "split_merge_invariance": "required_before_formal_cost_claims",
        },
        "experimental_design": {
            "case_boundary": {
                "canonical_C01_C03": "calibration",
                "canonical_C04_C09": "development_repeat_validation",
                "canonical_C10_plus": "unassigned_and_sealed",
                "source_C13_plus": "sealed",
            },
            "experimental_unit": protocol["experimental_unit"],
            "randomization": protocol["randomization"],
            "blocking": protocol["blocking"],
            "scheduled_primary_attempt_count": len(schedule_rows),
            "coverage_gate": protocol["coverage_gate"],
            "statistical_sufficiency": protocol["statistical_sufficiency"],
        },
        "legacy_compatibility": {
            "case_embedded_scalar_cost": "legacy_exploratory_replay_only",
            "EDAR_or_EVDA_R_rubric": "suspended_not_construct_validity_evidence",
            "two_rater_360_component_packet": "suspended_not_required_by_v0.3",
            "minimum_three_completed_attempts": "coverage_and_smoke_only_not_statistical_sufficiency",
            "v0.2_files_deleted_or_rewritten": False,
        },
        "readiness": {
            "construct_review_complete": True,
            "action_count": ontology["scope"]["action_count"],
            "counting_semantics_frozen": ontology["counting_semantics"]["status"] == "frozen_v0.1",
            "operational_action_mappings_resolved": False,
            "adapter_count": len(adapters),
            "implemented_adapter_count": len(implemented),
            "eligible_adapter_count": len(eligible),
            "execution_authorized": execution_authorized,
            "real_measurement_records_available": False,
            "coverage_gate_passed": False,
            "statistical_sufficiency_established": False,
            "scalar_transformation_model_frozen": False,
            "formal_measured_cost_profile_ready": False,
            "paper_or_patent_gate_open": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    contract = build_contract()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(contract["readiness"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
