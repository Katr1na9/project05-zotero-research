"""Run the authorized single-GPU RTX 4090 QLoRA smoke or primary phase.

The script is Linux-only and fail-closed to
/home/myy/project05-qwen25-4090-v0.1.  Smoke and primary are separate fresh
processes.  The smoke discards all trainable state; primary starts from the
fixed base snapshot and writes adapter-only epoch checkpoints.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import json
import math
import os
import random
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_HELPER = Path(__file__).with_name("train_qwen_qlora_primary.py")
PREFLIGHT_HELPER = Path(__file__).with_name("preflight_qwen_qlora_primary.py")
PREPARE_HELPER = Path(__file__).with_name("prepare_qwen_qlora_smoke.py")
SMOKE_AUDIT_NAME = "4090-longest-sequence-smoke-v0.1.json"
PRIMARY_AUDIT_NAME = "4090-primary-training-audit-v0.1.json"
PRIMARY_FAILURE_NAME = "4090-primary-training-failure-v0.1.json"
PROGRESS_NAME = "4090-primary-training-progress-v0.1.jsonl"


def _load_helper(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no module loader")
    spec.loader.exec_module(module)
    return module


PRIMARY = _load_helper(PRIMARY_HELPER, "project05_4090_primary_helpers")
PREFLIGHT = _load_helper(PREFLIGHT_HELPER, "project05_4090_preflight_helpers")
PREPARE = _load_helper(PREPARE_HELPER, "project05_4090_prepare_helpers")
load_json = PRIMARY.load_json
sha256_file = PRIMARY.sha256_file
sha256_text = PRIMARY.sha256_text
canonical_json = PRIMARY.canonical_json
encode_assistant_only = PRIMARY.encode_assistant_only
write_json_no_overwrite = PRIMARY.SMOKE.write_json_no_overwrite


def is_within(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def require_within(path: Path, root: Path, label: str) -> Path:
    resolved = Path(path).resolve()
    if not is_within(resolved, root):
        raise ValueError(f"{label} escapes the RTX 4090 execution boundary")
    return resolved


def validate_server_boundary(
    contract: dict[str, Any], run_root: Path, repo_root: Path = REPO_ROOT,
    platform_name: str | None = None,
) -> dict[str, Path]:
    platform_name = os.name if platform_name is None else platform_name
    boundary = contract["server_execution_boundary"]
    allowed_home = Path(boundary["allowed_home"]).resolve()
    expected_root = (allowed_home / boundary["run_directory_name"]).resolve()
    run_root = Path(run_root).resolve()
    repo_root = Path(repo_root).resolve()
    if platform_name != "posix":
        raise ValueError("RTX 4090 execution is Linux-only")
    if allowed_home != Path("/home/myy"):
        raise ValueError("allowed home differs from /home/myy")
    if run_root != expected_root:
        raise ValueError("run root differs from the exact RTX 4090 path")
    expected_repo = (run_root / boundary["bundle_subdirectory"]).resolve()
    if repo_root != expected_repo:
        raise ValueError("execution bundle differs from the exact contracted path")
    require_within(repo_root, run_root, "execution bundle")
    return {"allowed_home": allowed_home, "run_root": run_root, "repo_root": repo_root}


def validate_memory_gate(samples: list[dict[str, int]], config: dict[str, Any]) -> dict[str, Any]:
    if not samples:
        raise ValueError("memory samples are empty")
    hardware = config["hardware"]
    peak_allocated = max(row["allocated_bytes"] for row in samples)
    peak_reserved = max(row["reserved_bytes"] for row in samples)
    minimum_free = min(row["free_bytes"] for row in samples)
    passed = (
        peak_allocated <= hardware["maximum_peak_allocated_bytes"]
        and minimum_free >= hardware["minimum_synchronized_free_bytes"]
    )
    return {
        "sample_count": len(samples),
        "peak_allocated_bytes": peak_allocated,
        "maximum_peak_allocated_bytes": hardware["maximum_peak_allocated_bytes"],
        "peak_reserved_bytes_diagnostic": peak_reserved,
        "peak_reserved_is_blocking": False,
        "minimum_free_bytes": minimum_free,
        "minimum_synchronized_free_bytes": hardware["minimum_synchronized_free_bytes"],
        "passed": passed,
    }


def should_release_allocator_cache(sample: dict[str, int], config: dict[str, Any]) -> bool:
    """Return whether unused allocator cache must be released before the blocking sample."""
    hardware = config["hardware"]
    return bool(hardware.get("cache_normalized_free_memory_gate", False)) and (
        sample["free_bytes"] < hardware["minimum_synchronized_free_bytes"]
    )


def synchronized_memory_sample(torch: Any, event: str, step: int) -> dict[str, Any]:
    torch.cuda.synchronize(0)
    free, total = torch.cuda.mem_get_info(0)
    return {
        "event": event,
        "step": step,
        "allocated_bytes": int(torch.cuda.memory_allocated(0)),
        "reserved_bytes": int(torch.cuda.memory_reserved(0)),
        "free_bytes": int(free),
        "total_bytes": int(total),
    }


def _verify_hash_record(record: dict[str, str], label: str) -> Path:
    path = require_within(REPO_ROOT / record["path"], REPO_ROOT, label)
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"{label} SHA-256 mismatch")
    return path


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_contract_with_parent(contract_path: Path) -> dict[str, Any]:
    raw = load_json(contract_path)
    parent_record = raw.get("extends_contract")
    if parent_record is None:
        return raw
    parent_path = _verify_hash_record(parent_record, "parent contract")
    parent = load_json(parent_path)
    return _deep_merge(parent, raw)


def verify_static_authority(
    contract_path: Path,
    config_path: Path,
    authority_path: Path,
    run_root: Path,
) -> dict[str, Any]:
    contract_path = require_within(contract_path, REPO_ROOT, "contract")
    config_path = require_within(config_path, REPO_ROOT, "config")
    authority_path = require_within(authority_path, REPO_ROOT, "authority")
    contract = load_contract_with_parent(contract_path)
    expected_authority = require_within(
        REPO_ROOT / contract["authority_repository_path"], REPO_ROOT, "contract authority"
    )
    if authority_path != expected_authority:
        raise ValueError("authority path differs from the contract")
    boundary = validate_server_boundary(contract, run_root)
    config = load_json(config_path)
    authority = load_json(authority_path)
    if sha256_file(config_path) != contract["training_config"]["sha256"]:
        raise ValueError("training config differs from the contract")
    gate = authority["rtx4090_execution_gate"]
    if gate["contract_sha256"] != sha256_file(contract_path):
        raise ValueError("authority contract SHA-256 mismatch")
    if gate["training_config_sha256"] != sha256_file(config_path):
        raise ValueError("authority config SHA-256 mismatch")
    if not (
        gate.get("environment_and_weight_preparation_authorized", False)
        or gate.get("existing_preparation_reuse_authorized", False)
    ):
        raise PermissionError("environment preparation or reuse is not authorized")
    if not (
        gate.get("longest_sequence_smoke_authorized", False)
        or gate.get("compatible_prior_smoke_reuse_authorized", False)
    ):
        raise PermissionError("4090 smoke execution or exact reuse is not authorized")
    if not gate["primary_training_after_passed_smoke_authorized"]:
        raise PermissionError("primary training is not authorized")
    expected_smoke_executions = (
        1 if gate.get("longest_sequence_smoke_authorized", False) else 0
    )
    if (
        gate["maximum_smoke_executions"] != expected_smoke_executions
        or gate["maximum_primary_executions"] != 1
    ):
        raise ValueError("authority permits an unexpected smoke or primary run count")
    for label, record in contract["frozen_inputs"].items():
        _verify_hash_record(record, label)
    for label, record in contract["implementation"].items():
        _verify_hash_record(record, label)
    return {
        "contract": contract,
        "config": config,
        "authority": authority,
        **boundary,
    }


def verify_runtime_and_inputs(
    verified: dict[str, Any], preparation_audit_path: Path, pair_root: Path
) -> dict[str, Any]:
    contract = verified["contract"]
    config = verified["config"]
    run_root = verified["run_root"]
    preparation_audit_path = require_within(
        preparation_audit_path, run_root, "preparation audit"
    )
    pair_root = require_within(pair_root, run_root, "pair root")
    preparation = load_json(preparation_audit_path)
    if preparation.get("status") != "passed_runtime_and_fixed_revision_weight_gate":
        raise ValueError("runtime/model preparation Gate has not passed")
    current_contract_sha256 = sha256_file(
        verified["repo_root"] / contract["contract_repository_path"]
    )
    compatible_contracts = set(
        contract.get("preparation_audit_compatible_contract_sha256", [])
    )
    compatible_contracts.add(current_contract_sha256)
    if preparation.get("contract_sha256") not in compatible_contracts:
        raise ValueError("preparation audit belongs to another contract")
    snapshot_dir = require_within(
        Path(preparation["model_snapshot"]["snapshot_dir"]), run_root, "model snapshot"
    )
    model_lock = PREPARE.verify_snapshot(contract, snapshot_dir, run_root)
    train_record = contract["pair_payloads"]["train"]
    validation_record = contract["pair_payloads"]["training_validation"]
    train = PRIMARY.load_pair_file(pair_root / train_record["file"], train_record["sha256"])
    validation = PRIMARY.load_pair_file(
        pair_root / validation_record["file"], validation_record["sha256"]
    )
    data_report = PRIMARY.validate_primary_datasets(train, validation, config)
    serialization_record = contract["frozen_inputs"]["serialization_contract"]
    serialization = load_json(REPO_ROOT / serialization_record["path"])["serialization"]
    return {
        "preparation": preparation,
        "snapshot_dir": snapshot_dir,
        "model_lock": model_lock,
        "train": train,
        "validation": validation,
        "data_report": data_report,
        "serialization": serialization,
        "preparation_audit_path": preparation_audit_path,
    }


def _load_training_stack() -> dict[str, Any]:
    try:
        import bitsandbytes as bnb
        import torch
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            get_cosine_schedule_with_warmup,
        )
    except ImportError as error:
        raise RuntimeError("the frozen Linux QLoRA runtime is unavailable") from error
    return locals()


def _runtime_gpu_gate(stack: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    torch = stack["torch"]
    if not torch.cuda.is_available():
        raise ValueError("CUDA is unavailable")
    name = torch.cuda.get_device_name(0)
    capability = list(torch.cuda.get_device_capability(0))
    total = int(torch.cuda.get_device_properties(0).total_memory)
    hardware = config["hardware"]
    if name != hardware["execution_target"]:
        raise ValueError("GPU name differs from the RTX 4090 contract")
    if capability < hardware["minimum_compute_capability"]:
        raise ValueError("GPU compute capability is below the contract")
    if total < hardware["minimum_total_vram_bytes"]:
        raise ValueError("GPU total memory is below the contract")
    uuid = os.environ.get("PROJECT05_PHYSICAL_GPU_UUID", "")
    index = os.environ.get("PROJECT05_PHYSICAL_GPU_INDEX", "")
    if not uuid.startswith("GPU-") or not index.isdigit():
        raise ValueError("physical GPU UUID/index was not supplied by the launcher")
    free, _ = torch.cuda.mem_get_info(0)
    if free < hardware["maximum_peak_allocated_bytes"]:
        raise ValueError("selected RTX 4090 is no longer sufficiently idle")
    return {
        "name": name,
        "compute_capability": capability,
        "total_vram_bytes": total,
        "initial_free_bytes": int(free),
        "physical_uuid": uuid,
        "physical_index": int(index),
    }


def _build_model(
    stack: dict[str, Any], snapshot_dir: Path, config: dict[str, Any]
) -> tuple[Any, Any, list[Any], dict[str, Any]]:
    torch = stack["torch"]
    tokenizer = stack["AutoTokenizer"].from_pretrained(
        snapshot_dir, local_files_only=True, trust_remote_code=False
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    compute_dtype = {"float16": torch.float16}[config["quantization"]["compute_dtype"]]
    quantization = stack["BitsAndBytesConfig"](
        load_in_4bit=True,
        bnb_4bit_quant_type=config["quantization"]["type"],
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=config["quantization"]["double_quantization"],
    )
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(0)
    model = stack["AutoModelForCausalLM"].from_pretrained(
        snapshot_dir,
        local_files_only=True,
        trust_remote_code=False,
        quantization_config=quantization,
        device_map={"": 0},
        torch_dtype=compute_dtype,
    )
    model.config.use_cache = False
    model = stack["prepare_model_for_kbit_training"](
        model, use_gradient_checkpointing=config["gradient_checkpointing"]
    )
    lora = stack["LoraConfig"](
        r=config["lora"]["rank"],
        lora_alpha=config["lora"]["alpha"],
        lora_dropout=config["lora"]["dropout"],
        bias=config["lora"]["bias"],
        target_modules=config["lora"]["target_modules"],
        task_type="CAUSAL_LM",
    )
    model = stack["get_peft_model"](model, lora)
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    trainable = sum(parameter.numel() for parameter in parameters)
    total = sum(parameter.numel() for parameter in model.parameters())
    parameter_gate = PREFLIGHT.validate_trainable_ratio(trainable, total, 0.01)
    module_gate = PREFLIGHT.summarize_target_module_inventory(
        [name for name, _ in model.named_modules()], config["lora"]["target_modules"]
    )
    return model, tokenizer, parameters, build_model_inventory(
        trainable, total, parameter_gate, module_gate
    )


def build_model_inventory(
    trainable: int,
    total: int,
    parameter_gate: dict[str, Any],
    module_gate: dict[str, Any],
) -> dict[str, Any]:
    """Map the shared preflight reports into the 4090 execution audit schema."""
    return {
        "trainable_parameters": trainable,
        "total_parameters": total,
        "trainable_ratio": parameter_gate["ratio"],
        "target_module_counts": module_gate["counts"],
        "all_target_families_present": module_gate["all_target_families_present"],
    }


def _encode_all(examples: list[dict[str, Any]], serialization: dict[str, Any], tokenizer: Any, limit: int) -> dict[str, dict[str, list[int]]]:
    encoded = {}
    for example in examples:
        identity = example["example_id"]
        item = encode_assistant_only(example, serialization, tokenizer, limit)
        if all(label == -100 for label in item["labels"]):
            raise ValueError("assistant-only loss mask has no supervised token")
        encoded[identity] = item
    if len(encoded) != len(examples):
        raise ValueError("encoded example identities are not unique")
    return encoded


def run_smoke(
    verified: dict[str, Any], runtime: dict[str, Any], output_path: Path
) -> dict[str, Any]:
    started = time.monotonic()
    config = verified["config"]
    run_root = verified["run_root"]
    output_path = require_within(output_path, run_root, "smoke output")
    expected = (run_root / "server-output" / SMOKE_AUDIT_NAME).resolve()
    if output_path != expected:
        raise ValueError("smoke output path differs from the contract")
    if output_path.exists():
        raise FileExistsError("refusing to overwrite the 4090 smoke result")
    stack = _load_training_stack()
    torch = stack["torch"]
    gpu = _runtime_gpu_gate(stack, config)
    random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    torch.cuda.manual_seed_all(config["seed"])
    model, tokenizer, trainable_parameters, inventory = _build_model(
        stack, runtime["snapshot_dir"], config
    )
    encoded = _encode_all(
        runtime["train"], runtime["serialization"], tokenizer, config["sequence_length"]
    )
    ranked = sorted(
        runtime["train"],
        key=lambda item: (-len(encoded[item["example_id"]]["input_ids"]), sha256_text(item["example_id"])),
    )[: config["smoke"]["longest_examples"]]
    lengths = [len(encoded[item["example_id"]]["input_ids"]) for item in ranked]
    selection_rows = [
        {"example_id_sha256": sha256_text(item["example_id"]), "tokens": length}
        for item, length in zip(ranked, lengths)
    ]
    optimizer = stack["bnb"].optim.PagedAdamW8bit(
        trainable_parameters, lr=config["learning_rate"], weight_decay=config["weight_decay"]
    )
    optimizer.zero_grad(set_to_none=True)
    model.train()
    samples = [synchronized_memory_sample(torch, "model_optimizer_ready", 0)]
    losses = []
    for microbatch, example in enumerate(ranked, 1):
        item = encoded[example["example_id"]]
        batch = {
            key: torch.tensor([value], device="cuda", dtype=torch.long)
            for key, value in item.items()
        }
        loss = model(**batch).loss
        if not torch.isfinite(loss).item():
            raise ValueError("non-finite 4090 smoke loss")
        losses.append(float(loss.detach().cpu()))
        (loss / config["gradient_accumulation_steps"]).backward()
        del batch, loss
        samples.append(synchronized_memory_sample(torch, "backward_completed", microbatch))
    gradient = float(
        torch.nn.utils.clip_grad_norm_(
            trainable_parameters, config["maximum_gradient_norm"]
        ).detach().cpu()
    )
    if not math.isfinite(gradient):
        raise ValueError("non-finite 4090 smoke gradient norm")
    samples.append(synchronized_memory_sample(torch, "before_optimizer_step", 1))
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    samples.append(synchronized_memory_sample(torch, "after_optimizer_step", 1))
    memory = validate_memory_gate(samples, config)
    if not memory["passed"]:
        raise ValueError("4090 smoke memory Gate failed")
    del model, optimizer, tokenizer, encoded, trainable_parameters
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize(0)
    post_cleanup = int(torch.cuda.memory_reserved(0))
    if post_cleanup > config["hardware"]["maximum_post_cleanup_reserved_bytes"]:
        raise ValueError("4090 smoke post-cleanup memory Gate failed")
    result = {
        "schema_version": "project05-qwen25-4090-longest-sequence-smoke-v0.1",
        "status": "passed_4090_longest_sequence_smoke",
        "created_date": verified["authority"]["created_date"],
        "contract_sha256": sha256_file(verified["repo_root"] / verified["contract"]["contract_repository_path"]),
        "training_config_sha256": verified["contract"]["training_config"]["sha256"],
        "authority_sha256": sha256_file(verified["repo_root"] / verified["contract"]["authority_repository_path"]),
        "preparation_audit_sha256": sha256_file(runtime["preparation_audit_path"]),
        "gpu": gpu,
        "selection": {
            "examples": len(ranked),
            "lengths_descending": lengths,
            "selection_digest_sha256": sha256_text(canonical_json(selection_rows)),
            "raw_example_ids_recorded": False,
            "raw_pair_payload_recorded": False,
        },
        "training": {
            "microbatches": len(ranked),
            "optimizer_steps": 1,
            "loss_first": losses[0],
            "loss_last": losses[-1],
            "loss_mean": sum(losses) / len(losses),
            "losses_finite": all(math.isfinite(value) for value in losses),
            "gradient_norm": gradient,
            **inventory,
            "wall_seconds": time.monotonic() - started,
        },
        "memory_gate": {**memory, "post_cleanup_reserved_bytes": post_cleanup},
        "artifacts": {
            "adapter_saved": False,
            "checkpoint_saved": False,
            "generation_calls": 0,
        },
        "scope": {
            "development_or_test_accessed": False,
            "c07_c12_accessed": False,
            "m3_integrated": False,
            "paper_a_modified": False,
        },
        "next_gate": {"primary_training_authorized_by_same_user_authority": True},
    }
    write_json_no_overwrite(output_path, result)
    return result


def append_progress(path: Path, event: dict[str, Any]) -> None:
    allowed = {
        "event", "epoch", "optimizer_step", "optimizer_steps_total",
        "loss_mean_for_step", "gradient_norm", "learning_rate",
        "allocated_bytes", "reserved_bytes_diagnostic", "free_bytes",
        "allocator_cache_release_attempted",
        "pre_cache_release_reserved_bytes_diagnostic",
        "pre_cache_release_free_bytes_diagnostic",
        "elapsed_seconds", "created_date",
    }
    if set(event) - allowed:
        raise ValueError("progress event contains a non-sanitized field")
    with Path(path).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(event) + "\n")
        handle.flush()


def summarize(values: list[float], label: str) -> dict[str, Any]:
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError(f"{label} is empty or non-finite")
    return {
        "count": len(values), "first": values[0], "last": values[-1],
        "minimum": min(values), "maximum": max(values),
        "mean": sum(values) / len(values),
    }


def _save_checkpoint(
    model: Any, optimizer: Any, scheduler: Any, torch: Any,
    output_root: Path, epoch: int, trainer_state: dict[str, Any], maximum_file_bytes: int,
) -> dict[str, Any]:
    root = output_root / f"checkpoint-epoch-{epoch:03d}"
    root.mkdir(parents=False, exist_ok=False)
    model.save_pretrained(root / "adapter", safe_serialization=True)
    torch.save(optimizer.state_dict(), root / "optimizer.pt")
    torch.save(scheduler.state_dict(), root / "scheduler.pt")
    torch.save(
        {"python": random.getstate(), "torch_cpu": torch.get_rng_state(), "torch_cuda": torch.cuda.get_rng_state_all()},
        root / "rng-state.pt",
    )
    write_json_no_overwrite(root / "trainer-state.json", trainer_state)
    rows = PRIMARY.validate_primary_checkpoint(root, maximum_file_bytes)
    return {
        "epoch": epoch,
        "optimizer_step": trainer_state["optimizer_step"],
        "root": root.name,
        "files": [
            {"path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"]}
            for row in rows
        ],
        "adapter_only": True,
        "merged_model_saved": False,
    }


def run_primary(
    verified: dict[str, Any], runtime: dict[str, Any], smoke_path: Path
) -> dict[str, Any]:
    started = time.monotonic()
    config = verified["config"]
    run_root = verified["run_root"]
    smoke_path = require_within(smoke_path, run_root, "smoke audit")
    smoke = load_json(smoke_path)
    if smoke.get("status") != "passed_4090_longest_sequence_smoke":
        raise ValueError("passed 4090 smoke is required")
    current_contract_sha256 = sha256_file(
        verified["repo_root"] / verified["contract"]["contract_repository_path"]
    )
    current_config_sha256 = sha256_file(
        verified["repo_root"] / verified["contract"]["training_config"]["path"]
    )
    current_authority_sha256 = sha256_file(
        verified["repo_root"] / verified["contract"]["authority_repository_path"]
    )
    if smoke.get("contract_sha256") != current_contract_sha256:
        compatibility = verified["contract"].get("compatible_prior_smoke", {})
        expected = {
            "contract_sha256": smoke.get("contract_sha256"),
            "training_config_sha256": smoke.get("training_config_sha256"),
            "authority_sha256": smoke.get("authority_sha256"),
            "smoke_audit_sha256": sha256_file(smoke_path),
        }
        if compatibility != expected:
            raise ValueError("smoke audit belongs to another contract")
    output_root = (run_root / config["output_policy"]["run_subdirectory"]).resolve()
    require_within(output_root, run_root, "primary output")
    if output_root.exists():
        raise FileExistsError("refusing to overwrite or resume a primary run")
    output_root.mkdir(parents=True, exist_ok=False)
    progress = output_root / PROGRESS_NAME
    state = {"completed_epochs": 0, "optimizer_steps": 0, "microbatches": 0, "checkpoint_epochs": []}
    last_memory_gate = None
    last_memory_observation = None
    append_progress(progress, {
        "event": "primary_training_started", "epoch": 0, "optimizer_step": 0,
        "optimizer_steps_total": config["optimizer_steps"], "elapsed_seconds": 0.0,
        "created_date": verified["authority"]["created_date"],
    })
    try:
        stack = _load_training_stack()
        torch = stack["torch"]
        gpu = _runtime_gpu_gate(stack, config)
        if gpu["physical_uuid"] != smoke["gpu"]["physical_uuid"]:
            raise ValueError("primary GPU UUID differs from the passed smoke")
        random.seed(config["seed"])
        torch.manual_seed(config["seed"])
        torch.cuda.manual_seed_all(config["seed"])
        model, tokenizer, trainable_parameters, inventory = _build_model(
            stack, runtime["snapshot_dir"], config
        )
        encoded = _encode_all(
            runtime["train"], runtime["serialization"], tokenizer, config["sequence_length"]
        )
        optimizer = stack["bnb"].optim.PagedAdamW8bit(
            trainable_parameters, lr=config["learning_rate"], weight_decay=config["weight_decay"]
        )
        scheduler = stack["get_cosine_schedule_with_warmup"](
            optimizer,
            num_warmup_steps=config["scheduler"]["warmup_steps"],
            num_training_steps=config["optimizer_steps"],
        )
        optimizer.zero_grad(set_to_none=True)
        model.train()
        all_losses: list[float] = []
        all_gradients: list[float] = []
        epoch_summaries = []
        checkpoints = []
        memory_samples = [synchronized_memory_sample(torch, "model_optimizer_ready", 0)]
        maximum_wall = config["resource_limits"]["maximum_primary_wall_hours"] * 3600
        for epoch in range(1, config["epochs"] + 1):
            epoch_losses: list[float] = []
            epoch_gradients: list[float] = []
            accumulated: list[float] = []
            ordered = PRIMARY.order_epoch_examples(runtime["train"], config["seed"], epoch)
            for example in ordered:
                item = encoded[example["example_id"]]
                batch = {
                    key: torch.tensor([value], device="cuda", dtype=torch.long)
                    for key, value in item.items()
                }
                loss = model(**batch).loss
                if not torch.isfinite(loss).item():
                    raise ValueError("non-finite primary loss")
                loss_value = float(loss.detach().cpu())
                all_losses.append(loss_value)
                epoch_losses.append(loss_value)
                accumulated.append(loss_value)
                (loss / config["gradient_accumulation_steps"]).backward()
                state["microbatches"] += 1
                del batch, loss
                if len(accumulated) != config["gradient_accumulation_steps"]:
                    continue
                gradient = float(torch.nn.utils.clip_grad_norm_(
                    trainable_parameters, config["maximum_gradient_norm"]
                ).detach().cpu())
                if not math.isfinite(gradient):
                    raise ValueError("non-finite primary gradient norm")
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                state["optimizer_steps"] += 1
                all_gradients.append(gradient)
                epoch_gradients.append(gradient)
                pre_release_sample = synchronized_memory_sample(
                    torch, "optimizer_step_before_cache_normalization", state["optimizer_steps"]
                )
                cache_release_attempted = should_release_allocator_cache(
                    pre_release_sample, config
                )
                if cache_release_attempted:
                    torch.cuda.empty_cache()
                    sample = synchronized_memory_sample(
                        torch, "optimizer_step_completed", state["optimizer_steps"]
                    )
                else:
                    sample = {**pre_release_sample, "event": "optimizer_step_completed"}
                memory_samples.append(sample)
                memory = validate_memory_gate(memory_samples, config)
                last_memory_gate = memory
                last_memory_observation = {
                    "optimizer_step": state["optimizer_steps"],
                    "allocator_cache_release_attempted": cache_release_attempted,
                    "pre_cache_release_allocated_bytes": pre_release_sample["allocated_bytes"],
                    "pre_cache_release_reserved_bytes_diagnostic": pre_release_sample["reserved_bytes"],
                    "pre_cache_release_free_bytes_diagnostic": pre_release_sample["free_bytes"],
                    "blocking_allocated_bytes": sample["allocated_bytes"],
                    "blocking_reserved_bytes_diagnostic": sample["reserved_bytes"],
                    "blocking_free_bytes": sample["free_bytes"],
                }
                if not memory["passed"]:
                    raise ValueError("primary RTX 4090 memory Gate failed")
                elapsed = time.monotonic() - started
                if elapsed > maximum_wall:
                    raise TimeoutError("primary training exceeded the wall-time Gate")
                append_progress(progress, {
                    "event": "optimizer_step_completed", "epoch": epoch,
                    "optimizer_step": state["optimizer_steps"],
                    "optimizer_steps_total": config["optimizer_steps"],
                    "loss_mean_for_step": sum(accumulated) / len(accumulated),
                    "gradient_norm": gradient,
                    "learning_rate": scheduler.get_last_lr()[0],
                    "allocated_bytes": sample["allocated_bytes"],
                    "reserved_bytes_diagnostic": sample["reserved_bytes"],
                    "free_bytes": sample["free_bytes"], "elapsed_seconds": elapsed,
                    "allocator_cache_release_attempted": cache_release_attempted,
                    "pre_cache_release_reserved_bytes_diagnostic": pre_release_sample["reserved_bytes"],
                    "pre_cache_release_free_bytes_diagnostic": pre_release_sample["free_bytes"],
                })
                print(canonical_json({
                    "event": "optimizer_step_completed", "epoch": epoch,
                    "optimizer_step": state["optimizer_steps"],
                    "optimizer_steps_total": config["optimizer_steps"],
                    "loss_mean_for_step": sum(accumulated) / len(accumulated),
                    "elapsed_seconds": elapsed,
                }), flush=True)
                accumulated = []
            if accumulated:
                raise ValueError("epoch ended with a partial accumulation group")
            expected_step = epoch * config["optimizer_steps_per_epoch"]
            if state["optimizer_steps"] != expected_step:
                raise ValueError("epoch optimizer step count differs from the schedule")
            state["completed_epochs"] = epoch
            state["checkpoint_epochs"].append(epoch)
            epoch_summary = {
                "epoch": epoch, "optimizer_step_end": state["optimizer_steps"],
                "loss": summarize(epoch_losses, "epoch loss"),
                "gradient_norm": summarize(epoch_gradients, "epoch gradient norm"),
                "elapsed_seconds": time.monotonic() - started,
            }
            epoch_summaries.append(epoch_summary)
            trainer_state = {
                "schema_version": "project05-4090-primary-trainer-state-v0.1",
                "completed_epoch": epoch, "optimizer_step": state["optimizer_steps"],
                "microbatches": state["microbatches"],
                "contract_sha256": current_contract_sha256,
                "training_config_sha256": current_config_sha256,
                "authority_sha256": current_authority_sha256,
                "loss": epoch_summary["loss"],
                "gradient_norm": epoch_summary["gradient_norm"],
                "raw_pair_payload_recorded": False,
                "raw_generation_recorded": False,
            }
            checkpoints.append(_save_checkpoint(
                model, optimizer, scheduler, torch, output_root, epoch, trainer_state,
                config["resource_limits"]["maximum_adapter_file_bytes"],
            ))
            resource_bytes = PRIMARY.unique_physical_bytes([
                run_root / "local-runtime", run_root / "local-cache", run_root / "server-output"
            ])
            if resource_bytes > config["resource_limits"]["maximum_environment_cache_checkpoint_output_bytes"]:
                raise ValueError("runtime/cache/checkpoint bytes exceed the resource Gate")
            gc.collect()
            torch.cuda.empty_cache()
            append_progress(progress, {
                "event": "epoch_checkpoint_completed", "epoch": epoch,
                "optimizer_step": state["optimizer_steps"],
                "optimizer_steps_total": config["optimizer_steps"],
                "elapsed_seconds": time.monotonic() - started,
            })
        summary = {
            **state,
            "losses_finite": all(math.isfinite(value) for value in all_losses),
            "gradient_norms_finite": all(math.isfinite(value) for value in all_gradients),
        }
        if state["completed_epochs"] != config["epochs"] or state["optimizer_steps"] != config["optimizer_steps"]:
            raise ValueError("primary training completion Gate failed")
        memory = validate_memory_gate(memory_samples, config)
        result = {
            "schema_version": "project05-qwen25-4090-primary-training-audit-v0.1",
            "status": "passed_single_4090_primary_adapter_training",
            "created_date": verified["authority"]["created_date"],
            "contract_sha256": current_contract_sha256,
            "training_config_sha256": current_config_sha256,
            "authority_sha256": current_authority_sha256,
            "smoke_audit_sha256": sha256_file(smoke_path),
            "preparation_audit_sha256": sha256_file(runtime["preparation_audit_path"]),
            "model": {**runtime["model_lock"], "quantization": config["quantization"]},
            "gpu": gpu,
            "data_gate": PREFLIGHT.sanitize_dataset_report(runtime["data_report"]),
            "training": {
                **summary, **inventory,
                "loss": summarize(all_losses, "training loss"),
                "gradient_norm": summarize(all_gradients, "training gradient norm"),
                "epoch_summaries": epoch_summaries,
                "wall_seconds": time.monotonic() - started,
                "wall_limit_seconds": maximum_wall,
            },
            "memory_gate": memory,
            "checkpoints": checkpoints,
            "resources": {
                "runtime_cache_checkpoint_output_bytes": resource_bytes,
                "maximum_bytes": config["resource_limits"]["maximum_environment_cache_checkpoint_output_bytes"],
            },
            "privacy_and_scope": {
                "raw_pair_payload_recorded": False, "raw_generation_recorded": False,
                "model_generation_calls": 0, "development_or_test_accessed": False,
                "c07_c12_accessed": False, "m3_integrated": False,
                "server_connected": True, "paper_a_modified": False,
                "merged_model_saved": False, "hub_upload_used": False,
            },
            "next_gate": {
                "status": "hard_stop_for_checkpoint_selection_authorization",
                "checkpoint_selection_authorized": False,
                "formal_inference_authorized": False,
                "c07_c12_execution_authorized": False,
                "m3_integration_authorized": False,
            },
        }
        write_json_no_overwrite(output_root / PRIMARY_AUDIT_NAME, result)
        append_progress(progress, {
            "event": "primary_training_completed", "epoch": config["epochs"],
            "optimizer_step": state["optimizer_steps"],
            "optimizer_steps_total": config["optimizer_steps"],
            "elapsed_seconds": time.monotonic() - started,
        })
        return result
    except BaseException as error:
        failure = {
            "schema_version": "project05-qwen25-4090-primary-training-failure-v0.1",
            "status": "failed_or_interrupted_4090_primary_training",
            "created_date": verified["authority"]["created_date"],
            "failure_type": type(error).__name__, "failure_message": str(error)[:500],
            "completed_epochs": state["completed_epochs"],
            "optimizer_steps": state["optimizer_steps"],
            "microbatches": state["microbatches"],
            "checkpoint_epochs": state["checkpoint_epochs"],
            "elapsed_seconds": time.monotonic() - started,
            "automatic_restart_authorized": False,
            "resume_authorized": False,
            "checkpoint_selection_authorized": False,
        }
        if last_memory_gate is not None:
            failure["memory_gate"] = last_memory_gate
        if last_memory_observation is not None:
            failure["triggering_memory_observation"] = last_memory_observation
        failure_path = output_root / PRIMARY_FAILURE_NAME
        if not failure_path.exists():
            write_json_no_overwrite(failure_path, failure)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("smoke", "primary"), required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--preparation-audit", type=Path, required=True)
    parser.add_argument("--pair-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--smoke-audit", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verified = verify_static_authority(
        args.contract, args.config, args.authority, args.run_root
    )
    runtime = verify_runtime_and_inputs(
        verified, args.preparation_audit, args.pair_root
    )
    if args.phase == "smoke":
        if args.output is None or args.smoke_audit is not None:
            raise ValueError("smoke requires --output and forbids --smoke-audit")
        result = run_smoke(verified, runtime, args.output)
    else:
        if args.smoke_audit is None or args.output is not None:
            raise ValueError("primary requires --smoke-audit and forbids --output")
        result = run_primary(verified, runtime, args.smoke_audit)
    print(result["status"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
