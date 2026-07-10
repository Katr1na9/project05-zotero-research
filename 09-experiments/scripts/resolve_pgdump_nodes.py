#!/usr/bin/env python3
"""Resolve node hashes from a bounded PIDSMaker event window.

The event table stores node hash IDs. This script streams the three node tables
in the same PGDMP archive and emits only descriptors referenced by the already
extracted event window. Run it with the same temporary dependency as the event
extractor:

    uv run --no-project --with pgdumplib==4.0.0 python \
        09-experiments/scripts/resolve_pgdump_nodes.py --help
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


STREAMER_PATH = Path(__file__).with_name("stream_pgdump_event_window.py")
STREAMER_SPEC = importlib.util.spec_from_file_location(
    "stream_pgdump_event_window",
    STREAMER_PATH,
)
streamer = importlib.util.module_from_spec(STREAMER_SPEC)
assert STREAMER_SPEC.loader is not None
STREAMER_SPEC.loader.exec_module(streamer)


NODE_TABLE_SCHEMAS = {
    "file_node_table": (
        "file",
        ("node_uuid", "hash_id", "path", "index_id"),
    ),
    "netflow_node_table": (
        "netflow",
        (
            "node_uuid",
            "hash_id",
            "src_addr",
            "src_port",
            "dst_addr",
            "dst_port",
            "index_id",
        ),
    ),
    "subject_node_table": (
        "subject",
        ("node_uuid", "hash_id", "path", "cmd", "index_id"),
    ),
}


def read_event_node_hashes(event_path: Path) -> set[str]:
    """Collect hash IDs from the source and destination columns of events."""

    hashes: set[str] = set()
    with event_path.open("rb") as handle:
        for line_number, row in enumerate(handle, start=1):
            columns = row.rstrip(b"\r\n").split(b"\t")
            if len(columns) != len(streamer.EVENT_TABLE_COLUMNS):
                raise ValueError(
                    f"{event_path}:{line_number}: expected "
                    f"{len(streamer.EVENT_TABLE_COLUMNS)} COPY columns, "
                    f"found {len(columns)}"
                )
            hashes.add(columns[0].decode("ascii"))
            hashes.add(columns[3].decode("ascii"))
    return hashes


def node_record_from_copy_row(table_name: str, row: bytes) -> dict[str, str]:
    """Decode one PIDSMaker node-table COPY row into a compact JSON record."""

    try:
        node_type, field_names = NODE_TABLE_SCHEMAS[table_name]
    except KeyError as exc:
        raise ValueError(f"unsupported node table: {table_name}") from exc

    columns = row.rstrip(b"\r").split(b"\t")
    if len(columns) != len(field_names):
        raise ValueError(
            f"{table_name}: expected {len(field_names)} COPY columns, "
            f"found {len(columns)}"
        )
    record = {
        field_name: value.decode("utf-8", errors="replace")
        for field_name, value in zip(field_names, columns, strict=True)
    }
    record["node_type"] = node_type
    return record


def resolve_node_subset(
    archive_path: Path,
    event_path: Path,
    output_path: Path,
    summary_path: Path,
) -> dict[str, Any]:
    """Resolve only node records referenced by the extracted event window."""

    if not event_path.is_file():
        raise ValueError(f"missing event window: {event_path}")
    if not archive_path.is_file():
        raise ValueError(f"missing archive: {archive_path}")

    requested_hashes = read_event_node_hashes(event_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    dump, constants = streamer.load_catalog(archive_path)
    try:
        matched_hashes: set[str] = set()
        rows_scanned_by_table: dict[str, int] = {}
        matches_by_table: dict[str, int] = {}

        with output_path.open("w", encoding="utf-8", newline="\n") as output:
            for table_name in NODE_TABLE_SCHEMAS:
                entry = streamer.find_table_data_entry(dump, table_name)
                rows_scanned = 0
                matches = 0
                for row in streamer.iter_copy_lines(dump, constants, entry):
                    rows_scanned += 1
                    record = node_record_from_copy_row(table_name, row)
                    if record["hash_id"] not in requested_hashes:
                        continue
                    output.write(json.dumps(record, sort_keys=True))
                    output.write("\n")
                    matched_hashes.add(record["hash_id"])
                    matches += 1
                rows_scanned_by_table[table_name] = rows_scanned
                matches_by_table[table_name] = matches

        unresolved = requested_hashes - matched_hashes
        summary = {
            "archive_path": streamer.relative_display_path(archive_path),
            "event_path": streamer.relative_display_path(event_path),
            "output_path": streamer.relative_display_path(output_path),
            "event_node_hashes": len(requested_hashes),
            "resolved_node_hashes": len(matched_hashes),
            "unresolved_node_hashes": len(unresolved),
            "rows_scanned_by_table": rows_scanned_by_table,
            "matches_by_table": matches_by_table,
            "output_sha256": streamer.sha256_file(output_path),
        }
        summary_path.write_text(
            json.dumps(summary, indent=2) + "\n",
            encoding="utf-8",
        )
        return summary
    finally:
        if dump._handle is not None:
            dump._handle.close()
        dump._temp_dir.cleanup()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve node hashes from a bounded PIDSMaker event window."
    )
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = resolve_node_subset(
        archive_path=args.archive,
        event_path=args.events,
        output_path=args.output,
        summary_path=args.summary,
    )
    print(
        "Resolved "
        f"{summary['resolved_node_hashes']} / {summary['event_node_hashes']} "
        f"node hashes to {summary['output_path']}"
    )


if __name__ == "__main__":
    main()
