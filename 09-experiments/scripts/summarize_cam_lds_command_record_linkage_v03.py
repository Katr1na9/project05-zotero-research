#!/usr/bin/env python3
"""Strictly validate and redact a private CAM-LDS linkage audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
CASE_ID = re.compile(r"^C0*(?:1[3-9]|[2-9][0-9]|[1-9][0-9]{2,})(?:-|$)")
BLOCKERS = {
    "no_source_native_attack_mapping",
    "no_cross_case_unique_low_frequency_mapped_command_record_anchor",
    "insufficient_distinct_record_anchored_attack_mappings",
}
SOURCE_FIELDS = {
    "commands[].cmd",
    "commands[].exe",
    "commands[].commands[].cmd",
    "commands[].commands[].exe",
}
ROOT_KEYS = {
    "audit_id",
    "status",
    "scope",
    "eligible_case_count",
    "comparison_case_count",
    "maximum_records_per_anchor",
    "minimum_distinct_mapping_commitments",
    "case_reports",
    "automatic_case_bundle_ready_count",
    "command_values_disclosed",
    "telemetry_values_disclosed",
    "anchor_values_disclosed",
    "attack_mapping_values_disclosed",
    "record_snippets_disclosed",
    "ground_truth_opened",
    "cost_values_opened",
    "model_outputs_opened",
    "planner_or_model_executed",
    "one_shot_evaluation_consumed",
}
CASE_KEYS = {
    "case_id",
    "archive_sha256",
    "archive_member_count",
    "mapped_command_member_count",
    "mapped_command_object_count",
    "json_member_count",
    "log_member_count",
    "parsed_record_count",
    "structured_command_record_count",
    "candidate_command_anchor_count",
    "rare_unambiguous_anchor_count",
    "distinct_anchored_mapping_count",
    "source_native_mapping_gate_passed",
    "command_record_anchor_gate_passed",
    "minimum_chain_mapping_gate_passed",
    "automatic_case_bundle_ready",
    "source_specific_blockers",
    "rare_anchors",
}
ANCHOR_KEYS = {
    "anchor_id",
    "mapping_commitment",
    "metadata_source_fields",
    "record_hit_count",
    "cross_case_hit_count",
    "records",
}
RECORD_KEYS = {
    "case_id",
    "archive_id",
    "archive_member_id",
    "record_ordinal",
    "line_number",
    "record_sha256",
    "record_hash_basis",
    "matched_field_names",
}
FALSE_BOUNDARY_FLAGS = {
    "command_values_disclosed",
    "telemetry_values_disclosed",
    "anchor_values_disclosed",
    "attack_mapping_values_disclosed",
    "record_snippets_disclosed",
    "ground_truth_opened",
    "cost_values_opened",
    "model_outputs_opened",
    "planner_or_model_executed",
    "one_shot_evaluation_consumed",
}
SAFE_FIELD_FIRST = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_@<"
)
SAFE_FIELD_REST = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.@:<>[]-"
)


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


def validate_record(value: Any, *, field: str, case_id: str) -> None:
    record = require_object(value, field)
    require_exact_keys(record, RECORD_KEYS, field)
    if record["case_id"] != case_id:
        raise ValueError(f"{field}.case_id mismatch")
    require_sha256(record["archive_id"], f"{field}.archive_id")
    require_sha256(record["archive_member_id"], f"{field}.archive_member_id")
    require_count(record["record_ordinal"], f"{field}.record_ordinal", positive=True)
    if record["line_number"] is not None:
        require_count(record["line_number"], f"{field}.line_number", positive=True)
    require_sha256(record["record_sha256"], f"{field}.record_sha256")
    if record["record_hash_basis"] not in {
        "raw_jsonl_line",
        "canonical_json",
        "raw_log_line",
    }:
        raise ValueError(f"{field}.record_hash_basis is not allowed")
    fields = require_array(record["matched_field_names"], f"{field}.matched_field_names")
    if not fields or len(fields) != len(set(fields)):
        raise ValueError(f"{field}.matched_field_names must be non-empty and unique")
    for index, value in enumerate(fields):
        text = require_string(value, f"{field}.matched_field_names[{index}]")
        if not is_safe_field_path(text):
            raise ValueError(f"{field}.matched_field_names contains an unsafe field")


def validate_anchor(
    value: Any,
    *,
    field: str,
    case_id: str,
    maximum_records_per_anchor: int,
) -> str:
    anchor = require_object(value, field)
    require_exact_keys(anchor, ANCHOR_KEYS, field)
    require_sha256(anchor["anchor_id"], f"{field}.anchor_id")
    mapping_commitment = require_sha256(
        anchor["mapping_commitment"],
        f"{field}.mapping_commitment",
    )
    source_fields = require_array(
        anchor["metadata_source_fields"],
        f"{field}.metadata_source_fields",
    )
    if (
        not source_fields
        or len(source_fields) != len(set(source_fields))
        or not set(source_fields) <= SOURCE_FIELDS
    ):
        raise ValueError(f"{field}.metadata_source_fields is outside the allowlist")
    hit_count = require_count(
        anchor["record_hit_count"],
        f"{field}.record_hit_count",
        positive=True,
    )
    if hit_count > maximum_records_per_anchor:
        raise ValueError(f"{field}.record_hit_count is not low frequency")
    if anchor["cross_case_hit_count"] != 1:
        raise ValueError(f"{field}.cross_case_hit_count must equal one")
    records = require_array(anchor["records"], f"{field}.records")
    if len(records) != hit_count:
        raise ValueError(f"{field}.records must retain every low-frequency hit")
    for index, record in enumerate(records):
        validate_record(
            record,
            field=f"{field}.records[{index}]",
            case_id=case_id,
        )
    return mapping_commitment


def summarize_private_audit(
    audit: dict[str, Any],
    *,
    private_audit_sha256: str,
) -> dict[str, Any]:
    require_exact_keys(audit, ROOT_KEYS, "audit")
    if audit["audit_id"] != "project05-cam-lds-command-record-linkage-audit-v0.3":
        raise ValueError("Unexpected CAM private audit identifier")
    if audit["status"] != "complete":
        raise ValueError("CAM private audit is incomplete")
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
        audit["comparison_case_count"],
        "audit.comparison_case_count",
    )
    maximum_records = require_count(
        audit["maximum_records_per_anchor"],
        "audit.maximum_records_per_anchor",
        positive=True,
    )
    minimum_mappings = require_count(
        audit["minimum_distinct_mapping_commitments"],
        "audit.minimum_distinct_mapping_commitments",
        positive=True,
    )
    if minimum_mappings < 2:
        raise ValueError("At least two distinct mappings are required")
    cases = require_array(audit["case_reports"], "audit.case_reports")
    if len(cases) != eligible_count:
        raise ValueError("audit.case_reports does not match eligible_case_count")

    summaries: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()
    for index, raw_case in enumerate(cases):
        field = f"audit.case_reports[{index}]"
        case = require_object(raw_case, field)
        require_exact_keys(case, CASE_KEYS, field)
        case_id = require_string(case["case_id"], f"{field}.case_id")
        if CASE_ID.match(case_id) is None or case_id in seen_case_ids:
            raise ValueError(f"{field}.case_id is invalid or duplicated")
        seen_case_ids.add(case_id)
        archive_sha256 = require_sha256(
            case["archive_sha256"],
            f"{field}.archive_sha256",
        )
        count_fields = (
            "archive_member_count",
            "mapped_command_member_count",
            "mapped_command_object_count",
            "json_member_count",
            "log_member_count",
            "parsed_record_count",
            "structured_command_record_count",
            "candidate_command_anchor_count",
            "rare_unambiguous_anchor_count",
            "distinct_anchored_mapping_count",
        )
        counts = {
            name: require_count(case[name], f"{field}.{name}")
            for name in count_fields
        }
        if counts["structured_command_record_count"] > counts["parsed_record_count"]:
            raise ValueError(f"{field}.structured_command_record_count exceeds records")
        if counts["rare_unambiguous_anchor_count"] > counts[
            "candidate_command_anchor_count"
        ]:
            raise ValueError(f"{field}.rare anchors exceed candidates")
        source_gate = require_bool(
            case["source_native_mapping_gate_passed"],
            f"{field}.source_native_mapping_gate_passed",
        )
        record_gate = require_bool(
            case["command_record_anchor_gate_passed"],
            f"{field}.command_record_anchor_gate_passed",
        )
        chain_gate = require_bool(
            case["minimum_chain_mapping_gate_passed"],
            f"{field}.minimum_chain_mapping_gate_passed",
        )
        ready = require_bool(
            case["automatic_case_bundle_ready"],
            f"{field}.automatic_case_bundle_ready",
        )
        if source_gate != (counts["mapped_command_object_count"] > 0):
            raise ValueError(f"{field}.source_native_mapping_gate_passed is inconsistent")
        if record_gate != (counts["rare_unambiguous_anchor_count"] > 0):
            raise ValueError(f"{field}.command_record_anchor_gate_passed is inconsistent")
        if chain_gate != (
            counts["distinct_anchored_mapping_count"] >= minimum_mappings
        ):
            raise ValueError(f"{field}.minimum_chain_mapping_gate_passed is inconsistent")
        if ready != (source_gate and record_gate and chain_gate):
            raise ValueError(f"{field}.automatic_case_bundle_ready is inconsistent")
        blockers = require_array(
            case["source_specific_blockers"],
            f"{field}.source_specific_blockers",
        )
        if len(blockers) != len(set(blockers)) or not set(blockers) <= BLOCKERS:
            raise ValueError(f"{field}.source_specific_blockers is outside the allowlist")
        expected_blockers = set()
        if not source_gate:
            expected_blockers.add("no_source_native_attack_mapping")
        if not record_gate:
            expected_blockers.add(
                "no_cross_case_unique_low_frequency_mapped_command_record_anchor"
            )
        if record_gate and not chain_gate:
            expected_blockers.add(
                "insufficient_distinct_record_anchored_attack_mappings"
            )
        if set(blockers) != expected_blockers:
            raise ValueError(f"{field}.source_specific_blockers is inconsistent")
        anchors = require_array(case["rare_anchors"], f"{field}.rare_anchors")
        if len(anchors) != counts["rare_unambiguous_anchor_count"]:
            raise ValueError(f"{field}.rare_anchors count is inconsistent")
        observed_mappings = {
            validate_anchor(
                anchor,
                field=f"{field}.rare_anchors[{anchor_index}]",
                case_id=case_id,
                maximum_records_per_anchor=maximum_records,
            )
            for anchor_index, anchor in enumerate(anchors)
        }
        if len(observed_mappings) != counts["distinct_anchored_mapping_count"]:
            raise ValueError(f"{field}.distinct_anchored_mapping_count is inconsistent")
        summaries.append(
            {
                "case_id": case_id,
                "archive_sha256": archive_sha256,
                **counts,
                "source_native_mapping_gate_passed": source_gate,
                "command_record_anchor_gate_passed": record_gate,
                "minimum_chain_mapping_gate_passed": chain_gate,
                "automatic_case_bundle_ready": ready,
                "source_specific_blockers": blockers,
            }
        )

    observed_ready = sum(item["automatic_case_bundle_ready"] for item in summaries)
    if audit["automatic_case_bundle_ready_count"] != observed_ready:
        raise ValueError("automatic_case_bundle_ready_count is inconsistent")
    require_sha256(private_audit_sha256, "private_audit_sha256")
    return {
        "summary_id": "project05-cam-lds-command-record-linkage-summary-v0.3",
        "status": "private_audit_validated_and_redacted",
        "private_audit_sha256": private_audit_sha256,
        "eligible_case_count": eligible_count,
        "comparison_case_count": comparison_count,
        "total_parsed_record_count": sum(
            item["parsed_record_count"] for item in summaries
        ),
        "total_structured_command_record_count": sum(
            item["structured_command_record_count"] for item in summaries
        ),
        "source_native_mapping_gate_pass_count": sum(
            item["source_native_mapping_gate_passed"] for item in summaries
        ),
        "command_record_anchor_gate_pass_count": sum(
            item["command_record_anchor_gate_passed"] for item in summaries
        ),
        "minimum_chain_mapping_gate_pass_count": sum(
            item["minimum_chain_mapping_gate_passed"] for item in summaries
        ),
        "automatic_case_bundle_ready_count": observed_ready,
        "case_summaries": summaries,
        "record_locators_returned": False,
        "mapping_commitments_returned": False,
        "command_values_disclosed": False,
        "telemetry_values_disclosed": False,
        "anchor_values_disclosed": False,
        "attack_mapping_values_disclosed": False,
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
                "source_native_mapping_gate_pass_count": summary[
                    "source_native_mapping_gate_pass_count"
                ],
                "command_record_anchor_gate_pass_count": summary[
                    "command_record_anchor_gate_pass_count"
                ],
                "minimum_chain_mapping_gate_pass_count": summary[
                    "minimum_chain_mapping_gate_pass_count"
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
