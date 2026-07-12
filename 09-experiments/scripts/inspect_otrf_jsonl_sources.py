#!/usr/bin/env python3
"""Stream structural statistics from OTRF host and Zeek JSONL sources."""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO


def sorted_counts(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def canonical_host(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "<missing>"
    return value.split(".", 1)[0].upper()


def parse_iso_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def update_range(
    current_min: datetime | None,
    current_max: datetime | None,
    value: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    if value is None:
        return current_min, current_max
    return (
        value if current_min is None or value < current_min else current_min,
        value if current_max is None or value > current_max else current_max,
    )


def iso_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat().replace("+00:00", "Z")


def scan_host_stream(handle: BinaryIO, expected_hosts: set[str]) -> dict[str, Any]:
    rows = 0
    malformed = 0
    malformed_line_numbers: list[int] = []
    hosts: Counter[str] = Counter()
    channels: Counter[str] = Counter()
    providers: Counter[str] = Counter()
    event_ids: Counter[str] = Counter()
    minimum: datetime | None = None
    maximum: datetime | None = None

    for line_number, raw_line in enumerate(handle, start=1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            malformed += 1
            if len(malformed_line_numbers) < 20:
                malformed_line_numbers.append(line_number)
            continue
        rows += 1
        hosts[canonical_host(event.get("Hostname"))] += 1
        channels[str(event.get("Channel", "<missing>"))] += 1
        providers[str(event.get("SourceName", "<missing>"))] += 1
        event_ids[str(event.get("EventID", "<missing>"))] += 1
        minimum, maximum = update_range(
            minimum,
            maximum,
            parse_iso_utc(event.get("@timestamp")),
        )

    return {
        "parsed_rows": rows,
        "malformed_rows": malformed,
        "malformed_line_numbers": malformed_line_numbers,
        "timestamp_field": "@timestamp",
        "timestamp_min_utc": iso_or_none(minimum),
        "timestamp_max_utc": iso_or_none(maximum),
        "host_counts": sorted_counts(hosts),
        "expected_host_rows": {
            host: hosts.get(host, 0) for host in sorted(expected_hosts)
        },
        "channel_counts": sorted_counts(channels),
        "provider_counts": sorted_counts(providers),
        "event_id_counts": sorted_counts(event_ids),
    }


def scan_zeek_stream(path: Path) -> dict[str, Any]:
    rows = 0
    malformed = 0
    malformed_line_numbers: list[int] = []
    streams: Counter[str] = Counter()
    minimum: datetime | None = None
    maximum: datetime | None = None

    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                malformed += 1
                if len(malformed_line_numbers) < 20:
                    malformed_line_numbers.append(line_number)
                continue
            rows += 1
            streams[str(event.get("@stream", "<missing>"))] += 1
            try:
                timestamp = datetime.fromtimestamp(
                    float(event["ts"]),
                    tz=timezone.utc,
                )
            except (KeyError, TypeError, ValueError, OSError):
                timestamp = None
            minimum, maximum = update_range(minimum, maximum, timestamp)

    return {
        "parsed_rows": rows,
        "malformed_rows": malformed,
        "malformed_line_numbers": malformed_line_numbers,
        "timestamp_field": "ts",
        "timestamp_min_utc": iso_or_none(minimum),
        "timestamp_max_utc": iso_or_none(maximum),
        "stream_counts": sorted_counts(streams),
    }


def inspect_sources(
    host_archive: Path,
    zeek_log: Path,
    expected_hosts: set[str],
) -> dict[str, Any]:
    with zipfile.ZipFile(host_archive) as archive:
        file_members = [item for item in archive.infolist() if not item.is_dir()]
        if len(file_members) != 1:
            raise ValueError(
                f"Expected one host JSONL member, found {len(file_members)}"
            )
        member = file_members[0]
        with archive.open(member) as handle:
            host_summary = scan_host_stream(handle, expected_hosts)

    zeek_summary = scan_zeek_stream(zeek_log)
    host_summary["archive_member"] = member.filename
    host_summary["member_uncompressed_bytes"] = member.file_size
    return {
        "inspection_scope": "structural fields only; no IOC or motif search",
        "expected_hosts": sorted(expected_hosts),
        "host_events": host_summary,
        "zeek_events": zeek_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host-archive", type=Path, required=True)
    parser.add_argument("--zeek-log", type=Path, required=True)
    parser.add_argument("--expected-host", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = inspect_sources(
        args.host_archive,
        args.zeek_log,
        {canonical_host(value) for value in args.expected_host},
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
