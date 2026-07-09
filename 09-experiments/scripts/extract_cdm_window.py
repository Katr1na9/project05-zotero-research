#!/usr/bin/env python3
"""Stream a DARPA TC CDM archive into a bounded event/node evidence subset."""

from __future__ import annotations

import argparse
import json
import sqlite3
import tarfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


EVENT_TYPE = "Event"
UUID_FIELDS = ("subject", "predicateObject", "predicateObject2")


def unwrap_value(value: Any) -> Any:
    while isinstance(value, dict) and len(value) == 1:
        value = next(iter(value.values()))
    return value


def parse_record(line: bytes) -> tuple[str, dict[str, Any]]:
    line = line.strip()
    if line.endswith(b","):
        line = line[:-1]
    payload = json.loads(line)
    datum = payload["datum"]
    full_type, record = next(iter(datum.items()))
    return full_type.rsplit(".", 1)[-1], record


def event_references(record: dict[str, Any]) -> set[str]:
    return {
        value
        for field in UUID_FIELDS
        if (value := unwrap_value(record.get(field))) is not None
        and isinstance(value, str)
    }


def normalize_event(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": EVENT_TYPE,
        "event_uuid": unwrap_value(record.get("uuid")),
        "timestamp_nanos": int(unwrap_value(record["timestampNanos"])),
        "event_type": unwrap_value(record.get("type")),
        "subject_uuid": unwrap_value(record.get("subject")),
        "predicate_object_uuid": unwrap_value(record.get("predicateObject")),
        "predicate_object_2_uuid": unwrap_value(record.get("predicateObject2")),
        "raw": record,
    }


def iter_archive_lines(archive: Path) -> Iterable[bytes]:
    with tarfile.open(archive, "r|gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            stream = tar.extractfile(member)
            if stream is None:
                continue
            yield from stream


def iso_to_epoch_nanos(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    seconds = int(parsed.timestamp())
    return seconds * 1_000_000_000 + parsed.microsecond * 1_000


def extract_archive_window(
    archive: Path,
    output_dir: Path,
    case_id: str,
    start_ns: int,
    end_ns: int,
) -> dict[str, Any]:
    if start_ns > end_ns:
        raise ValueError("start_ns must not exceed end_ns")

    output_dir.mkdir(parents=True, exist_ok=True)
    events_path = output_dir / "events.jsonl"
    nodes_path = output_dir / "nodes.jsonl"
    index_path = output_dir / "node_index.sqlite"
    report_path = output_dir / "report.json"
    index_path.unlink(missing_ok=True)

    connection = sqlite3.connect(index_path)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute(
        """
        CREATE TABLE nodes (
            uuid TEXT PRIMARY KEY,
            record_type TEXT NOT NULL,
            raw_json TEXT NOT NULL
        )
        """
    )

    record_counts: Counter[str] = Counter()
    referenced_nodes: set[str] = set()
    invalid_lines = 0
    events_extracted = 0
    node_batch: list[tuple[str, str, str]] = []

    try:
        with events_path.open("w", encoding="utf-8") as events_file:
            for line in iter_archive_lines(archive):
                if not line.strip():
                    continue
                try:
                    record_type, record = parse_record(line)
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    invalid_lines += 1
                    continue

                record_counts[record_type] += 1
                if record_type == EVENT_TYPE:
                    try:
                        event = normalize_event(record)
                    except (KeyError, TypeError, ValueError):
                        invalid_lines += 1
                        continue
                    if start_ns <= event["timestamp_nanos"] <= end_ns:
                        events_file.write(
                            json.dumps(event, ensure_ascii=False) + "\n"
                        )
                        referenced_nodes.update(event_references(record))
                        events_extracted += 1
                    continue

                node_uuid = unwrap_value(record.get("uuid"))
                if not isinstance(node_uuid, str):
                    continue
                node_batch.append(
                    (
                        node_uuid,
                        record_type,
                        json.dumps(record, ensure_ascii=False),
                    )
                )
                if len(node_batch) >= 10_000:
                    connection.executemany(
                        "INSERT OR REPLACE INTO nodes VALUES (?, ?, ?)",
                        node_batch,
                    )
                    node_batch.clear()

        if node_batch:
            connection.executemany(
                "INSERT OR REPLACE INTO nodes VALUES (?, ?, ?)",
                node_batch,
            )
        connection.commit()

        resolved: dict[str, tuple[str, str]] = {}
        ordered_refs = sorted(referenced_nodes)
        for offset in range(0, len(ordered_refs), 900):
            chunk = ordered_refs[offset : offset + 900]
            placeholders = ",".join("?" for _ in chunk)
            for uuid, record_type, raw_json in connection.execute(
                f"""
                SELECT uuid, record_type, raw_json
                FROM nodes
                WHERE uuid IN ({placeholders})
                """,
                chunk,
            ):
                resolved[uuid] = (record_type, raw_json)

        with nodes_path.open("w", encoding="utf-8") as nodes_file:
            for uuid in sorted(resolved):
                record_type, raw_json = resolved[uuid]
                nodes_file.write(
                    json.dumps(
                        {
                            "record_type": record_type,
                            "node_uuid": uuid,
                            "raw": json.loads(raw_json),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
    finally:
        connection.close()

    unresolved = sorted(referenced_nodes - resolved.keys())
    report = {
        "case_id": case_id,
        "source_archive": archive.name,
        "context_window_nanos": {
            "start": start_ns,
            "end": end_ns,
        },
        "record_counts": dict(sorted(record_counts.items())),
        "invalid_lines": invalid_lines,
        "events_extracted": events_extracted,
        "referenced_nodes": len(referenced_nodes),
        "nodes_resolved": len(resolved),
        "unresolved_node_uuids": unresolved,
        "outputs": {
            "events": events_path.name,
            "nodes": nodes_path.name,
            "node_index": index_path.name,
        },
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    case = json.loads(args.case.read_text(encoding="utf-8"))
    window = case["utc_window"]
    report = extract_archive_window(
        archive=args.archive,
        output_dir=args.output_dir,
        case_id=case["case_id"],
        start_ns=iso_to_epoch_nanos(window["start"]),
        end_ns=iso_to_epoch_nanos(window["end"]),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
