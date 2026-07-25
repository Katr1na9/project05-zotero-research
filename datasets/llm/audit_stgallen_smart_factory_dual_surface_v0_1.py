"""Dormant fail-closed auditor for the verified St.Gallen dual surface.

``--mode plan`` verifies only the pinned CPython reader identity and never
stats or opens either acquired surface. ``--mode execute`` additionally
requires a separate authority JSON that simultaneously names both targets,
pins this script and the audit-contract hashes, and matches every cap.

An authorized execution keeps the protected Camunda manifest and the sensor
surface physically separate. Raw values, keys, identifiers, timestamps,
records, JSON pointers, byte offsets, paths, and notices are never persisted.
Only aggregate counts, digests, boolean gates, and non-sensitive reason codes
may be written.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import os
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


class AuditBlocked(RuntimeError):
    """A fail-closed condition represented by a non-sensitive reason code."""


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
RAW_ROOT = (
    SCRIPT_PATH.parent
    / "local_audit_cache"
    / "stgallen-smart-factory-bounded-v0.1"
    / "raw"
)
MANIFEST_PATH = RAW_ROOT / "protected_manifest" / "camunda-process.json"
SENSOR_PATH = (
    RAW_ROOT
    / "model_candidate"
    / "training_tenhertz_log_20230411-095748.txt"
)
CONTRACT_PATH = (
    REPO_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-stgallen-smart-factory-dual-reader-privacy-notice-"
    "schema-gt-exclusion-manifest-lineage-binding-pointer-audit-contract-"
    "v0.1-20260724.json"
)
RESULT_JSON_PATH = (
    REPO_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-stgallen-smart-factory-dual-surface-bounded-audit-"
    "result-v0.1-20260724.json"
)
RESULT_MD_PATH = RESULT_JSON_PATH.with_suffix(".md")

TARGET_IDS = (
    "stgallen_camunda_process_manifest_surface",
    "stgallen_training_sensor_log_surface",
)
MANIFEST_EXPECTED_BYTES = 111_548
MANIFEST_EXPECTED_MD5 = "a56fb7b92ad99a8106ff3c75a2d94c6f"
SENSOR_EXPECTED_BYTES = 59_901_231
SENSOR_EXPECTED_MD5 = "1b310fe1bbbbe53511db015375df8a41"

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

CAPS = {
    "maximum_wall_seconds": 300,
    "maximum_manifest_source_bytes": MANIFEST_EXPECTED_BYTES,
    "maximum_sensor_source_bytes": SENSOR_EXPECTED_BYTES,
    "maximum_total_source_bytes_read": 153_579_990,
    "maximum_manifest_json_depth": 32,
    "maximum_manifest_total_nodes": 200_000,
    "maximum_manifest_dict_keys_per_object": 1_024,
    "maximum_manifest_list_items_per_array": 100_000,
    "maximum_manifest_scalar_string_utf8_bytes": 65_536,
    "maximum_manifest_instance_candidates": 64,
    "maximum_sensor_lines": 2_000_000,
    "maximum_sensor_line_bytes": 1_048_576,
    "maximum_sensor_json_depth_per_record": 16,
    "maximum_sensor_nodes_per_record": 4_096,
    "maximum_sensor_total_nodes": 10_000_000,
    "maximum_sensor_dict_keys_per_object": 512,
    "maximum_sensor_list_items_per_array": 4_096,
    "maximum_sensor_scalar_string_utf8_bytes": 65_536,
    "maximum_pointer_round_trip_records": 32,
    "maximum_result_bytes_per_file": 262_144,
    "maximum_result_file_count": 2,
    "maximum_execute_count": 1,
}

NOTICE_TOKENS = (
    "license",
    "licence",
    "notice",
    "copyright",
    "copying",
    "readme",
    "attribution",
)
GROUND_TRUTH_TOKENS = (
    "groundtruth",
    "ground_truth",
    "label",
    "processinstance",
    "process_instance",
    "processid",
    "process_id",
    "activity",
    "stage",
    "station",
    "completion",
    "completed",
    "outcome",
    "verdict",
    "class",
)
SECRET_TOKENS = (
    "password",
    "passwd",
    "credential",
    "authorization",
    "secret",
    "cookie",
    "token",
    "apikey",
    "api_key",
)
NETWORK_IDENTIFIER_TOKENS = (
    "ip",
    "mac",
    "hostname",
    "host",
    "username",
    "user",
    "email",
    "url",
    "uri",
    "network",
    "ssid",
    "port",
)
TIMESTAMP_KEYS = {
    "time",
    "timestamp",
    "datetime",
    "eventtime",
    "eventtimestamp",
    "recordtime",
    "recordtimestamp",
    "ts",
}
TIMESTAMP_MILLISECOND_KEYS = {
    "timems",
    "timestampms",
    "eventtimems",
    "eventtimestampms",
    "epochms",
}
TIMESTAMP_MICROSECOND_KEYS = {
    "timeus",
    "timestampus",
    "eventtimeus",
    "eventtimestampus",
    "epochus",
}
TIMESTAMP_NANOSECOND_KEYS = {
    "timens",
    "timestampns",
    "eventtimens",
    "eventtimestampns",
    "epochns",
}

URL_PATTERN = re.compile(r"(?i)\b(?:https?|ftp)://")
EMAIL_PATTERN = re.compile(
    r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
)
IPV4_PATTERN = re.compile(
    r"(?<![0-9])(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})"
    r"(?:\.(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})){3}(?![0-9])"
)
MAC_PATTERN = re.compile(r"(?i)\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b")


@dataclass(frozen=True)
class ManifestInterval:
    """Protected in-memory interval; no raw identifier is retained."""

    instance_digest: str
    start_microseconds: int
    end_microseconds: int
    process_category: str
    state_category: str
    pointer_digest: str


@dataclass
class SourceReadBudget:
    """Counts only bytes read from the two acquired surfaces."""

    consumed: int = 0

    def add(self, amount: int) -> None:
        self.consumed += amount
        if self.consumed > CAPS["maximum_total_source_bytes_read"]:
            raise AuditBlocked("total_source_read_byte_cap_exceeded")


def _check_wall(started: float) -> None:
    if time.monotonic() - started > CAPS["maximum_wall_seconds"]:
        raise AuditBlocked("wall_time_cap_exceeded")


def _digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def _digest_source_file(
    path: Path, algorithm: str, budget: SourceReadBudget
) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            budget.add(len(chunk))
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
        "name": "CPython standard-library dual JSON and JSONL reader",
        "python_version": sys.version,
        "components": components,
        "identity_gate_passed": True,
    }


def _normalize_key(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _contains_token(value: str, tokens: Iterable[str]) -> bool:
    folded = value.casefold()
    normalized = _normalize_key(value)
    for token in tokens:
        folded_token = token.casefold()
        normalized_token = _normalize_key(token)
        if len(normalized_token) <= 3:
            if (
                normalized == normalized_token
                or normalized.startswith(normalized_token)
                or normalized.endswith(normalized_token)
            ):
                return True
        elif folded_token in folded or normalized_token in normalized:
            return True
    return False


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _opaque_instance_digest(value: str) -> str:
    return _sha256_bytes(
        b"project05-stgallen-process-instance-v0.1\x00"
        + value.encode("utf-8")
    )


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
            raise AuditBlocked("manifest_pointer_resolution_failed")
    return current


def _parse_time_microseconds(value: Any, normalized_key: str) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        if candidate.endswith(("Z", "z")):
            candidate = candidate[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        return int(parsed.timestamp() * 1_000_000)
    if isinstance(value, (int, float)):
        numeric = float(value)
        if normalized_key in TIMESTAMP_MILLISECOND_KEYS:
            return int(numeric * 1_000)
        if normalized_key in TIMESTAMP_MICROSECOND_KEYS:
            return int(numeric)
        if normalized_key in TIMESTAMP_NANOSECOND_KEYS:
            return int(numeric / 1_000)
    return None


def _unique_field(
    value: dict[str, Any], normalized_names: set[str]
) -> tuple[str, Any] | None:
    matches = [
        (key, child)
        for key, child in value.items()
        if _normalize_key(key) in normalized_names
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def _classify_process(value: dict[str, Any]) -> str:
    descriptors = []
    for key, child in value.items():
        if _normalize_key(key) in {
            "processdefinitionkey",
            "processdefinitionname",
            "processkey",
            "processname",
            "definitionkey",
            "definitionname",
        } and isinstance(child, str):
            descriptors.append(child.casefold())
    joined = "\x00".join(descriptors)
    storage = "storage" in joined
    production = "production" in joined
    if storage and not production:
        return "storage"
    if production and not storage:
        return "production"
    return "unknown_or_ambiguous"


def _classify_state(value: dict[str, Any]) -> str:
    state_field = _unique_field(
        value, {"state", "status", "completionstate", "executionstate"}
    )
    if state_field is None or not isinstance(state_field[1], str):
        return "missing_or_unknown"
    folded = state_field[1].casefold()
    if any(token in folded for token in ("completed", "complete", "finished")):
        return "completed"
    if any(token in folded for token in ("active", "running")):
        return "active"
    if any(token in folded for token in ("suspend", "pause")):
        return "suspended"
    if any(token in folded for token in ("terminate", "abort", "delete", "cancel")):
        return "terminated_or_aborted"
    return "other"


def _manifest_candidate(
    value: dict[str, Any], path: tuple[str | int, ...]
) -> ManifestInterval | None:
    start_field = _unique_field(
        value,
        {
            "starttime",
            "starttimestamp",
            "executionstarttime",
            "executionstarttimestamp",
        },
    )
    end_field = _unique_field(
        value,
        {
            "endtime",
            "endtimestamp",
            "executionendtime",
            "executionendtimestamp",
        },
    )
    if start_field is None or end_field is None:
        return None

    identifier_field = _unique_field(
        value,
        {
            "id",
            "processinstanceid",
            "processinstancekey",
            "businesskey",
        },
    )
    if identifier_field is None or not isinstance(identifier_field[1], str):
        return None
    identifier = identifier_field[1]
    if not identifier or len(identifier.encode("utf-8")) > 4_096:
        return None

    start = _parse_time_microseconds(
        start_field[1], _normalize_key(start_field[0])
    )
    end = _parse_time_microseconds(end_field[1], _normalize_key(end_field[0]))
    if start is None or end is None:
        return None

    return ManifestInterval(
        instance_digest=_opaque_instance_digest(identifier),
        start_microseconds=start,
        end_microseconds=end,
        process_category=_classify_process(value),
        state_category=_classify_state(value),
        pointer_digest=_sha256_text(_json_pointer(path)),
    )


def _inspect_manifest(root: Any, started: float) -> dict[str, object]:
    node_count = 0
    dict_count = 0
    list_count = 0
    scalar_count = 0
    key_count = 0
    maximum_depth_seen = 0
    maximum_string_bytes_seen = 0
    notice_key_match_count = 0
    secret_key_match_count = 0
    network_identifier_key_match_count = 0
    schema_signatures: Counter[str] = Counter()
    candidates: list[ManifestInterval] = []

    stack: list[tuple[Any, tuple[str | int, ...], int]] = [(root, (), 0)]
    while stack:
        _check_wall(started)
        value, path, depth = stack.pop()
        node_count += 1
        if node_count > CAPS["maximum_manifest_total_nodes"]:
            raise AuditBlocked("manifest_node_cap_exceeded")
        if depth > CAPS["maximum_manifest_json_depth"]:
            raise AuditBlocked("manifest_depth_cap_exceeded")
        maximum_depth_seen = max(maximum_depth_seen, depth)

        if isinstance(value, dict):
            dict_count += 1
            if len(value) > CAPS["maximum_manifest_dict_keys_per_object"]:
                raise AuditBlocked("manifest_dict_key_cap_exceeded")
            key_count += len(value)
            key_digests = sorted(_sha256_text(str(key)) for key in value)
            schema_signatures[_aggregate_digest(key_digests)] += 1

            candidate = _manifest_candidate(value, path)
            if candidate is not None:
                candidates.append(candidate)
                if (
                    len(candidates)
                    > CAPS["maximum_manifest_instance_candidates"]
                ):
                    raise AuditBlocked("manifest_candidate_cap_exceeded")
                if _resolve_path(root, path) is not value:
                    raise AuditBlocked("manifest_pointer_round_trip_failed")

            for key, child in value.items():
                encoded_key_bytes = len(key.encode("utf-8"))
                maximum_string_bytes_seen = max(
                    maximum_string_bytes_seen, encoded_key_bytes
                )
                if (
                    encoded_key_bytes
                    > CAPS["maximum_manifest_scalar_string_utf8_bytes"]
                ):
                    raise AuditBlocked("manifest_key_byte_cap_exceeded")
                if _contains_token(key, NOTICE_TOKENS):
                    notice_key_match_count += 1
                if _contains_token(key, SECRET_TOKENS):
                    secret_key_match_count += 1
                if _contains_token(key, NETWORK_IDENTIFIER_TOKENS):
                    network_identifier_key_match_count += 1
                stack.append((child, path + (key,), depth + 1))
        elif isinstance(value, list):
            list_count += 1
            if len(value) > CAPS["maximum_manifest_list_items_per_array"]:
                raise AuditBlocked("manifest_list_item_cap_exceeded")
            for index in range(len(value) - 1, -1, -1):
                stack.append((value[index], path + (index,), depth + 1))
        elif isinstance(value, str):
            scalar_count += 1
            encoded_value_bytes = len(value.encode("utf-8"))
            maximum_string_bytes_seen = max(
                maximum_string_bytes_seen, encoded_value_bytes
            )
            if (
                encoded_value_bytes
                > CAPS["maximum_manifest_scalar_string_utf8_bytes"]
            ):
                raise AuditBlocked("manifest_string_byte_cap_exceeded")
        else:
            scalar_count += 1

    candidate_digests = [item.instance_digest for item in candidates]
    unique_digests = sorted(set(candidate_digests))
    duplicate_candidate_count = len(candidate_digests) - len(unique_digests)
    invalid_interval_count = sum(
        1
        for item in candidates
        if item.end_microseconds <= item.start_microseconds
    )
    valid_intervals = sorted(
        (
            item
            for item in candidates
            if item.end_microseconds > item.start_microseconds
        ),
        key=lambda item: (item.start_microseconds, item.end_microseconds),
    )
    overlap_pair_count = sum(
        1
        for left, right in zip(valid_intervals, valid_intervals[1:])
        if right.start_microseconds < left.end_microseconds
    )
    process_categories = Counter(
        item.process_category for item in candidates
    )
    state_categories = Counter(item.state_category for item in candidates)
    pointer_candidates = sorted(
        _sha256_text(
            json.dumps(
                {
                    "artifact_md5": MANIFEST_EXPECTED_MD5,
                    "instance_sha256": item.instance_digest,
                    "json_pointer_sha256": item.pointer_digest,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        for item in candidates
    )
    bounded_manifest_gate = (
        len(candidates) == 10
        and len(unique_digests) == 10
        and duplicate_candidate_count == 0
        and invalid_interval_count == 0
        and overlap_pair_count == 0
        and process_categories["storage"] == 5
        and process_categories["production"] == 5
        and process_categories["unknown_or_ambiguous"] == 0
        and state_categories["completed"] == 10
        and state_categories["missing_or_unknown"] == 0
        and state_categories["other"] == 0
        and state_categories["active"] == 0
        and state_categories["suspended"] == 0
        and state_categories["terminated_or_aborted"] == 0
    )

    return {
        "intervals": valid_intervals,
        "instance_digest_set": set(unique_digests),
        "sanitized": {
            "parse": {
                "root_type": type(root).__name__,
                "node_count": node_count,
                "dictionary_count": dict_count,
                "list_count": list_count,
                "scalar_count": scalar_count,
                "key_count": key_count,
                "maximum_depth_seen": maximum_depth_seen,
                "maximum_string_bytes_seen": maximum_string_bytes_seen,
                "schema_signature_count": len(schema_signatures),
                "json_parse_passed": True,
                "raw_key_value_or_path_persisted": False,
            },
            "notice_privacy": {
                "notice_key_match_count": notice_key_match_count,
                "secret_key_match_count": secret_key_match_count,
                "network_identifier_key_match_count": (
                    network_identifier_key_match_count
                ),
                "raw_matching_key_value_or_notice_persisted": False,
                "protected_manifest_model_visibility": False,
            },
            "manifest_lineage": {
                "candidate_occurrence_count": len(candidates),
                "unique_instance_candidate_count": len(unique_digests),
                "curator_declared_ten_count_match": len(unique_digests) == 10,
                "duplicate_instance_candidate_count": duplicate_candidate_count,
                "invalid_interval_count": invalid_interval_count,
                "adjacent_interval_overlap_count": overlap_pair_count,
                "storage_category_count": process_categories["storage"],
                "production_category_count": process_categories["production"],
                "unknown_or_ambiguous_process_category_count": (
                    process_categories["unknown_or_ambiguous"]
                ),
                "completed_state_count": state_categories["completed"],
                "missing_or_unknown_state_count": (
                    state_categories["missing_or_unknown"]
                ),
                "other_state_count": state_categories["other"],
                "active_suspended_or_terminated_count": (
                    state_categories["active"]
                    + state_categories["suspended"]
                    + state_categories["terminated_or_aborted"]
                ),
                "instance_digest_set_sha256": _aggregate_digest(unique_digests),
                "pointer_candidate_count": len(pointer_candidates),
                "pointer_candidate_aggregate_sha256": _aggregate_digest(
                    pointer_candidates
                ),
                "bounded_manifest_probe_passed": bounded_manifest_gate,
                "duplicate_retry_partial_abort_reset_policy_fully_verified": False,
                "statistical_independence_verified": False,
                "lineage_credit": 0,
            },
        },
    }


def _read_and_inspect_manifest(
    started: float, budget: SourceReadBudget
) -> dict[str, object]:
    raw = MANIFEST_PATH.read_bytes()
    budget.add(len(raw))
    if len(raw) > CAPS["maximum_manifest_source_bytes"]:
        raise AuditBlocked("manifest_read_byte_cap_exceeded")
    if len(raw) != MANIFEST_EXPECTED_BYTES:
        raise AuditBlocked("manifest_changed_after_identity_gate")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise AuditBlocked("manifest_invalid_utf8") from error
    try:
        root = json.loads(text)
    except json.JSONDecodeError as error:
        raise AuditBlocked("manifest_invalid_json") from error
    if not isinstance(root, (dict, list)):
        raise AuditBlocked("manifest_root_not_object_or_array")
    return _inspect_manifest(root, started)


def _inspect_sensor_record(
    root: dict[str, Any],
    manifest_id_digests: set[str],
    started: float,
) -> dict[str, object]:
    node_count = 0
    key_count = 0
    maximum_depth = 0
    maximum_string_bytes = 0
    notice_key_matches = 0
    ground_truth_key_matches = 0
    ground_truth_value_matches = 0
    secret_key_matches = 0
    network_key_matches = 0
    url_value_matches = 0
    email_value_matches = 0
    ipv4_value_matches = 0
    mac_value_matches = 0
    exact_manifest_identifier_overlap_matches = 0
    timestamp_candidates: set[int] = set()

    stack: list[tuple[Any, int, str | None]] = [(root, 0, None)]
    while stack:
        _check_wall(started)
        value, depth, parent_key = stack.pop()
        node_count += 1
        if node_count > CAPS["maximum_sensor_nodes_per_record"]:
            raise AuditBlocked("sensor_record_node_cap_exceeded")
        if depth > CAPS["maximum_sensor_json_depth_per_record"]:
            raise AuditBlocked("sensor_record_depth_cap_exceeded")
        maximum_depth = max(maximum_depth, depth)

        if isinstance(value, dict):
            if len(value) > CAPS["maximum_sensor_dict_keys_per_object"]:
                raise AuditBlocked("sensor_record_dict_key_cap_exceeded")
            key_count += len(value)
            for key, child in value.items():
                encoded_key_bytes = len(key.encode("utf-8"))
                maximum_string_bytes = max(
                    maximum_string_bytes, encoded_key_bytes
                )
                if (
                    encoded_key_bytes
                    > CAPS["maximum_sensor_scalar_string_utf8_bytes"]
                ):
                    raise AuditBlocked("sensor_key_byte_cap_exceeded")
                normalized_key = _normalize_key(key)
                if _contains_token(key, NOTICE_TOKENS):
                    notice_key_matches += 1
                if _contains_token(key, GROUND_TRUTH_TOKENS):
                    ground_truth_key_matches += 1
                if _contains_token(key, SECRET_TOKENS):
                    secret_key_matches += 1
                if _contains_token(key, NETWORK_IDENTIFIER_TOKENS):
                    network_key_matches += 1
                timestamp = _parse_time_microseconds(child, normalized_key)
                if (
                    normalized_key in TIMESTAMP_KEYS
                    or normalized_key in TIMESTAMP_MILLISECOND_KEYS
                    or normalized_key in TIMESTAMP_MICROSECOND_KEYS
                    or normalized_key in TIMESTAMP_NANOSECOND_KEYS
                ) and timestamp is not None:
                    timestamp_candidates.add(timestamp)
                stack.append((child, depth + 1, key))
        elif isinstance(value, list):
            if len(value) > CAPS["maximum_sensor_list_items_per_array"]:
                raise AuditBlocked("sensor_record_list_item_cap_exceeded")
            for child in value:
                stack.append((child, depth + 1, parent_key))
        elif isinstance(value, str):
            encoded_value_bytes = len(value.encode("utf-8"))
            maximum_string_bytes = max(
                maximum_string_bytes, encoded_value_bytes
            )
            if (
                encoded_value_bytes
                > CAPS["maximum_sensor_scalar_string_utf8_bytes"]
            ):
                raise AuditBlocked("sensor_string_byte_cap_exceeded")
            if _contains_token(value, GROUND_TRUTH_TOKENS):
                ground_truth_value_matches += 1
            if URL_PATTERN.search(value):
                url_value_matches += 1
            if EMAIL_PATTERN.search(value):
                email_value_matches += 1
            if IPV4_PATTERN.search(value):
                ipv4_value_matches += 1
            if MAC_PATTERN.search(value):
                mac_value_matches += 1
            if _opaque_instance_digest(value) in manifest_id_digests:
                exact_manifest_identifier_overlap_matches += 1

    timestamp = None
    if len(timestamp_candidates) == 1:
        timestamp = next(iter(timestamp_candidates))
    return {
        "node_count": node_count,
        "key_count": key_count,
        "maximum_depth": maximum_depth,
        "maximum_string_bytes": maximum_string_bytes,
        "notice_key_matches": notice_key_matches,
        "ground_truth_key_matches": ground_truth_key_matches,
        "ground_truth_value_matches": ground_truth_value_matches,
        "secret_key_matches": secret_key_matches,
        "network_key_matches": network_key_matches,
        "url_value_matches": url_value_matches,
        "email_value_matches": email_value_matches,
        "ipv4_value_matches": ipv4_value_matches,
        "mac_value_matches": mac_value_matches,
        "exact_manifest_identifier_overlap_matches": (
            exact_manifest_identifier_overlap_matches
        ),
        "timestamp_candidate_count": len(timestamp_candidates),
        "timestamp": timestamp,
    }


def _record_pointer_digest(
    ordinal: int, offset: int, length: int, record_sha256: str
) -> str:
    canonical = json.dumps(
        {
            "artifact_md5": SENSOR_EXPECTED_MD5,
            "byte_length": length,
            "byte_offset": offset,
            "record_ordinal": ordinal,
            "record_sha256": record_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_text(canonical)


def _select_pointer_sample(
    heap: list[tuple[int, int, int, str]],
    ordinal: int,
    offset: int,
    length: int,
    record_sha256: str,
) -> None:
    rank = int(
        _sha256_text(
            f"{ordinal}:{offset}:{length}:{record_sha256}"
        )[:16],
        16,
    )
    item = (-rank, offset, length, record_sha256)
    cap = CAPS["maximum_pointer_round_trip_records"]
    if len(heap) < cap:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def _verify_pointer_samples(
    samples: list[tuple[int, int, int, str]],
    started: float,
    budget: SourceReadBudget,
) -> bool:
    with SENSOR_PATH.open("rb") as handle:
        for _, offset, length, expected_sha256 in sorted(samples):
            _check_wall(started)
            handle.seek(offset)
            raw = handle.read(length)
            budget.add(len(raw))
            if len(raw) != length or _sha256_bytes(raw) != expected_sha256:
                return False
    return True


def _bind_timestamp(
    timestamp: int, intervals: list[ManifestInterval]
) -> list[ManifestInterval]:
    return [
        interval
        for interval in intervals
        if interval.start_microseconds <= timestamp <= interval.end_microseconds
    ]


def _scan_sensor(
    intervals: list[ManifestInterval],
    manifest_id_digests: set[str],
    started: float,
    budget: SourceReadBudget,
) -> dict[str, object]:
    line_count = 0
    blank_line_count = 0
    parsed_record_count = 0
    invalid_json_record_count = 0
    non_object_record_count = 0
    total_nodes = 0
    total_keys = 0
    maximum_depth_seen = 0
    maximum_string_bytes_seen = 0
    maximum_line_bytes_seen = 0
    notice_key_match_count = 0
    ground_truth_key_match_count = 0
    ground_truth_value_match_count = 0
    secret_key_match_count = 0
    network_key_match_count = 0
    url_value_match_count = 0
    email_value_match_count = 0
    ipv4_value_match_count = 0
    mac_value_match_count = 0
    exact_manifest_identifier_overlap_count = 0
    missing_timestamp_count = 0
    multiple_timestamp_count = 0
    bound_record_count = 0
    unbound_record_count = 0
    ambiguous_record_count = 0
    schema_signatures: Counter[str] = Counter()
    per_interval_bound_counts: Counter[str] = Counter()
    pointer_digest_stream = hashlib.sha256()
    binding_digest_stream = hashlib.sha256()
    pointer_sample_heap: list[tuple[int, int, int, str]] = []
    total_bytes_read = 0

    with SENSOR_PATH.open("rb") as handle:
        while True:
            _check_wall(started)
            offset = handle.tell()
            raw_line = handle.readline(
                CAPS["maximum_sensor_line_bytes"] + 1
            )
            if not raw_line:
                break
            line_count += 1
            if line_count > CAPS["maximum_sensor_lines"]:
                raise AuditBlocked("sensor_line_cap_exceeded")
            length = len(raw_line)
            budget.add(length)
            total_bytes_read += length
            maximum_line_bytes_seen = max(maximum_line_bytes_seen, length)
            if length > CAPS["maximum_sensor_line_bytes"]:
                raise AuditBlocked("sensor_line_byte_cap_exceeded")
            record_sha256 = _sha256_bytes(raw_line)
            pointer_digest = _record_pointer_digest(
                line_count, offset, length, record_sha256
            )
            pointer_digest_stream.update(bytes.fromhex(pointer_digest))
            _select_pointer_sample(
                pointer_sample_heap,
                line_count,
                offset,
                length,
                record_sha256,
            )

            stripped = raw_line.rstrip(b"\r\n")
            if not stripped:
                blank_line_count += 1
                continue
            try:
                text = stripped.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                raise AuditBlocked("sensor_invalid_utf8") from error
            try:
                record = json.loads(text)
            except json.JSONDecodeError:
                invalid_json_record_count += 1
                continue
            if not isinstance(record, dict):
                non_object_record_count += 1
                continue
            parsed_record_count += 1
            schema_signatures[
                _aggregate_digest(
                    sorted(_sha256_text(str(key)) for key in record)
                )
            ] += 1
            inspected = _inspect_sensor_record(
                record, manifest_id_digests, started
            )
            total_nodes += int(inspected["node_count"])
            if total_nodes > CAPS["maximum_sensor_total_nodes"]:
                raise AuditBlocked("sensor_total_node_cap_exceeded")
            total_keys += int(inspected["key_count"])
            maximum_depth_seen = max(
                maximum_depth_seen, int(inspected["maximum_depth"])
            )
            maximum_string_bytes_seen = max(
                maximum_string_bytes_seen,
                int(inspected["maximum_string_bytes"]),
            )
            notice_key_match_count += int(inspected["notice_key_matches"])
            ground_truth_key_match_count += int(
                inspected["ground_truth_key_matches"]
            )
            ground_truth_value_match_count += int(
                inspected["ground_truth_value_matches"]
            )
            secret_key_match_count += int(inspected["secret_key_matches"])
            network_key_match_count += int(inspected["network_key_matches"])
            url_value_match_count += int(inspected["url_value_matches"])
            email_value_match_count += int(inspected["email_value_matches"])
            ipv4_value_match_count += int(inspected["ipv4_value_matches"])
            mac_value_match_count += int(inspected["mac_value_matches"])
            exact_manifest_identifier_overlap_count += int(
                inspected["exact_manifest_identifier_overlap_matches"]
            )

            candidate_count = int(inspected["timestamp_candidate_count"])
            timestamp = inspected["timestamp"]
            if candidate_count == 0:
                missing_timestamp_count += 1
                continue
            if candidate_count != 1 or timestamp is None:
                multiple_timestamp_count += 1
                continue
            matches = _bind_timestamp(int(timestamp), intervals)
            if len(matches) == 0:
                unbound_record_count += 1
            elif len(matches) > 1:
                ambiguous_record_count += 1
            else:
                bound_record_count += 1
                interval = matches[0]
                per_interval_bound_counts[interval.instance_digest] += 1
                binding_digest_stream.update(
                    bytes.fromhex(interval.instance_digest)
                )
                binding_digest_stream.update(bytes.fromhex(pointer_digest))

    if total_bytes_read != SENSOR_EXPECTED_BYTES:
        raise AuditBlocked("sensor_changed_during_stream")
    samples = [
        (rank, offset, length, record_sha256)
        for rank, offset, length, record_sha256 in pointer_sample_heap
    ]
    pointer_round_trip_passed = _verify_pointer_samples(
        samples, started, budget
    )
    every_manifest_interval_has_records = bool(intervals) and all(
        per_interval_bound_counts[item.instance_digest] > 0
        for item in intervals
    )
    schema_probe_passed = (
        parsed_record_count > 0
        and invalid_json_record_count == 0
        and non_object_record_count == 0
        and blank_line_count == 0
    )
    gt_exclusion_probe_passed = (
        ground_truth_key_match_count == 0
        and ground_truth_value_match_count == 0
        and exact_manifest_identifier_overlap_count == 0
    )
    privacy_probe_passed = (
        secret_key_match_count == 0
        and network_key_match_count == 0
        and url_value_match_count == 0
        and email_value_match_count == 0
        and ipv4_value_match_count == 0
        and mac_value_match_count == 0
    )
    binding_probe_passed = (
        parsed_record_count > 0
        and missing_timestamp_count == 0
        and multiple_timestamp_count == 0
        and ambiguous_record_count == 0
        and every_manifest_interval_has_records
    )

    return {
        "parse": {
            "input_bytes": total_bytes_read,
            "line_count": line_count,
            "blank_line_count": blank_line_count,
            "parsed_object_record_count": parsed_record_count,
            "invalid_json_record_count": invalid_json_record_count,
            "non_object_record_count": non_object_record_count,
            "total_node_count": total_nodes,
            "total_key_count": total_keys,
            "maximum_line_bytes_seen": maximum_line_bytes_seen,
            "maximum_depth_seen": maximum_depth_seen,
            "maximum_string_bytes_seen": maximum_string_bytes_seen,
            "schema_signature_count": len(schema_signatures),
            "schema_probe_passed": schema_probe_passed,
            "raw_record_key_value_or_schema_persisted": False,
        },
        "notice": {
            "notice_key_match_count": notice_key_match_count,
            "raw_notice_text_persisted": False,
            "record_scope_license_closes_field_or_third_party_rights": False,
            "notice_gate_passed": False,
        },
        "privacy": {
            "secret_key_match_count": secret_key_match_count,
            "network_identifier_key_match_count": network_key_match_count,
            "url_value_match_count": url_value_match_count,
            "email_value_match_count": email_value_match_count,
            "ipv4_value_match_count": ipv4_value_match_count,
            "mac_value_match_count": mac_value_match_count,
            "bounded_privacy_probe_passed": privacy_probe_passed,
            "full_privacy_gate_passed": False,
            "raw_matching_key_or_value_persisted": False,
        },
        "ground_truth_exclusion": {
            "ground_truth_key_match_count": ground_truth_key_match_count,
            "ground_truth_value_match_count": ground_truth_value_match_count,
            "exact_manifest_identifier_overlap_count": (
                exact_manifest_identifier_overlap_count
            ),
            "bounded_gt_exclusion_probe_passed": (
                gt_exclusion_probe_passed
            ),
            "protected_manifest_value_entered_sensor_result": False,
            "raw_matching_key_value_or_identifier_persisted": False,
        },
        "binding": {
            "records_with_no_timestamp_candidate": missing_timestamp_count,
            "records_with_multiple_timestamp_candidates": (
                multiple_timestamp_count
            ),
            "records_bound_to_exactly_one_interval": bound_record_count,
            "records_outside_all_intervals": unbound_record_count,
            "records_ambiguous_across_intervals": ambiguous_record_count,
            "manifest_intervals_with_one_or_more_bound_records": sum(
                1
                for item in intervals
                if per_interval_bound_counts[item.instance_digest] > 0
            ),
            "every_manifest_interval_has_bound_records": (
                every_manifest_interval_has_records
            ),
            "binding_aggregate_sha256": binding_digest_stream.hexdigest(),
            "bounded_binding_probe_passed": binding_probe_passed,
            "per_record_binding_persisted": False,
            "protected_instance_identifier_persisted": False,
            "binding_status": "provisional_probe_only_not_admitted",
        },
        "pointer": {
            "candidate_shape": (
                "sensor_artifact_md5 + record_ordinal + byte_offset + "
                "byte_length + record_sha256; protected binder injects only "
                "an opaque process-instance digest"
            ),
            "candidate_count": line_count,
            "candidate_aggregate_sha256": pointer_digest_stream.hexdigest(),
            "round_trip_sample_count": len(samples),
            "sampled_exact_byte_round_trip_passed": (
                pointer_round_trip_passed
            ),
            "raw_pointer_offset_ordinal_path_or_record_hash_persisted": False,
            "pointer_binding_authorized": False,
            "binding_status": "unbound",
        },
    }


def _verify_source_identity(
    path: Path,
    expected_bytes: int,
    expected_md5: str,
    code: str,
    budget: SourceReadBudget,
) -> dict[str, object]:
    if not path.is_file():
        raise AuditBlocked(f"{code}_missing")
    actual_bytes = path.stat().st_size
    if actual_bytes != expected_bytes:
        raise AuditBlocked(f"{code}_size_mismatch")
    actual_md5 = _digest_source_file(path, "md5", budget)
    if actual_md5 != expected_md5:
        raise AuditBlocked(f"{code}_md5_mismatch")
    return {
        "target_id": code,
        "bytes": actual_bytes,
        "md5": actual_md5,
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
    if authority.get("target_ids") != list(TARGET_IDS):
        raise AuditBlocked("execution_authority_target_set_mismatch")
    required_true = (
        "audit_execution_authorized",
        "protected_manifest_open_authorized",
        "protected_manifest_read_authorized",
        "protected_manifest_json_parse_authorized",
        "sensor_open_authorized",
        "sensor_read_authorized",
        "sensor_jsonl_parse_authorized",
        "privacy_notice_schema_gt_exclusion_authorized",
        "manifest_lineage_binding_pointer_probe_authorized",
    )
    if any(authority.get(key) is not True for key in required_true):
        raise AuditBlocked("execution_authority_scope_missing")
    required_false = (
        "automatic_retry_authorized",
        "resume_authorized",
        "protected_manifest_model_visibility_authorized",
        "raw_value_or_identifier_persistence_authorized",
        "source_role_change_authorized",
        "catalog_or_credit_change_authorized",
    )
    if any(authority.get(key) is not False for key in required_false):
        raise AuditBlocked("execution_authority_fail_closed_boundary_missing")
    if authority.get("caps") != CAPS:
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


def _result_status(
    manifest: dict[str, object], sensor: dict[str, object]
) -> str:
    manifest_gate = bool(
        manifest["manifest_lineage"]["bounded_manifest_probe_passed"]
    )
    if not sensor["ground_truth_exclusion"][
        "bounded_gt_exclusion_probe_passed"
    ]:
        return "fail_closed_sensor_ground_truth_surface_detected"
    if not sensor["privacy"]["bounded_privacy_probe_passed"]:
        return "fail_closed_sensor_privacy_or_identifier_surface_detected"
    if not sensor["parse"]["schema_probe_passed"]:
        return "fail_closed_sensor_schema_probe"
    if not manifest_gate:
        return "hold_manifest_lineage_shape_unclosed"
    if not sensor["binding"]["bounded_binding_probe_passed"]:
        return "hold_process_to_sensor_binding_unclosed"
    if not sensor["pointer"]["sampled_exact_byte_round_trip_passed"]:
        return "hold_pointer_round_trip_unclosed"
    return "bounded_probe_hold_notice_full_lineage_semantic_fit_and_source_role_unclosed"


def _write_sanitized_result(result: dict[str, object]) -> None:
    serialized = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if (
        len(serialized.encode("utf-8"))
        > CAPS["maximum_result_bytes_per_file"]
    ):
        raise AuditBlocked("json_result_byte_cap_exceeded")
    RESULT_JSON_PATH.write_text(serialized, encoding="utf-8")

    manifest = result["probe"]["protected_manifest"]["manifest_lineage"]
    sensor = result["probe"]["sensor"]
    markdown = f"""# St.Gallen dual-surface bounded audit result

