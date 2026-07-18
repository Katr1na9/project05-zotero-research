#!/usr/bin/env python3
"""Build a draft adapter registry from the governed real-only action ontology."""

from __future__ import annotations

import argparse
import hashlib
import json
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
DEFAULT_OUTPUT = (
    EXP
    / "governance"
    / "measurement_v0.3"
    / "action-executor-registry-v0.1-draft.json"
)
UNRESOLVED_CONTRACTS = [
    "actor_and_authority",
    "initial_state_and_preconditions",
    "invocation",
    "termination",
    "observation",
    "state_effects",
    "primitive_operation_boundary",
    "retry_policy",
    "shared_overhead_policy",
    "telemetry_emitter",
]
TELEMETRY_DIMENSIONS = [
    "analyst_seconds_by_role",
    "compute_wall_seconds",
    "compute_cpu_seconds",
    "memory_byte_seconds",
    "bytes_scanned",
    "records_scanned",
    "direct_currency",
    "authorization_wait_seconds",
    "downtime_seconds",
    "evidence_perturbations",
]
CONTRACT_FIELDS = [
    "actor_role",
    "authority_boundary",
    "initial_state_reset_procedure",
    "precondition_evaluator",
    "invocation_entrypoint",
    "target_parameter_mapping",
    "completion_and_timeout_criteria",
    "observation_schema_ref",
    "state_effect_mapping",
    "primitive_operation_definition",
    "retry_policy",
    "shared_overhead_policy",
    "telemetry_emitter",
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


def build_registry(
    ontology_path: Path,
    created_utc: str = "2026-07-18T00:00:00Z",
) -> dict[str, Any]:
    ontology = load_json(ontology_path)
    action_types = sorted({row["action_type"] for row in ontology.get("actions", [])})
    if not action_types:
        raise ValueError("Ontology contains no action types")
    if ontology.get("data_boundary", {}).get("C13_plus") != "sealed":
        raise ValueError("C13+ must remain sealed")
    adapters = []
    for action_type in action_types:
        adapters.append(
            {
                "action_type": action_type,
                "adapter_id": f"project05-adapter-{action_type.replace('_', '-')}-v0.1",
                "status": "unimplemented",
                "operational_cost_measurement_eligible": False,
                "oracle_input_fields_forbidden": [
                    "recoverable_claim_ids",
                    "oracle_effects",
                    "hidden_claim_ids",
                ],
                "contract": {field: None for field in CONTRACT_FIELDS},
                "unresolved_contracts": list(UNRESOLVED_CONTRACTS),
            }
        )
    return {
        "registry_id": "project05-action-executor-registry-v0.1-draft",
        "version": "0.1.0-draft",
        "status": "draft",
        "created_utc": created_utc,
        "ontology_profile": {
            "path": portable_path(ontology_path),
            "sha256": file_sha256(ontology_path),
        },
        "data_boundary": {
            "canonical_C01_C09": "real_cases_in_scope",
            "canonical_C10_plus": "unassigned_and_sealed",
            "source_C13_plus": "sealed",
        },
        "required_telemetry_dimensions": TELEMETRY_DIMENSIONS,
        "adapters": adapters,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--created-utc", default="2026-07-18T00:00:00Z")
    args = parser.parse_args()
    registry = build_registry(args.ontology, args.created_utc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "adapter_count": len(registry["adapters"]),
                "implemented_adapter_count": 0,
                "operational_cost_measurement_eligible": False,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
