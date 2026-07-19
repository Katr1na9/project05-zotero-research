"""Run one authorized RTX 4090 torch-AdamW stability diagnostic.

The diagnostic is Linux-only, scoped below /home/myy, uses the frozen formal
training payloads, and discards all model/optimizer state.  It is not a formal
training run and cannot produce an adapter or checkpoint.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import math
import os
import random
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = Path(__file__).with_name("execute_qwen_qlora_4090.py")
RESULT_NAME = "4090-optimizer-stability-diagnostic-v0.1.json"
FAILURE_NAME = "4090-optimizer-stability-diagnostic-failure-v0.1.json"
PROGRESS_NAME = "4090-optimizer-stability-progress-v0.1.jsonl"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no module loader")
    spec.loader.exec_module(module)
    return module


CORE = _load_module(CORE_PATH, "project05_4090_optimizer_diagnostic_core")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json_no_overwrite(path: Path, value: Any) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="\n")


def append_progress(path: Path, event: dict[str, Any]) -> None:
    allowed = {
        "event", "optimizer_step", "optimizer_steps_total", "microbatches",
        "loss_mean_for_step", "gradient_norm", "learning_rate",
        "allocated_bytes", "reserved_bytes_diagnostic", "free_bytes",
        "allocator_cache_release_attempted", "elapsed_seconds", "created_date",
    }
    if set(event) - allowed:
        raise ValueError("diagnostic progress event contains a non-sanitized field")
    with Path(path).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(event) + "\n")
        handle.flush()


def summarize(values: list[float], label: str) -> dict[str, Any]:
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError(f"{label} is empty or non-finite")
    return {
        "count": len(values),
        "first": values[0],
        "last": values[-1],
        "minimum": min(values),
        "maximum": max(values),
        "mean": sum(values) / len(values),
    }


def build_torch_adamw(stack: dict[str, Any], parameters: list[Any], config: dict[str, Any]):
    if config.get("optimizer") != "adamw_torch":
        raise ValueError("optimizer stability diagnostic requires adamw_torch")
    options = config.get("optimizer_parameters", {})
    expected = {
        "betas": [0.9, 0.999],
        "eps": 1e-8,
        "foreach": False,
        "fused": False,
        "capturable": False,
    }
    if options != expected:
        raise ValueError("torch AdamW implementation options differ from v0.33")
    return stack["torch"].optim.AdamW(
        parameters,
        lr=config["learning_rate"],
        weight_decay=config["weight_decay"],
        betas=tuple(options["betas"]),
        eps=options["eps"],
        foreach=options["foreach"],
        fused=options["fused"],
        capturable=options["capturable"],
    )


def verify_static_authority(
    contract_path: Path, config_path: Path, authority_path: Path, run_root: Path
) -> dict[str, Any]:
    contract_path = CORE.require_within(contract_path, REPO_ROOT, "diagnostic contract")
    config_path = CORE.require_within(config_path, REPO_ROOT, "diagnostic config")
    authority_path = CORE.require_within(authority_path, REPO_ROOT, "diagnostic authority")
    contract = CORE.load_contract_with_parent(contract_path)
    config = CORE.load_json(config_path)
    authority = CORE.load_json(authority_path)
    boundary = CORE.validate_server_boundary(contract, run_root, repo_root=REPO_ROOT)
    if contract_path != (REPO_ROOT / contract["contract_repository_path"]).resolve():
        raise ValueError("diagnostic contract path mismatch")
    if authority_path != (REPO_ROOT / contract["authority_repository_path"]).resolve():
        raise ValueError("diagnostic authority path mismatch")
    if CORE.sha256_file(config_path) != contract["training_config"]["sha256"]:
        raise ValueError("diagnostic config SHA-256 mismatch")
    gate = authority["optimizer_stability_gate"]
    if gate.get("contract_sha256") != CORE.sha256_file(contract_path):
        raise ValueError("diagnostic authority contract SHA-256 mismatch")
    if gate.get("training_config_sha256") != CORE.sha256_file(config_path):
        raise ValueError("diagnostic authority config SHA-256 mismatch")
    if not gate.get("authorized", False) or gate.get("maximum_executions") != 1:
        raise PermissionError("exactly one optimizer stability diagnostic is required")
    if gate.get("formal_primary_authorized", True):
        raise PermissionError("formal primary must remain closed")
    for label, record in contract["frozen_inputs"].items():
        CORE._verify_hash_record(record, label)
    for label in ("optimizer_diagnostic_executor", "optimizer_diagnostic_launcher"):
        CORE._verify_hash_record(contract["implementation"][label], label)
    return {
        "contract": contract,
        "config": config,
        "authority": authority,
        **boundary,
    }


def run_diagnostic(
    verified: dict[str, Any], runtime: dict[str, Any], smoke_path: Path
) -> dict[str, Any]:
    started = time.monotonic()
    config = verified["config"]
    run_root = verified["run_root"]
    smoke_path = CORE.require_within(smoke_path, run_root, "passed smoke audit")
    smoke = CORE.load_json(smoke_path)
    if smoke.get("status") != "passed_4090_longest_sequence_smoke":
        raise ValueError("passed 4090 smoke is required for GPU identity binding")
    if os.environ.get("CUDA_LAUNCH_BLOCKING") != "1":
        raise ValueError("CUDA_LAUNCH_BLOCKING=1 is required")

    output_root = (run_root / config["output_policy"]["run_subdirectory"]).resolve()
    CORE.require_within(output_root, run_root, "diagnostic output")
    if output_root.exists():
        raise FileExistsError("refusing to overwrite or resume an optimizer diagnostic")
    output_root.mkdir(parents=True, exist_ok=False)
    progress_path = output_root / PROGRESS_NAME
    target_steps = config["optimizer_stability_diagnostic"]["optimizer_steps"]
    target_microbatches = config["optimizer_stability_diagnostic"]["microbatches"]
    state = {"optimizer_steps": 0, "microbatches": 0}
    last_memory_gate = None
    append_progress(progress_path, {
        "event": "optimizer_stability_started",
        "optimizer_step": 0,
        "optimizer_steps_total": target_steps,
        "microbatches": 0,
        "elapsed_seconds": 0.0,
        "created_date": verified["authority"]["created_date"],
    })
    try:
        stack = CORE._load_training_stack()
        torch = stack["torch"]
        gpu = CORE._runtime_gpu_gate(stack, config)
        if gpu["physical_uuid"] != smoke["gpu"]["physical_uuid"]:
            raise ValueError("diagnostic GPU UUID differs from the passed smoke")
        random.seed(config["seed"])
        torch.manual_seed(config["seed"])
        torch.cuda.manual_seed_all(config["seed"])
        model, tokenizer, trainable_parameters, inventory = CORE._build_model(
            stack, runtime["snapshot_dir"], config
        )
        encoded = CORE._encode_all(
            runtime["train"], runtime["serialization"], tokenizer, config["sequence_length"]
        )
        optimizer = build_torch_adamw(stack, trainable_parameters, config)
        scheduler = stack["get_cosine_schedule_with_warmup"](
            optimizer,
            num_warmup_steps=config["scheduler"]["warmup_steps"],
            num_training_steps=config["optimizer_steps"],
        )
        optimizer.zero_grad(set_to_none=True)
        model.train()
        losses: list[float] = []
        gradients: list[float] = []
        accumulated: list[float] = []
        memory_samples = [CORE.synchronized_memory_sample(torch, "model_optimizer_ready", 0)]
        maximum_wall = config["resource_limits"]["maximum_diagnostic_wall_hours"] * 3600

        for epoch in range(1, config["epochs"] + 1):
            ordered = CORE.PRIMARY.order_epoch_examples(runtime["train"], config["seed"], epoch)
            for example in ordered:
                item = encoded[example["example_id"]]
                batch = {
                    key: torch.tensor([value], device="cuda", dtype=torch.long)
                    for key, value in item.items()
                }
                loss = model(**batch).loss
                if not torch.isfinite(loss).item():
                    raise ValueError("non-finite optimizer diagnostic loss")
                loss_value = float(loss.detach().cpu())
                losses.append(loss_value)
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
                    raise ValueError("non-finite optimizer diagnostic gradient norm")
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                state["optimizer_steps"] += 1
                gradients.append(gradient)
                sample = CORE.synchronized_memory_sample(
                    torch, "optimizer_step_before_cache_normalization", state["optimizer_steps"]
                )
                cache_release_attempted = CORE.should_release_allocator_cache(sample, config)
                if cache_release_attempted:
                    torch.cuda.empty_cache()
                    sample = CORE.synchronized_memory_sample(
                        torch, "optimizer_step_completed", state["optimizer_steps"]
                    )
                else:
                    sample = {**sample, "event": "optimizer_step_completed"}
                memory_samples.append(sample)
                last_memory_gate = CORE.validate_memory_gate(memory_samples, config)
                if not last_memory_gate["passed"]:
                    raise ValueError("optimizer diagnostic memory Gate failed")
                elapsed = time.monotonic() - started
                if elapsed > maximum_wall:
                    raise TimeoutError("optimizer diagnostic exceeded the wall-time Gate")
                append_progress(progress_path, {
                    "event": "optimizer_step_completed",
                    "optimizer_step": state["optimizer_steps"],
                    "optimizer_steps_total": target_steps,
                    "microbatches": state["microbatches"],
                    "loss_mean_for_step": sum(accumulated) / len(accumulated),
                    "gradient_norm": gradient,
                    "learning_rate": scheduler.get_last_lr()[0],
                    "allocated_bytes": sample["allocated_bytes"],
                    "reserved_bytes_diagnostic": sample["reserved_bytes"],
                    "free_bytes": sample["free_bytes"],
                    "allocator_cache_release_attempted": cache_release_attempted,
                    "elapsed_seconds": elapsed,
                })
                print(canonical_json({
                    "event": "optimizer_step_completed",
                    "optimizer_step": state["optimizer_steps"],
                    "optimizer_steps_total": target_steps,
                    "elapsed_seconds": elapsed,
                }), flush=True)
                accumulated = []
                if state["optimizer_steps"] == target_steps:
                    break
            if state["optimizer_steps"] == target_steps:
                break

        if state != {"optimizer_steps": target_steps, "microbatches": target_microbatches}:
            raise ValueError("optimizer stability completion counts differ from the contract")
        memory = CORE.validate_memory_gate(memory_samples, config)
        del model, optimizer, scheduler, tokenizer, encoded, trainable_parameters
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.synchronize(0)
        post_cleanup = int(torch.cuda.memory_reserved(0))
        if post_cleanup > config["hardware"]["maximum_post_cleanup_reserved_bytes"]:
            raise ValueError("optimizer diagnostic post-cleanup memory Gate failed")
        result = {
            "schema_version": "project05-qwen25-4090-optimizer-stability-v0.1",
            "status": "passed_torch_adamw_180_step_stability_diagnostic",
            "created_date": verified["authority"]["created_date"],
            "contract_sha256": CORE.sha256_file(
                REPO_ROOT / verified["contract"]["contract_repository_path"]
            ),
            "training_config_sha256": CORE.sha256_file(
                REPO_ROOT / verified["contract"]["training_config"]["path"]
            ),
            "authority_sha256": CORE.sha256_file(
                REPO_ROOT / verified["contract"]["authority_repository_path"]
            ),
            "smoke_audit_sha256": CORE.sha256_file(smoke_path),
            "preparation_audit_sha256": CORE.sha256_file(runtime["preparation_audit_path"]),
            "gpu": gpu,
            "optimizer": {
                "name": config["optimizer"],
                **config["optimizer_parameters"],
                "bitsandbytes_optimizer_used": False,
                "bitsandbytes_nf4_base_used": True,
            },
            "diagnostic": {
                **state,
                **inventory,
                "loss": summarize(losses, "diagnostic loss"),
                "gradient_norm": summarize(gradients, "diagnostic gradient norm"),
                "old_failure_step_exceeded": state["optimizer_steps"] > config["optimizer_stability_diagnostic"]["must_exceed_failed_step"],
                "cuda_launch_blocking": True,
                "wall_seconds": time.monotonic() - started,
            },
            "memory_gate": {**memory, "post_cleanup_reserved_bytes": post_cleanup},
            "artifacts": {
                "adapter_saved": False,
                "checkpoint_saved": False,
                "optimizer_state_saved": False,
                "generation_calls": 0,
                "raw_payload_recorded": False,
            },
            "scope": {
                "training_validation_accessed": False,
                "development_or_test_accessed": False,
                "c07_c12_accessed": False,
                "m3_integrated": False,
                "paper_a_modified": False,
            },
            "next_gate": {
                "status": "hard_stop_for_fresh_formal_training_authorization",
                "formal_primary_authorized": False,
                "checkpoint_selection_authorized": False,
                "formal_inference_authorized": False,
                "m3_integration_authorized": False,
            },
        }
        write_json_no_overwrite(output_root / RESULT_NAME, result)
        return result
    except BaseException as error:
        failure = {
            "schema_version": "project05-qwen25-4090-optimizer-stability-failure-v0.1",
            "status": "failed_4090_optimizer_stability_diagnostic",
            "created_date": verified["authority"]["created_date"],
            "failure_type": type(error).__name__,
            "failure_message": str(error)[:500],
            **state,
            "elapsed_seconds": time.monotonic() - started,
            "automatic_retry_authorized": False,
            "formal_primary_authorized": False,
        }
        if last_memory_gate is not None:
            failure["memory_gate"] = last_memory_gate
        failure_path = output_root / FAILURE_NAME
        if not failure_path.exists():
            write_json_no_overwrite(failure_path, failure)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--preparation-audit", type=Path, required=True)
    parser.add_argument("--pair-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--smoke-audit", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verified = verify_static_authority(
        args.contract, args.config, args.authority, args.run_root
    )
    runtime = CORE.verify_runtime_and_inputs(
        verified, args.preparation_audit, args.pair_root
    )
    result = run_diagnostic(verified, runtime, args.smoke_audit)
    print(result["status"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
