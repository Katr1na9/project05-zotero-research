#!/usr/bin/env python3
"""Read-only file-target CDM18 provenance-subgraph pilot executor.

This adapter deliberately accepts a small, safe invocation contract instead of a
legacy planner action.  In particular, legacy scalar cost, recoverable claims,
hidden claims, and oracle effects are not admissible inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterable

import psutil


FORBIDDEN_PLANNER_ORACLE_FIELDS = frozenset(
    {"recoverable_claim_ids", "oracle_effects", "hidden_claim_ids"}
)
ALLOWED_REQUEST_FIELDS = frozenset({"case_id", "action_id", "action_type", "target"})
EVENT_ENDPOINT_FIELDS = (
    "subject_uuid",
    "predicate_object_uuid",
    "predicate_object_2_uuid",
)
TARGET_PATH_FIELDS = ("predicateObjectPath", "predicateObject2Path")


class ScanAccounting:
    def __init__(self) -> None:
        self.bytes_scanned = 0
        self.records_scanned = 0

    def add_line(self, raw_line: bytes) -> None:
        self.bytes_scanned += len(raw_line)
        self.records_scanned += 1


class MemoryIntegral:
    """Trapezoidal RSS integral sampled at named execution boundaries."""

    def __init__(self) -> None:
        self._process = psutil.Process(os.getpid())
        self._last_time = time.perf_counter()
        self._last_rss = self._process.memory_info().rss
        self.byte_seconds = 0.0

    def checkpoint(self) -> None:
        current_time = time.perf_counter()
        current_rss = self._process.memory_info().rss
        self.byte_seconds += (
            (self._last_rss + current_rss) / 2.0
        ) * (current_time - self._last_time)
        self._last_time = current_time
        self._last_rss = current_rss


def validate_request(request: dict[str, Any]) -> None:
    forbidden = sorted(set(request) & FORBIDDEN_PLANNER_ORACLE_FIELDS)
    if forbidden:
        raise ValueError(f"forbidden planner-oracle fields: {forbidden}")
    unknown = sorted(set(request) - ALLOWED_REQUEST_FIELDS)
    if unknown:
        raise ValueError(f"unsupported invocation fields: {unknown}")
    missing = sorted(ALLOWED_REQUEST_FIELDS - set(request))
    if missing:
        raise ValueError(f"missing invocation fields: {missing}")
    if request["action_type"] != "query_host_subgraph":
        raise ValueError("adapter only supports query_host_subgraph actions")
    target = request["target"]
    if not isinstance(target, dict) or target.get("target_type") != "file":
        raise ValueError("file target is required for this pilot adapter")
    if not isinstance(target.get("target_value"), str) or not target["target_value"]:
        raise ValueError("file target_value must be a non-empty string")
    for field in ("case_id", "action_id"):
        if not isinstance(request[field], str) or not request[field]:
            raise ValueError(f"{field} must be a non-empty string")


def iter_jsonl(path: Path, accounting: ScanAccounting) -> Iterable[tuple[bytes, dict[str, Any]]]:
    with path.open("rb") as handle:
        for raw_line in handle:
            accounting.add_line(raw_line)
            if not raw_line.strip():
                continue
            value = json.loads(raw_line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL record must be an object: {path}")
            yield raw_line, value


def sha256_by_line(path: Path, accounting: ScanAccounting) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for raw_line in handle:
            accounting.add_line(raw_line)
            digest.update(raw_line)
    return digest.hexdigest()


def endpoint_uuids(event: dict[str, Any]) -> set[str]:
    return {
        value
        for field in EVENT_ENDPOINT_FIELDS
        if isinstance((value := event.get(field)), str) and value
    }


def path_scalar(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("string"), str):
        return value["string"]
    return None


def event_matches_exact_file_target(event: dict[str, Any], target_value: str) -> bool:
    raw = event.get("raw")
    if not isinstance(raw, dict):
        return False
    return any(path_scalar(raw.get(field)) == target_value for field in TARGET_PATH_FIELDS)


def write_raw_line(handle: BinaryIO, digest: Any, raw_line: bytes) -> None:
    handle.write(raw_line)
    digest.update(raw_line)


def execute_file_target(
    request: dict[str, Any],
    events_path: Path,
    nodes_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Execute the single-event-file form of the file-target pilot."""

    return execute_file_target_shards(request, [events_path], nodes_path, output_dir)


