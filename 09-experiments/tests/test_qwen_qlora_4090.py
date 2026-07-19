import hashlib
import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "09-experiments/scripts/execute_qwen_qlora_4090.py"
CONTRACT_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "qwen25-qlora-4090-training-contract-v0.2.json"
)
AUTHORITY_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.32.json"
)
CONFIG_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.2/"
    "training-config-v0.2.json"
)
LEGACY_CONTRACT_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "qwen25-qlora-4090-training-contract-v0.1.json"
)
LEGACY_AUTHORITY_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.30.json"
)
LEGACY_CONFIG_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.1/"
    "training-config-v0.1.json"
)
LOCAL_CONFIG_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_primary_v0.1/"
    "training-config-v0.1-local.json"
)
LAUNCHER_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.2/"
    "run-server-4090-v0.2.sh"
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
    module = load_script()
    raw_contract = load_json(CONTRACT_PATH)
    contract = module.load_contract_with_parent(CONTRACT_PATH)
    authority = load_json(AUTHORITY_PATH)
    assert raw_contract["version"] == "0.2.0"
    assert raw_contract["extends_contract"]["sha256"] == sha256(LEGACY_CONTRACT_PATH)
    assert authority["status"] == "implementation_ready_pending_explicit_retry_authorization"
    assert authority["authoritative_contract"]["sha256"] == sha256(CONTRACT_PATH)
    assert authority["rtx4090_execution_gate"]["contract_sha256"] == sha256(CONTRACT_PATH)
    assert contract["training_config"]["sha256"] == sha256(CONFIG_PATH)
    assert authority["rtx4090_execution_gate"]["training_config_sha256"] == sha256(CONFIG_PATH)
    for record in contract["frozen_inputs"].values():
        assert sha256(REPO_ROOT / record["path"]) == record["sha256"]
    for record in contract["implementation"].values():
        assert sha256(REPO_ROOT / record["path"]) == record["sha256"]
    assert sha256(REPO_ROOT / raw_contract["proposed_amendment"]["path"]) == (
        raw_contract["proposed_amendment"]["sha256"]
    )
    for record in raw_contract["attempt_history"].values():
        assert sha256(REPO_ROOT / record["path"]) == record["sha256"]
    assert contract["compatible_prior_smoke"]["smoke_audit_sha256"] == sha256(
        REPO_ROOT / (
            "09-experiments/llm_evidence_compiler_mainline/results/"
            "qwen25-4090-longest-sequence-smoke-result-v0.1.json"
        )
    )


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
    contract = load_script().load_contract_with_parent(CONTRACT_PATH)
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
    module = load_script()
    contract = module.load_contract_with_parent(CONTRACT_PATH)
    authority = load_json(AUTHORITY_PATH)
    assert contract["phase_gate"]["smoke"] == {
        "authorized": False,
        "maximum_executions": 0,
        "longest_train_examples": 16,
        "reuse_exact_prior_passed_smoke_only": True,
        "optimizer_steps": 0,
        "adapter_or_checkpoint_save": False,
    }
    assert contract["phase_gate"]["primary"]["authorized_after_explicit_user_reauthorization"] is False
    assert contract["phase_gate"]["primary"]["maximum_executions"] == 1
    assert contract["phase_gate"]["primary"]["resume_authorized"] is False
    assert authority["rtx4090_execution_gate"]["maximum_smoke_executions"] == 0
    assert authority["rtx4090_execution_gate"]["maximum_primary_executions"] == 1
    assert authority["rtx4090_execution_gate"]["primary_training_after_passed_smoke_authorized"] is False


