import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT_ROOT = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/results/"
    "paired_evaluation_v0.1"
)
GENERATION = RESULT_ROOT / "paired-generation-audit-v0.1.json"
METRICS = RESULT_ROOT / "paired-sanitized-metrics-v0.1.jsonl"
SCORE = RESULT_ROOT / "paired-score-audit-v0.1.json"
LOG = RESULT_ROOT / "paired-general-adapted-v0.41.detached.log"
RAW = RESULT_ROOT / "paired-raw-generations-v0.1.jsonl"
AUTHORITY = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "authority-lock-v0.43.json"
)
CONFIG = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/"
    "paired_evaluation_v0.1/paired-evaluation-config-v0.1.json"
)
SCORER_PATH = (
    ROOT / "09-experiments/scripts/score_qwen_general_adapted_paired.py"
)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_scorer():
    spec = importlib.util.spec_from_file_location(
        "project05_paired_result_scorer",
        SCORER_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_retrieved_sanitized_artifacts_match_frozen_hashes_and_counts():
    authority = load_json(AUTHORITY)
    expected = {
        "generation_audit": GENERATION,
        "sanitized_metrics": METRICS,
        "score_audit": SCORE,
        "detached_log": LOG,
    }
    for label, path in expected.items():
        assert authority["result_artifacts"][label]["sha256"] == sha(path)
    assert len(load_jsonl(METRICS)) == 32
    assert RAW.exists() is False


def test_server_side_scores_recompute_exactly_from_sanitized_rows():
    scorer = load_scorer()
    rows = load_jsonl(METRICS)
    recomputed = scorer.score_paired_rows(rows, load_json(CONFIG))
    assert recomputed == load_json(SCORE)["scores"]


def test_supported_class_collapse_is_preserved_not_hidden_by_macro_f1():
    score = load_json(SCORE)["scores"]
    general = score["conditions"]["QWEN-GENERAL"]
    adapted = score["conditions"]["QWEN-ADAPTED"]
    assert general["family_macro_support_decision_f1"] == 0.0
    assert adapted["family_macro_support_decision_f1"] == 0.5
    assert adapted["overall_supported_class_f1"] == 0.0
    assert adapted["overall_unsupported_class_f1"] == 1.0
    assert all(
        report["support_decision_f1"]["supported"] == 0.0
        for report in adapted["families"].values()
    )
    gate = score["adapter_diagnostic_gate"]
    assert gate["passed"] is False
    assert gate["checks"]["adapted_supported_f1_nonzero_overall"] is False
    assert gate["checks"]["adapted_supported_f1_nonzero_each_family"] is False


def test_failure_distributions_and_condition_order_are_exact():
    rows = load_jsonl(METRICS)
    by_condition = {
        condition: [row for row in rows if row["condition"] == condition]
        for condition in ("QWEN-GENERAL", "QWEN-ADAPTED")
    }
    assert Counter(
        row["failure_reason"] for row in by_condition["QWEN-GENERAL"]
    ) == {"invalid_top_level_schema": 16}
    assert Counter(
        row["predicted_decision"] for row in by_condition["QWEN-ADAPTED"]
    ) == {"invalid": 8, "unsupported_by_bound_pointer": 8}
    assert Counter(
        row["failure_reason"] for row in by_condition["QWEN-ADAPTED"]
    ) == {"invalid_edge_source_pointer": 8, None: 8}
    for rows_for_condition in by_condition.values():
        assert Counter(row["condition_position"] for row in rows_for_condition) == {
            0: 8,
            1: 8,
        }


def test_execution_integrity_resources_and_scope_all_remain_closed():
    generation = load_json(GENERATION)
    score = load_json(SCORE)
    assert generation["generation"]["calls"] == 32
    assert generation["generation"]["condition_counts"] == {
        "QWEN-ADAPTED": 16,
        "QWEN-GENERAL": 16,
    }
    assert generation["resources"]["peak_allocated_bytes"] <= generation[
        "resources"
    ]["maximum_peak_allocated_bytes"]
    assert generation["resources"]["final_free_bytes"] >= generation[
        "resources"
    ]["minimum_synchronized_free_bytes"]
    assert generation["resources"][
        "runtime_cache_checkpoint_output_bytes"
    ] <= generation["resources"][
        "maximum_runtime_cache_checkpoint_output_bytes"
    ]
    assert generation["privacy_and_scope"] == {
        "c07_c12_accessed": False,
        "development_or_test_accessed": False,
        "m3_integrated": False,
        "raw_generation_download_authorized": False,
        "train_accessed": False,
    }
    assert score["scores"]["technical_gate"]["passed"] is True
    assert score["next_gate"]["development_or_test_access_authorized"] is False
    assert score["next_gate"]["c07_c12_execution_authorized"] is False
    assert score["next_gate"]["m3_integration_authorized"] is False


def test_v043_consumes_execution_and_downgrades_adapter_without_rescue():
    authority = load_json(AUTHORITY)
    completion = authority["completion_gate"]
    assert completion["single_execution_consumed"] is True
    assert completion["technical_gate_passed"] is True
    assert completion["adapter_diagnostic_gate_passed"] is False
    assert completion["failure_audit_present"] is False
    disposition = authority["scientific_disposition"]
    assert disposition["qwen_adapted"] == "downgraded_not_mainline_eligible"
    assert disposition["qwen_general"] == "failed_strict_schema_atomic_gate"
    assert disposition["checkpoint_reselection_allowed"] is False
    assert disposition["parser_or_gate_repair_allowed"] is False
    assert disposition["paper_positive_claim_authorized"] is False
    assert authority["controller_eligible"] is False
