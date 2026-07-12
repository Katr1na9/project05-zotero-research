#!/usr/bin/env python3
"""Calibrate Project05 compiled proxies against adjudicated human labels."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


AGREEMENT_PATH = Path(__file__).with_name("analyze_annotation_agreement.py")
TASK_FILES = {
    "claim": "claim_annotations.csv",
    "intent": "intent_annotations.csv",
    "granularity": "granularity_annotations.csv",
}


def _load_agreement_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "project05_annotation_agreement",
        AGREEMENT_PATH,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load agreement module from {AGREEMENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AGREEMENT = _load_agreement_module()


def is_reviewed(row: dict[str, str]) -> bool:
    return row.get("reviewed", "").casefold() in AGREEMENT.REVIEWED_VALUES


def normalized_label(task: str, row: dict[str, str]) -> Any:
    if task == "claim":
        support = row.get("support_label", "")
        pointer = row.get("source_pointer_valid", "")
        AGREEMENT.validate_label("claim", support)
        AGREEMENT.validate_label("pointer", pointer)
        return support, pointer
    if task == "intent":
        return frozenset(
            AGREEMENT.parse_node_set(row.get("selected_node_ids_pipe", ""))
        )
    if task == "granularity":
        label = row.get("granularity_label", "")
        AGREEMENT.validate_label("granularity", label)
        return label
    raise ValueError(f"Unknown annotation task: {task}")


def resolve_final_labels(
    annotation_dir: Path,
    task: str,
    admin_items: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    filename = TASK_FILES[task]
    left = AGREEMENT.read_rows(annotation_dir / "annotator_A" / filename)
    right = AGREEMENT.read_rows(annotation_dir / "annotator_B" / filename)
    adjudicator_path = annotation_dir / "adjudicator" / filename
    adjudicator = (
        AGREEMENT.read_rows(adjudicator_path)
        if adjudicator_path.is_file()
        else {}
    )
    AGREEMENT.validate_rows_against_public(
        annotation_dir, task, "annotator_A", left
    )
    AGREEMENT.validate_rows_against_public(
        annotation_dir, task, "annotator_B", right
    )
    if adjudicator:
        AGREEMENT.validate_rows_against_public(
            annotation_dir, task, "adjudicator", adjudicator
        )
    expected = set(admin_items)
    for role, rows in (("annotator_A", left), ("annotator_B", right)):
        if set(rows) != expected:
            raise ValueError(
                f"{task}: {role} blind IDs do not match the admin key"
            )
    if adjudicator and set(adjudicator) != expected:
        raise ValueError(f"{task}: adjudicator blind IDs do not match the admin key")

    incomplete = [
        blind_id
        for blind_id in sorted(expected)
        if not is_reviewed(left[blind_id]) or not is_reviewed(right[blind_id])
    ]
    if incomplete:
        return {
            "status": "awaiting_annotations",
            "expected_items": len(expected),
            "paired_reviewed": len(expected) - len(incomplete),
            "disagreement_items": None,
            "unresolved_disagreements": None,
            "final_labels": {},
        }

    final_labels: dict[str, Any] = {}
    disagreements = 0
    unresolved = 0
    for blind_id in sorted(expected):
        left_label = normalized_label(task, left[blind_id])
        right_label = normalized_label(task, right[blind_id])
        if left_label == right_label:
            final_labels[blind_id] = left_label
            continue
        disagreements += 1
        row = adjudicator.get(blind_id)
        if row is None or not is_reviewed(row):
            unresolved += 1
            continue
        final_labels[blind_id] = normalized_label(task, row)
    return {
        "status": "complete" if unresolved == 0 else "awaiting_adjudication",
        "expected_items": len(expected),
        "paired_reviewed": len(expected),
        "disagreement_items": disagreements,
        "unresolved_disagreements": unresolved,
        "final_labels": final_labels,
    }


def rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return AGREEMENT.rounded(numerator / denominator)


def calibrate_claims(final: dict[str, tuple[str, str]]) -> dict[str, Any]:
    support = Counter(label[0] for label in final.values())
    pointers = Counter(label[1] for label in final.values())
    assessable_support = sum(
        support[label] for label in AGREEMENT.CLAIM_LABELS
    )
    assessable_pointers = pointers["yes"] + pointers["no"]
    return {
        "final_label_counts": {
            label: support[label]
            for label in [*AGREEMENT.CLAIM_LABELS, "U_unassessable"]
        },
        "compiled_claim_direct_acceptance_rate_assessable": rate(
            support["2_direct"], assessable_support
        ),
        "direct_or_partial_rate_assessable": rate(
            support["2_direct"] + support["1_partial"],
            assessable_support,
        ),
        "unassessable_rate": rate(
            support["U_unassessable"], len(final)
        ),
        "source_pointer_label_counts": {
            label: pointers[label]
            for label in ("yes", "no", "unassessable")
        },
        "source_pointer_valid_rate_assessable": rate(
            pointers["yes"], assessable_pointers
        ),
    }


def calibrate_intent(
    final: dict[str, frozenset[str]],
    admin: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    blind_ids = sorted(final)
    human = [set(final[blind_id]) for blind_id in blind_ids]
    compiled = [
        set(admin[blind_id].get("intended_cti_node_ids", []))
        for blind_id in blind_ids
    ]
    return {
        "comparison": "final_human_vs_compiled_public_intent",
        **AGREEMENT.multilabel_agreement(human, compiled),
    }


def calibrate_granularity(
    final: dict[str, str],
    admin: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    blind_ids = sorted(final)
    human = [final[blind_id] for blind_id in blind_ids]
    compiled = [
        admin[blind_id]["computed_granularity"] for blind_id in blind_ids
    ]
    labels = AGREEMENT.GRANULARITY_LABELS
    index = {label: position for position, label in enumerate(labels)}
    signed = [index[system] - index[person] for person, system in zip(human, compiled)]
    confusion = {person: {system: 0 for system in labels} for person in labels}
    for person, system in zip(human, compiled):
        confusion[person][system] += 1
    return {
        "comparison": "final_human_rows_vs_compiled_proxy_columns",
        "exact_match_rate": AGREEMENT.raw_agreement(human, compiled),
        "within_one_level_rate": rate(
            sum(abs(value) <= 1 for value in signed), len(signed)
        ),
        "quadratic_weighted_kappa": AGREEMENT.quadratic_weighted_kappa(
            human,
            compiled,
            labels,
        ),
        "compiled_over_granularity_rate": rate(
            sum(value > 0 for value in signed), len(signed)
        ),
        "compiled_under_granularity_rate": rate(
            sum(value < 0 for value in signed), len(signed)
        ),
        "mean_compiled_minus_human_levels": AGREEMENT.rounded(
            sum(signed) / len(signed)
        ) if signed else None,
        "confusion_matrix": confusion,
    }


def analyze_calibration(annotation_dir: Path) -> dict[str, Any]:
    admin_path = annotation_dir / "admin" / "admin_key.json"
    if not admin_path.is_file():
        raise FileNotFoundError(
            "Local administrator key is required after independent annotation; "
            f"missing {admin_path}"
        )
    admin = json.loads(admin_path.read_text(encoding="utf-8"))
    if set(admin) != set(TASK_FILES):
        raise ValueError("Admin key must contain claim, intent and granularity")

    resolved = {
        task: resolve_final_labels(annotation_dir, task, admin[task])
        for task in TASK_FILES
    }
    public_status = {
        task: {key: value for key, value in result.items() if key != "final_labels"}
        for task, result in resolved.items()
    }
    if any(
        result["status"] == "awaiting_annotations"
        for result in resolved.values()
    ):
        return {
            "status": "awaiting_annotations",
            "calibrated_human_items": 0,
            "task_status": public_status,
        }
    if any(
        result["status"] == "awaiting_adjudication"
        for result in resolved.values()
    ):
        return {
            "status": "awaiting_adjudication",
            "calibrated_human_items": 0,
            "task_status": public_status,
        }

    claim_final = resolved["claim"]["final_labels"]
    intent_final = resolved["intent"]["final_labels"]
    granularity_final = resolved["granularity"]["final_labels"]
    return {
        "status": "complete",
        "calibrated_human_items": sum(
            len(result["final_labels"]) for result in resolved.values()
        ),
        "task_status": public_status,
        "claim_support": calibrate_claims(claim_final),
        "public_intent": calibrate_intent(intent_final, admin["intent"]),
        "granularity": calibrate_granularity(
            granularity_final,
            admin["granularity"],
        ),
        "boundary": (
            "Aggregate human calibration only; recoverable claim sets and "
            "item-level administrator mappings are not emitted."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate compiled Project05 proxies after adjudication."
    )
    parser.add_argument("annotation_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze_calibration(args.annotation_dir)
    output = args.output or args.annotation_dir / "calibration_results.json"
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
