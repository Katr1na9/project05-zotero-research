"""Run the bounded, adapter-only Qwen2.5 QLoRA smoke on one RTX 4090.

This command consumes only the frozen train and training-validation pair
payloads. It executes exactly sixteen accumulated microbatches and one
optimizer step, saves/reloads an adapter, performs one eight-token validation
generation, and records no raw prompt, target, payload or generated text.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import random
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_SPLITS = {"train", "training-validation"}
PROHIBITED_PATH_PARTS = {
    "development",
    "test",
    "g2",
    "c07",
    "c08",
    "c09",
    "c10",
    "c11",
    "c12",
    "08-writing",
    "run_mvp.py",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_json(path: Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def is_within(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def require_within(path: Path, root: Path, label: str) -> Path:
    resolved = Path(path).resolve()
    if not is_within(resolved, root):
        raise ValueError(f"{label} escapes the execution boundary")
    lowered = {part.lower() for part in resolved.parts}
    if lowered & PROHIBITED_PATH_PARTS:
        raise ValueError(f"{label} contains a prohibited path component")
    return resolved


def write_json_no_overwrite(path: Path, value: Any) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"temporary output already exists: {temporary}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def validate_execution_boundary(
    contract: dict[str, Any], run_root: Path, repo_root: Path = REPO_ROOT
) -> tuple[Path, Path]:
    local = contract.get("execution_boundary")
    if local is not None:
        if local["mode"] != "repository_relative_local_windows":
            raise ValueError("unsupported local execution boundary mode")
        observed_repo = Path(repo_root).resolve()
        expected_root = (observed_repo / local["run_directory_name"]).resolve()
        run_root = Path(run_root).resolve()
        if os.name != "nt":
            raise ValueError("the local QLoRA smoke command is Windows-only")
        if run_root != expected_root:
            raise ValueError("run root differs from the repository-relative local path")
        if not is_within(run_root, observed_repo):
            raise ValueError("local run root escapes the repository")
        return observed_repo, run_root

    boundary = contract["server_execution_boundary"]
    allowed_home = Path(boundary["allowed_home"]).resolve()
    expected_root = (allowed_home / boundary["run_directory_name"]).resolve()
    run_root = Path(run_root).resolve()
    if os.name != "posix":
        raise ValueError("the 4090 smoke command is Linux-only")
    if run_root != expected_root:
        raise ValueError("run root differs from the exact contracted server path")
    if not is_within(repo_root, allowed_home):
        raise ValueError("repository is outside /home/myy")
    return allowed_home, run_root


validate_server_boundary = validate_execution_boundary


def resolve_field_path(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            raise ValueError(f"serialization source field is missing: {path}")
        current = current[segment]
    return current


def build_messages(
    example: dict[str, Any], serialization: dict[str, Any], include_assistant: bool
) -> list[dict[str, str]]:
    user = {
        output: resolve_field_path(example, source)
        for output, source in serialization["user_field_sources"].items()
    }
    messages = [
        {"role": "system", "content": serialization["system_message"]},
        {"role": "user", "content": canonical_json(user)},
    ]
    if include_assistant:
        assistant = {
            field: example[field] for field in serialization["assistant_fields"]
        }
        messages.append({"role": "assistant", "content": canonical_json(assistant)})
    return messages


def render_messages(
    messages: list[dict[str, str]], serialization: dict[str, Any]
) -> str:
    template = serialization["chat_turn_template"]
    return "".join(
        template.format(role=message["role"], content=message["content"])
        for message in messages
    )


def render_training_parts(
    example: dict[str, Any], serialization: dict[str, Any]
) -> tuple[str, str]:
    messages = build_messages(example, serialization, include_assistant=True)
    prompt = render_messages(messages[:2], serialization) + "<|im_start|>assistant\n"
    target = messages[2]["content"] + "<|im_end|>\n"
    return prompt, target


def encode_assistant_only(
    example: dict[str, Any], serialization: dict[str, Any], tokenizer: Any, limit: int
) -> dict[str, list[int]]:
    prompt, target = render_training_parts(example, serialization)
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
    target_ids = tokenizer.encode(target, add_special_tokens=False)
    input_ids = prompt_ids + target_ids
    if not target_ids:
        raise ValueError("assistant target tokenization is empty")
    if len(input_ids) > limit:
        raise ValueError("smoke example exceeds the no-truncation limit")
    return {
        "input_ids": input_ids,
        "attention_mask": [1] * len(input_ids),
        "labels": [-100] * len(prompt_ids) + target_ids,
    }


def load_pair_file(path: Path, expected_sha256: str) -> list[dict[str, Any]]:
    if sha256_file(path) != expected_sha256:
        raise ValueError("pair payload SHA-256 mismatch")
    output = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                output.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid pair JSONL at line {line_number}") from error
    return output


def stable_rank(example: dict[str, Any], seed: int, namespace: str) -> str:
    identity = example.get("example_id")
    if not isinstance(identity, str) or not identity:
        raise ValueError("pair example_id is missing")
    return sha256_text(f"{seed}|{namespace}|{identity}")


def select_smoke_examples(
    examples: list[dict[str, Any]], seed: int, per_class: int = 10
) -> dict[str, Any]:
    by_class: dict[str, list[dict[str, Any]]] = {
        "supported": [],
        "unsupported_by_bound_pointer": [],
    }
    for example in examples:
        decision = example.get("support_decision")
        if decision not in by_class:
            raise ValueError("unexpected support decision in train payload")
        by_class[decision].append(example)
    selected = []
    training = []
    for decision in sorted(by_class):
        ranked = sorted(
            by_class[decision], key=lambda item: stable_rank(item, seed, decision)
        )
        if len(ranked) < per_class:
            raise ValueError("insufficient examples for balanced smoke selection")
        chosen = ranked[:per_class]
        selected.extend(chosen)
        training.extend(chosen[:8])
    selected.sort(key=lambda item: stable_rank(item, seed, "selected-order"))
    training.sort(key=lambda item: stable_rank(item, seed, "training-order"))
    return {
        "selected": selected,
        "training": training,
        "selected_counts": {
            decision: sum(item["support_decision"] == decision for item in selected)
            for decision in sorted(by_class)
        },
        "training_counts": {
            decision: sum(item["support_decision"] == decision for item in training)
            for decision in sorted(by_class)
        },
    }


def validate_adapter_directory(adapter_dir: Path, maximum_file_bytes: int) -> list[dict[str, Any]]:
    allowed = {
        "README.md",
        "adapter_config.json",
        "adapter_model.safetensors",
    }
    observed = {path.name for path in adapter_dir.iterdir() if path.is_file()}
    required = {"adapter_config.json", "adapter_model.safetensors"}
    if not required <= observed or not observed <= allowed:
        raise ValueError("adapter output contains a missing or prohibited file")
    files = []
    for path in sorted(adapter_dir.iterdir()):
        if not path.is_file():
            raise ValueError("adapter output contains a nested directory")
        size = path.stat().st_size
        if size > maximum_file_bytes:
            raise ValueError("adapter output exceeds the file-size limit")
        files.append({"name": path.name, "bytes": size, "sha256": sha256_file(path)})
    return files


def sanitized_example_ids(examples: list[dict[str, Any]]) -> list[str]:
    return sorted(sha256_text(example["example_id"]) for example in examples)


def unique_physical_bytes(paths: list[Path]) -> int:
    observed: set[Path] = set()
    total = 0
    for root in paths:
        root = Path(root)
        if not root.exists():
            continue
        candidates = [root] if root.is_file() else (
            path for path in root.rglob("*") if path.is_file()
        )
        for path in candidates:
            physical = path.resolve()
            if physical in observed:
                continue
            observed.add(physical)
            total += physical.stat().st_size
    return total


def run_smoke(
    contract_path: Path,
    config_path: Path,
    preparation_audit_path: Path,
    pair_root: Path,
    run_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    contract = load_json(contract_path)
    config = load_json(config_path)
    allowed_root, run_root = validate_execution_boundary(contract, run_root)
    for path, label in (
        (contract_path, "contract"),
        (config_path, "training config"),
        (preparation_audit_path, "preparation audit"),
        (pair_root, "pair root"),
        (output_path, "smoke audit"),
    ):
        require_within(path, allowed_root, label)
    if sha256_file(config_path) != contract["training_config"]["sha256"]:
        raise ValueError("training configuration SHA-256 mismatch")

    serialization_path = REPO_ROOT / contract["data_inputs"][
        "serialization_contract_path"
    ]
    if (
        sha256_file(serialization_path)
        != contract["data_inputs"]["serialization_contract_sha256"]
    ):
        raise ValueError("serialization contract SHA-256 mismatch")
    serialization = load_json(serialization_path)["serialization"]

    preparation = load_json(preparation_audit_path)
    if preparation["status"] != "passed_runtime_and_fixed_revision_weight_gate":
        raise ValueError("runtime/model preparation Gate has not passed")
    if preparation["contract_sha256"] != sha256_file(contract_path):
        raise ValueError("preparation audit belongs to a different contract")
    snapshot_dir = require_within(
        Path(preparation["model_snapshot"]["snapshot_dir"]), run_root, "model snapshot"
    )

    pair_audit_path = REPO_ROOT / contract["data_inputs"]["pair_audit_path"]
    token_audit_path = REPO_ROOT / contract["data_inputs"]["token_audit_path"]
    if sha256_file(pair_audit_path) != contract["data_inputs"]["pair_audit_sha256"]:
        raise ValueError("pair audit SHA-256 mismatch")
    if sha256_file(token_audit_path) != contract["data_inputs"]["token_audit_sha256"]:
        raise ValueError("token audit SHA-256 mismatch")
    token_audit = load_json(token_audit_path)
    if not token_audit["gate"]["formal_data_gate_passed"]:
        raise ValueError("formal data/token Gate has not passed")

    pair_root = Path(pair_root)
    train_path = pair_root / "train.jsonl.gz"
    validation_path = pair_root / "training-validation.jsonl.gz"
    train_examples = load_pair_file(
        train_path, contract["data_inputs"]["train_pair_sha256"]
    )
    validation_examples = load_pair_file(
        validation_path,
        contract["data_inputs"]["training_validation_pair_sha256"],
    )
    selection = select_smoke_examples(
        train_examples, config["seed"], config["smoke_supported"]
    )
    if config["smoke_supported"] != config["smoke_pointer_unsupported"]:
        raise ValueError("smoke class quotas are not balanced")
    if len(selection["selected"]) != config["smoke_packet_limit"]:
        raise ValueError("smoke selection count differs from the configuration")
    if len(selection["training"]) != config["gradient_accumulation_steps"]:
        raise ValueError("training microbatch count differs from the configuration")

    try:
        import torch
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import bitsandbytes as bnb
    except ImportError as error:
        raise RuntimeError("the frozen QLoRA runtime is unavailable") from error

    random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    torch.cuda.manual_seed_all(config["seed"])
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot_dir, local_files_only=True, trust_remote_code=False
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    encodings = [
        encode_assistant_only(
            example, serialization, tokenizer, config["sequence_length"]
        )
        for example in selection["training"]
    ]
    if any(all(label == -100 for label in item["labels"]) for item in encodings):
        raise ValueError("assistant-only loss mask has no supervised tokens")

    compute_dtype = {"float16": torch.float16}[config["quantization"]["compute_dtype"]]
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=config["quantization"]["type"],
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=config["quantization"]["double_quantization"],
    )
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
    trainable = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    total = sum(parameter.numel() for parameter in model.parameters())
    ratio = trainable / total
    if trainable <= 0 or ratio >= 0.01:
        raise ValueError("trainable adapter ratio is outside (0, 1%)")

    optimizer = bnb.optim.PagedAdamW8bit(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=config["learning_rate"],
    )
    model.train()
    optimizer.zero_grad(set_to_none=True)
    losses = []
    for encoded in encodings:
        batch = {
            key: torch.tensor([value], device="cuda", dtype=torch.long)
            for key, value in encoded.items()
        }
        loss = model(**batch).loss
        if not torch.isfinite(loss).item():
            raise ValueError("non-finite smoke loss")
        losses.append(float(loss.detach().cpu()))
        (loss / config["gradient_accumulation_steps"]).backward()
    gradient_norm = float(
        torch.nn.utils.clip_grad_norm_(
            [parameter for parameter in model.parameters() if parameter.requires_grad],
            config["maximum_gradient_norm"],
        ).detach().cpu()
    )
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)

    adapter_dir = require_within(run_root / "local-output" / "adapter", run_root, "adapter")
    if adapter_dir.exists():
        raise FileExistsError("refusing to overwrite an existing adapter directory")
    adapter_dir.mkdir(parents=True)
    model.save_pretrained(adapter_dir, safe_serialization=True)
    adapter_files = validate_adapter_directory(
        adapter_dir, config["resource_limits"]["maximum_adapter_file_bytes"]
    )
    resource_bytes = unique_physical_bytes(
        [
            run_root / "local-runtime",
            run_root / "local-cache",
            run_root / "local-output",
        ]
    )
    resource_limit = config["resource_limits"][
        "maximum_environment_cache_adapter_bytes"
    ]
    if resource_bytes > resource_limit:
        raise ValueError("environment/cache/adapter bytes exceed the smoke limit")
    model.delete_adapter("default")
    model.load_adapter(str(adapter_dir), adapter_name="smoke_reloaded", is_trainable=False)
    model.set_adapter("smoke_reloaded")

    validation = min(
        validation_examples,
        key=lambda item: stable_rank(item, config["seed"], "validation"),
    )
    validation_messages = build_messages(
        validation, serialization, include_assistant=False
    )
    validation_prompt = render_messages(
        validation_messages, serialization
    ) + "<|im_start|>assistant\n"
    validation_ids = tokenizer.encode(validation_prompt, add_special_tokens=False)
    if len(validation_ids) > config["sequence_length"]:
        raise ValueError("validation prompt exceeds the no-truncation limit")
    model.eval()
    model.config.use_cache = True
    with torch.no_grad():
        generated = model.generate(
            input_ids=torch.tensor([validation_ids], device="cuda", dtype=torch.long),
            max_new_tokens=config["validation_generation_max_new_tokens"],
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    new_ids = generated[0, len(validation_ids) :].detach().cpu().tolist()
    raw_generation = tokenizer.decode(new_ids, skip_special_tokens=False)
    peak_bytes = torch.cuda.max_memory_reserved(0)
    peak_limit = int(
        config["hardware"]["maximum_operational_peak_vram_gib"] * 1024**3
    )
    if peak_bytes > peak_limit:
        raise ValueError("operational peak GPU memory exceeds the 4090 smoke limit")
    elapsed = time.monotonic() - started
    if elapsed > config["resource_limits"]["maximum_smoke_wall_minutes"] * 60:
        raise ValueError("smoke wall time exceeds the contract")

    return {
        "schema_version": "project05-qwen25-qlora-smoke-result-v0.1",
        "status": "passed_one_step_adapter_only_smoke",
        "contract_id": contract["contract_id"],
        "contract_sha256": sha256_file(contract_path),
        "training_config_sha256": sha256_file(config_path),
        "model": {
            "repository_id": contract["model"]["repository_id"],
            "revision": contract["model"]["revision"],
            "quantization": config["quantization"],
        },
        "selection": {
            "selected_examples": len(selection["selected"]),
            "training_microbatches": len(selection["training"]),
            "selected_counts": selection["selected_counts"],
            "training_counts": selection["training_counts"],
            "selected_id_hashes": sanitized_example_ids(selection["selected"]),
            "training_id_hashes": sanitized_example_ids(selection["training"]),
            "raw_pair_payload_recorded": False,
        },
        "training": {
            "optimizer_steps": 1,
            "loss_first": losses[0],
            "loss_last": losses[-1],
            "loss_mean": sum(losses) / len(losses),
            "losses_finite": all(math.isfinite(value) for value in losses),
            "gradient_norm": gradient_norm,
            "trainable_parameters": trainable,
            "total_parameters": total,
            "trainable_ratio": ratio,
            "peak_vram_bytes": peak_bytes,
            "peak_vram_limit_bytes": peak_limit,
            "wall_seconds": elapsed,
        },
        "adapter": {
            "adapter_only": True,
            "merged_model_saved": False,
            "saved_and_reloaded": True,
            "files": adapter_files,
        },
        "resources": {
            "environment_cache_adapter_bytes": resource_bytes,
            "maximum_environment_cache_adapter_bytes": resource_limit,
        },
        "validation_generation": {
            "examples": 1,
            "maximum_new_tokens": config["validation_generation_max_new_tokens"],
            "generated_token_count": len(new_ids),
            "generated_text_sha256": sha256_text(raw_generation),
            "raw_generation_recorded": False,
            "example_id_sha256": sha256_text(validation["example_id"]),
        },
        "authorization_boundary": {
            "primary_training_run": False,
            "formal_inference_run": False,
            "development_or_test_accessed": False,
            "c07_c12_accessed": False,
            "m3_integrated": False,
            "paper_a_modified": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--preparation-audit", type=Path, required=True)
    parser.add_argument("--pair-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_smoke(
        args.contract,
        args.config,
        args.preparation_audit,
        args.pair_root,
        args.run_root,
        args.output,
    )
    write_json_no_overwrite(args.output, result)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
