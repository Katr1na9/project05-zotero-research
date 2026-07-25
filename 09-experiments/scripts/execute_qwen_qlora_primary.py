"""Execute the single authorized Project05 Qwen2.5 QLoRA primary run.

The command is deliberately narrower than checkpoint selection or inference.
It consumes only the frozen train/training-validation pair files, executes the
single 3-epoch / 225-step adapter-only run, and saves one recoverable adapter
checkpoint at each epoch boundary.  It never loads development/test material,
generates model text, merges the adapter, or uploads an artifact.
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
PRIMARY_HELPER_PATH = Path(__file__).with_name("train_qwen_qlora_primary.py")
PREFLIGHT_HELPER_PATH = Path(__file__).with_name("preflight_qwen_qlora_primary.py")
EXPECTED_AUTHORITY_NAME = "authority-lock-v0.25.json"
FINAL_AUDIT_NAME = "primary-training-audit-v0.1.json"
FAILURE_AUDIT_NAME = "primary-training-failure-v0.1.json"
PROGRESS_NAME = "primary-training-progress-v0.1.jsonl"


def _load_helper(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no module loader")
    spec.loader.exec_module(module)
    return module


PRIMARY = _load_helper(PRIMARY_HELPER_PATH, "project05_primary_training_helpers")
PREFLIGHT = _load_helper(PREFLIGHT_HELPER_PATH, "project05_primary_preflight_helpers")
load_json = PRIMARY.load_json
sha256_file = PRIMARY.sha256_file
require_primary_path = PRIMARY.require_primary_path
canonical_json = PRIMARY.canonical_json
write_json_no_overwrite = PRIMARY.SMOKE.write_json_no_overwrite
encode_assistant_only = PRIMARY.encode_assistant_only


def expected_output_root(
    run_root: Path, contract: dict[str, Any], repo_root: Path = REPO_ROOT
) -> Path:
    run_root = require_primary_path(run_root, repo_root, "run root")
    expected_run_root = (
        Path(repo_root) / contract["execution_boundary"]["run_directory_name"]
    ).resolve()
    if run_root != expected_run_root:
        raise ValueError("run root differs from the frozen primary contract")
    output = require_primary_path(
        run_root / contract["execution_boundary"]["primary_output_subdirectory"],
        repo_root,
        "primary output root",
    )
    if output != (run_root / "local-output" / "primary-v0.1").resolve():
        raise ValueError("primary output root differs from the exact local path")
    return output


def append_progress(path: Path, event: dict[str, Any]) -> None:
    allowed = {
        "event",
        "epoch",
        "optimizer_step",
        "optimizer_steps_total",
        "loss_mean_for_step",
        "gradient_norm",
        "learning_rate",
        "peak_reserved_vram_bytes",
        "elapsed_seconds",
        "created_date",
    }
    if set(event) - allowed:
        raise ValueError("progress event contains a non-sanitized field")
    path = Path(path)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(event) + "\n")
        handle.flush()


def summarize_values(values: list[float], label: str) -> dict[str, float | int]:
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError(f"{label} values are empty or non-finite")
    return {
        "count": len(values),
        "first": values[0],
        "last": values[-1],
        "minimum": min(values),
        "maximum": max(values),
        "mean": sum(values) / len(values),
    }


def validate_completed_training(
    summary: dict[str, Any], config: dict[str, Any]
) -> None:
    if summary.get("completed_epochs") != config["epochs"]:
        raise ValueError("primary training did not complete every frozen epoch")
    if summary.get("optimizer_steps") != config["optimizer_steps"]:
        raise ValueError("primary training did not complete every optimizer step")
    if summary.get("microbatches") != (
        config["data"]["train_examples"] * config["epochs"]
    ):
        raise ValueError("primary training microbatch count is incomplete")
    checkpoints = summary.get("checkpoint_epochs")
    if checkpoints != config["checkpointing"]["epochs"]:
        raise ValueError("primary checkpoint epochs are incomplete")
    if not summary.get("losses_finite") or not summary.get("gradient_norms_finite"):
        raise ValueError("primary training contains a non-finite metric")


def checkpoint_manifest(
    checkpoint_root: Path, maximum_file_bytes: int
) -> list[dict[str, Any]]:
    rows = PRIMARY.validate_primary_checkpoint(checkpoint_root, maximum_file_bytes)
    return [
        {"path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"]}
        for row in rows
    ]


def _verify_authorized_inputs(
    contract_path: Path,
    config_path: Path,
    authority_path: Path,
    preflight_audit_path: Path,
    preparation_audit_path: Path,
    pair_root: Path,
    run_root: Path,
) -> dict[str, Any]:
    for path, label in (
        (contract_path, "primary contract"),
        (config_path, "training config"),
        (authority_path, "primary authority"),
        (preflight_audit_path, "preflight audit"),
        (preparation_audit_path, "preparation audit"),
        (pair_root, "pair root"),
        (run_root, "run root"),
    ):
        require_primary_path(path, REPO_ROOT, label)
    if Path(authority_path).name != EXPECTED_AUTHORITY_NAME:
        raise ValueError("primary authority filename is not the Task 4 authority")

    plan = PRIMARY.build_execution_plan(
        contract_path, config_path, authority_path, pair_root, run_root
    )
    contract = load_json(contract_path)
    config = load_json(config_path)
    authority = load_json(authority_path)
    gate = PRIMARY.require_primary_training_authority(
        authority, contract_path, config_path
    )
    if gate.get("maximum_executions") != 1:
        raise ValueError("primary authority must permit exactly one execution")
    if gate.get("resume_authorized"):
        raise ValueError("fresh Task 4 authority cannot authorize resume")
    if sha256_file(preflight_audit_path) != gate["preflight_audit_sha256"]:
        raise ValueError("primary preflight audit SHA-256 mismatch")
    preflight = load_json(preflight_audit_path)
    if preflight.get("status") != "passed_zero_step_primary_preflight":
        raise ValueError("primary preflight status is not passed")
    if preflight.get("execution", {}).get("optimizer_steps") != 0:
        raise ValueError("preflight audit is not a zero-step result")
    if sha256_file(preparation_audit_path) != gate["preparation_audit_sha256"]:
        raise ValueError("preparation audit SHA-256 mismatch")
    preparation = load_json(preparation_audit_path)
    if preparation.get("status") != "passed_runtime_and_fixed_revision_weight_gate":
        raise ValueError("runtime/model preparation Gate has not passed")

    output_root = expected_output_root(run_root, contract)
    if output_root.exists():
        raise FileExistsError("refusing to overwrite an existing primary run")
    return {
        "plan": plan,
        "contract": contract,
        "config": config,
        "authority": authority,
        "gate": gate,
        "preflight": preflight,
        "preparation": preparation,
        "output_root": output_root,
    }


def _save_epoch_checkpoint(
    model: Any,
    optimizer: Any,
    scheduler: Any,
    torch: Any,
    output_root: Path,
    epoch: int,
    trainer_state: dict[str, Any],
    maximum_file_bytes: int,
) -> dict[str, Any]:
    checkpoint_root = output_root / f"checkpoint-epoch-{epoch:03d}"
    checkpoint_root.mkdir(parents=False, exist_ok=False)
    adapter_dir = checkpoint_root / "adapter"
    model.save_pretrained(adapter_dir, safe_serialization=True)
    torch.save(optimizer.state_dict(), checkpoint_root / "optimizer.pt")
    torch.save(scheduler.state_dict(), checkpoint_root / "scheduler.pt")
    torch.save(
        {
            "python": random.getstate(),
            "torch_cpu": torch.get_rng_state(),
            "torch_cuda": torch.cuda.get_rng_state_all(),
        },
        checkpoint_root / "rng-state.pt",
    )
    write_json_no_overwrite(checkpoint_root / "trainer-state.json", trainer_state)
    files = checkpoint_manifest(checkpoint_root, maximum_file_bytes)
    return {
        "epoch": epoch,
        "optimizer_step": trainer_state["optimizer_step"],
        "root": checkpoint_root.name,
        "files": files,
        "adapter_only": True,
        "merged_model_saved": False,
    }


def run_primary_training(
    contract_path: Path,
    config_path: Path,
    authority_path: Path,
    preflight_audit_path: Path,
    preparation_audit_path: Path,
    pair_root: Path,
    run_root: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    verified = _verify_authorized_inputs(
        contract_path,
        config_path,
        authority_path,
        preflight_audit_path,
        preparation_audit_path,
        pair_root,
        run_root,
    )
    contract = verified["contract"]
    config = verified["config"]
    authority = verified["authority"]
    preparation = verified["preparation"]
    output_root = verified["output_root"]
    output_root.mkdir(parents=True, exist_ok=False)
    progress_path = output_root / PROGRESS_NAME
    state = {
        "completed_epochs": 0,
        "optimizer_steps": 0,
        "microbatches": 0,
        "checkpoint_epochs": [],
    }
    append_progress(
        progress_path,
        {
            "event": "primary_training_started",
            "epoch": 0,
            "optimizer_step": 0,
            "optimizer_steps_total": config["optimizer_steps"],
            "elapsed_seconds": 0.0,
            "created_date": authority["created_date"],
        },
    )

    try:
        serialization_record = contract["frozen_inputs"]["serialization_contract"]
        serialization_path = REPO_ROOT / serialization_record["path"]
        if sha256_file(serialization_path) != serialization_record["sha256"]:
            raise ValueError("serialization contract SHA-256 mismatch")
        serialization = load_json(serialization_path)["serialization"]

        train_record = contract["pair_payloads"]["train"]
        validation_record = contract["pair_payloads"]["training_validation"]
        train_examples = PRIMARY.load_pair_file(
            Path(pair_root) / train_record["file"], train_record["sha256"]
        )
        validation_examples = PRIMARY.load_pair_file(
            Path(pair_root) / validation_record["file"], validation_record["sha256"]
        )
        dataset_report = PRIMARY.validate_primary_datasets(
            train_examples, validation_examples, config
        )
        del validation_examples

        preflight_contract_path = REPO_ROOT / (
            "09-experiments/llm_evidence_compiler_mainline/contracts/"
            "qwen25-primary-preflight-contract-v0.1.json"
        )
        preflight_contract = load_json(preflight_contract_path)
        smoke_contract_record = preflight_contract["tracked_inputs"]["smoke_contract"]
        smoke_contract_path = REPO_ROOT / smoke_contract_record["path"]
        if sha256_file(smoke_contract_path) != smoke_contract_record["sha256"]:
            raise ValueError("smoke contract SHA-256 mismatch")
        smoke_contract = load_json(smoke_contract_path)
        snapshot_dir = require_primary_path(
            Path(preparation["model_snapshot"]["snapshot_dir"]),
            REPO_ROOT,
            "model snapshot",
        )
        model_lock = PREFLIGHT.PREPARE.verify_snapshot(
            smoke_contract, snapshot_dir, Path(run_root)
        )
        runtime_versions = PREFLIGHT._package_versions(
            smoke_contract["runtime_packages"]
        )

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
            raise RuntimeError("the frozen local QLoRA runtime is unavailable") from error

        if not torch.cuda.is_available():
            raise ValueError("CUDA is unavailable")
        if torch.cuda.get_device_name(0) != config["hardware"]["execution_target"]:
            raise ValueError("GPU name differs from the frozen primary configuration")
        if list(torch.cuda.get_device_capability(0)) != config["hardware"][
            "minimum_compute_capability"
        ]:
            raise ValueError("GPU compute capability differs from the frozen value")

        random.seed(config["seed"])
        torch.manual_seed(config["seed"])
        torch.cuda.manual_seed_all(config["seed"])
        tokenizer = AutoTokenizer.from_pretrained(
            snapshot_dir, local_files_only=True, trust_remote_code=False
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        encoded_by_id = {}
        for example in train_examples:
            identity = example["example_id"]
            encoded = encode_assistant_only(
                example, serialization, tokenizer, config["sequence_length"]
            )
            if all(label == -100 for label in encoded["labels"]):
                raise ValueError("assistant-only loss mask has no supervised tokens")
            encoded_by_id[identity] = encoded
        if len(encoded_by_id) != config["data"]["train_examples"]:
            raise ValueError("encoded training example count is incomplete")

        compute_dtype = {"float16": torch.float16}[
            config["quantization"]["compute_dtype"]
        ]
        quantization = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=config["quantization"]["type"],
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=config["quantization"][
                "double_quantization"
            ],
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
        trainable_parameters = [
            parameter for parameter in model.parameters() if parameter.requires_grad
        ]
        trainable = sum(parameter.numel() for parameter in trainable_parameters)
        total = sum(parameter.numel() for parameter in model.parameters())
        parameter_gate = PREFLIGHT.validate_trainable_ratio(
            trainable,
            total,
            contract["frozen_training_snapshot"]["maximum_trainable_ratio"],
        )
        module_gate = PREFLIGHT.summarize_target_module_inventory(
            [name for name, _ in model.named_modules()],
            config["lora"]["target_modules"],
        )

        optimizer = bnb.optim.PagedAdamW8bit(
            trainable_parameters,
            lr=config["learning_rate"],
            weight_decay=config["weight_decay"],
        )
        scheduler = get_cosine_schedule_with_warmup(
            optimizer,
            num_warmup_steps=config["scheduler"]["warmup_steps"],
            num_training_steps=config["optimizer_steps"],
        )
        optimizer.zero_grad(set_to_none=True)
        model.train()
        all_losses: list[float] = []
        all_gradient_norms: list[float] = []
        epoch_summaries = []
        checkpoints = []
        peak_limit = int(
            config["hardware"]["maximum_operational_peak_vram_gib"] * 1024**3
        )
        maximum_wall_seconds = (
            config["resource_limits"]["maximum_primary_wall_hours"] * 3600
        )

        for epoch in range(1, config["epochs"] + 1):
            epoch_losses: list[float] = []
            epoch_gradients: list[float] = []
            accumulated_losses: list[float] = []
            ordered = PRIMARY.order_epoch_examples(train_examples, config["seed"], epoch)
            for example in ordered:
                encoded = encoded_by_id[example["example_id"]]
                batch = {
                    key: torch.tensor([value], device="cuda", dtype=torch.long)
                    for key, value in encoded.items()
                }
                loss = model(**batch).loss
                if not torch.isfinite(loss).item():
                    raise ValueError("non-finite primary training loss")
                loss_value = float(loss.detach().cpu())
                all_losses.append(loss_value)
                epoch_losses.append(loss_value)
                accumulated_losses.append(loss_value)
                (loss / config["gradient_accumulation_steps"]).backward()
                state["microbatches"] += 1
                del batch
                del loss

                if len(accumulated_losses) != config["gradient_accumulation_steps"]:
                    continue
                gradient_norm_tensor = torch.nn.utils.clip_grad_norm_(
                    trainable_parameters, config["maximum_gradient_norm"]
                )
                gradient_norm = float(gradient_norm_tensor.detach().cpu())
                if not math.isfinite(gradient_norm):
                    raise ValueError("non-finite primary gradient norm")
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                state["optimizer_steps"] += 1
                all_gradient_norms.append(gradient_norm)
                epoch_gradients.append(gradient_norm)
                peak_reserved = torch.cuda.max_memory_reserved(0)
                if peak_reserved > peak_limit:
                    raise ValueError("operational peak GPU memory exceeds the frozen limit")
                elapsed = time.monotonic() - started
                if elapsed > maximum_wall_seconds:
                    raise TimeoutError("primary training exceeded the 24-hour wall limit")
                append_progress(
                    progress_path,
                    {
                        "event": "optimizer_step_completed",
                        "epoch": epoch,
                        "optimizer_step": state["optimizer_steps"],
                        "optimizer_steps_total": config["optimizer_steps"],
                        "loss_mean_for_step": sum(accumulated_losses)
                        / len(accumulated_losses),
                        "gradient_norm": gradient_norm,
                        "learning_rate": scheduler.get_last_lr()[0],
                        "peak_reserved_vram_bytes": peak_reserved,
                        "elapsed_seconds": elapsed,
                    },
                )
                print(
                    canonical_json(
                        {
                            "event": "optimizer_step_completed",
                            "epoch": epoch,
                            "optimizer_step": state["optimizer_steps"],
                            "optimizer_steps_total": config["optimizer_steps"],
                            "loss_mean_for_step": sum(accumulated_losses)
                            / len(accumulated_losses),
                            "elapsed_seconds": elapsed,
                        }
                    ),
                    flush=True,
                )
                accumulated_losses = []

            if accumulated_losses:
                raise ValueError("epoch ended with a partial accumulation group")
            expected_step = epoch * config["optimizer_steps_per_epoch"]
            if state["optimizer_steps"] != expected_step:
                raise ValueError("epoch optimizer step count differs from the schedule")
            state["completed_epochs"] = epoch
            state["checkpoint_epochs"].append(epoch)
            epoch_summary = {
                "epoch": epoch,
                "optimizer_step_end": state["optimizer_steps"],
                "loss": summarize_values(epoch_losses, "epoch loss"),
                "gradient_norm": summarize_values(
                    epoch_gradients, "epoch gradient norm"
                ),
                "elapsed_seconds": time.monotonic() - started,
            }
            epoch_summaries.append(epoch_summary)
            trainer_state = {
                "schema_version": "project05-primary-trainer-state-v0.1",
                "completed_epoch": epoch,
                "optimizer_step": state["optimizer_steps"],
                "microbatches": state["microbatches"],
                "contract_sha256": sha256_file(contract_path),
                "training_config_sha256": sha256_file(config_path),
                "authority_sha256": sha256_file(authority_path),
                "loss": epoch_summary["loss"],
                "gradient_norm": epoch_summary["gradient_norm"],
                "raw_pair_payload_recorded": False,
                "raw_generation_recorded": False,
            }
            checkpoint = _save_epoch_checkpoint(
                model,
                optimizer,
                scheduler,
                torch,
                output_root,
                epoch,
                trainer_state,
                config["resource_limits"]["maximum_adapter_file_bytes"],
            )
            checkpoints.append(checkpoint)
            resource_bytes = PRIMARY.unique_physical_bytes(
                [
                    Path(run_root) / "local-runtime",
                    Path(run_root) / "local-cache",
                    Path(run_root) / "local-output",
                ]
            )
            resource_limit = config["resource_limits"][
                "maximum_environment_cache_checkpoint_output_bytes"
            ]
            if resource_bytes > resource_limit:
                raise ValueError("runtime/cache/checkpoint bytes exceed the frozen limit")
            gc.collect()
            torch.cuda.empty_cache()
            append_progress(
                progress_path,
                {
                    "event": "epoch_checkpoint_completed",
                    "epoch": epoch,
                    "optimizer_step": state["optimizer_steps"],
                    "optimizer_steps_total": config["optimizer_steps"],
                    "peak_reserved_vram_bytes": torch.cuda.max_memory_reserved(0),
                    "elapsed_seconds": time.monotonic() - started,
                },
            )

        summary = {
            **state,
            "losses_finite": all(math.isfinite(value) for value in all_losses),
            "gradient_norms_finite": all(
                math.isfinite(value) for value in all_gradient_norms
            ),
        }
        validate_completed_training(summary, config)
        elapsed = time.monotonic() - started
        peak_reserved = torch.cuda.max_memory_reserved(0)
        resource_bytes = PRIMARY.unique_physical_bytes(
            [
                Path(run_root) / "local-runtime",
                Path(run_root) / "local-cache",
                Path(run_root) / "local-output",
            ]
        )
        result = {
            "schema_version": "project05-qwen25-primary-training-audit-v0.1",
            "status": "passed_single_primary_adapter_training",
            "created_date": authority["created_date"],
            "contract_sha256": sha256_file(contract_path),
            "training_config_sha256": sha256_file(config_path),
            "authority_sha256": sha256_file(authority_path),
            "preflight_audit_sha256": sha256_file(preflight_audit_path),
            "preparation_audit_sha256": sha256_file(preparation_audit_path),
            "model": {
                "repository_id": model_lock["repository_id"],
                "revision": model_lock["revision"],
                "file_count": model_lock["file_count"],
                "all_allowlisted_files_rehashed": True,
                "quantization": config["quantization"],
            },
            "runtime": {
                "packages": runtime_versions,
                "gpu_name": torch.cuda.get_device_name(0),
                "torch_cuda": str(torch.version.cuda),
            },
            "data_gate": PREFLIGHT.sanitize_dataset_report(dataset_report),
            "training": {
                **summary,
                "loss": summarize_values(all_losses, "training loss"),
                "gradient_norm": summarize_values(
                    all_gradient_norms, "training gradient norm"
                ),
                "epoch_summaries": epoch_summaries,
                "wall_seconds": elapsed,
                "wall_limit_seconds": maximum_wall_seconds,
                "trainable_parameters": trainable,
                "total_parameters": total,
                "trainable_ratio": parameter_gate["ratio"],
                "target_module_counts": module_gate["counts"],
                "peak_reserved_vram_bytes": peak_reserved,
                "peak_reserved_vram_limit_bytes": peak_limit,
            },
            "checkpoints": checkpoints,
            "resources": {
                "runtime_cache_checkpoint_output_bytes": resource_bytes,
                "maximum_bytes": config["resource_limits"][
                    "maximum_environment_cache_checkpoint_output_bytes"
                ],
            },
            "privacy_and_scope": {
                "raw_pair_payload_recorded": False,
                "raw_generation_recorded": False,
                "model_generation_calls": 0,
                "development_or_test_accessed": False,
                "c07_c12_accessed": False,
                "m3_integrated": False,
                "server_connected": False,
                "paper_a_modified": False,
                "merged_model_saved": False,
                "hub_upload_used": False,
            },
            "next_gate": {
                "status": "hard_stop_for_task5_checkpoint_selection_authorization",
                "checkpoint_selection_authorized": False,
                "formal_inference_authorized": False,
                "development_execution_authorized": False,
                "c07_c12_execution_authorized": False,
                "m3_integration_authorized": False,
            },
        }
        write_json_no_overwrite(output_root / FINAL_AUDIT_NAME, result)
        append_progress(
            progress_path,
            {
                "event": "primary_training_completed",
                "epoch": config["epochs"],
                "optimizer_step": state["optimizer_steps"],
                "optimizer_steps_total": config["optimizer_steps"],
                "peak_reserved_vram_bytes": peak_reserved,
                "elapsed_seconds": elapsed,
            },
        )
        return result
    except BaseException as error:
        failure = {
            "schema_version": "project05-qwen25-primary-training-failure-v0.1",
            "status": "failed_or_interrupted_primary_training",
            "created_date": verified["authority"]["created_date"],
            "contract_sha256": sha256_file(contract_path),
            "training_config_sha256": sha256_file(config_path),
            "authority_sha256": sha256_file(authority_path),
            "failure_type": type(error).__name__,
            "failure_message": str(error)[:500],
            "completed_epochs": state["completed_epochs"],
            "optimizer_steps": state["optimizer_steps"],
            "microbatches": state["microbatches"],
            "checkpoint_epochs": state["checkpoint_epochs"],
            "elapsed_seconds": time.monotonic() - started,
            "raw_pair_payload_recorded": False,
            "raw_generation_recorded": False,
            "automatic_restart_authorized": False,
            "checkpoint_selection_authorized": False,
        }
        failure_path = output_root / FAILURE_AUDIT_NAME
        if not failure_path.exists():
            write_json_no_overwrite(failure_path, failure)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--preflight-audit", type=Path, required=True)
    parser.add_argument("--preparation-audit", type=Path, required=True)
    parser.add_argument("--pair-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_primary_training(
        args.contract,
        args.config,
        args.authority,
        args.preflight_audit,
        args.preparation_audit,
        args.pair_root,
        args.run_root,
    )
    print(result["status"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