Status: `{result['status']}`

| Gate | Result |
|---|---|
| Protected manifest identity / JSON parse | pass / true |
| Unique process-instance candidates | {manifest['unique_instance_candidate_count']} |
| Curator ten-instance count match | {str(manifest['curator_declared_ten_count_match']).lower()} |
| Non-overlapping complete-interval probe | {str(manifest['bounded_manifest_probe_passed']).lower()} |
| Sensor schema probe | {str(sensor['parse']['schema_probe_passed']).lower()} |
| Sensor GT-exclusion probe | {str(sensor['ground_truth_exclusion']['bounded_gt_exclusion_probe_passed']).lower()} |
| Sensor privacy probe | {str(sensor['privacy']['bounded_privacy_probe_passed']).lower()} |
| Every manifest interval has bound records | {str(sensor['binding']['every_manifest_interval_has_bound_records']).lower()} |
| Ambiguous bound records | {sensor['binding']['records_ambiguous_across_intervals']} |
| Sampled pointer byte round trip | {str(sensor['pointer']['sampled_exact_byte_round_trip_passed']).lower()} |
| Notice / full lineage / source role | false / false / false |
| Pointer binding | unbound |
| Family / lineage / sample / quota credit | 0 / 0 / 0 / 0 |
| L2 Gate | false |

