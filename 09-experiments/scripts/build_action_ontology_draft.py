#!/usr/bin/env python3
"""Build the C01-C12 acquisition-action ontology sidecar without editing cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_EXAMPLES_DIR = EXP / "examples"
DEFAULT_REAL_CASES_DIR = EXP / "real_cases"
DEFAULT_OUTPUT = EXP / "governance" / "profiles" / "action-ontology-v0.1-draft.json"
CONSTRUCT_SYNTHESIS = (
    ROOT
    / "04-progress"
    / "cost-action-construct-review-v0.1-20260718"
    / "construct-synthesis.md"
)
SIMULATOR_RUNTIME = EXP / "scripts" / "run_mvp.py"
ACTION_TYPE_CHANNELS = {
    "extend_log_window": "log_retention",
    "query_host_subgraph": "host_forensics",
    "recover_network_summary": "network_telemetry",
    "ioc_enrichment": "threat_intel",
    "infrastructure_history": "threat_intel",
    "cti_report_lookup": "threat_intel",
    "malware_analysis": "sample_lab",
    "ttp_local_probe": "host_probe",
    "human_review": "analyst",
    "stop": "decision",
    "other": "other",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def validate_created_utc(value: str) -> str:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("--created-utc must include a timezone")
    return value


def case_number_from_dir(path: Path) -> int | None:
    match = re.match(r"^C([0-9]{2})(?:-|$)", path.name)
    return int(match.group(1)) if match else None


def discover_case_dirs(examples_dir: Path, real_cases_dir: Path) -> list[Path]:
    required = ("case_config.json", "acquisition_actions.json")
    indexed: list[tuple[str, Path]] = []
    for root in (examples_dir, real_cases_dir):
        if not root.is_dir():
            raise FileNotFoundError(f"Case root does not exist: {root}")
        for path in root.iterdir():
            number = case_number_from_dir(path)
            if (
                not path.is_dir()
                or number is None
                or not 1 <= number <= 12
                or not all((path / name).is_file() for name in required)
            ):
                continue
            case_id = str(load_json(path / "case_config.json")["case_id"])
            indexed.append((case_id, path))
    case_ids = [case_id for case_id, _ in indexed]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Duplicate case_id in C01-C12 action-ontology scope")
    return [path for _, path in sorted(indexed)]


def action_channel(action: dict[str, Any]) -> str:
    explicit = action.get("acquisition_channel")
    if explicit:
        return str(explicit)
    return ACTION_TYPE_CHANNELS.get(str(action.get("action_type", "other")), "other")


def phase_for_case(case_id: str) -> str:
    match = re.match(r"^C([0-9]{2})", case_id)
    if not match:
        raise ValueError(f"Cannot derive phase from case_id: {case_id}")
    case_number = int(match.group(1))
    if 1 <= case_number <= 6:
        return "calibration"
    if 7 <= case_number <= 12:
        return "development"
    raise ValueError(f"Case outside the C01-C12 boundary: {case_id}")


def build_action_entry(case_id: str, action: dict[str, Any]) -> dict[str, Any]:
    expected_effects = action.get("expected_effects") or {}
    return {
        "case_id": case_id,
        "action_id": str(action["action_id"]),
        "action_type": str(action["action_type"]),
        "phase": phase_for_case(case_id),
        "source_action_sha256": canonical_sha256(action),
        "abstraction_level": "planner_evidence_acquisition_decision",
        "actor_and_authority": {
            "actor_role": None,
            "authority_boundary": None,
            "mapping_status": "unresolved",
        },
        "target": action["target"],
        "preconditions": {
            "source_declared": action.get("preconditions", []),
            "mapping_status": (
                "resolved" if "preconditions" in action else "unresolved"
            ),
        },
        "invocation": {
            "acquisition_channel": action_channel(action),
            "natural_language_request": action.get("natural_language_request"),
            "machine_interface": None,
            "mapping_status": "unresolved",
        },
        "termination": {
            "success_criterion": None,
            "timeout_policy": None,
            "mapping_status": "unresolved",
        },
        "observation": {
            "declared_evidence_types": action.get("expected_evidence_types", []),
            "observation_schema_ref": None,
            "mapping_status": "unresolved",
        },
        "state_effects": {
            "declared_expected_effect_fields": sorted(expected_effects),
            "realized_effect_source": "executor_observation_not_planner_prior",
            "mapping_status": "unresolved",
        },
        "execution_mapping": {
            "attempt_unit": "unresolved",
            "primitive_operation_boundary": "unresolved",
            "retry_policy": "unresolved",
            "shared_overhead_policy": "unresolved",
        },
    }


def build_profile(
    examples_dir: Path,
    real_cases_dir: Path,
    created_utc: str,
) -> dict[str, Any]:
    created_utc = validate_created_utc(created_utc)
    if not CONSTRUCT_SYNTHESIS.is_file():
        raise FileNotFoundError(f"Construct synthesis is missing: {CONSTRUCT_SYNTHESIS}")
    case_dirs = discover_case_dirs(examples_dir, real_cases_dir)
    actions: list[dict[str, Any]] = []
    case_ids: list[str] = []
    for case_dir in case_dirs:
        case_id = str(load_json(case_dir / "case_config.json")["case_id"])
        case_ids.append(case_id)
        for action in load_json(case_dir / "acquisition_actions.json"):
            if action.get("action_type") == "stop" or action.get("action_id") == "STOP":
                continue
            actions.append(build_action_entry(case_id, action))
    actions.sort(key=lambda row: (row["case_id"], row["action_id"]))
    calibration_cases = [case_id for case_id in case_ids if phase_for_case(case_id) == "calibration"]
    development_cases = [case_id for case_id in case_ids if phase_for_case(case_id) == "development"]
    return {
        "profile_id": "project05-action-ontology-v0.1-draft",
        "version": "0.1.0-draft",
        "status": "draft",
        "created_utc": created_utc,
        "evidence_basis": {
            "construct_synthesis_ref": relative_path(CONSTRUCT_SYNTHESIS),
            "construct_synthesis_sha256": file_sha256(CONSTRUCT_SYNTHESIS),
        },
        "runtime_audit": {
            "current_executor_type": "outcome_reveal_simulator",
            "source_ref": "09-experiments/scripts/run_mvp.py::run_episode/recoverable_hidden/channel_is_up",
            "source_sha256": file_sha256(SIMULATOR_RUNTIME),
            "execution_mechanism": "seeded_channel_availability_then_recoverable_hidden_claim_set_reveal",
            "external_collector_invoked": False,
            "operational_cost_measurement_eligible": False,
            "blocking_reason": "No real per-action collector or adapter currently executes the eight acquisition action types and emits unit-bearing resource telemetry.",
        },
        "data_boundary": {
            "calibration_cases": calibration_cases,
            "development_cases": development_cases,
            "C13_plus": "sealed",
        },
        "scope": {
            "case_ids": case_ids,
            "action_count": len(actions),
            "legacy_case_files_mutated": False,
        },
        "counting_semantics": {
            "status": "frozen_v0.1",
            "planner_decision_count": {
                "unit": "accepted_planner_output",
                "definition": "Count each planner output accepted at a decision boundary; a selected STOP is one planner decision.",
                "stop_counts_as_decision": True,
            },
            "execution_attempt_count": {
                "unit": "executor_dispatch_attempt",
                "definition": "Count every dispatched acquisition execution separately, including failed, cancelled, and retried attempts.",
                "failures_count": True,
                "cancellations_count": True,
                "retries_are_new_attempts": True,
                "stop_counts_as_attempt": False,
            },
            "primitive_operation_count": {
                "unit": "instrumented_low_level_operation",
                "definition": "Count operations at the collector-defined primitive boundary; never infer one primitive from one planner action.",
                "implicit_one_per_planner_action_forbidden": True,
            },
            "split_merge_invariance": {
                "status": "required_before_formal_cost_claims",
                "rule": "Equivalent work must conserve raw resource totals when a planner action is split or merged; only the declared count level may change.",
                "required_tests": [
                    "split_equivalent",
                    "merge_equivalent",
                    "retry_not_mergeable",
                    "shared_overhead_conservation",
                ],
            },
        },
        "actions": actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--examples-dir", type=Path, default=DEFAULT_EXAMPLES_DIR)
    parser.add_argument("--real-cases-dir", type=Path, default=DEFAULT_REAL_CASES_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--created-utc", default="2026-07-18T00:00:00Z")
    args = parser.parse_args()
    profile = build_profile(args.examples_dir, args.real_cases_dir, args.created_utc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "case_count": len(profile["scope"]["case_ids"]),
                "action_count": profile["scope"]["action_count"],
                "status": profile["status"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
