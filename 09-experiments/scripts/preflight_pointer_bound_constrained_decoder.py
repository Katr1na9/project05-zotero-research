#!/usr/bin/env python3
"""Install and probe the v0.44 constrained decoder without loading a model."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ROOT = Path("/home/myy/project05-qwen25-4090-v0.1")
EXPECTED_DISTRIBUTION = "lm-format-enforcer"
EXPECTED_VERSION = "0.10.6"


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


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


def require_within(path: Path, root: Path, label: str) -> Path:
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(Path(root).resolve())
    except ValueError as error:
        raise ValueError(f"{label} escapes the authorized server root") from error
    return resolved


def verify_repo_record(record: dict[str, Any], label: str) -> Path:
    path = (REPO_ROOT / record["path"]).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as error:
        raise ValueError(f"{label} escapes the deployed repository") from error
    if not path.is_file():
        raise FileNotFoundError(f"{label} is missing")
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"{label} SHA-256 mismatch")
    return path


def validate_authority(
    authority_path: Path,
    run_root: Path,
    preparation_audit: Path,
    dependency_target: Path,
    output: Path,
    failure_output: Path,
) -> dict[str, Any]:
    run_root = Path(run_root).resolve()
    if run_root != EXPECTED_ROOT:
        raise ValueError("preflight run root differs from the sole authorized root")
    authority_path = require_within(authority_path, run_root, "authority")
    preparation_audit = require_within(
        preparation_audit,
        run_root,
        "preparation audit",
    )
    dependency_target = require_within(
        dependency_target,
        run_root,
        "dependency target",
    )
    output = require_within(output, run_root, "preflight output")
    failure_output = require_within(
        failure_output,
        run_root,
        "preflight failure output",
    )
    if output.exists() or failure_output.exists():
        raise FileExistsError("preflight success or failure audit already exists")
    authority = load_json(authority_path)
    gate = authority.get("compatibility_preflight_gate", {})
    if gate.get("authorized") is not True or gate.get("maximum_attempts") != 1:
        raise PermissionError("one explicit compatibility preflight is required")
    if gate.get("maximum_model_calls") != 0:
        raise PermissionError("compatibility preflight unexpectedly permits model calls")
    expected_paths = {
        "dependency_target": dependency_target,
        "output": output,
        "failure_output": failure_output,
    }
    for field, observed in expected_paths.items():
        expected = (run_root / gate[field]).resolve()
        if observed != expected:
            raise ValueError(f"{field} differs from the authority")
    if sha256_file(preparation_audit) != gate["preparation_audit_sha256"]:
        raise ValueError("preparation audit SHA-256 mismatch")
    for label, record in authority["hash_locked_artifacts"].items():
        verify_repo_record(record, label)
    if gate.get("dependency_distribution") != EXPECTED_DISTRIBUTION:
        raise ValueError("constrained-decoder distribution differs")
    if gate.get("dependency_version") != EXPECTED_VERSION:
        raise ValueError("constrained-decoder version differs")
    if any(
        gate.get(field) is not False
        for field in (
            "model_loading_authorized",
            "model_inference_authorized",
            "training_validation_payload_access_authorized",
            "development_or_test_access_authorized",
            "c07_c12_access_authorized",
            "m3_access_authorized",
            "automatic_retry_authorized",
        )
    ):
        raise PermissionError("preflight opens model, data, or retry scope")
    return authority


def target_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in Path(root).rglob("*") if path.is_file())


def install_isolated_dependency(
    requirements: Path,
    dependency_target: Path,
    run_root: Path,
    maximum_bytes: int,
) -> dict[str, Any]:
    dependency_target = Path(dependency_target)
    temporary = dependency_target.with_name(dependency_target.name + ".installing")
    if dependency_target.exists() or temporary.exists():
        raise FileExistsError("dependency target or installing directory already exists")
    temporary.mkdir(parents=True, exist_ok=False)
    cache = require_within(
        run_root / "local-cache/pip-v0.45",
        run_root,
        "pip cache",
    )
    temp_root = require_within(
        run_root / "local-cache/tmp-v0.45",
        run_root,
        "pip temporary directory",
    )
    cache.mkdir(parents=True, exist_ok=True)
    temp_root.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.update(
        {
            "PIP_CACHE_DIR": str(cache),
            "TMPDIR": str(temp_root),
            "TMP": str(temp_root),
            "TEMP": str(temp_root),
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INPUT": "1",
        }
    )
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "--target",
        str(temporary),
        "--requirement",
        str(requirements),
    ]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=run_root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        raise RuntimeError(
            "isolated_dependency_install_failed_returncode_"
            f"{completed.returncode}"
        )
    installed_bytes = target_bytes(temporary)
    if installed_bytes > maximum_bytes:
        raise ValueError("isolated dependency exceeds the byte Gate")
    temporary.replace(dependency_target)
    return {
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
        "installed_bytes": installed_bytes,
        "maximum_bytes": maximum_bytes,
        "pip_stdout_or_stderr_persisted": False,
        "automatic_retry_performed": False,
    }


def installed_distributions(dependency_target: Path) -> list[dict[str, str]]:
    output = []
    for distribution in importlib.metadata.distributions(path=[str(dependency_target)]):
        name = distribution.metadata.get("Name")
        if name:
            output.append({"name": name, "version": distribution.version})
    return sorted(output, key=lambda row: row["name"].lower())


def actual_target_ids(tokenizer: Any, prompt: str, target: str) -> tuple[list[int], list[int]]:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
    combined = tokenizer.encode(prompt + target, add_special_tokens=False)
    if combined[: len(prompt_ids)] == prompt_ids:
        return prompt_ids, combined[len(prompt_ids) :]
    return prompt_ids, tokenizer.encode(target, add_special_tokens=False)


def probe_branch(
    tokenizer: Any,
    torch: Any,
    schema: dict[str, Any],
    prompt: str,
    target: dict[str, Any],
) -> dict[str, Any]:
    from lmformatenforcer import JsonSchemaParser
    from lmformatenforcer.integrations.transformers import (
        build_transformers_prefix_allowed_tokens_fn,
    )

    parser = JsonSchemaParser(schema)
    prefix_fn = build_transformers_prefix_allowed_tokens_fn(tokenizer, parser)
    text = canonical_json(target)
    prompt_ids, target_ids = actual_target_ids(tokenizer, prompt, text)
    sequence = list(prompt_ids)
    minimum_allowed = None
    maximum_allowed = 0
    for index, token in enumerate(target_ids):
        allowed = list(prefix_fn(0, torch.tensor(sequence, dtype=torch.long)))
        if not allowed:
            raise ValueError(f"empty allowed-token set at target token {index}")
        if token not in allowed:
            raise ValueError(f"canonical target token rejected at index {index}")
        minimum_allowed = len(allowed) if minimum_allowed is None else min(
            minimum_allowed,
            len(allowed),
        )
        maximum_allowed = max(maximum_allowed, len(allowed))
        sequence.append(token)
    final_allowed = list(prefix_fn(0, torch.tensor(sequence, dtype=torch.long)))
    eos_ids = (
        tokenizer.eos_token_id
        if isinstance(tokenizer.eos_token_id, list)
        else [tokenizer.eos_token_id]
    )
    if not any(token in final_allowed for token in eos_ids):
        raise ValueError("EOS is not allowed after a complete constrained target")
    return {
        "canonical_target_sha256": hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest().upper(),
        "prompt_tokens": len(prompt_ids),
        "target_tokens": len(target_ids),
        "minimum_allowed_tokens": minimum_allowed,
        "maximum_allowed_tokens": maximum_allowed,
        "final_eos_allowed": True,
    }


def compatibility_probe(
    authority: dict[str, Any],
    run_root: Path,
    preparation_audit: Path,
    dependency_target: Path,
) -> dict[str, Any]:
    sys.path.insert(0, str(dependency_target))
    observed_version = importlib.metadata.version(EXPECTED_DISTRIBUTION)
    if observed_version != EXPECTED_VERSION:
        raise ValueError("installed constrained-decoder version differs")
    import lmformatenforcer
    import torch
    import transformers
    from jsonschema import Draft202012Validator
    from transformers import AutoTokenizer

    module_path = require_within(
        Path(lmformatenforcer.__file__),
        dependency_target,
        "lm-format-enforcer module",
    )
    preparation = load_json(preparation_audit)
    snapshot = require_within(
        Path(preparation["model_snapshot"]["snapshot_dir"]),
        run_root,
        "tokenizer snapshot",
    )
    schema_path = verify_repo_record(
        authority["hash_locked_artifacts"]["model_output_schema"],
        "model output schema",
    )
    serialization_path = verify_repo_record(
        authority["hash_locked_artifacts"]["serialization_contract"],
        "serialization contract",
    )
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    serialization = load_json(serialization_path)["serialization"]
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot,
        local_files_only=True,
        trust_remote_code=False,
    )
    fixture_pointer = {
        "artifact_id": "ART-PREFLIGHT",
        "record_id": "REC-PREFLIGHT",
        "record_sha256": "A" * 64,
    }
    fixture_candidate = {
        "subject_type": "process",
        "subject_value": "preflight.exe",
        "predicate": "wrote",
        "object_type": "file",
        "object_value": "/tmp/preflight.bin",
    }
    user = {
        "source_modality": "synthetic_preflight_only",
        "bound_pointer": fixture_pointer,
        "payload": {
            "process": "preflight.exe",
            "operation": "write",
            "path": "/tmp/preflight.bin",
        },
        "candidate": fixture_candidate,
    }
    template = serialization["chat_turn_template"]
    prompt = (
        template.format(role="system", content=serialization["system_message"])
        + template.format(role="user", content=canonical_json(user))
        + "<|im_start|>assistant\n"
    )
    branches = {
        "supported": probe_branch(
            tokenizer,
            torch,
            schema,
            prompt,
            {
                "support_decision": "supported",
                "edge_fields": fixture_candidate,
            },
        ),
        "unsupported_by_bound_pointer": probe_branch(
            tokenizer,
            torch,
            schema,
            prompt,
            {
                "support_decision": "unsupported_by_bound_pointer",
                "edge_fields": None,
            },
        ),
    }
    return {
        "distribution": EXPECTED_DISTRIBUTION,
        "version": observed_version,
        "module_path_relative_to_dependency_target": str(
            module_path.relative_to(dependency_target)
        ),
        "transformers_version": transformers.__version__,
        "torch_version": torch.__version__,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_snapshot_within_authorized_root": True,
        "schema_sha256": sha256_file(schema_path),
        "branches": branches,
        "model_class_imported": False,
        "model_loaded": False,
        "model_generate_calls": 0,
        "training_validation_payload_accessed": False,
    }


def run_preflight(
    authority_path: Path,
    run_root: Path,
    preparation_audit: Path,
    dependency_target: Path,
    output: Path,
    failure_output: Path,
) -> dict[str, Any]:
    authority = validate_authority(
        authority_path,
        run_root,
        preparation_audit,
        dependency_target,
        output,
        failure_output,
    )
    gate = authority["compatibility_preflight_gate"]
    requirements = verify_repo_record(
        authority["hash_locked_artifacts"]["runtime_requirement"],
        "runtime requirement",
    )
    started = time.monotonic()
    try:
        install = install_isolated_dependency(
            requirements,
            dependency_target,
            run_root,
            gate["maximum_dependency_target_bytes"],
        )
        probe = compatibility_probe(
            authority,
            run_root,
            preparation_audit,
            dependency_target,
        )
        distributions = installed_distributions(dependency_target)
        audit = {
            "schema_version": "project05-constrained-decoder-preflight-v0.1",
            "status": "passed_isolated_dependency_and_tokenizer_schema_preflight",
            "authority_sha256": sha256_file(authority_path),
            "requirements_sha256": sha256_file(requirements),
            "dependency_target_relative_to_run_root": str(
                dependency_target.relative_to(run_root)
            ),
            "install": install,
            "installed_distributions": distributions,
            "compatibility": probe,
            "total_elapsed_seconds": time.monotonic() - started,
            "scope": {
                "model_loaded": False,
                "model_calls": 0,
                "training_validation_payload_accessed": False,
                "development_or_test_accessed": False,
                "c07_c12_accessed": False,
                "m3_accessed": False,
                "server_other_directory_accessed": False,
                "automatic_retry_performed": False,
            },
            "next_gate": "new_single_atomic_model_execution_authority_required",
        }
        write_json_no_overwrite(output, audit)
        return audit
    except BaseException as error:
        failure = {
            "schema_version": "project05-constrained-decoder-preflight-failure-v0.1",
            "status": "failed_compatibility_preflight_no_automatic_retry",
            "authority_sha256": sha256_file(authority_path),
            "failure_type": type(error).__name__,
            "failure_message": str(error)[:500],
            "model_loaded": False,
            "model_calls": 0,
            "training_validation_payload_accessed": False,
            "automatic_retry_authorized": False,
            "unconstrained_fallback_authorized": False,
        }
        if not failure_output.exists():
            write_json_no_overwrite(failure_output, failure)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--preparation-audit", type=Path, required=True)
    parser.add_argument("--dependency-target", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--failure-output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_authority(
            args.authority,
            args.run_root,
            args.preparation_audit,
            args.dependency_target,
            args.output,
            args.failure_output,
        )
        print("v0.45 compatibility-preflight authority valid; no install performed")
        return 0
    result = run_preflight(
        args.authority,
        args.run_root,
        args.preparation_audit,
        args.dependency_target,
        args.output,
        args.failure_output,
    )
    print(result["status"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
