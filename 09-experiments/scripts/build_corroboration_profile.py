#!/usr/bin/env python3
"""Build an explicit provider/source-family mapping for k-of-n scans."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REAL_CASES = ROOT / "09-experiments" / "real_cases"
DEFAULT_OUTPUT = (
    ROOT
    / "09-experiments"
    / "governance"
    / "profiles"
    / "corroboration-source-groups-v0.1.json"
)
CASE_PREFIXES = ("C07", "C08", "C09", "C10", "C11", "C12")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def resolve_cases() -> list[Path]:
    resolved: list[Path] = []
    for prefix in CASE_PREFIXES:
        matches = sorted(path for path in REAL_CASES.glob(f"{prefix}-*") if path.is_dir())
        if len(matches) != 1:
            raise FileNotFoundError(
                f"Expected one {prefix} case under {REAL_CASES}; found {matches}"
            )
        resolved.append(matches[0])
    return resolved


def normalize_provider(provider: str) -> str:
    lowered = provider.casefold()
    if "powershell" in lowered:
        return "windows_powershell"
    if "sysmon" in lowered:
        return "windows_sysmon"
    if lowered == "security" or "windows-security" in lowered:
        return "windows_security"
    normalized = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return normalized or "unknown_provider"


def infer_source_group(claim: dict[str, Any]) -> tuple[str, str]:
    case_id = str(claim["case_id"])
    pointer = claim.get("source_pointer", {}) or {}
    artifact = str(pointer.get("artifact_id", "unknown_artifact"))
    record_id = str(pointer.get("record_id", ""))
    location = str(pointer.get("location", ""))
    source_type = str(claim.get("source_type", "unknown_source"))

    if case_id.startswith("C11-"):
        parts = record_id.split("|")
        if len(parts) >= 2 and parts[0] and parts[1]:
            host = re.sub(r"[^a-z0-9]+", "_", parts[0].casefold()).strip("_")
            provider = normalize_provider(parts[1])
            return (
                f"{host}:{provider}",
                "C11 source_pointer.record_id host and Windows provider family",
            )

    if case_id.startswith("C12-"):
        predicate = str(claim.get("predicate", ""))
        combined = f"{artifact} {location} {record_id} {predicate}".casefold()
        if (
            "asa" in combined
            or "blocked" in predicate.casefold()
            or source_type == "network_summary"
        ):
            return "asa_firewall", "C12 ASA artifact/location/blocked-flow predicate family"
        if "graphml" in combined or source_type == "provenance_graph":
            return "precinct_projection", "C12 vendor GraphML projection family"
        if "windows_event" in predicate.casefold() or "windows" in combined:
            return "windows_ad", "C12 Windows Event predicate family"

    fallback = re.sub(
        r"[^a-z0-9]+",
        "_",
        f"{artifact}:{source_type}".casefold(),
    ).strip("_")
    return fallback, "artifact_id plus source_type fallback"


def build() -> dict[str, Any]:
    assignments: list[dict[str, Any]] = []
    node_audit: list[dict[str, Any]] = []
    case_ids: list[str] = []
    for case_dir in resolve_cases():
        config = load_json(case_dir / "case_config.json")
        claims = load_json(case_dir / "evidence_claims.json")
        case_id = str(config["case_id"])
        case_ids.append(case_id)
        claim_map = {claim["claim_id"]: claim for claim in claims}
        group_map: dict[str, str] = {}
        for claim in claims:
            group, basis = infer_source_group(claim)
            group_map[claim["claim_id"]] = group
            assignments.append(
                {
                    "case_id": case_id,
                    "claim_id": claim["claim_id"],
                    "source_group": group,
                    "basis": basis,
                }
            )
        for node in config["cti_nodes"]:
            required = [str(item) for item in node["required_claim_ids"]]
            missing = [claim_id for claim_id in required if claim_id not in claim_map]
            if missing:
                raise ValueError(
                    f"{case_id}/{node['node_id']} references missing claims {missing}"
                )
            groups = {group_map[claim_id] for claim_id in required}
            node_audit.append(
                {
                    "case_id": case_id,
                    "node_id": node["node_id"],
                    "required_claim_count": len(set(required)),
                    "source_group_count": len(groups),
                    "claim_count_overstates_source_groups": len(set(required)) > len(groups),
                }
            )
    return {
        "$schema": "../../data_schema/corroboration_profile.schema.json",
        "profile_id": "project05-corroboration-source-groups-v0.1",
        "version": "0.1.0",
        "status": "frozen_mapping",
        "created_utc": "2026-07-13T16:00:00Z",
        "scope": {"case_ids": case_ids},
        "grouping_unit": "provider_or_source_family",
        "independence_boundary": (
            "Groups distinguish provider/source families, not organizations, sensors, "
            "or statistically independent observations. Source-group results are a "
            "corroboration diagnostic and must not be described as independent-source proof."
        ),
        "assignments": assignments,
        "node_audit": node_audit,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    profile = build()
    write_json(args.output, profile)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "case_count": len(profile["scope"]["case_ids"]),
                "claim_count": len(profile["assignments"]),
                "nodes_with_claim_source_collapse": sum(
                    row["claim_count_overstates_source_groups"]
                    for row in profile["node_audit"]
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
