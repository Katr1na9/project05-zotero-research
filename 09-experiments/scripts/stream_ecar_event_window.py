#!/usr/bin/env python3
"""Stream a hostname-bounded OpTC eCAR window into JSONL.

Supports plain JSONL, gzip JSONL, and AV-bypass password zips
(``.zip.passwdOPTC2019`` with password ``OPTC2019``).

This script only filters by hostname substring and inclusive/exclusive UTC
wall-clock bounds. It does not invent motifs or tune planners.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterator


DEFAULT_ZIP_PASSWORD = b"OPTC2019"


def parse_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must be timezone-aware: {value}")
    return parsed.astimezone(timezone.utc)


def event_timestamp_utc(event: dict[str, Any]) -> datetime:
    raw = event.get("timestamp")
    if raw is None:
        raise ValueError("eCAR event missing timestamp")
    if isinstance(raw, (int, float)):
        # epoch milliseconds
        return datetime.fromtimestamp(float(raw) / 1000.0, tz=timezone.utc)
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(f"naive eCAR timestamp: {raw}")
    return parsed.astimezone(timezone.utc)


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_hostname(value: str) -> str:
    return value.strip().rstrip(".").casefold()


def hostname_matches(hostname: str, needles: list[str]) -> bool:
    value = canonical_hostname(hostname)
    return any(canonical_hostname(needle) in value for needle in needles)


def hostname_exact_matches(hostname: str, expected_hosts: set[str]) -> bool:
    return canonical_hostname(hostname) in expected_hosts


def open_ecar_lines(path: Path, zip_password: bytes) -> Iterator[bytes]:
    """Yield raw JSON lines from jsonl / gz / password-zip inputs."""

    name = path.name.casefold()
    if "cryptoptc" in name:
        raise ValueError(
            f"Unsupported .cryptOPTC2019 input: {path}. "
            "Use the .zip.passwdOPTC2019 alternative or decrypt it upstream."
        )
    if name.endswith(".zip") or "passwdoptc" in name:
        with zipfile.ZipFile(path) as archive:
            members = [info for info in archive.infolist() if not info.is_dir()]
            if not members:
                raise ValueError(f"empty zip archive: {path}")
            # Prefer the largest member (the eCAR payload).
            member = max(members, key=lambda info: info.file_size)
            with archive.open(member, pwd=zip_password) as handle:
                member_name = member.filename.casefold()
                if member_name.endswith(".gz"):
                    with gzip.GzipFile(fileobj=handle) as gz_handle:
                        yield from iter_lines(gz_handle)
                else:
                    yield from iter_lines(handle)
        return

    if name.endswith(".gz"):
        with gzip.open(path, "rb") as handle:
            yield from iter_lines(handle)
        return

    with path.open("rb") as handle:
        yield from iter_lines(handle)


def iter_lines(handle: BinaryIO) -> Iterator[bytes]:
    for line in handle:
        if line.strip():
            yield line


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


def temporary_sibling(path: Path) -> Path:
    descriptor, name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    return Path(name)


def stream_window(
    inputs: list[Path],
    output_path: Path,
    summary_path: Path,
    hostnames: list[str],
    start_utc: str,
    end_utc: str,
    zip_password: bytes = DEFAULT_ZIP_PASSWORD,
    exact_hostnames: list[str] | None = None,
) -> dict[str, Any]:
    start = parse_utc(start_utc)
    end = parse_utc(end_utc)
    if start >= end:
        raise ValueError("start UTC must be earlier than end UTC")

    contains_hosts = [value for value in hostnames if value.strip()]
    exact_hosts = [value for value in (exact_hostnames or []) if value.strip()]
    if contains_hosts and exact_hosts:
        raise ValueError("provide hostname contains filters or exact hostnames, not both")
    if exact_hosts:
        hostname_match_mode = "exact"
        selected_hosts = exact_hosts
        expected_hostnames = {canonical_hostname(value) for value in exact_hosts}
    elif contains_hosts:
        hostname_match_mode = "contains"
        selected_hosts = contains_hosts
        expected_hostnames = set()
    else:
        raise ValueError("at least one hostname filter is required")

    if not inputs:
        raise ValueError("at least one input is required")
    for input_path in inputs:
        if not input_path.is_file():
            raise ValueError(f"missing input: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.resolve() == summary_path.resolve():
        raise ValueError("output and summary paths must differ")
    output_path_resolved = output_path.resolve()
    summary_path_resolved = summary_path.resolve()
    for input_path in inputs:
        input_resolved = input_path.resolve()
        if input_resolved in {output_path_resolved, summary_path_resolved}:
            raise ValueError("input paths must not overwrite output or summary paths")

    rows_scanned = 0
    rows_selected = 0
    rows_bad_json = 0
    rows_bad_timestamp = 0
    host_counts: dict[str, int] = {}
    object_counts: dict[str, int] = {}
    first_selected: datetime | None = None
    last_selected: datetime | None = None
    output_hasher = hashlib.sha256()
    temporary_output: Path | None = None
    temporary_summary: Path | None = None

    try:
        temporary_output = temporary_sibling(output_path)
        with temporary_output.open("w", encoding="utf-8", newline="\n") as output:
            for input_path in inputs:
                for raw_line in open_ecar_lines(input_path, zip_password):
                    rows_scanned += 1
                    try:
                        event = json.loads(raw_line)
                    except json.JSONDecodeError:
                        rows_bad_json += 1
                        continue
                    hostname = str(event.get("hostname") or "")
                    if hostname_match_mode == "exact":
                        matches_hostname = hostname_exact_matches(
                            hostname, expected_hostnames
                        )
                    else:
                        matches_hostname = hostname_matches(hostname, contains_hosts)
                    if not matches_hostname:
                        continue
                    try:
                        stamp = event_timestamp_utc(event)
                    except (ValueError, OverflowError, OSError):
                        rows_bad_timestamp += 1
                        continue
                    if stamp < start or stamp >= end:
                        continue

                    encoded = (
                        json.dumps(event, ensure_ascii=False, separators=(",", ":"))
                        + "\n"
                    )
                    output.write(encoded)
                    output_hasher.update(encoded.encode("utf-8"))
                    rows_selected += 1
                    host_counts[hostname] = host_counts.get(hostname, 0) + 1
                    object_name = str(event.get("object") or "")
                    object_counts[object_name] = object_counts.get(object_name, 0) + 1
                    if first_selected is None or stamp < first_selected:
                        first_selected = stamp
                    if last_selected is None or stamp > last_selected:
                        last_selected = stamp

        summary = {
            "source_format": "OpTC eCAR JSONL",
            "inputs": [relative_display_path(path) for path in inputs],
            "input_sha256": [sha256_file(path) for path in inputs],
            "hostnames": selected_hosts,
            "hostname_match_mode": hostname_match_mode,
            "utc_window": {"start": start_utc, "end": end_utc},
            "rows_scanned": rows_scanned,
            "rows_selected": rows_selected,
            "rows_bad_json": rows_bad_json,
            "rows_bad_timestamp": rows_bad_timestamp,
            "selected_host_counts": host_counts,
            "selected_object_counts": object_counts,
            "first_selected_timestamp_utc": (
                utc_iso(first_selected) if first_selected is not None else None
            ),
            "last_selected_timestamp_utc": (
                utc_iso(last_selected) if last_selected is not None else None
            ),
            "output_path": relative_display_path(output_path),
            "output_sha256": output_hasher.hexdigest().upper(),
            "scan_scope": "hostname_and_utc_window",
            "notes": [
                "Engineering extractor only; do not retune M3a from extraction stats.",
                "Passworded AV-bypass zips use OPTC2019 unless --zip-password overrides.",
                "cryptOPTC2019 files are rejected; use the password-zip twin or decrypt upstream.",
            ],
        }
        temporary_summary = temporary_sibling(summary_path)
        temporary_summary.write_text(
            json.dumps(summary, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_output.replace(output_path)
        temporary_output = None
        temporary_summary.replace(summary_path)
        temporary_summary = None
        return summary
    finally:
        for temporary_path in (temporary_output, temporary_summary):
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stream a hostname-bounded OpTC eCAR window to JSONL."
    )
    parser.add_argument(
        "--input",
        type=Path,
        action="append",
        required=True,
        help="eCAR jsonl/gz/password-zip path (repeatable)",
    )
    hostname_group = parser.add_mutually_exclusive_group(required=True)
    hostname_group.add_argument(
        "--hostname",
        action="append",
        help="Exact canonical hostname filter (repeatable, case-insensitive)",
    )
    hostname_group.add_argument(
        "--hostname-contains",
        action="append",
        help="Hostname substring filter (repeatable, case-insensitive)",
    )
    parser.add_argument("--start-utc", required=True)
    parser.add_argument("--end-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument(
        "--zip-password",
        default="OPTC2019",
        help="Password for AV-bypass zip inputs (default: OPTC2019)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = stream_window(
        inputs=args.input,
        output_path=args.output,
        summary_path=args.summary,
        hostnames=args.hostname_contains or [],
        start_utc=args.start_utc,
        end_utc=args.end_utc,
        zip_password=args.zip_password.encode("utf-8"),
        exact_hostnames=args.hostname or [],
    )
    print(
        f"Extracted {summary['rows_selected']} / {summary['rows_scanned']} "
        f"eCAR rows to {summary['output_path']}"
    )


if __name__ == "__main__":
    main()
