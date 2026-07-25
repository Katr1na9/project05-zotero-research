#!/usr/bin/env python3
"""Build non-destructive acquisition-cost governance artifacts.

The builder never edits acquisition_actions.json. It produces draft rubric and
measured profiles plus two independently ordered rating templates. Legacy
costs and action outcomes remain in the administrator inventory only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "09-experiments"
DEFAULT_PROFILE_DIR = EXPERIMENT_ROOT / "governance" / "profiles"
DEFAULT_ANNOTATION_DIR = EXPERIMENT_ROOT / "annotation" / "cost_v0.1"
DEFAULT_CREATED_UTC = "2026-07-13T16:00:00Z"
COMPONENTS = ("E", "V", "D", "A", "R")
ACTION_TYPE_CHANNELS = {
    "extend_log_window": "log_retention",
    "query_host_subgraph": "host_forensics",
    "recover_network_summary": "network_telemetry",
    "ioc_enrichment": "threat_intel",
    "infrastructure_history": "threat_intel",
    "cti_report_lookup": "threat_intel",
    "malware_analysis": "sample_lab",
    "ttp_local_probe": "host_probe",
    "human_review": "analyst",
    "other": "other",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_json(data: Any) -> str:
    payload = json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def display_path(path: Path) -> str:
    """Use stable repository-relative paths, while supporting external test roots."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def discover_case_dirs() -> list[Path]:
    case_dirs: list[Path] = []
    for parent in (EXPERIMENT_ROOT / "examples", EXPERIMENT_ROOT / "real_cases"):
        for path in parent.iterdir():
            if (
                path.is_dir()
                and path.name[:3].startswith("C")
                and path.name[1:3].isdigit()
                and (path / "case_config.json").is_file()
                and (path / "acquisition_actions.json").is_file()
            ):
                case_dirs.append(path)
    return sorted(
        case_dirs,
        key=lambda path: load_json(path / "case_config.json")["case_id"],
    )


def action_channel(action: dict[str, Any]) -> str:
    return str(
        action.get("acquisition_channel")
        or ACTION_TYPE_CHANNELS.get(action.get("action_type"), "other")
    )


