#!/usr/bin/env python3
"""Build a hash-anchored post-run audit without modifying frozen results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "09-experiments"
DEFAULT_SOURCE = EXPERIMENT_ROOT / "results" / "parameter_governance_v0.1"
DEFAULT_CORRECTED = (
    EXPERIMENT_ROOT / "results" / "parameter_governance_w6_v0.2"
)
DEFAULT_OUTPUT = (
    EXPERIMENT_ROOT / "results" / "parameter_governance_audit_v0.1"
)
PAIR_FIELDS = (
    "case_id",
    "mask_strategy",
    "mask_intensity",
    "seed",
    "planner",
)
CONDITION_FIELDS = PAIR_FIELDS[:-1]
OUTCOME_FIELDS = (
    "reached_target",
    "explicit_stop",
    "correct_target_stop",
    "correct_degrade_stop",
    "correct_stop",
    "ceiling_violation",
    "cost_to_target",
    "budget_used",
    "steps_to_target",
    "steps_taken",
    "actions_taken",
    "zero_yield_actions",
    "overlap_waste_cost",
    "initial_hidden_claims",
    "recovered_claims",
    "final_granularity",
    "final_node_coverage",
    "final_edge_coverage",
    "final_critical_gap_count",
    "premature_stop",
    "justified_degrade_stop",
    "oracle_reachable",
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


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def require_complete_run(path: Path, family: str) -> dict[str, Any]:
    manifest_path = path / "run_manifest.json"
    manifest = load_json(manifest_path)
    metadata = manifest["outputs"][family]
    names = {
        "result_sha256": (
            "action_prior_results.csv"
            if family == "priors"
            else None
        ),
        "summary_sha256": (
            "action_prior_summary.json"
            if family == "priors"
            else None
        ),
        "paired_stability_sha256": (
            "action_prior_paired_stability.json"
            if family == "priors"
            else None
        ),
    }
    for field, filename in names.items():
        if filename is None:
            continue
        actual = sha256_file(path / filename)
        if actual != metadata[field]:
            raise ValueError(
                f"Frozen result hash mismatch for {path / filename}: "
                f"{actual} != {metadata[field]}"
            )
    return manifest


def index_variant(
    rows: list[dict[str, str]], variant: str, planner: str | None = None
) -> dict[tuple[str, ...], dict[str, str]]:
    fields = CONDITION_FIELDS if planner is not None else PAIR_FIELDS
    selected = [
        row
        for row in rows
        if row["governance_variant"] == variant
        and (planner is None or row["planner"] == planner)
    ]
    indexed = {tuple(row[field] for field in fields): row for row in selected}
    if len(indexed) != len(selected):
        raise ValueError(f"Duplicate paired rows for {variant}/{planner}")
    return indexed


def transition_count(
    reference: dict[tuple[str, ...], dict[str, str]],
    candidate: dict[tuple[str, ...], dict[str, str]],
    reference_value: int,
    candidate_value: int,
) -> int:
    if set(reference) != set(candidate):
        raise ValueError("Variant pairing keys differ")
    return sum(
        int(reference[key]["reached_target"]) == reference_value
        and int(candidate[key]["reached_target"]) == candidate_value
        for key in reference
    )


def outcome_difference_count(
    reference: dict[tuple[str, ...], dict[str, str]],
    candidate: dict[tuple[str, ...], dict[str, str]],
) -> int:
    if set(reference) != set(candidate):
        raise ValueError("Variant pairing keys differ")
    return sum(
        tuple(reference[key].get(field, "") for field in OUTCOME_FIELDS)
        != tuple(candidate[key].get(field, "") for field in OUTCOME_FIELDS)
        for key in reference
    )


def project05_family_envelopes(source_dir: Path) -> dict[str, Any]:
    summary = load_json(source_dir / "governance_stability_summary.json")
    return {
        family: value["robustness_envelope_by_planner"]["project05_m2"]
        for family, value in summary.items()
    }


def build_findings(source_dir: Path, corrected_dir: Path) -> dict[str, Any]:
    source_manifest = require_complete_run(source_dir, "priors")
    corrected_manifest = require_complete_run(corrected_dir, "priors")
    source_rows = read_csv(source_dir / "action_prior_results.csv")
    corrected_rows = read_csv(corrected_dir / "action_prior_results.csv")

    old_legacy = index_variant(source_rows, "legacy_priors", "project05_m2")
    old_channel_low = index_variant(
        source_rows, "dev_measured_channel_x0.75", "project05_m2"
    )
    old_losses = transition_count(old_legacy, old_channel_low, 1, 0)

    legacy = index_variant(corrected_rows, "legacy_priors", "project05_m2")
    dev_base = index_variant(
        corrected_rows, "dev_measured_base", "project05_m2"
    )
    expert_low = index_variant(
        corrected_rows, "dev_measured_expert_x0.75", "project05_m2"
    )
    expert_high = index_variant(
        corrected_rows, "dev_measured_expert_x1.25", "project05_m2"
    )
    channel_low_m2 = index_variant(
        corrected_rows, "dev_measured_channel_x0.75", "project05_m2"
    )
    channel_high_m2 = index_variant(
        corrected_rows, "dev_measured_channel_x1.25", "project05_m2"
    )

    all_dev = index_variant(corrected_rows, "dev_measured_base")
    all_channel_low = index_variant(
        corrected_rows, "dev_measured_channel_x0.75"
    )
    all_channel_high = index_variant(
        corrected_rows, "dev_measured_channel_x1.25"
    )
    corrected_loss_keys = [
        key
        for key in legacy
        if int(legacy[key]["reached_target"]) == 1
        and int(dev_base[key]["reached_target"]) == 0
    ]
    cases_with_loss = sorted({key[0] for key in corrected_loss_keys})

    by_pair: dict[tuple[str, ...], set[str]] = {}
    for row in corrected_rows:
        key = tuple(row[field] for field in PAIR_FIELDS)
        by_pair.setdefault(key, set()).add(
            row["execution_channel_profile_sha256"]
        )
    execution_invariant = all(len(hashes) == 1 for hashes in by_pair.values())
    scopes = {row["channel_prior_scope"] for row in corrected_rows}
    consumed = {
        int(row["channel_prior_consumed_by_planner"])
        for row in corrected_rows
    }

    stability = load_json(
        corrected_dir / "action_prior_paired_stability.json"
    )
    envelope = stability["robustness_envelope_by_planner"]["project05_m2"]
    coverage = corrected_manifest["methodology_parameter_coverage"]
    return {
        "audit_id": "project05-parameter-governance-postrun-audit-v0.1",
        "audit_status": "complete_with_external_gates_open",
        "source_anchors": {
            "parameter_governance_v0.1_manifest_sha256": sha256_file(
                source_dir / "run_manifest.json"
            ),
            "corrected_w6_v0.2_manifest_sha256": sha256_file(
                corrected_dir / "run_manifest.json"
            ),
            "source_runner_sha256": source_manifest["runner_sha256"],
            "corrected_runner_sha256": corrected_manifest["runner_sha256"],
        },
        "statistical_boundary": {
            "independent_unit": "case_or_attack_chain",
            "independent_case_count": 6,
            "repeated_unit": "mask_strategy_x_mask_intensity_x_channel_seed",
            "pseudoreplication_prohibited": True,
            "inferential_statistics": "not_reported",
            "reason": "Only six independent cases are available and the 45 conditions per case are repeated measurements.",
        },
        "source_family_envelopes_project05_m2": project05_family_envelopes(
            source_dir
        ),
        "W6_channel_prior_confounding": {
            "v0.1_project05_m2_losses_vs_legacy": old_losses,
            "v0.1_project05_m2_loss_case_count": len(
                {
                    key[0]
                    for key in old_legacy
                    if int(old_legacy[key]["reached_target"]) == 1
                    and int(old_channel_low[key]["reached_target"]) == 0
                }
            ),
            "v0.1_channel_prior_inference_invalid": True,
            "reason": (
                "The v0.1 channel multiplier changed the execution-channel "
                "reliability used to realize channel_up, while built-in planners "
                "did not consume a separate channel-belief field. The intervention "
                "therefore mixed environment degradation with prior sensitivity."
            ),
            "v0.2_channel_prior_scope": (
                next(iter(scopes)) if len(scopes) == 1 else sorted(scopes)
            ),
            "v0.2_execution_profile_invariant_across_variants": execution_invariant,
            "v0.2_builtin_channel_prior_consumed_values": sorted(consumed),
            "v0.2_builtin_outcome_differences_channel_x0.75_vs_dev_base": outcome_difference_count(
                all_dev, all_channel_low
            ),
            "v0.2_builtin_outcome_differences_channel_x1.25_vs_dev_base": outcome_difference_count(
                all_dev, all_channel_high
            ),
            "remaining_test": "Run channel-belief sensitivity on AFA and depth-2 planners, which actually consume channel priors, while holding execution reliability fixed.",
        },
        "W6_corrected_project05_m2": {
            "analysis_unit": "case_or_attack_chain",
            "independent_case_count": len({key[0] for key in legacy}),
            "repeated_condition_count": len(legacy),
            "candidate_success_rate_min": envelope["candidate_success_rate_min"],
            "candidate_success_rate_max": envelope["candidate_success_rate_max"],
            "maximum_success_flip_rate_vs_legacy": envelope[
                "maximum_success_flip_rate_vs_baseline"
            ],
            "minimum_action_sequence_agreement_vs_legacy": envelope[
                "minimum_action_sequence_agreement_vs_baseline"
            ],
            "maximum_ceiling_violation_rate": envelope[
                "maximum_ceiling_violation_rate"
            ],
            "dev_base_losses_vs_legacy": transition_count(
                legacy, dev_base, 1, 0
            ),
            "expert_x0.75_additional_losses_vs_dev_base": transition_count(
                dev_base, expert_low, 1, 0
            ),
            "expert_x1.25_repairs_vs_dev_base": transition_count(
                dev_base, expert_high, 0, 1
            ),
            "channel_x0.75_outcome_differences_vs_dev_base": outcome_difference_count(
                dev_base, channel_low_m2
            ),
            "channel_x1.25_outcome_differences_vs_dev_base": outcome_difference_count(
                dev_base, channel_high_m2
            ),
            "cases_with_loss": cases_with_loss,
            "failure_conditions": [
                {
                    "case_id": key[0],
                    "mask_strategy": key[1],
                    "mask_intensity": key[2],
                    "seed": key[3],
                    "actions_taken": dev_base[key]["actions_taken"],
                    "premature_stop": int(dev_base[key]["premature_stop"]),
                    "justified_degrade_stop": int(
                        dev_base[key]["justified_degrade_stop"]
                    ),
                }
                for key in sorted(corrected_loss_keys)
            ],
            "inferential_statistics": "not_reported",
        },
        "completion_gates": {
            "rubric_cost": "blocked_pending_two_real_independent_raters_and_agreement",
            "measured_cost": "blocked_pending_action_level_operational_measurements",
            "round2_annotation": "blocked_pending_two_real_independent_annotators",
            "external_actor_accuracy": "not_identifiable_without_actor_or_analyst_utility_ground_truth",
            "all_experiments_complete": False,
            "paper_or_patent_gate": coverage["paper_or_patent_gate"],
        },
    }


def case_rows(
    corrected_dir: Path, findings: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = read_csv(corrected_dir / "action_prior_results.csv")
    stability = load_json(
        corrected_dir / "action_prior_paired_stability.json"
    )["by_planner"]["project05_m2"]
    output: list[dict[str, Any]] = []
    variants = list(load_json(corrected_dir / "action_prior_summary.json"))
    for variant in variants:
        selected = [
            row
            for row in rows
            if row["planner"] == "project05_m2"
            and row["governance_variant"] == variant
        ]
        for case_id in sorted({row["case_id"] for row in selected}):
            case = [row for row in selected if row["case_id"] == case_id]
            summary = stability[variant]["case_level"][case_id]
            output.append(
                {
                    "variant": variant,
                    "case_id": case_id,
                    "independent_unit": "case_or_attack_chain",
                    "repeated_condition_count": len(case),
                    "success_count": sum(int(row["reached_target"]) for row in case),
                    "success_rate": round(
                        sum(int(row["reached_target"]) for row in case) / len(case),
                        4,
                    ),
                    "success_flip_rate_vs_legacy": summary["success_flip_rate"],
                    "action_sequence_agreement_vs_legacy": summary[
                        "action_sequence_agreement_rate"
                    ],
                    "ceiling_violation_rate": summary[
                        "candidate_ceiling_violation_rate"
                    ],
                }
            )
    return output


def failure_rows(findings: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "analysis_unit": "case_or_attack_chain",
            "condition_role": "within_case_repeated_measure",
        }
        for row in findings["W6_corrected_project05_m2"]["failure_conditions"]
    ]


def readme(findings: dict[str, Any]) -> str:
    corrected = findings["W6_corrected_project05_m2"]
    confounding = findings["W6_channel_prior_confounding"]
    envelopes = findings["source_family_envelopes_project05_m2"]
    rows = []
    labels = {
        "C_cost": "C cost",
        "W1_thresholds": "W1 thresholds",
        "W7_corroboration": "W7 corroboration",
        "W2_m2_alpha": "W2 alpha",
    }
    for key in ("C_cost", "W1_thresholds", "W7_corroboration", "W2_m2_alpha"):
        value = envelopes[key]
        rows.append(
            f"| {labels[key]} | {value['candidate_success_rate_min']:.4f}–"
            f"{value['candidate_success_rate_max']:.4f} | "
            f"{value['maximum_success_flip_rate_vs_baseline']:.4f} | "
            f"{value['minimum_action_sequence_agreement_vs_baseline']:.4f} |"
        )
    rows.append(
        f"| W6 corrected priors | {corrected['candidate_success_rate_min']:.4f}–"
        f"{corrected['candidate_success_rate_max']:.4f} | "
        f"{corrected['maximum_success_flip_rate_vs_legacy']:.4f} | "
        f"{corrected['minimum_action_sequence_agreement_vs_legacy']:.4f} |"
    )
    table = "\n".join(rows)
    return f"""# Project05 parameter-governance post-run audit v0.1

