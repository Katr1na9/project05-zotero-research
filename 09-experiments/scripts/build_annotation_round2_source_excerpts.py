#!/usr/bin/env python3
"""Build local source excerpts for the presented Round 2 claim pointers."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE_BUILDER_PATH = Path(__file__).with_name("build_claim_source_excerpts.py")
PACKET_DIR = ROOT / "09-experiments" / "annotation" / "c07_c11_round2_v0.1"
PACKAGE_DIR = (
    ROOT
    / "09-experiments"
    / "annotation"
    / "source_excerpts"
    / "c07_c11_round2_v0.1"
)
OUTPUT_PATH = PACKAGE_DIR / "local" / "claim_source_excerpts.jsonl"
MANIFEST_PATH = PACKAGE_DIR / "source_excerpt_manifest.json"
PACKAGE_VERSION = "c07_c11_round2_source_excerpts_v0.1"


def _load_source_builder() -> Any:
    spec = importlib.util.spec_from_file_location(
        "project05_round2_source_base", SOURCE_BUILDER_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load source builder from {SOURCE_BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = _load_source_builder()


def build(
    root: Path = ROOT,
    packet_dir: Path = PACKET_DIR,
    output_path: Path = OUTPUT_PATH,
    manifest_path: Path = MANIFEST_PATH,
) -> dict[str, Any]:
    if output_path.exists() or manifest_path.exists():
        raise FileExistsError(
            "Round 2 source-excerpt output already exists; use a new versioned "
            f"path instead of overwriting: {output_path}"
        )
    manifest = SOURCE.build_package(
        root.resolve(),
        packet_dir.resolve(),
        output_path.resolve(),
        manifest_path.resolve(),
    )
    manifest.update(
        {
            "package_version": PACKAGE_VERSION,
            "annotation_packet_version": "c07_c11_round2_v0.1",
            "pointer_semantics": (
                "Excerpts resolve the pointer presented in the Round 2 public "
                "item, including deliberately wrong controls; original pointers "
                "and control labels are never consulted."
            ),
            "human_labels_present": False,
            "generation_command": (
                "python 09-experiments/scripts/"
                "build_annotation_round2_source_excerpts.py"
            ),
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build local canonical excerpts for Round 2 presented pointers."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--packet-dir", type=Path, default=PACKET_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    manifest = build(args.root, args.packet_dir, args.output, args.manifest)
    print(
        f"Wrote {manifest['excerpt_count']} Round 2 source excerpts; "
        f"SHA-256={manifest['local_excerpt_file']['sha256']}"
    )


if __name__ == "__main__":
    main()
