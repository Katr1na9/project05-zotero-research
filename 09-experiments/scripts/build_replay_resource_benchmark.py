#!/usr/bin/env python3
"""Build a real-only replay-I/O benchmark without mutating source cases.

The scalar used by this benchmark is deliberately narrow: one unit is one full
logical scan of the immutable replay artifacts for that case.  Raw byte counts
remain attached to every action so the normalization is exactly reversible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
EXECUTABLE_ACTION_TYPES = frozenset(
    {
        "extend_log_window",
        "query_host_subgraph",
        "recover_network_summary",
        "ttp_local_probe",
    }
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def portable_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def scan_bytes_for_action(
    action_type: str,
    event_bytes: int,
    node_bytes: int,
) -> int:
    total_bytes = event_bytes + node_bytes
    if total_bytes <= 0:
        raise ValueError("Replay artifacts must contain at least one byte")
    if action_type == "query_host_subgraph":
        return 2 * event_bytes + node_bytes if node_bytes else 2 * total_bytes
    if action_type == "recover_network_summary":
        return node_bytes if node_bytes else total_bytes
    if action_type in {"ttp_local_probe", "extend_log_window"}:
        return event_bytes if event_bytes else total_bytes
    raise ValueError(f"Action type is not executable in this benchmark: {action_type}")


def measurement_entry(
    case_id: str,
    action: dict[str, Any],
    raw_scan_bytes: int,
    case_full_scan_bytes: int,
    replay_refs: list[str],
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "action_id": action["action_id"],
        "legacy_cost": float(action["cost"]),
        "components": {component: None for component in ("E", "V", "D", "A", "R")},
        "measured_cost": raw_scan_bytes / case_full_scan_bytes,
        "measurement_evidence": {
            "case_events_scanned": None,
            "recoverable_matched_event_count": None,
            "observed_window_seconds": None,
            "bytes_scanned": raw_scan_bytes,
            "retention_window_days": None,
            "host_count": None,
            "limitations": [
                "This scenario measures deterministic replay data-access burden only.",
                "CPU, wall time, analyst time, delay loss, operational risk, and utility remain separate.",
                "The full-scan-equivalent normalization is case-local and exactly reversible from bytes_scanned.",
            ],
        },
        "rating_status": "not_applicable",
        "evidence_refs": replay_refs,
        "notes": [
            f"action_type={action['action_type']}",
            f"case_full_scan_bytes={case_full_scan_bytes}",
        ],
    }


def build_benchmark(
    cohort_path: Path,
    ontology_path: Path,
    source_cases_root: Path,
    output_dir: Path,
    profile_path: Path,
    *,
    created_utc: str,
) -> dict[str, Any]:
    cohort_path = Path(cohort_path)
    ontology_path = Path(ontology_path)
    source_cases_root = Path(source_cases_root)
    output_dir = Path(output_dir)
    profile_path = Path(profile_path)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Benchmark output must be new or empty: {output_dir}")
    if profile_path.exists():
        raise FileExistsError(f"Refusing to overwrite cost profile: {profile_path}")

    cohort = load_json(cohort_path)
    ontology = load_json(ontology_path)
    if cohort.get("unseen_boundary", {}).get("source_C13_plus") != "sealed":
        raise ValueError("C13+ must remain sealed")
    ontology_types = {row["action_type"] for row in ontology.get("actions", [])}
    if not EXECUTABLE_ACTION_TYPES <= ontology_types:
        raise ValueError("Ontology does not cover every executable replay action type")

    cases_output = output_dir / "cases"
    cases_output.mkdir(parents=True, exist_ok=True)
    profile_entries: list[dict[str, Any]] = []
    case_manifest: list[dict[str, Any]] = []
    for cohort_case in cohort.get("cases", []):
        source_case_id = str(cohort_case["source_case_id"])
        source_dir = source_cases_root / source_case_id
        if not source_dir.is_dir():
            raise FileNotFoundError(f"Source case unavailable: {source_dir}")
        config_path = source_dir / "case_config.json"
        claims_path = source_dir / "evidence_claims.json"
        actions_path = source_dir / "acquisition_actions.json"
        config = load_json(config_path)
        actions = load_json(actions_path)
        if config.get("case_id") != source_case_id:
            raise ValueError(f"Source case ID mismatch: {source_dir}")
        executable_actions = [
            action
            for action in actions
            if action.get("action_type") in EXECUTABLE_ACTION_TYPES
        ]
        if not executable_actions:
            raise ValueError(f"No executable replay actions remain for {source_case_id}")

        artifacts = cohort_case.get("replay_artifacts", [])
        event_bytes = sum(
            int(row["size_bytes"])
            for row in artifacts
            if not str(row["path"]).endswith("nodes.jsonl")
        )
        node_bytes = sum(
            int(row["size_bytes"])
            for row in artifacts
            if str(row["path"]).endswith("nodes.jsonl")
        )
        case_full_scan_bytes = event_bytes + node_bytes
        replay_refs = [str(row["path"]) for row in artifacts]
        for action in executable_actions:
            raw_scan_bytes = scan_bytes_for_action(
                str(action["action_type"]), event_bytes, node_bytes
            )
            profile_entries.append(
                measurement_entry(
                    source_case_id,
                    action,
                    raw_scan_bytes,
                    case_full_scan_bytes,
                    replay_refs,
                )
            )

        view_dir = cases_output / source_case_id
        view_dir.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(config_path, view_dir / config_path.name)
        shutil.copyfile(claims_path, view_dir / claims_path.name)
        (view_dir / actions_path.name).write_text(
            json.dumps(executable_actions, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        case_manifest.append(
            {
                "canonical_case_id": cohort_case["canonical_case_id"],
                "source_case_id": source_case_id,
                "phase": cohort_case["phase"],
                "source_action_count": len(actions),
                "executable_action_count": len(executable_actions),
                "case_full_scan_bytes": case_full_scan_bytes,
                "source_files_sha256": {
                    path.name: file_sha256(path)
                    for path in (config_path, claims_path, actions_path)
                },
                "view_files_sha256": {
                    path.name: file_sha256(path)
                    for path in sorted(view_dir.iterdir())
                },
            }
        )

    profile = {
        "$schema": "../../data_schema/cost_profile.schema.json",
        "profile_id": "project05-replay-full-scan-equivalent-cost-v0.1",
        "version": "0.1.0",
        "status": "frozen",
        "regime": "measured",
        "created_utc": created_utc,
        "standard_ref": "04-progress/cost-action-construct-review-v0.1-20260718/construct-synthesis.md",
        "scope": {"case_ids": [row["source_case_id"] for row in case_manifest]},
        "scoring": {
            "method": "precomputed_continuous",
            "unit": "case_replay_full_scan_equivalent",
            "formula": "action_raw_scan_bytes / case_full_scan_bytes",
        },
        "actions": profile_entries,
        "notes": [
            "This is a frozen single-resource benchmark scenario, not a universal total-cost standard.",
            "Infeasible human-review and external-service actions are removed by hard constraint rather than assigned an arbitrary penalty.",
        ],
    }
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "benchmark_id": "project05-replay-resource-benchmark-v0.1",
        "version": "0.1.0",
        "status": "frozen_single_resource_scenario",
        "created_utc": created_utc,
        "case_count": len(case_manifest),
        "executable_action_count": len(profile_entries),
        "executable_action_types": sorted(EXECUTABLE_ACTION_TYPES),
        "excluded_action_types": sorted(ontology_types - EXECUTABLE_ACTION_TYPES),
        "cost_construct": "deterministic_replay_data_access_burden",
        "scalar_unit": "case_replay_full_scan_equivalent",
        "raw_resource_unit": "bytes",
        "inputs": {
            portable_path(cohort_path): file_sha256(cohort_path),
            portable_path(ontology_path): file_sha256(ontology_path),
        },
        "profile": {
            "path": portable_path(profile_path),
            "sha256": file_sha256(profile_path),
        },
        "cases": case_manifest,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cohort",
        type=Path,
        default=EXP / "governance" / "cohorts" / "real-case-cohort-v0.3.json",
    )
    parser.add_argument(
        "--ontology",
        type=Path,
        default=EXP / "governance" / "profiles" / "action-ontology-v0.3-real-only-draft.json",
    )
    parser.add_argument("--source-cases", type=Path, default=EXP / "real_cases")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--created-utc", required=True)
    args = parser.parse_args()
    manifest = build_benchmark(
        args.cohort,
        args.ontology,
        args.source_cases,
        args.output_dir,
        args.profile,
        created_utc=args.created_utc,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
