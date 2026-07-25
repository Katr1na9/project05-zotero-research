#!/usr/bin/env python3
"""Validate action-adapter coverage and operational measurement readiness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_SCHEMA = EXP / "data_schema" / "action_executor_registry.schema.json"
EXPECTED_FORBIDDEN_ORACLE_FIELDS = {
    "recoverable_claim_ids",
    "oracle_effects",
    "hidden_claim_ids",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_reference(value: Any) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def validate_registry(
    registry_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    registry = load_json(registry_path)
    validator = Draft202012Validator(
        load_json(schema_path), format_checker=FormatChecker()
    )
    schema_errors = [
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(registry), key=lambda item: list(item.path))
    ]
    semantic_errors: list[str] = []
    ontology_meta = registry.get("ontology_profile", {})
    ontology_path = resolve_reference(ontology_meta.get("path", ""))
    if not ontology_path.is_file():
        semantic_errors.append(f"ontology profile unavailable: {ontology_path}")
        ontology = {}
    else:
        ontology = load_json(ontology_path)
        if file_sha256(ontology_path) != ontology_meta.get("sha256"):
            semantic_errors.append("ontology profile sha256 mismatch")
    expected_types = {row["action_type"] for row in ontology.get("actions", [])}
    if registry.get("data_boundary") != {
        "canonical_C01_C09": "real_cases_in_scope",
        "canonical_C10_plus": "unassigned_and_sealed",
        "source_C13_plus": "sealed",
    }:
        semantic_errors.append("registry data boundary is not canonical real-only C01-C09")
    adapters = registry.get("adapters", [])
    actual_types = [str(row.get("action_type", "")) for row in adapters]
    if len(actual_types) != len(set(actual_types)):
        semantic_errors.append("duplicate action_type adapter registrations")
    if set(actual_types) != expected_types:
        semantic_errors.append(
            f"adapter action-type coverage mismatch: missing={sorted(expected_types - set(actual_types))}, extra={sorted(set(actual_types) - expected_types)}"
        )
    for adapter in adapters:
        action_type = adapter.get("action_type")
        forbidden = set(adapter.get("oracle_input_fields_forbidden", []))
        if forbidden != EXPECTED_FORBIDDEN_ORACLE_FIELDS:
            semantic_errors.append(
                f"oracle input prohibition is incomplete for {action_type}"
            )
        if adapter.get("status") == "implemented" and not adapter.get(
            "operational_cost_measurement_eligible"
        ):
            semantic_errors.append(
                f"implemented adapter is not measurement-eligible: {action_type}"
            )
    implemented = [row for row in adapters if row.get("status") == "implemented"]
    eligible = [
        row for row in adapters if row.get("operational_cost_measurement_eligible") is True
    ]
    freeze_errors: list[str] = []
    if registry.get("status") == "frozen" and len(implemented) != len(adapters):
        freeze_errors.append("frozen registry contains unimplemented adapters")
    formal_ready = (
        not schema_errors
        and not semantic_errors
        and not freeze_errors
        and registry.get("status") == "frozen"
        and len(adapters) > 0
        and len(implemented) == len(adapters)
        and len(eligible) == len(adapters)
    )
    return {
        "registry_path": str(registry_path.resolve()),
        "status": registry.get("status"),
        "schema_valid": not schema_errors,
        "ontology_integrity_valid": not any(
            "ontology profile" in error for error in semantic_errors
        ),
        "action_type_coverage_valid": not any(
            "coverage mismatch" in error or "duplicate action_type" in error
            for error in semantic_errors
        ),
        "adapter_count": len(adapters),
        "implemented_adapter_count": len(implemented),
        "eligible_adapter_count": len(eligible),
        "formal_ready": formal_ready,
        "errors": schema_errors + semantic_errors + freeze_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    report = validate_registry(args.registry, args.schema)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if not report["errors"] else 1)


if __name__ == "__main__":
    main()
