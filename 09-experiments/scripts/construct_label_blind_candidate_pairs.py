#!/usr/bin/env python3
"""Construct the authorized label-blind pointer-bounded candidate pairs."""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import io
import json
import re
import sys
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import audit_beth_source_gate as beth_gate  # noqa: E402
import audit_label_blind_pair_tokens as token_gate  # noqa: E402
import build_candidate_edge_training as cedge  # noqa: E402


SCHEMA_VERSION = "project05-label-blind-candidate-pairs-v0.1"
TTP_ID_RE = re.compile(r"(?<![A-Za-z0-9])T[0-9]{4}(?:\.[0-9]{3})?(?![A-Za-z0-9])")
GENERATOR_FUNCTIONS = {
    "N1": cedge.generate_n1_object_swap,
    "N2": cedge.generate_n2_pointer_swap,
    "N4": cedge.generate_n4_time_mismatch,
}


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


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _require_file_hash(path: Path, expected: str, label: str) -> None:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"{label} is missing")
    if sha256_file(path) != expected:
        raise ValueError(f"{label} SHA-256 mismatch")


def validate_authorized_inputs(
    contract: dict[str, Any],
    *,
    positive_readiness_path: Path,
    beth_acquisition_path: Path,
    beth_audit_path: Path,
    field_map_path: Path,
    protected_lock_path: Path,
    selection_contract_path: Path | None = None,
    tokenizer_lock_path: Path | None = None,
) -> None:
    inputs = contract["inputs"]
    for path, key, label in (
        (
            positive_readiness_path,
            "positive_remap_readiness_sha256",
            "positive-remap readiness",
        ),
        (
            beth_acquisition_path,
            "beth_acquisition_manifest_sha256",
            "BETH acquisition manifest",
        ),
        (
            beth_audit_path,
            "beth_source_gate_audit_sha256",
            "BETH source-Gate audit",
        ),
        (field_map_path, "field_map_sha256", "v0.3 field map"),
        (protected_lock_path, "protected_lock_sha256", "protected lock"),
    ):
        _require_file_hash(path, inputs[key], label)
    if "token_aware_selection_contract_sha256" in inputs:
        if selection_contract_path is None or tokenizer_lock_path is None:
            raise ValueError("token-aware selection inputs are required")
        _require_file_hash(
            selection_contract_path,
            inputs["token_aware_selection_contract_sha256"],
            "token-aware selection contract",
        )
        _require_file_hash(
            tokenizer_lock_path,
            inputs["tokenizer_lock_sha256"],
            "tokenizer lock",
        )


def _origin_only_url(value: Any) -> str:
    parsed = urllib.parse.urlsplit(str(value or ""))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("source provenance URL is invalid")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def _sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("source record provenance is missing")
    output = copy.deepcopy(record)
    output["provenance"] = {
        "license_id": provenance.get("license_id"),
        "license_sha256": provenance.get("license_sha256"),
        "source_file_sha256": provenance.get("source_file_sha256"),
        "source_url": _origin_only_url(provenance.get("source_url")),
    }
    if any(not output["provenance"].get(key) for key in cedge.REQUIRED_PROVENANCE):
        raise ValueError("source record provenance is incomplete")
    return output


def _eligible_candidates(
    record: dict[str, Any], field_maps: dict[str, Any]
) -> list[dict[str, Any]]:
    proposed = list(record.get("observation_candidates") or [])
    proposed.extend(cedge.propose_record_candidates(record, field_maps))
    output: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    for candidate in proposed:
        encoded = canonical_bytes(candidate)
        if encoded in seen:
            continue
        seen.add(encoded)
        if cedge.validate_g0_candidate(record, candidate, field_maps)["eligible"]:
            output.append(copy.deepcopy(candidate))
    return output


def enrich_record(
    record: dict[str, Any], field_maps: dict[str, Any]
) -> dict[str, Any] | None:
    sanitized = _sanitize_record(record)
    candidates = _eligible_candidates(sanitized, field_maps)
    if not candidates:
        return None
    sanitized["observation_candidates"] = candidates
    return sanitized


