#!/usr/bin/env python3
"""Build a leakage-controlled expected-effects profile from C01-C06 only."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "09-experiments"
MVP_PATH = Path(__file__).with_name("run_mvp.py")
DEFAULT_OUTPUT = (
    EXPERIMENT_ROOT
    / "governance"
    / "profiles"
    / "action-priors-development-derived-v0.1.json"
)
TRAIN_PREFIXES = ("C01", "C02", "C03", "C04", "C05", "C06")
APPLICATION_PREFIXES = ("C07", "C08", "C09", "C10", "C11", "C12")


def load_script(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MVP = load_script(MVP_PATH, "project05_action_prior_mvp")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(prefixes: tuple[str, ...]) -> list[Path]:
    roots = (EXPERIMENT_ROOT / "examples", EXPERIMENT_ROOT / "real_cases")
    output = []
    for prefix in prefixes:
        matches = [
            path
            for root in roots
            for path in root.glob(f"{prefix}*")
            if path.is_dir()
            and all((path / name).is_file() for name in MVP.CASE_FILENAMES)
        ]
        if len(matches) != 1:
            raise FileNotFoundError(f"Expected one {prefix} case; found {matches}")
        output.append(matches[0])
    return output


def one_step_observations(case_dirs: list[Path]) -> dict[str, list[tuple[float, float]]]:
    observations: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for case_dir in case_dirs:
        config = MVP.load_json(case_dir / "case_config.json")
        claims = MVP.load_json(case_dir / "evidence_claims.json")
        actions = MVP.load_json(case_dir / "acquisition_actions.json")
        all_ids = {claim["claim_id"] for claim in claims}
        node_count = max(1, len(config["cti_nodes"]))
        for strategy, intensity, seed in MVP.experiment_conditions(config):
            hidden = MVP.build_hidden_claims(
                config, claims, strategy, seed, intensity
            )
            visible = all_ids - hidden
            before_g = MVP.granularity_index(
                config, MVP.supportable_granularity(config, visible)
            )
            before_cov = len(MVP.covered_node_ids(config, visible)) / node_count
            for action in actions:
                recovered = set(action.get("recoverable_claim_ids", [])) & hidden
                after_visible = visible | recovered
                after_g = MVP.granularity_index(
                    config,
                    MVP.supportable_granularity(config, after_visible),
                )
                after_cov = (
                    len(MVP.covered_node_ids(config, after_visible)) / node_count
                )
                observations[action["action_type"]].append(
                    (float(max(0, after_g - before_g)), max(0.0, after_cov - before_cov))
                )
    return observations


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6)


def build() -> dict[str, Any]:
    train_dirs = resolve(TRAIN_PREFIXES)
    application_dirs = resolve(APPLICATION_PREFIXES)
    train_ids = [MVP.load_json(path / "case_config.json")["case_id"] for path in train_dirs]
    application_ids = [
        MVP.load_json(path / "case_config.json")["case_id"]
        for path in application_dirs
    ]
    if set(train_ids) & set(application_ids):
        raise ValueError("Training and application cases must be disjoint")

    observations = one_step_observations(train_dirs)
    summary = {
        action_type: {
            "observation_count": len(rows),
            "mean_granularity_gain": mean([row[0] for row in rows]),
            "mean_coverage_delta": mean([row[1] for row in rows]),
        }
        for action_type, rows in sorted(observations.items())
    }

    actions: list[dict[str, Any]] = []
    channel_priors: list[dict[str, Any]] = []
    for case_dir in application_dirs:
        config = MVP.load_json(case_dir / "case_config.json")
        case_id = config["case_id"]
        channel_priors.append(
            {
                "case_id": case_id,
                "channel_reliability": {
                    str(key): float(value)
                    for key, value in (config.get("channel_reliability", {}) or {}).items()
                },
                "provenance": "legacy_expert_prior_not_empirically_calibrated",
            }
        )
        for action in MVP.load_json(case_dir / "acquisition_actions.json"):
            action_type = action["action_type"]
            if action_type not in summary:
                raise ValueError(
                    f"No C01-C06 donor observations for action type {action_type!r}"
                )
            legacy = action.get("expected_effects", {}) or {}
            actions.append(
                {
                    "case_id": case_id,
                    "action_id": action["action_id"],
                    "action_type": action_type,
                    "expected_effects": {
                        "expected_granularity_gain": summary[action_type][
                            "mean_granularity_gain"
                        ],
                        "expected_uncertainty_reduction": float(
                            legacy.get("expected_uncertainty_reduction", 0.0)
                        ),
                        "expected_over_attribution_risk_reduction": float(
                            legacy.get("expected_over_attribution_risk_reduction", 0.0)
                        ),
                        "expected_conflict_resolution": float(
                            legacy.get("expected_conflict_resolution", 0.0)
                        ),
                        "expected_coverage_delta": summary[action_type][
                            "mean_coverage_delta"
                        ],
                    },
                    "provenance": {
                        "expected_granularity_gain": "development_measured_by_action_type",
                        "expected_uncertainty_reduction": "legacy_expert_prior",
                        "expected_over_attribution_risk_reduction": "legacy_expert_prior",
                        "expected_conflict_resolution": "legacy_expert_prior",
                        "expected_coverage_delta": "development_measured_by_action_type",
                    },
                }
            )

    all_dirs = train_dirs + application_dirs
    hashes = {
        (path / filename).relative_to(ROOT).as_posix(): sha256_file(path / filename)
        for path in all_dirs
        for filename in MVP.CASE_FILENAMES
    }
    return {
        "$schema": "../../data_schema/action_prior_profile.schema.json",
        "profile_id": "project05-action-priors-development-derived-v0.1",
        "version": "0.1.0",
        "status": "frozen_development_derived",
        "created_utc": "2026-07-13T16:00:00Z",
        "training_scope": {"case_ids": train_ids},
        "application_scope": {"case_ids": application_ids},
        "leakage_boundary": (
            "Only C01-C06 recoverable outcomes are used to estimate action-type means. "
            "No C07-C12 recoverable outcomes or planner results enter this profile. "
            "Means are conditional on successful reveal and are static proxies, not calibrated utilities."
        ),
        "training_summary": summary,
        "actions": actions,
        "case_channel_priors": channel_priors,
        "input_sha256": hashes,
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
                "training_cases": len(profile["training_scope"]["case_ids"]),
                "application_cases": len(profile["application_scope"]["case_ids"]),
                "application_actions": len(profile["actions"]),
                "action_types": profile["training_summary"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
