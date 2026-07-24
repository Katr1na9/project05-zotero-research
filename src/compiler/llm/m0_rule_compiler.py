"""Fail-closed structural compiler for the project05_depth2_public M0 surface.

This module deliberately stops before Claim-ID minting, admission, and Kernel
ingestion.  It only turns an allowlisted public planner projection into a
structural external Claim IR package with null claim IDs.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


SURFACE_ID = "project05_depth2_public"
PROJECTION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-m0-depth2-public-field-projection-v0.1-20260724.json"
)
PROJECTION_SHA256 = (
    "4784ff3a29f2c3cb8d04bc187b1f2cd1d95b9ead51c3ad0d7c4da30f4cd557e8"
)
SCHEMA_PATH = "schemas/claim-ir-kernel.schema.json"
SCHEMA_SHA256 = (
    "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
)
DESIGN_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m0-rule-compiler-design-v0.1-20260724.json"
)
DESIGN_SHA256 = (
    "d579f2aec21a647cd695088ee5b947439a5e682c68fb687d8be592e1561647f3"
)

_GROUPS = frozenset({"config", "state", "action"})
_CONFIG_FIELDS = frozenset(
    {"case_id", "budget_total", "cti_nodes", "channel_reliability"}
)
_CONFIG_NODE_FIELDS = frozenset({"node_id", "stage", "critical"})
_STATE_FIELDS = frozenset(
    {
        "case_id",
        "step_index",
        "matched_cti_node_ids",
        "unmatched_cti_node_ids",
        "matched_cti_edge_ids",
        "unmatched_cti_edge_ids",
        "coverage",
        "budget",
        "remaining_action_ids",
    }
)
_COVERAGE_FIELDS = frozenset(
    {
        "cti_node_coverage",
        "cti_edge_coverage",
        "critical_gap_count",
        "stage_coverage",
        "evidence_type_coverage",
    }
)
_BUDGET_FIELDS = frozenset({"budget_total", "budget_used", "budget_remaining"})
_ACTION_FIELDS = frozenset(
    {
        "action_id",
        "case_id",
        "action_type",
        "acquisition_channel",
        "target",
        "cost",
        "intended_cti_node_ids",
        "expected_evidence_types",
        "expected_stages",
        "expected_effects",
        "status",
        "natural_language_request",
    }
)
_TARGET_FIELDS = frozenset({"target_type", "target_value"})
_EXPECTED_EFFECT_FIELDS = frozenset(
    {
        "expected_granularity_gain",
        "expected_uncertainty_reduction",
        "expected_over_attribution_risk_reduction",
        "expected_conflict_resolution",
        "expected_coverage_delta",
    }
)
_FORBIDDEN_KEYS = frozenset(
    {
        "label",
        "labels",
        "class",
        "attack",
        "technique",
        "verdict",
        "recoverable_claim_ids",
        "hidden_claim_ids",
        "required_claim_ids",
        "recovered_claim_ids",
        "actual_recovered_claims",
        "oracle",
        "oracle_path",
        "mask_strategy",
        "mask_intensity",
        "mask_membership",
        "random_seed",
        "run_id",
        "realized_recovery",
        "realized_outcomes",
        "actions_taken",
        "action_feedback",
        "recovered_count",
        "private_evidence",
        "hidden_evidence",
        "credentials",
        "secrets",
    }
)
_ALLOWED_SOURCE_FIELDS = frozenset(
    {
        "config.case_id",
        "config.budget_total",
        "config.cti_nodes.node_id",
        "config.cti_nodes.stage",
        "config.cti_nodes.critical",
        "config.channel_reliability",
        "state.case_id",
        "state.step_index",
        "state.matched_cti_node_ids",
        "state.unmatched_cti_node_ids",
        "state.matched_cti_edge_ids",
        "state.unmatched_cti_edge_ids",
        "state.coverage.cti_node_coverage",
        "state.coverage.cti_edge_coverage",
        "state.coverage.critical_gap_count",
        "state.coverage.stage_coverage",
        "state.coverage.evidence_type_coverage",
        "state.budget.budget_total",
        "state.budget.budget_used",
        "state.budget.budget_remaining",
        "state.remaining_action_ids",
        "action.action_id",
        "action.case_id",
        "action.action_type",
        "action.acquisition_channel",
        "action.target.target_type",
        "action.target.target_value",
        "action.cost",
        "action.intended_cti_node_ids",
        "action.expected_evidence_types",
        "action.expected_stages",
        "action.expected_effects.expected_granularity_gain",
        "action.expected_effects.expected_uncertainty_reduction",
        "action.expected_effects.expected_over_attribution_risk_reduction",
        "action.expected_effects.expected_conflict_resolution",
        "action.expected_effects.expected_coverage_delta",
        "action.status",
        "action.natural_language_request",
    }
)


class M0CompilerError(ValueError):
    """Raised when a public projection cannot pass the M0 fail-closed gate."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def verify_pins(repo_root: Path) -> None:
    """Verify the only accepted surface and all design/runtime pins."""

    expected = (
        (PROJECTION_PATH, PROJECTION_SHA256),
        (SCHEMA_PATH, SCHEMA_SHA256),
        (DESIGN_PATH, DESIGN_SHA256),
    )
    for relative_path, expected_sha in expected:
        path = repo_root / relative_path
        if not path.is_file():
            raise M0CompilerError("pin_missing", f"pinned file missing: {relative_path}")
        actual_sha = _sha256(path)
        if actual_sha != expected_sha:
            raise M0CompilerError(
                "pin_mismatch",
                f"pinned SHA mismatch for {relative_path}",
            )

    projection = _load_json(repo_root / PROJECTION_PATH)
    if (
        not isinstance(projection, Mapping)
        or projection.get("scope", {}).get("surface_id") != SURFACE_ID
    ):
        raise M0CompilerError("surface_mismatch", "projection surface is not project05_depth2_public")

    schema = _load_json(repo_root / SCHEMA_PATH)
    schema_surface = (
        schema.get("properties", {}).get("surface_id", {}).get("const")
        if isinstance(schema, Mapping)
        else None
    )
    if schema_surface != SURFACE_ID:
        raise M0CompilerError("schema_surface_mismatch", "schema surface is not project05_depth2_public")

    design = _load_json(repo_root / DESIGN_PATH)
    if (
        not isinstance(design, Mapping)
        or design.get("surface_scope", {}).get("surface_id") != SURFACE_ID
        or design.get("status") != "design_only_implementation_not_authorized"
    ):
        raise M0CompilerError("design_mismatch", "compiler design pin is not the accepted M0 design")


