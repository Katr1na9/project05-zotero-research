#!/usr/bin/env python3
"""Review frozen final-blind sample-size assumptions without opening outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from scipy.stats import nct, t


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object: {path}")
    return value


def paired_lower_tail_power(
    sample_size: int,
    effect: float,
    standard_deviation: float,
    alpha: float,
) -> float:
    degrees_freedom = sample_size - 1
    critical_value = t.ppf(alpha, degrees_freedom)
    noncentrality = -(effect / standard_deviation) * math.sqrt(sample_size)
    return float(nct.cdf(critical_value, degrees_freedom, noncentrality))


def required_n(
    effect: float,
    standard_deviation: float,
    alpha: float,
    target_power: float,
) -> int:
    for sample_size in range(3, 10001):
        if (
            paired_lower_tail_power(
                sample_size, effect, standard_deviation, alpha
            )
            >= target_power
        ):
            return sample_size
    raise ValueError("Required sample size exceeds search boundary")


def minimum_detectable_effect(
    sample_size: int,
    standard_deviation: float,
    alpha: float,
    target_power: float,
) -> float:
    lower = 0.0
    upper = standard_deviation * 3.0
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        if (
            paired_lower_tail_power(
                sample_size, midpoint, standard_deviation, alpha
            )
            >= target_power
        ):
            upper = midpoint
        else:
            lower = midpoint
    return upper


def zero_event_upper_bound(sample_size: int, alpha: float = 0.05) -> float:
    return 1.0 - alpha ** (1.0 / sample_size)


def required_zero_event_n(maximum_upper_probability: float = 0.05) -> int:
    sample_size = 1
    while zero_event_upper_bound(sample_size) > maximum_upper_probability:
        sample_size += 1
    return sample_size


def fixed_n_row(
    sample_size: int,
    effect: float,
    standard_deviation: float,
    alpha: float,
) -> dict[str, Any]:
    return {
        "independent_case_count": sample_size,
        "power_at_frozen_sesoi": paired_lower_tail_power(
            sample_size, effect, standard_deviation, alpha
        ),
        "mde_at_80_percent_power": minimum_detectable_effect(
            sample_size, standard_deviation, alpha, 0.80
        ),
        "mde_at_90_percent_power": minimum_detectable_effect(
            sample_size, standard_deviation, alpha, 0.90
        ),
        "zero_success_loss_one_sided_95_percent_upper_probability": (
            zero_event_upper_bound(sample_size)
        ),
    }


def build_review(
    power_design: dict[str, Any],
    qualification_audit: dict[str, Any],
    cost_profile: dict[str, Any],
    input_hashes: dict[str, str],
) -> dict[str, Any]:
    if power_design.get("final_blind_data_loaded") is not False:
        raise ValueError("Power design is not outcome-blind")
    forbidden_open_flags = (
        "file_contents_returned_to_model_development",
        "ground_truth_opened",
        "cost_values_opened",
        "model_outputs_opened_during_qualification",
        "one_shot_evaluation_consumed",
    )
    for field in forbidden_open_flags:
        if qualification_audit.get(field) is not False:
            raise ValueError(f"Qualification audit violates blind review: {field}")
    scoring = cost_profile.get("scoring", {})
    if scoring.get("unit") != "case_replay_full_scan_equivalent":
        raise ValueError("Unexpected measured-cost unit")

    model = power_design["cost_power_model"]
    decision = power_design["sample_size_decision"]
    effect = float(model["sesoi_measured_cost_units"])
    alpha = float(power_design["multiplicity"]["per_comparison_one_sided_alpha"])
    frozen_target_power = float(model["target_power"])
    conservative_sd = float(model["conservative_design_standard_deviation"])
    current_n = int(qualification_audit["actual_qualified_case_count"])
    unaudited = int(qualification_audit["unaudited_reserve_count"])
    frozen_n = int(decision["minimum_valid_complete_independent_cases"])
    phase_2_remaining = 3
    phase_2_ceiling = current_n + phase_2_remaining
    pool_ceiling = current_n + unaudited
    safety_n = required_zero_event_n(0.05)
    cost_n_80 = required_n(effect, conservative_sd, alpha, 0.80)
    cost_n_90 = required_n(effect, conservative_sd, alpha, 0.90)
    combined_n_80 = max(cost_n_80, safety_n)
    combined_n_90 = max(cost_n_90, safety_n)

    standard_deviations = [0.10, 0.125, 0.15]
    sensitivity = []
    for standard_deviation in standard_deviations:
        sensitivity.append(
            {
                "case_level_standard_deviation": standard_deviation,
                "required_n_at_80_percent_power": required_n(
                    effect, standard_deviation, alpha, 0.80
                ),
                "required_n_at_90_percent_power": required_n(
                    effect, standard_deviation, alpha, 0.90
                ),
            }
        )

    fixed_counts = sorted(
        {current_n, phase_2_ceiling, combined_n_80, pool_ceiling, frozen_n}
    )
    return {
        "review_id": "project05-m3star-final-blind-sample-size-review-v0.1",
        "status": "outcome_free_review_no_protocol_change",
        "paper_or_patent_updated": False,
        "final_blind_outcomes_opened": False,
        "current_frozen_protocol_still_controls": True,
        "input_sha256": input_hashes,
        "threshold_authority": {
            "externally_mandated_case_count": False,
            "statement": (
                "No field authority mandates 79 or 96 cases; both are Project05 "
                "design choices determined by effect, variance, alpha, power, "
                "safety precision, and attrition assumptions."
            ),
        },
        "cost_unit_and_sesoi": {
            "unit": scoring["unit"],
            "formula": scoring["formula"],
            "frozen_sesoi": effect,
            "interpretation": (
                "A 0.05 case-mean difference equals five percent of one "
                "case-local full-scan-equivalent data-access burden."
            ),
            "domain_or_decision_anchor_documented_before_review": False,
        },
        "frozen_assumptions": {
            "one_sided_alpha": alpha,
            "target_power": frozen_target_power,
            "conservative_case_level_standard_deviation": conservative_sd,
            "standardized_effect": effect / conservative_sd,
            "minimum_valid_complete_independent_cases": frozen_n,
            "legacy_recruitment_target": decision["operational_recruitment_target"],
        },
        "current_qualification_checkpoint": {
            "audited_candidate_count": qualification_audit[
                "audited_candidate_count"
            ],
            "qualified_independent_case_count": current_n,
            "not_qualified_count": qualification_audit[
                "actual_not_qualified_count"
            ],
            "unaudited_reserve_count": unaudited,
            "phase_2_ceiling_if_all_three_remaining_qualify": phase_2_ceiling,
            "frozen_pool_ceiling_if_all_reserves_qualify": pool_ceiling,
        },
        "independent_checks": {
            "cost_n_at_80_percent_power": cost_n_80,
            "cost_n_at_90_percent_power": cost_n_90,
            "zero_success_loss_n_for_one_sided_95_percent_upper_at_most_5_percent": safety_n,
            "combined_n_at_80_percent_power": combined_n_80,
            "combined_n_at_90_percent_power": combined_n_90,
        },
        "standard_deviation_sensitivity": sensitivity,
        "fixed_n_sensitivity": [
            fixed_n_row(count, effect, conservative_sd, alpha)
            for count in fixed_counts
        ],
        "design_options": [
            {
                "option": "retain_frozen_90_percent_design",
                "minimum_independent_cases": combined_n_90,
                "additional_qualified_cases_from_current_checkpoint": max(
                    combined_n_90 - current_n, 0
                ),
                "tradeoff": "Highest planned power; largest acquisition burden.",
            },
            {
                "option": "amend_to_conventional_80_percent_plus_safety_precision",
                "minimum_independent_cases": combined_n_80,
                "additional_qualified_cases_from_current_checkpoint": max(
                    combined_n_80 - current_n, 0
                ),
                "tradeoff": (
                    "Power decreases from 90% to at least 80% under the same "
                    "worst-case SD, while the zero-loss 95% upper bound remains "
                    "at most 5%."
                ),
            },
            {
                "option": "stop_at_current_checkpoint",
                "minimum_independent_cases": current_n,
                "additional_qualified_cases_from_current_checkpoint": 0,
                "tradeoff": (
                    "Does not meet either 80% power under SD=0.15 or the frozen "
                    "zero-loss 5% precision threshold; confirmatory claim would "
                    "need to be weakened."
                ),
            },
        ],
        "governance_decision": {
            "automatic_threshold_change_authorized": False,
            "protocol_amendment_required_before_any_threshold_change": True,
            "no_additional_candidate_download_authorized_by_this_review": True,
            "review_does_not_use_qualification_yield_to_estimate_model_effect": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--power-design", type=Path, required=True)
    parser.add_argument("--qualification-audit", type=Path, required=True)
    parser.add_argument("--cost-profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = {
        "power_design": args.power_design.resolve(strict=True),
        "qualification_audit": args.qualification_audit.resolve(strict=True),
        "cost_profile": args.cost_profile.resolve(strict=True),
    }
    review = build_review(
        load_json(paths["power_design"]),
        load_json(paths["qualification_audit"]),
        load_json(paths["cost_profile"]),
        {name: sha256(path) for name, path in paths.items()},
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(review, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(review, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
