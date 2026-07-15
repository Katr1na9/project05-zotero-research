#!/usr/bin/env python3
"""Run versioned Project05 parameter-governance experiment arms."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import itertools
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "09-experiments"
MVP_PATH = Path(__file__).with_name("run_mvp.py")
DEFAULT_GOVERNANCE = (
    EXPERIMENT_ROOT / "governance" / "parameter-governance-v0.2.json"
)
DEFAULT_CORROBORATION = (
    EXPERIMENT_ROOT
    / "governance"
    / "profiles"
    / "corroboration-source-groups-v0.1.json"
)
DEFAULT_ACTION_PRIORS = (
    EXPERIMENT_ROOT
    / "governance"
    / "profiles"
    / "action-priors-development-derived-v0.1.json"
)
DEFAULT_OUTPUT = EXPERIMENT_ROOT / "results" / "parameter_governance_v0.2"
AFA_ENDPOINT_CONTRACT = (
    EXPERIMENT_ROOT
    / "governance"
    / "contracts"
    / "afa-endpoint-contract-v0.1.json"
)
ROUND2_MANIFEST = (
    EXPERIMENT_ROOT
    / "annotation"
    / "c07_c11_round2_v0.1"
    / "packet_manifest.json"
)
REFERENCE_VARIANTS = {
    "cost_regime": "legacy",
    "threshold_grid": "n0.75_e0.60_s2",
    "corroboration_scan": "claim_k3",
    "m2_alpha_scan": "m2_alpha_0p75",
    "action_prior_sensitivity": "legacy_priors",
}
PAIR_KEYS = (
    "case_id",
    "mask_strategy",
    "mask_intensity",
    "seed",
    "planner",
)


def load_script(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MVP = load_script(MVP_PATH, "project05_parameter_governance_mvp")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty result set: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def resolve_cases(prefixes: tuple[str, ...]) -> list[Path]:
    roots = (EXPERIMENT_ROOT / "examples", EXPERIMENT_ROOT / "real_cases")
    resolved: list[Path] = []
    for prefix in prefixes:
        matches = [
            path
            for root in roots
            for path in root.glob(f"{prefix}*")
            if path.is_dir()
            and all((path / filename).is_file() for filename in MVP.CASE_FILENAMES)
        ]
        if len(matches) != 1:
            raise FileNotFoundError(
                f"Expected one complete {prefix} case; found {matches}"
            )
        resolved.append(matches[0])
    return resolved


def corroboration_maps(profile: dict[str, Any]) -> dict[str, dict[str, str]]:
    if profile.get("status") != "frozen_mapping":
        raise ValueError("Corroboration source-group profile is not frozen")
    output: dict[str, dict[str, str]] = {}
    for row in profile["assignments"]:
        case_map = output.setdefault(row["case_id"], {})
        claim_id = row["claim_id"]
        if claim_id in case_map:
            raise ValueError(f"Duplicate source-group assignment: {claim_id}")
        case_map[claim_id] = row["source_group"]
    return output


def add_oracle_reachability(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = ("case_id", "mask_strategy", "mask_intensity", "seed")
    oracle = {
        tuple(row[key] for key in keys): int(row["reached_target"])
        for row in rows
        if row["planner"] == "oracle_optimal"
    }
    output: list[dict[str, Any]] = []
    for row in rows:
        updated = dict(row)
        if row["planner"] == "full_evidence":
            updated["oracle_reachable"] = ""
        else:
            value = oracle.get(tuple(row[key] for key in keys))
            updated["oracle_reachable"] = "" if value is None else value
        output.append(updated)
    return output


def finalize_variant(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return add_oracle_reachability(MVP.add_oracle_relative_metrics(rows))


def run_standard_variant(
    case_dirs: list[Path],
    planners: tuple[str, ...],
    family: str,
    variant_id: str,
    configure: Callable[[dict[str, Any]], dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        config = configure(deepcopy(MVP.load_json(case_dir / "case_config.json")))
        claims = MVP.load_json(case_dir / "evidence_claims.json")
        actions = MVP.load_json(case_dir / "acquisition_actions.json")
        for strategy, intensity, seed in MVP.experiment_conditions(config):
            for planner in planners:
                row, _ = MVP.run_episode(
                    config,
                    claims,
                    actions,
                    strategy,
                    intensity,
                    seed,
                    planner,
                )
                row.update(
                    {
                        "governance_family": family,
                        "governance_variant": variant_id,
                        **metadata,
                    }
                )
                rows.append(row)
    return finalize_variant(rows)


def embedded_legacy_cost_identity(case_dirs: list[Path]) -> dict[str, str]:
    basis: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        config = MVP.load_json(case_dir / "case_config.json")
        for action in MVP.load_json(case_dir / "acquisition_actions.json"):
            if MVP.is_stop_action(action):
                continue
            basis.append(
                {
                    "case_id": config["case_id"],
                    "action_id": action["action_id"],
                    "cost": float(action["cost"]),
                }
            )
    basis.sort(key=lambda row: (row["case_id"], row["action_id"]))
    return {
        "cost_profile_id": "project05-embedded-legacy-costs-v1",
        "cost_profile_version": "1.0.0",
        "cost_profile_sha256": canonical_sha256(basis),
    }


def run_cost_scan(
    case_dirs: list[Path],
    planners: tuple[str, ...],
) -> list[dict[str, Any]]:
    legacy_identity = embedded_legacy_cost_identity(case_dirs)
    rows: list[dict[str, Any]] = []
    for regime in ("legacy", "uniform"):
        variant_rows: list[dict[str, Any]] = []
        for case_dir in case_dirs:
            config = MVP.load_json(case_dir / "case_config.json")
            claims = MVP.load_json(case_dir / "evidence_claims.json")
            source_actions = MVP.load_json(case_dir / "acquisition_actions.json")
            actions, metadata = MVP.apply_cost_regime(
                source_actions,
                config["case_id"],
                regime,
            )
            identity = legacy_identity if metadata is None else metadata
            for strategy, intensity, seed in MVP.experiment_conditions(config):
                for planner in planners:
                    row, _ = MVP.run_episode(
                        config,
                        claims,
                        actions,
                        strategy,
                        intensity,
                        seed,
                        planner,
                    )
                    row.update(
                        {
                            "governance_family": "cost_regime",
                            "governance_variant": regime,
                            "cost_regime": regime,
                            **identity,
                        }
                    )
                    variant_rows.append(row)
        rows.extend(finalize_variant(variant_rows))
    return rows


def threshold_variants(governance: dict[str, Any]) -> list[dict[str, Any]]:
    grid = governance["threshold_grid"]
    held = grid["held_constant"]
    variants = []
    for node, edge, stages in itertools.product(
        grid["g3_node_coverage"],
        grid["g3_edge_coverage"],
        grid["g2_min_stages"],
    ):
        variants.append(
            {
                "g3_node_coverage": float(node),
                "g3_edge_coverage": float(edge),
                "g2_node_coverage": float(held["g2_node_coverage"]),
                "g2_min_stages": int(stages),
                "g1_node_coverage": float(held["g1_node_coverage"]),
            }
        )
    return variants


def run_threshold_scan(
    case_dirs: list[Path],
    planners: tuple[str, ...],
    governance: dict[str, Any],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for thresholds in threshold_variants(governance):
        variant_id = (
            f"n{thresholds['g3_node_coverage']:.2f}_"
            f"e{thresholds['g3_edge_coverage']:.2f}_"
            f"s{thresholds['g2_min_stages']}"
        )

        def configure(config: dict[str, Any], values=thresholds) -> dict[str, Any]:
            config["granularity_thresholds"] = dict(values)
            return config

        output.extend(
            run_standard_variant(
                case_dirs,
                planners,
                "threshold_grid",
                variant_id,
                configure,
                {
                    "g3_node_coverage": thresholds["g3_node_coverage"],
                    "g3_edge_coverage": thresholds["g3_edge_coverage"],
                    "g2_min_stages": thresholds["g2_min_stages"],
                },
            )
        )
    return output


def run_corroboration_scan(
    case_dirs: list[Path],
    planners: tuple[str, ...],
    governance: dict[str, Any],
    source_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    maps = corroboration_maps(source_profile)
    for unit in governance["corroboration_scan"]["units"]:
        for k in governance["corroboration_scan"]["k_values"]:
            variant_id = f"{unit}_k{k}"

            def configure(
                config: dict[str, Any],
                selected_unit=unit,
                selected_k=int(k),
            ) -> dict[str, Any]:
                config["node_coverage_semantics"] = "K_OF_N"
                config["node_coverage_k"] = selected_k
                config["corroboration_unit"] = selected_unit
                if selected_unit == "source_group":
                    config["claim_source_groups"] = maps[config["case_id"]]
                return config

            output.extend(
                run_standard_variant(
                    case_dirs,
                    planners,
                    "corroboration_scan",
                    variant_id,
                    configure,
                    {
                        "corroboration_unit": unit,
                        "corroboration_k": int(k),
                    },
                )
            )
    return output


def select_m2_alpha(
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    alpha: float,
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
            -MVP.m2_action_score(action, state, actions, cost_coefficient=alpha),
            -int(MVP.is_stop_action(action)),
            action["cost"],
            -len(action.get("expected_stages", [])),
            action["action_id"],
        ),
    )


def alpha_name(alpha: float) -> str:
    return f"m2_alpha_{alpha:.2f}".replace(".", "p")


def run_alpha_scan(
    case_dirs: list[Path],
    governance: dict[str, Any],
) -> list[dict[str, Any]]:
    alphas = [float(value) for value in governance["m2_alpha_scan"]["cost_coefficients"]]
    rows: list[dict[str, Any]] = []
    for alpha in alphas:
        variant_id = alpha_name(alpha)
        variant_rows: list[dict[str, Any]] = []
        for case_dir in case_dirs:
            config = MVP.load_json(case_dir / "case_config.json")
            claims = MVP.load_json(case_dir / "evidence_claims.json")
            actions = MVP.load_json(case_dir / "acquisition_actions.json")
            for strategy, intensity, seed in MVP.experiment_conditions(config):
                selector = lambda cfg, state, public_actions, a=alpha: select_m2_alpha(
                    state, public_actions, a
                )
                row, _ = MVP.run_episode(
                    config,
                    claims,
                    actions,
                    strategy,
                    intensity,
                    seed,
                    "project05_m2",
                    action_selector=selector,
                )
                row.update(
                    {
                        "governance_family": "m2_alpha_scan",
                        "governance_variant": variant_id,
                        "m2_cost_alpha": alpha,
                    }
                )
                variant_rows.append(row)
                oracle, _ = MVP.run_episode(
                    config,
                    claims,
                    actions,
                    strategy,
                    intensity,
                    seed,
                    "oracle_optimal",
                )
                oracle.update(
                    {
                        "governance_family": "m2_alpha_scan",
                        "governance_variant": variant_id,
                        "m2_cost_alpha": alpha,
                    }
                )
                variant_rows.append(oracle)
        rows.extend(finalize_variant(variant_rows))
    return rows


def action_prior_maps(
    profile: dict[str, Any],
) -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, dict[str, float]]]:
    if profile.get("status") != "frozen_development_derived":
        raise ValueError("Action-prior profile is not frozen_development_derived")
    actions: dict[str, dict[str, dict[str, Any]]] = {}
    for entry in profile["actions"]:
        case_map = actions.setdefault(entry["case_id"], {})
        if entry["action_id"] in case_map:
            raise ValueError(f"Duplicate action-prior entry {entry['action_id']}")
        case_map[entry["action_id"]] = entry
    channels = {
        row["case_id"]: {
            str(channel): float(value)
            for channel, value in row["channel_reliability"].items()
        }
        for row in profile["case_channel_priors"]
    }
    return actions, channels


def apply_action_priors(
    config: dict[str, Any],
    actions: list[dict[str, Any]],
    entries: dict[str, dict[str, dict[str, Any]]],
    channels: dict[str, dict[str, float]],
    expert_multiplier: float,
    channel_multiplier: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    case_id = config["case_id"]
    case_entries = entries.get(case_id, {})
    expected_ids = {action["action_id"] for action in actions}
    if set(case_entries) != expected_ids:
        raise ValueError(
            f"Action-prior coverage mismatch for {case_id}: "
            f"missing={sorted(expected_ids-set(case_entries))}, "
            f"extra={sorted(set(case_entries)-expected_ids)}"
        )
    updated_actions = deepcopy(actions)
    expert_fields = (
        "expected_uncertainty_reduction",
        "expected_over_attribution_risk_reduction",
        "expected_conflict_resolution",
    )
    for action in updated_actions:
        effects = dict(case_entries[action["action_id"]]["expected_effects"])
        for field in expert_fields:
            effects[field] = min(1.0, max(0.0, float(effects[field]) * expert_multiplier))
        action["expected_effects"] = effects
    updated_config = deepcopy(config)
    updated_config["planner_channel_reliability"] = {
        channel: min(1.0, max(0.0, value * channel_multiplier))
        for channel, value in channels.get(case_id, {}).items()
    }
    return updated_config, updated_actions


def prior_variants(governance: dict[str, Any]) -> list[tuple[str, float, float, bool]]:
    variants = [("legacy_priors", 1.0, 1.0, True)]
    variants.append(("dev_measured_base", 1.0, 1.0, False))
    for multiplier in governance["expert_prior_sensitivity"][
        "expected_effect_multipliers"
    ]:
        value = float(multiplier)
        if value != 1.0:
            variants.append((f"dev_measured_expert_x{value:.2f}", value, 1.0, False))
    for multiplier in governance["expert_prior_sensitivity"][
        "channel_reliability_multipliers"
    ]:
        value = float(multiplier)
        if value != 1.0:
            variants.append((f"dev_measured_channel_x{value:.2f}", 1.0, value, False))
    return variants


def run_action_prior_scan(
    case_dirs: list[Path],
    planners: tuple[str, ...],
    governance: dict[str, Any],
    profile: dict[str, Any],
    profile_sha256: str,
) -> list[dict[str, Any]]:
    entries, channels = action_prior_maps(profile)
    rows: list[dict[str, Any]] = []
    for variant_id, expert_multiplier, channel_multiplier, legacy in prior_variants(
        governance
    ):
        variant_rows: list[dict[str, Any]] = []
        for case_dir in case_dirs:
            config = MVP.load_json(case_dir / "case_config.json")
            claims = MVP.load_json(case_dir / "evidence_claims.json")
            actions = MVP.load_json(case_dir / "acquisition_actions.json")
            if not legacy:
                config, actions = apply_action_priors(
                    config,
                    actions,
                    entries,
                    channels,
                    expert_multiplier,
                    channel_multiplier,
                )
            execution_channel_profile = config.get("channel_reliability", {}) or {}
            planner_channel_prior = config.get(
                "planner_channel_reliability", execution_channel_profile
            ) or {}
            for strategy, intensity, seed in MVP.experiment_conditions(config):
                for planner in planners:
                    row, _ = MVP.run_episode(
                        config,
                        claims,
                        actions,
                        strategy,
                        intensity,
                        seed,
                        planner,
                    )
                    row.update(
                        {
                            "governance_family": "action_prior_sensitivity",
                            "governance_variant": variant_id,
                            "action_prior_regime": "legacy" if legacy else "development_derived",
                            "expert_effect_multiplier": expert_multiplier,
                            "channel_prior_multiplier": channel_multiplier,
                            "action_prior_profile_sha256": "" if legacy else profile_sha256,
                            "execution_channel_profile_sha256": canonical_sha256(
                                execution_channel_profile
                            ),
                            "planner_channel_prior_sha256": canonical_sha256(
                                planner_channel_prior
                            ),
                            "channel_prior_scope": "planner_belief_only",
                            "channel_prior_consumed_by_planner": 0,
                            "execution_channel_profile_held_constant": 1,
                        }
                    )
                    variant_rows.append(row)
        rows.extend(finalize_variant(variant_rows))
    return rows


def evidence_limited_endpoints(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    reached = [row for row in rows if int(row["reached_target"]) == 1]
    oracle_reachable = [row for row in rows if row.get("oracle_reachable") == 1]
    oracle_unreachable = [row for row in rows if row.get("oracle_reachable") == 0]
    return {
        "repeated_condition_count": total,
        "target_decision_coverage": round(len(reached) / total, 4),
        "emitted_over_attribution_rate": round(
            sum(int(row.get("ceiling_violation", 0)) for row in rows) / total,
            4,
        ),
        "selective_evidence_safety_on_target_decisions": (
            round(
                1
                - sum(int(row.get("ceiling_violation", 0)) for row in reached)
                / len(reached),
                4,
            )
            if reached
            else None
        ),
        "correct_abstention_rate_when_oracle_unreachable": (
            round(
                sum(int(row.get("justified_degrade_stop", 0)) for row in oracle_unreachable)
                / len(oracle_unreachable),
                4,
            )
            if oracle_unreachable
            else None
        ),
        "premature_abstention_rate_when_oracle_reachable": (
            round(
                sum(int(row.get("premature_stop", 0)) for row in oracle_reachable)
                / len(oracle_reachable),
                4,
            )
            if oracle_reachable
            else None
        ),
        "external_actor_accuracy": None,
        "external_actor_accuracy_status": "not_identifiable_without_actor_or_analyst_utility_ground_truth",
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in rows:
        grouped.setdefault(str(row["governance_variant"]), {}).setdefault(
            str(row["planner"]), []
        ).append(row)
    return {
        variant: {
            planner: {
                "standard": MVP.summarize_group(planner_rows),
                "evidence_limited": evidence_limited_endpoints(planner_rows),
            }
            for planner, planner_rows in planners.items()
        }
        for variant, planners in grouped.items()
    }


def mean_or_none(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def paired_metrics(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
) -> dict[str, Any]:
    if not pairs:
        raise ValueError("Cannot summarize an empty paired comparison")
    baseline_success = [int(left["reached_target"]) for left, _ in pairs]
    candidate_success = [int(right["reached_target"]) for _, right in pairs]
    success_delta = [
        candidate - baseline
        for baseline, candidate in zip(baseline_success, candidate_success)
    ]
    joint_cost_delta = [
        float(right["cost_to_target"]) - float(left["cost_to_target"])
        for left, right in pairs
        if left.get("cost_to_target", "") != ""
        and right.get("cost_to_target", "") != ""
    ]
    budget_delta = [
        float(right["budget_used"]) - float(left["budget_used"])
        for left, right in pairs
    ]
    coverage_delta = [
        float(right["final_node_coverage"])
        - float(left["final_node_coverage"])
        for left, right in pairs
    ]
    sequence_matches = [
        str(left.get("actions_taken", ""))
        == str(right.get("actions_taken", ""))
        for left, right in pairs
    ]
    first_action_matches = [
        MVP.first_action_id(left) == MVP.first_action_id(right)
        for left, right in pairs
    ]
    ceiling_flips = [
        int(left.get("ceiling_violation", 0))
        != int(right.get("ceiling_violation", 0))
        for left, right in pairs
    ]
    return {
        "paired_repeated_condition_count": len(pairs),
        "baseline_success_rate": mean_or_none(
            [float(value) for value in baseline_success]
        ),
        "candidate_success_rate": mean_or_none(
            [float(value) for value in candidate_success]
        ),
        "success_rate_delta": mean_or_none(
            [float(value) for value in success_delta]
        ),
        "success_outcome_agreement_rate": mean_or_none(
            [float(value == 0) for value in success_delta]
        ),
        "success_flip_rate": mean_or_none(
            [float(value != 0) for value in success_delta]
        ),
        "success_gain_rate": mean_or_none(
            [float(value > 0) for value in success_delta]
        ),
        "success_loss_rate": mean_or_none(
            [float(value < 0) for value in success_delta]
        ),
        "joint_success_pair_count": len(joint_cost_delta),
        "mean_cost_to_target_delta_on_joint_success": mean_or_none(
            joint_cost_delta
        ),
        "mean_budget_used_delta": mean_or_none(budget_delta),
        "mean_final_node_coverage_delta": mean_or_none(coverage_delta),
        "action_sequence_agreement_rate": mean_or_none(
            [float(value) for value in sequence_matches]
        ),
        "first_action_agreement_rate": mean_or_none(
            [float(value) for value in first_action_matches]
        ),
        "ceiling_violation_flip_rate": mean_or_none(
            [float(value) for value in ceiling_flips]
        ),
        "candidate_ceiling_violation_rate": mean_or_none(
            [float(int(right.get("ceiling_violation", 0))) for _, right in pairs]
        ),
    }


def paired_stability(
    rows: list[dict[str, Any]],
    baseline_variant: str,
) -> dict[str, Any]:
    variants = sorted({str(row["governance_variant"]) for row in rows})
    planners = sorted({str(row["planner"]) for row in rows})
    if baseline_variant not in variants:
        raise ValueError(
            f"Paired baseline {baseline_variant!r} is absent from {variants}"
        )

    output: dict[str, dict[str, Any]] = {}
    envelopes: dict[str, Any] = {}
    for planner in planners:
        planner_rows = [row for row in rows if row["planner"] == planner]
        baseline_rows = [
            row
            for row in planner_rows
            if row["governance_variant"] == baseline_variant
        ]
        baseline_index: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in baseline_rows:
            key = tuple(row[field] for field in PAIR_KEYS)
            if key in baseline_index:
                raise ValueError(f"Duplicate baseline paired key: {key}")
            baseline_index[key] = row
        if not baseline_index:
            raise ValueError(
                f"No baseline rows for planner {planner}/{baseline_variant}"
            )

        planner_variants: dict[str, Any] = {}
        for variant in variants:
            candidate_index: dict[tuple[Any, ...], dict[str, Any]] = {}
            for row in planner_rows:
                if row["governance_variant"] != variant:
                    continue
                key = tuple(row[field] for field in PAIR_KEYS)
                if key in candidate_index:
                    raise ValueError(
                        f"Duplicate candidate paired key: {variant}/{key}"
                    )
                candidate_index[key] = row
            missing = sorted(set(baseline_index) - set(candidate_index))
            extra = sorted(set(candidate_index) - set(baseline_index))
            if missing or extra:
                raise ValueError(
                    f"Paired coverage mismatch for {planner}/{variant}: "
                    f"missing={missing[:3]}, extra={extra[:3]}"
                )
            pairs = [
                (baseline_index[key], candidate_index[key])
                for key in sorted(baseline_index, key=lambda value: tuple(map(str, value)))
            ]
            by_case: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
            for pair in pairs:
                by_case.setdefault(str(pair[0]["case_id"]), []).append(pair)
            case_metrics = {
                case_id: paired_metrics(case_pairs)
                for case_id, case_pairs in sorted(by_case.items())
            }
            case_success_deltas = [
                float(metrics["success_rate_delta"])
                for metrics in case_metrics.values()
            ]
            case_cost_deltas = [
                float(value)
                for metrics in case_metrics.values()
                if (value := metrics["mean_cost_to_target_delta_on_joint_success"])
                is not None
            ]
            case_action_agreement = [
                float(metrics["action_sequence_agreement_rate"])
                for metrics in case_metrics.values()
            ]
            planner_variants[variant] = {
                "overall_repeated_measure_summary": paired_metrics(pairs),
                "case_level": case_metrics,
                "independent_case_summary": {
                    "independent_case_count": len(case_metrics),
                    "mean_case_success_rate_delta": mean_or_none(
                        case_success_deltas
                    ),
                    "min_case_success_rate_delta": round(
                        min(case_success_deltas), 4
                    ),
                    "max_case_success_rate_delta": round(
                        max(case_success_deltas), 4
                    ),
                    "cases_with_success_gain": sum(
                        value > 0 for value in case_success_deltas
                    ),
                    "cases_with_no_success_change": sum(
                        value == 0 for value in case_success_deltas
                    ),
                    "cases_with_success_loss": sum(
                        value < 0 for value in case_success_deltas
                    ),
                    "mean_case_cost_delta_on_joint_success": mean_or_none(
                        case_cost_deltas
                    ),
                    "mean_case_action_sequence_agreement": mean_or_none(
                        case_action_agreement
                    ),
                },
            }
        output[planner] = planner_variants
        repeated = [
            value["overall_repeated_measure_summary"]
            for value in planner_variants.values()
        ]
        envelopes[planner] = {
            "variant_count": len(planner_variants),
            "candidate_success_rate_min": min(
                float(value["candidate_success_rate"]) for value in repeated
            ),
            "candidate_success_rate_max": max(
                float(value["candidate_success_rate"]) for value in repeated
            ),
            "maximum_success_flip_rate_vs_baseline": max(
                float(value["success_flip_rate"]) for value in repeated
            ),
            "minimum_action_sequence_agreement_vs_baseline": min(
                float(value["action_sequence_agreement_rate"])
                for value in repeated
            ),
            "maximum_ceiling_violation_rate": max(
                float(value["candidate_ceiling_violation_rate"])
                for value in repeated
            ),
            "all_variants_preserve_success_outcomes": all(
                float(value["success_flip_rate"]) == 0.0 for value in repeated
            ),
        }

    return {
        "baseline_variant": baseline_variant,
        "variant_count": len(variants),
        "analysis_unit": "case_or_attack_chain",
        "pairing_fields": list(PAIR_KEYS),
        "repeated_measure_note": (
            "Mask strategy, intensity, and seed are paired within case and are "
            "not counted as independent attacks; case-level summaries are the "
            "independent-unit view."
        ),
        "inferential_statistics": (
            "not_reported_because_case_count_is_small_and_conditions_are_repeated"
        ),
        "by_planner": output,
        "robustness_envelope_by_planner": envelopes,
    }


def compact_stability(stability: dict[str, Any]) -> dict[str, Any]:
    return {
        "baseline_variant": stability["baseline_variant"],
        "variant_count": stability["variant_count"],
        "analysis_unit": stability["analysis_unit"],
        "robustness_envelope_by_planner": stability[
            "robustness_envelope_by_planner"
        ],
    }


def input_hashes(case_dirs: list[Path]) -> dict[str, str]:
    paths = [
        case_dir / filename
        for case_dir in case_dirs
        for filename in MVP.CASE_FILENAMES
    ]
    return {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in paths}


def require_empty_output(path: Path) -> None:
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise FileExistsError(
            f"Governance output must be new or empty; refusing to overwrite {path}"
        )
    path.mkdir(parents=True, exist_ok=True)


def methodology_coverage(
    selected_families: tuple[str, ...],
    governance: dict[str, Any],
) -> dict[str, Any]:
    round2_status = (
        load_json(ROUND2_MANIFEST).get("status")
        if ROUND2_MANIFEST.is_file()
        else "not_built"
    )
    endpoint_contract = (
        {
            "path": AFA_ENDPOINT_CONTRACT.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(AFA_ENDPOINT_CONTRACT),
        }
        if AFA_ENDPOINT_CONTRACT.is_file()
        else None
    )
    return {
        "C_cost": {
            "status": "partial_gate_enforced",
            "executed_in_this_run": "cost" in selected_families,
            "runnable_regimes": ["legacy", "uniform"],
            "blocked_regimes": {
                "rubric": "requires_two_real_independent_raters_and_agreement",
                "measured": "requires_action_level_operational_measurements",
            },
            "formal_gate": governance["formal_cost_run_gate"],
        },
        "W1_thresholds": {
            "status": "executed" if "threshold" in selected_families else "not_selected",
            "paired_case_level_stability": "threshold" in selected_families,
        },
        "W7_corroboration": {
            "status": "executed" if "corroboration" in selected_families else "not_selected",
            "paired_case_level_stability": "corroboration" in selected_families,
        },
        "W2_m2_alpha": {
            "status": "executed" if "alpha" in selected_families else "not_selected",
            "paired_case_level_stability": "alpha" in selected_families,
        },
        "W6_action_and_channel_priors": {
            "status": "executed" if "priors" in selected_families else "not_selected",
            "paired_case_level_stability": "priors" in selected_families,
            "remaining_boundary": "uncertainty_risk_conflict_terms_remain_declared_expert_priors",
        },
        "W3_annotation_round2": {
            "status": round2_status,
            "manifest_sha256": (
                sha256_file(ROUND2_MANIFEST) if ROUND2_MANIFEST.is_file() else None
            ),
            "blocking_condition": "two_real_independent_annotations_not_yet_collected",
        },
        "W4_evidence_limited_endpoints": {
            "status": "computed_for_each_executed_variant",
            "external_actor_accuracy": None,
            "blocking_condition": "actor_or_analyst_utility_ground_truth_unavailable",
        },
        "W5_W9_afa_endpoint_and_leakage": {
            "status": "contract_frozen_and_runtime_allowlist_tested",
            "contract": endpoint_contract,
            "official_external_implementation_claimed": False,
        },
        "all_experiments_complete": False,
        "paper_or_patent_gate": "closed_until_human_and_operational_gates_are_satisfied",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--governance", type=Path, default=DEFAULT_GOVERNANCE)
    parser.add_argument(
        "--corroboration-profile", type=Path, default=DEFAULT_CORROBORATION
    )
    parser.add_argument(
        "--action-prior-profile", type=Path, default=DEFAULT_ACTION_PRIORS
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--families",
        nargs="+",
        choices=("cost", "threshold", "corroboration", "alpha", "priors"),
        default=("cost", "threshold", "corroboration", "alpha", "priors"),
    )
    parser.add_argument(
        "--planners",
        nargs="+",
        default=("all",),
        help="Built-in planners for threshold/corroboration; use 'all' or names.",
    )
    parser.add_argument("--case-prefixes", nargs="+")
    args = parser.parse_args()

    governance = load_json(args.governance)
    if governance.get("status") != "locked_for_new_governance_runs":
        raise ValueError("Governance configuration is not locked")
    prefixes = tuple(args.case_prefixes or governance["scope_case_prefixes"])
    case_dirs = resolve_cases(prefixes)
    planners = (
        tuple(MVP.PLANNERS)
        if tuple(args.planners) == ("all",)
        else tuple(args.planners)
    )
    unknown = sorted(set(planners) - set(MVP.PLANNERS))
    if unknown:
        raise ValueError(f"Unknown built-in planners: {unknown}")
    if "oracle_optimal" not in planners:
        planners = (*planners, "oracle_optimal")
    require_empty_output(args.output_dir)

    selected_families = tuple(args.families)
    outputs: dict[str, dict[str, Any]] = {}
    unified_stability: dict[str, Any] = {}
    if "cost" in selected_families:
        rows = run_cost_scan(case_dirs, planners)
        result_path = args.output_dir / "cost_regime_results.csv"
        summary_path = args.output_dir / "cost_regime_summary.json"
        stability_path = args.output_dir / "cost_regime_paired_stability.json"
        write_csv(result_path, rows)
        write_json(summary_path, summarize(rows))
        stability = paired_stability(rows, REFERENCE_VARIANTS["cost_regime"])
        write_json(stability_path, stability)
        unified_stability["C_cost"] = compact_stability(stability)
        outputs["cost"] = {
            "row_count": len(rows),
            "variant_count": 2,
            "executed_regimes": ["legacy", "uniform"],
            "blocked_regimes": ["rubric", "measured"],
            "result_sha256": sha256_file(result_path),
            "summary_sha256": sha256_file(summary_path),
            "paired_stability_sha256": sha256_file(stability_path),
        }
    if "threshold" in selected_families:
        rows = run_threshold_scan(case_dirs, planners, governance)
        result_path = args.output_dir / "threshold_grid_results.csv"
        summary_path = args.output_dir / "threshold_grid_summary.json"
        stability_path = args.output_dir / "threshold_grid_paired_stability.json"
        write_csv(result_path, rows)
        write_json(summary_path, summarize(rows))
        stability = paired_stability(rows, REFERENCE_VARIANTS["threshold_grid"])
        write_json(stability_path, stability)
        unified_stability["W1_thresholds"] = compact_stability(stability)
        outputs["threshold"] = {
            "row_count": len(rows),
            "variant_count": len(threshold_variants(governance)),
            "result_sha256": sha256_file(result_path),
            "summary_sha256": sha256_file(summary_path),
            "paired_stability_sha256": sha256_file(stability_path),
        }
    if "corroboration" in selected_families:
        source_profile = load_json(args.corroboration_profile)
        rows = run_corroboration_scan(
            case_dirs, planners, governance, source_profile
        )
        result_path = args.output_dir / "corroboration_results.csv"
        summary_path = args.output_dir / "corroboration_summary.json"
        stability_path = args.output_dir / "corroboration_paired_stability.json"
        write_csv(result_path, rows)
        write_json(summary_path, summarize(rows))
        stability = paired_stability(
            rows, REFERENCE_VARIANTS["corroboration_scan"]
        )
        write_json(stability_path, stability)
        unified_stability["W7_corroboration"] = compact_stability(stability)
        outputs["corroboration"] = {
            "row_count": len(rows),
            "variant_count": len(governance["corroboration_scan"]["units"])
            * len(governance["corroboration_scan"]["k_values"]),
            "source_profile_sha256": sha256_file(args.corroboration_profile),
            "result_sha256": sha256_file(result_path),
            "summary_sha256": sha256_file(summary_path),
            "paired_stability_sha256": sha256_file(stability_path),
        }
    if "alpha" in selected_families:
        rows = run_alpha_scan(case_dirs, governance)
        result_path = args.output_dir / "m2_alpha_results.csv"
        summary_path = args.output_dir / "m2_alpha_summary.json"
        stability_path = args.output_dir / "m2_alpha_paired_stability.json"
        write_csv(result_path, rows)
        write_json(summary_path, summarize(rows))
        stability = paired_stability(rows, REFERENCE_VARIANTS["m2_alpha_scan"])
        write_json(stability_path, stability)
        unified_stability["W2_m2_alpha"] = compact_stability(stability)
        outputs["alpha"] = {
            "row_count": len(rows),
            "alpha_count": len(governance["m2_alpha_scan"]["cost_coefficients"]),
            "result_sha256": sha256_file(result_path),
            "summary_sha256": sha256_file(summary_path),
            "paired_stability_sha256": sha256_file(stability_path),
        }
    if "priors" in selected_families:
        action_profile = load_json(args.action_prior_profile)
        action_profile_hash = sha256_file(args.action_prior_profile)
        rows = run_action_prior_scan(
            case_dirs,
            planners,
            governance,
            action_profile,
            action_profile_hash,
        )
        result_path = args.output_dir / "action_prior_results.csv"
        summary_path = args.output_dir / "action_prior_summary.json"
        stability_path = args.output_dir / "action_prior_paired_stability.json"
        write_csv(result_path, rows)
        write_json(summary_path, summarize(rows))
        stability = paired_stability(
            rows, REFERENCE_VARIANTS["action_prior_sensitivity"]
        )
        write_json(stability_path, stability)
        unified_stability["W6_action_channel_priors"] = compact_stability(stability)
        outputs["priors"] = {
            "row_count": len(rows),
            "variant_count": len(prior_variants(governance)),
            "action_prior_profile_sha256": action_profile_hash,
            "result_sha256": sha256_file(result_path),
            "summary_sha256": sha256_file(summary_path),
            "paired_stability_sha256": sha256_file(stability_path),
        }

    unified_stability_path = (
        args.output_dir / "governance_stability_summary.json"
    )
    write_json(unified_stability_path, unified_stability)

    manifest = {
        "governance_id": governance["governance_id"],
        "governance_version": governance["version"],
        "governance_sha256": sha256_file(args.governance),
        "run_mvp_sha256": sha256_file(MVP_PATH),
        "runner_sha256": sha256_file(Path(__file__)),
        "case_prefixes": list(prefixes),
        "independent_case_count": len(case_dirs),
        "planners": list(planners),
        "outputs": outputs,
        "unified_stability_summary_sha256": sha256_file(
            unified_stability_path
        ),
        "input_sha256": input_hashes(case_dirs),
        "statistical_unit": governance["statistical_unit"],
        "methodology_parameter_coverage": methodology_coverage(
            selected_families, governance
        ),
        "legacy_outputs_overwritten": False,
        "paper_or_patent_updated": False,
    }
    write_json(args.output_dir / "run_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
