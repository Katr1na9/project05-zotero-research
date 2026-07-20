import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT_ROOT = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/results/checkpoint_selection_v0.1"
)
AUDIT = RESULT_ROOT / "checkpoint-selection-audit-v0.1.json"
METRICS = RESULT_ROOT / "checkpoint-selection-metrics-v0.1.jsonl"
PROGRESS = RESULT_ROOT / "checkpoint-selection-progress-v0.1.jsonl"
AUTHORITY = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.40.json"
)
FORMAL_TRAINING = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/results/"
    "qwen25-4090-adamw-detached-primary-success-audit-v0.1.json"
)
SELECTOR = ROOT / "09-experiments/scripts/select_qwen_qlora_checkpoint_4090.py"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_selector():
    spec = importlib.util.spec_from_file_location(
        "project05_checkpoint_result_selector", SELECTOR
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sanitized_artifact_hashes_and_counts_are_frozen():
    authority, audit = load_json(AUTHORITY), load_json(AUDIT)
    for name, path in (
        ("audit", AUDIT),
        ("metrics", METRICS),
        ("progress", PROGRESS),
    ):
        record = authority["selection_result"][name]
        assert record["sha256"] == sha(path)
    rows, progress = load_jsonl(METRICS), load_jsonl(PROGRESS)
    assert len(rows) == audit["artifacts"]["metrics_rows"]["rows"] == 900
    assert len(progress) == authority["selection_result"]["progress"]["rows"] == 91
    assert Counter(row["epoch"] for row in rows) == {1: 300, 2: 300, 3: 300}
    assert progress[-1]["event"] == "checkpoint_selection_completed"
    assert progress[-1]["selected_epoch"] == 2


def test_metrics_recompute_and_epoch_two_is_the_strict_primary_winner():
    selector, audit = load_selector(), load_json(AUDIT)
    rows = load_jsonl(METRICS)
    for report in audit["checkpoints"]:
        observed = selector.score_rows(
            [row for row in rows if row["epoch"] == report["epoch"]]
        )
        assert observed == report["metrics"]
    selected = selector.choose_checkpoint(audit["checkpoints"])
    assert selected["epoch"] == audit["selected"]["epoch"] == 2
    assert selected["metrics"]["family_macro_support_decision_f1"] > max(
        report["metrics"]["family_macro_support_decision_f1"]
        for report in audit["checkpoints"]
        if report["epoch"] != 2
    )


def test_selected_adapter_matches_the_formal_epoch_two_checkpoint():
    audit, formal = load_json(AUDIT), load_json(FORMAL_TRAINING)
    epoch_two = next(row for row in formal["checkpoints"] if row["epoch"] == 2)
    adapter = next(
        row
        for row in epoch_two["files"]
        if row["path"] == "adapter/adapter_model.safetensors"
    )
    assert audit["selected"]["optimizer_step"] == epoch_two["optimizer_step"] == 150
    assert audit["selected"]["adapter_sha256"] == adapter["sha256"]


def test_class_collapse_is_preserved_as_a_blocking_scientific_diagnostic():
    authority, audit = load_json(AUTHORITY), load_json(AUDIT)
    for report in audit["checkpoints"]:
        for family in report["metrics"]["families"].values():
            assert family["support_decision_f1"]["supported"] == 0.0
    disposition = authority["scientific_disposition"]
    assert disposition["adapter_effectiveness_proven"] is False
    assert (
        disposition[
            "supported_class_f1_is_zero_for_both_families_at_all_three_checkpoints"
        ]
        is True
    )
    assert disposition["positive_paper_claim_authorized"] is False
    assert disposition["negative_or_harmful_adapter_result_must_remain_admissible"]


def test_raw_generations_and_downstream_scopes_remain_closed():
    authority, audit = load_json(AUTHORITY), load_json(AUDIT)
    assert not (
        RESULT_ROOT / "checkpoint-selection-raw-generations-v0.1.jsonl"
    ).exists()
    assert audit["artifacts"]["raw_generations"]["server_only"] is True
    assert audit["privacy_and_scope"]["development_or_test_accessed"] is False
    assert audit["privacy_and_scope"]["paired_general_vs_adapted_run"] is False
    gate = authority["next_gate"]
    assert gate["paired_evaluation_plan_contract_runner_and_tests_authorized"] is True
    assert gate["paired_model_execution_authorized"] is False
    assert gate["development_or_test_access_authorized"] is False
    assert gate["c07_c12_execution_authorized"] is False
    assert gate["m3_integration_authorized"] is False


def test_memory_resource_and_reproducibility_gates_passed():
    authority, audit = load_json(AUTHORITY), load_json(AUDIT)
    assert audit["memory"]["passed"] is True
    assert (
        audit["memory"]["final_free_bytes"]
        >= audit["memory"]["minimum_synchronized_free_bytes"]
    )
    assert (
        audit["resources"]["runtime_cache_checkpoint_output_bytes"]
        <= audit["resources"]["maximum_bytes"]
    )
    assert all(
        report["reproducibility"]["exact_raw_output_sha256_match"]
        and report["reproducibility"]["panel_examples"] == 16
        for report in audit["checkpoints"]
    )
    completion = authority["completion_gate"]
    assert completion["failure_audit_present"] is False
    assert completion["selection_process_present_after_completion"] is False
    assert completion["gpu_released_after_completion"] is True
    assert completion["raw_generation_downloaded"] is False
