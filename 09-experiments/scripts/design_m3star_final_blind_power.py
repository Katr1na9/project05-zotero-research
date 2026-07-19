#!/usr/bin/env python3
"""Precompute case-level power for the sealed M3* final-blind evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from scipy.stats import nct, t


PRIMARY_BASELINES = (
    "project05_m2",
    "project05_xgboost_policy",
    "project05_m3b_policy",
    "afa_voi_myopic",
    "afa_voi_rollout_h3",
    "project05_depth2_public",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def required_paired_t_n(
    effect: float,
    standard_deviation: float,
    alpha: float,
    target_power: float,
    maximum_n: int = 10000,
) -> dict[str, Any]:
    if effect <= 0.0 or standard_deviation <= 0.0:
        raise ValueError("Effect and standard deviation must be positive")
    if not 0.0 < alpha < 0.5 or not 0.0 < target_power < 1.0:
        raise ValueError("Invalid alpha or target power")
    standardized_effect = effect / standard_deviation
    for sample_size in range(3, maximum_n + 1):
        degrees_freedom = sample_size - 1
        critical_value = t.ppf(alpha, degrees_freedom)
        noncentrality = -standardized_effect * math.sqrt(sample_size)
        achieved_power = float(
            nct.cdf(critical_value, degrees_freedom, noncentrality)
        )
        if achieved_power >= target_power:
            return {
                "complete_independent_case_count": sample_size,
                "achieved_power": achieved_power,
                "standardized_effect": standardized_effect,
            }
    raise ValueError(f"Required sample size exceeds {maximum_n}")


def recruit_count(complete_count: int, invalid_fraction: float) -> int:
    if complete_count < 1 or not 0.0 <= invalid_fraction < 1.0:
        raise ValueError("Invalid completion target or invalid fraction")
    return math.ceil(complete_count / (1.0 - invalid_fraction))


def zero_event_upper_bound(
    sample_size: int,
    alpha: float = 0.05,
) -> float:
    """Exact one-sided Clopper-Pearson upper bound after zero events."""

    if sample_size < 1 or not 0.0 < alpha < 1.0:
        raise ValueError("Invalid zero-event interval inputs")
    return 1.0 - alpha ** (1.0 / sample_size)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development-analysis", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    development = json.loads(
        args.development_analysis.read_text(encoding="utf-8")
    )
    if development.get("independent_statistical_unit") != "case_id":
        raise ValueError("Development analysis does not use case-level inference")
    m2 = development["paired_case_level_effects"]["project05_m2"]
    m2_cost = m2["case_mean_cost_delta_descriptives"]

    sesoi = 0.05
    target_power = 0.90
    global_alpha = 0.05
    invalid_fraction = 0.15
    sd_scenarios = (0.10, 0.125, 0.15)
    sensitivity: list[dict[str, Any]] = []
    for standard_deviation in sd_scenarios:
        global_result = required_paired_t_n(
            sesoi,
            standard_deviation,
            global_alpha,
            target_power,
        )
        holm_result = required_paired_t_n(
            sesoi,
            standard_deviation,
            global_alpha / len(PRIMARY_BASELINES),
            target_power,
        )
        sensitivity.append(
            {
                "case_level_standard_deviation": standard_deviation,
                "global_conjunction": {
                    **global_result,
                    "recruitment_case_count_with_invalid_reserve": recruit_count(
                        global_result["complete_independent_case_count"],
                        invalid_fraction,
                    ),
                },
                "six_separate_holm_claims_worst_threshold": {
                    **holm_result,
                    "alpha": global_alpha / len(PRIMARY_BASELINES),
                    "recruitment_case_count_with_invalid_reserve": recruit_count(
                        holm_result["complete_independent_case_count"],
                        invalid_fraction,
                    ),
                },
            }
        )

    conservative = sensitivity[-1]["global_conjunction"]
    complete_required = int(conservative["complete_independent_case_count"])
    recruit_required = int(
        conservative["recruitment_case_count_with_invalid_reserve"]
    )
    operational_recruitment_target = int(math.ceil(recruit_required / 4.0) * 4)
    report = {
        "design_id": "project05-m3star-final-blind-power-design-v0.1",
        "status": "preregistration_candidate_not_yet_frozen",
        "paper_or_patent_updated": False,
        "final_blind_data_loaded": False,
        "c13_plus_boundary": "sealed",
        "independent_statistical_unit": "attack_chain_case_id",
        "within_case_conditions": {
            "count": 45,
            "role": "paired_repeated_measurements_only",
            "never_counted_as_independent_n": True,
        },
        "confirmatory_claim": (
            "M3* passes success/safety gates and has lower case-mean measured "
            "cost than every prespecified primary baseline"
        ),
        "primary_baselines": list(PRIMARY_BASELINES),
        "oracle_role": "ceiling_reference_not_a_baseline_to_outperform",
        "multiplicity": {
            "global_claim_structure": "intersection_union",
            "rule": "every baseline comparison must pass",
            "per_comparison_one_sided_alpha": global_alpha,
            "why_no_alpha_split_for_global_claim": (
                "the global null is the union of baseline-specific nulls and "
                "the superiority claim is made only if all are rejected"
            ),
            "separate_baseline_specific_claims": (
                "secondary_only_and_Holm_adjusted_if_reported_confirmatorily"
            ),
        },
        "cost_power_model": {
            "test": "one_sample_paired_case_mean_t_lower_tail",
            "null": "mean(M3star_cost_minus_baseline_cost) >= 0",
            "design_alternative": (
                "mean(M3star_cost_minus_baseline_cost) <= -0.05"
            ),
            "sesoi_measured_cost_units": sesoi,
            "target_power": target_power,
            "case_level_standard_deviation_sensitivity": list(sd_scenarios),
            "conservative_design_standard_deviation": sd_scenarios[-1],
            "invalid_case_reserve_fraction": invalid_fraction,
            "sensitivity": sensitivity,
        },
        "sample_size_decision": {
            "minimum_valid_complete_independent_cases": complete_required,
            "minimum_recruitment_cases": recruit_required,
            "operational_recruitment_target": operational_recruitment_target,
            "all_cases_must_be_new_and_unseen": True,
            "minimum_case_id_boundary": "C13+",
            "source_and_attack_chain_deduplication_required": True,
            "no_sample_size_reestimation_using_unblinded_outcomes": True,
        },
        "success_safety_gate": {
            "case_success_loss_definition": (
                "case-level M3* success rate is lower than the baseline over "
                "the frozen 45 paired conditions"
            ),
            "required_case_success_loss_count_per_baseline": 0,
            "one_sided_95_percent_upper_probability_after_zero_losses_at_n": {
                "n": complete_required,
                "upper_bound": zero_event_upper_bound(complete_required),
            },
            "maximum_allowed_upper_probability": 0.05,
            "budget_or_safety_violation_count_required": 0,
        },
        "analysis_gate": {
            "all_primary_baselines_must_pass": True,
            "cost_test_uses_case_means": True,
            "case_mean_cost_uses_only_frozen_joint_success_conditions": True,
            "minimum_joint_success_conditions_per_valid_case": 30,
            "effect_and_confidence_interval_reported_for_every_baseline": True,
            "permutation_or_wilcoxon_sensitivity_is_secondary": True,
            "failure_of_any_primary_gate_forbids_global_superiority_claim": True,
        },
        "development_context_not_used_as_independent_confirmation": {
            "case_count": development["independent_unit_count"],
            "m2_case_mean_cost_delta": m2_cost["mean"],
            "m2_case_mean_cost_delta_sd": m2_cost["sd"],
            "raw_development_effect_used_as_power_alternative": False,
            "reason": "small reused development cohort; fixed SESOI and SD sensitivity govern N",
        },
        "input_sha256": {
            "development_analysis": sha256(args.development_analysis),
            "design_script": sha256(Path(__file__)),
        },
    }
    path = args.output_dir / "power_design.json"
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report["sample_size_decision"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
