#!/usr/bin/env python3
"""Score a completed server-side General-vs-Adapted paired atomic run."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
RUNNER_PATH = SCRIPT_DIR / "run_qwen_general_adapted_paired.py"
METRICS_ROWS_NAME = "paired-sanitized-metrics-v0.1.jsonl"
SCORE_AUDIT_NAME = "paired-score-audit-v0.1.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no loader")
    spec.loader.exec_module(module)
    return module


RUNNER = _load(RUNNER_PATH, "project05_paired_runner_for_scorer")
SELECTOR = RUNNER.SELECTOR
GENERAL = RUNNER.GENERAL
ADAPTED = RUNNER.ADAPTED
CONDITIONS = RUNNER.CONDITIONS
DECISIONS = RUNNER.DECISIONS


def class_f1(gold: list[str], predicted: list[str], label: str) -> float:
    tp = sum(g == label and p == label for g, p in zip(gold, predicted))
    fp = sum(g != label and p == label for g, p in zip(gold, predicted))
    fn = sum(g == label and p != label for g, p in zip(gold, predicted))
    denominator = 2 * tp + fp + fn
    return 0.0 if denominator == 0 else 2 * tp / denominator


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def pair_generation_rows(
    raw_rows: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    paired: dict[str, dict[str, dict[str, Any]]] = {}
    for row in raw_rows:
        example_id = row.get("example_id_sha256")
        condition = row.get("condition")
        if condition not in CONDITIONS or not isinstance(example_id, str):
            raise ValueError("raw paired row identity is invalid")
        by_condition = paired.setdefault(example_id, {})
        if condition in by_condition:
            raise ValueError("duplicate condition for paired example")
        by_condition[condition] = row
    if any(set(rows) != set(CONDITIONS) for rows in paired.values()):
        raise ValueError("paired example is missing a condition")
    return paired


def assert_fair_pair(rows: dict[str, dict[str, Any]]) -> None:
    general, adapted = rows[GENERAL], rows[ADAPTED]
    allowed_differences = {
        "condition",
        "condition_position",
        "adapter_state",
        "raw_output",
        "raw_output_sha256",
        "eos_terminated",
        "generated_tokens",
        "latency_seconds",
        "peak_allocated_bytes",
    }
    all_keys = set(general) | set(adapted)
    for key in all_keys - allowed_differences:
        if general.get(key) != adapted.get(key):
            raise ValueError(f"forbidden between-condition difference: {key}")
    if {general["condition_position"], adapted["condition_position"]} != {0, 1}:
        raise ValueError("paired condition positions differ")
    if general["adapter_state"] != "off":
        raise ValueError("General adapter state differs")
    if adapted["adapter_state"] != "project05_obs_compiler:on":
        raise ValueError("Adapted adapter state differs")
    if not (
        general.get("same_loaded_base_process")
        and adapted.get("same_loaded_base_process")
    ):
        raise ValueError("same loaded base process was not preserved")


def make_sanitized_rows(
    raw_rows: list[dict[str, Any]],
    panel_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paired = pair_generation_rows(raw_rows)
    panel_by_hash = {
        RUNNER.sha256_text(row["example_id"]): row for row in panel_examples
    }
    if set(paired) != set(panel_by_hash):
        raise ValueError("generation panel differs from frozen scoring panel")
    sanitized: list[dict[str, Any]] = []
    for example_id in sorted(paired):
        pair = paired[example_id]
        assert_fair_pair(pair)
        gold_example = panel_by_hash[example_id]
        gold = {
            "support_decision": gold_example["support_decision"],
            "normalized_edge": gold_example["normalized_edge"],
            "pointer": gold_example["pointer"],
        }
        for condition in CONDITIONS:
            raw = pair[condition]
            prediction, error = SELECTOR.strict_prediction(
                raw["raw_output"],
                raw["eos_terminated"],
            )
            valid = prediction is not None
            predicted_decision = (
                prediction["support_decision"] if valid else "invalid"
            )
            pointer_exact = valid and prediction["pointer"] == gold["pointer"]
            edge_exact = (
                valid
                and prediction["normalized_edge"] == gold["normalized_edge"]
            )
            ceiling_violation = bool(
                valid
                and prediction["support_decision"] == "supported"
                and prediction["pointer"] != gold["pointer"]
            )
            sanitized.append(
                {
                    "schema_version": "project05-paired-sanitized-row-v0.1",
                    "example_id_sha256": example_id,
                    "source_family_id": gold_example["source_family_id"],
                    "source_modality": gold_example["source_modality"],
                    "gold_decision": gold["support_decision"],
                    "condition": condition,
                    "condition_position": raw["condition_position"],
                    "predicted_decision": predicted_decision,
                    "eos_terminated": raw["eos_terminated"],
                    "schema_valid": valid,
                    "failure_reason": error,
                    "pointer_exact": pointer_exact,
                    "normalized_edge_exact": edge_exact,
                    "ceiling_violation": ceiling_violation,
                    "generated_tokens": raw["generated_tokens"],
                    "latency_seconds": raw["latency_seconds"],
                    "peak_allocated_bytes": raw["peak_allocated_bytes"],
                    "raw_output_sha256": raw["raw_output_sha256"],
                    "raw_generation_included": False,
                    "controller_eligible": False,
                }
            )
    return sanitized


def score_condition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("condition rows are empty")
    family_reports: dict[str, Any] = {}
    for family in sorted({row["source_family_id"] for row in rows}):
        subset = [row for row in rows if row["source_family_id"] == family]
        gold = [row["gold_decision"] for row in subset]
        predicted = [row["predicted_decision"] for row in subset]
        class_scores = {
            label: class_f1(gold, predicted, label) for label in DECISIONS
        }
        family_reports[family] = {
            "examples": len(subset),
            "support_decision_f1": class_scores,
            "macro_support_decision_f1": sum(class_scores.values())
            / len(class_scores),
            "gold": dict(sorted(Counter(gold).items())),
            "predicted": dict(sorted(Counter(predicted).items())),
        }

    def rate(field: str) -> float:
        return sum(bool(row[field]) for row in rows) / len(rows)

    supported_output_rate = (
        sum(row["predicted_decision"] == "supported" for row in rows) / len(rows)
    )
    return {
        "examples": len(rows),
        "families": family_reports,
        "family_macro_support_decision_f1": sum(
            report["macro_support_decision_f1"]
            for report in family_reports.values()
        )
        / len(family_reports),
        "overall_supported_class_f1": class_f1(
            [row["gold_decision"] for row in rows],
            [row["predicted_decision"] for row in rows],
            "supported",
        ),
        "overall_unsupported_class_f1": class_f1(
            [row["gold_decision"] for row in rows],
            [row["predicted_decision"] for row in rows],
            "unsupported_by_bound_pointer",
        ),
        "schema_valid_rate": rate("schema_valid"),
        "invalid_rate": 1.0 - rate("schema_valid"),
        "pointer_exact_rate": rate("pointer_exact"),
        "normalized_edge_exact_rate": rate("normalized_edge_exact"),
        "ceiling_violation_rate": rate("ceiling_violation"),
        "supported_output_rate": supported_output_rate,
        "mean_latency_seconds": sum(
            float(row["latency_seconds"]) for row in rows
        )
        / len(rows),
        "maximum_peak_allocated_bytes": max(
            int(row["peak_allocated_bytes"]) for row in rows
        ),
    }


def score_paired_rows(
    sanitized_rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    expected = config["panel"]["exact_examples"]
    by_condition = {
        condition: [
            row for row in sanitized_rows if row["condition"] == condition
        ]
        for condition in CONDITIONS
    }
    if any(len(rows) != expected for rows in by_condition.values()):
        raise ValueError("sanitized paired condition count differs")
    metrics = {
        condition: score_condition(rows)
        for condition, rows in by_condition.items()
    }
    general, adapted = metrics[GENERAL], metrics[ADAPTED]
    deltas = {
        "family_macro_support_decision_f1": adapted[
            "family_macro_support_decision_f1"
        ]
        - general["family_macro_support_decision_f1"],
        "overall_supported_class_f1": adapted["overall_supported_class_f1"]
        - general["overall_supported_class_f1"],
        "overall_unsupported_class_f1": adapted[
            "overall_unsupported_class_f1"
        ]
        - general["overall_unsupported_class_f1"],
        "invalid_rate": adapted["invalid_rate"] - general["invalid_rate"],
        "pointer_exact_rate": adapted["pointer_exact_rate"]
        - general["pointer_exact_rate"],
        "normalized_edge_exact_rate": adapted["normalized_edge_exact_rate"]
        - general["normalized_edge_exact_rate"],
        "ceiling_violation_rate": adapted["ceiling_violation_rate"]
        - general["ceiling_violation_rate"],
        "supported_output_rate": adapted["supported_output_rate"]
        - general["supported_output_rate"],
    }
    technical = config["gates"]["technical"]
    technical_pass = (
        len(sanitized_rows) == technical["exact_calls"]
        and len({row["example_id_sha256"] for row in sanitized_rows})
        == technical["exact_examples"]
        and all(not row["raw_generation_included"] for row in sanitized_rows)
        and all(not row["controller_eligible"] for row in sanitized_rows)
    )
    diagnostic = config["gates"]["adapter_diagnostic"]
    supported_by_family = [
        adapted["families"][family]["support_decision_f1"]["supported"]
        for family in sorted(adapted["families"])
    ]
    diagnostic_checks = {
        "adapted_supported_f1_nonzero_overall": adapted[
            "overall_supported_class_f1"
        ]
        > diagnostic["minimum_exclusive_supported_class_f1"],
        "adapted_supported_f1_nonzero_each_family": all(
            value > diagnostic["minimum_exclusive_supported_class_f1"]
            for value in supported_by_family
        ),
        "family_macro_f1_not_lower": deltas[
            "family_macro_support_decision_f1"
        ]
        >= diagnostic["minimum_family_macro_f1_delta"],
        "invalid_rate_not_higher": deltas["invalid_rate"]
        <= diagnostic["maximum_invalid_rate_delta"],
        "pointer_exact_not_lower": deltas["pointer_exact_rate"]
        >= diagnostic["minimum_pointer_exact_rate_delta"],
        "unsupported_f1_guardrail": deltas["overall_unsupported_class_f1"]
        >= diagnostic["minimum_unsupported_class_f1_delta"],
        "coverage_guardrail": deltas["supported_output_rate"]
        >= diagnostic["minimum_supported_output_rate_delta"],
        "ceiling_not_higher": deltas["ceiling_violation_rate"]
        <= diagnostic["maximum_ceiling_violation_rate_delta"],
    }
    diagnostic_pass = all(diagnostic_checks.values())
    return {
        "conditions": metrics,
        "adapted_minus_general": deltas,
        "technical_gate": {
            "passed": technical_pass,
            "status": (
                "passed_atomic_execution_integrity"
                if technical_pass
                else "failed_atomic_execution_integrity"
            ),
        },
        "adapter_diagnostic_gate": {
            "passed": diagnostic_pass,
            "checks": diagnostic_checks,
            "status": (
                "passed_training_validation_diagnostic_not_test_evidence"
                if diagnostic_pass
                else "failed_or_collapsed_training_validation_diagnostic"
            ),
            "may_select_adapter_for_mainline": False,
            "may_change_checkpoint": False,
        },
        "scientific_scope": {
            "split": "training-validation",
            "independent_test_result": False,
            "paper_positive_claim_authorized": False,
            "supported_class_collapse_reported": True,
            "general_vs_adapted_final_gate_evaluated": False,
        },
    }


def score_authorized_run(
    verified: dict[str, Any],
    execution_authority: dict[str, Any],
    pair_root: Path,
    run_root: Path,
) -> dict[str, Any]:
    contract, config = verified["contract"], verified["config"]
    allowed_root = Path(contract["server_execution_boundary"]["allowed_root"]).resolve()
    if Path(run_root).resolve() != allowed_root:
        raise ValueError("paired scoring root differs")
    output_root = RUNNER.require_within(
        Path(run_root) / config["output_policy"]["run_subdirectory"],
        run_root,
        "paired scoring output",
    )
    generation_audit_path = output_root / RUNNER.GENERATION_AUDIT_NAME
    raw_path = output_root / RUNNER.RAW_ROWS_NAME
    generation = RUNNER.load_json(generation_audit_path)
    if generation.get("status") != "paired_generation_complete_scoring_pending":
        raise ValueError("completed locked generation is required")
    if RUNNER.sha256_file(raw_path) != generation["raw_rows"]["sha256"]:
        raise ValueError("raw generation changed before scoring")
    if (output_root / SCORE_AUDIT_NAME).exists():
        raise FileExistsError("refusing paired score overwrite or resume")
    pair_file = (
        RUNNER.require_within(pair_root, run_root, "paired scoring payload root")
        / contract["pair_payload"]["file"]
    )
    examples = RUNNER.load_pair_file(
        pair_file,
        contract["pair_payload"]["sha256"],
    )
    panel = RUNNER.select_atomic_panel(examples, config)
    raw_rows = load_jsonl(raw_path)
    sanitized = make_sanitized_rows(raw_rows, panel)
    scores = score_paired_rows(sanitized, config)
    rows_path = output_root / METRICS_ROWS_NAME
    for row in sanitized:
        RUNNER.append_jsonl(rows_path, row)
    audit = {
        "schema_version": "project05-paired-score-audit-v0.1",
        "status": "paired_training_validation_atomic_scoring_complete",
        "contract_sha256": RUNNER.sha256_file(verified["contract_path"]),
        "config_sha256": RUNNER.sha256_file(verified["config_path"]),
        "execution_authority_sha256": RUNNER.sha256_file(
            REPO_ROOT / execution_authority["authority_repository_path"]
        ),
        "generation_audit": {
            "path": RUNNER.GENERATION_AUDIT_NAME,
            "sha256": RUNNER.sha256_file(generation_audit_path),
        },
        "sanitized_metrics": {
            "file": METRICS_ROWS_NAME,
            "sha256": RUNNER.sha256_file(rows_path),
            "rows": len(sanitized),
        },
        "scores": scores,
        "raw_generation": {
            "server_only": True,
            "download_authorized": False,
            "included_in_sanitized_metrics": False,
        },
        "next_gate": {
            "status": "hard_stop_for_user_review",
            "automatic_development_execution_authorized": False,
            "development_or_test_access_authorized": False,
            "c07_c12_execution_authorized": False,
            "m3_integration_authorized": False,
            "paper_positive_claim_authorized": False,
        },
    }
    RUNNER.write_json_no_overwrite(output_root / SCORE_AUDIT_NAME, audit)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--implementation-authority", type=Path, required=True)
    parser.add_argument("--execution-authority", type=Path, required=True)
    parser.add_argument("--pair-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    verified = RUNNER.validate_implementation_bundle(
        args.contract,
        args.config,
        args.implementation_authority,
    )
    execution = RUNNER.validate_execution_authority(
        args.execution_authority,
        verified,
    )
    result = score_authorized_run(
        verified,
        execution,
        args.pair_root,
        args.run_root,
    )
    print(result["status"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
