"""Run the frozen AInception/Liwa bounded manifest and lineage audit.

The auditor never extracts archives and never persists raw member paths or
payload values.  It records only aggregate manifest hashes, bounded schema
categories, day-level timestamp summaries, irreversible identifiers, and
fail-closed decisions defined by the frozen contract.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


class AuditBlocked(RuntimeError):
    """Raised when a frozen fail-closed rule is triggered."""


def _digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def _stable_hash(*values: str) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()


def _normalized_member_path(value: str) -> str | None:
    raw = str(value).replace("\\", "/")
    while raw.startswith("./"):
        raw = raw[2:]
    if re.match(r"^[a-zA-Z]:/", raw):
        return None
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        return None
    return path.as_posix()


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", value.casefold())
        if token
    }


def _has_policy_token(value: str, policy_tokens: Iterable[str]) -> bool:
    folded = value.casefold()
    value_tokens = _tokens(folded)
    for policy in policy_tokens:
        policy_folded = str(policy).casefold()
        policy_parts = _tokens(policy_folded)
        if policy_parts and policy_parts.issubset(value_tokens):
            return True
        if policy_folded and policy_folded in folded:
            return True
    return False


def _parse_day(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        raw = float(value)
        if raw > 10_000_000_000:
            raw /= 1000.0
        try:
            return datetime.fromtimestamp(raw, tz=timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        match = re.match(r"^(\d{4}-\d{2}-\d{2})", text)
        return match.group(1) if match else None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).date().isoformat()


def _flatten_scalars(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(child, (dict, list)):
                rows.extend(_flatten_scalars(child, path))
            else:
                rows.append((path, child))
    elif isinstance(value, list):
        for child in value[:8]:
            rows.extend(_flatten_scalars(child, prefix))
    return rows


def _field_categories(field: str, categories: dict[str, list[str]]) -> set[str]:
    field_tokens = _tokens(field)
    matched: set[str] = set()
    for category, names in categories.items():
        for name in names:
            name_tokens = _tokens(str(name))
            if name_tokens and name_tokens.issubset(field_tokens):
                matched.add(category)
                break
    return matched


def _read_member_bytes(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    maximum_bytes: int,
) -> bytes:
    with archive.open(info, "r") as handle:
        return handle.read(maximum_bytes)


def _probe_text_member(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    *,
    family: str,
    path_hash: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    maximum_bytes = int(policy["maximum_bytes_read_per_text_member"])
    maximum_records = int(policy["maximum_records_read_per_text_member"])
    raw = _read_member_bytes(archive, info, maximum_bytes)
    bounded_hash = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig", errors="replace")
    suffix = PurePosixPath(info.filename).suffix.casefold()
    categories = policy["safe_field_categories"]
    category_counts: Counter[str] = Counter()
    days: set[str] = set()
    host_hashes: set[str] = set()
    record_id_nonempty_count = 0
    sampled_records = 0

    def consume(fields: Iterable[tuple[str, Any]]) -> None:
        nonlocal record_id_nonempty_count
        for field, value in fields:
            matched = _field_categories(field, categories)
            for category in matched:
                category_counts[category] += 1
            if "forbidden_supervision" in matched:
                continue
            if "timestamp" in matched:
                day = _parse_day(value)
                if day is not None:
                    days.add(day)
            if "host" in matched and value not in (None, ""):
                host_hashes.add(_stable_hash(family, "host", str(value)))
            if "record_id" in matched and value not in (None, ""):
                record_id_nonempty_count += 1

    if suffix == ".csv":
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        for row in reader:
            if sampled_records >= maximum_records:
                break
            sampled_records += 1
            consume((str(key), value) for key, value in row.items() if key is not None)
    elif suffix in {".json", ".jsonl", ".ndjson"}:
        for line in text.splitlines():
            if sampled_records >= maximum_records:
                break
            line = line.strip().lstrip("[").rstrip(",]")
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            sampled_records += 1
            consume(_flatten_scalars(value))
    else:
        for line in text.splitlines()[:maximum_records]:
            sampled_records += 1
            match = re.match(r"^(\d{4}-\d{2}-\d{2})", line.strip())
            if match:
                days.add(match.group(1))

    present = {key for key, count in category_counts.items() if count > 0}
    raw_event_schema = "timestamp" in present and bool(
        present
        & {"record_id", "host", "channel_or_provider", "raw_event_payload"}
    )
    pointer_capable_schema = "timestamp" in present and bool(
        present & {"record_id", "host", "channel_or_provider"}
    )
    detector_only_summary = (
        "detector_summary" in present and not raw_event_schema
    )
    return {
        "member_path_hash": path_hash,
        "suffix": suffix,
        "member_uncompressed_bytes": int(info.file_size),
        "bounded_bytes_read": len(raw),
        "bounded_probe_sha256": bounded_hash,
        "sampled_record_count": sampled_records,
        "field_category_counts": dict(sorted(category_counts.items())),
        "raw_event_schema": raw_event_schema,
        "pointer_capable_schema": pointer_capable_schema,
        "detector_only_summary": detector_only_summary,
        "forbidden_supervision_field_count": category_counts.get(
            "forbidden_supervision", 0
        ),
        "record_id_nonempty_count": record_id_nonempty_count,
        "hashed_host_cardinality": len(host_hashes),
        "timestamp_day_count": len(days),
        "first_day_utc": min(days) if days else None,
        "last_day_utc": max(days) if days else None,
        "raw_values_persisted": False,
    }


def _manifest(
    archive: zipfile.ZipFile,
    *,
    family: str,
    archive_key: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    forbidden_tokens = policy["forbidden_path_tokens"]
    binary_suffixes = {value.casefold() for value in policy["excluded_binary_suffixes"]}
    raw_suffixes = {value.casefold() for value in policy["raw_evidence_manifest_suffixes"]}
    notice_tokens = policy["notice_name_tokens"]
    normalized_rows: list[dict[str, Any]] = []
    raw_member_paths: list[str] = []
    text_member_paths: list[str] = []
    notice_member_paths: list[str] = []
    unsafe_path_count = 0
    duplicate_path_count = 0
    directory_count = 0
    names_seen: set[str] = set()
    suffix_counts: Counter[str] = Counter()
    excluded_counts: Counter[str] = Counter()
    total_compressed = 0
    total_uncompressed = 0

    for info in archive.infolist():
        total_compressed += int(info.compress_size)
        total_uncompressed += int(info.file_size)
        normalized = _normalized_member_path(info.filename)
        if normalized is None:
            unsafe_path_count += 1
            continue
        if normalized in names_seen:
            duplicate_path_count += 1
        names_seen.add(normalized)
        if info.is_dir():
            directory_count += 1
            continue
        suffix = PurePosixPath(normalized).suffix.casefold() or "<none>"
        suffix_counts[suffix] += 1
        path_hash = _stable_hash(family, archive_key, normalized)
        normalized_rows.append(
            {
                "normalized": normalized,
                "path_hash": path_hash,
                "suffix": suffix,
                "file_size": int(info.file_size),
                "compress_size": int(info.compress_size),
                "crc": int(info.CRC),
                "info": info,
            }
        )
        basename = PurePosixPath(normalized).name
        is_notice = _has_policy_token(basename, notice_tokens)
        if is_notice:
            notice_member_paths.append(normalized)
        forbidden = _has_policy_token(normalized, forbidden_tokens)
        if forbidden:
            excluded_counts["forbidden_path_token"] += 1
            continue
        if suffix in binary_suffixes:
            excluded_counts["excluded_binary_suffix"] += 1
            continue
        if suffix in raw_suffixes:
            raw_member_paths.append(normalized)
            if suffix in {
                value.casefold() for value in policy["text_probe_suffixes"]
            }:
                text_member_paths.append(normalized)
        else:
            excluded_counts["suffix_not_in_raw_allowlist"] += 1

    signature_rows = [
        f"{row['normalized']}|{row['file_size']}|{row['compress_size']}|{row['crc']:08x}"
        for row in sorted(normalized_rows, key=lambda item: item["normalized"])
    ]
    crc_rows = [
        f"{row['file_size']}|{row['crc']:08x}"
        for row in sorted(normalized_rows, key=lambda item: (item["file_size"], item["crc"]))
    ]
    path_hashes = sorted(row["path_hash"] for row in normalized_rows)
    return {
        "rows": normalized_rows,
        "row_by_path": {row["normalized"]: row for row in normalized_rows},
        "raw_member_paths": sorted(raw_member_paths),
        "text_member_paths": sorted(text_member_paths),
        "notice_member_paths": sorted(set(notice_member_paths)),
        "persisted": {
            "member_count": len(normalized_rows),
            "directory_count": directory_count,
            "compressed_bytes": total_compressed,
            "uncompressed_bytes": total_uncompressed,
            "unsafe_path_count": unsafe_path_count,
            "duplicate_member_path_count": duplicate_path_count,
            "suffix_counts": dict(sorted(suffix_counts.items())),
            "excluded_category_counts": dict(sorted(excluded_counts.items())),
            "notice_member_count": len(set(notice_member_paths)),
            "eligible_raw_member_count": len(raw_member_paths),
            "eligible_text_member_count": len(text_member_paths),
            "member_path_aggregate_hash": hashlib.sha256(
                "\n".join(signature_rows).encode("utf-8")
            ).hexdigest(),
            "crc32_aggregate_hash": hashlib.sha256(
                "\n".join(crc_rows).encode("utf-8")
            ).hexdigest(),
            "member_path_hashes": path_hashes[
                : int(policy["maximum_persisted_member_path_hashes_per_archive"])
            ],
            "raw_member_paths_persisted": False,
        },
        "identity_set": {
            _stable_hash(
                row["normalized"], str(row["file_size"]), f"{row['crc']:08x}"
            )
            for row in normalized_rows
        },
    }


def _scan_notices(
    archive: zipfile.ZipFile,
    manifest: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    paths = manifest["notice_member_paths"]
    maximum_members = int(policy["maximum_notice_members_read_per_archive"])
    if len(paths) > maximum_members:
        raise AuditBlocked("notice member count exceeds frozen cap")
    maximum_bytes = int(policy["maximum_notice_bytes_read_per_member"])
    conflicts: Counter[str] = Counter()
    scanned_hashes: list[str] = []
    for path in paths:
        row = manifest["row_by_path"][path]
        raw = _read_member_bytes(archive, row["info"], maximum_bytes)
        scanned_hashes.append(hashlib.sha256(raw).hexdigest())
        text = raw.decode("utf-8", errors="ignore").casefold()
        for token in policy["conflicting_notice_tokens"]:
            if str(token).casefold() in text:
                conflicts[str(token)] += 1
    return {
        "notice_member_count": len(paths),
        "notice_members_scanned": len(paths),
        "notice_content_hash_aggregate": hashlib.sha256(
            "\n".join(sorted(scanned_hashes)).encode("utf-8")
        ).hexdigest(),
        "conflicting_notice_token_counts": dict(sorted(conflicts.items())),
        "nested_notice_conflict_detected": bool(conflicts),
        "notice_text_persisted": False,
    }


def _select_ainception_members(paths: list[str], maximum: int) -> list[str]:
    by_suffix: dict[str, list[str]] = defaultdict(list)
    for path in sorted(paths):
        by_suffix[PurePosixPath(path).suffix.casefold()].append(path)
    selected: list[str] = []
    for suffix in sorted(by_suffix):
        rows = by_suffix[suffix]
        selected.append(rows[0])
        if rows[-1] != rows[0]:
            selected.append(rows[-1])
    for path in sorted(paths):
        if path not in selected:
            selected.append(path)
    return selected[:maximum]


def _archive_identity(path: Path, row: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise AuditBlocked("authorized archive is missing")
    actual_bytes = path.stat().st_size
    if actual_bytes != int(row["expected_bytes"]):
        raise AuditBlocked(
            f"archive byte drift: expected {row['expected_bytes']} got {actual_bytes}"
        )
    actual_md5 = _digest_file(path, "md5")
    if actual_md5 != str(row["expected_md5"]).casefold():
        raise AuditBlocked("archive MD5 drift")
    return {
        "archive_bytes": actual_bytes,
        "archive_md5": actual_md5,
        "archive_sha256": _digest_file(path, "sha256"),
    }


def _audit_ainception_archive(
    path: Path,
    row: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    identity = _archive_identity(path, row)
    manifest_policy = contract["global_manifest_policy"]
    probe_policy = contract["bounded_probe_policy"]
    with zipfile.ZipFile(path) as archive:
        manifest = _manifest(
            archive,
            family=row["source_family_id"],
            archive_key=row["source_key"],
            policy=manifest_policy,
        )
        notices = _scan_notices(archive, manifest, manifest_policy)
        selected = _select_ainception_members(
            manifest["text_member_paths"],
            int(probe_policy["maximum_text_members_read_per_ainception_archive"]),
        )
        probes: list[dict[str, Any]] = []
        total_probe_bytes = 0
        for member in selected:
            info_row = manifest["row_by_path"][member]
            probe = _probe_text_member(
                archive,
                info_row["info"],
                family=row["source_family_id"],
                path_hash=info_row["path_hash"],
                policy=probe_policy,
            )
            total_probe_bytes += int(probe["bounded_bytes_read"])
            if total_probe_bytes > int(
                probe_policy["maximum_total_text_probe_bytes_per_ainception_archive"]
            ):
                raise AuditBlocked("AInception text probe byte cap exceeded")
            probes.append(probe)
    structural_pass = (
        manifest["persisted"]["unsafe_path_count"] == 0
        and manifest["persisted"]["duplicate_member_path_count"] == 0
        and manifest["persisted"]["eligible_raw_member_count"] > 0
        and not notices["nested_notice_conflict_detected"]
    )
    return {
        "source_family_id": row["source_family_id"],
        "source_key": row["source_key"],
        "selection_stratum": row["selection_stratum"],
        "status": "completed" if structural_pass else "completed_gate_failed",
        **identity,
        "manifest": manifest["persisted"],
        "notice_audit": notices,
        "bounded_probe": {
            "selected_member_count": len(probes),
            "bounded_bytes_read": total_probe_bytes,
            "members": probes,
            "raw_values_persisted": False,
        },
        "structural_gate_passed": structural_pass,
        "source_native_lineage_candidate": structural_pass,
        "statistical_independence_verified": False,
        "_identity_set": manifest["identity_set"],
    }


def _derive_liwa_run_token(path: str, view_tokens: Iterable[str]) -> str | None:
    parts = re.findall(r"[a-z0-9]+", PurePosixPath(path).stem.casefold())
    view = {token.casefold() for token in view_tokens}
    kept = [token for token in parts if token not in view]
    if not kept or not any(any(char.isdigit() for char in token) for token in kept):
        return None
    return "|".join(kept)


def _audit_liwa_archive(
    path: Path,
    row: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    identity = _archive_identity(path, row)
    manifest_policy = contract["global_manifest_policy"]
    probe_policy = contract["bounded_probe_policy"]
    lineage_policy = contract["lineage_policy"]["liwa"]
    with zipfile.ZipFile(path) as archive:
        manifest = _manifest(
            archive,
            family=row["source_family_id"],
            archive_key=row["source_key"],
            policy=manifest_policy,
        )
        notices = _scan_notices(archive, manifest, manifest_policy)
        csv_paths = [
            value
            for value in manifest["text_member_paths"]
            if PurePosixPath(value).suffix.casefold() == ".csv"
        ]
        maximum_members = int(probe_policy["maximum_text_members_read_liwa"])
        if len(csv_paths) > maximum_members:
            raise AuditBlocked("Liwa eligible CSV count exceeds frozen cap")
        probes: list[dict[str, Any]] = []
        total_probe_bytes = 0
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        unstable_member_count = 0
        for member in sorted(csv_paths):
            info_row = manifest["row_by_path"][member]
            probe = _probe_text_member(
                archive,
                info_row["info"],
                family=row["source_family_id"],
                path_hash=info_row["path_hash"],
                policy=probe_policy,
            )
            total_probe_bytes += int(probe["bounded_bytes_read"])
            if total_probe_bytes > int(probe_policy["maximum_total_text_probe_bytes_liwa"]):
                raise AuditBlocked("Liwa text probe byte cap exceeded")
            token = _derive_liwa_run_token(
                member,
                lineage_policy["logging_view_tokens_removed_before_grouping"],
            )
            if token is None:
                unstable_member_count += 1
                run_hash = None
            else:
                run_hash = _stable_hash(row["source_family_id"], "run", token)
                groups[run_hash].append(probe)
            probe["run_group_hash"] = run_hash
            probes.append(probe)

    content_to_groups: dict[str, set[str]] = defaultdict(set)
    for group_hash, group_probes in groups.items():
        for probe in group_probes:
            content_to_groups[probe["bounded_probe_sha256"]].add(group_hash)
    duplicated_groups = {
        group_hash
        for group_hashes in content_to_groups.values()
        if len(group_hashes) > 1
        for group_hash in group_hashes
    }
    group_results: list[dict[str, Any]] = []
    passed_groups = 0
    for group_hash in sorted(groups):
        group_probes = groups[group_hash]
        raw_schema_count = sum(bool(probe["raw_event_schema"]) for probe in group_probes)
        detector_only_count = sum(
            bool(probe["detector_only_summary"]) for probe in group_probes
        )
        duplicate = group_hash in duplicated_groups
        passed = raw_schema_count > 0 and not duplicate
        passed_groups += int(passed)
        group_results.append(
            {
                "run_group_hash": group_hash,
                "member_view_count": len(group_probes),
                "raw_event_schema_member_count": raw_schema_count,
                "detector_only_member_count": detector_only_count,
                "duplicate_bounded_content_across_groups": duplicate,
                "bounded_source_native_group_passed": passed,
                "statistical_independence_verified": False,
            }
        )
    required_groups = int(
        lineage_policy["minimum_source_native_lineage_candidates_for_future_role_review"]
    )
    structural_pass = (
        manifest["persisted"]["unsafe_path_count"] == 0
        and manifest["persisted"]["duplicate_member_path_count"] == 0
        and len(csv_paths) > 0
        and not notices["nested_notice_conflict_detected"]
    )
    lineage_pass = structural_pass and passed_groups >= required_groups
    return {
        "source_family_id": row["source_family_id"],
        "source_key": row["source_key"],
        "selection_stratum": row["selection_stratum"],
        "status": "completed" if structural_pass else "completed_gate_failed",
        **identity,
        "manifest": manifest["persisted"],
        "notice_audit": notices,
        "bounded_probe": {
            "selected_csv_member_count": len(probes),
            "bounded_bytes_read": total_probe_bytes,
            "members": probes,
            "raw_values_persisted": False,
        },
        "grouping": {
            "stable_run_group_count": len(groups),
            "unstable_run_member_count": unstable_member_count,
            "bounded_source_native_group_passed_count": passed_groups,
            "minimum_required_for_future_role_review": required_groups,
            "groups": group_results,
            "lineage_gate_passed": lineage_pass,
            "statistical_independence_verified": False,
            "null_or_benign_lineage_verified": False,
        },
        "structural_gate_passed": structural_pass,
        "lineage_gate_passed": lineage_pass,
    }


def _pairwise_jaccard(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    for index, left in enumerate(rows):
        for right in rows[index + 1 :]:
            union = left["_identity_set"] | right["_identity_set"]
            intersection = left["_identity_set"] & right["_identity_set"]
            comparisons.append(
                {
                    "left_archive_sha256": left["archive_sha256"],
                    "right_archive_sha256": right["archive_sha256"],
                    "manifest_identity_jaccard": (
                        len(intersection) / len(union) if union else 1.0
                    ),
                    "identical_manifest_signature": (
                        left["manifest"]["member_path_aggregate_hash"]
                        == right["manifest"]["member_path_aggregate_hash"]
                    ),
                }
            )
    return comparisons


def _validate_contract(contract: dict[str, Any], cwd: Path) -> Path:
    if contract.get("status") != "frozen_before_payload_acquisition":
        raise AuditBlocked("contract is not frozen before acquisition")
    scope = contract.get("scope", {})
    required_false = [
        "label_value_read_authorized",
        "ground_truth_read_authorized",
        "supervision_generation_authorized",
        "normalization_generation_authorized",
        "family_role_change_authorized",
        "quota_status_change_authorized",
        "train_admission_authorized",
        "baseline_authorized",
        "fine_tuning_authorized",
        "l2_gate_passed",
        "git_push_authorized",
    ]
    if any(scope.get(key) is not False for key in required_false):
        raise AuditBlocked("one or more authority prohibitions are not frozen")
    files = contract.get("acquisition", {}).get("files", [])
    if len(files) != 5:
        raise AuditBlocked("contract must authorize exactly five archives")
    families = Counter(row.get("source_family_id") for row in files)
    if families != Counter(
        {"ainception_zenodo_2025": 4, "liwa_ad_endpoint_telemetry_30run_2026": 1}
    ):
        raise AuditBlocked("contract family or archive count drift")
    local_paths = [str(row.get("local_relative_path", "")) for row in files]
    if len(set(local_paths)) != len(local_paths):
        raise AuditBlocked("duplicate local archive path")
    if any(
        Path(value).is_absolute() or ".." in PurePosixPath(value.replace("\\", "/")).parts
        for value in local_paths
    ):
        raise AuditBlocked("unsafe local archive path")
    if any(
        not str(row.get("download_url", "")).startswith("https://zenodo.org/api/records/")
        for row in files
    ):
        raise AuditBlocked("download URL is outside frozen Zenodo scope")
    expected_total = sum(int(row["expected_bytes"]) for row in files)
    if expected_total != int(contract["acquisition"]["maximum_total_download_bytes"]):
        raise AuditBlocked("download byte total drift")
    local_root = (cwd / contract["acquisition"]["local_root"]).resolve()
    if cwd.resolve() not in local_root.parents:
        raise AuditBlocked("local acquisition root escapes worktree")
    return local_root


def run_audit(contract_path: Path, output_path: Path) -> dict[str, Any]:
    contract_bytes = contract_path.read_bytes()
    contract = json.loads(contract_bytes)
    cwd = Path.cwd().resolve()
    local_root = _validate_contract(contract, cwd)
    expected_output = contract["output_contract"]["machine_report_path"].replace(
        "\\", "/"
    )
    if not output_path.resolve().as_posix().endswith(expected_output):
        raise AuditBlocked("output path does not match frozen contract")

    results: list[dict[str, Any]] = []
    for row in contract["acquisition"]["files"]:
        archive_path = local_root / row["local_relative_path"]
        try:
            if row["source_family_id"] == "ainception_zenodo_2025":
                result = _audit_ainception_archive(archive_path, row, contract)
            else:
                result = _audit_liwa_archive(archive_path, row, contract)
            results.append(result)
        except (
            AuditBlocked,
            OSError,
            ValueError,
            csv.Error,
            json.JSONDecodeError,
            zipfile.BadZipFile,
        ) as error:
            results.append(
                {
                    "source_family_id": row["source_family_id"],
                    "source_key": row["source_key"],
                    "status": "blocked",
                    "error": f"{type(error).__name__}: {error}",
                }
            )

    ainception = [
        row for row in results if row["source_family_id"] == "ainception_zenodo_2025"
    ]
    liwa_rows = [
        row
        for row in results
        if row["source_family_id"] == "liwa_ad_endpoint_telemetry_30run_2026"
    ]
    comparisons = (
        _pairwise_jaccard([row for row in ainception if row["status"] != "blocked"])
        if ainception
        else []
    )
    duplicate_manifest = any(row["identical_manifest_signature"] for row in comparisons)
    ainception_lineage_count = sum(
        row.get("source_native_lineage_candidate") is True for row in ainception
    )
    ainception_gate = (
        len(ainception) == 4
        and ainception_lineage_count == 4
        and not duplicate_manifest
        and all(row.get("status") != "blocked" for row in ainception)
    )
    liwa_gate = bool(liwa_rows) and liwa_rows[0].get("lineage_gate_passed") is True
    technical_block = any(row.get("status") == "blocked" for row in results)

    for row in ainception:
        row.pop("_identity_set", None)
    report = {
        "schema_version": "project05-llm-editor-l2-ainception-liwa-bounded-manifest-lineage-audit-result-v0.1",
        "audit_date": "2026-07-22",
        "contract_sha256": hashlib.sha256(contract_bytes).hexdigest().upper(),
        "contract_authority_base_commit": contract["authority_base_commit"],
        "contract_status": contract["status"],
        "status": (
            "blocked_no_authority_transition"
            if technical_block
            else "completed_no_authority_transition"
        ),
        "scope": {
            "exact_archive_acquisition_performed": True,
            "manifest_and_bounded_lineage_probe_performed": True,
            "label_or_ground_truth_values_used": False,
            "raw_member_paths_persisted": False,
            "raw_payload_values_persisted": False,
            "supervision_generated": False,
            "normalization_generated": False,
            "family_roles_changed": False,
            "quota_status_changed": False,
            "train_admission_applied": False,
            "baseline_run": False,
            "fine_tuning_run": False,
            "cert_or_iot23_downloaded": False,
            "protected_family_payload_read": False,
            "kernel_or_m3_work_performed": False,
            "l2_gate_passed": False,
            "git_push_performed": False,
        },
        "archives": results,
        "ainception_pairwise_manifest_comparisons": comparisons,
        "family_assessment": {
            "ainception": {
                "selected_archive_count": len(ainception),
                "bounded_source_native_lineage_candidate_count": ainception_lineage_count,
                "identical_manifest_pair_detected": duplicate_manifest,
                "future_role_review_evidence_gate_passed": ainception_gate,
                "statistical_independence_verified": False,
                "counts_toward_train_or_lineage_quota": False,
            },
            "liwa": {
                "archive_count": len(liwa_rows),
                "bounded_source_native_lineage_candidate_count": (
                    liwa_rows[0]
                    .get("grouping", {})
                    .get("bounded_source_native_group_passed_count", 0)
                    if liwa_rows
                    else 0
                ),
                "future_role_review_evidence_gate_passed": liwa_gate,
                "statistical_independence_verified": False,
                "null_or_benign_lineage_verified": False,
                "counts_toward_train_or_lineage_quota": False,
            },
        },
        "gate": {
            "technical_audit_completed": not technical_block,
            "ainception_future_role_review_evidence_gate_passed": ainception_gate,
            "liwa_future_role_review_evidence_gate_passed": liwa_gate,
            "train_source_approved": False,
            "family_role_change_applied": False,
            "train_or_lineage_quota_credit_awarded": False,
            "baseline_authorized": False,
            "fine_tuning_authorized": False,
            "l2_gate_passed": False,
            "git_push_authorized": False,
            "next_action_requires_separate_user_authorization": True,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if args.validate_only:
        local_root = _validate_contract(contract, Path.cwd().resolve())
        print(
            json.dumps(
                {
                    "status": "contract_valid",
                    "archive_count": len(contract["acquisition"]["files"]),
                    "maximum_total_download_bytes": contract["acquisition"][
                        "maximum_total_download_bytes"
                    ],
                    "local_root": local_root.as_posix(),
                },
                sort_keys=True,
            )
        )
        return 0
    if args.output is None:
        raise SystemExit("--output is required unless --validate-only is used")
    report = run_audit(args.contract, args.output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "technical_audit_completed": report["gate"][
                    "technical_audit_completed"
                ],
                "ainception_gate": report["gate"][
                    "ainception_future_role_review_evidence_gate_passed"
                ],
                "liwa_gate": report["gate"][
                    "liwa_future_role_review_evidence_gate_passed"
                ],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "completed_no_authority_transition" else 2


if __name__ == "__main__":
    raise SystemExit(main())
