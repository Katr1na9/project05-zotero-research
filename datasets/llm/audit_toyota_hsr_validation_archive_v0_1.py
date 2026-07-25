from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import time
import unicodedata
from pathlib import Path
from typing import Any, BinaryIO


TARGET_ID = "toyota_hsr_place_action_validation_archive"
EXPECTED_COMPRESSED_BYTES = 365_983_836
EXPECTED_COMPRESSED_MD5 = "76cb0cab741c3a55eaf662df979f4637"

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TARGET_PATH = (
    REPOSITORY_ROOT
    / "datasets"
    / "llm"
    / "local_audit_cache"
    / "toyota-hsr-placement-bounded-v0.1"
    / "raw"
    / "place_action_validation.tar.gz"
)
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-toyota-hsr-validation-gzip-tar-reader-privacy-outcome-manifest-lineage-pointer-audit-contract-v0.1-20260724.json"
)
READER_AMENDMENT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-toyota-hsr-validation-gzip-tar-reader-tool-amendment-v0.1-20260724.json"
)
RESULT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-toyota-hsr-validation-bounded-archive-audit-result-v0.1-20260724.json"
)

CAPS: dict[str, int | bool] = {
    "maximum_wall_seconds": 300,
    "maximum_compressed_source_bytes": EXPECTED_COMPRESSED_BYTES,
    "maximum_decompressed_stream_bytes": 17_179_869_184,
    "maximum_member_count": 250_000,
    "maximum_member_declared_bytes": 8_589_934_592,
    "maximum_total_declared_member_bytes": 17_179_869_184,
    "maximum_path_utf8_bytes": 1_024,
    "maximum_total_path_utf8_bytes": 33_554_432,
    "maximum_unique_path_digests": 250_000,
    "maximum_pax_header_count_per_member": 128,
    "maximum_pax_header_utf8_bytes_per_member": 262_144,
    "maximum_notice_candidate_count": 64,
    "maximum_notice_bytes_per_member": 65_536,
    "maximum_total_notice_bytes": 524_288,
    "maximum_notice_token_count": 8_192,
    "maximum_manifest_group_candidates": 4_096,
    "minimum_outcome_blind_group_candidates": 4,
    "maximum_result_bytes": 262_144,
    "maximum_result_file_count": 1,
    "maximum_execute_count": 1,
    "nested_archive_open_allowed": False,
    "extract_to_disk_allowed": False,
    "persist_raw_path_notice_or_member_content_allowed": False,
    "automatic_retry_allowed": False,
    "resume_allowed": False,
}

READER_COMPONENTS = (
    {
        "name": "venv_python_executable",
        "path": Path(os.environ["LOCALAPPDATA"])
        / "hermes"
        / "hermes-agent"
        / "venv"
        / "Scripts"
        / "python.exe",
        "bytes": 45_568,
        "sha256": "0cf37e7be6ee71edef78e6c81f7dcef58237b204af36d6e83393c96538a52372",
    },
    {
        "name": "base_python_executable",
        "path": Path(os.environ["APPDATA"])
        / "uv"
        / "python"
        / "cpython-3.11-windows-x86_64-none"
        / "python.exe",
        "bytes": 91_648,
        "sha256": "ae7e969410d751d010c2ca03394fe5c53230fbf48ca7d368b897e455eca14fba",
    },
    {
        "name": "python311_dll",
        "path": Path(os.environ["APPDATA"])
        / "uv"
        / "python"
        / "cpython-3.11-windows-x86_64-none"
        / "python311.dll",
        "bytes": 5_842_944,
        "sha256": "e1b53c741751563eca9eac70378de5be36994adac8c27e8ec375971579e23b50",
    },
    {
        "name": "stdlib_gzip_module",
        "path": Path(os.environ["APPDATA"])
        / "uv"
        / "python"
        / "cpython-3.11-windows-x86_64-none"
        / "Lib"
        / "gzip.py",
        "bytes": 24_074,
        "sha256": "8e0a7f850ef481fea41e0de9b52b4a014573b58e500ae83b92e5888d7a061008",
    },
    {
        "name": "stdlib_tarfile_module",
        "path": Path(os.environ["APPDATA"])
        / "uv"
        / "python"
        / "cpython-3.11-windows-x86_64-none"
        / "Lib"
        / "tarfile.py",
        "bytes": 111_943,
        "sha256": "8d54813fe9ede7fcef47aff61d26976eac7512a41873d36ac2fa1b610a0fd835",
    },
    {
        "name": "stdlib_hashlib_module",
        "path": Path(os.environ["APPDATA"])
        / "uv"
        / "python"
        / "cpython-3.11-windows-x86_64-none"
        / "Lib"
        / "hashlib.py",
        "bytes": 11_765,
        "sha256": "e2bffb462e4d43e6637b9450e259e8ba2a56626ba3037d68aa1cee68b3f61d4a",
    },
    {
        "name": "stdlib_json_module",
        "path": Path(os.environ["APPDATA"])
        / "uv"
        / "python"
        / "cpython-3.11-windows-x86_64-none"
        / "Lib"
        / "json"
        / "__init__.py",
        "bytes": 14_020,
        "sha256": "d5d41e2c29049515d295d81a6d40b4890fbec8d8482cfb401630f8ef2f77e4d5",
    },
)

