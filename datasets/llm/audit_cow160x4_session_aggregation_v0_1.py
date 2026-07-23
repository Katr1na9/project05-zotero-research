"""Fail-closed bounded auditor for COW160x4 session_aggregation.jsonl.gz.

This module is dormant by default.  ``--mode plan`` verifies only the pinned
local Python reader and never stats or opens the gzip target.  ``--mode
execute`` additionally requires a separate authority JSON that pins the
current script and audit-contract hashes.  Execution is intentionally bounded,
never extracts or persists decompressed content, and writes only aggregate
sanitized results.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import time
import zlib
from collections import Counter
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
    / "cow160x4-bounded-v0.1"
    / "raw"
    / "session_aggregation.jsonl.gz"
)
CONTRACT_PATH = (
    REPO_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-cow160x4-gzip-reader-privacy-notice-schema-"
    "manifest-lineage-pointer-audit-contract-v0.1-20260723.json"
)
RESULT_JSON_PATH = (
    REPO_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-cow160x4-bounded-audit-result-v0.1-20260723.json"
)
RESULT_MD_PATH = RESULT_JSON_PATH.with_suffix(".md")

TARGET_ID = "cow160x4_session_aggregation_jsonl_gz"
EXPECTED_COMPRESSED_BYTES = 1_328_104_319
EXPECTED_COMPRESSED_MD5 = "1f3897650fb420c97c14ff452398c3f8"

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
EXPECTED_GZIP_MODULE = EXPECTED_BASE_EXECUTABLE.parent / "Lib" / "gzip.py"
EXPECTED_GZIP_MODULE_BYTES = 24_074
EXPECTED_GZIP_MODULE_SHA256 = (
    "8e0a7f850ef481fea41e0de9b52b4a014573b58e500ae83b92e5888d7a061008"
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
EXPECTED_ZLIB_COMPILE_VERSION = "1.3.2"
EXPECTED_ZLIB_RUNTIME_VERSION = "1.3.2"

MAXIMUM_WALL_SECONDS = 300
MAXIMUM_DECOMPRESSED_BYTES_RETURNED = 32 * 1024 * 1024
MAXIMUM_JSONL_LINES = 4_096
MAXIMUM_LINE_BYTES = 256 * 1024
MAXIMUM_OBJECT_KEYS = 256
MAXIMUM_JSON_DEPTH = 4
MAXIMUM_SESSION_UTF8_BYTES = 256
MAXIMUM_SCALAR_STRING_UTF8_BYTES = 16 * 1024
MAXIMUM_NOTICE_KEYS = 16
MAXIMUM_RESULT_BYTES = 256 * 1024

REQUIRED_DECLARED_FIELDS = frozenset(
    {
        "session",
        "src_ip",
        "honeypot_ip",
        "first_seen",
        "last_seen",
        "total_events",
    }
)
SENSITIVE_FIELD_TOKENS = (
    "password",
    "passwd",
    "credential",
    "command",
    "input",
    "url",
    "filename",
    "file_hash",
    "fingerprint",
    "geo",
    "country",
    "payload",
    "message",
)
NOTICE_KEY_TOKENS = (
    "license",
    "licence",
    "notice",
    "copyright",
    "copying",
    "readme",
)


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
    if Path(gzip.__file__).resolve() != EXPECTED_GZIP_MODULE.resolve():
        raise AuditBlocked("gzip_module_path_mismatch")
    if Path(json.__file__).resolve() != EXPECTED_JSON_MODULE.resolve():
        raise AuditBlocked("json_module_path_mismatch")
    if Path(hashlib.__file__).resolve() != EXPECTED_HASHLIB_MODULE.resolve():
        raise AuditBlocked("hashlib_module_path_mismatch")
    if (
        zlib.ZLIB_VERSION != EXPECTED_ZLIB_COMPILE_VERSION
        or zlib.ZLIB_RUNTIME_VERSION != EXPECTED_ZLIB_RUNTIME_VERSION
    ):
        raise AuditBlocked("zlib_version_mismatch")

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
            EXPECTED_GZIP_MODULE,
            EXPECTED_GZIP_MODULE_BYTES,
            EXPECTED_GZIP_MODULE_SHA256,
            "stdlib_gzip_module",
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
    ]
    return {
        "name": "CPython standard-library gzip/json/hashlib reader",
        "python_version": sys.version,
        "zlib_compile_version": zlib.ZLIB_VERSION,
        "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
        "components": components,
        "identity_gate_passed": True,
    }


def _json_depth(value: Any, current: int = 0) -> int:
    if current > MAXIMUM_JSON_DEPTH:
        return current
    if isinstance(value, dict):
        return max(
            [current]
            + [_json_depth(item, current + 1) for item in value.values()]
        )
    if isinstance(value, list):
        return max([current] + [_json_depth(item, current + 1) for item in value])
    return current


def _iter_scalar_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_scalar_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_scalar_strings(item)


def _canonical_digest(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


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
    if authority.get("audit_execution_authorized") is not True:
        raise AuditBlocked("audit_execution_not_authorized")
    if authority.get("gzip_open_authorized") is not True:
        raise AuditBlocked("gzip_open_not_authorized")
    if authority.get("decompression_authorized") is not True:
        raise AuditBlocked("decompression_not_authorized")
    if authority.get("automatic_retry_authorized") is not False:
        raise AuditBlocked("automatic_retry_boundary_missing")
    if authority.get("resume_authorized") is not False:
        raise AuditBlocked("resume_boundary_missing")

    caps = authority.get("caps", {})
    expected_caps = {
        "maximum_wall_seconds": MAXIMUM_WALL_SECONDS,
        "maximum_decompressed_bytes_returned": (
            MAXIMUM_DECOMPRESSED_BYTES_RETURNED
        ),
        "maximum_jsonl_lines": MAXIMUM_JSONL_LINES,
        "maximum_line_bytes": MAXIMUM_LINE_BYTES,
        "maximum_object_keys": MAXIMUM_OBJECT_KEYS,
        "maximum_json_depth": MAXIMUM_JSON_DEPTH,
        "maximum_result_bytes": MAXIMUM_RESULT_BYTES,
    }
    if caps != expected_caps:
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


def _verify_source_identity() -> dict[str, object]:
    if not SOURCE_PATH.is_file():
        raise AuditBlocked("source_missing")
    actual_bytes = SOURCE_PATH.stat().st_size
    if actual_bytes != EXPECTED_COMPRESSED_BYTES:
        raise AuditBlocked("source_size_mismatch")
    actual_md5 = _digest_file(SOURCE_PATH, "md5")
    if actual_md5 != EXPECTED_COMPRESSED_MD5:
        raise AuditBlocked("source_md5_mismatch")
    return {
        "target_id": TARGET_ID,
        "source_key": "session_aggregation.jsonl.gz",
        "compressed_bytes": actual_bytes,
        "compressed_md5": actual_md5,
        "identity_gate_passed": True,
    }


def _schema_and_lineage_probe() -> dict[str, object]:
    started = time.monotonic()
    line_count = 0
    decompressed_bytes = 0
    invalid_json_count = 0
    non_object_count = 0
    missing_required_field_count = 0
    excessive_depth_count = 0
    excessive_key_count = 0
    excessive_scalar_string_count = 0
    invalid_session_count = 0
    sensitive_key_record_count = 0
    notice_envelope_count = 0
    unknown_key_count = 0
    duplicate_session_count = 0
    schema_signatures: Counter[str] = Counter()
    session_digests: set[str] = set()
    pointer_rows: list[str] = []
    event_count_field_count_max = 0

    with gzip.open(SOURCE_PATH, "rb") as handle:
        while line_count < MAXIMUM_JSONL_LINES:
            if time.monotonic() - started > MAXIMUM_WALL_SECONDS:
                raise AuditBlocked("wall_time_cap_exceeded")
            raw = handle.readline(MAXIMUM_LINE_BYTES + 1)
            if not raw:
                break
            if len(raw) > MAXIMUM_LINE_BYTES:
                raise AuditBlocked("line_byte_cap_exceeded")
            decompressed_bytes += len(raw)
            if decompressed_bytes > MAXIMUM_DECOMPRESSED_BYTES_RETURNED:
                raise AuditBlocked("decompressed_byte_cap_exceeded")
            line_count += 1

            try:
                text = raw.decode("utf-8", errors="strict")
                value = json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError):
                invalid_json_count += 1
                continue
            if not isinstance(value, dict):
                non_object_count += 1
                continue
            if len(value) > MAXIMUM_OBJECT_KEYS:
                excessive_key_count += 1
                continue
            if _json_depth(value) > MAXIMUM_JSON_DEPTH:
                excessive_depth_count += 1
                continue
            if any(
                len(item.encode("utf-8")) > MAXIMUM_SCALAR_STRING_UTF8_BYTES
                for item in _iter_scalar_strings(value)
            ):
                excessive_scalar_string_count += 1
                continue

            keys = {str(key) for key in value}
            folded_keys = {key.casefold() for key in keys}
            if any(
                any(token in key for token in SENSITIVE_FIELD_TOKENS)
                for key in folded_keys
            ):
                sensitive_key_record_count += 1
            if any(
                any(token in key for token in NOTICE_KEY_TOKENS)
                for key in folded_keys
            ):
                notice_envelope_count += 1
                if notice_envelope_count > MAXIMUM_NOTICE_KEYS:
                    raise AuditBlocked("notice_key_cap_exceeded")

            if not REQUIRED_DECLARED_FIELDS.issubset(keys):
                missing_required_field_count += 1
            extra_keys = keys - REQUIRED_DECLARED_FIELDS
            unknown_key_count += len(extra_keys)
            event_count_field_count_max = max(
                event_count_field_count_max, len(extra_keys)
            )
            schema_signatures[_canonical_digest(sorted(keys))] += 1

            session = value.get("session")
            if (
                not isinstance(session, str)
                or not session
                or len(session.encode("utf-8")) > MAXIMUM_SESSION_UTF8_BYTES
                or any(ord(char) < 32 or ord(char) == 127 for char in session)
            ):
                invalid_session_count += 1
                continue
            session_digest = hashlib.sha256(session.encode("utf-8")).hexdigest()
            if session_digest in session_digests:
                duplicate_session_count += 1
            session_digests.add(session_digest)

            pointer_candidate = json.dumps(
                {
                    "artifact_md5": EXPECTED_COMPRESSED_MD5,
                    "record_ordinal": line_count,
                    "session_sha256": session_digest,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            if pointer_candidate != json.dumps(
                json.loads(pointer_candidate),
                sort_keys=True,
                separators=(",", ":"),
            ):
                raise AuditBlocked("pointer_canonical_round_trip_failed")
            pointer_rows.append(hashlib.sha256(pointer_candidate.encode()).hexdigest())

    if line_count == 0:
        raise AuditBlocked("empty_bounded_probe")

    structural_failure_count = sum(
        (
            invalid_json_count,
            non_object_count,
            missing_required_field_count,
            excessive_depth_count,
            excessive_key_count,
            excessive_scalar_string_count,
            invalid_session_count,
        )
    )
    minimum_four = len(session_digests) >= 4
    schema_probe_passed = structural_failure_count == 0
    field_isolation_passed = sensitive_key_record_count == 0
    pointer_probe_passed = schema_probe_passed and bool(pointer_rows)

    return {
        "bounded_probe": {
            "line_count": line_count,
            "decompressed_bytes_returned": decompressed_bytes,
            "line_cap": MAXIMUM_JSONL_LINES,
            "decompressed_byte_cap": MAXIMUM_DECOMPRESSED_BYTES_RETURNED,
            "wall_seconds_cap": MAXIMUM_WALL_SECONDS,
            "raw_line_or_value_persisted": False,
        },
        "notice": {
            "notice_envelope_key_count": notice_envelope_count,
            "dedicated_notice_channel_verified": False,
            "record_scope_license_closes_nested_rights": False,
            "nested_notice_gate_passed": False,
        },
        "schema": {
            "invalid_json_count": invalid_json_count,
            "non_object_count": non_object_count,
            "missing_required_field_count": missing_required_field_count,
            "excessive_depth_count": excessive_depth_count,
            "excessive_key_count": excessive_key_count,
            "excessive_scalar_string_count": excessive_scalar_string_count,
            "invalid_session_count": invalid_session_count,
            "schema_signature_count": len(schema_signatures),
            "unknown_or_event_count_field_occurrences": unknown_key_count,
            "maximum_unknown_or_event_count_fields_per_record": (
                event_count_field_count_max
            ),
            "schema_probe_passed": schema_probe_passed,
            "raw_keys_or_values_persisted": False,
        },
        "privacy": {
            "sensitive_key_record_count": sensitive_key_record_count,
            "src_ip_or_honeypot_ip_value_persisted": False,
            "session_value_persisted": False,
            "timestamp_value_persisted": False,
            "credential_command_url_filename_fingerprint_geolocation_payload_or_message_value_persisted": False,
            "field_isolation_probe_passed": field_isolation_passed,
            "full_privacy_gate_passed": False,
        },
        "manifest_lineage": {
            "unique_opaque_session_count_in_bounded_probe": len(session_digests),
            "duplicate_session_count_in_bounded_probe": duplicate_session_count,
            "minimum_four_nonempty_session_candidates_present": minimum_four,
            "one_session_to_one_record_globally_verified": False,
            "duplicate_reconnect_retry_or_campaign_policy_verified": False,
            "statistical_independence_verified": False,
            "lineage_credit": 0,
            "quota_credit": 0,
        },
        "pointer": {
            "candidate_shape": (
                "artifact_md5 + decompressed_record_ordinal + session_sha256"
            ),
            "candidate_count": len(pointer_rows),
            "candidate_aggregate_sha256": _canonical_digest(sorted(pointer_rows)),
            "canonical_in_memory_round_trip_passed": pointer_probe_passed,
            "gzip_random_access_available": False,
            "source_round_trip_globally_verified": False,
            "binding_status": "unbound",
            "pointer_binding_authorized": False,
            "raw_session_or_pointer_persisted": False,
        },
    }


def _write_sanitized_result(result: dict[str, object]) -> None:
    serialized = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if len(serialized.encode("utf-8")) > MAXIMUM_RESULT_BYTES:
        raise AuditBlocked("result_byte_cap_exceeded")
    RESULT_JSON_PATH.write_text(serialized, encoding="utf-8")
    probe = result["probe"]
    markdown = f"""# COW160x4 bounded gzip audit result

