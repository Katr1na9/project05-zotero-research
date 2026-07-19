import hashlib
import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "09-experiments/scripts/execute_qwen_qlora_4090.py"
CONTRACT_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "qwen25-qlora-4090-training-contract-v0.1.json"
)
AUTHORITY_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.30.json"
)
CONFIG_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.1/"
    "training-config-v0.1.json"
)
LOCAL_CONFIG_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_primary_v0.1/"
    "training-config-v0.1-local.json"
)
LAUNCHER_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.1/"
    "run-server-4090-v0.1.sh"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_script():
    spec = importlib.util.spec_from_file_location("project05_4090_executor_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_and_authority_hash_chain_is_closed():
    contract = load_json(CONTRACT_PATH)
    authority = load_json(AUTHORITY_PATH)
    assert authority["authoritative_contract"]["sha256"] == sha256(CONTRACT_PATH)
    assert authority["rtx4090_execution_gate"]["contract_sha256"] == sha256(CONTRACT_PATH)
    assert contract["training_config"]["sha256"] == sha256(CONFIG_PATH)
    assert authority["rtx4090_execution_gate"]["training_config_sha256"] == sha256(CONFIG_PATH)
    for record in contract["frozen_inputs"].values():
        assert sha256(REPO_ROOT / record["path"]) == record["sha256"]
    for record in contract["implementation"].values():
        assert sha256(REPO_ROOT / record["path"]) == record["sha256"]


def test_4090_migration_does_not_change_scientific_configuration():
    server = load_json(CONFIG_PATH)
    local = load_json(LOCAL_CONFIG_PATH)
    exact_fields = [
        "base_model_id",
        "base_resolved_commit",
        "quantization",
        "lora",
        "data",
        "sequence_length",
        "allow_truncation",
        "micro_batch_size",
        "gradient_accumulation_steps",
        "effective_batch_size",
        "epochs",
        "optimizer_steps",
        "optimizer_steps_per_epoch",
        "learning_rate",
        "optimizer",
        "weight_decay",
        "scheduler",
        "gradient_checkpointing",
        "maximum_gradient_norm",
        "seed",
        "loss_mask",
        "checkpointing",
    ]
    for field in exact_fields:
        assert server[field] == local[field], field


def test_contract_is_single_gpu_and_exact_home_scoped():
    contract = load_json(CONTRACT_PATH)
    authority = load_json(AUTHORITY_PATH)
    boundary = contract["server_execution_boundary"]
    assert boundary["allowed_home"] == "/home/myy"
    assert boundary["run_directory_name"] == "project05-qwen25-4090-v0.1"
    assert boundary["explicit_read_list_outside_allowed_home"] == []
    assert boundary["explicit_write_list_outside_allowed_home"] == []
    assert contract["execution_host"]["single_visible_gpu_required"] is True
    assert authority["user_decision"]["multi_gpu_training_authorized"] is False
    assert "multi_gpu_training" in contract["not_authorized"]


def test_smoke_must_pass_before_one_primary_execution():
    contract = load_json(CONTRACT_PATH)
    authority = load_json(AUTHORITY_PATH)
    assert contract["phase_gate"]["smoke"] == {
        "authorized": True,
        "maximum_executions": 1,
        "longest_train_examples": 16,
        "optimizer_steps": 1,
        "adapter_or_checkpoint_save": False,
    }
    assert contract["phase_gate"]["primary"]["authorized_after_passed_smoke"] is True
    assert contract["phase_gate"]["primary"]["maximum_executions"] == 1
    assert contract["phase_gate"]["primary"]["resume_authorized"] is False
    assert authority["rtx4090_execution_gate"]["maximum_primary_executions"] == 1


def test_memory_gate_uses_allocated_and_free_but_not_reserved():
    module = load_script()
    config = load_json(CONFIG_PATH)
    limit = config["hardware"]["maximum_peak_allocated_bytes"]
    minimum_free = config["hardware"]["minimum_synchronized_free_bytes"]
    samples = [{
        "allocated_bytes": limit,
        "reserved_bytes": limit + 10_000_000_000,
        "free_bytes": minimum_free,
    }]
    gate = module.validate_memory_gate(samples, config)
    assert gate["passed"] is True
    assert gate["peak_reserved_is_blocking"] is False


def test_memory_gate_rejects_allocated_or_free_boundary_violation():
    module = load_script()
    config = load_json(CONFIG_PATH)
    limit = config["hardware"]["maximum_peak_allocated_bytes"]
    minimum_free = config["hardware"]["minimum_synchronized_free_bytes"]
    allocated_failure = [{
        "allocated_bytes": limit + 1,
        "reserved_bytes": 0,
        "free_bytes": minimum_free,
    }]
    free_failure = [{
        "allocated_bytes": limit,
        "reserved_bytes": 0,
        "free_bytes": minimum_free - 1,
    }]
    assert module.validate_memory_gate(allocated_failure, config)["passed"] is False
    assert module.validate_memory_gate(free_failure, config)["passed"] is False


def test_launcher_discards_pathological_login_environment_and_binds_uuid():
    text = LAUNCHER_PATH.read_text(encoding="utf-8")
    assert "/usr/bin/env -i" in text
    assert "LD_LIBRARY_PATH" not in text
    assert 'CUDA_VISIBLE_DEVICES="${physical_gpu_uuid}"' in text
    assert "nvidia-smi --query-gpu=index,uuid,name,memory.free,memory.used" in text
    assert "memory.free" in text
    assert "memory.used" in text
    assert "runtime-ready-v0.1" in text
    assert "--index-strategy unsafe-best-match" in text


def test_downstream_scopes_remain_closed():
    contract = load_json(CONTRACT_PATH)
    authority = load_json(AUTHORITY_PATH)
    closed = {
        "checkpoint_selection",
        "training_validation_generation",
        "development_or_test_packet_access",
        "c07_c12_model_execution",
        "formal_inference",
        "m3_runtime_integration",
        "merged_model_save",
        "hub_upload",
        "paper_a_result_change",
    }
    assert closed <= set(contract["not_authorized"])
    assert authority["next_gate"]["checkpoint_selection_authorized"] is False
    assert authority["next_gate"]["formal_inference_authorized"] is False
    assert authority["next_gate"]["m3_integration_authorized"] is False
