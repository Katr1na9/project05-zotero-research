#!/usr/bin/env python3
"""Reacquire the frozen missing blind artifacts without opening their contents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


PLAN_ID = "project05-m3star-final-blind-missing-reacquisition-allowlist-v0.3"
PLAN_STATUS = "frozen_before_missing_payload_reacquisition"
EXPECTED_RECORD_COUNT = 5
EXPECTED_FILE_COUNT = 15
EXPECTED_DOWNLOAD_BYTES = 18_308_224_167
PROGRESS_INTERVAL_BYTES = 256 * 1024 * 1024
MD5_PATTERN = re.compile(r"^[0-9a-f]{32}$")
ALLOWED_ACCESS_CLASSES = {
    "sealed_mixed_container_curator_only_until_split",
    "sealed_telemetry_payload",
    "curator_only_boundary_material",
    "ground_truth_custodian_only_sealed",
}
EXPECTED_RECORDS = {
    "19483937": ("ait-log-data-set-v2.1", "phase2/ait-log-data-set-v2.1"),
    "16911636": ("apt-sandworm-dataset", "phase3/apt-sandworm-dataset"),
    "17659656": ("ainception-storylines", "phase3/ainception-storylines"),
    "8042347": (
        "locked-shields-partners-run-23",
        "phase3/locked-shields-partners-run-23",
    ),
    "14900873": (
        "locked-shields-partners-run-24",
        "phase3/locked-shields-partners-run-24",
    ),
}
EXPECTED_FILES = {
    (
        "19483937",
        "wardbeck_no-pcaps.zip",
        818462147,
        "14eeacd83571a83615c2cce1f6a6eacf",
        "sealed_mixed_container_curator_only_until_split",
    ),
    (
        "19483937",
        "wilson_no-pcaps.zip",
        1083526183,
        "98285593473dc05d0a6899f7cdefcd2d",
        "sealed_mixed_container_curator_only_until_split",
    ),
    (
        "19483937",
        "shaw_no-pcaps.zip",
        1319137852,
        "f890a1f52bc9f893b44254ad86118e39",
        "sealed_mixed_container_curator_only_until_split",
    ),
    (
        "16911636",
        "SandwormAPT.pcap",
        1814217841,
        "bd5d20ab543180e2311c472586d425b1",
        "sealed_telemetry_payload",
    ),
    (
        "16911636",
        "APT_Dataset_Readme.pdf",
        525281,
        "ecfe84f85a3773ea89d28366f1099b24",
        "curator_only_boundary_material",
    ),
    (
        "17659656",
        "SL700_variant_f_a.zip",
        3358489764,
        "8852767f1bc07b4f308483c448a31849",
        "sealed_mixed_container_curator_only_until_split",
    ),
    (
        "8042347",
        "ls23pr_availabilityevents_v1.csv",
        5253571,
        "44ce2cc38ae928a45e339bcfd7e5a070",
        "ground_truth_custodian_only_sealed",
    ),
    (
        "8042347",
        "ls23pr_attacknarratives_v1.json",
        9668498,
        "e139c125e325a5acb1ae2b0958e0ebf5",
        "ground_truth_custodian_only_sealed",
    ),
    (
        "8042347",
        "ls23pr_flows.zip",
        1925103715,
        "f3f5bf9f7cecf2186511eabb38f7accc",
        "sealed_telemetry_payload",
    ),
    (
        "8042347",
        "port-stats.zip",
        472379,
        "32893bb77f7a7c3b5c4d06c3da39aa73",
        "curator_only_boundary_material",
    ),
    (
        "8042347",
        "indexes_openlog_others.json",
        11285,
        "5896cc83c07234e755373905601ebf7c",
        "curator_only_boundary_material",
    ),
    (
        "14900873",
        "lspr24_v2.parquet",
        2775972952,
        "a407011e9edbe615ce58a1e625c0a340",
        "sealed_telemetry_payload",
    ),
    (
        "14900873",
        "eve.log",
        145368223,
        "7706badbf6f5759be544d7bcaabcd235",
        "sealed_telemetry_payload",
    ),
    (
        "14900873",
        "ossec-archive-host-logs.json",
        5040738653,
        "46c4dd79e90ee26d40736996b52abd91",
        "sealed_telemetry_payload",
    ),
    (
        "14900873",
        "attack_narratives.json",
        11275823,
        "4d9be4a2aea86b425dadcb446440752b",
        "ground_truth_custodian_only_sealed",
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_and_sha256(path: Path) -> tuple[str, str]:
    md5_digest = hashlib.md5(usedforsecurity=False)
    sha_digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            md5_digest.update(chunk)
            sha_digest.update(chunk)
    return md5_digest.hexdigest(), sha_digest.hexdigest()


def safe_relative_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field} must remain inside the destination root")
    return path


def iter_files(plan: dict[str, Any]) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    for record in plan["records"]:
        for item in record["files"]:
            yield record, item


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("plan_id") != PLAN_ID or plan.get("status") != PLAN_STATUS:
        raise ValueError("The frozen v0.3 missing-artifact allowlist is required")
    records = plan.get("records")
    if not isinstance(records, list) or len(records) != EXPECTED_RECORD_COUNT:
        raise ValueError("Allowlist must contain exactly five official records")
    record_ids: set[str] = set()
    identities: set[tuple[str, str]] = set()
    observed_files: set[tuple[str, str, int, str, str]] = set()
    total_bytes = 0
    file_count = 0
    for record_index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"records[{record_index}] must be an object")
        record_id = str(record.get("record_id", ""))
        if not record_id.isdigit() or record_id in record_ids:
            raise ValueError("Record ids must be unique Zenodo numeric ids")
        record_ids.add(record_id)
        destination_subdir = safe_relative_path(
            record.get("destination_subdir"),
            f"records[{record_index}].destination_subdir",
        )
        expected_record = EXPECTED_RECORDS.get(record_id)
        if expected_record != (
            record.get("source_id"),
            destination_subdir.as_posix(),
        ):
            raise ValueError("Record source or destination differs from the freeze")
        api_url = str(record.get("record_api_url", ""))
        if api_url != f"https://zenodo.org/api/records/{record_id}":
            raise ValueError("Record API URL differs from the exact Zenodo endpoint")
        files = record.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError(f"records[{record_index}].files must be non-empty")
        for file_index, item in enumerate(files):
            prefix = f"records[{record_index}].files[{file_index}]"
            if not isinstance(item, dict):
                raise ValueError(f"{prefix} must be an object")
            key_path = safe_relative_path(item.get("key"), f"{prefix}.key")
            if len(key_path.parts) != 1:
                raise ValueError(f"{prefix}.key must be a single filename")
            identity = (record_id, str(key_path))
            if identity in identities:
                raise ValueError("Duplicate record/file identity in allowlist")
            identities.add(identity)
            size = item.get("size")
            if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
                raise ValueError(f"{prefix}.size must be a positive integer")
            total_bytes += size
            file_count += 1
            publisher_md5 = str(item.get("publisher_md5", ""))
            if not MD5_PATTERN.fullmatch(publisher_md5):
                raise ValueError(f"{prefix}.publisher_md5 is malformed")
            parsed = urlparse(str(item.get("download_url", "")))
            expected_path = (
                f"/api/records/{record_id}/files/{key_path.as_posix()}/content"
            )
            if (
                parsed.scheme != "https"
                or parsed.netloc != "zenodo.org"
                or parsed.path != expected_path
                or parsed.params
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(f"{prefix}.download_url is outside the exact endpoint")
            if item.get("access_class") not in ALLOWED_ACCESS_CLASSES:
                raise ValueError(f"{prefix}.access_class is not permitted")
            observed_files.add(
                (
                    record_id,
                    str(key_path),
                    size,
                    publisher_md5,
                    str(item["access_class"]),
                )
            )
    if file_count != EXPECTED_FILE_COUNT or total_bytes != EXPECTED_DOWNLOAD_BYTES:
        raise ValueError("Allowlist file count or byte total differs from the freeze")
    if observed_files != EXPECTED_FILES:
        raise ValueError("Allowlist identity set differs from the frozen 15 files")
    scope = plan.get("scope", {})
    if (
        scope.get("official_record_count") != EXPECTED_RECORD_COUNT
        or scope.get("file_count") != EXPECTED_FILE_COUNT
        or scope.get("download_bytes") != EXPECTED_DOWNLOAD_BYTES
    ):
        raise ValueError("Allowlist scope summary differs from its file records")
    rules = plan.get("rules", {})
    for field in (
        "exact_record_file_and_size_allowlist_only",
        "verify_publisher_md5_before_finalizing",
        "compute_private_sha256_without_opening_payload",
        "archives_or_payloads_must_not_be_opened_by_model_development",
        "ground_truth_custodian_files_must_remain_sealed",
        "labelled_sandworm_flow_csv_forbidden",
        "unreviewed_ainception_sl300_forbidden",
        "nonselected_ainception_sl700_variants_forbidden",
    ):
        if rules.get(field) is not True:
            raise ValueError(f"Allowlist rule {field} must remain true")
    if plan.get("one_shot_evaluation_consumed") is not False:
        raise ValueError("One-shot evaluation must remain unconsumed")
    return {
        "record_count": len(records),
        "file_count": file_count,
        "download_bytes": total_bytes,
    }


def destination_path(
    destination_root: Path,
    record: dict[str, Any],
    item: dict[str, Any],
) -> Path:
    relative = safe_relative_path(record["destination_subdir"], "destination_subdir")
    key = safe_relative_path(item["key"], "key")
    root = destination_root.resolve()
    path = (root / relative / key).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Download path escapes the isolated destination root") from exc
    return path


def inspect_local_state(
    plan: dict[str, Any],
    destination_root: Path,
) -> dict[str, Any]:
    existing_complete_count = 0
    existing_complete_bytes = 0
    existing_partial_count = 0
    existing_partial_bytes = 0
    invalid_complete_count = 0
    remaining_bytes = 0
    for record, item in iter_files(plan):
        path = destination_path(destination_root, record, item)
        partial = path.with_suffix(path.suffix + ".part")
        if path.is_file():
            if path.stat().st_size == item["size"]:
                observed_md5, _ = md5_and_sha256(path)
                if observed_md5 == item["publisher_md5"]:
                    existing_complete_count += 1
                    existing_complete_bytes += item["size"]
                    continue
            invalid_complete_count += 1
            remaining_bytes += item["size"]
            continue
        partial_size = partial.stat().st_size if partial.is_file() else 0
        if partial_size > item["size"]:
            raise ValueError(f"Partial file exceeds allowlisted size: {partial.name}")
        if partial_size:
            existing_partial_count += 1
            existing_partial_bytes += partial_size
        remaining_bytes += item["size"] - partial_size
    usage = shutil.disk_usage(destination_root)
    return {
        "plan_valid": True,
        "file_count": EXPECTED_FILE_COUNT,
        "download_bytes": EXPECTED_DOWNLOAD_BYTES,
        "existing_complete_count": existing_complete_count,
        "existing_complete_bytes": existing_complete_bytes,
        "existing_partial_count": existing_partial_count,
        "existing_partial_bytes": existing_partial_bytes,
        "invalid_complete_count": invalid_complete_count,
        "remaining_bytes": remaining_bytes,
        "destination_free_bytes": usage.free,
        "destination_has_required_remaining_space": usage.free > remaining_bytes,
        "payload_contents_opened": False,
        "ground_truth_opened": False,
        "one_shot_evaluation_consumed": False,
    }


def download_one(
    record: dict[str, Any],
    item: dict[str, Any],
    destination_root: Path,
) -> dict[str, Any]:
    path = destination_path(destination_root, record, item)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.stat().st_size != item["size"]:
            raise ValueError(f"Existing final file has the wrong size: {path.name}")
        observed_md5, observed_sha256 = md5_and_sha256(path)
        if observed_md5 != item["publisher_md5"]:
            raise ValueError(f"Existing final file has the wrong MD5: {path.name}")
        return {
            "record_id": record["record_id"],
            "source_id": record["source_id"],
            "key": item["key"],
            "size": item["size"],
            "publisher_md5_verified": True,
            "sha256": observed_sha256,
            "download_reused": True,
            "access_class": item["access_class"],
        }
    partial = path.with_suffix(path.suffix + ".part")
    current = partial.stat().st_size if partial.exists() else 0
    if current > item["size"]:
        raise ValueError(f"Partial file exceeds allowlisted size: {partial.name}")
    headers = {
        "User-Agent": "Project05-final-blind-reconstruction-v0.3",
        "Accept": "*/*",
    }
    if current:
        headers["Range"] = f"bytes={current}-"
    request = urllib.request.Request(item["download_url"], headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        status = getattr(response, "status", response.getcode())
        if current and status == 206:
            mode = "ab"
        elif current and status == 200:
            current = 0
            mode = "wb"
        elif not current and status == 200:
            mode = "wb"
        else:
            raise ValueError(f"Unexpected HTTP status {status} for {item['key']}")
        downloaded = current
        next_progress = (
            ((downloaded // PROGRESS_INTERVAL_BYTES) + 1)
            * PROGRESS_INTERVAL_BYTES
        )
        with partial.open(mode) as handle:
            while True:
                chunk = response.read(8 * 1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                if downloaded > item["size"]:
                    raise ValueError(f"Download exceeds allowlisted size: {item['key']}")
                if downloaded >= next_progress:
                    print(
                        json.dumps(
                            {
                                "status": "download_progress",
                                "record_id": record["record_id"],
                                "key": item["key"],
                                "downloaded_bytes": downloaded,
                                "expected_bytes": item["size"],
                            }
                        ),
                        flush=True,
                    )
                    next_progress += PROGRESS_INTERVAL_BYTES
    if partial.stat().st_size != item["size"]:
        raise ValueError(f"Downloaded size mismatch: {item['key']}")
    observed_md5, observed_sha256 = md5_and_sha256(partial)
    if observed_md5 != item["publisher_md5"]:
        raise ValueError(f"Publisher MD5 mismatch: {item['key']}")
    os.replace(partial, path)
    return {
        "record_id": record["record_id"],
        "source_id": record["source_id"],
        "key": item["key"],
        "size": item["size"],
        "publisher_md5_verified": True,
        "sha256": observed_sha256,
        "download_reused": False,
        "access_class": item["access_class"],
    }


def execute(
    plan_path: Path,
    plan: dict[str, Any],
    destination_root: Path,
    private_ledger_path: Path,
    *,
    max_files: int | None,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    selected = list(iter_files(plan))
    if max_files is not None:
        if max_files <= 0:
            raise ValueError("--max-files must be positive")
        selected = selected[:max_files]
    for index, (record, item) in enumerate(selected, start=1):
        print(
            json.dumps(
                {
                    "status": "download_start",
                    "file_index": index,
                    "selected_file_count": len(selected),
                    "record_id": record["record_id"],
                    "key": item["key"],
                    "expected_bytes": item["size"],
                }
            ),
            flush=True,
        )
        entry = download_one(record, item, destination_root)
        entries.append(entry)
        ledger = {
            "ledger_id": "project05-m3star-final-blind-missing-reacquisition-private-v0.3",
            "status": (
                "reacquisition_complete"
                if len(entries) == EXPECTED_FILE_COUNT
                else "reacquisition_checkpoint"
            ),
            "updated_utc": utc_now(),
            "allowlist_sha256": sha256(plan_path),
            "selected_file_count": len(selected),
            "completed_file_count": len(entries),
            "completed_bytes": sum(item["size"] for item in entries),
            "entries": entries,
            "payload_contents_opened": False,
            "ground_truth_opened": False,
            "cost_values_opened": False,
            "model_outputs_opened": False,
            "one_shot_evaluation_consumed": False,
        }
        write_json(private_ledger_path, ledger)
        print(
            json.dumps(
                {
                    "status": "download_verified",
                    "file_index": index,
                    "selected_file_count": len(selected),
                    "record_id": record["record_id"],
                    "key": item["key"],
                    "size": item["size"],
                    "publisher_md5_verified": True,
                }
            ),
            flush=True,
        )
    return {
        "status": (
            "reacquisition_complete"
            if len(entries) == EXPECTED_FILE_COUNT
            else "reacquisition_checkpoint"
        ),
        "selected_file_count": len(selected),
        "completed_file_count": len(entries),
        "completed_bytes": sum(item["size"] for item in entries),
        "payload_contents_opened": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened": False,
        "one_shot_evaluation_consumed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--destination-root", type=Path, required=True)
    parser.add_argument("--private-ledger", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-files", type=int)
    args = parser.parse_args()
    if args.preflight_only == args.execute:
        parser.error("Choose exactly one of --preflight-only or --execute")
    plan_path = args.allowlist.resolve(strict=True)
    plan = load_json(plan_path)
    validation = validate_plan(plan)
    args.destination_root.mkdir(parents=True, exist_ok=True)
    if args.preflight_only:
        report = {
            **validation,
            **inspect_local_state(plan, args.destination_root),
        }
    else:
        report = execute(
            plan_path,
            plan,
            args.destination_root,
            args.private_ledger,
            max_files=args.max_files,
        )
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
