#!/usr/bin/env python3
"""Create a content-agnostic, path-safe inventory for a ZIP archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def unsafe_member_reason(name: str) -> str | None:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or normalized.startswith("/"):
        return "absolute_path"
    if WINDOWS_DRIVE.match(normalized):
        return "windows_drive_path"
    if ".." in path.parts:
        return "parent_traversal"
    return None


def inspect_archive(path: Path, *, check_crc: bool = True) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    unsafe_members: list[dict[str, str]] = []

    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        for info in infos:
            reason = unsafe_member_reason(info.filename)
            if reason:
                unsafe_members.append(
                    {"name": info.filename, "reason": reason}
                )
            entries.append(
                {
                    "name": info.filename,
                    "is_directory": info.is_dir(),
                    "compressed_size": info.compress_size,
                    "uncompressed_size": info.file_size,
                    "crc32": f"{info.CRC:08X}",
                    "compression_method": info.compress_type,
                }
            )
        first_bad_crc_member = archive.testzip() if check_crc else None

    names = [entry["name"] for entry in entries]
    duplicate_names = sorted(
        name for name, count in Counter(names).items() if count > 1
    )
    folded = Counter(name.casefold() for name in names)
    casefold_collisions = sorted(
        name for name, count in folded.items() if count > 1
    )
    compressed_total = sum(entry["compressed_size"] for entry in entries)
    uncompressed_total = sum(entry["uncompressed_size"] for entry in entries)

    return {
        "archive_path": path.as_posix(),
        "archive_size_bytes": path.stat().st_size,
        "archive_sha256": sha256_file(path),
        "member_count": len(entries),
        "file_member_count": sum(not entry["is_directory"] for entry in entries),
        "compressed_member_bytes": compressed_total,
        "uncompressed_member_bytes": uncompressed_total,
        "aggregate_expansion_ratio": round(
            uncompressed_total / max(1, compressed_total),
            4,
        ),
        "path_safety_pass": not unsafe_members,
        "unsafe_members": unsafe_members,
        "duplicate_names": duplicate_names,
        "casefold_collisions": casefold_collisions,
        "crc_checked": check_crc,
        "first_bad_crc_member": first_bad_crc_member,
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-crc", action="store_true")
    args = parser.parse_args()

    result = inspect_archive(args.archive, check_crc=not args.skip_crc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output}")

    if not result["path_safety_pass"] or result["first_bad_crc_member"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
