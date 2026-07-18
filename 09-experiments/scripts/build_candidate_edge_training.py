#!/usr/bin/env python3
"""Build and audit pointer-bounded candidate-edge supervision.

The module is deliberately model- and tokenizer-free.  It never interprets a
legacy packet-null row as a candidate-edge negative and does not construct a
formal training set under the current authority.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import re
import shlex
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "project05-candidate-edge-training-v0.1"
POINTER_KEYS = ("artifact_id", "record_id")
REQUIRED_PROVENANCE = (
    "license_id",
    "license_sha256",
    "source_file_sha256",
    "source_url",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def record_sha256(record: dict[str, Any]) -> str:
    return sha256_bytes(canonical_bytes(record))


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_field_maps(path: Path, lock_path: Path) -> dict[str, Any]:
    path = Path(path)
    lock_path = Path(lock_path)
    lock = load_json(lock_path)
    if lock.get("mutable") is not False:
        raise ValueError("field-map lock must be immutable")
    if lock.get("map_path") != path.name:
        raise ValueError("field-map lock path mismatch")
    actual = sha256_bytes(path.read_bytes())
    if actual != lock.get("map_sha256"):
        raise ValueError("field-map hash mismatch")
    maps = load_json(path)
    families = maps.get("families")
    if not isinstance(families, dict) or len(families) != lock.get("source_family_count"):
        raise ValueError("field-map family count mismatch")
    return maps


_AUDIT_EXECVE_RE = re.compile(
    r'^type=EXECVE msg=audit\((?P<timestamp>\d+(?:\.\d+)?):(?P<serial>\d+)\): '
    r'argc=(?P<argc>\d+)(?P<arguments>(?:\s+a\d+=(?:"(?:\\.|[^"\\])*"|\S+))*)$'
)
_AUDIT_ARGUMENT_RE = re.compile(
    r'a(?P<index>\d+)=(?P<value>"(?:\\.|[^"\\])*"|\S+)'
)
_AUDIT_PROCTITLE_RE = re.compile(
    r'^type=PROCTITLE msg=audit\((?P<timestamp>\d+(?:\.\d+)?):(?P<serial>\d+)\): '
    r'proctitle=(?P<hex>[0-9A-Fa-f]+)$'
)
_LOGHUB_OOM_RE = re.compile(
    r'^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+'
    r'(?P<clock>\d{2}:\d{2}:\d{2})\s+(?P<host>[A-Za-z0-9._-]+) '
    r'kernel: Out of Memory: Killed process (?P<pid>[1-9]\d*) '
    r'\((?P<process>[^()\r\n]+)\)\.$'
)


def _record_message(record: dict[str, Any], family: str) -> str | None:
    if record.get("source_family_id") != family:
        return None
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    message = payload.get("message")
    return message if isinstance(message, str) and message else None


def _record_source_pointer(record: dict[str, Any]) -> dict[str, str] | None:
    if any(not record.get(key) for key in POINTER_KEYS):
        return None
    return {key: str(record[key]) for key in POINTER_KEYS}


def _decode_execve_argument(raw: str) -> str | None:
    if raw.startswith('"'):
        try:
            values = shlex.split(raw, posix=True)
        except ValueError:
            return None
        value = values[0] if len(values) == 1 else None
    elif len(raw) % 2 == 0 and re.fullmatch(r"[0-9A-Fa-f]+", raw):
        try:
            value = bytes.fromhex(raw).decode("utf-8", errors="strict")
        except (ValueError, UnicodeDecodeError):
            return None
    else:
        value = raw
    if not value or "\x00" in value or "\r" in value or "\n" in value:
        return None
    return value


def _execution_candidate(
    record: dict[str, Any], arguments: list[str], event_time: str
) -> dict[str, Any] | None:
    pointer = _record_source_pointer(record)
    if pointer is None or not arguments:
        return None
    return {
        "subject_type": "process",
        "subject_value": arguments[0],
        "predicate": "executed",
        "object_type": "command",
        "object_value": " ".join(arguments),
        "event_time": event_time,
        "source_pointer": pointer,
    }


def parse_linux_audit_execve_candidate(
    record: dict[str, Any],
) -> dict[str, Any] | None:
    message = _record_message(record, "ait_cam_lds_manifestations_filtered")
    if message is None:
        return None
    match = _AUDIT_EXECVE_RE.fullmatch(message)
    if match is None:
        return None
    argc = int(match.group("argc"))
    if argc < 1:
        return None
    parsed: dict[int, str] = {}
    for argument in _AUDIT_ARGUMENT_RE.finditer(match.group("arguments")):
        index = int(argument.group("index"))
        if index in parsed:
            return None
        value = _decode_execve_argument(argument.group("value"))
        if value is None:
            return None
        parsed[index] = value
    if sorted(parsed) != list(range(argc)):
        return None
    return _execution_candidate(
        record,
        [parsed[index] for index in range(argc)],
        match.group("timestamp"),
    )


def parse_linux_audit_proctitle_candidate(
    record: dict[str, Any],
) -> dict[str, Any] | None:
    message = _record_message(record, "ait_cam_lds_manifestations_filtered")
    if message is None:
        return None
    match = _AUDIT_PROCTITLE_RE.fullmatch(message)
    if match is None:
        return None
    try:
        raw = bytes.fromhex(match.group("hex"))
    except ValueError:
        return None
    parts = raw.split(b"\x00")
    if parts and parts[-1] == b"":
        parts.pop()
    if not parts or any(not part for part in parts):
        return None
    try:
        arguments = [part.decode("utf-8", errors="strict") for part in parts]
    except UnicodeDecodeError:
        return None
    if any("\r" in value or "\n" in value for value in arguments):
        return None
    return _execution_candidate(record, arguments, match.group("timestamp"))


def parse_loghub_oom_candidate(record: dict[str, Any]) -> dict[str, Any] | None:
    message = _record_message(record, "logpai_loghub_linux")
    if message is None:
        return None
    match = _LOGHUB_OOM_RE.fullmatch(message)
    pointer = _record_source_pointer(record)
    if match is None or pointer is None:
        return None
    return {
        "subject_type": "system",
        "subject_value": f"kernel@{match.group('host')}",
        "predicate": "terminated",
        "object_type": "process",
        "object_value": f"{match.group('process')}#pid={match.group('pid')}",
        "source_pointer": pointer,
    }


_CANDIDATE_PARSERS = {
    "linux_audit_execve_v1": parse_linux_audit_execve_candidate,
    "linux_audit_proctitle_hex_v1": parse_linux_audit_proctitle_candidate,
    "loghub_oom_killed_process_v1": parse_loghub_oom_candidate,
}


def _run_candidate_parser(name: str, record: dict[str, Any]) -> dict[str, Any] | None:
    parser = _CANDIDATE_PARSERS.get(name)
    if parser is None:
        raise ValueError(f"unsupported frozen candidate parser: {name}")
    return parser(record)


def propose_record_candidates(
    record: dict[str, Any], field_maps: dict[str, Any]
) -> list[dict[str, Any]]:
    family_map = field_maps.get("families", {}).get(record.get("source_family_id"))
    if not isinstance(family_map, dict) or family_map.get("g0_status") != "eligible":
        return []
    output: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    for template in family_map.get("templates", []):
        parser_name = template.get("candidate_parser")
        if not parser_name:
            continue
        candidate = _run_candidate_parser(parser_name, record)
        if candidate is None or not _template_matches_shape(template, candidate):
            continue
        encoded = canonical_bytes(candidate)
        if encoded not in seen:
            output.append(candidate)
            seen.add(encoded)
    return output


def _field_value(payload: dict[str, Any], rule: dict[str, Any]) -> str | None:
    fields = rule.get("fields")
    if not isinstance(fields, list) or not fields:
        return None
    values = [payload.get(field) for field in fields]
    if any(value is None or str(value) == "" for value in values):
        return None
    transform = rule.get("transform")
    if transform == "field" and len(values) == 1:
        return str(values[0])
    if transform == "join_host_port" and len(values) == 2:
        return f"{values[0]}:{values[1]}"
    raise ValueError(f"unsupported frozen field transform: {transform}")


def _candidate_pointer(candidate: dict[str, Any]) -> dict[str, Any]:
    pointer = candidate.get("source_pointer")
    return pointer if isinstance(pointer, dict) else {}


def _pointer_matches(record: dict[str, Any], candidate: dict[str, Any]) -> bool:
    pointer = _candidate_pointer(candidate)
    return all(pointer.get(key) == record.get(key) for key in POINTER_KEYS)


def _template_matches_shape(template: dict[str, Any], candidate: dict[str, Any]) -> bool:
    return all(
        candidate.get(key) == template.get(key)
        for key in ("subject_type", "predicate", "object_type")
    )


def validate_g0_candidate(
    record: dict[str, Any],
    candidate: dict[str, Any],
    field_maps: dict[str, Any],
) -> dict[str, Any]:
    reasons: set[str] = set()
    family = record.get("source_family_id")
    family_map = field_maps.get("families", {}).get(family)
    if family_map is None:
        return {"eligible": False, "template_id": None, "reason_codes": ["source_family_unmapped"]}
    if not _pointer_matches(record, candidate):
        reasons.add("pointer_mismatch")
    provenance = record.get("provenance")
    if not isinstance(provenance, dict) or any(
        not provenance.get(key) for key in REQUIRED_PROVENANCE
    ):
        reasons.add("provenance_missing")
    if family_map.get("g0_status") != "eligible":
        reasons.update(family_map.get("ineligible_reason_codes") or ["source_family_g0_ineligible"])
        return {"eligible": False, "template_id": None, "reason_codes": sorted(reasons)}
    payload = record.get("payload")
    if not isinstance(payload, dict):
        reasons.add("payload_missing")
        return {"eligible": False, "template_id": None, "reason_codes": sorted(reasons)}
    shaped = [
        template
        for template in family_map.get("templates", [])
        if _template_matches_shape(template, candidate)
    ]
    if not shaped:
        reasons.add("field_map_template_missing")
        return {"eligible": False, "template_id": None, "reason_codes": sorted(reasons)}

    parser_templates = [
        template for template in shaped if template.get("candidate_parser")
    ]
    if parser_templates:
        matched_template = None
        candidate_bytes = canonical_bytes(candidate)
        for parser_template in parser_templates:
            recomputed = _run_candidate_parser(
                parser_template["candidate_parser"], record
            )
            if recomputed is not None and canonical_bytes(recomputed) == candidate_bytes:
                matched_template = parser_template
                break
        if matched_template is None:
            reasons.add("parser_candidate_mismatch")
        return {
            "eligible": not reasons,
            "template_id": (
                matched_template["template_id"] if not reasons else None
            ),
            "reason_codes": sorted(reasons),
        }

    template = shaped[0]
    subject = _field_value(payload, template["subject_rule"])
    obj = _field_value(payload, template["object_rule"])
    if subject is None:
        reasons.add("explicit_subject_field_missing")
    elif candidate.get("subject_value") != subject:
        reasons.add("subject_field_mismatch")
    if obj is None:
        reasons.add("explicit_object_field_missing")
    elif candidate.get("object_value") != obj:
        reasons.add("object_field_mismatch")
    if "event_time" in candidate:
        time_rule = template.get("time_rule")
        if not time_rule:
            reasons.add("explicit_time_field_missing")
        else:
            event_time = _field_value(payload, time_rule)
            if event_time is None:
                reasons.add("explicit_time_field_missing")
            elif candidate.get("event_time") != event_time:
                reasons.add("time_field_mismatch")
    return {
        "eligible": not reasons,
        "template_id": template["template_id"] if not reasons else None,
        "reason_codes": sorted(reasons),
    }


def _pointer_for(record: dict[str, Any]) -> dict[str, str]:
    return {
        "artifact_id": str(record["artifact_id"]),
        "record_id": str(record["record_id"]),
        "record_sha256": record_sha256(record),
    }


def _packet_key(record: dict[str, Any]) -> str:
    return f"{record['source_family_id']}::{record['document_id']}"


def build_supported_example(
    record: dict[str, Any],
    candidate: dict[str, Any],
    field_maps: dict[str, Any],
) -> dict[str, Any]:
    if record.get("null_eligible_candidate") and not record.get("observation_candidates"):
        raise ValueError("legacy packet null cannot be reinterpreted")
    report = validate_g0_candidate(record, candidate, field_maps)
    if not report["eligible"]:
        raise ValueError(f"candidate is not G0 supported: {report['reason_codes']}")
    family = record["source_family_id"]
    family_map = field_maps["families"][family]
    pointer = _pointer_for(record)
    source_record = {
        "artifact_id": record["artifact_id"],
        "document_id": record["document_id"],
        "record_id": record["record_id"],
        "record_sha256": pointer["record_sha256"],
        "payload": copy.deepcopy(record["payload"]),
        "provenance": copy.deepcopy(record["provenance"]),
    }
    identity = {
        "family": family,
        "pointer": pointer,
        "candidate": candidate,
        "support_decision": "supported",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "example_id": "CEDGE-" + sha256_bytes(canonical_bytes(identity))[:24],
        "split_role": family_map["split_role"],
        "source_family_id": family,
        "source_modality": family_map["source_modality"],
        "packet_key": _packet_key(record),
        "source_record": source_record,
        "candidate": copy.deepcopy(candidate),
        "support_decision": "supported",
        "normalized_edge": copy.deepcopy(candidate),
        "pointer": pointer,
        "reason_code": "field_map_supported",
        "field_map_id": report["template_id"],
        "negative_proof": None,
    }


def _family_map_for_example(
    example: dict[str, Any], field_maps: dict[str, Any]
) -> dict[str, Any]:
    family = example.get("source_family_id")
    family_map = field_maps.get("families", {}).get(family)
    if not isinstance(family_map, dict):
        raise ValueError("source family is not frozen in field maps")
    return family_map


def _template_by_id(family_map: dict[str, Any], template_id: str) -> dict[str, Any]:
    for template in family_map.get("templates", []):
        if template.get("template_id") == template_id:
            return template
    raise ValueError("field-map template is not frozen")


def _eligible_donor_candidates(
    donor: dict[str, Any], field_maps: dict[str, Any]
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    output = []
    for candidate in donor.get("observation_candidates") or []:
        report = validate_g0_candidate(donor, candidate, field_maps)
        if report["eligible"]:
            output.append((candidate, report))
    return output


def _require_same_family_and_packet(
    positive: dict[str, Any], donor: dict[str, Any]
) -> None:
    if positive.get("source_family_id") != donor.get("source_family_id"):
        raise ValueError("negative donor source family mismatch")
    if positive.get("packet_key") != _packet_key(donor):
        raise ValueError("negative donor must be in the same packet")


def _source_record_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": record["artifact_id"],
        "document_id": record["document_id"],
        "record_id": record["record_id"],
        "record_sha256": record_sha256(record),
        "payload": copy.deepcopy(record["payload"]),
        "provenance": copy.deepcopy(record["provenance"]),
    }


def _negative_example(
    positive: dict[str, Any],
    candidate_after: dict[str, Any],
    *,
    generator: str,
    reason_code: str,
    bound_record_sha256: str,
    donor_record_sha256: str | None,
    source_record: dict[str, Any],
    pointer: dict[str, Any],
    same_packet: bool,
) -> dict[str, Any]:
    proof = {
        "proof_version": "pointer-bounded-negative-v1",
        "generator": generator,
        "same_packet": same_packet,
        "positive_record_sha256": positive["pointer"]["record_sha256"],
        "bound_record_sha256": bound_record_sha256,
        "donor_record_sha256": donor_record_sha256,
        "candidate_before": copy.deepcopy(positive["candidate"]),
        "candidate_after": copy.deepcopy(candidate_after),
        "field_map_id": positive["field_map_id"],
        "mechanical_checks": {
            "candidate_not_supported_by_bound_record": True,
            "world_false_claim_made": False,
            "path_or_scenario_supervision_used": False,
            "source_family_matched": True,
        },
    }
    identity = {
        "family": positive["source_family_id"],
        "pointer": pointer,
        "candidate": candidate_after,
        "generator": generator,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "example_id": "CEDGE-" + sha256_bytes(canonical_bytes(identity))[:24],
        "split_role": positive["split_role"],
        "source_family_id": positive["source_family_id"],
        "source_modality": positive["source_modality"],
        "packet_key": positive["packet_key"],
        "source_record": copy.deepcopy(source_record),
        "candidate": copy.deepcopy(candidate_after),
        "support_decision": "unsupported_by_bound_pointer",
        "normalized_edge": None,
        "pointer": copy.deepcopy(pointer),
        "reason_code": reason_code,
        "field_map_id": positive["field_map_id"],
        "negative_proof": proof,
    }


def generate_n1_object_swap(
    positive: dict[str, Any],
    donor: dict[str, Any],
    field_maps: dict[str, Any],
) -> dict[str, Any]:
    _require_same_family_and_packet(positive, donor)
    before = positive["candidate"]
    candidates = [
        candidate
        for candidate, _ in _eligible_donor_candidates(donor, field_maps)
        if candidate.get("object_type") == before.get("object_type")
        and candidate.get("object_value") != before.get("object_value")
    ]
    if not candidates:
        raise ValueError("same-type donor object is unavailable")
    after = copy.deepcopy(before)
    after["object_value"] = candidates[0]["object_value"]
    positive_hash = positive["pointer"]["record_sha256"]
    return _negative_example(
        positive,
        after,
        generator="N1",
        reason_code="same_type_object_swap",
        bound_record_sha256=positive_hash,
        donor_record_sha256=record_sha256(donor),
        source_record=positive["source_record"],
        pointer=positive["pointer"],
        same_packet=True,
    )


def generate_n2_pointer_swap(
    positive: dict[str, Any],
    bound_record: dict[str, Any],
    field_maps: dict[str, Any],
) -> dict[str, Any]:
    _require_same_family_and_packet(positive, bound_record)
    after = copy.deepcopy(positive["candidate"])
    after["source_pointer"] = {
        "artifact_id": bound_record["artifact_id"],
        "record_id": bound_record["record_id"],
    }
    report = validate_g0_candidate(bound_record, after, field_maps)
    if report["eligible"]:
        raise ValueError("pointer swap remains supported by bound record")
    bound_hash = record_sha256(bound_record)
    pointer = _pointer_for(bound_record)
    return _negative_example(
        positive,
        after,
        generator="N2",
        reason_code="pointer_swap",
        bound_record_sha256=bound_hash,
        donor_record_sha256=bound_hash,
        source_record=_source_record_snapshot(bound_record),
        pointer=pointer,
        same_packet=True,
    )


def generate_n3_predicate_incompatibility(
    positive: dict[str, Any],
    replacement_predicate: str,
    field_maps: dict[str, Any],
) -> dict[str, Any]:
    family_map = _family_map_for_example(positive, field_maps)
    template = _template_by_id(family_map, positive["field_map_id"])
    if replacement_predicate not in template.get("incompatible_predicates", []):
        raise ValueError("predicate is not in the frozen incompatible set")
    after = copy.deepcopy(positive["candidate"])
    after["predicate"] = replacement_predicate
    positive_hash = positive["pointer"]["record_sha256"]
    return _negative_example(
        positive,
        after,
        generator="N3",
        reason_code="predicate_field_incompatibility",
        bound_record_sha256=positive_hash,
        donor_record_sha256=None,
        source_record=positive["source_record"],
        pointer=positive["pointer"],
        same_packet=True,
    )


def generate_n4_time_mismatch(
    positive: dict[str, Any],
    donor: dict[str, Any],
    field_maps: dict[str, Any],
) -> dict[str, Any]:
    _require_same_family_and_packet(positive, donor)
    before = positive["candidate"]
    if not before.get("event_time"):
        raise ValueError("positive candidate has no explicit event time")
    candidates = [
        candidate
        for candidate, _ in _eligible_donor_candidates(donor, field_maps)
        if candidate.get("event_time")
        and candidate.get("event_time") != before.get("event_time")
    ]
    if not candidates:
        raise ValueError("distinct explicit donor event time is unavailable")
    after = copy.deepcopy(before)
    after["event_time"] = candidates[0]["event_time"]
    positive_hash = positive["pointer"]["record_sha256"]
    return _negative_example(
        positive,
        after,
        generator="N4",
        reason_code="explicit_timestamp_mismatch",
        bound_record_sha256=positive_hash,
        donor_record_sha256=record_sha256(donor),
        source_record=positive["source_record"],
        pointer=positive["pointer"],
        same_packet=True,
    )


def validate_negative_example(
    example: dict[str, Any],
    record_index: dict[str, dict[str, Any]],
    field_maps: dict[str, Any],
) -> dict[str, Any]:
    reasons: set[str] = set()
    if example.get("support_decision") != "unsupported_by_bound_pointer":
        reasons.add("negative_support_decision_invalid")
    if example.get("normalized_edge") is not None:
        reasons.add("negative_normalized_edge_must_be_null")
    proof = example.get("negative_proof")
    if not isinstance(proof, dict):
        return {"valid": False, "reason_codes": ["negative_proof_missing"]}
    required = {
        "proof_version",
        "generator",
        "same_packet",
        "positive_record_sha256",
        "bound_record_sha256",
        "donor_record_sha256",
        "candidate_before",
        "candidate_after",
        "field_map_id",
        "mechanical_checks",
    }
    if not required <= set(proof):
        return {"valid": False, "reason_codes": ["negative_proof_fields_missing"]}
    checks = proof.get("mechanical_checks")
    if not isinstance(checks, dict):
        return {"valid": False, "reason_codes": ["mechanical_checks_missing"]}
    if checks.get("world_false_claim_made") is not False:
        reasons.add("world_false_claim_forbidden")
    if checks.get("path_or_scenario_supervision_used") is not False:
        reasons.add("path_or_scenario_supervision_forbidden")
    if checks.get("source_family_matched") is not True:
        reasons.add("source_family_proof_failed")
    if checks.get("candidate_not_supported_by_bound_record") is not True:
        reasons.add("unsupported_check_not_asserted")
    positive_record = record_index.get(proof["positive_record_sha256"])
    bound_record = record_index.get(proof["bound_record_sha256"])
    donor_hash = proof.get("donor_record_sha256")
    donor_record = record_index.get(donor_hash) if donor_hash else None
    if positive_record is None:
        reasons.add("positive_record_missing")
    if bound_record is None:
        reasons.add("bound_record_missing")
    if donor_hash and donor_record is None:
        reasons.add("donor_record_missing")
    family = example.get("source_family_id")
    for row in (positive_record, bound_record, donor_record):
        if row is not None and row.get("source_family_id") != family:
            reasons.add("source_family_mismatch")
    if proof.get("candidate_after") != example.get("candidate"):
        reasons.add("candidate_after_mismatch")
    if positive_record is not None:
        before_report = validate_g0_candidate(
            positive_record, proof["candidate_before"], field_maps
        )
        if not before_report["eligible"]:
            reasons.add("positive_candidate_not_g0")
        elif before_report["template_id"] != proof.get("field_map_id"):
            reasons.add("field_map_id_mismatch")
    if bound_record is not None:
        after_report = validate_g0_candidate(
            bound_record, proof["candidate_after"], field_maps
        )
        if after_report["eligible"]:
            reasons.add("candidate_still_supported_by_bound_record")
        pointer = example.get("pointer") or {}
        if pointer.get("record_sha256") != proof["bound_record_sha256"]:
            reasons.add("bound_pointer_hash_mismatch")
    if proof.get("generator") in {"N1", "N2", "N4"}:
        if proof.get("same_packet") is not True:
            reasons.add("same_packet_proof_failed")
        if positive_record is not None and bound_record is not None:
            if _packet_key(positive_record) != _packet_key(bound_record):
                reasons.add("bound_record_cross_packet")
        if positive_record is not None and donor_record is not None:
            if _packet_key(positive_record) != _packet_key(donor_record):
                reasons.add("donor_record_cross_packet")
    return {"valid": not reasons, "reason_codes": sorted(reasons)}


def evaluate_non_token_gate(
    train_counts: dict[str, int],
    validation_counts: dict[str, int],
) -> dict[str, Any]:
    train = {family: int(count) for family, count in train_counts.items() if count > 0}
    validation = {
        family: int(count) for family, count in validation_counts.items() if count > 0
    }
    train_positive = sum(train.values())
    validation_positive = sum(validation.values())
    train_pairs = 2 * train_positive
    validation_pairs = 2 * validation_positive
    reasons: list[str] = []
    if train_pairs < 1200:
        reasons.append("train_candidate_pairs_below_1200")
    if validation_pairs < 300:
        reasons.append("validation_candidate_pairs_below_300")
    if len(train) < 4:
        reasons.append("train_g0_positive_families_below_4")
    if len(validation) < 2:
        reasons.append("validation_g0_positive_families_below_2")
    overlap = sorted(set(train) & set(validation))
    if overlap:
        reasons.append("train_validation_family_overlap")
    return {
        "status": (
            "failed_non_token_data_gate"
            if reasons
            else "passed_non_token_gate_token_gate_pending"
        ),
        "failure_reasons": sorted(reasons),
        "train_g0_positive_count": train_positive,
        "validation_g0_positive_count": validation_positive,
        "train_g0_positive_families": sorted(train),
        "validation_g0_positive_families": sorted(validation),
        "family_overlap": overlap,
        "maximum_balanced_train_pairs": train_pairs,
        "maximum_balanced_validation_pairs": validation_pairs,
        "token_gate_status": "not_measured_not_authorized",
    }


def _iter_jsonl_gzip(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_number}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"non-object JSONL row at {path}:{line_number}")
            yield value


def audit_historical_proposals(
    records_root: Path,
    field_maps: dict[str, Any],
) -> dict[str, Any]:
    records_root = Path(records_root)
    if not records_root.is_dir():
        raise ValueError("historical records root is missing")
    family_reports: dict[str, dict[str, Any]] = {}
    file_manifest: list[dict[str, Any]] = []
    train_counts: dict[str, int] = {}
    validation_counts: dict[str, int] = {}
    seen_families: set[str] = set()
    for split_role in ("train", "training-validation"):
        split_root = records_root / split_role
        if not split_root.is_dir():
            raise ValueError(f"historical split is missing: {split_role}")
        for path in sorted(split_root.glob("*.jsonl.gz")):
            family = path.name[: -len(".jsonl.gz")]
            if family in seen_families:
                raise ValueError(f"source family appears in multiple splits: {family}")
            seen_families.add(family)
            family_map = field_maps.get("families", {}).get(family)
            if not isinstance(family_map, dict):
                raise ValueError(f"historical source family is unmapped: {family}")
            if family_map.get("split_role") != split_role:
                raise ValueError(f"historical source split mismatch: {family}")
            report = {
                "source_family_id": family,
                "split_role": split_role,
                "source_modality": family_map["source_modality"],
                "records": 0,
                "legacy_packet_null_rows": 0,
                "observation_proposals": 0,
                "g0_positive_candidates": 0,
                "g0_ineligibility_reasons": {},
            }
            for record in _iter_jsonl_gzip(path):
                if record.get("source_family_id") != family:
                    raise ValueError(f"record family mismatch in {path}")
                report["records"] += 1
                if record.get("null_eligible_candidate"):
                    report["legacy_packet_null_rows"] += 1
                candidates = record.get("observation_candidates") or []
                if not isinstance(candidates, list):
                    raise ValueError(f"observation_candidates is not an array in {path}")
                report["observation_proposals"] += len(candidates)
                for candidate in candidates:
                    result = validate_g0_candidate(record, candidate, field_maps)
                    if result["eligible"]:
                        report["g0_positive_candidates"] += 1
                    else:
                        for reason in result["reason_codes"]:
                            counts = report["g0_ineligibility_reasons"]
                            counts[reason] = counts.get(reason, 0) + 1
            report["g0_ineligibility_reasons"] = dict(
                sorted(report["g0_ineligibility_reasons"].items())
            )
            family_reports[family] = report
            if report["g0_positive_candidates"]:
                target = train_counts if split_role == "train" else validation_counts
                target[family] = report["g0_positive_candidates"]
            file_manifest.append(
                {
                    "relative_path": path.relative_to(records_root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_bytes(path.read_bytes()),
                }
            )
    missing = sorted(set(field_maps.get("families", {})) - seen_families)
    if missing:
        raise ValueError(f"frozen source families missing from historical root: {missing}")
    gate = evaluate_non_token_gate(train_counts, validation_counts)
    return {
        "readiness_id": "project05-qwen-candidate-edge-readiness-v0.1",
        "version": "0.1.0",
        "created_date": "2026-07-18",
        "status": gate["status"],
        "scope": "read_only_historical_g0_quantity_audit",
        "historical_source_root": records_root.as_posix(),
        "source_file_manifest": file_manifest,
        "source_file_manifest_sha256": sha256_bytes(canonical_bytes(file_manifest)),
        "families": [family_reports[key] for key in sorted(family_reports)],
        "non_token_gate": gate,
        "formal_data_gate_passed": False,
        "formal_data_gate_reason": (
            "non_token_gate_failed"
            if gate["status"] == "failed_non_token_data_gate"
            else "token_gate_not_measured_not_authorized"
        ),
        "legacy_packet_null_credit": 0,
        "execution_claims": {
            "formal_candidate_pairs_constructed": False,
            "corpus_copied_into_mainline": False,
            "tokenizer_used": False,
            "model_used": False,
            "runtime_modified": False,
            "training_run": False,
            "formal_inference_run": False,
        },
        "hard_stops": [
            "do_not_reinterpret_legacy_packet_null",
            "do_not_construct_formal_candidate_pairs",
            "do_not_download_tokenizer_or_model",
            "do_not_install_or_modify_runtime",
            "do_not_train_or_run_formal_inference",
            "do_not_integrate_into_m3_runtime",
        ],
    }


def audit_positive_remap(
    records_root: Path,
    field_maps: dict[str, Any],
    baseline_readiness: dict[str, Any],
) -> dict[str, Any]:
    """Recompute parser-grounded positives without rewriting source records."""

    records_root = Path(records_root)
    if not records_root.is_dir():
        raise ValueError("historical records root is missing")
    if baseline_readiness.get("readiness_id") != (
        "project05-qwen-candidate-edge-readiness-v0.1"
    ):
        raise ValueError("baseline readiness identity mismatch")
    if baseline_readiness.get("formal_data_gate_passed") is not False:
        raise ValueError("baseline readiness must preserve the formal hard stop")

    baseline_families = {
        row["source_family_id"]: row
        for row in baseline_readiness.get("families", [])
        if isinstance(row, dict) and row.get("source_family_id")
    }
    frozen_families = field_maps.get("families", {})
    if set(baseline_families) != set(frozen_families):
        raise ValueError("baseline and v0.2 source-family sets differ")

    family_reports: dict[str, dict[str, Any]] = {}
    for family, baseline in baseline_families.items():
        family_map = frozen_families[family]
        if baseline.get("split_role") != family_map.get("split_role"):
            raise ValueError(f"baseline split mismatch: {family}")
        family_reports[family] = {
            "source_family_id": family,
            "split_role": family_map["split_role"],
            "source_modality": family_map["source_modality"],
            "records_scanned": 0,
            "baseline_g0_positive_candidates": int(
                baseline.get("g0_positive_candidates", 0)
            ),
            "new_parser_g0_positive_candidates": 0,
            "projected_g0_positive_candidates": 0,
            "parser_template_counts": {},
            "legacy_packet_null_rows": int(
                baseline.get("legacy_packet_null_rows", 0)
            ),
            "legacy_packet_null_negative_credit": 0,
        }

    manifest = baseline_readiness.get("source_file_manifest")
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("baseline source manifest is missing")
    seen_families: set[str] = set()
    for entry in manifest:
        relative = entry.get("relative_path")
        if not isinstance(relative, str):
            raise ValueError("baseline source manifest path is invalid")
        path = records_root / Path(relative)
        if not path.is_file():
            raise ValueError(f"historical source file is missing: {relative}")
        if path.stat().st_size != entry.get("bytes"):
            raise ValueError(f"historical source byte count mismatch: {relative}")
        if sha256_bytes(path.read_bytes()) != entry.get("sha256"):
            raise ValueError(f"historical source hash mismatch: {relative}")
        split_role = Path(relative).parts[0]
        family = path.name[: -len(".jsonl.gz")]
        if family in seen_families:
            raise ValueError(f"source family appears more than once: {family}")
        seen_families.add(family)
        report = family_reports.get(family)
        if report is None or report["split_role"] != split_role:
            raise ValueError(f"historical source family/split mismatch: {relative}")
        seen_candidates: set[bytes] = set()
        for record in _iter_jsonl_gzip(path):
            if record.get("source_family_id") != family:
                raise ValueError(f"record family mismatch in {relative}")
            report["records_scanned"] += 1
            for candidate in propose_record_candidates(record, field_maps):
                validation = validate_g0_candidate(record, candidate, field_maps)
                if not validation["eligible"]:
                    raise ValueError(
                        f"parser proposed a non-G0 candidate in {relative}: "
                        f"{validation['reason_codes']}"
                    )
                identity = canonical_bytes(
                    {
                        "source_family_id": family,
                        "source_pointer": candidate["source_pointer"],
                        "candidate": candidate,
                    }
                )
                if identity in seen_candidates:
                    raise ValueError(f"duplicate parser candidate in {relative}")
                seen_candidates.add(identity)
                report["new_parser_g0_positive_candidates"] += 1
                template_id = validation["template_id"]
                counts = report["parser_template_counts"]
                counts[template_id] = counts.get(template_id, 0) + 1
        report["parser_template_counts"] = dict(
            sorted(report["parser_template_counts"].items())
        )

    if seen_families != set(family_reports):
        missing = sorted(set(family_reports) - seen_families)
        raise ValueError(f"historical source families are missing: {missing}")

    train_counts: dict[str, int] = {}
    validation_counts: dict[str, int] = {}
    for family, report in family_reports.items():
        projected = (
            report["baseline_g0_positive_candidates"]
            + report["new_parser_g0_positive_candidates"]
        )
        report["projected_g0_positive_candidates"] = projected
        if projected:
            target = (
                train_counts
                if report["split_role"] == "train"
                else validation_counts
            )
            target[family] = projected
    gate = evaluate_non_token_gate(train_counts, validation_counts)
    return {
        "readiness_id": "project05-qwen-positive-remap-readiness-v0.1",
        "version": "0.1.0",
        "created_date": "2026-07-18",
        "status": gate["status"],
        "scope": "read_only_record_local_positive_remap_audit",
        "historical_source_root": records_root.as_posix(),
        "baseline_readiness_id": baseline_readiness["readiness_id"],
        "baseline_readiness_canonical_sha256": sha256_bytes(
            canonical_bytes(baseline_readiness)
        ),
        "field_map_version": field_maps.get("map_version"),
        "source_file_manifest": copy.deepcopy(manifest),
        "families": [family_reports[key] for key in sorted(family_reports)],
        "non_token_gate": gate,
        "formal_data_gate_passed": False,
        "formal_data_gate_reason": "non_token_gate_failed",
        "legacy_packet_null_negative_credit": 0,
        "remaining_source_gap": {
            "train_g0_positive_families_required": 4,
            "train_g0_positive_families_observed": len(
                gate["train_g0_positive_families"]
            ),
            "missing_train_families": max(
                0, 4 - len(gate["train_g0_positive_families"])
            ),
            "beth_status": "metadata_candidate_not_download_authorized",
        },
        "execution_claims": {
            "source_records_rewritten": False,
            "formal_candidate_pairs_constructed": False,
            "corpus_copied_into_mainline": False,
            "tokenizer_used": False,
            "model_used": False,
            "runtime_modified": False,
            "training_run": False,
            "formal_inference_run": False,
            "m3_runtime_integrated": False,
        },
        "hard_stops": [
            "beth_download_requires_separate_user_authorization",
            "do_not_construct_formal_candidate_pairs",
            "do_not_download_tokenizer_or_model",
            "do_not_install_or_modify_runtime",
            "do_not_train_or_run_formal_inference",
            "do_not_integrate_into_m3_runtime",
        ],
    }


def write_json_no_overwrite(path: Path, value: Any) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"temporary output already exists: {temporary}")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="run a read-only historical G0 audit")
    audit.add_argument("--records-root", type=Path, required=True)
    audit.add_argument("--field-maps", type=Path, required=True)
    audit.add_argument("--field-map-lock", type=Path, required=True)
    audit.add_argument("--output", type=Path, required=True)
    remap = subparsers.add_parser(
        "positive-remap-audit",
        help="run the authorized read-only record-parser remap audit",
    )
    remap.add_argument("--records-root", type=Path, required=True)
    remap.add_argument("--field-maps", type=Path, required=True)
    remap.add_argument("--field-map-lock", type=Path, required=True)
    remap.add_argument("--baseline-readiness", type=Path, required=True)
    remap.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    field_maps = load_field_maps(args.field_maps, args.field_map_lock)
    if args.command == "audit":
        report = audit_historical_proposals(args.records_root, field_maps)
    elif args.command == "positive-remap-audit":
        report = audit_positive_remap(
            args.records_root,
            field_maps,
            load_json(args.baseline_readiness),
        )
    else:
        raise ValueError("unsupported command")
    write_json_no_overwrite(args.output, report)
    print(
        f"Candidate-edge audit {report['status']}: "
        f"{report['non_token_gate']['train_g0_positive_count']} train G0, "
        f"{report['non_token_gate']['validation_g0_positive_count']} validation G0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