EXPECTED_PYTHON_VERSION = (
    "3.11.15 (main, Jun 23 2026, 15:20:37) [MSC v.1944 64 bit (AMD64)]"
)
EXPECTED_ZLIB_COMPILE_VERSION = "1.3.2"
EXPECTED_ZLIB_RUNTIME_VERSION = "1.3.2"

NOTICE_BASENAMES = {
    "license",
    "license.txt",
    "license.md",
    "licence",
    "licence.txt",
    "notice",
    "notice.txt",
    "copying",
    "copying.txt",
    "copyright",
    "copyright.txt",
    "readme",
    "readme.txt",
    "readme.md",
    "citation",
    "citation.cff",
}
NOTICE_TOKENS = {
    "license",
    "licence",
    "copyright",
    "notice",
    "copying",
    "attribution",
    "creative",
    "commons",
    "third-party",
    "third_party",
}
PROTECTED_OUTCOME_SPLIT_TOKENS = {
    "success",
    "successful",
    "failure",
    "failed",
    "anomaly",
    "anomalous",
    "collision",
    "label",
    "labels",
    "groundtruth",
    "ground_truth",
    "truth",
    "train",
    "training",
    "validation",
    "validate",
    "test",
    "testing",
    "split",
    "class",
    "positive",
    "negative",
}
PRIVACY_PATH_TOKENS = {
    "user",
    "username",
    "person",
    "human",
    "email",
    "phone",
    "address",
    "location",
    "host",
    "hostname",
    "device",
    "serial",
    "ip",
    "mac",
    "credential",
    "password",
    "secret",
}
CONTENT_EXCLUSION_TOKENS = {
    "rgb",
    "image",
    "images",
    "camera",
    "depth",
    "pointcloud",
    "point_cloud",
    "calibration",
    "telemetry",
    "annotation",
    "annotations",
    "model",
    "models",
    "mesh",
    "texture",
    "video",
}
CONTENT_EXCLUSION_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".gif",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".pcd",
    ".ply",
    ".obj",
    ".stl",
    ".bag",
    ".npy",
    ".npz",
    ".bin",
}
NESTED_ARCHIVE_SUFFIXES = {
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".tgz",
    ".tar.gz",
    ".gz",
    ".bz2",
    ".xz",
}
TRIAL_SEGMENT_RE = re.compile(
    r"^(?:trial|run|episode|session)[-_]?[a-z0-9][a-z0-9._-]{0,127}$",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


class AuditFailure(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class LimitedDecompressedReader(io.RawIOBase):
    def __init__(self, source: BinaryIO, start_time: float) -> None:
        self._source = source
        self._start_time = start_time
        self.bytes_read = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def _check_wall(self) -> None:
        if time.monotonic() - self._start_time > int(CAPS["maximum_wall_seconds"]):
            raise AuditFailure("wall_time_cap_exceeded")

    def read(self, size: int = -1) -> bytes:
        self._check_wall()
        data = self._source.read(size)
        self.bytes_read += len(data)
        if self.bytes_read > int(CAPS["maximum_decompressed_stream_bytes"]):
            raise AuditFailure("decompressed_stream_byte_cap_exceeded")
        return data

    def readinto(self, buffer: bytearray) -> int:
        data = self.read(len(buffer))
        length = len(data)
        buffer[:length] = data
        return length


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def verify_reader_identity() -> dict[str, Any]:
    observed_components: list[dict[str, Any]] = []
    for component in READER_COMPONENTS:
        path = Path(component["path"])
        if not path.is_file():
            raise AuditFailure("reader_component_missing")
        observed_size = path.stat().st_size
        observed_sha256 = sha256_file(path)
        if observed_size != int(component["bytes"]):
            raise AuditFailure("reader_component_size_mismatch")
        if observed_sha256 != str(component["sha256"]):
            raise AuditFailure("reader_component_sha256_mismatch")
        observed_components.append(
            {
                "name": component["name"],
                "bytes": observed_size,
                "sha256": observed_sha256,
            }
        )

    if sys.version.replace("\n", " ") != EXPECTED_PYTHON_VERSION:
        raise AuditFailure("python_version_mismatch")
    if gzip.__file__ is None or tarfile.__file__ is None:
        raise AuditFailure("stdlib_reader_module_location_missing")

    import zlib

    if zlib.ZLIB_VERSION != EXPECTED_ZLIB_COMPILE_VERSION:
        raise AuditFailure("zlib_compile_version_mismatch")
    if zlib.ZLIB_RUNTIME_VERSION != EXPECTED_ZLIB_RUNTIME_VERSION:
        raise AuditFailure("zlib_runtime_version_mismatch")

    return {
        "reader_component_count": len(observed_components),
        "all_component_hashes_match": True,
        "python_version_matches": True,
        "zlib_compile_version": zlib.ZLIB_VERSION,
        "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
    }


def require_bool(value: Any, expected: bool, reason_code: str) -> None:
    if type(value) is not bool or value is not expected:
        raise AuditFailure(reason_code)


def require_int(value: Any, expected: int, reason_code: str) -> None:
    if type(value) is not int or value != expected:
        raise AuditFailure(reason_code)


def require_str(value: Any, expected: str, reason_code: str) -> None:
    if type(value) is not str or value != expected:
        raise AuditFailure(reason_code)


def validate_authority(authority_path: Path) -> dict[str, Any]:
    if not authority_path.is_file():
        raise AuditFailure("execution_authority_missing")
    try:
        authority = json.loads(authority_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditFailure("execution_authority_invalid_json") from exc

    require_str(authority.get("status"), "authorized_once", "authority_status_mismatch")
    require_str(authority.get("target_id"), TARGET_ID, "authority_target_mismatch")
    require_int(
        authority.get("execution_count_authorized"),
        1,
        "authority_execute_count_mismatch",
    )
    require_int(
        authority.get("execution_count_consumed"),
        0,
        "authority_already_consumed",
    )
    require_bool(
        authority.get("audit_execution_authorized"),
        True,
        "audit_not_authorized",
    )
    require_bool(
        authority.get("gzip_open_authorized"),
        True,
        "gzip_open_not_authorized",
    )
    require_bool(
        authority.get("tar_header_and_member_path_read_authorized"),
        True,
        "tar_header_read_not_authorized",
    )
    require_bool(
        authority.get("bounded_notice_member_read_authorized"),
        True,
        "notice_read_not_authorized",
    )
    require_bool(
        authority.get("automatic_retry_authorized"),
        False,
        "automatic_retry_cannot_be_authorized",
    )
    require_bool(
        authority.get("resume_authorized"),
        False,
        "resume_cannot_be_authorized",
    )
    require_bool(
        authority.get("nested_archive_open_authorized"),
        False,
        "nested_archive_open_cannot_be_authorized",
    )
    require_bool(
        authority.get("archive_extraction_authorized"),
        False,
        "archive_extraction_cannot_be_authorized",
    )

    hashes = authority.get("pinned_hashes")
    if not isinstance(hashes, dict):
        raise AuditFailure("authority_hashes_missing")
    require_str(
        hashes.get("script_sha256"),
        sha256_file(Path(__file__).resolve()),
        "authority_script_sha256_mismatch",
    )
    require_str(
        hashes.get("contract_sha256"),
        sha256_file(CONTRACT_PATH),
        "authority_contract_sha256_mismatch",
    )
    require_str(
        hashes.get("reader_amendment_sha256"),
        sha256_file(READER_AMENDMENT_PATH),
        "authority_reader_sha256_mismatch",
    )

    authority_caps = authority.get("caps")
    if authority_caps != CAPS:
        raise AuditFailure("authority_caps_mismatch")
    return authority


def verify_source_identity_before_open() -> dict[str, Any]:
    if not TARGET_PATH.is_file():
        raise AuditFailure("target_missing")
    observed_bytes = TARGET_PATH.stat().st_size
    if observed_bytes != EXPECTED_COMPRESSED_BYTES:
        raise AuditFailure("compressed_size_mismatch")
    observed_md5 = md5_file(TARGET_PATH)
    if observed_md5 != EXPECTED_COMPRESSED_MD5:
        raise AuditFailure("compressed_md5_mismatch")
    return {
        "compressed_bytes": observed_bytes,
        "compressed_md5": observed_md5,
        "identity_verified": True,
    }


def path_tokens(normalized_path: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(normalized_path)}


def has_any_suffix(lower_path: str, suffixes: set[str]) -> bool:
    return any(lower_path.endswith(suffix) for suffix in suffixes)


def notice_candidate(normalized_path: str) -> bool:
    basename = normalized_path.rsplit("/", 1)[-1].lower()
    return basename in NOTICE_BASENAMES


def extract_outcome_blind_group_candidate(normalized_path: str) -> str | None:
    segments = [segment for segment in normalized_path.split("/") if segment]
    for index, segment in enumerate(segments):
        lower = segment.lower()
        tokens = path_tokens(lower)
        if tokens & PROTECTED_OUTCOME_SPLIT_TOKENS:
            continue
        if TRIAL_SEGMENT_RE.fullmatch(lower):
            return lower
        if (
            lower.isdigit()
            and index > 0
            and segments[index - 1].lower() in {"trial", "run", "episode", "session"}
        ):
            return f"{segments[index - 1].lower()}:{lower}"
    return None


def pax_header_size(member: tarfile.TarInfo) -> tuple[int, int]:
    count = len(member.pax_headers)
    encoded = canonical_json_bytes(member.pax_headers)
    return count, len(encoded)


def bounded_notice_probe(
    archive: tarfile.TarFile,
    member: tarfile.TarInfo,
    counters: dict[str, int],
    notice_hasher: hashlib._Hash,
) -> None:
    if counters["notice_candidate_count"] >= int(CAPS["maximum_notice_candidate_count"]):
        raise AuditFailure("notice_candidate_cap_exceeded")
    if member.size < 0 or member.size > int(CAPS["maximum_notice_bytes_per_member"]):
        raise AuditFailure("notice_member_byte_cap_exceeded")
    if (
        counters["notice_bytes_read"] + member.size
        > int(CAPS["maximum_total_notice_bytes"])
    ):
        raise AuditFailure("total_notice_byte_cap_exceeded")

    extracted = archive.extractfile(member)
    if extracted is None:
        raise AuditFailure("notice_member_unreadable")
    data = extracted.read(int(CAPS["maximum_notice_bytes_per_member"]) + 1)
    if len(data) > int(CAPS["maximum_notice_bytes_per_member"]):
        raise AuditFailure("notice_member_returned_over_cap")
    counters["notice_candidate_count"] += 1
    counters["notice_bytes_read"] += len(data)

    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        counters["notice_utf8_failure_count"] += 1
        return

    tokens = path_tokens(text)
    counters["notice_token_count"] += len(tokens)
    if counters["notice_token_count"] > int(CAPS["maximum_notice_token_count"]):
        raise AuditFailure("notice_token_cap_exceeded")
    counters["notice_rights_token_match_count"] += len(tokens & NOTICE_TOKENS)
    notice_hasher.update(hashlib.sha256(data).digest())


def audit_archive() -> dict[str, Any]:
    start_time = time.monotonic()
    counters = {
        "member_count": 0,
        "regular_member_count": 0,
        "directory_member_count": 0,
        "symlink_member_count": 0,
        "hardlink_member_count": 0,
        "special_member_count": 0,
        "declared_member_bytes": 0,
        "path_utf8_bytes": 0,
        "duplicate_path_digest_count": 0,
        "unsafe_path_count": 0,
        "pax_header_count": 0,
        "pax_header_utf8_bytes": 0,
        "nested_archive_member_count": 0,
        "protected_outcome_split_path_count": 0,
        "privacy_path_token_count": 0,
        "excluded_content_member_count": 0,
        "notice_candidate_count": 0,
        "notice_bytes_read": 0,
        "notice_utf8_failure_count": 0,
        "notice_token_count": 0,
        "notice_rights_token_match_count": 0,
        "manifest_candidate_occurrence_count": 0,
    }
    path_digests: set[bytes] = set()
    group_digests: set[bytes] = set()
    group_occurrence_digests: list[bytes] = []
    notice_hasher = hashlib.sha256()

    with TARGET_PATH.open("rb") as raw_handle:
        with gzip.GzipFile(fileobj=raw_handle, mode="rb") as gzip_handle:
            limited = LimitedDecompressedReader(gzip_handle, start_time)
            with tarfile.open(fileobj=limited, mode="r|") as archive:
                for member in archive:
                    if time.monotonic() - start_time > int(CAPS["maximum_wall_seconds"]):
                        raise AuditFailure("wall_time_cap_exceeded")

                    counters["member_count"] += 1
                    if counters["member_count"] > int(CAPS["maximum_member_count"]):
                        raise AuditFailure("member_count_cap_exceeded")
                    if member.size < 0:
                        raise AuditFailure("negative_member_size")
                    if member.size > int(CAPS["maximum_member_declared_bytes"]):
                        raise AuditFailure("member_declared_byte_cap_exceeded")
                    counters["declared_member_bytes"] += member.size
                    if (
                        counters["declared_member_bytes"]
                        > int(CAPS["maximum_total_declared_member_bytes"])
                    ):
                        raise AuditFailure("total_declared_member_byte_cap_exceeded")

                    try:
                        normalized_path = unicodedata.normalize("NFKC", member.name)
                        path_bytes = normalized_path.encode("utf-8", errors="strict")
                    except (UnicodeError, ValueError) as exc:
                        raise AuditFailure("member_path_encoding_failure") from exc
                    if len(path_bytes) > int(CAPS["maximum_path_utf8_bytes"]):
                        raise AuditFailure("member_path_byte_cap_exceeded")
                    counters["path_utf8_bytes"] += len(path_bytes)
                    if (
                        counters["path_utf8_bytes"]
                        > int(CAPS["maximum_total_path_utf8_bytes"])
                    ):
                        raise AuditFailure("total_path_byte_cap_exceeded")

                    canonical_path = normalized_path.replace("\\", "/")
                    segments = [segment for segment in canonical_path.split("/") if segment]
                    if (
                        "\x00" in canonical_path
                        or canonical_path.startswith("/")
                        or re.match(r"^[A-Za-z]:/", canonical_path)
                        or any(segment == ".." for segment in segments)
                    ):
                        counters["unsafe_path_count"] += 1

                    path_digest = hashlib.sha256(path_bytes).digest()
                    if path_digest in path_digests:
                        counters["duplicate_path_digest_count"] += 1
                    else:
                        path_digests.add(path_digest)
                    if len(path_digests) > int(CAPS["maximum_unique_path_digests"]):
                        raise AuditFailure("unique_path_digest_cap_exceeded")

                    pax_count, pax_bytes = pax_header_size(member)
                    if pax_count > int(CAPS["maximum_pax_header_count_per_member"]):
                        raise AuditFailure("pax_header_count_cap_exceeded")
                    if pax_bytes > int(CAPS["maximum_pax_header_utf8_bytes_per_member"]):
                        raise AuditFailure("pax_header_byte_cap_exceeded")
                    counters["pax_header_count"] += pax_count
                    counters["pax_header_utf8_bytes"] += pax_bytes

                    lower_path = canonical_path.lower()
                    tokens = path_tokens(lower_path)
                    if tokens & PROTECTED_OUTCOME_SPLIT_TOKENS:
                        counters["protected_outcome_split_path_count"] += 1
                    counters["privacy_path_token_count"] += len(
                        tokens & PRIVACY_PATH_TOKENS
                    )
                    if (
                        tokens & CONTENT_EXCLUSION_TOKENS
                        or has_any_suffix(lower_path, CONTENT_EXCLUSION_SUFFIXES)
                    ):
                        counters["excluded_content_member_count"] += 1
                    if has_any_suffix(lower_path, NESTED_ARCHIVE_SUFFIXES):
                        counters["nested_archive_member_count"] += 1

                    if member.isreg():
                        counters["regular_member_count"] += 1
                    elif member.isdir():
                        counters["directory_member_count"] += 1
                    elif member.issym():
                        counters["symlink_member_count"] += 1
                    elif member.islnk():
                        counters["hardlink_member_count"] += 1
                    else:
                        counters["special_member_count"] += 1

                    if (
                        member.isreg()
                        and notice_candidate(canonical_path)
                        and not has_any_suffix(lower_path, NESTED_ARCHIVE_SUFFIXES)
                    ):
                        bounded_notice_probe(
                            archive,
                            member,
                            counters,
                            notice_hasher,
                        )

                    group_candidate = extract_outcome_blind_group_candidate(
                        canonical_path
                    )
                    if group_candidate is not None:
                        counters["manifest_candidate_occurrence_count"] += 1
                        group_digest = hashlib.sha256(
                            b"toyota-hsr-outcome-blind-group-v0.1\x00"
                            + group_candidate.encode("utf-8")
                        ).digest()
                        group_digests.add(group_digest)
                        group_occurrence_digests.append(group_digest)
                        if len(group_digests) > int(
                            CAPS["maximum_manifest_group_candidates"]
                        ):
                            raise AuditFailure("manifest_group_candidate_cap_exceeded")

    manifest_aggregate_digest = hashlib.sha256(
        b"".join(sorted(group_digests))
    ).hexdigest()
    occurrence_digest = hashlib.sha256(
        b"".join(sorted(group_occurrence_digests))
    ).hexdigest()
    notice_aggregate_digest = notice_hasher.hexdigest()
    unique_groups = len(group_digests)

    outcome_blind_candidate_manifest_constructed = (
        unique_groups >= int(CAPS["minimum_outcome_blind_group_candidates"])
        and counters["unsafe_path_count"] == 0
    )
    nested_notice_gate = (
        counters["notice_candidate_count"] > 0
        and counters["notice_utf8_failure_count"] == 0
        and counters["notice_rights_token_match_count"] > 0
        and counters["nested_archive_member_count"] == 0
    )
    privacy_gate = (
        counters["unsafe_path_count"] == 0
        and counters["symlink_member_count"] == 0
        and counters["hardlink_member_count"] == 0
        and counters["special_member_count"] == 0
    )

    return {
        "status": "bounded_archive_probe_complete_hold_source_role_not_authorized",
        "target_id": TARGET_ID,
        "reader": {
            "gzip_tar_stream_completed": True,
            "decompressed_stream_bytes": limited.bytes_read,
        },
        "aggregate_counts": counters,
        "aggregate_digests": {
            "unique_path_set_sha256": hashlib.sha256(
                b"".join(sorted(path_digests))
            ).hexdigest(),
            "manifest_group_set_sha256": manifest_aggregate_digest,
            "manifest_group_occurrences_sha256": occurrence_digest,
            "notice_content_set_sha256": notice_aggregate_digest,
        },
        "manifest": {
            "candidate_group_count": unique_groups,
            "candidate_occurrence_count": counters[
                "manifest_candidate_occurrence_count"
            ],
            "minimum_required": int(
                CAPS["minimum_outcome_blind_group_candidates"]
            ),
            "outcome_split_tokens_excluded_from_group_keys": True,
            "candidate_manifest_constructed": outcome_blind_candidate_manifest_constructed,
            "external_validation_and_success_composition_resolved": False,
            "lineage_independence_verified": False,
            "lineage_credit": 0,
        },
        "gates": {
            "nested_notice_gate": nested_notice_gate,
            "privacy_header_gate": privacy_gate,
            "outcome_blind_candidate_manifest_gate": outcome_blind_candidate_manifest_constructed,
            "external_outcome_composition_gate": False,
            "lineage_independence_gate": False,
            "pointer_binding_gate": False,
            "source_role_gate": False,
        },
        "pointer": {
            "binding_status": "unbound",
            "pointer_candidates_emitted": 0,
            "bound_case_evidence_emitted": 0,
        },
        "authority": {
            "source_role_approved": False,
            "effective_catalog_written": False,
            "family_credit": 0,
            "lineage_credit": 0,
            "sample_credit": 0,
            "quota_credit": 0,
            "l2_gate_passed": False,
            "automatic_next_stage_authorized": False,
        },
        "sanitization": {
            "raw_member_path_persisted": False,
            "raw_notice_text_persisted": False,
            "ordinary_member_content_persisted": False,
            "per_group_identifier_or_digest_persisted": False,
            "image_depth_outcome_split_or_annotation_content_read": False,
            "nested_archive_opened": False,
            "archive_extracted": False,
        },
    }


def write_sanitized_result(result: dict[str, Any]) -> None:
    if RESULT_PATH.exists():
        raise AuditFailure("result_already_exists")
    encoded = canonical_json_bytes(result) + b"\n"
    if len(encoded) > int(CAPS["maximum_result_bytes"]):
        raise AuditFailure("sanitized_result_byte_cap_exceeded")
    RESULT_PATH.write_bytes(encoded)


def execute(authority_path: Path) -> int:
    started = time.monotonic()
    reason_code: str | None = None
    source_opened = False
    archive_opened = False
    try:
        reader_result = verify_reader_identity()
        validate_authority(authority_path)
        source_identity = verify_source_identity_before_open()
        source_opened = True
        archive_opened = True
        archive_result = audit_archive()
        result = {
            "schema_version": "project05-llm-editor-l2-toyota-hsr-validation-bounded-archive-audit-result-v0.1",
            "result_kind": "sanitized_aggregate_only",
            "reader_identity": reader_result,
            "source_identity": source_identity,
            "archive_probe": archive_result,
            "execution": {
                "execute_count": 1,
                "wall_seconds": round(time.monotonic() - started, 3),
                "automatic_retry_performed": False,
                "source_opened": source_opened,
                "archive_opened": archive_opened,
                "hard_stop_required": True,
            },
        }
        write_sanitized_result(result)
        return 0
    except AuditFailure as exc:
        reason_code = exc.reason_code
    except (OSError, EOFError, tarfile.TarError, gzip.BadGzipFile):
        reason_code = "sanitized_reader_or_io_failure"
    except Exception:
        reason_code = "sanitized_unexpected_failure"

    failure = {
        "schema_version": "project05-llm-editor-l2-toyota-hsr-validation-bounded-archive-audit-result-v0.1",
        "result_kind": "sanitized_terminal_failure",
        "status": "failed_closed_no_automatic_retry",
        "target_id": TARGET_ID,
        "reason_code": reason_code,
        "execution": {
            "execute_count": 1,
            "wall_seconds": round(time.monotonic() - started, 3),
            "source_opened": source_opened,
            "archive_opened": archive_opened,
            "automatic_retry_performed": False,
            "hard_stop_required": True,
        },
        "pointer": {
            "binding_status": "unbound",
            "pointer_candidates_emitted": 0,
        },
        "authority": {
            "source_role_approved": False,
            "effective_catalog_written": False,
            "family_credit": 0,
            "lineage_credit": 0,
            "sample_credit": 0,
            "quota_credit": 0,
            "l2_gate_passed": False,
        },
        "sanitization": {
            "raw_member_path_persisted": False,
            "raw_notice_text_persisted": False,
            "ordinary_member_content_persisted": False,
            "nested_archive_opened": False,
            "archive_extracted": False,
        },
    }
    try:
        write_sanitized_result(failure)
    except AuditFailure:
        pass
    return 2


def plan() -> int:
    reader_result = verify_reader_identity()
    output = {
        "status": "plan_reader_identity_only_target_not_statted_or_opened",
        "target_id": TARGET_ID,
        "reader_identity": reader_result,
        "contract_exists": CONTRACT_PATH.is_file(),
        "reader_amendment_exists": READER_AMENDMENT_PATH.is_file(),
        "target_statted_or_opened": False,
        "audit_executed": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("plan", "execute"), required=True)
    parser.add_argument("--authority-json", type=Path)
    args = parser.parse_args()

    if args.mode == "plan":
        if args.authority_json is not None:
            raise SystemExit("plan mode does not accept an authority")
        return plan()
    if args.authority_json is None:
        raise SystemExit("execute mode requires --authority-json")
    return execute(args.authority_json.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
