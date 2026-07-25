#!/usr/bin/env python3
"""Build WP2 public artifacts and private execution/reference manifests.

The builder resolves the 58 frozen C04-C12 source pointers against local raw
or bounded source files. Public outputs contain request-scoped IDs and source
records only. Canonical claim/node/action IDs remain physically private.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import importlib.util
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_ROOT.parent
DEFAULT_OUTPUT = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "generated"
    / "wp2"
)
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
TECHNIQUE_PATTERN = re.compile(r"\bT\d{4}(?:\.\d{3})?\b", re.I)
SENSITIVE_LABEL_PATTERN = re.compile(r"\b(?:apt29|named actor|campaign label)\b", re.I)
SOURCE_FORBIDDEN_KEY_PARTS = (
    "canonical_claim",
    "gold_claim",
    "claim_id",
    "recoverable_claim",
    "required_claim",
    "mapped_tactic",
    "mapped_technique",
    "motif_id",
    "attack_label",
    "actor_label",
    "campaign_label",
    "ground_truth",
)
GENERIC_PREDICATES = {
    "EVENT_ACCEPT": "accepted_external_connection",
    "EVENT_CONNECT": "connected_to",
    "EVENT_EXECUTE": "executed",
    "EVENT_OPEN": "opened",
    "EVENT_READ": "read",
    "EVENT_RECVFROM": "received_data_from",
    "EVENT_SENDTO": "sent_data_to",
    "EVENT_WRITE": "wrote",
    "FILE:CREATE": "created",
    "FILE:READ": "read",
    "FILE:WRITE": "wrote",
    "FLOW:MESSAGE": "connected_to",
    "PROCESS:CREATE": "executed",
    "REGISTRY:MODIFY": "set_registry_value_for",
    "WINDOWS:11": "created",
    "WINDOWS:4688": "executed",
    "WINDOWS:800": "executed_command",
    "WINDOWS:4104": "executed_command",
    "WITFOO:BLOCK": "attempted_blocked_connection_to",
    "WITFOO:4672": "received_special_privileges_on",
}

# These contracts are part of the public compiler interface.  They are fixed
# from observable operation families and public target-stage semantics, not
# from the private ``required_claim_ids`` or reference-claim predicates.  This
# distinction matters: admission may check a public vocabulary, but it must
# never learn which predicate the frozen author reference expects at a node.
PREDICATE_CLAIM_TYPE = {
    "accepted_external_connection": "network_connection",
    "attempted_blocked_connection_to": "network_connection",
    "connected_to": "network_connection",
    "received_data_from": "network_connection",
    "sent_data_to": "network_connection",
    "created": "file_activity",
    "opened": "file_activity",
    "read": "file_activity",
    "wrote": "file_activity",
    "executed": "process_execution",
    "executed_command": "process_execution",
    "set_registry_value_for": "registry_modification",
    "received_special_privileges_on": "credential_activity",
}
SOURCE_PREDICATE_ALLOWLIST = {
    "local_log": sorted(PREDICATE_CLAIM_TYPE),
    "host_forensics": sorted(PREDICATE_CLAIM_TYPE),
    "provenance_graph": sorted(PREDICATE_CLAIM_TYPE),
    "network_summary": sorted(
        predicate
        for predicate, claim_type in PREDICATE_CLAIM_TYPE.items()
        if claim_type == "network_connection"
    ),
}
STAGE_PREDICATE_ALLOWLIST = {
    "initial_access": {
        "accepted_external_connection",
        "connected_to",
        "created",
        "executed",
        "received_data_from",
        "wrote",
    },
    "execution": {
        "created",
        "executed",
        "executed_command",
        "received_data_from",
        "wrote",
    },
    "command_and_control": {
        "accepted_external_connection",
        "attempted_blocked_connection_to",
        "connected_to",
        "received_data_from",
        "sent_data_to",
    },
    "discovery": {"connected_to", "executed", "executed_command", "opened", "read"},
    "collection": {"created", "executed", "executed_command", "opened", "read", "wrote"},
    "exfiltration": {"connected_to", "sent_data_to", "wrote"},
    "privilege_escalation": {
        "executed",
        "executed_command",
        "received_special_privileges_on",
        "set_registry_value_for",
        "wrote",
    },
    "post_compromise": {"created", "executed", "opened", "wrote"},
    "lateral_movement": {
        "connected_to",
        "executed",
        "executed_command",
        "received_special_privileges_on",
    },
    "collection_exfiltration": {
        "connected_to",
        "created",
        "executed",
        "executed_command",
        "opened",
        "read",
        "sent_data_to",
        "wrote",
    },
    "network_observation": {
        "accepted_external_connection",
        "attempted_blocked_connection_to",
        "connected_to",
        "received_data_from",
        "sent_data_to",
    },
    "credential_observation": {"received_special_privileges_on"},
    "cross_channel_correlation": {
        "accepted_external_connection",
        "attempted_blocked_connection_to",
        "connected_to",
        "received_data_from",
        "received_special_privileges_on",
        "sent_data_to",
    },
    # Local observation claims cannot mechanically establish actor/campaign
    # attribution.  The sentinel keeps the schema non-empty while ensuring no
    # compiler-emitted local predicate can be admitted for that target.
    "actor_attribution": {"unsupported_by_local_observation"},
}


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_sibling(
    "project05_compiler_public_builder_for_wp2",
    "build_compiler_public_request.py",
)
RUN_MVP = load_sibling("project05_run_mvp_for_wp2", "run_mvp.py")


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def case_prefix(case_id: str) -> str:
    prefix = case_id[:3]
    if prefix not in CASE_LAYOUT:
        raise ValueError(f"unsupported WP2 case: {case_id}")
    return prefix


def public_case_id(case_id: str) -> str:
    return f"{case_prefix(case_id)}-compiler-evaluation"


def scrub_public_source(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            folded = str(key).casefold()
            if str(key) in BUILDER.FORBIDDEN_PUBLIC_KEYS or any(
                part in folded for part in SOURCE_FORBIDDEN_KEY_PARTS
            ):
                continue
            clean[str(key)] = scrub_public_source(item)
        return clean
    if isinstance(value, list):
        return [scrub_public_source(item) for item in value]
    if isinstance(value, str) and (
        TECHNIQUE_PATTERN.search(value) or SENSITIVE_LABEL_PATTERN.search(value)
    ):
        return "[redacted-source-label]"
    return value


def compile_bytes_pattern(values: Iterable[str]) -> re.Pattern[bytes]:
    encoded = sorted({str(value).encode("utf-8") for value in values})
    if not encoded:
        return re.compile(b"(?!)")
    return re.compile(b"(?:" + b"|".join(re.escape(value) for value in encoded) + b")")


def collect_jsonl_targets(
    path: Path,
    target_ids: set[str],
    id_field: str,
) -> dict[str, dict[str, Any]]:
    targets: dict[str, dict[str, Any]] = {}
    pattern = compile_bytes_pattern(target_ids)
    with path.open("rb") as handle:
        for raw_line in handle:
            if not raw_line.strip() or pattern.search(raw_line) is None:
                continue
            row = json.loads(raw_line)
            record_id = str(row.get(id_field) or "")
            if record_id in target_ids:
                targets[record_id] = row
            if len(targets) == len(target_ids):
                break
    missing = sorted(target_ids.difference(targets))
    if missing:
        raise ValueError(f"records not found in {path}: {missing}")
    return targets


def load_selected_e3_nodes(
    path: Path,
    events: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    needed = {
        str(event.get(field))
        for event in events
        for field in ("subject_uuid", "predicate_object_uuid", "predicate_object_2_uuid")
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


def e3_payload(event: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    resolved = {}
    for field in ("subject_uuid", "predicate_object_uuid", "predicate_object_2_uuid"):
        node_id = event.get(field)
        if node_id and str(node_id) in nodes:
            resolved[field] = nodes[str(node_id)]
    return {"event": event, "resolved_nodes": resolved}


def load_e3_records(source_code: str, record_ids: set[str]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    base = EXPERIMENT_ROOT / "real_data" / "darpa_tc_e3" / "extracted" / source_code
    event_path = base / "events.jsonl"
    node_path = base / "nodes.jsonl"
    events = collect_jsonl_targets(event_path, record_ids, "event_uuid")
    nodes = load_selected_e3_nodes(node_path, events.values())
    payloads = {record_id: e3_payload(event, nodes) for record_id, event in events.items()}
    summary = load_json(
        EXPERIMENT_ROOT / "real_data" / "darpa_tc_e3" / "derived" / f"{source_code}_extraction_summary.json"
    )
    inventory = [
        {
            "role": "bounded_event_file",
            "path": str(event_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "size_bytes": event_path.stat().st_size,
            "expected_sha256": summary["outputs"]["events_sha256"],
            "hash_provenance": "frozen_extraction_summary",
        },
        {
            "role": "resolved_node_file",
            "path": str(node_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "size_bytes": node_path.stat().st_size,
            "expected_sha256": summary["outputs"]["nodes_sha256"],
            "hash_provenance": "frozen_extraction_summary",
        },
    ]
    return payloads, inventory


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
            f"{path}:{line_number}: expected {len(PGDMP_COLUMNS)} columns, found {len(columns)}"
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


def load_pgdump_records(source_code: str, record_ids: set[str]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    base = EXPERIMENT_ROOT / "real_data" / "darpa_tc_e5" / "extracted"
    event_path = base / f"{source_code}_event_table.tsv"
    node_path = base / f"{source_code}_nodes.jsonl"
    nodes = load_pgdump_nodes(node_path)
    targets: dict[str, dict[str, Any]] = {}
    pattern = compile_bytes_pattern(record_ids)
    with event_path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if pattern.search(raw_line) is None:
                continue
            event = parse_pgdump_row(raw_line, event_path, line_number)
            if event["event_uuid"] in record_ids:
                targets[event["event_uuid"]] = event
            if len(targets) == len(record_ids):
                break
    missing = sorted(record_ids.difference(targets))
    if missing:
        raise ValueError(f"records not found in {event_path}: {missing}")
    payloads = {
        record_id: {
            "event": event,
            "resolved_src_node": nodes.get(event["src_node"]),
            "resolved_dst_node": nodes.get(event["dst_node"]),
        }
        for record_id, event in targets.items()
    }
    source_manifest = load_json(
        EXPERIMENT_ROOT / "annotation" / "source_excerpts" / "c07_c11_v0.1" / "source_excerpt_manifest.json"
    )
    artifact_key = {
        "R04": "darpa_e5_R04_pidsmaker_event_table",
        "R05": "darpa_e5_R05_pidsmaker_event_table",
    }[source_code]
    source = source_manifest["source_artifacts"][artifact_key]
    inventory = []
    for role, key in (("bounded_event_file", "event_window"), ("resolved_node_file", "resolved_nodes")):
        row = source[key]
        inventory.append(
            {
                "role": role,
                "path": row["path"],
                "size_bytes": row["size_bytes"],
                "expected_sha256": row["sha256"],
                "hash_provenance": row["hash_provenance"],
            }
        )
    return payloads, inventory


def load_ecar_records(source_code: str, record_ids: set[str]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    filename = {
        "R06": "R06_sysclient0201_window.jsonl",
        "R07": "R07_sysclient0351_window.jsonl",
    }[source_code]
    path = EXPERIMENT_ROOT / "real_data" / "darpa_optc" / "extracted" / filename
    events = collect_jsonl_targets(path, record_ids, "id")
    payloads = {record_id: {"event": event} for record_id, event in events.items()}
    manifest = load_json(EXPERIMENT_ROOT / "real_data" / "darpa_optc" / "manifest.json")
    artifact_id = "r06_sysclient0201_window" if source_code == "R06" else "r07_sysclient0351_window"
    metadata = next(row for row in manifest["derived_artifacts"] if row["artifact_id"] == artifact_id)
    inventory = [
        {
            "role": "bounded_event_file",
            "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "size_bytes": path.stat().st_size,
            "expected_sha256": metadata["sha256"],
            "hash_provenance": "frozen_dataset_manifest",
        }
    ]
    return payloads, inventory


def otrf_line_number(pointer: dict[str, Any]) -> int:
    match = re.search(r"\bline\s+(\d+)\b", str(pointer.get("location") or ""))
    if not match:
        raise ValueError(f"OTRF source pointer has no line number: {pointer}")
    return int(match.group(1))


def load_otrf_records(claims: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    archive_path = EXPERIMENT_ROOT / "real_data" / "otrf_apt29" / "raw" / "apt29_evals_day1_manual.zip"
    target_by_line = {otrf_line_number(claim["source_pointer"]): claim for claim in claims}
    targets: dict[int, dict[str, Any]] = {}
    member_name = ""
    with zipfile.ZipFile(archive_path) as archive:
        members = [entry for entry in archive.infolist() if not entry.is_dir()]
        if len(members) != 1:
            raise ValueError(f"unexpected OTRF member count: {len(members)}")
        member_name = members[0].filename
        with archive.open(members[0]) as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                if line_number in target_by_line:
                    targets[line_number] = json.loads(raw_line)
                if len(targets) == len(target_by_line) and line_number >= max(target_by_line):
                    break
    missing = sorted(set(target_by_line).difference(targets))
    if missing:
        raise ValueError(f"OTRF lines not found: {missing}")
    payloads = {
        str(claim["source_pointer"]["record_id"]): {
            "event": targets[line_number],
            "line_number": line_number,
        }
        for line_number, claim in target_by_line.items()
    }
    source_manifest = load_json(
        EXPERIMENT_ROOT / "annotation" / "source_excerpts" / "c07_c11_v0.1" / "source_excerpt_manifest.json"
    )
    source = source_manifest["source_artifacts"]["otrf_apt29_day1_host_events"]
    inventory = [
        {
            "role": "zip_contained_event_file",
            "path": source["raw_parent"]["path"],
            "size_bytes": source["raw_parent"]["size_bytes"],
            "expected_sha256": source["raw_parent"]["sha256"],
            "hash_provenance": source["raw_parent"]["hash_provenance"],
            "archive_member": member_name,
            "archive_member_sha256": source["archive_member_sha256"],
        }
    ]
    return payloads, inventory


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
                    "values": [child.text for child in element if child.text and child.text.strip()],
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
        "document_sha256": BUILDER.sha256_file(path),
        "document_size_bytes": path.stat().st_size,
        "nodes": nodes,
        "edges": edges,
    }


def load_witfoo_records(claims: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    base = EXPERIMENT_ROOT / "real_data" / "witfoo_precinct6"
    lock = load_json(base / "c12_case_compile_lock_v0.1.json")
    incident_id = str(lock["selected_incident_id"])
    incident_path = base / "raw" / "incidents" / f"{incident_id}.json"
    graph_path = base / "raw" / "graphs" / f"{incident_id}.graphml"
    incident = load_json(incident_path)
    leads = incident.get("leads") or {}
    selection = lock["claim_selection"]
    product_name = str(selection["network_aggregate"]["product_name"])
    aggregate_leads = [
        lead
        for _, lead in sorted(leads.items())
        if str((lead.get("product") or {}).get("name") or "") == product_name
    ]
    payloads: dict[str, dict[str, Any]] = {}
    for claim in claims:
        record_id = str(claim["source_pointer"]["record_id"])
        if record_id.startswith("aggregate:"):
            payloads[record_id] = {"incident_id": incident.get("id"), "leads": aggregate_leads}
        elif record_id == incident_id:
            payloads[record_id] = graphml_payload(graph_path)
        else:
            lead = leads.get(record_id)
            if lead is None:
                raise ValueError(f"WitFoo lead not found: {record_id}")
            payloads[record_id] = {"incident_id": incident.get("id"), "lead": lead}
    inventory = [
        {
            "role": "incident_json",
            "path": str(incident_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "size_bytes": incident_path.stat().st_size,
            "expected_sha256": lock["input_integrity"]["incident_line_sha256"],
            "hash_provenance": "frozen_case_compile_lock_incident_line",
        },
        {
            "role": "incident_graphml",
            "path": str(graph_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "size_bytes": graph_path.stat().st_size,
            "expected_sha256": lock["input_integrity"]["graphml_sha256"],
            "hash_provenance": "frozen_case_compile_lock",
        },
    ]
    return payloads, inventory


def load_case_payloads(
    case_dir: Path,
    claims: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    prefix = case_prefix(str(claims[0]["case_id"]))
    _, family, source_code = CASE_LAYOUT[prefix]
    record_ids = {str(claim["source_pointer"]["record_id"]) for claim in claims}
    if family == "e3":
        return load_e3_records(source_code, record_ids)
    if family == "pgdump":
        return load_pgdump_records(source_code, record_ids)
    if family == "ecar":
        return load_ecar_records(source_code, record_ids)
    if family == "otrf":
        return load_otrf_records(claims)
    if family == "witfoo":
        return load_witfoo_records(claims)
    raise ValueError(f"unsupported source family: {family}")


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = first_string(value.get("string"), value.get("value"))
            if nested:
                return nested
    return None


def operation_token(payload: dict[str, Any]) -> str | None:
    event = payload.get("event") if isinstance(payload.get("event"), dict) else payload
    if event.get("event_type") or event.get("operation"):
        return str(event.get("event_type") or event.get("operation")).upper()
    if event.get("object") and event.get("action"):
        return f"{event['object']}:{event['action']}".upper()
    if event.get("EventID") is not None:
        return f"WINDOWS:{event['EventID']}".upper()
    lead = payload.get("lead") if isinstance(payload.get("lead"), dict) else None
    if lead:
        artifact = lead.get("artifact") if isinstance(lead.get("artifact"), dict) else {}
        if artifact.get("action") == "block" or lead.get("block"):
            return "WITFOO:BLOCK"
        for field in ("eventcode", "event_id", "EventID"):
            if artifact.get(field) is not None:
                return f"WITFOO:{artifact[field]}".upper()
    return None


def inferred_claim_type(predicate: str | None) -> str | None:
    return PREDICATE_CLAIM_TYPE.get(str(predicate)) if predicate else None


def public_target_contract(stage: str) -> tuple[list[str], list[str]]:
    predicates = sorted(STAGE_PREDICATE_ALLOWLIST.get(str(stage), set(PREDICATE_CLAIM_TYPE)))
    claim_types = sorted(
        {
            PREDICATE_CLAIM_TYPE.get(predicate, "other")
            for predicate in predicates
        }
    )
    return claim_types, predicates


def extract_scope(payload: dict[str, Any]) -> dict[str, str] | None:
    event = payload.get("event") if isinstance(payload.get("event"), dict) else {}
    scope: dict[str, str] = {}
    host = first_string(event.get("hostname"), event.get("Computer"), event.get("Hostname"))
    process_id = first_string(event.get("pid"), event.get("ProcessId"), event.get("ProcessID"))
    if host:
        scope["host_id"] = host
    if process_id:
        scope["process_id"] = process_id
    return scope or None


def nanos_to_iso(value: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(value) / 1_000_000_000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, OSError):
        return None


def extract_time_window(payload: dict[str, Any]) -> dict[str, str] | None:
    event = payload.get("event") if isinstance(payload.get("event"), dict) else {}
    value = first_string(
        event.get("timestamp"),
        event.get("@timestamp"),
        event.get("UtcTime"),
        event.get("TimeCreated"),
    )
    if not value and event.get("timestamp_nanos") is not None:
        value = nanos_to_iso(event.get("timestamp_nanos"))
    return {"start": value, "end": value} if value else None


def normalized_surface_status(claim: dict[str, Any], payload: dict[str, Any]) -> dict[str, bool]:
    tokens = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                tokens.append(str(key).casefold())
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif item is not None:
            tokens.append(str(item).casefold())

    visit(payload)
    return {
        "subject_surface_present": any(str(claim["subject"]["value"]).casefold() in token for token in tokens),
        "object_surface_present": any(str(claim["object"]["value"]).casefold() in token for token in tokens),
    }


def case_directories() -> list[Path]:
    root = EXPERIMENT_ROOT / "real_cases"
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and path.name[:3] in CASE_LAYOUT
    )


def build_case_bundle(case_dir: Path) -> dict[str, Any]:
    claims = sorted(load_json(case_dir / "evidence_claims.json"), key=lambda row: row["claim_id"])
    config = load_json(case_dir / "case_config.json")
    actions = load_json(case_dir / "acquisition_actions.json")
    canonical_case_id = str(config["case_id"])
    public_id = public_case_id(canonical_case_id)
    payload_by_record, source_inventory = load_case_payloads(case_dir, claims)
    claim_to_nodes: dict[str, list[str]] = {claim["claim_id"]: [] for claim in claims}
    public_node_by_canonical: dict[str, str] = {}
    for node in config["cti_nodes"]:
        public_node_by_canonical[node["node_id"]] = BUILDER.derive_scoped_id(
            "NODE", public_id, node["node_id"], length=16
        )
        for claim_id in node["required_claim_ids"]:
            claim_to_nodes.setdefault(claim_id, []).append(node["node_id"])

    artifacts: list[dict[str, Any]] = []
    private_claims: list[dict[str, Any]] = []
    artifact_by_claim: dict[str, str] = {}
    record_by_claim: dict[str, str] = {}
    present_source_types: set[str] = set()
    for claim in claims:
        original_record = str(claim["source_pointer"]["record_id"])
        if original_record not in payload_by_record:
            raise ValueError(f"unresolved claim pointer: {claim['claim_id']}")
        payload = scrub_public_source(payload_by_record[original_record])
        artifact_id = BUILDER.derive_scoped_id(
            "ART",
            public_id,
            claim["source_pointer"]["artifact_id"],
            original_record,
            claim["source_type"],
            length=16,
        )
        record_id = BUILDER.derive_scoped_id(
            "REC", public_id, claim["source_pointer"], length=16
        )
        pointer = claim["source_pointer"]
        line_start = pointer.get("line_start")
        if line_start is None and pointer.get("location"):
            match = re.search(r"\bline\s+(\d+)\b", str(pointer["location"]))
            line_start = int(match.group(1)) if match else None
        record = BUILDER.build_record(
            record_id,
            payload,
            location=pointer.get("location"),
            line_start=line_start,
            scope=extract_scope(payload),
            time_window=extract_time_window(payload),
        )
        artifact = BUILDER.build_artifact(
            artifact_id,
            claim["source_type"],
            [record],
            scope=extract_scope(payload),
        )
        artifacts.append(artifact)
        artifact_by_claim[claim["claim_id"]] = artifact_id
        record_by_claim[claim["claim_id"]] = record_id
        token = operation_token(payload)
        generic_predicate = GENERIC_PREDICATES.get(token or "")
        present_source_types.add(claim["source_type"])
        private_claims.append(
            {
                "canonical_claim_id": claim["claim_id"],
                "public_artifact_id": artifact_id,
                "public_record_id": record_id,
                "original_source_pointer": copy.deepcopy(claim["source_pointer"]),
                "public_target_node_ids": sorted(
                    public_node_by_canonical[node_id]
                    for node_id in claim_to_nodes.get(claim["claim_id"], [])
                ),
                "operation_token": token,
                "generic_predicate": generic_predicate,
                "reference_claim": copy.deepcopy(claim),
                "surface_diagnostic": normalized_surface_status(claim, payload),
            }
        )

    public_nodes = []
    for node in config["cti_nodes"]:
        allowed_types, allowed_predicates = public_target_contract(node["stage"])
        label = re.sub(r"^N\d+_?", "", node["node_id"]).replace("_", " ").strip()
        description = f"stage={node['stage']}; behavior={label or node['stage']}"
        public_nodes.append(
            BUILDER.build_target_node(
                public_node_by_canonical[node["node_id"]],
                description,
                allowed_claim_types=allowed_types,
                allowed_predicates=allowed_predicates,
            )
        )
    public_edges = [
        {
            "edge_id": BUILDER.derive_scoped_id("EDGE", public_id, edge["edge_id"], length=16),
            "source": public_node_by_canonical[edge["source"]],
            "target": public_node_by_canonical[edge["target"]],
        }
        for edge in config["cti_edges"]
    ]

    public_scenarios = []
    private_scenarios = []
    intensities = config.get("mask_intensities") or [config.get("mask_intensity", 0.4)]
    for strategy in config["mask_strategies"]:
        for intensity in intensities:
            for seed in config["random_seeds"]:
                hidden = RUN_MVP.build_hidden_claims(
                    config,
                    claims,
                    strategy,
                    int(seed),
                    float(intensity),
                )
                scenario_id = BUILDER.derive_scoped_id(
                    "SCN", public_id, strategy, intensity, seed
                )
                initial = sorted(
                    artifact_by_claim[claim["claim_id"]]
                    for claim in claims
                    if claim["claim_id"] not in hidden
                )
                public_scenarios.append(
                    {
                        "scenario_id": scenario_id,
                        "case_id": public_id,
                        "initial_visible_artifact_ids": initial,
                        "initial_visible_artifact_count": len(initial),
                    }
                )
                private_scenarios.append(
                    {
                        "scenario_id": scenario_id,
                        "canonical_case_id": canonical_case_id,
                        "mask_strategy": strategy,
                        "mask_intensity": float(intensity),
                        "random_seed": int(seed),
                        "hidden_claim_ids": sorted(hidden),
                    }
                )
    private_actions = []
    for action in actions:
        reveal_artifacts = sorted(
            {
                artifact_by_claim[claim_id]
                for claim_id in action.get("recoverable_claim_ids", [])
                if claim_id in artifact_by_claim
            }
        )
        private_actions.append(
            {
                "public_action_id": BUILDER.derive_scoped_id(
                    "ACT", public_id, action["action_id"], length=16
                ),
                "canonical_action_id": action["action_id"],
                "recoverable_claim_ids": sorted(action.get("recoverable_claim_ids", [])),
                "reveals_artifact_ids_on_success": reveal_artifacts,
                "acquisition_channel": RUN_MVP.acquisition_channel(action),
            }
        )

    public_case = {
        "case_id": public_id,
        "split": CASE_LAYOUT[case_prefix(canonical_case_id)][0],
        "nodes": sorted(public_nodes, key=lambda row: row["node_id"]),
        "edges": sorted(public_edges, key=lambda row: row["edge_id"]),
        "predicate_allowlist": {
            source: SOURCE_PREDICATE_ALLOWLIST.get(source, sorted(PREDICATE_CLAIM_TYPE))
            for source in sorted(present_source_types)
        },
        "stage_a_target_contract": "frozen_public_stage_vocabulary_v0.1_without_reference_claims",
    }
    private_case = {
        "canonical_case_id": canonical_case_id,
        "public_case_id": public_id,
        "claims": private_claims,
        "node_id_map": public_node_by_canonical,
        "actions": private_actions,
        "scenarios": private_scenarios,
    }
    return {
        "artifacts": sorted(artifacts, key=lambda row: row["artifact_id"]),
        "public_case": public_case,
        "public_scenarios": sorted(public_scenarios, key=lambda row: row["scenario_id"]),
        "private_case": private_case,
        "source_inventory": source_inventory,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl_gz(path: Path, rows: Iterable[Any]) -> None:
    payload = b"".join(BUILDER.canonical_json_bytes(row) + b"\n" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(payload, mtime=0))


def public_private_scan(public_values: Iterable[Any], private_values: Iterable[Any]) -> dict[str, Any]:
    for value in public_values:
        BUILDER.assert_public_boundary(value)
    private_ids: set[str] = set()
    for value in private_values:
        blob = BUILDER.canonical_json_text(value)
        private_ids.update(re.findall(r"\bC[0-9]{2}-EC-[0-9]{3}\b", blob))
    public_blob = "\n".join(BUILDER.canonical_json_text(value) for value in public_values)
    collisions = sorted(identifier for identifier in private_ids if identifier in public_blob)
    return {
        "status": "passed" if not collisions else "failed",
        "private_identifier_count": len(private_ids),
        "private_identifier_collisions": collisions,
    }


def build_all(output_dir: Path) -> dict[str, Any]:
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing non-empty WP2 output directory: {output}")
    bundles = [build_case_bundle(case_dir) for case_dir in case_directories()]
    artifacts = sorted(
        [artifact for bundle in bundles for artifact in bundle["artifacts"]],
        key=lambda row: row["artifact_id"],
    )
    public_cases = sorted(
        [bundle["public_case"] for bundle in bundles], key=lambda row: row["case_id"]
    )
    public_scenarios = sorted(
        [row for bundle in bundles for row in bundle["public_scenarios"]],
        key=lambda row: row["scenario_id"],
    )
    private_cases = [bundle["private_case"] for bundle in bundles]
    source_inventory = {
        bundle["public_case"]["case_id"]: bundle["source_inventory"]
        for bundle in bundles
    }
    artifact_catalog = {
        "catalog_version": "project05-mainline-compiler-artifacts-v0.1",
        "artifacts": [
            {
                "artifact_id": artifact["artifact_id"],
                "source_type": artifact["source_type"],
                "artifact_sha256": artifact["artifact_sha256"],
                "record_ids": [record["record_id"] for record in artifact["records"]],
                "record_count": len(artifact["records"]),
            }
            for artifact in artifacts
        ],
    }
    target_catalog = {
        "catalog_version": "project05-mainline-target-nodes-stage-a-v0.1",
        "cases": public_cases,
    }
    visibility_manifest = {
        "manifest_version": "project05-mainline-public-visibility-v0.1",
        "scenarios": public_scenarios,
        "mask_metadata_visible": False,
        "future_action_outcomes_visible": False,
    }
    private_reference = {
        "manifest_version": "project05-mainline-private-reference-v0.1",
        "scorer_only": True,
        "cases": private_cases,
    }
    private_execution = {
        "manifest_version": "project05-mainline-private-execution-v0.1",
        "compiler_visible": False,
        "planner_visible": False,
        "cases": [
            {
                "canonical_case_id": case["canonical_case_id"],
                "public_case_id": case["public_case_id"],
                "actions": case["actions"],
                "scenarios": case["scenarios"],
            }
            for case in private_cases
        ],
    }
    scan = public_private_scan(
        [artifact_catalog, target_catalog, visibility_manifest, *artifacts],
        [private_reference, private_execution],
    )
    surface_rows = [
        claim["surface_diagnostic"]
        for case in private_cases
        for claim in case["claims"]
    ]
    claim_count = sum(len(case["claims"]) for case in private_cases)
    action_count = sum(len(case["actions"]) for case in private_cases)
    report = {
        "report_id": "project05-mainline-compiler-wp2-data-readiness-v0.1",
        "status": (
            "passed_pointer_resolution_with_surface_diagnostics"
            if claim_count == 58 and scan["status"] == "passed"
            else "failed"
        ),
        "case_count": len(private_cases),
        "development_case_count": sum(case["split"] == "development" for case in public_cases),
        "test_case_count": sum(case["split"] == "test" for case in public_cases),
        "frozen_reference_claim_count": claim_count,
        "resolved_pointer_count": len(artifacts),
        "public_artifact_count": len(artifacts),
        "public_target_node_count": sum(len(case["nodes"]) for case in public_cases),
        "public_target_edge_count": sum(len(case["edges"]) for case in public_cases),
        "private_action_count": action_count,
        "public_visibility_scenario_count": len(public_scenarios),
        "reference_surface_diagnostic": {
            "subject_surface_present_count": sum(row["subject_surface_present"] for row in surface_rows),
            "object_surface_present_count": sum(row["object_surface_present"] for row in surface_rows),
            "both_surface_present_count": sum(
                row["subject_surface_present"] and row["object_surface_present"]
                for row in surface_rows
            ),
            "interpretation": "diagnostic_only; frozen author claims may aggregate or normalize raw fields",
        },
        "public_private_scan": scan,
        "source_inventory": source_inventory,
        "model_runtime_used": False,
        "training_used": False,
        "human_audit_required": False,
        "public_contract_reference_fields_used": False,
        "public_predicate_contract_policy": "fixed_observable_operation_and_public_stage_vocabulary_v0.1",
        "stage_a_limitation": (
            "target descriptions come from the frozen public case graph and use a fixed "
            "stage vocabulary without required_claim_ids or reference predicates; CTI text "
            "extraction is not evaluated in WP2"
        ),
    }
    write_jsonl_gz(output / "public" / "artifact_records.jsonl.gz", artifacts)
    write_json(output / "public" / "artifact_catalog.json", artifact_catalog)
    write_json(output / "public" / "target_node_catalog.json", target_catalog)
    write_json(output / "public" / "visibility_scenarios.json", visibility_manifest)
    write_json(output / "private" / "reference_map.json", private_reference)
    write_json(output / "private" / "execution_visibility.json", private_execution)
    write_json(output / "data-readiness.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_all(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
