#!/usr/bin/env python3
"""Build deterministic, answer-key-separated annotation distribution ZIPs."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


BUNDLE_VERSION = "c07_c11_v0.2_distribution_v0.1"
FIXED_ZIP_TIME = (2026, 7, 13, 0, 0, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def zip_bytes(archive: zipfile.ZipFile, arcname: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, payload)


def build_one_bundle(
    output_path: Path,
    annotator: str,
    files: list[tuple[str, Path]],
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w") as archive:
        for arcname, source_path in sorted(files):
            zip_bytes(archive, arcname, source_path.read_bytes())
        zip_bytes(
            archive,
            "ANNOTATOR_ID.txt",
            f"annotator_{annotator}\n".encode("ascii"),
        )
    archived_files = sorted(
        [arcname for arcname, _ in files] + ["ANNOTATOR_ID.txt"]
    )
    return {
        "annotator": annotator,
        "filename": output_path.name,
        "size_bytes": output_path.stat().st_size,
        "sha256": sha256_file(output_path),
        "files": archived_files,
    }


def build_bundles(root: Path, output_dir: Path, manifest_path: Path) -> dict[str, Any]:
    experiment_root = root / "09-experiments"
    packet_dir = experiment_root / "annotation" / "c07_c11_v0.2"
    source_package = (
        experiment_root
        / "annotation"
        / "source_excerpts"
        / "c07_c11_v0.1"
    )
    source_payload = source_package / "local" / "claim_source_excerpts.jsonl"
    if not source_payload.is_file():
        raise FileNotFoundError(
            "local source excerpts are missing; run "
            "build_claim_source_excerpts.py first"
        )

    common_files = [
        ("README.md", manifest_path.parent / "ANNOTATOR-INSTRUCTIONS.md"),
        ("CODEBOOK.md", root / "08-writing" / "human-annotation-evaluation-protocol-v0.2-20260712.md"),
        ("public/claim_items.jsonl", packet_dir / "public" / "claim_items.jsonl"),
        ("public/intent_items.jsonl", packet_dir / "public" / "intent_items.jsonl"),
        ("public/granularity_items.jsonl", packet_dir / "public" / "granularity_items.jsonl"),
        ("source/claim_source_excerpts.jsonl", source_payload),
        ("tools/view_source_excerpt.py", experiment_root / "scripts" / "view_claim_source_excerpt.py"),
    ]
    bundles: dict[str, Any] = {}
    for annotator in ("A", "B"):
        source_dir = packet_dir / f"annotator_{annotator}"
        files = common_files + [
            ("annotations/claim_annotations.csv", source_dir / "claim_annotations.csv"),
            ("annotations/intent_annotations.csv", source_dir / "intent_annotations.csv"),
            ("annotations/granularity_annotations.csv", source_dir / "granularity_annotations.csv"),
        ]
        output_path = output_dir / f"annotator_{annotator}_bundle.zip"
        bundles[f"annotator_{annotator}"] = build_one_bundle(
            output_path, annotator, files
        )

    packet_manifest = packet_dir / "packet_manifest.json"
    excerpt_manifest = source_package / "source_excerpt_manifest.json"
    manifest = {
        "bundle_version": BUNDLE_VERSION,
        "annotation_packet_sha256": sha256_file(packet_manifest),
        "source_excerpt_manifest_sha256": sha256_file(excerpt_manifest),
        "bundles": bundles,
        "separation_checks": {
            "admin_key_included": False,
            "other_annotator_csv_included": False,
            "paper_or_planner_results_included": False,
            "recoverable_claim_ids_included": False,
        },
        "distribution_status": "ready_to_distribute_local",
        "human_labels_present": False,
        "generation_command": (
            "python 09-experiments/scripts/"
            "build_annotation_distribution_bundles.py"
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
    package_dir = (
        root
        / "09-experiments"
        / "annotation"
        / "distribution"
        / BUNDLE_VERSION
    )
    parser = argparse.ArgumentParser(
        description="Build isolated local annotation bundles for annotators A/B."
    )
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument(
        "--output-dir", type=Path, default=package_dir / "local"
    )
    parser.add_argument(
        "--manifest", type=Path, default=package_dir / "bundle_manifest.json"
    )
    args = parser.parse_args()
    manifest = build_bundles(
        args.root.resolve(),
        args.output_dir.resolve(),
        args.manifest.resolve(),
    )
    for name, bundle in manifest["bundles"].items():
        print(f"{name}: {bundle['sha256']} ({bundle['size_bytes']} bytes)")


if __name__ == "__main__":
    main()
