#!/usr/bin/env python3
"""Validate the real-only canonical action ontology v0.3 and source aliases."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_SCHEMA = EXP / "data_schema" / "action_ontology_profile.schema.json"
BUILDER_PATH = Path(__file__).with_name("build_action_ontology_v03.py")


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("project05_action_ontology_v03_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load builder: {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_reference(value: Any) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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
) -> dict[str, Any]:
    profile = load_json(profile_path)
    validator = Draft202012Validator(
        load_json(schema_path), format_checker=FormatChecker()
    )
    schema_errors = [
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(profile), key=lambda item: list(item.path))
    ]
    integrity_errors: list[str] = []
    cohort_meta = profile.get("case_cohort", {})
    cohort_path = resolve_reference(cohort_meta.get("path", ""))
    if not cohort_path.is_file():
        integrity_errors.append(f"case cohort unavailable: {cohort_path}")
        cohort = {}
    else:
        cohort = load_json(cohort_path)
        if file_sha256(cohort_path) != cohort_meta.get("sha256"):
            integrity_errors.append("case cohort sha256 mismatch")
    expected: dict[tuple[str, str], dict[str, Any]] = {}
    expected_sources: dict[tuple[str, str], tuple[str, str, Path]] = {}
    for mapping in cohort.get("cases", []):
        canonical_case_id = str(mapping["canonical_case_id"])
        source_case_id = str(mapping["source_case_id"])
        source_action_path = resolve_reference(mapping["source_case_path"]) / "acquisition_actions.json"
        for source_action in load_json(source_action_path):
            if source_action.get("action_type") == "stop" or source_action.get("action_id") == "STOP":
                continue
            source_action_id = str(source_action["action_id"])
            canonical_action_id = BUILDER.canonical_action_id(
                canonical_case_id, source_action_id
            )
            key = (canonical_case_id, canonical_action_id)
            expected[key] = source_action
            expected_sources[key] = (
                source_case_id,
                source_action_id,
                source_action_path,
            )
    seen: set[tuple[str, str]] = set()
    for entry in profile.get("actions", []):
        key = (str(entry.get("case_id", "")), str(entry.get("action_id", "")))
        if key in seen:
            integrity_errors.append(f"duplicate canonical action: {'/'.join(key)}")
        seen.add(key)
        source = expected.get(key)
        if source is None:
            continue
        source_case_id, source_action_id, source_action_path = expected_sources[key]
        if entry.get("source_case_id") != source_case_id:
            integrity_errors.append(f"source_case_id mismatch: {'/'.join(key)}")
        if entry.get("source_action_id") != source_action_id:
            integrity_errors.append(f"source_action_id mismatch: {'/'.join(key)}")
        if resolve_reference(entry.get("source_action_ref")) != source_action_path:
            integrity_errors.append(f"source_action_ref mismatch: {'/'.join(key)}")
        if entry.get("source_action_sha256") != canonical_sha256(source):
            integrity_errors.append(f"source action hash mismatch: {'/'.join(key)}")
        if entry.get("target") != source.get("target"):
            integrity_errors.append(f"target replay mismatch: {'/'.join(key)}")
        if "cost" in entry or "cost_breakdown" in entry:
            integrity_errors.append(f"legacy cost leaked into ontology: {'/'.join(key)}")
    missing = sorted(set(expected) - seen)
    extra = sorted(seen - set(expected))
    if missing or extra:
        integrity_errors.append(f"canonical coverage mismatch: missing={missing}, extra={extra}")
    if profile.get("scope", {}).get("case_ids") != [f"C{number:02d}" for number in range(1, 10)]:
        integrity_errors.append("scope.case_ids must be exactly canonical C01-C09")
    if profile.get("scope", {}).get("action_count") != len(expected):
        integrity_errors.append("scope.action_count does not equal real-only source coverage")
    if any(entry.get("source_case_id", "").startswith(("C01-", "C02-", "C03-")) for entry in profile.get("actions", [])):
        integrity_errors.append("toy source case leaked into real-only ontology")
    unresolved = unresolved_mapping_paths(profile)
    readiness_errors: list[str] = []
    if profile.get("status") == "frozen" and unresolved:
        readiness_errors.append(
            f"frozen profile contains {len(unresolved)} unresolved operational mappings"
        )
    formal_ready = (
        not schema_errors
        and not integrity_errors
        and not readiness_errors
        and profile.get("status") == "frozen"
        and not unresolved
    )
    return {
        "profile_path": str(profile_path.resolve()),
        "schema_valid": not schema_errors,
        "source_alias_integrity_valid": not integrity_errors,
        "canonical_case_count": len(profile.get("scope", {}).get("case_ids", [])),
        "action_count": len(profile.get("actions", [])),
        "action_type_count": len({row.get("action_type") for row in profile.get("actions", [])}),
        "toy_action_count": sum(
            row.get("source_case_id", "").startswith(("C01-", "C02-", "C03-"))
            for row in profile.get("actions", [])
        ),
        "unresolved_mapping_count": len(unresolved),
        "formal_ready": formal_ready,
        "errors": schema_errors + integrity_errors + readiness_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    report = validate_profile(args.profile, args.schema)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if not report["errors"] else 1)


if __name__ == "__main__":
    main()
