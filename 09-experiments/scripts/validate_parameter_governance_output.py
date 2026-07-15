#!/usr/bin/env python3
"""Validate a completed Project05 parameter-governance output directory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


FAMILY_FILES = {
    "cost": (
        "cost_regime_results.csv",
        "cost_regime_summary.json",
        "cost_regime_paired_stability.json",
    ),
    "threshold": (
        "threshold_grid_results.csv",
        "threshold_grid_summary.json",
        "threshold_grid_paired_stability.json",
    ),
    "corroboration": (
        "corroboration_results.csv",
        "corroboration_summary.json",
        "corroboration_paired_stability.json",
    ),
    "alpha": (
        "m2_alpha_results.csv",
        "m2_alpha_summary.json",
        "m2_alpha_paired_stability.json",
    ),
    "priors": (
        "action_prior_results.csv",
        "action_prior_summary.json",
        "action_prior_paired_stability.json",
    ),
}
PAIR_KEY_FIELDS = (
    "governance_variant",
    "case_id",
    "mask_strategy",
    "mask_intensity",
    "seed",
    "planner",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate(output_dir: Path) -> dict[str, Any]:
    manifest_path = output_dir / "run_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = load_json(manifest_path)
    if manifest.get("legacy_outputs_overwritten") is not False:
        raise ValueError("Manifest does not certify legacy_outputs_overwritten=false")
    if manifest.get("paper_or_patent_updated") is not False:
        raise ValueError("Manifest does not certify paper_or_patent_updated=false")
    case_count = int(manifest["independent_case_count"])
    if case_count != len(manifest["case_prefixes"]):
        raise ValueError("Independent case count does not match case-prefix scope")

    report: dict[str, Any] = {
        "independent_case_count": case_count,
        "families": {},
        "total_row_count": 0,
    }
    for family, metadata in manifest["outputs"].items():
        if family not in FAMILY_FILES:
            raise ValueError(f"Unknown output family in manifest: {family}")
        result_name, summary_name, stability_name = FAMILY_FILES[family]
        result_path = output_dir / result_name
        summary_path = output_dir / summary_name
        stability_path = output_dir / stability_name
        for path in (result_path, summary_path, stability_path):
            if not path.is_file():
                raise FileNotFoundError(path)
        expected_hashes = {
            result_path: metadata["result_sha256"],
            summary_path: metadata["summary_sha256"],
            stability_path: metadata["paired_stability_sha256"],
        }
        for path, expected in expected_hashes.items():
            actual = sha256_file(path)
            if actual != expected:
                raise ValueError(
                    f"SHA-256 mismatch for {path.name}: {actual} != {expected}"
                )

        rows = read_csv(result_path)
        if len(rows) != int(metadata["row_count"]):
            raise ValueError(
                f"Row-count mismatch for {family}: {len(rows)} != "
                f"{metadata['row_count']}"
            )
        keys = [tuple(row[field] for field in PAIR_KEY_FIELDS) for row in rows]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate paired condition keys in {family}")
        cases = {row["case_id"] for row in rows}
        if len(cases) != case_count:
            raise ValueError(
                f"Family {family} has {len(cases)} cases, expected {case_count}"
            )

        summary = load_json(summary_path)
        stability = load_json(stability_path)
        variants = {row["governance_variant"] for row in rows}
        if set(summary) != variants:
            raise ValueError(f"Summary variants do not match rows for {family}")
        if int(stability["variant_count"]) != len(variants):
            raise ValueError(f"Stability variant count mismatch for {family}")
        if stability["analysis_unit"] != "case_or_attack_chain":
            raise ValueError(f"Invalid stability analysis unit for {family}")
        for variant_summary in summary.values():
            for planner_summary in variant_summary.values():
                endpoint = planner_summary["evidence_limited"]
                if endpoint["external_actor_accuracy"] is not None:
                    raise ValueError(
                        f"External actor accuracy was fabricated in {family}"
                    )
                if "not_identifiable" not in endpoint[
                    "external_actor_accuracy_status"
                ]:
                    raise ValueError(
                        f"Missing actor-GT non-identifiability in {family}"
                    )
        for planner_variants in stability["by_planner"].values():
            if set(planner_variants) != variants:
                raise ValueError(
                    f"Paired stability does not cover all variants for {family}"
                )
            for variant in planner_variants.values():
                independent = variant["independent_case_summary"]
                if int(independent["independent_case_count"]) != case_count:
                    raise ValueError(
                        f"Case-level stability count mismatch for {family}"
                    )

        if family == "cost":
            regimes = {row["cost_regime"] for row in rows}
            if regimes != {"legacy", "uniform"}:
                raise ValueError(f"Unexpected executed cost regimes: {regimes}")
            if set(metadata["blocked_regimes"]) != {"rubric", "measured"}:
                raise ValueError("Formal blocked cost regimes were not preserved")

        report["families"][family] = {
            "row_count": len(rows),
            "variant_count": len(variants),
            "planner_count": len({row["planner"] for row in rows}),
            "sha256_verified": True,
            "paired_case_level_verified": True,
            "actor_accuracy_not_fabricated": True,
        }
        report["total_row_count"] += len(rows)

    unified_path = output_dir / "governance_stability_summary.json"
    if sha256_file(unified_path) != manifest["unified_stability_summary_sha256"]:
        raise ValueError("Unified stability summary SHA-256 mismatch")
    coverage = manifest["methodology_parameter_coverage"]
    if coverage["all_experiments_complete"] is not False:
        raise ValueError("Incomplete human/operational gates were marked complete")
    if not str(coverage["paper_or_patent_gate"]).startswith("closed"):
        raise ValueError("Paper/patent gate is not closed")
    report["unified_stability_sha256_verified"] = True
    report["paper_or_patent_gate"] = coverage["paper_or_patent_gate"]
    report["validation_status"] = "passed"
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
