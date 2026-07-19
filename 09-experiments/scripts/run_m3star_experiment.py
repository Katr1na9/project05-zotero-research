#!/usr/bin/env python3
"""Train and evaluate the auditable M3* dual-head controller.

This runner is deliberately separate from paper generation.  C01-C06 are the
model-development cases, C07-C12 are reusable development evaluation cases,
and any C13+ prefix is guarded as a one-shot final-blind evaluation.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any


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

DEVELOPMENT_EVALUATION_PREFIXES = (
    "C07-",
    "C08-",
    "C09-",
    "C10-",
    "C11-",
    "C12-",
)
METHOD_SPECS: tuple[dict[str, Any], ...] = (
    {
        "planner_id": "project05_m3star_h3_dual",
        "kind": "m3star",
        "horizon": 3,
        "use_action_value": True,
        "myopic_safety_shield": True,
        "stochastic_dominance_shield": True,
        "use_policy_expert_consensus": True,
    },
    {
        "planner_id": "project05_m3star_h3_no_dominance_dual",
        "kind": "m3star",
        "horizon": 3,
        "use_action_value": True,
        "myopic_safety_shield": True,
        "stochastic_dominance_shield": False,
    },
    {
        "planner_id": "project05_m3star_h3_unshielded_dual",
        "kind": "m3star",
        "horizon": 3,
        "use_action_value": True,
        "myopic_safety_shield": False,
        "stochastic_dominance_shield": True,
    },
    {
        "planner_id": "project05_m3star_h3_transition_only",
        "kind": "m3star",
        "horizon": 3,
        "use_action_value": False,
        "myopic_safety_shield": True,
        "stochastic_dominance_shield": True,
    },
    {
        "planner_id": "project05_m3star_h1_dual",
        "kind": "m3star",
        "horizon": 1,
        "use_action_value": True,
        "myopic_safety_shield": True,
        "stochastic_dominance_shield": True,
    },
    {
        "planner_id": "project05_xgboost_policy",
        "kind": "xgboost",
    },
    {
        "planner_id": "project05_m3b_policy",
        "kind": "logistic",
    },
    {
        "planner_id": "project05_m2",
        "kind": "builtin",
    },
    {
        "planner_id": "oracle_optimal",
        "kind": "builtin",
    },
)
CORE_METHOD = "project05_m3star_h3_dual"
CORE_BASELINES = (
    "project05_m2",
    "project05_xgboost_policy",
    "project05_m3b_policy",
)


def runtime_contract_metadata() -> dict[str, Any]:
    return run_m3star.runtime_adapter.contract_metadata(
        run_m3star.RUNTIME_CONTRACT,
    )


def cost_profile_identity(
    cost_regime: str,
    cost_profile: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if cost_regime == "legacy":
        return None
    if cost_regime == "uniform":
        document = run_mvp.BUILTIN_UNIFORM_COST_PROFILE
        return {
            "profile_id": str(document["profile_id"]),
            "version": str(document["version"]),
            "status": str(document["status"]),
            "regime": "uniform",
            "sha256": run_mvp.canonical_json_sha256(document),
            "source_path": None,
        }
    if cost_profile is None:
        raise ValueError(f"{cost_regime} cost runs require a cost profile")
    document = cost_profile.get("document")
    if not isinstance(document, dict):
        raise ValueError("Cost profile bundle is missing its document")
    return {
        "profile_id": str(document["profile_id"]),
        "version": str(document["version"]),
        "status": str(document["status"]),
        "regime": str(document["regime"]),
        "sha256": str(cost_profile["sha256"]),
        "source_path": str(cost_profile["source_path"]),
    }


def cost_claim_context(
    cost_regime: str,
    evaluation_role: str,
    profile_identity: dict[str, Any] | None,
) -> dict[str, Any]:
    if cost_regime not in {"rubric", "measured"}:
        reason = "non_normative_cost_regime"
    elif evaluation_role != "final_blind":
        reason = "development_evaluation_not_final_blind_confirmation"
    else:
        reason = "final_gate_must_be_evaluated_after_one_shot_confirmation"
    return {
        "formal_cost_claim_allowed": False,
        "reason": reason,
        "cost_regime": cost_regime,
        "cost_profile_identity": profile_identity,
        "evaluation_role": evaluation_role,
    }


CONDITION_FIELDS = (
    "case_id",
    "mask_strategy",
    "mask_intensity",
    "seed",
)


def _case_number(prefix: str) -> int | None:
    match = re.match(r"^C(\d+)", str(prefix), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def validate_evaluation_scope(
    prefixes: tuple[str, ...],
    role: str,
    confirm_final_test_once: bool,
) -> None:
    if not prefixes:
        raise ValueError("At least one evaluation case prefix is required")
    if len(set(prefixes)) != len(prefixes):
        raise ValueError(f"Duplicate evaluation prefixes: {prefixes}")
    final_prefixes = [
        prefix
        for prefix in prefixes
        if (_case_number(prefix) or 0) >= 13
    ]
    if final_prefixes and role != "final_blind":
        raise ValueError(
            "C13+ cases are reserved for final_blind evaluation; "
            f"requested={final_prefixes}"
        )
    if role == "final_blind" and not confirm_final_test_once:
        raise ValueError(
            "final_blind evaluation requires explicit one-shot confirmation"
        )
    if role == "development" and prefixes != DEVELOPMENT_EVALUATION_PREFIXES:
        raise ValueError(
            "development evaluation is frozen to C07-C12; use a distinct role "
            "for any other split"
        )


def validate_case_id_partition(
    train_case_ids: list[str] | tuple[str, ...] | set[str],
    evaluation_case_ids: list[str] | tuple[str, ...] | set[str],
) -> None:
    overlap = set(train_case_ids) & set(evaluation_case_ids)
    if overlap:
        raise ValueError(
            "M3* training and evaluation case IDs must be disjoint; "
            f"overlap={sorted(overlap)}"
        )


def select_experiment_case_dirs(
    examples_root: Path,
    real_cases_root: Path,
    evaluation_prefixes: tuple[str, ...],
    training_scope: str,
) -> tuple[list[Path], list[Path]]:
    return run_xgboost.selected_case_dirs(
        examples_root,
        real_cases_root,
        test_prefixes=evaluation_prefixes,
        training_scope=training_scope,
    )


def select_evaluation_subset(
    held_out_cases: list[
        tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]
    ],
    subset_prefixes: tuple[str, ...] | None,
) -> list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]]:
    """Filter only evaluation execution; never redefine the held-out split."""

    if subset_prefixes is None:
        return list(held_out_cases)
    if not subset_prefixes or len(set(subset_prefixes)) != len(subset_prefixes):
        raise ValueError(
            f"Evaluation subset prefixes must be nonempty and unique: {subset_prefixes}"
        )
    matched_by_prefix = {
        prefix: [
            case
            for case in held_out_cases
            if str(case[0]["case_id"]).startswith(prefix)
        ]
        for prefix in subset_prefixes
    }
    unmatched = [
        prefix for prefix, cases in matched_by_prefix.items() if not cases
    ]
    if unmatched:
        raise ValueError(
            f"Evaluation subset prefix matched no held-out case: {unmatched}"
        )
    selected_ids = {
        str(case[0]["case_id"])
        for cases in matched_by_prefix.values()
        for case in cases
    }
    return [
        case
        for case in held_out_cases
        if str(case[0]["case_id"]) in selected_ids
    ]


def _index_by_condition(
    rows: list[dict[str, Any]],
    planner_id: str,
) -> dict[tuple[Any, ...], dict[str, Any]]:
    indexed: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        if row.get("planner") != planner_id:
            continue
        key = tuple(row[field] for field in CONDITION_FIELDS)
        if key in indexed:
            raise ValueError(
                f"Duplicate {planner_id} row for condition {key}"
            )
        indexed[key] = row
    return indexed


def paired_against(
    rows: list[dict[str, Any]],
    candidate_id: str,
    baseline_id: str,
) -> dict[str, Any]:
    candidate = _index_by_condition(rows, candidate_id)
    baseline = _index_by_condition(rows, baseline_id)
    if set(candidate) != set(baseline):
        missing_candidate = sorted(set(baseline) - set(candidate))
        missing_baseline = sorted(set(candidate) - set(baseline))
        raise ValueError(
            "Paired method conditions do not match; "
            f"missing_candidate={missing_candidate[:3]}, "
            f"missing_baseline={missing_baseline[:3]}"
        )

    success_losses = 0
    success_gains = 0
    cost_deltas: list[float] = []
    cost_wins = 0
    cost_ties = 0
    cost_losses = 0
    action_sequence_changes = 0
    budget_totals: set[float] = set()
    for key in sorted(candidate):
        candidate_row = candidate[key]
        baseline_row = baseline[key]
        candidate_budget = candidate_row.get("budget_total")
        baseline_budget = baseline_row.get("budget_total")
        if (candidate_budget in (None, "")) != (
            baseline_budget in (None, "")
        ):
            raise ValueError(f"Paired budget metadata missing for condition {key}")
        if candidate_budget not in (None, ""):
            candidate_budget = float(candidate_budget)
            baseline_budget = float(baseline_budget)
            if not math.isclose(
                candidate_budget,
                baseline_budget,
                rel_tol=0.0,
                abs_tol=1e-9,
            ):
                raise ValueError(
                    f"Paired budgets do not match for condition {key}: "
                    f"candidate={candidate_budget}, baseline={baseline_budget}"
                )
            budget_totals.add(candidate_budget)
        candidate_success = int(candidate_row.get("reached_target", 0)) == 1
        baseline_success = int(baseline_row.get("reached_target", 0)) == 1
        success_losses += int(not candidate_success and baseline_success)
        success_gains += int(candidate_success and not baseline_success)
        action_sequence_changes += int(
            str(candidate_row.get("actions_taken", ""))
            != str(baseline_row.get("actions_taken", ""))
        )
        if not (candidate_success and baseline_success):
            continue
        delta = float(candidate_row["cost_to_target"]) - float(
            baseline_row["cost_to_target"]
        )
        cost_deltas.append(delta)
        if delta < -1e-9:
            cost_wins += 1
        elif delta > 1e-9:
            cost_losses += 1
        else:
            cost_ties += 1

    return {
        "candidate": candidate_id,
        "baseline": baseline_id,
        "paired_conditions": len(candidate),
        "success_loss_count": success_losses,
        "success_gain_count": success_gains,
        "both_success_count": len(cost_deltas),
        "cost_win_count": cost_wins,
        "cost_tie_count": cost_ties,
        "cost_loss_count": cost_losses,
        "total_cost_delta_on_both_success": round(sum(cost_deltas), 6),
        "mean_cost_delta_on_both_success": (
            round(sum(cost_deltas) / len(cost_deltas), 6)
            if cost_deltas
            else None
        ),
        "budget_total": (
            next(iter(budget_totals)) if len(budget_totals) == 1 else None
        ),
        "action_sequence_change_count": action_sequence_changes,
    }


def casewise_paired_against(
    rows: list[dict[str, Any]],
    candidate_id: str,
    baseline_id: str,
) -> dict[str, dict[str, Any]]:
    return {
        str(case_id): paired_against(
            [row for row in rows if row["case_id"] == case_id],
            candidate_id,
            baseline_id,
        )
        for case_id in sorted({row["case_id"] for row in rows})
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def write_json_gzip(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write an empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    preferred = [
        *CONDITION_FIELDS,
        "planner",
        "reached_target",
        "cost_to_target",
        "steps_to_target",
        "actions_taken",
        "budget_used",
        "cost_regret_vs_oracle",
        "oracle_top1_action_hit",
        "premature_stop",
        "ceiling_violation",
    ]
    all_fields = {field for row in rows for field in row}
    fields = [field for field in preferred if field in all_fields]
    fields.extend(sorted(all_fields - set(fields)))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _public_model_metadata(model: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in model.items()
        if key != "booster" and not key.endswith("_booster")
    }


def _dataset_summary(
    node_rows: list[dict[str, Any]],
    action_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    node_positives = sum(int(row["label_node_resolved"]) for row in node_rows)
    action_positives = sum(
        int(row["label_oracle_optimal_action"]) for row in action_rows
    )
    unreachable = sum(
        1 - int(row["label_oracle_reachable_via_action"])
        for row in action_rows
    )
    finite_cost_targets = [
        float(row["label_oracle_cost_via_action"])
        for row in action_rows
        if row.get("label_oracle_cost_via_action") not in (None, "")
        and math.isfinite(float(row["label_oracle_cost_via_action"]))
    ]
    return {
        "decision_state_count": len({row["state_id"] for row in node_rows}),
        "node_transition_row_count": len(node_rows),
        "node_positive_rate": round(node_positives / len(node_rows), 6),
        "state_action_row_count": len(action_rows),
        "oracle_optimal_action_positive_rate": round(
            action_positives / len(action_rows),
            6,
        ),
        "oracle_unreachable_action_rate": round(
            unreachable / len(action_rows),
            6,
        ),
        "finite_oracle_cost_target_count": len(finite_cost_targets),
        "mean_oracle_cost_target": round(
            sum(finite_cost_targets) / len(finite_cost_targets),
            6,
        ),
    }


def build_training_datasets(
    train_cases: list[
        tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]
    ],
    max_depth: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    node_rows: list[dict[str, Any]] = []
    started = time.monotonic()
    for index, (config, claims, actions) in enumerate(train_cases, start=1):
        case_started = time.monotonic()
        case_rows = run_m3star.build_reachable_transition_rows(
            config,
            claims,
            actions,
            max_depth=max_depth,
        )
        node_rows.extend(case_rows)
        print(
            "[dataset] "
            f"case={config['case_id']} {index}/{len(train_cases)} "
            f"rows={len(case_rows)} cumulative={len(node_rows)} "
            f"seconds={time.monotonic() - case_started:.1f}",
            flush=True,
        )
    action_rows = run_m3star.aggregate_action_value_rows(node_rows)
    print(
        "[dataset] complete "
        f"node_rows={len(node_rows)} action_rows={len(action_rows)} "
        f"seconds={time.monotonic() - started:.1f}",
        flush=True,
    )
    return node_rows, action_rows


def train_models(
    train_dirs: list[Path],
    train_cases: list[
        tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]
    ],
    max_depth: int,
    boost_rounds: int,
    cost_regime: str,
    cost_profile: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    node_rows, action_rows = build_training_datasets(train_cases, max_depth)
    print("[train] fitting M3* graph-transition head", flush=True)
    transition_model = run_m3star.train_graph_transition_model(
        node_rows,
        boost_rounds=boost_rounds,
    )
    print("[train] fitting M3* graph action-value head", flush=True)
    action_value_model = run_m3star.train_graph_action_value_model(
        action_rows,
        boost_rounds=boost_rounds,
    )
    print("[train] fitting M3* pairwise action-rank head", flush=True)
    action_rank_model = run_m3star.train_graph_action_rank_model(
        action_rows,
        boost_rounds=boost_rounds,
    )
    baseline_rows = run_xgboost.build_rows_for_cost_regime(
        train_dirs,
        cost_regime,
        cost_profile,
    )
    print("[train] fitting frozen XGBoost baseline", flush=True)
    xgboost_model = run_xgboost.train_xgboost(
        baseline_rows,
        run_xgboost.FEATURE_COLUMNS,
        run_xgboost.PRIMARY_LABEL,
        boost_rounds=boost_rounds,
    )
    print("[train] fitting Logistic/M3b baseline", flush=True)
    logistic_model = run_m3b.train_logistic_baseline(
        baseline_rows,
        run_xgboost.FEATURE_COLUMNS,
        run_xgboost.PRIMARY_LABEL,
    )
    models = {
        "transition": transition_model,
        "action_value": action_value_model,
        "action_rank": action_rank_model,
        "xgboost": xgboost_model,
        "logistic": logistic_model,
    }
    dataset = {
        "node_rows": node_rows,
        "action_rows": action_rows,
        "baseline_rows": baseline_rows,
        "summary": _dataset_summary(node_rows, action_rows),
    }
    return models, dataset


def build_policy_expert_advisor(models: dict[str, Any]) -> Any:
    rank_predictor = run_m3star.model_action_rank_predictor(
        models["action_rank"]
    )

    def advise(
        config: dict[str, Any],
        state: dict[str, Any],
        actions: list[dict[str, Any]],
    ) -> dict[str, str]:
        xgboost_action = run_xgboost.select_xgboost_action(
            config,
            state,
            actions,
            models["xgboost"],
            run_xgboost.FROZEN_COST_PENALTY,
        )
        logistic_action = run_xgboost.select_logistic_action(
            config,
            state,
            actions,
            models["logistic"],
            run_xgboost.FROZEN_COST_PENALTY,
        )
        snapshot = run_m3star.public_graph_snapshot(config, state, actions)
        candidates = run_m3star._candidate_actions(snapshot)
        rank_scores = rank_predictor(snapshot, candidates)
        ranked = sorted(
            candidates,
            key=lambda action: (
                -float(rank_scores[action["action_id"]]),
                float(action["cost"]),
                str(action["action_id"]),
            ),
        )
        return {
            "xgboost": (
                run_mvp.STOP_ACTION_ID
                if xgboost_action is None
                else str(xgboost_action["action_id"])
            ),
            "logistic": (
                run_mvp.STOP_ACTION_ID
                if logistic_action is None
                else str(logistic_action["action_id"])
            ),
            "pairwise_rank": (
                run_mvp.STOP_ACTION_ID
                if not ranked
                else str(ranked[0]["action_id"])
            ),
        }

    return advise


def _run_method(
    spec: dict[str, Any],
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    condition: tuple[str, float, int],
    models: dict[str, Any],
    target_reach_threshold: float,
    max_outcome_nodes: int,
    max_explicit_outcomes: int | None,
) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
    strategy, intensity, seed = condition
    kind = spec["kind"]
    if kind == "m3star":
        row, trace = run_m3star.run_m3star_model_episode(
            config,
            claims,
            actions,
            strategy,
            intensity,
            seed,
            models["transition"],
            action_value_model=(
                models["action_value"]
                if spec["use_action_value"]
                else None
            ),
            horizon=spec["horizon"],
            max_outcome_nodes=max_outcome_nodes,
            max_explicit_outcomes=max_explicit_outcomes,
            target_reach_threshold=target_reach_threshold,
            myopic_safety_shield=spec["myopic_safety_shield"],
            stochastic_dominance_shield=spec.get(
                "stochastic_dominance_shield",
                True,
            ),
            policy_expert_advisor=(
                build_policy_expert_advisor(models)
                if spec.get("use_policy_expert_consensus", False)
                else None
            ),
        )
        row["planner"] = spec["planner_id"]
        row["m3star_requested_horizon"] = spec["horizon"]
        row["m3star_uses_action_value"] = int(spec["use_action_value"])
        row["m3star_myopic_safety_shield"] = int(
            spec["myopic_safety_shield"]
        )
        row["m3star_stochastic_dominance_shield"] = int(
            spec.get("stochastic_dominance_shield", True)
        )
        row["m3star_uses_policy_expert_consensus"] = int(
            spec.get("use_policy_expert_consensus", False)
        )
        return row, trace
    if kind == "xgboost":
        row, _ = run_xgboost.run_xgboost_episode(
            config,
            claims,
            actions,
            strategy,
            intensity,
            seed,
            models["xgboost"],
            run_xgboost.FROZEN_COST_PENALTY,
        )
        return row, None
    if kind == "logistic":
        row, _ = run_xgboost.run_logistic_episode(
            config,
            claims,
            actions,
            strategy,
            intensity,
            seed,
            models["logistic"],
            run_xgboost.FROZEN_COST_PENALTY,
        )
        return row, None
    row, _ = run_mvp.run_episode(
        config,
        claims,
        actions,
        strategy,
        intensity,
        seed,
        spec["planner_id"],
    )
    return row, None


def evaluate_partition(
    partition: str,
    cases: list[
        tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]
    ],
    models: dict[str, Any],
    output_dir: Path,
    target_reach_threshold: float,
    max_outcome_nodes: int,
    max_explicit_outcomes: int | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    all_traces: list[dict[str, Any]] = []
    total_conditions = sum(
        len(run_mvp.experiment_conditions(config))
        for config, _, _ in cases
    )
    completed_conditions = 0
    started = time.monotonic()
    for case_index, (config, claims, actions) in enumerate(cases, start=1):
        case_rows: list[dict[str, Any]] = []
        conditions = run_mvp.experiment_conditions(config)
        print(
            f"[evaluate:{partition}] case={config['case_id']} "
            f"{case_index}/{len(cases)} conditions={len(conditions)}",
            flush=True,
        )
        for condition_index, condition in enumerate(conditions, start=1):
            for spec in METHOD_SPECS:
                row, trace = _run_method(
                    spec,
                    config,
                    claims,
                    actions,
                    condition,
                    models,
                    target_reach_threshold,
                    max_outcome_nodes,
                    max_explicit_outcomes,
                )
                row["evaluation_partition"] = partition
                row["budget_total"] = float(config["budget_total"])
                case_rows.append(row)
                if trace is not None:
                    all_traces.append(
                        {
                            "case_id": config["case_id"],
                            "mask_strategy": condition[0],
                            "mask_intensity": condition[1],
                            "seed": condition[2],
                            "planner": spec["planner_id"],
                            "result": row,
                            "trace": trace,
                        }
                    )
            completed_conditions += 1
            if condition_index % 9 == 0 or condition_index == len(conditions):
                print(
                    f"[evaluate:{partition}] case={config['case_id']} "
                    f"condition={condition_index}/{len(conditions)} "
                    f"global={completed_conditions}/{total_conditions} "
                    f"rows={len(all_rows) + len(case_rows)} "
                    f"seconds={time.monotonic() - started:.1f}",
                    flush=True,
                )
        enriched_case_rows = run_mvp.add_oracle_relative_metrics(case_rows)
        all_rows.extend(enriched_case_rows)
        write_csv(
            output_dir / f"{partition}_checkpoint_results.csv",
            all_rows,
        )
        print(
            f"[evaluate:{partition}] checkpoint case={config['case_id']} "
            f"rows={len(all_rows)}",
            flush=True,
        )
    return all_rows, all_traces


def summarize_horizon_traces(
    trace_packages: list[dict[str, Any]],
) -> dict[str, Any]:
    def aggregate(packages: list[dict[str, Any]]) -> dict[str, Any]:
        reason_counts: Counter[str] = Counter()
        decision_count = 0
        first_step_divergences = 0
        candidate_first_step_divergences = 0
        dominance_substitution_count = 0
        divergent_packages: list[dict[str, Any]] = []
        candidate_divergent_packages: list[dict[str, Any]] = []
        dominance_packages: list[dict[str, Any]] = []
        for package in packages:
            decisions = [
                event["m3star_decision"]
                for event in package.get("trace", [])
                if event.get("event") == "action_taken"
                and "m3star_decision" in event
            ]
            decision_count += len(decisions)
            episode_diverged = False
            episode_candidate_diverged = False
            episode_substituted = False
            for decision_index, decision in enumerate(decisions):
                reason = str(
                    decision.get("horizon_selection_reason", "unknown")
                )
                reason_counts[reason] += 1
                nonmyopic_was_evaluated = reason in {
                    "counterfactual_rollout_shield",
                    "counterfactual_rollout_dominance",
                    "nonmyopic_plan_selected",
                    "nonmyopic_no_positive_plan",
                }
                candidate_diverged = (
                    nonmyopic_was_evaluated
                    and decision.get("myopic_action_id")
                    != decision.get("nonmyopic_action_id")
                )
                diverged = (
                    candidate_diverged
                    and decision.get("selected_action_id")
                    == decision.get("nonmyopic_action_id")
                )
                if candidate_diverged and decision_index == 0:
                    candidate_first_step_divergences += 1
                if diverged and decision_index == 0:
                    first_step_divergences += 1
                episode_candidate_diverged = (
                    episode_candidate_diverged or candidate_diverged
                )
                episode_diverged = episode_diverged or diverged
                substituted = bool(
                    decision.get("dominance_substitution_applied", 0)
                )
                dominance_substitution_count += int(substituted)
                episode_substituted = episode_substituted or substituted
            if episode_candidate_diverged:
                candidate_divergent_packages.append(package)
            if episode_diverged:
                divergent_packages.append(package)
            if episode_substituted:
                dominance_packages.append(package)
        successes = sum(
            int(package.get("result", {}).get("reached_target", 0))
            for package in divergent_packages
        )
        budgets = [
            float(package.get("result", {}).get("budget_used", 0.0))
            for package in divergent_packages
        ]
        return {
            "episode_count": len(packages),
            "decision_count": decision_count,
            "candidate_first_step_divergence_count": (
                candidate_first_step_divergences
            ),
            "candidate_any_step_divergence_count": len(
                candidate_divergent_packages
            ),
            "first_step_divergence_count": first_step_divergences,
            "any_step_divergence_count": len(divergent_packages),
            "dominance_substitution_count": dominance_substitution_count,
            "dominance_substitution_episode_count": len(dominance_packages),
            "dominance_substitution_episode_success_rate": (
                round(
                    sum(
                        int(
                            package.get("result", {}).get(
                                "reached_target",
                                0,
                            )
                        )
                        for package in dominance_packages
                    )
                    / len(dominance_packages),
                    6,
                )
                if dominance_packages
                else None
            ),
            "divergent_episode_success_rate": (
                round(successes / len(divergent_packages), 6)
                if divergent_packages
                else None
            ),
            "divergent_episode_mean_budget_used": (
                round(sum(budgets) / len(budgets), 6)
                if budgets
                else None
            ),
            "horizon_selection_reason_counts": dict(
                sorted(reason_counts.items())
            ),
        }

    by_planner: dict[str, list[dict[str, Any]]] = {}
    for package in trace_packages:
        by_planner.setdefault(str(package["planner"]), []).append(package)
    summary: dict[str, Any] = {}
    for planner, packages in sorted(by_planner.items()):
        by_case = {
            str(case_id): aggregate(
                [
                    package
                    for package in packages
                    if package["case_id"] == case_id
                ]
            )
            for case_id in sorted({package["case_id"] for package in packages})
        }
        summary[planner] = {
            **aggregate(packages),
            "by_case": by_case,
        }
    return summary


def strict_core_gate(
    paired: dict[str, dict[str, Any]],
    paired_by_case: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    overall = {
        baseline: (
            comparison["success_loss_count"] == 0
            and comparison["mean_cost_delta_on_both_success"] is not None
            and comparison["mean_cost_delta_on_both_success"] < 0.0
        )
        for baseline, comparison in paired.items()
    }

    def case_pareto_detail(comparison: dict[str, Any]) -> dict[str, Any]:
        success_losses = int(comparison["success_loss_count"])
        success_gains = int(comparison.get("success_gain_count", 0))
        both_success = int(comparison.get("both_success_count", 0))
        mean_delta = comparison.get("mean_cost_delta_on_both_success")
        total_delta = comparison.get("total_cost_delta_on_both_success")
        if total_delta is None and mean_delta is not None:
            total_delta = float(mean_delta) * both_success
        total_delta = (
            round(float(total_delta), 6) if total_delta is not None else None
        )
        rescue_cost_cap = comparison.get("budget_total")
        rescue_cost_cap = (
            float(rescue_cost_cap)
            if rescue_cost_cap not in (None, "")
            else None
        )
        incremental_cost = (
            max(0.0, total_delta) / success_gains
            if total_delta is not None and success_gains > 0
            else None
        )
        detail = {
            "passed": False,
            "acceptance_mode": None,
            "rejection_reason": None,
            "zero_success_losses": success_losses == 0,
            "success_gain_count": success_gains,
            "both_success_count": both_success,
            "total_cost_delta_on_both_success": total_delta,
            "incremental_cost_per_success_gain": incremental_cost,
            "rescue_cost_cap": rescue_cost_cap,
        }
        if success_losses != 0:
            detail["rejection_reason"] = "success_loss"
            return detail
        if total_delta is None:
            detail["rejection_reason"] = "joint_success_cost_unavailable"
            return detail
        if total_delta <= 0.0:
            detail["passed"] = True
            detail["acceptance_mode"] = "cost_noninferior"
            return detail
        if success_gains == 0:
            detail["rejection_reason"] = "cost_regression_without_success_gain"
            return detail
        if rescue_cost_cap is None or rescue_cost_cap <= 0.0:
            detail["rejection_reason"] = "rescue_cost_cap_unavailable"
            return detail
        if incremental_cost is not None and incremental_cost < (
            rescue_cost_cap - 1e-9
        ):
            detail["passed"] = True
            detail["acceptance_mode"] = "bounded_rescue_cost"
            return detail
        detail["rejection_reason"] = "rescue_cost_cap_not_met"
        return detail

    case_details = {
        baseline: {
            case_id: case_pareto_detail(comparison)
            for case_id, comparison in case_rows.items()
        }
        for baseline, case_rows in paired_by_case.items()
    }
    case_pareto = {
        baseline: {
            case_id: bool(detail["passed"])
            for case_id, detail in case_rows.items()
        }
        for baseline, case_rows in case_details.items()
    }
    return {
        "criterion": (
            "overall_zero_success_losses_and_strictly_lower_paired_cost;_"
            "every_case_zero_success_losses_and_either_noninferior_paired_cost_"
            "or_incremental_rescue_cost_strictly_below_case_budget"
        ),
        "overall_by_baseline": overall,
        "case_pareto_by_baseline": case_pareto,
        "case_pareto_details_by_baseline": case_details,
        "all_core_baselines_pass": (
            all(overall.values())
            and all(
                passed
                for case_rows in case_pareto.values()
                for passed in case_rows.values()
            )
        ),
    }


def summarize_results(
    rows: list[dict[str, Any]],
    traces: list[dict[str, Any]] | None = None,
    *,
    cost_regime: str = "legacy",
    profile_identity: dict[str, Any] | None = None,
    evaluation_role: str = "development",
) -> dict[str, Any]:
    stratified = run_mvp.summarize_stratified(rows)
    paired = {
        baseline: paired_against(rows, CORE_METHOD, baseline)
        for baseline in CORE_BASELINES
    }
    paired_by_case = {
        baseline: casewise_paired_against(rows, CORE_METHOD, baseline)
        for baseline in CORE_BASELINES
    }
    gate = strict_core_gate(paired, paired_by_case)
    gate.update(
        cost_claim_context(
            cost_regime,
            evaluation_role,
            profile_identity,
        )
    )
    summary = {
        **stratified,
        "paired_core_method": paired,
        "paired_core_method_by_case": paired_by_case,
        "legacy_debug_gate": gate,
    }
    if traces is not None:
        summary["horizon_trace_summary"] = summarize_horizon_traces(traces)
    return summary


def _save_models(output_dir: Path, models: dict[str, Any]) -> dict[str, Any]:
    model_dir = output_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    for name in ("transition", "action_value", "action_rank", "xgboost"):
        path = model_dir / f"{name}.json"
        models[name]["booster"].save_model(path)
        files[name] = str(path.relative_to(output_dir))
        if name == "action_value" and "reachability_booster" in models[name]:
            reachability_path = model_dir / "action_reachability.json"
            models[name]["reachability_booster"].save_model(
                reachability_path
            )
            files["action_reachability"] = str(
                reachability_path.relative_to(output_dir)
            )
        if name == "action_value" and "cost_booster" in models[name]:
            cost_path = model_dir / "action_cost.json"
            models[name]["cost_booster"].save_model(cost_path)
            files["action_cost"] = str(cost_path.relative_to(output_dir))
    metadata = {
        name: _public_model_metadata(model)
        for name, model in models.items()
    }
    write_json(model_dir / "model_metadata.json", metadata)
    return {
        "files": files,
        "metadata": metadata,
    }


def _output_hashes(output_dir: Path) -> dict[str, str]:
    return {
        str(path.relative_to(output_dir)).replace("\\", "/"): sha256(path)
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.name != "evaluation_manifest.json"
    }


def run_experiment(
    examples_root: Path,
    real_cases_root: Path,
    output_dir: Path,
    *,
    evaluation_prefixes: tuple[str, ...] = DEVELOPMENT_EVALUATION_PREFIXES,
    evaluation_subset_prefixes: tuple[str, ...] | None = None,
    evaluation_role: str = "development",
    confirm_final_test_once: bool = False,
    partitions: tuple[str, ...] = ("train", "development"),
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
    training_scope: str = "legacy_six",
    max_depth: int = 3,
    boost_rounds: int = 150,
    target_reach_threshold: float = run_m3star.DEFAULT_TARGET_REACH_THRESHOLD,
    max_outcome_nodes: int = 8,
    max_explicit_outcomes: int | None = None,
) -> dict[str, Any]:
    validate_evaluation_scope(
        evaluation_prefixes,
        evaluation_role,
        confirm_final_test_once,
    )
    if evaluation_subset_prefixes is not None and evaluation_role != "development":
        raise ValueError(
            "Evaluation subset filtering is allowed only for reusable development cases"
        )
    unknown_partitions = set(partitions) - {"train", "development"}
    if unknown_partitions or not partitions:
        raise ValueError(f"Invalid evaluation partitions: {partitions}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    train_dirs, evaluation_dirs = select_experiment_case_dirs(
        examples_root,
        real_cases_root,
        evaluation_prefixes,
        training_scope,
    )
    train_cases = run_xgboost.load_cases(
        train_dirs,
        cost_regime,
        cost_profile,
    )
    held_out_cases = run_xgboost.load_cases(
        evaluation_dirs,
        cost_regime,
        cost_profile,
    )
    train_case_ids = [config["case_id"] for config, _, _ in train_cases]
    held_out_case_ids = [
        config["case_id"] for config, _, _ in held_out_cases
    ]
    validate_case_id_partition(train_case_ids, held_out_case_ids)
    evaluation_cases = select_evaluation_subset(
        held_out_cases,
        evaluation_subset_prefixes,
    )
    evaluation_case_ids = [
        config["case_id"] for config, _, _ in evaluation_cases
    ]
    print(
        f"[design] train_cases={len(train_cases)} "
        f"held_out_cases={len(held_out_cases)} "
        f"evaluation_cases={len(evaluation_cases)} methods={len(METHOD_SPECS)} "
        f"cost_regime={cost_regime}",
        flush=True,
    )

    models, dataset = train_models(
        train_dirs,
        train_cases,
        max_depth,
        boost_rounds,
        cost_regime,
        cost_profile,
    )
    model_manifest = _save_models(output_dir, models)
    write_json(
        output_dir / "training_dataset_summary.json",
        {
            **dataset["summary"],
            "train_case_ids": train_case_ids,
            "max_depth": max_depth,
            "case_split_before_mask_generation": True,
        },
    )

    partition_cases = {
        "train": train_cases,
        "development": evaluation_cases,
    }
    profile_identity = cost_profile_identity(cost_regime, cost_profile)
    partition_reports: dict[str, Any] = {}
    for partition in partitions:
        rows, traces = evaluate_partition(
            partition,
            partition_cases[partition],
            models,
            output_dir,
            target_reach_threshold,
            max_outcome_nodes,
            max_explicit_outcomes,
        )
        summary = summarize_results(
            rows,
            traces,
            cost_regime=cost_regime,
            profile_identity=profile_identity,
            evaluation_role=evaluation_role,
        )
        write_csv(output_dir / f"{partition}_policy_results.csv", rows)
        write_json_gzip(
            output_dir / f"{partition}_m3star_traces.json.gz",
            traces,
        )
        write_json(output_dir / f"{partition}_summary.json", summary)
        partition_reports[partition] = summary

    report = {
        "experiment_id": (
            "project05-m3star-post-selection-dominance-method-development-v0.8"
        ),
        "status": "method_development_only",
        "paper_or_patent_updated": False,
        "formal_cost_claim_allowed": False,
        "cost_regime": cost_regime,
        "cost_profile_identity": profile_identity,
        "training_scope": training_scope,
        "train_case_ids": train_case_ids,
        "held_out_case_ids": held_out_case_ids,
        "evaluation_case_ids": evaluation_case_ids,
        "evaluation_subset_prefixes": (
            list(evaluation_subset_prefixes)
            if evaluation_subset_prefixes is not None
            else None
        ),
        "evaluation_role": evaluation_role,
        "partitions": list(partitions),
        "method_specs": list(METHOD_SPECS),
        "configuration": {
            "max_depth": max_depth,
            "boost_rounds": boost_rounds,
            "target_reach_threshold": target_reach_threshold,
            "max_outcome_nodes": max_outcome_nodes,
            "max_explicit_outcomes": max_explicit_outcomes,
        },
        "runtime_contract": runtime_contract_metadata(),
        "training_dataset": dataset["summary"],
        "models": model_manifest,
        "partition_reports": partition_reports,
        "final_blind_gate": {
            "c13_plus_used": any(
                (_case_number(prefix) or 0) >= 13
                for prefix in evaluation_prefixes
            ),
            "one_shot_confirmation": confirm_final_test_once,
        },
    }
    write_json(output_dir / "experiment_report.json", report)
    manifest = {
        "runner_sha256": sha256(Path(__file__)),
        "run_m3star_sha256": sha256(Path(__file__).with_name("run_m3star.py")),
        "run_xgboost_sha256": sha256(Path(__file__).with_name("run_xgboost.py")),
        "run_m3b_sha256": sha256(Path(__file__).with_name("run_m3b.py")),
        "run_mvp_sha256": sha256(Path(__file__).with_name("run_mvp.py")),
        "runtime_contract": runtime_contract_metadata(),
        "output_sha256": _output_hashes(output_dir),
    }
    write_json(output_dir / "evaluation_manifest.json", manifest)
    print(
        "[complete] "
        f"output={output_dir} partitions={','.join(partitions)}",
        flush=True,
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the M3* dual-head method-development experiment."
    )
    parser.add_argument("--examples-root", type=Path, required=True)
    parser.add_argument("--real-cases-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--evaluation-prefixes",
        nargs="+",
        default=list(DEVELOPMENT_EVALUATION_PREFIXES),
    )
    parser.add_argument(
        "--evaluation-subset-prefixes",
        nargs="+",
        help=(
            "Run only this subset after the frozen held-out split is formed; "
            "development role only"
        ),
    )
    parser.add_argument(
        "--evaluation-role",
        choices=("development", "final_blind"),
        default="development",
    )
    parser.add_argument("--confirm-final-test-once", action="store_true")
    parser.add_argument(
        "--partition",
        choices=("train", "development", "both"),
        default="both",
    )
    parser.add_argument(
        "--cost-regime",
        choices=run_mvp.COST_REGIMES,
        default="legacy",
    )
    parser.add_argument("--cost-profile", type=Path)
    parser.add_argument(
        "--training-scope",
        choices=("legacy_six", "real_only_three"),
        default="legacy_six",
    )
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--boost-rounds", type=int, default=150)
    parser.add_argument(
        "--target-reach-threshold",
        type=float,
        default=run_m3star.DEFAULT_TARGET_REACH_THRESHOLD,
    )
    parser.add_argument("--max-outcome-nodes", type=int, default=8)
    parser.add_argument("--max-explicit-outcomes", type=int)
    args = parser.parse_args()
    if args.cost_regime in {"rubric", "measured"} and args.cost_profile is None:
        parser.error(f"--cost-profile is required for {args.cost_regime}")
    if args.cost_regime in {"legacy", "uniform"} and args.cost_profile is not None:
        parser.error(f"--cost-profile is invalid for {args.cost_regime}")
    cost_profile = (
        run_mvp.load_cost_profile(args.cost_profile)
        if args.cost_profile is not None
        else None
    )
    partitions = (
        ("train", "development")
        if args.partition == "both"
        else (args.partition,)
    )
    report = run_experiment(
        args.examples_root,
        args.real_cases_root,
        args.output_dir,
        evaluation_prefixes=tuple(args.evaluation_prefixes),
        evaluation_subset_prefixes=(
            tuple(args.evaluation_subset_prefixes)
            if args.evaluation_subset_prefixes is not None
            else None
        ),
        evaluation_role=args.evaluation_role,
        confirm_final_test_once=args.confirm_final_test_once,
        partitions=partitions,
        cost_regime=args.cost_regime,
        cost_profile=cost_profile,
        training_scope=args.training_scope,
        max_depth=args.max_depth,
        boost_rounds=args.boost_rounds,
        target_reach_threshold=args.target_reach_threshold,
        max_outcome_nodes=args.max_outcome_nodes,
        max_explicit_outcomes=args.max_explicit_outcomes,
    )
    print(
        json.dumps(
            {
                "experiment_id": report["experiment_id"],
                "partitions": report["partitions"],
                "output_dir": str(args.output_dir.resolve()),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
