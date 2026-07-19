"""Run the zero-step, zero-generation Project05 primary QLoRA preflight."""

from __future__ import annotations

import argparse
import gc
import importlib.metadata
import importlib.util
import os
import shutil
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_HELPER_PATH = Path(__file__).with_name("train_qwen_qlora_primary.py")
PREPARE_HELPER_PATH = Path(__file__).with_name("prepare_qwen_qlora_smoke.py")


def _load_helper(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no module loader")
    spec.loader.exec_module(module)
    return module


PRIMARY = _load_helper(PRIMARY_HELPER_PATH, "project05_primary_training_helpers")
PREPARE = _load_helper(PREPARE_HELPER_PATH, "project05_smoke_prepare_helpers")
load_json = PRIMARY.load_json
sha256_file = PRIMARY.sha256_file
require_primary_path = PRIMARY.require_primary_path
write_json_no_overwrite = PRIMARY.SMOKE.write_json_no_overwrite


def _require_equal(observed: Any, expected: Any, label: str) -> None:
    if observed != expected:
        raise ValueError(f"{label} differs from the preflight contract")


def verify_preflight_contract(
    contract_path: Path,
    primary_contract_path: Path,
    config_path: Path,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    contract_path = require_primary_path(contract_path, repo_root, "preflight contract")
    primary_contract_path = require_primary_path(
        primary_contract_path, repo_root, "primary contract"
    )
    config_path = require_primary_path(config_path, repo_root, "training config")
    contract = load_json(contract_path)
    _require_equal(
        primary_contract_path,
        (repo_root / contract["primary_training_contract"]["path"]).resolve(),
        "primary contract path",
    )
    _require_equal(
        config_path,
        (repo_root / contract["training_config"]["path"]).resolve(),
        "training config path",
    )
    _require_equal(
        sha256_file(primary_contract_path),
        contract["primary_training_contract"]["sha256"],
        "primary contract SHA-256",
    )
    _require_equal(
        sha256_file(config_path),
        contract["training_config"]["sha256"],
        "training config SHA-256",
    )
    parent = contract["parent_authority"]
    _require_equal(
        sha256_file(repo_root / parent["path"]),
        parent["sha256"],
        "parent authority SHA-256",
    )
    for name, record in contract["tracked_inputs"].items():
        _require_equal(
            sha256_file(repo_root / record["path"]),
            record["sha256"],
            f"{name} SHA-256",
        )
    verified = PRIMARY.verify_contract_files(
        primary_contract_path, config_path, repo_root
    )
    return {
        "contract": contract,
        "primary_contract": verified["contract"],
        "config": verified["config"],
    }


def require_preflight_authority(
    authority: dict[str, Any],
    contract_path: Path,
    primary_contract_path: Path,
    config_path: Path,
) -> dict[str, Any]:
    gate = authority.get("preflight_gate")
    if not gate or not gate.get("authorized"):
        raise PermissionError("primary preflight is not authorized")
    if gate.get("contract_sha256") != sha256_file(contract_path):
        raise ValueError("preflight authority contract SHA-256 mismatch")
    if gate.get("primary_contract_sha256") != sha256_file(primary_contract_path):
        raise ValueError("preflight authority primary contract SHA-256 mismatch")
    if gate.get("training_config_sha256") != sha256_file(config_path):
        raise ValueError("preflight authority training config SHA-256 mismatch")
    if authority.get("next_gate", {}).get("primary_training_authorized"):
        raise ValueError("preflight authority cannot also authorize primary training")
    return gate


def project_primary_wall_time(
    smoke_step_seconds: float,
    optimizer_steps: int,
    multiplier: float,
    validation_and_io_hours: float,
    maximum_hours: float,
) -> dict[str, Any]:
    if min(
        smoke_step_seconds,
        optimizer_steps,
        multiplier,
        validation_and_io_hours,
        maximum_hours,
    ) <= 0:
        raise ValueError("time projection inputs must be positive")
    linear = smoke_step_seconds * optimizer_steps / 3600
    conservative = linear * multiplier + validation_and_io_hours
    return {
        "smoke_step_seconds": smoke_step_seconds,
        "optimizer_steps": optimizer_steps,
        "linear_training_hours": linear,
        "conservative_multiplier": multiplier,
        "validation_and_checkpoint_io_reserve_hours": validation_and_io_hours,
        "conservative_total_hours": conservative,
        "maximum_hours": maximum_hours,
        "passed": conservative <= maximum_hours,
        "interpretation": "capacity_projection_not_a_training_result",
    }


def summarize_target_module_inventory(
    module_names: list[str], target_modules: list[str]
) -> dict[str, Any]:
    counts = {
        target: sum(
            name == target or name.endswith(f".{target}") for name in module_names
        )
        for target in target_modules
    }
    missing = sorted(target for target, count in counts.items() if count == 0)
    if missing:
        raise ValueError(f"target module families are missing: {missing}")
    return {
        "counts": counts,
        "total_matches": sum(counts.values()),
        "all_target_families_present": True,
    }


def validate_trainable_ratio(
    trainable: int, total: int, maximum_ratio: float
) -> dict[str, Any]:
    if trainable <= 0 or total <= 0 or trainable > total:
        raise ValueError("trainable and total parameter counts are invalid")
    ratio = trainable / total
    if ratio >= maximum_ratio:
        raise ValueError("trainable parameter ratio is not strictly below the limit")
    return {
        "trainable_parameters": trainable,
        "total_parameters": total,
        "ratio": ratio,
        "maximum_ratio": maximum_ratio,
        "passed": True,
    }


def sanitize_dataset_report(report: dict[str, Any]) -> dict[str, Any]:
    output = {
        "train": {
            "examples": report["train"]["examples"],
            "decisions": report["train"]["decisions"],
            "families": report["train"]["families"],
        },
        "training_validation": {
            "examples": report["training_validation"]["examples"],
            "decisions": report["training_validation"]["decisions"],
            "families": report["training_validation"]["families"],
        },
        "family_overlap": report["family_overlap"],
    }
    def walk_keys(value: Any) -> set[str]:
        if isinstance(value, dict):
            keys = set(value)
            for item in value.values():
                keys.update(walk_keys(item))
            return keys
        if isinstance(value, list):
            keys = set()
            for item in value:
                keys.update(walk_keys(item))
            return keys
        return set()

    if walk_keys(output) & {"payload", "example_id", "candidate", "pointer"}:
        raise ValueError("sanitized dataset report contains raw example material")
    return output


def validate_output_path(output: Path, run_root: Path) -> Path:
    output = Path(output).resolve()
    run_root = Path(run_root).resolve()
    expected = (run_root / "local-output" / "primary-preflight-v0.1.json").resolve()
    if output != expected:
        raise ValueError("preflight output path differs from the exact local path")
    if not PRIMARY.is_within(output, run_root):
        raise ValueError("preflight output escapes the local run root")
    if output.exists():
        raise FileExistsError("refusing to overwrite the existing preflight output")
    return output


def _package_versions(expected: dict[str, str]) -> dict[str, str]:
    observed = {}
    for package, version in expected.items():
        if package == "python":
            continue
        actual = importlib.metadata.version(package)
        if actual != version:
            raise ValueError(f"runtime package version mismatch: {package}")
        observed[package] = actual
    return observed


def _local_input_path(
    contract: dict[str, Any], name: str, repo_root: Path = REPO_ROOT
) -> Path:
    record = contract["local_inputs"][name]
    path = require_primary_path(repo_root / record["path"], repo_root, name)
    _require_equal(sha256_file(path), record["sha256"], f"{name} SHA-256")
    return path


def run_preflight(
    contract_path: Path,
    authority_path: Path,
    primary_contract_path: Path,
    config_path: Path,
    run_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    verified = verify_preflight_contract(
        contract_path, primary_contract_path, config_path
    )
    contract = verified["contract"]
    primary_contract = verified["primary_contract"]
    config = verified["config"]
    authority_path = require_primary_path(authority_path, REPO_ROOT, "authority")
    authority = load_json(authority_path)
    require_preflight_authority(
        authority, contract_path, primary_contract_path, config_path
    )
    run_root = require_primary_path(run_root, REPO_ROOT, "run root")
    expected_run_root = (
        REPO_ROOT / contract["execution_boundary"]["run_directory_name"]
    ).resolve()
    _require_equal(run_root, expected_run_root, "run root")
    if os.name != "nt":
        raise ValueError("local primary preflight is Windows-only")
    output_path = validate_output_path(output_path, run_root)

    preparation_path = _local_input_path(contract, "smoke_preparation_audit")
    train_path = _local_input_path(contract, "train_pairs")
    validation_path = _local_input_path(contract, "training_validation_pairs")
    preparation = load_json(preparation_path)
    _require_equal(
        preparation["status"],
        "passed_runtime_and_fixed_revision_weight_gate",
        "smoke preparation status",
    )

    train_record = primary_contract["pair_payloads"]["train"]
    validation_record = primary_contract["pair_payloads"]["training_validation"]
    train = PRIMARY.load_pair_file(train_path, train_record["sha256"])
    training_validation = PRIMARY.load_pair_file(
        validation_path, validation_record["sha256"]
    )
    dataset_report = PRIMARY.validate_primary_datasets(
        train, training_validation, config
    )
    del train
    del training_validation

    smoke_contract_record = contract["tracked_inputs"]["smoke_contract"]
    smoke_contract = load_json(REPO_ROOT / smoke_contract_record["path"])
    snapshot_dir = require_primary_path(
        Path(preparation["model_snapshot"]["snapshot_dir"]),
        REPO_ROOT,
        "model snapshot",
    )
    model_lock = PREPARE.verify_snapshot(smoke_contract, snapshot_dir, run_root)
    package_versions = _package_versions(smoke_contract["runtime_packages"])

    try:
        import torch
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    except ImportError as error:
        raise RuntimeError("the frozen local QLoRA runtime is unavailable") from error

    if not torch.cuda.is_available():
        raise ValueError("CUDA is unavailable")
    gpu_name = torch.cuda.get_device_name(0)
    _require_equal(gpu_name, config["hardware"]["execution_target"], "GPU name")
    compute_capability = list(torch.cuda.get_device_capability(0))
    _require_equal(
        compute_capability,
        config["hardware"]["minimum_compute_capability"],
        "compute capability",
    )
    total_vram = torch.cuda.get_device_properties(0).total_memory
    minimum_vram = int(config["hardware"]["minimum_total_vram_gib"] * 1024**3)
    if total_vram < minimum_vram:
        raise ValueError("GPU total VRAM is below the preflight minimum")

    compute_dtype = {"float16": torch.float16}[
        config["quantization"]["compute_dtype"]
    ]
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=config["quantization"]["type"],
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=config["quantization"]["double_quantization"],
    )
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(0)
    model = AutoModelForCausalLM.from_pretrained(
        snapshot_dir,
        local_files_only=True,
        trust_remote_code=False,
        quantization_config=quantization,
        device_map={"": 0},
        torch_dtype=compute_dtype,
    )
    module_inventory = summarize_target_module_inventory(
        [name for name, _ in model.named_modules()],
        config["lora"]["target_modules"],
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(
        model, use_gradient_checkpointing=config["gradient_checkpointing"]
    )
    lora = LoraConfig(
        r=config["lora"]["rank"],
        lora_alpha=config["lora"]["alpha"],
        lora_dropout=config["lora"]["dropout"],
        bias=config["lora"]["bias"],
        target_modules=config["lora"]["target_modules"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    trainable = sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )
    total = sum(parameter.numel() for parameter in model.parameters())
    parameter_gate = validate_trainable_ratio(
        trainable,
        total,
        primary_contract["frozen_training_snapshot"]["maximum_trainable_ratio"],
    )
    peak_vram = torch.cuda.max_memory_reserved(0)
    peak_limit = int(
        config["hardware"]["maximum_operational_peak_vram_gib"] * 1024**3
    )
    if peak_vram > peak_limit:
        raise ValueError("preflight peak reserved VRAM exceeds the frozen limit")
    del model
    del lora
    del quantization
    gc.collect()
    torch.cuda.empty_cache()
    post_cleanup_reserved = torch.cuda.memory_reserved(0)

    smoke_result_record = contract["tracked_inputs"]["smoke_result"]
    smoke_result = load_json(REPO_ROOT / smoke_result_record["path"])
    projection_contract = contract["time_projection"]
    _require_equal(
        smoke_result["smoke_gate"]["wall_seconds"],
        projection_contract["smoke_optimizer_step_seconds"],
        "smoke step seconds",
    )
    wall_projection = project_primary_wall_time(
        projection_contract["smoke_optimizer_step_seconds"],
        projection_contract["primary_optimizer_steps"],
        projection_contract["conservative_multiplier"],
        projection_contract["validation_and_checkpoint_io_reserve_hours"],
        projection_contract["maximum_projected_hours"],
    )
    if not wall_projection["passed"]:
        raise ValueError("projected primary wall time exceeds the frozen limit")

    resource_bytes = PRIMARY.unique_physical_bytes(
        [
            run_root / "local-runtime",
            run_root / "local-cache",
            run_root / "local-output",
        ]
    )
    resource_projection = contract["resource_projection"]
    projected_resource_bytes = (
        resource_bytes + resource_projection["checkpoint_and_result_reserve_bytes"]
    )
    if projected_resource_bytes > resource_projection["maximum_total_bytes"]:
        raise ValueError("projected local resource bytes exceed the frozen limit")
    disk = shutil.disk_usage(REPO_ROOT)

    result = {
        "schema_version": "project05-qwen25-primary-preflight-result-v0.1",
        "status": "passed_zero_step_primary_preflight",
        "created_date": contract["created_date"],
        "contract_id": contract["contract_id"],
        "contract_sha256": sha256_file(contract_path),
        "authority_sha256": sha256_file(authority_path),
        "primary_contract_sha256": sha256_file(primary_contract_path),
        "training_config_sha256": sha256_file(config_path),
        "data_gate": sanitize_dataset_report(dataset_report),
        "model_snapshot": {
            "repository_id": model_lock["repository_id"],
            "revision": model_lock["revision"],
            "file_count": model_lock["file_count"],
            "repository_bytes": model_lock["repository_bytes"],
            "weight_bytes": model_lock["weight_bytes"],
            "all_allowlisted_files_rehashed": True,
        },
        "runtime": {
            "python": preparation["runtime"]["python"],
            "packages": package_versions,
            "torch_cuda": str(torch.version.cuda),
            "gpu_name": gpu_name,
            "compute_capability": compute_capability,
            "total_vram_bytes": total_vram,
        },
        "lora_inventory": {
            "target_modules": config["lora"]["target_modules"],
            **module_inventory,
            **parameter_gate,
            "adapter_attached_in_memory_only": True,
            "adapter_saved": False,
        },
        "memory_gate": {
            "peak_reserved_bytes": peak_vram,
            "peak_limit_bytes": peak_limit,
            "post_cleanup_reserved_bytes": post_cleanup_reserved,
            "passed": True,
        },
        "wall_time_projection": wall_projection,
        "resource_gate": {
            "current_runtime_cache_output_bytes": resource_bytes,
            "checkpoint_and_result_reserve_bytes": resource_projection[
                "checkpoint_and_result_reserve_bytes"
            ],
            "projected_total_bytes": projected_resource_bytes,
            "maximum_total_bytes": resource_projection["maximum_total_bytes"],
            "disk_free_bytes": disk.free,
            "passed": True,
        },
        "execution": {
            "preflight_wall_seconds": time.monotonic() - started,
            "model_forward_calls": 0,
            "generation_calls": 0,
            "loss_calls": 0,
            "backward_calls": 0,
            "optimizer_objects_created": 0,
            "optimizer_steps": 0,
            "scheduler_objects_created": 0,
            "adapter_or_checkpoint_files_written": 0,
            "network_or_download_used": False,
        },
        "privacy_and_scope": {
            "raw_pair_payload_recorded": False,
            "example_ids_recorded": False,
            "raw_model_output_recorded": False,
            "development_or_test_accessed": False,
            "c07_c12_accessed": False,
            "m3_integrated": False,
            "server_connected": False,
            "paper_a_modified": False,
        },
        "next_gate": {
            "status": "hard_stop_for_primary_training_authorization",
            "primary_training_authorized": False,
            "formal_inference_authorized": False,
            "c07_c12_execution_authorized": False,
            "m3_integration_authorized": False,
        },
    }
    write_json_no_overwrite(output_path, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--primary-contract", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_preflight(
        args.contract,
        args.authority,
        args.primary_contract,
        args.config,
        args.run_root,
        args.output,
    )
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