def test_corrected_smoke_authority_preserves_single_optimizer_bearing_execution():
    authority = load_json(LEGACY_AUTHORITY_PATH)
    correction = authority["corrected_smoke_authority"]
    assert authority["version"] == "0.30.1"
    assert correction["first_launcher_attempt_forward_calls"] == 0
    assert correction["first_launcher_attempt_backward_calls"] == 0
    assert correction["first_launcher_attempt_optimizer_steps"] == 0
    assert correction["first_launcher_attempt_adapter_or_checkpoint_writes"] == 0
    assert correction["first_launcher_attempt_counts_as_optimizer_bearing_smoke_execution"] is False
    assert correction["corrected_smoke_rerun_authorized"] is True
    assert correction["maximum_optimizer_bearing_smoke_executions"] == 1
    assert correction["automatic_retry_after_corrected_smoke_authorized"] is False
    assert correction["scientific_configuration_change_authorized"] is False
    assert authority["rtx4090_execution_gate"]["maximum_optimizer_bearing_smoke_executions"] == 1


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


def test_v02_releases_only_unused_cache_after_free_threshold_is_crossed():
    module = load_script()
    config = load_json(CONFIG_PATH)
    threshold = config["hardware"]["minimum_synchronized_free_bytes"]
    assert module.should_release_allocator_cache(
        {"free_bytes": threshold}, config
    ) is False
    assert module.should_release_allocator_cache(
        {"free_bytes": threshold - 1}, config
    ) is True
    legacy = load_json(LEGACY_CONFIG_PATH)
    assert module.should_release_allocator_cache(
        {"free_bytes": 0}, legacy
    ) is False


def test_v02_preserves_scientific_configuration_and_memory_thresholds():
    original = load_json(LEGACY_CONFIG_PATH)
    revised = load_json(CONFIG_PATH)
    frozen = [
        "base_model_id", "base_resolved_commit", "quantization", "lora", "data",
        "sequence_length", "allow_truncation", "micro_batch_size",
        "gradient_accumulation_steps", "effective_batch_size", "epochs",
        "optimizer_steps", "optimizer_steps_per_epoch", "learning_rate",
        "optimizer", "weight_decay", "scheduler", "gradient_checkpointing",
        "maximum_gradient_norm", "seed", "loss_mask", "checkpointing",
    ]
    for field in frozen:
        assert revised[field] == original[field], field
    for field in [
        "maximum_peak_allocated_bytes", "minimum_synchronized_free_bytes",
        "maximum_post_cleanup_reserved_bytes", "peak_reserved_is_diagnostic_only",
    ]:
        assert revised["hardware"][field] == original["hardware"][field], field
    assert revised["hardware"]["cache_normalized_free_memory_gate"] is True
    assert revised["output_policy"]["run_subdirectory"] == "server-output/primary-v0.2"


def test_model_inventory_consumes_shared_preflight_schema():
    module = load_script()
    report = module.build_model_inventory(
        trainable=40,
        total=10_000,
        parameter_gate={"ratio": 0.004, "passed": True},
        module_gate={
            "counts": {"q_proj": 28, "down_proj": 28},
            "total_matches": 56,
            "all_target_families_present": True,
        },
    )
    assert report == {
        "trainable_parameters": 40,
        "total_parameters": 10_000,
        "trainable_ratio": 0.004,
        "target_module_counts": {"q_proj": 28, "down_proj": 28},
        "all_target_families_present": True,
    }


def test_launcher_discards_pathological_login_environment_and_binds_uuid():
    text = LAUNCHER_PATH.read_text(encoding="utf-8")
    assert "/usr/bin/env -i" in text
    assert "LD_LIBRARY_PATH" not in text
    assert 'CUDA_VISIBLE_DEVICES="${physical_gpu_uuid}"' in text
    assert 'expected="${smoke_gpu_uuid}"' in text
    assert "nvidia-smi --query-gpu=index,uuid,name,memory.free,memory.used" in text
    assert "memory.free" in text
    assert "memory.used" in text
    assert "runtime-ready-v0.1" in text
    assert "pip install" not in text


def test_downstream_scopes_remain_closed():
    contract = load_script().load_contract_with_parent(CONTRACT_PATH)
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
