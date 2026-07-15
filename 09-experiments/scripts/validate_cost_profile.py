#!/usr/bin/env python3
"""Validate Project05 cost-profile structure, coverage, and formal readiness."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "09-experiments"
DEFAULT_SCHEMA = EXPERIMENT_ROOT / "data_schema" / "cost_profile.schema.json"
DEFAULT_EXAMPLES_DIR = EXPERIMENT_ROOT / "examples"
DEFAULT_REAL_CASES_DIR = EXPERIMENT_ROOT / "real_cases"
MVP_PATH = Path(__file__).with_name("run_mvp.py")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_mvp() -> Any:
    spec = importlib.util.spec_from_file_location("project05_cost_profile_mvp", MVP_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load simulator from {MVP_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_cases(examples_dir: Path, real_cases_dir: Path) -> dict[str, Path]:
    required = ("case_config.json", "acquisition_actions.json")
    indexed: dict[str, Path] = {}
    for root in (examples_dir, real_cases_dir):
        if not root.is_dir():
            raise FileNotFoundError(f"Case root does not exist: {root}")
        for case_dir in root.iterdir():
            if not case_dir.is_dir() or not all(
                (case_dir / name).is_file() for name in required
            ):
                continue
            case_id = load_json(case_dir / "case_config.json")["case_id"]
            if case_id in indexed:
                raise ValueError(f"Duplicate case_id in repository: {case_id}")
            indexed[case_id] = case_dir
    return indexed


def schema_errors(profile: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(profile), key=lambda item: list(item.path))
    ]


def validate_coverage(
    profile: dict[str, Any],
    case_dirs: dict[str, Path],
) -> list[str]:
    errors: list[str] = []
    scope_case_ids = profile.get("scope", {}).get("case_ids", [])
    entries = profile.get("actions", [])
    indexed: dict[str, set[str]] = {}
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = (entry.get("case_id"), entry.get("action_id"))
        if not all(isinstance(value, str) for value in key):
            continue
        if key in seen:
            errors.append(f"duplicate profile action: {key[0]}/{key[1]}")
        seen.add(key)
        indexed.setdefault(key[0], set()).add(key[1])

    undeclared = sorted(set(indexed) - set(scope_case_ids))
    if undeclared:
        errors.append(f"profile actions occur outside declared scope: {undeclared}")
    for case_id in scope_case_ids:
        case_dir = case_dirs.get(case_id)
        if case_dir is None:
            errors.append(f"declared case is absent from repository: {case_id}")
            continue
        actions = load_json(case_dir / "acquisition_actions.json")
        expected = {action["action_id"] for action in actions}
        actual = indexed.get(case_id, set())
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            errors.append(
                f"coverage mismatch for {case_id}: missing={missing}, extra={extra}"
            )
    return errors


def readiness_report(
    profile_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    examples_dir: Path = DEFAULT_EXAMPLES_DIR,
    real_cases_dir: Path = DEFAULT_REAL_CASES_DIR,
    require_frozen: bool = False,
) -> dict[str, Any]:
    profile = load_json(profile_path)
    schema = load_json(schema_path)
    structural_errors = schema_errors(profile, schema)
    case_dirs = discover_cases(examples_dir, real_cases_dir)
    coverage_errors = validate_coverage(profile, case_dirs)
    status = profile.get("status")
    regime = profile.get("regime")
    actions = profile.get("actions") if isinstance(profile.get("actions"), list) else []
    pending_components = (
        sum(
            1
            for entry in actions
            for component in (entry.get("components") or {}).values()
            if component is None
        )
        if regime == "rubric"
        else 0
    )
    pending_measured = (
        sum(entry.get("measured_cost") is None for entry in actions)
        if regime == "measured"
        else 0
    )
    formal_errors: list[str] = []
    if require_frozen and status != "frozen":
        formal_errors.append("profile status is not frozen")
    if not structural_errors and not coverage_errors and status == "frozen":
        mvp = load_mvp()
        bundle = mvp.load_cost_profile(profile_path)
        for case_id in profile["scope"]["case_ids"]:
            case_dir = case_dirs[case_id]
            case_actions = mvp.load_json(case_dir / "acquisition_actions.json")
            try:
                mvp.apply_cost_regime(case_actions, case_id, regime, bundle)
            except ValueError as exc:
                formal_errors.append(f"{case_id}: {exc}")

    formal_ready = not structural_errors and not coverage_errors and not formal_errors and status == "frozen"
    return {
        "profile_path": str(profile_path.resolve()),
        "profile_id": profile.get("profile_id"),
        "version": profile.get("version"),
        "status": status,
        "regime": regime,
        "schema_valid": not structural_errors,
        "coverage_valid": not coverage_errors,
        "formal_ready": formal_ready,
        "case_count": len(profile.get("scope", {}).get("case_ids", [])),
        "action_count": len(actions),
        "pending_component_values": pending_components,
        "pending_measured_costs": pending_measured,
        "errors": structural_errors + coverage_errors + formal_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a Project05 acquisition-cost profile."
    )
    parser.add_argument("profile", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--examples-dir", type=Path, default=DEFAULT_EXAMPLES_DIR)
    parser.add_argument("--real-cases-dir", type=Path, default=DEFAULT_REAL_CASES_DIR)
    parser.add_argument(
        "--require-frozen",
        action="store_true",
        help="Fail unless the profile is complete, frozen, and executable.",
    )
    args = parser.parse_args()
    report = readiness_report(
        args.profile,
        args.schema,
        args.examples_dir,
        args.real_cases_dir,
        args.require_frozen,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
