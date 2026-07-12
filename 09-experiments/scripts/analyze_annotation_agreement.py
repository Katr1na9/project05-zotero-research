#!/usr/bin/env python3
"""Compute agreement for two independent Project05 human annotators."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


CLAIM_LABELS = ["0_unsupported", "1_partial", "2_direct"]
CLAIM_ALL_LABELS = set(CLAIM_LABELS) | {"U_unassessable"}
POINTER_LABELS = {"yes", "no", "unassessable"}
GRANULARITY_LABELS = [
    "G0_unknown",
    "G1_technique",
    "G2_tactic_intent",
    "G3_campaign",
]
REVIEWED_VALUES = {"yes", "y", "true", "1"}
PUBLIC_FILES = {
    "claim": "claim_items.jsonl",
    "intent": "intent_items.jsonl",
    "granularity": "granularity_items.jsonl",
}


def rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 4)


def nominal_kappa(left: list[str], right: list[str]) -> float | None:
    if len(left) != len(right):
        raise ValueError("Label vectors must have equal length")
    if not left:
        return None
    labels = sorted(set(left) | set(right))
    count = len(left)
    observed = sum(a == b for a, b in zip(left, right)) / count
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum(
        (left_counts[label] / count) * (right_counts[label] / count)
        for label in labels
    )
    if expected == 1.0:
        return 1.0 if observed == 1.0 else None
    return rounded((observed - expected) / (1.0 - expected))


def quadratic_weighted_kappa(
    left: list[str], right: list[str], ordered_labels: list[str]
) -> float | None:
    if len(left) != len(right):
        raise ValueError("Label vectors must have equal length")
    if not left:
        return None
    index = {label: position for position, label in enumerate(ordered_labels)}
    if any(label not in index for label in left + right):
        raise ValueError("Ordinal label is outside the declared order")
    count = len(left)
    denominator = max(1, len(ordered_labels) - 1) ** 2
    observed = sum(
        ((index[a] - index[b]) ** 2) / denominator
        for a, b in zip(left, right)
    ) / count
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum(
        (left_counts[a] / count)
        * (right_counts[b] / count)
        * (((index[a] - index[b]) ** 2) / denominator)
        for a in ordered_labels
        for b in ordered_labels
    )
    if expected == 0.0:
        return 1.0 if observed == 0.0 else None
    return rounded(1.0 - observed / expected)


def multilabel_agreement(
    left: list[set[str]], right: list[set[str]]
) -> dict[str, float | None]:
    if len(left) != len(right):
        raise ValueError("Multilabel vectors must have equal length")
    if not left:
        return {
            "exact_match_rate": None,
            "mean_jaccard": None,
            "micro_precision": None,
            "micro_recall": None,
            "micro_f1": None,
        }
    exact = sum(a == b for a, b in zip(left, right)) / len(left)
    jaccards = [
        len(a & b) / len(a | b) if (a | b) else 1.0
        for a, b in zip(left, right)
    ]
    true_positive = sum(len(a & b) for a, b in zip(left, right))
    predicted = sum(len(a) for a in left)
    reference = sum(len(b) for b in right)
    precision = true_positive / predicted if predicted else (1.0 if not reference else 0.0)
    recall = true_positive / reference if reference else (1.0 if not predicted else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "exact_match_rate": rounded(exact),
        "mean_jaccard": rounded(sum(jaccards) / len(jaccards)),
        "micro_precision": rounded(precision),
        "micro_recall": rounded(recall),
        "micro_f1": rounded(f1),
    }


def validate_label(task: str, label: str) -> None:
    allowed = {
        "claim": CLAIM_ALL_LABELS,
        "pointer": POINTER_LABELS,
        "granularity": set(GRANULARITY_LABELS),
    }.get(task)
    if allowed is None or label not in allowed:
        raise ValueError(f"Invalid {task} label: {label!r}")


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        blind_id = row.get("blind_id", "").strip()
        if not blind_id or blind_id in indexed:
            raise ValueError(f"Missing or duplicate blind_id in {path}: {blind_id!r}")
        indexed[blind_id] = {key: (value or "").strip() for key, value in row.items()}
    return indexed


def read_public_rows(path: Path) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        blind_id = str(row.get("blind_id", "")).strip()
        if not blind_id or blind_id in indexed:
            raise ValueError(
                f"Missing or duplicate blind_id in {path}: {blind_id!r}"
            )
        indexed[blind_id] = row
    return indexed


def validate_rows_against_public(
    annotation_dir: Path,
    task: str,
    role: str,
    rows: dict[str, dict[str, str]],
) -> None:
    public_path = annotation_dir / "public" / PUBLIC_FILES[task]
    if not public_path.is_file():
        return
    public = read_public_rows(public_path)
    if set(rows) != set(public):
        raise ValueError(f"{task}: {role} blind IDs do not match public items")
    if task != "intent":
        return
    for blind_id, row in rows.items():
        if row.get("reviewed", "").casefold() not in REVIEWED_VALUES:
            continue
        selected = parse_node_set(row.get("selected_node_ids_pipe", ""))
        candidates = {
            node["node_id"] for node in public[blind_id]["candidate_nodes"]
        }
        unknown = selected - candidates
        if unknown:
            raise ValueError(
                f"{task}: {role} selected unknown nodes for {blind_id}: "
                f"{sorted(unknown)}"
            )


def paired_reviewed(
    left: dict[str, dict[str, str]], right: dict[str, dict[str, str]]
) -> list[tuple[dict[str, str], dict[str, str]]]:
    return [
        (left[blind_id], right[blind_id])
        for blind_id in sorted(set(left) & set(right))
        if left[blind_id].get("reviewed", "").casefold() in REVIEWED_VALUES
        and right[blind_id].get("reviewed", "").casefold() in REVIEWED_VALUES
    ]


def raw_agreement(left: list[str], right: list[str]) -> float | None:
    if not left:
        return None
    return rounded(sum(a == b for a, b in zip(left, right)) / len(left))


def analyze_claims(pairs: list[tuple[dict[str, str], dict[str, str]]]) -> dict[str, Any]:
    support_left = [left.get("support_label", "") for left, _ in pairs]
    support_right = [right.get("support_label", "") for _, right in pairs]
    pointer_left = [left.get("source_pointer_valid", "") for left, _ in pairs]
    pointer_right = [right.get("source_pointer_valid", "") for _, right in pairs]
    for label in support_left + support_right:
        validate_label("claim", label)
    for label in pointer_left + pointer_right:
        validate_label("pointer", label)
    ordinal_pairs = [
        (a, b)
        for a, b in zip(support_left, support_right)
        if a != "U_unassessable" and b != "U_unassessable"
    ]
    ordinal_left = [a for a, _ in ordinal_pairs]
    ordinal_right = [b for _, b in ordinal_pairs]
    unassessable = sum(
        label == "U_unassessable" for label in support_left + support_right
    )
    return {
        "paired_items": len(pairs),
        "ordinal_items_after_U_exclusion": len(ordinal_pairs),
        "raw_agreement_rate": raw_agreement(support_left, support_right),
        "quadratic_weighted_kappa": quadratic_weighted_kappa(
            ordinal_left, ordinal_right, CLAIM_LABELS
        ),
        "unassessable_label_rate": rounded(
            unassessable / max(1, len(support_left) + len(support_right))
        ),
        "source_pointer_raw_agreement_rate": raw_agreement(
            pointer_left, pointer_right
        ),
        "source_pointer_cohen_kappa": nominal_kappa(pointer_left, pointer_right),
    }


def parse_node_set(value: str) -> set[str]:
    return {node.strip() for node in value.split("|") if node.strip()}


def analyze_intent(pairs: list[tuple[dict[str, str], dict[str, str]]]) -> dict[str, Any]:
    left = [parse_node_set(a.get("selected_node_ids_pipe", "")) for a, _ in pairs]
    right = [parse_node_set(b.get("selected_node_ids_pipe", "")) for _, b in pairs]
    return {"paired_items": len(pairs), **multilabel_agreement(left, right)}


def analyze_granularity(
    pairs: list[tuple[dict[str, str], dict[str, str]]]
) -> dict[str, Any]:
    left = [a.get("granularity_label", "") for a, _ in pairs]
    right = [b.get("granularity_label", "") for _, b in pairs]
    for label in left + right:
        validate_label("granularity", label)
    index = {label: position for position, label in enumerate(GRANULARITY_LABELS)}
    confusion = {
        a: {b: 0 for b in GRANULARITY_LABELS} for a in GRANULARITY_LABELS
    }
    for a, b in zip(left, right):
        confusion[a][b] += 1
    return {
        "paired_items": len(pairs),
        "raw_agreement_rate": raw_agreement(left, right),
        "within_one_level_rate": rounded(
            sum(abs(index[a] - index[b]) <= 1 for a, b in zip(left, right))
            / max(1, len(left))
        ),
        "quadratic_weighted_kappa": quadratic_weighted_kappa(
            left, right, GRANULARITY_LABELS
        ),
        "confusion_matrix_A_rows_B_columns": confusion,
    }


def analyze_annotation_dir(annotation_dir: Path) -> dict[str, Any]:
    filenames = {
        "claim": "claim_annotations.csv",
        "intent": "intent_annotations.csv",
        "granularity": "granularity_annotations.csv",
    }
    task_data: dict[str, tuple[list[tuple[dict[str, str], dict[str, str]]], int]] = {}
    for task, filename in filenames.items():
        left = read_rows(annotation_dir / "annotator_A" / filename)
        right = read_rows(annotation_dir / "annotator_B" / filename)
        validate_rows_against_public(
            annotation_dir, task, "annotator_A", left
        )
        validate_rows_against_public(
            annotation_dir, task, "annotator_B", right
        )
        total_ids = len(set(left) | set(right))
        task_data[task] = (paired_reviewed(left, right), total_ids)

    compared = sum(len(pairs) for pairs, _ in task_data.values())
    completeness = {
        task: {
            "paired_reviewed": len(pairs),
            "expected_items": total,
        }
        for task, (pairs, total) in task_data.items()
    }
    if compared == 0:
        return {
            "status": "awaiting_annotations",
            "human_labels_compared": 0,
            "completeness": completeness,
        }

    complete = all(len(pairs) == total for pairs, total in task_data.values())
    result = {
        "status": "complete" if complete else "partial",
        "human_labels_compared": compared,
        "completeness": completeness,
    }
    if task_data["claim"][0]:
        result["claim_support"] = analyze_claims(task_data["claim"][0])
    if task_data["intent"][0]:
        result["public_intent"] = analyze_intent(task_data["intent"][0])
    if task_data["granularity"][0]:
        result["granularity"] = analyze_granularity(task_data["granularity"][0])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze two human annotation files.")
    parser.add_argument("annotation_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze_annotation_dir(args.annotation_dir)
    output = args.output or args.annotation_dir / "agreement_results.json"
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