No raw manifest or sensor key, value, record, process-instance identifier,
timestamp, byte offset, ordinal, JSON pointer, local path, or notice is
persisted. The protected manifest never becomes model-visible.
"""
    if (
        len(markdown.encode("utf-8"))
        > CAPS["maximum_result_bytes_per_file"]
    ):
        raise AuditBlocked("markdown_result_byte_cap_exceeded")
    RESULT_MD_PATH.write_text(markdown, encoding="utf-8")


def _write_sanitized_failure(reason_code: str) -> None:
    if RESULT_JSON_PATH.exists() or RESULT_MD_PATH.exists():
        return
    result = {
        "schema_version": (
            "project05-llm-editor-l2-stgallen-smart-factory-dual-surface-"
            "bounded-audit-result-v0.1"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed_closed_terminal_no_automatic_retry",
        "target_ids": list(TARGET_IDS),
        "reason_code": reason_code,
        "content": {
            "raw_manifest_or_sensor_content_persisted": False,
            "raw_identifier_timestamp_pointer_or_path_persisted": False,
            "protected_manifest_model_visible": False,
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
    if (
        len(serialized.encode("utf-8"))
        <= CAPS["maximum_result_bytes_per_file"]
    ):
        RESULT_JSON_PATH.write_text(serialized, encoding="utf-8")
        RESULT_MD_PATH.write_text(
            "# St.Gallen dual-surface bounded audit failure\n\n"
            "Status: `failed_closed_terminal_no_automatic_retry`\n\n"
            f"Reason code: `{reason_code}`\n\n"
            "No raw manifest or sensor content, identifier, timestamp, "
            "pointer, path, or notice is persisted. No role or credit "
            "changed.\n",
            encoding="utf-8",
        )


def execute_audit(authority_path: Path) -> dict[str, object]:
    started = time.monotonic()
    budget = SourceReadBudget()
    authority = _verify_execution_authority(authority_path)
    reader = _verify_reader_identity()
    manifest_identity = _verify_source_identity(
        MANIFEST_PATH,
        MANIFEST_EXPECTED_BYTES,
        MANIFEST_EXPECTED_MD5,
        TARGET_IDS[0],
        budget,
    )
    sensor_identity = _verify_source_identity(
        SENSOR_PATH,
        SENSOR_EXPECTED_BYTES,
        SENSOR_EXPECTED_MD5,
        TARGET_IDS[1],
        budget,
    )
    manifest_probe_internal = _read_and_inspect_manifest(started, budget)
    sensor_probe = _scan_sensor(
        manifest_probe_internal["intervals"],
        manifest_probe_internal["instance_digest_set"],
        started,
        budget,
    )
    manifest_probe = manifest_probe_internal["sanitized"]
    result: dict[str, object] = {
        "schema_version": (
            "project05-llm-editor-l2-stgallen-smart-factory-dual-surface-"
            "bounded-audit-result-v0.1"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": _result_status(manifest_probe, sensor_probe),
        "target_ids": list(TARGET_IDS),
        "authority": authority,
        "reader": reader,
        "source_identity": {
            "protected_manifest": manifest_identity,
            "sensor": sensor_identity,
            "total_source_bytes_read": budget.consumed,
            "maximum_total_source_bytes_read": CAPS[
                "maximum_total_source_bytes_read"
            ],
        },
        "probe": {
            "protected_manifest": manifest_probe,
            "sensor": sensor_probe,
        },
        "scope": {
            "protected_manifest_opened_and_parsed_in_memory": True,
            "sensor_streamed_and_parsed_in_memory": True,
            "raw_manifest_or_sensor_key_value_record_persisted": False,
            "raw_identifier_timestamp_pointer_or_path_persisted": False,
            "protected_manifest_model_visible": False,
            "ground_truth_used_as_model_supervision": False,
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
                        "status": (
                            "plan_reader_identity_passed_surfaces_not_touched"
                        ),
                        "reader_identity_gate_passed": (
                            reader["identity_gate_passed"]
                        ),
                        "surfaces_statted_or_opened": False,
                        "manifest_parsed": False,
                        "sensor_streamed": False,
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
