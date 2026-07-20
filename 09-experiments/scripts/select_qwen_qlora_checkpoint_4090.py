"""Select one Project05 QLoRA checkpoint on frozen training-validation only."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_RUNNER_PATH = Path(__file__).with_name("execute_qwen_qlora_4090_adamw_primary.py")
AUDIT_NAME = "checkpoint-selection-audit-v0.1.json"
ROWS_NAME = "checkpoint-selection-metrics-v0.1.jsonl"
RAW_NAME = "checkpoint-selection-raw-generations-v0.1.jsonl"
PROGRESS_NAME = "checkpoint-selection-progress-v0.1.jsonl"
FAILURE_NAME = "checkpoint-selection-failure-v0.1.json"
DECISIONS = ("supported", "unsupported_by_bound_pointer")
EDGE_KEYS = {"subject_type", "subject_value", "predicate", "object_type", "object_value", "source_pointer"}
POINTER_KEYS = {"artifact_id", "record_id", "record_sha256"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"{name} has no loader")
    spec.loader.exec_module(module)
    return module


PRIMARY_RUNNER = _load(PRIMARY_RUNNER_PATH, "project05_selection_primary_runner")
DIAG = PRIMARY_RUNNER.DIAG
CORE = PRIMARY_RUNNER.CORE


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(CORE.canonical_json(value) + "\n")
        handle.flush()


def strict_prediction(text: str, eos_terminated: bool) -> tuple[dict[str, Any] | None, str | None]:
    if not eos_terminated:
        return None, "missing_eos_or_max_tokens"
    try:
        value = json.loads(text.strip())
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(value, dict) or set(value) != {"support_decision", "normalized_edge", "pointer"}:
        return None, "invalid_top_level_schema"
    decision = value["support_decision"]
    pointer = value["pointer"]
    edge = value["normalized_edge"]
    if decision not in DECISIONS:
        return None, "invalid_support_decision"
    if not isinstance(pointer, dict) or set(pointer) != POINTER_KEYS or not all(isinstance(pointer[key], str) for key in POINTER_KEYS):
        return None, "invalid_pointer_schema"
    if decision == "unsupported_by_bound_pointer":
        if edge is not None:
            return None, "unsupported_edge_must_be_null"
    else:
        if not isinstance(edge, dict) or set(edge) != EDGE_KEYS:
            return None, "invalid_edge_schema"
        if not all(isinstance(edge[key], str) for key in EDGE_KEYS - {"source_pointer"}):
            return None, "invalid_edge_value_type"
        source_pointer = edge["source_pointer"]
        if not isinstance(source_pointer, dict) or set(source_pointer) != POINTER_KEYS:
            return None, "invalid_edge_source_pointer"
        if not all(isinstance(source_pointer[key], str) for key in POINTER_KEYS):
            return None, "invalid_edge_source_pointer_type"
    return value, None


def class_f1(gold: list[str], predicted: list[str], label: str) -> float:
    tp = sum(g == label and p == label for g, p in zip(gold, predicted))
    fp = sum(g != label and p == label for g, p in zip(gold, predicted))
    fn = sum(g == label and p != label for g, p in zip(gold, predicted))
    denominator = 2 * tp + fp + fn
    return 0.0 if denominator == 0 else 2 * tp / denominator


def score_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("selection rows are empty")
    family_reports = {}
    for family in sorted({row["source_family_id"] for row in rows}):
        subset = [row for row in rows if row["source_family_id"] == family]
        gold = [row["gold_decision"] for row in subset]
        predicted = [row["predicted_decision"] for row in subset]
        per_class = {label: class_f1(gold, predicted, label) for label in DECISIONS}
        family_reports[family] = {
            "examples": len(subset),
            "support_decision_f1": per_class,
            "macro_support_decision_f1": sum(per_class.values()) / len(per_class),
            "gold": dict(sorted(Counter(gold).items())),
            "predicted": dict(sorted(Counter(predicted).items())),
        }
    def rate(field: str) -> float:
        return sum(bool(row[field]) for row in rows) / len(rows)
    target_tokens = sum(int(row["assistant_target_tokens"]) for row in rows)
    if target_tokens <= 0:
        raise ValueError("assistant target token count is empty")
    return {
        "examples": len(rows),
        "families": family_reports,
        "family_macro_support_decision_f1": sum(row["macro_support_decision_f1"] for row in family_reports.values()) / len(family_reports),
        "canonical_json_exact_match_rate": rate("canonical_json_exact"),
        "normalized_edge_exact_match_rate": rate("normalized_edge_exact"),
        "pointer_exact_match_rate": rate("pointer_exact"),
        "json_valid_rate": rate("json_valid"),
        "schema_valid_rate": rate("schema_valid"),
        "eos_termination_rate": rate("eos_terminated"),
        "assistant_token_nll": sum(
            float(row["assistant_token_nll"]) * int(row["assistant_target_tokens"])
            for row in rows
        ) / target_tokens,
        "assistant_target_tokens": target_tokens,
    }


def selection_key(report: dict[str, Any]) -> tuple[float, float, float, float, float, int]:
    metrics = report["metrics"]
    return (
        metrics["family_macro_support_decision_f1"],
        metrics["canonical_json_exact_match_rate"],
        metrics["normalized_edge_exact_match_rate"],
        metrics["pointer_exact_match_rate"],
        -metrics["assistant_token_nll"],
        -report["epoch"],
    )


def choose_checkpoint(reports: list[dict[str, Any]]) -> dict[str, Any]:
    if [row["epoch"] for row in reports] != [1, 2, 3]:
        raise ValueError("selection requires epoch 1, 2, and 3 in order")
    return max(reports, key=selection_key)


def validate_config(config: dict[str, Any]) -> None:
    if config["data"]["split"] != "training-validation" or config["data"]["examples"] != 300:
        raise ValueError("selection data boundary differs from the frozen protocol")
    if config["data"]["families"] != {"logpai_loghub_linux": 150, "zeek_non_pcap_test_logs": 150}:
        raise ValueError("selection family quotas differ")
    if config["data"]["decisions_per_family"] != {"supported": 75, "unsupported_by_bound_pointer": 75}:
        raise ValueError("selection decision quotas differ")
    decode = config["decode"]
    if decode != {"do_sample": False, "maximum_new_tokens": 256, "repair_invalid_output": False, "batch_size": 1, "require_eos_termination": True}:
        raise ValueError("decode configuration differs from the frozen protocol")
    if [row["epoch"] for row in config["checkpoints"]] != [1, 2, 3]:
        raise ValueError("checkpoint list differs")
    if config["selection"]["primary_metric"] != "family_macro_support_decision_f1":
        raise ValueError("primary metric differs")
    if config["selection"]["tie_breakers"] != ["canonical_json_exact_match_rate", "normalized_edge_exact_match_rate", "pointer_exact_match_rate", "assistant_token_nll", "earlier_epoch"]:
        raise ValueError("tie-breakers differ")
    if config["reproducibility"]["total_examples_per_checkpoint"] != 16:
        raise ValueError("reproducibility panel differs")


def verify_checkpoint_inventory(
    checkpoint_root: Path,
    formal_result: dict[str, Any],
    config: dict[str, Any],
) -> dict[int, Path]:
    """Verify every file in all three server-only checkpoints before loading PEFT."""
    if formal_result.get("status") != "passed_single_4090_adamw_primary_adapter_training":
        raise ValueError("passed formal training result is required")
    expected_reports = formal_result.get("checkpoints")
    if not isinstance(expected_reports, list) or [row.get("epoch") for row in expected_reports] != [1, 2, 3]:
        raise ValueError("formal checkpoint inventory differs")
    config_by_epoch = {row["epoch"]: row for row in config["checkpoints"]}
    adapter_dirs: dict[int, Path] = {}
    for report in expected_reports:
        epoch = report["epoch"]
        configured = config_by_epoch.get(epoch)
        if configured is None or configured["optimizer_step"] != report.get("optimizer_step"):
            raise ValueError(f"epoch {epoch} optimizer-step inventory mismatch")
        if report.get("adapter_only") is not True or report.get("merged_model_saved") is not False:
            raise ValueError(f"epoch {epoch} is not an adapter-only checkpoint")
        root_name = f"checkpoint-epoch-{epoch:03d}"
        if report.get("root") != root_name:
            raise ValueError(f"epoch {epoch} checkpoint root mismatch")
        epoch_root = CORE.require_within(checkpoint_root / root_name, checkpoint_root, f"epoch {epoch} checkpoint")
        expected_files = report.get("files")
        if not isinstance(expected_files, list) or len(expected_files) != 7:
            raise ValueError(f"epoch {epoch} checkpoint file manifest differs")
        expected_paths = sorted(row.get("path") for row in expected_files)
        actual_paths = sorted(
            path.relative_to(epoch_root).as_posix()
            for path in epoch_root.rglob("*")
            if path.is_file()
        )
        if actual_paths != expected_paths:
            raise ValueError(f"epoch {epoch} checkpoint file inventory mismatch")
        for record in expected_files:
            file_path = CORE.require_within(epoch_root / record["path"], epoch_root, f"epoch {epoch} checkpoint file")
            if not file_path.is_file() or file_path.stat().st_size != record["bytes"]:
                raise ValueError(f"epoch {epoch} checkpoint byte-size mismatch: {record['path']}")
            if CORE.sha256_file(file_path) != record["sha256"]:
                raise ValueError(f"epoch {epoch} checkpoint SHA-256 mismatch: {record['path']}")
        adapter_record = next(row for row in expected_files if row["path"] == "adapter/adapter_model.safetensors")
        if adapter_record["sha256"] != configured["adapter_sha256"]:
            raise ValueError(f"epoch {epoch} configured adapter SHA-256 mismatch")
        adapter_dirs[epoch] = epoch_root / "adapter"
    return adapter_dirs


def verify_authority(contract_path: Path, config_path: Path, authority_path: Path, run_root: Path) -> dict[str, Any]:
    contract_path = CORE.require_within(contract_path, REPO_ROOT, "selection contract")
    config_path = CORE.require_within(config_path, REPO_ROOT, "selection config")
    authority_path = CORE.require_within(authority_path, REPO_ROOT, "selection authority")
    contract = DIAG.load_contract_chain(contract_path)
    config = CORE.load_json(config_path)
    authority = CORE.load_json(authority_path)
    boundary = CORE.validate_server_boundary(contract, run_root, repo_root=REPO_ROOT)
    if contract_path != (REPO_ROOT / contract["contract_repository_path"]).resolve():
        raise ValueError("selection contract path mismatch")
    if authority_path != (REPO_ROOT / contract["authority_repository_path"]).resolve():
        raise ValueError("selection authority path mismatch")
    if CORE.sha256_file(config_path) != contract["selection_config"]["sha256"]:
        raise ValueError("selection config hash mismatch")
    gate = authority["checkpoint_selection_gate"]
    if gate["contract_sha256"] != CORE.sha256_file(contract_path) or gate["selection_config_sha256"] != CORE.sha256_file(config_path):
        raise ValueError("selection authority hash mismatch")
    if not gate["authorized"] or gate["maximum_executions"] != 1:
        raise PermissionError("exactly one checkpoint selection execution is required")
    if gate["development_or_test_access_authorized"] or gate["paired_evaluation_authorized"] or gate["m3_integration_authorized"]:
        raise PermissionError("downstream scopes must remain closed")
    CORE._verify_hash_record(authority["parent_authority"], "selection parent authority")
    CORE._verify_hash_record(contract["approved_amendment"], "selection amendment")
    CORE._verify_hash_record(contract["formal_training_completion_authority"], "formal training completion authority")
    formal_result_path = CORE._verify_hash_record(contract["formal_training_result"], "formal training result")
    CORE._verify_hash_record(contract["selection_config"], "selection config")
    for label, record in contract["frozen_inputs"].items():
        CORE._verify_hash_record(record, label)
    for label in ("checkpoint_selector", "checkpoint_selection_launcher"):
        CORE._verify_hash_record(contract["implementation"][label], label)
    validate_config(config)
    completion = CORE.load_json(REPO_ROOT / contract["formal_training_completion_authority"]["path"])
    if completion.get("formal_result", {}).get("sha256") != contract["formal_training_result"]["sha256"]:
        raise ValueError("formal completion authority/result chain mismatch")
    if completion.get("completion_gate", {}).get("formal_result_eligible") is not True:
        raise ValueError("formal training result is not eligible")
    formal_result = CORE.load_json(formal_result_path)
    return {"contract": contract, "config": config, "authority": authority, "formal_result": formal_result, **boundary}


def load_validation(verified: dict[str, Any], pair_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pair_root = CORE.require_within(pair_root, verified["run_root"], "selection pair root")
    expected_root = (REPO_ROOT / "09-experiments/llm_evidence_compiler_mainline/candidate_pairs_v0.2/local-data").resolve()
    if pair_root != expected_root:
        raise ValueError("selection pair root differs")
    record = verified["contract"]["pair_payloads"]["training_validation"]
    examples = CORE.PRIMARY.load_pair_file(pair_root / record["file"], record["sha256"])
    families = Counter(row.get("source_family_id") for row in examples)
    decisions = {family: Counter(row.get("support_decision") for row in examples if row.get("source_family_id") == family) for family in families}
    if len(examples) != 300 or dict(sorted(families.items())) != verified["config"]["data"]["families"]:
        raise ValueError("selection validation dataset differs")
    for family, counts in decisions.items():
        if dict(sorted(counts.items())) != verified["config"]["data"]["decisions_per_family"]:
            raise ValueError(f"selection class quota differs for {family}")
    if any(row.get("split_role") != "training-validation" for row in examples):
        raise ValueError("non-training-validation row entered selection")
    return examples, {"examples": len(examples), "families": dict(sorted(families.items())), "decisions_per_family": {key: dict(sorted(value.items())) for key, value in sorted(decisions.items())}}


def balanced_repro_panel(examples: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    chosen = []
    count = config["reproducibility"]["examples_per_family_decision"]
    seed = config["reproducibility"]["seed"]
    for family in sorted(config["data"]["families"]):
        for decision in DECISIONS:
            group = [row for row in examples if row["source_family_id"] == family and row["support_decision"] == decision]
            group.sort(key=lambda row: CORE.sha256_text(f"{seed}|repro|{row['example_id']}"))
            chosen.extend(group[:count])
    if len(chosen) != config["reproducibility"]["total_examples_per_checkpoint"]:
        raise ValueError("reproducibility panel count differs")
    return chosen


def build_prompt_and_target(example: dict[str, Any], serialization: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    prompt, target_with_end = CORE.PRIMARY.SMOKE.render_training_parts(example, serialization)
    suffix = "<|im_end|>\n"
    if not target_with_end.endswith(suffix):
        raise ValueError("assistant target suffix differs")
    gold = {field: example[field] for field in serialization["assistant_fields"]}
    return prompt, target_with_end, gold


def decode_once(model: Any, tokenizer: Any, torch: Any, prompt: str, config: dict[str, Any]) -> dict[str, Any]:
    encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
    input_ids = encoded["input_ids"].to("cuda")
    attention_mask = encoded["attention_mask"].to("cuda")
    started = time.monotonic()
    with torch.inference_mode():
        output = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=False,
            max_new_tokens=config["decode"]["maximum_new_tokens"],
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )
    torch.cuda.synchronize(0)
    generated = output[0, input_ids.shape[1]:].tolist()
    eos_ids = tokenizer.eos_token_id if isinstance(tokenizer.eos_token_id, list) else [tokenizer.eos_token_id]
    eos_position = next((index for index, token in enumerate(generated) if token in eos_ids), None)
    eos_terminated = eos_position is not None and len(generated) <= config["decode"]["maximum_new_tokens"]
    content_ids = generated[:eos_position] if eos_position is not None else generated
    text = tokenizer.decode(content_ids, skip_special_tokens=False)
    raw_hash = CORE.sha256_text(text)
    return {"text": text, "raw_output_sha256": raw_hash, "generated_tokens": len(generated), "eos_terminated": eos_terminated, "latency_seconds": time.monotonic() - started}


def target_nll(model: Any, tokenizer: Any, torch: Any, example: dict[str, Any], serialization: dict[str, Any], limit: int) -> tuple[float, int]:
    item = CORE.encode_assistant_only(example, serialization, tokenizer, limit)
    assistant_tokens = sum(label != -100 for label in item["labels"])
    if assistant_tokens <= 0:
        raise ValueError("assistant target token count is empty")
    batch = {key: torch.tensor([value], device="cuda", dtype=torch.long) for key, value in item.items()}
    with torch.inference_mode():
        loss = model(**batch).loss
    value = float(loss.detach().cpu())
    if not math.isfinite(value):
        raise ValueError("non-finite assistant-token NLL")
    return value, assistant_tokens


def evaluate_checkpoint(model: Any, tokenizer: Any, torch: Any, examples: list[dict[str, Any]], serialization: dict[str, Any], config: dict[str, Any], epoch: int, adapter_name: str, raw_path: Path, rows_path: Path, progress_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    model.set_adapter(adapter_name)
    model.eval()
    rows = []
    for index, example in enumerate(examples, 1):
        prompt, _, gold = build_prompt_and_target(example, serialization)
        generated = decode_once(model, tokenizer, torch, prompt, config)
        prediction, error = strict_prediction(generated["text"], generated["eos_terminated"])
        schema_valid = prediction is not None
        canonical_exact = schema_valid and CORE.canonical_json(prediction) == CORE.canonical_json(gold)
        edge_exact = schema_valid and prediction["normalized_edge"] == gold["normalized_edge"]
        pointer_exact = schema_valid and prediction["pointer"] == gold["pointer"]
        nll, assistant_tokens = target_nll(model, tokenizer, torch, example, serialization, 1024)
        row = {
            "epoch": epoch,
            "example_id_sha256": CORE.sha256_text(example["example_id"]),
            "source_family_id": example["source_family_id"],
            "gold_decision": example["support_decision"],
            "predicted_decision": prediction["support_decision"] if schema_valid else "invalid",
            "eos_terminated": generated["eos_terminated"],
            "json_valid": error not in {"invalid_json", "missing_eos_or_max_tokens"},
            "schema_valid": schema_valid,
            "failure_reason": error,
            "canonical_json_exact": canonical_exact,
            "normalized_edge_exact": edge_exact,
            "pointer_exact": pointer_exact,
            "assistant_token_nll": nll,
            "assistant_target_tokens": assistant_tokens,
            "generated_tokens": generated["generated_tokens"],
            "raw_output_sha256": generated["raw_output_sha256"],
            "latency_seconds": generated["latency_seconds"],
        }
        rows.append(row)
        append_jsonl(rows_path, row)
        append_jsonl(raw_path, {"epoch": epoch, "example_id_sha256": row["example_id_sha256"], "raw_output": generated["text"], "raw_output_sha256": generated["raw_output_sha256"]})
        if index % 10 == 0 or index == len(examples):
            append_jsonl(progress_path, {"event": "checkpoint_selection_progress", "epoch": epoch, "examples_completed": index, "examples_total": len(examples), "elapsed_seconds": sum(item["latency_seconds"] for item in rows)})
    return score_rows(rows), rows


def run_selection(verified: dict[str, Any], examples: list[dict[str, Any]], dataset_report: dict[str, Any], preparation_audit: Path) -> dict[str, Any]:
    started = time.monotonic()
    config, contract, run_root = verified["config"], verified["contract"], verified["run_root"]
    preparation_audit = CORE.require_within(preparation_audit, run_root, "preparation audit")
    if CORE.sha256_file(preparation_audit) != contract["selection_inputs"]["preparation_audit_sha256"]:
        raise ValueError("preparation audit hash mismatch")
    preparation = CORE.load_json(preparation_audit)
    if preparation.get("status") != "passed_runtime_and_fixed_revision_weight_gate":
        raise ValueError("passed preparation audit is required")
    snapshot_dir = CORE.require_within(Path(preparation["model_snapshot"]["snapshot_dir"]), run_root, "model snapshot")
    output_root = (run_root / config["output_policy"]["run_subdirectory"]).resolve()
    CORE.require_within(output_root, run_root, "selection output")
    if output_root.exists():
        raise FileExistsError("refusing to overwrite or resume checkpoint selection")
    output_root.mkdir(parents=True, exist_ok=False)
    raw_path, rows_path, progress_path = output_root / RAW_NAME, output_root / ROWS_NAME, output_root / PROGRESS_NAME
    state = {"completed_epochs": [], "examples_completed": 0}
    try:
        checkpoint_root = CORE.require_within(
            run_root / contract["checkpoint_source"]["run_subdirectory"],
            run_root,
            "formal checkpoint root",
        )
        adapter_dirs = verify_checkpoint_inventory(
            checkpoint_root, verified["formal_result"], config
        )
        stack = CORE._load_training_stack()
        torch = stack["torch"]
        from peft import PeftModel
        gpu = CORE._runtime_gpu_gate(stack, config)
        tokenizer = stack["AutoTokenizer"].from_pretrained(snapshot_dir, local_files_only=True, trust_remote_code=False)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        compute_dtype = torch.float16
        quantization = stack["BitsAndBytesConfig"](load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=compute_dtype, bnb_4bit_use_double_quant=True)
        torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(0)
        base = stack["AutoModelForCausalLM"].from_pretrained(snapshot_dir, local_files_only=True, trust_remote_code=False, quantization_config=quantization, device_map={"": 0}, torch_dtype=compute_dtype)
        base.config.use_cache = True
        reports = []
        model = None
        for item in config["checkpoints"]:
            epoch = item["epoch"]
            adapter_dir = adapter_dirs[epoch]
            name = f"epoch_{epoch:03d}"
            if model is None:
                model = PeftModel.from_pretrained(base, adapter_dir, adapter_name=name, is_trainable=False)
            else:
                model.load_adapter(adapter_dir, adapter_name=name, is_trainable=False)
        serialization_record = contract["frozen_inputs"]["serialization_contract"]
        serialization = CORE.load_json(REPO_ROOT / serialization_record["path"])["serialization"]
        panel = balanced_repro_panel(examples, config)
        panel_hashes = [CORE.sha256_text(row["example_id"]) for row in panel]
        for item in config["checkpoints"]:
            epoch, name = item["epoch"], f"epoch_{item['epoch']:03d}"
            metrics, rows = evaluate_checkpoint(model, tokenizer, torch, examples, serialization, config, epoch, name, raw_path, rows_path, progress_path)
            state["completed_epochs"].append(epoch); state["examples_completed"] += len(rows)
            first = {row["example_id_sha256"]: row["raw_output_sha256"] for row in rows if row["example_id_sha256"] in panel_hashes}
            repeated = {}
            model.set_adapter(name); model.eval()
            for example in panel:
                prompt, _, _ = build_prompt_and_target(example, serialization)
                again = decode_once(model, tokenizer, torch, prompt, config)
                repeated[CORE.sha256_text(example["example_id"])] = again["raw_output_sha256"]
            reproducible = first == repeated and len(first) == len(panel)
            if not reproducible:
                raise ValueError(f"epoch {epoch} deterministic reproducibility Gate failed")
            reports.append({"epoch": epoch, "optimizer_step": item["optimizer_step"], "adapter_sha256": item["adapter_sha256"], "metrics": metrics, "reproducibility": {"panel_examples": len(panel), "exact_raw_output_sha256_match": True}})
        selected = choose_checkpoint(reports)
        torch.cuda.synchronize(0)
        pre_normalization_free, total = torch.cuda.mem_get_info(0)
        final_cache_release_attempted = False
        if (
            config["hardware"].get("cache_normalized_free_memory_gate", False)
            and int(pre_normalization_free) < config["hardware"]["minimum_synchronized_free_bytes"]
        ):
            final_cache_release_attempted = True
            torch.cuda.empty_cache()
            torch.cuda.synchronize(0)
        free, total = torch.cuda.mem_get_info(0)
        peak = int(torch.cuda.max_memory_allocated(0))
        resources = CORE.PRIMARY.unique_physical_bytes([run_root / "local-runtime", run_root / "local-cache", run_root / "server-output"])
        wall = time.monotonic() - started
        if peak > config["hardware"]["maximum_peak_allocated_bytes"] or int(free) < config["hardware"]["minimum_synchronized_free_bytes"]:
            raise ValueError("checkpoint selection memory Gate failed")
        if resources > config["resource_limits"]["maximum_runtime_cache_checkpoint_output_bytes"] or wall > config["resource_limits"]["maximum_wall_hours"] * 3600:
            raise ValueError("checkpoint selection resource Gate failed")
        append_jsonl(progress_path, {"event": "checkpoint_selection_completed", "selected_epoch": selected["epoch"], "elapsed_seconds": wall})
        result = {
            "schema_version": "project05-qwen25-checkpoint-selection-v0.1",
            "status": "passed_training_validation_checkpoint_selection",
            "created_date": verified["authority"]["created_date"],
            "contract_sha256": CORE.sha256_file(REPO_ROOT / contract["contract_repository_path"]),
            "selection_config_sha256": CORE.sha256_file(REPO_ROOT / contract["selection_config"]["path"]),
            "authority_sha256": CORE.sha256_file(REPO_ROOT / contract["authority_repository_path"]),
            "formal_training_result_sha256": contract["formal_training_result"]["sha256"],
            "dataset": dataset_report,
            "gpu": gpu,
            "checkpoints": reports,
            "selected": {"epoch": selected["epoch"], "optimizer_step": selected["optimizer_step"], "adapter_sha256": selected["adapter_sha256"], "selection_key": list(selection_key(selected))},
            "artifacts": {"metrics_rows": {"file": ROWS_NAME, "sha256": CORE.sha256_file(rows_path), "rows": 900}, "raw_generations": {"file": RAW_NAME, "sha256": CORE.sha256_file(raw_path), "rows": 900, "server_only": True}, "progress": {"file": PROGRESS_NAME, "sha256": CORE.sha256_file(progress_path)}},
            "memory": {"peak_allocated_bytes": peak, "maximum_peak_allocated_bytes": config["hardware"]["maximum_peak_allocated_bytes"], "pre_cache_normalization_free_bytes": int(pre_normalization_free), "final_cache_release_attempted": final_cache_release_attempted, "final_free_bytes": int(free), "minimum_synchronized_free_bytes": config["hardware"]["minimum_synchronized_free_bytes"], "total_bytes": int(total), "passed": True},
            "resources": {"runtime_cache_checkpoint_output_bytes": resources, "maximum_bytes": config["resource_limits"]["maximum_runtime_cache_checkpoint_output_bytes"], "wall_seconds": wall, "maximum_wall_hours": config["resource_limits"]["maximum_wall_hours"]},
            "privacy_and_scope": {"raw_generation_in_committed_audit": False, "train_split_accessed": False, "development_or_test_accessed": False, "c07_c12_accessed": False, "paired_general_vs_adapted_run": False, "m3_integrated": False, "checkpoint_downloaded": False, "hub_upload_used": False},
            "next_gate": {"status": "hard_stop_for_general_vs_adapted_paired_evaluation_authorization", "paired_evaluation_authorized": False, "development_or_test_authorized": False, "m3_integration_authorized": False, "paper_positive_claim_authorized": False},
        }
        CORE.write_json_no_overwrite(output_root / AUDIT_NAME, result)
        return result
    except BaseException as error:
        failure = {"schema_version": "project05-qwen25-checkpoint-selection-failure-v0.1", "status": "failed_or_interrupted_checkpoint_selection", "created_date": verified["authority"]["created_date"], "failure_type": type(error).__name__, "failure_message": str(error)[:500], **state, "automatic_retry_authorized": False, "development_or_test_accessed": False, "m3_integrated": False}
        if not (output_root / FAILURE_NAME).exists():
            CORE.write_json_no_overwrite(output_root / FAILURE_NAME, failure)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("contract", "config", "authority", "pair-root", "run-root", "preparation-audit"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    verified = verify_authority(args.contract, args.config, args.authority, args.run_root)
    examples, dataset_report = load_validation(verified, args.pair_root)
    result = run_selection(verified, examples, dataset_report, args.preparation_audit)
    print(result["status"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
