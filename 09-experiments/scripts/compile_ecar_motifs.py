#!/usr/bin/env python3
"""Compile bounded OpTC eCAR events into auditable motif claims."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


EXACT_MATCH_OPERATORS = {
    "object_in": "object",
    "action_in": "action",
    "event_type_in": "event_type",
    "hostname_in": "hostname",
    "process_in": "process",
    "path_in": "path",
    "remote_ip_in": "remote_ip",
}
CONTAINS_MATCH_OPERATORS = {
    "hostname_contains_any": "hostname",
    "process_contains_any": "process",
    "path_contains_any": "path",
    "remote_ip_contains_any": "remote_ip",
    "property_contains_any": "property",
}
ALLOWED_MATCH_OPERATORS = frozenset(
    {*EXACT_MATCH_OPERATORS, *CONTAINS_MATCH_OPERATORS}
)


def load_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def normalized_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        values = [values]
    return {str(value).casefold() for value in values if value is not None}


def validate_match_rule(rule: Any) -> None:
    if not isinstance(rule, dict):
        raise ValueError("motif match must be an object")
    if not rule:
        raise ValueError("motif match must contain at least one operator")
    unknown = set(rule).difference(ALLOWED_MATCH_OPERATORS)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"unknown match operator(s): {names}")


def validate_motif_spec(spec: Any) -> list[dict[str, Any]]:
    if not isinstance(spec, dict):
        raise ValueError("motif spec must be an object")
    for field in ("case_id", "artifact_id"):
        value = spec.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"motif spec requires a non-empty {field}")

    motifs = spec.get("motifs")
    if not isinstance(motifs, list) or not motifs:
        raise ValueError("motif spec requires a non-empty motifs list")

    seen_ids: set[str] = set()
    for index, motif in enumerate(motifs):
        if not isinstance(motif, dict):
            raise ValueError(f"motif at index {index} must be an object")
        motif_id = motif.get("motif_id")
        if not isinstance(motif_id, str) or not motif_id.strip():
            raise ValueError(f"motif at index {index} requires a non-empty motif_id")
        if motif_id in seen_ids:
            raise ValueError(f"duplicate motif_id: {motif_id}")
        seen_ids.add(motif_id)
        validate_match_rule(motif.get("match"))
        if not isinstance(motif.get("claim"), dict):
            raise ValueError(f"motif {motif_id} claim must be an object")
    return motifs


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def event_timestamp_utc(event: dict[str, Any]) -> datetime:
    raw = event["timestamp"]
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw) / 1000.0, tz=timezone.utc)
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(f"naive eCAR timestamp: {raw}")
    return parsed.astimezone(timezone.utc)


def event_context(event: dict[str, Any]) -> dict[str, Any]:
    """Flatten eCAR object/action/properties into matchable fields."""

    properties = event.get("properties") or {}
    if not isinstance(properties, dict):
        properties = {}

    processes: set[str] = set()
    paths: set[str] = set()
    remote_ips: set[str] = set()
    property_blobs: set[str] = set()

    for field in ("image_path", "command_line", "parent_image_path"):
        value = properties.get(field)
        if value:
            processes.add(str(value))
    for field in (
        "image_path",
        "file_path",
        "path",
        "name",
        "key",
        "module_path",
    ):
        value = properties.get(field)
        if value:
            paths.add(str(value))
    for field in ("src_ip", "dest_ip", "dst_ip"):
        value = properties.get(field)
        if value:
            remote_ips.add(str(value))
    for key, value in properties.items():
        property_blobs.add(f"{key}={value}")

    object_name = str(event.get("object") or "")
    action_name = str(event.get("action") or "")
    return {
        "event_id": str(event.get("id") or ""),
        "hostname": str(event.get("hostname") or ""),
        "object": object_name,
        "action": action_name,
        "event_type": f"{object_name}:{action_name}",
        "process": sorted(processes),
        "path": sorted(paths),
        "remote_ip": sorted(remote_ips),
        "property": sorted(property_blobs),
        "timestamp_utc": utc_iso(event_timestamp_utc(event)),
    }


def matches_rule(
    context: dict[str, Any],
    rule: dict[str, Any],
    *,
    already_validated: bool = False,
) -> bool:
    if not already_validated:
        validate_match_rule(rule)

    for operator, field in EXACT_MATCH_OPERATORS.items():
        if operator not in rule:
            continue
        actual = context.get(field)
        if isinstance(actual, list):
            haystack = normalized_set(actual)
        else:
            haystack = normalized_set([actual])
        if not haystack.intersection(normalized_set(rule[operator])):
            return False

    for operator, field in CONTAINS_MATCH_OPERATORS.items():
        if operator not in rule:
            continue
        actual = context.get(field)
        if isinstance(actual, list):
            haystack = normalized_set(actual)
        else:
            haystack = normalized_set([actual])
        needles = normalized_set(rule[operator])
        if not any(needle in value for value in haystack for needle in needles):
            return False
    return True


def compile_motifs(
    events: Iterable[dict[str, Any]],
    spec: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    motifs = validate_motif_spec(spec)

    motif_states = {
        motif["motif_id"]: {
            "count": 0,
            "first_timestamp": None,
            "last_timestamp": None,
            "representative_event_ids": [],
        }
        for motif in motifs
    }
    events_scanned = 0

    for event in events:
        events_scanned += 1
        context = event_context(event)
        for motif in motifs:
            if not matches_rule(
                context,
                motif["match"],
                already_validated=True,
            ):
                continue
            state = motif_states[motif["motif_id"]]
            state["count"] += 1
            stamp = event_timestamp_utc(event)
            if state["first_timestamp"] is None or stamp < state["first_timestamp"]:
                state["first_timestamp"] = stamp
            if state["last_timestamp"] is None or stamp > state["last_timestamp"]:
                state["last_timestamp"] = stamp
            event_id = context["event_id"]
            if event_id and len(state["representative_event_ids"]) < 5:
                state["representative_event_ids"].append(event_id)

    claims: list[dict[str, Any]] = []
    report_motifs: dict[str, Any] = {}
    for motif in motifs:
        motif_id = motif["motif_id"]
        state = motif_states[motif_id]
        if state["count"] == 0:
            report_motifs[motif_id] = {
                "status": "not_observed",
                "matched_event_count": 0,
                "representative_event_ids": [],
            }
            continue

        claim = deepcopy(motif["claim"])
        representatives = state["representative_event_ids"]
        claim["claim_id"] = motif_id
        claim["case_id"] = spec["case_id"]
        claim["source_pointer"] = {
            "artifact_id": spec["artifact_id"],
            "record_id": representatives[0] if representatives else "",
        }
        first_timestamp_utc = utc_iso(state["first_timestamp"])
        last_timestamp_utc = utc_iso(state["last_timestamp"])
        audit_note = (
            f"matched_event_count={state['count']}; "
            f"first_timestamp_utc={first_timestamp_utc}; "
            f"last_timestamp_utc={last_timestamp_utc}; "
            "representative_event_ids="
            + ",".join(representatives)
        )
        if claim.get("notes"):
            audit_note = f"{claim['notes']} {audit_note}"
        claim["notes"] = audit_note
        claims.append(claim)
        report_motifs[motif_id] = {
            "status": "observed",
            "matched_event_count": state["count"],
            "first_timestamp_utc": first_timestamp_utc,
            "last_timestamp_utc": last_timestamp_utc,
            "representative_event_ids": representatives,
        }

    report = {
        "case_id": spec["case_id"],
        "artifact_id": spec["artifact_id"],
        "events_scanned": events_scanned,
        "motifs_requested": len(spec["motifs"]),
        "motifs_observed": len(claims),
        "motifs": report_motifs,
    }
    return claims, report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile bounded OpTC eCAR events into motif claims."
    )
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    claims, report = compile_motifs(load_jsonl(args.events), spec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(claims, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(
        f"Compiled {report['motifs_observed']}/{report['motifs_requested']} "
        f"motifs from {report['events_scanned']} events"
    )


if __name__ == "__main__":
    main()
