"""Fail-closed bounded auditor for the identity-verified LO2v2 index.

This module is dormant by default. ``--mode plan`` verifies only the pinned
local Python reader and never stats or opens the JSON target. ``--mode
execute`` additionally requires a separate authority JSON that pins the
current script and audit-contract hashes and matches every execution cap.

Execution reads the single identity-verified JSON object only in memory,
persists no raw key, value, run identifier, test identity, path, timestamp, or
pointer, and writes aggregate sanitized results only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


class AuditBlocked(RuntimeError):
    """A fail-closed condition represented by a non-sensitive reason code."""


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
SOURCE_PATH = (
    SCRIPT_PATH.parent
    / "local_audit_cache"
    / "lo2v2-bounded-v0.1"
    / "raw"
    / "LO2v2_index.json"
)
CONTRACT_PATH = (
    REPO_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-lo2v2-index-json-reader-privacy-notice-schema-"
    "manifest-lineage-label-v1-v2-pointer-audit-contract-v0.1-20260723.json"
)
RESULT_JSON_PATH = (
    REPO_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-result-v0.1-20260723.json"
)
RESULT_MD_PATH = RESULT_JSON_PATH.with_suffix(".md")

TARGET_ID = "lo2v2_index_json"
EXPECTED_SOURCE_BYTES = 31_028_530
EXPECTED_SOURCE_MD5 = "2efcff67820ba1df40fae362919271eb"

EXPECTED_PYTHON_VERSION = (
    "3.11.15 (main, Jun 23 2026, 15:20:37) [MSC v.1944 64 bit (AMD64)]"
)
EXPECTED_VENV_EXECUTABLE = (
    Path(os.environ["LOCALAPPDATA"])
    / "hermes"
    / "hermes-agent"
    / "venv"
    / "Scripts"
    / "python.exe"
)
EXPECTED_VENV_EXECUTABLE_BYTES = 45_568
EXPECTED_VENV_EXECUTABLE_SHA256 = (
    "0cf37e7be6ee71edef78e6c81f7dcef58237b204af36d6e83393c96538a52372"
)
EXPECTED_BASE_EXECUTABLE = (
    Path(os.environ["APPDATA"])
    / "uv"
    / "python"
    / "cpython-3.11-windows-x86_64-none"
    / "python.exe"
)
EXPECTED_BASE_EXECUTABLE_BYTES = 91_648
EXPECTED_BASE_EXECUTABLE_SHA256 = (
    "ae7e969410d751d010c2ca03394fe5c53230fbf48ca7d368b897e455eca14fba"
)
EXPECTED_PYTHON_DLL = EXPECTED_BASE_EXECUTABLE.parent / "python311.dll"
EXPECTED_PYTHON_DLL_BYTES = 5_842_944
EXPECTED_PYTHON_DLL_SHA256 = (
    "e1b53c741751563eca9eac70378de5be36994adac8c27e8ec375971579e23b50"
)
EXPECTED_JSON_MODULE = (
    EXPECTED_BASE_EXECUTABLE.parent / "Lib" / "json" / "__init__.py"
)
EXPECTED_JSON_MODULE_BYTES = 14_020
EXPECTED_JSON_MODULE_SHA256 = (
    "d5d41e2c29049515d295d81a6d40b4890fbec8d8482cfb401630f8ef2f77e4d5"
)
EXPECTED_HASHLIB_MODULE = EXPECTED_BASE_EXECUTABLE.parent / "Lib" / "hashlib.py"
EXPECTED_HASHLIB_MODULE_BYTES = 11_765
EXPECTED_HASHLIB_MODULE_SHA256 = (
    "e2bffb462e4d43e6637b9450e259e8ba2a56626ba3037d68aa1cee68b3f61d4a"
)
EXPECTED_RE_MODULE = EXPECTED_BASE_EXECUTABLE.parent / "Lib" / "re" / "__init__.py"
EXPECTED_RE_MODULE_BYTES = 15_889
EXPECTED_RE_MODULE_SHA256 = (
    "029ead61f362489e9bb034f4c2503abee95462056541e9ad07715de3c353b0da"
)

MAXIMUM_WALL_SECONDS = 300
MAXIMUM_INPUT_BYTES = EXPECTED_SOURCE_BYTES
MAXIMUM_JSON_DEPTH = 32
MAXIMUM_TOTAL_NODES = 2_000_000
MAXIMUM_DICT_KEYS_PER_OBJECT = 4_096
MAXIMUM_LIST_ITEMS_PER_ARRAY = 200_000
MAXIMUM_SCALAR_STRING_UTF8_BYTES = 262_144
MAXIMUM_RUN_CANDIDATES = 4_096
MAXIMUM_RESULT_BYTES = 262_144

RUN_IDENTIFIER_PATTERN = re.compile(r"^LO2_run_[0-9]{9,}$")
NOTICE_KEY_TOKENS = (
    "license",
    "licence",
    "notice",
    "copyright",
    "copying",
    "readme",
)
LABEL_OR_SUPERVISION_TOKENS = (
    "correct",
    "error",
    "failure",
    "anomaly",
    "expected",
    "response",
    "outcome",
    "status",
    "label",
    "ground_truth",
    "task",
    "test",
)
PRIVACY_OR_IDENTIFIER_TOKENS = (
    "password",
    "passwd",
    "credential",
    "authorization",
    "secret",
    "cookie",
    "token",
    "username",
    "email",
    "header",
    "url",
    "ip",
    "host",
    "container",
    "service",
    "path",
    "file",
    "trace",
)
TEST_CONTAINER_TOKENS = ("test", "task")


def _digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def _verify_file_identity(
    path: Path, expected_bytes: int, expected_sha256: str, code: str
) -> dict[str, object]:
    if not path.is_file():
        raise AuditBlocked(f"{code}_missing")
    actual_bytes = path.stat().st_size
    if actual_bytes != expected_bytes:
        raise AuditBlocked(f"{code}_size_mismatch")
    actual_sha256 = _digest_file(path, "sha256")
    if actual_sha256 != expected_sha256:
        raise AuditBlocked(f"{code}_sha256_mismatch")
    return {
        "component": code,
        "bytes": actual_bytes,
        "sha256": actual_sha256,
        "identity_gate_passed": True,
    }


def _verify_reader_identity() -> dict[str, object]:
    if sys.version != EXPECTED_PYTHON_VERSION:
        raise AuditBlocked("python_version_mismatch")
    if Path(sys.executable).resolve() != EXPECTED_VENV_EXECUTABLE.resolve():
        raise AuditBlocked("python_venv_executable_path_mismatch")
    if Path(getattr(sys, "_base_executable", "")).resolve() != (
        EXPECTED_BASE_EXECUTABLE.resolve()
    ):
        raise AuditBlocked("python_base_executable_path_mismatch")
    if Path(json.__file__).resolve() != EXPECTED_JSON_MODULE.resolve():
        raise AuditBlocked("json_module_path_mismatch")
    if Path(hashlib.__file__).resolve() != EXPECTED_HASHLIB_MODULE.resolve():
        raise AuditBlocked("hashlib_module_path_mismatch")
    if Path(re.__file__).resolve() != EXPECTED_RE_MODULE.resolve():
        raise AuditBlocked("re_module_path_mismatch")

    components = [
        _verify_file_identity(
            EXPECTED_VENV_EXECUTABLE,
            EXPECTED_VENV_EXECUTABLE_BYTES,
            EXPECTED_VENV_EXECUTABLE_SHA256,
            "venv_python_executable",
        ),
        _verify_file_identity(
            EXPECTED_BASE_EXECUTABLE,
            EXPECTED_BASE_EXECUTABLE_BYTES,
            EXPECTED_BASE_EXECUTABLE_SHA256,
            "base_python_executable",
        ),
        _verify_file_identity(
            EXPECTED_PYTHON_DLL,
            EXPECTED_PYTHON_DLL_BYTES,
            EXPECTED_PYTHON_DLL_SHA256,
            "python311_dll",
        ),
        _verify_file_identity(
            EXPECTED_JSON_MODULE,
            EXPECTED_JSON_MODULE_BYTES,
            EXPECTED_JSON_MODULE_SHA256,
            "stdlib_json_module",
        ),
        _verify_file_identity(
            EXPECTED_HASHLIB_MODULE,
            EXPECTED_HASHLIB_MODULE_BYTES,
            EXPECTED_HASHLIB_MODULE_SHA256,
            "stdlib_hashlib_module",
        ),
        _verify_file_identity(
            EXPECTED_RE_MODULE,
            EXPECTED_RE_MODULE_BYTES,
            EXPECTED_RE_MODULE_SHA256,
            "stdlib_re_module",
        ),
    ]
    return {
        "name": "CPython standard-library json/hashlib/re reader",
        "python_version": sys.version,
        "components": components,
        "identity_gate_passed": True,
    }


def _verify_execution_authority(authority_path: Path) -> dict[str, object]:
    if RESULT_JSON_PATH.exists() or RESULT_MD_PATH.exists():
        raise AuditBlocked("result_already_exists_execute_once_gate")
    if not authority_path.is_file():
        raise AuditBlocked("execution_authority_missing")
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    if authority.get("status") != "authorized_once":
        raise AuditBlocked("execution_authority_status_invalid")
    if authority.get("target_id") != TARGET_ID:
        raise AuditBlocked("execution_authority_target_mismatch")
    required_true = (
        "audit_execution_authorized",
        "json_open_authorized",
        "json_read_authorized",
        "json_parse_authorized",
        "label_scan_authorized",
        "v1_v2_digest_preparation_authorized",
        "pointer_probe_authorized",
    )
    if any(authority.get(key) is not True for key in required_true):
        raise AuditBlocked("execution_authority_scope_missing")
    if authority.get("automatic_retry_authorized") is not False:
        raise AuditBlocked("automatic_retry_boundary_missing")
    if authority.get("resume_authorized") is not False:
        raise AuditBlocked("resume_boundary_missing")

    expected_caps = {
        "maximum_wall_seconds": MAXIMUM_WALL_SECONDS,
        "maximum_input_bytes": MAXIMUM_INPUT_BYTES,
        "maximum_json_depth": MAXIMUM_JSON_DEPTH,
        "maximum_total_nodes": MAXIMUM_TOTAL_NODES,
        "maximum_dict_keys_per_object": MAXIMUM_DICT_KEYS_PER_OBJECT,
        "maximum_list_items_per_array": MAXIMUM_LIST_ITEMS_PER_ARRAY,
        "maximum_scalar_string_utf8_bytes": (
            MAXIMUM_SCALAR_STRING_UTF8_BYTES
        ),
        "maximum_run_candidates": MAXIMUM_RUN_CANDIDATES,
        "maximum_result_bytes": MAXIMUM_RESULT_BYTES,
    }
    if authority.get("caps") != expected_caps:
        raise AuditBlocked("execution_authority_caps_mismatch")

    actual_contract_sha256 = _digest_file(CONTRACT_PATH, "sha256")
    actual_script_sha256 = _digest_file(SCRIPT_PATH, "sha256")
    if authority.get("audit_contract_sha256") != actual_contract_sha256:
        raise AuditBlocked("execution_authority_contract_hash_mismatch")
    if authority.get("audit_script_sha256") != actual_script_sha256:
        raise AuditBlocked("execution_authority_script_hash_mismatch")

    return {
        "authority_file_sha256": _digest_file(authority_path, "sha256"),
        "contract_sha256": actual_contract_sha256,
        "script_sha256": actual_script_sha256,
        "execute_once_gate_passed": True,
    }


def _read_identity_verified_source() -> tuple[bytes, dict[str, object]]:
    if not SOURCE_PATH.is_file():
        raise AuditBlocked("source_missing")
    actual_bytes = SOURCE_PATH.stat().st_size
    if actual_bytes != EXPECTED_SOURCE_BYTES:
        raise AuditBlocked("source_size_mismatch")
    actual_md5 = _digest_file(SOURCE_PATH, "md5")
    if actual_md5 != EXPECTED_SOURCE_MD5:
        raise AuditBlocked("source_md5_mismatch")
    raw = SOURCE_PATH.read_bytes()
    if len(raw) != EXPECTED_SOURCE_BYTES:
        raise AuditBlocked("source_changed_after_identity_check")
    return raw, {
        "target_id": TARGET_ID,
        "source_key": "LO2v2_index.json",
        "bytes": actual_bytes,
        "md5": actual_md5,
        "identity_gate_passed": True,
    }


def _contains_token(value: str, tokens: Iterable[str]) -> bool:
    folded = value.casefold()
    return any(token in folded for token in tokens)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _aggregate_digest(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        encoded = value.encode("ascii")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _json_pointer(path: tuple[str | int, ...]) -> str:
    def encode(token: str | int) -> str:
        return str(token).replace("~", "~0").replace("/", "~1")

    return "".join(f"/{encode(token)}" for token in path)


def _resolve_path(root: Any, path: tuple[str | int, ...]) -> Any:
    current = root
    for token in path:
        if isinstance(current, dict) and isinstance(token, str):
            current = current[token]
        elif isinstance(current, list) and isinstance(token, int):
            current = current[token]
        else:
            raise AuditBlocked("pointer_path_resolution_failed")
    return current


def _inspect_json(root: Any, started: float) -> dict[str, object]:
    node_count = 0
    dict_count = 0
    list_count = 0
    scalar_count = 0
    key_count = 0
    maximum_depth_seen = 0
    maximum_string_bytes_seen = 0
    notice_key_match_count = 0
    label_surface_match_count = 0
    privacy_identifier_match_count = 0
    test_identity_candidate_count = 0
    schema_signatures: Counter[str] = Counter()
    list_length_histogram: Counter[int] = Counter()
    run_occurrences: list[tuple[str, str, tuple[str | int, ...], str]] = []
    run_locations: dict[str, set[str]] = defaultdict(set)
    run_test_container_lengths: dict[str, set[int]] = defaultdict(set)

    stack: list[tuple[Any, tuple[str | int, ...], int, str | None]] = [
        (root, (), 0, None)
    ]
    while stack:
        if time.monotonic() - started > MAXIMUM_WALL_SECONDS:
            raise AuditBlocked("wall_time_cap_exceeded")
        value, path, depth, inherited_run_digest = stack.pop()
        node_count += 1
        if node_count > MAXIMUM_TOTAL_NODES:
            raise AuditBlocked("total_node_cap_exceeded")
        if depth > MAXIMUM_JSON_DEPTH:
            raise AuditBlocked("json_depth_cap_exceeded")
        maximum_depth_seen = max(maximum_depth_seen, depth)

        if isinstance(value, dict):
            dict_count += 1
            if len(value) > MAXIMUM_DICT_KEYS_PER_OBJECT:
                raise AuditBlocked("dict_key_cap_exceeded")
            key_count += len(value)
            keys = [str(key) for key in value]
            schema_signatures[
                _aggregate_digest(_sha256_text(key) for key in sorted(keys))
            ] += 1

            local_run_digest = inherited_run_digest
            string_run_values = [
                item
                for item in value.values()
                if isinstance(item, str) and RUN_IDENTIFIER_PATTERN.fullmatch(item)
            ]
            if len(string_run_values) == 1:
                local_run_digest = _sha256_text(string_run_values[0])

            for key, child in value.items():
                encoded_key_bytes = len(key.encode("utf-8"))
                maximum_string_bytes_seen = max(
                    maximum_string_bytes_seen, encoded_key_bytes
                )
                if encoded_key_bytes > MAXIMUM_SCALAR_STRING_UTF8_BYTES:
                    raise AuditBlocked("key_string_byte_cap_exceeded")
                if _contains_token(key, NOTICE_KEY_TOKENS):
                    notice_key_match_count += 1
                if _contains_token(key, LABEL_OR_SUPERVISION_TOKENS):
                    label_surface_match_count += 1
                if _contains_token(key, PRIVACY_OR_IDENTIFIER_TOKENS):
                    privacy_identifier_match_count += 1
                if _contains_token(key, TEST_CONTAINER_TOKENS):
                    test_identity_candidate_count += 1

                child_path = path + (key,)
                child_run_digest = local_run_digest
                if RUN_IDENTIFIER_PATTERN.fullmatch(key):
                    child_run_digest = _sha256_text(key)
                    pointer_digest = _sha256_text(_json_pointer(child_path))
                    run_occurrences.append(
                        (child_run_digest, pointer_digest, child_path, "key")
                    )
                    run_locations[child_run_digest].add(pointer_digest)
                if (
                    child_run_digest is not None
                    and _contains_token(key, TEST_CONTAINER_TOKENS)
                    and isinstance(child, (dict, list))
                ):
                    run_test_container_lengths[child_run_digest].add(len(child))
                stack.append((child, child_path, depth + 1, child_run_digest))

        elif isinstance(value, list):
            list_count += 1
            if len(value) > MAXIMUM_LIST_ITEMS_PER_ARRAY:
                raise AuditBlocked("list_item_cap_exceeded")
            list_length_histogram[len(value)] += 1
            for index in range(len(value) - 1, -1, -1):
                stack.append(
                    (value[index], path + (index,), depth + 1, inherited_run_digest)
                )

        elif isinstance(value, str):
            scalar_count += 1
            encoded_value_bytes = len(value.encode("utf-8"))
            maximum_string_bytes_seen = max(
                maximum_string_bytes_seen, encoded_value_bytes
            )
            if encoded_value_bytes > MAXIMUM_SCALAR_STRING_UTF8_BYTES:
                raise AuditBlocked("scalar_string_byte_cap_exceeded")
            if _contains_token(value, LABEL_OR_SUPERVISION_TOKENS):
                label_surface_match_count += 1
            if _contains_token(value, PRIVACY_OR_IDENTIFIER_TOKENS):
                privacy_identifier_match_count += 1
            if RUN_IDENTIFIER_PATTERN.fullmatch(value):
                run_digest = _sha256_text(value)
                pointer_digest = _sha256_text(_json_pointer(path))
                run_occurrences.append((run_digest, pointer_digest, path, "value"))
                run_locations[run_digest].add(pointer_digest)
        else:
            scalar_count += 1

        if len(run_occurrences) > MAXIMUM_RUN_CANDIDATES:
            raise AuditBlocked("run_candidate_cap_exceeded")

    pointer_digests: list[str] = []
    pointer_round_trip_passed = True
    for run_digest, pointer_digest, path, occurrence_kind in run_occurrences:
        if occurrence_kind == "value":
            resolved = _resolve_path(root, path)
            if not isinstance(resolved, str) or _sha256_text(resolved) != run_digest:
                pointer_round_trip_passed = False
        else:
            if not path or not isinstance(path[-1], str):
                pointer_round_trip_passed = False
            else:
                parent = _resolve_path(root, path[:-1])
                if not isinstance(parent, dict) or path[-1] not in parent:
                    pointer_round_trip_passed = False
        candidate = json.dumps(
            {
                "artifact_md5": EXPECTED_SOURCE_MD5,
                "json_pointer_sha256": pointer_digest,
                "run_id_sha256": run_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        if candidate != json.dumps(
            json.loads(candidate), sort_keys=True, separators=(",", ":")
        ):
            pointer_round_trip_passed = False
        pointer_digests.append(_sha256_text(candidate))

    unique_run_digests = sorted(run_locations)
    runs_with_54_test_container = sum(
        1
        for digest in unique_run_digests
        if 54 in run_test_container_lengths.get(digest, set())
    )
    run_count_matches_curator = len(unique_run_digests) == 115
    one_location_per_run_candidate = all(
        len(locations) == 1 for locations in run_locations.values()
    )
    label_isolation_probe_passed = (
        label_surface_match_count == 0 and test_identity_candidate_count == 0
    )
    privacy_identifier_probe_passed = privacy_identifier_match_count == 0

    return {
        "bounded_parse": {
            "input_bytes": EXPECTED_SOURCE_BYTES,
            "maximum_input_bytes": MAXIMUM_INPUT_BYTES,
            "node_count": node_count,
            "node_cap": MAXIMUM_TOTAL_NODES,
            "dictionary_count": dict_count,
            "list_count": list_count,
            "scalar_count": scalar_count,
            "key_count": key_count,
            "maximum_depth_seen": maximum_depth_seen,
            "depth_cap": MAXIMUM_JSON_DEPTH,
            "maximum_scalar_string_bytes_seen": maximum_string_bytes_seen,
            "raw_key_value_or_path_persisted": False,
        },
        "notice": {
            "notice_key_match_count": notice_key_match_count,
            "raw_notice_text_persisted": False,
            "record_scope_license_closes_nested_rights": False,
            "nested_notice_gate_passed": False,
        },
        "schema": {
            "root_type": type(root).__name__,
            "root_member_count": len(root) if isinstance(root, (dict, list)) else 0,
            "schema_signature_count": len(schema_signatures),
            "distinct_list_length_count": len(list_length_histogram),
            "json_parse_passed": True,
            "full_semantic_schema_verified": False,
            "raw_schema_key_set_or_example_persisted": False,
        },
        "privacy": {
            "privacy_or_identifier_token_match_count": (
                privacy_identifier_match_count
            ),
            "privacy_identifier_probe_passed": privacy_identifier_probe_passed,
            "full_privacy_gate_passed": False,
            "raw_matching_key_or_value_persisted": False,
        },
        "label_isolation": {
            "label_or_supervision_token_match_count": label_surface_match_count,
            "test_or_task_identity_candidate_count": (
                test_identity_candidate_count
            ),
            "label_isolation_probe_passed": label_isolation_probe_passed,
            "initialization_row_leak_remediation_verified": False,
            "raw_test_task_label_or_value_persisted": False,
        },
        "manifest_lineage": {
            "run_candidate_occurrence_count": len(run_occurrences),
            "unique_run_candidate_count": len(unique_run_digests),
            "run_count_matches_curator_declared_115": run_count_matches_curator,
            "one_location_per_run_candidate": one_location_per_run_candidate,
            "run_candidates_with_54_item_test_container": (
                runs_with_54_test_container
            ),
            "all_115_runs_have_detected_54_item_test_container": (
                run_count_matches_curator and runs_with_54_test_container == 115
            ),
            "v2_run_digest_set_sha256": _aggregate_digest(unique_run_digests),
            "unique_completed_execution_globally_verified": False,
            "duplicate_retry_partial_and_repeated_system_policy_verified": False,
            "statistical_independence_verified": False,
            "family_credit": 0,
            "lineage_credit": 0,
            "sample_credit": 0,
            "quota_credit": 0,
        },
        "v1_v2_overlap": {
            "v2_run_digest_set_prepared": bool(unique_run_digests),
            "v1_artifact_or_run_digest_set_available": False,
            "comparison_performed": False,
            "exact_or_near_overlap_verified_absent": False,
            "overlap_gate_passed": False,
        },
        "pointer": {
            "candidate_shape": (
                "artifact_md5 + run_id_sha256 + json_pointer_sha256"
            ),
            "candidate_count": len(pointer_digests),
            "candidate_aggregate_sha256": _aggregate_digest(
                sorted(pointer_digests)
            ),
            "canonical_in_memory_round_trip_passed": pointer_round_trip_passed,
            "raw_json_pointer_or_run_identifier_persisted": False,
            "runtime_log_metric_or_trace_binding_verified": False,
            "normalization_to_source_round_trip_verified": False,
            "binding_status": "unbound",
            "pointer_binding_authorized": False,
        },
    }


def _parse_and_probe(raw: bytes) -> dict[str, object]:
    started = time.monotonic()
    if len(raw) > MAXIMUM_INPUT_BYTES:
        raise AuditBlocked("input_byte_cap_exceeded")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise AuditBlocked("invalid_utf8") from error
    try:
        root = json.loads(text)
    except json.JSONDecodeError as error:
        raise AuditBlocked("invalid_json") from error
    if not isinstance(root, (dict, list)):
        raise AuditBlocked("root_type_not_object_or_array")
    if time.monotonic() - started > MAXIMUM_WALL_SECONDS:
        raise AuditBlocked("wall_time_cap_exceeded")
    return _inspect_json(root, started)


def _result_status(probe: dict[str, object]) -> str:
    if not probe["label_isolation"]["label_isolation_probe_passed"]:
        return "fail_closed_protected_label_surface_detected"
    if not probe["privacy"]["privacy_identifier_probe_passed"]:
        return "fail_closed_privacy_or_identifier_surface_detected"
    if not probe["manifest_lineage"]["run_count_matches_curator_declared_115"]:
        return "hold_manifest_run_count_unclosed"
    return "bounded_probe_hold_notice_lineage_v1_v2_and_pointer_unclosed"


def _write_sanitized_result(result: dict[str, object]) -> None:
    serialized = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if len(serialized.encode("utf-8")) > MAXIMUM_RESULT_BYTES:
        raise AuditBlocked("result_byte_cap_exceeded")
    RESULT_JSON_PATH.write_text(serialized, encoding="utf-8")
    probe = result["probe"]
    markdown = f"""# LO2v2 index bounded audit result

