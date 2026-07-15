#!/usr/bin/env python3
"""Build deterministic, physically separated LLM evaluation packets."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Literal
from xml.etree import ElementTree


FORBIDDEN_PUBLIC_KEYS = {
    "acceptable_observations",
    "canonical_claim_id",
    "claim_id",
    "gold_claim_id",
    "recoverable_claim_ids",
    "required_claim_ids",
}

PACKET_SEED = 2026071501
NULL_SEED = 2026071502
PUBLIC_CASE_SUFFIX = "evaluation-case"
CASE_LAYOUT = {
    "C04": ("development", "e3", "R01"),
    "C05": ("development", "e3", "R02"),
    "C06": ("development", "e3", "R03"),
    "C07": ("test", "pgdump", "R04"),
    "C08": ("test", "pgdump", "R05"),
    "C09": ("test", "ecar", "R06"),
    "C10": ("test", "ecar", "R07"),
    "C11": ("test", "otrf", "R08"),
    "C12": ("test", "witfoo", "R09"),
}
FAMILY_SOURCE_TYPES = {
    "e3": "darpa_cdm_event",
    "pgdump": "pidsmaker_pgdmp_event",
    "ecar": "optc_ecar_event",
    "otrf": "otrf_windows_event",
    "witfoo": "witfoo_incident_lead",
}
PGDMP_COLUMNS = (
    "src_node",
    "src_index_id",
    "operation",
    "dst_node",
    "dst_index_id",
    "event_uuid",
    "timestamp_nanos",
    "event_row_id",
)
FORBIDDEN_SOURCE_KEY_PARTS = (
    "attack",
    "actor",
    "campaign",
    "claim_id",
    "confidence",
    "mapped_tactic",
    "mapped_technique",
    "motif_id",
    "notes",
    "target",
)
PROJECT_ID_PATTERN = re.compile(r"\bC(?:0[4-9]|1[0-2])-(?:EC|MC)-\d+\b", re.I)
TECHNIQUE_PATTERN = re.compile(r"\bT\d{4}(?:\.\d{3})?\b", re.I)
SENSITIVE_LABEL_PATTERN = re.compile(r"\b(?:apt29|actor|campaign)\b", re.I)
_CASE_RECORD_CACHE: dict[
    tuple[str, str], tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]
] = {}
_NULL_REVIEW_FLAGS: dict[str, set[str]] = {}


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def digest_id(prefix: str, payload: bytes) -> str:
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:24].upper()}"


def derive_request_id(public_body: dict[str, Any]) -> str:
    body = {key: value for key, value in public_body.items() if key != "request_id"}
    return digest_id("REQ", canonical_json(body))


def derive_candidate_claim_id(
    request_id: str,
    condition_id: str,
    attempt_index: int,
    output_index: int,
) -> str:
    payload = (
        f"{request_id}|{condition_id}|{attempt_index}|{output_index}".encode(
            "utf-8"
        )
    )
    return digest_id("CC", payload)


def derive_gold_claim_id(case_id: str, canonical_claim_id: str) -> str:
    return digest_id(
        "GOLD", f"{case_id}|{canonical_claim_id}".encode("utf-8")
    )


def make_packet_record(
    source_type: str,
    source_pointer: dict[str, str],
    source_payload: dict[str, Any],
) -> dict[str, Any]:
    pointer = {
        "artifact_id": str(source_pointer["artifact_id"]),
        "record_id": str(source_pointer["record_id"]),
    }
    return {
        "packet_record_id": digest_id("REC", canonical_json(pointer)),
        "source_type": str(source_type),
        "source_pointer": pointer,
        "record_sha256": sha256_bytes(canonical_json(source_payload)),
        "source_payload": source_payload,
    }


def case_prefix(case_id: str) -> str:
    prefix = str(case_id)[:3]
    if prefix not in CASE_LAYOUT:
        raise ValueError(f"unsupported Phase 1 case: {case_id}")
    return prefix


def public_case_id(case_id: str) -> str:
    return f"{case_prefix(case_id)}-{PUBLIC_CASE_SUFFIX}"


def public_artifact_id(case_id: str, slot: int = 1) -> str:
    return f"SRC-{case_prefix(case_id)}-{slot:02d}"


def scrub_public_source(value: Any) -> Any:
    """Remove constructed labels while retaining literal frozen-source fields."""

    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            folded = str(key).casefold()
            if any(part in folded for part in FORBIDDEN_SOURCE_KEY_PARTS):
                continue
            clean[str(key)] = scrub_public_source(item)
        return clean
    if isinstance(value, list):
        return [scrub_public_source(item) for item in value]
    if isinstance(value, str):
        if (
            PROJECT_ID_PATTERN.search(value)
            or TECHNIQUE_PATTERN.search(value)
            or SENSITIVE_LABEL_PATTERN.search(value)
        ):
            return "[redacted-source-label]"
    return value


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_claims(case_dir: Path) -> list[dict[str, Any]]:
    claims = load_json(case_dir / "evidence_claims.json")
    if not isinstance(claims, list) or not claims:
        raise ValueError(f"case has no evidence claims: {case_dir}")
    return sorted(claims, key=lambda item: str(item["claim_id"]))


def source_record_from_claim(
    case_id: str,
    claim_by_record_id: dict[str, dict[str, Any]],
    record_id: str,
    source_payload: dict[str, Any],
    *,
    artifact_slot: int = 1,
    null_source_type: str,
) -> dict[str, Any]:
    claim = claim_by_record_id.get(record_id)
    source_type = str(claim["source_type"]) if claim else null_source_type
    return make_packet_record(
        source_type,
        {
            "artifact_id": public_artifact_id(case_id, artifact_slot),
            "record_id": record_id,
        },
        scrub_public_source(source_payload),
    )


def null_review_flags(record: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(_NULL_REVIEW_FLAGS.get(record["packet_record_id"], set())))


def compile_bytes_pattern(values: Iterable[str]) -> re.Pattern[bytes]:
    encoded = sorted({str(value).encode("utf-8") for value in values})
    if not encoded:
        return re.compile(b"(?!)")
    return re.compile(b"(?:" + b"|".join(re.escape(value) for value in encoded) + b")")


def collect_jsonl_rows(
    path: Path,
    target_ids: set[str],
    id_field: str,
    null_count: int,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    targets: dict[str, dict[str, Any]] = {}
    null_rows: list[dict[str, Any]] = []
    target_pattern = compile_bytes_pattern(target_ids)
    with path.open("rb") as handle:
        for raw_line in handle:
            if not raw_line.strip():
                continue
            needs_null = len(null_rows) < null_count
            if not needs_null and target_pattern.search(raw_line) is None:
                continue
            row = json.loads(raw_line)
            record_id = str(row.get(id_field) or "")
            if record_id in target_ids:
                targets[record_id] = row
            elif needs_null and record_id:
                null_rows.append(row)
            if len(targets) == len(target_ids) and len(null_rows) >= null_count:
                break
    missing = sorted(target_ids.difference(targets))
    if missing:
        raise ValueError(f"records not found in {path}: {missing}")
    return targets, null_rows


def load_selected_e3_nodes(
    path: Path,
    events: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    needed = {
        str(event.get(field))
        for event in events
        for field in (
            "subject_uuid",
            "predicate_object_uuid",
            "predicate_object_2_uuid",
        )
        if event.get(field)
    }
    nodes: dict[str, dict[str, Any]] = {}
    pattern = compile_bytes_pattern(needed)
    with path.open("rb") as handle:
        for raw_line in handle:
            if pattern.search(raw_line) is None:
                continue
            node = json.loads(raw_line)
            node_id = str(node.get("node_uuid") or "")
            if node_id in needed:
                nodes[node_id] = node
            if len(nodes) == len(needed):
                break
    return nodes


def e3_payload(
    event: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    resolved = {}
    for field in (
        "subject_uuid",
        "predicate_object_uuid",
        "predicate_object_2_uuid",
    ):
        node_id = event.get(field)
        if node_id and str(node_id) in nodes:
            resolved[field] = nodes[str(node_id)]
    return {"event": event, "resolved_nodes": resolved}


def load_e3_case(
    root: Path,
    case_dir: Path,
    source_code: str,
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base = root / "09-experiments" / "real_data" / "darpa_tc_e3" / "extracted" / source_code
    claim_by_record = {
        str(claim["source_pointer"]["record_id"]): claim for claim in claims
    }
    target_rows, null_rows = collect_jsonl_rows(
        base / "events.jsonl",
        set(claim_by_record),
        "event_uuid",
        len(claims) * 3,
    )
    selected_events = [*target_rows.values(), *null_rows]
    nodes = load_selected_e3_nodes(base / "nodes.jsonl", selected_events)
    rows = []
    for event in selected_events:
        record_id = str(event["event_uuid"])
        rows.append(
            source_record_from_claim(
                str(claims[0]["case_id"]),
                claim_by_record,
                record_id,
                e3_payload(event, nodes),
                null_source_type=FAMILY_SOURCE_TYPES["e3"],
            )
        )
    return rows


def load_pgdump_nodes(path: Path) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                node = json.loads(line)
                nodes[str(node["hash_id"])] = node
    return nodes


def parse_pgdump_row(raw_line: bytes, path: Path, line_number: int) -> dict[str, Any]:
    columns = raw_line.rstrip(b"\r\n").split(b"\t")
    if len(columns) != len(PGDMP_COLUMNS):
        raise ValueError(
            f"{path}:{line_number}: expected {len(PGDMP_COLUMNS)} columns, "
            f"found {len(columns)}"
        )
    return {
        "src_node": columns[0].decode("ascii"),
        "src_index_id": int(columns[1]),
        "operation": columns[2].decode("utf-8"),
        "dst_node": columns[3].decode("ascii"),
        "dst_index_id": int(columns[4]),
        "event_uuid": columns[5].decode("ascii"),
        "timestamp_nanos": int(columns[6]),
        "event_row_id": int(columns[7]),
    }


def load_pgdump_case(
    root: Path,
    case_dir: Path,
    source_code: str,
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base = root / "09-experiments" / "real_data" / "darpa_tc_e5" / "extracted"
    event_path = base / f"{source_code}_event_table.tsv"
    nodes = load_pgdump_nodes(base / f"{source_code}_nodes.jsonl")
    claim_by_record = {
        str(claim["source_pointer"]["record_id"]): claim for claim in claims
    }
    targets: dict[str, dict[str, Any]] = {}
    null_rows: list[dict[str, Any]] = []
    target_pattern = compile_bytes_pattern(claim_by_record)
    with event_path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            needs_null = len(null_rows) < len(claims) * 3
            if not needs_null and target_pattern.search(raw_line) is None:
                continue
            event = parse_pgdump_row(raw_line, event_path, line_number)
            record_id = event["event_uuid"]
            if record_id in claim_by_record:
                targets[record_id] = event
            elif needs_null:
                null_rows.append(event)
            if len(targets) == len(claim_by_record) and len(null_rows) >= len(claims) * 3:
                break
    missing = sorted(set(claim_by_record).difference(targets))
    if missing:
        raise ValueError(f"records not found in {event_path}: {missing}")

    rows = []
    for event in [*targets.values(), *null_rows]:
        payload = {
            "event": event,
            "resolved_src_node": nodes.get(event["src_node"]),
            "resolved_dst_node": nodes.get(event["dst_node"]),
        }
        rows.append(
            source_record_from_claim(
                str(claims[0]["case_id"]),
                claim_by_record,
                event["event_uuid"],
                payload,
                null_source_type=FAMILY_SOURCE_TYPES["pgdump"],
            )
        )
    return rows


def load_ecar_case(
    root: Path,
    case_dir: Path,
    source_code: str,
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    suffix = {
        "R06": "R06_sysclient0201_window.jsonl",
        "R07": "R07_sysclient0351_window.jsonl",
    }[source_code]
    event_path = root / "09-experiments" / "real_data" / "darpa_optc" / "extracted" / suffix
    claim_by_record = {
        str(claim["source_pointer"]["record_id"]): claim for claim in claims
    }
    targets, null_rows = collect_jsonl_rows(
        event_path,
        set(claim_by_record),
        "id",
        len(claims) * 3,
    )
    rows = []
    for event in [*targets.values(), *null_rows]:
        record_id = str(event["id"])
        rows.append(
            source_record_from_claim(
                str(claims[0]["case_id"]),
                claim_by_record,
                record_id,
                {"event": event},
                null_source_type=FAMILY_SOURCE_TYPES["ecar"],
            )
        )
    return rows


def otrf_line_number(pointer: dict[str, Any]) -> int:
    match = re.search(r"\bline\s+(\d+)\b", str(pointer.get("location") or ""))
    if not match:
        raise ValueError(f"OTRF source pointer has no line number: {pointer}")
    return int(match.group(1))


def otrf_null_record_id(event: dict[str, Any], line_number: int) -> str:
    parts = (
        event.get("Computer") or event.get("Hostname") or "unknown-host",
        event.get("Channel") or event.get("SourceName") or "unknown-channel",
        event.get("RecordNumber") or "unknown-record",
        event.get("EventID") or "unknown-event",
        f"line:{line_number}",
    )
    return "|".join(str(value) for value in parts)


def load_otrf_case(
    root: Path,
    case_dir: Path,
    source_code: str,
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del case_dir, source_code
    archive_path = (
        root
        / "09-experiments"
        / "real_data"
        / "otrf_apt29"
        / "raw"
        / "apt29_evals_day1_manual.zip"
    )
    target_by_line = {
        otrf_line_number(claim["source_pointer"]): claim for claim in claims
    }
    targets: dict[int, dict[str, Any]] = {}
    null_rows: list[tuple[int, dict[str, Any]]] = []
    with zipfile.ZipFile(archive_path) as archive:
        members = [entry for entry in archive.infolist() if not entry.is_dir()]
        if len(members) != 1:
            raise ValueError(f"unexpected OTRF member count: {len(members)}")
        with archive.open(members[0]) as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                is_target = line_number in target_by_line
                needs_null = len(null_rows) < len(claims) * 3
                if not is_target and not needs_null:
                    if len(targets) == len(target_by_line) and line_number > max(target_by_line):
                        break
                    continue
                event = json.loads(raw_line)
                if is_target:
                    targets[line_number] = event
                elif needs_null:
                    null_rows.append((line_number, event))
                if (
                    len(targets) == len(target_by_line)
                    and len(null_rows) >= len(claims) * 3
                    and line_number >= max(target_by_line)
                ):
                    break
    missing = sorted(set(target_by_line).difference(targets))
    if missing:
        raise ValueError(f"OTRF lines not found: {missing}")

    case_id = str(claims[0]["case_id"])
    claim_by_record = {
        str(claim["source_pointer"]["record_id"]): claim for claim in claims
    }
    rows = []
    for line_number, claim in target_by_line.items():
        record_id = str(claim["source_pointer"]["record_id"])
        rows.append(
            source_record_from_claim(
                case_id,
                claim_by_record,
                record_id,
                {"event": targets[line_number], "line_number": line_number},
                null_source_type=FAMILY_SOURCE_TYPES["otrf"],
            )
        )
    for line_number, event in null_rows:
        record_id = otrf_null_record_id(event, line_number)
        rows.append(
            source_record_from_claim(
                case_id,
                claim_by_record,
                record_id,
                {"event": event, "line_number": line_number},
                null_source_type=FAMILY_SOURCE_TYPES["otrf"],
            )
        )
    return rows


def graphml_payload(path: Path) -> dict[str, Any]:
    root = ElementTree.parse(path).getroot()
    nodes = []
    edges = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "node":
            nodes.append(
                {
                    "id": element.attrib.get("id"),
                    "values": [
                        child.text
                        for child in element
                        if child.text and child.text.strip()
                    ],
                }
            )
        elif tag == "edge":
            edges.append(
                {
                    "source": element.attrib.get("source"),
                    "destination": element.attrib.get("target"),
                }
            )
    return {
        "document_sha256": sha256_file(path),
        "document_size_bytes": path.stat().st_size,
        "nodes": nodes,
        "edges": edges,
    }


def load_witfoo_case(
    root: Path,
    case_dir: Path,
    source_code: str,
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del case_dir, source_code
    base = root / "09-experiments" / "real_data" / "witfoo_precinct6"
    lock = load_json(base / "c12_case_compile_lock_v0.1.json")
    incident_id = str(lock["selected_incident_id"])
    incident = load_json(base / "raw" / "incidents" / f"{incident_id}.json")
    leads = incident.get("leads") or {}
    if not isinstance(leads, dict):
        raise ValueError("WitFoo incident leads must be an object")
    graph_path = base / "raw" / "graphs" / f"{incident_id}.graphml"
    claim_by_record = {
        str(claim["source_pointer"]["record_id"]): claim for claim in claims
    }
    case_id = str(claims[0]["case_id"])
    selection = lock["claim_selection"]
    product_name = str(selection["network_aggregate"]["product_name"])
    aggregate_lead_items = [
        (record_id, lead)
        for record_id, lead in sorted(leads.items())
        if str((lead.get("product") or {}).get("name") or "") == product_name
    ]
    aggregate_leads = [lead for _, lead in aggregate_lead_items]

    rows = []
    for claim in claims:
        record_id = str(claim["source_pointer"]["record_id"])
        if record_id.startswith("aggregate:"):
            payload = {
                "incident_id": incident.get("id"),
                "leads": aggregate_leads,
            }
            artifact_slot = 1
        elif record_id == incident_id:
            payload = graphml_payload(graph_path)
            artifact_slot = 2
        else:
            lead = leads.get(record_id)
            if lead is None:
                raise ValueError(f"WitFoo lead not found: {record_id}")
            payload = {"incident_id": incident.get("id"), "lead": lead}
            artifact_slot = 1
        rows.append(
            source_record_from_claim(
                case_id,
                claim_by_record,
                record_id,
                payload,
                artifact_slot=artifact_slot,
                null_source_type=FAMILY_SOURCE_TYPES["witfoo"],
            )
        )

    aggregate_lead_ids = {
        record_id for record_id, _ in aggregate_lead_items
    }
    excluded = set(claim_by_record)
    null_needed = len(claims) * 3
    for record_id, lead in sorted(leads.items()):
        if record_id in excluded:
            continue
        record = source_record_from_claim(
            case_id,
            claim_by_record,
            str(record_id),
            {"incident_id": incident.get("id"), "lead": lead},
            null_source_type=FAMILY_SOURCE_TYPES["witfoo"],
        )
        if record_id in aggregate_lead_ids:
            _NULL_REVIEW_FLAGS.setdefault(record["packet_record_id"], set()).add(
                "constituent_of_aggregate_observation"
            )
        rows.append(record)
        null_needed -= 1
        if null_needed == 0:
            break
    if null_needed:
        raise ValueError(f"WitFoo null pool short by {null_needed} records")
    return rows


SOURCE_ADAPTERS = {
    "e3": load_e3_case,
    "pgdump": load_pgdump_case,
    "ecar": load_ecar_case,
    "otrf": load_otrf_case,
    "witfoo": load_witfoo_case,
}


def load_case_records(
    root: Path,
    case_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    root = root.resolve()
    key = (str(root), case_dir.name)
    if key in _CASE_RECORD_CACHE:
        return _CASE_RECORD_CACHE[key]

    claims = load_claims(case_dir)
    prefix = case_prefix(str(claims[0]["case_id"]))
    _, family, source_code = CASE_LAYOUT[prefix]
    records = SOURCE_ADAPTERS[family](root, case_dir, source_code, claims)
    records = sorted(records, key=lambda item: item["packet_record_id"])
    lookup = {
        str(record["source_pointer"]["record_id"]): record for record in records
    }
    if len(lookup) != len(records):
        raise ValueError(f"duplicate source record IDs in {case_dir.name}")
    result = (records, lookup)
    _CASE_RECORD_CACHE[key] = result
    return result


def gold_observation(
    claim: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "canonical_claim_id": str(claim["claim_id"]),
        "source_type": str(record["source_type"]),
        "subject": claim["subject"],
        "predicate": str(claim["predicate"]),
        "object": claim["object"],
        "source_pointer": record["source_pointer"],
    }


def build_positive_packets(
    case_id: str,
    records: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prefix = case_prefix(case_id)
    split = CASE_LAYOUT[prefix][0]
    support_ceiling = {
        "C04": "G3_campaign",
        "C05": "G2_tactic_intent",
        "C06": "G3_campaign",
        "C07": "G3_campaign",
        "C08": "G3_campaign",
        "C09": "G3_campaign",
        "C10": "G3_campaign",
        "C11": "G2_tactic_intent",
        "C12": "G1_technique",
    }[prefix]
    by_record = {
        str(record["source_pointer"]["record_id"]): record for record in records
    }
    claimed_records = []
    claim_by_record = {}
    for claim in claims:
        record_id = str(claim["source_pointer"]["record_id"])
        if record_id not in by_record:
            raise ValueError(f"representative source record is missing: {record_id}")
        claimed_records.append(by_record[record_id])
        claim_by_record[record_id] = claim
    claimed_records = sorted(
        {row["packet_record_id"]: row for row in claimed_records}.values(),
        key=lambda item: item["packet_record_id"],
    )
    random.Random(f"{seed}|{prefix}").shuffle(claimed_records)
    position = {
        str(row["source_pointer"]["record_id"]): index
        for index, row in enumerate(claimed_records)
    }

    public_rows = []
    private_rows = []
    for claim in sorted(claims, key=lambda item: str(item["claim_id"])):
        target_record_id = str(claim["source_pointer"]["record_id"])
        start = position[target_record_id]
        selected = [
            claimed_records[(start + offset) % len(claimed_records)]
            for offset in range(min(3, len(claimed_records)))
        ]
        selected_ids = {
            str(record["source_pointer"]["record_id"]) for record in selected
        }
        acceptable = [
            gold_observation(claim_by_record[record_id], by_record[record_id])
            for record_id in sorted(selected_ids)
            if record_id in claim_by_record
        ]
        public, private = build_packet_pair(
            case_id=public_case_id(case_id),
            split=split,
            packet_role="positive",
            support_ceiling=support_ceiling,
            records=selected,
            acceptable_observations=acceptable,
        )
        public_rows.append(public)
        private_rows.append(private)
    return public_rows, private_rows


def build_null_candidates(
    case_id: str,
    records: list[dict[str, Any]],
    claimed_record_ids: set[str],
    positive_packets: list[dict[str, Any]],
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prefix = case_prefix(case_id)
    split = CASE_LAYOUT[prefix][0]
    support_ceiling = positive_packets[0]["support_ceiling"]
    pool = [
        record
        for record in records
        if str(record["source_pointer"]["record_id"]) not in claimed_record_ids
    ]
    pool.sort(key=lambda item: item["packet_record_id"])
    random.Random(f"{seed}|{prefix}").shuffle(pool)
    if not pool:
        raise ValueError(f"no matched-null records available for {case_id}")

    selections = []
    usage: Counter[str] = Counter()
    cursor = 0
    for _ in positive_packets:
        selected = []
        for _ in range(3):
            record = pool[cursor % len(pool)]
            cursor += 1
            selected.append(record)
            usage[record["packet_record_id"]] += 1
        selections.append(selected)

    public_rows = []
    private_rows = []
    for selected in selections:
        public, private = build_packet_pair(
            case_id=public_case_id(case_id),
            split=split,
            packet_role="null",
            support_ceiling=support_ceiling,
            records=selected,
            acceptable_observations=[],
        )
        private["status"] = "pending_human_construction_audit"
        private["construction_metadata"] = {
            "record_reuse_count": {
                record["packet_record_id"]: usage[record["packet_record_id"]]
                for record in selected
            },
            "review_flags": sorted(
                {
                    flag
                    for record in selected
                    for flag in null_review_flags(record)
                }
            ),
        }
        public_rows.append(public)
        private_rows.append(private)
    return public_rows, private_rows


def build_packet_pair(
    case_id: str,
    split: str,
    packet_role: str,
    support_ceiling: str,
    records: list[dict[str, Any]],
    acceptable_observations: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    public = {
        "case_id": case_id,
        "split": split,
        "packet_role": packet_role,
        "support_ceiling": support_ceiling,
        "records": sorted(records, key=lambda item: item["packet_record_id"]),
    }
    public["request_id"] = derive_request_id(public)

    private_observations = []
    for observation in acceptable_observations:
        canonical_claim_id = str(observation["canonical_claim_id"])
        private_observation = {
            key: value
            for key, value in observation.items()
            if key != "gold_claim_id"
        }
        private_observation["gold_claim_id"] = derive_gold_claim_id(
            case_id, canonical_claim_id
        )
        private_observations.append(private_observation)
    private_observations.sort(key=lambda item: item["gold_claim_id"])
    private = {
        "request_id": public["request_id"],
        "case_id": case_id,
        "packet_role": packet_role,
        "acceptable_observations": private_observations,
    }
    assert_public_safe(public)
    return public, private


def iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_keys(item)


def assert_public_safe(value: Any) -> None:
    present = FORBIDDEN_PUBLIC_KEYS & set(iter_keys(value))
    if present:
        raise ValueError(f"forbidden private keys in public payload: {sorted(present)}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b"".join(canonical_json(row) + b"\n" for row in rows)
    path.write_bytes(gzip.compress(payload, mtime=0))


def private_identifiers(private_rows: Iterable[dict[str, Any]]) -> set[str]:
    identifiers: set[str] = set()
    for row in private_rows:
        for observation in row.get("acceptable_observations", []):
            for key in ("canonical_claim_id", "gold_claim_id"):
                value = observation.get(key)
                if value:
                    identifiers.add(str(value))
    return identifiers


def write_bundle(
    output_dir: Path,
    public_rows: list[dict[str, Any]],
    private_rows: list[dict[str, Any]],
    public_catalog: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"refusing to overwrite non-empty bundle: {output_dir}")
    if [row["request_id"] for row in public_rows] != [
        row["request_id"] for row in private_rows
    ]:
        raise ValueError("public/private request ordering mismatch")

    for row in public_rows:
        assert_public_safe(row)
    assert_public_safe(public_catalog)

    public_projection = {
        "packets": public_rows,
        "catalog": public_catalog,
        "metadata": metadata,
    }
    serialized_public = canonical_json(public_projection).decode("utf-8")
    leaked = sorted(
        identifier
        for identifier in private_identifiers(private_rows)
        if identifier in serialized_public
    )
    if leaked:
        raise ValueError(f"private identifiers leaked into public payload: {leaked}")

    public_dir = output_dir / "public"
    private_dir = output_dir / "private"
    packets_path = public_dir / "context_packets.jsonl.gz"
    catalog_path = public_dir / "public_cti_catalog.json"
    input_manifest_path = public_dir / "input_manifest.json"
    gold_path = private_dir / "observation_gold.jsonl.gz"
    gold_manifest_path = private_dir / "gold_manifest.json"

    write_jsonl_gz(packets_path, public_rows)
    write_json(catalog_path, public_catalog)
    input_manifest = {
        **metadata,
        "packet_count": len(public_rows),
        "separation_status": "separated",
        "private_identifiers_included": False,
        "files": {
            "context_packets.jsonl.gz": sha256_file(packets_path),
            "public_cti_catalog.json": sha256_file(catalog_path),
        },
    }
    write_json(input_manifest_path, input_manifest)

    write_jsonl_gz(gold_path, private_rows)
    gold_manifest = {
        **metadata,
        "packet_count": len(private_rows),
        "separation_status": "private_scorer_only",
        "public_input_manifest_sha256": sha256_file(input_manifest_path),
        "observation_gold_sha256": sha256_file(gold_path),
    }
    write_json(gold_manifest_path, gold_manifest)
    return input_manifest


def build_split(
    root: Path,
    split: Literal["development", "test"],
    output_dir: Path,
) -> dict[str, Any]:
    if split not in {"development", "test"}:
        raise ValueError(f"unsupported split: {split}")
    case_root = root / "09-experiments" / "real_cases"
    case_dirs = [
        case_dir
        for case_dir in sorted(case_root.iterdir(), key=lambda item: item.name)
        if case_dir.is_dir()
        and case_prefix(case_dir.name) in CASE_LAYOUT
        and CASE_LAYOUT[case_prefix(case_dir.name)][0] == split
    ]
    public_rows: list[dict[str, Any]] = []
    private_rows: list[dict[str, Any]] = []
    artifact_counts: Counter[str] = Counter()
    for case_dir in case_dirs:
        claims = load_claims(case_dir)
        canonical_case_id = str(claims[0]["case_id"])
        records, _ = load_case_records(root, case_dir)
        positive_public, positive_private = build_positive_packets(
            canonical_case_id,
            records,
            claims,
            PACKET_SEED,
        )
        claimed_record_ids = {
            str(claim["source_pointer"]["record_id"]) for claim in claims
        }
        null_public, null_private = build_null_candidates(
            canonical_case_id,
            records,
            claimed_record_ids,
            positive_public,
            NULL_SEED,
        )
        public_rows.extend([*positive_public, *null_public])
        private_rows.extend([*positive_private, *null_private])
        for record in records:
            artifact_counts[record["source_pointer"]["artifact_id"]] += 1

    combined = list(zip(public_rows, private_rows))
    combined.sort(key=lambda pair: pair[0]["request_id"])
    public_rows = [pair[0] for pair in combined]
    private_rows = [pair[1] for pair in combined]
    positive_count = sum(row["packet_role"] == "positive" for row in public_rows)
    null_count = sum(row["packet_role"] == "null" for row in public_rows)
    metadata = {
        "bundle_version": "project05-llm-phase1-packet-draft-v0.2",
        "split": split,
        "status": "draft_pending_human_null_construction_audit",
        "formal_ready": False,
        "null_construction_audit": "pending",
        "case_count": len(case_dirs),
        "packet_counts": {"positive": positive_count, "null": null_count},
        "packet_seed": PACKET_SEED,
        "null_seed": NULL_SEED,
    }
    catalog = {
        "catalog_version": "project05-llm-phase1-public-source-catalog-v0.2",
        "artifacts": [
            {"artifact_id": artifact_id, "record_count": artifact_counts[artifact_id]}
            for artifact_id in sorted(artifact_counts)
        ],
    }
    manifest = write_bundle(
        output_dir,
        public_rows=public_rows,
        private_rows=private_rows,
        public_catalog=catalog,
        metadata=metadata,
    )
    return {
        **manifest,
        "case_count": len(case_dirs),
        "packet_counts": {"positive": positive_count, "null": null_count},
    }


def build_case_fixture_with_two_distractors() -> tuple[dict[str, Any], dict[str, Any]]:
    case_id = "C07-evaluation-case"
    records = [
        make_packet_record(
            "local_log",
            {"artifact_id": "SRC-C07-01", "record_id": f"event-{index}"},
            {"event": {"operation": "read", "path": f"/tmp/file-{index}"}},
        )
        for index in range(1, 4)
    ]
    acceptable = [
        {
            "canonical_claim_id": "C07-EC-001",
            "source_type": "local_log",
            "subject": {"entity_type": "process", "value": "reader"},
            "predicate": "read",
            "object": {"entity_type": "file", "value": "/tmp/file-1"},
            "source_pointer": records[0]["source_pointer"],
        }
    ]
    return build_packet_pair(
        case_id=case_id,
        split="test",
        packet_role="positive",
        support_ceiling="G1_technique",
        records=records,
        acceptable_observations=acceptable,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build deterministic public/private LLM Phase 1 packet drafts."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--split", choices=("development", "test"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draft", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.draft:
        raise SystemExit("Task 3 only authorizes --draft packet generation")
    result = build_split(args.root.resolve(), args.split, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
