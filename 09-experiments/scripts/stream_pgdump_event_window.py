#!/usr/bin/env python3
"""Stream a bounded PIDSMaker event_table window from a PGDMP archive.

The script deliberately avoids ``pgdumplib.load()`` because that method caches
every table locally. It reads only the archive catalog, then streams the COPY
payload for ``event_table`` and writes matching rows without materializing the
full provenance graph.

Run with the pinned temporary dependency, for example:

    uv run --no-project --with pgdumplib==4.0.0 python \
        09-experiments/scripts/stream_pgdump_event_window.py --help
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Generator, Iterable


EVENT_TABLE_COLUMNS = (
    "src_node",
    "src_index_id",
    "operation",
    "dst_node",
    "dst_index_id",
    "event_uuid",
    "timestamp_rec",
    "_id",
)


def utc_to_epoch_ns(value: str) -> int:
    """Convert an explicit UTC ISO-8601 timestamp to epoch nanoseconds."""

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("timestamp must use a UTC offset")

    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = parsed - epoch
    return (
        delta.days * 86_400_000_000_000
        + delta.seconds * 1_000_000_000
        + delta.microseconds * 1_000
    )


def event_timestamp_ns(row: bytes) -> int:
    """Read ``timestamp_rec`` from one tab-delimited event_table COPY row."""

    columns = row.rstrip(b"\r").split(b"\t")
    if len(columns) != len(EVENT_TABLE_COLUMNS):
        raise ValueError(
            "expected 8 COPY columns in event_table row, "
            f"found {len(columns)}"
        )
    try:
        return int(columns[6])
    except ValueError as exc:
        raise ValueError("event_table timestamp_rec is not an integer") from exc


def event_in_window(row: bytes, start_ns: int, end_ns: int) -> bool:
    """Return whether a row falls in a start-inclusive, end-exclusive window."""

    timestamp_ns = event_timestamp_ns(row)
    return start_ns <= timestamp_ns < end_ns


def require_pgdumplib() -> tuple[Any, Any]:
    """Load the optional archive parser only when archive work is requested."""

    try:
        from pgdumplib import constants
        from pgdumplib.dump import Dump
    except ImportError as exc:
        raise RuntimeError(
            "pgdumplib is required. Run with "
            "`uv run --no-project --with pgdumplib==4.0.0 python ...`."
        ) from exc
    return Dump, constants


def load_catalog(archive_path: Path) -> tuple[Any, Any]:
    """Load only PGDMP metadata and table-of-contents entries."""

    dump_class, constants = require_pgdumplib()

    class CatalogOnlyDump(dump_class):
        def _cache_table_data(self, dump_id: int) -> None:
            return None

        def _cache_blobs(self, dump_id: int) -> None:
            return None

    dump = CatalogOnlyDump().load(archive_path)
    return dump, constants


def find_table_data_entry(dump: Any, table_name: str) -> Any:
    """Return one public TABLE DATA entry by its table name."""

    entries = [
        entry
        for entry in dump.entries
        if entry.desc == "TABLE DATA"
        and entry.namespace == "public"
        and entry.tag == table_name
    ]
    if len(entries) != 1:
        raise ValueError(
            f"expected exactly one public.{table_name} TABLE DATA entry, "
            f"found {len(entries)}"
        )
    return entries[0]


def find_event_table_entry(dump: Any) -> Any:
    """Return the public.event_table data entry from a PIDSMaker archive."""

    return find_table_data_entry(dump, "event_table")


def iter_copy_lines(
    dump: Any,
    constants: Any,
    entry: Any,
) -> Generator[bytes, None, None]:
    """Yield COPY rows from one compressed custom-archive table entry."""

    if dump.compression_algorithm != constants.COMPRESSION_GZIP:
        raise ValueError(
            "only gzip-compatible PGDMP payloads are supported, got "
            f"{dump.compression_algorithm!r}"
        )
    if dump._handle is None:
        raise ValueError("archive handle is not initialized")

    dump._handle.seek(entry.offset)
    block_type, dump_id = dump._read_block_header()
    if block_type != constants.BLK_DATA or dump_id != entry.dump_id:
        raise ValueError(
            "event_table archive block does not match its table-of-contents entry"
        )

    decompressor = zlib.decompressobj()
    buffer = b""
    saw_terminator = False

    def complete_lines(data: bytes) -> tuple[list[bytes], bytes]:
        pieces = data.split(b"\n")
        return pieces[:-1], pieces[-1]

    while True:
        chunk_size = dump._read_int()
        if chunk_size <= 0:
            break
        compressed = dump._handle.read(chunk_size)
        if len(compressed) != chunk_size:
            raise ValueError("truncated compressed PGDMP payload")

        buffer += decompressor.decompress(compressed)
        lines, buffer = complete_lines(buffer)
        for line in lines:
            if line == b"\\.":
                saw_terminator = True
                break
            if line:
                yield line
        if saw_terminator:
            return

        if chunk_size < constants.ZLIB_IN_SIZE:
            buffer += decompressor.flush()
            lines, buffer = complete_lines(buffer)
            for line in lines:
                if line == b"\\.":
                    saw_terminator = True
                    break
                if line:
                    yield line
            if saw_terminator:
                return
            break

    if not saw_terminator:
        raise ValueError("event_table COPY payload ended without a terminator")


def archive_catalog_payload(dump: Any) -> dict[str, Any]:
    """Create a small serializable catalog record without raw data."""

    table_entries = []
    for entry in dump.entries:
        if entry.desc != "TABLE DATA":
            continue
        table_entries.append(
            {
                "schema": entry.namespace,
                "table": entry.tag,
                "dump_id": entry.dump_id,
                "offset": entry.offset,
                "copy_statement": entry.copy_stmt.strip(),
            }
        )
    return {
        "archive_version": ".".join(str(part) for part in dump.version),
        "database": dump.dbname,
        "server_version": dump.server_version,
        "dump_version": dump.dump_version,
        "archive_timestamp": dump.timestamp.isoformat(),
        "compression_algorithm": dump.compression_algorithm,
        "entry_count": len(dump.entries),
        "table_data_entries": table_entries,
    }


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().upper()


def relative_display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


def stream_window(
    archive_path: Path,
    output_path: Path,
    summary_path: Path,
    start_utc: str,
    end_utc: str,
    catalog_path: Path | None = None,
) -> dict[str, Any]:
    """Extract one full-scan event window and emit reproducibility metadata."""

    start_ns = utc_to_epoch_ns(start_utc)
    end_ns = utc_to_epoch_ns(end_utc)
    if start_ns >= end_ns:
        raise ValueError("start UTC timestamp must be earlier than end UTC timestamp")
    if not archive_path.is_file():
        raise ValueError(f"missing archive: {archive_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    if catalog_path is not None:
        catalog_path.parent.mkdir(parents=True, exist_ok=True)

    dump, constants = load_catalog(archive_path)
    try:
        entry = find_event_table_entry(dump)
        catalog = archive_catalog_payload(dump)
        if catalog_path is not None:
            catalog_path.write_text(
                json.dumps(catalog, indent=2) + "\n",
                encoding="utf-8",
            )

        rows_scanned = 0
        rows_selected = 0
        timestamp_inversions = 0
        first_scanned_timestamp_ns: int | None = None
        previous_timestamp_ns: int | None = None
        last_scanned_timestamp_ns: int | None = None
        minimum_timestamp_ns: int | None = None
        maximum_timestamp_ns: int | None = None

        with output_path.open("wb") as output:
            for row in iter_copy_lines(dump, constants, entry):
                timestamp_ns = event_timestamp_ns(row)
                rows_scanned += 1
                if first_scanned_timestamp_ns is None:
                    first_scanned_timestamp_ns = timestamp_ns
                    minimum_timestamp_ns = timestamp_ns
                    maximum_timestamp_ns = timestamp_ns
                else:
                    minimum_timestamp_ns = min(minimum_timestamp_ns, timestamp_ns)
                    maximum_timestamp_ns = max(maximum_timestamp_ns, timestamp_ns)
                if (
                    previous_timestamp_ns is not None
                    and timestamp_ns < previous_timestamp_ns
                ):
                    timestamp_inversions += 1
                previous_timestamp_ns = timestamp_ns
                last_scanned_timestamp_ns = timestamp_ns

                if start_ns <= timestamp_ns < end_ns:
                    output.write(row)
                    output.write(b"\n")
                    rows_selected += 1

        summary = {
            "source_format": "PostgreSQL custom archive (PGDMP)",
            "archive_path": relative_display_path(archive_path),
            "archive_size_bytes": archive_path.stat().st_size,
            "archive_sha256": sha256_file(archive_path),
            "event_table": {
                "schema": entry.namespace,
                "table": entry.tag,
                "columns": list(EVENT_TABLE_COLUMNS),
                "dump_id": entry.dump_id,
            },
            "utc_window": {"start": start_utc, "end": end_utc},
            "timestamp_window_ns": {"start": start_ns, "end": end_ns},
            "rows_scanned": rows_scanned,
            "rows_selected": rows_selected,
            "first_scanned_timestamp_ns": first_scanned_timestamp_ns,
            "last_scanned_timestamp_ns": last_scanned_timestamp_ns,
            "minimum_scanned_timestamp_ns": minimum_timestamp_ns,
            "maximum_scanned_timestamp_ns": maximum_timestamp_ns,
            "timestamp_inversions": timestamp_inversions,
            "timestamp_monotonic_non_decreasing": timestamp_inversions == 0,
            "scan_scope": "full_event_table",
            "output_path": relative_display_path(output_path),
            "output_sha256": sha256_file(output_path),
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
        description="Stream a bounded PIDSMaker event_table window from PGDMP."
    )
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--start-utc", required=True)
    parser.add_argument("--end-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--catalog-json", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = stream_window(
        archive_path=args.archive,
        output_path=args.output,
        summary_path=args.summary,
        start_utc=args.start_utc,
        end_utc=args.end_utc,
        catalog_path=args.catalog_json,
    )
    print(
        "Extracted "
        f"{summary['rows_selected']} / {summary['rows_scanned']} event rows "
        f"to {summary['output_path']}"
    )


if __name__ == "__main__":
    main()