Status: `{result['status']}`

| Gate | Result |
|---|---|
| Source identity | pass |
| Reader identity | pass |
| JSON parse | {str(probe['schema']['json_parse_passed']).lower()} |
| Unique run candidates | {probe['manifest_lineage']['unique_run_candidate_count']} |
| Curator 115-run count match | {str(probe['manifest_lineage']['run_count_matches_curator_declared_115']).lower()} |
| Label-isolation probe | {str(probe['label_isolation']['label_isolation_probe_passed']).lower()} |
| Privacy/identifier probe | {str(probe['privacy']['privacy_identifier_probe_passed']).lower()} |
| Nested-notice Gate | false |
| v1/v2 overlap Gate | false |
| Statistical independence | false |
| Pointer binding | unbound |
| Family / lineage / sample / quota credit | 0 / 0 / 0 / 0 |
| Source role / L2 Gate | false / false |

No raw JSON, key, value, run identifier, test or task identity, path, timestamp,
notice text, pointer, or local payload path is persisted.
"""
    if len(markdown.encode("utf-8")) > MAXIMUM_RESULT_BYTES:
        raise AuditBlocked("markdown_result_byte_cap_exceeded")
    RESULT_MD_PATH.write_text(markdown, encoding="utf-8")


def _write_sanitized_failure(reason_code: str) -> None:
    if RESULT_JSON_PATH.exists() or RESULT_MD_PATH.exists():
        return
    result = {
        "schema_version": (
            "project05-llm-editor-l2-lo2v2-index-bounded-audit-result-v0.1"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed_closed_terminal_no_automatic_retry",
        "target_id": TARGET_ID,
        "reason_code": reason_code,
        "content": {
            "raw_json_key_value_or_path_persisted": False,
            "run_or_test_identifier_persisted": False,
            "local_payload_path_persisted": False,
        },
        "scope": {
            "automatic_retry_authorized": False,
            "source_role_changed": False,
            "family_credit": 0,
            "lineage_credit": 0,
            "sample_credit": 0,
            "quota_credit": 0,
            "l2_gate_passed": False,
        },
    }
    serialized = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if len(serialized.encode("utf-8")) <= MAXIMUM_RESULT_BYTES:
        RESULT_JSON_PATH.write_text(serialized, encoding="utf-8")
        RESULT_MD_PATH.write_text(
            "# LO2v2 index bounded audit failure\n\n"
            "Status: `failed_closed_terminal_no_automatic_retry`\n\n"
            f"Reason code: `{reason_code}`\n\n"
            "No raw JSON, key, value, run or test identifier, pointer, or local "
            "payload path is persisted. No role or credit changed.\n",
            encoding="utf-8",
        )


def execute_audit(authority_path: Path) -> dict[str, object]:
    authority = _verify_execution_authority(authority_path)
    reader = _verify_reader_identity()
    raw, source = _read_identity_verified_source()
    probe = _parse_and_probe(raw)
    result: dict[str, object] = {
        "schema_version": (
            "project05-llm-editor-l2-lo2v2-index-bounded-audit-result-v0.1"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": _result_status(probe),
        "target_id": TARGET_ID,
        "authority": authority,
        "reader": reader,
        "source_identity": source,
        "probe": probe,
        "scope": {
            "json_opened": True,
            "json_parsed_in_memory": True,
            "raw_json_key_value_or_path_persisted": False,
            "run_or_test_identifier_persisted": False,
            "label_or_ground_truth_used_as_supervision": False,
            "training_sample_generated": False,
            "effective_catalog_written": False,
            "source_role_changed": False,
            "family_credit": 0,
            "lineage_credit": 0,
            "sample_credit": 0,
            "quota_credit": 0,
            "baseline_or_fine_tuning_run": False,
            "kernel_gamma_or_m3_modified": False,
            "l2_gate_passed": False,
        },
    }
    _write_sanitized_result(result)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("plan", "execute"), required=True)
    parser.add_argument("--authority-json", type=Path)
    args = parser.parse_args(argv)
    try:
        reader = _verify_reader_identity()
        if args.mode == "plan":
            print(
                json.dumps(
                    {
                        "status": "plan_reader_identity_passed_source_not_touched",
                        "reader_identity_gate_passed": (
                            reader["identity_gate_passed"]
                        ),
                        "source_statted_or_opened": False,
                        "json_opened": False,
                        "json_parsed": False,
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.authority_json is None:
            raise AuditBlocked("execute_requires_separate_authority_json")
        result = execute_audit(args.authority_json.resolve())
        print(json.dumps({"status": result["status"]}, sort_keys=True))
        return 0
    except (AuditBlocked, OSError, ValueError) as error:
        reason = str(error) if isinstance(error, AuditBlocked) else "reader_failure"
        if args.mode == "execute":
            _write_sanitized_failure(reason)
        print(
            json.dumps({"status": "blocked", "reason_code": reason}),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
