#!/usr/bin/env python3
"""Certify M3* regret against the exact Oracle on frozen reachable states.

This is a method-development audit.  Hidden realised outcomes are used only by
the evaluator and the exact Oracle; the M3* runtime receives the same public
state/action views as the production experiment runner.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import time
from pathlib import Path
from typing import Any, Callable

import xgboost as xgb


def load_script(name: str) -> Any:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


run_m3star = load_script("run_m3star")
run_m3star_experiment = load_script("run_m3star_experiment")
run_xgboost = load_script("run_xgboost")
run_mvp = run_xgboost.run_mvp

CORE_METHOD = run_m3star_experiment.CORE_METHOD
REGRET_TOLERANCE = 1e-9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_booster(path: Path) -> xgb.Booster:
    booster = xgb.Booster()
    booster.load_model(path)
    # Generic runtime parameters are not guaranteed to survive a model-only
    # XGBoost save.  The frozen trainers all used nthread=1; restoring it also
    # avoids large thread-launch overhead for our many tiny state predictions.
    booster.set_param({"nthread": 1})
    return booster


def load_saved_models(result_dir: Path) -> dict[str, Any]:
    """Load every frozen model used by the v0.8 core policy without retraining."""

    model_dir = result_dir / "models"
    metadata = load_json(model_dir / "model_metadata.json")
    models: dict[str, Any] = {
        "transition": {
            **metadata["transition"],
            "booster": load_booster(model_dir / "transition.json"),
        },
        "action_value": {
            **metadata["action_value"],
            "booster": load_booster(model_dir / "action_value.json"),
            "reachability_booster": load_booster(
                model_dir / "action_reachability.json"
            ),
            "cost_booster": load_booster(model_dir / "action_cost.json"),
        },
        "action_rank": {
            **metadata["action_rank"],
            "booster": load_booster(model_dir / "action_rank.json"),
        },
        "xgboost": {
            **metadata["xgboost"],
            "booster": load_booster(model_dir / "xgboost.json"),
        },
        # The transparent logistic model is fully represented by these frozen
        # means/scales/weights/bias fields; it has no external binary artefact.
        "logistic": metadata["logistic"],
    }
    if not run_m3star.has_action_reachability_head(models["action_value"]):
        raise ValueError(f"Missing reachability head in {model_dir}")
    if "cost_booster" not in models["action_value"]:
        raise ValueError(f"Missing cost head in {model_dir}")
    return models


def load_frozen_cases(
    cases_root: Path,
    case_ids: list[str],
    cost_profile: dict[str, Any],
) -> list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]]:
    by_id: dict[str, Path] = {}
    for case_dir in run_mvp.discover_case_dirs(cases_root):
        config = load_json(case_dir / "case_config.json")
        by_id[str(config["case_id"])] = case_dir
    missing = sorted(set(case_ids) - set(by_id))
    if missing:
        raise ValueError(f"Frozen evaluation cases are missing: {missing}")
    return run_xgboost.load_cases(
        [by_id[case_id] for case_id in case_ids],
        "measured",
        cost_profile,
    )


def build_runtime(
    models: dict[str, Any],
    configuration: dict[str, Any],
    *,
    learned_head_majority_shield: bool = False,
) -> dict[str, Any]:
    action_model = models["action_value"]
    return {
        "transition_predictor": run_m3star.model_transition_predictor(
            models["transition"],
            max_outcome_nodes=int(configuration["max_outcome_nodes"]),
            max_explicit_outcomes=configuration["max_explicit_outcomes"],
        ),
        "action_value_predictor": run_m3star.model_action_value_predictor(
            action_model
        ),
        "action_reachability_predictor": (
            run_m3star.model_action_reachability_predictor(action_model)
        ),
        "action_cost_predictor": run_m3star.model_action_cost_predictor(
            action_model
        ),
        "policy_expert_advisor": (
            run_m3star_experiment.build_policy_expert_advisor(models)
        ),
        "horizon": 3,
        "target_reach_threshold": float(
            configuration["target_reach_threshold"]
        ),
        "myopic_safety_shield": True,
        "stochastic_dominance_shield": True,
        "learned_head_majority_shield": learned_head_majority_shield,
    }


def select_core_action(
    config: dict[str, Any],
    public_state: dict[str, Any],
    public_actions: list[dict[str, Any]],
    runtime: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply the exact v0.8 M3* planner and its frozen expert-consensus layer."""

    plan = run_m3star.plan_m3star_action(
        config,
        public_state,
        public_actions,
        runtime["transition_predictor"],
        horizon=runtime["horizon"],
        target_reach_threshold=runtime["target_reach_threshold"],
        action_value_predictor=runtime["action_value_predictor"],
        action_reachability_predictor=runtime["action_reachability_predictor"],
        action_cost_predictor=runtime["action_cost_predictor"],
        myopic_safety_shield=runtime["myopic_safety_shield"],
        stochastic_dominance_shield=runtime["stochastic_dominance_shield"],
        learned_head_majority_shield=runtime[
            "learned_head_majority_shield"
        ],
    )
    by_id = run_mvp.action_by_id(public_actions)
    source_id = str(plan["action_id"] or run_mvp.STOP_ACTION_ID)
    if source_id not in by_id:
        raise ValueError(f"M3* selected an unavailable action: {source_id}")

    recommendations = runtime["policy_expert_advisor"](
        config,
        public_state,
        public_actions,
    )
    recommended_ids = {str(value) for value in recommendations.values()}
    candidate_reachabilities: dict[str, float] = {}
    if len(recommended_ids) == 1 and run_mvp.STOP_ACTION_ID not in recommended_ids:
        candidate_id = next(iter(recommended_ids))
        candidate = by_id.get(candidate_id)
        if candidate is not None:
            snapshot = run_m3star.public_graph_snapshot(
                config,
                public_state,
                public_actions,
            )
            candidate_reachabilities = runtime["action_reachability_predictor"](
                snapshot,
                [candidate],
            )
    consensus = run_m3star._apply_policy_expert_consensus(
        source_id,
        public_actions,
        recommendations,
        candidate_reachabilities,
        runtime["target_reach_threshold"],
    )
    selected_id = str(consensus["selected_action_id"])
    if selected_id not in by_id:
        raise ValueError(
            f"M3* consensus selected an unavailable action: {selected_id}"
        )
    return by_id[selected_id], {
        "source_action_id": source_id,
        "selected_action_id": selected_id,
        "consensus_applied": int(consensus["expert_consensus_applied"]),
    }


