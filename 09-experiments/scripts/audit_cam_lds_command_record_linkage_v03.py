#!/usr/bin/env python3
"""Audit source-native CAM-LDS command-to-record linkage without value return.

The isolated curator uses this tool to bridge a command object that already
contains source-native ATT&CK metadata to a concrete record in the same
publisher archive.  Only exact-boundary, within-case-low-frequency, and
cross-case-unique command anchors are retained.  Command text, ATT&CK values,
telemetry values, snippets, and semantic member paths never enter the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_otrf_high_precision_record_anchors_v03 import (  # noqa: E402
    CMDLET_TOKEN,
    FILE_TOKEN,
    Record,
    canonical_record_bytes,
    commitment,
    file_sha256,
    normalize_anchor,
    records_from_json_stream,
    sanitized_field_name,
    sha256_bytes,
)


MAPPING_KEYS = {
    "tactic",
    "tactics",
    "technique",
    "technique_name",
    "techniques",
}
DIRECT_ACTION_KEYS = {"cmd", "exe"}
SELECTED_TELEMETRY_KEYS = {
    "cmd",
    "comm",
    "command",
    "command_shell",
    "command_timeout",
    "exe",
    "execve",
    "parent",
    "process",
    "program_name",
    "proctitle",
}
PATH_TOKEN = re.compile(
    r"(?i)(?<![A-Za-z0-9])"
    r"(?:[A-Za-z]:[\\/]|/)[A-Za-z0-9_.$@%+~(){}[\]\\/-]{5,}"
    r"(?![A-Za-z0-9])"
)
KEY_VALUE_TOKEN = re.compile(
    r"""(?<!\S)([A-Za-z_][A-Za-z0-9_]*)="""
    r"""(?:"([^"]*)"|'([^']*)'|(\S+))"""
)
PREFIX_LENGTH = 6


@dataclass(frozen=True)
class CaseArchive:
    case_id: str
    archive_path: Path
    comparison_only: bool = False


@dataclass
class CommandAnchor:
    normalized: str
    mapping_commitments: set[str]
    metadata_source_fields: set[str]


@dataclass(frozen=True)
class RecordLocator:
    case_id: str
    archive_id: str
    member_id: str
    record_ordinal: int
    line_number: int | None
    record_sha256: str
    record_hash_basis: str
    matched_field_names: tuple[str, ...]


class PrefixMatcher:
    def __init__(self, anchors: Iterable[str]):
        self.anchors = sorted(set(anchors), key=lambda value: (-len(value), value))
        self.by_prefix: dict[str, list[str]] = defaultdict(list)
        for anchor in self.anchors:
            if len(anchor) < PREFIX_LENGTH:
                raise ValueError("Every command anchor must meet the prefix length")
            self.by_prefix[anchor[:PREFIX_LENGTH]].append(anchor)

    @staticmethod
    def _has_exact_boundary(text: str, anchor: str) -> bool:
        start = text.find(anchor)
        while start >= 0:
            end = start + len(anchor)
            left_ok = start == 0 or not text[start - 1].isalnum()
            right_ok = end == len(text) or not text[end].isalnum()
            if left_ok and right_ok:
                return True
            start = text.find(anchor, start + 1)
        return False

    def match(self, value: str) -> set[str]:
        text = normalize_anchor(value)
        if len(text) < PREFIX_LENGTH:
            return set()
        prefixes = {
            text[index : index + PREFIX_LENGTH]
            for index in range(len(text) - PREFIX_LENGTH + 1)
        }
        candidates = {
            anchor
            for prefix in prefixes
            for anchor in self.by_prefix.get(prefix, ())
        }
        return {
            anchor
            for anchor in candidates
            if self._has_exact_boundary(text, anchor)
        }


