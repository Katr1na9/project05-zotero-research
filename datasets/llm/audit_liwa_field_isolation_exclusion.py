"""Execute the frozen Liwa field-isolation and protected-exclusion audit.

The executor never extracts the archive and never persists raw member paths,
payload values, forbidden supervision, or protected material.  It emits only
hashes, aggregate counts, quarantine reason codes, and fail-closed verdicts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, NamedTuple


CANDIDATE_ID = "liwa_ad_endpoint_telemetry_30run_2026"
EXPECTED_PROTECTED_FAMILIES = {
    "darpa_tc_e3",
    "darpa_tc_e5",
    "darpa_optc",
    "otrf_apt29",
    "witfoo_precinct6",
}
FIELD_ACTIONS = {
    "forbidden_supervision",
    "detector_summary",
    "binder_only",
    "candidate_raw_event",
    "unknown",
}


class AuditBlocked(RuntimeError):
    """Raised when a frozen contract condition fails closed."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest_bytes(value: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, value).hexdigest().lower()


def digest_file(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def stable_hash(*values: str) -> str:
    return digest_bytes("|".join(values).encode("utf-8"))


def normalized_member_path(value: str) -> str | None:
    raw = str(value).replace("\\", "/")
    while raw.startswith("./"):
        raw = raw[2:]
    if re.match(r"^[a-zA-Z]:/", raw):
        return None
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        return None
    return path.as_posix()


def normalize_field_name(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def normalized_text(value: Any) -> str:
    if isinstance(value, (dict, list)):
        raw = canonical_json(value).decode("utf-8")
    else:
        raw = str(value)
    return " ".join(unicodedata.normalize("NFKC", raw).casefold().split())


def hashed_character_ngrams(value: str, n: int) -> set[str]:
    text = normalized_text(value)
    if not text:
        return set()
    grams = {text} if len(text) < n else {
        text[index : index + n] for index in range(len(text) - n + 1)
    }
    return {digest_bytes(gram.encode("utf-8")) for gram in grams}


def _key_contains(normalized_field: str, normalized_token: str) -> bool:
    if not normalized_token:
        return False
    padded = f"_{normalized_field}_"
    return f"_{normalized_token}_" in padded


def classify_field(field: Any, contract: dict[str, Any]) -> str:
    normalized = normalize_field_name(field)
    isolation = contract["field_isolation_contract"]
    for token in isolation["forbidden_supervision_tokens"]:
        if _key_contains(normalized, normalize_field_name(token)):
            return "forbidden_supervision"
    if normalized.startswith("source_rule_"):
        return "detector_summary"
    for token in isolation["detector_summary_tokens"]:
        if _key_contains(normalized, normalize_field_name(token)):
            return "detector_summary"
    binder_exact = {
        "index",
        "id",
        "source_id",
        "source_data_win_system_eventrecordid",
    }
    if normalized in binder_exact:
        return "binder_only"
    wrapper_deny = {
        "version",
        "source_manager_name",
        "source_location",
        "source_input_type",
    }
    if normalized in wrapper_deny or normalized.startswith("source_decoder_"):
        return "detector_summary"
    candidate_prefixes = (
        "source_agent_",
        "source_data_",
        "source_predecoder_",
    )
    if normalized.startswith(candidate_prefixes) or normalized in {
        "source_full_log",
        "source_timestamp",
    }:
        return "candidate_raw_event"
    return "unknown"


def compile_field_actions(
    headers: Iterable[Any], contract: dict[str, Any]
) -> list[tuple[str, str]]:
    actions = [
        (normalize_field_name(field), classify_field(field, contract))
        for field in headers
    ]
    invalid = [action for _, action in actions if action not in FIELD_ACTIONS]
    if invalid:
        raise AuditBlocked("invalid field action")
    if any(action == "unknown" for _, action in actions):
        unknown_hashes = sorted(
            digest_bytes(field.encode("utf-8"))
            for field, action in actions
            if action == "unknown"
        )
        raise AuditBlocked(
            "unknown field names fail closed: " + ",".join(unknown_hashes)
        )
    return actions


def isolate_row(
    actions: list[tuple[str, str]], values: list[str]
) -> dict[str, Any]:
    if len(actions) != len(values):
        raise AuditBlocked("CSV row width differs from frozen header width")
    model_view: list[list[str]] = []
    binder: list[list[str]] = []
    denied_nonempty: Counter[str] = Counter()
    action_nonempty: Counter[str] = Counter()
    for (field, action), value in zip(actions, values):
        if value not in (None, ""):
            action_nonempty[action] += 1
        if action == "candidate_raw_event":
            model_view.append([field, value])
        elif action == "binder_only":
            binder.append([field, value])
        elif value not in (None, ""):
            denied_nonempty[action] += 1
    return {
        "model_view": model_view,
        "binder": binder,
        "denied_nonempty": dict(denied_nonempty),
        "action_nonempty": dict(action_nonempty),
    }


def build_pointer_audit(
    *,
    archive_sha256: str,
    record_revision: int,
    member_path_hash: str,
    member_content_hash: str,
    row_index: int,
    raw_record_hash: str,
    binder_values: list[list[str]],
    model_view_values: list[list[str]],
) -> dict[str, str]:
    stable_ids = [value for _, value in binder_values if value not in (None, "")]
    record_identity = stable_hash(
        "source-record",
        str(row_index),
        raw_record_hash,
        *stable_ids,
    )
    source_span_hash = digest_bytes(canonical_json(model_view_values))
    pointer_hash = stable_hash(
        archive_sha256,
        str(record_revision),
        member_path_hash,
        member_content_hash,
        record_identity,
        source_span_hash,
    )
    return {
        "record_identity_hash": record_identity,
        "source_span_hash": source_span_hash,
        "pointer_candidate_hash": pointer_hash,
        "binding_status": "unbound" if stable_ids else "ambiguous",
    }


class ScanOutcome(NamedTuple):
    exact: bool
    near: bool
    maximum_jaccard: float

    @property
    def matched(self) -> bool:
        return self.exact or self.near


class ProtectedScanner:
    def __init__(self, lock: dict[str, Any]):
        validate_protected_lock(lock)
        self.n = int(lock["character_ngram_n"])
        self.minimum_chars = int(lock["minimum_protected_text_chars"])
        self.threshold = float(lock["near_duplicate_threshold"])
        self.exact_hashes = {
            str(value).casefold() for value in lock["normalized_text_hashes"]
        }
        self.signatures: list[set[str]] = []
        self.inverted: dict[str, list[int]] = defaultdict(list)
        for index, row in enumerate(lock["ngram_signatures"]):
            grams = {str(value).casefold() for value in row["ngram_hashes"]}
            if not grams or len(grams) != int(row["ngram_count"]):
                raise AuditBlocked("protected n-gram signature malformed")
            self.signatures.append(grams)
            for gram in grams:
                self.inverted[gram].append(index)

    def scan(self, value: Any) -> ScanOutcome:
        text = normalized_text(value)
        if len(text) < self.minimum_chars:
            return ScanOutcome(False, False, 0.0)
        value_hash = digest_bytes(text.encode("utf-8"))
        if value_hash in self.exact_hashes:
            return ScanOutcome(True, False, 1.0)
        grams = hashed_character_ngrams(text, self.n)
        overlaps: Counter[int] = Counter()
        for gram in grams:
            for index in self.inverted.get(gram, ()):
                overlaps[index] += 1
        maximum = 0.0
        near = False
        for index, intersection in overlaps.items():
            union = len(grams) + len(self.signatures[index]) - intersection
            score = intersection / union if union else 1.0
            maximum = max(maximum, score)
            if score >= self.threshold:
                near = True
        return ScanOutcome(False, near, maximum)


def validate_protected_lock(lock: dict[str, Any]) -> None:
    if lock.get("contains_raw_test_payload") is not False:
        raise AuditBlocked("protected lock contains raw test payload")
    if lock.get("contains_raw_private_gold") is not False:
        raise AuditBlocked("protected lock contains raw private gold")
    if set(lock.get("blocked_family_ids", [])) != EXPECTED_PROTECTED_FAMILIES:
        raise AuditBlocked("protected family set changed")
    if int(lock.get("character_ngram_n", 0)) != 5:
        raise AuditBlocked("protected n-gram size changed")
    if int(lock.get("minimum_protected_text_chars", 0)) != 16:
        raise AuditBlocked("protected minimum text length changed")
    if float(lock.get("near_duplicate_threshold", 0)) != 0.85:
        raise AuditBlocked("protected threshold changed")
    if not lock.get("normalized_text_hashes") or not lock.get("ngram_signatures"):
        raise AuditBlocked("protected lock is empty")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AuditBlocked(f"expected JSON object: {path.name}")
    return value


def validate_authority(authority: dict[str, Any], root: Path) -> dict[str, Path]:
    if authority.get("status") != "authorized_for_single_candidate_scoped_execution":
        raise AuditBlocked("execution authority status mismatch")
    if authority.get("candidate_id") != CANDIDATE_ID:
        raise AuditBlocked("execution authority candidate mismatch")
    quota = authority.get("quota_lock", {})
    numeric = [value for key, value in quota.items() if key.endswith("credit")]
    if not numeric or any(int(value) != 0 for value in numeric):
        raise AuditBlocked("execution authority quota is not zero")
    frozen = authority["frozen_inputs"]
    paths: dict[str, Path] = {}
    for key in (
        "contract",
        "catalog",
        "bounded_result",
        "source_role_review",
        "protected_lock",
    ):
        path = (root / frozen[f"{key}_path"]).resolve()
        if root.resolve() not in path.parents:
            raise AuditBlocked(f"{key} path escapes worktree")
        if digest_file(path) != str(frozen[f"{key}_sha256"]).casefold():
            raise AuditBlocked(f"{key} hash mismatch")
        paths[key] = path
    archive = (root / frozen["archive_path"]).resolve()
    if root.resolve() not in archive.parents:
        raise AuditBlocked("archive path escapes worktree")
    if archive.stat().st_size != int(frozen["archive_bytes"]):
        raise AuditBlocked("archive size mismatch")
    if digest_file(archive, "md5") != str(frozen["archive_md5"]).casefold():
        raise AuditBlocked("archive MD5 mismatch")
    paths["archive"] = archive
    return paths


def prior_member_groups(result: dict[str, Any]) -> tuple[str, dict[str, str | None]]:
    rows = [
        row
        for row in result.get("archives", [])
        if row.get("source_family_id") == CANDIDATE_ID
    ]
    if len(rows) != 1:
        raise AuditBlocked("bounded result does not contain exactly one Liwa archive")
    row = rows[0]
    mapping: dict[str, str | None] = {}
    for probe in row["bounded_probe"]["members"]:
        mapping[str(probe["member_path_hash"])] = probe.get("run_group_hash")
    if len(mapping) != 31:
        raise AuditBlocked("bounded Liwa member map changed")
    return str(row["source_key"]), mapping


def protected_artifact_hashes(lock: dict[str, Any]) -> set[str]:
    hashes: set[str] = set()
    for key in ("source_file_sha256", "source_manifest_sha256"):
        value = lock.get(key, {})
        if isinstance(value, dict):
            hashes.update(str(item).casefold() for item in value.values())
    return hashes


def read_csv(raw: bytes) -> tuple[list[str], list[list[str]]]:
    try:
        text = raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise AuditBlocked("Liwa CSV is not strict UTF-8") from exc
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect=dialect)
    try:
        headers = next(reader)
    except StopIteration as exc:
        raise AuditBlocked("empty Liwa CSV") from exc
    rows = [list(row) for row in reader]
    return headers, rows


def scan_model_view(
    scanner: ProtectedScanner,
    model_view: list[list[str]],
) -> tuple[bool, bool, float]:
    exact = False
    near = False
    maximum = 0.0
    for _, value in model_view:
        outcome = scanner.scan(value)
        exact = exact or outcome.exact
        near = near or outcome.near
        maximum = max(maximum, outcome.maximum_jaccard)
    if model_view:
        outcome = scanner.scan(model_view)
        exact = exact or outcome.exact
        near = near or outcome.near
        maximum = max(maximum, outcome.maximum_jaccard)
    return exact, near, maximum


def run_pass(
    *,
    archive_path: Path,
    contract: dict[str, Any],
    lock: dict[str, Any],
    source_key: str,
    member_groups: dict[str, str | None],
    archive_sha256: str,
    quarantined_record_hashes: set[str] | None = None,
) -> dict[str, Any]:
    scanner = ProtectedScanner(lock)
    protected_hashes = protected_artifact_hashes(lock)
    action_columns: Counter[str] = Counter()
    action_nonempty: Counter[str] = Counter()
    group_counts: dict[str, Counter[str]] = defaultdict(Counter)
    quarantined: set[str] = set()
    exact_records = 0
    near_records = 0
    maximum_jaccard = 0.0
    total_records = 0
    scanned_records = 0
    ambiguous_pointer_records = 0
    exact_member_hash_count = 0
    member_count = 0
    header_shape_hashes: Counter[str] = Counter()
    field_identity_hashes: set[str] = set()

    with zipfile.ZipFile(archive_path) as archive:
        csv_infos = sorted(
            [
                info
                for info in archive.infolist()
                if not info.is_dir() and info.filename.casefold().endswith(".csv")
            ],
            key=lambda info: info.filename,
        )
        if len(csv_infos) != 31:
            raise AuditBlocked("Liwa CSV member count changed")

        compiled: list[tuple[zipfile.ZipInfo, bytes, str, str | None, list[tuple[str, str]], list[list[str]]]] = []
        for info in csv_infos:
            normalized_path = normalized_member_path(info.filename)
            if normalized_path is None:
                raise AuditBlocked("unsafe Liwa member path")
            member_path_hash = stable_hash(CANDIDATE_ID, source_key, normalized_path)
            if member_path_hash not in member_groups:
                raise AuditBlocked("Liwa member is absent from bounded map")
            raw = archive.read(info)
            member_hash = digest_bytes(raw)
            exact_member_hash_count += int(member_hash in protected_hashes)
            headers, rows = read_csv(raw)
            actions = compile_field_actions(headers, contract)
            header_shape_hashes[digest_bytes(canonical_json(actions))] += 1
            for field, action in actions:
                action_columns[action] += 1
                field_identity_hashes.add(digest_bytes(field.encode("utf-8")))
            compiled.append(
                (
                    info,
                    raw,
                    member_path_hash,
                    member_groups[member_path_hash],
                    actions,
                    rows,
                )
            )

        for _, raw, member_path_hash, run_group_hash, actions, rows in compiled:
            member_count += 1
            member_hash = digest_bytes(raw)
            member_exact = member_hash in protected_hashes
            group_key = run_group_hash or "unstable_group"
            for row_index, values in enumerate(rows):
                total_records += 1
                isolated = isolate_row(actions, values)
                for key, count in isolated["action_nonempty"].items():
                    action_nonempty[key] += int(count)
                raw_record_hash = digest_bytes(canonical_json(values))
                pointer = build_pointer_audit(
                    archive_sha256=archive_sha256,
                    record_revision=int(contract["frozen_source_identity"]["record_revision"]),
                    member_path_hash=member_path_hash,
                    member_content_hash=member_hash,
                    row_index=row_index,
                    raw_record_hash=raw_record_hash,
                    binder_values=isolated["binder"],
                    model_view_values=isolated["model_view"],
                )
                record_hash = pointer["pointer_candidate_hash"]
                group_counts[group_key]["total_records"] += 1
                if pointer["binding_status"] == "ambiguous":
                    ambiguous_pointer_records += 1
                if quarantined_record_hashes is not None and record_hash in quarantined_record_hashes:
                    group_counts[group_key]["prefilter_quarantined_records"] += 1
                    continue
                scanned_records += 1
                exact, near, maximum = scan_model_view(
                    scanner, isolated["model_view"]
                )
                exact = exact or member_exact
                exact_records += int(exact)
                near_records += int(near)
                maximum_jaccard = max(maximum_jaccard, maximum)
                if exact or near:
                    quarantined.add(record_hash)
                    group_counts[group_key]["matched_records"] += 1
                else:
                    group_counts[group_key]["clean_records"] += 1

    safe_groups = [
        {
            "run_group_hash": None if key == "unstable_group" else key,
            "stable_source_native_group": key != "unstable_group",
            **dict(sorted(counts.items())),
        }
        for key, counts in sorted(group_counts.items())
    ]
    return {
        "csv_member_count": member_count,
        "record_count": total_records,
        "scanned_record_count": scanned_records,
        "field_action_column_counts": dict(sorted(action_columns.items())),
        "field_action_nonempty_value_counts": dict(sorted(action_nonempty.items())),
        "distinct_field_identity_hash_count": len(field_identity_hashes),
        "header_shape_hash_counts": dict(sorted(header_shape_hashes.items())),
        "exact_protected_member_hash_count": exact_member_hash_count,
        "exact_match_record_count": exact_records,
        "near_duplicate_match_record_count": near_records,
        "matched_record_count": len(quarantined),
        "matched_candidate_record_hashes": sorted(quarantined),
        "maximum_jaccard": maximum_jaccard,
        "ambiguous_pointer_record_count": ambiguous_pointer_records,
        "run_groups": safe_groups,
        "raw_member_paths_persisted": False,
        "raw_payload_values_persisted": False,
        "forbidden_supervision_values_persisted": False,
        "protected_payload_persisted": False,
    }


def execute(authority_path: Path, output_path: Path) -> dict[str, Any]:
    root = Path.cwd().resolve()
    authority = load_json(authority_path)
    paths = validate_authority(authority, root)
    contract = load_json(paths["contract"])
    catalog = load_json(paths["catalog"])
    bounded = load_json(paths["bounded_result"])
    lock = load_json(paths["protected_lock"])

    if contract.get("status") != "draft_frozen_not_execution_authority":
        raise AuditBlocked("frozen design contract status changed")
    if contract.get("candidate_id") != CANDIDATE_ID:
        raise AuditBlocked("contract candidate mismatch")
    if catalog["gate"]["liwa_family_quota_credit"] != 0:
        raise AuditBlocked("catalog family quota is nonzero")
    if catalog["gate"]["liwa_lineage_quota_credit"] != 0:
        raise AuditBlocked("catalog lineage quota is nonzero")
    if catalog["gate"]["liwa_sample_quota_credit"] != 0:
        raise AuditBlocked("catalog sample quota is nonzero")

    source_key, member_groups = prior_member_groups(bounded)
    archive_sha256 = digest_file(paths["archive"])
    protected_hashes = protected_artifact_hashes(lock)
    archive_exact = archive_sha256 in protected_hashes

    first = run_pass(
        archive_path=paths["archive"],
        contract=contract,
        lock=lock,
        source_key=source_key,
        member_groups=member_groups,
        archive_sha256=archive_sha256,
    )
    quarantined = set(first["matched_candidate_record_hashes"])
    if archive_exact:
        raise AuditBlocked("Liwa archive exactly matches a protected artifact")
    second = run_pass(
        archive_path=paths["archive"],
        contract=contract,
        lock=lock,
        source_key=source_key,
        member_groups=member_groups,
        archive_sha256=archive_sha256,
        quarantined_record_hashes=quarantined,
    )
    post_clean = (
        second["exact_match_record_count"] == 0
        and second["near_duplicate_match_record_count"] == 0
        and second["matched_record_count"] == 0
    )
    status = (
        "passed_no_authority_transition"
        if post_clean
        else "blocked_protected_exclusion"
    )
    result = {
        "schema_version": "project05-llm-editor-l2-liwa-field-isolation-protected-exclusion-result-v0.1",
        "created_date": "2026-07-23",
        "status": status,
        "candidate_id": CANDIDATE_ID,
        "authority": {
            "path": authority_path.as_posix(),
            "sha256": digest_file(authority_path),
            "authority_base_commit": authority["authority_base_commit"],
        },
        "input_hashes": {
            "contract_sha256": digest_file(paths["contract"]),
            "catalog_sha256": digest_file(paths["catalog"]),
            "bounded_result_sha256": digest_file(paths["bounded_result"]),
            "source_role_review_sha256": digest_file(paths["source_role_review"]),
            "protected_lock_sha256": digest_file(paths["protected_lock"]),
            "archive_sha256": archive_sha256,
            "executor_sha256": digest_file(Path(__file__).resolve()),
        },
        "field_isolation": {
            "status": "passed" if first["record_count"] > 0 else "blocked",
            "csv_member_count": first["csv_member_count"],
            "record_count": first["record_count"],
            "field_action_column_counts": first["field_action_column_counts"],
            "field_action_nonempty_value_counts": first[
                "field_action_nonempty_value_counts"
            ],
            "distinct_field_identity_hash_count": first[
                "distinct_field_identity_hash_count"
            ],
            "header_shape_hash_counts": first["header_shape_hash_counts"],
            "unknown_field_count": 0,
            "raw_member_paths_persisted": False,
            "raw_payload_values_persisted": False,
            "forbidden_supervision_values_persisted": False,
        },
        "pointer_audit": {
            "programmatic_binding_only": True,
            "record_count": first["record_count"],
            "ambiguous_pointer_record_count": first[
                "ambiguous_pointer_record_count"
            ],
            "bound_case_evidence_count": 0,
            "raw_member_paths_visible_to_model": False,
        },
        "protected_exclusion_prefilter": {
            "archive_exact_match": archive_exact,
            "member_exact_match_count": first[
                "exact_protected_member_hash_count"
            ],
            "record_exact_match_count": first["exact_match_record_count"],
            "record_near_duplicate_match_count": first[
                "near_duplicate_match_record_count"
            ],
            "quarantined_record_count": first["matched_record_count"],
            "quarantined_candidate_record_hashes": first[
                "matched_candidate_record_hashes"
            ],
            "maximum_jaccard": first["maximum_jaccard"],
            "threshold": float(lock["near_duplicate_threshold"]),
        },
        "protected_exclusion_post_quarantine_rescan": {
            "scanned_record_count": second["scanned_record_count"],
            "exact_match_record_count": second["exact_match_record_count"],
            "near_duplicate_match_record_count": second[
                "near_duplicate_match_record_count"
            ],
            "remaining_match_record_count": second["matched_record_count"],
            "maximum_jaccard": second["maximum_jaccard"],
            "passed": post_clean,
        },
        "run_group_counts": first["run_groups"],
        "quota_and_authority_lock": {
            "effective_catalog_role": "train_candidate",
            "family_credit": 0,
            "lineage_credit": 0,
            "sample_credit": 0,
            "sample_materialization_authorized": False,
            "baseline_authorized": False,
            "fine_tuning_authorized": False,
            "l2_gate_passed": False,
            "kernel_or_m3_modified": False,
            "git_push_authorized": False,
        },
        "persistence_audit": {
            "raw_member_paths_persisted": False,
            "raw_liwa_values_persisted": False,
            "forbidden_supervision_values_persisted": False,
            "protected_payload_persisted": False,
            "model_generations_persisted": False,
        },
        "next_gate": "separate quota-capacity, lineage, and source-role admission review",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = execute(args.authority, args.output)
    except (AuditBlocked, csv.Error, json.JSONDecodeError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 2
    print(
        json.dumps(
            {
                "status": result["status"],
                "records": result["field_isolation"]["record_count"],
                "quarantined": result["protected_exclusion_prefilter"][
                    "quarantined_record_count"
                ],
                "post_rescan_matches": result[
                    "protected_exclusion_post_quarantine_rescan"
                ]["remaining_match_record_count"],
                "quota": result["quota_and_authority_lock"]["family_credit"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "passed_no_authority_transition" else 3


if __name__ == "__main__":
    raise SystemExit(main())