def rollout_core_policy_from_state(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    decision: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    """Execute the complete M3* policy from one enumerated hidden state."""

    episode_actions = run_mvp.ensure_stop_action(config, actions)
    public_actions = run_mvp.planner_action_views(episode_actions)
    full_by_id = run_mvp.action_by_id(episode_actions)
    visible_ids = set(decision["visible_ids"])
    hidden_ids = set(decision["hidden_ids"])
    recovered_ids = set(decision["recovered_ids"])
    actions_taken = list(decision["actions_taken"])
    action_feedback = list(decision["action_feedback"])
    budget_used = float(decision["budget_used"])
    continuation_cost = 0.0
    action_path: list[str] = []
    source_action_path: list[str] = []
    consensus_substitutions = 0
    target_index = run_mvp.granularity_index(
        config,
        config["target_granularity"],
    )

    for continuation_step in range(len(episode_actions) + 1):
        state = run_mvp.build_state(
            config,
            claims,
            episode_actions,
            f"{decision['state_id']}|oracle-regret-audit",
            int(decision["state_depth"]) + continuation_step,
            decision["mask_strategy"],
            decision["mask_intensity"],
            decision["seed"],
            visible_ids,
            hidden_ids,
            recovered_ids,
            actions_taken,
            budget_used,
            action_feedback,
        )
        if run_mvp.granularity_index(
            config,
            state["supportable_granularity"],
        ) >= target_index:
            return {
                "success": True,
                "cost_to_go": continuation_cost,
                "action_path": action_path,
                "source_action_path": source_action_path,
                "consensus_substitution_count": consensus_substitutions,
                "terminal_reason": "target_reached",
            }

        selected_public, selection = select_core_action(
            config,
            run_mvp.planner_state_view(state),
            public_actions,
            runtime,
        )
        selected_id = str(selected_public["action_id"])
        selected = full_by_id[selected_id]
        action_path.append(selected_id)
        source_action_path.append(str(selection["source_action_id"]))
        consensus_substitutions += int(selection["consensus_applied"])
        action_cost = float(selected["cost"])
        if action_cost > float(state["budget"]["budget_remaining"]) + 1e-9:
            raise ValueError(f"M3* selected an over-budget action: {selected_id}")
        continuation_cost += action_cost
        budget_used += action_cost
        actions_taken.append(selected_id)

        if run_mvp.is_stop_action(selected):
            action_feedback.append(
                {
                    "action_id": selected_id,
                    "action_type": selected["action_type"],
                    "recovered_count": 0,
                }
            )
            return {
                "success": False,
                "cost_to_go": continuation_cost,
                "action_path": action_path,
                "source_action_path": source_action_path,
                "consensus_substitution_count": consensus_substitutions,
                "terminal_reason": "explicit_stop",
            }

        recovered = run_mvp.realized_recovery(
            config,
            selected,
            hidden_ids,
            int(decision["seed"]),
        )
        action_feedback.append(
            {
                "action_id": selected_id,
                "action_type": selected.get("action_type", "other"),
                "recovered_count": len(recovered),
            }
        )
        visible_ids |= recovered
        hidden_ids -= recovered
        recovered_ids |= recovered

    return {
        "success": False,
        "cost_to_go": continuation_cost,
        "action_path": action_path,
        "source_action_path": source_action_path,
        "consensus_substitution_count": consensus_substitutions,
        "terminal_reason": "step_limit",
    }


def classify_regret(
    *,
    oracle_cost: float,
    oracle_path: list[str] | tuple[str, ...],
    policy_success: bool,
    policy_cost: float,
    policy_path: list[str] | tuple[str, ...],
    tolerance: float = REGRET_TOLERANCE,
) -> dict[str, Any]:
    """Classify extended regret without hiding success losses as missing cost."""

    oracle_reachable = math.isfinite(float(oracle_cost))
    if not oracle_reachable:
        return {
            "regret_status": (
                "oracle_contradiction" if policy_success else "both_unreachable"
            ),
            "oracle_reachable": 0,
            "policy_success": int(policy_success),
            "success_loss": 0,
            "oracle_contradiction": int(policy_success),
            "absolute_regret": None,
            "relative_regret": None,
            "zero_regret": 0,
            "first_action_match": int(
                bool(oracle_path)
                and bool(policy_path)
                and oracle_path[0] == policy_path[0]
            ),
        }
    if not policy_success:
        return {
            "regret_status": "unbounded_success_loss",
            "oracle_reachable": 1,
            "policy_success": 0,
            "success_loss": 1,
            "oracle_contradiction": 0,
            "absolute_regret": None,
            "relative_regret": None,
            "zero_regret": 0,
            "first_action_match": int(
                bool(oracle_path)
                and bool(policy_path)
                and oracle_path[0] == policy_path[0]
            ),
        }

    regret = float(policy_cost) - float(oracle_cost)
    if regret < -tolerance:
        return {
            "regret_status": "oracle_cost_violation",
            "oracle_reachable": 1,
            "policy_success": 1,
            "success_loss": 0,
            "oracle_contradiction": 1,
            "absolute_regret": regret,
            "relative_regret": regret / max(float(oracle_cost), tolerance),
            "zero_regret": 0,
            "first_action_match": int(
                bool(oracle_path)
                and bool(policy_path)
                and oracle_path[0] == policy_path[0]
            ),
        }
    regret = max(0.0, regret)
    is_zero = math.isclose(regret, 0.0, rel_tol=0.0, abs_tol=tolerance)
    return {
        "regret_status": "zero" if is_zero else "positive",
        "oracle_reachable": 1,
        "policy_success": 1,
        "success_loss": 0,
        "oracle_contradiction": 0,
        "absolute_regret": 0.0 if is_zero else regret,
        "relative_regret": (
            0.0
            if is_zero
            else regret / max(float(oracle_cost), tolerance)
        ),
        "zero_regret": int(is_zero),
        "first_action_match": int(
            bool(oracle_path)
            and bool(policy_path)
            and oracle_path[0] == policy_path[0]
        ),
    }


def audit_decision_state(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    decision: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    oracle_cost, oracle_path = run_mvp.oracle_optimal_plan(
        config,
        actions,
        decision["visible_ids"],
        decision["hidden_ids"],
        int(decision["seed"]),
        float(decision["state"]["budget"]["budget_remaining"]),
        actions_taken=decision["actions_taken"],
    )
    policy = rollout_core_policy_from_state(
        config,
        claims,
        actions,
        decision,
        runtime,
    )
    classification = classify_regret(
        oracle_cost=oracle_cost,
        oracle_path=oracle_path,
        policy_success=bool(policy["success"]),
        policy_cost=float(policy["cost_to_go"]),
        policy_path=policy["action_path"],
    )
    return {
        **decision_identity_fields(config, decision),
        "oracle_cost_to_go": (
            round(float(oracle_cost), 9) if math.isfinite(oracle_cost) else None
        ),
        "oracle_action_path": ">".join(oracle_path),
        "m3star_cost_to_go": round(float(policy["cost_to_go"]), 9),
        "m3star_action_path": ">".join(policy["action_path"]),
        "m3star_source_action_path": ">".join(policy["source_action_path"]),
        "m3star_terminal_reason": policy["terminal_reason"],
        "consensus_substitution_count": policy[
            "consensus_substitution_count"
        ],
        **classification,
    }


def decision_identity_fields(
    config: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    return {
        "case_id": config["case_id"],
        "condition_id": decision["condition_id"],
        "mask_strategy": decision["mask_strategy"],
        "mask_intensity": decision["mask_intensity"],
        "seed": decision["seed"],
        "state_id": decision["state_id"],
        "state_depth": decision["state_depth"],
        "prefix_action_path": ">".join(decision["action_path"]),
        "budget_remaining": round(
            float(decision["state"]["budget"]["budget_remaining"]), 9
        ),
        "visible_claim_count": len(decision["visible_ids"]),
        "hidden_claim_count": len(decision["hidden_ids"]),
    }


def decision_cache_key(decision: dict[str, Any]) -> tuple[Any, ...]:
    """Key only evaluator-equivalent states; condition labels are irrelevant."""

    return (
        int(decision["seed"]),
        frozenset(decision["visible_ids"]),
        frozenset(decision["hidden_ids"]),
        frozenset(decision["recovered_ids"]),
        tuple(decision["actions_taken"]),
        round(float(decision["budget_used"]), 9),
        tuple(
            (
                str(feedback["action_id"]),
                str(feedback["action_type"]),
                int(feedback["recovered_count"]),
            )
            for feedback in decision["action_feedback"]
        ),
    )


def quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    finite = [
        float(row["absolute_regret"])
        for row in rows
        if row.get("absolute_regret") is not None
        and not int(row.get("oracle_contradiction", 0))
    ]
    comparable = [
        row
        for row in rows
        if int(row.get("oracle_reachable", 0))
        and int(row.get("policy_success", 0))
        and not int(row.get("oracle_contradiction", 0))
    ]
    zero_count = sum(int(row.get("zero_regret", 0)) for row in comparable)
    return {
        "state_count": len(rows),
        "oracle_reachable_state_count": sum(
            int(row.get("oracle_reachable", 0)) for row in rows
        ),
        "both_unreachable_state_count": sum(
            row.get("regret_status") == "both_unreachable" for row in rows
        ),
        "comparable_success_state_count": len(comparable),
        "success_loss_count": sum(int(row.get("success_loss", 0)) for row in rows),
        "oracle_contradiction_count": sum(
            int(row.get("oracle_contradiction", 0)) for row in rows
        ),
        "finite_max_absolute_regret": max(finite) if finite else None,
        "mean_absolute_regret": (
            sum(finite) / len(finite) if finite else None
        ),
        "p95_absolute_regret": quantile(finite, 0.95),
        "p99_absolute_regret": quantile(finite, 0.99),
        "zero_regret_state_count": zero_count,
        "zero_regret_state_proportion": (
            zero_count / len(comparable) if comparable else None
        ),
    }


def summarize_regret_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    overall = summarize_group(rows)
    by_case = {
        case_id: summarize_group(
            [row for row in rows if str(row["case_id"]) == case_id]
        )
        for case_id in sorted({str(row["case_id"]) for row in rows})
    }
    by_depth = {
        str(depth): summarize_group(
            [row for row in rows if int(row["state_depth"]) == depth]
        )
        for depth in sorted({int(row["state_depth"]) for row in rows})
    }
    if overall["oracle_contradiction_count"]:
        claim_status = "invalid_oracle_contradiction"
        epsilon = None
    elif overall["success_loss_count"]:
        claim_status = "unbounded_due_to_success_loss"
        epsilon = None
    else:
        epsilon = overall["finite_max_absolute_regret"]
        claim_status = (
            "exact_optimal_within_enumerated_frozen_model"
            if epsilon is not None and epsilon <= REGRET_TOLERANCE
            else "bounded_regret_within_enumerated_frozen_model"
        )

    def worst_key(row: dict[str, Any]) -> tuple[int, float, str]:
        return (
            int(row.get("success_loss", 0)),
            (
                float(row["absolute_regret"])
                if row.get("absolute_regret") is not None
                else -1.0
            ),
            str(row["state_id"]),
        )

    worst_rows = sorted(rows, key=worst_key, reverse=True)[:20]
    worst_states = [
        {
            key: row[key]
            for key in (
                "case_id",
                "state_id",
                "state_depth",
                "prefix_action_path",
                "oracle_cost_to_go",
                "oracle_action_path",
                "m3star_cost_to_go",
                "m3star_action_path",
                "m3star_terminal_reason",
                "regret_status",
                "absolute_regret",
                "relative_regret",
            )
        }
        for row in worst_rows
    ]
    return {
        "overall": overall,
        "by_case": by_case,
        "by_state_depth": by_depth,
        "certificate": {
            "claim_status": claim_status,
            "epsilon_absolute_cost": epsilon,
            "regret_tolerance": REGRET_TOLERANCE,
            "domain": "oracle-reachable enumerated states only",
            "unreachable_states_checked_for_oracle_contradiction": True,
            "not_proven_beyond_enumerated_model": True,
        },
        "worst_states": worst_states,
    }


def audit_cases(
    cases: list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]],
    runtime: dict[str, Any],
    max_depth: int,
    progress: Callable[[str], None] = print,
    checkpoint_dir: Path | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total_started = time.monotonic()
    total_cache_hits = 0
    for case_index, (config, claims, actions) in enumerate(cases, start=1):
        started = time.monotonic()
        case_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
        case_cache_hits = 0
        decisions = run_m3star.enumerate_reachable_decision_states(
            config,
            claims,
            actions,
            max_depth=max_depth,
        )
        progress(
            "[enumerate] "
            f"case={config['case_id']} {case_index}/{len(cases)} "
            f"states={len(decisions)}"
        )
        for index, decision in enumerate(decisions, start=1):
            cache_key = decision_cache_key(decision)
            cached = case_cache.get(cache_key)
            if cached is None:
                evaluated = audit_decision_state(
                    config,
                    claims,
                    actions,
                    decision,
                    runtime,
                )
                identity_keys = set(decision_identity_fields(config, decision))
                cached = {
                    key: value
                    for key, value in evaluated.items()
                    if key not in identity_keys
                }
                case_cache[cache_key] = cached
                rows.append(evaluated)
            else:
                case_cache_hits += 1
                total_cache_hits += 1
                rows.append(
                    {
                        **decision_identity_fields(config, decision),
                        **cached,
                    }
                )
            if index % 50 == 0 or index == len(decisions):
                progress(
                    "[audit] "
                    f"case={config['case_id']} states={index}/{len(decisions)} "
                    f"cache_hits={case_cache_hits} "
                    f"seconds={time.monotonic() - started:.1f}"
                )
        if checkpoint_dir is not None:
            checkpoint = {
                "status": "running",
                "completed_case_count": case_index,
                "total_case_count": len(cases),
                "last_completed_case_id": config["case_id"],
                "state_count": len(rows),
                "cache_hit_count": total_cache_hits,
                "elapsed_seconds": round(time.monotonic() - total_started, 3),
            }
            (checkpoint_dir / "progress.json").write_text(
                json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        progress(
            "[case-complete] "
            f"case={config['case_id']} states={len(decisions)} "
            f"cache_hits={case_cache_hits} "
            f"seconds={time.monotonic() - started:.1f}"
        )
    progress(
        f"[audit-complete] states={len(rows)} "
        f"seconds={time.monotonic() - total_started:.1f}"
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty Oracle-regret audit")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--cases-root", type=Path, required=True)
    parser.add_argument("--cost-profile", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--candidate-learned-head-majority-shield",
        action="store_true",
        help="Audit a development candidate; the frozen v0.8 default remains off.",
    )
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    experiment = load_json(args.result_dir / "experiment_report.json")
    if experiment.get("cost_regime") != "measured":
        raise ValueError("Oracle-regret certification requires measured cost")
    if CORE_METHOD not in {
        spec.get("planner_id") for spec in experiment.get("method_specs", [])
    }:
        raise ValueError(f"Frozen result does not contain {CORE_METHOD}")
    core_spec = next(
        spec
        for spec in experiment["method_specs"]
        if spec.get("planner_id") == CORE_METHOD
    )
    expected_core = {
        "horizon": 3,
        "use_action_value": True,
        "myopic_safety_shield": True,
        "stochastic_dominance_shield": True,
        "use_policy_expert_consensus": True,
    }
    for field, expected in expected_core.items():
        if core_spec.get(field) != expected:
            raise ValueError(
                f"Frozen core contract mismatch for {field}: "
                f"{core_spec.get(field)!r} != {expected!r}"
            )

    cost_profile = run_mvp.load_cost_profile(args.cost_profile)
    expected_profile_hash = experiment["cost_profile_identity"]["sha256"]
    if cost_profile["sha256"] != expected_profile_hash:
        raise ValueError(
            "Cost profile differs from the frozen experiment: "
            f"{cost_profile['sha256']} != {expected_profile_hash}"
        )
    case_ids = [str(value) for value in experiment["evaluation_case_ids"]]
    cases = load_frozen_cases(args.cases_root, case_ids, cost_profile)
    models = load_saved_models(args.result_dir)
    runtime = build_runtime(
        models,
        experiment["configuration"],
        learned_head_majority_shield=(
            args.candidate_learned_head_majority_shield
        ),
    )
    max_depth = int(experiment["configuration"]["max_depth"])
    rows = audit_cases(
        cases,
        runtime,
        max_depth,
        progress=lambda message: print(message, flush=True),
        checkpoint_dir=args.output_dir,
    )

    csv_path = args.output_dir / "state_oracle_regret.csv"
    write_csv(csv_path, rows)
    summary = summarize_regret_rows(rows)
    report = {
        "audit_id": (
            "project05-m3star-exact-oracle-regret-audit-majority-candidate-v0.2"
            if args.candidate_learned_head_majority_shield
            else "project05-m3star-exact-oracle-regret-audit-v0.1"
        ),
        "status": "frozen_model_internal_method_development_audit",
        "paper_or_patent_updated": False,
        "formal_external_claim_allowed": False,
        "core_method": CORE_METHOD,
        "candidate_modifications": {
            "learned_head_majority_shield": (
                args.candidate_learned_head_majority_shield
            ),
            "frozen_models_retrained": False,
        },
        "independent_statistical_unit": "case_id",
        "within_case_conditions_are_repeated_measurements": True,
        "oracle": {
            "kind": "exact_recursive_minimum_cost_search_with_memoization",
            "success_precedes_cost": True,
            "stop_actions_excluded_from_recovery_paths": True,
        },
        "enumeration": {
            "kind": "shared_training_and_audit_breadth_first_state_enumerator",
            "max_depth": max_depth,
            "decision_state_depths": list(range(max_depth)),
            "case_ids": case_ids,
            "condition_count": len(
                {
                    (row["case_id"], row["condition_id"])
                    for row in rows
                }
            ),
            "state_count": len(rows),
        },
        "frozen_inputs": {
            "experiment_report_sha256": sha256(
                args.result_dir / "experiment_report.json"
            ),
            "evaluation_manifest_sha256": sha256(
                args.result_dir / "evaluation_manifest.json"
            ),
            "model_metadata_sha256": sha256(
                args.result_dir / "models" / "model_metadata.json"
            ),
            "cost_profile_sha256": cost_profile["sha256"],
            "runtime_contract": experiment["runtime_contract"],
            "run_m3star_sha256": sha256(
                Path(__file__).with_name("run_m3star.py")
            ),
            "audit_runner_sha256": sha256(Path(__file__)),
        },
        "summary": summary,
        "scope_limitations": [
            "Certificate applies only to Oracle-reachable states enumerated by the frozen model and action set.",
            "It does not prove optimality on unenumerated states, future data, changed costs, or future algorithms.",
            "C07-C12 remain reusable development cases and are not an external final blind test.",
        ],
        "state_csv": csv_path.name,
        "state_csv_sha256": sha256(csv_path),
    }
    report_path = args.output_dir / "oracle_regret_audit.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (args.output_dir / "progress.json").write_text(
        json.dumps(
            {
                "status": "complete",
                "completed_case_count": len(cases),
                "total_case_count": len(cases),
                "state_count": len(rows),
                "claim_status": summary["certificate"]["claim_status"],
                "epsilon_absolute_cost": summary["certificate"][
                    "epsilon_absolute_cost"
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary["certificate"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