def load_historical_records(
    records_root: Path,
    readiness: dict[str, Any],
    required_families: set[str],
    field_maps: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    records_root = Path(records_root)
    if not records_root.is_dir():
        raise ValueError("historical records root is missing")
    manifest = readiness.get("source_file_manifest")
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("positive-remap source manifest is missing")
    output: dict[str, list[dict[str, Any]]] = {family: [] for family in required_families}
    seen_files: set[str] = set()
    for entry in manifest:
        relative = entry.get("relative_path")
        if not isinstance(relative, str) or relative in seen_files:
            raise ValueError("historical source manifest path is invalid")
        seen_files.add(relative)
        path = records_root / Path(relative)
        if not path.is_file():
            raise ValueError(f"historical source file is missing: {relative}")
        if path.stat().st_size != entry.get("bytes"):
            raise ValueError(f"historical source byte count mismatch: {relative}")
        if sha256_file(path) != entry.get("sha256"):
            raise ValueError(f"historical source SHA-256 mismatch: {relative}")
        family = path.name[: -len(".jsonl.gz")]
        if family not in required_families:
            continue
        expected_split = field_maps["families"][family]["split_role"]
        if Path(relative).parts[0] != expected_split:
            raise ValueError(f"historical source split mismatch: {family}")
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"invalid historical JSONL at {relative}:{line_number}"
                    ) from error
                if not isinstance(record, dict) or record.get("source_family_id") != family:
                    raise ValueError(f"historical record family mismatch: {relative}")
                enriched = enrich_record(record, field_maps)
                if enriched is not None:
                    output[family].append(enriched)
    duplicate_counts: dict[str, int] = {}
    for family, rows in output.items():
        output[family], duplicate_counts[family] = deduplicate_exact_records(rows)
    missing = sorted(family for family, rows in output.items() if not rows)
    if missing:
        raise ValueError(f"required historical positive families are empty: {missing}")
    return output, duplicate_counts


