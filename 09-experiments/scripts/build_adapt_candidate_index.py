#!/usr/bin/env python3
"""Build provider-wide malicious process candidates from ADAPT E3 contexts."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
from typing import TextIO


PROVIDERS = ("5dir", "cadets")


def open_context(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(
            path,
            "rt",
            encoding="utf-8",
            errors="replace",
            newline="",
        )
    return path.open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline="",
    )


def context_name(path: Path) -> str:
    name = path.name
    if name.endswith(".csv.gz"):
        return name[: -len(".csv.gz")]
    if name.endswith(".csv"):
        return name[: -len(".csv")]
    return path.stem


def load_ground_truth(provider_dir: Path, provider: str) -> set[str]:
    path = provider_dir / f"{provider}_main.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            row["uuid"]
            for row in csv.DictReader(handle)
            if row.get("uuid")
        }


def build_provider_index(
    provider_dir: Path,
    provider: str,
) -> dict:
    ground_truth = load_ground_truth(provider_dir, provider)
    processes = {
        uuid: {}
        for uuid in sorted(ground_truth)
    }
    matched: set[str] = set()
    context_stats: dict[str, dict[str, int]] = {}

    context_paths = sorted(provider_dir.glob("Process*.csv*"))
    for path in context_paths:
        name = context_name(path)
        matched_in_context = 0
        with open_context(path) as handle:
            reader = csv.reader(handle)
            header = next(reader)
            for row in reader:
                if not row or row[0] not in ground_truth:
                    continue
                matched.add(row[0])
                matched_in_context += 1
                processes[row[0]][name] = sorted(
                    {
                        header[index]
                        for index, value in enumerate(row[1:], start=1)
                        if value == "1" and header[index]
                    }
                )
        context_stats[name] = {
            "matched_process_count": matched_in_context,
        }

    return {
        "provider": provider,
        "ground_truth_count": len(ground_truth),
        "matched_uuid_count": len(matched),
        "missing_uuids": sorted(ground_truth - matched),
        "episode_assignment": "unresolved_without_raw_time",
        "context_stats": context_stats,
        "processes": processes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--adapt-root",
        type=Path,
        required=True,
        help="Path containing ADAPT E3 main/5dir and main/cadets.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()

    main_dir = args.adapt_root / "main"
    result = {
        "source_repository": "https://gitlab.com/adaptdata/e3",
        "source_commit": args.source_commit,
        "limitations": [
            "Provider-wide ground truth is not separated by episode.",
            "Contexts omit event timestamps and original provenance edges.",
            "UUIDs are candidates for later lookup in official CDM data.",
        ],
        "providers": {
            provider: build_provider_index(
                main_dir / provider,
                provider,
            )
            for provider in PROVIDERS
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