This directory is an audit overlay. It does not modify the frozen v0.1 results and does not update any paper or patent.

## Main correction

The v0.1 W6 `channel ×0.75` arm mixed planner belief with execution-channel degradation. Its {confounding['v0.1_project05_m2_losses_vs_legacy']} Project05-M2 losses are therefore not valid evidence of channel-prior sensitivity. In the corrected v0.2 run, execution reliability is fixed and channel multipliers are planner-belief-only. Built-in planners do not consume that field, so both channel arms have zero outcome differences from `dev_measured_base`.

The remaining corrected W6 effect comes from the development-derived expected-effects profile: {corrected['dev_base_losses_vs_legacy']} losses among 270 repeated conditions, all within one of six independent cases (C11). Expert-prior ×1.25 repairs those three conditions; ×0.75 adds no further losses. These are descriptive case-level findings, not an inferential sample of 270 attacks.

## Project05-M2 robustness envelopes

| Family | Success-rate range | Max flip vs baseline | Min action-sequence agreement |
|---|---:|---:|---:|
{table}

## Open gates

- Rubric cost awaits two real independent raters and agreement statistics.
- Measured cost awaits action-level operational measurements.
- W3 Round 2 awaits two real independent annotators.
- External actor/selective accuracy awaits external actor or analyst-utility ground truth.
- Channel-prior sensitivity still requires AFA/depth-2 runners with fixed execution reliability.

