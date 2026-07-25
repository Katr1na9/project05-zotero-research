#!/usr/bin/env python3
"""Build the seeded real-only C01-C09 coverage schedule for cost telemetry v0.3."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_ONTOLOGY = (
    EXP
    / "governance"
    / "profiles"
    / "action-ontology-v0.3-real-only-draft.json"
)
DEFAULT_REGISTRY = (
    EXP
    / "governance"
    / "measurement_v0.3"
    / "action-executor-registry-v0.1-draft.json"
)
DEFAULT_OUTPUT_DIR = EXP / "governance" / "measurement_v0.3"
SCHEDULE_ID = "project05-operational-cost-minimum-coverage-schedule-v0.3"
PROTOCOL_ID = "project05-operational-cost-measurement-protocol-v0.3"
SCHEDULE_FILENAME = "minimum-coverage-schedule-v0.3.csv"
PROTOCOL_FILENAME = "operational-cost-measurement-protocol-v0.3.json"
MANIFEST_FILENAME = "schedule-build-manifest-v0.3.json"
SCHEDULE_FIELDS = [
    "schedule_id",
    "scheduled_run_index",
    "phase_run_index",
    "phase",
    "attempt_round",
    "block_id",
    "block_position",
    "case_id",
    "action_id",
    "action_type",
    "planned_planner_decision_id",
    "planned_execution_attempt_id",
    "assignment_status",
    "machine_id",
    "cache_state",
    "executor_id",
    "execution_date",
    "environment_id",
    "initial_state_id",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def portable_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def derived_seed(seed: int, phase: str, attempt_round: int) -> int:
    digest = hashlib.sha256(f"{seed}:{phase}:{attempt_round}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def build_schedule(
    ontology: dict[str, Any],
    seed: int = 20260718,
    minimum_attempt_rounds: int = 3,
) -> list[dict[str, Any]]:
    if ontology.get("counting_semantics", {}).get("status") != "frozen_v0.1":
        raise ValueError("Action counting semantics must be frozen_v0.1")
    if ontology.get("data_boundary", {}).get("C13_plus") != "sealed":
        raise ValueError("C13+ must remain sealed")
    if ontology.get("scope", {}).get("case_ids") != [
        f"C{number:02d}" for number in range(1, 10)
    ]:
        raise ValueError("The v0.3 schedule requires canonical real-only C01-C09")
    if minimum_attempt_rounds < 3:
        raise ValueError("Minimum coverage schedule requires at least 3 attempt rounds")
    grouped = {
        phase: sorted(
            [row for row in ontology.get("actions", []) if row.get("phase") == phase],
            key=lambda row: (row["case_id"], row["action_id"]),
        )
        for phase in ("calibration", "development")
    }
    if not grouped["calibration"] or not grouped["development"]:
        raise ValueError("Both calibration and development action strata are required")
    rows: list[dict[str, Any]] = []
    phase_indices = {"calibration": 0, "development": 0}
    for phase in ("calibration", "development"):
        for attempt_round in range(1, minimum_attempt_rounds + 1):
            block = list(grouped[phase])
            random.Random(derived_seed(seed, phase, attempt_round)).shuffle(block)
            block_id = f"{phase}-round-{attempt_round:02d}"
            for block_position, action in enumerate(block, start=1):
                phase_indices[phase] += 1
                global_index = len(rows) + 1
                action_token = f"{action['case_id']}--{action['action_id']}--r{attempt_round:02d}"
                rows.append(
                    {
                        "schedule_id": SCHEDULE_ID,
                        "scheduled_run_index": global_index,
                        "phase_run_index": phase_indices[phase],
                        "phase": phase,
                        "attempt_round": attempt_round,
                        "block_id": block_id,
                        "block_position": block_position,
                        "case_id": action["case_id"],
                        "action_id": action["action_id"],
                        "action_type": action["action_type"],
                        "planned_planner_decision_id": f"decision--{action_token}",
                        "planned_execution_attempt_id": f"attempt--{action_token}",
                        "assignment_status": "unassigned",
                        "machine_id": "",
                        "cache_state": "",
                        "executor_id": "",
                        "execution_date": "",
                        "environment_id": "",
                        "initial_state_id": "",
                    }
                )
    return rows


def build_protocol(
    ontology_path: Path,
    registry_path: Path,
    schedule_path: Path,
    schedule_rows: list[dict[str, Any]],
    seed: int,
    minimum_attempt_rounds: int,
) -> dict[str, Any]:
    registry = load_json(registry_path)
    adapters = registry.get("adapters", [])
    adapters_ready = (
        registry.get("status") == "frozen"
        and bool(adapters)
        and all(
            row.get("status") == "implemented"
            and row.get("operational_cost_measurement_eligible") is True
            for row in adapters
        )
    )
    return {
        "protocol_id": PROTOCOL_ID,
        "version": "0.3.0",
        "status": "draft_pending_runtime_block_assignments_and_statistical_sufficiency",
        "execution_readiness": (
            "authorized_action_adapters_frozen"
            if adapters_ready
            else "blocked_no_real_action_executor"
        ),
        "schedule_authorization": (
            "execution_authorized"
            if adapters_ready
            else "template_only_do_not_execute_until_action_adapters_are_frozen"
        ),
        "action_executor_registry": {
            "path": portable_path(registry_path),
            "sha256": file_sha256(registry_path),
        },
        "ontology_profile": {
            "path": portable_path(ontology_path),
            "sha256": file_sha256(ontology_path),
        },
        "experimental_unit": "independent_execution_attempt_from_declared_initial_state",
        "counting_semantics": {
            "planner_decision_count": "unique accepted planner_decision_id including STOP",
            "execution_attempt_count": "unique execution_attempt_id including failures cancellations and retries",
            "primitive_operation_count": "sum of instrumented primitive_operation_count; never inferred from planner actions",
        },
        "coverage_gate": {
            "purpose": "coverage_and_smoke_only",
            "minimum_completed_primary_attempts_per_action": minimum_attempt_rounds,
            "formal_statistical_claim_authorized": False,
        },
        "statistical_sufficiency": {
            "status": "not_established_by_coverage_gate",
            "required_separate_analysis": True,
        },
        "randomization": {
            "method": "seeded_blocked_permutation",
            "seed": seed,
            "within_block_order": "randomized",
        },
        "blocking": {
            "design_blocks": ["phase", "attempt_round"],
            "recorded_nuisance_factors": [
                "case_id",
                "machine_id",
                "cache_state",
                "executor_id",
                "execution_date",
                "environment_id",
            ],
        },
        "failure_policy": "retain_and_include_all_attempts_in_failure_and_resource_distributions",
        "retry_policy": "each_retry_is_a_new_linked_execution_attempt_not_an_independent_coverage_replicate",
        "shared_overhead_policy": "track_unallocated",
        "scalar_cost_status": "undefined_until_transformation_model_is_separately_calibrated_and_frozen",
        "schedule": {
            "schedule_id": SCHEDULE_ID,
            "path": portable_path(schedule_path),
            "sha256": file_sha256(schedule_path),
            "scheduled_primary_attempt_count": len(schedule_rows),
        },
        "data_boundary": {
            "canonical_C01_C03": "calibration",
            "canonical_C04_C09": "development_repeat_validation",
            "canonical_C10_plus": "unassigned_and_sealed",
            "source_C13_plus": "sealed",
        },
    }


def write_schedule(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEDULE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_outputs(
    ontology_path: Path,
    output_dir: Path,
    seed: int,
    minimum_attempt_rounds: int,
    overwrite: bool = False,
    registry_path: Path = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    outputs = [
        output_dir / SCHEDULE_FILENAME,
        output_dir / PROTOCOL_FILENAME,
        output_dir / MANIFEST_FILENAME,
    ]
    if not overwrite and any(path.exists() for path in outputs):
        raise FileExistsError(f"Refusing to overwrite existing v0.3 schedule outputs: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    ontology = load_json(ontology_path)
    if not registry_path.is_file():
        raise FileNotFoundError(
            f"Action executor registry must be built before the schedule: {registry_path}"
        )
    rows = build_schedule(ontology, seed, minimum_attempt_rounds)
    schedule_path = output_dir / SCHEDULE_FILENAME
    write_schedule(schedule_path, rows)
    protocol = build_protocol(
        ontology_path,
        registry_path,
        schedule_path,
        rows,
        seed,
        minimum_attempt_rounds,
    )
    protocol_path = output_dir / PROTOCOL_FILENAME
    protocol_path.write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    manifest = {
        "builder": "09-experiments/scripts/build_operational_cost_schedule_v03.py",
        "seed": seed,
        "minimum_attempt_rounds": minimum_attempt_rounds,
        "case_count": len(ontology["scope"]["case_ids"]),
        "unique_action_count": len(ontology["actions"]),
        "scheduled_primary_attempt_count": len(rows),
        "calibration_scheduled_attempt_count": sum(row["phase"] == "calibration" for row in rows),
        "development_scheduled_attempt_count": sum(row["phase"] == "development" for row in rows),
        "inputs": {
            portable_path(ontology_path): file_sha256(ontology_path),
            portable_path(registry_path): file_sha256(registry_path),
        },
        "outputs": {
            schedule_path.name: file_sha256(schedule_path),
            protocol_path.name: file_sha256(protocol_path),
        },
    }
    manifest_path = output_dir / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=20260718)
    parser.add_argument("--minimum-attempt-rounds", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    manifest = build_outputs(
        args.ontology,
        args.output_dir,
        args.seed,
        args.minimum_attempt_rounds,
        args.overwrite,
        args.registry,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