def deduplicate_exact_records(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    duplicates = 0
    for record in records:
        digest = cedge.record_sha256(record)
        if digest in seen:
            duplicates += 1
            continue
        seen.add(digest)
        output.append(record)
    return output, duplicates


def normalize_beth_row(
    row: dict[str, str],
    *,
    row_number: int,
    source_sha256: str,
    license_sha256: str,
    source_url: str,
) -> dict[str, Any] | None:
    visible = {
        "timestamp": str(row.get("timestamp") or "").strip(),
        "process_id": str(row.get("processId") or "").strip(),
        "parent_process_id": str(row.get("parentProcessId") or "").strip(),
        "user_id": str(row.get("userId") or "").strip(),
        "process_name": str(row.get("processName") or "").strip(),
        "host_name": str(row.get("hostName") or "").strip(),
        "event_id": str(row.get("eventId") or "").strip(),
        "event_name": str(row.get("eventName") or "").strip(),
        "args_num": str(row.get("argsNum") or "").strip(),
        "return_value": str(row.get("returnValue") or "").strip(),
        "args": str(row.get("args") or "").strip(),
    }
    required = (
        "timestamp",
        "process_id",
        "parent_process_id",
        "process_name",
        "host_name",
        "event_name",
    )
    if any(not visible[key] for key in required):
        return None
    artifact_id = "ART-" + sha256_bytes(f"beth:{source_sha256}".encode())[:16]
    document_id = "DOC-" + sha256_bytes(
        f"beth-document:{source_sha256}".encode()
    )[:16]
    record_identity = {
        "artifact_id": artifact_id,
        "row_number": int(row_number),
        "payload": visible,
    }
    record_id = "REC-" + sha256_bytes(canonical_bytes(record_identity))[:16]
    record = {
        "schema_version": "project05-source-record-v0.1",
        "source_family_id": "beth_process_events",
        "source_type": "endpoint_event",
        "artifact_id": artifact_id,
        "document_id": document_id,
        "record_id": record_id,
        "payload": visible,
        "provenance": {
            "license_id": "CC0-1.0",
            "license_sha256": license_sha256,
            "source_file_sha256": source_sha256,
            "source_url": _origin_only_url(source_url),
        },
        "observation_candidates": [],
        "null_eligible_candidate": False,
    }
    return record


def load_beth_selection_pool(
    source_path: Path,
    acquisition: dict[str, Any],
    source_audit: dict[str, Any],
    beth_contract: dict[str, Any],
    field_maps: dict[str, Any],
    pool_limit: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_path = Path(source_path)
    expected = beth_contract["dataset"]
    if source_audit.get("status") != "passed_candidate_fourth_family_source_gate":
        raise ValueError("BETH source Gate did not pass")
    if source_audit.get("g0_audit", {}).get("eligible_candidates", 0) < pool_limit:
        raise ValueError("BETH source Gate has fewer candidates than the pool limit")
    if source_path.stat().st_size != expected["expected_csv_bytes"]:
        raise ValueError("BETH source bytes no longer match the frozen contract")
    if sha256_file(source_path) != expected["expected_csv_sha256"]:
        raise ValueError("BETH source SHA-256 no longer matches the frozen contract")
    if acquisition.get("sha256") != expected["expected_csv_sha256"]:
        raise ValueError("BETH acquisition manifest identity mismatch")
    if acquisition.get("license_status") != "passed_cc0_v3_no_conflicting_notice":
        raise ValueError("BETH license Gate is not passed")
    license_sha256 = acquisition.get("license_evidence", {}).get("legalcode_sha256")
    if not license_sha256:
        raise ValueError("BETH CC0 legalcode evidence is missing")
    rows: list[dict[str, Any]] = []
    rows_examined = 0
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if list(reader.fieldnames or []) != beth_contract["required_schema_fields"]:
            raise ValueError("BETH CSV schema changed after the source Gate")
        for row_number, row in enumerate(reader, start=2):
            rows_examined += 1
            if None in row or any(value is None for value in row.values()):
                raise ValueError("BETH CSV row width mismatch")
            record = normalize_beth_row(
                row,
                row_number=row_number,
                source_sha256=expected["expected_csv_sha256"],
                license_sha256=license_sha256,
                source_url=acquisition["requested_url"],
            )
            if record is None:
                continue
            enriched = enrich_record(record, field_maps)
            if enriched is None:
                continue
            rows.append(enriched)
            if len(rows) == pool_limit:
                break
    if len(rows) != pool_limit:
        raise ValueError("BETH deterministic selection pool is incomplete")
    return rows, {
        "rows_examined": rows_examined,
        "eligible_rows_retained": len(rows),
        "label_values_read": False,
        "label_values_used": False,
        "standalone_normalized_records_written": False,
    }


def _generator_plan(quotas: dict[str, int]) -> list[str]:
    remaining = {name: int(quotas.get(name, 0)) for name in ("N1", "N2", "N3", "N4")}
    if any(value < 0 for value in remaining.values()):
        raise ValueError("negative generator quota must be non-negative")
    output: list[str] = []
    while any(remaining.values()):
        for name in ("N1", "N2", "N3", "N4"):
            if remaining[name]:
                output.append(name)
                remaining[name] -= 1
    return output


def _negative_candidates(
    generator: str,
    positive: dict[str, Any],
    positive_record: dict[str, Any],
    packet_records: list[dict[str, Any]],
    field_maps: dict[str, Any],
    used_negative_ids: set[str],
) -> Iterable[dict[str, Any]]:
    if generator == "N3":
        family_map = field_maps["families"][positive["source_family_id"]]
        template = cedge._template_by_id(family_map, positive["field_map_id"])
        replacements = template.get("incompatible_predicates") or []
        if not replacements:
            return
        for replacement in replacements:
            try:
                negative = cedge.generate_n3_predicate_incompatibility(
                    positive, replacement, field_maps
                )
            except ValueError:
                continue
            if negative["example_id"] not in used_negative_ids:
                yield negative
        return
    function = GENERATOR_FUNCTIONS[generator]
    positive_hash = cedge.record_sha256(positive_record)
    donors = sorted(packet_records, key=cedge.record_sha256)
    for donor in donors:
        if cedge.record_sha256(donor) == positive_hash:
            continue
        try:
            negative = function(positive, donor, field_maps)
            if negative["example_id"] in used_negative_ids:
                continue
            yield negative
        except ValueError:
            continue


def _try_negative(
    generator: str,
    positive: dict[str, Any],
    positive_record: dict[str, Any],
    packet_records: list[dict[str, Any]],
    field_maps: dict[str, Any],
    used_negative_ids: set[str],
) -> dict[str, Any] | None:
    return next(
        iter(
            _negative_candidates(
                generator,
                positive,
                positive_record,
                packet_records,
                field_maps,
                used_negative_ids,
            )
        ),
        None,
    )


def serialized_token_count(
    example: dict[str, Any],
    *,
    tokenizer: Any,
    serialization: dict[str, Any],
) -> int:
    messages = token_gate.build_messages(example, serialization)
    rendered = token_gate.render_messages(messages, serialization)
    count = len(tokenizer.encode(rendered, add_special_tokens=False).ids)
    if count <= 0:
        raise ValueError("tokenizer returned an empty encoding")
    return count


def construct_family_pairs(
    records: list[dict[str, Any]],
    *,
    positive_quota: int,
    generator_quotas: dict[str, int],
    field_maps: dict[str, Any],
    tokenizer: Any | None = None,
    serialization: dict[str, Any] | None = None,
    maximum_example_tokens: int | None = None,
) -> tuple[
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, Any],
]:
    if sum(int(value) for value in generator_quotas.values()) != positive_quota:
        raise ValueError("negative-generator quotas do not equal the positive quota")
    record_index = {cedge.record_sha256(record): record for record in records}
    if len(record_index) != len(records):
        raise ValueError("duplicate normalized source records are present")
    packets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    entries: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for record in records:
        packets[cedge._packet_key(record)].append(record)
        for candidate in record.get("observation_candidates") or []:
            positive = cedge.build_supported_example(record, candidate, field_maps)
            entries.append((record, positive))
    entries.sort(key=lambda item: item[1]["example_id"])
    used_positive_ids: set[str] = set()
    used_negative_ids: set[str] = set()
    examples: list[dict[str, Any]] = []
    length_rejections = Counter()
    length_aware = tokenizer is not None
    if length_aware != (serialization is not None and maximum_example_tokens is not None):
        raise ValueError("token-aware selection inputs must be supplied together")
    for generator in _generator_plan(generator_quotas):
        selected = None
        for record, positive in entries:
            if positive["example_id"] in used_positive_ids:
                continue
            positive_tokens = None
            if length_aware:
                positive_tokens = serialized_token_count(
                    positive,
                    tokenizer=tokenizer,
                    serialization=serialization,
                )
                if positive_tokens > maximum_example_tokens:
                    length_rejections[f"{generator}:positive"] += 1
                    continue
            negatives = _negative_candidates(
                generator,
                positive,
                record,
                packets[positive["packet_key"]],
                field_maps,
                used_negative_ids,
            )
            for negative in negatives:
                validation = cedge.validate_negative_example(
                    negative, record_index, field_maps
                )
                if not validation["valid"]:
                    raise ValueError(
                        f"generated {generator} proof failed: {validation['reason_codes']}"
                    )
                negative_tokens = None
                if length_aware:
                    negative_tokens = serialized_token_count(
                        negative,
                        tokenizer=tokenizer,
                        serialization=serialization,
                    )
                    if negative_tokens > maximum_example_tokens:
                        length_rejections[f"{generator}:negative"] += 1
                        continue
                selected = (
                    positive,
                    negative,
                    positive_tokens,
                    negative_tokens,
                )
                break
            if selected is None:
                continue
            break
        if selected is None:
            raise ValueError(
                f"source family cannot satisfy the frozen {generator} quota"
            )
        positive, negative, _, _ = selected
        used_positive_ids.add(positive["example_id"])
        used_negative_ids.add(negative["example_id"])
        examples.extend((positive, negative))
    if len(used_positive_ids) != positive_quota:
        raise ValueError("source family positive quota is incomplete")
    return examples, record_index, {
        "enabled": length_aware,
        "maximum_example_tokens": maximum_example_tokens,
        "rejected_candidate_serializations": sum(length_rejections.values()),
        "rejections_by_generator_and_role": dict(sorted(length_rejections.items())),
        "accepted_examples_truncated": 0,
        "accepted_examples_rewritten": 0,
    }


def _walk_values(value: Any, keys: list[str], strings: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(str(key))
            _walk_values(item, keys, strings)
    elif isinstance(value, list):
        for item in value:
            _walk_values(item, keys, strings)
    elif isinstance(value, str):
        strings.add(value)


def load_tokenizer_for_selection(
    *,
    selection_contract_path: Path,
    tokenizer_lock_path: Path,
    tokenizer_snapshot_path: Path,
    tokenizer_wheel_path: Path,
) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    selection = load_json(selection_contract_path)
    lock = load_json(tokenizer_lock_path)
    if selection.get("status") != "authorized_token_aware_pair_selection_only":
        raise ValueError("token-aware selection authority is absent")
    if selection.get("truncation_allowed") is not False:
        raise ValueError("token-aware selection contract permits truncation")
    identity = selection["tokenizer_identity"]
    for key in ("repository_id", "revision", "snapshot_manifest_sha256"):
        if identity[key] != lock[key]:
            raise ValueError(f"tokenizer selection identity mismatch: {key}")
    engine = lock["engine"]
    if identity["engine_version"] != engine["version"]:
        raise ValueError("tokenizer engine version differs from the selection contract")
    if identity["engine_wheel_sha256"] != engine["wheel_sha256"]:
        raise ValueError("tokenizer wheel differs from the selection contract")
    snapshot = Path(tokenizer_snapshot_path)
    expected_files = sorted(entry["name"] for entry in lock["files"])
    observed_files = sorted(path.name for path in snapshot.iterdir() if path.is_file())
    if observed_files != expected_files:
        raise ValueError("tokenizer snapshot differs from the locked allowlist")
    for entry in lock["files"]:
        path = snapshot / entry["name"]
        if path.stat().st_size != entry["bytes"] or sha256_file(path) != entry["sha256"]:
            raise ValueError(f"tokenizer snapshot file changed: {entry['name']}")
    wheel = Path(tokenizer_wheel_path)
    if (
        not wheel.is_file()
        or wheel.stat().st_size != engine["wheel_bytes"]
        or sha256_file(wheel) != engine["wheel_sha256"]
    ):
        raise ValueError("isolated tokenizer wheel changed")
    try:
        import tokenizers
        from tokenizers import Tokenizer
    except ImportError as error:
        raise RuntimeError(
            "isolated tokenizers engine is unavailable; do not substitute a tokenizer"
        ) from error
    if tokenizers.__version__ != identity["engine_version"]:
        raise ValueError("loaded tokenizer engine version differs from the contract")
    tokenizer = Tokenizer.from_file(str(snapshot / "tokenizer.json"))
    for marker in ("<|im_start|>", "<|im_end|>"):
        if tokenizer.token_to_id(marker) is None:
            raise ValueError(f"Qwen chat marker is absent: {marker}")
        if len(tokenizer.encode(marker, add_special_tokens=False).ids) != 1:
            raise ValueError(f"Qwen chat marker is not one token: {marker}")
    return tokenizer, selection, {
        "selection_contract_id": selection["contract_id"],
        "selection_contract_sha256": sha256_file(selection_contract_path),
        "tokenizer_lock_sha256": sha256_file(tokenizer_lock_path),
        "repository_id": identity["repository_id"],
        "revision": identity["revision"],
        "engine_version": identity["engine_version"],
        "maximum_example_tokens": selection["maximum_example_tokens"],
        "truncation_allowed": False,
    }


def audit_examples(
    examples_by_split: dict[str, list[dict[str, Any]]],
    record_index: dict[str, dict[str, Any]],
    field_maps: dict[str, Any],
    contract: dict[str, Any],
    protected_lock: dict[str, Any],
) -> dict[str, Any]:
    forbidden_keys = {key.casefold() for key in contract["forbidden_supervision_keys"]}
    all_ids: set[str] = set()
    split_reports: dict[str, Any] = {}
    proof_total = 0
    proof_passed = 0
    pointer_passed = 0
    modality_passed = 0
    all_examples = 0
    observed_keys: list[str] = []
    observed_strings: set[str] = set()
    dataset_digest = hashlib.sha256()
    families_by_split: dict[str, set[str]] = {}
    for split in ("train", "training-validation"):
        examples = sorted(examples_by_split[split], key=lambda row: row["example_id"])
        examples_by_split[split] = examples
        support_counts = Counter()
        family_support: dict[str, Counter[str]] = defaultdict(Counter)
        generators = Counter()
        same_packet = 0
        families: set[str] = set()
        for example in examples:
            encoded = canonical_bytes(example)
            dataset_digest.update(encoded)
            dataset_digest.update(b"\n")
            all_examples += 1
            example_id = example.get("example_id")
            if example_id in all_ids:
                raise ValueError("duplicate candidate-pair example ID")
            all_ids.add(example_id)
            if example.get("split_role") != split:
                raise ValueError("candidate-pair split mismatch")
            family = example.get("source_family_id")
            family_map = field_maps.get("families", {}).get(family)
            if not isinstance(family_map, dict) or family_map.get("split_role") != split:
                raise ValueError("candidate-pair family/split mismatch")
            families.add(family)
            decision = example.get("support_decision")
            support_counts[decision] += 1
            family_support[family][decision] += 1
            source_record = example.get("source_record") or {}
            pointer = example.get("pointer") or {}
            if (
                pointer.get("record_sha256") == source_record.get("record_sha256")
                and pointer.get("artifact_id") == source_record.get("artifact_id")
                and pointer.get("record_id") == source_record.get("record_id")
            ):
                pointer_passed += 1
            if example.get("source_modality") == family_map.get("source_modality"):
                modality_passed += 1
            if decision == "supported":
                record = record_index.get(pointer.get("record_sha256"))
                if record is None or not cedge.validate_g0_candidate(
                    record, example.get("candidate") or {}, field_maps
                )["eligible"]:
                    raise ValueError("supported example failed G0 revalidation")
                if example.get("normalized_edge") != example.get("candidate"):
                    raise ValueError("supported normalized edge changed")
            elif decision == "unsupported_by_bound_pointer":
                proof_total += 1
                validation = cedge.validate_negative_example(
                    example, record_index, field_maps
                )
                if not validation["valid"]:
                    raise ValueError(
                        f"negative proof revalidation failed: {validation['reason_codes']}"
                    )
                proof_passed += 1
                generator = example["negative_proof"]["generator"]
                generators[generator] += 1
                if example["negative_proof"].get("same_packet") is True:
                    same_packet += 1
            else:
                raise ValueError("candidate-pair support decision is invalid")
            _walk_values(example, observed_keys, observed_strings)
        supported = support_counts["supported"]
        unsupported = support_counts["unsupported_by_bound_pointer"]
        total = len(examples)
        expected_total = contract["data_gate"][
            "exact_train_candidate_pairs"
            if split == "train"
            else "exact_training_validation_candidate_pairs"
        ]
        if total != expected_total or supported != unsupported:
            raise ValueError("candidate-pair split count or balance mismatch")
        expected_positive = contract["positive_quotas"][split]
        for family, quota in expected_positive.items():
            counts = family_support.get(family, Counter())
            if counts["supported"] != quota or counts["unsupported_by_bound_pointer"] != quota:
                raise ValueError(f"candidate-pair family quota mismatch: {family}")
        expected_generators = Counter()
        for quotas in contract["negative_generator_quotas"][split].values():
            expected_generators.update({key: int(value) for key, value in quotas.items()})
        expected_generators += Counter()
        if generators != +expected_generators:
            raise ValueError("negative-generator quotas changed")
        nonzero_generators = {key: value for key, value in generators.items() if value}
        if len(nonzero_generators) < contract["data_gate"]["minimum_negative_generator_families"]:
            raise ValueError("too few negative-generator families")
        maximum_fraction = max(nonzero_generators.values()) / unsupported
        if maximum_fraction > contract["data_gate"]["maximum_single_negative_generator_fraction"]:
            raise ValueError("one negative generator exceeds the fraction cap")
        same_packet_fraction = same_packet / unsupported
        if same_packet_fraction < contract["data_gate"]["minimum_same_packet_negative_fraction"]:
            raise ValueError("same-packet negative fraction is below the minimum")
        split_reports[split] = {
            "examples": total,
            "supported": supported,
            "unsupported_by_bound_pointer": unsupported,
            "supported_fraction": supported / total,
            "families": {
                family: dict(sorted(counts.items()))
                for family, counts in sorted(family_support.items())
            },
            "negative_generators": dict(sorted(nonzero_generators.items())),
            "maximum_single_negative_generator_fraction": maximum_fraction,
            "same_packet_negative_fraction": same_packet_fraction,
        }
        families_by_split[split] = families
    overlap = sorted(
        families_by_split["train"] & families_by_split["training-validation"]
    )
    if overlap:
        raise ValueError("train and training-validation source families overlap")
    forbidden_observed = sorted(
        {key for key in observed_keys if key.casefold() in forbidden_keys}
    )
    ttp_values = sorted(value for value in observed_strings if TTP_ID_RE.search(value))
    if forbidden_observed or ttp_values:
        raise ValueError("forbidden label/TTP supervision entered candidate pairs")
    scanner = beth_gate.ProtectedScanner(protected_lock)
    for value in sorted(observed_strings):
        scanner.scan(value)
    protected = scanner.report()
    if protected["exact_matches"] or protected["near_matches"]:
        raise ValueError("protected test-family material entered candidate pairs")
    if pointer_passed != all_examples or modality_passed != all_examples:
        raise ValueError("pointer or source-modality audit failed")
    if proof_total == 0 or proof_passed != proof_total:
        raise ValueError("negative proof pass fraction is not 1.0")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "passed_non_token_data_gate_token_gate_pending",
        "splits": split_reports,
        "dataset": {
            "examples": all_examples,
            "supported": sum(row["supported"] for row in split_reports.values()),
            "unsupported_by_bound_pointer": sum(
                row["unsupported_by_bound_pointer"] for row in split_reports.values()
            ),
            "canonical_example_digest": dataset_digest.hexdigest().upper(),
            "duplicate_example_ids": 0,
            "train_validation_family_overlap": overlap,
        },
        "proof_audit": {
            "validated_negatives": proof_total,
            "passed_negatives": proof_passed,
            "pass_fraction": proof_passed / proof_total,
        },
        "pointer_audit": {
            "passed_examples": pointer_passed,
            "pass_fraction": pointer_passed / all_examples,
        },
        "modality_audit": {
            "passed_examples": modality_passed,
            "pass_fraction": modality_passed / all_examples,
        },
        "supervision_audit": {
            "forbidden_keys_observed": forbidden_observed,
            "ttp_identifier_values_observed": [],
            "beth_label_values_read": False,
            "beth_label_values_used": False,
        },
        "protected_scan": protected,
        "non_token_data_gate_passed": True,
        "token_gate_status": contract["data_gate"]["token_gate_status"],
        "formal_data_gate_passed": False,
    }


def write_deterministic_gzip_jsonl(
    path: Path, examples: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite candidate-pair file: {path}")
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"candidate-pair temporary file exists: {temporary}")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with temporary.open("xb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as text:
                    for example in examples:
                        text.write(canonical_bytes(example).decode("utf-8"))
                        text.write("\n")
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "relative_name": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_json_no_overwrite(path: Path, value: Any) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"audit temporary output exists: {temporary}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def construct_dataset(
    *,
    records_root: Path,
    positive_readiness_path: Path,
    beth_source_path: Path,
    beth_acquisition_path: Path,
    beth_audit_path: Path,
    beth_contract_path: Path,
    field_map_path: Path,
    field_map_lock_path: Path,
    protected_lock_path: Path,
    pair_contract_path: Path,
    output_root: Path,
    selection_contract_path: Path | None = None,
    tokenizer_lock_path: Path | None = None,
    tokenizer_snapshot_path: Path | None = None,
    tokenizer_wheel_path: Path | None = None,
) -> dict[str, Any]:
    contract = load_json(pair_contract_path)
    validate_authorized_inputs(
        contract,
        positive_readiness_path=positive_readiness_path,
        beth_acquisition_path=beth_acquisition_path,
        beth_audit_path=beth_audit_path,
        field_map_path=field_map_path,
        protected_lock_path=protected_lock_path,
        selection_contract_path=selection_contract_path,
        tokenizer_lock_path=tokenizer_lock_path,
    )
    if contract.get("formal_candidate_pair_construction_allowed") is not True:
        raise ValueError("candidate-pair construction authority is absent")
    selection = None
    tokenizer = None
    selection_runtime_audit = None
    if "token_aware_selection_contract_sha256" in contract["inputs"]:
        if any(
            path is None
            for path in (
                selection_contract_path,
                tokenizer_lock_path,
                tokenizer_snapshot_path,
                tokenizer_wheel_path,
            )
        ):
            raise ValueError("token-aware selection runtime inputs are incomplete")
        tokenizer, selection, selection_runtime_audit = load_tokenizer_for_selection(
            selection_contract_path=selection_contract_path,
            tokenizer_lock_path=tokenizer_lock_path,
            tokenizer_snapshot_path=tokenizer_snapshot_path,
            tokenizer_wheel_path=tokenizer_wheel_path,
        )
    field_maps = cedge.load_field_maps(field_map_path, field_map_lock_path)
    expected_families = set(contract["positive_quotas"]["train"]) | set(
        contract["positive_quotas"]["training-validation"]
    )
    historical_families = expected_families - {"beth_process_events"}
    records, historical_duplicate_counts = load_historical_records(
        records_root,
        load_json(positive_readiness_path),
        historical_families,
        field_maps,
    )
    beth_rows, beth_pool_audit = load_beth_selection_pool(
        beth_source_path,
        load_json(beth_acquisition_path),
        load_json(beth_audit_path),
        load_json(beth_contract_path),
        field_maps,
        int(contract["beth_normalization"]["selection_pool_max_eligible_rows"]),
    )
    records["beth_process_events"] = beth_rows
    examples_by_split: dict[str, list[dict[str, Any]]] = {
        "train": [],
        "training-validation": [],
    }
    record_index: dict[str, dict[str, Any]] = {}
    selection_reports: dict[str, dict[str, Any]] = {
        "train": {},
        "training-validation": {},
    }
    for split in ("train", "training-validation"):
        for family, quota in sorted(contract["positive_quotas"][split].items()):
            try:
                family_examples, family_index, selection_report = construct_family_pairs(
                    records[family],
                    positive_quota=int(quota),
                    generator_quotas=contract["negative_generator_quotas"][split][
                        family
                    ],
                    field_maps=field_maps,
                    tokenizer=tokenizer,
                    serialization=(selection or {}).get("serialization"),
                    maximum_example_tokens=(selection or {}).get(
                        "maximum_example_tokens"
                    ),
                )
            except ValueError as error:
                raise ValueError(f"{split}/{family}: {error}") from error
            examples_by_split[split].extend(family_examples)
            selection_reports[split][family] = selection_report
            for key, value in family_index.items():
                if key in record_index:
                    raise ValueError("record SHA-256 collides across source families")
                record_index[key] = value
    audit = audit_examples(
        examples_by_split,
        record_index,
        field_maps,
        contract,
        load_json(protected_lock_path),
    )
    output_root = Path(output_root)
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError("candidate-pair output directory is not empty")
    manifests: list[dict[str, Any]] = []
    try:
        manifests.append(
            {
                "split_role": "train",
                **write_deterministic_gzip_jsonl(
                    output_root / "train.jsonl.gz", examples_by_split["train"]
                ),
            }
        )
        manifests.append(
            {
                "split_role": "training-validation",
                **write_deterministic_gzip_jsonl(
                    output_root / "training-validation.jsonl.gz",
                    examples_by_split["training-validation"],
                ),
            }
        )
    except BaseException:
        for path in output_root.glob("*.jsonl.gz") if output_root.exists() else ():
            path.unlink(missing_ok=True)
        raise
    audit.update(
        {
            "created_date": contract["created_date"],
            "contract_id": contract["contract_id"],
            "field_map_version": field_maps["map_version"],
            "pair_file_manifest": manifests,
            "pair_file_manifest_sha256": sha256_bytes(canonical_bytes(manifests)),
            "beth_selection_pool": beth_pool_audit,
            "historical_exact_duplicate_rows_removed": dict(
                sorted(historical_duplicate_counts.items())
            ),
            "execution_claims": {
                "candidate_pairs_constructed": True,
                "pair_files_git_ignored": True,
                "standalone_normalized_records_written": False,
                "tokenizer_used": tokenizer is not None,
                "tokenizer_used_for_length_aware_selection_only": tokenizer is not None,
                "model_downloaded": False,
                "model_used": False,
                "training_run": False,
                "formal_inference_run": False,
                "m3_runtime_integrated": False,
            },
            "length_aware_selection": {
                "enabled": tokenizer is not None,
                "runtime": selection_runtime_audit,
                "families": selection_reports,
                "selection_scope": "same_family_same_negative_generator",
                "cross_family_substitution": False,
                "quota_change": False,
                "accepted_examples_truncated": 0,
                "accepted_examples_rewritten": 0,
            },
        }
    )
    return audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records-root", type=Path, required=True)
    parser.add_argument("--positive-readiness", type=Path, required=True)
    parser.add_argument("--beth-source", type=Path, required=True)
    parser.add_argument("--beth-acquisition", type=Path, required=True)
    parser.add_argument("--beth-audit", type=Path, required=True)
    parser.add_argument("--beth-contract", type=Path, required=True)
    parser.add_argument("--field-maps", type=Path, required=True)
    parser.add_argument("--field-map-lock", type=Path, required=True)
    parser.add_argument("--protected-lock", type=Path, required=True)
    parser.add_argument("--pair-contract", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--selection-contract", type=Path)
    parser.add_argument("--tokenizer-lock", type=Path)
    parser.add_argument("--tokenizer-snapshot", type=Path)
    parser.add_argument("--tokenizer-wheel", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = construct_dataset(
        records_root=args.records_root,
        positive_readiness_path=args.positive_readiness,
        beth_source_path=args.beth_source,
        beth_acquisition_path=args.beth_acquisition,
        beth_audit_path=args.beth_audit,
        beth_contract_path=args.beth_contract,
        field_map_path=args.field_maps,
        field_map_lock_path=args.field_map_lock,
        protected_lock_path=args.protected_lock,
        pair_contract_path=args.pair_contract,
        output_root=args.output_root,
        selection_contract_path=args.selection_contract,
        tokenizer_lock_path=args.tokenizer_lock,
        tokenizer_snapshot_path=args.tokenizer_snapshot,
        tokenizer_wheel_path=args.tokenizer_wheel,
    )
    write_json_no_overwrite(args.audit_output, audit)
    print(
        f"Label-blind pairs {audit['status']}: "
        f"{audit['dataset']['examples']} examples; token Gate pending"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
