#!/usr/bin/env python3
"""Run a hash-locked General-vs-Adapted paired atomic evaluation.

Importing this module is model-lazy: torch, transformers, bitsandbytes and PEFT
are imported only by ``PeftPairedBackend.load`` after a separate execution
authority has passed. The current v0.41 implementation authority is therefore
insufficient to perform model inference.
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import importlib.util
import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Protocol


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
CONTRACT_ROOT = (
    REPO_ROOT / "09-experiments/llm_evidence_compiler_mainline/contracts"
)
GENERAL = "QWEN-GENERAL"
ADAPTED = "QWEN-ADAPTED"
CONDITIONS = (GENERAL, ADAPTED)
DECISIONS = ("supported", "unsupported_by_bound_pointer")
RAW_ROWS_NAME = "paired-raw-generations-v0.1.jsonl"
GENERATION_AUDIT_NAME = "paired-generation-audit-v0.1.json"
FAILURE_NAME = "paired-generation-failure-v0.1.json"
PROHIBITED_PARTS = {
    "development",
    "test",
    "c07",
    "c08",
    "c09",
    "c10",
    "c11",
    "c12",
    "m3",
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no loader")
    spec.loader.exec_module(module)
    return module


SMOKE = _load(
    SCRIPT_DIR / "train_qwen_qlora_smoke.py",
    "project05_paired_smoke_helpers",
)
SELECTOR = _load(
    SCRIPT_DIR / "select_qwen_qlora_checkpoint_4090.py",
    "project05_paired_selection_helpers",
)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    with Path(path).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(value) + "\n")
        handle.flush()


def require_within(path: Path, root: Path, label: str) -> Path:
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(Path(root).resolve())
    except ValueError as error:
        raise ValueError(f"{label} escapes the execution boundary") from error
    return resolved


def verify_hash_record(record: dict[str, Any], label: str) -> Path:
    path = require_within(REPO_ROOT / record["path"], REPO_ROOT, label)
    if not path.is_file():
        raise FileNotFoundError(f"{label} is missing: {path}")
    observed = sha256_file(path)
    if observed != record["sha256"]:
        raise ValueError(f"{label} SHA-256 mismatch")
    return path


def validate_config(config: dict[str, Any]) -> None:
    if config.get("conditions") != [GENERAL, ADAPTED]:
        raise ValueError("paired conditions differ from the frozen order")
    panel = config.get("panel", {})
    if panel != {
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
        "selection_seed": 2026072001,
        "without_replacement": True,
        "panel_identity_server_only": True,
    }:
        raise ValueError("paired atomic panel configuration differs")
    if config.get("condition_order") != {
        "seed": 2026071801,
        "blocking_factors": [
            "source_family_id",
            "support_decision",
        ],
        "exactly_balanced_within_block": True,
    }:
        raise ValueError("condition-order configuration differs")
    if config.get("decode") != {
        "do_sample": False,
        "maximum_new_tokens": 256,
        "repair_invalid_output": False,
        "require_eos_termination": True,
        "batch_size": 1,
    }:
        raise ValueError("decode configuration differs")
    if config.get("model_difference") != {
        "only_allowed_difference": "adapter_state",
        "general": "off",
        "adapted": "project05_obs_compiler:on",
        "same_loaded_base_process_required": True,
    }:
        raise ValueError("model-difference contract differs")
    if config.get("output_policy", {}).get("raw_generation") != "server_only":
        raise ValueError("raw generations must remain server-only")
    if config.get("output_policy", {}).get("controller_eligible") is not False:
        raise ValueError("paired atomic output cannot be controller-eligible")


def validate_implementation_bundle(
    contract_path: Path,
    config_path: Path,
    authority_path: Path,
) -> dict[str, Any]:
    contract_path = require_within(contract_path, REPO_ROOT, "paired contract")
    config_path = require_within(config_path, REPO_ROOT, "paired config")
    authority_path = require_within(
        authority_path, REPO_ROOT, "paired implementation authority"
    )
    contract = load_json(contract_path)
    config = load_json(config_path)
    authority = load_json(authority_path)
    if contract_path != (REPO_ROOT / contract["contract_repository_path"]).resolve():
        raise ValueError("paired contract path differs")
    if config_path != (REPO_ROOT / contract["paired_config"]["path"]).resolve():
        raise ValueError("paired config path differs")
    if authority_path != (
        REPO_ROOT / contract["implementation_authority"]["path"]
    ).resolve():
        raise ValueError("paired implementation authority path differs")
    if sha256_file(config_path) != contract["paired_config"]["sha256"]:
        raise ValueError("paired config SHA-256 mismatch")
    if sha256_file(contract_path) != authority["paired_gate"]["contract_sha256"]:
        raise ValueError("paired contract/authority SHA-256 mismatch")
    if sha256_file(config_path) != authority["paired_gate"]["config_sha256"]:
        raise ValueError("paired config/authority SHA-256 mismatch")
    for label in (
        "parent_authority",
        "approved_amendment",
        "paired_fairness_contract",
        "checkpoint_selection_audit",
        "serialization_contract",
        "training_validation_payload_lock",
        "model_preparation_audit",
    ):
        verify_hash_record(contract[label], label)
    for label, record in contract["implementation"].items():
        verify_hash_record(record, label)
    selected = contract["selected_adapter"]
    selection = load_json(
        REPO_ROOT / contract["checkpoint_selection_audit"]["path"]
    )["selected"]
    if (
        selected["epoch"] != selection["epoch"]
        or selected["optimizer_step"] != selection["optimizer_step"]
        or selected["adapter_sha256"] != selection["adapter_sha256"]
    ):
        raise ValueError("selected adapter differs from checkpoint selection")
    validate_config(config)
    if authority["paired_gate"]["implementation_authorized"] is not True:
        raise PermissionError("paired implementation authority is closed")
    if authority["paired_gate"]["model_execution_authorized"] is not False:
        raise ValueError("v0.41 must not authorize model execution")
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
        execution_authority_path, REPO_ROOT, "paired execution authority"
    )
    authority = load_json(path)
    gate = authority.get("paired_execution_gate", {})
    if gate.get("authorized") is not True or gate.get("maximum_executions") != 1:
        raise PermissionError("one explicit paired execution is required")
    if gate.get("contract_sha256") != sha256_file(verified["contract_path"]):
        raise ValueError("execution authority contract SHA-256 mismatch")
    if gate.get("config_sha256") != sha256_file(verified["config_path"]):
        raise ValueError("execution authority config SHA-256 mismatch")
    if gate.get("split") != "training-validation" or gate.get("examples") != 16:
        raise PermissionError("execution authority exceeds the atomic panel")
    if any(
        gate.get(field) is not False
        for field in (
            "development_or_test_access_authorized",
            "c07_c12_execution_authorized",
            "m3_integration_authorized",
            "automatic_retry_authorized",
        )
    ):
        raise PermissionError("downstream or retry scope is open")
    parent = authority.get("parent_authority", {})
    if parent.get("path") != verified["contract"]["implementation_authority"]["path"]:
        raise ValueError("execution authority parent differs")
    verify_hash_record(parent, "execution authority parent")
    return authority


def load_pair_file(path: Path, expected_sha256: str) -> list[dict[str, Any]]:
    if sha256_file(path) != expected_sha256:
        raise ValueError("training-validation payload SHA-256 mismatch")
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid pair JSONL at line {line_number}"
                ) from error
    return rows


def validate_source_examples(
    examples: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    panel = config["panel"]
    if len(examples) != panel["source_examples"]:
        raise ValueError("training-validation example count differs")
    if any(row.get("split_role") != panel["split"] for row in examples):
        raise ValueError("non-training-validation example entered the panel")
    families = Counter(row.get("source_family_id") for row in examples)
    if dict(sorted(families.items())) != panel["families"]:
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
                    f"{panel['selection_seed']}|panel|{row['example_id']}"
                )
            )
            selected.extend(group[: panel["examples_per_family_decision"]])
    if len(selected) != panel["exact_examples"]:
        raise ValueError("paired atomic panel size differs")
    if len({row["example_id"] for row in selected}) != len(selected):
        raise ValueError("paired atomic panel contains duplicate examples")
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
                f"{seed}|order|{key[0]}|{key[1]}|{row['example_id']}"
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
        raise ValueError("condition order is not globally balanced")
    return orders


def render_prompt(example: dict[str, Any], serialization: dict[str, Any]) -> str:
    prompt, _ = SMOKE.render_training_parts(example, serialization)
    forbidden = serialization["forbidden_message_fields"]
    user_messages = SMOKE.build_messages(
        example, serialization, include_assistant=False
    )
    serialized_user = user_messages[-1]["content"]
    for field in forbidden:
        if f'"{field}"' in serialized_user:
            raise ValueError(f"forbidden field entered paired prompt: {field}")
    return prompt


def expected_shared_manifest_keys() -> tuple[str, ...]:
    return (
        "base_snapshot_sha256",
        "tokenizer_snapshot_sha256",
        "runtime_lock_sha256",
        "quantization_config_sha256",
        "serialization_contract_sha256",
        "atomic_admission_sha256",
        "scorer_sha256",
        "max_context_tokens",
        "decode_config_sha256",
        "hardware_id",
    )


class PairedBackend(Protocol):
    def shared_manifest(self) -> dict[str, Any]:
        ...

    def generate(
        self,
        condition: str,
        prompt: str,
        example: dict[str, Any],
    ) -> dict[str, Any]:
        ...


def public_input_sha256(example: dict[str, Any]) -> str:
    """Hash only fields visible to the model, never labels or private scoring data."""
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
    if not isinstance(generated.get("raw_output"), str):
        raise ValueError("backend raw output is missing")
    if generated.get("raw_output_sha256") != sha256_text(
        generated["raw_output"]
    ):
        raise ValueError("backend raw-output SHA-256 mismatch")


def run_panel(
    panel: list[dict[str, Any]],
    config: dict[str, Any],
    serialization: dict[str, Any],
    backend: PairedBackend,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(panel) != config["panel"]["exact_examples"]:
        raise ValueError("run panel size differs")
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
        public_input_hash = public_input_sha256(example)
        for position, condition in enumerate(orders[example["example_id"]]):
            generated = backend.generate(condition, prompt, example)
            validate_generation(generated, condition, shared)
            rows.append(
                {
                    "schema_version": "project05-paired-raw-row-v0.1",
                    "condition": condition,
                    "condition_position": position,
                    "adapter_state": generated["adapter_state"],
                    "same_loaded_base_process": True,
                    "example_id_sha256": example_hash,
                    "source_family_id": example["source_family_id"],
                    "source_modality": example["source_modality"],
                    "public_input_sha256": public_input_hash,
                    "prompt_sha256": prompt_hash,
                    "decode_config_sha256": shared["decode_config_sha256"],
                    "base_snapshot_sha256": shared["base_snapshot_sha256"],
                    "tokenizer_snapshot_sha256": shared[
                        "tokenizer_snapshot_sha256"
                    ],
                    "runtime_lock_sha256": shared["runtime_lock_sha256"],
                    "quantization_config_sha256": shared[
                        "quantization_config_sha256"
                    ],
                    "hardware_id": shared["hardware_id"],
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
        raise ValueError("paired condition counts differ")
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


class PeftPairedBackend:
    """Single-process Qwen/PEFT backend, loaded only after execution authority."""

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        torch: Any,
        adapter_name: str,
        shared: dict[str, Any],
        config: dict[str, Any],
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.torch = torch
        self.adapter_name = adapter_name
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
    ) -> "PeftPairedBackend":
        stack = SELECTOR.CORE._load_training_stack()
        torch = stack["torch"]
        from peft import PeftModel

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
        snapshot_identity = sha256_text(
            canonical_json(preparation["model_snapshot"]["files"])
        )
        tokenizer_files = [
            row
            for row in preparation["model_snapshot"]["files"]
            if row["path"]
            in {"merges.txt", "tokenizer.json", "tokenizer_config.json", "vocab.json"}
        ]
        shared = {
            "base_snapshot_sha256": snapshot_identity,
            "tokenizer_snapshot_sha256": sha256_text(
                canonical_json(tokenizer_files)
            ),
            "runtime_lock_sha256": sha256_text(
                canonical_json(preparation["runtime"])
            ),
            "quantization_config_sha256": sha256_text(
                canonical_json(config["quantization"])
            ),
            "serialization_contract_sha256": contract[
                "serialization_contract"
            ]["sha256"],
            "atomic_admission_sha256": contract["implementation"][
                "frozen_strict_parser"
            ]["sha256"],
            "scorer_sha256": contract["implementation"]["paired_scorer"][
                "sha256"
            ],
            "max_context_tokens": config["sequence_length"],
            "decode_config_sha256": sha256_text(
                canonical_json(config["decode"])
            ),
            "hardware_id": preparation["runtime"]["gpu_name"],
        }
        return cls(model, tokenizer, torch, adapter_name, shared, config)

    def shared_manifest(self) -> dict[str, Any]:
        return dict(self._shared)

    def generate(
        self,
        condition: str,
        prompt: str,
        example: dict[str, Any],
    ) -> dict[str, Any]:
        if os.getpid() != self.process_id:
            raise RuntimeError("paired backend process identity changed")
        self.model.set_adapter(self.adapter_name)
        manager = (
            self.model.disable_adapter()
            if condition == GENERAL
            else contextlib.nullcontext()
        )
        with manager:
            generated = SELECTOR.decode_once(
                self.model,
                self.tokenizer,
                self.torch,
                prompt,
                {
                    "decode": {
                        "maximum_new_tokens": self.config["decode"][
                            "maximum_new_tokens"
                        ]
                    }
                },
            )
        return {
            **self._shared,
            "adapter_state": (
                "off"
                if condition == GENERAL
                else "project05_obs_compiler:on"
            ),
            "same_loaded_base_process": True,
            "raw_output": generated["text"],
            "raw_output_sha256": generated["raw_output_sha256"],
            "eos_terminated": generated["eos_terminated"],
            "input_tokens": len(
                self.tokenizer.encode(prompt, add_special_tokens=False)
            ),
            "generated_tokens": generated["generated_tokens"],
            "latency_seconds": generated["latency_seconds"],
            "peak_allocated_bytes": int(
                self.torch.cuda.max_memory_allocated(0)
            ),
        }


def run_authorized_execution(
    verified: dict[str, Any],
    execution_authority: dict[str, Any],
    pair_root: Path,
    run_root: Path,
    preparation_audit: Path,
) -> dict[str, Any]:
    if os.name != "posix":
        raise RuntimeError("authorized paired model execution is Linux-only")
    contract, config = verified["contract"], verified["config"]
    allowed_root = Path(contract["server_execution_boundary"]["allowed_root"]).resolve()
    run_root = Path(run_root).resolve()
    if run_root != allowed_root:
        raise ValueError("paired run root differs from the sole allowed server root")
    pair_root = require_within(pair_root, run_root, "paired payload root")
    preparation_audit = require_within(
        preparation_audit, run_root, "model preparation audit"
    )
    preparation = load_json(preparation_audit)
    if sha256_file(preparation_audit) != contract["model_preparation_audit"][
        "sha256"
    ]:
        raise ValueError("model preparation audit SHA-256 mismatch")
    pair_file = pair_root / contract["pair_payload"]["file"]
    examples = load_pair_file(pair_file, contract["pair_payload"]["sha256"])
    panel = select_atomic_panel(examples, config)
    serialization = load_json(
        REPO_ROOT / contract["serialization_contract"]["path"]
    )["serialization"]
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
        "paired output",
    )
    if output_root.exists():
        raise FileExistsError("refusing paired execution overwrite or resume")
    output_root.mkdir(parents=True, exist_ok=False)
    raw_path = output_root / RAW_ROWS_NAME
    try:
        backend = PeftPairedBackend.load(
            snapshot_dir,
            adapter_dir,
            preparation,
            contract,
            config,
        )
        rows, summary = run_panel(panel, config, serialization, backend)
        for row in rows:
            append_jsonl(raw_path, row)
        backend.torch.cuda.synchronize(0)
        pre_normalization_free, total = backend.torch.cuda.mem_get_info(0)
        cache_release_attempted = False
        if (
            config["hardware"]["cache_normalized_free_memory_gate"]
            and int(pre_normalization_free)
            < config["hardware"]["minimum_synchronized_free_bytes"]
        ):
            cache_release_attempted = True
            backend.torch.cuda.empty_cache()
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
            raise ValueError("paired execution peak-memory Gate failed")
        if int(free) < config["hardware"]["minimum_synchronized_free_bytes"]:
            raise ValueError("paired execution free-memory Gate failed")
        if (
            summary["wall_seconds"]
            > config["resource_limits"]["maximum_wall_hours"] * 3600
        ):
            raise ValueError("paired execution wall-time Gate failed")
        if (
            resources
            > config["resource_limits"][
                "maximum_runtime_cache_checkpoint_output_bytes"
            ]
        ):
            raise ValueError("paired execution resource-size Gate failed")
        audit = {
            "schema_version": "project05-paired-generation-audit-v0.1",
            "status": "paired_generation_complete_scoring_pending",
            "contract_sha256": sha256_file(verified["contract_path"]),
            "config_sha256": sha256_file(verified["config_path"]),
            "execution_authority_sha256": sha256_file(
                REPO_ROOT
                / execution_authority["authority_repository_path"]
            ),
            "selected_epoch": contract["selected_adapter"]["epoch"],
            "selected_adapter_sha256": contract["selected_adapter"][
                "adapter_sha256"
            ],
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
                "maximum_peak_allocated_bytes": config["hardware"][
                    "maximum_peak_allocated_bytes"
                ],
                "pre_cache_normalization_free_bytes": int(
                    pre_normalization_free
                ),
                "cache_release_attempted": cache_release_attempted,
                "final_free_bytes": int(free),
                "minimum_synchronized_free_bytes": config["hardware"][
                    "minimum_synchronized_free_bytes"
                ],
                "total_vram_bytes": int(total),
                "runtime_cache_checkpoint_output_bytes": resources,
                "maximum_runtime_cache_checkpoint_output_bytes": config[
                    "resource_limits"
                ]["maximum_runtime_cache_checkpoint_output_bytes"],
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
            "next_gate": "server_side_scoring_then_hard_stop",
        }
        write_json_no_overwrite(output_root / GENERATION_AUDIT_NAME, audit)
        return audit
    except BaseException as error:
        failure = {
            "schema_version": "project05-paired-generation-failure-v0.1",
            "status": "failed_paired_generation_no_automatic_retry",
            "failure_type": type(error).__name__,
            "failure_message": str(error)[:500],
            "automatic_retry_authorized": False,
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
        print("paired implementation bundle valid; model execution remains closed")
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
    execution = validate_execution_authority(
        args.execution_authority,
        verified,
    )
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