Status: `{result['status']}`

| Gate | Result |
|---|---|
| Compressed identity | pass |
| Reader identity | pass |
| Bounded JSONL lines | {probe['bounded_probe']['line_count']} |
| Schema probe | {str(probe['schema']['schema_probe_passed']).lower()} |
| Field-isolation probe | {str(probe['privacy']['field_isolation_probe_passed']).lower()} |
| Nested-notice Gate | false |
| Unique session candidates in bounded probe | {probe['manifest_lineage']['unique_opaque_session_count_in_bounded_probe']} |
| Statistical independence | false |
| Pointer binding | unbound |
| Lineage / quota credit | 0 / 0 |
| Source role / L2 Gate | false / false |

No raw line, field value, session identifier, IP, timestamp, pointer, or local
payload path is persisted.
"""
    if len(markdown.encode("utf-8")) > MAXIMUM_RESULT_BYTES:
        raise AuditBlocked("markdown_result_byte_cap_exceeded")
    RESULT_MD_PATH.write_text(markdown, encoding="utf-8")


def _write_sanitized_failure(reason_code: str) -> None:
    if RESULT_JSON_PATH.exists() or RESULT_MD_PATH.exists():
        return
    result = {
        "schema_version": (
            "project05-llm-editor-l2-cow160x4-bounded-audit-result-v0.1"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed_closed_terminal_no_automatic_retry",
        "target_id": TARGET_ID,
        "reason_code": reason_code,
        "content": {
            "raw_line_key_or_value_persisted": False,
            "session_identifier_persisted": False,
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
            "# COW160x4 bounded gzip audit failure\n\n"
            "Status: `failed_closed_terminal_no_automatic_retry`\n\n"
            f"Reason code: `{reason_code}`\n\n"
            "No raw line, key, value, session identifier, pointer, or local "
            "payload path is persisted. No role or credit changed.\n",
            encoding="utf-8",
        )


def execute_audit(authority_path: Path) -> dict[str, object]:
    authority = _verify_execution_authority(authority_path)
    reader = _verify_reader_identity()
    source = _verify_source_identity()
    probe = _schema_and_lineage_probe()
    status = "bounded_probe_hold_nested_notice_and_full_lineage_unclosed"
    if not probe["schema"]["schema_probe_passed"]:
        status = "fail_closed_schema_probe"
    elif not probe["privacy"]["field_isolation_probe_passed"]:
        status = "fail_closed_sensitive_field_key_detected"
    result: dict[str, object] = {
        "schema_version": (
            "project05-llm-editor-l2-cow160x4-bounded-audit-result-v0.1"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "target_id": TARGET_ID,
        "authority": authority,
        "reader": reader,
        "source_identity": source,
        "probe": probe,
        "scope": {
            "gzip_opened": True,
            "decompressed_content_persisted": False,
            "raw_line_key_or_value_persisted": False,
            "label_or_ground_truth_read": False,
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
                        "gzip_opened": False,
                        "decompressed": False,
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
