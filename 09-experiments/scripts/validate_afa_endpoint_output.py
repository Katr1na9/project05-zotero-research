#!/usr/bin/env python3
"""Validate a frozen Project05 AFA endpoint-contract result directory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


PAIR_FIELDS = (
    "case_id",
    "mask_strategy",
    "mask_intensity",
    "seed",
    "planner",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(output_dir: Path) -> dict[str, Any]:
    manifest_path = output_dir / "evaluation_manifest.json"
    manifest = load_json(manifest_path)
    if manifest.get("paper_or_patent_updated") is not False:
        raise ValueError("AFA manifest does not certify paper_or_patent_updated=false")
    if manifest.get("all_experiments_complete") is not False:
        raise ValueError("AFA manifest incorrectly marks all experiments complete")
    if not str(manifest.get("paper_or_patent_gate", "")).startswith("closed"):
        raise ValueError("AFA paper/patent gate is not closed")
    contract = manifest["endpoint_contract"]
    if contract.get("runtime_allowlist_enforced") is not True:
        raise ValueError("AFA runtime allowlist is not certified")
    statistical = manifest["statistical_unit"]
    if statistical.get("independent") != "case_or_attack_chain":
        raise ValueError("Invalid independent statistical unit")
    if statistical.get("pseudoreplication_forbidden") is not True:
        raise ValueError("Pseudoreplication boundary is missing")

    for filename, expected in manifest["output_sha256"].items():
        path = output_dir / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(
                f"SHA-256 mismatch for {filename}: {actual} != {expected}"
            )

    rows = read_csv(output_dir / "afa_voi_policy_results.csv")
    keys = [tuple(row[field] for field in PAIR_FIELDS) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate AFA paired condition keys")
    cases = {row["case_id"] for row in rows}
    planners = {row["planner"] for row in rows}
    if len(cases) != int(manifest["independent_case_count"]):
        raise ValueError("Independent case count mismatch")
    if planners != set(manifest["planners"]):
        raise ValueError("Planner set mismatch")
    repeated = {
        (
            row["case_id"],
            row["mask_strategy"],
            row["mask_intensity"],
            row["seed"],
        )
        for row in rows
    }
    if len(repeated) != int(manifest["repeated_condition_count"]):
        raise ValueError("Repeated condition count mismatch")
    expected_rows = len(repeated) * len(planners)
    if len(rows) != expected_rows:
        raise ValueError(f"Row count {len(rows)} != {expected_rows}")

    if {row["channel_prior_scope"] for row in rows} != {
        "planner_belief_only"
    }:
        raise ValueError("AFA channel prior was not planner-belief-only")
    if {
        int(row["execution_channel_profile_held_constant"]) for row in rows
    } != {1}:
        raise ValueError("Execution channel profile was not held constant")
    multiplier = float(manifest["channel_prior_intervention"]["multiplier"])
    if {float(row["channel_prior_multiplier"]) for row in rows} != {
        multiplier
    }:
        raise ValueError("Row-level channel prior multiplier mismatch")
    consumed = set(
        manifest["channel_prior_intervention"]["consumed_by_planners"]
    )
    for row in rows:
        expected = int(row["planner"] in consumed)
        if int(row["channel_prior_consumed_by_planner"]) != expected:
            raise ValueError(
                f"Incorrect channel-prior consumption flag for {row['planner']}"
            )
    execution_hashes: dict[str, set[str]] = {}
    for row in rows:
        execution_hashes.setdefault(row["case_id"], set()).add(
            row["execution_channel_profile_sha256"]
        )
    if not all(len(values) == 1 for values in execution_hashes.values()):
        raise ValueError("Execution channel profile changed within a case")

    return {
        "validation_status": "passed",
        "independent_case_count": len(cases),
        "repeated_condition_count": len(repeated),
        "planner_count": len(planners),
        "row_count": len(rows),
        "output_sha256_verified": True,
        "unique_pair_keys_verified": True,
        "execution_profile_held_constant": True,
        "channel_prior_scope": "planner_belief_only",
        "paper_or_patent_updated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
