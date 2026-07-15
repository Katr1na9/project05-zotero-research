#!/usr/bin/env python3
"""Train and replay the frozen Project05 XGBoost action-value baseline."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import xgboost as xgb


def load_script(name: str) -> Any:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


run_m3b = load_script("run_m3b")
run_mvp = run_m3b.run_mvp
runtime_adapter = load_script("planner_runtime_adapter")
RUNTIME_CONTRACT = runtime_adapter.load_contract()
FEATURE_COLUMNS = run_m3b.FEATURE_COLUMNS
LABEL_COLUMNS = [
    "label_resolves_critical_gap_node",
    "label_yield_positive",
    "label_reaches_target_after_action",
]
PRIMARY_LABEL = "label_resolves_critical_gap_node"
FROZEN_PARAMS: dict[str, Any] = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "max_depth": 3,
    "eta": 0.05,
    "min_child_weight": 1.0,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "lambda": 1.0,
    "alpha": 0.0,
    "seed": 11,
    "nthread": 1,
}
FROZEN_BOOST_ROUNDS = 150
FROZEN_COST_PENALTY = 0.1
DEFAULT_TEST_PREFIXES = ("C07-", "C08-", "C09-")
C07_C10_TEST_PREFIXES = (*DEFAULT_TEST_PREFIXES, "C10-")


def matrix(
    rows: list[dict[str, Any]],
    feature_columns: list[str],
    label_column: str | None = None,
) -> xgb.DMatrix:
    values = np.asarray(
        [[float(row[column]) for column in feature_columns] for row in rows],
        dtype=np.float32,
    )
    labels = None
    if label_column is not None:
        labels = np.asarray([int(row[label_column]) for row in rows], dtype=np.float32)
    return xgb.DMatrix(values, label=labels, feature_names=feature_columns)


def train_xgboost(
    rows: list[dict[str, Any]],
    feature_columns: list[str],
    label_column: str,
    *,
    params: dict[str, Any] | None = None,
    boost_rounds: int = FROZEN_BOOST_ROUNDS,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("Cannot train XGBoost on an empty dataset")
    labels = {int(row[label_column]) for row in rows}
    if labels != {0, 1}:
        raise ValueError(
            f"XGBoost label {label_column} requires both classes; found {sorted(labels)}"
        )
    frozen = dict(FROZEN_PARAMS if params is None else params)
    booster = xgb.train(
        frozen,
        matrix(rows, feature_columns, label_column),
        num_boost_round=boost_rounds,
    )
    return {
        "booster": booster,
        "feature_columns": list(feature_columns),
        "label_column": label_column,
        "params": frozen,
        "boost_rounds": int(boost_rounds),
    }


def predict_probabilities(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[float]:
    if not rows:
        return []
    predictions = model["booster"].predict(
        matrix(rows, model["feature_columns"])
    )
    return [float(value) for value in predictions]


def predict_probability(model: dict[str, Any], row: dict[str, Any]) -> float:
    return predict_probabilities(model, [row])[0]


def top1_label_hit_rate(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
    label_column: str,
) -> float | None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["group_id"]), []).append(row)
    if not grouped:
        return None
    hits = 0
    for group_rows in grouped.values():
        probabilities = predict_probabilities(model, group_rows)
        selected_index = max(
            range(len(group_rows)),
            key=lambda index: (
                probabilities[index],
                -float(group_rows[index].get("cost", 0.0)),
                str(group_rows[index]["action_id"]),
            ),
        )
        hits += int(group_rows[selected_index][label_column] == 1)
    return hits / len(grouped)


def evaluate_model(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
    label_column: str,
) -> dict[str, Any]:
    labels = [int(row[label_column]) for row in rows]
    probabilities = predict_probabilities(model, rows)
    predictions = [int(probability >= 0.5) for probability in probabilities]
    accuracy = (
        sum(int(prediction == label) for prediction, label in zip(predictions, labels))
        / len(labels)
        if labels
        else None
    )
    return {
        "rows": len(rows),
        "positive_rate": sum(labels) / len(labels) if labels else None,
        "accuracy_at_0_5": accuracy,
        "brier_score": run_m3b.brier_score(probabilities, labels),
        "auroc": run_m3b.auroc(probabilities, labels),
        "average_precision": run_m3b.average_precision(probabilities, labels),
        "top1_label_hit_rate": top1_label_hit_rate(model, rows, label_column),
    }


def add_predictions(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    probabilities = predict_probabilities(model, rows)
    return [
        {**row, "xgboost_probability": round(probability, 6)}
        for row, probability in zip(rows, probabilities)
    ]


def xgboost_action_score(
    config: dict[str, Any],
    state: dict[str, Any],
    action: dict[str, Any],
    model: dict[str, Any],
    cost_penalty: float,
) -> tuple[float, float]:
    if run_mvp.is_stop_action(action):
        return 0.0, 0.0
    features = runtime_adapter.build_ml_feature_row(
        config,
        state,
        action,
        run_m3b.feature_row,
        FEATURE_COLUMNS,
        RUNTIME_CONTRACT,
    )
    probability = predict_probability(model, features)
    utility = probability - cost_penalty * float(action["cost"])
    return utility, probability


def select_xgboost_action(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    model: dict[str, Any],
    cost_penalty: float,
) -> dict[str, Any] | None:
    view = runtime_adapter.build_runtime_view(
        config, state, actions, RUNTIME_CONTRACT
    )
    config = view["config"]
    state = view["state"]
    actions = view["actions"]
    candidates = run_mvp.available_actions(
        actions,
        state.get("actions_taken", []),
        state["budget"]["budget_remaining"],
    )
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda action: (
            *xgboost_action_score(config, state, action, model, cost_penalty),
            int(run_mvp.is_stop_action(action)),
            -float(action["cost"]),
            action["action_id"],
        ),
    )


def logistic_action_score(
    config: dict[str, Any],
    state: dict[str, Any],
    action: dict[str, Any],
    model: dict[str, Any],
    cost_penalty: float,
) -> tuple[float, float]:
    if run_mvp.is_stop_action(action):
        return 0.0, 0.0
    features = runtime_adapter.build_ml_feature_row(
        config,
        state,
        action,
        run_m3b.feature_row,
        FEATURE_COLUMNS,
        RUNTIME_CONTRACT,
    )
    probability = run_m3b.predict_probability(model, features)
    utility = probability - cost_penalty * float(action["cost"])
    return utility, probability


def select_logistic_action(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    model: dict[str, Any],
    cost_penalty: float,
) -> dict[str, Any] | None:
    view = runtime_adapter.build_runtime_view(
        config, state, actions, RUNTIME_CONTRACT
    )
    config = view["config"]
    state = view["state"]
    actions = view["actions"]
    candidates = run_mvp.available_actions(
        actions,
        state.get("actions_taken", []),
        state["budget"]["budget_remaining"],
    )
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda action: (
            *logistic_action_score(config, state, action, model, cost_penalty),
            int(run_mvp.is_stop_action(action)),
            -float(action["cost"]),
            action["action_id"],
        ),
    )


def run_xgboost_episode(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    mask_strategy: str,
    mask_intensity: float,
    seed: int,
    model: dict[str, Any],
    cost_penalty: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actions = run_mvp.ensure_stop_action(config, actions)
    result, trace = run_mvp.run_episode(
        config,
        claims,
        actions,
        mask_strategy,
        mask_intensity,
        seed,
        "project05_xgboost_policy",
        action_selector=lambda episode_config, state, episode_actions: select_xgboost_action(
            episode_config,
            state,
            episode_actions,
            model,
            cost_penalty,
        ),
    )
    actions_by_id = run_mvp.action_by_id(actions)
    for prior_event, event in zip(trace, trace[1:]):
        if event.get("event") != "action_taken":
            continue
        action = actions_by_id[event["action_id"]]
        utility, probability = xgboost_action_score(
            config,
            prior_event["state"],
            action,
            model,
            cost_penalty,
        )
        event["xgboost_probability"] = round(probability, 6)
        event["xgboost_utility"] = round(utility, 6)
    return result, trace


def run_logistic_episode(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    mask_strategy: str,
    mask_intensity: float,
    seed: int,
    model: dict[str, Any],
    cost_penalty: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actions = run_mvp.ensure_stop_action(config, actions)
    return run_mvp.run_episode(
        config,
        claims,
        actions,
        mask_strategy,
        mask_intensity,
        seed,
        "project05_m3b_policy",
        action_selector=lambda episode_config, state, episode_actions: select_logistic_action(
            episode_config,
            state,
            episode_actions,
            model,
            cost_penalty,
        ),
    )


def selected_case_dirs(
    examples_root: Path,
    real_cases_root: Path,
    include_c10: bool = False,
    test_prefixes: tuple[str, ...] | None = None,
) -> tuple[list[Path], list[Path]]:
    if include_c10 and test_prefixes is not None:
        raise ValueError("--include-c10 and explicit test_prefixes are mutually exclusive")
    examples = run_mvp.discover_case_dirs(examples_root)
    real = run_mvp.discover_case_dirs(real_cases_root)
    train = examples + [
        path for path in real if path.name.startswith(("C04-", "C05-", "C06-"))
    ]
    selected_prefixes = (
        C07_C10_TEST_PREFIXES
        if include_c10
        else tuple(test_prefixes or DEFAULT_TEST_PREFIXES)
    )
    if not selected_prefixes:
        raise ValueError("At least one test case prefix is required")
    if len(set(selected_prefixes)) != len(selected_prefixes):
        raise ValueError(f"Duplicate test case prefixes: {selected_prefixes}")
    test = [path for path in real if path.name.startswith(selected_prefixes)]
    expected_test_cases = len(selected_prefixes)
    if len(train) != 6 or len(test) != expected_test_cases:
        raise ValueError(
            f"Expected 6 train and {expected_test_cases} test cases, "
            f"found {len(train)} and {len(test)} for prefixes {selected_prefixes}"
        )
    return train, test


def load_cases(
    case_dirs: list[Path],
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]]:
    cases = []
    for case_dir in case_dirs:
        config = run_m3b.load_json(case_dir / "case_config.json")
        claims = run_m3b.load_json(case_dir / "evidence_claims.json")
        actions = run_m3b.load_json(case_dir / "acquisition_actions.json")
        actions, _ = run_mvp.apply_cost_regime(
            actions, config["case_id"], cost_regime, cost_profile
        )
        cases.append((config, claims, actions))
    return cases


def build_rows_for_cost_regime(
    case_dirs: list[Path],
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for config, claims, actions in load_cases(case_dirs, cost_regime, cost_profile):
        rows.extend(run_m3b.build_case_rows(config, claims, actions))
    return rows


def cost_profile_identities(
    case_dirs: list[Path],
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> dict[str, dict[str, str]]:
    identities: dict[str, dict[str, str]] = {}
    for case_dir in case_dirs:
        config = run_m3b.load_json(case_dir / "case_config.json")
        actions = run_m3b.load_json(case_dir / "acquisition_actions.json")
        actions, metadata = run_mvp.apply_cost_regime(
            actions, config["case_id"], cost_regime, cost_profile
        )
        identities[config["case_id"]] = run_mvp.cost_profile_identity(
            actions, config["case_id"], cost_regime, metadata
        )
    return identities


def evaluate_policy(
    cases: list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]],
    xgboost_model: dict[str, Any],
    logistic_model: dict[str, Any],
    cost_penalty: float,
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    baseline_planners = [
        "coverage_greedy",
        "project05_m2",
        "project05_m3a_gap_compat",
        "oracle_optimal",
    ]
    for config, claims, actions in cases:
        _, cost_metadata = run_mvp.apply_cost_regime(
            actions,
            config["case_id"],
            cost_regime,
            cost_profile,
        )
        for strategy, intensity, seed in run_mvp.experiment_conditions(config):
            xgb_row, xgb_trace = run_xgboost_episode(
                config,
                claims,
                actions,
                strategy,
                intensity,
                seed,
                xgboost_model,
                cost_penalty,
            )
            if cost_metadata is not None:
                xgb_row.update(cost_metadata)
            rows.append(xgb_row)
            traces.append(
                {
                    "run_id": run_mvp.make_run_id(
                        config["case_id"],
                        strategy,
                        intensity,
                        seed,
                        "project05_xgboost_policy",
                    ),
                    "result": xgb_row,
                    "trace": xgb_trace,
                }
            )
            logistic_row, _ = run_logistic_episode(
                config,
                claims,
                actions,
                strategy,
                intensity,
                seed,
                logistic_model,
                cost_penalty,
            )
            if cost_metadata is not None:
                logistic_row.update(cost_metadata)
            rows.append(logistic_row)
            for planner in baseline_planners:
                row, _ = run_mvp.run_episode(
                    config,
                    claims,
                    actions,
                    strategy,
                    intensity,
                    seed,
                    planner,
                )
                if cost_metadata is not None:
                    row.update(cost_metadata)
                rows.append(row)
    return run_mvp.add_oracle_relative_metrics(rows), traces


def public_model_metadata(model: dict[str, Any]) -> dict[str, Any]:
    booster: xgb.Booster = model["booster"]
    return {
        "feature_columns": model["feature_columns"],
        "label_column": model["label_column"],
        "params": model["params"],
        "boost_rounds": model["boost_rounds"],
        "feature_importance_gain": {
            key: float(value)
            for key, value in booster.get_score(importance_type="gain").items()
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_json_gzip(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
    # mtime=0 keeps the gzip bytes reproducible across runs.
    path.write_bytes(gzip.compress(payload, mtime=0))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_empty_output(path: Path) -> None:
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise FileExistsError(
            f"XGBoost output must be new or empty; refusing to overwrite {path}"
        )
    path.mkdir(parents=True, exist_ok=True)


def embedded_cost_profiles(case_dirs: list[Path]) -> dict[str, dict[str, str]]:
    return cost_profile_identities(case_dirs, "legacy")


def evaluation_manifest(
    train_dirs: list[Path],
    test_dirs: list[Path],
    experiment_id: str,
    output_hashes: dict[str, str],
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    train_ids = [
        run_m3b.load_json(path / "case_config.json")["case_id"]
        for path in train_dirs
    ]
    test_ids = [
        run_m3b.load_json(path / "case_config.json")["case_id"]
        for path in test_dirs
    ]
    if set(train_ids) & set(test_ids):
        raise ValueError("XGBoost training and test cases must be disjoint")
    all_dirs = train_dirs + test_dirs
    return {
        "experiment_id": experiment_id,
        "train_case_ids": train_ids,
        "test_case_ids": test_ids,
        "independent_test_case_count": len(test_ids),
        "training_test_overlap": [],
        "statistical_unit": RUNTIME_CONTRACT["document"]["statistical_unit"],
        "feature_contract": {
            "columns": list(FEATURE_COLUMNS),
            "hidden_outcome_fields_excluded": True,
            "target_case_outcome_prior_excluded": True,
        },
        "cost_regime": cost_regime,
        "cost_profile_identity_by_case": cost_profile_identities(
            test_dirs, cost_regime, cost_profile
        ),
        "training_cost_profile_identity_by_case": cost_profile_identities(
            train_dirs, cost_regime, cost_profile
        ),
        "endpoint_boundary": {
            **runtime_adapter.contract_metadata(RUNTIME_CONTRACT),
            "hidden_recovery_invariance_tested": True,
            "runtime_labels_visible": False,
            "realized_outcomes_visible": False,
        },
        "input_sha256": {
            (case_dir / filename).resolve().relative_to(
                Path(__file__).resolve().parents[2]
            ).as_posix(): sha256(
                (case_dir / filename).resolve()
            )
            for case_dir in all_dirs
            for filename in run_mvp.CASE_FILENAMES
        },
        "output_sha256": dict(sorted(output_hashes.items())),
        "runner_sha256": sha256(Path(__file__)),
        "run_m3b_sha256": sha256(Path(__file__).with_name("run_m3b.py")),
        "run_mvp_sha256": sha256(Path(__file__).with_name("run_mvp.py")),
        "endpoint_adapter_sha256": sha256(
            Path(__file__).with_name("planner_runtime_adapter.py")
        ),
        "external_actor_accuracy": None,
        "all_experiments_complete": False,
        "paper_or_patent_gate": "closed_until_human_and_operational_gates_are_satisfied",
        "paper_or_patent_updated": False,
    }


def run_experiment(
    examples_root: Path,
    real_cases_root: Path,
    output_dir: Path,
    include_c10: bool = False,
    test_prefixes: tuple[str, ...] | None = None,
    experiment_id: str | None = None,
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    train_dirs, test_dirs = selected_case_dirs(
        examples_root,
        real_cases_root,
        include_c10=include_c10,
        test_prefixes=test_prefixes,
    )
    require_empty_output(output_dir)
    train_rows = build_rows_for_cost_regime(train_dirs, cost_regime, cost_profile)
    test_rows = build_rows_for_cost_regime(test_dirs, cost_regime, cost_profile)

    models: dict[str, dict[str, Any]] = {}
    classification: dict[str, Any] = {}
    for label in LABEL_COLUMNS:
        model = train_xgboost(train_rows, FEATURE_COLUMNS, label)
        models[label] = model
        logistic = run_m3b.train_logistic_baseline(train_rows, FEATURE_COLUMNS, label)
        model_path = output_dir / f"xgboost_{label}.json"
        model["booster"].save_model(model_path)
        classification[label] = {
            "xgboost": {
                "train": evaluate_model(model, train_rows, label),
                "test": evaluate_model(model, test_rows, label),
            },
            "logistic": {
                "train": run_m3b.evaluate_model(logistic, train_rows, label),
                "test": run_m3b.evaluate_model(logistic, test_rows, label),
            },
            "model": public_model_metadata(model),
            "model_file": model_path.name,
            "model_sha256": sha256(model_path),
        }

    primary_model = models[PRIMARY_LABEL]
    primary_logistic = run_m3b.train_logistic_baseline(
        train_rows,
        FEATURE_COLUMNS,
        PRIMARY_LABEL,
    )
    policy_rows, policy_traces = evaluate_policy(
        load_cases(test_dirs, cost_regime, cost_profile),
        primary_model,
        primary_logistic,
        FROZEN_COST_PENALTY,
        cost_regime,
        cost_profile,
    )
    if experiment_id is None:
        if include_c10:
            experiment_id = "project05-xgboost-action-value-v0.2-c10"
        elif test_prefixes is not None:
            suffix = "-".join(prefix.rstrip("-").casefold() for prefix in test_prefixes)
            experiment_id = f"project05-xgboost-{suffix}-frozen-transfer-v0.1"
        else:
            experiment_id = "project05-xgboost-action-value-v0.1"
    report = {
        "experiment_id": experiment_id,
        "xgboost_version": xgb.__version__,
        "numpy_version": np.__version__,
        "train_case_ids": [
            run_m3b.load_json(path / "case_config.json")["case_id"]
            for path in train_dirs
        ],
        "test_case_ids": [
            run_m3b.load_json(path / "case_config.json")["case_id"]
            for path in test_dirs
        ],
        "train_row_count": len(train_rows),
        "test_row_count": len(test_rows),
        "feature_columns": FEATURE_COLUMNS,
        "primary_label": PRIMARY_LABEL,
        "cost_penalty": FROZEN_COST_PENALTY,
        "cost_regime": cost_regime,
        "classification": classification,
        "policy_summary": run_mvp.summarize_stratified(policy_rows),
    }
    predictions_path = output_dir / "xgboost_test_predictions.csv"
    policy_path = output_dir / "xgboost_policy_results.csv"
    traces_path = output_dir / "xgboost_policy_traces.json.gz"
    summary_path = output_dir / "xgboost_experiment_summary.json"
    manifest_path = output_dir / "evaluation_manifest.json"
    write_csv(predictions_path, add_predictions(primary_model, test_rows))
    write_csv(policy_path, policy_rows)
    write_json_gzip(traces_path, policy_traces)
    write_json(summary_path, report)
    output_hashes = {
        path.name: sha256(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path != manifest_path
    }
    write_json(
        manifest_path,
        evaluation_manifest(
            train_dirs,
            test_dirs,
            experiment_id,
            output_hashes,
            cost_regime,
            cost_profile,
        ),
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen Project05 XGBoost action-value experiment."
    )
    parser.add_argument("--examples-root", type=Path, required=True)
    parser.add_argument("--real-cases-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--include-c10",
        action="store_true",
        help="Add parameter-locked C10 without changing C01-C06 training.",
    )
    parser.add_argument(
        "--test-prefixes",
        nargs="+",
        help=(
            "Explicit real-case directory prefixes to evaluate while retaining "
            "C01-C06 training; mutually exclusive with --include-c10."
        ),
    )
    parser.add_argument(
        "--experiment-id",
        help="Explicit frozen-transfer experiment identifier for the output report.",
    )
    parser.add_argument(
        "--cost-regime",
        choices=run_mvp.COST_REGIMES,
        default="legacy",
        help="Embedded legacy, built-in uniform, or frozen rubric/measured costs.",
    )
    parser.add_argument(
        "--cost-profile",
        type=Path,
        help="Frozen profile required for rubric/measured cost regimes.",
    )
    args = parser.parse_args()
    if args.cost_regime in {"rubric", "measured"} and args.cost_profile is None:
        parser.error(f"--cost-profile is required for --cost-regime {args.cost_regime}")
    if args.cost_regime in {"legacy", "uniform"} and args.cost_profile is not None:
        parser.error(f"--cost-profile is not valid for --cost-regime {args.cost_regime}")
    cost_profile = (
        run_mvp.load_cost_profile(args.cost_profile)
        if args.cost_profile is not None
        else None
    )
    report = run_experiment(
        args.examples_root,
        args.real_cases_root,
        args.output_dir,
        include_c10=args.include_c10,
        test_prefixes=tuple(args.test_prefixes) if args.test_prefixes else None,
        experiment_id=args.experiment_id,
        cost_regime=args.cost_regime,
        cost_profile=cost_profile,
    )
    print(
        json.dumps(
            {
                "train_rows": report["train_row_count"],
                "test_rows": report["test_row_count"],
                "policy_summary": report["policy_summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
