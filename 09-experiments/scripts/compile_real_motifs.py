#!/usr/bin/env python3
"""Compile bounded DARPA CDM events into auditable behavior-motif claims."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def unwrap_value(value: Any) -> Any:
    while isinstance(value, dict) and len(value) == 1:
        value = next(iter(value.values()))
    return value


def build_node_lookup(nodes_path: Path) -> dict[str, dict[str, Any]]:
    return {
        node["node_uuid"]: node
        for node in load_jsonl(nodes_path)
    }


def add_string(values: set[str], value: Any) -> None:
    value = unwrap_value(value)
    if isinstance(value, str) and value:
        values.add(value)


def event_context(
    event: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    raw = event.get("raw", {})
    properties = raw.get("properties") or {}
    properties = properties.get("map") or {}

    processes: set[str] = set()
    paths: set[str] = set()
    remote_ips: set[str] = set()
    for key in ("exec", "image_path", "process_name", "commandLine"):
        add_string(processes, properties.get(key))

    for key in ("predicateObjectPath", "predicateObject2Path"):
        add_string(paths, raw.get(key))

    referenced = [
        event.get("subject_uuid"),
        event.get("predicate_object_uuid"),
        event.get("predicate_object_2_uuid"),
    ]
    for uuid in referenced:
        node = nodes.get(uuid)
        if not node:
            continue
        node_raw = node.get("raw", {})
        for key in ("cmdLine", "path", "name"):
            add_string(processes, node_raw.get(key))
        add_string(paths, node_raw.get("path"))
        base = node_raw.get("baseObject") or {}
        base_properties = (base.get("properties") or {}).get("map") or {}
        for key in ("path", "filename"):
            add_string(paths, base.get(key))
            add_string(paths, base_properties.get(key))
        add_string(remote_ips, node_raw.get("remoteAddress"))

    return {
        "event_type": event.get("event_type"),
        "process": sorted(processes),
        "path": sorted(paths),
        "remote_ip": sorted(remote_ips),
        "subject_uuid": event.get("subject_uuid"),
        "predicate_uuid": event.get("predicate_object_uuid"),
    }


def normalized_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        values = [values]
    return {
        str(value).casefold()
        for value in values
        if value is not None
    }


def matches_rule(context: dict[str, Any], rule: dict[str, Any]) -> bool:
    exact_operators = {
        "event_type_in": "event_type",
        "process_in": "process",
        "path_in": "path",
        "remote_ip_in": "remote_ip",
    }
    contains_operators = {
        "process_contains_any": "process",
        "path_contains_any": "path",
    }
    for operator, field in exact_operators.items():
        if operator not in rule:
            continue
        actual = normalized_set(context.get(field))
        expected = normalized_set(rule[operator])
        if not actual.intersection(expected):
            return False
    for operator, field in contains_operators.items():
        if operator not in rule:
            continue
        actual = normalized_set(context.get(field))
        expected = normalized_set(rule[operator])
        if not any(
            needle in value
            for value in actual
            for needle in expected
        ):
            return False
    return True


def compile_motifs(
    events_path: Path,
    nodes_path: Path,
    spec: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    nodes = build_node_lookup(nodes_path)
    motif_states = {
        motif["motif_id"]: {
            "count": 0,
            "first_timestamp_nanos": None,
            "last_timestamp_nanos": None,
            "representative_event_uuids": [],
        }
        for motif in spec["motifs"]
    }
    events_scanned = 0

    for event in load_jsonl(events_path):
        events_scanned += 1
        context = event_context(event, nodes)
        for motif in spec["motifs"]:
            if not matches_rule(context, motif["match"]):
                continue
            state = motif_states[motif["motif_id"]]
            state["count"] += 1
            timestamp = event.get("timestamp_nanos")
            if timestamp is not None:
                if (
                    state["first_timestamp_nanos"] is None
                    or timestamp < state["first_timestamp_nanos"]
                ):
                    state["first_timestamp_nanos"] = timestamp
                if (
                    state["last_timestamp_nanos"] is None
                    or timestamp > state["last_timestamp_nanos"]
                ):
                    state["last_timestamp_nanos"] = timestamp
            event_uuid = event.get("event_uuid")
            if (
                event_uuid
                and len(state["representative_event_uuids"]) < 5
            ):
                state["representative_event_uuids"].append(event_uuid)

    claims: list[dict[str, Any]] = []
    report_motifs: dict[str, Any] = {}
    for motif in spec["motifs"]:
        motif_id = motif["motif_id"]
        state = motif_states[motif_id]
        if state["count"] == 0:
            report_motifs[motif_id] = {
                "status": "not_observed",
                "matched_event_count": 0,
                "representative_event_uuids": [],
            }
            continue

        representatives = state["representative_event_uuids"]
        claim = deepcopy(motif["claim"])
        claim["claim_id"] = motif_id
        claim["case_id"] = spec["case_id"]
        claim["source_pointer"] = {
            "artifact_id": spec["artifact_id"],
            "record_id": representatives[0],
        }
        audit_note = (
            f"matched_event_count={state['count']}; "
            f"first_timestamp_nanos={state['first_timestamp_nanos']}; "
            f"last_timestamp_nanos={state['last_timestamp_nanos']}; "
            "representative_event_uuids="
            + ",".join(representatives)
        )
        if claim.get("notes"):
            audit_note = f"{claim['notes']} {audit_note}"
        claim["notes"] = audit_note
        claims.append(claim)
        report_motifs[motif_id] = {
            "status": "observed",
            "matched_event_count": state["count"],
            "first_timestamp_nanos": state["first_timestamp_nanos"],
            "last_timestamp_nanos": state["last_timestamp_nanos"],
            "representative_event_uuids": representatives,
        }

    report = {
        "case_id": spec["case_id"],
        "artifact_id": spec["artifact_id"],
        "events_scanned": events_scanned,
        "nodes_loaded": len(nodes),
        "motifs_requested": len(spec["motifs"]),
        "motifs_observed": len(claims),
        "motifs": report_motifs,
    }
    return claims, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--nodes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    claims, report = compile_motifs(args.events, args.nodes, spec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(claims, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path = args.report or args.output.with_name("motif_report.json")
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Compiled {len(claims)}/{len(spec['motifs'])} motifs "
        f"from {report['events_scanned']} events"
    )


if __name__ == "__main__":
    main()
