"""Execute one hash-authorized fresh RTX 4090 AdamW QLoRA primary."""

from __future__ import annotations

import argparse
import importlib.util
import math
import random
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTIC_PATH = Path(__file__).with_name("diagnose_qwen_qlora_optimizer_4090.py")
AUDIT_NAME = "4090-adamw-primary-training-audit-v0.1.json"
FAILURE_NAME = "4090-adamw-primary-training-failure-v0.1.json"
PROGRESS_NAME = "4090-adamw-primary-training-progress-v0.1.jsonl"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no loader")
    spec.loader.exec_module(module)
    return module


DIAG = _load(DIAGNOSTIC_PATH, "project05_adamw_primary_dependencies")
CORE = DIAG.CORE


def verify_authority(contract_path: Path, config_path: Path, authority_path: Path, run_root: Path):
    contract_path = CORE.require_within(contract_path, REPO_ROOT, "formal contract")
    config_path = CORE.require_within(config_path, REPO_ROOT, "formal config")
    authority_path = CORE.require_within(authority_path, REPO_ROOT, "formal authority")
    contract = DIAG.load_contract_chain(contract_path)
    config = CORE.load_json(config_path)
    authority = CORE.load_json(authority_path)
    boundary = CORE.validate_server_boundary(contract, run_root, repo_root=REPO_ROOT)
    if contract_path != (REPO_ROOT / contract["contract_repository_path"]).resolve():
        raise ValueError("formal contract path mismatch")
    if authority_path != (REPO_ROOT / contract["authority_repository_path"]).resolve():
        raise ValueError("formal authority path mismatch")
    if contract["training_config"]["sha256"] != CORE.sha256_file(config_path):
        raise ValueError("formal contract config hash mismatch")
    gate = authority["fresh_adamw_primary_gate"]
    if gate["contract_sha256"] != CORE.sha256_file(contract_path):
        raise ValueError("formal authority contract hash mismatch")
    if gate["training_config_sha256"] != CORE.sha256_file(config_path):
        raise ValueError("formal authority config hash mismatch")
    if not gate["authorized"] or gate["maximum_executions"] != 1:
        raise PermissionError("exactly one fresh formal primary is required")
    if gate["resume_authorized"] or gate["checkpoint_selection_authorized"]:
        raise PermissionError("resume and checkpoint selection must remain closed")
    for label, record in contract["frozen_inputs"].items():
        CORE._verify_hash_record(record, label)
    for label in ("adamw_primary_executor", "adamw_primary_launcher"):
        CORE._verify_hash_record(contract["implementation"][label], label)
    return {"contract": contract, "config": config, "authority": authority, **boundary}


