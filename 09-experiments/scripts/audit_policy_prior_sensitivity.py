#!/usr/bin/env python3
"""Audit AFA and Depth-2 channel-belief sensitivity with fixed execution state."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "09-experiments" / "results"
DEFAULT_AFA = {
    "x0.75": RESULTS / "afa_endpoint_c07_c12_prior_x0.75_v0.1",
    "x1.00": RESULTS / "afa_endpoint_c07_c12_v0.1",
    "x1.25": RESULTS / "afa_endpoint_c07_c12_prior_x1.25_v0.1",
}
DEFAULT_DEPTH2 = {
    "x0.75": RESULTS / "depth2_endpoint_c07_c12_prior_x0.75_v0.2",
    "x1.00": RESULTS / "depth2_endpoint_c07_c12_v0.2",
    "x1.25": RESULTS / "depth2_endpoint_c07_c12_prior_x1.25_v0.2",
}
DEFAULT_OUTPUT = RESULTS / "policy_prior_sensitivity_audit_v0.1"
KEY_FIELDS = (
    "case_id",
    "mask_strategy",
    "mask_intensity",
    "seed",
    "planner",
)
OUTCOME_FIELDS = (
    "reached_target",
    "cost_to_target",
    "budget_used",
    "actions_taken",
    "final_granularity",
    "final_node_coverage",
    "final_edge_coverage",
    "correct_stop",
    "premature_stop",
    "justified_degrade_stop",
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


def verify_run(path: Path) -> dict[str, Any]:
    manifest = load_json(path / "evaluation_manifest.json")
    for filename, expected in manifest["output_sha256"].items():
        actual = sha256_file(path / filename)
        if actual != expected:
            raise ValueError(f"Output hash mismatch: {path / filename}")
    return manifest


def indexed_rows(path: Path, filename: str) -> dict[tuple[str, ...], dict[str, str]]:
    rows = read_csv(path / filename)
    indexed = {tuple(row[field] for field in KEY_FIELDS): row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"Duplicate paired keys in {path / filename}")
    return indexed


def outcome_signature(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row.get(field, "") for field in OUTCOME_FIELDS)


def compare_planner(
    baseline: dict[tuple[str, ...], dict[str, str]],
    candidate: dict[tuple[str, ...], dict[str, str]],
    planner: str,
) -> dict[str, Any]:
    keys = sorted(key for key in baseline if key[-1] == planner)
    if set(keys) != {key for key in candidate if key[-1] == planner}:
        raise ValueError(f"Pairing mismatch for {planner}")
    changed = [
        key
        for key in keys
        if outcome_signature(baseline[key]) != outcome_signature(candidate[key])
    ]
    losses = [
        key
        for key in keys
        if int(baseline[key]["reached_target"]) == 1
        and int(candidate[key]["reached_target"]) == 0
    ]
    gains = [
        key
        for key in keys
        if int(baseline[key]["reached_target"]) == 0
        and int(candidate[key]["reached_target"]) == 1
    ]
    action_changes = [
        key
        for key in keys
        if baseline[key]["actions_taken"] != candidate[key]["actions_taken"]
    ]
    return {
        "paired_repeated_condition_count": len(keys),
        "baseline_success_count": sum(
            int(baseline[key]["reached_target"]) for key in keys
        ),
        "candidate_success_count": sum(
            int(candidate[key]["reached_target"]) for key in keys
        ),
        "success_losses": len(losses),
        "success_gains": len(gains),
        "outcome_difference_count": len(changed),
        "action_sequence_changes": len(action_changes),
        "cases_with_outcome_difference": sorted({key[0] for key in changed}),
        "cases_with_success_flip": sorted({key[0] for key in losses + gains}),
        "success_flip_conditions": [
            {
                "direction": "loss" if key in losses else "gain",
                "case_id": key[0],
                "mask_strategy": key[1],
                "mask_intensity": key[2],
                "seed": key[3],
                "baseline_actions": baseline[key]["actions_taken"],
                "candidate_actions": candidate[key]["actions_taken"],
            }
            for key in losses + gains
        ],
    }


def family_findings(
    paths: dict[str, Path],
    results_filename: str,
    planners: list[str],
    runtime_allowlist_enforced: bool | None,
    hidden_outcome_invariance_tested: bool,
) -> dict[str, Any]:
    manifests = {variant: verify_run(path) for variant, path in paths.items()}
    if runtime_allowlist_enforced is None:
        runtime_claims = {
            bool(
                manifest.get("endpoint_contract", manifest.get("endpoint_boundary", {})).get(
                    "runtime_allowlist_enforced", False
                )
            )
            for manifest in manifests.values()
        }
        if len(runtime_claims) != 1:
            raise ValueError("Runtime-allowlist claim differs across sensitivity arms")
        runtime_allowlist_enforced = runtime_claims.pop()
    rows = {
        variant: indexed_rows(path, results_filename)
        for variant, path in paths.items()
    }
    baseline = rows["x1.00"]
    all_keys = set(baseline)
    execution_invariant = True
    for variant, candidate in rows.items():
        if set(candidate) != all_keys:
            raise ValueError(f"Pairing mismatch in {variant}")
        for key in all_keys:
            if (
                candidate[key]["execution_channel_profile_sha256"]
                != baseline[key]["execution_channel_profile_sha256"]
            ):
                execution_invariant = False
    return {
        "independent_case_count": int(
            manifests["x1.00"]["independent_case_count"]
        ),
        "repeated_condition_count": int(
            manifests["x1.00"]["repeated_condition_count"]
        ),
        "analysis_unit": "case_or_attack_chain",
        "execution_profile_invariant_across_prior_arms": execution_invariant,
        "runtime_allowlist_enforced": runtime_allowlist_enforced,
        "hidden_outcome_invariance_tested": hidden_outcome_invariance_tested,
        "x0.75": {
            planner: compare_planner(baseline, rows["x0.75"], planner)
            for planner in planners
        },
        "x1.25": {
            planner: compare_planner(baseline, rows["x1.25"], planner)
            for planner in planners
        },
    }


def build_findings(
    afa_paths: dict[str, Path] | None = None,
    depth2_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    afa = afa_paths or DEFAULT_AFA
    depth2 = depth2_paths or DEFAULT_DEPTH2
    anchors = {
        f"AFA_{variant}_manifest_sha256": sha256_file(
            path / "evaluation_manifest.json"
        )
        for variant, path in afa.items()
    }
    anchors.update(
        {
            f"Depth2_{variant}_manifest_sha256": sha256_file(
                path / "evaluation_manifest.json"
            )
            for variant, path in depth2.items()
        }
    )
    return {
        "audit_id": "project05-policy-prior-sensitivity-audit-v0.1",
        "source_anchors": dict(sorted(anchors.items())),
        "statistical_boundary": {
            "independent_unit": "case_or_attack_chain",
            "independent_case_count": 6,
            "repeated_unit": "mask_strategy_x_mask_intensity_x_seed",
            "repeated_conditions_must_not_be_counted_as_independent_attacks": True,
            "inferential_statistics": "not_reported",
        },
        "AFA": family_findings(
            afa,
            "afa_voi_policy_results.csv",
            [
                "project05_m2",
                "afa_voi_myopic",
                "afa_voi_rollout_h3",
                "oracle_optimal",
            ],
            runtime_allowlist_enforced=None,
            hidden_outcome_invariance_tested=True,
        ),
        "Depth2": family_findings(
            depth2,
            "nonmyopic_policy_results.csv",
            ["project05_m2", "project05_depth2_public", "oracle_optimal"],
            runtime_allowlist_enforced=None,
            hidden_outcome_invariance_tested=True,
        ),
        "all_experiments_complete": False,
        "paper_or_patent_gate": "closed_until_human_and_operational_gates_are_satisfied",
        "paper_or_patent_updated": False,
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def case_rows(findings: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in ("AFA", "Depth2"):
        for variant in ("x0.75", "x1.25"):
            for planner, summary in findings[family][variant].items():
                changed_cases = set(summary["cases_with_outcome_difference"])
                flip_cases = set(summary["cases_with_success_flip"])
                for case_id in sorted(changed_cases | flip_cases):
                    rows.append(
                        {
                            "family": family,
                            "variant": variant,
                            "planner": planner,
                            "case_id": case_id,
                            "independent_unit": "case_or_attack_chain",
                            "has_outcome_difference": int(case_id in changed_cases),
                            "has_success_flip": int(case_id in flip_cases),
                        }
                    )
    return rows


def flip_rows(findings: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in ("AFA", "Depth2"):
        for variant in ("x0.75", "x1.25"):
            for planner, summary in findings[family][variant].items():
                for flip in summary["success_flip_conditions"]:
                    rows.append(
                        {
                            "family": family,
                            "variant": variant,
                            "planner": planner,
                            **flip,
                            "condition_role": "within_case_repeated_measure",
                        }
                    )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty audit CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def readme(findings: dict[str, Any]) -> str:
    afa_low = findings["AFA"]["x0.75"]
    depth_low = findings["Depth2"]["x0.75"]["project05_depth2_public"]
    depth_boundary = (
        "Depth-2 now uses the frozen dedicated runtime allowlist; declared "
        "expected effects remain visible while realized outcomes are forbidden."
        if findings["Depth2"]["runtime_allowlist_enforced"]
        else "Depth-2 has tested hidden-outcome invariance but still requires a dedicated allowlist that permits declared `expected_effects`; this gap remains open and is not represented as complete."
    )
    return f"""# Policy channel-prior sensitivity audit

