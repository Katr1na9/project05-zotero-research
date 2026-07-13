#!/usr/bin/env python3
"""Audit C12 GraphML projections and recoverable incident-lead evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, BinaryIO, Iterator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCK = (
    ROOT
    / "09-experiments"
    / "real_data"
    / "witfoo_precinct6"
    / "c12_intake_lock_v0.1.json"
)
DEFAULT_CANDIDATES = (
    ROOT
    / "09-experiments"
    / "results"
    / "c12_witfoo_screen_v0.1"
    / "candidate_index.json"
)
GRAPHML_NS = {"g": "http://graphml.graphdrawing.org/xmlns"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def source_url(lock: dict[str, Any], relative_path: str) -> str:
    dataset = lock["dataset"]
    return (
        "https://huggingface.co/datasets/"
        f"{dataset['dataset_id']}/resolve/{dataset['revision']}/{relative_path}"
    )


def open_source(source: str) -> BinaryIO:
    if not source.casefold().startswith(("http://", "https://")):
        local = Path(source)
        if local.is_file():
            return local.open("rb")
        raise FileNotFoundError(f"C12 event source does not exist: {local}")
    request = urllib.request.Request(
        source,
        headers={"User-Agent": "Project05-C12-event-audit/0.1"},
    )
    return urllib.request.urlopen(request, timeout=180)  # noqa: S310


def download(source: str, destination: Path) -> bytes:
    if destination.is_file():
        return destination.read_bytes()
    with open_source(source) as handle:
        payload = handle.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return payload


def parse_json_array(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [value]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def parse_graphml(payload: bytes) -> dict[str, Any]:
    root = ET.fromstring(payload)
    key_names = {
        item.attrib["id"]: item.attrib.get("attr.name", item.attrib["id"])
        for item in root.findall("g:key", GRAPHML_NS)
    }
    nodes = root.findall(".//g:node", GRAPHML_NS)
    edges = root.findall(".//g:edge", GRAPHML_NS)
    node_types: Counter[str] = Counter()
    node_products: Counter[str] = Counter()
    edge_types: Counter[str] = Counter()
    populated_edge_fields: Counter[str] = Counter()
    telemetry_edges = 0

    for node in nodes:
        values = {
            key_names.get(data.attrib["key"], data.attrib["key"]): data.text or ""
            for data in node.findall("g:data", GRAPHML_NS)
        }
        node_types[values.get("type", "missing")] += 1
        node_products.update(parse_json_array(values.get("products")))

    telemetry_fields = {"message_type", "action", "protocol", "stream"}
    for edge in edges:
        values = {
            key_names.get(data.attrib["key"], data.attrib["key"]): data.text or ""
            for data in edge.findall("g:data", GRAPHML_NS)
        }
        edge_type = values.get("type", "missing")
        edge_types[edge_type] += 1
        present = {name for name in telemetry_fields if values.get(name)}
        populated_edge_fields.update(present)
        if edge_type != "INCIDENT_LINK" or present:
            telemetry_edges += 1

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_types": dict(sorted(node_types.items())),
        "node_product_mentions": dict(sorted(node_products.items())),
        "edge_types": dict(sorted(edge_types.items())),
        "populated_telemetry_edge_fields": dict(sorted(populated_edge_fields.items())),
        "telemetry_edge_count": telemetry_edges,
        "projection_only": telemetry_edges == 0,
    }


def incident_source_profile(
    leads: list[dict[str, Any]],
    product_taxonomy: dict[str, dict[str, str]],
    stream_taxonomy: dict[str, dict[str, str]],
) -> dict[str, Any]:
    products: Counter[str] = Counter()
    product_families: Counter[str] = Counter()
    product_channels: Counter[str] = Counter()
    streams: Counter[str] = Counter()
    stream_families: Counter[str] = Counter()
    stream_channels: Counter[str] = Counter()
    verified_channels: Counter[str] = Counter()
    product_stream_pairs: Counter[str] = Counter()
    mismatched_pairs: Counter[str] = Counter()
    unmapped_products: Counter[str] = Counter()
    unmapped_streams: Counter[str] = Counter()
    for lead in leads:
        product = lead.get("product") or {}
        artifact = lead.get("artifact") or {}
        product_label = str(product.get("name") or "missing")
        stream_label = str(artifact.get("streamname") or "missing")
        products[product_label] += 1
        streams[stream_label] += 1
        pair = f"{product_label} <- {stream_label}"
        product_stream_pairs[pair] += 1
        product_mapping = product_taxonomy.get(product_label)
        stream_mapping = stream_taxonomy.get(stream_label)
        if product_mapping is None:
            unmapped_products[product_label] += 1
        else:
            product_families[product_mapping["family"]] += 1
            product_channels[product_mapping["channel"]] += 1
        if stream_mapping is None:
            unmapped_streams[stream_label] += 1
        else:
            stream_families[stream_mapping["family"]] += 1
            stream_channels[stream_mapping["channel"]] += 1
        if product_mapping is not None and stream_mapping is not None:
            if product_mapping["channel"] == stream_mapping["channel"]:
                verified_channels[stream_mapping["channel"]] += 1
            else:
                mismatched_pairs[pair] += 1
    return {
        "lead_products": dict(sorted(products.items())),
        "lead_product_families": dict(sorted(product_families.items())),
        "lead_product_channels": dict(sorted(product_channels.items())),
        "lead_streams": dict(sorted(streams.items())),
        "lead_stream_families": dict(sorted(stream_families.items())),
        "lead_stream_channels": dict(sorted(stream_channels.items())),
        "verified_sensor_channels": dict(sorted(verified_channels.items())),
        "lead_product_stream_pairs": dict(sorted(product_stream_pairs.items())),
        "channel_mismatched_product_stream_pairs": dict(sorted(mismatched_pairs.items())),
        "unmapped_lead_products": dict(sorted(unmapped_products.items())),
        "unmapped_lead_streams": dict(sorted(unmapped_streams.items())),
    }


def summarize_incident(
    record: dict[str, Any],
    expected: dict[str, Any],
    product_taxonomy: dict[str, dict[str, str]],
    stream_taxonomy: dict[str, dict[str, str]],
    raw_line_sha256: str,
) -> dict[str, Any]:
    leads = list((record.get("leads") or {}).values())
    sources = incident_source_profile(leads, product_taxonomy, stream_taxonomy)
    message_types: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    descriptions: Counter[str] = Counter()
    vendors: Counter[str] = Counter()
    source_fields = Counter()
    detail_hashes: set[str] = set()
    observed_times: list[int] = []

    for lead in leads:
        artifact = lead.get("artifact") or {}
        product = lead.get("product") or {}
        message_types[str(artifact.get("messagetype") or "missing")] += 1
        actions[str(artifact.get("action") or "missing")] += 1
        descriptions[str(lead.get("description") or "missing")] += 1
        vendors[str(product.get("vendor_name") or "missing")] += 1
        for field in ("artifact", "details", "observed_at", "node_id", "product"):
            if lead.get(field) not in (None, "", {}, []):
                source_fields[field] += 1
        details = str(lead.get("details") or "")
        if details:
            detail_hashes.add(sha256_bytes(details.encode("utf-8")))
        if lead.get("observed_at") is not None:
            observed_times.append(int(lead["observed_at"]))

    lead_count_matches = len(leads) == int(expected["lead_count"])
    product_families = sources["lead_product_families"]
    stream_channels = sources["lead_stream_channels"]
    verified_channels = sources["verified_sensor_channels"]
    all_source_fields_present = all(
        source_fields[field] == len(leads)
        for field in ("artifact", "details", "observed_at", "node_id", "product")
    )
    recoverability_pass = (
        lead_count_matches
        and not sources["unmapped_lead_products"]
        and not sources["unmapped_lead_streams"]
        and len(product_families) >= 2
        and len(stream_channels) >= 2
        and len(verified_channels) >= 2
        and all_source_fields_present
    )
    return {
        "incident_id": record.get("id"),
        "raw_incident_line_sha256": raw_line_sha256,
        "status_name": record.get("status_name"),
        "organization_id_sanitized": record.get("_org_id") or record.get("org"),
        "mo_name": record.get("mo_name"),
        "actors_count": len(record.get("actors") or []),
        "reported_lead_count": record.get("lead_count"),
        "extracted_lead_count": len(leads),
        "lead_count_matches_metadata": lead_count_matches,
        **sources,
        "lead_vendors": dict(sorted(vendors.items())),
        "lead_message_types": dict(sorted(message_types.items())),
        "lead_actions": dict(sorted(actions.items())),
        "lead_descriptions": dict(sorted(descriptions.items())),
        "lead_source_field_coverage": dict(sorted(source_fields.items())),
        "unique_sanitized_detail_count": len(detail_hashes),
        "observed_time_min": min(observed_times) if observed_times else None,
        "observed_time_max": max(observed_times) if observed_times else None,
        "recoverability_gate": {
            "pass": recoverability_pass,
            "requires_two_product_families": len(product_families) >= 2,
            "requires_two_independent_stream_channels": len(stream_channels) >= 2,
            "requires_two_product_stream_verified_channels": len(
                verified_channels
            ) >= 2,
            "requires_all_lead_products_mapped": not sources[
                "unmapped_lead_products"
            ],
            "requires_all_lead_streams_mapped": not sources[
                "unmapped_lead_streams"
            ],
            "requires_complete_lead_source_pointers": all_source_fields_present,
        },
    }


def scan_incidents(
    source: str,
    candidates: dict[str, dict[str, Any]],
    product_taxonomy: dict[str, dict[str, str]],
    stream_taxonomy: dict[str, dict[str, str]],
    raw_directory: Path,
    max_records: int | None,
) -> dict[str, Any]:
    wanted = set(candidates)
    found: dict[str, dict[str, Any]] = {}
    scanned = 0
    bytes_scanned = 0
    reached_eof = True
    with open_source(source) as handle:
        for raw_line in handle:
            if max_records is not None and scanned >= max_records:
                reached_eof = False
                break
            scanned += 1
            bytes_scanned += len(raw_line)
            record = json.loads(raw_line)
            incident_id = str(record.get("id"))
            if incident_id in wanted:
                raw_directory.mkdir(parents=True, exist_ok=True)
                (raw_directory / f"{incident_id}.json").write_bytes(raw_line)
                found[incident_id] = summarize_incident(
                    record,
                    candidates[incident_id],
                    product_taxonomy,
                    stream_taxonomy,
                    sha256_bytes(raw_line),
                )
                wanted.remove(incident_id)
                print(
                    f"found {incident_id} at record {scanned}; remaining={len(wanted)}",
                    flush=True,
                )
                if not wanted:
                    reached_eof = False
                    break
            if scanned % 1000 == 0:
                print(
                    f"scanned {scanned} incident records; remaining={len(wanted)}",
                    flush=True,
                )
    return {
        "extraction_method": "sequential_jsonl_scan",
        "records_scanned": scanned,
        "bytes_scanned": bytes_scanned,
        "reached_eof": reached_eof,
        "found_incident_ids": sorted(found),
        "missing_incident_ids": sorted(wanted),
        "incidents": [found[key] for key in sorted(found)],
    }


class RangeReader:
    def __init__(self, source: str) -> None:
        request = urllib.request.Request(
            source,
            method="HEAD",
            headers={"User-Agent": "Project05-C12-range-reader/0.1"},
        )
        with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310
            self.url = response.geturl()
            self.size = int(response.headers["Content-Length"])
        self.request_count = 0
        self.bytes_transferred = 0

    def fetch(self, start: int, end: int) -> bytes:
        bounded_start = max(0, start)
        bounded_end = min(self.size - 1, end)
        request = urllib.request.Request(
            self.url,
            headers={
                "Range": f"bytes={bounded_start}-{bounded_end}",
                "User-Agent": "Project05-C12-range-reader/0.1",
            },
        )
        with urllib.request.urlopen(request, timeout=240) as response:  # noqa: S310
            payload = response.read()
        self.request_count += 1
        self.bytes_transferred += len(payload)
        return payload


def load_report_order(source: str) -> tuple[dict[str, int], int]:
    order: dict[str, int] = {}
    with open_source(source) as handle:
        for index, raw_line in enumerate(handle, start=1):
            if raw_line.strip():
                order[str(json.loads(raw_line)["incident_id"])] = index
    return order, len(order)


def complete_jsonl_rows(
    payload: bytes,
    absolute_start: int,
    order: dict[str, int],
    aligned_start: bool = False,
) -> list[tuple[int, int, bytes, dict[str, Any]]]:
    parts = payload.splitlines(keepends=True)
    offset = absolute_start
    if absolute_start > 0 and not aligned_start and parts:
        offset += len(parts.pop(0))
    rows: list[tuple[int, int, bytes, dict[str, Any]]] = []
    for raw_line in parts:
        line_start = offset
        offset += len(raw_line)
        if not raw_line.endswith(b"\n"):
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        incident_id = str(record.get("id"))
        record_index = order.get(incident_id)
        if record_index is not None:
            rows.append((record_index, line_start, raw_line, record))
    return rows


def locate_jsonl_record(
    reader: RangeReader,
    target_index: int,
    order: dict[str, int],
    total_records: int,
    anchors: dict[int, tuple[int, int]],
    sample_bytes: int = 2 * 1024 * 1024,
) -> tuple[bytes, dict[str, Any], int]:
    for attempt in range(1, 13):
        lower_index = max(index for index in anchors if index <= target_index)
        upper_index = min(index for index in anchors if index > target_index)
        lower_offset = anchors[lower_index][0] + anchors[lower_index][1]
        upper_offset = anchors[upper_index][0]
        denominator = max(1, upper_index - lower_index)
        fraction = (target_index - lower_index) / denominator
        guess = int(lower_offset + fraction * (upper_offset - lower_offset))
        start = max(lower_offset, guess - sample_bytes // 2)
        payload = reader.fetch(start, start + sample_bytes - 1)
        rows = complete_jsonl_rows(payload, start, order)
        for record_index, line_start, raw_line, record in rows:
            anchors[record_index] = (line_start, len(raw_line))
            if record_index == target_index:
                print(
                    f"range-located index {target_index} at byte {line_start} "
                    f"on attempt {attempt}",
                    flush=True,
                )
                return raw_line, record, line_start
        print(
            f"range attempt {attempt} for index {target_index}: "
            f"parsed={len(rows)} anchors={len(anchors)}",
            flush=True,
        )
        if not rows:
            sample_bytes *= 2

    lower_index = max(index for index in anchors if index < target_index)
    upper_index = min(index for index in anchors if index > target_index)
    if upper_index - lower_index == 2:
        start = anchors[lower_index][0] + anchors[lower_index][1]
        end = anchors[upper_index][0] - 1
        payload = reader.fetch(start, end)
        rows = complete_jsonl_rows(payload, start, order, aligned_start=True)
        for record_index, line_start, raw_line, record in rows:
            if record_index == target_index:
                anchors[record_index] = (line_start, len(raw_line))
                return raw_line, record, line_start
    raise RuntimeError(
        f"Could not range-locate JSONL record index {target_index} "
        f"within {reader.request_count} requests"
    )


def extract_incidents_by_index(
    source: str,
    attack_reports_source: str,
    candidates: dict[str, dict[str, Any]],
    product_taxonomy: dict[str, dict[str, str]],
    stream_taxonomy: dict[str, dict[str, str]],
    raw_directory: Path,
) -> dict[str, Any]:
    order, total_records = load_report_order(attack_reports_source)
    expected_order = {
        incident_id: int(candidate["source_record_index_1based"])
        for incident_id, candidate in candidates.items()
    }
    order_mismatches = {
        incident_id: {
            "candidate_index": expected_index,
            "attack_report_index": order.get(incident_id),
        }
        for incident_id, expected_index in expected_order.items()
        if order.get(incident_id) != expected_index
    }
    if order_mismatches:
        raise ValueError(f"C12 report-order mismatch: {order_mismatches}")

    reader = RangeReader(source)
    anchors: dict[int, tuple[int, int]] = {
        1: (0, 0),
        total_records + 1: (reader.size, 0),
    }
    found: dict[str, dict[str, Any]] = {}
    byte_offsets: dict[str, int | None] = {}
    cache_hit_count = 0
    for incident_id, target_index in sorted(
        expected_order.items(), key=lambda item: item[1]
    ):
        destination = raw_directory / f"{incident_id}.json"
        if destination.is_file():
            raw_line = destination.read_bytes()
            record = json.loads(raw_line)
            line_start = None
            cache_hit_count += 1
        else:
            raw_line, record, line_start = locate_jsonl_record(
                reader,
                target_index,
                order,
                total_records,
                anchors,
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw_line)
        if str(record.get("id")) != incident_id:
            raise ValueError(
                f"Range extraction returned {record.get('id')} for {incident_id}"
            )
        byte_offsets[incident_id] = line_start
        found[incident_id] = summarize_incident(
            record,
            candidates[incident_id],
            product_taxonomy,
            stream_taxonomy,
            sha256_bytes(raw_line),
        )

    return {
        "extraction_method": "http_range_by_frozen_record_index",
        "attack_report_order_gate": {
            "pass": not order_mismatches,
            "record_count": total_records,
            "mismatches": order_mismatches,
        },
        "source_file_size": reader.size,
        "range_request_count": reader.request_count,
        "bytes_transferred": reader.bytes_transferred,
        "cache_hit_count": cache_hit_count,
        "byte_offsets": byte_offsets,
        "found_incident_ids": sorted(found),
        "missing_incident_ids": [],
        "incidents": [found[key] for key in sorted(found)],
    }


def audit(
    lock: dict[str, Any],
    candidate_index: dict[str, Any],
    raw_directory: Path,
    incidents_source: str,
    attack_reports_source: str | None,
    max_records: int | None = None,
) -> dict[str, Any]:
    candidates = {
        str(item["incident_id"]): item for item in candidate_index["candidates"]
    }
    graph_audits: list[dict[str, Any]] = []
    for incident_id, candidate in candidates.items():
        graph_path = str(candidate["graph_path"])
        destination = raw_directory / "graphs" / f"{incident_id}.graphml"
        payload = download(source_url(lock, graph_path), destination)
        graph_audits.append(
            {
                "incident_id": incident_id,
                "graph_path": graph_path,
                "graphml_sha256": sha256_bytes(payload),
                **parse_graphml(payload),
            }
        )

    if (
        incidents_source.casefold().startswith(("http://", "https://"))
        and attack_reports_source is not None
        and max_records is None
    ):
        incident_scan = extract_incidents_by_index(
            incidents_source,
            attack_reports_source,
            candidates,
            lock["product_taxonomy"],
            lock["stream_taxonomy"],
            raw_directory / "incidents",
        )
    else:
        incident_scan = scan_incidents(
            incidents_source,
            candidates,
            lock["product_taxonomy"],
            lock["stream_taxonomy"],
            raw_directory / "incidents",
            max_records,
        )
    graph_by_id = {item["incident_id"]: item for item in graph_audits}
    incident_by_id = {
        item["incident_id"]: item for item in incident_scan["incidents"]
    }
    joined: list[dict[str, Any]] = []
    for incident_id in candidates:
        graph = graph_by_id.get(incident_id)
        incident = incident_by_id.get(incident_id)
        joined.append(
            {
                "incident_id": incident_id,
                "metadata_rank": list(candidates).index(incident_id) + 1,
                "graph_projection_only": graph["projection_only"] if graph else None,
                "lead_recoverability_pass": (
                    incident["recoverability_gate"]["pass"] if incident else False
                ),
            }
        )
    eligible = [
        item for item in joined if item["lead_recoverability_pass"] is True
    ]
    selected = eligible[0]["incident_id"] if eligible else None
    return {
        "audit_id": "project05-c12-witfoo-event-source-audit-v0.1",
        "source": {
            "dataset_id": lock["dataset"]["dataset_id"],
            "revision": lock["dataset"]["revision"],
            "incidents_source": incidents_source,
        },
        "graphml_audits": graph_audits,
        "incident_scan": incident_scan,
        "candidate_gates": joined,
        "decision": {
            "event_source_gate_pass": selected is not None,
            "selected_primary_incident_id": selected,
            "paper_result_claim_allowed": False,
            "status": (
                "event_source_recoverable_case_compilation_pending"
                if selected is not None
                else "no_recoverable_multichannel_candidate"
            ),
            "next_step": (
                "compile_C12_claims_actions_and_intended_recoverable_separation"
                if selected is not None
                else "select_a_different_operational_dataset"
            ),
        },
        "claim_boundary": [
            "GraphML INCIDENT_LINK edges are vendor-correlation projections, not raw telemetry actions.",
            "Recoverability is established from embedded incident leads and their source fields.",
            "Analyst disposition is not independent actor-attribution ground truth.",
            "Passing this audit permits case compilation only, not a paper result claim.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit C12 GraphML projections and embedded incident leads."
    )
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--incidents-source")
    parser.add_argument(
        "--attack-reports-source",
        help="Local or remote attack_reports.jsonl used to verify record order.",
    )
    parser.add_argument("--max-records", type=int)
    parser.add_argument(
        "--raw-directory",
        type=Path,
        default=ROOT / "09-experiments" / "real_data" / "witfoo_precinct6" / "raw",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "09-experiments"
            / "results"
            / "c12_witfoo_event_audit_v0.1"
            / "audit.json"
        ),
    )
    args = parser.parse_args()
    lock = load_json(args.lock)
    candidates = load_json(args.candidates)
    incidents_source = args.incidents_source or source_url(
        lock, "graph/incidents.jsonl"
    )
    default_reports = args.raw_directory / "attack_reports.jsonl"
    attack_reports_source = args.attack_reports_source
    if attack_reports_source is None:
        attack_reports_source = (
            str(default_reports)
            if default_reports.is_file()
            else source_url(lock, lock["dataset"]["attack_reports_path"])
        )
    result = audit(
        lock,
        candidates,
        args.raw_directory,
        incidents_source,
        attack_reports_source,
        args.max_records,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["decision"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
