import hashlib
import json
import math
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.34.json"
)
RESULT_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/results/"
    "qwen25-4090-optimizer-stability-diagnostic-v0.1.json"
)
PROGRESS_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/results/"
    "qwen25-4090-optimizer-stability-progress-v0.1.jsonl"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_post_run_authority_hashes_all_sanitized_artifacts():
    authority = load_json(AUTHORITY_PATH)
    for record in authority["result_artifacts"].values():
        assert sha256(REPO_ROOT / record["path"]) == record["sha256"]
    parent = authority["parent_authority"]
    assert sha256(REPO_ROOT / parent["path"]) == parent["sha256"]


def test_diagnostic_completed_and_exceeded_the_old_failure_step():
    result = load_json(RESULT_PATH)
    assert result["status"] == "passed_torch_adamw_180_step_stability_diagnostic"
    assert result["diagnostic"]["optimizer_steps"] == 180
    assert result["diagnostic"]["microbatches"] == 2880
    assert result["diagnostic"]["old_failure_step_exceeded"] is True
    assert result["optimizer"]["name"] == "adamw_torch"
    assert result["optimizer"]["bitsandbytes_optimizer_used"] is False
    assert result["optimizer"]["bitsandbytes_nf4_base_used"] is True


def test_numeric_memory_and_no_artifact_gates_passed():
    result = load_json(RESULT_PATH)
    loss = result["diagnostic"]["loss"]
    gradient = result["diagnostic"]["gradient_norm"]
    assert loss["count"] == 2880
    assert gradient["count"] == 180
    assert all(math.isfinite(loss[key]) for key in ("first", "last", "minimum", "maximum", "mean"))
    assert all(math.isfinite(gradient[key]) for key in ("first", "last", "minimum", "maximum", "mean"))
    assert result["memory_gate"]["passed"] is True
    assert result["memory_gate"]["peak_allocated_bytes"] <= result["memory_gate"]["maximum_peak_allocated_bytes"]
    assert result["memory_gate"]["minimum_free_bytes"] >= result["memory_gate"]["minimum_synchronized_free_bytes"]
    assert result["memory_gate"]["post_cleanup_reserved_bytes"] <= 268435456
    assert result["artifacts"] == {
        "adapter_saved": False,
        "checkpoint_saved": False,
        "optimizer_state_saved": False,
        "generation_calls": 0,
        "raw_payload_recorded": False,
    }


def test_progress_is_complete_sanitized_and_cache_normalized():
    rows = [json.loads(line) for line in PROGRESS_PATH.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 181
    assert rows[0]["event"] == "optimizer_stability_started"
    steps = rows[1:]
    assert [row["optimizer_step"] for row in steps] == list(range(1, 181))
    assert all(row["event"] == "optimizer_step_completed" for row in steps)
    assert sum(bool(row["allocator_cache_release_attempted"]) for row in steps) == 105
    forbidden = {"prompt", "target", "input_ids", "labels", "example_id", "raw_payload"}
    assert all(not (forbidden & set(row)) for row in rows)


def test_all_formal_and_downstream_scopes_remain_closed():
    authority = load_json(AUTHORITY_PATH)
    next_gate = authority["next_gate"]
    assert next_gate["fresh_225_step_three_epoch_primary_authorized"] is False
    assert next_gate["v0_2_checkpoint_selection_authorized"] is False
    assert next_gate["formal_inference_authorized"] is False
    assert next_gate["m3_integration_authorized"] is False
    assert "formal_primary_training" in authority["not_authorized"]
