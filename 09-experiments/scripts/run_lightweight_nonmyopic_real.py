#!/usr/bin/env python3
"""Evaluate a public-information depth-2 planner on Project05 real cases.

The planner deliberately has no access to hidden or recoverable claim IDs. Its
second step is a public surrogate: an acquisition either produces one positive
feedback event and fills its declared coverage dimensions, or produces a
zero-yield feedback event. Both branches are weighted by the channel prior.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MVP_PATH = Path(__file__).with_name("cost_profile_runtime.py")
ENDPOINT_ADAPTER_PATH = Path(__file__).with_name("planner_runtime_adapter.py")
PLANNER = "project05_depth2_public"
DISCOUNT = 0.8
FAILURE_COST_WEIGHT = 1.0
BASELINES = ("project05_m2", PLANNER, "oracle_optimal")
DEFAULT_CASE_PREFIXES = ("C07", "C08", "C09", "C10")


def _load_mvp() -> Any:
    spec = importlib.util.spec_from_file_location("project05_run_mvp", MVP_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load governed cost runtime from {MVP_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MVP = _load_mvp()


def _load_endpoint_adapter() -> Any:
    spec = importlib.util.spec_from_file_location(
        "project05_depth2_runtime_adapter", ENDPOINT_ADAPTER_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load runtime adapter from {ENDPOINT_ADAPTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENDPOINT = _load_endpoint_adapter()
ENDPOINT_CONTRACT = ENDPOINT.load_contract()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def channel_prior(config: dict[str, Any], action: dict[str, Any]) -> float:
    channel = MVP.acquisition_channel(action)
    reliability = config.get("channel_reliability", {}).get(channel, 1.0)
    return min(1.0, max(0.0, float(reliability)))


def planner_config_for_channel_prior(
    execution_config: dict[str, Any], multiplier: float
) -> tuple[dict[str, Any], dict[str, Any]]:
    value = float(multiplier)
    if value < 0.0:
        raise ValueError("channel-prior multiplier must be nonnegative")
    execution_profile = {
        str(channel): float(reliability)
        for channel, reliability in (
            execution_config.get("channel_reliability", {}) or {}
        ).items()
    }
    planner_profile = {
        channel: round(min(1.0, max(0.0, reliability * value)), 12)
        for channel, reliability in execution_profile.items()
    }
    planner_config = deepcopy(execution_config)
    planner_config["channel_reliability"] = planner_profile
    return planner_config, {
        "channel_prior_multiplier": value,
        "channel_prior_scope": "planner_belief_only",
        "execution_channel_profile_sha256": canonical_sha256(execution_profile),
        "planner_channel_prior_sha256": canonical_sha256(planner_profile),
        "execution_channel_profile_held_constant": 1,
    }


def public_surrogate_state(
    state: dict[str, Any],
    action: dict[str, Any],
    success: bool,
) -> dict[str, Any]:
    """Return a copied public-state surrogate after one hypothetical action."""

    updated = deepcopy(state)
    cost = float(action.get("cost", 0.0))
    budget = updated.setdefault("budget", {})
    budget["budget_used"] = float(budget.get("budget_used", 0.0)) + cost
    budget["budget_remaining"] = max(
        0.0,
        float(budget.get("budget_remaining", 0.0)) - cost,
    )
    updated.setdefault("actions_taken", []).append(action["action_id"])
    updated.setdefault("action_feedback", []).append(
        {
            "action_id": action["action_id"],
            "action_type": action.get("action_type", ""),
            "recovered_count": int(success),
        }
    )

    if success:
        coverage = updated.setdefault("coverage", {})
        stage_coverage = coverage.setdefault("stage_coverage", {})
        evidence_coverage = coverage.setdefault("evidence_type_coverage", {})
        for stage in action.get("expected_stages", []):
            stage_coverage[stage] = 1.0
        for evidence_type in action.get("expected_evidence_types", []):
            evidence_coverage[evidence_type] = 1.0

        intended = set(action.get("intended_cti_node_ids", []))
        unmatched = updated.get("unmatched_cti_node_ids")
        if isinstance(unmatched, list):
            updated["unmatched_cti_node_ids"] = [
                node_id for node_id in unmatched if node_id not in intended
            ]
    return updated


def best_second_step_value(
    state: dict[str, Any],
    actions: list[dict[str, Any]],
) -> float:
    candidates = MVP.available_actions(
        actions,
        state.get("actions_taken", []),
        float(state.get("budget", {}).get("budget_remaining", 0.0)),
    )
    return max(
        (MVP.m2_action_score(action, state, actions) for action in candidates),
        default=0.0,
    )


def public_depth2_score(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    action: dict[str, Any],
) -> float:
    if MVP.is_stop_action(action):
        return 0.0

    immediate = MVP.m2_action_score(action, state, actions)
    reliability = channel_prior(config, action)
    success_state = public_surrogate_state(state, action, success=True)
    zero_yield_state = public_surrogate_state(state, action, success=False)
    future = (
        reliability * best_second_step_value(success_state, actions)
        + (1.0 - reliability) * best_second_step_value(zero_yield_state, actions)
    )
    failure_cost = (1.0 - reliability) * float(action.get("cost", 0.0))
    return immediate + DISCOUNT * future - FAILURE_COST_WEIGHT * failure_cost


def select_depth2_public(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Select using only action declarations, public state, and channel priors."""

    endpoint_view = ENDPOINT.build_runtime_view(
        config,
        state,
        actions,
        ENDPOINT_CONTRACT,
    )
    config = endpoint_view["config"]
    state = endpoint_view["state"]
    actions = endpoint_view["actions"]
    candidates = MVP.available_actions(
        actions,
        state.get("actions_taken", []),
        float(state.get("budget", {}).get("budget_remaining", 0.0)),
    )
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda action: (
            public_depth2_score(config, state, actions, action),
            int(MVP.is_stop_action(action)),
            -float(action.get("cost", 0.0)),
            str(action.get("action_id", "")),
        ),
    )


