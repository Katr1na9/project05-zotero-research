#!/usr/bin/env python3
"""Compare two independent candidate-pair constructions without raw output."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def manifest_by_name(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    manifest = audit.get("pair_file_manifest")
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("candidate-pair manifest is missing")
    output = {entry["relative_name"]: entry for entry in manifest}
    if len(output) != len(manifest):
        raise ValueError("candidate-pair manifest has duplicate names")
    return output


def verify_payload(root: Path, manifest: dict[str, dict[str, Any]]) -> None:
    for name, entry in manifest.items():
        path = Path(root) / name
        if not path.is_file():
            raise ValueError(f"candidate-pair payload is missing: {name}")
        if path.stat().st_size != entry["bytes"]:
            raise ValueError(f"candidate-pair payload size changed: {name}")
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"candidate-pair payload hash changed: {name}")


def compare(
    canonical_audit: dict[str, Any],
    canonical_root: Path,
    reproduction_audit: dict[str, Any],
    reproduction_root: Path,
) -> dict[str, Any]:
    if canonical_audit["contract_id"] != reproduction_audit["contract_id"]:
        raise ValueError("construction contracts differ")
    canonical_manifest = manifest_by_name(canonical_audit)
    reproduction_manifest = manifest_by_name(reproduction_audit)
    if set(canonical_manifest) != set(reproduction_manifest):
        raise ValueError("pair payload file sets differ")
    verify_payload(canonical_root, canonical_manifest)
    verify_payload(reproduction_root, reproduction_manifest)
    files: dict[str, Any] = {}
    for name in sorted(canonical_manifest):
        left = canonical_manifest[name]
        right = reproduction_manifest[name]
        match = left["bytes"] == right["bytes"] and left["sha256"] == right["sha256"]
        files[name] = {
            "canonical_bytes": left["bytes"],
            "reproduction_bytes": right["bytes"],
            "canonical_sha256": left["sha256"],
            "reproduction_sha256": right["sha256"],
            "byte_identical": match,
        }
        if not match:
            raise ValueError(f"candidate-pair reproduction differs: {name}")
    canonical_digest = canonical_audit["dataset"]["canonical_example_digest"]
    reproduction_digest = reproduction_audit["dataset"]["canonical_example_digest"]
    canonical_manifest_digest = canonical_audit["pair_file_manifest_sha256"]
    reproduction_manifest_digest = reproduction_audit["pair_file_manifest_sha256"]
    canonical_selection = canonical_audit["length_aware_selection"]
    reproduction_selection = reproduction_audit["length_aware_selection"]
    selection_match = canonical_selection == reproduction_selection
    if (
        canonical_digest != reproduction_digest
        or canonical_manifest_digest != reproduction_manifest_digest
        or not selection_match
    ):
        raise ValueError("candidate-pair audit reproduction differs")
    return {
        "audit_id": "project05-label-blind-pair-determinism-v0.2",
        "created_date": canonical_audit["created_date"],
        "status": "passed_byte_identical_token_aware_reconstruction",
        "contract_id": canonical_audit["contract_id"],
        "runs": 2,
        "same_inputs_implementation_and_selection_contract": True,
        "output_comparison": files,
        "canonical_example_digest": {
            "canonical": canonical_digest,
            "reproduction": reproduction_digest,
            "match": True,
        },
        "pair_file_manifest_sha256": {
            "canonical": canonical_manifest_digest,
            "reproduction": reproduction_manifest_digest,
            "match": True,
        },
        "length_aware_selection_audit_match": selection_match,
        "reproduction_payload_retention": "delete_after_hash_comparison",
        "tokenizer_used_for_selection_only": True,
        "accepted_examples_truncated": 0,
        "accepted_examples_rewritten": 0,
        "model_used": False,
        "training_run": False,
        "formal_inference_run": False,
        "m3_runtime_integrated": False,
    }


def write_json_no_overwrite(path: Path, value: Any) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-audit", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--reproduction-audit", type=Path, required=True)
    parser.add_argument("--reproduction-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = compare(
        load_json(args.canonical_audit),
        args.canonical_root,
        load_json(args.reproduction_audit),
        args.reproduction_root,
    )
    write_json_no_overwrite(args.output, result)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
