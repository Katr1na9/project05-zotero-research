#!/usr/bin/env python3
"""Validate and summarize an isolated OTRF record-anchor audit.

The input is already value-free, but it contains record-level locator
commitments.  This second gate applies an exact schema allowlist and emits only
case identifiers, counts, hashes, gate booleans, and fixed blocker codes for
the model-development side.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
CASE_ID = re.compile(r"^C0*(?:1[3-9]|[2-9][0-9]|[1-9][0-9]{2,})(?:-|$)")
SAFE_FIELD_FIRST = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_@<"
)
SAFE_FIELD_REST = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.@:<>[]-"
)
BLOCKERS = {
    "no_cross_scenario_unique_low_frequency_record_anchor",
    "no_explicit_tool_to_attack_mapping_linkage",
}
ROOT_KEYS = {
    "audit_id",
    "status",
    "scope",
    "eligible_case_count",
    "comparison_scenario_count",
    "max_records_per_anchor",
    "case_reports",
    "automatic_case_bundle_ready_count",
    "payload_values_disclosed",
    "anchor_values_disclosed",
    "snippets_disclosed",
    "timestamps_or_host_values_disclosed",
    "attack_label_values_disclosed",
    "ground_truth_opened",
    "cost_values_opened",
    "model_outputs_opened",
    "planner_or_model_executed",
    "one_shot_evaluation_consumed",
}
CASE_KEYS = {
    "case_id",
    "metadata_sha256",
    "source_artifact_sha256",
    "parsed_record_count",
    "structured_tool_count",
    "attack_mapping_count",
    "candidate_anchor_count",
    "rare_anchor_count",
    "record_anchor_gate_passed",
    "explicit_mapping_linkage_present",
    "automatic_case_bundle_ready",
    "source_specific_blockers",
    "rare_anchors",
}
ANCHOR_KEYS = {
    "anchor_id",
    "metadata_source_fields",
    "record_hit_count",
    "cross_scenario_hit_count",
    "records",
}
RECORD_KEYS = {
    "case_id",
    "artifact_id",
    "archive_member_id",
    "record_ordinal",
    "line_number",
    "record_sha256",
    "record_hash_basis",
    "matched_field_names",
}
FALSE_BOUNDARY_FLAGS = {
    "payload_values_disclosed",
    "anchor_values_disclosed",
    "snippets_disclosed",
    "timestamps_or_host_values_disclosed",
    "attack_label_values_disclosed",
    "ground_truth_opened",
    "cost_values_opened",
    "model_outputs_opened",
    "planner_or_model_executed",
    "one_shot_evaluation_consumed",
}


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    observed = set(value)
    if observed != expected:
        raise ValueError(
            f"{field} violates the exact allowlist; "
            f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
        )


def require_array(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be boolean")
    return value


def require_count(value: Any, field: str, *, positive: bool = False) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if value < (1 if positive else 0):
        raise ValueError(f"{field} is outside its allowed range")
    return value


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def require_sha256(value: Any, field: str) -> str:
    text = require_string(value, field)
    if SHA256.fullmatch(text) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256")
    return text


def is_safe_field_path(value: str) -> bool:
    return (
        1 <= len(value) <= 512
        and value[0] in SAFE_FIELD_FIRST
        and all(character in SAFE_FIELD_REST for character in value[1:])
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_record(
    value: Any,
    *,
    field: str,
    case_id: str,
) -> None:
    record = require_object(value, field)
    require_exact_keys(record, RECORD_KEYS, field)
    if record["case_id"] != case_id:
        raise ValueError(f"{field}.case_id mismatch")
    require_sha256(record["artifact_id"], f"{field}.artifact_id")
    require_sha256(record["archive_member_id"], f"{field}.archive_member_id")
    require_count(record["record_ordinal"], f"{field}.record_ordinal", positive=True)
    line_number = record["line_number"]
    if line_number is not None:
        require_count(line_number, f"{field}.line_number", positive=True)
    require_sha256(record["record_sha256"], f"{field}.record_sha256")
    if record["record_hash_basis"] not in {"raw_jsonl_line", "canonical_json"}:
        raise ValueError(f"{field}.record_hash_basis is not allowed")
    matched_fields = require_array(
        record["matched_field_names"],
        f"{field}.matched_field_names",
    )
    if not matched_fields or len(matched_fields) != len(set(matched_fields)):
        raise ValueError(f"{field}.matched_field_names must be non-empty and unique")
    for index, name in enumerate(matched_fields):
        text = require_string(name, f"{field}.matched_field_names[{index}]")
        if not is_safe_field_path(text):
            raise ValueError(f"{field}.matched_field_names contains an unsafe field")


def validate_anchor(
    value: Any,
    *,
    field: str,
    case_id: str,
    max_records_per_anchor: int,
) -> None:
    anchor = require_object(value, field)
    require_exact_keys(anchor, ANCHOR_KEYS, field)
    require_sha256(anchor["anchor_id"], f"{field}.anchor_id")
    source_fields = require_array(
        anchor["metadata_source_fields"],
        f"{field}.metadata_source_fields",
    )
    allowed_source_fields = {
        "simulation.tools[].name",
        "simulation.tools[].module",
        "simulation.tools[].script",
    }
    if (
        not source_fields
        or len(source_fields) != len(set(source_fields))
        or not set(source_fields) <= allowed_source_fields
    ):
        raise ValueError(f"{field}.metadata_source_fields is outside the allowlist")
    hit_count = require_count(
        anchor["record_hit_count"],
        f"{field}.record_hit_count",
        positive=True,
    )
    if hit_count > max_records_per_anchor:
        raise ValueError(f"{field}.record_hit_count is not rare")
    if anchor["cross_scenario_hit_count"] != 1:
        raise ValueError(f"{field}.cross_scenario_hit_count must equal one")
    records = require_array(anchor["records"], f"{field}.records")
    if len(records) != hit_count:
        raise ValueError(f"{field}.records must retain every rare hit")
    for index, record in enumerate(records):
        validate_record(
            record,
            field=f"{field}.records[{index}]",
            case_id=case_id,
        )


def summarize_private_audit(
    audit: dict[str, Any],
    *,
    private_audit_sha256: str,
) -> dict[str, Any]:
    require_exact_keys(audit, ROOT_KEYS, "audit")
    if audit["audit_id"] != "project05-otrf-high-precision-record-anchor-audit-v0.3":
        raise ValueError("Unexpected private audit identifier")
    if audit["status"] != "complete":
        raise ValueError("Private audit is incomplete")
    require_string(audit["scope"], "audit.scope")
    for flag in FALSE_BOUNDARY_FLAGS:
        if require_bool(audit[flag], f"audit.{flag}"):
            raise ValueError(f"audit.{flag} must remain false")
    eligible_count = require_count(
        audit["eligible_case_count"],
        "audit.eligible_case_count",
        positive=True,
    )
    comparison_count = require_count(
        audit["comparison_scenario_count"],
        "audit.comparison_scenario_count",
    )
    max_records = require_count(
        audit["max_records_per_anchor"],
        "audit.max_records_per_anchor",
        positive=True,
    )
    cases = require_array(audit["case_reports"], "audit.case_reports")
    if len(cases) != eligible_count:
        raise ValueError("audit.case_reports does not match eligible_case_count")

    case_summaries: list[dict[str, Any]] = []
    observed_case_ids: set[str] = set()
    for index, raw_case in enumerate(cases):
        field = f"audit.case_reports[{index}]"
        case = require_object(raw_case, field)
        require_exact_keys(case, CASE_KEYS, field)
        case_id = require_string(case["case_id"], f"{field}.case_id")
        if CASE_ID.match(case_id) is None or case_id in observed_case_ids:
            raise ValueError(f"{field}.case_id is invalid or duplicated")
        observed_case_ids.add(case_id)
        metadata_sha256 = require_sha256(
            case["metadata_sha256"],
            f"{field}.metadata_sha256",
        )
        artifact_hashes = require_array(
            case["source_artifact_sha256"],
            f"{field}.source_artifact_sha256",
        )
        if not artifact_hashes or len(artifact_hashes) != len(set(artifact_hashes)):
            raise ValueError(f"{field}.source_artifact_sha256 must be non-empty and unique")
        for artifact_index, value in enumerate(artifact_hashes):
            require_sha256(
                value,
                f"{field}.source_artifact_sha256[{artifact_index}]",
            )
        parsed_count = require_count(
            case["parsed_record_count"],
            f"{field}.parsed_record_count",
        )
        structured_tool_count = require_count(
            case["structured_tool_count"],
            f"{field}.structured_tool_count",
        )
        mapping_count = require_count(
            case["attack_mapping_count"],
            f"{field}.attack_mapping_count",
        )
        candidate_count = require_count(
            case["candidate_anchor_count"],
            f"{field}.candidate_anchor_count",
        )
        rare_count = require_count(
            case["rare_anchor_count"],
            f"{field}.rare_anchor_count",
        )
        if rare_count > candidate_count:
            raise ValueError(f"{field}.rare_anchor_count exceeds candidates")
        record_gate = require_bool(
            case["record_anchor_gate_passed"],
            f"{field}.record_anchor_gate_passed",
        )
        mapping_gate = require_bool(
            case["explicit_mapping_linkage_present"],
            f"{field}.explicit_mapping_linkage_present",
        )
        automatic_ready = require_bool(
            case["automatic_case_bundle_ready"],
            f"{field}.automatic_case_bundle_ready",
        )
        if record_gate != (rare_count > 0):
            raise ValueError(f"{field}.record_anchor_gate_passed is inconsistent")
        if automatic_ready != (record_gate and mapping_gate):
            raise ValueError(f"{field}.automatic_case_bundle_ready is inconsistent")
        blockers = require_array(
            case["source_specific_blockers"],
            f"{field}.source_specific_blockers",
        )
        if len(blockers) != len(set(blockers)) or not set(blockers) <= BLOCKERS:
            raise ValueError(f"{field}.source_specific_blockers is outside the allowlist")
        expected_blockers = set()
        if not record_gate:
            expected_blockers.add(
                "no_cross_scenario_unique_low_frequency_record_anchor"
            )
        if not mapping_gate:
            expected_blockers.add("no_explicit_tool_to_attack_mapping_linkage")
        if set(blockers) != expected_blockers:
            raise ValueError(f"{field}.source_specific_blockers is inconsistent")
        anchors = require_array(case["rare_anchors"], f"{field}.rare_anchors")
        if len(anchors) != rare_count:
            raise ValueError(f"{field}.rare_anchors does not match rare_anchor_count")
        for anchor_index, anchor in enumerate(anchors):
            validate_anchor(
                anchor,
                field=f"{field}.rare_anchors[{anchor_index}]",
                case_id=case_id,
                max_records_per_anchor=max_records,
            )
        case_summaries.append(
            {
                "case_id": case_id,
                "metadata_sha256": metadata_sha256,
                "source_artifact_sha256": artifact_hashes,
                "parsed_record_count": parsed_count,
                "structured_tool_count": structured_tool_count,
                "attack_mapping_count": mapping_count,
                "candidate_anchor_count": candidate_count,
                "rare_anchor_count": rare_count,
                "record_anchor_gate_passed": record_gate,
                "explicit_mapping_linkage_present": mapping_gate,
                "automatic_case_bundle_ready": automatic_ready,
                "source_specific_blockers": blockers,
            }
        )

    observed_ready = sum(item["automatic_case_bundle_ready"] for item in case_summaries)
    if audit["automatic_case_bundle_ready_count"] != observed_ready:
        raise ValueError("automatic_case_bundle_ready_count is inconsistent")
    require_sha256(private_audit_sha256, "private_audit_sha256")
    return {
        "summary_id": "project05-otrf-record-anchor-audit-summary-v0.3",
        "status": "private_audit_validated_and_redacted",
        "private_audit_sha256": private_audit_sha256,
        "eligible_case_count": eligible_count,
        "comparison_scenario_count": comparison_count,
        "total_parsed_record_count": sum(
            item["parsed_record_count"] for item in case_summaries
        ),
        "record_anchor_gate_pass_count": sum(
            item["record_anchor_gate_passed"] for item in case_summaries
        ),
        "mapping_linkage_gate_pass_count": sum(
            item["explicit_mapping_linkage_present"] for item in case_summaries
        ),
        "automatic_case_bundle_ready_count": observed_ready,
        "case_summaries": case_summaries,
        "record_locators_returned": False,
        "payload_values_disclosed": False,
        "anchor_values_disclosed": False,
        "attack_label_values_disclosed": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened": False,
        "planner_or_model_executed": False,
        "one_shot_evaluation_consumed": False,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.private_audit.read_text(encoding="utf-8"))
    summary = summarize_private_audit(
        require_object(audit, "audit"),
        private_audit_sha256=file_sha256(args.private_audit),
    )
    write_json(args.output, summary)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "eligible_case_count": summary["eligible_case_count"],
                "record_anchor_gate_pass_count": summary[
                    "record_anchor_gate_pass_count"
                ],
                "mapping_linkage_gate_pass_count": summary[
                    "mapping_linkage_gate_pass_count"
                ],
                "automatic_case_bundle_ready_count": summary[
                    "automatic_case_bundle_ready_count"
                ],
                "one_shot_evaluation_consumed": False,
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
