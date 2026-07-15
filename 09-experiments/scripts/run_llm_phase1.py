#!/usr/bin/env python3
"""Run dependency-free Rule/stub stages for Project05 LLM Phase 1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import inspect
import json
import random
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = EXPERIMENT_ROOT / "llm_compiler_v0.2" / "experiment_config.json"
PROMPT_DIR = EXPERIMENT_ROOT / "llm_compiler_v0.2" / "prompts"
SCHEMA_DIR = EXPERIMENT_ROOT / "data_schema"
CONTRACT_PATH = (
    EXPERIMENT_ROOT / "governance" / "contracts" / "llm-compiler-contract-v0.2.json"
)
RUNNER_PATH = Path(__file__).resolve()
RULE_IMPLEMENTATION_VERSION = "project05-rule-compiler-v0.2"
PROMPT_FILES = (
    "compiler-system-v0.2.txt",
    "compiler-user-v0.2.txt",
    "structured-system-v0.2.txt",
    "direct-system-v0.2.txt",
)
SCHEMA_FILES = (
    "llm_context_packet.schema.json",
    "llm_compiler_result.schema.json",
    "llm_conclusion_result.schema.json",
    "llm_run_manifest.schema.json",
)
STAGE_HASH_CHAIN_KEYS = (
    "stage1_prompt_sha256",
    "stage1_raw_sha256",
    "admission_sha256",
    "stage2_input_sha256",
    "stage2_prompt_sha256",
    "stage2_raw_sha256",
    "final_result_sha256",
)
SHA256_PATTERN = re.compile(r"^[A-F0-9]{64}$")
REQUIRED_READINESS_CHECKS = (
    "targeted_tests",
    "public_private_scan",
    "prompt_config_lock",
    "test_bundle_shape",
    "dependency_isolation",
    "no_model_output",
    "forbidden_file_diff",
)
TARGET_TEST_MODULES = (
    "09-experiments.tests.test_llm_packet_separation",
    "09-experiments.tests.test_llm_phase1_contract",
    "09-experiments.tests.test_llm_phase1_validation",
    "09-experiments.tests.test_llm_phase1_scoring",
    "09-experiments.tests.test_llm_compiler_pilot",
)
FORBIDDEN_INFERENCE_PACKAGES = (
    "torch",
    "transformers",
    "accelerate",
    "bitsandbytes",
    "jsonschema",
)


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_BUILDER = load_sibling(
    "project05_llm_packet_builder_for_runner",
    "build_llm_evaluation_packets.py",
)
_VALIDATOR = load_sibling(
    "project05_llm_validator_for_runner",
    "validate_llm_phase1_output.py",
)
_SCORER = load_sibling(
    "project05_llm_scorer_for_runner",
    "score_llm_phase1.py",
)

canonical_json = _BUILDER.canonical_json
derive_candidate_claim_id = _BUILDER.derive_candidate_claim_id
read_jsonl_gz = _BUILDER.read_jsonl_gz
write_json = _BUILDER.write_json
write_jsonl_gz = _BUILDER.write_jsonl_gz


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest().upper()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def read_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text(encoding="utf-8")


class InferenceBackend:
    """Small backend boundary that keeps model imports out of pre-model code."""

    backend_id = "abstract_inference_backend"

    def generate(
        self,
        messages: list[dict[str, str]],
        generation_config: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError


class StubBackend(InferenceBackend):
    """Deterministic, dependency-free backend used only for contract tests."""

    backend_id = "deterministic_stub_v0.2"

    def __init__(self, responses: Iterable[Any] | None = None):
        self._responses = list(responses or [])

    def generate(
        self,
        messages: list[dict[str, str]],
        generation_config: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        del generation_config
        request = json.loads(messages[-1]["content"])
        if self._responses:
            payload = self._responses.pop(0)
            text = (
                payload
                if isinstance(payload, str)
                else json.dumps(payload, ensure_ascii=False, sort_keys=True)
            )
        else:
            stage = request.get("stage")
            if stage == "compiler":
                payload = {"status": "abstain", "candidate_claims": []}
            else:
                stage_input = request.get("stage2_input") or {}
                gaps = list(stage_input.get("explicit_gaps") or [])
                payload = {
                    "status": "abstain",
                    "observation_claims": [],
                    "highest_supported_granularity": "G0_unknown",
                    "path_summary": None,
                    "actor": None,
                    "campaign": None,
                    "missing_evidence": gaps or ["no_supported_observation"],
                    "abstain": True,
                    "citations": [],
                }
            text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        telemetry = {
            "latency_ms": 0.0,
            "peak_vram_mb": 0,
            "input_tokens": None,
            "output_tokens": None,
            "error_code": None,
        }
        return text, telemetry


def generation_for(
    condition_id: str,
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    config = load_json(config_path)
    try:
        return dict(config["conditions"][condition_id]["generation"])
    except KeyError as error:
        raise ValueError(f"unknown condition: {condition_id}") from error


def compiler_messages(
    packet: dict[str, Any],
    condition_id: str,
    attempt_index: int,
) -> list[dict[str, str]]:
    request = {
        "stage": "compiler",
        "protocol": read_prompt("compiler-user-v0.2.txt"),
        "condition_id": condition_id,
        "attempt_index": int(attempt_index),
        "packet": packet,
    }
    return [
        {"role": "system", "content": read_prompt("compiler-system-v0.2.txt")},
        {
            "role": "user",
            "content": canonical_json(request).decode("utf-8"),
        },
    ]


def conclusion_messages(
    stage: str,
    payload: dict[str, Any],
    attempt_index: int,
) -> list[dict[str, str]]:
    if stage == "structured":
        prompt_name = "structured-system-v0.2.txt"
        request = {
            "stage": stage,
            "attempt_index": int(attempt_index),
            "stage2_input": payload,
        }
    elif stage == "direct":
        prompt_name = "direct-system-v0.2.txt"
        request = {
            "stage": stage,
            "attempt_index": int(attempt_index),
            "packet": payload,
        }
    else:
        raise ValueError(f"unsupported conclusion stage: {stage}")
    return [
        {"role": "system", "content": read_prompt(prompt_name)},
        {
            "role": "user",
            "content": canonical_json(request).decode("utf-8"),
        },
    ]


def normalize_telemetry(
    telemetry: Any,
    error_code: str | None = None,
) -> dict[str, Any]:
    source = telemetry if isinstance(telemetry, dict) else {}
    return {
        "latency_ms": source.get("latency_ms"),
        "peak_vram_mb": source.get("peak_vram_mb"),
        "input_tokens": source.get("input_tokens"),
        "output_tokens": source.get("output_tokens"),
        "error_code": error_code if error_code is not None else source.get("error_code"),
    }


def parse_json_object(raw_text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        return None, "json_parse_error"
    if not isinstance(payload, dict):
        return None, "json_root_not_object"
    return payload, None


def bind_missing_candidate_ids(
    claims: Any,
    request_id: str,
    condition_id: str,
    attempt_index: int,
) -> Any:
    if not isinstance(claims, list):
        return claims
    bound = []
    for output_index, claim in enumerate(claims):
        if isinstance(claim, dict):
            claim = dict(claim)
            claim.setdefault(
                "candidate_claim_id",
                derive_candidate_claim_id(
                    request_id,
                    condition_id,
                    attempt_index,
                    output_index,
                ),
            )
        bound.append(claim)
    return bound


def compiler_result_from_raw(
    packet: dict[str, Any],
    condition_id: str,
    attempt_index: int,
    raw_text: str,
    telemetry: dict[str, Any],
) -> dict[str, Any]:
    payload, error_code = parse_json_object(raw_text)
    if payload is None:
        return {
            "request_id": packet["request_id"],
            "condition_id": condition_id,
            "attempt_index": int(attempt_index),
            "status": "invalid",
            "candidate_claims": [],
            "telemetry": normalize_telemetry(telemetry, error_code),
        }
    claims = bind_missing_candidate_ids(
        payload.get("candidate_claims"),
        packet["request_id"],
        condition_id,
        int(attempt_index),
    )
    if not isinstance(claims, list):
        return {
            "request_id": packet["request_id"],
            "condition_id": condition_id,
            "attempt_index": int(attempt_index),
            "status": "invalid",
            "candidate_claims": [],
            "telemetry": normalize_telemetry(
                telemetry, "candidate_claims_not_array"
            ),
        }
    status = payload.get("status")
    if status not in {"completed", "abstain", "invalid", "error"}:
        status = "completed" if claims else "abstain"
    return {
        "request_id": packet["request_id"],
        "condition_id": condition_id,
        "attempt_index": int(attempt_index),
        "status": status,
        "candidate_claims": claims,
        "telemetry": normalize_telemetry(telemetry),
    }


def conclusion_result_from_raw(
    packet: dict[str, Any],
    condition_id: str,
    attempt_index: int,
    raw_text: str,
) -> dict[str, Any]:
    payload, error_code = parse_json_object(raw_text)
    if payload is None:
        payload = {
            "status": "invalid",
            "observation_claims": [],
            "highest_supported_granularity": "G0_unknown",
            "path_summary": None,
            "actor": None,
            "campaign": None,
            "missing_evidence": [str(error_code)],
            "abstain": True,
            "citations": [],
        }
    observations = bind_missing_candidate_ids(
        payload.get("observation_claims", []),
        packet["request_id"],
        condition_id,
        int(attempt_index),
    )
    if not isinstance(observations, list):
        observations = []
        payload["status"] = "invalid"
        payload["missing_evidence"] = ["observation_claims_not_array"]
        payload["abstain"] = True
    return {
        "request_id": packet["request_id"],
        "condition_id": condition_id,
        "attempt_index": int(attempt_index),
        "status": payload.get("status", "completed"),
        "observation_claims": observations,
        "highest_supported_granularity": payload.get(
            "highest_supported_granularity", "G0_unknown"
        ),
        "path_summary": payload.get("path_summary"),
        "actor": payload.get("actor"),
        "campaign": payload.get("campaign"),
        "missing_evidence": list(payload.get("missing_evidence") or []),
        "abstain": bool(payload.get("abstain", not observations)),
        "citations": list(payload.get("citations") or []),
    }


def stage_chain(**values: Any) -> dict[str, Any]:
    return {key: values.get(key) for key in STAGE_HASH_CHAIN_KEYS}


def run_compiler(
    packet: dict[str, Any],
    condition_id: str,
    backend: InferenceBackend,
    attempt_index: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if condition_id not in {"general_compiler", "security_compiler"}:
        raise ValueError("run_compiler requires a model compiler condition")
    messages = compiler_messages(packet, condition_id, attempt_index)
    raw_text, telemetry = backend.generate(
        messages,
        generation_for(condition_id),
    )
    result = compiler_result_from_raw(
        packet,
        condition_id,
        attempt_index,
        raw_text,
        telemetry,
    )
    result_sha256 = sha256_value(result)
    chain = stage_chain(
        stage1_prompt_sha256=sha256_value(messages),
        stage1_raw_sha256=sha256_text(raw_text),
        final_result_sha256=result_sha256,
    )
    manifest = {
        "condition_id": condition_id,
        "attempt_index": int(attempt_index),
        "backend_id": backend.backend_id,
        "stage_hash_chain": chain,
        "result_sha256": result_sha256,
        "status": "failed" if result["status"] in {"invalid", "error"} else "completed",
    }
    return result, manifest


def run_structured(
    packet: dict[str, Any],
    backend: InferenceBackend,
    attempt_index: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    compiler_result, compiler_manifest = run_compiler(
        packet,
        "general_compiler",
        backend,
        attempt_index,
    )
    admission = _VALIDATOR.admit_candidates(compiler_result, packet)
    stage2_input = _VALIDATOR.build_structured_stage2_input(
        admission,
        packet["support_ceiling"],
    )
    messages = conclusion_messages("structured", stage2_input, attempt_index)
    raw_text, _ = backend.generate(
        messages,
        generation_for("general_structured"),
    )
    result = conclusion_result_from_raw(
        packet,
        "general_structured",
        attempt_index,
        raw_text,
    )
    result_sha256 = sha256_value(result)
    chain = stage_chain(
        stage1_prompt_sha256=compiler_manifest["stage_hash_chain"][
            "stage1_prompt_sha256"
        ],
        stage1_raw_sha256=compiler_manifest["stage_hash_chain"][
            "stage1_raw_sha256"
        ],
        admission_sha256=sha256_value(admission),
        stage2_input_sha256=sha256_value(stage2_input),
        stage2_prompt_sha256=sha256_value(messages),
        stage2_raw_sha256=sha256_text(raw_text),
        final_result_sha256=result_sha256,
    )
    manifest = {
        "condition_id": "general_structured",
        "attempt_index": int(attempt_index),
        "backend_id": backend.backend_id,
        "stage_hash_chain": chain,
        "result_sha256": result_sha256,
        "status": "failed" if result["status"] in {"invalid", "error"} else "completed",
    }
    return result, manifest


def run_direct(
    packet: dict[str, Any],
    backend: InferenceBackend,
    attempt_index: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    messages = conclusion_messages("direct", packet, attempt_index)
    raw_text, _ = backend.generate(
        messages,
        generation_for("general_direct"),
    )
    result = conclusion_result_from_raw(
        packet,
        "general_direct",
        attempt_index,
        raw_text,
    )
    result_sha256 = sha256_value(result)
    chain = stage_chain(
        stage1_prompt_sha256=sha256_value(messages),
        stage1_raw_sha256=sha256_text(raw_text),
        final_result_sha256=result_sha256,
    )
    manifest = {
        "condition_id": "general_direct",
        "attempt_index": int(attempt_index),
        "backend_id": backend.backend_id,
        "stage_hash_chain": chain,
        "result_sha256": result_sha256,
        "status": "failed" if result["status"] in {"invalid", "error"} else "completed",
    }
    return result, manifest


def hash_chain_complete(manifest: dict[str, Any]) -> bool:
    chain = manifest.get("stage_hash_chain")
    if not isinstance(chain, dict) or list(chain) != list(STAGE_HASH_CHAIN_KEYS):
        return False
    if not all(
        isinstance(chain.get(key), str) and SHA256_PATTERN.fullmatch(chain[key])
        for key in STAGE_HASH_CHAIN_KEYS
    ):
        return False
    return chain["final_result_sha256"] == manifest.get("result_sha256")


def select_repeat_panel(
    rows: Iterable[dict[str, Any]],
    seed: int,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        case_prefix = str(row.get("case_id") or "").split("-", 1)[0]
        role = str(row.get("packet_role") or "")
        if case_prefix and role in {"positive", "null"}:
            groups.setdefault((case_prefix, role), []).append(row)
    cases = sorted({case for case, _ in groups})
    if len(cases) != 6:
        raise ValueError("repeat panel requires exactly six test cases")
    rng = random.Random(int(seed))
    panel = []
    for case in cases:
        for role in ("positive", "null"):
            candidates = sorted(
                groups.get((case, role), []),
                key=lambda row: str(row.get("request_id") or ""),
            )
            if not candidates:
                raise ValueError(f"repeat panel missing {case}/{role}")
            panel.append(dict(candidates[rng.randrange(len(candidates))]))
    return panel


def calculate_call_budget(config: dict[str, Any]) -> dict[str, int]:
    test = config["splits"]["test"]
    packet_count = int(test["positive_packets"]) + int(test["null_packets"])
    first_pass = packet_count * 4
    repeat = (
        int(config["repeat_panel"]["packet_count"])
        * len(config["repeat_panel"]["conditions"])
        * len(config["repeat_panel"]["additional_attempt_indices"])
    )
    maximum = first_pass + repeat
    declared = config["call_budget"]
    expected = {
        "first_pass": first_pass,
        "repeat_diagnostic": repeat,
        "maximum_formal": maximum,
    }
    mismatches = [
        key for key, value in expected.items() if int(declared.get(key, -1)) != value
    ]
    if mismatches:
        raise ValueError(f"call budget mismatch: {mismatches}")
    return {
        "first_pass": first_pass,
        "repeat_diagnostic": repeat,
        "maximum": maximum,
    }


def freeze_prompt_config_lock(
    output_path: Path,
    config_path: Path = CONFIG_PATH,
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    output_path = Path(output_path)
    if output_path.exists():
        raise ValueError(f"refusing to overwrite prompt/config lock: {output_path}")
    prompt_hashes = {
        name: sha256_file(PROMPT_DIR / name) for name in PROMPT_FILES
    }
    schema_hashes = {
        name: sha256_file(SCHEMA_DIR / name) for name in SCHEMA_FILES
    }
    lock = {
        "status": "frozen_pre_model",
        "prompt_sha256": prompt_hashes,
        "schema_sha256": schema_hashes,
        "config_file_sha256": sha256_file(Path(config_path)),
        "contract_sha256": sha256_file(Path(contract_path)),
    }
    lock["lock_sha256"] = sha256_value(lock)
    write_json(output_path, lock)
    return lock


def validate_prompt_config_lock(
    lock_path: Path,
    config_path: Path = CONFIG_PATH,
    contract_path: Path = CONTRACT_PATH,
) -> list[str]:
    lock = load_json(Path(lock_path))
    errors = []
    expected_prompts = {
        name: sha256_file(PROMPT_DIR / name) for name in PROMPT_FILES
    }
    expected_schemas = {
        name: sha256_file(SCHEMA_DIR / name) for name in SCHEMA_FILES
    }
    if lock.get("prompt_sha256") != expected_prompts:
        errors.append("prompt_hash_mismatch")
    if lock.get("schema_sha256") != expected_schemas:
        errors.append("schema_hash_mismatch")
    if lock.get("config_file_sha256") != sha256_file(Path(config_path)):
        errors.append("config_hash_mismatch")
    if lock.get("contract_sha256") != sha256_file(Path(contract_path)):
        errors.append("contract_hash_mismatch")
    lock_body = {key: value for key, value in lock.items() if key != "lock_sha256"}
    if lock.get("lock_sha256") != sha256_value(lock_body):
        errors.append("lock_hash_mismatch")
    if lock.get("status") != "frozen_pre_model":
        errors.append("lock_status_invalid")
    return sorted(errors)


def scan_packet_bundle(bundle_dir: Path) -> list[str]:
    bundle_dir = Path(bundle_dir)
    public_dir = bundle_dir / "public"
    private_dir = bundle_dir / "private"
    errors = []
    try:
        public_rows = read_jsonl_gz(public_dir / "context_packets.jsonl.gz")
        private_rows = read_jsonl_gz(private_dir / "observation_gold.jsonl.gz")
        catalog = load_json(public_dir / "public_cti_catalog.json")
        input_manifest = load_json(public_dir / "input_manifest.json")
        for row in public_rows:
            _BUILDER.assert_public_safe(row)
        _BUILDER.assert_public_safe(catalog)
        decoded_public = b"\n".join(
            [canonical_json(row) for row in public_rows]
            + [canonical_json(catalog), canonical_json(input_manifest)]
        )
        if any(
            identifier.encode("utf-8") in decoded_public
            for identifier in _BUILDER.private_identifiers(private_rows)
        ):
            errors.append("private_identifier_in_public_bytes")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        errors.append("packet_bundle_unreadable_or_unsafe")
    return sorted(set(errors))


def assemble_pre_model_readiness(
    checks: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    failed_required = [
        name
        for name in REQUIRED_READINESS_CHECKS
        if (checks.get(name) or {}).get("status") != "passed"
    ]
    gate_blockers = [
        name
        for name in ("null_construction_audit", "rule_baseline_snapshot")
        if (checks.get(name) or {}).get("status") != "passed"
    ]
    blockers = failed_required + gate_blockers
    ready = not blockers
    if failed_required:
        status = "blocked_pre_model_checks"
    elif gate_blockers:
        status = "blocked_pending_human_gates"
    else:
        status = "ready_to_request_model_authorization"
    return {
        "report_version": "project05-llm-phase1-pre-model-readiness-v0.2",
        "status": status,
        "ready_to_request_model_authorization": ready,
        "hard_stop": "A",
        "checks": checks,
        "blockers": blockers,
    }


def run_targeted_pre_model_tests() -> dict[str, Any]:
    command = [sys.executable, "-m", "unittest", *TARGET_TEST_MODULES, "-v"]
    completed = subprocess.run(
        command,
        cwd=EXPERIMENT_ROOT.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    matches = re.findall(r"Ran (\d+) tests?", output)
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "modules": list(TARGET_TEST_MODULES),
        "old_pilot_included": TARGET_TEST_MODULES[-1],
        "returncode": completed.returncode,
        "test_count": int(matches[-1]) if matches else None,
        "output_sha256": sha256_text(output),
    }


def inspect_test_bundle_shape() -> dict[str, Any]:
    manifest_path = (
        EXPERIMENT_ROOT
        / "llm_compiler_v0.2"
        / "generated"
        / "test"
        / "public"
        / "input_manifest.json"
    )
    try:
        manifest = load_json(manifest_path)
        file_hashes_match = all(
            (manifest_path.parent / filename).exists()
            and sha256_file(manifest_path.parent / filename) == expected_hash
            for filename, expected_hash in (manifest.get("files") or {}).items()
        )
        expected = (
            manifest.get("packet_count") == 64
            and manifest.get("case_count") == 6
            and manifest.get("packet_counts") == {"positive": 32, "null": 32}
            and manifest.get("split") == "test"
            and len(manifest.get("files") or {}) == 2
            and file_hashes_match
        )
    except (OSError, ValueError, json.JSONDecodeError):
        manifest = {}
        file_hashes_match = False
        expected = False
    return {
        "status": "passed" if expected else "failed",
        "packet_count": manifest.get("packet_count"),
        "case_count": manifest.get("case_count"),
        "packet_counts": manifest.get("packet_counts"),
        "declared_file_hashes_match": file_hashes_match,
        "formal_ready": bool(manifest.get("formal_ready")),
    }


def null_audit_split_frozen(
    rows: list[dict[str, Any]],
    private_manifest: dict[str, Any],
    expected_count: int,
    audit_sha256: str,
) -> bool:
    completed = 0
    for row in rows:
        author = str(row.get("author_id") or "").strip()
        reviewer = str(row.get("reviewer_id") or "").strip()
        decisions_are_yes = (
            str(row.get("author_no_acceptable_observation") or "").casefold()
            == "yes"
            and str(
                row.get("reviewer_no_acceptable_observation") or ""
            ).casefold()
            == "yes"
        )
        if decisions_are_yes and author and reviewer and author != reviewer:
            completed += 1
    frozen = private_manifest.get("null_construction_audit") or {}
    return (
        len(rows) == expected_count
        and completed == expected_count
        and frozen.get("status") == "frozen"
        and frozen.get("audit_sha256") == audit_sha256
        and int(frozen.get("confirmed_count") or 0) == expected_count
    )


def inspect_null_construction_audits() -> dict[str, Any]:
    audit_dir = (
        EXPERIMENT_ROOT
        / "llm_compiler_v0.2"
        / "generated"
        / "null-construction-audit"
    )
    expected_counts = {"development": 26, "test": 32}
    summaries = {}
    all_frozen = True
    malformed = False
    all_human_complete = True
    for split, expected_count in expected_counts.items():
        path = audit_dir / f"{split}.csv"
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            private_manifest = load_json(
                audit_dir.parent / split / "private" / "gold_manifest.json"
            )
            audit_sha256 = sha256_file(path)
        except OSError:
            rows = []
            private_manifest = {}
            audit_sha256 = ""
            malformed = True
        completed = 0
        for row in rows:
            author = str(row.get("author_id") or "").strip()
            reviewer = str(row.get("reviewer_id") or "").strip()
            decisions_are_yes = (
                str(row.get("author_no_acceptable_observation") or "").casefold()
                == "yes"
                and str(
                    row.get("reviewer_no_acceptable_observation") or ""
                ).casefold()
                == "yes"
            )
            if decisions_are_yes and author and reviewer and author != reviewer:
                completed += 1
        human_complete = len(rows) == expected_count and completed == expected_count
        split_frozen = null_audit_split_frozen(
            rows,
            private_manifest,
            expected_count,
            audit_sha256,
        )
        all_frozen = all_frozen and split_frozen
        all_human_complete = all_human_complete and human_complete
        malformed = malformed or len(rows) != expected_count
        summaries[split] = {
            "expected_rows": expected_count,
            "actual_rows": len(rows),
            "two_person_confirmed_rows": completed,
            "manifest_frozen": split_frozen,
            "audit_sha256": audit_sha256 or None,
        }
    if malformed:
        status = "failed"
    elif all_frozen:
        status = "passed"
    elif all_human_complete:
        status = "pending_freeze"
    else:
        status = "pending_human"
    return {"status": status, "splits": summaries}


def inspect_rule_snapshot() -> dict[str, Any]:
    snapshot_path = (
        EXPERIMENT_ROOT
        / "llm_compiler_v0.2"
        / "generated"
        / "frozen"
        / "rule-baseline-development.json"
    )
    if not snapshot_path.exists():
        return {
            "status": "missing",
            "reason": "development null audit must freeze before Rule snapshot",
        }
    try:
        require_rule_snapshot_unchanged(
            snapshot_path,
            CONFIG_PATH,
            CONTRACT_PATH,
        )
    except (OSError, KeyError, TypeError, ValueError) as error:
        return {"status": "failed", "reason": str(error)}
    return {
        "status": "passed",
        "snapshot_sha256": sha256_file(snapshot_path),
    }


def inspect_dependency_isolation() -> dict[str, Any]:
    installed = [
        name
        for name in FORBIDDEN_INFERENCE_PACKAGES
        if importlib.util.find_spec(name) is not None
    ]
    loaded = [
        name
        for name in FORBIDDEN_INFERENCE_PACKAGES
        if name in sys.modules
    ]
    local_cache_paths = [
        EXPERIMENT_ROOT.parent / ".venv-llm-phase1",
        EXPERIMENT_ROOT / "llm_compiler_v0.2" / "models",
        EXPERIMENT_ROOT / "llm_compiler_v0.2" / "generated" / "models",
    ]
    present_cache_paths = [
        str(path.relative_to(EXPERIMENT_ROOT.parent))
        for path in local_cache_paths
        if path.exists()
    ]
    runtime = load_json(CONFIG_PATH).get("runtime") or {}
    runtime_closed = not any(bool(value) for value in runtime.values())
    passed = not installed and not loaded and not present_cache_paths and runtime_closed
    return {
        "status": "passed" if passed else "failed",
        "packages_checked": list(FORBIDDEN_INFERENCE_PACKAGES),
        "installed": installed,
        "loaded": loaded,
        "local_model_or_venv_paths": present_cache_paths,
        "runtime_authorizations_all_false": runtime_closed,
    }


def inspect_forbidden_file_diff() -> dict[str, Any]:
    pathspecs = (
        "09-experiments/scripts/run_mvp.py",
        "09-experiments/real_cases",
        "08-writing/paper-main*",
        "08-writing/patent*",
    )
    command = ["git", "diff", "--name-only", "--", *pathspecs]
    completed = subprocess.run(
        command,
        cwd=EXPERIMENT_ROOT.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    changed = [line for line in completed.stdout.splitlines() if line.strip()]
    return {
        "status": (
            "passed" if completed.returncode == 0 and not changed else "failed"
        ),
        "changed_files": changed,
    }


def find_model_output_files(generated_root: Path) -> list[str]:
    generated_root = Path(generated_root)
    files = []
    for directory_name in ("runs", "g2-audit"):
        directory = generated_root / directory_name
        if directory.exists():
            for path in directory.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(generated_root)
                if (
                    directory_name == "runs"
                    and len(relative.parts) > 1
                    and relative.parts[1].startswith("rule-development")
                ):
                    continue
                files.append(relative.as_posix())
    return sorted(files)


def generate_pre_model_readiness(output_path: Path) -> dict[str, Any]:
    output_path = Path(output_path)
    if output_path.exists():
        raise ValueError(f"refusing to overwrite readiness evidence: {output_path}")
    generated_root = EXPERIMENT_ROOT / "llm_compiler_v0.2" / "generated"
    bundle_errors = {
        split: scan_packet_bundle(generated_root / split)
        for split in ("development", "test")
    }
    prompt_errors = validate_prompt_config_lock(
        generated_root / "frozen" / "prompt-config-lock.json"
    )
    model_output_files = find_model_output_files(generated_root)
    checks = {
        "targeted_tests": run_targeted_pre_model_tests(),
        "public_private_scan": {
            "status": (
                "passed" if not any(bundle_errors.values()) else "failed"
            ),
            "errors": bundle_errors,
        },
        "prompt_config_lock": {
            "status": "passed" if not prompt_errors else "failed",
            "errors": prompt_errors,
        },
        "test_bundle_shape": inspect_test_bundle_shape(),
        "dependency_isolation": inspect_dependency_isolation(),
        "no_model_output": {
            "status": "passed" if not model_output_files else "failed",
            "files": model_output_files,
        },
        "forbidden_file_diff": inspect_forbidden_file_diff(),
        "null_construction_audit": inspect_null_construction_audits(),
        "rule_baseline_snapshot": inspect_rule_snapshot(),
    }
    report = assemble_pre_model_readiness(checks)
    report.update(
        {
            "generated_at_utc": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "authorized_scope": ["RQ1", "RQ5"],
            "paper_a_isolated": True,
            "model_output_exists": bool(model_output_files),
            "model_output_files": model_output_files,
            "implementation_sha256": {
                "run_llm_phase1.py": sha256_file(RUNNER_PATH),
                "test_llm_phase1_validation.py": sha256_file(
                    EXPERIMENT_ROOT / "tests" / "test_llm_phase1_validation.py"
                ),
            },
            "phase2_authorized": False,
            "phase3_authorized": False,
            "g2_failure_paper_form": "negative_evaluation_or_interface_pilot",
        }
    )
    write_json(output_path, report)
    return report


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = first_string(value.get("string"), value.get("value"))
            if nested:
                return nested
    return None


def process_from_command_line(value: Any) -> str | None:
    command_line = first_string(value)
    if not command_line:
        return None
    text = command_line.strip()
    if text.startswith('"'):
        closing = text.find('"', 1)
        if closing > 1:
            return text[1:closing]
    return text.split(None, 1)[0] if text else None


def entity_type_for(value: str, hint: str = "") -> str:
    folded_hint = hint.casefold()
    folded = value.casefold()
    if "ip" in folded_hint or resembles_ip(value):
        return "ip"
    if any(token in folded_hint for token in ("file", "path", "key")):
        return "registry_key" if "key" in folded_hint else "file"
    if "host" in folded_hint or "computer" in folded_hint:
        return "host"
    if "user" in folded_hint or "principal" in folded_hint:
        return "user"
    if "command" in folded_hint or folded.startswith(("cmd ", "powershell ")):
        return "command"
    return "process"


def resembles_ip(value: str) -> bool:
    parts = value.split(":", 1)[0].split(".")
    return len(parts) == 4 and all(part.isdigit() for part in parts)


def entity(value: str | None, hint: str = "") -> dict[str, str] | None:
    if not value:
        return None
    return {"entity_type": entity_type_for(value, hint), "value": value}


def node_entity(node: Any, role: str) -> dict[str, str] | None:
    if not isinstance(node, dict):
        return None
    raw = node.get("raw") if isinstance(node.get("raw"), dict) else {}
    base = raw.get("baseObject") if isinstance(raw.get("baseObject"), dict) else {}
    base_properties = (
        (base.get("properties") or {}).get("map")
        if isinstance(base.get("properties"), dict)
        else {}
    ) or {}
    raw_properties = (
        (raw.get("properties") or {}).get("map")
        if isinstance(raw.get("properties"), dict)
        else {}
    ) or {}
    node_type = str(node.get("node_type") or raw.get("type") or role)
    if role == "process":
        process = process_from_command_line(raw.get("cmdLine"))
        if process:
            return entity(process, "process")
    candidates = (
        (node.get("path"), "path"),
        (node.get("cmd"), "command"),
        (node.get("src_addr"), "ip"),
        (node.get("dst_addr"), "ip"),
        (raw.get("path"), "path"),
        (raw.get("name"), node_type),
        (raw.get("remoteAddress"), "ip"),
        (raw_properties.get("exec"), "process"),
        (raw_properties.get("path"), "path"),
        (raw_properties.get("partial_path"), "path"),
        (raw_properties.get("address"), "ip"),
        (base.get("path"), "path"),
        (base.get("filename"), "file"),
        (base_properties.get("path"), "path"),
        (base_properties.get("filename"), "file"),
    )
    for value, hint in candidates:
        result = entity(first_string(value), str(hint))
        if result:
            return result
    return None


def operation_token(payload: dict[str, Any]) -> str | None:
    event = payload.get("event") if isinstance(payload.get("event"), dict) else payload
    if event.get("event_type") or event.get("operation"):
        return str(event.get("event_type") or event.get("operation")).upper()
    if event.get("object") and event.get("action"):
        return f"{event['object']}:{event['action']}".upper()
    if event.get("EventID") is not None:
        return f"WINDOWS:{event['EventID']}".upper()
    lead = payload.get("lead") if isinstance(payload.get("lead"), dict) else None
    if lead:
        artifact = lead.get("artifact") if isinstance(lead.get("artifact"), dict) else {}
        if artifact.get("action") == "block" or lead.get("block"):
            return "WITFOO:BLOCK"
        for field in ("eventcode", "event_id", "EventID"):
            if artifact.get(field) is not None:
                return f"WITFOO:{artifact[field]}".upper()
    return None


def payload_entities(
    payload: dict[str, Any],
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    if isinstance(payload.get("resolved_src_node"), dict):
        return (
            node_entity(payload["resolved_src_node"], "process"),
            node_entity(payload.get("resolved_dst_node"), "object"),
        )
    resolved = payload.get("resolved_nodes")
    if isinstance(resolved, dict):
        subject = node_entity(resolved.get("subject_uuid"), "process")
        object_value = node_entity(
            resolved.get("predicate_object_uuid")
            or resolved.get("predicate_object_2_uuid"),
            "object",
        )
        if subject and object_value:
            return subject, object_value
    else:
        subject = None
        object_value = None

    event = payload.get("event") if isinstance(payload.get("event"), dict) else payload
    raw = event.get("raw") if isinstance(event.get("raw"), dict) else {}
    raw_properties = (
        (raw.get("properties") or {}).get("map")
        if isinstance(raw.get("properties"), dict)
        else {}
    ) or {}
    properties = event.get("properties") if isinstance(event.get("properties"), dict) else {}
    subject_fields = (
        (raw_properties.get("exec"), "process"),
        (process_from_command_line(raw_properties.get("cmdLine")), "process"),
        (event.get("process"), "process"),
        (properties.get("image_path"), "process"),
        (properties.get("command_line"), "command"),
        (event.get("Image"), "process"),
        (event.get("ParentProcessName"), "process"),
        (event.get("SubjectUserName"), "user"),
        (event.get("Computer"), "host"),
    )
    object_fields = (
        (raw.get("predicateObjectPath"), "path"),
        (raw_properties.get("partial_path"), "path"),
        (raw_properties.get("path"), "path"),
        (raw_properties.get("address"), "ip"),
        (event.get("path"), "path"),
        (properties.get("file_path"), "file"),
        (properties.get("path"), "path"),
        (properties.get("key"), "key"),
        (properties.get("dest_ip") or properties.get("dst_ip"), "ip"),
        (event.get("TargetFilename"), "file"),
        (event.get("NewProcessName"), "process"),
        (event.get("ScriptBlockText"), "command"),
    )
    subject = subject or next(
        (
            result
            for value, hint in subject_fields
            if (result := entity(first_string(value), hint))
        ),
        None,
    )
    object_value = object_value or next(
        (
            result
            for value, hint in object_fields
            if (result := entity(first_string(value), hint))
        ),
        None,
    )
    if subject and object_value:
        return subject, object_value

    lead = payload.get("lead") if isinstance(payload.get("lead"), dict) else None
    if lead:
        artifact = lead.get("artifact") if isinstance(lead.get("artifact"), dict) else {}
        subject = entity(
            first_string(artifact.get("clientip"), artifact.get("username")),
            "ip" if artifact.get("clientip") else "user",
        )
        object_value = entity(
            first_string(artifact.get("serverip"), artifact.get("senderhost")),
            "ip" if artifact.get("serverip") else "host",
        )
    return subject, object_value


def operation_map(config_path: Path = CONFIG_PATH) -> dict[str, str]:
    config = load_json(config_path)
    return {
        str(key).upper(): str(value)
        for key, value in config["rule_baseline"]["operation_map"].items()
    }


def rule_compile(packet: dict[str, Any]) -> dict[str, Any]:
    mapping = operation_map()
    candidates = []
    for record in packet.get("records", []):
        token = operation_token(record["source_payload"])
        predicate = mapping.get(str(token).upper()) if token else None
        subject, object_value = payload_entities(record["source_payload"])
        if not predicate or not subject or not object_value:
            continue
        output_index = len(candidates)
        candidate = {
            "candidate_claim_id": derive_candidate_claim_id(
                packet["request_id"], "rule_compiler", 0, output_index
            ),
            "source_type": record["source_type"],
            "subject": subject,
            "predicate": predicate,
            "object": object_value,
            "source_pointer": dict(record["source_pointer"]),
        }
        if not _VALIDATOR.validate_candidate(
            candidate,
            packet,
            "rule_compiler",
            0,
            output_index,
        ):
            candidates.append(candidate)
    return {
        "request_id": packet["request_id"],
        "condition_id": "rule_compiler",
        "attempt_index": 0,
        "status": "completed" if candidates else "abstain",
        "candidate_claims": candidates,
        "telemetry": {
            "latency_ms": 0.0,
            "peak_vram_mb": 0,
            "input_tokens": None,
            "output_tokens": None,
            "error_code": None,
        },
    }


RULE_FINGERPRINT_FUNCTIONS = (
    first_string,
    process_from_command_line,
    resembles_ip,
    entity_type_for,
    entity,
    node_entity,
    operation_token,
    payload_entities,
    rule_compile,
)


def rule_implementation_sha256(config_path: Path) -> str:
    payload = {
        "version": RULE_IMPLEMENTATION_VERSION,
        "operation_map": operation_map(config_path),
        "functions": [inspect.getsource(function) for function in RULE_FINGERPRINT_FUNCTIONS],
    }
    return sha256_value(payload)


def as_value(value_or_path: Any) -> Any:
    if isinstance(value_or_path, Path):
        return load_json(value_or_path)
    return value_or_path


def compiler_result_schema_valid(
    result: dict[str, Any],
    packet: dict[str, Any],
) -> bool:
    required = {
        "request_id",
        "condition_id",
        "attempt_index",
        "status",
        "candidate_claims",
        "telemetry",
    }
    if set(result) != required:
        return False
    if result.get("request_id") != packet.get("request_id"):
        return False
    if result.get("condition_id") != "rule_compiler":
        return False
    if result.get("attempt_index") != 0:
        return False
    if result.get("status") not in {"completed", "abstain"}:
        return False
    candidates = result.get("candidate_claims")
    if not isinstance(candidates, list):
        return False
    return not any(
        _VALIDATOR.validate_candidate(
            candidate,
            packet,
            "rule_compiler",
            0,
            output_index,
        )
        for output_index, candidate in enumerate(candidates)
    )


def run_rule_development_bundle(
    bundle_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    bundle_dir = Path(bundle_dir)
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"refusing to overwrite non-empty Rule run: {output_dir}")

    public_manifest_path = bundle_dir / "public" / "input_manifest.json"
    private_manifest_path = bundle_dir / "private" / "gold_manifest.json"
    public_manifest = load_json(public_manifest_path)
    private_manifest = load_json(private_manifest_path)
    if public_manifest.get("split") != "development":
        raise ValueError("Rule baseline may run on development split only")
    audit = private_manifest.get("null_construction_audit") or {}
    if audit.get("status") != "frozen":
        raise ValueError("development null construction audit is not frozen")
    if private_manifest.get("public_input_manifest_sha256") != sha256_file(
        public_manifest_path
    ):
        raise ValueError("public/private development manifest hash mismatch")

    public_rows = read_jsonl_gz(
        bundle_dir / "public" / "context_packets.jsonl.gz"
    )
    private_rows = read_jsonl_gz(
        bundle_dir / "private" / "observation_gold.jsonl.gz"
    )
    if [row.get("request_id") for row in public_rows] != [
        row.get("request_id") for row in private_rows
    ]:
        raise ValueError("public/private Rule input ordering mismatch")

    rows = []
    for packet, private_gold in zip(public_rows, private_rows):
        result = rule_compile(packet)
        admission = _VALIDATOR.admit_candidates(result, packet)
        scoring_packet = dict(packet)
        scoring_packet["compiler_status"] = result["status"]
        score = _SCORER.score_project_gold_packet(
            scoring_packet,
            admission["admitted_claims"],
            private_gold,
        )
        rows.append(
            {
                "request_id": packet["request_id"],
                "case_id": packet["case_id"],
                "packet_role": packet["packet_role"],
                "schema_valid": compiler_result_schema_valid(result, packet),
                "project_gold_packet_agreement": score[
                    "project_gold_packet_agreement"
                ],
                "score": score,
                "admission": admission,
                "result": result,
            }
        )

    run_manifest = {
        "status": "completed_pre_model_rule_run",
        "split": "development",
        "packet_count": len(rows),
        "positive_count": sum(row["packet_role"] == "positive" for row in rows),
        "null_count": sum(row["packet_role"] == "null" for row in rows),
        "agreement_count": sum(
            row["project_gold_packet_agreement"] == 1.0 for row in rows
        ),
        "input_manifest_sha256": sha256_file(public_manifest_path),
        "null_construction_audit": dict(audit),
        "rule_implementation_sha256": rule_implementation_sha256(CONFIG_PATH),
        "rule_results_sha256": sha256_value(rows),
    }
    write_json(output_dir / "rule_results.json", rows)
    write_json(output_dir / "run_manifest.json", run_manifest)
    return run_manifest


def freeze_rule_snapshot(
    config_path,
    contract_path,
    development_manifest,
    rule_results,
    output_path,
):
    config_path = Path(config_path)
    contract_path = Path(contract_path)
    output_path = Path(output_path)
    if output_path.exists():
        raise ValueError(f"refusing to overwrite rule baseline snapshot: {output_path}")
    manifest = as_value(development_manifest)
    rows = as_value(rule_results)
    if manifest.get("split") != "development":
        raise ValueError("rule baseline snapshot requires development split")
    audit = manifest.get("null_construction_audit") or {}
    if audit.get("status") != "frozen":
        raise ValueError("development null construction audit is not frozen")
    if len(rows) != int(manifest.get("packet_count") or 0):
        raise ValueError("rule result count does not match development manifest")

    positives = [row for row in rows if row.get("packet_role") == "positive"]
    nulls = [row for row in rows if row.get("packet_role") == "null"]
    claim_counts = [
        len((row.get("result") or {}).get("candidate_claims") or []) for row in rows
    ]
    positive_claiming = sum(
        bool((row.get("result") or {}).get("candidate_claims")) for row in positives
    )
    null_claiming = sum(
        bool((row.get("result") or {}).get("candidate_claims")) for row in nulls
    )
    strength_pass = positive_claiming > 0 and null_claiming < len(nulls)
    distribution = Counter(str(value) for value in claim_counts)
    snapshot = {
        "status": (
            "frozen_before_any_llm_output"
            if strength_pass
            else "failed_before_any_llm_output"
        ),
        "split": "development",
        "packet_count": len(rows),
        "positive_count": len(positives),
        "null_count": len(nulls),
        "schema_valid_rate": sum(bool(row.get("schema_valid")) for row in rows)
        / len(rows),
        "claim_count_distribution": dict(sorted(distribution.items())),
        "abstain_rate": sum(
            (row.get("result") or {}).get("status") == "abstain" for row in rows
        )
        / len(rows),
        "project_gold_packet_agreement": sum(
            float(row.get("project_gold_packet_agreement") or 0.0) for row in rows
        )
        / len(rows),
        "baseline_strength_gate": "passed" if strength_pass else "failed",
        "config_sha256": sha256_file(config_path),
        "contract_sha256": sha256_file(contract_path),
        "runner_sha256": rule_implementation_sha256(config_path),
        "development_input_manifest_sha256": manifest[
            "input_manifest_sha256"
        ],
        "rule_results_sha256": sha256_value(rows),
        "null_construction_audit_sha256": audit["audit_sha256"],
    }
    write_json(output_path, snapshot)
    output_path.with_suffix(".sha256").write_text(
        sha256_file(output_path) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if not strength_pass:
        raise ValueError("rule baseline strength gate failed")
    return snapshot


def require_rule_snapshot_unchanged(
    snapshot_path,
    config_path,
    contract_path,
) -> None:
    snapshot_path = Path(snapshot_path)
    config_path = Path(config_path)
    contract_path = Path(contract_path)
    if not snapshot_path.exists():
        raise ValueError("rule baseline snapshot is missing")
    snapshot = load_json(snapshot_path)
    if snapshot.get("baseline_strength_gate") != "passed":
        raise ValueError("rule baseline strength gate is not passed")
    expected = {
        "config_sha256": sha256_file(config_path),
        "contract_sha256": sha256_file(contract_path),
        "runner_sha256": rule_implementation_sha256(config_path),
    }
    mismatches = [
        key for key, value in expected.items() if snapshot.get(key) != value
    ]
    if mismatches:
        raise ValueError(f"rule baseline snapshot hash mismatch: {mismatches}")
    if snapshot.get("status") != "frozen_before_any_llm_output":
        raise ValueError("rule baseline snapshot status is not frozen")


def preflight_llm_backend(snapshot_path, config_path, contract_path) -> None:
    require_rule_snapshot_unchanged(snapshot_path, config_path, contract_path)


def run_condition(
    config,
    packet,
    condition_id,
    backend,
    attempt_index=0,
):
    if condition_id not in config.get("conditions", {}):
        raise ValueError(f"unknown condition: {condition_id}")
    if condition_id == "rule_compiler" and backend == "rule":
        result = rule_compile(packet)
        result["attempt_index"] = int(attempt_index)
        return result, {
            "condition_id": condition_id,
            "attempt_index": int(attempt_index),
            "result_sha256": sha256_value(result),
        }
    if isinstance(backend, StubBackend):
        if condition_id in {"general_compiler", "security_compiler"}:
            return run_compiler(packet, condition_id, backend, attempt_index)
        if condition_id == "general_structured":
            return run_structured(packet, backend, attempt_index)
        if condition_id == "general_direct":
            return run_direct(packet, backend, attempt_index)
    raise ValueError("model backends remain unauthorized before the Rule snapshot Gate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Project05 LLM Phase 1 conditions.")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--split", choices=("development", "test"))
    parser.add_argument("--condition")
    parser.add_argument("--backend")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--freeze-rule-snapshot", type=Path)
    parser.add_argument("--rule-run", type=Path)
    parser.add_argument("--freeze-prompt-config-lock", type=Path)
    parser.add_argument("--pre-model-readiness", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.freeze_prompt_config_lock:
        frozen = freeze_prompt_config_lock(args.freeze_prompt_config_lock)
        print(json.dumps(frozen, ensure_ascii=False, sort_keys=True))
        raise SystemExit(0)
    if args.pre_model_readiness:
        readiness = generate_pre_model_readiness(args.pre_model_readiness)
        print(json.dumps(readiness, ensure_ascii=False, sort_keys=True))
        raise SystemExit(0)
    if args.freeze_rule_snapshot:
        if args.rule_run is None:
            raise SystemExit("--freeze-rule-snapshot requires --rule-run")
        snapshot = freeze_rule_snapshot(
            args.config,
            CONTRACT_PATH,
            args.rule_run / "run_manifest.json",
            args.rule_run / "rule_results.json",
            args.freeze_rule_snapshot,
        )
        print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True))
        raise SystemExit(0)
    if args.condition == "rule_compiler" and args.backend == "rule":
        if args.split != "development" or args.output is None:
            raise SystemExit(
                "formal Rule run requires --split development and --output"
            )
        bundle_dir = (
            EXPERIMENT_ROOT
            / "llm_compiler_v0.2"
            / "generated"
            / "development"
        )
        run = run_rule_development_bundle(bundle_dir, args.output)
        print(json.dumps(run, ensure_ascii=False, sort_keys=True))
        raise SystemExit(0)
    raise SystemExit(
        "No authorized pre-model action selected; model backends remain blocked."
    )