All comparisons are paired within six independent cases. The 270 mask/intensity/seed conditions are repeated measurements, not 270 independent attacks. No inferential p-values are reported.

## Findings

- AFA myopic at ×0.75: {afa_low['afa_voi_myopic']['success_losses']} success losses and {afa_low['afa_voi_myopic']['outcome_difference_count']} outcome differences versus ×1.00.
- AFA rollout-h3 at ×0.75: success unchanged, but {afa_low['afa_voi_rollout_h3']['action_sequence_changes']} action sequences changed.
- Depth-2 at ×0.75: {depth_low['success_losses']} loss and {depth_low['success_gains']} gain offset in the aggregate success count; {depth_low['action_sequence_changes']} action sequences changed.
- At ×1.25, no tested policy changed actions or outcomes under the present discrete decision boundary.
- M2 and oracle controls did not change across prior arms, supporting fixed execution-environment isolation.

## Endpoint boundary

AFA uses the frozen runtime allowlist. {depth_boundary}

`all_experiments_complete=false`; paper/patent writing remains closed.
"""


def write_audit(
    output_dir: Path,
    afa_paths: dict[str, Path] | None = None,
    depth2_paths: dict[str, Path] | None = None,
    audit_id: str | None = None,
) -> dict[str, Any]:
    if output_dir.exists() and (
        not output_dir.is_dir() or any(output_dir.iterdir())
    ):
        raise FileExistsError(f"Audit output must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    findings = build_findings(afa_paths, depth2_paths)
    if audit_id is not None:
        findings["audit_id"] = audit_id
    findings_path = output_dir / "findings.json"
    cases_path = output_dir / "case_level_changes.csv"
    flips_path = output_dir / "paired_success_flips.csv"
    readme_path = output_dir / "README.md"
    write_json(findings_path, findings)
    write_csv(cases_path, case_rows(findings))
    write_csv(flips_path, flip_rows(findings))
    readme_path.write_text(readme(findings), encoding="utf-8", newline="\n")
    manifest = {
        "audit_id": findings["audit_id"],
        "status": "frozen_postrun_audit",
        "source_anchors": findings["source_anchors"],
        "outputs": {
            path.name: sha256_file(path)
            for path in (findings_path, cases_path, flips_path, readme_path)
        },
        "independent_unit": "case_or_attack_chain",
        "inferential_statistics_reported": False,
        "paper_or_patent_updated": False,
    }
    write_json(output_dir / "audit_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--depth-low", type=Path)
    parser.add_argument("--depth-baseline", type=Path)
    parser.add_argument("--depth-high", type=Path)
    parser.add_argument("--audit-id")
    args = parser.parse_args()
    depth_args = (args.depth_low, args.depth_baseline, args.depth_high)
    if any(depth_args) and not all(depth_args):
        parser.error("--depth-low, --depth-baseline, and --depth-high are required together")
    depth_paths = (
        {"x0.75": args.depth_low, "x1.00": args.depth_baseline, "x1.25": args.depth_high}
        if all(depth_args)
        else None
    )
    manifest = write_audit(
        args.output_dir,
        depth2_paths=depth_paths,
        audit_id=args.audit_id,
    )
    print(
        json.dumps(
            {
                "audit_id": manifest["audit_id"],
                "output_dir": str(args.output_dir),
                "output_count": len(manifest["outputs"]),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
