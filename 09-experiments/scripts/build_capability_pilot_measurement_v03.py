#!/usr/bin/env python3
"""Translate a real adapter capability pilot into an explicitly non-formal v0.3 record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def returned_evidence_count(observation: dict[str, Any]) -> int:
    """Select the adapter-specific returned-observation cardinality."""

    if (
        observation.get("schema_id")
        == "project05-cdm18-observed-remote-endpoint-summary-v0.1"
    ):
        value = observation.get("observed_remote_endpoint_count")
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("network summary endpoint count must be a non-negative integer")
        return value
    return int(observation.get("subgraph_event_count", 0)) + int(
        observation.get("subgraph_node_count", 0)
    )


def select_schedule_row(
    rows: list[dict[str, str]],
    scheduled_run_index: int,
    case_id: str,
    action_id: str,
) -> dict[str, str]:
    for row in rows:
        if int(row["scheduled_run_index"]) == scheduled_run_index:
            if row.get("case_id") != case_id or row.get("action_id") != action_id:
                raise ValueError("selected schedule row does not match pilot case/action")
            return row
    raise ValueError(f"scheduled_run_index is absent from schedule: {scheduled_run_index}")


def build_measurement_record(
    pilot_result: dict[str, Any],
    schedule_rows: list[dict[str, str]],
    *,
    scheduled_run_index: int,
    machine_id: str,
    environment_id: str,
    initial_state_id: str,
    host_count: int = 1,
    cache_state: str = "unknown",
) -> dict[str, Any]:
    """Build a schema-shaped record that is permanently excluded from formal coverage.

    The record references a matching schedule row solely so the existing v0.3
    validator can check its action identity.  Its declared randomization deviation
    and missing initial-state reset prevent it from contributing to coverage.
    """

    invocation = pilot_result.get("invocation")
    if not isinstance(invocation, dict):
        raise ValueError("pilot result has no invocation")
    case_id = invocation.get("case_id")
    action_id = invocation.get("action_id")
    if not isinstance(case_id, str) or not isinstance(action_id, str):
        raise ValueError("pilot invocation case_id/action_id must be strings")
    row = select_schedule_row(schedule_rows, scheduled_run_index, case_id, action_id)
    resource_trace = pilot_result.get("resource_trace")
    observation = pilot_result.get("observation")
    if not isinstance(resource_trace, dict) or not isinstance(observation, dict):
        raise ValueError("pilot result lacks resource_trace or observation")
    for field in (
        "started_utc",
        "ended_utc",
        "execution_status",
        "termination_reason",
        "primitive_operation_count",
    ):
        if field not in pilot_result:
            raise ValueError(f"pilot result lacks {field}")
    if host_count < 0:
        raise ValueError("host_count must be non-negative")
    if cache_state not in {"cold", "warm", "controlled", "unknown"}:
        raise ValueError("cache_state is invalid")

    attempt_token = f"{case_id}--{action_id}--schedule-{scheduled_run_index:03d}"
    return {
        "measurement_id": f"capability-pilot--{attempt_token}",
        "case_id": case_id,
        "action_id": action_id,
        "phase": row["phase"],
        "planner_decision_id": f"capability-pilot-decision--{attempt_token}",
        "execution_attempt_id": f"capability-pilot-attempt--{attempt_token}",
        "retry_of_attempt_id": None,
        "attempt_round": int(row["attempt_round"]),
        "scheduled_run_index": scheduled_run_index,
        "block_id": row["block_id"],
        "randomization_deviation": {
            "deviation_type": "unscheduled_capability_pilot",
            "reason": "Executed before the action-executor registry and controlled initial-state protocol were frozen; excluded from formal schedule compliance, coverage, and scalar-cost claims.",
            "adjudication_status": "accepted",
        },
        "started_utc": pilot_result["started_utc"],
        "ended_utc": pilot_result["ended_utc"],
        "execution_status": pilot_result["execution_status"],
        "termination_reason": pilot_result["termination_reason"],
        "primitive_operation_count": pilot_result["primitive_operation_count"],
        "resource_trace": copy_json(resource_trace),
        "context_covariates": {
            "host_count": host_count,
            "retention_window_days": None,
            "authorization": {
                "required": False,
                "boundary": "none",
                "approval_reference": None,
            },
            "machine_id": machine_id,
            "cache_state": cache_state,
            "executor_id": pilot_result.get(
                "adapter_id", "project05-query-host-subgraph-file-pilot-v0.1"
            ),
            "execution_date": str(pilot_result["started_utc"])[:10],
            "environment_id": environment_id,
            "initial_state_id": initial_state_id,
            "initial_state_reset": False,
        },
        "hard_constraints": {
            "authorization_satisfied": True,
            "data_available": True,
            "safety_gate_passed": True,
            "violations": [],
        },
        "observation_summary": {
            "returned_evidence_count": returned_evidence_count(observation),
            "evidence_perturbations": copy_json(
                observation.get("evidence_perturbations", [])
            ),
            "downtime_seconds": observation.get("downtime_seconds"),
        },
    }


def write_measurement_source(path: Path, record: dict[str, Any]) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite capability pilot record: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([record], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def load_schedule_rows(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-run", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--scheduled-run-index", type=int, required=True)
    parser.add_argument("--machine-id", required=True)
    parser.add_argument("--environment-id", required=True)
    parser.add_argument("--initial-state-id", required=True)
    parser.add_argument("--host-count", type=int, default=1)
    parser.add_argument("--cache-state", choices=["cold", "warm", "controlled", "unknown"], default="unknown")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = build_measurement_record(
        load_json(args.pilot_run),
        load_schedule_rows(args.schedule),
        scheduled_run_index=args.scheduled_run_index,
        machine_id=args.machine_id,
        environment_id=args.environment_id,
        initial_state_id=args.initial_state_id,
        host_count=args.host_count,
        cache_state=args.cache_state,
    )
    write_measurement_source(args.output, record)
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "measurement_id": record["measurement_id"],
                "formal_coverage_eligible": False,
                "randomization_deviation": record["randomization_deviation"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
