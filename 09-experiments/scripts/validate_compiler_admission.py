#!/usr/bin/env python3
"""Mechanically admit source-grounded evidence-compiler candidates.

The validator never reads private references. Admission establishes contract
eligibility, not semantic truth: reference claims and human labels belong only
in a separate scorer.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
CONTRACT_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "contracts"
EVIDENCE_SCHEMA_PATH = EXPERIMENT_ROOT / "data_schema" / "evidence_claim.schema.json"
FORBIDDEN_CONCLUSION_ENTITIES = frozenset({"actor", "campaign"})
NORMALIZATION_METHOD = "frozen_surface_nfkc_casefold_v0.1"


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_sibling(
    "project05_compiler_public_builder_for_admission",
    "build_compiler_public_request.py",
)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validator_for(path: Path) -> Draft202012Validator:
    return Draft202012Validator(
        load_json(path),
        format_checker=FormatChecker(),
    )


CANDIDATE_VALIDATOR = validator_for(CONTRACT_ROOT / "candidate_claim_envelope.schema.json")
REQUEST_VALIDATOR = validator_for(CONTRACT_ROOT / "compiler_public_request.schema.json")
ENTITY_VALIDATOR = validator_for(CONTRACT_ROOT / "entity_binding.schema.json")
LINK_VALIDATOR = validator_for(CONTRACT_ROOT / "claim_node_link.schema.json")
DECISION_VALIDATOR = validator_for(CONTRACT_ROOT / "compiler_decision.schema.json")
EVIDENCE_VALIDATOR = validator_for(EVIDENCE_SCHEMA_PATH)


def normalize_surface(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    return " ".join(text.split())


def scalar_tokens(value: Any) -> list[str]:
    tokens: list[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                tokens.append(normalize_surface(key))
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif item is not None:
            tokens.append(normalize_surface(item))

    visit(value)
    return [token for token in tokens if token]


def surface_is_present(value: str, payload_tokens: Iterable[str]) -> bool:
    needle = normalize_surface(value)
    return bool(needle) and any(
        needle == token or needle in token or token in needle
        for token in payload_tokens
        if token
    )


def parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def time_conflicts(
    claim_window: dict[str, Any] | None,
    record_window: dict[str, Any] | None,
) -> bool:
    if not claim_window or not record_window:
        return False
    try:
        claim_start = parse_datetime(claim_window.get("start", claim_window.get("end")))
        claim_end = parse_datetime(claim_window.get("end", claim_window.get("start")))
        record_start = parse_datetime(record_window.get("start", record_window.get("end")))
        record_end = parse_datetime(record_window.get("end", record_window.get("start")))
    except (TypeError, ValueError):
        return True
    return claim_start < record_start or claim_end > record_end or claim_start > claim_end


def request_indexes(
    request: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]], dict[str, dict[str, Any]]]:
    artifacts: dict[str, dict[str, Any]] = {}
    records: dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]] = {}
    for artifact in request.get("visible_artifacts", []):
        artifact_id = artifact.get("artifact_id")
        if artifact_id in artifacts:
            raise ValueError(f"duplicate visible artifact: {artifact_id}")
        artifacts[artifact_id] = artifact
        for record in artifact.get("records", []):
            key = (artifact_id, record.get("record_id"))
            if key in records:
                raise ValueError(f"duplicate visible record: {key}")
            records[key] = (artifact, record)
    nodes = {row.get("node_id"): row for row in request.get("target_nodes", [])}
    return artifacts, records, nodes


def schema_reason_codes(candidate: Any) -> list[str]:
    errors = sorted(CANDIDATE_VALIDATOR.iter_errors(candidate), key=lambda error: list(error.path))
    return ["schema_invalid"] if errors else []


def candidate_reason_codes(
    candidate: dict[str, Any],
    request: dict[str, Any],
    records: dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]],
    expected_run_id: str,
) -> tuple[list[str], tuple[dict[str, Any], dict[str, Any]] | None]:
    reasons = schema_reason_codes(candidate)
    if reasons:
        return reasons, None
    if candidate["request_id"] != request.get("request_id"):
        reasons.append("request_mismatch")
    if candidate["compiler_run_id"] != expected_run_id:
        reasons.append("compiler_run_mismatch")
    pointer = candidate["source_pointer"]
    record_bundle = records.get((pointer["artifact_id"], pointer["record_id"]))
    if record_bundle is None:
        reasons.append("pointer_missing")
        return sorted(set(reasons)), None
    artifact, record = record_bundle
    claim = candidate["proposed_claim"]
    if claim["source_pointer"] != pointer:
        reasons.append("pointer_mismatch")
    if claim["case_id"] != request.get("case_id"):
        reasons.append("case_mismatch")
    if claim["source_type"] != artifact.get("source_type"):
        reasons.append("source_type_mismatch")
    allowed = request.get("predicate_allowlist", {}).get(claim["source_type"], [])
    if claim["predicate"] not in allowed:
        reasons.append("predicate_not_allowed")
    if {
        claim["subject"].get("entity_type"),
        claim["object"].get("entity_type"),
    } & FORBIDDEN_CONCLUSION_ENTITIES:
        reasons.append("conclusion_entity_forbidden")
    payload_tokens = scalar_tokens(record.get("payload", {}))
    if not surface_is_present(claim["subject"]["value"], payload_tokens) or not surface_is_present(
        claim["object"]["value"], payload_tokens
    ):
        reasons.append("surface_value_missing")
    if any(
        not surface_is_present(quote, payload_tokens)
        for quote in candidate["source_quote_or_fields"]
    ):
        reasons.append("source_quote_missing")
    source_scope = dict(artifact.get("scope") or {})
    source_scope.update(record.get("scope") or {})
    proposed_scope = candidate["entity_scope"]
    if proposed_scope["scope_status"] == "known":
        supplied_fields = [
            key for key in ("host_id", "tenant_id", "process_id") if proposed_scope.get(key)
        ]
        if not supplied_fields:
            reasons.append("entity_scope_ambiguous")
        for field in supplied_fields:
            if field not in source_scope:
                reasons.append("entity_scope_ambiguous")
            elif normalize_surface(proposed_scope[field]) != normalize_surface(source_scope[field]):
                reasons.append("entity_scope_conflict")
    if time_conflicts(claim.get("time_window"), record.get("time_window")):
        reasons.append("time_conflict")
    return sorted(set(reasons)), record_bundle


def admitted_claim_from_candidate(
    candidate: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    proposed = candidate["proposed_claim"]
    claim: dict[str, Any] = {
        "claim_id": BUILDER.derive_scoped_id(
            "ADM", candidate["request_id"], candidate["candidate_id"]
        ),
        "case_id": proposed["case_id"],
        "source_type": proposed["source_type"],
        "claim_type": proposed["claim_type"],
        "subject": copy.deepcopy(proposed["subject"]),
        "predicate": proposed["predicate"],
        "object": copy.deepcopy(proposed["object"]),
        "observable_status": "visible",
        "source_pointer": {
            **copy.deepcopy(candidate["source_pointer"]),
            "hash": record["record_sha256"],
        },
    }
    if proposed.get("time_window"):
        claim["time_window"] = copy.deepcopy(proposed["time_window"])
    EVIDENCE_VALIDATOR.validate(claim)
    return claim


def claim_dedup_key(claim: dict[str, Any]) -> str:
    key = {
        "case_id": claim["case_id"],
        "source_type": claim["source_type"],
        "claim_type": claim["claim_type"],
        "subject": {
            "entity_type": claim["subject"]["entity_type"],
            "value": normalize_surface(claim["subject"]["value"]),
        },
        "predicate": claim["predicate"],
        "object": {
            "entity_type": claim["object"]["entity_type"],
            "value": normalize_surface(claim["object"]["value"]),
        },
        "time_window": claim.get("time_window"),
        "source_pointer": {
            "artifact_id": claim["source_pointer"]["artifact_id"],
            "record_id": claim["source_pointer"].get("record_id"),
        },
    }
    return BUILDER.sha256_value(key)


def build_entity_bindings(
    candidate: dict[str, Any],
    claim: dict[str, Any],
) -> list[dict[str, Any]]:
    output = []
    for role in ("subject", "object"):
        entity = claim[role]
        entity_key = BUILDER.derive_scoped_id(
            "ENT",
            claim["case_id"],
            entity["entity_type"],
            normalize_surface(entity["value"]),
            candidate["entity_scope"],
        )
        binding: dict[str, Any] = {
            "binding_id": BUILDER.derive_scoped_id(
                "BIND", claim["claim_id"], role, entity_key
            ),
            "request_id": candidate["request_id"],
            "entity_key": entity_key,
            "entity_role": role,
            "entity_type": entity["entity_type"],
            "surface_value": entity["value"],
            "normalized_value": entity.get(
                "normalized_value", normalize_surface(entity["value"])
            ),
            "scope": copy.deepcopy(candidate["entity_scope"]),
            "admitted_claim_ids": [claim["claim_id"]],
            "normalization_method": NORMALIZATION_METHOD,
        }
        if claim.get("time_window"):
            binding["time_window"] = copy.deepcopy(claim["time_window"])
        ENTITY_VALIDATOR.validate(binding)
        output.append(binding)
    return output


def build_links(
    candidate: dict[str, Any],
    claim: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    links: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for target_id in candidate["proposed_target_node_ids"]:
        node = nodes.get(target_id)
        reasons: list[str] = []
        if node is None:
            reasons.append("target_node_unknown")
        elif (
            claim["claim_type"] not in node["allowed_claim_types"]
            or claim["predicate"] not in node["allowed_predicates"]
        ):
            reasons.append("target_link_ineligible")
        if reasons:
            rejected.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "target_node_id": target_id,
                    "reason_codes": sorted(set(reasons)),
                }
            )
            continue
        link = {
            "link_id": BUILDER.derive_scoped_id(
                "LINK", claim["claim_id"], target_id, "supports"
            ),
            "request_id": candidate["request_id"],
            "compiler_run_id": candidate["compiler_run_id"],
            "admitted_claim_id": claim["claim_id"],
            "target_node_id": target_id,
            "link_type": "supports",
            "source_pointer": copy.deepcopy(claim["source_pointer"]),
            "mechanical_eligibility": "passed",
            "controller_eligible": True,
        }
        LINK_VALIDATOR.validate(link)
        links.append(link)
    return links, rejected


def empty_decision(
    request_id: str,
    compiler_run_id: str,
    status: str,
    abstention_reasons: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "compiler_run_id": compiler_run_id,
        "status": status,
        "admitted_claims": [],
        "entity_bindings": [],
        "claim_node_links": [],
        "unlinked_claim_ids": [],
        "rejections": [],
        "link_rejections": [],
        "abstention_reasons": sorted(set(abstention_reasons or [])),
        "counts": {
            "input_candidates": 0,
            "admitted_claims": 0,
            "rejected_candidates": 0,
            "admitted_links": 0,
            "rejected_links": 0,
            "duplicates_merged": 0,
        },
    }


def admit_candidates(
    request: dict[str, Any],
    candidate_bundle: dict[str, Any],
) -> dict[str, Any]:
    request_errors = sorted(
        {"request_schema_invalid"}
        if list(REQUEST_VALIDATOR.iter_errors(request))
        else set()
    )
    request_errors.extend(BUILDER.validate_public_request_integrity(request))
    request_errors = sorted(set(request_errors))
    if request_errors:
        raise ValueError(f"public request integrity failed: {request_errors}")
    compiler_run_id = str(candidate_bundle.get("compiler_run_id") or "RUN-" + "0" * 24)
    request_id = str(request.get("request_id") or "")
    candidates = candidate_bundle.get("candidate_claims")
    if not isinstance(candidates, list):
        decision = empty_decision(request_id, compiler_run_id, "invalid")
        decision["abstention_reasons"] = ["candidate_claims_not_array"]
        DECISION_VALIDATOR.validate(decision)
        return decision
    if candidate_bundle.get("request_id") != request_id:
        decision = empty_decision(request_id, compiler_run_id, "invalid")
        decision["abstention_reasons"] = ["request_mismatch"]
        decision["counts"]["input_candidates"] = len(candidates)
        DECISION_VALIDATOR.validate(decision)
        return decision
    if candidate_bundle.get("status") not in {"completed", "abstain"}:
        decision = empty_decision(request_id, compiler_run_id, "invalid")
        decision["abstention_reasons"] = ["candidate_bundle_status_invalid"]
        decision["counts"]["input_candidates"] = len(candidates)
        DECISION_VALIDATOR.validate(decision)
        return decision
    _, records, nodes = request_indexes(request)
    decision = empty_decision(request_id, compiler_run_id, "completed")
    decision["counts"]["input_candidates"] = len(candidates)
    seen_claims: set[str] = set()
    linked_claim_ids: set[str] = set()

    for raw_candidate in candidates:
        candidate_id = (
            raw_candidate.get("candidate_id", "<missing>")
            if isinstance(raw_candidate, dict)
            else "<invalid>"
        )
        if not isinstance(raw_candidate, dict):
            decision["rejections"].append(
                {"candidate_id": candidate_id, "reason_codes": ["schema_invalid"]}
            )
            continue
        reasons, record_bundle = candidate_reason_codes(
            raw_candidate,
            request,
            records,
            compiler_run_id,
        )
        if reasons or record_bundle is None:
            decision["rejections"].append(
                {"candidate_id": candidate_id, "reason_codes": reasons or ["pointer_missing"]}
            )
            continue
        _, record = record_bundle
        try:
            claim = admitted_claim_from_candidate(raw_candidate, record)
        except Exception:
            decision["rejections"].append(
                {"candidate_id": candidate_id, "reason_codes": ["schema_invalid"]}
            )
            continue
        dedup_key = claim_dedup_key(claim)
        if dedup_key in seen_claims:
            decision["counts"]["duplicates_merged"] += 1
            continue
        seen_claims.add(dedup_key)
        decision["admitted_claims"].append(claim)
        decision["entity_bindings"].extend(build_entity_bindings(raw_candidate, claim))
        links, link_rejections = build_links(raw_candidate, claim, nodes)
        decision["claim_node_links"].extend(links)
        decision["link_rejections"].extend(link_rejections)
        if links:
            linked_claim_ids.add(claim["claim_id"])

    decision["unlinked_claim_ids"] = sorted(
        claim["claim_id"]
        for claim in decision["admitted_claims"]
        if claim["claim_id"] not in linked_claim_ids
    )
    decision["rejections"] = sorted(
        decision["rejections"], key=lambda row: row["candidate_id"]
    )
    decision["link_rejections"] = sorted(
        decision["link_rejections"],
        key=lambda row: (row["candidate_id"], row["target_node_id"]),
    )
    decision["counts"].update(
        {
            "admitted_claims": len(decision["admitted_claims"]),
            "rejected_candidates": len(decision["rejections"]),
            "admitted_links": len(decision["claim_node_links"]),
            "rejected_links": len(decision["link_rejections"]),
        }
    )
    if not candidates:
        decision["status"] = "abstain"
        decision["abstention_reasons"] = sorted(
            set(candidate_bundle.get("abstention_reasons") or ["no_supported_observation"])
        )
    elif not decision["admitted_claims"]:
        decision["status"] = "rejected"
    DECISION_VALIDATOR.validate(decision)
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = load_json(args.request)
    candidates = load_json(args.candidates)
    decision = admit_candidates(request, candidates)
    BUILDER.write_json_no_overwrite(args.output, decision)
    print(
        f"Admission {decision['status']}: "
        f"{decision['counts']['admitted_claims']} claims, "
        f"{decision['counts']['admitted_links']} links"
    )


if __name__ == "__main__":
    main()
