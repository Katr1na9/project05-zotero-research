"""Validate and stage the frozen Project05 primary QLoRA training contract.

This Tasks 1-2 implementation is deliberately model-lazy.  It defines the
immutable schedule, dataset checks, path boundary, checkpoint layout and
execution-authority guard, but the current authority cannot start preflight,
load a model, create an optimizer or run training.  A later authority must pin
this contract/config and a passed preflight before an execution body is added.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_HELPER_PATH = Path(__file__).with_name("train_qwen_qlora_smoke.py")
PROHIBITED_PATH_PARTS = {
    "development",
    "test",
    "g2",
    "m3",
    "c04",
    "c05",
    "c06",
    "c07",
    "c08",
    "c09",
    "c10",
    "c11",
    "c12",
    "08-writing",
    "real_cases",
    "run_mvp.py",
}
EXPECTED_TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]
EXPECTED_DECISIONS = {"supported", "unsupported_by_bound_pointer"}


def _load_smoke_helpers():
    spec = importlib.util.spec_from_file_location(
        "project05_qwen_qlora_smoke_helpers", SMOKE_HELPER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("smoke helper module has no loader")
    spec.loader.exec_module(module)
    return module


SMOKE = _load_smoke_helpers()
canonical_json = SMOKE.canonical_json
load_json = SMOKE.load_json
sha256_file = SMOKE.sha256_file
sha256_text = SMOKE.sha256_text
load_pair_file = SMOKE.load_pair_file
encode_assistant_only = SMOKE.encode_assistant_only
validate_adapter_directory = SMOKE.validate_adapter_directory
unique_physical_bytes = SMOKE.unique_physical_bytes


def is_within(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def require_primary_path(
    path: Path, root: Path = REPO_ROOT, label: str = "path"
) -> Path:
    resolved = Path(path).resolve()
    root = Path(root).resolve()
    if not is_within(resolved, root):
        raise ValueError(f"{label} escapes the repository execution boundary")
    lowered = {part.casefold() for part in resolved.parts}
    if lowered & PROHIBITED_PATH_PARTS:
        raise ValueError(f"{label} contains a prohibited path component")
    return resolved


def _require_equal(observed: Any, expected: Any, label: str) -> None:
    if observed != expected:
        raise ValueError(f"{label} differs from the frozen primary contract")


def build_training_schedule(config: dict[str, Any]) -> dict[str, Any]:
    train_examples = config["data"]["train_examples"]
    epochs = config["epochs"]
    accumulation = config["gradient_accumulation_steps"]
    micro_batch = config["micro_batch_size"]
    if micro_batch != 1:
        raise ValueError("primary microbatch must remain one")
    if train_examples % accumulation:
        raise ValueError("train examples must be divisible by gradient accumulation")
    steps_per_epoch = train_examples // accumulation
    microbatches = train_examples * epochs
    optimizer_steps = steps_per_epoch * epochs
    warmup_steps = math.ceil(optimizer_steps * config["scheduler"]["warmup_ratio"])
    schedule = {
        "microbatches": microbatches,
        "optimizer_steps": optimizer_steps,
        "optimizer_steps_per_epoch": steps_per_epoch,
        "checkpoint_steps": [steps_per_epoch * epoch for epoch in range(1, epochs + 1)],
        "warmup_steps": warmup_steps,
    }
    _require_equal(
        optimizer_steps, config["optimizer_steps"], "optimizer step count"
    )
    _require_equal(
        steps_per_epoch,
        config["optimizer_steps_per_epoch"],
        "optimizer steps per epoch",
    )
    _require_equal(
        warmup_steps, config["scheduler"]["warmup_steps"], "warmup step count"
    )
    _require_equal(
        schedule["checkpoint_steps"],
        [
            steps_per_epoch * epoch
            for epoch in config["checkpointing"]["epochs"]
        ],
        "checkpoint schedule",
    )
    return schedule


def validate_primary_config(
    config: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    snapshot = contract["frozen_training_snapshot"]
    direct = {
        "sequence_length": config["sequence_length"],
        "allow_truncation": config["allow_truncation"],
        "epochs": config["epochs"],
        "micro_batch_size": config["micro_batch_size"],
        "gradient_accumulation_steps": config["gradient_accumulation_steps"],
        "optimizer_steps": config["optimizer_steps"],
        "learning_rate": config["learning_rate"],
        "optimizer": config["optimizer"],
        "weight_decay": config["weight_decay"],
        "scheduler": config["scheduler"]["name"],
        "warmup_steps": config["scheduler"]["warmup_steps"],
        "seed": config["seed"],
        "maximum_operational_peak_vram_gib": config["hardware"][
            "maximum_operational_peak_vram_gib"
        ],
        "maximum_primary_wall_hours": config["resource_limits"][
            "maximum_primary_wall_hours"
        ],
        "maximum_total_resource_bytes": config["resource_limits"][
            "maximum_environment_cache_checkpoint_output_bytes"
        ],
        "adapter_only": config["output_policy"]["adapter_only"],
    }
    for key, expected in snapshot.items():
        if key == "maximum_trainable_ratio":
            continue
        _require_equal(direct[key], expected, key)
    _require_equal(config["base_model_id"], contract["model"]["repository_id"], "model")
    _require_equal(
        config["base_resolved_commit"], contract["model"]["revision"], "revision"
    )
    _require_equal(config["lora"], contract["lora_snapshot"], "LoRA configuration")
    _require_equal(
        config["lora"]["target_modules"],
        EXPECTED_TARGET_MODULES,
        "LoRA target modules",
    )
    _require_equal(config["quantization"]["bits"], 4, "quantization bits")
    _require_equal(config["quantization"]["type"], "nf4", "quantization type")
    _require_equal(
        config["quantization"]["double_quantization"],
        True,
        "double quantization",
    )
    _require_equal(
        config["quantization"]["compute_dtype"], "float16", "compute dtype"
    )
    _require_equal(config["data"]["train_examples"], 1200, "train examples")
    _require_equal(
        config["data"]["training_validation_examples"],
        300,
        "training-validation examples",
    )
    _require_equal(config["data"]["supported_fraction"], 0.5, "supported fraction")
    _require_equal(config["effective_batch_size"], 16, "effective batch size")
    _require_equal(config["loss_mask"], "assistant_target_only", "loss mask")
    _require_equal(
        config["checkpointing"]["epochs"], [1, 2, 3], "checkpoint epochs"
    )
    selection = contract["checkpoint_selection_snapshot"]
    _require_equal(
        config["training_validation"]["examples"],
        selection["examples"],
        "checkpoint selection example count",
    )
    for key in (
        "evaluate_all_examples",
        "do_sample",
        "maximum_new_tokens",
        "repair_invalid_output",
        "primary_metric",
        "tie_breakers",
    ):
        _require_equal(
            config["training_validation"][key],
            selection[key],
            f"checkpoint selection {key}",
        )
    if config["output_policy"]["allow_merged_model"]:
        raise ValueError("merged model output is prohibited")
    if config["output_policy"]["allow_hub_upload"]:
        raise ValueError("Hub upload is prohibited")
    return build_training_schedule(config)


def verify_contract_files(
    contract_path: Path, config_path: Path, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    contract_path = require_primary_path(contract_path, repo_root, "contract")
    config_path = require_primary_path(config_path, repo_root, "training config")
    contract = load_json(contract_path)
    config = load_json(config_path)
    expected_config_path = (repo_root / contract["training_config"]["path"]).resolve()
    _require_equal(config_path, expected_config_path, "training config path")
    _require_equal(
        sha256_file(config_path),
        contract["training_config"]["sha256"],
        "training config SHA-256",
    )
    for group in ("parent_authority", "approved_plan"):
        record = contract[group]
        path = (repo_root / record["path"]).resolve()
        _require_equal(sha256_file(path), record["sha256"], f"{group} SHA-256")
    for name, record in contract["frozen_inputs"].items():
        path = (repo_root / record["path"]).resolve()
        _require_equal(sha256_file(path), record["sha256"], f"{name} SHA-256")
    validate_primary_config(config, contract)
    return {"contract": contract, "config": config}


def _example_identity(example: dict[str, Any]) -> str:
    identity = example.get("example_id")
    if not isinstance(identity, str) or not identity:
        raise ValueError("pair example_id is missing")
    return identity


def order_epoch_examples(
    examples: list[dict[str, Any]], seed: int, epoch: int
) -> list[dict[str, Any]]:
    if epoch < 1:
        raise ValueError("epoch must be positive")
    identities = [_example_identity(example) for example in examples]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate pair example_id in epoch input")
    return sorted(
        examples,
        key=lambda example: sha256_text(
            f"{seed}|primary-epoch-{epoch}|{_example_identity(example)}"
        ),
    )


def _split_report(examples: list[dict[str, Any]], split: str) -> dict[str, Any]:
    identities = [_example_identity(example) for example in examples]
    if len(set(identities)) != len(identities):
        raise ValueError(f"duplicate example_id in {split}")
    decisions = Counter(example.get("support_decision") for example in examples)
    if set(decisions) != EXPECTED_DECISIONS:
        raise ValueError(f"unexpected support decision in {split}")
    families = Counter(example.get("source_family_id") for example in examples)
    if None in families or "" in families:
        raise ValueError(f"source family is missing in {split}")
    return {
        "examples": len(examples),
        "decisions": dict(sorted(decisions.items())),
        "families": dict(sorted(families.items())),
        "example_ids": set(identities),
    }


def validate_primary_datasets(
    train: list[dict[str, Any]],
    training_validation: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    train_report = _split_report(train, "train")
    validation_report = _split_report(training_validation, "training-validation")
    family_overlap = sorted(
        set(train_report["families"]) & set(validation_report["families"])
    )
    if family_overlap:
        raise ValueError("train/training-validation source family overlap")
    id_overlap = train_report["example_ids"] & validation_report["example_ids"]
    if id_overlap:
        raise ValueError("train/training-validation example_id overlap")
    expected = config["data"]
    _require_equal(train_report["examples"], expected["train_examples"], "train count")
    _require_equal(
        validation_report["examples"],
        expected["training_validation_examples"],
        "training-validation count",
    )
    _require_equal(
        len(train_report["families"]),
        expected["train_source_families"],
        "train family count",
    )
    _require_equal(
        len(validation_report["families"]),
        expected["training_validation_source_families"],
        "training-validation family count",
    )
    for report, label in (
        (train_report, "train"),
        (validation_report, "training-validation"),
    ):
        supported = report["decisions"]["supported"]
        _require_equal(
            supported / report["examples"],
            expected["supported_fraction"],
            f"{label} supported fraction",
        )
    return {
        "train": {
            key: value
            for key, value in train_report.items()
            if key != "example_ids"
        },
        "training_validation": {
            key: value
            for key, value in validation_report.items()
            if key != "example_ids"
        },
        "family_overlap": family_overlap,
        "example_id_overlap": [],
    }


def require_primary_training_authority(
    authority: dict[str, Any], contract_path: Path, config_path: Path
) -> dict[str, Any]:
    gate = authority.get("primary_training_gate")
    next_gate = authority.get("next_gate", {})
    if not gate or not gate.get("authorized") or not next_gate.get(
        "primary_training_authorized"
    ):
        raise PermissionError("primary training is not authorized")
    observed_contract = sha256_file(contract_path)
    observed_config = sha256_file(config_path)
    if gate.get("contract_sha256") != observed_contract:
        raise ValueError("execution authority contract SHA-256 mismatch")
    if gate.get("training_config_sha256") != observed_config:
        raise ValueError("execution authority training config SHA-256 mismatch")
    if not gate.get("preflight_required"):
        raise ValueError("execution authority must require a passed preflight")
    if not gate.get("preflight_passed"):
        raise ValueError("execution authority does not record a passed preflight")
    preflight_sha256 = gate.get("preflight_audit_sha256", "")
    if len(preflight_sha256) != 64 or any(
        character not in "0123456789ABCDEF" for character in preflight_sha256
    ):
        raise ValueError("execution authority preflight audit SHA-256 is invalid")
    return gate


def validate_primary_checkpoint(
    checkpoint_root: Path, maximum_file_bytes: int
) -> list[dict[str, Any]]:
    checkpoint_root = Path(checkpoint_root)
    if not checkpoint_root.is_dir():
        raise ValueError("checkpoint root is missing")
    allowed_files = {
        "trainer-state.json",
        "optimizer.pt",
        "scheduler.pt",
        "rng-state.pt",
    }
    allowed_directories = {"adapter"}
    observed_files = {
        path.name for path in checkpoint_root.iterdir() if path.is_file()
    }
    observed_directories = {
        path.name for path in checkpoint_root.iterdir() if path.is_dir()
    }
    if observed_files != allowed_files:
        raise ValueError("checkpoint contains a missing or prohibited top-level file")
    if observed_directories != allowed_directories:
        raise ValueError("checkpoint contains a missing or prohibited directory")
    rows = []
    for path in sorted(checkpoint_root.iterdir()):
        if path.is_dir():
            for item in validate_adapter_directory(path, maximum_file_bytes):
                rows.append({"path": f"adapter/{item['name']}", **item})
            continue
        size = path.stat().st_size
        if size > maximum_file_bytes:
            raise ValueError("checkpoint state file exceeds the file-size limit")
        rows.append(
            {
                "path": path.name,
                "name": path.name,
                "bytes": size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def build_execution_plan(
    contract_path: Path,
    config_path: Path,
    authority_path: Path,
    pair_root: Path,
    run_root: Path,
) -> dict[str, Any]:
    verified = verify_contract_files(contract_path, config_path)
    contract = verified["contract"]
    config = verified["config"]
    authority_path = require_primary_path(authority_path, REPO_ROOT, "authority")
    pair_root = require_primary_path(pair_root, REPO_ROOT, "pair root")
    run_root = require_primary_path(run_root, REPO_ROOT, "run root")
    expected_run_root = (
        REPO_ROOT / contract["execution_boundary"]["run_directory_name"]
    ).resolve()
    _require_equal(run_root, expected_run_root, "run root")
    if os.name != "nt":
        raise ValueError("primary local training is Windows-only")
    authority = load_json(authority_path)
    require_primary_training_authority(authority, contract_path, config_path)
    train_record = contract["pair_payloads"]["train"]
    validation_record = contract["pair_payloads"]["training_validation"]
    train = load_pair_file(pair_root / train_record["file"], train_record["sha256"])
    validation = load_pair_file(
        pair_root / validation_record["file"], validation_record["sha256"]
    )
    dataset_report = validate_primary_datasets(train, validation, config)
    return {
        "status": "validated_primary_training_execution_plan",
        "contract_sha256": sha256_file(contract_path),
        "training_config_sha256": sha256_file(config_path),
        "authority_sha256": sha256_file(authority_path),
        "schedule": build_training_schedule(config),
        "dataset": dataset_report,
        "output_root": str(
            run_root / contract["execution_boundary"]["primary_output_subdirectory"]
        ),
        "model_or_optimizer_loaded": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--pair-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_execution_plan(
        args.contract,
        args.config,
        args.authority,
        args.pair_root,
        args.run_root,
    )
    raise RuntimeError(
        "primary execution body is intentionally absent at HARD STOP T1-B; "
        f"validated plan {canonical_json(plan)}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
