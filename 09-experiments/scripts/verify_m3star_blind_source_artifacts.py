#!/usr/bin/env python3
"""Verify curator-downloaded source artifacts without parsing their contents."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


HEX_PATTERNS = {
    "md5": re.compile(r"^[0-9a-f]{32}$"),
    "sha256": re.compile(r"^[0-9a-f]{64}$"),
}
CURATOR_ACCESS_CLASSES = {
    "public_non_label_metadata",
    "sealed_telemetry_payload",
    "curator_only_boundary_material",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def require_false(value: Any, field: str) -> None:
    if value is not False:
        raise ValueError(f"{field} must be false")


def resolve_artifact(root: Path, relative_path: str, field: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{field} must stay within artifact_root")
    candidate = (root / relative).resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{field} resolves outside artifact_root") from exc
    if not candidate.is_file():
        raise ValueError(f"{field} must resolve to a regular file")
    return candidate


def digest_file(path: Path) -> tuple[int, str, str]:
    md5_digest = hashlib.md5(usedforsecurity=False)
    sha256_digest = hashlib.sha256()
    size_bytes = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size_bytes += len(chunk)
            md5_digest.update(chunk)
            sha256_digest.update(chunk)
    return size_bytes, md5_digest.hexdigest(), sha256_digest.hexdigest()


def validate_catalog(catalog: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
    if catalog.get("status") != "curator_prepared":
        raise ValueError("Source artifact catalog must have status curator_prepared")
    catalog_id = require_nonempty_string(catalog.get("catalog_id"), "catalog_id")
    curation_team_id = require_nonempty_string(
        catalog.get("curation_team_id"), "curation_team_id"
    )
    model_team_id = require_nonempty_string(
        catalog.get("model_development_team_id"), "model_development_team_id"
    )
    if curation_team_id == model_team_id:
        raise ValueError("Curation and model-development identities must be distinct")
    if catalog.get("teams_are_disjoint") is not True:
        raise ValueError("teams_are_disjoint must be true")
    if catalog.get("curator_blind_to_model_outputs") is not True:
        raise ValueError("curator_blind_to_model_outputs must be true")
    if catalog.get("model_developers_blind_to_candidate_payloads") is not True:
        raise ValueError("model_developers_blind_to_candidate_payloads must be true")
    require_false(catalog.get("case_credit_claimed"), "case_credit_claimed")

    records = catalog.get("artifacts")
    if not isinstance(records, list) or not records:
        raise ValueError("artifacts must be a non-empty array")
    artifact_root = artifact_root.resolve(strict=True)
    if not artifact_root.is_dir():
        raise ValueError("artifact_root must be a directory")

    observed_keys: set[tuple[str, str]] = set()
    observed_paths: set[str] = set()
    verified: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"artifacts[{index}] must be an object")
        prefix = f"artifacts[{index}]"
        source_id = require_nonempty_string(record.get("source_id"), f"{prefix}.source_id")
        artifact_id = require_nonempty_string(
            record.get("artifact_id"), f"{prefix}.artifact_id"
        )
        key = (source_id, artifact_id)
        if key in observed_keys:
            raise ValueError(f"Duplicate source/artifact identity: {source_id}/{artifact_id}")
        observed_keys.add(key)

        access_class = require_nonempty_string(
            record.get("access_class"), f"{prefix}.access_class"
        )
        if access_class not in CURATOR_ACCESS_CLASSES:
            raise ValueError(
                f"{prefix}.access_class is not available to the isolated curator"
            )
        require_false(
            record.get("opened_by_model_development"),
            f"{prefix}.opened_by_model_development",
        )
        require_false(record.get("case_credit_claimed"), f"{prefix}.case_credit_claimed")

        relative_path = require_nonempty_string(
            record.get("relative_path"), f"{prefix}.relative_path"
        )
        if relative_path in observed_paths:
            raise ValueError(f"Duplicate relative artifact path: {relative_path}")
        observed_paths.add(relative_path)
        path = resolve_artifact(artifact_root, relative_path, f"{prefix}.relative_path")

        expected_size = record.get("expected_size_bytes")
        if not isinstance(expected_size, int) or expected_size < 0:
            raise ValueError(f"{prefix}.expected_size_bytes must be a non-negative integer")
        checksum = record.get("publisher_checksum")
        if not isinstance(checksum, dict):
            raise ValueError(f"{prefix}.publisher_checksum must be an object")
        algorithm = str(checksum.get("algorithm", "")).lower()
        if algorithm not in HEX_PATTERNS:
            raise ValueError(f"{prefix}.publisher_checksum.algorithm is unsupported")
        expected_digest = str(checksum.get("value", "")).lower()
        if not HEX_PATTERNS[algorithm].fullmatch(expected_digest):
            raise ValueError(f"{prefix}.publisher_checksum.value is malformed")

        size_bytes, md5_digest, sha256_digest = digest_file(path)
        if size_bytes != expected_size:
            raise ValueError(
                f"{prefix} size mismatch: expected {expected_size}, observed {size_bytes}"
            )
        observed_digest = md5_digest if algorithm == "md5" else sha256_digest
        if observed_digest != expected_digest:
            raise ValueError(f"{prefix} publisher checksum mismatch")
        verified.append(
            {
                "source_id": source_id,
                "artifact_id": artifact_id,
                "relative_path": relative_path,
                "access_class": access_class,
                "size_bytes": size_bytes,
                "publisher_checksum_algorithm": algorithm,
                "publisher_checksum_verified": True,
                "sha256": sha256_digest,
                "opened_by_model_development": False,
                "case_credit_claimed": False,
            }
        )

    return {
        "status": "source_artifact_hash_checks_passed",
        "catalog_id": catalog_id,
        "curation_team_id": curation_team_id,
        "artifact_count": len(verified),
        "artifacts": verified,
        "file_contents_parsed": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened": False,
        "case_credit_claimed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_catalog(load_json(args.catalog), args.artifact_root)
    if args.output is not None:
        write_json(args.output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
