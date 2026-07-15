#!/usr/bin/env python3
"""Build auditable draft cost profiles and blinded rating templates.

This script never edits acquisition_actions.json. It harvests only observable
case/action facts, preserves missing measurements as null, and emits draft
profiles that run_mvp.py will refuse until real raters/measurements are complete
and the profile status is explicitly frozen.
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
DEFAULT_EXAMPLES_DIR = EXPERIMENT_ROOT / "examples"
DEFAULT_REAL_CASES_DIR = EXPERIMENT_ROOT / "real_cases"
STANDARD_REF = "08-writing/cost-assignment-standard-v0.1-20260714.md"
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
    "stop": "decision",
    "other": "other",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def validate_created_utc(value: str) -> str:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("--created-utc must include a timezone (normally Z)")
    return value


def discover_case_dirs(examples_dir: Path, real_cases_dir: Path) -> list[Path]:
    required = ("case_config.json", "evidence_claims.json", "acquisition_actions.json")
    candidates: list[Path] = []
    for root in (examples_dir, real_cases_dir):
        if not root.is_dir():
            raise FileNotFoundError(f"Case root does not exist: {root}")
        candidates.extend(
            path
            for path in root.iterdir()
            if path.is_dir()
            and path.name.startswith("C")
            and all((path / name).is_file() for name in required)
        )
    identified = [
        (load_json(path / "case_config.json")["case_id"], path)
        for path in candidates
    ]
    case_ids = [case_id for case_id, _ in identified]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Duplicate case_id discovered while building cost profiles")
    return [path for _, path in sorted(identified)]


def action_channel(action: dict[str, Any]) -> str:
    explicit = action.get("acquisition_channel")
    if explicit:
        return str(explicit)
    return ACTION_TYPE_CHANNELS.get(str(action.get("action_type", "other")), "other")


def parse_utc_timestamp(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return None


def measurement_evidence(
    case_dir: Path,
    action: dict[str, Any],
) -> dict[str, Any]:
    report_path = case_dir / "motif_report.json"
    report = load_json(report_path) if report_path.is_file() else {}
    case_events_scanned = report.get("events_scanned")
    if not isinstance(case_events_scanned, (int, float)):
        case_events_scanned = None

    motifs = report.get("motifs") if isinstance(report, dict) else None
    selected: list[dict[str, Any]] = []
    if isinstance(motifs, dict):
        for claim_id in action.get("recoverable_claim_ids", []):
            motif = motifs.get(claim_id)
            if isinstance(motif, dict):
                selected.append(motif)

    counts = [
        motif["matched_event_count"]
        for motif in selected
        if isinstance(motif.get("matched_event_count"), (int, float))
    ]
    recoverable_matched_event_count = sum(counts) if counts else None

    first_values: list[float] = []
    last_values: list[float] = []
    for motif in selected:
        first_nanos = motif.get("first_timestamp_nanos")
        last_nanos = motif.get("last_timestamp_nanos")
        if isinstance(first_nanos, (int, float)):
            first_values.append(float(first_nanos) / 1_000_000_000)
        if isinstance(last_nanos, (int, float)):
            last_values.append(float(last_nanos) / 1_000_000_000)
        first_utc = parse_utc_timestamp(motif.get("first_timestamp_utc"))
        last_utc = parse_utc_timestamp(motif.get("last_timestamp_utc"))
        if first_utc is not None:
            first_values.append(first_utc)
        if last_utc is not None:
            last_values.append(last_utc)
    observed_window_seconds = (
        max(0.0, max(last_values) - min(first_values))
        if first_values and last_values
        else None
    )

    limitations = [
        "case_events_scanned is compilation-wide, not action-specific",
        "recoverable_matched_event_count is observed yield, not scan cost",
        "observed_window_seconds is evidence span, not retention lifetime",
        "bytes_scanned, retention_window_days, and host_count require new measurement",
    ]
    if not report_path.is_file():
        limitations.append("no motif_report.json is available for this case")
    elif not isinstance(motifs, dict):
        limitations.append("motif report has no action-addressable per-claim counts")
    return {
        "case_events_scanned": case_events_scanned,
        "recoverable_matched_event_count": recoverable_matched_event_count,
        "observed_window_seconds": (
            round(observed_window_seconds, 6)
            if observed_window_seconds is not None
            else None
        ),
        "bytes_scanned": None,
        "retention_window_days": None,
        "host_count": None,
        "limitations": limitations,
    }


def item_id(action_id: str) -> str:
    digest = hashlib.sha256(f"project05-cost-v0.1|{action_id}".encode()).hexdigest()
    return f"COST-{digest[:12].upper()}"


def collect_actions(case_dirs: list[Path]) -> tuple[list[dict[str, Any]], list[Path]]:
    records: list[dict[str, Any]] = []
    inputs: list[Path] = []
    seen_action_ids: set[str] = set()
    for case_dir in case_dirs:
        config_path = case_dir / "case_config.json"
        actions_path = case_dir / "acquisition_actions.json"
        claims_path = case_dir / "evidence_claims.json"
        motif_path = case_dir / "motif_report.json"
        inputs.extend([config_path, actions_path, claims_path])
        if motif_path.is_file():
            inputs.append(motif_path)
        config = load_json(config_path)
        actions = load_json(actions_path)
        if not isinstance(actions, list):
            raise ValueError(f"Expected an action array: {actions_path}")
        for action in actions:
            action_id_value = action.get("action_id")
            if not isinstance(action_id_value, str) or not action_id_value:
                raise ValueError(f"Action without action_id in {actions_path}")
            if action_id_value in seen_action_ids:
                raise ValueError(f"Duplicate action_id: {action_id_value}")
            seen_action_ids.add(action_id_value)
            target = action.get("target") or {}
            expected_types = action.get("expected_evidence_types") or []
            records.append(
                {
                    "case_id": config["case_id"],
                    "action_id": action_id_value,
                    "item_id": item_id(action_id_value),
                    "action_type": action.get("action_type", "other"),
                    "acquisition_channel": action_channel(action),
                    "target_type": target.get("target_type", ""),
                    "target_value": target.get("target_value", ""),
                    "expected_evidence_types": "|".join(map(str, expected_types)),
                    "natural_language_request": action.get("natural_language_request", ""),
                    "legacy_cost": float(action["cost"]),
                    "measurement_evidence": measurement_evidence(case_dir, action),
                    "actions_ref": relative_path(actions_path),
                    "motif_ref": relative_path(motif_path) if motif_path.is_file() else "",
                }
            )
    records.sort(key=lambda record: (record["case_id"], record["action_id"]))
    generated_item_ids = [record["item_id"] for record in records]
    if len(generated_item_ids) != len(set(generated_item_ids)):
        raise ValueError("Pseudonymous cost item_id collision")
    return records, sorted(set(inputs), key=relative_path)


def profile_actions(records: list[dict[str, Any]], regime: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for record in records:
        refs = [record["actions_ref"]]
        if record["motif_ref"]:
            refs.append(record["motif_ref"])
        output.append(
            {
                "case_id": record["case_id"],
                "action_id": record["action_id"],
                "legacy_cost": record["legacy_cost"],
                "components": {component: None for component in COMPONENTS},
                "measured_cost": None,
                "measurement_evidence": record["measurement_evidence"],
                "rating_status": (
                    "pending_independent_rating"
                    if regime == "rubric"
                    else "not_applicable"
                ),
                "evidence_refs": refs,
                "notes": [
                    "Draft only; no component or measured cost is frozen.",
                    "Legacy cost is retained for audit and is not an input to blinded rating.",
                ],
            }
        )
    return output


def build_profile(
    records: list[dict[str, Any]],
    regime: str,
    version: str,
    created_utc: str,
) -> dict[str, Any]:
    if regime == "rubric":
        scoring = {
            "method": "weighted_sum_scaled_round",
            "unit": "relative acquisition-cost band",
            "formula": "TBD before profile freeze: weights, scale, rounding, and bounds",
        }
    else:
        scoring = {
            "method": "precomputed_continuous",
            "unit": "normalized relative operational cost",
            "formula": "TBD before profile freeze: operational metric normalization",
        }
    return {
        "$schema": "https://github.com/Katr1na9/project05-zotero-research/schemas/cost_profile.schema.json",
        "profile_id": f"project05-{regime}-cost-v0.1",
        "version": version,
        "status": "draft",
        "regime": regime,
        "created_utc": created_utc,
        "standard_ref": STANDARD_REF,
        "notes": [
            "Generated without modifying case action files.",
            "Planner outcomes and expected-effect scores are excluded from rating packets.",
            "run_mvp.py rejects this profile until it is complete and frozen.",
        ],
        "scope": {
            "case_ids": sorted({record["case_id"] for record in records}),
        },
        "scoring": scoring,
        "actions": profile_actions(records, regime),
    }


def inventory_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        evidence = record["measurement_evidence"]
        rows.append(
            {
                "case_id": record["case_id"],
                "action_id": record["action_id"],
                "item_id": record["item_id"],
                "action_type": record["action_type"],
                "acquisition_channel": record["acquisition_channel"],
                "target_type": record["target_type"],
                "target_value": record["target_value"],
                "legacy_cost": record["legacy_cost"],
                "case_events_scanned": evidence["case_events_scanned"],
                "recoverable_matched_event_count": evidence[
                    "recoverable_matched_event_count"
                ],
                "observed_window_seconds": evidence["observed_window_seconds"],
                "measurement_gap": "bytes_scanned|retention_window_days|host_count",
                "actions_ref": record["actions_ref"],
                "motif_ref": record["motif_ref"],
            }
        )
    return rows


def rating_rows(
    records: list[dict[str, Any]],
    annotator_code: str,
    seed: int,
) -> list[dict[str, Any]]:
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    package_id = f"COST-RUBRIC-V0.1-{annotator_code}"
    rows: list[dict[str, Any]] = []
    for record in shuffled:
        evidence = record["measurement_evidence"]
        rows.append(
            {
                "package_id": package_id,
                "annotator_code": annotator_code,
                "item_id": record["item_id"],
                "action_type": record["action_type"],
                "acquisition_channel": record["acquisition_channel"],
                "target_type": record["target_type"],
                "target_value": record["target_value"],
                "expected_evidence_types": record["expected_evidence_types"],
                "natural_language_request": record["natural_language_request"],
                "case_events_scanned": evidence["case_events_scanned"],
                "case_events_scanned_scope": (
                    "case_compilation_not_action_specific"
                    if evidence["case_events_scanned"] is not None
                    else "unavailable"
                ),
                "E_score": "",
                "V_score": "",
                "D_score": "",
                "A_score": "",
                "R_score": "",
                "rating_confidence": "",
                "rating_evidence_note": "",
            }
        )
    return rows


def measurement_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": record["case_id"],
            "action_id": record["action_id"],
            "action_type": record["action_type"],
            "acquisition_channel": record["acquisition_channel"],
            "trial_id": "",
            "analyst_minutes": "",
            "machine_seconds": "",
            "bytes_scanned": "",
            "records_scanned": "",
            "host_count": "",
            "retention_window_days": "",
            "authorization_tier_0_3": "",
            "perturbation_tier_0_3": "",
            "measurement_notes": "",
        }
        for record in records
    ]


def ensure_empty_output(output_dir: Path) -> None:
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise FileExistsError(
            f"Refusing to overwrite non-empty draft directory: {output_dir}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)


def build(args: argparse.Namespace) -> dict[str, Any]:
    created_utc = validate_created_utc(args.created_utc)
    output_dir = args.output_dir.resolve()
    ensure_empty_output(output_dir)
    case_dirs = discover_case_dirs(args.examples_dir, args.real_cases_dir)
    records, input_paths = collect_actions(case_dirs)
    for path in (
        Path(__file__).resolve(),
        EXPERIMENT_ROOT / "data_schema" / "cost_profile.schema.json",
        ROOT / STANDARD_REF,
    ):
        if path.is_file():
            input_paths.append(path)
    input_paths = sorted(set(input_paths), key=relative_path)

    rubric_path = output_dir / "rubric-cost-profile-v0.1-draft.json"
    measured_path = output_dir / "measured-cost-profile-v0.1-draft.json"
    inventory_path = output_dir / "action-cost-inventory.csv"
    packet_a_path = output_dir / "cost-rating-packet-A.csv"
    packet_b_path = output_dir / "cost-rating-packet-B.csv"
    measurement_path = output_dir / "measured-cost-collection-template.csv"

    write_json(
        rubric_path,
        build_profile(records, "rubric", args.profile_version, created_utc),
    )
    write_json(
        measured_path,
        build_profile(records, "measured", args.profile_version, created_utc),
    )
    inventory_fields = [
        "case_id",
        "action_id",
        "item_id",
        "action_type",
        "acquisition_channel",
        "target_type",
        "target_value",
        "legacy_cost",
        "case_events_scanned",
        "recoverable_matched_event_count",
        "observed_window_seconds",
        "measurement_gap",
        "actions_ref",
        "motif_ref",
    ]
    rating_fields = [
        "package_id",
        "annotator_code",
        "item_id",
        "action_type",
        "acquisition_channel",
        "target_type",
        "target_value",
        "expected_evidence_types",
        "natural_language_request",
        "case_events_scanned",
        "case_events_scanned_scope",
        "E_score",
        "V_score",
        "D_score",
        "A_score",
        "R_score",
        "rating_confidence",
        "rating_evidence_note",
    ]
    measurement_fields = [
        "case_id",
        "action_id",
        "action_type",
        "acquisition_channel",
        "trial_id",
        "analyst_minutes",
        "machine_seconds",
        "bytes_scanned",
        "records_scanned",
        "host_count",
        "retention_window_days",
        "authorization_tier_0_3",
        "perturbation_tier_0_3",
        "measurement_notes",
    ]
    write_csv(inventory_path, inventory_rows(records), inventory_fields)
    write_csv(
        packet_a_path,
        rating_rows(records, "A", args.seed),
        rating_fields,
    )
    write_csv(
        packet_b_path,
        rating_rows(records, "B", args.seed + 1),
        rating_fields,
    )
    write_csv(measurement_path, measurement_rows(records), measurement_fields)

    generated = [
        rubric_path,
        measured_path,
        inventory_path,
        packet_a_path,
        packet_b_path,
        measurement_path,
    ]
    manifest = {
        "created_utc": created_utc,
        "profile_version": args.profile_version,
        "seed": args.seed,
        "case_count": len(case_dirs),
        "action_count": len(records),
        "inputs": [
            {"path": relative_path(path), "sha256": sha256_file(path)}
            for path in input_paths
        ],
        "outputs": [
            {
                "path": path.relative_to(output_dir).as_posix(),
                "sha256": sha256_file(path),
            }
            for path in generated
        ],
    }
    write_json(output_dir / "build-manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build draft Project05 cost profiles and rating templates."
    )
    parser.add_argument("--examples-dir", type=Path, default=DEFAULT_EXAMPLES_DIR)
    parser.add_argument("--real-cases-dir", type=Path, default=DEFAULT_REAL_CASES_DIR)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--created-utc", required=True)
    parser.add_argument("--profile-version", default="0.1.0-draft")
    parser.add_argument("--seed", type=int, default=20260714)
    args = parser.parse_args()
    manifest = build(args)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
