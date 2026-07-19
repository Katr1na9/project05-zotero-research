import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "09-experiments/scripts/diagnose_qwen_qlora_optimizer_4090.py"
CONTRACT_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "qwen25-qlora-4090-training-contract-v0.3.json"
)
AUTHORITY_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.33.json"
)
CONFIG_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.3/"
    "training-config-v0.3.json"
)
V02_CONFIG_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.2/"
    "training-config-v0.2.json"
)
V02_CONTRACT_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "qwen25-qlora-4090-training-contract-v0.2.json"
)
AMENDMENT_PATH = REPO_ROOT / (
    "08-writing/llm-evidence-compiler-qwen25-4090-optimizer-stability-"
    "amendment-v0.33-20260719.md"
)
LAUNCHER_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.3/"
    "run-optimizer-stability-4090-v0.3.sh"
)
FAILURE_SUMMARY_PATH = REPO_ROOT / (
    "09-experiments/llm_evidence_compiler_mainline/results/"
    "qwen25-4090-primary-v0.2-failure-summary-v0.1.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_script():
    spec = importlib.util.spec_from_file_location(
        "project05_optimizer_stability_test", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v033_hash_chain_and_single_diagnostic_authority_are_closed():
    contract = load_json(CONTRACT_PATH)
    authority = load_json(AUTHORITY_PATH)
    assert contract["extends_contract"]["sha256"] == sha256(V02_CONTRACT_PATH)
    assert contract["training_config"]["sha256"] == sha256(CONFIG_PATH)
    assert contract["approved_optimizer_amendment"]["sha256"] == sha256(AMENDMENT_PATH)
    assert authority["authoritative_contract"]["sha256"] == sha256(CONTRACT_PATH)
    assert authority["optimizer_stability_gate"]["contract_sha256"] == sha256(CONTRACT_PATH)
    assert authority["optimizer_stability_gate"]["training_config_sha256"] == sha256(CONFIG_PATH)
    assert authority["optimizer_stability_gate"]["maximum_executions"] == 1
    assert authority["optimizer_stability_gate"]["formal_primary_authorized"] is False
    for record in contract["implementation"].values():
        assert sha256(REPO_ROOT / record["path"]) == record["sha256"]


def test_optimizer_change_is_isolated_from_scientific_configuration():
    previous = load_json(V02_CONFIG_PATH)
    revised = load_json(CONFIG_PATH)
    frozen = [
        "base_model_id", "base_resolved_commit", "quantization", "lora", "data",
        "sequence_length", "allow_truncation", "micro_batch_size",
        "gradient_accumulation_steps", "effective_batch_size", "epochs",
        "optimizer_steps", "optimizer_steps_per_epoch", "learning_rate",
        "weight_decay", "scheduler", "gradient_checkpointing",
        "maximum_gradient_norm", "seed", "loss_mask",
    ]
    for field in frozen:
        assert revised[field] == previous[field], field
    assert previous["optimizer"] == "paged_adamw_8bit"
    assert revised["optimizer"] == "adamw_torch"
    assert revised["optimizer_parameters"] == {
        "betas": [0.9, 0.999],
        "eps": 1e-8,
        "foreach": False,
        "fused": False,
        "capturable": False,
    }
    for field in [
        "maximum_peak_allocated_bytes", "minimum_synchronized_free_bytes",
        "maximum_post_cleanup_reserved_bytes", "peak_reserved_is_diagnostic_only",
        "cache_normalized_free_memory_gate",
    ]:
        assert revised["hardware"][field] == previous["hardware"][field], field


def test_diagnostic_exceeds_old_failure_point_without_saving_state():
    config = load_json(CONFIG_PATH)
    diagnostic = config["optimizer_stability_diagnostic"]
    failure = load_json(FAILURE_SUMMARY_PATH)
    assert failure["optimizer_steps_completed"] == 173
    assert failure["memory_gate"]["passed"] is True
    assert diagnostic["must_exceed_failed_step"] == 173
    assert diagnostic["optimizer_steps"] == 180
    assert diagnostic["optimizer_steps"] > failure["optimizer_steps_completed"]
    assert diagnostic["microbatches"] == (
        diagnostic["optimizer_steps"] * config["gradient_accumulation_steps"]
    )
    assert diagnostic["save_adapter"] is False
    assert diagnostic["save_checkpoint"] is False
    assert diagnostic["generation_calls"] == 0


def test_torch_adamw_factory_is_single_tensor_and_fully_pinned():
    module = load_script()
    config = load_json(CONFIG_PATH)
    captured = {}

    def adamw(parameters, **kwargs):
        captured["parameters"] = parameters
        captured["kwargs"] = kwargs
        return "optimizer"

    stack = {"torch": SimpleNamespace(optim=SimpleNamespace(AdamW=adamw))}
    parameters = [object(), object()]
    assert module.build_torch_adamw(stack, parameters, config) == "optimizer"
    assert captured == {
        "parameters": parameters,
        "kwargs": {
            "lr": 0.0002,
            "weight_decay": 0.0,
            "betas": (0.9, 0.999),
            "eps": 1e-8,
            "foreach": False,
            "fused": False,
            "capturable": False,
        },
    }


def test_launcher_is_home_scoped_gpu_bound_and_synchronous():
    text = LAUNCHER_PATH.read_text(encoding="utf-8")
    assert 'readonly ALLOWED_HOME="/home/myy"' in text
    assert 'readonly RUN_ROOT="${ALLOWED_HOME}/project05-qwen25-4090-v0.1"' in text
    assert "/usr/bin/env -i" in text
    assert 'CUDA_VISIBLE_DEVICES="${physical_gpu_uuid}"' in text
    assert 'CUDA_LAUNCH_BLOCKING="1"' in text
    assert 'expected="${smoke_gpu_uuid}"' in text
    assert "--smoke-audit" in text
    assert "pip install" not in text
    assert "--phase primary" not in text


def test_formal_and_downstream_scopes_remain_closed():
    contract = load_json(CONTRACT_PATH)
    authority = load_json(AUTHORITY_PATH)
    closed = {
        "formal_primary_training",
        "automatic_retry_or_resume",
        "v0_2_checkpoint_selection_or_resume",
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
    assert closed <= set(authority["not_authorized"])
    assert authority["next_gate"]["formal_primary_authorized"] is False
    assert authority["next_gate"]["checkpoint_selection_authorized"] is False
    assert authority["next_gate"]["m3_integration_authorized"] is False
