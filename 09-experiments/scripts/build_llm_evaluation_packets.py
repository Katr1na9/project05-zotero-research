#!/usr/bin/env python3
"""Build deterministic, physically separated LLM evaluation packets."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


FORBIDDEN_PUBLIC_KEYS = {
    "acceptable_observations",
    "canonical_claim_id",
    "claim_id",
    "gold_claim_id",
    "recoverable_claim_ids",
    "required_claim_ids",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def digest_id(prefix: str, payload: bytes) -> str:
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:24].upper()}"


def derive_request_id(public_body: dict[str, Any]) -> str:
    body = {key: value for key, value in public_body.items() if key != "request_id"}
    return digest_id("REQ", canonical_json(body))


def derive_candidate_claim_id(
    request_id: str,
    condition_id: str,
    attempt_index: int,
    output_index: int,
) -> str:
    payload = (
        f"{request_id}|{condition_id}|{attempt_index}|{output_index}".encode(
            "utf-8"
        )
    )
    return digest_id("CC", payload)


def derive_gold_claim_id(case_id: str, canonical_claim_id: str) -> str:
    return digest_id(
        "GOLD", f"{case_id}|{canonical_claim_id}".encode("utf-8")
    )


def make_packet_record(
    source_type: str,
    source_pointer: dict[str, str],
    source_payload: dict[str, Any],
) -> dict[str, Any]:
    pointer = {
        "artifact_id": str(source_pointer["artifact_id"]),
        "record_id": str(source_pointer["record_id"]),
    }
    return {
        "packet_record_id": digest_id("REC", canonical_json(pointer)),
        "source_type": str(source_type),
        "source_pointer": pointer,
        "record_sha256": sha256_bytes(canonical_json(source_payload)),
        "source_payload": source_payload,
    }


def build_packet_pair(
    case_id: str,
    split: str,
    packet_role: str,
    support_ceiling: str,
    records: list[dict[str, Any]],
    acceptable_observations: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    public = {
        "case_id": case_id,
        "split": split,
        "packet_role": packet_role,
        "support_ceiling": support_ceiling,
        "records": sorted(records, key=lambda item: item["packet_record_id"]),
    }
    public["request_id"] = derive_request_id(public)

    private_observations = []
    for observation in acceptable_observations:
        canonical_claim_id = str(observation["canonical_claim_id"])
        private_observation = {
            key: value
            for key, value in observation.items()
            if key != "gold_claim_id"
        }
        private_observation["gold_claim_id"] = derive_gold_claim_id(
            case_id, canonical_claim_id
        )
        private_observations.append(private_observation)
    private_observations.sort(key=lambda item: item["gold_claim_id"])
    private = {
        "request_id": public["request_id"],
        "case_id": case_id,
        "packet_role": packet_role,
        "acceptable_observations": private_observations,
    }
    assert_public_safe(public)
    return public, private


def iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_keys(item)


def assert_public_safe(value: Any) -> None:
    present = FORBIDDEN_PUBLIC_KEYS & set(iter_keys(value))
    if present:
        raise ValueError(f"forbidden private keys in public payload: {sorted(present)}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b"".join(canonical_json(row) + b"\n" for row in rows)
    path.write_bytes(gzip.compress(payload, mtime=0))


def private_identifiers(private_rows: Iterable[dict[str, Any]]) -> set[str]:
    identifiers: set[str] = set()
    for row in private_rows:
        for observation in row.get("acceptable_observations", []):
            for key in ("canonical_claim_id", "gold_claim_id"):
                value = observation.get(key)
                if value:
                    identifiers.add(str(value))
    return identifiers


def write_bundle(
    output_dir: Path,
    public_rows: list[dict[str, Any]],
    private_rows: list[dict[str, Any]],
    public_catalog: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"refusing to overwrite non-empty bundle: {output_dir}")
    if [row["request_id"] for row in public_rows] != [
        row["request_id"] for row in private_rows
    ]:
        raise ValueError("public/private request ordering mismatch")

    for row in public_rows:
        assert_public_safe(row)
    assert_public_safe(public_catalog)

    public_projection = {
        "packets": public_rows,
        "catalog": public_catalog,
        "metadata": metadata,
    }
    serialized_public = canonical_json(public_projection).decode("utf-8")
    leaked = sorted(
        identifier
        for identifier in private_identifiers(private_rows)
        if identifier in serialized_public
    )
    if leaked:
        raise ValueError(f"private identifiers leaked into public payload: {leaked}")

    public_dir = output_dir / "public"
    private_dir = output_dir / "private"
    packets_path = public_dir / "context_packets.jsonl.gz"
    catalog_path = public_dir / "public_cti_catalog.json"
    input_manifest_path = public_dir / "input_manifest.json"
    gold_path = private_dir / "observation_gold.jsonl.gz"
    gold_manifest_path = private_dir / "gold_manifest.json"

    write_jsonl_gz(packets_path, public_rows)
    write_json(catalog_path, public_catalog)
    input_manifest = {
        **metadata,
        "packet_count": len(public_rows),
        "separation_status": "separated",
        "private_identifiers_included": False,
        "files": {
            "context_packets.jsonl.gz": sha256_file(packets_path),
            "public_cti_catalog.json": sha256_file(catalog_path),
        },
    }
    write_json(input_manifest_path, input_manifest)

    write_jsonl_gz(gold_path, private_rows)
    gold_manifest = {
        **metadata,
        "packet_count": len(private_rows),
        "separation_status": "private_scorer_only",
        "public_input_manifest_sha256": sha256_file(input_manifest_path),
        "observation_gold_sha256": sha256_file(gold_path),
    }
    write_json(gold_manifest_path, gold_manifest)
    return input_manifest


if __name__ == "__main__":
    raise SystemExit(
        "Packet source adapters are added in the next implementation task."
    )
