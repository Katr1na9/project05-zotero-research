#!/usr/bin/env python3
"""Decode one local claim source excerpt to stdout without writing plaintext."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def decode_source_payload(value: Any) -> Any:
    if isinstance(value, dict):
        if set(value) == {"__encoding__", "value"}:
            if value["__encoding__"] != "utf8_hex":
                raise ValueError(f"unsupported source encoding: {value}")
            return bytes.fromhex(value["value"]).decode("utf-8")
        return {
            key: decode_source_payload(item) for key, item in value.items()
        }
    if isinstance(value, list):
        return [decode_source_payload(item) for item in value]
    return value


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="View one locally held canonical claim source excerpt."
    )
    parser.add_argument("blind_id")
    parser.add_argument(
        "--input",
        type=Path,
        default=(
            root
            / "09-experiments"
            / "annotation"
            / "source_excerpts"
            / "c07_c11_v0.1"
            / "local"
            / "claim_source_excerpts.jsonl"
        ),
    )
    args = parser.parse_args()
    with args.input.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row["blind_id"] != args.blind_id:
                continue
            decoded = decode_source_payload(row["source_excerpt"])
            output = {
                "blind_id": row["blind_id"],
                "source_pointer": row["source_pointer"],
                "record_locator": row["record_locator"],
                "source_excerpt": decoded,
                "excerpt_sha256": row["excerpt_sha256"],
            }
            print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
            return
    raise SystemExit(f"blind_id not found: {args.blind_id}")


if __name__ == "__main__":
    main()
