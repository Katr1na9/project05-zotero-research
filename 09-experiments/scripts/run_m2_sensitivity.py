#!/usr/bin/env python3
"""Run preregistered M2-weight and granularity-proxy sensitivity analyses."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MVP_PATH = Path(__file__).with_name("run_mvp.py")

BASE_WEIGHTS = {
    "granularity": 2.00,
    "uncertainty": 1.50,
    "risk": 1.50,
    "stage_gap": 1.50,
    "evidence_gap": 1.00,
    "overlap": 1.50,
    "no_yield": 1.00,
    "cost": 0.75,
}

THRESHOLD_VARIANTS = {
    "lenient": {
        "g3_node_coverage": 0.65,
        "g3_edge_coverage": 0.50,
        "g2_node_coverage": 0.35,
        "g2_min_stages": 2,
        "g1_node_coverage": 0.10,
    },
    "default": {
        "g3_node_coverage": 0.75,
        "g3_edge_coverage": 0.60,
        "g2_node_coverage": 0.45,
        "g2_min_stages": 2,
        "g1_node_coverage": 0.15,
    },
    "conservative": {
        "g3_node_coverage": 0.85,
        "g3_edge_coverage": 0.70,
        "g2_node_coverage": 0.55,
        "g2_min_stages": 2,
        "g1_node_coverage": 0.25,
    },
}


def _load_mvp() -> Any:
    spec = importlib.util.spec_from_file_location("project05_sensitivity_mvp", MVP_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load simulator from {MVP_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MVP = _load_mvp()


def weight_variants() -> dict[str, dict[str, float]]:
    variants = {"m2_base": dict(BASE_WEIGHTS)}
    for component in BASE_WEIGHTS:
        for multiplier in (0.75, 1.25):
            weights = dict(BASE_WEIGHTS)
            weights[component] *= multiplier
            variants[f"m2_{component}_x{multiplier:.2f}"] = weights
    return variants


def weighted_m2_action_score(
    action: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    weights: dict[str, float],
) -> float:
    coverage = state.get("coverage", {})
    stage_coverage = coverage.get("stage_coverage", {})
    evidence_coverage = coverage.get("evidence_type_coverage", {})
    expected_stages = action.get("expected_stages", [])
    expected_evidence_types = action.get("expected_evidence_types", [])
    stage_gap = (
        sum(1.0 - float(stage_coverage.get(stage, 0.0)) for stage in expected_stages)
        / len(expected_stages)
        if expected_stages
        else 0.0
    )
    evidence_gap = (
        sum(
            1.0 - float(evidence_coverage.get(evidence_type, 0.0))
            for evidence_type in expected_evidence_types
        )
        / len(expected_evidence_types)
        if expected_evidence_types
        else 0.0
    )
    action_map = MVP.action_by_id(actions)
    signature = MVP.action_signature(action)
    overlap = max(
        (
            MVP.jaccard(signature, MVP.action_signature(action_map[action_id]))
            for action_id in state.get("actions_taken", [])
            if action_id in action_map
        ),
        default=0.0,
    )
    same_type_feedback = [
        feedback
        for feedback in state.get("action_feedback", [])
        if feedback.get("action_type") == action.get("action_type")
    ]
    no_yield = (
        sum(int(feedback.get("recovered_count", 0)) == 0 for feedback in same_type_feedback)
        / len(same_type_feedback)
        if same_type_feedback
        else 0.0
    )
    cost_ratio = float(action["cost"]) / max(
        0.1, float(state["budget"]["budget_remaining"])
    )
    return (
        weights["granularity"]
        * MVP.expected_effect(action, "expected_granularity_gain")
        + weights["uncertainty"]
        * MVP.expected_effect(action, "expected_uncertainty_reduction")
        + weights["risk"]
        * MVP.expected_effect(action, "expected_over_attribution_risk_reduction")
        + weights["stage_gap"] * stage_gap
        + weights["evidence_gap"] * evidence_gap
        - weights["overlap"] * overlap
        - weights["no_yield"] * no_yield
        - weights["cost"] * cost_ratio
    )


def select_weighted_m2(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    weights: dict[str, float],
) -> dict[str, Any] | None:
    candidates = MVP.available_actions(
        actions,
        state.get("actions_taken", []),
        float(state["budget"]["budget_remaining"]),
    )
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda action: (
            -weighted_m2_action_score(action, state, actions, weights),
            -int(MVP.is_stop_action(action)),
            float(action["cost"]),
            -len(action.get("expected_stages", [])),
            action["action_id"],
        ),
    )


def resolve_prefixed_cases(root: Path, prefixes: tuple[str, ...]) -> list[Path]:
    resolved = []
    for prefix in prefixes:
        matches = sorted(
            path
            for path in root.glob(f"{prefix}*")
            if path.is_dir()
            and all((path / filename).is_file() for filename in MVP.CASE_FILENAMES)
        )
        if len(matches) != 1:
            raise FileNotFoundError(
                f"Expected one complete {prefix} case under {root}; found {matches}"
            )
        resolved.append(matches[0])
    return resolved


def holdout_case_dirs() -> list[Path]:
    return resolve_prefixed_cases(
        ROOT / "09-experiments" / "real_cases", ("C07", "C08", "C09", "C10")
    )


def development_case_dirs() -> list[Path]:
    examples = resolve_prefixed_cases(
        ROOT / "09-experiments" / "examples", ("C01", "C02", "C03")
    )
    real = resolve_prefixed_cases(
        ROOT / "09-experiments" / "real_cases", ("C04", "C05", "C06")
    )
    return examples + real


def run_weight_analysis(case_dirs: list[Path]) -> list[dict[str, Any]]:
    variants = weight_variants()
    rows: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        config = MVP.load_json(case_dir / "case_config.json")
        claims = MVP.load_json(case_dir / "evidence_claims.json")
        actions = MVP.load_json(case_dir / "acquisition_actions.json")
        for strategy, intensity, seed in MVP.experiment_conditions(config):
            for planner, weights in variants.items():
                selector = lambda cfg, st, acts, w=weights: select_weighted_m2(
                    cfg, st, acts, w
                )
                row, _ = MVP.run_episode(
                    config,
                    claims,
                    actions,
                    strategy,
                    intensity,
                    seed,
                    planner,
                    action_selector=selector,
                )
                rows.append(row)
            oracle, _ = MVP.run_episode(
                config,
                claims,
                actions,
                strategy,
                intensity,
                seed,
                "oracle_optimal",
            )
            rows.append(oracle)
    return MVP.add_oracle_relative_metrics(rows)


def compare_weight_variants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ("case_id", "mask_strategy", "mask_intensity", "seed")
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = tuple(row[field] for field in keys)
        grouped.setdefault(key, {})[row["planner"]] = row
    output = {}
    for planner in weight_variants():
        if planner == "m2_base":
            continue
        first_matches = wins = ties = losses = regressions = repairs = 0
        differences = []
        for planners in grouped.values():
            base = planners["m2_base"]
            candidate = planners[planner]
            first_matches += int(MVP.first_action_id(base) == MVP.first_action_id(candidate))
            base_success = int(base["reached_target"])
            candidate_success = int(candidate["reached_target"])
            repairs += int(candidate_success and not base_success)
            regressions += int(base_success and not candidate_success)
            if base_success and candidate_success:
                difference = float(candidate["cost_to_target"]) - float(base["cost_to_target"])
                differences.append(difference)
                wins += int(difference < 0)
                ties += int(difference == 0)
                losses += int(difference > 0)
        output[planner] = {
            "first_action_agreement_rate": round(first_matches / len(grouped), 4),
            "success_repairs_vs_base": repairs,
            "success_regressions_vs_base": regressions,
            "cost_wins_vs_base": wins,
            "cost_ties_vs_base": ties,
            "cost_losses_vs_base": losses,
            "mean_cost_difference_vs_base": (
                round(sum(differences) / len(differences), 4) if differences else None
            ),
        }
    return output


def run_proxy_variants(
    case_dirs: list[Path], variants: list[tuple[str, str, dict[str, float]]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant_name, semantics, thresholds in variants:
        variant_rows: list[dict[str, Any]] = []
        for case_dir in case_dirs:
            config = MVP.load_json(case_dir / "case_config.json")
            config["node_coverage_semantics"] = semantics
            config["granularity_thresholds"] = dict(thresholds)
            claims = MVP.load_json(case_dir / "evidence_claims.json")
            actions = MVP.load_json(case_dir / "acquisition_actions.json")
            for strategy, intensity, seed in MVP.experiment_conditions(config):
                for planner in ("project05_m2", "oracle_optimal"):
                    row, _ = MVP.run_episode(
                        config,
                        claims,
                        actions,
                        strategy,
                        intensity,
                        seed,
                        planner,
                    )
                    variant_rows.append(row)
        for row in MVP.add_oracle_relative_metrics(variant_rows):
            updated = dict(row)
            updated["sensitivity_variant"] = variant_name
            updated["node_coverage_semantics"] = semantics
            rows.append(updated)
    return rows


def summarize_proxy_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in rows:
        grouped.setdefault(row["sensitivity_variant"], {}).setdefault(
            row["planner"], []
        ).append(row)
    return {
        variant: {
            planner: MVP.summarize_group(planner_rows)
            for planner, planner_rows in planners.items()
        }
        for variant, planners in grouped.items()
    }


def all_holdout_proxy_variants() -> list[tuple[str, str, dict[str, float]]]:
    return [
        (f"{semantics}_{name}", semantics, thresholds)
        for semantics in ("OR", "AND")
        for name, thresholds in THRESHOLD_VARIANTS.items()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frozen Project05 sensitivity analyses.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "09-experiments" / "results" / "m2_sensitivity_v0.1",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    weight_rows = run_weight_analysis(holdout_case_dirs())
    MVP.write_csv(args.output_dir / "m2_weight_results.csv", weight_rows)
    MVP.write_json(
        args.output_dir / "m2_weight_summary.json", MVP.summarize_stratified(weight_rows)
    )
    MVP.write_json(
        args.output_dir / "m2_weight_comparison.json",
        compare_weight_variants(weight_rows),
    )

    holdout_proxy_rows = run_proxy_variants(
        holdout_case_dirs(), all_holdout_proxy_variants()
    )
    MVP.write_csv(
        args.output_dir / "granularity_holdout_results.csv", holdout_proxy_rows
    )
    MVP.write_json(
        args.output_dir / "granularity_holdout_summary.json",
        summarize_proxy_rows(holdout_proxy_rows),
    )

    dev_variants = [
        ("OR_default", "OR", THRESHOLD_VARIANTS["default"]),
        ("AND_default", "AND", THRESHOLD_VARIANTS["default"]),
    ]
    dev_rows = run_proxy_variants(development_case_dirs(), dev_variants)
    MVP.write_csv(args.output_dir / "coverage_semantics_dev_results.csv", dev_rows)
    MVP.write_json(
        args.output_dir / "coverage_semantics_dev_summary.json",
        summarize_proxy_rows(dev_rows),
    )
    manifest = {
        "weight_variant_count_including_base": len(weight_variants()),
        "holdout_independent_case_count": 4,
        "development_independent_case_count": 6,
        "holdout_or_and_identifiable": False,
        "reason": "Every C07-C10 CTI node has exactly one required claim.",
        "threshold_variants": THRESHOLD_VARIANTS,
    }
    MVP.write_json(args.output_dir / "sensitivity_manifest.json", manifest)
    print(f"Wrote frozen sensitivity analysis to {args.output_dir}")


if __name__ == "__main__":
    main()
