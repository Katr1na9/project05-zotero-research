#!/usr/bin/env python3
"""Validate a corrected Project05 Depth-2 result directory."""

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
    manifest = load_json(output_dir / "evaluation_manifest.json")
    if manifest.get("paper_or_patent_updated") is not False:
        raise ValueError("Depth-2 manifest does not close paper/patent writing")
    if manifest.get("all_experiments_complete") is not False:
        raise ValueError("Depth-2 manifest incorrectly marks experiments complete")
    if not str(manifest.get("paper_or_patent_gate", "")).startswith("closed"):
        raise ValueError("Depth-2 paper/patent gate is not closed")
    statistical = manifest["statistical_unit"]
    if statistical.get("independent") != "case_or_attack_chain":
        raise ValueError("Invalid Depth-2 independent unit")
    if statistical.get("pseudoreplication_forbidden") is not True:
        raise ValueError("Depth-2 pseudoreplication boundary is missing")
    boundary = manifest["endpoint_boundary"]
    if boundary.get("runtime_allowlist_enforced") is not True:
        raise ValueError("Depth-2 runtime allowlist is not certified")
    if len(str(boundary.get("sha256", ""))) != 64:
        raise ValueError("Depth-2 runtime contract hash is invalid")
    if boundary.get("hidden_outcome_invariance_tested") is not True:
        raise ValueError("Depth-2 hidden-outcome invariance is not certified")
    if boundary.get("realized_outcomes_visible") is not False:
        raise ValueError("Depth-2 boundary exposes realized outcomes")

    for filename, expected in manifest["output_sha256"].items():
        path = output_dir / filename
        if sha256_file(path) != expected:
            raise ValueError(f"SHA-256 mismatch for {filename}")

    rows = read_csv(output_dir / "nonmyopic_policy_results.csv")
    keys = [tuple(row[field] for field in PAIR_FIELDS) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate Depth-2 paired condition keys")
    cases = {row["case_id"] for row in rows}
    planners = {row["planner"] for row in rows}
    repeated = {
        (
            row["case_id"],
            row["mask_strategy"],
            row["mask_intensity"],
            row["seed"],
        )
        for row in rows
    }
    if len(cases) != int(manifest["independent_case_count"]):
        raise ValueError("Depth-2 independent case count mismatch")
    if planners != set(manifest["planners"]):
        raise ValueError("Depth-2 planner set mismatch")
    if len(repeated) != int(manifest["repeated_condition_count"]):
        raise ValueError("Depth-2 repeated condition count mismatch")
    if len(rows) != len(repeated) * len(planners):
        raise ValueError("Depth-2 row count mismatch")

    if {row["channel_prior_scope"] for row in rows} != {
        "planner_belief_only"
    }:
        raise ValueError("Depth-2 prior scope is not planner-belief-only")
    if {
        int(row["execution_channel_profile_held_constant"]) for row in rows
    } != {1}:
        raise ValueError("Depth-2 execution profile was not held constant")
    multiplier = float(manifest["channel_prior_intervention"]["multiplier"])
    if {float(row["channel_prior_multiplier"]) for row in rows} != {
        multiplier
    }:
        raise ValueError("Depth-2 row-level multiplier mismatch")
    consumed = set(
        manifest["channel_prior_intervention"]["consumed_by_planners"]
    )
    for row in rows:
        if int(row["channel_prior_consumed_by_planner"]) != int(
            row["planner"] in consumed
        ):
            raise ValueError("Depth-2 channel-prior consumption flag mismatch")
    execution_hashes: dict[str, set[str]] = {}
    for row in rows:
        execution_hashes.setdefault(row["case_id"], set()).add(
            row["execution_channel_profile_sha256"]
        )
    if not all(len(values) == 1 for values in execution_hashes.values()):
        raise ValueError("Depth-2 execution profile changed within a case")

    return {
        "validation_status": "passed_with_runtime_allowlist",
        "independent_case_count": len(cases),
        "repeated_condition_count": len(repeated),
        "planner_count": len(planners),
        "row_count": len(rows),
        "output_sha256_verified": True,
        "unique_pair_keys_verified": True,
        "execution_profile_held_constant": True,
        "runtime_allowlist_enforced": True,
        "hidden_outcome_invariance_tested": True,
        "paper_or_patent_updated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
