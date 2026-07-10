"""Build and evaluate the Project05 M3b counterfactual utility baseline.

M3b turns the M3a action-gap representation into supervised state-action
examples. Features are public state/action descriptors; labels are computed
from counterfactual recovery outcomes for offline training and evaluation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import importlib.util


MVP_PATH = Path(__file__).with_name("run_mvp.py")
MVP_SPEC = importlib.util.spec_from_file_location("run_mvp", MVP_PATH)
run_mvp = importlib.util.module_from_spec(MVP_SPEC)
assert MVP_SPEC.loader is not None
MVP_SPEC.loader.exec_module(run_mvp)


FEATURE_COLUMNS = [
    "cost",
    "budget_remaining",
    "cti_node_coverage",
    "cti_edge_coverage",
    "critical_gap_count",
    "intended_node_count",
    "intended_gap_overlap_count",
    "intended_critical_gap_overlap_count",
    "intended_gap_precision",
    "intended_gap_recall",
    "expected_granularity_gain",
    "expected_uncertainty_reduction",
    "expected_over_attribution_risk_reduction",
    "expected_conflict_resolution",
    "expected_coverage_delta",
]
LABEL_COLUMNS = [
    "label_yield_positive",
    "label_resolves_any_gap_node",
    "label_resolves_critical_gap_node",
    "label_reaches_target_after_action",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty CSV")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def resolve_case_dirs(root: Path) -> list[Path]:
    if all((root / filename).is_file() for filename in run_mvp.CASE_FILENAMES):
        return [root]
    return run_mvp.discover_case_dirs(root)


def condition_group_id(
    case_id: str,
    mask_strategy: str,
    mask_intensity: float,
    seed: int,
) -> str:
    return f"{case_id}|{mask_strategy}|{float(mask_intensity):.3f}|{seed}"


def feature_row(
    config: dict[str, Any],
    state: dict[str, Any],
    action: dict[str, Any],
) -> dict[str, float]:
    coverage = state["coverage"]
    intended_nodes = set(action.get("intended_cti_node_ids", []))
    unmatched_nodes = set(state.get("unmatched_cti_node_ids", []))
    critical_nodes = run_mvp.critical_cti_node_ids(config)
    intended_gap_overlap = intended_nodes & unmatched_nodes
    intended_critical_gap_overlap = intended_gap_overlap & critical_nodes

    return {
        "cost": float(action["cost"]),
        "budget_remaining": float(state["budget"]["budget_remaining"]),
        "cti_node_coverage": float(coverage["cti_node_coverage"]),
        "cti_edge_coverage": float(coverage["cti_edge_coverage"]),
        "critical_gap_count": float(coverage["critical_gap_count"]),
        "intended_node_count": float(len(intended_nodes)),
        "intended_gap_overlap_count": float(len(intended_gap_overlap)),
        "intended_critical_gap_overlap_count": float(
            len(intended_critical_gap_overlap)
        ),
        "intended_gap_precision": float(
            len(intended_gap_overlap) / max(1, len(intended_nodes))
        ),
        "intended_gap_recall": float(
            len(intended_gap_overlap) / max(1, len(unmatched_nodes))
        ),
        "expected_granularity_gain": run_mvp.expected_effect(
            action,
            "expected_granularity_gain",
        ),
        "expected_uncertainty_reduction": run_mvp.expected_effect(
            action,
            "expected_uncertainty_reduction",
        ),
        "expected_over_attribution_risk_reduction": run_mvp.expected_effect(
            action,
            "expected_over_attribution_risk_reduction",
        ),
        "expected_conflict_resolution": run_mvp.expected_effect(
            action,
            "expected_conflict_resolution",
        ),
        "expected_coverage_delta": run_mvp.expected_effect(
            action,
            "expected_coverage_delta",
        ),
    }


def counterfactual_labels(
    config: dict[str, Any],
    visible_ids: set[str],
    hidden_ids: set[str],
    action: dict[str, Any],
) -> dict[str, int]:
    before_nodes = run_mvp.covered_node_ids(config, visible_ids)
    recovered = run_mvp.recoverable_hidden(action, hidden_ids)
    after_visible = visible_ids | recovered
    after_nodes = run_mvp.covered_node_ids(config, after_visible)
    resolved_nodes = (
        after_nodes
        - before_nodes
    ) & {
        node["node_id"]
        for node in config["cti_nodes"]
        if node["node_id"] not in before_nodes
    }
    critical_resolved = resolved_nodes & run_mvp.critical_cti_node_ids(config)
    after_granularity = run_mvp.supportable_granularity(config, after_visible)

    return {
        "label_yield_positive": int(bool(recovered)),
        "label_resolves_any_gap_node": int(bool(resolved_nodes)),
        "label_resolves_critical_gap_node": int(bool(critical_resolved)),
        "label_reaches_target_after_action": int(
            run_mvp.granularity_index(config, after_granularity)
            >= run_mvp.granularity_index(config, config["target_granularity"])
        ),
        "recovered_claim_count": len(recovered),
        "resolved_node_count": len(resolved_nodes),
        "resolved_critical_node_count": len(critical_resolved),
        "after_granularity": after_granularity,
    }


def build_case_rows(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_ids = {claim["claim_id"] for claim in claims}

    for mask_strategy, mask_intensity, seed in run_mvp.experiment_conditions(config):
        hidden_ids = run_mvp.build_hidden_claims(
            config,
            claims,
            mask_strategy,
            seed,
            mask_intensity,
        )
        visible_ids = all_ids - hidden_ids
        group_id = condition_group_id(
            config["case_id"],
            mask_strategy,
            mask_intensity,
            seed,
        )
        state = run_mvp.build_state(
            config,
            claims,
            actions,
            f"{group_id}|m3b",
            0,
            mask_strategy,
            mask_intensity,
            seed,
            visible_ids,
            hidden_ids,
            set(),
            [],
            0.0,
        )
        for action in run_mvp.available_actions(
            actions,
            [],
            state["budget"]["budget_remaining"],
        ):
            row = {
                "group_id": group_id,
                "case_id": config["case_id"],
                "mask_strategy": mask_strategy,
                "mask_intensity": mask_intensity,
                "seed": seed,
                "action_id": action["action_id"],
                "initial_granularity": state["supportable_granularity"],
                "target_granularity": config["target_granularity"],
            }
            row.update(feature_row(config, state, action))
            row.update(counterfactual_labels(config, visible_ids, hidden_ids, action))
            rows.append(row)

    return rows


def build_rows_for_case_dirs(case_dirs: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        rows.extend(
            build_case_rows(
                load_json(case_dir / "case_config.json"),
                load_json(case_dir / "evidence_claims.json"),
                load_json(case_dir / "acquisition_actions.json"),
            )
        )
    return rows


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def train_logistic_baseline(
    rows: list[dict[str, Any]],
    feature_columns: list[str],
    label_column: str,
    epochs: int = 800,
    learning_rate: float = 0.1,
    l2: float = 0.01,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("Cannot train on an empty dataset")

    means = {
        column: sum(float(row[column]) for row in rows) / len(rows)
        for column in feature_columns
    }
    scales = {}
    for column in feature_columns:
        variance = (
            sum((float(row[column]) - means[column]) ** 2 for row in rows)
            / len(rows)
        )
        scales[column] = math.sqrt(variance) or 1.0

    weights = [0.0 for _ in feature_columns]
    bias = 0.0
    n = float(len(rows))

    for _ in range(epochs):
        grad_w = [0.0 for _ in feature_columns]
        grad_b = 0.0
        for row in rows:
            xs = [
                (float(row[column]) - means[column]) / scales[column]
                for column in feature_columns
            ]
            y = float(row[label_column])
            pred = sigmoid(bias + sum(w * x for w, x in zip(weights, xs)))
            error = pred - y
            grad_b += error
            for index, x in enumerate(xs):
                grad_w[index] += error * x

        bias -= learning_rate * grad_b / n
        for index, weight in enumerate(weights):
            regularized = (grad_w[index] / n) + l2 * weight
            weights[index] -= learning_rate * regularized

    return {
        "feature_columns": feature_columns[:],
        "label_column": label_column,
        "means": means,
        "scales": scales,
        "weights": weights,
        "bias": bias,
    }


def predict_probability(model: dict[str, Any], row: dict[str, Any]) -> float:
    score = float(model["bias"])
    for column, weight in zip(model["feature_columns"], model["weights"]):
        x = (float(row[column]) - model["means"][column]) / model["scales"][column]
        score += float(weight) * x
    return sigmoid(score)


def brier_score(probs: list[float], labels: list[int]) -> float | None:
    if not probs:
        return None
    return sum((prob - label) ** 2 for prob, label in zip(probs, labels)) / len(probs)


def auroc(probs: list[float], labels: list[int]) -> float | None:
    pos = [prob for prob, label in zip(probs, labels) if label == 1]
    neg = [prob for prob, label in zip(probs, labels) if label == 0]
    if not pos or not neg:
        return None
    wins = 0.0
    for pos_prob in pos:
        for neg_prob in neg:
            if pos_prob > neg_prob:
                wins += 1.0
            elif pos_prob == neg_prob:
                wins += 0.5
    return wins / (len(pos) * len(neg))


def average_precision(probs: list[float], labels: list[int]) -> float | None:
    positives = sum(labels)
    if positives == 0:
        return None
    ranked = sorted(zip(probs, labels), key=lambda item: item[0], reverse=True)
    hit_count = 0
    precision_sum = 0.0
    for rank, (_, label) in enumerate(ranked, start=1):
        if label == 1:
            hit_count += 1
            precision_sum += hit_count / rank
    return precision_sum / positives


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
        selected = max(
            group_rows,
            key=lambda row: (
                predict_probability(model, row),
                -float(row.get("cost", 0.0)),
                str(row["action_id"]),
            ),
        )
        hits += int(selected[label_column] == 1)
    return hits / len(grouped)


def evaluate_model(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
    label_column: str,
) -> dict[str, Any]:
    labels = [int(row[label_column]) for row in rows]
    probs = [predict_probability(model, row) for row in rows]
    predictions = [int(prob >= 0.5) for prob in probs]
    accuracy = (
        sum(int(pred == label) for pred, label in zip(predictions, labels))
        / len(labels)
        if labels
        else None
    )
    return {
        "rows": len(rows),
        "positive_rate": sum(labels) / len(labels) if labels else None,
        "accuracy_at_0_5": accuracy,
        "brier_score": brier_score(probs, labels),
        "auroc": auroc(probs, labels),
        "average_precision": average_precision(probs, labels),
        "top1_label_hit_rate": top1_label_hit_rate(model, rows, label_column),
    }


def add_predictions(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    predicted: list[dict[str, Any]] = []
    for row in rows:
        updated = dict(row)
        updated["predicted_probability"] = round(
            predict_probability(model, row),
            6,
        )
        predicted.append(updated)
    return predicted


def run_experiment(
    train_root: Path,
    test_root: Path,
    output_dir: Path,
    label_column: str,
) -> dict[str, Any]:
    train_dirs = resolve_case_dirs(train_root)
    test_dirs = resolve_case_dirs(test_root)
    train_rows = build_rows_for_case_dirs(train_dirs)
    test_rows = build_rows_for_case_dirs(test_dirs)
    model = train_logistic_baseline(train_rows, FEATURE_COLUMNS, label_column)
    metrics = {
        "label_column": label_column,
        "feature_columns": FEATURE_COLUMNS,
        "train_case_count": len(train_dirs),
        "test_case_count": len(test_dirs),
        "train": evaluate_model(model, train_rows, label_column),
        "test": evaluate_model(model, test_rows, label_column),
        "model": model,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "m3b_train_rows.csv", train_rows)
    write_csv(output_dir / "m3b_test_rows.csv", test_rows)
    write_csv(output_dir / "m3b_test_predictions.csv", add_predictions(model, test_rows))
    write_json(output_dir / "m3b_metrics.json", metrics)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and evaluate the Project05 M3b utility baseline.",
    )
    parser.add_argument("--train-dir", type=Path, required=True)
    parser.add_argument("--test-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--label-column",
        choices=LABEL_COLUMNS,
        default="label_resolves_critical_gap_node",
    )
    args = parser.parse_args()

    metrics = run_experiment(
        args.train_dir,
        args.test_dir,
        args.output_dir,
        args.label_column,
    )
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
