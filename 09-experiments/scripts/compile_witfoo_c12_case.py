#!/usr/bin/env python3
"""Compile the frozen WitFoo C12 operational stress case from raw leads."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "09-experiments" / "real_data" / "witfoo_precinct6"
DEFAULT_LOCK = DATA_ROOT / "c12_case_compile_lock_v0.1.json"
DEFAULT_INTAKE_LOCK = DATA_ROOT / "c12_intake_lock_v0.1.json"
DEFAULT_CANDIDATES = (
    ROOT
    / "09-experiments"
    / "results"
    / "c12_witfoo_screen_v0.1"
    / "candidate_index.json"
)
DEFAULT_EVENT_AUDIT = (
    ROOT
    / "09-experiments"
    / "results"
    / "c12_witfoo_event_audit_v0.1"
    / "audit.json"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def iso_time(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def lead_by_id(record: dict[str, Any], lead_id: str) -> dict[str, Any]:
    lead = (record.get("leads") or {}).get(lead_id)
    if lead is None:
        raise ValueError(f"Frozen C12 lead is missing: {lead_id}")
    return lead


def source_pointer(
    artifact_id: str,
    location: str,
    record_id: str,
    content_hash: str,
) -> dict[str, str]:
    return {
        "artifact_id": artifact_id,
        "location": location,
        "record_id": record_id,
        "hash": content_hash,
    }


def detail_hash(lead: dict[str, Any]) -> str:
    details = str(lead.get("details") or "").encode("utf-8")
    return hashlib.sha256(details).hexdigest().upper()


def compile_case(
    lock: dict[str, Any],
    incident: dict[str, Any],
    graph_hash: str,
) -> dict[str, Any]:
    case_id = lock["case_id"]
    incident_id = lock["selected_incident_id"]
    if incident.get("id") != incident_id:
        raise ValueError(f"Expected incident {incident_id}, got {incident.get('id')}")

    selection = lock["claim_selection"]
    network_leads = [
        lead
        for lead in (incident.get("leads") or {}).values()
        if (lead.get("product") or {}).get("name")
        == selection["network_aggregate"]["product_name"]
    ]
    expected_network_count = int(
        selection["network_aggregate"]["expected_lead_count"]
    )
    if len(network_leads) != expected_network_count:
        raise ValueError(
            f"Expected {expected_network_count} ASA leads, got {len(network_leads)}"
        )
    representative = lead_by_id(
        incident, selection["network_aggregate"]["representative_lead_id"]
    )
    port_445 = lead_by_id(incident, selection["network_port_445_lead_id"])
    identity = [lead_by_id(incident, value) for value in selection["identity_lead_ids"]]

    network_artifacts = [lead.get("artifact") or {} for lead in network_leads]
    network_start = min(int(lead["observed_at"]) for lead in network_leads)
    network_end = max(int(lead["observed_at"]) for lead in network_leads)
    source_ips = {str(item.get("clientip")) for item in network_artifacts}
    target_ips = {str(item.get("serverip")) for item in network_artifacts}
    target_ports = {str(item.get("serverport")) for item in network_artifacts}
    protocols = Counter(str(item.get("protocol")) for item in network_artifacts)
    source_record = lock["source_record_index_1based"]
    incident_artifact = f"witfoo_incident_leads_{incident_id}"
    graph_artifact = f"witfoo_incident_graphml_{incident_id}"
    incident_hash = lock["input_integrity"]["incident_line_sha256"]

    claims = [
        {
            "claim_id": "C12-EC-001",
            "case_id": case_id,
            "source_type": "network_summary",
            "claim_type": "network_connection",
            "subject": {
                "entity_type": "ip",
                "value": f"{len(source_ips)} sanitized source IPs",
            },
            "predicate": "generated_blocked_connection_attempts_to",
            "object": {
                "entity_type": "ip",
                "value": f"{len(target_ips)} sanitized destination IPs across {len(target_ports)} ports",
            },
            "time_window": {"start": iso_time(network_start), "end": iso_time(network_end)},
            "mapped_tactic": [],
            "mapped_technique": [],
            "evidence_strength": "strong",
            "confidence": 0.99,
            "observable_status": "visible",
            "source_pointer": source_pointer(
                incident_artifact,
                f"graph/incidents.jsonl record {source_record}; ASA Firewall leads (n={len(network_leads)})",
                f"aggregate:ASA Firewall:{len(network_leads)}",
                incident_hash,
            ),
            "supports_hypotheses": ["C12_multichannel_security_incident"],
            "tags": [
                "hideable",
                "real_witfoo",
                "production_soc",
                "analyst_disrupted",
                "provider:asa_firewall",
                "stage:network_observation",
                "node:N01_perimeter_activity",
                "node:N03_cross_channel_context",
                "critical",
                "discriminative",
                "aggregate",
            ],
            "notes": (
                f"Observed aggregate only: {len(network_leads)} blocked leads from "
                f"{len(source_ips)} structured source IPs to {len(target_ips)} structured "
                f"destination IPs over {len(target_ports)} ports; protocol counts={dict(protocols)}. "
                "This does not establish one actor or malicious intent."
            ),
        },
        {
            "claim_id": "C12-EC-002",
            "case_id": case_id,
            "source_type": "local_log",
            "claim_type": "network_connection",
            "subject": {
                "entity_type": "ip",
                "value": str((port_445.get("artifact") or {}).get("clientip")),
            },
            "predicate": "attempted_blocked_tcp_connection_to_port_445_on",
            "object": {
                "entity_type": "ip",
                "value": str((port_445.get("artifact") or {}).get("serverip")),
            },
            "time_window": {
                "start": iso_time(int(port_445["observed_at"])),
                "end": iso_time(int(port_445["observed_at"])),
            },
            "mapped_tactic": [],
            "mapped_technique": [],
            "evidence_strength": "supporting",
            "confidence": 0.99,
            "observable_status": "visible",
            "source_pointer": source_pointer(
                incident_artifact,
                f"graph/incidents.jsonl record {source_record}; leads.{port_445['id']}",
                str(port_445["id"]),
                detail_hash(port_445),
            ),
            "supports_hypotheses": ["C12_multichannel_security_incident"],
            "tags": [
                "hideable",
                "real_witfoo",
                "production_soc",
                "provider:asa_firewall",
                "stage:network_observation",
                "node:N01_perimeter_activity",
                "critical",
                "discriminative",
                "representative",
            ],
            "notes": (
                "Structured ASA fields record a blocked TCP connection to destination port 445. "
                "Sanitized structured fields and embedded message entities are intentionally not joined."
            ),
        },
    ]

    for number, lead in enumerate(identity, start=3):
        artifact = lead.get("artifact") or {}
        claims.append(
            {
                "claim_id": f"C12-EC-{number:03d}",
                "case_id": case_id,
                "source_type": "local_log",
                "claim_type": "credential_activity",
                "subject": {
                    "entity_type": "user",
                    "value": str(artifact.get("username") or "unknown"),
                },
                "predicate": "received_windows_event_4672_special_privileges_on",
                "object": {
                    "entity_type": "host",
                    "value": str(artifact.get("senderhost") or lead.get("node_id")),
                },
                "time_window": {
                    "start": iso_time(int(lead["observed_at"])),
                    "end": iso_time(int(lead["observed_at"])),
                },
                "mapped_tactic": [],
                "mapped_technique": [],
                "evidence_strength": "strong",
                "confidence": 0.99,
                "observable_status": "visible",
                "source_pointer": source_pointer(
                    incident_artifact,
                    f"graph/incidents.jsonl record {source_record}; leads.{lead['id']}",
                    str(lead["id"]),
                    detail_hash(lead),
                ),
                "supports_hypotheses": ["C12_multichannel_security_incident"],
                "tags": [
                    "hideable",
                    "real_witfoo",
                    "production_soc",
                    "provider:windows_ad",
                    "stage:credential_observation",
                    "node:N02_privileged_identity_activity",
                    "critical",
                    "discriminative",
                    "unique",
                ],
                "notes": (
                    "Windows Security Event 4672 records special privileges for SYSTEM. "
                    "The event is an observation, not proof of adversarial privilege escalation."
                ),
            }
        )

    claims.append(
        {
            "claim_id": "C12-EC-005",
            "case_id": case_id,
            "source_type": "provenance_graph",
            "claim_type": "other",
            "subject": {"entity_type": "report", "value": incident_id},
            "predicate": "vendor_correlated_as_single_incident_across",
            "object": {
                "entity_type": "report",
                "value": "ASA Firewall and Windows Active Directory",
            },
            "time_window": {"start": iso_time(network_start), "end": iso_time(network_end)},
            "mapped_tactic": [],
            "mapped_technique": [],
            "evidence_strength": "context",
            "confidence": 0.8,
            "observable_status": "visible",
            "source_pointer": source_pointer(
                graph_artifact,
                f"graph/incidents_graphml/f/{incident_id}.graphml",
                incident_id,
                graph_hash,
            ),
            "supports_hypotheses": ["C12_multichannel_security_incident"],
            "tags": [
                "hideable",
                "real_witfoo",
                "production_soc",
                "provider:precinct_projection",
                "stage:cross_channel_correlation",
                "node:N03_cross_channel_context",
                "context_only",
                "vendor_oracle",
            ],
            "notes": (
                "All 49 GraphML edges are INCIDENT_LINK projections. This claim records "
                "vendor correlation context and is not independent provenance or ground truth."
            ),
        }
    )

    config = {
        "case_id": case_id,
        "source_case_id": incident_id,
        "case_name": "WitFoo Precinct 6 production-SOC multichannel incident f10c7270",
        "description": (
            "Natural operational external stress case compiled from analyst-disrupted "
            "WitFoo incident leads. Raw ASA and Windows audit streams are recoverable; "
            "actor and campaign attribution remain unsupported."
        ),
        "development_only": False,
        "holdout_role": "natural_operational_production_soc_parameter_locked_stress_case",
        "node_coverage_semantics": "AND",
        "target_granularity": "G1_technique",
        "support_ceiling": "G1_technique",
        "budget_total": 8,
        "mask_intensities": [0.2, 0.4, 0.6],
        "mask_strategies": ["random", "stage", "discriminative"],
        "random_seeds": [11, 23, 37, 41, 53],
        "fixed_action_order": ["C12-AA-001", "C12-AA-002", "C12-AA-003", "C12-AA-004"],
        "stage_mask_tags": [
            "stage:network_observation",
            "stage:credential_observation",
            "stage:cross_channel_correlation",
            "stage:actor_attribution",
        ],
        "discriminative_claim_ids": [
            "C12-EC-001",
            "C12-EC-002",
            "C12-EC-003",
            "C12-EC-004",
        ],
        "channel_reliability": {
            "asa_summary": 1.0,
            "asa_targeted_probe": 1.0,
            "windows_security_audit": 1.0,
            "precinct_projection_review": 1.0,
        },
        "cti_nodes": [
            {
                "node_id": "N01_perimeter_activity",
                "stage": "network_observation",
                "required_claim_ids": ["C12-EC-001", "C12-EC-002"],
                "critical": True,
            },
            {
                "node_id": "N02_privileged_identity_activity",
                "stage": "credential_observation",
                "required_claim_ids": ["C12-EC-003", "C12-EC-004"],
                "critical": True,
            },
            {
                "node_id": "N03_cross_channel_context",
                "stage": "cross_channel_correlation",
                "required_claim_ids": ["C12-EC-001", "C12-EC-003", "C12-EC-005"],
                "critical": True,
            },
            {
                "node_id": "N04_actor_campaign_attribution",
                "stage": "actor_attribution",
                "required_claim_ids": [],
                "critical": True,
                "natural_gap": "No actor label or independent campaign ground truth is present.",
            },
        ],
        "cti_edges": [
            {"edge_id": "E01", "source": "N01_perimeter_activity", "target": "N03_cross_channel_context"},
            {"edge_id": "E02", "source": "N02_privileged_identity_activity", "target": "N03_cross_channel_context"},
            {"edge_id": "E03", "source": "N03_cross_channel_context", "target": "N04_actor_campaign_attribution"},
        ],
        "natural_incompleteness": {
            "unsupported_nodes": ["N04_actor_campaign_attribution"],
            "actor_label_limit": "actors is empty and no independent actor-attribution truth exists.",
            "timestamp_limit": "Vendor observed_at and embedded source clocks are inconsistent; no causal event ordering is claimed.",
            "entity_link_limit": "Structured and embedded-message pseudonyms are not joined across sanitization layers.",
            "graph_limit": "GraphML contains only vendor INCIDENT_LINK projections.",
            "policy": "Retain the natural gap and cap the case at G1.",
        },
        "granularity_order": [
            "G0_unknown",
            "G1_technique",
            "G2_tactic_intent",
            "G3_campaign",
            "G4_actor_cluster",
            "G5_named_actor",
        ],
    }

    actions = [
        {
            "action_id": "C12-AA-001",
            "case_id": case_id,
            "action_type": "recover_network_summary",
            "acquisition_channel": "asa_summary",
            "target": {"target_type": "time_window", "target_value": "ASA blocked-connection summary for the frozen incident window"},
            "cost": 2,
            "recoverable_claim_ids": ["C12-EC-001"],
            "intended_cti_node_ids": ["N01_perimeter_activity", "N03_cross_channel_context", "N04_actor_campaign_attribution"],
            "expected_evidence_types": ["network_summary"],
            "expected_stages": ["network_observation", "cross_channel_correlation", "actor_attribution"],
            "expected_effects": {"expected_granularity_gain": 1, "expected_uncertainty_reduction": 0.3, "expected_over_attribution_risk_reduction": 0.25, "expected_conflict_resolution": 0.05, "expected_coverage_delta": 0.2},
            "status": "available",
            "natural_language_request": "Summarize blocked ASA connections across the frozen incident window without reading vendor attribution labels.",
            "notes": "Public intent over-declares cross-channel and actor value; actual recovery is the perimeter aggregate only.",
        },
        {
            "action_id": "C12-AA-002",
            "case_id": case_id,
            "action_type": "ttp_local_probe",
            "acquisition_channel": "asa_targeted_probe",
            "target": {"target_type": "technique", "target_value": "targeted service-access observation around destination port 445"},
            "cost": 1,
            "recoverable_claim_ids": ["C12-EC-002"],
            "intended_cti_node_ids": ["N01_perimeter_activity", "N03_cross_channel_context"],
            "expected_evidence_types": ["local_log"],
            "expected_stages": ["network_observation", "cross_channel_correlation"],
            "expected_effects": {"expected_granularity_gain": 1, "expected_uncertainty_reduction": 0.16, "expected_over_attribution_risk_reduction": 0.14, "expected_conflict_resolution": 0.02, "expected_coverage_delta": 0.12},
            "status": "available",
            "natural_language_request": "Recover a representative ASA record for the blocked destination-port-445 observation.",
            "notes": "The action recovers an observation, not a validated ATT&CK technique label.",
        },
        {
            "action_id": "C12-AA-003",
            "case_id": case_id,
            "action_type": "query_host_subgraph",
            "acquisition_channel": "windows_security_audit",
            "target": {"target_type": "host", "target_value": "Windows Security 4672 observations in the frozen incident"},
            "cost": 3,
            "recoverable_claim_ids": ["C12-EC-003", "C12-EC-004"],
            "intended_cti_node_ids": ["N02_privileged_identity_activity", "N03_cross_channel_context", "N04_actor_campaign_attribution"],
            "expected_evidence_types": ["local_log"],
            "expected_stages": ["credential_observation", "cross_channel_correlation", "actor_attribution"],
            "expected_effects": {"expected_granularity_gain": 1, "expected_uncertainty_reduction": 0.34, "expected_over_attribution_risk_reduction": 0.32, "expected_conflict_resolution": 0.08, "expected_coverage_delta": 0.3},
            "status": "available",
            "natural_language_request": "Recover Windows Security Event 4672 records linked to the frozen incident.",
            "notes": "Actual recovery supports privileged identity observations only; it cannot identify an actor.",
        },
        {
            "action_id": "C12-AA-004",
            "case_id": case_id,
            "action_type": "human_review",
            "acquisition_channel": "precinct_projection_review",
            "target": {"target_type": "case", "target_value": incident_id},
            "cost": 2,
            "recoverable_claim_ids": ["C12-EC-005"],
            "intended_cti_node_ids": ["N03_cross_channel_context", "N04_actor_campaign_attribution"],
            "expected_evidence_types": ["human_review"],
            "expected_stages": ["cross_channel_correlation", "actor_attribution"],
            "expected_effects": {"expected_granularity_gain": 0, "expected_uncertainty_reduction": 0.1, "expected_over_attribution_risk_reduction": 0.18, "expected_conflict_resolution": 0.12, "expected_coverage_delta": 0.1},
            "status": "available",
            "natural_language_request": "Review the vendor incident projection and record its provenance boundary.",
            "notes": "The recovered claim is vendor correlation context, not independent analyst or actor truth.",
        },
    ]

    motifs = [
        {"motif_id": "C12-M01", "claim_id": "C12-EC-001", "node_id": "N01_perimeter_activity", "record_index_1based": source_record, "record_id": "aggregate:ASA Firewall:117", "anchor": "117 ASA Firewall leads", "provider_family": "asa_firewall"},
        {"motif_id": "C12-M02", "claim_id": "C12-EC-002", "node_id": "N01_perimeter_activity", "record_index_1based": source_record, "record_id": str(port_445["id"]), "anchor": "structured destination port 445", "provider_family": "asa_firewall"},
        {"motif_id": "C12-M03", "claim_id": "C12-EC-003", "node_id": "N02_privileged_identity_activity", "record_index_1based": source_record, "record_id": str(identity[0]["id"]), "anchor": "Windows Event 4672", "provider_family": "windows_ad"},
        {"motif_id": "C12-M04", "claim_id": "C12-EC-004", "node_id": "N02_privileged_identity_activity", "record_index_1based": source_record, "record_id": str(identity[1]["id"]), "anchor": "Windows Event 4672", "provider_family": "windows_ad"},
        {"motif_id": "C12-M05", "claim_id": "C12-EC-005", "node_id": "N03_cross_channel_context", "record_index_1based": source_record, "record_id": incident_id, "anchor": "49 INCIDENT_LINK edges", "provider_family": "precinct_projection"},
    ]
    motif_spec = {
        "case_id": case_id,
        "source_case_id": incident_id,
        "source_artifact_id": incident_artifact,
        "source_member": "graph/incidents.jsonl",
        "selection_source": "../../real_data/witfoo_precinct6/c12_case_compile_lock_v0.1.json",
        "node_coverage_semantics": "AND",
        "motifs": motifs,
        "natural_gap": {"node_id": "N04_actor_campaign_attribution", "matched_records": 0, "handling": "Keep uncovered and cap the case at G1."},
    }
    motif_report = {
        "case_id": case_id,
        "source_case_id": incident_id,
        "compile_status": "compiled_event_backed_operational_stress_case",
        "event_source_gate": "PASS",
        "selected_claim_count": len(claims),
        "selected_provider_families": ["asa_firewall", "precinct_projection", "windows_ad"],
        "node_results": [
            {"node_id": "N01_perimeter_activity", "status": "compiled", "claim_ids": ["C12-EC-001", "C12-EC-002"], "provider_families": ["asa_firewall"]},
            {"node_id": "N02_privileged_identity_activity", "status": "compiled", "claim_ids": ["C12-EC-003", "C12-EC-004"], "provider_families": ["windows_ad"]},
            {"node_id": "N03_cross_channel_context", "status": "compiled_context_only", "claim_ids": ["C12-EC-001", "C12-EC-003", "C12-EC-005"], "provider_families": ["asa_firewall", "windows_ad", "precinct_projection"]},
            {"node_id": "N04_actor_campaign_attribution", "status": "natural_gap", "claim_ids": [], "reason": "No actor label or independent campaign truth."},
        ],
        "support_decision": {"compiled_target": "G1_technique", "compiled_ceiling": "G1_technique", "reason": "Raw observations support behavior-level investigation only; actor and campaign conclusions remain unsupported."},
        "source_boundaries": lock["frozen_boundaries"],
    }
    return {
        "case_config.json": config,
        "evidence_claims.json": claims,
        "acquisition_actions.json": actions,
        "motif_spec.json": motif_spec,
        "motif_report.json": motif_report,
    }


def verify_inputs(lock: dict[str, Any], paths: dict[str, Path]) -> None:
    expected = lock["input_integrity"]
    checks = {
        "intake_lock_sha256": sha256(paths["intake_lock"]),
        "candidate_index_sha256": sha256(paths["candidate_index"]),
        "event_audit_sha256": sha256(paths["event_audit"]),
        "incident_line_sha256": sha256(paths["incident"]),
        "graphml_sha256": sha256(paths["graphml"]),
    }
    mismatches = {
        key: {"expected": expected[key], "observed": observed}
        for key, observed in checks.items()
        if expected[key] != observed
    }
    if mismatches:
        raise ValueError(f"C12 compile input integrity mismatch: {mismatches}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile the frozen C12 WitFoo case.")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument(
        "--output-root", type=Path, default=ROOT / "09-experiments" / "real_cases"
    )
    args = parser.parse_args()
    lock = load_json(args.lock)
    incident_id = lock["selected_incident_id"]
    paths = {
        "intake_lock": DEFAULT_INTAKE_LOCK,
        "candidate_index": DEFAULT_CANDIDATES,
        "event_audit": DEFAULT_EVENT_AUDIT,
        "incident": DATA_ROOT / "raw" / "incidents" / f"{incident_id}.json",
        "graphml": DATA_ROOT / "raw" / "graphs" / f"{incident_id}.graphml",
    }
    verify_inputs(lock, paths)
    outputs = compile_case(
        lock,
        load_json(paths["incident"]),
        sha256(paths["graphml"]),
    )
    output_directory = args.output_root / lock["case_id"]
    output_directory.mkdir(parents=True, exist_ok=True)
    for filename, payload in outputs.items():
        (output_directory / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "case_id": lock["case_id"],
                "output_directory": str(output_directory.relative_to(ROOT)),
                "claims": len(outputs["evidence_claims.json"]),
                "actions": len(outputs["acquisition_actions.json"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