def _timestamp_seconds(motif: dict[str, Any], prefix: str) -> float | None:
    nanos = motif.get(f"{prefix}_timestamp_nanos")
    if isinstance(nanos, (int, float)):
        return float(nanos) / 1_000_000_000.0
    utc = motif.get(f"{prefix}_timestamp_utc")
    if isinstance(utc, str) and utc:
        try:
            return datetime.fromisoformat(utc.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def measurement_evidence(
    case_dir: Path,
    action: dict[str, Any],
) -> dict[str, Any]:
    report_path = case_dir / "motif_report.json"
    report = load_json(report_path) if report_path.is_file() else {}
    motifs = report.get("motifs", {}) if isinstance(report, dict) else {}
    selected = [
        motifs[claim_id]
        for claim_id in action.get("recoverable_claim_ids", [])
        if claim_id in motifs and isinstance(motifs[claim_id], dict)
    ]
    matched_counts = [
        motif.get("matched_event_count")
        for motif in selected
        if isinstance(motif.get("matched_event_count"), (int, float))
    ]
    starts = [
        value
        for motif in selected
        if (value := _timestamp_seconds(motif, "first")) is not None
    ]
    ends = [
        value
        for motif in selected
        if (value := _timestamp_seconds(motif, "last")) is not None
    ]
    limitations = [
        "case_events_scanned is compilation-wide, not an action-specific scan count",
        "recoverable_matched_event_count is observed yield, not collection effort or bytes scanned",
        "bytes, retention window, authorization boundary, and host count require new operational measurements",
    ]
    if not report_path.is_file():
        limitations.append("no motif_report.json is available for this case")
    elif not motifs:
        limitations.append("motif report contains no action-addressable motif counts")
    return {
        "case_events_scanned": (
            report.get("events_scanned")
            if isinstance(report.get("events_scanned"), (int, float))
            else None
        ),
        "recoverable_matched_event_count": (
            sum(matched_counts) if matched_counts else None
        ),
        "observed_window_seconds": (
            max(ends) - min(starts) if starts and ends else None
        ),
        "bytes_scanned": None,
        "retention_window_days": None,
        "host_count": None,
        "limitations": limitations,
    }


def collect_actions() -> tuple[list[str], list[dict[str, Any]]]:
    case_ids: list[str] = []
    rows: list[dict[str, Any]] = []
    for case_dir in discover_case_dirs():
        config = load_json(case_dir / "case_config.json")
        case_id = str(config["case_id"])
        case_ids.append(case_id)
        relative_case_dir = case_dir.relative_to(ROOT).as_posix()
        for action in load_json(case_dir / "acquisition_actions.json"):
            rows.append(
                {
                    "case_id": case_id,
                    "case_dir": relative_case_dir,
                    "action_id": action["action_id"],
                    "action_type": action["action_type"],
                    "acquisition_channel": action_channel(action),
                    "target_type": action.get("target", {}).get("target_type", ""),
                    "target_value": action.get("target", {}).get("target_value", ""),
                    "expected_evidence_types": "|".join(
                        action.get("expected_evidence_types", [])
                    ),
                    "natural_language_request": action.get(
                        "natural_language_request", ""
                    ),
                    "legacy_cost": float(action["cost"]),
                    "recoverable_claim_count": len(
                        action.get("recoverable_claim_ids", [])
                    ),
                    "measurement_evidence": measurement_evidence(case_dir, action),
                    "evidence_refs": [
                        f"{relative_case_dir}/acquisition_actions.json",
                        *(
                            [f"{relative_case_dir}/motif_report.json"]
                            if (case_dir / "motif_report.json").is_file()
                            else []
                        ),
                    ],
                }
            )
    return case_ids, rows


def profile_entry(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": row["case_id"],
        "action_id": row["action_id"],
        "legacy_cost": row["legacy_cost"],
        "components": {component: None for component in COMPONENTS},
        "measured_cost": None,
        "measurement_evidence": row["measurement_evidence"],
        "rating_status": "pending_independent_rating",
        "evidence_refs": row["evidence_refs"],
        "notes": [
            "No component score or measured cost has been imputed by the builder."
        ],
    }


def build_profiles(
    case_ids: list[str],
    rows: list[dict[str, Any]],
    created_utc: str,
    rubric_scale: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    base = {
        "$schema": "../../data_schema/cost_profile.schema.json",
        "created_utc": created_utc,
        "standard_ref": "../../../08-writing/cost-assignment-standard-v0.1-20260714.md",
        "scope": {"case_ids": case_ids},
        "actions": [profile_entry(row) for row in rows],
    }
    rubric = {
        **base,
        "profile_id": "project05-cost-rubric-v0.1-draft",
        "version": "0.1.0-draft",
        "status": "draft",
        "regime": "rubric",
        "notes": [
            "Prospective lock for new governance runs only; legacy planner results already exist.",
            "Scale is provisional until rating training and agreement analysis are complete.",
        ],
        "scoring": {
            "method": "weighted_sum_scaled_round",
            "volatility_treatment": "separate_delay_loss",
            "weights": {component: 1.0 for component in COMPONENTS},
            "scale": rubric_scale,
            "rounding": "half_up",
            "minimum_cost": 1.0,
            "maximum_cost": 4.0,
            "unit": "relative_acquisition_cost_band",
            "formula": "clip(round_half_up(sum(w_i * component_i for i in E,D,A,R) / scale), 1, 4); V is modeled separately as delay loss",
        },
    }
    measured = {
        **base,
        "profile_id": "project05-cost-measured-v0.1-draft",
        "version": "0.1.0-draft",
        "status": "draft",
        "regime": "measured",
        "notes": [
            "Operational measurements are incomplete; this profile must not be frozen or run.",
            "Compilation-wide event counts and observed yields are evidence only, not measured action costs.",
        ],
        "scoring": {
            "method": "precomputed_continuous",
            "unit": "normalized_relative_operational_cost",
            "formula": "pending: freeze normalization before collecting formal operational measurements",
        },
    }
    return rubric, measured


def blind_item_id(action_id: str) -> str:
    digest = hashlib.sha256(f"project05-cost-v0.1|{action_id}".encode()).hexdigest()
    return f"COST-{digest[:12].upper()}"


def build_rating_rows(
    rows: list[dict[str, Any]],
    annotator_code: str,
    seed: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        evidence = row["measurement_evidence"]
        output.append(
            {
                "package_id": f"cost_v0.1_{annotator_code}",
                "annotator_code": annotator_code,
                "item_id": blind_item_id(row["action_id"]),
                "action_type": row["action_type"],
                "acquisition_channel": row["acquisition_channel"],
                "target_type": row["target_type"],
                "target_value": row["target_value"],
                "expected_evidence_types": row["expected_evidence_types"],
                "natural_language_request": row["natural_language_request"],
                "case_events_scanned_evidence": evidence["case_events_scanned"],
                "observed_window_seconds_evidence": evidence[
                    "observed_window_seconds"
                ],
                "E": "",
                "V": "",
                "D": "",
                "A": "",
                "R": "",
                "rating_confidence": "",
                "rating_evidence": "",
                "reviewed": "no",
            }
        )
    random.Random(seed).shuffle(output)
    return output


def build(
    profile_dir: Path,
    annotation_dir: Path,
    created_utc: str = DEFAULT_CREATED_UTC,
    rubric_scale: float = 3.75,
) -> dict[str, Any]:
    case_ids, rows = collect_actions()
    rubric, measured = build_profiles(case_ids, rows, created_utc, rubric_scale)
    rubric_path = profile_dir / "cost-rubric-v0.1-draft.json"
    measured_path = profile_dir / "cost-measured-v0.1-draft.json"
    write_json(rubric_path, rubric)
    write_json(measured_path, measured)

    admin_fields = [
        "item_id",
        "case_id",
        "action_id",
        "action_type",
        "acquisition_channel",
        "legacy_cost",
        "recoverable_claim_count",
        "case_dir",
    ]
    admin_rows = [
        {field: (blind_item_id(row["action_id"]) if field == "item_id" else row[field])
         for field in admin_fields}
        for row in rows
    ]
    write_csv(annotation_dir / "admin" / "item_key.csv", admin_rows, admin_fields)

    rating_fields = list(build_rating_rows(rows[:1], "A", 20260714)[0])
    packets: dict[str, str] = {}
    for annotator_code, seed in (("A", 20260714), ("B", 20260715)):
        packet_path = annotation_dir / "public" / f"cost_ratings_{annotator_code}.csv"
        write_csv(
            packet_path,
            build_rating_rows(rows, annotator_code, seed),
            rating_fields,
        )
        packets[annotator_code] = display_path(packet_path)

    collection_fields = [
        "item_id",
        "measurement_id",
        "attempt_id",
        "started_utc",
        "ended_utc",
        "analyst_seconds",
        "compute_seconds",
        "records_scanned",
        "bytes_scanned",
        "host_count",
        "retention_window_days",
        "authorization_required",
        "authorization_boundary",
        "approval_reference",
        "system_perturbation_events",
        "execution_status",
        "collector",
        "source_system",
        "measurement_notes",
    ]
    write_csv(
        annotation_dir / "public" / "measured_cost_collection_template.csv",
        [
            {field: blind_item_id(row["action_id"]) if field == "item_id" else ""
             for field in collection_fields}
            for row in rows
        ],
        collection_fields,
    )

    manifest = {
        "artifact_version": "cost_governance_v0.1",
        "status": "draft_awaiting_two_independent_raters_and_measurements",
        "created_utc": created_utc,
        "independent_case_count": len(case_ids),
        "action_count": len(rows),
        "profiles": {
            "rubric": display_path(rubric_path),
            "rubric_canonical_sha256": sha256_json(rubric),
            "measured": display_path(measured_path),
            "measured_canonical_sha256": sha256_json(measured),
        },
        "rating_packets": packets,
        "legacy_cost_visible_to_raters": False,
        "planner_results_visible_to_raters": False,
        "formal_run_allowed": False,
    }
    write_json(annotation_dir / "packet_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build draft cost profiles and independent rating packets."
    )
    parser.add_argument("--profile-dir", type=Path, default=DEFAULT_PROFILE_DIR)
    parser.add_argument("--annotation-dir", type=Path, default=DEFAULT_ANNOTATION_DIR)
    parser.add_argument("--created-utc", default=DEFAULT_CREATED_UTC)
    parser.add_argument("--rubric-scale", type=float, default=3.75)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                args.profile_dir,
                args.annotation_dir,
                args.created_utc,
                args.rubric_scale,
            ),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