`all_experiments_complete=false`; the paper/patent gate remains closed.
"""


def write_audit(
    output_dir: Path,
    source_dir: Path,
    corrected_dir: Path,
) -> dict[str, Any]:
    if output_dir.exists() and (
        not output_dir.is_dir() or any(output_dir.iterdir())
    ):
        raise FileExistsError(f"Audit output must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    findings = build_findings(source_dir, corrected_dir)
    findings_path = output_dir / "findings.json"
    case_path = output_dir / "w6_case_findings.csv"
    failure_path = output_dir / "w6_failure_conditions.csv"
    readme_path = output_dir / "README.md"
    write_json(findings_path, findings)
    write_csv(case_path, case_rows(corrected_dir, findings))
    write_csv(failure_path, failure_rows(findings))
    readme_path.write_text(readme(findings), encoding="utf-8", newline="\n")
    manifest = {
        "audit_id": findings["audit_id"],
        "status": "frozen_postrun_audit",
        "source_anchors": findings["source_anchors"],
        "outputs": {
            path.name: sha256_file(path)
            for path in (findings_path, case_path, failure_path, readme_path)
        },
        "independent_unit": "case_or_attack_chain",
        "inferential_statistics_reported": False,
        "frozen_results_modified": False,
        "paper_or_patent_updated": False,
    }
    write_json(output_dir / "audit_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--corrected-dir", type=Path, default=DEFAULT_CORRECTED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = write_audit(args.output_dir, args.source_dir, args.corrected_dir)
    print(
        json.dumps(
            {
                "audit_id": manifest["audit_id"],
                "output_dir": str(args.output_dir),
                "output_count": len(manifest["outputs"]),
                "paper_or_patent_updated": False,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
