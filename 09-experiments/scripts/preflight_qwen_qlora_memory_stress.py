"""Run the one-shot longest-sequence QLoRA memory stress preflight.

The stress run performs exactly sixteen forward/backward microbatches and one
optimizer step under the frozen primary configuration.  All trainable state is
discarded in memory; no adapter, checkpoint, generation, or raw example data is
written.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import math
import os
import random
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_PATH = Path(__file__).with_name("train_qwen_qlora_primary.py")
PREFLIGHT_PATH = Path(__file__).with_name("preflight_qwen_qlora_primary.py")
EXPECTED_AUTHORITY_NAME = "authority-lock-v0.27.json"
EXPECTED_ALLOCATOR = "max_split_size_mb:128,garbage_collection_threshold:0.8"


def _load_helper(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no module loader")
    spec.loader.exec_module(module)
    return module


PRIMARY = _load_helper(PRIMARY_PATH, "project05_memory_stress_primary")
PREFLIGHT = _load_helper(PREFLIGHT_PATH, "project05_memory_stress_preflight")
load_json = PRIMARY.load_json
sha256_file = PRIMARY.sha256_file
sha256_text = PRIMARY.sha256_text
canonical_json = PRIMARY.canonical_json
write_json_no_overwrite = PRIMARY.SMOKE.write_json_no_overwrite
require_primary_path = PRIMARY.require_primary_path
encode_assistant_only = PRIMARY.encode_assistant_only


def rank_stress_candidates(
    identity_lengths: list[tuple[str, int]], count: int
) -> list[tuple[str, int]]:
    if count <= 0 or len(identity_lengths) < count:
        raise ValueError("stress candidate count is invalid")
    identities = [identity for identity, _ in identity_lengths]
    if len(set(identities)) != len(identities):
        raise ValueError("stress candidate identities are not unique")
    if any(not identity or length <= 0 for identity, length in identity_lengths):
        raise ValueError("stress candidate identity or length is invalid")
    return sorted(
        identity_lengths,
        key=lambda row: (-row[1], sha256_text(row[0])),
    )[:count]


def validate_stress_selection(
    ranked: list[tuple[str, int]], contract: dict[str, Any]
) -> dict[str, Any]:
    expected = contract["selection"]
    lengths = [length for _, length in ranked]
    if lengths != expected["expected_lengths_descending"]:
        raise ValueError("stress selection lengths differ from the frozen envelope")
    if min(lengths) != expected["expected_min_tokens"]:
        raise ValueError("stress selection minimum length differs")
    if max(lengths) != expected["expected_max_tokens"]:
        raise ValueError("stress selection maximum length differs")
    if sum(lengths) != expected["expected_total_tokens"]:
        raise ValueError("stress selection total tokens differs")
    digest_rows = [
        {"example_id_sha256": sha256_text(identity), "tokens": length}
        for identity, length in ranked
    ]
    return {
        "examples": len(ranked),
        "lengths_descending": lengths,
        "minimum_tokens": min(lengths),
        "maximum_tokens": max(lengths),
        "total_tokens": sum(lengths),
        "mean_tokens": sum(lengths) / len(lengths),
        "selection_digest_sha256": sha256_text(canonical_json(digest_rows)),
        "raw_example_ids_recorded": False,
        "raw_payload_recorded": False,
    }


def verify_stress_contract(
    contract_path: Path, authority_path: Path, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    contract_path = require_primary_path(contract_path, repo_root, "stress contract")
    authority_path = require_primary_path(authority_path, repo_root, "stress authority")
    if authority_path.name != EXPECTED_AUTHORITY_NAME:
        raise ValueError("stress authority filename is not v0.27")
    contract = load_json(contract_path)
    for name in ("parent_authority", "approved_amendment"):
        record = contract[name]
        if sha256_file(repo_root / record["path"]) != record["sha256"]:
            raise ValueError(f"{name} SHA-256 mismatch")
    for name, record in contract["frozen_inputs"].items():
        if sha256_file(repo_root / record["path"]) != record["sha256"]:
            raise ValueError(f"{name} SHA-256 mismatch")
    for name, record in contract["local_inputs"].items():
        if sha256_file(repo_root / record["path"]) != record["sha256"]:
            raise ValueError(f"{name} SHA-256 mismatch")
    authority = load_json(authority_path)
    gate = authority.get("memory_stress_gate", {})
    if not gate.get("authorized"):
        raise PermissionError("memory stress preflight is not authorized")
    if gate.get("contract_sha256") != sha256_file(contract_path):
        raise ValueError("stress authority contract SHA-256 mismatch")
    if gate.get("maximum_executions") != 1:
        raise ValueError("stress authority must allow exactly one execution")
    if authority.get("next_gate", {}).get("primary_training_authorized"):
        raise ValueError("stress authority cannot authorize primary retry")
    return {"contract": contract, "authority": authority, "gate": gate}


def exact_output_path(contract: dict[str, Any], run_root: Path) -> Path:
    run_root = require_primary_path(run_root, REPO_ROOT, "run root")
    expected_root = (REPO_ROOT / contract["execution_boundary"]["run_root"]).resolve()
    if run_root != expected_root:
        raise ValueError("stress run root differs from the contract")
    output = require_primary_path(
        run_root / contract["execution_boundary"]["output_path"],
        REPO_ROOT,
        "stress output",
    )
    if output.exists():
        raise FileExistsError("refusing to overwrite the stress preflight result")
    return output


def run_memory_stress(
    contract_path: Path,
    authority_path: Path,
    run_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    verified = verify_stress_contract(contract_path, authority_path)
    contract = verified["contract"]
    authority = verified["authority"]
    run_root = require_primary_path(run_root, REPO_ROOT, "run root")
    expected_output = exact_output_path(contract, run_root)
    output_path = require_primary_path(output_path, REPO_ROOT, "stress output")
    if output_path != expected_output:
        raise ValueError("stress output path differs from the contract")
    allocator = os.environ.get("PYTORCH_CUDA_ALLOC_CONF")
    if allocator != contract["stabilization"]["pytorch_cuda_alloc_conf"]:
        raise ValueError("PYTORCH_CUDA_ALLOC_CONF differs from the amendment")

    primary_contract_record = contract["frozen_inputs"]["primary_training_contract"]
    primary_config_record = contract["frozen_inputs"]["primary_training_config"]
    primary_contract_path = REPO_ROOT / primary_contract_record["path"]
    primary_config_path = REPO_ROOT / primary_config_record["path"]
    verified_primary = PRIMARY.verify_contract_files(
        primary_contract_path, primary_config_path
    )
    primary_contract = verified_primary["contract"]
    config = verified_primary["config"]
    preparation = load_json(REPO_ROOT / contract["local_inputs"]["preparation_audit"]["path"])
    pair_root = (
        REPO_ROOT
        / "09-experiments/llm_evidence_compiler_mainline/candidate_pairs_v0.2/local-data"
    )
    train = PRIMARY.load_pair_file(
        pair_root / primary_contract["pair_payloads"]["train"]["file"],
        primary_contract["pair_payloads"]["train"]["sha256"],
    )
    validation = PRIMARY.load_pair_file(
        pair_root / primary_contract["pair_payloads"]["training_validation"]["file"],
        primary_contract["pair_payloads"]["training_validation"]["sha256"],
    )
    dataset_report = PRIMARY.validate_primary_datasets(train, validation, config)
    del validation

    serialization_record = primary_contract["frozen_inputs"]["serialization_contract"]
    serialization = load_json(REPO_ROOT / serialization_record["path"])["serialization"]
    primary_preflight_contract = load_json(
        REPO_ROOT / contract["frozen_inputs"]["primary_preflight_contract"]["path"]
    )
    smoke_record = primary_preflight_contract["tracked_inputs"]["smoke_contract"]
    smoke_contract = load_json(REPO_ROOT / smoke_record["path"])
    snapshot_dir = require_primary_path(
        Path(preparation["model_snapshot"]["snapshot_dir"]),
        REPO_ROOT,
        "model snapshot",
    )

    state = {"microbatches": 0, "optimizer_steps": 0}
    torch = None
    try:
        model_lock = PREFLIGHT.PREPARE.verify_snapshot(
            smoke_contract, snapshot_dir, run_root
        )
        runtime_versions = PREFLIGHT._package_versions(
            smoke_contract["runtime_packages"]
        )
        try:
            import bitsandbytes as bnb
            import torch as torch_runtime
            from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                BitsAndBytesConfig,
                get_cosine_schedule_with_warmup,
            )
        except ImportError as error:
            raise RuntimeError("the frozen local QLoRA runtime is unavailable") from error
        torch = torch_runtime
        if not torch.cuda.is_available():
            raise ValueError("CUDA is unavailable")
        if torch.cuda.get_device_name(0) != config["hardware"]["execution_target"]:
            raise ValueError("GPU identity differs from the primary configuration")

        random.seed(config["seed"])
        torch.manual_seed(config["seed"])
        torch.cuda.manual_seed_all(config["seed"])
        tokenizer = AutoTokenizer.from_pretrained(
            snapshot_dir, local_files_only=True, trust_remote_code=False
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        encoded_by_id = {}
        identity_lengths = []
        for example in train:
            encoded = encode_assistant_only(
                example, serialization, tokenizer, config["sequence_length"]
            )
            identity = example["example_id"]
            encoded_by_id[identity] = encoded
            identity_lengths.append((identity, len(encoded["input_ids"])))
        ranked = rank_stress_candidates(
            identity_lengths, contract["selection"]["examples"]
        )
        selection_report = validate_stress_selection(ranked, contract)
        encodings = [encoded_by_id[identity] for identity, _ in ranked]
        del encoded_by_id
        del identity_lengths
        del train

        compute_dtype = {"float16": torch.float16}[
            config["quantization"]["compute_dtype"]
        ]
        quantization = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=config["quantization"]["type"],
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=config["quantization"]["double_quantization"],
        )
        gc.collect()
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
            primary_contract["frozen_training_snapshot"]["maximum_trainable_ratio"],
        )
        module_gate = PREFLIGHT.summarize_target_module_inventory(
            [name for name, _ in model.named_modules()], config["lora"]["target_modules"]
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
        losses = []
        post_microbatch_memory = []
        for index, encoded in enumerate(encodings, 1):
            batch = {
                key: torch.tensor([value], device="cuda", dtype=torch.long)
                for key, value in encoded.items()
            }
            loss = model(**batch).loss
            if not torch.isfinite(loss).item():
                raise ValueError("non-finite stress loss")
            losses.append(float(loss.detach().cpu()))
            (loss / config["gradient_accumulation_steps"]).backward()
            state["microbatches"] = index
            del batch
            del loss
            gc.collect()
            torch.cuda.empty_cache()
            post_microbatch_memory.append(
                {
                    "microbatch": index,
                    "tokens": len(encoded["input_ids"]),
                    "allocated_bytes": torch.cuda.memory_allocated(0),
                    "reserved_bytes": torch.cuda.memory_reserved(0),
                }
            )
        gradient_norm = float(
            torch.nn.utils.clip_grad_norm_(
                trainable_parameters, config["maximum_gradient_norm"]
            ).detach().cpu()
        )
        if not math.isfinite(gradient_norm):
            raise ValueError("non-finite stress gradient norm")
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad(set_to_none=True)
        state["optimizer_steps"] = 1
        torch.cuda.synchronize(0)
        peak_allocated = torch.cuda.max_memory_allocated(0)
        peak_reserved = torch.cuda.max_memory_reserved(0)
        peak_limit = contract["memory_gate"]["peak_reserved_limit_bytes"]
        passed = peak_reserved <= peak_limit
        status = (
            "passed_memory_stress_preflight"
            if passed
            else "failed_memory_stress_preflight_peak_reserved"
        )
        del optimizer
        del scheduler
        del model
        del lora
        del quantization
        del trainable_parameters
        gc.collect()
        torch.cuda.empty_cache()
        post_cleanup_reserved = torch.cuda.memory_reserved(0)
        result = {
            "schema_version": "project05-qwen25-memory-stress-result-v0.1",
            "status": status,
            "created_date": authority["created_date"],
            "contract_sha256": sha256_file(contract_path),
            "authority_sha256": sha256_file(authority_path),
            "primary_contract_sha256": sha256_file(primary_contract_path),
            "training_config_sha256": sha256_file(primary_config_path),
            "allocator": allocator,
            "selection": selection_report,
            "data_gate": PREFLIGHT.sanitize_dataset_report(dataset_report),
            "model": {
                "repository_id": model_lock["repository_id"],
                "revision": model_lock["revision"],
                "all_allowlisted_files_rehashed": True,
            },
            "runtime": {
                "packages": runtime_versions,
                "gpu_name": torch.cuda.get_device_name(0),
                "torch_cuda": str(torch.version.cuda),
            },
            "execution": {
                "microbatches": state["microbatches"],
                "optimizer_steps": state["optimizer_steps"],
                "loss_first": losses[0],
                "loss_last": losses[-1],
                "loss_mean": sum(losses) / len(losses),
                "losses_finite": all(math.isfinite(value) for value in losses),
                "gradient_norm": gradient_norm,
                "trainable_parameters": trainable,
                "total_parameters": total,
                "trainable_ratio": parameter_gate["ratio"],
                "target_module_counts": module_gate["counts"],
                "wall_seconds": time.monotonic() - started,
                "adapter_or_checkpoint_files_written": 0,
                "model_generation_calls": 0,
            },
            "memory_gate": {
                "peak_allocated_bytes": peak_allocated,
                "peak_reserved_bytes": peak_reserved,
                "peak_reserved_limit_bytes": peak_limit,
                "post_cleanup_reserved_bytes": post_cleanup_reserved,
                "post_microbatch_memory": post_microbatch_memory,
                "cuda_oom": False,
                "passed": passed,
            },
            "privacy_and_scope": {
                "raw_example_ids_recorded": False,
                "raw_pair_payload_recorded": False,
                "raw_generation_recorded": False,
                "development_or_test_accessed": False,
                "c07_c12_accessed": False,
                "m3_integrated": False,
                "server_connected": False,
                "paper_a_modified": False,
                "adapter_saved": False,
                "checkpoint_saved": False,
            },
            "next_gate": {
                "status": "hard_stop_for_result_review_and_separate_retry_authorization",
                "primary_retry_authorized": False,
                "checkpoint_selection_authorized": False,
                "formal_inference_authorized": False,
                "c07_c12_execution_authorized": False,
                "m3_integration_authorized": False,
            },
        }
    except BaseException as error:
        if torch is not None:
            try:
                gc.collect()
                torch.cuda.empty_cache()
                post_cleanup_reserved = torch.cuda.memory_reserved(0)
            except BaseException:
                post_cleanup_reserved = None
        else:
            post_cleanup_reserved = None
        result = {
            "schema_version": "project05-qwen25-memory-stress-result-v0.1",
            "status": "failed_memory_stress_preflight_exception",
            "created_date": authority["created_date"],
            "contract_sha256": sha256_file(contract_path),
            "authority_sha256": sha256_file(authority_path),
            "allocator": allocator,
            "failure": {
                "type": type(error).__name__,
                "message": str(error)[:500],
                "microbatches_completed": state["microbatches"],
                "optimizer_steps": state["optimizer_steps"],
                "post_cleanup_reserved_bytes": post_cleanup_reserved,
            },
            "privacy_and_scope": {
                "raw_example_ids_recorded": False,
                "raw_pair_payload_recorded": False,
                "raw_generation_recorded": False,
                "adapter_or_checkpoint_files_written": 0,
            },
            "next_gate": {
                "status": "hard_stop_after_failed_stress_preflight",
                "primary_retry_authorized": False,
                "checkpoint_selection_authorized": False,
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
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_memory_stress(
        args.contract, args.authority, args.run_root, args.output
    )
    print(result["status"], flush=True)
    return 0 if result["status"] == "passed_memory_stress_preflight" else 2


if __name__ == "__main__":
    raise SystemExit(main())
