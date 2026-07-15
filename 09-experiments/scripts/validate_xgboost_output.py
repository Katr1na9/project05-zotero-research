#!/usr/bin/env python3
"""Validate frozen Project05 XGBoost/Logistic transfer outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


PAIR_FIELDS = ("case_id", "mask_strategy", "mask_intensity", "seed", "planner")
EXPECTED_PROVENANCE = {
    "legacy": "case_embedded_legacy_exogenous_cost",
    "uniform": "uniform_frozen_exogenous_cost",
    "rubric": "rubric_frozen_independent_ratings",
    "measured": "measured_frozen_operational_cost",
}


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
        raise ValueError("ML manifest does not close paper/patent writing")
    if manifest.get("all_experiments_complete") is not False:
        raise ValueError("ML manifest incorrectly marks all experiments complete")
    if not str(manifest.get("paper_or_patent_gate", "")).startswith("closed"):
        raise ValueError("ML paper/patent gate is not closed")
    if manifest.get("external_actor_accuracy", "not-null") is not None:
        raise ValueError("ML external actor accuracy must remain null without ground truth")
    if set(manifest["train_case_ids"]) & set(manifest["test_case_ids"]):
        raise ValueError("ML train/test case overlap")
    if manifest.get("training_test_overlap") != []:
        raise ValueError("ML training_test_overlap must be empty")
    boundary = manifest["endpoint_boundary"]
    if boundary.get("runtime_allowlist_enforced") is not True:
        raise ValueError("ML runtime allowlist is not certified")
    if boundary.get("runtime_labels_visible") is not False:
        raise ValueError("ML runtime labels are visible")
    if boundary.get("realized_outcomes_visible") is not False:
        raise ValueError("ML realized outcomes are visible")
    if len(str(boundary.get("sha256", ""))) != 64:
        raise ValueError("ML runtime contract SHA-256 is invalid")
    statistical = manifest["statistical_unit"]
    if statistical.get("independent") != "case_or_attack_chain":
        raise ValueError("ML independent unit is invalid")
    if statistical.get("pseudoreplication_forbidden") is not True:
        raise ValueError("ML pseudoreplication boundary is missing")

    cost_regime = manifest["cost_regime"]
    provenance = EXPECTED_PROVENANCE.get(cost_regime)
    if provenance is None:
        raise ValueError(f"Unknown ML cost regime: {cost_regime}")
    for section in (
        "cost_profile_identity_by_case",
        "training_cost_profile_identity_by_case",
    ):
        identities = manifest[section]
        if not identities:
            raise ValueError(f"Empty ML {section}")
        for identity in identities.values():
            if identity.get("provenance") != provenance:
                raise ValueError(f"ML cost provenance mismatch in {section}")
            if len(str(identity.get("sha256", ""))) != 64:
                raise ValueError(f"Invalid ML cost profile SHA-256 in {section}")

    for filename, expected in manifest["output_sha256"].items():
        path = output_dir / filename
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"ML output SHA-256 mismatch: {filename}")

    rows = read_csv(output_dir / "xgboost_policy_results.csv")
    keys = [tuple(row[field] for field in PAIR_FIELDS) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate ML policy condition keys")
    cases = {row["case_id"] for row in rows}
    planners = {row["planner"] for row in rows}
    repeated = {
        (row["case_id"], row["mask_strategy"], row["mask_intensity"], row["seed"])
        for row in rows
    }
    if cases != set(manifest["test_case_ids"]):
        raise ValueError("ML policy case set mismatch")
    if len(cases) != int(manifest["independent_test_case_count"]):
        raise ValueError("ML independent case count mismatch")
    if len(rows) != len(repeated) * len(planners):
        raise ValueError("ML policy row count mismatch")
    if cost_regime != "legacy":
        if {row.get("cost_regime") for row in rows} != {cost_regime}:
            raise ValueError("ML row-level cost regime mismatch")
        if any(len(row.get("cost_profile_sha256", "")) != 64 for row in rows):
            raise ValueError("ML row-level cost profile hash is invalid")
    return {
        "validation_status": "passed",
        "cost_regime": cost_regime,
        "independent_case_count": len(cases),
        "repeated_condition_count": len(repeated),
        "planner_count": len(planners),
        "row_count": len(rows),
        "output_sha256_verified": True,
        "runtime_allowlist_enforced": True,
        "training_test_disjoint": True,
        "paper_or_patent_updated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
