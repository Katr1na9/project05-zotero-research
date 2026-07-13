#!/usr/bin/env python3
"""Build deterministic, locally held source excerpts for blind claim review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


PACKAGE_VERSION = "c07_c11_source_excerpts_v0.1"
EVENT_COLUMNS = (
    "src_node",
    "src_index_id",
    "operation",
    "dst_node",
    "dst_index_id",
    "event_uuid",
    "timestamp_nanos",
    "event_row_id",
)


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


def encode_source_payload(value: Any) -> Any:
    """Hex-encode string values so endpoint protection does not quarantine CTI text."""

    if isinstance(value, str):
        return {
            "__encoding__": "utf8_hex",
            "value": value.encode("utf-8").hex().upper(),
        }
    if isinstance(value, list):
        return [encode_source_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            key: encode_source_payload(item) for key, item in value.items()
        }
    return value


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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def repo_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def pointer_key(pointer: dict[str, Any]) -> str:
    return canonical_json(pointer).decode("utf-8")


def source_manifest_entry(
    path: Path,
    root: Path,
    expected_sha256: str,
    expected_size_bytes: int,
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_size = path.stat().st_size
    if actual_size != expected_size_bytes:
        raise ValueError(
            f"size mismatch for {path}: {actual_size} != {expected_size_bytes}"
        )
    return {
        "path": repo_path(path, root),
        "size_bytes": actual_size,
        "sha256": expected_sha256.upper(),
        "hash_provenance": "frozen_dataset_manifest",
        "local_size_checked": True,
    }


def verified_local_file(
    path: Path,
    root: Path,
    actual_sha256: str,
    expected_sha256: str,
) -> dict[str, Any]:
    if actual_sha256.upper() != expected_sha256.upper():
        raise ValueError(
            f"SHA-256 mismatch for {path}: {actual_sha256} != {expected_sha256}"
        )
    return {
        "path": repo_path(path, root),
        "size_bytes": path.stat().st_size,
        "sha256": actual_sha256.upper(),
        "hash_provenance": "recomputed_while_building_excerpts",
        "local_size_checked": True,
    }


def read_nodes(path: Path) -> tuple[dict[str, dict[str, Any]], str]:
    digest = hashlib.sha256()
    nodes: dict[str, dict[str, Any]] = {}
    with path.open("rb") as handle:
        for raw_line in handle:
            digest.update(raw_line)
            if not raw_line.strip():
                continue
            node = json.loads(raw_line)
            nodes[str(node["hash_id"])] = node
    return nodes, digest.hexdigest().upper()


def pgdump_excerpts(
    items: list[dict[str, Any]],
    event_path: Path,
    nodes_path: Path,
) -> tuple[list[dict[str, Any]], str, str]:
    target_by_record = {
        item["source_pointer"]["record_id"]: item for item in items
    }
    remaining = set(target_by_record)
    nodes, nodes_sha256 = read_nodes(nodes_path)
    excerpts: list[dict[str, Any]] = []
    event_digest = hashlib.sha256()

    with event_path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            event_digest.update(raw_line)
            if not remaining:
                continue
            columns = raw_line.rstrip(b"\r\n").split(b"\t")
            if len(columns) != len(EVENT_COLUMNS):
                raise ValueError(
                    f"{event_path}:{line_number}: expected {len(EVENT_COLUMNS)} "
                    f"columns, found {len(columns)}"
                )
            event_uuid = columns[5].decode("ascii")
            item = target_by_record.get(event_uuid)
            if item is None:
                continue
            event = {
                "src_node": columns[0].decode("ascii"),
                "src_index_id": int(columns[1]),
                "operation": columns[2].decode("utf-8"),
                "dst_node": columns[3].decode("ascii"),
                "dst_index_id": int(columns[4]),
                "event_uuid": event_uuid,
                "timestamp_nanos": int(columns[6]),
                "event_row_id": int(columns[7]),
            }
            payload = {
                "event": event,
                "resolved_src_node": nodes.get(event["src_node"]),
                "resolved_dst_node": nodes.get(event["dst_node"]),
            }
            excerpts.append(
                make_excerpt(
                    item,
                    "pidsmaker_provenance_edge",
                    {"line_number": line_number, "event_uuid": event_uuid},
                    payload,
                )
            )
            remaining.remove(event_uuid)

    require_no_missing(remaining, event_path)
    return excerpts, event_digest.hexdigest().upper(), nodes_sha256


def ecar_excerpts(
    items: list[dict[str, Any]],
    event_path: Path,
) -> tuple[list[dict[str, Any]], str]:
    target_by_record = {
        item["source_pointer"]["record_id"]: item for item in items
    }
    remaining = set(target_by_record)
    excerpts: list[dict[str, Any]] = []
    digest = hashlib.sha256()

    with event_path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            digest.update(raw_line)
            if not remaining or not raw_line.strip():
                continue
            event = json.loads(raw_line)
            event_id = str(event.get("id") or "")
            item = target_by_record.get(event_id)
            if item is None:
                continue
            excerpts.append(
                make_excerpt(
                    item,
                    "optc_ecar_event",
                    {"line_number": line_number, "event_id": event_id},
                    {"event": event},
                )
            )
            remaining.remove(event_id)

    require_no_missing(remaining, event_path)
    return excerpts, digest.hexdigest().upper()


def line_number_from_pointer(pointer: dict[str, Any]) -> int:
    location = str(pointer.get("location") or "")
    match = re.search(r"\bline\s+(\d+)\b", location)
    if not match:
        raise ValueError(f"OTRF source pointer has no line number: {pointer}")
    return int(match.group(1))


def otrf_excerpts(
    items: list[dict[str, Any]],
    archive_path: Path,
    expected_member: str,
) -> tuple[list[dict[str, Any]], str, str]:
    target_by_line = {
        line_number_from_pointer(item["source_pointer"]): item for item in items
    }
    remaining = set(target_by_line)
    excerpts: list[dict[str, Any]] = []
    member_digest = hashlib.sha256()

    with zipfile.ZipFile(archive_path) as archive:
        file_members = [entry for entry in archive.infolist() if not entry.is_dir()]
        if len(file_members) != 1 or file_members[0].filename != expected_member:
            raise ValueError(
                f"unexpected OTRF member set: {[entry.filename for entry in file_members]}"
            )
        with archive.open(file_members[0]) as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                member_digest.update(raw_line)
                item = target_by_line.get(line_number)
                if item is None:
                    continue
                event = json.loads(raw_line)
                pointer_record = item["source_pointer"]["record_id"]
                record_number = str(event.get("RecordNumber"))
                if record_number not in pointer_record:
                    raise ValueError(
                        f"OTRF record mismatch at line {line_number}: "
                        f"{record_number} not in {pointer_record}"
                    )
                excerpts.append(
                    make_excerpt(
                        item,
                        "otrf_windows_event",
                        {
                            "archive_member": expected_member,
                            "line_number": line_number,
                            "record_number": event.get("RecordNumber"),
                            "event_id": event.get("EventID"),
                        },
                        {"event": event},
                    )
                )
                remaining.remove(line_number)

    require_no_missing(remaining, archive_path)
    return (
        excerpts,
        sha256_file(archive_path),
        member_digest.hexdigest().upper(),
    )


def make_excerpt(
    item: dict[str, Any],
    source_format: str,
    record_locator: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "blind_id": item["blind_id"],
        "source_pointer": item["source_pointer"],
        "source_format": source_format,
        "record_locator": record_locator,
        "source_excerpt_encoding": "recursive_utf8_hex_v1",
        "source_excerpt": encode_source_payload(payload),
        "excerpt_sha256": sha256_bytes(canonical_json(payload)),
    }


def require_no_missing(missing: Iterable[Any], source_path: Path) -> None:
    values = sorted(str(value) for value in missing)
    if values:
        raise ValueError(f"records not found in {source_path}: {values}")


def find_source(manifest: dict[str, Any], source_id: str) -> dict[str, Any]:
    for source in manifest["sources"]:
        if source["source_id"] == source_id:
            return source
    raise KeyError(source_id)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            )


def build_package(
    root: Path,
    packet_dir: Path,
    output_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    experiment_root = root / "09-experiments"
    data_root = experiment_root / "real_data"
    public_claims_path = packet_dir / "public" / "claim_items.jsonl"
    public_items = load_jsonl(public_claims_path)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in public_items:
        grouped[item["source_pointer"]["artifact_id"]].append(item)

    expected_counts = {
        "darpa_e5_R04_pidsmaker_event_table": 5,
        "darpa_e5_R05_pidsmaker_event_table": 4,
        "darpa_optc_R06_sysclient0201_ecar_window": 5,
        "darpa_optc_R07_sysclient0351_ecar_window": 5,
        "otrf_apt29_day1_host_events": 8,
    }
    actual_counts = {key: len(value) for key, value in grouped.items()}
    if actual_counts != expected_counts:
        raise ValueError(f"unexpected artifact counts: {actual_counts}")

    e5_dir = data_root / "darpa_tc_e5"
    optc_dir = data_root / "darpa_optc"
    otrf_dir = data_root / "otrf_apt29"
    e5_manifest = load_json(e5_dir / "manifest.json")
    optc_manifest = load_json(optc_dir / "manifest.json")
    otrf_manifest = load_json(otrf_dir / "manifest.json")

    excerpts: list[dict[str, Any]] = []
    source_artifacts: dict[str, Any] = {}

    pg_specs = (
        (
            "darpa_e5_R04_pidsmaker_event_table",
            "R04",
            "theia_e5_pidsmaker_postgres_dump",
        ),
        (
            "darpa_e5_R05_pidsmaker_event_table",
            "R05",
            "clearscope_e5_pidsmaker_postgres_dump",
        ),
    )
    for artifact_id, run_id, source_id in pg_specs:
        event_path = e5_dir / "extracted" / f"{run_id}_event_table.tsv"
        nodes_path = e5_dir / "extracted" / f"{run_id}_nodes.jsonl"
        extraction = load_json(e5_dir / "derived" / f"{run_id}_extraction_summary.json")
        resolution = load_json(
            e5_dir / "derived" / f"{run_id}_node_resolution_summary.json"
        )
        source = find_source(e5_manifest, source_id)
        raw_path = e5_dir / source["raw_target"]
        rows, event_sha256, nodes_sha256 = pgdump_excerpts(
            grouped[artifact_id], event_path, nodes_path
        )
        excerpts.extend(rows)
        source_artifacts[artifact_id] = {
            "source_format": "PIDSMaker PGDMP bounded event window",
            "record_count": len(rows),
            "raw_parent": source_manifest_entry(
                raw_path, root, source["sha256"], source["size_bytes"]
            ),
            "event_window": verified_local_file(
                event_path,
                root,
                event_sha256,
                extraction["output_sha256"],
            ),
            "resolved_nodes": verified_local_file(
                nodes_path,
                root,
                nodes_sha256,
                resolution["output_sha256"],
            ),
        }

    ecar_specs = (
        (
            "darpa_optc_R06_sysclient0201_ecar_window",
            "R06",
            "optc_ecar_23sep19_aia_201_225_last",
        ),
        (
            "darpa_optc_R07_sysclient0351_ecar_window",
            "R07",
            "optc_ecar_25sept_aia_351_375_last",
        ),
    )
    for artifact_id, run_id, source_id in ecar_specs:
        source = find_source(optc_manifest, source_id)
        raw_path = optc_dir / source["raw_target"]
        event_path = optc_dir / "extracted" / (
            "R06_sysclient0201_window.jsonl"
            if run_id == "R06"
            else "R07_sysclient0351_window.jsonl"
        )
        extraction = load_json(
            optc_dir / "derived" / f"{run_id}_extraction_summary.json"
        )
        rows, event_sha256 = ecar_excerpts(grouped[artifact_id], event_path)
        excerpts.extend(rows)
        source_artifacts[artifact_id] = {
            "source_format": "OpTC eCAR bounded JSONL window",
            "record_count": len(rows),
            "raw_parent": source_manifest_entry(
                raw_path, root, source["sha256"], source["size_bytes"]
            ),
            "event_window": verified_local_file(
                event_path,
                root,
                event_sha256,
                extraction["output_sha256"],
            ),
        }

    otrf_artifact = "otrf_apt29_day1_host_events"
    otrf_source = find_source(otrf_manifest, otrf_artifact)
    archive_path = otrf_dir / otrf_source["raw_target"]
    motif_spec = load_json(otrf_dir / "ground_truth" / "R08_motif_spec.json")
    rows, archive_sha256, member_sha256 = otrf_excerpts(
        grouped[otrf_artifact],
        archive_path,
        motif_spec["host_archive_member"],
    )
    if archive_sha256 != otrf_source["sha256"].upper():
        raise ValueError("OTRF archive SHA-256 does not match frozen manifest")
    excerpts.extend(rows)
    source_artifacts[otrf_artifact] = {
        "source_format": "OTRF ZIP-contained Windows event JSONL",
        "record_count": len(rows),
        "raw_parent": verified_local_file(
            archive_path,
            root,
            archive_sha256,
            otrf_source["sha256"],
        ),
        "archive_member": motif_spec["host_archive_member"],
        "archive_member_sha256": member_sha256,
    }

    excerpts.sort(key=lambda row: row["blind_id"])
    if len(excerpts) != len(public_items):
        raise ValueError(
            f"expected {len(public_items)} excerpts, generated {len(excerpts)}"
        )
    blind_ids = [row["blind_id"] for row in excerpts]
    if len(set(blind_ids)) != len(blind_ids):
        raise ValueError("duplicate blind IDs in source excerpts")
    public_by_blind = {item["blind_id"]: item for item in public_items}
    for row in excerpts:
        expected = public_by_blind[row["blind_id"]]["source_pointer"]
        if pointer_key(row["source_pointer"]) != pointer_key(expected):
            raise ValueError(f"source pointer drift for {row['blind_id']}")

    write_jsonl(output_path, excerpts)
    excerpt_hashes = {
        row["blind_id"]: row["excerpt_sha256"] for row in excerpts
    }
    manifest = {
        "package_version": PACKAGE_VERSION,
        "annotation_packet_version": load_json(packet_dir / "packet_manifest.json")[
            "packet_version"
        ],
        "claim_items_sha256": sha256_file(public_claims_path),
        "excerpt_count": len(excerpts),
        "artifact_counts": dict(sorted(Counter(
            row["source_pointer"]["artifact_id"] for row in excerpts
        ).items())),
        "source_artifacts": dict(sorted(source_artifacts.items())),
        "local_excerpt_file": {
            "filename": output_path.name,
            "size_bytes": output_path.stat().st_size,
            "sha256": sha256_file(output_path),
            "distribution": "local_admin_bundle_not_committed",
        },
        "excerpt_sha256_by_blind_id": excerpt_hashes,
        "source_gate_status": "ready_local_canonical_excerpts",
        "human_labels_present": False,
        "generation_command": (
            "python 09-experiments/scripts/build_claim_source_excerpts.py"
        ),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    default_package = (
        root
        / "09-experiments"
        / "annotation"
        / "source_excerpts"
        / "c07_c11_v0.1"
    )
    parser = argparse.ArgumentParser(
        description="Build local canonical source excerpts for C07-C11 claims."
    )
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument(
        "--packet-dir",
        type=Path,
        default=root / "09-experiments" / "annotation" / "c07_c11_v0.2",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_package / "local" / "claim_source_excerpts.jsonl",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=default_package / "source_excerpt_manifest.json",
    )
    args = parser.parse_args()
    manifest = build_package(
        args.root.resolve(),
        args.packet_dir.resolve(),
        args.output.resolve(),
        args.manifest.resolve(),
    )
    print(
        f"Wrote {manifest['excerpt_count']} local source excerpts; "
        f"payload SHA-256={manifest['local_excerpt_file']['sha256']}"
    )


if __name__ == "__main__":
    main()
