#!/usr/bin/env python3
"""Build the frozen real-only C01-C09 alias cohort without renaming source files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
DEFAULT_OUTPUT = EXP / "governance" / "cohorts" / "real-case-cohort-v0.3.json"
REAL_CASE_NAMES = [
    "C04-darpa-e3-fivedirections",
    "C05-darpa-e3-cadets",
    "C06-darpa-e3-cadets-0412",
    "C07-darpa-e5-theia-0515",
    "C08-darpa-e5-clearscope-0515",
    "C09-darpa-optc-sysclient0201-0923",
    "C10-darpa-optc-sysclient0351-0925",
    "C11-otrf-apt29-day1-scranton-nashua",
    "C12-witfoo-precinct6-f10c7270",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def artifact(
    path: Path,
    declared_sha256: str,
    declared_digest_source: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Replay artifact is unavailable: {path}")
    return {
        "path": relative_path(path),
        "sha256": declared_sha256.casefold(),
        "size_bytes": path.stat().st_size,
        "declared_digest_source": {
            "path": relative_path(declared_digest_source),
            "sha256": file_sha256(declared_digest_source),
        },
    }


def resolve_dataset_output(dataset_root: Path, declared_path: str) -> Path:
    path = Path(declared_path)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "09-experiments":
        return ROOT / path
    return dataset_root / path


def replay_artifacts() -> dict[str, list[dict[str, Any]]]:
    e3 = EXP / "real_data" / "darpa_tc_e3"
    e5 = EXP / "real_data" / "darpa_tc_e5"
    optc = EXP / "real_data" / "darpa_optc"
    otrf = EXP / "real_data" / "otrf_apt29"
    witfoo = EXP / "real_data" / "witfoo_precinct6"
    result: dict[str, list[dict[str, Any]]] = {}
    for source_number, canonical_number in zip((1, 2, 3), (1, 2, 3)):
        summary_path = e3 / "derived" / f"R{source_number:02d}_extraction_summary.json"
        summary = load_json(summary_path)
        result[f"C{canonical_number:02d}"] = [
            artifact(
                e3 / "extracted" / f"R{source_number:02d}" / "events.jsonl",
                summary["outputs"]["events_sha256"],
                summary_path,
            ),
            artifact(
                e3 / "extracted" / f"R{source_number:02d}" / "nodes.jsonl",
                summary["outputs"]["nodes_sha256"],
                summary_path,
            ),
        ]
    for source_number, canonical_number in ((4, 4), (5, 5)):
        summary_path = e5 / "derived" / f"R{source_number:02d}_extraction_summary.json"
        summary = load_json(summary_path)
        result[f"C{canonical_number:02d}"] = [
            artifact(
                resolve_dataset_output(e5, summary["output_path"]),
                summary["output_sha256"],
                summary_path,
            )
        ]
    for source_number, canonical_number in ((6, 6), (7, 7)):
        summary_path = optc / "derived" / f"R{source_number:02d}_extraction_summary.json"
        summary = load_json(summary_path)
        result[f"C{canonical_number:02d}"] = [
            artifact(
                resolve_dataset_output(optc, summary["output_path"]),
                summary["output_sha256"],
                summary_path,
            )
        ]
    otrf_manifest = load_json(otrf / "manifest.json")
    otrf_source = next(
        row
        for row in otrf_manifest["sources"]
        if row["source_id"] == "otrf_apt29_day1_host_events"
    )
    result["C08"] = [
        artifact(
            otrf / otrf_source["raw_target"],
            otrf_source["sha256"],
            otrf / "manifest.json",
        )
    ]
    witfoo_lock = load_json(witfoo / "c12_case_compile_lock_v0.1.json")
    incident_id = witfoo_lock["selected_incident_id"]
    result["C09"] = [
        artifact(
            witfoo / "raw" / "graphs" / f"{incident_id}.graphml",
            witfoo_lock["input_integrity"]["graphml_sha256"],
            witfoo / "c12_case_compile_lock_v0.1.json",
        )
    ]
    return result


def build_cohort(created_utc: str = "2026-07-18T00:00:00Z") -> dict[str, Any]:
    replay = replay_artifacts()
    cases = []
    for canonical_number, source_name in enumerate(REAL_CASE_NAMES, start=1):
        canonical_id = f"C{canonical_number:02d}"
        case_dir = EXP / "real_cases" / source_name
        config_path = case_dir / "case_config.json"
        config = load_json(config_path)
        cases.append(
            {
                "canonical_case_id": canonical_id,
                "source_case_id": config["case_id"],
                "source_case_path": relative_path(case_dir),
                "source_case_config_sha256": file_sha256(config_path),
                "upstream_case_id": str(config.get("source_case_id", config["case_id"])),
                "phase": "calibration" if canonical_number <= 3 else "development",
                "replay_artifacts": replay[canonical_id],
            }
        )
    toy_exclusions = []
    for toy_number in range(1, 4):
        case_dir = EXP / "examples" / f"C{toy_number:02d}"
        config_path = case_dir / "case_config.json"
        config = load_json(config_path)
        toy_exclusions.append(
            {
                "source_case_id": config["case_id"],
                "source_case_path": relative_path(case_dir),
                "source_case_config_sha256": file_sha256(config_path),
                "reason": "no_replayable_original_event_data_for_operational_acquisition_cost",
                "permitted_use": "toy_unit_and_interface_tests_only",
                "formal_experiment_included": False,
                "paper_result_included": False,
            }
        )
    return {
        "cohort_id": "project05-real-case-cohort-v0.3",
        "version": "0.3.0",
        "status": "frozen",
        "created_utc": created_utc,
        "renaming_policy": "canonical_alias_only_preserve_source_ids_paths_and_files",
        "phase_policy": {
            "C01_C03": "calibration",
            "C04_C09": "development_repeat_validation",
        },
        "cases": cases,
        "toy_exclusions": toy_exclusions,
        "unseen_boundary": {
            "source_C13_plus": "sealed",
            "canonical_C10_plus": "unassigned_and_sealed",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--created-utc", default="2026-07-18T00:00:00Z")
    args = parser.parse_args()
    cohort = build_cohort(args.created_utc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(cohort, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "canonical_case_count": len(cohort["cases"]),
                "toy_exclusion_count": len(cohort["toy_exclusions"]),
                "calibration_case_count": sum(row["phase"] == "calibration" for row in cohort["cases"]),
                "development_case_count": sum(row["phase"] == "development" for row in cohort["cases"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
