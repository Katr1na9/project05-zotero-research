#!/usr/bin/env python3
"""Audit OTRF record anchors without returning telemetry or label values.

This utility is intended for the isolated final-blind curator.  It derives
candidate anchors only from the structured ``simulation.tools`` metadata
fields, scans JSON telemetry, and returns commitments, counts, field names,
record ordinals, and record SHA-256 values.  It never returns the anchor text,
matched telemetry values, snippets, timestamps, hosts, labels, or narratives.

An event anchor and an ATT&CK mapping are deliberately separate gates.  A
source package that lists tools and attack mappings side by side, but does not
bind a tool to a particular mapping, is not eligible for automatic case-bundle
construction even when rare event anchors are found.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Iterator

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only in a lean runtime
    raise RuntimeError("PyYAML is required for OTRF metadata parsing") from exc


TOOL_FIELDS = ("name", "module", "script")
MAPPING_KEYS_ON_TOOL = {
    "attack_id",
    "attack_mapping",
    "attack_mappings",
    "tactic",
    "tactics",
    "technique",
    "technique_id",
}
TOOL_KEYS_ON_MAPPING = {
    "command",
    "module",
    "simulation_tool",
    "simulation_tools",
    "tool",
    "tools",
}
GENERIC_ANCHORS = {
    "cmd.exe",
    "command prompt",
    "java",
    "metasploit",
    "powershell",
    "powershell.exe",
    "python",
    "python.exe",
    "rundll32.exe",
    "windows",
    "wscript.exe",
}
FILE_TOKEN = re.compile(
    r"(?i)(?<![A-Za-z0-9])"
    r"[A-Za-z0-9_.-]{3,}\.(?:bat|class|cmd|dll|exe|jar|js|ps1|py|vbs)"
    r"(?![A-Za-z0-9])"
)
CMDLET_TOKEN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"[A-Z][A-Za-z0-9]{2,}-[A-Z][A-Za-z0-9-]{3,}"
    r"(?![A-Za-z0-9])"
)
SAFE_FIELD_NAME = re.compile(r"^[A-Za-z_@][A-Za-z0-9_.@-]{0,63}$")


@dataclass(frozen=True)
class ScenarioSpec:
    case_id: str
    scenario_name: str
    comparison_only: bool = False


@dataclass(frozen=True)
class Anchor:
    normalized: str
    source_fields: tuple[str, ...]


@dataclass(frozen=True)
class Record:
    artifact_id: str
    member_id: str
    record_ordinal: int
    line_number: int | None
    value: Any
    record_sha256: str
    record_hash_basis: str


@dataclass(frozen=True)
class AnchorMatcher:
    pattern: re.Pattern[str]
    anchor_by_group: dict[str, str]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_record_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def commitment(key: bytes, namespace: str, value: str) -> str:
    message = f"{namespace}\0{value}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def normalize_anchor(value: str) -> str:
    return " ".join(value.casefold().split()).strip(" \t\r\n\"'`")


def is_specific_anchor(raw_value: str) -> bool:
    normalized = normalize_anchor(raw_value)
    if not 8 <= len(normalized) <= 128:
        return False
    if normalized in GENERIC_ANCHORS:
        return False
    if sum(character.isalnum() for character in normalized) < 5:
        return False
    has_internal_camel = bool(re.search(r"[a-z][A-Z]", raw_value))
    has_specific_punctuation = bool(re.search(r"[._/-]", normalized))
    has_digit = any(character.isdigit() for character in normalized)
    is_long_single_token = " " not in normalized and len(normalized) >= 12
    return has_internal_camel or has_specific_punctuation or has_digit or is_long_single_token


def anchors_from_tool_field(field: str, value: Any) -> set[str]:
    if not isinstance(value, str) or not value.strip():
        return set()
    candidates: set[str] = set()
    if field in {"name", "module"}:
        candidates.add(value)
        candidates.update(FILE_TOKEN.findall(value))
    elif field == "script":
        # Script bodies may contain hosts, accounts, and IOCs.  Only executable
        # or module-like tokens and PowerShell cmdlet forms are admissible.
        candidates.update(FILE_TOKEN.findall(value))
        candidates.update(CMDLET_TOKEN.findall(value))
    return {
        normalize_anchor(candidate)
        for candidate in candidates
        if is_specific_anchor(candidate)
    }


def extract_anchors(metadata: dict[str, Any]) -> list[Anchor]:
    tools = metadata.get("simulation", {}).get("tools", [])
    if not isinstance(tools, list):
        return []
    fields_by_anchor: dict[str, set[str]] = defaultdict(set)
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        for field in TOOL_FIELDS:
            for anchor in anchors_from_tool_field(field, tool.get(field)):
                fields_by_anchor[anchor].add(f"simulation.tools[].{field}")
    return [
        Anchor(anchor, tuple(sorted(source_fields)))
        for anchor, source_fields in sorted(fields_by_anchor.items())
    ]


def has_explicit_mapping_linkage(metadata: dict[str, Any]) -> bool:
    simulation = metadata.get("simulation", {})
    tools = simulation.get("tools", []) if isinstance(simulation, dict) else []
    mappings = metadata.get("attack_mappings", [])
    tool_link = any(
        isinstance(tool, dict) and bool(set(tool) & MAPPING_KEYS_ON_TOOL)
        for tool in tools
    )
    mapping_link = any(
        isinstance(mapping, dict) and bool(set(mapping) & TOOL_KEYS_ON_MAPPING)
        for mapping in mappings
    )
    return tool_link or mapping_link


def sanitized_field_name(value: Any) -> str:
    text = str(value)
    if SAFE_FIELD_NAME.fullmatch(text):
        return text
    return f"field_sha256:{sha256_bytes(text.encode('utf-8'))}"


def iter_text_fields(value: Any, prefix: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            field = sanitized_field_name(key)
            path = f"{prefix}.{field}" if prefix else field
            yield from iter_text_fields(child, path)
    elif isinstance(value, list):
        path = f"{prefix}[]" if prefix else "[]"
        for child in value:
            yield from iter_text_fields(child, path)
    elif isinstance(value, str):
        yield prefix or "<root>", value


def record_from_value(
    value: Any,
    *,
    artifact_id: str,
    member_id: str,
    record_ordinal: int,
    line_number: int | None,
    raw_bytes: bytes | None = None,
) -> Record:
    payload = raw_bytes if raw_bytes is not None else canonical_record_bytes(value)
    return Record(
        artifact_id=artifact_id,
        member_id=member_id,
        record_ordinal=record_ordinal,
        line_number=line_number,
        value=value,
        record_sha256=sha256_bytes(payload),
        record_hash_basis=("raw_jsonl_line" if raw_bytes is not None else "canonical_json"),
    )


def records_from_document(
    document: Any,
    *,
    artifact_id: str,
    member_id: str,
) -> Iterator[Record]:
    if isinstance(document, list):
        values = document
    elif isinstance(document, dict):
        list_candidates: list[list[Any]] = []

        def collect_record_lists(value: Any, depth: int = 0) -> None:
            if depth > 6:
                return
            if isinstance(value, list):
                if value and all(isinstance(item, dict) for item in value):
                    list_candidates.append(value)
                return
            if isinstance(value, dict):
                for child in value.values():
                    collect_record_lists(child, depth + 1)

        collect_record_lists(document)
        values = max(list_candidates, key=len) if list_candidates else [document]
    else:
        values = [document]
    for ordinal, value in enumerate(values, start=1):
        yield record_from_value(
            value,
            artifact_id=artifact_id,
            member_id=member_id,
            record_ordinal=ordinal,
            line_number=None,
        )


def records_from_json_stream(
    stream: BinaryIO,
    *,
    artifact_id: str,
    member_id: str,
) -> Iterator[Record]:
    lines = enumerate(stream, start=1)

    def next_nonblank() -> tuple[int, bytes] | None:
        for line_number, raw_line in lines:
            if raw_line.strip():
                return line_number, raw_line
        return None

    first_item = next_nonblank()
    if first_item is None:
        return
    first_line_number, first = first_item
    second_item = next_nonblank()
    second_line_number, second = second_item if second_item is not None else (None, b"")

    first_value: Any | None = None
    second_value: Any | None = None
    try:
        first_value = json.loads(first)
        if second:
            second_value = json.loads(second)
    except (json.JSONDecodeError, UnicodeDecodeError):
        first_value = None
        second_value = None

    if isinstance(first_value, dict) and (not second or isinstance(second_value, dict)):
        ordinal = 1
        yield record_from_value(
            first_value,
            artifact_id=artifact_id,
            member_id=member_id,
            record_ordinal=ordinal,
            line_number=first_line_number,
            raw_bytes=first.rstrip(b"\r\n"),
        )
        if second:
            ordinal += 1
            yield record_from_value(
                second_value,
                artifact_id=artifact_id,
                member_id=member_id,
                record_ordinal=ordinal,
                line_number=second_line_number,
                raw_bytes=second.rstrip(b"\r\n"),
            )
        for line_number, raw_line in lines:
            if not raw_line.strip():
                continue
            try:
                value = json.loads(raw_line)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise ValueError("Malformed JSONL record without payload disclosure") from exc
            ordinal += 1
            yield record_from_value(
                value,
                artifact_id=artifact_id,
                member_id=member_id,
                record_ordinal=ordinal,
                line_number=line_number,
                raw_bytes=raw_line.rstrip(b"\r\n"),
            )
        return

    payload = first + second + b"".join(raw_line for _, raw_line in lines)
    try:
        document = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Malformed JSON document without payload disclosure") from exc
    yield from records_from_document(
        document,
        artifact_id=artifact_id,
        member_id=member_id,
    )


def iter_scenario_records(
    scenario_dir: Path,
    key: bytes,
) -> Iterator[Record]:
    for artifact in sorted(scenario_dir.glob("*.zip")):
        artifact_key = f"{scenario_dir.name}/{artifact.name}"
        artifact_id = commitment(key, "artifact-path", artifact_key)
        try:
            archive = zipfile.ZipFile(artifact)
        except zipfile.BadZipFile as exc:
            raise ValueError("Invalid source archive without path disclosure") from exc
        with archive:
            for member in sorted(archive.infolist(), key=lambda item: item.filename):
                if member.is_dir() or Path(member.filename).suffix.casefold() not in {
                    ".json",
                    ".jsonl",
                    ".ndjson",
                }:
                    continue
                member_id = commitment(
                    key,
                    "archive-member",
                    f"{artifact_key}/{member.filename}",
                )
                with archive.open(member) as stream:
                    for record in records_from_json_stream(
                        stream,
                        artifact_id=artifact_id,
                        member_id=member_id,
                    ):
                        yield record


def compile_anchor_pattern(anchors: Iterable[str]) -> AnchorMatcher | None:
    ordered = sorted(set(anchors), key=lambda value: (-len(value), value))
    if not ordered:
        return None
    alternatives = [
        rf"(?<![A-Za-z0-9])(?P<A{index}>{re.escape(anchor)})(?![A-Za-z0-9])"
        for index, anchor in enumerate(ordered)
    ]
    return AnchorMatcher(
        pattern=re.compile("|".join(alternatives), re.IGNORECASE),
        anchor_by_group={
            f"A{index}": anchor for index, anchor in enumerate(ordered)
        },
    )


def matched_anchors_by_field(
    record: Any,
    matcher: AnchorMatcher | None,
) -> dict[str, set[str]]:
    if matcher is None:
        return {}
    fields: dict[str, set[str]] = defaultdict(set)
    for field_path, text in iter_text_fields(record):
        for match in matcher.pattern.finditer(text):
            group = match.lastgroup
            if group is not None:
                fields[matcher.anchor_by_group[group]].add(field_path)
    return fields


def load_metadata(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError("Malformed OTRF metadata without value disclosure") from exc
    if not isinstance(value, dict):
        raise ValueError("OTRF metadata root must be an object")
    return value


def audit_compound_scenarios(
    compound_root: Path,
    scenarios: list[ScenarioSpec],
    *,
    commitment_key: bytes,
    max_records_per_anchor: int = 5,
) -> dict[str, Any]:
    if not commitment_key:
        raise ValueError("A non-empty private commitment key is required")
    if max_records_per_anchor < 1:
        raise ValueError("max_records_per_anchor must be positive")
    if not scenarios or all(item.comparison_only for item in scenarios):
        raise ValueError("At least one non-comparison scenario is required")
    all_case_ids = [item.case_id for item in scenarios]
    if len(all_case_ids) != len(set(all_case_ids)):
        raise ValueError("Internal scenario identifiers must be unique")
    scenario_names = [item.scenario_name for item in scenarios]
    if len(scenario_names) != len(set(scenario_names)):
        raise ValueError("OTRF scenarios must be unique")
    if any(
        Path(name).is_absolute()
        or len(Path(name).parts) != 1
        or any(part in {"", ".", ".."} for part in Path(name).parts)
        for name in scenario_names
    ):
        raise ValueError("Invalid OTRF scenario identifier")
    case_ids = [item.case_id for item in scenarios if not item.comparison_only]

    metadata_by_case: dict[str, dict[str, Any]] = {}
    anchors_by_case: dict[str, list[Anchor]] = {}
    all_anchor_values: set[str] = set()
    scenario_by_case = {item.case_id: item for item in scenarios}
    for spec in scenarios:
        metadata_path = compound_root / "_metadata" / f"{spec.scenario_name}.yaml"
        scenario_dir = compound_root / spec.scenario_name
        if not metadata_path.is_file() or not scenario_dir.is_dir():
            raise ValueError("A requested OTRF scenario is incomplete")
        metadata = load_metadata(metadata_path)
        anchors = extract_anchors(metadata)
        metadata_by_case[spec.case_id] = metadata
        anchors_by_case[spec.case_id] = anchors
        all_anchor_values.update(anchor.normalized for anchor in anchors)

    pattern = compile_anchor_pattern(all_anchor_values)
    hit_counts: dict[str, int] = defaultdict(int)
    hit_cases: dict[str, set[str]] = defaultdict(set)
    retained_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    parsed_records: dict[str, int] = defaultdict(int)
    artifact_digests: dict[str, set[str]] = defaultdict(set)

    for spec in scenarios:
        scenario_dir = compound_root / spec.scenario_name
        artifact_digests[spec.case_id].update(
            file_sha256(path) for path in sorted(scenario_dir.glob("*.zip"))
        )
        for record in iter_scenario_records(scenario_dir, commitment_key):
            parsed_records[spec.case_id] += 1
            matched = matched_anchors_by_field(record.value, pattern)
            for anchor, field_paths in matched.items():
                hit_counts[anchor] += 1
                hit_cases[anchor].add(spec.case_id)
                if len(retained_records[anchor]) <= max_records_per_anchor:
                    retained_records[anchor].append(
                        {
                            "case_id": spec.case_id,
                            "artifact_id": record.artifact_id,
                            "archive_member_id": record.member_id,
                            "record_ordinal": record.record_ordinal,
                            "line_number": record.line_number,
                            "record_sha256": record.record_sha256,
                            "record_hash_basis": record.record_hash_basis,
                            "matched_field_names": sorted(field_paths),
                        }
                    )

    case_reports: list[dict[str, Any]] = []
    for case_id in case_ids:
        metadata = metadata_by_case[case_id]
        anchors = anchors_by_case[case_id]
        rare_anchors = [
            anchor
            for anchor in anchors
            if 0 < hit_counts[anchor.normalized] <= max_records_per_anchor
            and hit_cases[anchor.normalized] == {case_id}
        ]
        anchor_reports = []
        for anchor in rare_anchors:
            anchor_id = commitment(commitment_key, "anchor", anchor.normalized)
            anchor_reports.append(
                {
                    "anchor_id": anchor_id,
                    "metadata_source_fields": list(anchor.source_fields),
                    "record_hit_count": hit_counts[anchor.normalized],
                    "cross_scenario_hit_count": len(hit_cases[anchor.normalized]),
                    "records": retained_records[anchor.normalized],
                }
            )
        mapping_linkage = has_explicit_mapping_linkage(metadata)
        attack_mappings = metadata.get("attack_mappings", [])
        if not isinstance(attack_mappings, list):
            attack_mappings = []
        simulation = metadata.get("simulation", {})
        tools = simulation.get("tools", []) if isinstance(simulation, dict) else []
        if not isinstance(tools, list):
            tools = []
        blockers: list[str] = []
        if not rare_anchors:
            blockers.append("no_cross_scenario_unique_low_frequency_record_anchor")
        if not mapping_linkage:
            blockers.append("no_explicit_tool_to_attack_mapping_linkage")
        case_reports.append(
            {
                "case_id": case_id,
                "metadata_sha256": file_sha256(
                    compound_root
                    / "_metadata"
                    / f"{scenario_by_case[case_id].scenario_name}.yaml"
                ),
                "source_artifact_sha256": sorted(artifact_digests[case_id]),
                "parsed_record_count": parsed_records[case_id],
                "structured_tool_count": len(tools),
                "attack_mapping_count": len(attack_mappings),
                "candidate_anchor_count": len(anchors),
                "rare_anchor_count": len(rare_anchors),
                "record_anchor_gate_passed": bool(rare_anchors),
                "explicit_mapping_linkage_present": mapping_linkage,
                "automatic_case_bundle_ready": bool(rare_anchors) and mapping_linkage,
                "source_specific_blockers": blockers,
                "rare_anchors": anchor_reports,
            }
        )

    return {
        "audit_id": "project05-otrf-high-precision-record-anchor-audit-v0.3",
        "status": "complete",
        "scope": "isolated curator; metadata-derived rare record anchors only",
        "eligible_case_count": len(case_ids),
        "comparison_scenario_count": sum(item.comparison_only for item in scenarios),
        "max_records_per_anchor": max_records_per_anchor,
        "case_reports": case_reports,
        "automatic_case_bundle_ready_count": sum(
            item["automatic_case_bundle_ready"] for item in case_reports
        ),
        "payload_values_disclosed": False,
        "anchor_values_disclosed": False,
        "snippets_disclosed": False,
        "timestamps_or_host_values_disclosed": False,
        "attack_label_values_disclosed": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened": False,
        "planner_or_model_executed": False,
        "one_shot_evaluation_consumed": False,
    }


def parse_scenario(value: str, comparison_only: bool) -> ScenarioSpec:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Scenario must be CASE_ID=SOURCE_DIRECTORY")
    case_id, scenario_name = value.split("=", 1)
    scenario_path = Path(scenario_name)
    if (
        not case_id
        or not scenario_name
        or scenario_path.is_absolute()
        or len(scenario_path.parts) != 1
        or any(part in {"", ".", ".."} for part in scenario_path.parts)
    ):
        raise argparse.ArgumentTypeError("Invalid scenario specification")
    return ScenarioSpec(case_id, scenario_name, comparison_only=comparison_only)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compound-root", type=Path, required=True)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--comparison", action="append", default=[])
    parser.add_argument("--commitment-key-file", type=Path, required=True)
    parser.add_argument("--max-records-per-anchor", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    scenarios = [parse_scenario(value, False) for value in args.case]
    scenarios.extend(parse_scenario(value, True) for value in args.comparison)
    report = audit_compound_scenarios(
        args.compound_root,
        scenarios,
        commitment_key=args.commitment_key_file.read_bytes(),
        max_records_per_anchor=args.max_records_per_anchor,
    )
    write_json(args.output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "eligible_case_count": report["eligible_case_count"],
                "automatic_case_bundle_ready_count": report[
                    "automatic_case_bundle_ready_count"
                ],
                "payload_values_disclosed": False,
                "model_outputs_opened": False,
                "one_shot_evaluation_consumed": False,
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
