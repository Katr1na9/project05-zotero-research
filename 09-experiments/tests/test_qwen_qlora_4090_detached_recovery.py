import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTERRUPTION = ROOT / "09-experiments/llm_evidence_compiler_mainline/results/qwen25-4090-adamw-primary-v0.35-interruption-summary-v0.1.json"
CLOSURE = ROOT / "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.36.json"
AUTHORITY = ROOT / "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.37.json"
CONTRACT = ROOT / "09-experiments/llm_evidence_compiler_mainline/contracts/qwen25-qlora-4090-training-contract-v0.5.json"
CONFIG = ROOT / "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.5/training-config-v0.5.json"
OLD_CONFIG = ROOT / "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.4/training-config-v0.4.json"
LAUNCHER = ROOT / "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.5/run-adamw-primary-detached-4090-v0.5.sh"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_interrupted_run_is_closed_without_promoting_partial_checkpoints():
    result, closure = load(INTERRUPTION), load(CLOSURE)
    assert result["status"] == "externally_interrupted_incomplete_formal_primary"
    assert result["progress"]["optimizer_steps_completed"] == 194
    assert result["progress"]["optimizer_steps_total"] == 225
    assert result["formal_result_eligible"] is False
    assert result["checkpoint_inventory"]["checkpoint_selection_authorized"] is False
    assert closure["execution_disposition"]["v035_execution_complete"] is False
    assert closure["execution_disposition"]["v035_output_must_remain_immutable"] is True
    assert closure["sanitized_result"]["sha256"] == sha(INTERRUPTION)


def test_recovery_hash_chain_and_single_fresh_gate():
    contract, authority = load(CONTRACT), load(AUTHORITY)
    assert authority["authoritative_contract"]["sha256"] == sha(CONTRACT)
    assert authority["fresh_adamw_primary_gate"]["contract_sha256"] == sha(CONTRACT)
    assert authority["fresh_adamw_primary_gate"]["training_config_sha256"] == sha(CONFIG)
    assert authority["fresh_adamw_primary_gate"]["launcher_sha256"] == sha(LAUNCHER)
    assert contract["training_config"]["sha256"] == sha(CONFIG)
    assert contract["implementation"]["adamw_primary_launcher"]["sha256"] == sha(LAUNCHER)
    assert contract["interruption_closure_authority"]["sha256"] == sha(CLOSURE)
    gate = authority["fresh_adamw_primary_gate"]
    assert gate["maximum_executions"] == 1
    assert gate["fresh_initialization_required"] is True
    assert gate["detached_worker_required"] is True
    assert gate["resume_authorized"] is False
    assert gate["checkpoint_selection_authorized"] is False


def test_scientific_configuration_is_unchanged_except_new_output_route():
    old, new = load(OLD_CONFIG), load(CONFIG)
    ignored = {"config_id", "version", "created_date", "output_policy"}
    assert {key: value for key, value in new.items() if key not in ignored} == {
        key: value for key, value in old.items() if key not in ignored
    }
    old_output = dict(old["output_policy"])
    new_output = dict(new["output_policy"])
    assert old_output.pop("run_subdirectory") == "server-output/primary-adamw-v0.35"
    assert new_output.pop("run_subdirectory") == "server-output/primary-adamw-detached-v0.37"
    assert new_output == old_output


def test_launcher_detaches_worker_and_remains_scoped():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'readonly ALLOWED_HOME="/home/myy"' in text
    assert "/usr/bin/nohup /usr/bin/setsid /bin/bash" in text
    assert '>"${LOG_PATH}" 2>&1 < /dev/null &' in text
    assert '"$0" worker' in text
    assert 'exec /usr/bin/env -i HOME="${ALLOWED_HOME}"' in text
    assert 'CUDA_VISIBLE_DEVICES="${physical_gpu_uuid}"' in text
    assert '[[ ! -e "${OUTPUT_ROOT}" ]]' in text
    assert "checkpoint-epoch-002" not in text
    assert "pip install" not in text
    assert "CUDA_LAUNCH_BLOCKING" not in text


def test_downstream_scopes_remain_closed():
    authority = load(AUTHORITY)
    assert authority["next_gate"]["checkpoint_selection_authorized"] is False
    assert authority["next_gate"]["training_validation_generation_authorized"] is False
    assert authority["next_gate"]["formal_inference_authorized"] is False
    assert authority["next_gate"]["m3_integration_authorized"] is False
    assert authority["next_gate"]["paper_positive_claim_authorized"] is False
