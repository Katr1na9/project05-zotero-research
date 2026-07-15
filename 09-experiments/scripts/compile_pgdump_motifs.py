#!/usr/bin/env python3
"""Compile bounded PIDSMaker PGDMP events into auditable motif claims."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable


EVENT_COLUMNS = (
    "src_node",
    "src_index_id",
    "operation",
    "dst_node",
    "dst_index_id",
    "event_uuid",
    "timestamp_rec",
    "_id",
)


def load_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def load_event_rows(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("rb") as handle:
        for line_number, row in enumerate(handle, start=1):
            columns = row.rstrip(b"\r\n").split(b"\t")
            if len(columns) != len(EVENT_COLUMNS):
                raise ValueError(
                    f"{path}:{line_number}: expected {len(EVENT_COLUMNS)} "
                    f"COPY columns, found {len(columns)}"
                )
            yield {
                "src_node": columns[0].decode("ascii"),
                "operation": columns[2].decode("utf-8"),
                "dst_node": columns[3].decode("ascii"),
                "event_uuid": columns[5].decode("ascii"),
                "timestamp_nanos": int(columns[6]),
                "event_row_id": int(columns[7]),
            }


def build_node_lookup(nodes_path: Path) -> dict[str, dict[str, Any]]:
    return {
        node["hash_id"]: node
        for node in load_jsonl(nodes_path)
    }


def normalized_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        values = [values]
    return {
        str(value).casefold()
        for value in values
        if value is not None
    }


def event_context(
    event: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Collect path, process, and endpoint observables for an event edge."""

    processes: set[str] = set()
    paths: set[str] = set()
    remote_ips: set[str] = set()

    for node_hash in (event["src_node"], event["dst_node"]):
        node = nodes.get(node_hash)
        if not node:
            continue
        node_type = node.get("node_type")
        if node_type == "subject":
            for field in ("path", "cmd"):
                value = node.get(field)
                if value:
                    processes.add(str(value))
        elif node_type == "file":
            path = node.get("path")
            if path:
                paths.add(str(path))
        elif node_type == "netflow":
            for field in ("src_addr", "dst_addr"):
                value = node.get(field)
                if value:
                    remote_ips.add(str(value))

    return {
        "event_type": event["operation"],
        "process": sorted(processes),
        "path": sorted(paths),
        "remote_ip": sorted(remote_ips),
        "src_node": event["src_node"],
        "dst_node": event["dst_node"],
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
        if not normalized_set(context.get(field)).intersection(
            normalized_set(rule[operator])
        ):
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
    events: Iterable[dict[str, Any]],
    nodes: dict[str, dict[str, Any]],
    spec: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compile observed motifs and retain representative event UUIDs."""

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

    for event in events:
        events_scanned += 1
        context = event_context(event, nodes)
        for motif in spec["motifs"]:
            if not matches_rule(context, motif["match"]):
                continue
            state = motif_states[motif["motif_id"]]
            state["count"] += 1
            timestamp = event["timestamp_nanos"]
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
            if len(state["representative_event_uuids"]) < 5:
                state["representative_event_uuids"].append(event["event_uuid"])

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

        claim = deepcopy(motif["claim"])
        representatives = state["representative_event_uuids"]
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
    parser = argparse.ArgumentParser(
        description="Compile bounded PIDSMaker events into motif claims."
    )
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--nodes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    claims, report = compile_motifs(
        load_event_rows(args.events),
        build_node_lookup(args.nodes),
        spec,
    )
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
