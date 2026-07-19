"""Lock and audit the bounded Qwen2.5 tokenizer-length Gate.

This script never loads a model and never truncates, pads, drops or rewrites an
example. Tokenizer artifacts and the isolated engine live in Git-ignored local
directories; only counts and hashes are emitted.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_json(path: Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def require_file_hash(path: Path, expected: str, label: str) -> None:
    if not Path(path).is_file():
        raise ValueError(f"{label} is missing")
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} SHA-256 mismatch")


def validate_contract_inputs(contract: dict[str, Any]) -> None:
    inputs = contract["inputs"]
    for prefix in (
        "pair_data_gate_audit",
        "pair_determinism_audit",
        "qwen_fairness_contract",
    ):
        require_file_hash(
            REPO_ROOT / inputs[f"{prefix}_path"],
            inputs[f"{prefix}_sha256"],
            prefix,
        )
    fairness = load_json(REPO_ROOT / inputs["qwen_fairness_contract_path"])
    shared = fairness["shared_model_identity"]
    tokenizer = contract["tokenizer"]
    if shared["model_id"] != tokenizer["repository_id"]:
        raise ValueError("tokenizer repository differs from fairness contract")
    if shared["revision"] != tokenizer["revision"]:
        raise ValueError("tokenizer revision differs from fairness contract")


def build_tokenizer_lock(
    contract: dict[str, Any],
    contract_path: Path,
    snapshot_dir: Path,
    wheel_path: Path,
) -> dict[str, Any]:
    validate_contract_inputs(contract)
    snapshot_dir = Path(snapshot_dir)
    wheel_path = Path(wheel_path)
    if not snapshot_dir.is_dir():
        raise ValueError("tokenizer snapshot directory is missing")
    allowed = sorted(contract["tokenizer"]["allowlisted_files"])
    observed = sorted(path.name for path in snapshot_dir.iterdir() if path.is_file())
    if observed != allowed:
        raise ValueError("tokenizer snapshot files differ from the allowlist")
    if not wheel_path.is_file():
        raise ValueError("isolated tokenizers wheel is missing")
    files = []
    total_bytes = 0
    for name in allowed:
        path = snapshot_dir / name
        size = path.stat().st_size
        total_bytes += size
        files.append({"name": name, "bytes": size, "sha256": sha256_file(path)})
    if total_bytes > contract["tokenizer"]["maximum_total_download_bytes"]:
        raise ValueError("tokenizer snapshot exceeds the bounded byte limit")
    config = load_json(snapshot_dir / "tokenizer_config.json")
    chat_template = config.get("chat_template")
    if not isinstance(chat_template, str):
        raise ValueError("Qwen tokenizer chat_template is absent or non-string")
    for marker in ("<|im_start|>", "<|im_end|>", "message.role"):
        if marker not in chat_template:
            raise ValueError(f"Qwen chat_template marker is missing: {marker}")
    return {
        "schema_version": "project05-tokenizer-lock-v0.1",
        "created_date": contract["created_date"],
        "status": "passed_tokenizer_only_snapshot_lock",
        "contract_id": contract["contract_id"],
        "contract_sha256": sha256_file(contract_path),
        "repository_id": contract["tokenizer"]["repository_id"],
        "revision": contract["tokenizer"]["revision"],
        "files": files,
        "file_count": len(files),
        "total_bytes": total_bytes,
        "snapshot_manifest_sha256": sha256_bytes(canonical_bytes(files)),
        "chat_template_sha256": sha256_bytes(chat_template.encode("utf-8")),
        "engine": {
            "package": contract["tokenizer"]["engine_package"],
            "version": contract["tokenizer"]["engine_version"],
            "wheel_name": wheel_path.name,
            "wheel_bytes": wheel_path.stat().st_size,
            "wheel_sha256": sha256_file(wheel_path),
            "install_mode": contract["tokenizer"]["engine_install_mode"],
        },
        "download_boundary": {
            "allowlisted_tokenizer_files_only": True,
            "model_config_downloaded": False,
            "model_weight_downloaded": False,
            "transformers_installed": False,
            "torch_installed": False,
            "peft_installed": False,
            "bitsandbytes_installed": False,
        },
    }


def walk_keys(value: Any) -> set[str]:
    output: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            output.add(str(key))
            output.update(walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            output.update(walk_keys(child))
    return output


def build_messages(
    example: dict[str, Any], serialization: dict[str, Any]
) -> list[dict[str, str]]:
    user = {
        field: copy.deepcopy(example[field]) for field in serialization["user_fields"]
    }
    assistant = {
        field: copy.deepcopy(example[field])
        for field in serialization["assistant_fields"]
    }
    forbidden = set(serialization["forbidden_message_fields"])
    observed_forbidden = (walk_keys(user) | walk_keys(assistant)) & forbidden
    if observed_forbidden:
        raise ValueError(
            f"forbidden message fields observed: {sorted(observed_forbidden)}"
        )
    return [
        {"role": "system", "content": serialization["system_message"]},
        {"role": "user", "content": canonical_json(user)},
        {"role": "assistant", "content": canonical_json(assistant)},
    ]


def render_messages(
    messages: list[dict[str, str]], serialization: dict[str, Any]
) -> str:
    roles = [message["role"] for message in messages]
    if roles != serialization["role_order"]:
        raise ValueError("message role order differs from the frozen contract")
    template = serialization["chat_turn_template"]
    return "".join(
        template.format(role=message["role"], content=message["content"])
        for message in messages
    )


def nearest_rank(values: list[int], quantile: float) -> int:
    if not values:
        raise ValueError("cannot compute a percentile over an empty list")
    if not 0 < quantile <= 1:
        raise ValueError("quantile must be in (0, 1]")
    ordered = sorted(values)
    return ordered[math.ceil(quantile * len(ordered)) - 1]


def distribution(values: list[int], limit: int) -> dict[str, Any]:
    if not values:
        raise ValueError("token distribution is empty")
    return {
        "count": len(values),
        "min": min(values),
        "p50": nearest_rank(values, 0.50),
        "p95": nearest_rank(values, 0.95),
        "max": max(values),
        "over_limit": sum(value > limit for value in values),
    }


def validate_lock(
    lock: dict[str, Any],
    contract: dict[str, Any],
    contract_path: Path,
    snapshot_dir: Path,
    wheel_path: Path,
) -> None:
    rebuilt = build_tokenizer_lock(contract, contract_path, snapshot_dir, wheel_path)
    if lock != rebuilt:
        raise ValueError("tokenizer lock does not match current local bytes")


def load_pair_examples(
    pair_root: Path,
    pair_audit: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    manifest = pair_audit["pair_file_manifest"]
    output: list[tuple[str, dict[str, Any]]] = []
    for entry in manifest:
        path = Path(pair_root) / entry["relative_name"]
        if path.stat().st_size != entry["bytes"]:
            raise ValueError("pair payload byte count mismatch")
        if sha256_file(path) != entry["sha256"]:
            raise ValueError("pair payload SHA-256 mismatch")
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    example = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"invalid pair JSONL at {path.name}:{line_number}"
                    ) from error
                output.append((entry["split_role"], example))
    return output


def audit_tokens(
    contract: dict[str, Any],
    contract_path: Path,
    lock: dict[str, Any],
    lock_path: Path,
    snapshot_dir: Path,
    wheel_path: Path,
    pair_root: Path,
    tokenizer: Any,
    engine_version: str,
) -> dict[str, Any]:
    validate_contract_inputs(contract)
    validate_lock(lock, contract, contract_path, snapshot_dir, wheel_path)
    if engine_version != contract["tokenizer"]["engine_version"]:
        raise ValueError("loaded tokenizer engine version differs from the contract")
    if tokenizer.token_to_id("<|im_start|>") is None:
        raise ValueError("Qwen im_start token is absent")
    if tokenizer.token_to_id("<|im_end|>") is None:
        raise ValueError("Qwen im_end token is absent")
    for marker in ("<|im_start|>", "<|im_end|>"):
        if len(tokenizer.encode(marker, add_special_tokens=False).ids) != 1:
            raise ValueError(f"Qwen chat marker is not one token: {marker}")

    pair_audit_path = REPO_ROOT / contract["inputs"]["pair_data_gate_audit_path"]
    pair_audit = load_json(pair_audit_path)
    examples = load_pair_examples(pair_root, pair_audit)
    serialization = contract["serialization"]
    limit = int(contract["gate"]["maximum_example_tokens"])
    by_split: dict[str, list[int]] = defaultdict(list)
    by_family: dict[str, list[int]] = defaultdict(list)
    all_values: list[int] = []
    role_counts = Counter()
    support_counts = Counter()
    digest = hashlib.sha256()
    for split, example in examples:
        messages = build_messages(example, serialization)
        rendered = render_messages(messages, serialization)
        encoded = tokenizer.encode(rendered, add_special_tokens=False)
        count = len(encoded.ids)
        if count <= 0:
            raise ValueError("tokenizer returned an empty encoding")
        by_split[split].append(count)
        by_family[example["source_family_id"]].append(count)
        all_values.append(count)
        role_counts.update(message["role"] for message in messages)
        support_counts[example["support_decision"]] += 1
        payload = rendered.encode("utf-8")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)

    gate = contract["gate"]
    if len(examples) != gate["exact_total_examples"]:
        raise ValueError("total example count differs from the token Gate contract")
    if len(by_split["train"]) != gate["exact_train_examples"]:
        raise ValueError("train example count differs from the token Gate contract")
    if (
        len(by_split["training-validation"])
        != gate["exact_training_validation_examples"]
    ):
        raise ValueError("training-validation count differs from the contract")

    split_distributions = {
        split: distribution(values, limit)
        for split, values in sorted(by_split.items())
    }
    family_distributions = {
        family: distribution(values, limit)
        for family, values in sorted(by_family.items())
    }
    overall = distribution(all_values, limit)
    p95_limit = int(gate["maximum_p95_tokens"])
    p95_pass = overall["p95"] <= p95_limit and all(
        report["p95"] <= p95_limit for report in split_distributions.values()
    )
    max_pass = overall["max"] <= limit
    over_limit_pass = overall["over_limit"] <= gate["maximum_over_limit_examples"]
    token_gate_passed = p95_pass and max_pass and over_limit_pass
    status = (
        "passed_tokenizer_length_gate"
        if token_gate_passed
        else "failed_closed_tokenizer_length_gate"
    )
    return {
        "schema_version": "project05-label-blind-token-length-audit-v0.1",
        "created_date": contract["created_date"],
        "status": status,
        "contract_id": contract["contract_id"],
        "contract_sha256": sha256_file(contract_path),
        "tokenizer_lock_path": str(
            Path(lock_path).resolve().relative_to(REPO_ROOT)
        ).replace("\\", "/"),
        "tokenizer_lock_sha256": sha256_file(lock_path),
        "tokenizer_identity": {
            "repository_id": lock["repository_id"],
            "revision": lock["revision"],
            "snapshot_manifest_sha256": lock["snapshot_manifest_sha256"],
            "chat_template_sha256": lock["chat_template_sha256"],
            "engine_package": lock["engine"]["package"],
            "engine_version": engine_version,
            "engine_wheel_sha256": lock["engine"]["wheel_sha256"],
        },
        "serialization": {
            "serialization_id": serialization["serialization_id"],
            "contract_sha256": sha256_bytes(canonical_bytes(serialization)),
            "rendered_dataset_sha256": digest.hexdigest().upper(),
            "messages_per_example": 3,
            "role_counts": dict(sorted(role_counts.items())),
            "negative_proof_exposed": False,
            "generator_identity_exposed": False,
        },
        "dataset": {
            "examples": len(examples),
            "support_decisions": dict(sorted(support_counts.items())),
            "overall": overall,
            "splits": split_distributions,
            "families": family_distributions,
        },
        "gate": {
            "percentile_definition": gate["percentile_definition"],
            "maximum_p95_tokens": p95_limit,
            "maximum_example_tokens": limit,
            "p95_pass": p95_pass,
            "max_pass": max_pass,
            "over_limit_pass": over_limit_pass,
            "examples_excluded": 0,
            "examples_truncated": 0,
            "examples_rewritten": 0,
            "token_gate_passed": token_gate_passed,
            "formal_data_gate_passed": bool(
                pair_audit.get("non_token_data_gate_passed") and token_gate_passed
            ),
        },
        "execution_claims": {
            "tokenizer_used": True,
            "tokenizer_only_engine_used": True,
            "model_config_downloaded": False,
            "model_weight_downloaded": False,
            "model_used": False,
            "training_runtime_installed": False,
            "training_run": False,
            "formal_inference_run": False,
            "m3_runtime_integrated": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    lock = subparsers.add_parser("lock")
    lock.add_argument("--contract", type=Path, required=True)
    lock.add_argument("--snapshot", type=Path, required=True)
    lock.add_argument("--wheel", type=Path, required=True)
    lock.add_argument("--output", type=Path, required=True)
    audit = subparsers.add_parser("audit")
    audit.add_argument("--contract", type=Path, required=True)
    audit.add_argument("--lock", type=Path, required=True)
    audit.add_argument("--snapshot", type=Path, required=True)
    audit.add_argument("--wheel", type=Path, required=True)
    audit.add_argument("--pair-root", type=Path, required=True)
    audit.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract = load_json(args.contract)
    if args.command == "lock":
        result = build_tokenizer_lock(
            contract, args.contract, args.snapshot, args.wheel
        )
    else:
        lock = load_json(args.lock)
        try:
            import tokenizers
            from tokenizers import Tokenizer
        except ImportError as error:
            raise RuntimeError(
                "isolated tokenizers engine is unavailable; do not substitute a tokenizer"
            ) from error
        tokenizer = Tokenizer.from_file(str(args.snapshot / "tokenizer.json"))
        result = audit_tokens(
            contract,
            args.contract,
            lock,
            args.lock,
            args.snapshot,
            args.wheel,
            args.pair_root,
            tokenizer,
            tokenizers.__version__,
        )
    write_json_no_overwrite(args.output, result)
    print(f"{result['status']}: {result.get('dataset', {}).get('examples', 4)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
