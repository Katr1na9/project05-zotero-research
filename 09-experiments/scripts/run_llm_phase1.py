#!/usr/bin/env python3
"""Run dependency-free Rule/stub stages for Project05 LLM Phase 1."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = EXPERIMENT_ROOT / "llm_compiler_v0.2" / "experiment_config.json"
CONTRACT_PATH = (
    EXPERIMENT_ROOT / "governance" / "contracts" / "llm-compiler-contract-v0.2.json"
)
RUNNER_PATH = Path(__file__).resolve()
RULE_IMPLEMENTATION_VERSION = "project05-rule-compiler-v0.2"


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_BUILDER = load_sibling(
    "project05_llm_packet_builder_for_runner",
    "build_llm_evaluation_packets.py",
)
_VALIDATOR = load_sibling(
    "project05_llm_validator_for_runner",
    "validate_llm_phase1_output.py",
)

canonical_json = _BUILDER.canonical_json
derive_candidate_claim_id = _BUILDER.derive_candidate_claim_id
read_jsonl_gz = _BUILDER.read_jsonl_gz
write_json = _BUILDER.write_json
write_jsonl_gz = _BUILDER.write_jsonl_gz


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest().upper()


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def entity_type_for(value: str, hint: str = "") -> str:
    folded_hint = hint.casefold()
    folded = value.casefold()
    if "ip" in folded_hint or resembles_ip(value):
        return "ip"
    if any(token in folded_hint for token in ("file", "path", "key")):
        return "registry_key" if "key" in folded_hint else "file"
    if "host" in folded_hint or "computer" in folded_hint:
        return "host"
    if "user" in folded_hint or "principal" in folded_hint:
        return "user"
    if "command" in folded_hint or folded.startswith(("cmd ", "powershell ")):
        return "command"
    return "process"


def resembles_ip(value: str) -> bool:
    parts = value.split(":", 1)[0].split(".")
    return len(parts) == 4 and all(part.isdigit() for part in parts)


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
    node_type = str(node.get("node_type") or raw.get("type") or role)
    candidates = (
        (node.get("path"), "path"),
        (node.get("cmd"), "command"),
        (node.get("src_addr"), "ip"),
        (node.get("dst_addr"), "ip"),
        (raw.get("cmdLine"), "command"),
        (raw.get("path"), "path"),
        (raw.get("name"), node_type),
        (raw.get("remoteAddress"), "ip"),
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
    if isinstance(resolved, dict):
        return (
            node_entity(resolved.get("subject_uuid"), "process"),
            node_entity(
                resolved.get("predicate_object_uuid")
                or resolved.get("predicate_object_2_uuid"),
                "object",
            ),
        )

    event = payload.get("event") if isinstance(payload.get("event"), dict) else payload
    properties = event.get("properties") if isinstance(event.get("properties"), dict) else {}
    subject_fields = (
        (event.get("process"), "process"),
        (properties.get("image_path"), "process"),
        (properties.get("command_line"), "command"),
        (event.get("Image"), "process"),
        (event.get("ParentProcessName"), "process"),
        (event.get("SubjectUserName"), "user"),
        (event.get("Computer"), "host"),
    )
    object_fields = (
        (event.get("path"), "path"),
        (properties.get("file_path"), "file"),
        (properties.get("path"), "path"),
        (properties.get("key"), "key"),
        (properties.get("dest_ip") or properties.get("dst_ip"), "ip"),
        (event.get("TargetFilename"), "file"),
        (event.get("NewProcessName"), "process"),
        (event.get("ScriptBlockText"), "command"),
    )
    subject = next(
        (
            result
            for value, hint in subject_fields
            if (result := entity(first_string(value), hint))
        ),
        None,
    )
    object_value = next(
        (
            result
            for value, hint in object_fields
            if (result := entity(first_string(value), hint))
        ),
        None,
    )
    if subject and object_value:
        return subject, object_value

    lead = payload.get("lead") if isinstance(payload.get("lead"), dict) else None
    if lead:
        artifact = lead.get("artifact") if isinstance(lead.get("artifact"), dict) else {}
        subject = entity(
            first_string(artifact.get("clientip"), artifact.get("username")),
            "ip" if artifact.get("clientip") else "user",
        )
        object_value = entity(
            first_string(artifact.get("serverip"), artifact.get("senderhost")),
            "ip" if artifact.get("serverip") else "host",
        )
    return subject, object_value


def operation_map(config_path: Path = CONFIG_PATH) -> dict[str, str]:
    config = load_json(config_path)
    return {
        str(key).upper(): str(value)
        for key, value in config["rule_baseline"]["operation_map"].items()
    }


def rule_compile(packet: dict[str, Any]) -> dict[str, Any]:
    mapping = operation_map()
    candidates = []
    for record in packet.get("records", []):
        token = operation_token(record["source_payload"])
        predicate = mapping.get(str(token).upper()) if token else None
        subject, object_value = payload_entities(record["source_payload"])
        if not predicate or not subject or not object_value:
            continue
        output_index = len(candidates)
        candidate = {
            "candidate_claim_id": derive_candidate_claim_id(
                packet["request_id"], "rule_compiler", 0, output_index
            ),
            "source_type": record["source_type"],
            "subject": subject,
            "predicate": predicate,
            "object": object_value,
            "source_pointer": dict(record["source_pointer"]),
        }
        if not _VALIDATOR.validate_candidate(
            candidate,
            packet,
            "rule_compiler",
            0,
            output_index,
        ):
            candidates.append(candidate)
    return {
        "request_id": packet["request_id"],
        "condition_id": "rule_compiler",
        "attempt_index": 0,
        "status": "completed" if candidates else "abstain",
        "candidate_claims": candidates,
        "telemetry": {
            "latency_ms": 0.0,
            "peak_vram_mb": 0,
            "input_tokens": None,
            "output_tokens": None,
            "error_code": None,
        },
    }


RULE_FINGERPRINT_FUNCTIONS = (
    resembles_ip,
    entity_type_for,
    entity,
    node_entity,
    operation_token,
    payload_entities,
    rule_compile,
)


def rule_implementation_sha256(config_path: Path) -> str:
    payload = {
        "version": RULE_IMPLEMENTATION_VERSION,
        "operation_map": operation_map(config_path),
        "functions": [inspect.getsource(function) for function in RULE_FINGERPRINT_FUNCTIONS],
    }
    return sha256_value(payload)


def as_value(value_or_path: Any) -> Any:
    if isinstance(value_or_path, Path):
        return load_json(value_or_path)
    return value_or_path


def freeze_rule_snapshot(
    config_path,
    contract_path,
    development_manifest,
    rule_results,
    output_path,
):
    config_path = Path(config_path)
    contract_path = Path(contract_path)
    output_path = Path(output_path)
    if output_path.exists():
        raise ValueError(f"refusing to overwrite rule baseline snapshot: {output_path}")
    manifest = as_value(development_manifest)
    rows = as_value(rule_results)
    if manifest.get("split") != "development":
        raise ValueError("rule baseline snapshot requires development split")
    audit = manifest.get("null_construction_audit") or {}
    if audit.get("status") != "frozen":
        raise ValueError("development null construction audit is not frozen")
    if len(rows) != int(manifest.get("packet_count") or 0):
        raise ValueError("rule result count does not match development manifest")

    positives = [row for row in rows if row.get("packet_role") == "positive"]
    nulls = [row for row in rows if row.get("packet_role") == "null"]
    claim_counts = [
        len((row.get("result") or {}).get("candidate_claims") or []) for row in rows
    ]
    positive_claiming = sum(
        bool((row.get("result") or {}).get("candidate_claims")) for row in positives
    )
    null_claiming = sum(
        bool((row.get("result") or {}).get("candidate_claims")) for row in nulls
    )
    strength_pass = positive_claiming > 0 and null_claiming < len(nulls)
    distribution = Counter(str(value) for value in claim_counts)
    snapshot = {
        "status": "frozen_before_any_llm_output",
        "split": "development",
        "packet_count": len(rows),
        "positive_count": len(positives),
        "null_count": len(nulls),
        "schema_valid_rate": sum(bool(row.get("schema_valid")) for row in rows)
        / len(rows),
        "claim_count_distribution": dict(sorted(distribution.items())),
        "abstain_rate": sum(
            (row.get("result") or {}).get("status") == "abstain" for row in rows
        )
        / len(rows),
        "project_gold_packet_agreement": sum(
            float(row.get("project_gold_packet_agreement") or 0.0) for row in rows
        )
        / len(rows),
        "baseline_strength_gate": "passed" if strength_pass else "failed",
        "config_sha256": sha256_file(config_path),
        "contract_sha256": sha256_file(contract_path),
        "runner_sha256": rule_implementation_sha256(config_path),
        "development_input_manifest_sha256": manifest[
            "input_manifest_sha256"
        ],
        "rule_results_sha256": sha256_value(rows),
        "null_construction_audit_sha256": audit["audit_sha256"],
    }
    write_json(output_path, snapshot)
    output_path.with_suffix(".sha256").write_text(
        sha256_file(output_path) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if not strength_pass:
        raise ValueError("rule baseline strength gate failed")
    return snapshot


def require_rule_snapshot_unchanged(
    snapshot_path,
    config_path,
    contract_path,
) -> None:
    snapshot_path = Path(snapshot_path)
    config_path = Path(config_path)
    contract_path = Path(contract_path)
    if not snapshot_path.exists():
        raise ValueError("rule baseline snapshot is missing")
    snapshot = load_json(snapshot_path)
    expected = {
        "config_sha256": sha256_file(config_path),
        "contract_sha256": sha256_file(contract_path),
        "runner_sha256": rule_implementation_sha256(config_path),
    }
    mismatches = [
        key for key, value in expected.items() if snapshot.get(key) != value
    ]
    if mismatches:
        raise ValueError(f"rule baseline snapshot hash mismatch: {mismatches}")
    if snapshot.get("status") != "frozen_before_any_llm_output":
        raise ValueError("rule baseline snapshot status is not frozen")


def preflight_llm_backend(snapshot_path, config_path, contract_path) -> None:
    require_rule_snapshot_unchanged(snapshot_path, config_path, contract_path)


def run_condition(
    config,
    packet,
    condition_id,
    backend,
    attempt_index=0,
):
    del config
    if condition_id == "rule_compiler" and backend == "rule":
        result = rule_compile(packet)
        result["attempt_index"] = int(attempt_index)
        return result, {
            "condition_id": condition_id,
            "attempt_index": int(attempt_index),
            "result_sha256": sha256_value(result),
        }
    raise ValueError("model backends remain unauthorized before the Rule snapshot Gate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Project05 LLM Phase 1 conditions.")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--split", choices=("development", "test"))
    parser.add_argument("--condition")
    parser.add_argument("--backend")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--freeze-rule-snapshot", type=Path)
    parser.add_argument("--rule-run", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(
        "Formal Rule execution is blocked until the development null audit is frozen; "
        "use the tested module interfaces after that Gate."
    )