def run_primary(verified: dict[str, Any], runtime: dict[str, Any], smoke_path: Path):
    started = time.monotonic()
    config = verified["config"]
    run_root = verified["run_root"]
    smoke_path = CORE.require_within(smoke_path, run_root, "smoke audit")
    smoke = CORE.load_json(smoke_path)
    if smoke.get("status") != "passed_4090_longest_sequence_smoke":
        raise ValueError("passed smoke is required")
    output_root = (run_root / config["output_policy"]["run_subdirectory"]).resolve()
    CORE.require_within(output_root, run_root, "formal output")
    if output_root.exists():
        raise FileExistsError("refusing to overwrite or resume formal primary")
    output_root.mkdir(parents=True, exist_ok=False)
    progress = output_root / PROGRESS_NAME
    state = {"completed_epochs": 0, "optimizer_steps": 0, "microbatches": 0, "checkpoint_epochs": []}
    last_memory_gate = None
    CORE.append_progress(progress, {
        "event": "primary_training_started", "epoch": 0, "optimizer_step": 0,
        "optimizer_steps_total": config["optimizer_steps"], "elapsed_seconds": 0.0,
        "created_date": verified["authority"]["created_date"],
    })
    try:
        stack = CORE._load_training_stack()
        torch = stack["torch"]
        gpu = CORE._runtime_gpu_gate(stack, config)
        if gpu["physical_uuid"] != smoke["gpu"]["physical_uuid"]:
            raise ValueError("formal GPU UUID differs from smoke")
        random.seed(config["seed"])
        torch.manual_seed(config["seed"])
        torch.cuda.manual_seed_all(config["seed"])
        model, tokenizer, trainable_parameters, inventory = CORE._build_model(stack, runtime["snapshot_dir"], config)
        encoded = CORE._encode_all(runtime["train"], runtime["serialization"], tokenizer, config["sequence_length"])
        optimizer = DIAG.build_torch_adamw(stack, trainable_parameters, config)
        scheduler = stack["get_cosine_schedule_with_warmup"](
            optimizer, num_warmup_steps=config["scheduler"]["warmup_steps"],
            num_training_steps=config["optimizer_steps"],
        )
        optimizer.zero_grad(set_to_none=True)
        model.train()
        losses, gradients, epoch_summaries, checkpoints = [], [], [], []
        memory_samples = [CORE.synchronized_memory_sample(torch, "model_optimizer_ready", 0)]
        maximum_wall = config["resource_limits"]["maximum_primary_wall_hours"] * 3600
        current_contract_sha = CORE.sha256_file(REPO_ROOT / verified["contract"]["contract_repository_path"])
        current_config_sha = CORE.sha256_file(REPO_ROOT / verified["contract"]["training_config"]["path"])
        current_authority_sha = CORE.sha256_file(REPO_ROOT / verified["contract"]["authority_repository_path"])
        for epoch in range(1, config["epochs"] + 1):
            epoch_losses, epoch_gradients, accumulated = [], [], []
            for example in CORE.PRIMARY.order_epoch_examples(runtime["train"], config["seed"], epoch):
                item = encoded[example["example_id"]]
                batch = {key: torch.tensor([value], device="cuda", dtype=torch.long) for key, value in item.items()}
                loss = model(**batch).loss
                if not torch.isfinite(loss).item():
                    raise ValueError("non-finite formal loss")
                value = float(loss.detach().cpu())
                losses.append(value); epoch_losses.append(value); accumulated.append(value)
                (loss / config["gradient_accumulation_steps"]).backward()
                state["microbatches"] += 1
                del batch, loss
                if len(accumulated) != config["gradient_accumulation_steps"]:
                    continue
                gradient = float(torch.nn.utils.clip_grad_norm_(trainable_parameters, config["maximum_gradient_norm"]).detach().cpu())
                if not math.isfinite(gradient):
                    raise ValueError("non-finite formal gradient")
                optimizer.step(); scheduler.step(); optimizer.zero_grad(set_to_none=True)
                state["optimizer_steps"] += 1
                gradients.append(gradient); epoch_gradients.append(gradient)
                pre_sample = CORE.synchronized_memory_sample(torch, "optimizer_step_before_cache_normalization", state["optimizer_steps"])
                released = CORE.should_release_allocator_cache(pre_sample, config)
                if released:
                    torch.cuda.empty_cache()
                    sample = CORE.synchronized_memory_sample(torch, "optimizer_step_completed", state["optimizer_steps"])
                else:
                    sample = {**pre_sample, "event": "optimizer_step_completed"}
                memory_samples.append(sample)
                last_memory_gate = CORE.validate_memory_gate(memory_samples, config)
                if not last_memory_gate["passed"]:
                    raise ValueError("formal memory Gate failed")
                elapsed = time.monotonic() - started
                if elapsed > maximum_wall:
                    raise TimeoutError("formal wall-time Gate failed")
                CORE.append_progress(progress, {
                    "event": "optimizer_step_completed", "epoch": epoch,
                    "optimizer_step": state["optimizer_steps"], "optimizer_steps_total": config["optimizer_steps"],
                    "loss_mean_for_step": sum(accumulated) / len(accumulated), "gradient_norm": gradient,
                    "learning_rate": scheduler.get_last_lr()[0], "allocated_bytes": sample["allocated_bytes"],
                    "reserved_bytes_diagnostic": sample["reserved_bytes"], "free_bytes": sample["free_bytes"],
                    "allocator_cache_release_attempted": released,
                    "pre_cache_release_reserved_bytes_diagnostic": pre_sample["reserved_bytes"],
                    "pre_cache_release_free_bytes_diagnostic": pre_sample["free_bytes"], "elapsed_seconds": elapsed,
                })
                print(CORE.canonical_json({"event": "optimizer_step_completed", "epoch": epoch, "optimizer_step": state["optimizer_steps"], "optimizer_steps_total": config["optimizer_steps"], "elapsed_seconds": elapsed}), flush=True)
                accumulated = []
            if accumulated or state["optimizer_steps"] != epoch * config["optimizer_steps_per_epoch"]:
                raise ValueError("formal epoch count Gate failed")
            state["completed_epochs"] = epoch
            state["checkpoint_epochs"].append(epoch)
            epoch_summary = {
                "epoch": epoch, "optimizer_step_end": state["optimizer_steps"],
                "loss": CORE.summarize(epoch_losses, "epoch loss"),
                "gradient_norm": CORE.summarize(epoch_gradients, "epoch gradient"),
                "elapsed_seconds": time.monotonic() - started,
            }
            epoch_summaries.append(epoch_summary)
            trainer_state = {
                "schema_version": "project05-4090-adamw-trainer-state-v0.1",
                "completed_epoch": epoch, "optimizer_step": state["optimizer_steps"],
                "microbatches": state["microbatches"], "contract_sha256": current_contract_sha,
                "training_config_sha256": current_config_sha, "authority_sha256": current_authority_sha,
                "loss": epoch_summary["loss"], "gradient_norm": epoch_summary["gradient_norm"],
                "raw_pair_payload_recorded": False, "raw_generation_recorded": False,
            }
            checkpoints.append(CORE._save_checkpoint(model, optimizer, scheduler, torch, output_root, epoch, trainer_state, config["resource_limits"]["maximum_adapter_file_bytes"]))
            resource_bytes = CORE.PRIMARY.unique_physical_bytes([run_root / "local-runtime", run_root / "local-cache", run_root / "server-output"])
            if resource_bytes > config["resource_limits"]["maximum_environment_cache_checkpoint_output_bytes"]:
                raise ValueError("formal resource byte Gate failed")
            CORE.append_progress(progress, {"event": "epoch_checkpoint_completed", "epoch": epoch, "optimizer_step": state["optimizer_steps"], "optimizer_steps_total": config["optimizer_steps"], "elapsed_seconds": time.monotonic() - started})
        if state["completed_epochs"] != 3 or state["optimizer_steps"] != 225 or state["microbatches"] != 3600:
            raise ValueError("formal completion Gate failed")
        result = {
            "schema_version": "project05-qwen25-4090-adamw-primary-v0.1",
            "status": "passed_single_4090_adamw_primary_adapter_training",
            "created_date": verified["authority"]["created_date"],
            "contract_sha256": current_contract_sha, "training_config_sha256": current_config_sha,
            "authority_sha256": current_authority_sha, "smoke_audit_sha256": CORE.sha256_file(smoke_path),
            "preparation_audit_sha256": CORE.sha256_file(runtime["preparation_audit_path"]),
            "model": {**runtime["model_lock"], "quantization": config["quantization"]}, "gpu": gpu,
            "data_gate": CORE.PREFLIGHT.sanitize_dataset_report(runtime["data_report"]),
            "optimizer": {"name": config["optimizer"], **config["optimizer_parameters"], "bitsandbytes_optimizer_used": False},
            "training": {**state, **inventory, "loss": CORE.summarize(losses, "formal loss"), "gradient_norm": CORE.summarize(gradients, "formal gradient"), "epoch_summaries": epoch_summaries, "wall_seconds": time.monotonic() - started},
            "memory_gate": CORE.validate_memory_gate(memory_samples, config), "checkpoints": checkpoints,
            "resources": {"runtime_cache_checkpoint_output_bytes": resource_bytes, "maximum_bytes": config["resource_limits"]["maximum_environment_cache_checkpoint_output_bytes"]},
            "privacy_and_scope": {"raw_pair_payload_recorded": False, "raw_generation_recorded": False, "model_generation_calls": 0, "development_or_test_accessed": False, "c07_c12_accessed": False, "m3_integrated": False, "paper_a_modified": False, "merged_model_saved": False, "hub_upload_used": False},
            "next_gate": {"status": "hard_stop_for_checkpoint_selection_and_evaluation_authorization", "checkpoint_selection_authorized": False, "formal_inference_authorized": False, "m3_integration_authorized": False},
        }
        CORE.write_json_no_overwrite(output_root / AUDIT_NAME, result)
        CORE.append_progress(progress, {"event": "primary_training_completed", "epoch": 3, "optimizer_step": 225, "optimizer_steps_total": 225, "elapsed_seconds": time.monotonic() - started})
        return result
    except BaseException as error:
        failure = {"schema_version": "project05-qwen25-4090-adamw-primary-failure-v0.1", "status": "failed_or_interrupted_4090_adamw_primary", "created_date": verified["authority"]["created_date"], "failure_type": type(error).__name__, "failure_message": str(error)[:500], **state, "elapsed_seconds": time.monotonic() - started, "automatic_restart_authorized": False, "resume_authorized": False, "checkpoint_selection_authorized": False}
        if last_memory_gate is not None:
            failure["memory_gate"] = last_memory_gate
        if not (output_root / FAILURE_NAME).exists():
            CORE.write_json_no_overwrite(output_root / FAILURE_NAME, failure)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("contract", "config", "authority", "preparation-audit", "pair-root", "run-root", "smoke-audit"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    verified = verify_authority(args.contract, args.config, args.authority, args.run_root)
    runtime = CORE.verify_runtime_and_inputs(verified, args.preparation_audit, args.pair_root)
    result = run_primary(verified, runtime, args.smoke_audit)
    print(result["status"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
