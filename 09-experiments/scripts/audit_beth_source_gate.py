#!/usr/bin/env python3
"""Bounded BETH v3 single-file acquisition and read-only source-gate audit."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import math
import os
import re
import stat
import unicodedata
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, BinaryIO


DATASET_REF = "katehighnam/beth-dataset"
DATASET_VERSION_NUMBER = 3
ALLOWLISTED_FILE = "labelled_2021may-ip-10-100-1-105.csv"
ALLOWLISTED_TRANSPORT_ZIP = f"{ALLOWLISTED_FILE}.zip"
MAXIMUM_DOWNLOADED_BYTES = 512 * 1024 * 1024
MAXIMUM_COMPRESSION_RATIO = 100
MAXIMUM_METADATA_BYTES = 2 * 1024 * 1024
MAXIMUM_LEGALCODE_BYTES = 64 * 1024
CC0_LEGALCODE_SHA256 = "A2010F343487D3F7618AFFE54F789F5487602331C0A8D03F49E9A7C547CF0499"
DOWNLOAD_ENDPOINT = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "katehighnam/beth-dataset"
)
METADATA_VIEW_URL = (
    "https://www.kaggle.com/api/v1/datasets/view/katehighnam/beth-dataset"
    "?datasetVersionNumber=3"
)
METADATA_FILES_URL = (
    "https://www.kaggle.com/api/v1/datasets/list/katehighnam/beth-dataset"
    "?datasetVersionNumber=3&pageSize=100"
)
CC0_LEGALCODE_URL = (
    "https://creativecommons.org/publicdomain/zero/1.0/legalcode.txt"
)
SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
CONTRACT_PATH = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "contracts"
    / "beth-source-gate-contract-v0.2.json"
)
PAGE_EXTRACT_PATH = (
    EXPERIMENT_ROOT.parent
    / "08-writing"
    / "llm-evidence-compiler-positive-source-gap-audit-v0.1-20260718"
    / "extract-02-beth-kaggle.json"
)
PROTECTED_LOCK_PATH = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp4"
    / "generated"
    / "retrieval-v0.1"
    / "protected-signature-lock-v0.1.json"
)
PROHIBITED_SUPERVISION_FIELDS = frozenset(
    {"sus", "evil", "original_split", "filename", "host_role", "attack_narrative"}
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalized_text(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())


def hashed_character_ngrams(value: str, n: int) -> set[str]:
    text = normalized_text(value)
    if not text:
        return set()
    grams = {text} if len(text) < n else {
        text[index : index + n] for index in range(len(text) - n + 1)
    }
    return {sha256_bytes(gram.encode("utf-8")) for gram in grams}


def build_download_url(
    dataset_ref: str,
    version: int,
    file_name: str,
    max_bytes: int,
) -> str:
    if dataset_ref != DATASET_REF:
        raise ValueError("BETH dataset reference is not allowlisted")
    if version != DATASET_VERSION_NUMBER:
        raise ValueError("BETH dataset version must be exactly 3")
    if file_name != ALLOWLISTED_FILE:
        raise ValueError("BETH source file is not allowlisted")
    if max_bytes != MAXIMUM_DOWNLOADED_BYTES:
        raise ValueError("BETH byte cap must remain exactly 512 MiB")
    query = urllib.parse.urlencode(
        {"datasetVersionNumber": version, "fileName": file_name}
    )
    return f"{DOWNLOAD_ENDPOINT}?{query}"


def load_kaggle_authorization(
    *,
    home: Path | None = None,
    environ: dict[str, str] | None = None,
) -> str:
    environment = os.environ if environ is None else environ
    username = environment.get("KAGGLE_USERNAME", "").strip()
    key = environment.get("KAGGLE_KEY", "").strip()
    if bool(username) != bool(key):
        raise PermissionError("both KAGGLE_USERNAME and KAGGLE_KEY are required")
    if not username:
        base = Path.home() if home is None else Path(home)
        config_path = base / ".kaggle" / "kaggle.json"
        if not config_path.is_file():
            raise PermissionError("Kaggle credentials are unavailable outside the repository")
        if config_path.stat().st_size > 16 * 1024:
            raise PermissionError("Kaggle credential file is unexpectedly large")
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PermissionError("Kaggle credential file cannot be parsed") from error
        username = str(config.get("username") or "").strip()
        key = str(config.get("key") or "").strip()
    if not username or not key:
        raise PermissionError("Kaggle username/key credentials are incomplete")
    encoded = base64.b64encode(f"{username}:{key}".encode("utf-8")).decode("ascii")
    return f"Basic {encoded}"


def copy_bounded_stream(
    stream: BinaryIO,
    destination: Path,
    max_bytes: int = MAXIMUM_DOWNLOADED_BYTES,
    *,
    chunk_size: int = 1024 * 1024,
) -> dict[str, Any]:
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite source file: {destination}")
    temporary = destination.with_name(destination.name + ".part")
    if temporary.exists():
        raise FileExistsError(f"partial source file already exists: {temporary}")
    if max_bytes <= 0 or chunk_size <= 0:
        raise ValueError("byte and chunk limits must be positive")
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    try:
        with temporary.open("xb") as output:
            while True:
                chunk = stream.read(min(chunk_size, max_bytes - total + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("retrieval exceeds the authorized byte cap")
                output.write(chunk)
                digest.update(chunk)
        temporary.replace(destination)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise
    return {
        "bytes": total,
        "sha256": digest.hexdigest().upper(),
        "path": destination.as_posix(),
    }


def _response_names(final_url: str, content_disposition: str) -> set[str]:
    names: set[str] = set()
    final_name = Path(urllib.parse.unquote(urllib.parse.urlparse(final_url).path)).name
    if final_name:
        names.add(final_name)
    for match in re.finditer(
        r"filename\*?=(?:UTF-8''|\")?([^\";]+)",
        content_disposition or "",
        flags=re.IGNORECASE,
    ):
        names.add(urllib.parse.unquote(match.group(1).strip()))
    return names


def _redacted_response_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, "", "")
    )


def _validate_single_member_zip(archive_path: Path) -> zipfile.ZipInfo:
    try:
        with zipfile.ZipFile(archive_path, "r") as bundle:
            members = bundle.infolist()
            if len(members) != 1:
                raise ValueError("BETH transport ZIP must contain exactly one member")
            member = members[0]
            if member.filename != ALLOWLISTED_FILE:
                raise ValueError("BETH transport ZIP member is not allowlisted")
            if member.is_dir() or Path(member.filename).name != member.filename:
                raise ValueError("BETH transport ZIP member must be a root-level file")
            if member.flag_bits & 0x1:
                raise ValueError("BETH transport ZIP member must not be encrypted")
            unix_mode = (member.external_attr >> 16) & 0xFFFF
            if stat.S_IFMT(unix_mode) == stat.S_IFLNK:
                raise ValueError("BETH transport ZIP member must not be a symbolic link")
            if member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError("BETH transport ZIP compression method is not allowlisted")
            if member.compress_size < 0 or member.compress_size > MAXIMUM_DOWNLOADED_BYTES:
                raise ValueError("BETH compressed member exceeds the byte cap")
            if member.file_size < 0 or member.file_size > MAXIMUM_DOWNLOADED_BYTES:
                raise ValueError("BETH uncompressed member exceeds the byte cap")
            if member.file_size and member.compress_size == 0:
                raise ValueError("BETH transport ZIP has an invalid compression ratio")
            ratio = member.file_size / max(member.compress_size, 1)
            if ratio > MAXIMUM_COMPRESSION_RATIO:
                raise ValueError("BETH transport ZIP exceeds the compression-ratio cap")
            return member
    except zipfile.BadZipFile as error:
        raise ValueError("BETH transport response is not a valid ZIP") from error


def _extract_single_member_zip(
    archive_path: Path,
    destination: Path,
) -> dict[str, Any]:
    member = _validate_single_member_zip(archive_path)
    try:
        with zipfile.ZipFile(archive_path, "r") as bundle:
            with bundle.open(member, "r") as source:
                copied = copy_bounded_stream(
                    source,
                    destination,
                    max_bytes=MAXIMUM_DOWNLOADED_BYTES,
                )
    except (zipfile.BadZipFile, RuntimeError) as error:
        Path(destination).unlink(missing_ok=True)
        Path(str(destination) + ".part").unlink(missing_ok=True)
        raise ValueError("BETH transport ZIP failed integrity validation") from error
    return copied


def retrieve_single_file(
    destination: Path,
    *,
    opener=urllib.request.urlopen,
    timeout: int = 90,
    authorization: str | None = None,
) -> dict[str, Any]:
    requested_url = build_download_url(
        DATASET_REF,
        DATASET_VERSION_NUMBER,
        ALLOWLISTED_FILE,
        MAXIMUM_DOWNLOADED_BYTES,
    )
    auth_header = authorization or load_kaggle_authorization()
    if not auth_header.startswith("Basic "):
        raise PermissionError("unsupported Kaggle authorization scheme")
    request = urllib.request.Request(
        requested_url,
        headers={
            "User-Agent": "Project05-BETH-bounded-source-gate/0.1",
            "Accept": "text/csv,application/octet-stream;q=0.8,*/*;q=0.1",
            "Accept-Encoding": "identity",
            "Authorization": auth_header,
        },
    )
    destination = Path(destination)
    archive_path = destination.with_name(destination.name + ".zip")
    transport: dict[str, Any]
    try:
        with opener(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            if status != 200:
                raise ValueError(f"BETH retrieval returned HTTP {status}")
            headers = response.headers
            declared = headers.get("Content-Length")
            if declared is not None:
                try:
                    declared_bytes = int(declared)
                except ValueError as error:
                    raise ValueError("BETH Content-Length is invalid") from error
                if declared_bytes < 0 or declared_bytes > MAXIMUM_DOWNLOADED_BYTES:
                    raise ValueError("BETH declared response exceeds the byte cap")
            final_url = response.geturl()
            disposition = headers.get("Content-Disposition", "")
            response_names = _response_names(final_url, disposition)
            content_type = headers.get("Content-Type", "")
            if response_names == {ALLOWLISTED_FILE}:
                copied = copy_bounded_stream(
                    response,
                    destination,
                    max_bytes=MAXIMUM_DOWNLOADED_BYTES,
                )
                transport = {"kind": "direct_csv"}
            elif response_names == {ALLOWLISTED_TRANSPORT_ZIP}:
                archive = copy_bounded_stream(
                    response,
                    archive_path,
                    max_bytes=MAXIMUM_DOWNLOADED_BYTES,
                )
                copied = _extract_single_member_zip(archive_path, destination)
                transport = {
                    "kind": "single_member_zip",
                    "archive_path": archive["path"],
                    "archive_bytes": archive["bytes"],
                    "archive_sha256": archive["sha256"],
                    "member_count": 1,
                }
            else:
                raise ValueError("BETH response does not identify the allowlisted file")
        validate_csv_payload_kind(destination)
    except BaseException:
        destination.unlink(missing_ok=True)
        destination.with_name(destination.name + ".part").unlink(missing_ok=True)
        archive_path.unlink(missing_ok=True)
        archive_path.with_name(archive_path.name + ".part").unlink(missing_ok=True)
        raise
    return {
        "dataset_ref": DATASET_REF,
        "dataset_version_number": DATASET_VERSION_NUMBER,
        "file_name": ALLOWLISTED_FILE,
        "requested_url": requested_url,
        "final_url": _redacted_response_url(final_url),
        "http_status": status,
        "response_content_type": content_type,
        "response_content_disposition": disposition,
        "maximum_downloaded_bytes": MAXIMUM_DOWNLOADED_BYTES,
        "transport": transport,
        **copied,
    }


def _retrieve_json(
    url: str,
    authorization: str,
    *,
    opener=urllib.request.urlopen,
    timeout: int = 90,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Project05-BETH-license-audit/0.1",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Authorization": authorization,
        },
    )
    with opener(request, timeout=timeout) as response:
        status = int(getattr(response, "status", 200))
        if status != 200:
            raise ValueError(f"BETH metadata retrieval returned HTTP {status}")
        body = response.read(MAXIMUM_METADATA_BYTES + 1)
    if len(body) > MAXIMUM_METADATA_BYTES:
        raise ValueError("BETH metadata response exceeds the byte cap")
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("BETH metadata response is not valid JSON") from error
    if not isinstance(value, dict):
        raise ValueError("BETH metadata response is not an object")
    return value


def retrieve_kaggle_metadata_bundle(
    contract: dict[str, Any],
    *,
    page_extract_path: Path = PAGE_EXTRACT_PATH,
    opener=urllib.request.urlopen,
    timeout: int = 90,
    authorization: str | None = None,
) -> dict[str, Any]:
    auth_header = authorization or load_kaggle_authorization()
    if not auth_header.startswith("Basic "):
        raise PermissionError("unsupported Kaggle authorization scheme")
    page_extract_path = Path(page_extract_path)
    page_hash = sha256_file(page_extract_path)
    expected_page_hash = contract["license_evidence"]["page_extract_sha256"]
    if page_hash != expected_page_hash:
        raise ValueError("tracked Kaggle page extract SHA-256 mismatch")
    bundle = {
        "dataset_view": _retrieve_json(
            METADATA_VIEW_URL,
            auth_header,
            opener=opener,
            timeout=timeout,
        ),
        "file_inventory": _retrieve_json(
            METADATA_FILES_URL,
            auth_header,
            opener=opener,
            timeout=timeout,
        ),
        "request": {
            "dataset_version_number": DATASET_VERSION_NUMBER,
            "dataset_view_url": METADATA_VIEW_URL,
            "dataset_files_url": METADATA_FILES_URL,
            "page_extract_sha256": page_hash,
        },
    }
    _validate_metadata_bundle(bundle, contract)
    return bundle


def retrieve_cc0_legalcode(
    destination: Path,
    *,
    opener=urllib.request.urlopen,
    timeout: int = 90,
    expected_sha256: str = CC0_LEGALCODE_SHA256,
) -> dict[str, Any]:
    request = urllib.request.Request(
        CC0_LEGALCODE_URL,
        headers={
            "User-Agent": "Project05-BETH-license-audit/0.1",
            "Accept": "text/plain",
            "Accept-Encoding": "identity",
        },
    )
    destination = Path(destination)
    try:
        with opener(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            if status != 200:
                raise ValueError(f"CC0 legalcode retrieval returned HTTP {status}")
            copied = copy_bounded_stream(
                response,
                destination,
                max_bytes=MAXIMUM_LEGALCODE_BYTES,
            )
        if copied["sha256"] != expected_sha256:
            raise ValueError("official CC0 legalcode SHA-256 mismatch")
    except BaseException:
        destination.unlink(missing_ok=True)
        destination.with_name(destination.name + ".part").unlink(missing_ok=True)
        raise
    return {
        "url": CC0_LEGALCODE_URL,
        "http_status": status,
        **copied,
    }


def validate_csv_payload_kind(path: Path) -> None:
    with Path(path).open("rb") as handle:
        prefix = handle.read(4096)
    stripped = prefix.lstrip()
    lowered = stripped[:64].lower()
    if prefix.startswith((b"PK\x03\x04", b"\x1f\x8b")):
        raise ValueError("BETH response is an archive rather than the allowlisted CSV")
    if lowered.startswith((b"<html", b"<!doctype html")):
        raise ValueError("BETH response is HTML rather than the allowlisted CSV")
    if lowered.startswith((b"{", b"[")):
        raise ValueError("BETH response is JSON rather than the allowlisted CSV")
    if b"," not in prefix or b"\n" not in prefix:
        raise ValueError("BETH response does not have a CSV header")


def _metadata_file_names(metadata: dict[str, Any]) -> set[str]:
    rows = metadata.get("datasetFiles")
    if not isinstance(rows, list):
        rows = metadata.get("files")
    if not isinstance(rows, list):
        return set()
    names: set[str] = set()
    for row in rows:
        if isinstance(row, dict):
            value = row.get("name") or row.get("ref") or row.get("fileName")
            if isinstance(value, str):
                names.add(Path(value).name)
    return names


def _metadata_components(
    metadata: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if "dataset_view" not in metadata and "file_inventory" not in metadata:
        return metadata, metadata, {}
    view = metadata.get("dataset_view")
    inventory = metadata.get("file_inventory")
    request = metadata.get("request")
    if not isinstance(view, dict) or not isinstance(inventory, dict):
        raise ValueError("Kaggle composite metadata is malformed")
    if not isinstance(request, dict):
        raise ValueError("Kaggle composite metadata request evidence is missing")
    return view, inventory, request


def _validate_metadata_bundle(
    metadata: dict[str, Any], contract: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    view, inventory, request = _metadata_components(metadata)
    expected = contract["dataset"]
    metadata_ref = view.get("ref") or view.get("datasetRef")
    metadata_version = view.get("versionNumber")
    if metadata_version is None:
        metadata_version = view.get("currentVersionNumber")
    if (
        metadata_ref != expected["dataset_ref"]
        or metadata_version != expected["dataset_version_number"]
    ):
        raise ValueError("Kaggle metadata does not bind dataset version 3")
    license_name = str(view.get("licenseName") or view.get("license") or "").strip()
    if normalized_text(license_name) not in {
        "cc0: public domain",
        "cc0-1.0",
        "cc0 1.0",
    }:
        raise ValueError("Kaggle version-3 metadata is not explicitly CC0")
    expected_inventory = set(
        contract.get("license_evidence", {}).get("expected_file_inventory", [])
    )
    observed_inventory = _metadata_file_names(inventory)
    if expected_inventory and observed_inventory != expected_inventory:
        raise ValueError("Kaggle file inventory does not match the frozen 15-file set")
    if expected["allowlisted_file"] not in observed_inventory:
        raise ValueError("Kaggle metadata does not list the allowlisted source file")
    if "license_evidence" in contract:
        expected_page_hash = contract["license_evidence"]["page_extract_sha256"]
        if request.get("dataset_version_number") != expected["dataset_version_number"]:
            raise ValueError("Kaggle metadata request did not pin dataset version 3")
        if request.get("page_extract_sha256") != expected_page_hash:
            raise ValueError("Kaggle page extract evidence SHA-256 mismatch")
    return view, inventory, request


def _frozen_source_identity_errors(
    source_path: Path,
    retrieval_manifest: dict[str, Any],
    expected: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected_bytes = expected.get("expected_csv_bytes")
    expected_sha256 = expected.get("expected_csv_sha256")
    if expected_bytes is not None and source_path.stat().st_size != expected_bytes:
        errors.append("frozen_csv_byte_count_mismatch")
    if expected_sha256 is not None and sha256_file(source_path) != expected_sha256:
        errors.append("frozen_csv_sha256_mismatch")
    expected_archive_bytes = expected.get("expected_transport_zip_bytes")
    expected_archive_sha256 = expected.get("expected_transport_zip_sha256")
    if expected_archive_bytes is not None or expected_archive_sha256 is not None:
        transport = retrieval_manifest.get("transport")
        if not isinstance(transport, dict) or transport.get("kind") != "single_member_zip":
            errors.append("frozen_transport_identity_missing")
        else:
            if transport.get("archive_bytes") != expected_archive_bytes:
                errors.append("frozen_transport_byte_count_mismatch")
            if transport.get("archive_sha256") != expected_archive_sha256:
                errors.append("frozen_transport_sha256_mismatch")
    return errors


def finalize_license_audit(
    source_path: Path,
    retrieval_manifest: dict[str, Any],
    kaggle_metadata: dict[str, Any],
    legalcode_bytes: bytes,
    contract: dict[str, Any],
    *,
    expected_legalcode_sha256: str = CC0_LEGALCODE_SHA256,
) -> dict[str, Any]:
    source_path = Path(source_path)
    expected = contract["dataset"]
    if (
        retrieval_manifest.get("dataset_ref") != expected["dataset_ref"]
        or retrieval_manifest.get("dataset_version_number")
        != expected["dataset_version_number"]
        or retrieval_manifest.get("file_name") != expected["allowlisted_file"]
        or retrieval_manifest.get("bytes") != source_path.stat().st_size
        or retrieval_manifest.get("sha256") != sha256_file(source_path)
    ):
        raise ValueError("retrieval manifest does not bind the authorized source bytes")
    frozen_errors = _frozen_source_identity_errors(
        source_path, retrieval_manifest, expected
    )
    if frozen_errors:
        raise ValueError("; ".join(frozen_errors))
    view, inventory, request_evidence = _validate_metadata_bundle(
        kaggle_metadata, contract
    )
    metadata_ref = view.get("ref") or view.get("datasetRef")
    metadata_version = view.get("versionNumber")
    if metadata_version is None:
        metadata_version = view.get("currentVersionNumber")
    license_name = str(view.get("licenseName") or view.get("license") or "").strip()
    legalcode_sha256 = sha256_bytes(legalcode_bytes)
    if legalcode_sha256 != expected_legalcode_sha256:
        raise ValueError("official CC0 legalcode SHA-256 mismatch")
    validate_csv_payload_kind(source_path)
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        first_row = next(csv.reader(handle), [])
    if first_row != list(contract["required_schema_fields"]):
        raise ValueError("single CSV has a preamble, notice, or unexpected first row")
    expected_header_hash = contract.get("required_schema_order_sha256")
    if expected_header_hash and sha256_bytes(canonical_bytes(first_row)) != expected_header_hash:
        raise ValueError("single CSV header order SHA-256 mismatch")
    finalized = dict(retrieval_manifest)
    finalized.update(
        {
            "license_status": "passed_cc0_v3_no_conflicting_notice",
            "nested_notice_conflicts": [],
            "license_evidence": {
                "metadata_ref": metadata_ref,
                "metadata_version_number": metadata_version,
                "metadata_license_name": license_name,
                "metadata_file_count": len(_metadata_file_names(inventory)),
                "dataset_view_canonical_sha256": sha256_bytes(canonical_bytes(view)),
                "file_inventory_canonical_sha256": sha256_bytes(
                    canonical_bytes(inventory)
                ),
                "page_extract_sha256": request_evidence.get(
                    "page_extract_sha256"
                ),
                "metadata_canonical_sha256": sha256_bytes(
                    canonical_bytes(kaggle_metadata)
                ),
                "legalcode_sha256": legalcode_sha256,
                "nested_notice_check": "single_csv_schema_header_is_first_row",
            },
        }
    )
    return finalized


def _validate_exclusion_lock(lock: dict[str, Any]) -> None:
    if lock.get("contains_raw_test_payload") is not False:
        raise ValueError("protected lock contains raw test payload")
    if lock.get("contains_raw_private_gold") is not False:
        raise ValueError("protected lock contains raw private gold")
    if lock.get("character_ngram_n") != 5:
        raise ValueError("protected lock n-gram size changed")
    if float(lock.get("near_duplicate_threshold", 0)) != 0.85:
        raise ValueError("protected lock threshold changed")


class ProtectedScanner:
    def __init__(self, lock: dict[str, Any]):
        _validate_exclusion_lock(lock)
        self.n = int(lock["character_ngram_n"])
        self.minimum_chars = int(lock["minimum_protected_text_chars"])
        self.threshold = float(lock["near_duplicate_threshold"])
        self.exact_hashes = set(lock.get("normalized_text_hashes", []))
        self.signatures: list[set[str]] = []
        self.signature_hashes: list[str] = []
        self.inverted: dict[str, list[int]] = defaultdict(list)
        for index, row in enumerate(lock.get("ngram_signatures", [])):
            grams = set(row.get("ngram_hashes", []))
            if not grams or len(grams) != row.get("ngram_count"):
                raise ValueError("protected n-gram signature is malformed")
            self.signatures.append(grams)
            self.signature_hashes.append(str(row.get("normalized_text_sha256")))
            for gram in grams:
                self.inverted[gram].append(index)
        self.exact_matches = 0
        self.near_matches = 0
        self.maximum_jaccard = 0.0
        self.matched_hashes: set[str] = set()

    def scan(self, value: Any) -> None:
        text = normalized_text(value)
        if len(text) < self.minimum_chars:
            return
        value_hash = sha256_bytes(text.encode("utf-8"))
        if value_hash in self.exact_hashes:
            self.exact_matches += 1
            self.matched_hashes.add(value_hash)
            return
        grams = hashed_character_ngrams(text, self.n)
        overlaps: Counter[int] = Counter()
        for gram in grams:
            for index in self.inverted.get(gram, ()):
                overlaps[index] += 1
        for index, intersection in overlaps.items():
            union = len(grams) + len(self.signatures[index]) - intersection
            score = intersection / union if union else 1.0
            self.maximum_jaccard = max(self.maximum_jaccard, score)
            if score >= self.threshold:
                self.near_matches += 1
                self.matched_hashes.add(self.signature_hashes[index])

    def report(self) -> dict[str, Any]:
        return {
            "status": (
                "passed_clean"
                if self.exact_matches == 0 and self.near_matches == 0
                else "failed_matches_present"
            ),
            "threshold": self.threshold,
            "exact_matches": self.exact_matches,
            "near_matches": self.near_matches,
            "maximum_jaccard": self.maximum_jaccard,
            "matched_normalized_hashes": sorted(self.matched_hashes),
            "raw_matches": [],
            "contains_raw_protected_payload": False,
        }


def _valid_uint(value: Any) -> str | None:
    text = str(value).strip()
    if not re.fullmatch(r"[0-9]+", text):
        return None
    return str(int(text))


def _valid_timestamp(value: Any) -> str | None:
    text = str(value).strip()
    try:
        number = float(text)
    except ValueError:
        return None
    return text if math.isfinite(number) and number >= 0 else None


def _candidate_basis(row: dict[str, str], row_number: int) -> dict[str, Any] | None:
    process_id = _valid_uint(row.get("processId"))
    parent_process_id = _valid_uint(row.get("parentProcessId"))
    timestamp = _valid_timestamp(row.get("timestamp"))
    process_name = str(row.get("processName") or "").strip()
    host_name = str(row.get("hostName") or "").strip()
    event_name = str(row.get("eventName") or "").strip()
    if not all(
        (process_id, parent_process_id, timestamp, process_name, host_name, event_name)
    ):
        return None
    return {
        "pointer": {"row_number": row_number},
        "subject_type": "process",
        "subject_value": f"pid={parent_process_id}@{host_name}",
        "predicate": "parent_of",
        "object_type": "process",
        "object_value": f"{process_name}#pid={process_id}@{host_name}",
        "event_time": timestamp,
        "bound_event_name": event_name,
    }


def _identity_errors(
    path: Path, contract: dict[str, Any], acquisition: dict[str, Any]
) -> list[str]:
    expected = contract["dataset"]
    errors: list[str] = []
    if (
        acquisition.get("dataset_ref") != expected["dataset_ref"]
        or acquisition.get("dataset_version_number")
        != expected["dataset_version_number"]
        or acquisition.get("file_name") != expected["allowlisted_file"]
    ):
        errors.append("acquisition_identity_mismatch")
    if path.stat().st_size != acquisition.get("bytes"):
        errors.append("acquisition_byte_count_mismatch")
    if sha256_file(path) != acquisition.get("sha256"):
        errors.append("acquisition_sha256_mismatch")
    if path.stat().st_size > expected["maximum_downloaded_bytes"]:
        errors.append("acquisition_exceeds_byte_cap")
    if acquisition.get("license_status") != "passed_cc0_v3_no_conflicting_notice":
        errors.append("license_not_passed")
    if acquisition.get("nested_notice_conflicts") != []:
        errors.append("nested_notice_conflict")
    errors.extend(_frozen_source_identity_errors(path, acquisition, expected))
    return errors


def audit_beth_csv(
    path: Path,
    contract: dict[str, Any],
    exclusion_lock: dict[str, Any],
    acquisition: dict[str, Any],
) -> dict[str, Any]:
    path = Path(path)
    errors = _identity_errors(path, contract, acquisition)
    try:
        validate_csv_payload_kind(path)
    except ValueError:
        errors.append("payload_not_allowlisted_csv")
    scanner = ProtectedScanner(exclusion_lock)
    required = list(contract["required_schema_fields"])
    candidate_digest = hashlib.sha256()
    record_count = 0
    eligible = 0
    abstained = 0
    schema_fields: list[str] = []
    if "payload_not_allowlisted_csv" not in errors:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            schema_fields = list(reader.fieldnames or [])
            if len(schema_fields) != len(set(schema_fields)) or schema_fields != required:
                errors.append("csv_schema_mismatch")
            elif (
                contract.get("required_schema_order_sha256")
                and sha256_bytes(canonical_bytes(schema_fields))
                != contract["required_schema_order_sha256"]
            ):
                errors.append("csv_schema_order_sha256_mismatch")
            else:
                for row_number, row in enumerate(reader, start=2):
                    record_count += 1
                    if None in row or any(value is None for value in row.values()):
                        errors.append("csv_row_width_mismatch")
                        continue
                    for value in row.values():
                        scanner.scan(value)
                    allowed = {
                        key: value
                        for key, value in row.items()
                        if key not in PROHIBITED_SUPERVISION_FIELDS
                    }
                    candidate = _candidate_basis(allowed, row_number)
                    if candidate is None:
                        abstained += 1
                        continue
                    candidate_digest.update(canonical_bytes(candidate))
                    candidate_digest.update(b"\n")
                    eligible += 1
    protected = scanner.report()
    if protected["exact_matches"]:
        errors.append("protected_exact_match")
    if protected["near_matches"]:
        errors.append("protected_near_match")
    minimum = int(contract["g0_audit"]["minimum_unique_pointer_bound_candidates"])
    if eligible < minimum:
        errors.append("g0_candidate_count_below_minimum")
    errors = sorted(set(errors))
    status = "passed_candidate_fourth_family_source_gate" if not errors else "failed_closed"
    return {
        "schema_version": "project05-beth-single-file-source-gate-audit-v0.1",
        "status": status,
        "errors": errors,
        "source_identity": {
            "dataset_ref": acquisition.get("dataset_ref"),
            "dataset_version_number": acquisition.get("dataset_version_number"),
            "file_name": acquisition.get("file_name"),
            "bytes": acquisition.get("bytes"),
            "sha256": acquisition.get("sha256"),
        },
        "license_audit": {
            "status": acquisition.get("license_status"),
            "nested_notice_conflicts": acquisition.get("nested_notice_conflicts"),
        },
        "schema_audit": {
            "observed_fields": schema_fields,
            "required_fields": required,
            "record_count": record_count,
        },
        "prohibited_supervision": {
            "fields_present_but_stripped": sorted(
                set(schema_fields) & PROHIBITED_SUPERVISION_FIELDS
            ),
            "fields_used": [],
            "label_invariant_by_construction": True,
        },
        "protected_scan": protected,
        "g0_audit": {
            "template_id": "beth_record_local_parent_process_v1",
            "eligible_candidates": eligible,
            "abstained_records": abstained,
            "minimum_required": minimum,
            "candidate_digest": candidate_digest.hexdigest().upper(),
            "candidate_records_emitted": False,
        },
        "family_gate": {
            "candidate_fourth_train_family": status.startswith("passed_"),
            "formal_data_gate_passed": False,
            "next_gate": "formal pair construction remains separately unauthorized",
        },
        "execution_claims": {
            "normalized_records_written": False,
            "candidate_records_written": False,
            "candidate_pairs_constructed": False,
            "tokenizer_used": False,
            "model_used": False,
            "training_run": False,
            "formal_inference_run": False,
            "m3_runtime_integrated": False,
        },
    }


def build_waiting_report() -> dict[str, Any]:
    return {
        "schema_version": "project05-beth-single-file-source-gate-status-v0.1",
        "created_date": "2026-07-18",
        "status": "awaiting_kaggle_authentication",
        "authority_id": "project05-llm-evidence-compiler-beth-source-gate-v0.7",
        "request": {
            "dataset_ref": DATASET_REF,
            "dataset_version_number": DATASET_VERSION_NUMBER,
            "file_name": ALLOWLISTED_FILE,
            "maximum_downloaded_bytes": MAXIMUM_DOWNLOADED_BYTES,
            "url": build_download_url(
                DATASET_REF,
                DATASET_VERSION_NUMBER,
                ALLOWLISTED_FILE,
                MAXIMUM_DOWNLOADED_BYTES,
            ),
            "network_endpoint_verified": False,
        },
        "observations": [
            {
                "method": "HEAD",
                "url_shape": "filename_as_path_segment",
                "http_status": 404,
                "corpus_bytes_retrieved": 0,
                "disposition": "rejected_endpoint_shape_not_reused",
            },
            {
                "method": "HEAD",
                "url_shape": "official_request_fields_as_query",
                "http_status": 404,
                "corpus_bytes_retrieved": 0,
                "disposition": "anonymous_single_file_request_unavailable",
            },
            {
                "source": "Kaggle/kaggle-api official client",
                "method": "dataset_download_file",
                "request_fields_verified": [
                    "owner_slug",
                    "dataset_slug",
                    "dataset_version_number",
                    "file_name",
                ],
            },
            {
                "source": "Kaggle public datasets/view API",
                "http_status": 200,
                "current_version_number": 3,
                "license_name": "CC0: Public Domain",
                "returned_file_count": 0,
                "corpus_bytes_retrieved": 0,
            },
            {
                "source": "local Kaggle credential check",
                "credential_file_present": False,
                "credential_content_read": False,
            },
        ],
        "blocking_condition": {
            "code": "kaggle_authentication_required_or_single_file_endpoint_not_public",
            "local_credentials_present": False,
            "scientific_gate_failure": False,
            "scope_expansion_allowed": False,
        },
        "execution_claims": {
            "corpus_downloaded": False,
            "corpus_bytes_retrieved": 0,
            "schema_audit_run_on_real_beth_file": False,
            "protected_scan_run_on_real_beth_file": False,
            "candidate_records_written": False,
            "candidate_pairs_constructed": False,
            "tokenizer_used": False,
            "model_used": False,
            "training_run": False,
            "formal_inference_run": False,
            "m3_runtime_integrated": False,
        },
        "next_action": "authenticate to Kaggle outside the repository, then run the frozen single-file retrieve command",
    }


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_no_overwrite(path: Path, value: Any) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite source-gate output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"source-gate temporary output exists: {temporary}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("request-url", help="print the frozen request URL")
    waiting = subparsers.add_parser(
        "waiting-report", help="write the fail-closed external-access status"
    )
    waiting.add_argument("--output", type=Path, required=True)
    retrieve = subparsers.add_parser(
        "retrieve", help="retrieve only the authorized BETH v3 source file"
    )
    retrieve.add_argument("--output", type=Path, required=True)
    retrieve.add_argument("--manifest", type=Path, required=True)
    metadata = subparsers.add_parser(
        "retrieve-metadata",
        help="retrieve bounded official Kaggle view and file-inventory metadata",
    )
    metadata.add_argument("--output", type=Path, required=True)
    metadata.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    metadata.add_argument("--page-extract", type=Path, default=PAGE_EXTRACT_PATH)
    legalcode = subparsers.add_parser(
        "retrieve-legalcode", help="retrieve and hash-lock official CC0 legalcode"
    )
    legalcode.add_argument("--output", type=Path, required=True)
    license_gate = subparsers.add_parser(
        "finalize-license",
        help="bind version-3 metadata and official CC0 legalcode to retrieved bytes",
    )
    license_gate.add_argument("--source", type=Path, required=True)
    license_gate.add_argument("--retrieval-manifest", type=Path, required=True)
    license_gate.add_argument("--kaggle-metadata", type=Path, required=True)
    license_gate.add_argument("--legalcode", type=Path, required=True)
    license_gate.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    license_gate.add_argument("--output", type=Path, required=True)
    audit = subparsers.add_parser(
        "audit", help="run the read-only schema, exclusion and G0 count audit"
    )
    audit.add_argument("--source", type=Path, required=True)
    audit.add_argument("--acquisition-manifest", type=Path, required=True)
    audit.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    audit.add_argument("--protected-lock", type=Path, default=PROTECTED_LOCK_PATH)
    audit.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "request-url":
        print(
            build_download_url(
                DATASET_REF,
                DATASET_VERSION_NUMBER,
                ALLOWLISTED_FILE,
                MAXIMUM_DOWNLOADED_BYTES,
            )
        )
        return 0
    if args.command == "waiting-report":
        write_json_no_overwrite(args.output, build_waiting_report())
        return 0
    if args.command == "retrieve":
        manifest = retrieve_single_file(args.output)
        manifest["license_status"] = "pending_post_acquisition_recheck"
        manifest["nested_notice_conflicts"] = None
        write_json_no_overwrite(args.manifest, manifest)
        return 0
    if args.command == "retrieve-metadata":
        bundle = retrieve_kaggle_metadata_bundle(
            load_json(args.contract),
            page_extract_path=args.page_extract,
        )
        write_json_no_overwrite(args.output, bundle)
        return 0
    if args.command == "retrieve-legalcode":
        retrieve_cc0_legalcode(args.output)
        return 0
    if args.command == "finalize-license":
        manifest = finalize_license_audit(
            args.source,
            load_json(args.retrieval_manifest),
            load_json(args.kaggle_metadata),
            args.legalcode.read_bytes(),
            load_json(args.contract),
        )
        write_json_no_overwrite(args.output, manifest)
        return 0
    if args.command == "audit":
        report = audit_beth_csv(
            args.source,
            load_json(args.contract),
            load_json(args.protected_lock),
            load_json(args.acquisition_manifest),
        )
        write_json_no_overwrite(args.output, report)
        return 0 if report["status"].startswith("passed_") else 1
    raise ValueError("unsupported command")


if __name__ == "__main__":
    raise SystemExit(main())