def canonical_mapping_commitment(key: bytes, metadata: dict[str, Any]) -> str:
    mapping = {
        field: metadata[field]
        for field in sorted(MAPPING_KEYS)
        if field in metadata
    }
    encoded = json.dumps(
        mapping,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return commitment(key, "cam-mapping", encoded)


def is_mapped_command_object(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    metadata = value.get("metadata")
    return isinstance(metadata, dict) and bool(set(metadata) & MAPPING_KEYS)


def iter_mapped_command_objects(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if is_mapped_command_object(value):
            yield value
        for child in value.values():
            yield from iter_mapped_command_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_mapped_command_objects(child)


def iter_direct_action_strings(value: dict[str, Any]) -> Iterator[tuple[str, str]]:
    for field in DIRECT_ACTION_KEYS:
        child = value.get(field)
        if isinstance(child, str) and child.strip():
            yield f"commands[].{field}", child
    nested = value.get("commands")
    if isinstance(nested, list):
        for child in nested:
            if not isinstance(child, dict):
                continue
            for field in DIRECT_ACTION_KEYS:
                nested_value = child.get(field)
                if isinstance(nested_value, str) and nested_value.strip():
                    yield f"commands[].commands[].{field}", nested_value


def is_specific_full_command(value: str) -> bool:
    normalized = normalize_anchor(value)
    if not 12 <= len(normalized) <= 512:
        return False
    if normalized in {"powershell", "cmd.exe", "bash", "sh", "python"}:
        return False
    token_count = len(normalized.split())
    has_specific_syntax = bool(re.search(r"[./\\_=-]|\d", normalized))
    return token_count >= 2 and has_specific_syntax


def anchors_from_action(value: str) -> set[str]:
    candidates = set(FILE_TOKEN.findall(value))
    candidates.update(CMDLET_TOKEN.findall(value))
    candidates.update(PATH_TOKEN.findall(value))
    if is_specific_full_command(value):
        candidates.add(value)
    anchors = {normalize_anchor(candidate) for candidate in candidates}
    return {
        anchor
        for anchor in anchors
        if len(anchor) >= 8 and sum(character.isalnum() for character in anchor) >= 5
    }


def extract_command_anchors(
    document: Any,
    key: bytes,
) -> tuple[dict[str, CommandAnchor], int]:
    anchors: dict[str, CommandAnchor] = {}
    mapped_object_count = 0
    for command_object in iter_mapped_command_objects(document):
        mapped_object_count += 1
        metadata = command_object["metadata"]
        mapping_id = canonical_mapping_commitment(key, metadata)
        for source_field, action in iter_direct_action_strings(command_object):
            for normalized in anchors_from_action(action):
                anchor = anchors.setdefault(
                    normalized,
                    CommandAnchor(normalized, set(), set()),
                )
                anchor.mapping_commitments.add(mapping_id)
                anchor.metadata_source_fields.add(source_field)
    return anchors, mapped_object_count


def merge_command_anchors(
    destination: dict[str, CommandAnchor],
    source: dict[str, CommandAnchor],
) -> None:
    for normalized, item in source.items():
        current = destination.setdefault(
            normalized,
            CommandAnchor(normalized, set(), set()),
        )
        current.mapping_commitments.update(item.mapping_commitments)
        current.metadata_source_fields.update(item.metadata_source_fields)


def parse_structured_document(payload: bytes, suffix: str) -> Any | None:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return None
    try:
        if suffix == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError):
        return None


def inspect_archive_for_commands(
    archive_path: Path,
    key: bytes,
    *,
    maximum_document_bytes: int = 8 * 1024 * 1024,
) -> tuple[dict[str, CommandAnchor], dict[str, Any], set[str]]:
    anchors: dict[str, CommandAnchor] = {}
    command_member_ids: set[str] = set()
    command_member_names: set[str] = set()
    mapped_object_count = 0
    member_count = 0
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            member_count += 1
            suffix = Path(member.filename).suffix.casefold()
            if suffix not in {".json", ".yaml", ".yml"}:
                continue
            if member.file_size > maximum_document_bytes:
                continue
            with archive.open(member) as stream:
                payload = stream.read()
            document = parse_structured_document(payload, suffix)
            if document is None:
                continue
            member_anchors, object_count = extract_command_anchors(document, key)
            if object_count == 0:
                continue
            merge_command_anchors(anchors, member_anchors)
            mapped_object_count += object_count
            command_member_ids.add(
                commitment(key, "cam-command-member", member.filename)
            )
            command_member_names.add(member.filename)
    return (
        anchors,
        {
            "archive_member_count": member_count,
            "mapped_command_member_count": len(command_member_ids),
            "mapped_command_object_count": mapped_object_count,
        },
        command_member_names,
    )


def iter_selected_text_fields(
    value: Any,
    prefix: str = "",
) -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for raw_key, child in value.items():
            key_text = str(raw_key)
            key = sanitized_field_name(key_text)
            path = f"{prefix}.{key}" if prefix else key
            if key_text.casefold() in SELECTED_TELEMETRY_KEYS:
                if isinstance(child, str):
                    yield path, child
                elif isinstance(child, list):
                    for item in child:
                        if isinstance(item, str):
                            yield f"{path}[]", item
            yield from iter_selected_text_fields(child, path)
    elif isinstance(value, list):
        path = f"{prefix}[]" if prefix else "[]"
        for child in value:
            yield from iter_selected_text_fields(child, path)


def selected_fields_from_log_line(raw_line: bytes) -> list[tuple[str, str]]:
    try:
        text = raw_line.decode("utf-8")
    except UnicodeDecodeError:
        return []
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            value = None
        if value is not None:
            return list(iter_selected_text_fields(value))
    selected: list[tuple[str, str]] = []
    for match in KEY_VALUE_TOKEN.finditer(stripped):
        field = match.group(1)
        if field.casefold() not in SELECTED_TELEMETRY_KEYS:
            continue
        value = next(
            group
            for group in match.groups()[1:]
            if group is not None
        )
        selected.append((sanitized_field_name(field), value))
    return selected


def match_fields(
    fields: Iterable[tuple[str, str]],
    matcher: PrefixMatcher,
) -> dict[str, set[str]]:
    matched: dict[str, set[str]] = defaultdict(set)
    for field, value in fields:
        for anchor in matcher.match(value):
            matched[anchor].add(field)
    return matched


def record_locator(
    *,
    case_id: str,
    archive_id: str,
    member_id: str,
    record_ordinal: int,
    line_number: int | None,
    record_sha256: str,
    record_hash_basis: str,
    field_names: set[str],
) -> RecordLocator:
    return RecordLocator(
        case_id=case_id,
        archive_id=archive_id,
        member_id=member_id,
        record_ordinal=record_ordinal,
        line_number=line_number,
        record_sha256=record_sha256,
        record_hash_basis=record_hash_basis,
        matched_field_names=tuple(sorted(field_names)),
    )


def scan_json_member(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    *,
    case_id: str,
    archive_id: str,
    member_id: str,
    matcher: PrefixMatcher,
    on_match: Callable[[set[str], RecordLocator], None],
) -> tuple[int, int]:
    parsed = 0
    structured = 0
    with archive.open(member) as stream:
        try:
            records = records_from_json_stream(
                stream,
                artifact_id=archive_id,
                member_id=member_id,
            )
            for record in records:
                parsed += 1
                fields = list(iter_selected_text_fields(record.value))
                if fields:
                    structured += 1
                record_matches = match_fields(fields, matcher)
                if not record_matches:
                    continue
                all_anchors = set(record_matches)
                field_names = {
                    field
                    for values in record_matches.values()
                    for field in values
                }
                on_match(
                    all_anchors,
                    record_locator(
                        case_id=case_id,
                        archive_id=archive_id,
                        member_id=member_id,
                        record_ordinal=record.record_ordinal,
                        line_number=record.line_number,
                        record_sha256=record.record_sha256,
                        record_hash_basis=record.record_hash_basis,
                        field_names=field_names,
                    ),
                )
        except ValueError:
            return 0, 0
    return parsed, structured


def scan_log_member(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    *,
    case_id: str,
    archive_id: str,
    member_id: str,
    matcher: PrefixMatcher,
    on_match: Callable[[set[str], RecordLocator], None],
) -> tuple[int, int]:
    parsed = 0
    structured = 0
    with archive.open(member) as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            if not raw_line.strip():
                continue
            parsed += 1
            fields = selected_fields_from_log_line(raw_line)
            if fields:
                structured += 1
            record_matches = match_fields(fields, matcher)
            if not record_matches:
                continue
            all_anchors = set(record_matches)
            field_names = {
                field
                for values in record_matches.values()
                for field in values
            }
            on_match(
                all_anchors,
                record_locator(
                    case_id=case_id,
                    archive_id=archive_id,
                    member_id=member_id,
                    record_ordinal=parsed,
                    line_number=line_number,
                    record_sha256=sha256_bytes(raw_line.rstrip(b"\r\n")),
                    record_hash_basis="raw_log_line",
                    field_names=field_names,
                ),
            )
    return parsed, structured


def locator_to_dict(locator: RecordLocator) -> dict[str, Any]:
    return {
        "case_id": locator.case_id,
        "archive_id": locator.archive_id,
        "archive_member_id": locator.member_id,
        "record_ordinal": locator.record_ordinal,
        "line_number": locator.line_number,
        "record_sha256": locator.record_sha256,
        "record_hash_basis": locator.record_hash_basis,
        "matched_field_names": list(locator.matched_field_names),
    }


def audit_cam_archives(
    cases: list[CaseArchive],
    *,
    commitment_key: bytes,
    maximum_records_per_anchor: int = 5,
    minimum_distinct_mapping_commitments: int = 2,
) -> dict[str, Any]:
    if len(commitment_key) < 32:
        raise ValueError("The private commitment key must contain at least 32 bytes")
    if maximum_records_per_anchor < 1:
        raise ValueError("maximum_records_per_anchor must be positive")
    if minimum_distinct_mapping_commitments < 2:
        raise ValueError("At least two mapped nodes are required for a chain case")
    if not cases or all(case.comparison_only for case in cases):
        raise ValueError("At least one eligible case is required")
    case_ids = [case.case_id for case in cases]
    paths = [str(case.archive_path.resolve()) for case in cases]
    if len(case_ids) != len(set(case_ids)) or len(paths) != len(set(paths)):
        raise ValueError("Case identifiers and archive paths must be unique")
    if any(not case.archive_path.is_file() for case in cases):
        raise ValueError("Every CAM case archive must exist")

    anchors_by_case: dict[str, dict[str, CommandAnchor]] = {}
    structural_by_case: dict[str, dict[str, Any]] = {}
    command_members_by_case: dict[str, set[str]] = {}
    global_anchors: set[str] = set()
    for case in cases:
        anchors, structural, command_members = inspect_archive_for_commands(
            case.archive_path,
            commitment_key,
        )
        anchors_by_case[case.case_id] = anchors
        structural_by_case[case.case_id] = structural
        command_members_by_case[case.case_id] = command_members
        global_anchors.update(anchors)

    matcher = PrefixMatcher(global_anchors)
    hit_counts: dict[str, int] = defaultdict(int)
    hit_cases: dict[str, set[str]] = defaultdict(set)
    retained: dict[str, list[RecordLocator]] = defaultdict(list)
    parsed_records: dict[str, int] = defaultdict(int)
    structured_records: dict[str, int] = defaultdict(int)
    json_members: dict[str, int] = defaultdict(int)
    log_members: dict[str, int] = defaultdict(int)

    def retain_matches(
        matched_anchors: set[str],
        locator: RecordLocator,
    ) -> None:
        for anchor in matched_anchors:
            hit_counts[anchor] += 1
            hit_cases[anchor].add(locator.case_id)
            if len(retained[anchor]) <= maximum_records_per_anchor:
                retained[anchor].append(locator)

    for case in cases:
        archive_sha256 = file_sha256(case.archive_path)
        archive_id = commitment(
            commitment_key,
            "cam-archive",
            f"{case.case_id}:{archive_sha256}",
        )
        with zipfile.ZipFile(case.archive_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                if member.filename in command_members_by_case[case.case_id]:
                    continue
                suffix = Path(member.filename).suffix.casefold()
                if suffix not in {".json", ".log"}:
                    continue
                member_id = commitment(
                    commitment_key,
                    "cam-telemetry-member",
                    f"{archive_sha256}:{member.filename}",
                )
                if suffix == ".json":
                    json_members[case.case_id] += 1
                    parsed, structured = scan_json_member(
                        archive,
                        member,
                        case_id=case.case_id,
                        archive_id=archive_id,
                        member_id=member_id,
                        matcher=matcher,
                        on_match=retain_matches,
                    )
                else:
                    log_members[case.case_id] += 1
                    parsed, structured = scan_log_member(
                        archive,
                        member,
                        case_id=case.case_id,
                        archive_id=archive_id,
                        member_id=member_id,
                        matcher=matcher,
                        on_match=retain_matches,
                    )
                parsed_records[case.case_id] += parsed
                structured_records[case.case_id] += structured

    reports: list[dict[str, Any]] = []
    for case in cases:
        if case.comparison_only:
            continue
        command_anchors = anchors_by_case[case.case_id]
        rare_unambiguous = [
            anchor
            for anchor, details in command_anchors.items()
            if len(details.mapping_commitments) == 1
            and 0 < hit_counts[anchor] <= maximum_records_per_anchor
            and hit_cases[anchor] == {case.case_id}
        ]
        mapping_commitments = {
            next(iter(command_anchors[anchor].mapping_commitments))
            for anchor in rare_unambiguous
        }
        record_gate = bool(rare_unambiguous)
        chain_gate = (
            len(mapping_commitments) >= minimum_distinct_mapping_commitments
        )
        source_mapping_gate = (
            structural_by_case[case.case_id]["mapped_command_object_count"] > 0
        )
        ready = source_mapping_gate and record_gate and chain_gate
        blockers: list[str] = []
        if not source_mapping_gate:
            blockers.append("no_source_native_attack_mapping")
        if not record_gate:
            blockers.append(
                "no_cross_case_unique_low_frequency_mapped_command_record_anchor"
            )
        if record_gate and not chain_gate:
            blockers.append("insufficient_distinct_record_anchored_attack_mappings")
        anchor_reports = []
        for anchor in rare_unambiguous:
            details = command_anchors[anchor]
            anchor_reports.append(
                {
                    "anchor_id": commitment(
                        commitment_key,
                        "cam-command-anchor",
                        anchor,
                    ),
                    "mapping_commitment": next(
                        iter(details.mapping_commitments)
                    ),
                    "metadata_source_fields": sorted(
                        details.metadata_source_fields
                    ),
                    "record_hit_count": hit_counts[anchor],
                    "cross_case_hit_count": len(hit_cases[anchor]),
                    "records": [
                        locator_to_dict(locator)
                        for locator in retained[anchor]
                    ],
                }
            )
        reports.append(
            {
                "case_id": case.case_id,
                "archive_sha256": file_sha256(case.archive_path),
                **structural_by_case[case.case_id],
                "json_member_count": json_members[case.case_id],
                "log_member_count": log_members[case.case_id],
                "parsed_record_count": parsed_records[case.case_id],
                "structured_command_record_count": structured_records[case.case_id],
                "candidate_command_anchor_count": len(command_anchors),
                "rare_unambiguous_anchor_count": len(rare_unambiguous),
                "distinct_anchored_mapping_count": len(mapping_commitments),
                "source_native_mapping_gate_passed": source_mapping_gate,
                "command_record_anchor_gate_passed": record_gate,
                "minimum_chain_mapping_gate_passed": chain_gate,
                "automatic_case_bundle_ready": ready,
                "source_specific_blockers": blockers,
                "rare_anchors": anchor_reports,
            }
        )

    return {
        "audit_id": "project05-cam-lds-command-record-linkage-audit-v0.3",
        "status": "complete",
        "scope": "isolated curator; source-native mapped commands to structured records",
        "eligible_case_count": len(reports),
        "comparison_case_count": sum(case.comparison_only for case in cases),
        "maximum_records_per_anchor": maximum_records_per_anchor,
        "minimum_distinct_mapping_commitments": minimum_distinct_mapping_commitments,
        "case_reports": reports,
        "automatic_case_bundle_ready_count": sum(
            report["automatic_case_bundle_ready"] for report in reports
        ),
        "command_values_disclosed": False,
        "telemetry_values_disclosed": False,
        "anchor_values_disclosed": False,
        "attack_mapping_values_disclosed": False,
        "record_snippets_disclosed": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened": False,
        "planner_or_model_executed": False,
        "one_shot_evaluation_consumed": False,
    }


def parse_case(value: str, comparison_only: bool) -> CaseArchive:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Case must be CASE_ID=ARCHIVE_PATH")
    case_id, raw_path = value.split("=", 1)
    if not case_id or not raw_path:
        raise argparse.ArgumentTypeError("Invalid CAM case specification")
    return CaseArchive(case_id, Path(raw_path), comparison_only)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--comparison", action="append", default=[])
    parser.add_argument("--commitment-key-file", type=Path, required=True)
    parser.add_argument("--maximum-records-per-anchor", type=int, default=5)
    parser.add_argument(
        "--minimum-distinct-mapping-commitments",
        type=int,
        default=2,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = [parse_case(value, False) for value in args.case]
    cases.extend(parse_case(value, True) for value in args.comparison)
    report = audit_cam_archives(
        cases,
        commitment_key=args.commitment_key_file.read_bytes(),
        maximum_records_per_anchor=args.maximum_records_per_anchor,
        minimum_distinct_mapping_commitments=args.minimum_distinct_mapping_commitments,
    )
    write_json(args.output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "eligible_case_count": report["eligible_case_count"],
                "comparison_case_count": report["comparison_case_count"],
                "automatic_case_bundle_ready_count": report[
                    "automatic_case_bundle_ready_count"
                ],
                "command_values_disclosed": False,
                "telemetry_values_disclosed": False,
                "model_outputs_opened": False,
                "one_shot_evaluation_consumed": False,
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
