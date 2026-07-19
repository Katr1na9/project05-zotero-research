import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments/scripts/execute_qwen_qlora_4090_adamw_primary.py"
CONTRACT = ROOT / "09-experiments/llm_evidence_compiler_mainline/contracts/qwen25-qlora-4090-training-contract-v0.4.json"
AUTHORITY = ROOT / "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.35.json"
CONFIG = ROOT / "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.4/training-config-v0.4.json"
V02_CONFIG = ROOT / "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.2/training-config-v0.2.json"
LAUNCHER = ROOT / "09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.4/run-adamw-primary-4090-v0.4.sh"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_hash_chain_and_single_fresh_execution():
    contract, authority = load(CONTRACT), load(AUTHORITY)
    assert authority["authoritative_contract"]["sha256"] == sha(CONTRACT)
    assert authority["fresh_adamw_primary_gate"]["contract_sha256"] == sha(CONTRACT)
    assert authority["fresh_adamw_primary_gate"]["training_config_sha256"] == sha(CONFIG)
    assert contract["training_config"]["sha256"] == sha(CONFIG)
    assert authority["fresh_adamw_primary_gate"]["maximum_executions"] == 1
    assert authority["fresh_adamw_primary_gate"]["fresh_initialization_required"] is True
    assert authority["fresh_adamw_primary_gate"]["resume_authorized"] is False
    for record in contract["implementation"].values():
        assert sha(ROOT / record["path"]) == record["sha256"]


def test_only_optimizer_implementation_and_output_route_change():
    old, new = load(V02_CONFIG), load(CONFIG)
    frozen = [
        "base_model_id", "base_resolved_commit", "quantization", "lora", "data",
        "sequence_length", "allow_truncation", "micro_batch_size",
        "gradient_accumulation_steps", "effective_batch_size", "epochs",
        "optimizer_steps", "optimizer_steps_per_epoch", "learning_rate", "weight_decay",
        "scheduler", "gradient_checkpointing", "maximum_gradient_norm", "seed",
        "loss_mask", "checkpointing", "hardware", "resource_limits",
    ]
    for field in frozen:
        assert new[field] == old[field], field
    assert old["optimizer"] == "paged_adamw_8bit"
    assert new["optimizer"] == "adamw_torch"
    assert new["optimizer_parameters"] == {
        "betas": [0.9, 0.999], "eps": 1e-8, "foreach": False,
        "fused": False, "capturable": False,
    }
    assert new["output_policy"]["run_subdirectory"] == "server-output/primary-adamw-v0.35"


def test_launcher_is_scoped_and_does_not_enable_synchronous_diagnostic_mode():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'readonly ALLOWED_HOME="/home/myy"' in text
    assert 'CUDA_VISIBLE_DEVICES="${physical_gpu_uuid}"' in text
    assert "CUDA_LAUNCH_BLOCKING" not in text
    assert "pip install" not in text
    assert "primary-adamw-v0.35" not in text
    assert "--smoke-audit" in text


def test_formal_runner_is_importable_and_downstream_remains_closed():
    spec = importlib.util.spec_from_file_location("project05_adamw_primary_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    authority = load(AUTHORITY)
    assert module.AUDIT_NAME.endswith("audit-v0.1.json")
    assert authority["next_gate"]["checkpoint_selection_authorized"] is False
    assert authority["next_gate"]["training_validation_generation_authorized"] is False
    assert authority["next_gate"]["m3_integration_authorized"] is False
