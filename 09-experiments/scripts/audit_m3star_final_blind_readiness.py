#!/usr/bin/env python3
"""Static, non-consuming readiness audit for the sealed M3* final blind run."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_runner() -> Any:
    path = Path(__file__).with_name("run_m3star_final_blind.py")
    spec = importlib.util.spec_from_file_location("run_m3star_final_blind", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def audit_readiness(
    protocol_path: Path,
    frozen_model_result_dir: Path,
    training_cost_profile_path: Path,
    cases_root: Path,
    dataset_manifest_path: Path,
    evaluation_cost_profile_path: Path,
    consumption_ledger: Path,
) -> dict[str, Any]:
    blockers: list[str] = []
    static_error: str | None = None
    try:
        runner.static_protocol_checks(
            protocol_path,
            frozen_model_result_dir,
            training_cost_profile_path,
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        static_error = f"{type(exc).__name__}: {exc}"
        blockers.append("Frozen implementation/protocol static checks failed.")

    cases_root_present = cases_root.is_dir()
    dataset_manifest_present = dataset_manifest_path.is_file()
    evaluation_cost_profile_present = evaluation_cost_profile_path.is_file()
    ledger_absent = not consumption_ledger.exists()
    if not cases_root_present:
        blockers.append(
            "No C13+ final-blind cases directory is present at the frozen input location; "
            "the current observable recruitment count is 0 of 96."
        )
    if not dataset_manifest_present:
        blockers.append("No frozen C13+ dataset manifest is present.")
    if not evaluation_cost_profile_present:
        blockers.append(
            "No distinct frozen measured-cost profile for the C13+ cohort is present."
        )
    if not ledger_absent:
        blockers.append("The one-shot final-blind consumption ledger already exists.")

    external_inputs_present = all(
        (
            cases_root_present,
            dataset_manifest_present,
            evaluation_cost_profile_present,
        )
    )
    static_gate_pass = static_error is None and ledger_absent
    return {
        "audit_id": "project05-m3star-final-blind-readiness-audit-v0.1",
        "status": (
            "external_inputs_present_preflight_required"
            if static_gate_pass and external_inputs_present
            else "blocked_before_preflight"
        ),
        "checked_utc": utc_now(),
        "protocol_path": str(protocol_path),
        "protocol_sha256": runner.sha256(protocol_path),
        "implementation_and_protocol_static_gate_pass": static_error is None,
        "implementation_static_error": static_error,
        "consumption_ledger_absent": ledger_absent,
        "cases_root_present": cases_root_present,
        "observable_recruitment_count": 0 if not cases_root_present else None,
        "operational_recruitment_target": runner.OPERATIONAL_RECRUITMENT_TARGET,
        "dataset_manifest_present": dataset_manifest_present,
        "evaluation_cost_profile_present": evaluation_cost_profile_present,
        "external_inputs_present": external_inputs_present,
        "ready_for_non_consuming_preflight": static_gate_pass and external_inputs_present,
        "ready_for_one_shot_execution": False,
        "why_execution_is_false": (
            "The full hash, C13+ boundary, 96-case, exact cost-coverage, and seal checks "
            "must pass the non-consuming preflight before one-shot authorization."
        ),
        "c13_plus_case_contents_opened": False,
        "ground_truth_opened": False,
        "consumption_ledger_created": False,
        "blockers": blockers,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--frozen-model-result-dir", type=Path, required=True)
    parser.add_argument("--training-cost-profile", type=Path, required=True)
    parser.add_argument("--cases-root", type=Path, required=True)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--evaluation-cost-profile", type=Path, required=True)
    parser.add_argument("--consumption-ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit_readiness(
        args.protocol,
        args.frozen_model_result_dir,
        args.training_cost_profile,
        args.cases_root,
        args.dataset_manifest,
        args.evaluation_cost_profile,
        args.consumption_ledger,
    )
    write_json(args.output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
