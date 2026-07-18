#!/usr/bin/env python3
"""Build the real-only canonical C01-C09 action ontology v0.3 sidecar."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
BASE_BUILDER_PATH = Path(__file__).with_name("build_action_ontology_draft.py")
DEFAULT_COHORT = EXP / "governance" / "cohorts" / "real-case-cohort-v0.3.json"
DEFAULT_OUTPUT = EXP / "governance" / "profiles" / "action-ontology-v0.3-real-only-draft.json"


def load_base_builder() -> Any:
    spec = importlib.util.spec_from_file_location("project05_action_ontology_base", BASE_BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load ontology base builder: {BASE_BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base_builder()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_reference(value: Any) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def canonical_action_id(canonical_case_id: str, source_action_id: str) -> str:
    match = re.match(r"^C[0-9]{2}-AA-(.+)$", source_action_id)
    if not match:
        raise ValueError(f"Cannot canonicalize source action ID: {source_action_id}")
    return f"{canonical_case_id}-AA-{match.group(1)}"


def frozen_counting_semantics() -> dict[str, Any]:
    return {
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
    }


def build_profile(
    cohort_path: Path = DEFAULT_COHORT,
    created_utc: str = "2026-07-18T00:00:00Z",
) -> dict[str, Any]:
    cohort = load_json(cohort_path)
    if cohort.get("status") != "frozen":
        raise ValueError("The real-only case cohort must be frozen")
    actions: list[dict[str, Any]] = []
    for mapping in cohort.get("cases", []):
        canonical_case_id = str(mapping["canonical_case_id"])
        source_case_id = str(mapping["source_case_id"])
        source_case_dir = resolve_reference(mapping["source_case_path"])
        action_path = source_case_dir / "acquisition_actions.json"
        for source_action in load_json(action_path):
            if source_action.get("action_type") == "stop" or source_action.get("action_id") == "STOP":
                continue
            entry = BASE.build_action_entry(source_case_id, source_action)
            source_action_id = str(source_action["action_id"])
            entry.update(
                {
                    "case_id": canonical_case_id,
                    "action_id": canonical_action_id(canonical_case_id, source_action_id),
                    "source_case_id": source_case_id,
                    "source_action_id": source_action_id,
                    "source_action_ref": relative_path(action_path),
                    "phase": mapping["phase"],
                }
            )
            actions.append(entry)
    actions.sort(key=lambda row: (row["case_id"], row["action_id"]))
    case_ids = [row["canonical_case_id"] for row in cohort["cases"]]
    return {
        "profile_id": "project05-action-ontology-v0.3-real-only-draft",
        "version": "0.3.0-draft",
        "status": "draft",
        "created_utc": created_utc,
        "evidence_basis": {
            "construct_synthesis_ref": relative_path(BASE.CONSTRUCT_SYNTHESIS),
            "construct_synthesis_sha256": file_sha256(BASE.CONSTRUCT_SYNTHESIS),
        },
        "case_cohort": {
            "path": relative_path(cohort_path),
            "sha256": file_sha256(cohort_path),
        },
        "runtime_audit": {
            "current_executor_type": "outcome_reveal_simulator",
            "source_ref": "09-experiments/scripts/run_mvp.py::run_episode/recoverable_hidden/channel_is_up",
            "source_sha256": file_sha256(BASE.SIMULATOR_RUNTIME),
            "execution_mechanism": "seeded_channel_availability_then_recoverable_hidden_claim_set_reveal",
            "external_collector_invoked": False,
            "operational_cost_measurement_eligible": False,
            "blocking_reason": "The real-only cohort has replay artifacts, but action-specific adapters remain incomplete and the planner runtime still reveals hidden claims in simulation.",
        },
        "data_boundary": {
            "calibration_cases": case_ids[:3],
            "development_cases": case_ids[3:],
            "C13_plus": "sealed",
            "canonical_C10_plus": "unassigned_and_sealed",
        },
        "scope": {
            "case_ids": case_ids,
            "action_count": len(actions),
            "legacy_case_files_mutated": False,
        },
        "counting_semantics": frozen_counting_semantics(),
        "actions": actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--created-utc", default="2026-07-18T00:00:00Z")
    args = parser.parse_args()
    profile = build_profile(args.cohort, args.created_utc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "case_count": len(profile["scope"]["case_ids"]),
                "action_count": profile["scope"]["action_count"],
                "action_type_count": len({row["action_type"] for row in profile["actions"]}),
                "toy_cases_included": False,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
