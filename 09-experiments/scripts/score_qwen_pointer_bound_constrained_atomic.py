#!/usr/bin/env python3
"""Score the pointer-bound constrained training-validation diagnostic."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
RUNNER_PATH = SCRIPT_DIR / "run_qwen_pointer_bound_constrained_atomic.py"
BINDER_PATH = SCRIPT_DIR / "bind_pointer_bound_compiler_output.py"
METRICS_ROWS_NAME = "pointer-bound-sanitized-metrics-v0.1.jsonl"
SCORE_AUDIT_NAME = "pointer-bound-score-audit-v0.1.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no loader")
    spec.loader.exec_module(module)
    return module


RUNNER = _load(RUNNER_PATH, "project05_pointer_bound_runner_for_scorer")
BINDER = _load(BINDER_PATH, "project05_pointer_bound_binder_for_scorer")
GENERAL = RUNNER.GENERAL
ADAPTED = RUNNER.ADAPTED
CONDITIONS = RUNNER.CONDITIONS
DECISIONS = RUNNER.DECISIONS


class NoEligibleCheckpointError(ValueError):
    """Raised when every checkpoint fails the positive-generation hard Gate."""


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
            raise ValueError("pointer-bound row identity is invalid")
        by_condition = paired.setdefault(example_id, {})
        if condition in by_condition:
            raise ValueError("duplicate pointer-bound condition")
        by_condition[condition] = row
    if any(set(rows) != set(CONDITIONS) for rows in paired.values()):
        raise ValueError("pointer-bound example is missing a condition")
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
    for key in (set(general) | set(adapted)) - allowed_differences:
        if general.get(key) != adapted.get(key):
            raise ValueError(f"forbidden between-condition difference: {key}")
    if {general["condition_position"], adapted["condition_position"]} != {0, 1}:
        raise ValueError("pointer-bound condition positions differ")
    if general.get("adapter_state") != "off":
        raise ValueError("General adapter state differs")
    if adapted.get("adapter_state") != "project05_obs_compiler:on":
        raise ValueError("Adapted adapter state differs")
    if not general.get("schema_constrained") or not adapted.get("schema_constrained"):
        raise ValueError("constrained decoding was not shared")


def parse_and_bind(
    raw_output: str,
    bound_pointer: dict[str, str],
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        model_output = json.loads(raw_output.strip())
    except json.JSONDecodeError:
        return None, "invalid_json_after_constrained_decoding"
    try:
        return BINDER.bind_pointer(model_output, bound_pointer), None
    except BINDER.PointerBindingError as error:
        return None, str(error)


def make_sanitized_rows(
    raw_rows: list[dict[str, Any]],
    panel_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paired = pair_generation_rows(raw_rows)
    panel_by_hash = {
        RUNNER.sha256_text(row["example_id"]): row for row in panel_examples
    }
    if set(paired) != set(panel_by_hash):
        raise ValueError("generation panel differs from pointer-bound scoring panel")
    sanitized: list[dict[str, Any]] = []
    for example_id in sorted(paired):
        pair = paired[example_id]
        assert_fair_pair(pair)
        gold = panel_by_hash[example_id]
        for condition in CONDITIONS:
            raw = pair[condition]
            bound, error = parse_and_bind(raw["raw_output"], gold["pointer"])
            schema_valid = bound is not None
            predicted = bound["support_decision"] if schema_valid else "invalid"
            predicted_supported = predicted == "supported"
            pointer_integrity = bool(
                schema_valid
                and bound["pointer"] == gold["pointer"]
                and (
                    not predicted_supported
                    or bound["normalized_edge"]["source_pointer"]
                    == gold["pointer"]
                )
            )
            gold_supported = gold["support_decision"] == "supported"
            supported_schema_valid = bool(
                gold_supported
                and predicted_supported
                and schema_valid
                and pointer_integrity
            )
            supported_edge_exact = bool(
                supported_schema_valid
                and bound["normalized_edge"] == gold["normalized_edge"]
            )
            sanitized.append(
                {
                    "schema_version": "project05-pointer-bound-sanitized-row-v0.1",
                    "example_id_sha256": example_id,
                    "source_family_id": gold["source_family_id"],
                    "source_modality": gold["source_modality"],
                    "gold_decision": gold["support_decision"],
                    "condition": condition,
                    "condition_position": raw["condition_position"],
                    "predicted_decision": predicted,
                    "schema_constrained": bool(raw["schema_constrained"]),
                    "pointer_free_schema_valid": schema_valid,
                    "bound_schema_valid": schema_valid,
                    "failure_reason": error,
                    "supported_schema_valid": supported_schema_valid,
                    "supported_edge_exact": supported_edge_exact,
                    "pointer_binding_integrity": pointer_integrity,
                    "unsupported_no_edge": bool(
                        not gold_supported
                        and schema_valid
                        and predicted == "unsupported_by_bound_pointer"
                        and bound["normalized_edge"] is None
                    ),
                    "eos_terminated": raw["eos_terminated"],
                    "generated_tokens": raw["generated_tokens"],
                    "latency_seconds": raw["latency_seconds"],
                    "peak_allocated_bytes": raw["peak_allocated_bytes"],
                    "raw_output_sha256": raw["raw_output_sha256"],
                    "raw_generation_included": False,
                    "controller_eligible": False,
                }
            )
    return sanitized


def _rate(rows: list[dict[str, Any]], field: str) -> float:
    return 0.0 if not rows else sum(bool(row[field]) for row in rows) / len(rows)


def _slice_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gold = [row["gold_decision"] for row in rows]
    predicted = [row["predicted_decision"] for row in rows]
    supported_rows = [row for row in rows if row["gold_decision"] == "supported"]
    predicted_supported = [
        row for row in rows if row["predicted_decision"] == "supported"
    ]
    supported_f1 = class_f1(gold, predicted, "supported")
    unsupported_f1 = class_f1(
        gold,
        predicted,
        "unsupported_by_bound_pointer",
    )
    return {
        "examples": len(rows),
        "gold": dict(sorted(Counter(gold).items())),
        "predicted": dict(sorted(Counter(predicted).items())),
        "support_decision_f1": {
            "supported": supported_f1,
            "unsupported_by_bound_pointer": unsupported_f1,
        },
        "macro_support_decision_f1": (supported_f1 + unsupported_f1) / 2,
        "pointer_free_schema_valid_rate": _rate(rows, "pointer_free_schema_valid"),
        "supported_schema_valid_rate": _rate(
            supported_rows,
            "supported_schema_valid",
        ),
        "supported_edge_exact_rate": _rate(
            supported_rows,
            "supported_edge_exact",
        ),
        "pointer_binding_integrity_rate": _rate(
            predicted_supported,
            "pointer_binding_integrity",
        ),
        "predicted_supported_examples": len(predicted_supported),
        "unsupported_no_edge_rate": _rate(
            [
                row
                for row in rows
                if row["gold_decision"] == "unsupported_by_bound_pointer"
            ],
            "unsupported_no_edge",
        ),
    }


def score_condition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("condition rows are empty")
    families = {
        family: _slice_metrics(
            [row for row in rows if row["source_family_id"] == family]
        )
        for family in sorted({row["source_family_id"] for row in rows})
    }
    overall = _slice_metrics(rows)
    overall["families"] = families
    overall["family_macro_support_decision_f1"] = sum(
        report["macro_support_decision_f1"] for report in families.values()
    ) / len(families)
    overall["mean_latency_seconds"] = sum(
        float(row["latency_seconds"]) for row in rows
    ) / len(rows)
    overall["maximum_peak_allocated_bytes"] = max(
        int(row["peak_allocated_bytes"]) for row in rows
    )
    return overall


def positive_generation_checks(
    metrics: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, bool]:
    gate = config["gates"]["positive_generation"]
    families = list(metrics["families"].values())
    return {
        "supported_schema_valid_overall": metrics[
            "supported_schema_valid_rate"
        ]
        >= gate["minimum_supported_schema_valid_rate_overall"],
        "supported_schema_valid_each_family": all(
            report["supported_schema_valid_rate"]
            >= gate["minimum_supported_schema_valid_rate_each_family"]
            for report in families
        ),
        "supported_f1_nonzero_overall": metrics["support_decision_f1"][
            "supported"
        ]
        > gate["minimum_exclusive_supported_class_f1_overall"],
        "supported_f1_nonzero_each_family": all(
            report["support_decision_f1"]["supported"]
            > gate["minimum_exclusive_supported_class_f1_each_family"]
            for report in families
        ),
        "unsupported_f1_guardrail_overall": metrics["support_decision_f1"][
            "unsupported_by_bound_pointer"
        ]
        > gate["minimum_exclusive_unsupported_class_f1_overall"],
        "unsupported_f1_guardrail_each_family": all(
            report["support_decision_f1"]["unsupported_by_bound_pointer"]
            > gate["minimum_exclusive_unsupported_class_f1_each_family"]
            for report in families
        ),
        "pointer_binding_integrity": (
            metrics["predicted_supported_examples"] > 0
            and metrics["pointer_binding_integrity_rate"]
            == gate["required_pointer_binding_integrity_rate"]
        ),
    }


def checkpoint_is_eligible(
    metrics: dict[str, Any],
    config: dict[str, Any],
) -> bool:
    return all(positive_generation_checks(metrics, config).values())


def checkpoint_selection_key(report: dict[str, Any]) -> tuple[Any, ...]:
    metrics = report["metrics"]
    return (
        metrics["supported_schema_valid_rate"],
        metrics["support_decision_f1"]["supported"],
        metrics["supported_edge_exact_rate"],
        metrics["support_decision_f1"]["unsupported_by_bound_pointer"],
        metrics["family_macro_support_decision_f1"],
        -float(metrics.get("assistant_token_nll", float("inf"))),
        -int(report["epoch"]),
    )


def choose_checkpoint(
    reports: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    eligible = [
        report
        for report in reports
        if checkpoint_is_eligible(report["metrics"], config)
    ]
    if not eligible:
        raise NoEligibleCheckpointError(
            "no checkpoint passed supported-schema and supported-F1 hard Gates"
        )
    return max(eligible, key=checkpoint_selection_key)


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
        raise ValueError("pointer-bound condition count differs")
    metrics = {
        condition: score_condition(rows)
        for condition, rows in by_condition.items()
    }
    gates = {}
    for condition, report in metrics.items():
        checks = positive_generation_checks(report, config)
        gates[condition] = {
            "passed": all(checks.values()),
            "checks": checks,
            "macro_f1_may_override": False,
        }
    technical = config["gates"]["technical"]
    technical_pass = (
        len(sanitized_rows) == technical["exact_calls"]
        and len({row["example_id_sha256"] for row in sanitized_rows})
        == technical["exact_examples"]
        and all(row["schema_constrained"] for row in sanitized_rows)
        and all(not row["raw_generation_included"] for row in sanitized_rows)
        and all(not row["controller_eligible"] for row in sanitized_rows)
    )
    any_positive = any(gate["passed"] for gate in gates.values())
    return {
        "conditions": metrics,
        "technical_gate": {
            "passed": technical_pass,
            "status": (
                "passed_pointer_bound_atomic_integrity"
                if technical_pass
                else "failed_pointer_bound_atomic_integrity"
            ),
        },
        "positive_generation_gate": {
            "conditions": gates,
            "passed_any_condition": any_positive,
            "macro_f1_may_override": False,
        },
        "next_disposition": {
            "s0_s3_data_design_may_be_considered": any_positive,
            "new_qlora_training_authorized": False,
            "formal_test_authorized": False,
            "adapter_mainline_eligible": False,
            "fallback_if_all_conditions_fail": "retain_rule_strong_and_reuse_hybrid",
        },
        "scientific_scope": {
            "split": "training-validation",
            "independent_test_result": False,
            "v043_result_modified_or_rescored": False,
            "paper_positive_claim_authorized": False,
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
        raise ValueError("pointer-bound scoring root differs")
    output_root = RUNNER.require_within(
        Path(run_root) / config["output_policy"]["run_subdirectory"],
        run_root,
        "pointer-bound scoring output",
    )
    generation_path = output_root / RUNNER.GENERATION_AUDIT_NAME
    raw_path = output_root / RUNNER.RAW_ROWS_NAME
    generation = RUNNER.load_json(generation_path)
    if generation.get("status") != "pointer_bound_generation_complete_scoring_pending":
        raise ValueError("completed pointer-bound generation is required")
    if RUNNER.sha256_file(raw_path) != generation["raw_rows"]["sha256"]:
        raise ValueError("pointer-bound raw generation changed before scoring")
    if (output_root / SCORE_AUDIT_NAME).exists():
        raise FileExistsError("refusing pointer-bound score overwrite or resume")
    pair_file = (
        RUNNER.require_within(pair_root, run_root, "pointer-bound payload root")
        / contract["pair_payload"]["file"]
    )
    examples = RUNNER.LEGACY.load_pair_file(
        pair_file,
        contract["pair_payload"]["sha256"],
    )
    panel = RUNNER.select_atomic_panel(examples, config)
    sanitized = make_sanitized_rows(load_jsonl(raw_path), panel)
    scores = score_paired_rows(sanitized, config)
    rows_path = output_root / METRICS_ROWS_NAME
    for row in sanitized:
        RUNNER.append_jsonl(rows_path, row)
    audit = {
        "schema_version": "project05-pointer-bound-score-audit-v0.1",
        "status": "pointer_bound_training_validation_atomic_scoring_complete",
        "contract_sha256": RUNNER.sha256_file(verified["contract_path"]),
        "config_sha256": RUNNER.sha256_file(verified["config_path"]),
        "execution_authority_sha256": RUNNER.sha256_file(
            REPO_ROOT / execution_authority["authority_repository_path"]
        ),
        "generation_audit": {
            "path": RUNNER.GENERATION_AUDIT_NAME,
            "sha256": RUNNER.sha256_file(generation_path),
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
            "s0_s3_data_design_authorized": False,
            "new_qlora_training_authorized": False,
            "development_or_test_access_authorized": False,
            "c07_c12_execution_authorized": False,
            "m3_integration_authorized": False,
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