def execute_file_target_shards(
    request: dict[str, Any],
    event_paths: list[Path],
    nodes_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Extract a one-hop file provenance subgraph with measured raw telemetry.

    The primitive boundary is one raw JSONL source line read.  The adapter first
    verifies every immutable source input by line, then performs one seed scan and
    one incident-event expansion scan across the ordered event shards, plus one
    node-resolution scan. It writes only derived evidence to ``output_dir`` and
    never changes any source file.
    """

    validate_request(request)
    event_paths = [Path(path) for path in event_paths]
    nodes_path = Path(nodes_path)
    output_dir = Path(output_dir)
    if not event_paths or not all(path.is_file() for path in event_paths) or not nodes_path.is_file():
        raise FileNotFoundError("event shards and nodes JSONL input must all exist")
    if len({path.resolve() for path in event_paths}) != len(event_paths):
        raise ValueError("event shard paths must be unique within one logical execution")
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite observation output: {output_dir}")

    accounting = ScanAccounting()
    memory = MemoryIntegral()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    started_utc = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )

    event_integrity = [
        {"path": path.resolve().as_posix(), "sha256": sha256_by_line(path, accounting)}
        for path in event_paths
    ]
    nodes_sha256 = sha256_by_line(nodes_path, accounting)
    memory.checkpoint()

    target_value = request["target"]["target_value"]
    seed_nodes: set[str] = set()
    target_match_event_count = 0
    for event_path in event_paths:
        for _, event in iter_jsonl(event_path, accounting):
            if event_matches_exact_file_target(event, target_value):
                target_match_event_count += 1
                seed_nodes.update(endpoint_uuids(event))
    memory.checkpoint()

    output_dir.mkdir(parents=True, exist_ok=False)
    event_output_path = output_dir / "subgraph-events.jsonl"
    node_output_path = output_dir / "subgraph-nodes.jsonl"
    selected_nodes: set[str] = set()
    subgraph_event_count = 0
    event_output_sha256 = hashlib.sha256()
    with event_output_path.open("wb") as event_output:
        for event_path in event_paths:
            for raw_line, event in iter_jsonl(event_path, accounting):
                endpoints = endpoint_uuids(event)
                if endpoints & seed_nodes:
                    write_raw_line(event_output, event_output_sha256, raw_line)
                    selected_nodes.update(endpoints)
                    subgraph_event_count += 1
    memory.checkpoint()

    subgraph_node_count = 0
    node_output_sha256 = hashlib.sha256()
    with node_output_path.open("wb") as node_output:
        for raw_line, node in iter_jsonl(nodes_path, accounting):
            node_uuid = node.get("node_uuid")
            if isinstance(node_uuid, str) and node_uuid in selected_nodes:
                write_raw_line(node_output, node_output_sha256, raw_line)
                subgraph_node_count += 1
    memory.checkpoint()

    adapter_source_path = Path(__file__).resolve()
    adapter_source_sha256 = hashlib.sha256(adapter_source_path.read_bytes()).hexdigest()
    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    ended_utc = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )
    return {
        "adapter_id": "project05-query-host-subgraph-file-pilot-v0.1",
        "adapter_source": {
            "path": adapter_source_path.as_posix(),
            "sha256": adapter_source_sha256,
        },
        "invocation": {
            "case_id": request["case_id"],
            "action_id": request["action_id"],
            "action_type": request["action_type"],
            "target": dict(request["target"]),
        },
        "started_utc": started_utc,
        "ended_utc": ended_utc,
        "execution_status": "completed",
        "termination_reason": "completed_after_integrity_seed_one_hop_and_node_resolution_scans",
        "primitive_operation_definition": "one raw JSONL source line read, including immutable-input integrity scans",
        "primitive_operation_count": accounting.records_scanned,
        "resource_trace": {
            "analyst_time_by_role": [],
            "compute": {
                "wall_seconds": wall_seconds,
                "cpu_seconds": cpu_seconds,
                "memory_byte_seconds": memory.byte_seconds,
            },
            "data_access": {
                "bytes_scanned": accounting.bytes_scanned,
                "records_scanned": accounting.records_scanned,
            },
            "direct_currency": {"amount": 0.0, "currency": "CNY"},
            "authorization_wait_seconds": 0.0,
            "shared_overhead": {
                "setup_seconds": 0.0,
                "allocation_status": "unallocated",
                "allocation_rule": None,
            },
        },
        "input_integrity": {
            "events": event_integrity[0] if len(event_integrity) == 1 else None,
            "event_shards": event_integrity,
            "nodes": {"path": nodes_path.resolve().as_posix(), "sha256": nodes_sha256},
        },
        "observation": {
            "schema_id": "project05-cdm18-file-one-hop-subgraph-v0.1",
            "one_hop_definition": "all event records with at least one endpoint UUID in the exact-target seed endpoint set",
            "target_match_event_count": target_match_event_count,
            "seed_node_count": len(seed_nodes),
            "subgraph_event_count": subgraph_event_count,
            "subgraph_node_count": subgraph_node_count,
            "evidence_perturbations": [],
            "downtime_seconds": 0.0,
            "artifacts": {
                "events": {
                    "path": event_output_path.resolve().as_posix(),
                    "sha256": event_output_sha256.hexdigest(),
                },
                "nodes": {
                    "path": node_output_path.resolve().as_posix(),
                    "sha256": node_output_sha256.hexdigest(),
                },
            },
        },
    }


def write_execution_result(path: Path, result: dict[str, Any]) -> None:
    """Persist one adapter run without allowing a prior record to be replaced."""

    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite pilot run record: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--action-id", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--nodes", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--result-path", type=Path)
    args = parser.parse_args()
    result = execute_file_target(
        {
            "case_id": args.case_id,
            "action_id": args.action_id,
            "action_type": "query_host_subgraph",
            "target": {"target_type": "file", "target_value": args.target},
        },
        args.events,
        args.nodes,
        args.output_dir,
    )
    if args.result_path is not None:
        write_execution_result(args.result_path, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
