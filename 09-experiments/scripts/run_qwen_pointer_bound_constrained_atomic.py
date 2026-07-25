#!/usr/bin/env python3
"""Run the pointer-bound constrained training-validation atomic diagnostic.

This v0.44 route is separate from the completed v0.43 negative result.  Model
output never contains an evidence pointer.  JSON Schema constrained decoding
produces a decision plus pointer-free semantic edge slots, and trusted code
then binds the already-visible pointer.  Importing this module is model-lazy
and does not require torch, PEFT, or the constrained-decoding dependency.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Protocol


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
GENERAL = "QWEN-GENERAL"
ADAPTED = "QWEN-ADAPTED"
CONDITIONS = (GENERAL, ADAPTED)
DECISIONS = ("supported", "unsupported_by_bound_pointer")
RAW_ROWS_NAME = "pointer-bound-raw-generations-v0.1.jsonl"
GENERATION_AUDIT_NAME = "pointer-bound-generation-audit-v0.1.json"
FAILURE_NAME = "pointer-bound-generation-failure-v0.1.json"
EXPECTED_CONSTRAINED_DISTRIBUTION = "lm-format-enforcer"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no loader")
    spec.loader.exec_module(module)
    return module


LEGACY = _load(
    SCRIPT_DIR / "run_qwen_general_adapted_paired.py",
    "project05_pointer_bound_legacy_helpers",
)
BINDER = _load(
    SCRIPT_DIR / "bind_pointer_bound_compiler_output.py",
    "project05_pointer_binding",
)
SELECTOR = LEGACY.SELECTOR


def canonical_json(value: Any) -> str:
    return LEGACY.canonical_json(value)


def sha256_text(value: str) -> str:
    return LEGACY.sha256_text(value)


def sha256_file(path: Path) -> str:
    return LEGACY.sha256_file(path)


def load_json(path: Path) -> Any:
    return LEGACY.load_json(path)


def write_json_no_overwrite(path: Path, value: Any) -> None:
    LEGACY.write_json_no_overwrite(path, value)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    LEGACY.append_jsonl(path, value)


def require_within(path: Path, root: Path, label: str) -> Path:
    return LEGACY.require_within(path, root, label)


def verify_hash_record(record: dict[str, Any], label: str) -> Path:
    return LEGACY.verify_hash_record(record, label)


def validate_config(config: dict[str, Any]) -> None:
    if config.get("conditions") != [GENERAL, ADAPTED]:
        raise ValueError("pointer-bound conditions differ")
    panel = config.get("panel", {})
    expected_panel = {
        "split": "training-validation",
        "source_examples": 300,
        "exact_examples": 16,
        "families": {
            "logpai_loghub_linux": 150,
            "zeek_non_pcap_test_logs": 150,
        },
        "decisions_per_family": {
            "supported": 75,
            "unsupported_by_bound_pointer": 75,
        },
        "examples_per_family_decision": 4,
        "selection_seed": 2026072002,
        "must_differ_from_v041_panel_seed": 2026072001,
        "without_replacement": True,
        "panel_identity_server_only": True,
    }
    if panel != expected_panel:
        raise ValueError("pointer-bound atomic panel configuration differs")
    if panel["selection_seed"] == panel["must_differ_from_v041_panel_seed"]:
        raise ValueError("pointer-bound panel silently reuses the v0.41 seed")
    if config.get("condition_order") != {
        "seed": 2026071802,
        "blocking_factors": ["source_family_id", "support_decision"],
        "exactly_balanced_within_block": True,
    }:
        raise ValueError("pointer-bound condition order differs")
    constrained = config.get("constrained_decoding", {})
    if constrained != {
        "engine_distribution": EXPECTED_CONSTRAINED_DISTRIBUTION,
        "engine_version": "0.10.6",
        "integration": "transformers_prefix_allowed_tokens_fn",
        "json_schema_path": (
            "09-experiments/data_schema/"
            "pointer_bound_compiler_output.schema.json"
        ),
        "schema_support_preflight_required": True,
        "unconstrained_fallback_allowed": False,
        "repair_invalid_output_allowed": False,
        "retry_allowed": False,
        "pointer_in_model_output_allowed": False,
    }:
        raise ValueError("constrained-decoding configuration differs")
    if config.get("decode") != {
        "do_sample": False,
        "maximum_new_tokens": 192,
        "require_eos_termination": True,
        "batch_size": 1,
    }:
        raise ValueError("pointer-bound decode configuration differs")
    gates = config.get("gates", {})
    positive = gates.get("positive_generation", {})
    if positive.get("macro_f1_may_override_failed_positive_gate") is not False:
        raise ValueError("macro F1 is allowed to override the positive Gate")
    if config.get("checkpoint_selection_policy", {}).get(
        "eligibility_precedes_ranking"
    ) is not True:
        raise ValueError("checkpoint ranking precedes positive eligibility")
    output = config.get("output_policy", {})
    if output.get("raw_generation") != "server_only":
        raise ValueError("raw generations must remain server-only")
    if output.get("controller_eligible") is not False:
        raise ValueError("atomic diagnostic output cannot enter the controller")


def validate_implementation_bundle(
    contract_path: Path,
    config_path: Path,
    authority_path: Path,
) -> dict[str, Any]:
    contract_path = require_within(contract_path, REPO_ROOT, "v0.44 contract")
    config_path = require_within(config_path, REPO_ROOT, "v0.44 config")
    authority_path = require_within(authority_path, REPO_ROOT, "v0.44 authority")
    contract = load_json(contract_path)
    config = load_json(config_path)
    authority = load_json(authority_path)
    if contract_path != (REPO_ROOT / contract["contract_repository_path"]).resolve():
        raise ValueError("v0.44 contract path differs")
    if config_path != (REPO_ROOT / contract["config"]["path"]).resolve():
        raise ValueError("v0.44 config path differs")
    if authority_path != (
        REPO_ROOT / contract["implementation_authority"]["path"]
    ).resolve():
        raise ValueError("v0.44 implementation authority path differs")
    if sha256_file(config_path) != contract["config"]["sha256"]:
        raise ValueError("v0.44 config SHA-256 mismatch")
    if sha256_file(contract_path) != authority["implementation_gate"][
        "contract_sha256"
    ]:
        raise ValueError("v0.44 contract/authority SHA-256 mismatch")
    for label in (
        "parent_negative_result_authority",
        "approved_amendment",
        "serialization_contract",
        "model_output_schema",
        "runtime_requirement",
        "training_validation_payload_lock",
        "model_preparation_audit",
    ):
        verify_hash_record(contract[label], label)
    for label, record in contract["implementation"].items():
        verify_hash_record(record, label)
    validate_config(config)
    if authority["implementation_gate"].get("model_free_implementation_authorized") is not True:
        raise PermissionError("v0.44 model-free implementation is closed")
    if authority["implementation_gate"].get("model_execution_authorized") is not False:
        raise ValueError("v0.44 must not authorize model execution")
    return {
        "contract": contract,
        "config": config,
        "authority": authority,
        "contract_path": contract_path,
        "config_path": config_path,
        "authority_path": authority_path,
    }


def validate_execution_authority(
    execution_authority_path: Path,
    verified: dict[str, Any],
) -> dict[str, Any]:
    path = require_within(
        execution_authority_path,
        REPO_ROOT,
        "pointer-bound execution authority",
    )
    authority = load_json(path)
    gate = authority.get("pointer_bound_execution_gate", {})
    if gate.get("authorized") is not True or gate.get("maximum_executions") != 1:
        raise PermissionError("one new explicit pointer-bound execution is required")
    if gate.get("contract_sha256") != sha256_file(verified["contract_path"]):
        raise ValueError("pointer-bound execution contract SHA-256 mismatch")
    if gate.get("config_sha256") != sha256_file(verified["config_path"]):
        raise ValueError("pointer-bound execution config SHA-256 mismatch")
    if gate.get("split") != "training-validation" or gate.get("examples") != 16:
        raise PermissionError("pointer-bound execution exceeds the atomic panel")
    if any(
        gate.get(field) is not False
        for field in (
            "train_access_authorized",
            "development_or_test_access_authorized",
            "c07_c12_execution_authorized",
            "m3_integration_authorized",
            "automatic_retry_authorized",
            "unconstrained_fallback_authorized",
        )
    ):
        raise PermissionError("pointer-bound downstream, retry, or fallback scope is open")
    dependency = authority.get("runtime_dependency_audit")
    verify_hash_record(dependency, "runtime dependency audit")
    return authority


def validate_source_examples(
    examples: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    panel = config["panel"]
    if len(examples) != panel["source_examples"]:
        raise ValueError("training-validation example count differs")
    if any(row.get("split_role") != panel["split"] for row in examples):
        raise ValueError("non-training-validation example entered the panel")
    if dict(sorted(Counter(row.get("source_family_id") for row in examples).items())) != panel["families"]:
        raise ValueError("training-validation family quotas differ")
    for family in panel["families"]:
        counts = Counter(
            row.get("support_decision")
            for row in examples
            if row.get("source_family_id") == family
        )
        if dict(sorted(counts.items())) != panel["decisions_per_family"]:
            raise ValueError(f"decision quotas differ for {family}")


def select_atomic_panel(
    examples: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    validate_source_examples(examples, config)
    panel = config["panel"]
    selected: list[dict[str, Any]] = []
    for family in sorted(panel["families"]):
        for decision in DECISIONS:
            group = [
                row
                for row in examples
                if row["source_family_id"] == family
                and row["support_decision"] == decision
            ]
            group.sort(
                key=lambda row: sha256_text(
                    f"{panel['selection_seed']}|pointer-bound|{row['example_id']}"
                )
            )
            selected.extend(group[: panel["examples_per_family_decision"]])
    if len(selected) != panel["exact_examples"]:
        raise ValueError("pointer-bound panel size differs")
    if len({row["example_id"] for row in selected}) != len(selected):
        raise ValueError("pointer-bound panel contains duplicate examples")
    return selected


def build_condition_orders(
    panel: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, list[str]]:
    seed = config["condition_order"]["seed"]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in panel:
        groups[(row["source_family_id"], row["support_decision"])].append(row)
    orders: dict[str, list[str]] = {}
    for key, rows in sorted(groups.items()):
        rows.sort(
            key=lambda row: sha256_text(
                f"{seed}|pointer-bound-order|{key[0]}|{key[1]}|{row['example_id']}"
            )
        )
        if len(rows) % 2:
            raise ValueError("condition-order block cannot be exactly balanced")
        for index, row in enumerate(rows):
            orders[row["example_id"]] = (
                [GENERAL, ADAPTED] if index % 2 == 0 else [ADAPTED, GENERAL]
            )
    if Counter(order[0] for order in orders.values()) != {
        GENERAL: len(panel) // 2,
        ADAPTED: len(panel) // 2,
    }:
        raise ValueError("pointer-bound condition order is not balanced")
    return orders


def resolve_field_path(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            raise ValueError(f"serialization source field is missing: {path}")
        current = current[segment]
    return current


def render_prompt(example: dict[str, Any], serialization: dict[str, Any]) -> str:
    user = {
        output: resolve_field_path(example, source)
        for output, source in serialization["user_field_sources"].items()
    }
    user_text = canonical_json(user)
    for field in serialization["forbidden_message_fields"]:
        if f'"{field}"' in user_text:
            raise ValueError(f"forbidden field entered pointer-bound prompt: {field}")
    template = serialization["chat_turn_template"]
    return (
        template.format(role="system", content=serialization["system_message"])
        + template.format(role="user", content=user_text)
        + "<|im_start|>assistant\n"
    )


def public_input_sha256(example: dict[str, Any]) -> str:
    return sha256_text(
        canonical_json(
            {
                "source_modality": example["source_modality"],
                "bound_pointer": example["pointer"],
                "payload": example["source_record"]["payload"],
                "candidate": example["candidate"],
            }
        )
    )


def expected_shared_manifest_keys() -> tuple[str, ...]:
    return (
        "base_snapshot_sha256",
        "tokenizer_snapshot_sha256",
        "runtime_lock_sha256",
        "quantization_config_sha256",
        "serialization_contract_sha256",
        "model_output_schema_sha256",
        "pointer_binder_sha256",
        "scorer_sha256",
        "constrained_decoder_distribution",
        "constrained_decoder_version",
        "decode_config_sha256",
        "hardware_id",
    )


class ConstrainedBackend(Protocol):
    def shared_manifest(self) -> dict[str, Any]:
        ...

    def generate(
        self,
        condition: str,
        prompt: str,
        example: dict[str, Any],
    ) -> dict[str, Any]:
        ...


def validate_generation(
    generated: dict[str, Any],
    condition: str,
    shared: dict[str, Any],
) -> None:
    expected_state = "off" if condition == GENERAL else "project05_obs_compiler:on"
    if generated.get("adapter_state") != expected_state:
        raise ValueError("backend adapter state differs from condition")
    if generated.get("same_loaded_base_process") is not True:
        raise ValueError("conditions did not share one loaded base process")
    for key in expected_shared_manifest_keys():
        if generated.get(key) != shared.get(key):
            raise ValueError(f"between-condition shared field differs: {key}")
    if generated.get("schema_constrained") is not True:
        raise ValueError("backend did not apply constrained decoding")
    if not isinstance(generated.get("raw_output"), str):
        raise ValueError("backend raw output is missing")
    if generated.get("raw_output_sha256") != sha256_text(generated["raw_output"]):
        raise ValueError("backend raw-output SHA-256 mismatch")
    parsed = json.loads(generated["raw_output"].strip())
    BINDER.validate_model_output(parsed)


def run_panel(
    panel: list[dict[str, Any]],
    config: dict[str, Any],
    serialization: dict[str, Any],
    backend: ConstrainedBackend,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(panel) != config["panel"]["exact_examples"]:
        raise ValueError("pointer-bound run panel size differs")
    orders = build_condition_orders(panel, config)
    shared = backend.shared_manifest()
    missing = set(expected_shared_manifest_keys()) - set(shared)
    if missing:
        raise ValueError(f"backend shared manifest is incomplete: {sorted(missing)}")
    rows: list[dict[str, Any]] = []
    started = time.monotonic()
    for example in panel:
        prompt = render_prompt(example, serialization)
        prompt_hash = sha256_text(prompt)
        example_hash = sha256_text(example["example_id"])
        for position, condition in enumerate(orders[example["example_id"]]):
            generated = backend.generate(condition, prompt, example)
            validate_generation(generated, condition, shared)
            rows.append(
                {
                    "schema_version": "project05-pointer-bound-raw-row-v0.1",
                    "condition": condition,
                    "condition_position": position,
                    "adapter_state": generated["adapter_state"],
                    "same_loaded_base_process": True,
                    "schema_constrained": True,
                    "example_id_sha256": example_hash,
                    "source_family_id": example["source_family_id"],
                    "source_modality": example["source_modality"],
                    "public_input_sha256": public_input_sha256(example),
                    "prompt_sha256": prompt_hash,
                    **{key: shared[key] for key in expected_shared_manifest_keys()},
                    "raw_output": generated["raw_output"],
                    "raw_output_sha256": generated["raw_output_sha256"],
                    "eos_terminated": generated["eos_terminated"],
                    "input_tokens": generated["input_tokens"],
                    "generated_tokens": generated["generated_tokens"],
                    "latency_seconds": generated["latency_seconds"],
                    "peak_allocated_bytes": generated["peak_allocated_bytes"],
                }
            )
    counts = Counter(row["condition"] for row in rows)
    if counts != {GENERAL: len(panel), ADAPTED: len(panel)}:
        raise ValueError("pointer-bound condition counts differ")
    return rows, {
        "examples": len(panel),
        "calls": len(rows),
        "condition_counts": dict(sorted(counts.items())),
        "first_condition_counts": dict(
            sorted(Counter(order[0] for order in orders.values()).items())
        ),
        "shared_manifest": shared,
        "wall_seconds": time.monotonic() - started,
        "raw_generation_server_only": True,
        "controller_eligible": False,
    }


class LmFormatEnforcerPeftBackend:
    """PEFT backend with grammar-level JSON Schema token filtering."""

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        torch: Any,
        adapter_name: str,
        prefix_allowed_tokens_fn: Any,
        shared: dict[str, Any],
        config: dict[str, Any],
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.torch = torch
        self.adapter_name = adapter_name
        self.prefix_allowed_tokens_fn = prefix_allowed_tokens_fn
        self._shared = shared
        self.config = config
        self.process_id = os.getpid()

    @classmethod
    def load(
        cls,
        snapshot_dir: Path,
        adapter_dir: Path,
        preparation: dict[str, Any],
        contract: dict[str, Any],
        config: dict[str, Any],
        schema: dict[str, Any],
    ) -> "LmFormatEnforcerPeftBackend":
        expected_version = config["constrained_decoding"]["engine_version"]
        observed_version = importlib.metadata.version(
            EXPECTED_CONSTRAINED_DISTRIBUTION
        )
        if observed_version != expected_version:
            raise RuntimeError("constrained-decoding package version differs")
        from lmformatenforcer import JsonSchemaParser
        from lmformatenforcer.integrations.transformers import (
            build_transformers_prefix_allowed_tokens_fn,
        )
        from peft import PeftModel

        stack = SELECTOR.CORE._load_training_stack()
        torch = stack["torch"]
        if sha256_file(adapter_dir / "adapter_model.safetensors") != contract[
            "selected_adapter"
        ]["adapter_sha256"]:
            raise ValueError("selected adapter SHA-256 mismatch")
        SELECTOR.CORE._runtime_gpu_gate(stack, config)
        tokenizer = stack["AutoTokenizer"].from_pretrained(
            snapshot_dir,
            local_files_only=True,
            trust_remote_code=False,
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        parser = JsonSchemaParser(schema)
        prefix_allowed_tokens_fn = build_transformers_prefix_allowed_tokens_fn(
            tokenizer,
            parser,
        )
        quantization = stack["BitsAndBytesConfig"](
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(0)
        base = stack["AutoModelForCausalLM"].from_pretrained(
            snapshot_dir,
            local_files_only=True,
            trust_remote_code=False,
            quantization_config=quantization,
            device_map={"": 0},
            torch_dtype=torch.float16,
        )
        base.config.use_cache = True
        adapter_name = "project05_obs_compiler"
        model = PeftModel.from_pretrained(
            base,
            adapter_dir,
            adapter_name=adapter_name,
            is_trainable=False,
        )
        model.eval()
        files = preparation["model_snapshot"]["files"]
        tokenizer_files = [
            row
            for row in files
            if row["path"]
            in {"merges.txt", "tokenizer.json", "tokenizer_config.json", "vocab.json"}
        ]
        shared = {
            "base_snapshot_sha256": sha256_text(canonical_json(files)),
            "tokenizer_snapshot_sha256": sha256_text(
                canonical_json(tokenizer_files)
            ),
            "runtime_lock_sha256": sha256_text(canonical_json(preparation["runtime"])),
            "quantization_config_sha256": sha256_text(
                canonical_json(config["quantization"])
            ),
            "serialization_contract_sha256": contract["serialization_contract"][
                "sha256"
            ],
            "model_output_schema_sha256": contract["model_output_schema"]["sha256"],
            "pointer_binder_sha256": contract["implementation"]["pointer_binder"][
                "sha256"
            ],
            "scorer_sha256": contract["implementation"]["scorer"]["sha256"],
            "constrained_decoder_distribution": EXPECTED_CONSTRAINED_DISTRIBUTION,
            "constrained_decoder_version": observed_version,
            "decode_config_sha256": sha256_text(canonical_json(config["decode"])),
            "hardware_id": preparation["runtime"]["gpu_name"],
        }
        return cls(
            model,
            tokenizer,
            torch,
            adapter_name,
            prefix_allowed_tokens_fn,
            shared,
            config,
        )

    def shared_manifest(self) -> dict[str, Any]:
        return dict(self._shared)

    def generate(
        self,
        condition: str,
        prompt: str,
        example: dict[str, Any],
    ) -> dict[str, Any]:
        if os.getpid() != self.process_id:
            raise RuntimeError("pointer-bound backend process identity changed")
        self.model.set_adapter(self.adapter_name)
        manager = (
            self.model.disable_adapter()
            if condition == GENERAL
            else contextlib.nullcontext()
        )
        encoded = self.tokenizer(
            prompt,
            return_tensors="pt",
            add_special_tokens=False,
        )
        input_ids = encoded["input_ids"].to("cuda")
        attention_mask = encoded["attention_mask"].to("cuda")
        started = time.monotonic()
        with manager, self.torch.inference_mode():
            output = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                do_sample=False,
                max_new_tokens=self.config["decode"]["maximum_new_tokens"],
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
                prefix_allowed_tokens_fn=self.prefix_allowed_tokens_fn,
            )
        self.torch.cuda.synchronize(0)
        generated = output[0, input_ids.shape[1] :].tolist()
        eos_ids = (
            self.tokenizer.eos_token_id
            if isinstance(self.tokenizer.eos_token_id, list)
            else [self.tokenizer.eos_token_id]
        )
        eos_position = next(
            (index for index, token in enumerate(generated) if token in eos_ids),
            None,
        )
        eos_terminated = eos_position is not None
        if self.config["decode"]["require_eos_termination"] and not eos_terminated:
            raise ValueError("constrained generation did not terminate with EOS")
        content_ids = generated[:eos_position] if eos_position is not None else generated
        text = self.tokenizer.decode(content_ids, skip_special_tokens=False)
        parsed = json.loads(text.strip())
        BINDER.validate_model_output(parsed)
        return {
            **self._shared,
            "adapter_state": (
                "off" if condition == GENERAL else "project05_obs_compiler:on"
            ),
            "same_loaded_base_process": True,
            "schema_constrained": True,
            "raw_output": text,
            "raw_output_sha256": sha256_text(text),
            "eos_terminated": eos_terminated,
            "input_tokens": int(input_ids.shape[1]),
            "generated_tokens": len(generated),
            "latency_seconds": time.monotonic() - started,
            "peak_allocated_bytes": int(self.torch.cuda.max_memory_allocated(0)),
        }


def run_authorized_execution(
    verified: dict[str, Any],
    execution_authority: dict[str, Any],
    pair_root: Path,
    run_root: Path,
    preparation_audit: Path,
) -> dict[str, Any]:
    if os.name != "posix":
        raise RuntimeError("authorized pointer-bound model execution is Linux-only")
    contract, config = verified["contract"], verified["config"]
    allowed_root = Path(contract["server_execution_boundary"]["allowed_root"]).resolve()
    run_root = Path(run_root).resolve()
    if run_root != allowed_root:
        raise ValueError("pointer-bound run root differs")
    pair_root = require_within(pair_root, run_root, "pointer-bound payload root")
    preparation_audit = require_within(
        preparation_audit,
        run_root,
        "model preparation audit",
    )
    preparation = load_json(preparation_audit)
    if sha256_file(preparation_audit) != contract["model_preparation_audit"]["sha256"]:
        raise ValueError("model preparation audit SHA-256 mismatch")
    pair_file = pair_root / contract["pair_payload"]["file"]
    examples = LEGACY.load_pair_file(pair_file, contract["pair_payload"]["sha256"])
    panel = select_atomic_panel(examples, config)
    serialization = load_json(
        REPO_ROOT / contract["serialization_contract"]["path"]
    )["serialization"]
    schema = load_json(REPO_ROOT / contract["model_output_schema"]["path"])
    snapshot_dir = require_within(
        Path(preparation["model_snapshot"]["snapshot_dir"]),
        run_root,
        "model snapshot",
    )
    adapter_dir = require_within(
        run_root / contract["selected_adapter"]["server_relative_path"],
        run_root,
        "selected adapter",
    )
    output_root = require_within(
        run_root / config["output_policy"]["run_subdirectory"],
        run_root,
        "pointer-bound output",
    )
    if output_root.exists():
        raise FileExistsError("refusing pointer-bound overwrite or resume")
    output_root.mkdir(parents=True, exist_ok=False)
    raw_path = output_root / RAW_ROWS_NAME
    try:
        backend = LmFormatEnforcerPeftBackend.load(
            snapshot_dir,
            adapter_dir,
            preparation,
            contract,
            config,
            schema,
        )
        rows, summary = run_panel(panel, config, serialization, backend)
        for row in rows:
            append_jsonl(raw_path, row)
        backend.torch.cuda.synchronize(0)
        free, total = backend.torch.cuda.mem_get_info(0)
        peak = int(backend.torch.cuda.max_memory_allocated(0))
        resources = SELECTOR.CORE.PRIMARY.unique_physical_bytes(
            [
                run_root / "local-runtime",
                run_root / "local-cache",
                run_root / "server-output",
            ]
        )
        if peak > config["hardware"]["maximum_peak_allocated_bytes"]:
            raise ValueError("pointer-bound peak-memory Gate failed")
        if int(free) < config["hardware"]["minimum_synchronized_free_bytes"]:
            raise ValueError("pointer-bound free-memory Gate failed")
        if summary["wall_seconds"] > config["resource_limits"]["maximum_wall_hours"] * 3600:
            raise ValueError("pointer-bound wall-time Gate failed")
        if resources > config["resource_limits"]["maximum_runtime_cache_checkpoint_output_bytes"]:
            raise ValueError("pointer-bound resource-size Gate failed")
        audit = {
            "schema_version": "project05-pointer-bound-generation-audit-v0.1",
            "status": "pointer_bound_generation_complete_scoring_pending",
            "contract_sha256": sha256_file(verified["contract_path"]),
            "config_sha256": sha256_file(verified["config_path"]),
            "execution_authority_sha256": sha256_file(
                REPO_ROOT / execution_authority["authority_repository_path"]
            ),
            "panel": {
                "examples": len(panel),
                "panel_identity_sha256": sha256_text(
                    canonical_json(
                        sorted(sha256_text(row["example_id"]) for row in panel)
                    )
                ),
                "identity_server_only": True,
            },
            "generation": summary,
            "resources": {
                "peak_allocated_bytes": peak,
                "final_free_bytes": int(free),
                "total_vram_bytes": int(total),
                "runtime_cache_checkpoint_output_bytes": resources,
            },
            "raw_rows": {
                "file": RAW_ROWS_NAME,
                "sha256": sha256_file(raw_path),
                "rows": len(rows),
                "server_only": True,
            },
            "privacy_and_scope": {
                "train_accessed": False,
                "development_or_test_accessed": False,
                "c07_c12_accessed": False,
                "m3_integrated": False,
                "raw_generation_download_authorized": False,
            },
            "next_gate": "server_side_pointer_binding_scoring_then_hard_stop",
        }
        write_json_no_overwrite(output_root / GENERATION_AUDIT_NAME, audit)
        return audit
    except BaseException as error:
        failure = {
            "schema_version": "project05-pointer-bound-generation-failure-v0.1",
            "status": "failed_pointer_bound_generation_no_automatic_retry",
            "failure_type": type(error).__name__,
            "failure_message": str(error)[:500],
            "automatic_retry_authorized": False,
            "unconstrained_fallback_authorized": False,
            "development_or_test_accessed": False,
            "m3_integrated": False,
        }
        if not (output_root / FAILURE_NAME).exists():
            write_json_no_overwrite(output_root / FAILURE_NAME, failure)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--implementation-authority", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--execution-authority", type=Path)
    parser.add_argument("--pair-root", type=Path)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--preparation-audit", type=Path)
    args = parser.parse_args()
    verified = validate_implementation_bundle(
        args.contract,
        args.config,
        args.implementation_authority,
    )
    if args.validate_only:
        print("v0.44 implementation valid; dependency install and model execution closed")
        return 0
    required = (
        args.execution_authority,
        args.pair_root,
        args.run_root,
        args.preparation_audit,
    )
    if any(value is None for value in required):
        raise ValueError(
            "execution authority, pair root, run root and preparation audit are required"
        )
    execution = validate_execution_authority(args.execution_authority, verified)
    result = run_authorized_execution(
        verified,
        execution,
        args.pair_root,
        args.run_root,
        args.preparation_audit,
    )
    print(result["status"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