def execute_cases(
    case_dirs: list[Path],
    channel_prior_multiplier: float = 1.0,
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        config = MVP.load_json(case_dir / "case_config.json")
        claims = MVP.load_json(case_dir / "evidence_claims.json")
        actions = MVP.load_json(case_dir / "acquisition_actions.json")
        actions, cost_metadata = MVP.apply_cost_regime(
            actions,
            config["case_id"],
            cost_regime,
            cost_profile,
        )
        planner_config, prior_metadata = planner_config_for_channel_prior(
            config, channel_prior_multiplier
        )
        for strategy, intensity, seed in MVP.experiment_conditions(config):
            for planner in BASELINES:
                selector = None
                if planner == PLANNER:
                    selector = (
                        lambda cfg, st, acts, pc=planner_config: select_depth2_public(
                            pc, st, acts
                        )
                    )
                result, trace = MVP.run_episode(
                    config,
                    claims,
                    actions,
                    strategy,
                    intensity,
                    seed,
                    planner,
                    action_selector=selector,
                )
                result.update(prior_metadata)
                if cost_metadata is not None:
                    result.update(cost_metadata)
                result["channel_prior_consumed_by_planner"] = int(
                    planner == PLANNER
                )
                rows.append(result)
                traces.append(
                    {
                        "run_id": MVP.make_run_id(
                            config["case_id"], strategy, intensity, seed, planner
                        ),
                        "result": result,
                        "trace": trace,
                    }
                )
    return MVP.add_oracle_relative_metrics(rows), traces


def paired_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    key_fields = ("case_id", "mask_strategy", "mask_intensity", "seed")
    paired: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        paired.setdefault(key, {})[row["planner"]] = row

    wins = ties = losses = both_success = repairs = regressions = 0
    cost_differences: list[float] = []
    by_case: dict[str, list[float]] = {}
    for key, planners in paired.items():
        m2 = planners.get("project05_m2")
        depth2 = planners.get(PLANNER)
        if m2 is None or depth2 is None:
            continue
        m2_success = int(m2["reached_target"])
        depth2_success = int(depth2["reached_target"])
        repairs += int(depth2_success == 1 and m2_success == 0)
        regressions += int(depth2_success == 0 and m2_success == 1)
        if not (m2_success and depth2_success):
            continue
        both_success += 1
        difference = float(depth2["cost_to_target"]) - float(m2["cost_to_target"])
        cost_differences.append(difference)
        by_case.setdefault(str(key[0]), []).append(difference)
        wins += int(difference < 0)
        ties += int(difference == 0)
        losses += int(difference > 0)

    return {
        "paired_condition_count": len(paired),
        "both_success_count": both_success,
        "depth2_success_repairs": repairs,
        "depth2_success_regressions": regressions,
        "depth2_cost_wins": wins,
        "cost_ties": ties,
        "depth2_cost_losses": losses,
        "mean_cost_difference_depth2_minus_m2": (
            round(sum(cost_differences) / len(cost_differences), 4)
            if cost_differences
            else None
        ),
        "by_case_mean_cost_difference": {
            case_id: round(sum(values) / len(values), 4)
            for case_id, values in sorted(by_case.items())
        },
    }


def evaluation_manifest(
    case_dirs: list[Path],
    rows: list[dict[str, Any]],
    experiment_id: str,
    channel_prior_multiplier: float,
    output_hashes: dict[str, str],
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "experiment_id": experiment_id,
        "case_prefixes": [path.name.split("-", 1)[0] for path in case_dirs],
        "case_ids": sorted({row["case_id"] for row in rows}),
        "independent_case_count": len({row["case_id"] for row in rows}),
        "repeated_condition_count": len(
            {
                (
                    row["case_id"],
                    row["mask_strategy"],
                    row["mask_intensity"],
                    row["seed"],
                )
                for row in rows
            }
        ),
        "planners": list(BASELINES),
        "frozen_parameters": {
            "discount": DISCOUNT,
            "failure_cost_weight": FAILURE_COST_WEIGHT,
        },
        "information_boundary": "public_surrogate_state_and_channel_priors_only",
        "channel_prior_intervention": {
            "multiplier": float(channel_prior_multiplier),
            "scope": "planner_belief_only",
            "execution_reliability_source": "frozen_case_config",
            "execution_profile_held_constant": True,
            "consumed_by_planners": [PLANNER],
        },
        "statistical_unit": ENDPOINT_CONTRACT["document"]["statistical_unit"],
        "cost_regime": cost_regime,
        "cost_profile_identity_by_case": cost_profile_identities(
            case_dirs, cost_regime, cost_profile
        ),
        "endpoint_boundary": {
            **ENDPOINT.contract_metadata(ENDPOINT_CONTRACT),
            "hidden_outcome_invariance_tested": True,
            "declared_expected_effects_visible": True,
            "realized_outcomes_visible": False,
        },
        "input_sha256": {
            (case_dir / filename).resolve().relative_to(ROOT).as_posix(): sha256_file(
                (case_dir / filename).resolve()
            )
            for case_dir in case_dirs
            for filename in MVP.CASE_FILENAMES
        },
        "output_sha256": dict(sorted(output_hashes.items())),
        "run_mvp_sha256": sha256_file(MVP_PATH),
        "endpoint_adapter_sha256": sha256_file(ENDPOINT_ADAPTER_PATH),
        "runner_sha256": sha256_file(Path(__file__)),
        "all_experiments_complete": False,
        "paper_or_patent_gate": "closed_until_human_and_operational_gates_are_satisfied",
        "paper_or_patent_updated": False,
    }


def cost_profile_identities(
    case_dirs: list[Path],
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> dict[str, dict[str, str]]:
    identities: dict[str, dict[str, str]] = {}
    for case_dir in case_dirs:
        config = MVP.load_json(case_dir / "case_config.json")
        actions = MVP.load_json(case_dir / "acquisition_actions.json")
        actions, metadata = MVP.apply_cost_regime(
            actions, config["case_id"], cost_regime, cost_profile
        )
        identities[config["case_id"]] = MVP.cost_profile_identity(
            actions, config["case_id"], cost_regime, metadata
        )
    return identities


def write_traces(path: Path, traces: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(traces, ensure_ascii=False).encode("utf-8")
    path.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))


def resolve_case_dirs(
    cases_root: Path,
    case_prefixes: tuple[str, ...] = DEFAULT_CASE_PREFIXES,
) -> list[Path]:
    if not case_prefixes:
        raise ValueError("At least one case prefix is required")
    if len(set(case_prefixes)) != len(case_prefixes):
        raise ValueError(f"Duplicate case prefixes: {case_prefixes}")
    resolved: list[Path] = []
    for case_id in case_prefixes:
        matches = sorted(
            path
            for path in cases_root.glob(f"{case_id}*")
            if path.is_dir()
            and all((path / filename).is_file() for filename in MVP.CASE_FILENAMES)
        )
        if len(matches) != 1:
            raise FileNotFoundError(
                f"Expected one complete {case_id} directory under {cases_root}, "
                f"found {matches}"
            )
        resolved.append(matches[0])
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen public depth-2 planner on selected real cases."
    )
    parser.add_argument(
        "--cases-root",
        type=Path,
        default=ROOT / "09-experiments" / "real_cases",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "09-experiments" / "results" / "nonmyopic_real_v0.1",
    )
    parser.add_argument(
        "--case-prefixes",
        nargs="+",
        default=list(DEFAULT_CASE_PREFIXES),
        help="Case directory prefixes; defaults to C07 C08 C09 C10.",
    )
    parser.add_argument(
        "--experiment-id",
    )
    parser.add_argument(
        "--channel-prior-multiplier",
        type=float,
        default=1.0,
        help=(
            "Planner-belief multiplier only; execution channel reliability "
            "remains frozen to each case config."
        ),
    )
    parser.add_argument(
        "--cost-regime",
        choices=MVP.COST_REGIMES,
        default="legacy",
        help="Embedded legacy, built-in uniform, or frozen rubric/measured costs.",
    )
    parser.add_argument(
        "--cost-profile",
        type=Path,
        help="Frozen profile required for rubric/measured cost regimes.",
    )
    args = parser.parse_args()
    if args.cost_regime in {"rubric", "measured"} and args.cost_profile is None:
        parser.error(f"--cost-profile is required for --cost-regime {args.cost_regime}")
    if args.cost_regime in {"legacy", "uniform"} and args.cost_profile is not None:
        parser.error(f"--cost-profile is not valid for --cost-regime {args.cost_regime}")
    cost_profile = (
        MVP.load_cost_profile(args.cost_profile)
        if args.cost_profile is not None
        else None
    )
    if args.output_dir.exists() and (
        not args.output_dir.is_dir() or any(args.output_dir.iterdir())
    ):
        parser.error(
            "Depth-2 governance runs require a new or empty --output-dir; "
            "existing/frozen results are never overwritten"
        )

    case_prefixes = tuple(args.case_prefixes)
    experiment_id = args.experiment_id or (
        "project05-depth2-public-c07-c10-v0.1"
        if case_prefixes == DEFAULT_CASE_PREFIXES
        else "project05-depth2-public-"
        + "-".join(prefix.casefold() for prefix in case_prefixes)
        + "-frozen-transfer-v0.1"
    )
    case_dirs = resolve_case_dirs(args.cases_root, case_prefixes)

    rows, traces = execute_cases(
        case_dirs,
        channel_prior_multiplier=args.channel_prior_multiplier,
        cost_regime=args.cost_regime,
        cost_profile=cost_profile,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.output_dir / "nonmyopic_policy_results.csv"
    summary_path = args.output_dir / "nonmyopic_policy_summary.json"
    paired_path = args.output_dir / "nonmyopic_paired_summary.json"
    traces_path = args.output_dir / "nonmyopic_policy_traces.json.gz"
    manifest_path = args.output_dir / "evaluation_manifest.json"
    MVP.write_csv(results_path, rows)
    MVP.write_json(
        summary_path,
        MVP.summarize_stratified(rows),
    )
    MVP.write_json(
        paired_path,
        paired_summary(rows),
    )
    write_traces(traces_path, traces)
    output_hashes = {
        path.name: sha256_file(path)
        for path in (results_path, summary_path, paired_path, traces_path)
    }
    MVP.write_json(
        manifest_path,
        evaluation_manifest(
            case_dirs,
            rows,
            experiment_id,
            args.channel_prior_multiplier,
            output_hashes,
            args.cost_regime,
            cost_profile,
        ),
    )
    print(f"Wrote frozen evaluation to {args.output_dir}")


if __name__ == "__main__":
    main()
