#!/usr/bin/env python3
"""Audit conservative XGBoost/Logistic advice on frozen M3* traces.

This is an offline diagnostic. Hidden recovery outcomes are used only to
evaluate proposed substitutions and are never exposed to a runtime planner.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

import xgboost as xgb


def load_script(name: str) -> Any:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


run_m3star = load_script("run_m3star")
run_xgboost = load_script("run_xgboost")
run_m3b = run_xgboost.run_m3b
run_mvp = run_xgboost.run_mvp

CORE_METHOD = "project05_m3star_h3_dual"
XGBOOST_METHOD = "project05_xgboost_policy"
LOGISTIC_METHOD = "project05_m3b_policy"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_traces(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def load_booster(path: Path) -> xgb.Booster:
    booster = xgb.Booster()
    booster.load_model(path)
    return booster


def load_saved_models(
    result_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    model_dir = result_dir / "models"
    metadata = load_json(model_dir / "model_metadata.json")
    xgboost_model = {
        **metadata["xgboost"],
        "booster": load_booster(model_dir / "xgboost.json"),
    }
    transition_model = {
        **metadata["transition"],
        "booster": load_booster(model_dir / "transition.json"),
    }
    action_model = {
        **metadata["action_value"],
        "booster": load_booster(model_dir / "action_value.json"),
    }
    reachability_path = model_dir / "action_reachability.json"
    if reachability_path.is_file():
        action_model["reachability_booster"] = load_booster(reachability_path)
    cost_path = model_dir / "action_cost.json"
    if cost_path.is_file():
        action_model["cost_booster"] = load_booster(cost_path)
    if not run_m3star.has_action_reachability_head(action_model):
        raise ValueError(f"Missing M3* reachability head in {model_dir}")
    return xgboost_model, transition_model, action_model


def one_step_target_reach_probability(
    snapshot: dict[str, Any],
    action: dict[str, Any],
    transition_predictor: Any,
) -> float:
    probability = 0.0
    outcomes = run_m3star._normalised_outcomes(
        snapshot,
        transition_predictor(snapshot, action),
    )
    for outcome in outcomes:
        projected = run_m3star._project_snapshot(
            snapshot,
            action,
            outcome["resolved_node_ids"],
        )
        if run_m3star._target_reached(projected):
            probability += float(outcome["probability"])
    return probability


def train_logistic_model(
    cases_root: Path,
    cost_profile: dict[str, Any],
) -> tuple[dict[str, Any], list[str], int]:
    train_dirs = [
        path
        for path in run_mvp.discover_case_dirs(cases_root)
        if path.name.startswith(("C04-", "C05-", "C06-"))
    ]
    if len(train_dirs) != 3:
        raise ValueError(f"Expected three calibration cases, found {train_dirs}")
    rows = run_xgboost.build_rows_for_cost_regime(
        train_dirs,
        "measured",
        cost_profile,
    )
    model = run_m3b.train_logistic_baseline(
        rows,
        run_xgboost.FEATURE_COLUMNS,
        run_xgboost.PRIMARY_LABEL,
    )
    return model, [path.name for path in train_dirs], len(rows)


def train_action_aux_models(
    cases_root: Path,
    cost_profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], int]:
    train_dirs = [
        path
        for path in run_mvp.discover_case_dirs(cases_root)
        if path.name.startswith(("C04-", "C05-", "C06-"))
    ]
    node_rows: list[dict[str, Any]] = []
    for config, claims, actions in run_xgboost.load_cases(
        train_dirs,
        "measured",
        cost_profile,
    ):
        node_rows.extend(
            run_m3star.build_reachable_transition_rows(
                config,
                claims,
                actions,
                max_depth=3,
            )
        )
    action_rows = run_m3star.aggregate_action_value_rows(node_rows)
    yield_labels: dict[tuple[str, str, str], int] = {}
    for row in node_rows:
        key = (
            str(row["case_id"]),
            str(row["state_id"]),
            str(row["action_id"]),
        )
        label = int(row["label_yield_positive"])
        prior = yield_labels.setdefault(key, label)
        if prior != label:
            raise ValueError(f"Inconsistent action-yield label for {key}")
    for row in action_rows:
        row["label_yield_positive"] = yield_labels[
            (
                str(row["case_id"]),
                str(row["state_id"]),
                str(row["action_id"]),
            )
        ]
    labels = {int(row["label_yield_positive"]) for row in action_rows}
    if labels != {0, 1}:
        raise ValueError(f"Action-yield head needs both classes, found {labels}")
    booster = xgb.train(
        dict(run_m3star.ACTION_VALUE_PARAMS),
        run_m3star._action_value_matrix(
            action_rows,
            label_column="label_yield_positive",
        ),
        num_boost_round=150,
    )
    rank_rows = sorted(
        action_rows,
        key=lambda row: (
            str(row["case_id"]),
            str(row["state_id"]),
            str(row["action_id"]),
        ),
    )
    group_sizes: list[int] = []
    prior_group: tuple[str, str] | None = None
    for row in rank_rows:
        group = (str(row["case_id"]), str(row["state_id"]))
        if group != prior_group:
            group_sizes.append(0)
            prior_group = group
        group_sizes[-1] += 1
    rank_matrix = run_m3star._action_value_matrix(
        rank_rows,
        label_column="label_oracle_optimal_action",
    )
    rank_matrix.set_group(group_sizes)
    rank_params = {
        **dict(run_m3star.ACTION_VALUE_PARAMS),
        "objective": "rank:pairwise",
        "eval_metric": "ndcg",
    }
    rank_booster = xgb.train(
        rank_params,
        rank_matrix,
        num_boost_round=150,
    )
    yield_model = {
        "model_family": "m3star_graph_action_yield_xgboost_audit_v0.1",
        "booster": booster,
        "feature_columns": list(run_m3star.ACTION_VALUE_FEATURE_COLUMNS),
        "label_column": "label_yield_positive",
    }
    rank_model = {
        "model_family": "m3star_graph_action_pairwise_rank_xgboost_audit_v0.1",
        "booster": rank_booster,
        "feature_columns": list(run_m3star.ACTION_VALUE_FEATURE_COLUMNS),
        "label_column": "label_oracle_optimal_action",
        "params": rank_params,
    }
    return yield_model, rank_model, len(action_rows)


def action_rank_scores(
    model: dict[str, Any],
    snapshot: dict[str, Any],
    actions: list[dict[str, Any]],
) -> dict[str, float]:
    rows = run_m3star.action_value_feature_rows(snapshot, actions)
    if not rows:
        return {}
    scores = model["booster"].predict(run_m3star._action_value_matrix(rows))
    return {
        str(row["action_id"]): float(score)
        for row, score in zip(rows, scores)
    }


def load_cases(
    cases_root: Path,
    cost_profile: dict[str, Any],
) -> dict[str, tuple[dict[str, Any], list[dict[str, Any]]]]:
    loaded: dict[str, tuple[dict[str, Any], list[dict[str, Any]]]] = {}
    for case_dir in run_mvp.discover_case_dirs(cases_root):
        config = load_json(case_dir / "case_config.json")
        actions = load_json(case_dir / "acquisition_actions.json")
        actions, _ = run_mvp.apply_cost_regime(
            actions,
            config["case_id"],
            "measured",
            cost_profile,
        )
        loaded[config["case_id"]] = (
            config,
            run_mvp.ensure_stop_action(config, actions),
        )
    return loaded


def condition_key(row: dict[str, Any]) -> tuple[str, str, float, int]:
    return (
        str(row["case_id"]),
        str(row["mask_strategy"]),
        float(row["mask_intensity"]),
        int(row["seed"]),
    )


def load_policy_index(result_dir: Path) -> dict[tuple[Any, ...], dict[str, Any]]:
    indexed: dict[tuple[Any, ...], dict[str, Any]] = {}
    with (result_dir / "development_policy_results.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            key = (*condition_key(row), str(row["planner"]))
            if key in indexed:
                raise ValueError(f"Duplicate policy result: {key}")
            indexed[key] = row
    return indexed


def audit_result_dir(
    result_dir: Path,
    cases: dict[str, tuple[dict[str, Any], list[dict[str, Any]]]],
    logistic_model: dict[str, Any],
    yield_model: dict[str, Any],
    rank_model: dict[str, Any],
    threshold: float,
    yield_threshold: float,
) -> list[dict[str, Any]]:
    xgboost_model, transition_model, action_model = load_saved_models(result_dir)
    transition_predictor = run_m3star.model_transition_predictor(
        transition_model,
        max_outcome_nodes=8,
        max_explicit_outcomes=None,
    )
    reachability_predictor = run_m3star.model_action_reachability_predictor(
        action_model
    )
    action_value_predictor = run_m3star.model_action_value_predictor(action_model)
    action_cost_predictor = run_m3star.model_action_cost_predictor(action_model)
    yield_predictor = run_m3star.model_action_value_predictor(yield_model)
    policy_index = load_policy_index(result_dir)
    trace_path = result_dir / "development_m3star_traces.json.gz"
    packages = load_traces(trace_path)
    audit_rows: list[dict[str, Any]] = []
    for package in packages:
        if package.get("planner") != CORE_METHOD:
            continue
        case_id = str(package["case_id"])
        config, actions = cases[case_id]
        actions_by_id = run_mvp.action_by_id(actions)
        key = condition_key(package)
        xgboost_result = policy_index[(*key, XGBOOST_METHOD)]
        logistic_result = policy_index[(*key, LOGISTIC_METHOD)]
        trace = package["trace"]
        for event_index, event in enumerate(trace):
            if event.get("event") != "action_taken":
                continue
            if event_index == 0:
                raise AssertionError("Action event has no preceding state")
            state = trace[event_index - 1]["state"]
            decision = event["m3star_decision"]
            selected_id = str(decision["selected_action_id"])
            xgboost_action = run_xgboost.select_xgboost_action(
                config,
                state,
                actions,
                xgboost_model,
                run_xgboost.FROZEN_COST_PENALTY,
            )
            logistic_action = run_xgboost.select_logistic_action(
                config,
                state,
                actions,
                logistic_model,
                run_xgboost.FROZEN_COST_PENALTY,
            )
            xgboost_id = None if xgboost_action is None else xgboost_action["action_id"]
            logistic_id = None if logistic_action is None else logistic_action["action_id"]
            experts_agree = xgboost_id == logistic_id and xgboost_id is not None
            candidate_id = str(xgboost_id) if experts_agree else None
            non_stop = candidate_id not in (None, run_mvp.STOP_ACTION_ID)
            candidate_action = actions_by_id.get(candidate_id) if non_stop else None
            selected_action = actions_by_id[selected_id]
            candidate_reachability = None
            candidate_transition_reachability = None
            selected_transition_reachability = None
            candidate_action_value = None
            selected_action_value = None
            candidate_action_cost_to_go = None
            selected_action_cost_to_go = None
            candidate_context: dict[str, float] = {}
            selected_context: dict[str, float] = {}
            xgboost_candidate_utility = None
            xgboost_candidate_probability = None
            logistic_candidate_utility = None
            logistic_candidate_probability = None
            candidate_yield_probability = None
            selected_yield_probability = None
            ranker_action_id = None
            candidate_rank_score = None
            selected_rank_score = None
            ranker_margin = None
            if candidate_action is not None:
                snapshot = run_m3star.public_graph_snapshot(config, state, actions)
                candidate_reachability = reachability_predictor(
                    snapshot,
                    [candidate_action],
                )[candidate_id]
                candidate_transition_reachability = (
                    one_step_target_reach_probability(
                        snapshot,
                        candidate_action,
                        transition_predictor,
                    )
                )
                selected_transition_reachability = (
                    one_step_target_reach_probability(
                        snapshot,
                        selected_action,
                        transition_predictor,
                    )
                )
                candidate_action_value = action_value_predictor(
                    snapshot,
                    [candidate_action],
                )[candidate_id]
                selected_action_value = action_value_predictor(
                    snapshot,
                    [selected_action],
                )[selected_id]
                candidate_action_cost_to_go = action_cost_predictor(
                    snapshot,
                    [candidate_action],
                )[candidate_id]
                selected_action_cost_to_go = action_cost_predictor(
                    snapshot,
                    [selected_action],
                )[selected_id]
                candidate_context = run_m3star._action_context_features(
                    snapshot,
                    candidate_action,
                )
                selected_context = run_m3star._action_context_features(
                    snapshot,
                    selected_action,
                )
                (
                    xgboost_candidate_utility,
                    xgboost_candidate_probability,
                ) = run_xgboost.xgboost_action_score(
                    config,
                    state,
                    candidate_action,
                    xgboost_model,
                    run_xgboost.FROZEN_COST_PENALTY,
                )
                (
                    logistic_candidate_utility,
                    logistic_candidate_probability,
                ) = run_xgboost.logistic_action_score(
                    config,
                    state,
                    candidate_action,
                    logistic_model,
                    run_xgboost.FROZEN_COST_PENALTY,
                )
                candidate_yield_probability = yield_predictor(
                    snapshot,
                    [candidate_action],
                )[candidate_id]
                selected_yield_probability = yield_predictor(
                    snapshot,
                    [selected_action],
                )[selected_id]
                rank_candidates = run_m3star._candidate_actions(snapshot)
                rank_scores = action_rank_scores(
                    rank_model,
                    snapshot,
                    rank_candidates,
                )
                ranked = sorted(
                    rank_candidates,
                    key=lambda action: (
                        -float(rank_scores[action["action_id"]]),
                        float(action["cost"]),
                        str(action["action_id"]),
                    ),
                )
                if ranked:
                    ranker_action_id = str(ranked[0]["action_id"])
                    candidate_rank_score = rank_scores[candidate_id]
                    selected_rank_score = rank_scores[selected_id]
                    runner_up_score = (
                        float(rank_scores[ranked[1]["action_id"]])
                        if len(ranked) > 1
                        else float(rank_scores[ranked[0]["action_id"]])
                    )
                    ranker_margin = (
                        float(rank_scores[ranked[0]["action_id"]])
                        - runner_up_score
                    )
            (
                xgboost_selected_utility,
                xgboost_selected_probability,
            ) = run_xgboost.xgboost_action_score(
                config,
                state,
                selected_action,
                xgboost_model,
                run_xgboost.FROZEN_COST_PENALTY,
            )
            (
                logistic_selected_utility,
                logistic_selected_probability,
            ) = run_xgboost.logistic_action_score(
                config,
                state,
                selected_action,
                logistic_model,
                run_xgboost.FROZEN_COST_PENALTY,
            )
            candidate_cost = (
                float(candidate_action["cost"])
                if candidate_action is not None
                else None
            )
            selected_cost = float(selected_action["cost"])
            eligible = bool(
                candidate_action is not None
                and candidate_id != selected_id
                and candidate_cost <= selected_cost + 1e-9
                and candidate_reachability is not None
                and candidate_reachability >= threshold
            )
            transition_noninferior = bool(
                candidate_transition_reachability is not None
                and selected_transition_reachability is not None
                and candidate_transition_reachability
                >= selected_transition_reachability - 1e-9
            )
            strict_eligible = eligible and transition_noninferior
            yield_gated_eligible = bool(
                eligible
                and candidate_yield_probability is not None
                and selected_yield_probability is not None
                and candidate_yield_probability >= yield_threshold
                and candidate_yield_probability
                >= selected_yield_probability - 1e-9
            )
            rank_gated_eligible = bool(
                eligible and ranker_action_id == candidate_id
            )
            hidden_ids = set(state.get("hidden_claim_ids", []))
            candidate_recovered = (
                run_mvp.realized_recovery(
                    config,
                    candidate_action,
                    hidden_ids,
                    int(package["seed"]),
                )
                if candidate_action is not None
                else set()
            )
            selected_recovered = run_mvp.realized_recovery(
                config,
                selected_action,
                hidden_ids,
                int(package["seed"]),
            )
            audit_rows.append(
                {
                    "source_result_dir": str(result_dir).replace("\\", "/"),
                    "case_id": case_id,
                    "mask_strategy": str(package["mask_strategy"]),
                    "mask_intensity": float(package["mask_intensity"]),
                    "seed": int(package["seed"]),
                    "decision_index": sum(
                        1
                        for prior in trace[: event_index + 1]
                        if prior.get("event") == "action_taken"
                    )
                    - 1,
                    "m3star_action_id": selected_id,
                    "m3star_action_cost": selected_cost,
                    "xgboost_action_id": xgboost_id,
                    "logistic_action_id": logistic_id,
                    "experts_agree": int(experts_agree),
                    "candidate_action_id": candidate_id,
                    "candidate_action_cost": candidate_cost,
                    "candidate_reachability": candidate_reachability,
                    "candidate_action_value_probability": candidate_action_value,
                    "m3star_action_value_probability": selected_action_value,
                    "candidate_action_cost_to_go": candidate_action_cost_to_go,
                    "m3star_action_cost_to_go": selected_action_cost_to_go,
                    "xgboost_candidate_probability": xgboost_candidate_probability,
                    "xgboost_m3star_probability": xgboost_selected_probability,
                    "xgboost_candidate_utility": xgboost_candidate_utility,
                    "xgboost_m3star_utility": xgboost_selected_utility,
                    "logistic_candidate_probability": (
                        logistic_candidate_probability
                    ),
                    "logistic_m3star_probability": logistic_selected_probability,
                    "logistic_candidate_utility": logistic_candidate_utility,
                    "logistic_m3star_utility": logistic_selected_utility,
                    "candidate_yield_probability": candidate_yield_probability,
                    "m3star_yield_probability": selected_yield_probability,
                    "ranker_action_id": ranker_action_id,
                    "candidate_rank_score": candidate_rank_score,
                    "m3star_rank_score": selected_rank_score,
                    "ranker_top_margin": ranker_margin,
                    "candidate_intended_gap_precision": candidate_context.get(
                        "intended_gap_precision"
                    ),
                    "m3star_intended_gap_precision": selected_context.get(
                        "intended_gap_precision"
                    ),
                    "candidate_intended_gap_recall": candidate_context.get(
                        "intended_gap_recall"
                    ),
                    "m3star_intended_gap_recall": selected_context.get(
                        "intended_gap_recall"
                    ),
                    "candidate_critical_gap_overlap": candidate_context.get(
                        "intended_critical_gap_overlap_count"
                    ),
                    "m3star_critical_gap_overlap": selected_context.get(
                        "intended_critical_gap_overlap_count"
                    ),
                    "candidate_transition_reachability": (
                        candidate_transition_reachability
                    ),
                    "m3star_transition_reachability": (
                        selected_transition_reachability
                    ),
                    "candidate_transition_noninferior": int(
                        transition_noninferior
                    ),
                    "candidate_differs_from_m3star": int(
                        candidate_id is not None and candidate_id != selected_id
                    ),
                    "consensus_substitution_eligible": int(eligible),
                    "transition_gated_substitution_eligible": int(
                        strict_eligible
                    ),
                    "yield_gated_substitution_eligible": int(
                        yield_gated_eligible
                    ),
                    "rank_gated_substitution_eligible": int(
                        rank_gated_eligible
                    ),
                    "xgboost_episode_success": int(
                        xgboost_result["reached_target"]
                    ),
                    "logistic_episode_success": int(
                        logistic_result["reached_target"]
                    ),
                    "candidate_recovered_count": len(candidate_recovered),
                    "m3star_recovered_count": len(selected_recovered),
                    "candidate_zero_yield_offline": int(
                        candidate_action is not None and not candidate_recovered
                    ),
                    "m3star_zero_yield_offline": int(not selected_recovered),
                }
            )
    return audit_rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[str, dict[str, Any]] = {}
    for case_id in sorted({str(row["case_id"]) for row in rows}):
        case_rows = [row for row in rows if row["case_id"] == case_id]
        eligible = [
            row for row in case_rows if row["consensus_substitution_eligible"]
        ]
        strict_eligible = [
            row
            for row in case_rows
            if row["transition_gated_substitution_eligible"]
        ]
        yield_eligible = [
            row
            for row in case_rows
            if row["yield_gated_substitution_eligible"]
        ]
        rank_eligible = [
            row
            for row in case_rows
            if row["rank_gated_substitution_eligible"]
        ]
        pairs = Counter(
            (row["m3star_action_id"], row["candidate_action_id"])
            for row in eligible
        )
        by_case[case_id] = {
            "decision_count": len(case_rows),
            "expert_agreement_count": sum(
                int(row["experts_agree"]) for row in case_rows
            ),
            "eligible_substitution_count": len(eligible),
            "transition_gated_substitution_count": len(strict_eligible),
            "yield_gated_substitution_count": len(yield_eligible),
            "rank_gated_substitution_count": len(rank_eligible),
            "rank_gated_in_logistic_failure_episode_count": sum(
                1
                for row in rank_eligible
                if not row["logistic_episode_success"]
            ),
            "rank_gated_candidate_zero_yield_count": sum(
                int(row["candidate_zero_yield_offline"])
                for row in rank_eligible
            ),
            "yield_gated_in_logistic_failure_episode_count": sum(
                1
                for row in yield_eligible
                if not row["logistic_episode_success"]
            ),
            "yield_gated_candidate_zero_yield_count": sum(
                int(row["candidate_zero_yield_offline"])
                for row in yield_eligible
            ),
            "transition_gated_in_logistic_failure_episode_count": sum(
                1
                for row in strict_eligible
                if not row["logistic_episode_success"]
            ),
            "transition_gated_candidate_zero_yield_count": sum(
                int(row["candidate_zero_yield_offline"])
                for row in strict_eligible
            ),
            "eligible_in_logistic_failure_episode_count": sum(
                1 for row in eligible if not row["logistic_episode_success"]
            ),
            "eligible_in_xgboost_failure_episode_count": sum(
                1 for row in eligible if not row["xgboost_episode_success"]
            ),
            "eligible_candidate_zero_yield_count": sum(
                int(row["candidate_zero_yield_offline"]) for row in eligible
            ),
            "eligible_m3star_zero_yield_count": sum(
                int(row["m3star_zero_yield_offline"]) for row in eligible
            ),
            "eligible_action_pairs": [
                {
                    "m3star_action_id": source,
                    "candidate_action_id": target,
                    "count": count,
                }
                for (source, target), count in sorted(pairs.items())
            ],
        }
    eligible = [row for row in rows if row["consensus_substitution_eligible"]]
    strict_eligible = [
        row for row in rows if row["transition_gated_substitution_eligible"]
    ]
    yield_eligible = [
        row for row in rows if row["yield_gated_substitution_eligible"]
    ]
    rank_eligible = [
        row for row in rows if row["rank_gated_substitution_eligible"]
    ]
    return {
        "decision_count": len(rows),
        "expert_agreement_count": sum(int(row["experts_agree"]) for row in rows),
        "eligible_substitution_count": len(eligible),
        "transition_gated_substitution_count": len(strict_eligible),
        "yield_gated_substitution_count": len(yield_eligible),
        "rank_gated_substitution_count": len(rank_eligible),
        "rank_gated_in_logistic_failure_episode_count": sum(
            1 for row in rank_eligible if not row["logistic_episode_success"]
        ),
        "rank_gated_candidate_zero_yield_count": sum(
            int(row["candidate_zero_yield_offline"])
            for row in rank_eligible
        ),
        "yield_gated_in_logistic_failure_episode_count": sum(
            1 for row in yield_eligible if not row["logistic_episode_success"]
        ),
        "yield_gated_candidate_zero_yield_count": sum(
            int(row["candidate_zero_yield_offline"])
            for row in yield_eligible
        ),
        "transition_gated_in_logistic_failure_episode_count": sum(
            1 for row in strict_eligible if not row["logistic_episode_success"]
        ),
        "transition_gated_candidate_zero_yield_count": sum(
            int(row["candidate_zero_yield_offline"])
            for row in strict_eligible
        ),
        "eligible_in_logistic_failure_episode_count": sum(
            1 for row in eligible if not row["logistic_episode_success"]
        ),
        "eligible_candidate_zero_yield_count": sum(
            int(row["candidate_zero_yield_offline"]) for row in eligible
        ),
        "by_case": by_case,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty consensus audit")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dirs", type=Path, nargs="+", required=True)
    parser.add_argument("--cases-root", type=Path, required=True)
    parser.add_argument("--cost-profile", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reachability-threshold", type=float, default=0.9)
    parser.add_argument("--yield-threshold", type=float, default=0.9)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    cost_profile = run_mvp.load_cost_profile(args.cost_profile)
    cases = load_cases(args.cases_root, cost_profile)
    logistic_model, train_case_dirs, train_row_count = train_logistic_model(
        args.cases_root,
        cost_profile,
    )
    yield_model, rank_model, yield_train_row_count = train_action_aux_models(
        args.cases_root,
        cost_profile,
    )
    rows: list[dict[str, Any]] = []
    for result_dir in args.result_dirs:
        rows.extend(
            audit_result_dir(
                result_dir,
                cases,
                logistic_model,
                yield_model,
                rank_model,
                args.reachability_threshold,
                args.yield_threshold,
            )
        )
    csv_path = args.output_dir / "expert_consensus_decisions.csv"
    write_csv(csv_path, rows)
    report = {
        "audit_id": "project05-m3star-policy-expert-consensus-audit-v0.1",
        "status": "offline_method_development_diagnostic",
        "runtime_use_of_hidden_outcomes": False,
        "independent_statistical_unit": "case_id",
        "within_case_conditions_are_repeated_measurements": True,
        "reachability_threshold": args.reachability_threshold,
        "yield_threshold": args.yield_threshold,
        "cost_rule": "candidate_measured_cost <= m3star_measured_cost",
        "expert_rule": "xgboost_action_id == logistic_action_id != STOP",
        "training_case_dirs": train_case_dirs,
        "logistic_training_row_count": train_row_count,
        "yield_training_row_count": yield_train_row_count,
        "cost_profile_sha256": cost_profile["sha256"],
        "inputs": {
            str(path).replace("\\", "/"): {
                "policy_results_sha256": sha256(
                    path / "development_policy_results.csv"
                ),
                "m3star_traces_sha256": sha256(
                    path / "development_m3star_traces.json.gz"
                ),
                "model_metadata_sha256": sha256(
                    path / "models" / "model_metadata.json"
                ),
            }
            for path in args.result_dirs
        },
        "summary": summarize(rows),
        "decision_csv": csv_path.name,
        "decision_csv_sha256": sha256(csv_path),
    }
    (args.output_dir / "expert_consensus_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
