#!/usr/bin/env python3
"""Read-only CDM18 remote-endpoint-summary pilot executor for C02/R02.

The adapter is intentionally narrower than the planner action type.  It proves
that one real case-scoped network summary can be executed and measured without
using legacy cost, recoverable claims, hidden claims, or oracle effects.  It does
not infer which observed endpoints are external because R02 has no frozen local
network boundary and its local addresses include publicly routable space.
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
ALLOWLISTED_INVOCATION = {
    "case_id": "C02",
    "action_id": "C02-AA-003",
    "action_type": "recover_network_summary",
    "target_type": "case",
    "target_value": "R02 external endpoints",
}


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
    target = request.get("target")
    observed = {
        "case_id": request.get("case_id"),
        "action_id": request.get("action_id"),
        "action_type": request.get("action_type"),
        "target_type": target.get("target_type") if isinstance(target, dict) else None,
        "target_value": target.get("target_value") if isinstance(target, dict) else None,
    }
    if observed != ALLOWLISTED_INVOCATION:
        raise ValueError("adapter only supports the allow-listed R02 case target")


def iter_jsonl(
    path: Path, accounting: ScanAccounting
) -> Iterable[tuple[bytes, dict[str, Any]]]:
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


def protocol_scalar(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, dict) and isinstance(value.get("string"), str):
        return value["string"] or None
    return None


def endpoint_key(raw: dict[str, Any]) -> tuple[str, int, str | None] | None:
    remote_address = raw.get("remoteAddress")
    remote_port = raw.get("remotePort")
    if not isinstance(remote_address, str) or not remote_address:
        return None
    if isinstance(remote_port, bool) or not isinstance(remote_port, int) or remote_port < 0:
        return None
    return remote_address, remote_port, protocol_scalar(raw.get("ipProtocol"))


def new_endpoint_summary(key: tuple[str, int, str | None]) -> dict[str, Any]:
    return {
        "remote_address": key[0],
        "remote_port": key[1],
        "ip_protocol": key[2],
        "netflow_object_count": 0,
        "local_addresses": set(),
        "local_ports": set(),
        "unknown_local_port_count": 0,
        "source_node_uuids": set(),
    }


def add_netflow_object(summary: dict[str, Any], node: dict[str, Any]) -> None:
    raw = node["raw"]
    summary["netflow_object_count"] += 1
    local_address = raw.get("localAddress")
    if isinstance(local_address, str) and local_address:
        summary["local_addresses"].add(local_address)
    local_port = raw.get("localPort")
    if isinstance(local_port, int) and not isinstance(local_port, bool) and local_port >= 0:
        summary["local_ports"].add(local_port)
    else:
        summary["unknown_local_port_count"] += 1
    node_uuid = node.get("node_uuid")
    if isinstance(node_uuid, str) and node_uuid:
        summary["source_node_uuids"].add(node_uuid)


def serializable_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "remote_address": summary["remote_address"],
        "remote_port": summary["remote_port"],
        "ip_protocol": summary["ip_protocol"],
        "netflow_object_count": summary["netflow_object_count"],
        "local_addresses": sorted(summary["local_addresses"]),
        "local_ports": sorted(summary["local_ports"]),
        "unknown_local_port_count": summary["unknown_local_port_count"],
        "source_node_uuids": sorted(summary["source_node_uuids"]),
    }


def write_summary_line(handle: BinaryIO, digest: Any, row: dict[str, Any]) -> None:
    payload = (
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
    handle.write(payload)
    digest.update(payload)


def execute_case_target(
    request: dict[str, Any], nodes_path: Path, output_dir: Path
) -> dict[str, Any]:
    """Execute the single-node-file form of the bounded R02 case pilot."""

    return execute_case_target_shards(request, [nodes_path], output_dir)


def execute_case_target_shards(
    request: dict[str, Any], node_paths: list[Path], output_dir: Path
) -> dict[str, Any]:
    """Summarize observed remote endpoints with measured raw-input telemetry.

    One primitive operation is one raw JSONL source line read.  Every immutable
    node input is read once for SHA-256 integrity and once for extraction.  The
    external/internal classification remains unresolved and is never inferred
    from RFC1918 membership, threat labels, planner effects, or ground truth.
    """

    validate_request(request)
    node_paths = [Path(path) for path in node_paths]
    output_dir = Path(output_dir)
    if not node_paths or not all(path.is_file() for path in node_paths):
        raise FileNotFoundError("node JSONL shards must all exist")
    if len({path.resolve() for path in node_paths}) != len(node_paths):
        raise ValueError("node shard paths must be unique within one logical execution")
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite observation output: {output_dir}")

    accounting = ScanAccounting()
    memory = MemoryIntegral()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    started_utc = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )

    node_integrity = [
        {"path": path.resolve().as_posix(), "sha256": sha256_by_line(path, accounting)}
        for path in node_paths
    ]
    memory.checkpoint()

    endpoints: dict[tuple[str, int, str | None], dict[str, Any]] = {}
    netflow_object_count = 0
    unusable_netflow_object_count = 0
    missing_protocol_object_count = 0
    unknown_local_port_count = 0
    for node_path in node_paths:
        for _, node in iter_jsonl(node_path, accounting):
            if node.get("record_type") != "NetFlowObject":
                continue
            raw = node.get("raw")
            if not isinstance(raw, dict):
                unusable_netflow_object_count += 1
                continue
            key = endpoint_key(raw)
            if key is None:
                unusable_netflow_object_count += 1
                continue
            netflow_object_count += 1
            if key[2] is None:
                missing_protocol_object_count += 1
            local_port = raw.get("localPort")
            if (
                isinstance(local_port, bool)
                or not isinstance(local_port, int)
                or local_port < 0
            ):
                unknown_local_port_count += 1
            summary = endpoints.setdefault(key, new_endpoint_summary(key))
            add_netflow_object(summary, node)
    memory.checkpoint()

    output_dir.mkdir(parents=True, exist_ok=False)
    summary_path = output_dir / "observed-remote-endpoints.jsonl"
    summary_sha256 = hashlib.sha256()
    with summary_path.open("wb") as summary_output:
        for key in sorted(endpoints, key=lambda item: (item[0], item[1], item[2] or "")):
            write_summary_line(
                summary_output, summary_sha256, serializable_summary(endpoints[key])
            )
    memory.checkpoint()

    adapter_source_path = Path(__file__).resolve()
    adapter_source_sha256 = hashlib.sha256(adapter_source_path.read_bytes()).hexdigest()
    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    ended_utc = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )
    return {
        "adapter_id": "project05-recover-network-summary-r02-case-pilot-v0.1",
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
        "termination_reason": "completed_observed_remote_endpoint_summary_external_classification_unresolved",
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
            "nodes": node_integrity[0] if len(node_integrity) == 1 else None,
            "node_shards": node_integrity,
        },
        "observation": {
            "schema_id": "project05-cdm18-observed-remote-endpoint-summary-v0.1",
            "summarization_key": "exact (remoteAddress, remotePort, ipProtocol) tuple; missing protocol retained as null",
            "requested_scope_status": "partial_external_classification_unresolved",
            "external_classification": {
                "status": "unresolved",
                "reason": "No pre-registered local-network boundary is available for R02; RFC1918 membership is not a valid substitute because observed local addresses include publicly routable space.",
                "external_endpoint_count": None,
            },
            "netflow_object_count": netflow_object_count,
            "unusable_netflow_object_count": unusable_netflow_object_count,
            "missing_protocol_object_count": missing_protocol_object_count,
            "unknown_local_port_count": unknown_local_port_count,
            "observed_remote_endpoint_count": len(endpoints),
            "evidence_perturbations": [],
            "downtime_seconds": 0.0,
            "artifacts": {
                "remote_endpoints": {
                    "path": summary_path.resolve().as_posix(),
                    "sha256": summary_sha256.hexdigest(),
                }
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
    parser.add_argument("--nodes", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--result-path", type=Path)
    args = parser.parse_args()
    request = {
        "case_id": args.case_id,
        "action_id": args.action_id,
        "action_type": "recover_network_summary",
        "target": {"target_type": "case", "target_value": args.target},
    }
    result = execute_case_target_shards(request, args.nodes, args.output_dir)
    if args.result_path is not None:
        write_execution_result(args.result_path, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
