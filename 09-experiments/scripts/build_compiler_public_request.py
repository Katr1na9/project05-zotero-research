#!/usr/bin/env python3
"""Build fail-closed public requests for the mainline evidence compiler.

This module is deliberately model- and private-reference-free. It accepts only
explicitly public artifacts and target-node contracts, derives request-scoped
identifiers, and rejects oracle/canonical-answer fields recursively.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "canonical_claim_id",
        "gold_claim_id",
        "gold",
        "private_gold",
        "required_claim_ids",
        "recoverable_claim_ids",
        "hidden_claim_ids",
        "recovered_claim_ids",
        "discriminative_claim_ids",
        "oracle",
        "oracle_path",
        "action_execution_truth",
        "realized_recovery",
        "actual_recovered_claims",
        "expected_gain",
        "expected_claims",
        "support_ceiling",
        "target_granularity",
        "correct_stop",
        "optimal_action",
        "label",
        "labels",
        "score",
        "scorer_output",
    }
)
CANONICAL_CLAIM_ID = re.compile(r"\bC[0-9]{2}(?:-[A-Za-z0-9_-]+)*-EC-[0-9]{3,}\b")
SOURCE_TYPES = frozenset(
    {
        "cti_text",
        "attck_knowledge",
        "local_log",
        "host_forensics",
        "provenance_graph",
        "network_summary",
        "ioc_enrichment",
        "malware_analysis",
        "infrastructure_history",
        "human_review",
        "synthetic",
    }
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_json_text(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def derive_scoped_id(prefix: str, *parts: Any, length: int = 24) -> str:
    material = canonical_json_bytes([str(part) for part in parts])
    digest = hashlib.sha256(material).hexdigest().upper()
    return f"{prefix}-{digest[:length]}"


def recursive_key_hits(value: Any, forbidden: set[str] | frozenset[str]) -> list[str]:
    hits: list[str] = []

    def visit(item: Any, path: str) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                child_path = f"{path}.{key}" if path else str(key)
                if str(key) in forbidden:
                    hits.append(child_path)
                visit(child, child_path)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                visit(child, f"{path}[{index}]")

    visit(value, "")
    return hits


def assert_public_boundary(
    value: Any,
    private_identifiers: list[str] | tuple[str, ...] = (),
) -> None:
    hits = recursive_key_hits(value, FORBIDDEN_PUBLIC_KEYS)
    if hits:
        raise ValueError(f"public request contains forbidden keys: {hits}")
    blob = canonical_json_text(value)
    if CANONICAL_CLAIM_ID.search(blob):
        raise ValueError("public request contains canonical claim identifier")
    collisions = sorted(
        identifier for identifier in set(private_identifiers) if identifier and identifier in blob
    )
    if collisions:
        raise ValueError(f"public request contains private identifiers: {collisions}")


def _clean_scope(scope: dict[str, Any] | None) -> dict[str, str] | None:
    if scope is None:
        return None
    allowed = ("host_id", "tenant_id", "process_id")
    unknown = sorted(set(scope) - set(allowed))
    if unknown:
        raise ValueError(f"scope contains unsupported fields: {unknown}")
    output = {key: str(scope[key]) for key in allowed if scope.get(key) not in (None, "")}
    return output or None


def _clean_time_window(value: dict[str, Any] | None) -> dict[str, str] | None:
    if value is None:
        return None
    unknown = sorted(set(value) - {"start", "end"})
    if unknown:
        raise ValueError(f"time_window contains unsupported fields: {unknown}")
    output = {key: str(value[key]) for key in ("start", "end") if value.get(key)}
    if not output:
        raise ValueError("time_window must contain start or end")
    return output


def build_record(
    record_id: str,
    payload: dict[str, Any],
    *,
    location: str | None = None,
    line_start: int | None = None,
    line_end: int | None = None,
    scope: dict[str, Any] | None = None,
    time_window: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not re.fullmatch(r"REC-[A-F0-9]{16}", record_id):
        raise ValueError("record_id must be request-scoped REC-<16 hex>")
    if not isinstance(payload, dict):
        raise ValueError("record payload must be an object")
    record: dict[str, Any] = {
        "record_id": record_id,
        "record_sha256": sha256_value(payload),
        "payload": copy.deepcopy(payload),
    }
    if location is not None:
        record["location"] = str(location)
    if line_start is not None:
        record["line_start"] = int(line_start)
    if line_end is not None:
        record["line_end"] = int(line_end)
    cleaned_scope = _clean_scope(scope)
    if cleaned_scope:
        record["scope"] = cleaned_scope
    cleaned_time = _clean_time_window(time_window)
    if cleaned_time:
        record["time_window"] = cleaned_time
    assert_public_boundary(record)
    return record


def build_artifact(
    artifact_id: str,
    source_type: str,
    records: list[dict[str, Any]],
    *,
    scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not re.fullmatch(r"ART-[A-F0-9]{16}", artifact_id):
        raise ValueError("artifact_id must be request-scoped ART-<16 hex>")
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"unsupported source_type: {source_type}")
    if not records:
        raise ValueError("artifact requires at least one record")
    record_ids = [row.get("record_id") for row in records]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("artifact record IDs must be unique")
    core: dict[str, Any] = {
        "artifact_id": artifact_id,
        "source_type": source_type,
        "records": copy.deepcopy(records),
    }
    cleaned_scope = _clean_scope(scope)
    if cleaned_scope:
        core["scope"] = cleaned_scope
    artifact = dict(core)
    artifact["artifact_sha256"] = sha256_value(core)
    assert_public_boundary(artifact)
    return artifact


def build_target_node(
    node_id: str,
    description: str,
    *,
    allowed_claim_types: list[str],
    allowed_predicates: list[str],
    source_pointer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not re.fullmatch(r"NODE-[A-F0-9]{16}", node_id):
        raise ValueError("node_id must be request-scoped NODE-<16 hex>")
    if not description.strip():
        raise ValueError("target node description must be non-empty")
    if not allowed_claim_types or not allowed_predicates:
        raise ValueError("target node requires claim-type and predicate allowlists")
    node: dict[str, Any] = {
        "node_id": node_id,
        "description": description,
        "allowed_claim_types": sorted(set(allowed_claim_types)),
        "allowed_predicates": sorted(set(allowed_predicates)),
    }
    if source_pointer is not None:
        node["source_pointer"] = copy.deepcopy(source_pointer)
    assert_public_boundary(node)
    return node


def build_public_request(
    *,
    case_id: str,
    split: str,
    step_index: int,
    visible_artifacts: list[dict[str, Any]],
    target_nodes: list[dict[str, Any]],
    predicate_allowlist: dict[str, list[str]],
) -> dict[str, Any]:
    if not re.match(r"^C[0-9]{2}", case_id):
        raise ValueError("case_id must start with C followed by two digits")
    if split not in {"unit", "development", "test"}:
        raise ValueError("split must be unit, development, or test")
    if int(step_index) < 0:
        raise ValueError("step_index must be nonnegative")
    artifact_ids = [row.get("artifact_id") for row in visible_artifacts]
    node_ids = [row.get("node_id") for row in target_nodes]
    if len(artifact_ids) != len(set(artifact_ids)):
        raise ValueError("visible artifact IDs must be unique")
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("target node IDs must be unique")
    allowlist = {
        str(source): sorted(set(str(item) for item in values))
        for source, values in predicate_allowlist.items()
    }
    if not allowlist or any(not values for values in allowlist.values()):
        raise ValueError("predicate allowlist must contain non-empty entries")
    body = {
        "case_id": case_id,
        "split": split,
        "step_index": int(step_index),
        "visible_artifacts": sorted(
            copy.deepcopy(visible_artifacts), key=lambda row: row["artifact_id"]
        ),
        "target_nodes": sorted(
            copy.deepcopy(target_nodes), key=lambda row: row["node_id"]
        ),
        "predicate_allowlist": allowlist,
    }
    assert_public_boundary(body)
    content_hash = sha256_value(body)
    request = {
        "request_id": f"REQ-{content_hash[:24]}",
        "request_content_sha256": content_hash,
        **body,
    }
    assert_public_boundary(request)
    return request


def validate_public_request_integrity(request: dict[str, Any]) -> list[str]:
    """Return deterministic integrity errors without consulting private state."""

    errors: list[str] = []
    try:
        assert_public_boundary(request)
    except ValueError:
        errors.append("public_boundary_violation")
    required_body = {
        key: request.get(key)
        for key in (
            "case_id",
            "split",
            "step_index",
            "visible_artifacts",
            "target_nodes",
            "predicate_allowlist",
        )
    }
    content_hash = sha256_value(required_body)
    if request.get("request_content_sha256") != content_hash:
        errors.append("request_hash_mismatch")
    if request.get("request_id") != f"REQ-{content_hash[:24]}":
        errors.append("request_id_mismatch")
    seen_artifacts: set[str] = set()
    for artifact in request.get("visible_artifacts", []) or []:
        artifact_id = artifact.get("artifact_id")
        if artifact_id in seen_artifacts:
            errors.append("duplicate_artifact_id")
        seen_artifacts.add(artifact_id)
        core = {key: copy.deepcopy(value) for key, value in artifact.items() if key != "artifact_sha256"}
        if artifact.get("artifact_sha256") != sha256_value(core):
            errors.append("artifact_hash_mismatch")
        seen_records: set[str] = set()
        for record in artifact.get("records", []) or []:
            record_id = record.get("record_id")
            if record_id in seen_records:
                errors.append("duplicate_record_id")
            seen_records.add(record_id)
            if record.get("record_sha256") != sha256_value(record.get("payload")):
                errors.append("record_hash_mismatch")
    return sorted(set(errors))


def ensure_public_path(path: Path, public_root: Path) -> Path:
    resolved = Path(path).resolve()
    root = Path(public_root).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"path is outside the public root: {resolved}") from error
    relative_parts = [part.casefold() for part in resolved.relative_to(root).parts]
    if "private" in relative_parts:
        raise ValueError("path under private directory is not a public input")
    return resolved


def write_json_no_overwrite(path: Path, value: Any) -> None:
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--public-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_path = ensure_public_path(args.public_input, args.public_root)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    request = build_public_request(**source)
    write_json_no_overwrite(args.output, request)
    print(f"Wrote public compiler request {request['request_id']} to {args.output}")


if __name__ == "__main__":
    main()