def compile_public_projection(
    document: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Compile one public projection into a structural, non-admitted package."""

    verify_pins(repo_root)
    _reject_forbidden_keys(document)
    if not isinstance(document, Mapping):
        raise M0CompilerError("input_type", "projection must be an object")
    if set(document) != _GROUPS:
        raise M0CompilerError(
            "top_level_surface",
            "projection must contain exactly config, state, and action",
        )
    for group in _GROUPS:
        if not isinstance(document[group], Mapping):
            raise M0CompilerError("group_type", f"{group} must be an object")

    claims: list[dict[str, Any]] = []
    _collect_config(document["config"], claims)
    _collect_state(document["state"], claims)
    _collect_action(document["action"], claims)
    if not claims:
        raise M0CompilerError("empty_projection", "projection contains no allowlisted fields")

    canonical_claims = _canonical_json(claims)
    content_hash = hashlib.sha256(canonical_claims.encode("utf-8")).hexdigest()
    package_seed = f"{SURFACE_ID}|{PROJECTION_SHA256}".encode("utf-8")
    package_id = "pkg_" + hashlib.sha256(package_seed).hexdigest()[:32]
    field_path_set = sorted({claim["source_field"] for claim in claims})

    return {
        "schema_version": "claim-ir-external-v0.1",
        "package_id": package_id,
        "surface_id": SURFACE_ID,
        "kernel_state": "pending_kernel_schema",
        "claim_id_state": "not_minted",
        "admission_state": "not_admitted",
        "projection_ref": {
            "path": PROJECTION_PATH,
            "sha256": PROJECTION_SHA256,
            "surface_id": SURFACE_ID,
        },
        "claims": claims,
        "manifest": {
            "claim_count": len(claims),
            "field_path_set": field_path_set,
            "projection_sha256": PROJECTION_SHA256,
            "content_hash": content_hash,
        },
    }


def run_fixture_directory(
    fixture_dir: Path,
    output_dir: Path,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Run JSON fixtures and write only sanitized structural outputs/reports."""

    fixture_dir = fixture_dir.resolve()
    output_dir = output_dir.resolve()
    repo_root = repo_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for fixture_path in sorted(fixture_dir.glob("*.json")):
        fixture_id = fixture_path.stem
        try:
            document = _load_json(fixture_path)
            package = compile_public_projection(document, repo_root=repo_root)
            output_path = output_dir / f"{fixture_id}.output.json"
            output_path.write_text(
                json.dumps(package, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            results.append(
                {
                    "fixture_id": fixture_id,
                    "outcome": "accepted_structural",
                    "output_file": output_path.name,
                    "claim_count": package["manifest"]["claim_count"],
                    "claim_id_state": package["claim_id_state"],
                    "admission_state": package["admission_state"],
                    "kernel_state": package["kernel_state"],
                    "claim_ids_null": all(
                        claim["claim_id"] is None for claim in package["claims"]
                    ),
                }
            )
        except M0CompilerError as exc:
            results.append(
                {
                    "fixture_id": fixture_id,
                    "outcome": "rejected",
                    "error_code": exc.code,
                    "package_emitted": False,
                }
            )
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            results.append(
                {
                    "fixture_id": fixture_id,
                    "outcome": "rejected",
                    "error_code": "malformed_fixture",
                    "package_emitted": False,
                    "error_type": type(exc).__name__,
                }
            )

    report = {
        "surface_id": SURFACE_ID,
        "projection_sha256": PROJECTION_SHA256,
        "schema_sha256": SCHEMA_SHA256,
        "compiler_design_sha256": DESIGN_SHA256,
        "mode": "structural_only",
        "results": results,
        "claim_id_minting_performed": False,
        "kernel_write_performed": False,
        "admission_performed": False,
    }
    (output_dir / "run-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def _collect_config(value: Mapping[str, Any], claims: list[dict[str, Any]]) -> None:
    _reject_unknown(value, _CONFIG_FIELDS, "config")
    for field in ("case_id", "budget_total", "channel_reliability"):
        if field in value:
            _append_claim(claims, "config." + field, value[field], "public_config")
    if "cti_nodes" in value:
        nodes = value["cti_nodes"]
        if not isinstance(nodes, list) or len(nodes) > 4096:
            raise M0CompilerError("field_shape", "config.cti_nodes must be a bounded array")
        for node in nodes:
            if not isinstance(node, Mapping):
                raise M0CompilerError("field_shape", "config.cti_nodes entries must be objects")
            _reject_unknown(node, _CONFIG_NODE_FIELDS, "config.cti_nodes")
            for field in _CONFIG_NODE_FIELDS:
                if field in node:
                    _append_claim(
                        claims,
                        f"config.cti_nodes.{field}",
                        node[field],
                        "public_config",
                    )


def _collect_state(value: Mapping[str, Any], claims: list[dict[str, Any]]) -> None:
    _reject_unknown(value, _STATE_FIELDS, "state")
    for field in (
        "case_id",
        "step_index",
        "matched_cti_node_ids",
        "unmatched_cti_node_ids",
        "matched_cti_edge_ids",
        "unmatched_cti_edge_ids",
        "remaining_action_ids",
    ):
        if field in value:
            _append_claim(claims, "state." + field, value[field], "public_alignment_state")
    if "coverage" in value:
        coverage = value["coverage"]
        if not isinstance(coverage, Mapping):
            raise M0CompilerError("field_shape", "state.coverage must be an object")
        _reject_unknown(coverage, _COVERAGE_FIELDS, "state.coverage")
        for field in _COVERAGE_FIELDS:
            if field in coverage:
                _append_claim(
                    claims,
                    f"state.coverage.{field}",
                    coverage[field],
                    "public_alignment_state",
                )
    if "budget" in value:
        budget = value["budget"]
        if not isinstance(budget, Mapping):
            raise M0CompilerError("field_shape", "state.budget must be an object")
        _reject_unknown(budget, _BUDGET_FIELDS, "state.budget")
        for field in _BUDGET_FIELDS:
            if field in budget:
                _append_claim(
                    claims,
                    f"state.budget.{field}",
                    budget[field],
                    "public_alignment_state",
                )


def _collect_action(value: Mapping[str, Any], claims: list[dict[str, Any]]) -> None:
    _reject_unknown(value, _ACTION_FIELDS, "action")
    for field in (
        "action_id",
        "case_id",
        "action_type",
        "acquisition_channel",
        "cost",
        "intended_cti_node_ids",
        "expected_evidence_types",
        "expected_stages",
        "status",
        "natural_language_request",
    ):
        if field in value:
            _append_claim(
                claims,
                "action." + field,
                value[field],
                "public_action_declaration",
            )
    if "target" in value:
        target = value["target"]
        if not isinstance(target, Mapping):
            raise M0CompilerError("field_shape", "action.target must be an object")
        _reject_unknown(target, _TARGET_FIELDS, "action.target")
        for field in _TARGET_FIELDS:
            if field in target:
                _append_claim(
                    claims,
                    f"action.target.{field}",
                    target[field],
                    "public_action_declaration",
                )
    if "expected_effects" in value:
        effects = value["expected_effects"]
        if not isinstance(effects, Mapping):
            raise M0CompilerError("field_shape", "action.expected_effects must be an object")
        _reject_unknown(effects, _EXPECTED_EFFECT_FIELDS, "action.expected_effects")
        for field in _EXPECTED_EFFECT_FIELDS:
            if field in effects:
                _append_claim(
                    claims,
                    f"action.expected_effects.{field}",
                    effects[field],
                    "public_prospective_effect",
                )


def _append_claim(
    claims: list[dict[str, Any]],
    source_field: str,
    value: Any,
    claim_kind: str,
) -> None:
    if source_field not in _ALLOWED_SOURCE_FIELDS:
        raise M0CompilerError("field_not_allowlisted", f"field is not allowlisted: {source_field}")
    canonical_value = _validate_and_copy_value(value, source_field)
    claims.append(
        {
            "claim_id": None,
            "claim_id_state": "not_minted",
            "claim_kind": claim_kind,
            "source_field": source_field,
            "value_type": _value_type(canonical_value, source_field),
            "value": canonical_value,
            "admission_state": "not_admitted",
        }
    )


def _validate_and_copy_value(value: Any, source_field: str) -> Any:
    if value is None:
        raise M0CompilerError("null_value", f"null is not permitted for {source_field}")
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            finite_value = math.isfinite(float(value))
            bounded_value = abs(float(value)) <= 1e12
        except OverflowError as exc:
            raise M0CompilerError(
                "number_bound",
                f"number is out of bounds for {source_field}",
            ) from exc
        if not finite_value or not bounded_value:
            raise M0CompilerError("number_bound", f"number is out of bounds for {source_field}")
        return value
    if isinstance(value, str):
        if not value or len(value) > 1024:
            raise M0CompilerError("text_bound", f"text is empty or too long for {source_field}")
        return value
    if isinstance(value, list):
        if len(value) > 4096:
            raise M0CompilerError("array_bound", f"array is too large for {source_field}")
        copied: list[Any] = []
        for item in value:
            if isinstance(item, (Mapping, list, tuple)) or item is None:
                raise M0CompilerError("array_shape", f"nested value is not permitted for {source_field}")
            copied.append(_validate_and_copy_value(item, source_field))
        return copied
    raise M0CompilerError("value_type", f"unsupported public value for {source_field}")


def _value_type(value: Any, source_field: str) -> str:
    if isinstance(value, bool):
        return "bounded_boolean"
    if isinstance(value, (int, float)):
        return "bounded_number"
    if isinstance(value, list):
        return "opaque_reference"
    if source_field.endswith("natural_language_request"):
        return "bounded_public_text"
    if any(
        token in source_field
        for token in (
            "stage",
            "action_type",
            "acquisition_channel",
            "status",
            "evidence_types",
            "target_type",
        )
    ):
        return "bounded_enum"
    if "id" in source_field or source_field.endswith("target_value"):
        return "opaque_reference"
    return "bounded_public_text"


def _reject_forbidden_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(key)
            field_path = ".".join((*path, str(key)))
            if normalized in _FORBIDDEN_KEYS:
                raise M0CompilerError("forbidden_field", f"forbidden field: {field_path}")
            _reject_forbidden_keys(nested, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_forbidden_keys(nested, (*path, str(index)))


def _reject_unknown(value: Mapping[str, Any], allowed: frozenset[str], path: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        names = ", ".join(sorted(map(str, unknown)))
        raise M0CompilerError("unknown_field", f"unknown field(s) at {path}: {names}")


def _normalize_key(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise M0CompilerError("json_read", f"cannot read JSON: {path.name}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--mode", choices=("structural", "execute"), default="structural")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.mode != "structural":
        print("execute mode is not implemented or authorized for M0", file=sys.stderr)
        return 2
    if args.fixture_dir is None or args.output_dir is None:
        print("--fixture-dir and --output-dir are required", file=sys.stderr)
        return 2
    repo_root = Path(__file__).resolve().parents[3]
    report = run_fixture_directory(
        args.fixture_dir,
        args.output_dir,
        repo_root=repo_root,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["results"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
