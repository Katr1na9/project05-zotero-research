#!/usr/bin/env python3
"""Probe only preregistered OTRF motif anchors in a host JSONL archive."""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


def canonical_host(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "<missing>"
    return value.split(".", 1)[0].upper()


def provider_family(event: dict[str, Any]) -> str:
    channel = str(event.get("Channel", "")).casefold()
    source = str(event.get("SourceName", "")).casefold()
    combined = f"{channel} {source}"
    if "powershell" in combined:
        return "powershell"
    if "wmi-activity" in combined:
        return "wmi"
    if "sysmon" in combined:
        return "sysmon"
    if "security" in channel or "security-auditing" in source:
        return "security"
    if channel == "system" or "service control manager" in source:
        return "system"
    return "other"


def evidence_component(event: dict[str, Any]) -> str:
    event_id = str(event.get("EventID", ""))
    mapping = {
        "1": "process_creation",
        "3": "network_connection",
        "11": "file_creation",
        "12": "registry_create_delete",
        "13": "registry_value_set",
        "14": "registry_rename",
        "23": "file_delete",
        "4103": "powershell_module",
        "4104": "powershell_script_block",
        "4657": "registry_value_change",
        "4663": "object_access",
        "4688": "process_creation",
        "4697": "service_install",
        "5156": "network_connection",
        "7045": "service_install",
    }
    return mapping.get(event_id, f"event_{event_id or 'missing'}")


def searchable_values(
    event: dict[str, Any],
    fields: list[str],
) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for field in fields:
        value = event.get(field)
        if isinstance(value, (str, int, float)):
            values.append((field, str(value)))
    return values


def snippet(value: str, term: str, radius: int = 100) -> str:
    folded = value.casefold()
    index = folded.find(term.casefold())
    if index < 0:
        return value[: radius * 2]
    start = max(0, index - radius)
    end = min(len(value), index + len(term) + radius)
    compact = value[start:end].replace("\r", " ").replace("\n", " ")
    return " ".join(compact.split())


def record_locator(event: dict[str, Any], line_number: int) -> str:
    return "|".join(
        [
            canonical_host(event.get("Hostname")),
            str(event.get("Channel", "<missing>")),
            str(event.get("RecordNumber", "<missing>")),
            str(event.get("EventID", "<missing>")),
            f"line:{line_number}",
        ]
    )


def probe_archive(
    archive_path: Path,
    spec: dict[str, Any],
    *,
    max_records_per_node: int = 30,
) -> dict[str, Any]:
    fields = list(spec["searchable_fields"])
    nodes = {node["node_id"]: node for node in spec["nodes"]}
    expected_hosts = {
        node_id: {canonical_host(value) for value in node["expected_hosts"]}
        for node_id, node in nodes.items()
    }
    matched_records: dict[str, dict[str, dict[str, Any]]] = {
        node_id: {} for node_id in nodes
    }
    matched_anchors: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    parsed_rows = 0
    malformed_rows = 0

    with zipfile.ZipFile(archive_path) as archive:
        file_members = [item for item in archive.infolist() if not item.is_dir()]
        if len(file_members) != 1:
            raise ValueError(f"Expected one JSONL member, found {len(file_members)}")
        if file_members[0].filename != spec["host_archive_member"]:
            raise ValueError("Archive member does not match frozen motif spec")
        with archive.open(file_members[0]) as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                if not raw_line.strip():
                    continue
                try:
                    event = json.loads(raw_line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    malformed_rows += 1
                    continue
                parsed_rows += 1
                host = canonical_host(event.get("Hostname"))
                values = searchable_values(event, fields)
                folded_values = [(field, value, value.casefold()) for field, value in values]

                for node_id, node in nodes.items():
                    if host not in expected_hosts[node_id]:
                        continue
                    record_matches: list[dict[str, str]] = []
                    for anchor in node["anchors"]:
                        for term in anchor["terms"]:
                            term_folded = term.casefold()
                            found = next(
                                (
                                    (field, value)
                                    for field, value, folded in folded_values
                                    if term_folded in folded
                                ),
                                None,
                            )
                            if found is None:
                                continue
                            matched_anchors[node_id].add(anchor["anchor_id"])
                            record_matches.append(
                                {
                                    "anchor_id": anchor["anchor_id"],
                                    "term": term,
                                    "field": found[0],
                                    "snippet": snippet(found[1], term),
                                }
                            )
                    if not record_matches:
                        continue

                    locator = record_locator(event, line_number)
                    if locator not in matched_records[node_id]:
                        matched_records[node_id][locator] = {
                            "record_locator": locator,
                            "timestamp_utc": event.get("@timestamp"),
                            "hostname": event.get("Hostname"),
                            "channel": event.get("Channel"),
                            "source_name": event.get("SourceName"),
                            "event_id": event.get("EventID"),
                            "record_number": event.get("RecordNumber"),
                            "provider_family": provider_family(event),
                            "evidence_component": evidence_component(event),
                            "matches": record_matches,
                        }
                    else:
                        matched_records[node_id][locator]["matches"].extend(
                            record_matches
                        )

    node_summaries: list[dict[str, Any]] = []
    passing_nodes = 0
    for node_id, node in nodes.items():
        records = list(matched_records[node_id].values())
        family_counts = Counter(record["provider_family"] for record in records)
        anchor_family_counts: Counter[str] = Counter()
        representative_by_anchor_family: dict[str, dict[str, Any]] = {}
        for record in records:
            record_anchor_ids = {
                match["anchor_id"] for match in record["matches"]
            }
            for anchor_id in record_anchor_ids:
                key = f"{anchor_id}|{record['provider_family']}"
                anchor_family_counts[key] += 1
                representative_by_anchor_family.setdefault(key, record)
        counted_families = sorted(
            family for family in family_counts if family != "other"
        )
        anchor_ids = {anchor["anchor_id"] for anchor in node["anchors"]}
        node_pass = (
            bool(matched_anchors[node_id])
            and len(counted_families)
            >= node["minimum_distinct_provider_families"]
        )
        if node_pass and node["critical"]:
            passing_nodes += 1
        node_summaries.append(
            {
                "node_id": node_id,
                "critical": bool(node["critical"]),
                "matched_record_count": len(records),
                "matched_anchor_ids": sorted(matched_anchors[node_id]),
                "missing_anchor_ids": sorted(anchor_ids - matched_anchors[node_id]),
                "provider_family_counts": dict(sorted(family_counts.items())),
                "anchor_provider_family_counts": dict(
                    sorted(anchor_family_counts.items())
                ),
                "counted_provider_families": counted_families,
                "minimum_distinct_provider_families": node[
                    "minimum_distinct_provider_families"
                ],
                "multiclaim_node_pass": node_pass,
                "representative_by_anchor_provider_family": [
                    {
                        "anchor_provider_family": key,
                        "record": representative_by_anchor_family[key],
                    }
                    for key in sorted(representative_by_anchor_family)
                ],
                "representative_records": records[:max_records_per_node],
            }
        )

    required = spec["gate"]["minimum_passing_critical_nodes"]
    return {
        "case_id": spec["case_id"],
        "motif_spec_version": spec["spec_version"],
        "inspection_scope": "frozen anchors and searchable fields only",
        "parsed_rows": parsed_rows,
        "malformed_rows": malformed_rows,
        "passing_critical_node_count": passing_nodes,
        "required_passing_critical_node_count": required,
        "d3_multiclaim_gate": "PASS" if passing_nodes >= required else "FAIL",
        "nodes": node_summaries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-records-per-node", type=int, default=30)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    result = probe_archive(
        args.archive,
        spec,
        max_records_per_node=args.max_records_per_node,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output}: D3={result['d3_multiclaim_gate']}")


if __name__ == "__main__":
    main()
