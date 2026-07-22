"""Run the frozen CAM-LDS/SOCBED lineage-only audit.

The auditor deliberately exposes no semantic event payload.  It retains only
hashed grouping identifiers, counts, date-level timestamp summaries, structural
checks, and frozen-gate decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO


class AuditBlocked(RuntimeError):
    """Raised when a frozen fail-closed rule is triggered."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _stable_id(family: str, kind: str, value: str) -> str:
    digest = hashlib.sha256(f"{family}|{kind}|{value}".encode("utf-8")).hexdigest()
    return f"{kind.upper()}-{digest[:20]}"


def _normalized_member_path(value: str) -> str | None:
    raw = str(value).replace("\\", "/").lstrip("./")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        return None
    return path.as_posix()


def _path_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", value.casefold())
        if token
    }


def _has_forbidden_path_token(path: str, forbidden: list[str]) -> bool:
    tokens = _path_tokens(path)
    for value in forbidden:
        folded = value.casefold()
        value_tokens = _path_tokens(folded)
        if len(value_tokens) == 1 and next(iter(value_tokens)) in tokens:
            return True
        if folded in path.casefold():
            return True
    return False


def _lookup(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        raw = float(value)
        if raw > 10_000_000_000:
            raw /= 1000.0
        try:
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        match = re.match(
            r"^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:[.,](\d+))?",
            text,
        )
        if not match:
            return None
        try:
            parsed = datetime.fromisoformat(f"{match.group(1)}T{match.group(2)}")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _extract_allowed_scalars(
    line: bytes,
    *,
    allowed_fields: list[str],
    forbidden_fields: list[str],
    family: str,
) -> tuple[list[datetime], set[str]]:
    try:
        text = line.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        return [], set()
    if not text:
        return [], set()

    timestamps: list[datetime] = []
    hosts: set[str] = set()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = None

    if isinstance(value, dict):
        forbidden = {token.casefold() for token in forbidden_fields}
        present_tokens: set[str] = set()
        stack: list[Any] = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, child in current.items():
                    present_tokens.update(_path_tokens(str(key)))
                    if isinstance(child, (dict, list)):
                        stack.append(child)
            elif isinstance(current, list):
                stack.extend(child for child in current if isinstance(child, (dict, list)))
        forbidden_present = present_tokens & forbidden

        if forbidden_present:
            return [], set()

        for field in allowed_fields:
            # A forbidden token anywhere in the exact field name wins.
            if _path_tokens(field) & forbidden:
                continue
            scalar = _lookup(value, field)
            if field in {"@timestamp", "timestamp", "ts"}:
                parsed = _parse_timestamp(scalar)
                if parsed is not None:
                    timestamps.append(parsed)
            elif scalar is not None and not isinstance(scalar, (dict, list, bool)):
                host = str(scalar).strip()
                if host:
                    hosts.add(_stable_id(family, "host", host))
        return timestamps, hosts

    # Plain-text fallback only consumes an ISO timestamp prefix and the next token.
    prefix = re.match(
        r"^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+(\S+)",
        text,
    )
    if prefix:
        parsed = _parse_timestamp(prefix.group(1))
        if parsed is not None:
            timestamps.append(parsed)
        hosts.add(_stable_id(family, "host", prefix.group(2)))
    return timestamps, hosts


def _read_sample(
    handle: BinaryIO,
    *,
    max_lines: int,
    max_bytes: int,
    allowed_fields: list[str],
    forbidden_fields: list[str],
    family: str,
    hash_full_member: bool,
) -> dict[str, Any]:
    timestamps: list[datetime] = []
    hosts: set[str] = set()
    digest = hashlib.sha256()
    bytes_read = 0
    lines_read = 0
    line_index = 0
    while True:
        remaining = max_bytes - bytes_read
        if remaining <= 0:
            raise AuditBlocked("frozen payload byte cap exceeded")
        line = handle.readline(min(1024 * 1024, remaining + 1))
        if not line:
            break
        bytes_read += len(line)
        if bytes_read > max_bytes:
            raise AuditBlocked("frozen payload byte cap exceeded")
        if hash_full_member:
            digest.update(line)
        if line_index < max_lines:
            parsed_times, parsed_hosts = _extract_allowed_scalars(
                line,
                allowed_fields=allowed_fields,
                forbidden_fields=forbidden_fields,
                family=family,
            )
            timestamps.extend(parsed_times)
            hosts.update(parsed_hosts)
            lines_read += 1
        line_index += 1
        if not hash_full_member and line_index >= max_lines:
            break
    return {
        "bytes_read": bytes_read,
        "sampled_lines": lines_read,
        "total_lines_streamed": line_index,
        "timestamps": timestamps,
        "hosts": hosts,
        "member_sha256": digest.hexdigest().upper() if hash_full_member else None,
    }


def _archive_identity(path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise AuditBlocked("authorized archive is missing")
    actual_bytes = path.stat().st_size
    if actual_bytes > int(policy["maximum_archive_bytes"]):
        raise AuditBlocked("archive exceeds frozen byte cap")
    suffix = str(policy["path_suffix"]).replace("\\", "/")
    if not path.resolve().as_posix().endswith(suffix):
        raise AuditBlocked("archive path does not match frozen suffix")
    actual_sha256 = _sha256_file(path)
    if actual_sha256 != str(policy["sha256"]).upper():
        raise AuditBlocked("archive SHA-256 drift")
    return {"archive_bytes": actual_bytes, "archive_sha256": actual_sha256}


def _date_summary(timestamps: list[datetime]) -> dict[str, Any]:
    if not timestamps:
        return {
            "timestamp_count": 0,
            "first_day_utc": None,
            "last_day_utc": None,
            "distinct_day_count": 0,
        }
    days = sorted({value.date().isoformat() for value in timestamps})
    return {
        "timestamp_count": len(timestamps),
        "first_day_utc": days[0],
        "last_day_utc": days[-1],
        "distinct_day_count": len(days),
    }


def _cam_member_details(path: str, policy: dict[str, Any], global_policy: dict[str, Any]) -> dict[str, str] | None:
    normalized = _normalized_member_path(path)
    if normalized is None or _has_forbidden_path_token(
        normalized, global_policy["forbidden_path_tokens"]
    ):
        return None
    parts = list(PurePosixPath(normalized).parts)
    folded = [part.casefold() for part in parts]
    required = [value.casefold() for value in policy["member_allowlist"]["required_path_markers"]]
    if any(value not in folded for value in required):
        return None
    if PurePosixPath(normalized).suffix.casefold() not in {
        value.casefold() for value in policy["member_allowlist"]["allowed_suffixes"]
    }:
        return None
    padded = f"/{normalized.casefold()}/"
    for marker in policy["member_allowlist"]["forbidden_path_markers"]:
        folded_marker = str(marker).casefold()
        if folded_marker.endswith(".json"):
            if normalized.casefold().endswith(f"/{folded_marker}"):
                return None
        elif f"/{folded_marker}/" in padded:
            return None
    steps_index = folded.index("steps")
    logs_index = folded.index("logs", steps_index + 1)
    if steps_index == 0 or logs_index <= steps_index + 1:
        return None
    collection_anchor = "/".join(parts[:steps_index])
    step_anchor = "/".join(parts[:logs_index])
    host_scope = parts[logs_index + 1] if logs_index + 2 < len(parts) else "missing"
    return {
        "normalized": normalized,
        "collection_anchor": collection_anchor,
        "step_anchor": step_anchor,
        "host_scope": host_scope,
    }


def _audit_cam(
    archive_path: Path,
    policy: dict[str, Any],
    global_policy: dict[str, Any],
) -> dict[str, Any]:
    identity = _archive_identity(archive_path, policy["archive"])
    eligible: dict[str, dict[str, Any]] = {}
    step_members: dict[str, list[str]] = defaultdict(list)
    collection_steps: dict[str, set[str]] = defaultdict(set)
    collection_hosts: dict[str, set[str]] = defaultdict(set)
    central_member_count = 0
    central_uncompressed_bytes = 0

    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            central_member_count += 1
            central_uncompressed_bytes += int(info.file_size)
            if info.is_dir():
                continue
            details = _cam_member_details(info.filename, policy, global_policy)
            if details is None:
                continue
            if info.file_size > int(policy["archive"]["maximum_member_uncompressed_bytes"]):
                raise AuditBlocked("CAM-LDS eligible member exceeds frozen member byte cap")
            normalized = details["normalized"]
            eligible[normalized] = {"info": info, **details}
            step_members[details["step_anchor"]].append(normalized)
            collection_steps[details["collection_anchor"]].add(details["step_anchor"])
            collection_hosts[details["collection_anchor"]].add(details["host_scope"])

        selected: list[str] = []
        for step_anchor in sorted(step_members):
            names = sorted(step_members[step_anchor])
            selected.append(names[0])
            if names[-1] != names[0]:
                selected.append(names[-1])
        if len(selected) > int(policy["archive"]["maximum_payload_members_read"]):
            raise AuditBlocked("CAM-LDS selected members exceed frozen member cap")

        total_payload_bytes = 0
        total_sampled_lines = 0
        total_timestamps = 0
        group_times: dict[str, list[datetime]] = defaultdict(list)
        group_hosts: dict[str, set[str]] = defaultdict(set)
        for name in selected:
            details = eligible[name]
            remaining = int(policy["archive"]["maximum_payload_bytes_read"]) - total_payload_bytes
            if remaining <= 0:
                raise AuditBlocked("CAM-LDS frozen payload byte cap exceeded")
            with archive.open(details["info"], "r") as handle:
                sample = _read_sample(
                    handle,
                    max_lines=int(policy["deterministic_sampling"]["maximum_lines_per_member"]),
                    max_bytes=min(
                        remaining,
                        int(policy["archive"]["maximum_member_uncompressed_bytes"]),
                    ),
                    allowed_fields=global_policy["payload_scalar_fields_allowed"],
                    forbidden_fields=global_policy["forbidden_field_tokens"],
                    family=policy["source_family_id"],
                    hash_full_member=False,
                )
            total_payload_bytes += int(sample["bytes_read"])
            total_sampled_lines += int(sample["sampled_lines"])
            total_timestamps += len(sample["timestamps"])
            group_times[details["collection_anchor"]].extend(sample["timestamps"])
            group_hosts[details["collection_anchor"]].update(sample["hosts"])

    collections = []
    for anchor in sorted(collection_steps):
        timestamps = group_times.get(anchor, [])
        collections.append(
            {
                "collection_id": _stable_id(policy["source_family_id"], "collection", anchor),
                "step_group_count": len(collection_steps[anchor]),
                "path_host_scope_count": len(collection_hosts[anchor]),
                "payload_host_scope_count": len(group_hosts.get(anchor, set())),
                **_date_summary(timestamps),
                "independent_run_verified": False,
            }
        )

    return {
        "source_family_id": policy["source_family_id"],
        "status": "completed_with_independence_unproven",
        **identity,
        "central_directory": {
            "member_count": central_member_count,
            "uncompressed_bytes": central_uncompressed_bytes,
            "eligible_member_count": len(eligible),
        },
        "bounded_payload_read": {
            "selected_member_count": len(selected),
            "bytes_read": total_payload_bytes,
            "sampled_line_count": total_sampled_lines,
            "timestamp_parse_count": total_timestamps,
            "raw_values_persisted": False,
        },
        "grouping": {
            "collection_candidate_count": len(collections),
            "step_group_count": len(step_members),
            "collections": collections,
            "verified_independent_lineage_count": None,
            "independence_demonstrated": False,
            "counts_toward_independent_lineage_quota": False,
            "verdict": "source_native_collection_grouping_supported_independence_unproven",
        },
    }


def _audit_socbed(
    archive_path: Path,
    policy: dict[str, Any],
    global_policy: dict[str, Any],
) -> dict[str, Any]:
    identity = _archive_identity(archive_path, policy["archive"])
    pattern = re.compile(policy["member_allowlist"]["path_regex"])
    eligible: list[dict[str, Any]] = []
    central_member_count = 0
    central_uncompressed_bytes = 0

    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            central_member_count += 1
            central_uncompressed_bytes += int(info.file_size)
            if info.is_dir():
                continue
            normalized = _normalized_member_path(info.filename)
            if normalized is None or _has_forbidden_path_token(
                normalized, global_policy["forbidden_path_tokens"]
            ):
                continue
            match = pattern.search(normalized)
            if not match:
                continue
            if info.file_size > int(policy["archive"]["maximum_member_uncompressed_bytes"]):
                raise AuditBlocked("SOCBED eligible member exceeds frozen member byte cap")
            eligible.append(
                {
                    "info": info,
                    "normalized": normalized,
                    "run_key": match.group(1),
                    "view_key": PurePosixPath(normalized).parent.as_posix(),
                }
            )
        if len(eligible) > int(policy["archive"]["maximum_payload_members_read"]):
            raise AuditBlocked("SOCBED eligible members exceed frozen member cap")

        total_payload_bytes = 0
        total_sampled_lines = 0
        file_rows: list[dict[str, Any]] = []
        for item in sorted(eligible, key=lambda row: row["normalized"]):
            remaining = int(policy["archive"]["maximum_payload_bytes_read"]) - total_payload_bytes
            if remaining <= 0:
                raise AuditBlocked("SOCBED frozen payload byte cap exceeded")
            with archive.open(item["info"], "r") as handle:
                sample = _read_sample(
                    handle,
                    max_lines=int(policy["deterministic_sampling"]["maximum_lines_per_member"]),
                    max_bytes=min(
                        remaining,
                        int(policy["archive"]["maximum_member_uncompressed_bytes"]),
                    ),
                    allowed_fields=global_policy["payload_scalar_fields_allowed"],
                    forbidden_fields=global_policy["forbidden_field_tokens"],
                    family=policy["source_family_id"],
                    hash_full_member=True,
                )
            total_payload_bytes += int(sample["bytes_read"])
            total_sampled_lines += int(sample["sampled_lines"])
            exact_timestamp_signature = hashlib.sha256(
                "\n".join(value.isoformat() for value in sample["timestamps"]).encode("utf-8")
            ).hexdigest()
            file_rows.append(
                {
                    "run_key": item["run_key"],
                    "view_key": item["view_key"],
                    "member_sha256": sample["member_sha256"],
                    "timestamp_signature": exact_timestamp_signature,
                    "timestamps": sample["timestamps"],
                    "hosts": sample["hosts"],
                    "sampled_lines": sample["sampled_lines"],
                }
            )

    global_views = sorted({row["view_key"] for row in file_rows})
    by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in file_rows:
        by_run[row["run_key"]].append(row)

    hash_to_runs: dict[str, set[str]] = defaultdict(set)
    signature_to_runs: dict[str, set[str]] = defaultdict(set)
    for row in file_rows:
        hash_to_runs[row["member_sha256"]].add(row["run_key"])
        signature_to_runs[row["timestamp_signature"]].add(row["run_key"])
    duplicate_content_runs = {
        run for runs in hash_to_runs.values() if len(runs) > 1 for run in runs
    }
    duplicate_time_signature_runs = {
        run for runs in signature_to_runs.values() if len(runs) > 1 for run in runs
    }

    run_summaries = []
    bounded_run_group_count = 0
    for run_key in sorted(by_run, key=lambda value: int(value)):
        rows = by_run[run_key]
        views = [row["view_key"] for row in rows]
        unique_hashes = {row["member_sha256"] for row in rows}
        structural_pass = (
            len(rows) == len(global_views)
            and len(set(views)) == len(global_views)
            and set(views) == set(global_views)
            and len(unique_hashes) == len(rows)
        )
        view_days = [
            {timestamp.date().isoformat() for timestamp in row["timestamps"]}
            for row in rows
        ]
        temporal_pass = bool(view_days) and all(days for days in view_days)
        if temporal_pass:
            temporal_pass = bool(set.intersection(*view_days))
        duplicate_flag = (
            run_key in duplicate_content_runs or run_key in duplicate_time_signature_runs
        )
        bounded_pass = structural_pass and temporal_pass and not duplicate_flag
        bounded_run_group_count += int(bounded_pass)
        timestamps = [timestamp for row in rows for timestamp in row["timestamps"]]
        hosts = {host for row in rows for host in row["hosts"]}
        run_summaries.append(
            {
                "run_id": _stable_id(policy["source_family_id"], "run", run_key),
                "view_count": len(set(views)),
                "sampled_host_count": len(hosts),
                "structural_gate_passed": structural_pass,
                "temporal_gate_passed": temporal_pass,
                "duplicate_content_or_time_signature": duplicate_flag,
                "bounded_run_group_passed": bounded_pass,
                **_date_summary(timestamps),
                "statistical_independence_verified": False,
            }
        )

    grouping_supported = bool(run_summaries) and bounded_run_group_count == len(run_summaries)
    return {
        "source_family_id": policy["source_family_id"],
        "status": "completed_with_independence_unproven",
        **identity,
        "central_directory": {
            "member_count": central_member_count,
            "uncompressed_bytes": central_uncompressed_bytes,
            "eligible_member_count": len(eligible),
        },
        "bounded_payload_read": {
            "selected_member_count": len(eligible),
            "bytes_read": total_payload_bytes,
            "sampled_line_count": total_sampled_lines,
            "raw_values_persisted": False,
        },
        "grouping": {
            "parent_view_count": len(global_views),
            "run_suffix_count": len(run_summaries),
            "bounded_run_group_count": bounded_run_group_count,
            "all_run_groups_passed": grouping_supported,
            "runs": run_summaries,
            "verified_independent_lineage_count": None,
            "statistical_independence_demonstrated": False,
            "counts_toward_independent_lineage_quota": False,
            "verdict": (
                "source_native_run_grouping_supported_independence_unproven"
                if grouping_supported
                else "source_native_run_grouping_not_fully_supported"
            ),
        },
    }


def run_audit(
    contract_path: Path,
    cam_archive: Path,
    socbed_archive: Path,
    output_path: Path,
) -> dict[str, Any]:
    contract_bytes = contract_path.read_bytes()
    contract = json.loads(contract_bytes)
    if contract.get("status") != "frozen_before_payload_lineage_audit":
        raise AuditBlocked("contract is not frozen")
    if contract.get("scope", {}).get("label_read_authorized") is not False:
        raise AuditBlocked("label prohibition is not frozen")
    if contract.get("scope", {}).get("family_role_change_authorized") is not False:
        raise AuditBlocked("role-change prohibition is not frozen")

    policies = {
        row["source_family_id"]: row for row in contract.get("families", [])
    }
    expected = {
        "ait_cam_lds_manifestations_filtered",
        "fkie_socbed_acsac2021_winlogbeat",
    }
    if set(policies) != expected:
        raise AuditBlocked("contract family scope drift")
    expected_output = contract["output_contract"]["machine_report_path"].replace(
        "\\", "/"
    )
    if not output_path.resolve().as_posix().endswith(expected_output):
        raise AuditBlocked("output path does not match frozen contract")

    global_policy = contract["global_read_policy"]
    results = []
    for family, archive, runner in (
        (
            "ait_cam_lds_manifestations_filtered",
            cam_archive,
            _audit_cam,
        ),
        (
            "fkie_socbed_acsac2021_winlogbeat",
            socbed_archive,
            _audit_socbed,
        ),
    ):
        try:
            results.append(runner(archive, policies[family], global_policy))
        except (AuditBlocked, OSError, ValueError, zipfile.BadZipFile) as error:
            results.append(
                {
                    "source_family_id": family,
                    "status": "blocked",
                    "error": f"{type(error).__name__}: {error}",
                    "counts_toward_independent_lineage_quota": False,
                }
            )

    report = {
        "schema_version": "project05-llm-editor-l2-bounded-lineage-audit-result-v0.1",
        "audit_date": "2026-07-22",
        "contract_sha256": hashlib.sha256(contract_bytes).hexdigest().upper(),
        "contract_authority_base_commit": contract["authority_base_commit"],
        "contract_status": contract["status"],
        "status": (
            "completed_no_authority_transition"
            if all(row["status"] != "blocked" for row in results)
            else "blocked_no_authority_transition"
        ),
        "scope": {
            "lineage_only_payload_read_performed": True,
            "label_values_used": False,
            "semantic_event_fields_persisted": False,
            "supervision_generated": False,
            "normalization_generated": False,
            "family_roles_changed": False,
            "quota_status_changed": False,
            "baseline_run": False,
            "fine_tuning_run": False,
            "hdfs_replacement_advanced": False,
            "cert_or_iot23_downloaded": False,
            "l2_gate_passed": False,
        },
        "families": results,
        "gate": {
            "audit_completed": all(row["status"] != "blocked" for row in results),
            "cam_independent_lineage_demonstrated": False,
            "socbed_statistical_independence_demonstrated": False,
            "train_lineage_quota_passed": False,
            "family_role_change_applied": False,
            "baseline_authorized": False,
            "fine_tuning_authorized": False,
            "l2_gate_passed": False,
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
    parser.add_argument("--cam-archive", type=Path, required=True)
    parser.add_argument("--socbed-archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = run_audit(
        args.contract,
        args.cam_archive,
        args.socbed_archive,
        args.output,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "contract_sha256": report["contract_sha256"],
                "families": [
                    {
                        "source_family_id": row["source_family_id"],
                        "status": row["status"],
                        "verdict": row.get("grouping", {}).get("verdict"),
                    }
                    for row in report["families"]
                ],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "completed_no_authority_transition" else 2


if __name__ == "__main__":
    raise SystemExit(main())
