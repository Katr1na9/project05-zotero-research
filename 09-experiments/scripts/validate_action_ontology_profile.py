#!/usr/bin/env python3
"""Validate action-ontology schema, source replay, coverage, and freeze readiness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_SCHEMA = EXP / "data_schema" / "action_ontology_profile.schema.json"
DEFAULT_EXAMPLES_DIR = EXP / "examples"
DEFAULT_REAL_CASES_DIR = EXP / "real_cases"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def schema_errors(profile: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(profile), key=lambda item: list(item.path))
    ]


def discover_actions(
    examples_dir: Path, real_cases_dir: Path
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, str]]:
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    phases: dict[str, str] = {}
    for root in (examples_dir, real_cases_dir):
        if not root.is_dir():
            raise FileNotFoundError(f"Case root does not exist: {root}")
        for case_dir in root.iterdir():
            if not case_dir.is_dir() or not (case_dir / "case_config.json").is_file() or not (case_dir / "acquisition_actions.json").is_file():
                continue
            config = load_json(case_dir / "case_config.json")
            case_id = str(config["case_id"])
            prefix = case_id[:3]
            if not (len(prefix) == 3 and prefix[0] == "C" and prefix[1:].isdigit()):
                continue
            case_number = int(prefix[1:])
            if not 1 <= case_number <= 12:
                continue
            phases[case_id] = "calibration" if case_number <= 6 else "development"
            for action in load_json(case_dir / "acquisition_actions.json"):
                if action.get("action_type") == "stop" or action.get("action_id") == "STOP":
                    continue
                key = (case_id, str(action["action_id"]))
                if key in indexed:
                    raise ValueError(f"Duplicate source case/action: {'/'.join(key)}")
                indexed[key] = action
    return indexed, phases


def unresolved_mapping_paths(profile: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for entry in profile.get("actions", []):
        prefix = f"{entry.get('case_id')}/{entry.get('action_id')}"
        for section in (
            "actor_and_authority",
            "preconditions",
            "invocation",
            "termination",
            "observation",
            "state_effects",
        ):
            if entry.get(section, {}).get("mapping_status") != "resolved":
                paths.append(f"{prefix}/{section}")
        for field, status in entry.get("execution_mapping", {}).items():
            if status != "resolved":
                paths.append(f"{prefix}/execution_mapping/{field}")
    return paths


def validate_profile(
    profile_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    examples_dir: Path = DEFAULT_EXAMPLES_DIR,
    real_cases_dir: Path = DEFAULT_REAL_CASES_DIR,
) -> dict[str, Any]:
    profile = load_json(profile_path)
    structural_errors = schema_errors(profile, load_json(schema_path))
    source_actions, source_phases = discover_actions(examples_dir, real_cases_dir)
    coverage_errors: list[str] = []
    integrity_errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    global_action_ids: set[str] = set()
    for entry in profile.get("actions", []):
        key = (str(entry.get("case_id", "")), str(entry.get("action_id", "")))
        if key in seen:
            coverage_errors.append(f"duplicate profile case/action: {'/'.join(key)}")
        seen.add(key)
        action_id = key[1]
        if action_id in global_action_ids:
            coverage_errors.append(f"action_id is not globally unique: {action_id}")
        global_action_ids.add(action_id)
        source = source_actions.get(key)
        if source is None:
            continue
        if entry.get("source_action_sha256") != canonical_sha256(source):
            integrity_errors.append(f"source action hash mismatch: {'/'.join(key)}")
        if entry.get("phase") != source_phases[key[0]]:
            integrity_errors.append(f"phase mismatch: {'/'.join(key)}")
        if entry.get("target") != source.get("target"):
            integrity_errors.append(f"target does not replay source: {'/'.join(key)}")
        if "cost" in entry or "cost_breakdown" in entry:
            integrity_errors.append(f"legacy cost leaked into ontology sidecar: {'/'.join(key)}")
    missing = sorted(set(source_actions) - seen)
    extra = sorted(seen - set(source_actions))
    if missing or extra:
        coverage_errors.append(f"coverage mismatch: missing={missing}, extra={extra}")
    if profile.get("scope", {}).get("action_count") != len(profile.get("actions", [])):
        coverage_errors.append("scope.action_count does not equal the profile action array")
    expected_case_ids = sorted(source_phases)
    if sorted(profile.get("scope", {}).get("case_ids", [])) != expected_case_ids:
        coverage_errors.append("scope.case_ids does not exactly cover C01-C12")

    evidence_basis = profile.get("evidence_basis", {})
    evidence_ref = evidence_basis.get("construct_synthesis_ref")
    if isinstance(evidence_ref, str):
        evidence_path = (ROOT / evidence_ref).resolve()
        if not evidence_path.is_file():
            integrity_errors.append(f"construct synthesis is unavailable: {evidence_ref}")
        elif hashlib.sha256(evidence_path.read_bytes()).hexdigest() != evidence_basis.get("construct_synthesis_sha256"):
            integrity_errors.append("construct synthesis hash mismatch")
    runtime_audit = profile.get("runtime_audit", {})
    runtime_ref = runtime_audit.get("source_ref")
    if isinstance(runtime_ref, str):
        runtime_path_text = runtime_ref.split("::", 1)[0]
        runtime_path = (ROOT / runtime_path_text).resolve()
        if not runtime_path.is_file():
            integrity_errors.append(f"simulator runtime is unavailable: {runtime_path_text}")
        elif hashlib.sha256(runtime_path.read_bytes()).hexdigest() != runtime_audit.get("source_sha256"):
            integrity_errors.append("simulator runtime hash mismatch")

    unresolved = unresolved_mapping_paths(profile)
    readiness_errors: list[str] = []
    if profile.get("status") == "frozen" and unresolved:
        readiness_errors.append(
            f"frozen profile contains {len(unresolved)} unresolved operational mappings"
        )
    formal_ready = (
        not structural_errors
        and not coverage_errors
        and not integrity_errors
        and not readiness_errors
        and profile.get("status") == "frozen"
        and not unresolved
    )
    return {
        "profile_path": str(profile_path.resolve()),
        "profile_id": profile.get("profile_id"),
        "status": profile.get("status"),
        "schema_valid": not structural_errors,
        "coverage_valid": not coverage_errors,
        "source_integrity_valid": not integrity_errors,
        "counting_semantics_status": profile.get("counting_semantics", {}).get("status"),
        "operational_cost_measurement_eligible": profile.get("runtime_audit", {}).get("operational_cost_measurement_eligible"),
        "case_count": len(profile.get("scope", {}).get("case_ids", [])),
        "action_count": len(profile.get("actions", [])),
        "unresolved_mapping_count": len(unresolved),
        "unresolved_mappings": unresolved,
        "formal_ready": formal_ready,
        "errors": structural_errors + coverage_errors + integrity_errors + readiness_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--examples-dir", type=Path, default=DEFAULT_EXAMPLES_DIR)
    parser.add_argument("--real-cases-dir", type=Path, default=DEFAULT_REAL_CASES_DIR)
    args = parser.parse_args()
    report = validate_profile(
        args.profile, args.schema, args.examples_dir, args.real_cases_dir
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if not report["errors"] else 1)


if __name__ == "__main__":
    main()
