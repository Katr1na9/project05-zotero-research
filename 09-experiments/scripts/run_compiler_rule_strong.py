#!/usr/bin/env python3
"""Run and freeze the development-only RULE-STRONG compiler baseline.

The runner reads only the WP2 public package.  It uses deterministic source
adapters, a fixed observable-operation vocabulary, and conservative public
target-description linking.  It never reads private references, canonical
claim/node/action IDs, model output, or test-case records during compilation.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
DEFAULT_WP2_ROOT = (
    EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "generated" / "wp2"
)
DEFAULT_OUTPUT = DEFAULT_WP2_ROOT / "rule-strong-development"
RULE_VERSION = "project05-mainline-rule-strong-v0.1"

OPERATION_MAP = {
    "EVENT_ACCEPT": "accepted_external_connection",
    "EVENT_CONNECT": "connected_to",
    "EVENT_CLOSE": "connected_to",
    "EVENT_EXECUTE": "executed",
    "EVENT_OPEN": "opened",
    "EVENT_READ": "read",
    "EVENT_RECVFROM": "received_data_from",
    "EVENT_SENDTO": "sent_data_to",
    "EVENT_WRITE": "wrote",
    "FILE:CREATE": "created",
    "FILE:READ": "read",
    "FILE:WRITE": "wrote",
    "FLOW:MESSAGE": "connected_to",
    "FLOW:START": "connected_to",
    "PROCESS:CREATE": "executed",
    "REGISTRY:ADD": "set_registry_value_for",
    "REGISTRY:MODIFY": "set_registry_value_for",
    "SHELL:COMMAND": "executed_command",
    "THREAD:REMOTE_CREATE": "executed",
    "WINDOWS:11": "created",
    "WINDOWS:4688": "executed",
    "WINDOWS:800": "executed_command",
    "WINDOWS:4104": "executed_command",
    "WITFOO:BLOCK": "attempted_blocked_connection_to",
    "WITFOO:4672": "received_special_privileges_on",
}
PREDICATE_CLAIM_TYPE = {
    "accepted_external_connection": "network_connection",
    "attempted_blocked_connection_to": "network_connection",
    "connected_to": "network_connection",
    "received_data_from": "network_connection",
    "sent_data_to": "network_connection",
    "created": "file_activity",
    "opened": "file_activity",
    "read": "file_activity",
    "wrote": "file_activity",
    "executed": "process_execution",
    "executed_command": "process_execution",
    "set_registry_value_for": "registry_modification",
    "received_special_privileges_on": "credential_activity",
}
PREDICATE_TARGET_HINTS = {
    "accepted_external_connection": {"access", "initial", "perimeter"},
    "attempted_blocked_connection_to": {"c2", "control", "network", "perimeter"},
    "connected_to": {"c2", "command", "control", "lateral", "network"},
    "received_data_from": {"c2", "command", "control", "initial", "payload"},
    "sent_data_to": {"c2", "control", "exfil", "exfiltration", "network"},
    "created": {"collection", "execution", "payload", "post", "privilege"},
    "opened": {"collection", "discovery", "post"},
    "read": {"collection", "discovery"},
    "wrote": {"collection", "execution", "exfiltration", "payload", "post"},
    "executed": {"discovery", "execution", "initial", "payload", "privilege"},
    "executed_command": {"collection", "discovery", "execution", "lateral", "privilege"},
    "set_registry_value_for": {"persistence", "privilege"},
    "received_special_privileges_on": {"credential", "privilege"},
}
GENERIC_BEHAVIOR_WORDS = {
    "access",
    "activity",
    "command",
    "context",
    "control",
    "execution",
    "initial",
    "network",
    "observation",
    "payload",
    "post",
    "privilege",
}


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_sibling(
    "project05_compiler_public_builder_for_rule_strong",
    "build_compiler_public_request.py",
)
ADMISSION = load_sibling(
    "project05_compiler_admission_for_rule_strong",
    "validate_compiler_admission.py",
)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite Rule output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl_gz(path: Path, rows: Iterable[Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite Rule output: {path}")
    payload = b"".join(BUILDER.canonical_json_bytes(row) + b"\n" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(payload, mtime=0))


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = first_string(value.get("string"), value.get("value"))
            if nested:
                return nested
    return None


def process_from_command_line(value: Any) -> str | None:
    command_line = first_string(value)
    if not command_line:
        return None
    text = command_line.strip()
    if text.startswith('"'):
        closing = text.find('"', 1)
        if closing > 1:
            return text[1:closing]
    return text.split(None, 1)[0] if text else None


def resembles_ip(value: str) -> bool:
    candidate = value.strip("[]").split(":", 1)[0]
    parts = candidate.split(".")
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)


def entity_type_for(value: str, hint: str = "") -> str:
    folded_hint = hint.casefold()
    folded = value.casefold()
    if "ip" in folded_hint or "address" in folded_hint or resembles_ip(value):
        return "ip"
    if any(token in folded_hint for token in ("file", "path", "key")):
        return "registry_key" if "key" in folded_hint else "file"
    if "host" in folded_hint or "computer" in folded_hint:
        return "host"
    if "user" in folded_hint or "principal" in folded_hint or "account" in folded_hint:
        return "user"
    if "command" in folded_hint or folded.startswith(("cmd ", "powershell ")):
        return "command"
    return "process"


def entity(value: str | None, hint: str = "") -> dict[str, str] | None:
    if not value:
        return None
    return {"entity_type": entity_type_for(value, hint), "value": value}


def node_entity(node: Any, role: str) -> dict[str, str] | None:
    if not isinstance(node, dict):
        return None
    raw = node.get("raw") if isinstance(node.get("raw"), dict) else {}
    base = raw.get("baseObject") if isinstance(raw.get("baseObject"), dict) else {}
    base_properties = (
        (base.get("properties") or {}).get("map")
        if isinstance(base.get("properties"), dict)
        else {}
    ) or {}
    raw_properties = (
        (raw.get("properties") or {}).get("map")
        if isinstance(raw.get("properties"), dict)
        else {}
    ) or {}
    node_type = str(node.get("node_type") or raw.get("type") or role)
    if role == "process":
        process = process_from_command_line(raw.get("cmdLine"))
        if process:
            return entity(process, "process")
    candidates = (
        (node.get("path"), "path"),
        (node.get("cmd"), "command"),
        (node.get("src_addr"), "ip"),
        (node.get("dst_addr"), "ip"),
        (raw.get("path"), "path"),
        (raw.get("name"), node_type),
        (raw.get("remoteAddress"), "ip"),
        (raw.get("hostId"), "host"),
        (raw_properties.get("exec"), "process"),
        (raw_properties.get("path"), "path"),
        (raw_properties.get("partial_path"), "path"),
        (raw_properties.get("address"), "ip"),
        (base.get("path"), "path"),
        (base.get("filename"), "file"),
        (base_properties.get("path"), "path"),
        (base_properties.get("filename"), "file"),
    )
    for value, hint in candidates:
        result = entity(first_string(value), str(hint))
        if result:
            return result
    return None


def operation_token(payload: dict[str, Any]) -> str | None:
    event = payload.get("event") if isinstance(payload.get("event"), dict) else payload
    if event.get("event_type") or event.get("operation"):
        return str(event.get("event_type") or event.get("operation")).upper()
    if event.get("object") and event.get("action"):
        return f"{event['object']}:{event['action']}".upper()
    if event.get("EventID") is not None:
        return f"WINDOWS:{event['EventID']}".upper()
    lead = payload.get("lead") if isinstance(payload.get("lead"), dict) else None
    if lead:
        artifact = lead.get("artifact") if isinstance(lead.get("artifact"), dict) else {}
        if artifact.get("action") == "block" or lead.get("block"):
            return "WITFOO:BLOCK"
        for field in ("eventcode", "event_id", "EventID"):
            if artifact.get(field) is not None:
                return f"WITFOO:{artifact[field]}".upper()
    return None


def payload_entities(
    payload: dict[str, Any],
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    if isinstance(payload.get("resolved_src_node"), dict):
        return (
            node_entity(payload["resolved_src_node"], "process"),
            node_entity(payload.get("resolved_dst_node"), "object"),
        )
    resolved = payload.get("resolved_nodes")
    subject = None
    object_value = None
    if isinstance(resolved, dict):
        subject = node_entity(resolved.get("subject_uuid"), "process")
        object_value = node_entity(
            resolved.get("predicate_object_uuid")
            or resolved.get("predicate_object_2_uuid"),
            "object",
        )
        if subject and object_value:
            return subject, object_value

    event = payload.get("event") if isinstance(payload.get("event"), dict) else payload
    raw = event.get("raw") if isinstance(event.get("raw"), dict) else {}
    raw_properties = (
        (raw.get("properties") or {}).get("map")
        if isinstance(raw.get("properties"), dict)
        else {}
    ) or {}
    properties = event.get("properties") if isinstance(event.get("properties"), dict) else {}
    subject_fields = (
        (raw_properties.get("exec"), "process"),
        (process_from_command_line(raw_properties.get("cmdLine")), "process"),
        (event.get("process"), "process"),
        (properties.get("image_path"), "process"),
        (properties.get("command_line"), "command"),
        (event.get("Image"), "process"),
        (event.get("ParentProcessName"), "process"),
        (event.get("SubjectUserName"), "user"),
        (event.get("Computer"), "host"),
        (event.get("Hostname"), "host"),
    )
    object_fields = (
        (raw.get("predicateObjectPath"), "path"),
        (raw.get("predicateObject2Path"), "path"),
        (raw_properties.get("partial_path"), "path"),
        (raw_properties.get("path"), "path"),
        (raw_properties.get("address"), "ip"),
        (event.get("path"), "path"),
        (properties.get("file_path"), "file"),
        (properties.get("path"), "path"),
        (properties.get("key"), "key"),
        (properties.get("dest_ip") or properties.get("dst_ip"), "ip"),
        (event.get("TargetFilename"), "file"),
        (event.get("NewProcessName"), "process"),
        (event.get("ScriptBlockText"), "command"),
    )
    subject = subject or next(
        (
            result
            for value, hint in subject_fields
            if (result := entity(first_string(value), hint))
        ),
        None,
    )
    object_value = object_value or next(
        (
            result
            for value, hint in object_fields
            if (result := entity(first_string(value), hint))
        ),
        None,
    )
    return subject, object_value


def pointer_for(artifact: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    pointer: dict[str, Any] = {
        "artifact_id": artifact["artifact_id"],
        "record_id": record["record_id"],
    }
    for field in ("location", "line_start", "line_end"):
        if record.get(field) is not None:
            pointer[field] = record[field]
    return pointer


def scope_for(artifact: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    scope = dict(artifact.get("scope") or {})
    scope.update(record.get("scope") or {})
    if not scope:
        return {"scope_status": "unknown"}
    return {"scope_status": "known", **scope}


def words(value: str) -> set[str]:
    return {part for part in re.findall(r"[a-z0-9]+", value.casefold()) if part}


def target_ids_for(
    request: dict[str, Any],
    predicate: str,
    claim_type: str,
    subject: dict[str, str],
    object_value: dict[str, str],
) -> list[str]:
    eligible = [
        node
        for node in request["target_nodes"]
        if predicate in node["allowed_predicates"]
        and claim_type in node["allowed_claim_types"]
    ]
    if not eligible:
        return []
    entity_words = words(subject["value"] + " " + object_value["value"])
    hint_words = PREDICATE_TARGET_HINTS.get(predicate, set())
    scored: list[tuple[int, str]] = []
    for node in eligible:
        description_words = words(node["description"])
        behavior_words = description_words.difference(GENERIC_BEHAVIOR_WORDS)
        surface_overlap = len(entity_words.intersection(behavior_words))
        semantic_overlap = len(description_words.intersection(hint_words))
        scored.append((surface_overlap * 10 + semantic_overlap, node["node_id"]))
    maximum = max(score for score, _ in scored)
    winners = sorted(node_id for score, node_id in scored if score == maximum)
    if maximum > 0 and len(winners) == 1:
        return winners
    if len(eligible) == 1:
        return [eligible[0]["node_id"]]
    return []


def compile_request(request: dict[str, Any]) -> dict[str, Any]:
    compiler_run_id = BUILDER.derive_scoped_id(
        "RUN", RULE_VERSION, request["request_id"], length=24
    )
    candidates = []
    skipped = []
    for artifact in request["visible_artifacts"]:
        for record in artifact["records"]:
            token = operation_token(record["payload"])
            predicate = OPERATION_MAP.get(str(token).upper()) if token else None
            subject, object_value = payload_entities(record["payload"])
            if not predicate or not subject or not object_value:
                skipped.append(
                    {
                        "artifact_id": artifact["artifact_id"],
                        "record_id": record["record_id"],
                        "reason": (
                            "operation_unmapped"
                            if not predicate
                            else "entity_pair_unresolved"
                        ),
                        "operation_token": token,
                    }
                )
                continue
            claim_type = PREDICATE_CLAIM_TYPE[predicate]
            pointer = pointer_for(artifact, record)
            candidate_id = BUILDER.derive_scoped_id(
                "CAND", RULE_VERSION, request["request_id"], pointer, length=24
            )
            proposed_claim: dict[str, Any] = {
                "case_id": request["case_id"],
                "source_type": artifact["source_type"],
                "claim_type": claim_type,
                "subject": subject,
                "predicate": predicate,
                "object": object_value,
                "observable_status": "visible",
                "source_pointer": copy.deepcopy(pointer),
            }
            if record.get("time_window"):
                proposed_claim["time_window"] = copy.deepcopy(record["time_window"])
            candidates.append(
                {
                    "compiler_run_id": compiler_run_id,
                    "request_id": request["request_id"],
                    "candidate_id": candidate_id,
                    "source_pointer": copy.deepcopy(pointer),
                    "source_quote_or_fields": [subject["value"], object_value["value"]],
                    "entity_scope": scope_for(artifact, record),
                    "proposed_claim": proposed_claim,
                    "proposed_target_node_ids": target_ids_for(
                        request, predicate, claim_type, subject, object_value
                    ),
                }
            )
    return {
        "compiler_run_id": compiler_run_id,
        "request_id": request["request_id"],
        "status": "completed" if candidates else "abstain",
        "candidate_claims": candidates,
        "abstention_reasons": [] if candidates else ["no_rule_supported_observation"],
        "diagnostic_skips": skipped,
    }


def build_development_requests(public_root: Path) -> list[dict[str, Any]]:
    public_root = Path(public_root)
    artifacts = {
        row["artifact_id"]: row
        for row in read_jsonl_gz(public_root / "artifact_records.jsonl.gz")
    }
    target_catalog = load_json(public_root / "target_node_catalog.json")
    visibility = load_json(public_root / "visibility_scenarios.json")
    visible_ids_by_case: dict[str, set[str]] = {}
    for scenario in visibility["scenarios"]:
        visible_ids_by_case.setdefault(scenario["case_id"], set()).update(
            scenario["initial_visible_artifact_ids"]
        )
    requests = []
    for case in target_catalog["cases"]:
        if case["split"] != "development":
            continue
        artifact_ids = sorted(visible_ids_by_case.get(case["case_id"], set()))
        if not artifact_ids:
            raise ValueError(f"development case has no public artifacts: {case['case_id']}")
        requests.append(
            BUILDER.build_public_request(
                case_id=case["case_id"],
                split="development",
                step_index=0,
                visible_artifacts=[artifacts[artifact_id] for artifact_id in artifact_ids],
                target_nodes=case["nodes"],
                predicate_allowlist=case["predicate_allowlist"],
            )
        )
    case_ids = [request["case_id"] for request in requests]
    if case_ids != [
        "C04-compiler-evaluation",
        "C05-compiler-evaluation",
        "C06-compiler-evaluation",
    ]:
        raise ValueError(f"development-only boundary mismatch: {case_ids}")
    return requests


def run(public_root: Path, output_dir: Path) -> dict[str, Any]:
    public_root = Path(public_root)
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing non-empty Rule output directory: {output_dir}")
    requests = build_development_requests(public_root)
    rows = []
    for request in requests:
        raw = compile_request(request)
        admission_input = {key: value for key, value in raw.items() if key != "diagnostic_skips"}
        decision = ADMISSION.admit_candidates(request, admission_input)
        rows.append(
            {
                "case_id": request["case_id"],
                "request_id": request["request_id"],
                "request_content_sha256": request["request_content_sha256"],
                "artifact_count": len(request["visible_artifacts"]),
                "record_count": sum(len(row["records"]) for row in request["visible_artifacts"]),
                "raw_candidates": raw,
                "admission_decision": decision,
            }
        )
    result_core = {
        "rule_version": RULE_VERSION,
        "split": "development",
        "rows": rows,
    }
    snapshot = {
        "snapshot_id": "project05-mainline-rule-strong-development-snapshot-v0.1",
        "status": "frozen_before_any_llm_output",
        "rule_version": RULE_VERSION,
        "split": "development",
        "case_ids": [row["case_id"] for row in rows],
        "case_count": len(rows),
        "request_count": len(rows),
        "artifact_count": sum(row["artifact_count"] for row in rows),
        "record_count": sum(row["record_count"] for row in rows),
        "raw_candidate_count": sum(
            len(row["raw_candidates"]["candidate_claims"]) for row in rows
        ),
        "diagnostic_skip_count": sum(
            len(row["raw_candidates"]["diagnostic_skips"]) for row in rows
        ),
        "admitted_claim_count": sum(
            row["admission_decision"]["counts"]["admitted_claims"] for row in rows
        ),
        "admitted_link_count": sum(
            row["admission_decision"]["counts"]["admitted_links"] for row in rows
        ),
        "rejected_candidate_count": sum(
            row["admission_decision"]["counts"]["rejected_candidates"] for row in rows
        ),
        "rejected_link_count": sum(
            row["admission_decision"]["counts"]["rejected_links"] for row in rows
        ),
        "development_only_boundary": "passed",
        "test_case_ids_processed": [],
        "private_files_read": False,
        "reference_data_used": False,
        "model_runtime_used": False,
        "training_used": False,
        "human_audit_required": False,
        "operation_map": OPERATION_MAP,
        "target_link_policy": "unique_max_public_description_overlap_v0.1_else_unlinked",
        "results_sha256": BUILDER.sha256_value(result_core),
        "input_sha256": {
            "artifact_records.jsonl.gz": BUILDER.sha256_file(
                public_root / "artifact_records.jsonl.gz"
            ),
            "target_node_catalog.json": BUILDER.sha256_file(
                public_root / "target_node_catalog.json"
            ),
            "visibility_scenarios.json": BUILDER.sha256_file(
                public_root / "visibility_scenarios.json"
            ),
        },
        "implementation_sha256": {
            "run_compiler_rule_strong.py": BUILDER.sha256_file(Path(__file__)),
            "build_compiler_public_request.py": BUILDER.sha256_file(
                SCRIPT_DIR / "build_compiler_public_request.py"
            ),
            "validate_compiler_admission.py": BUILDER.sha256_file(
                SCRIPT_DIR / "validate_compiler_admission.py"
            ),
        },
    }
    write_jsonl_gz(output_dir / "public-requests.jsonl.gz", requests)
    write_json(output_dir / "rule-results.json", result_core)
    write_json(output_dir / "rule-strong-development-snapshot.json", snapshot)
    (output_dir / "rule-strong-development-snapshot.sha256").write_text(
        BUILDER.sha256_file(output_dir / "rule-strong-development-snapshot.json") + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wp2-root", type=Path, default=DEFAULT_WP2_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    snapshot = run(args.wp2_root / "public", args.output_dir)
    print(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
