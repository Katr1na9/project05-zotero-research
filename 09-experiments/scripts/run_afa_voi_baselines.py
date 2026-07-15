#!/usr/bin/env python3
"""Run public-information AFA value-of-information baselines on selected cases.

These are task adapters for the generic AFA objective family, not official
implementations of NOCTA or WinRegRL. They deliberately use no hidden claim or
realized channel fields.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import itertools
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MVP_PATH = Path(__file__).with_name("run_mvp.py")
ENDPOINT_ADAPTER_PATH = Path(__file__).with_name("afa_endpoint_adapter.py")
MYOPIC = "afa_voi_myopic"
ROLLOUT = "afa_voi_rollout_h3"
ROLLOUT_HORIZON = 3
PLANNERS = ("project05_m2", MYOPIC, ROLLOUT, "oracle_optimal")
DEFAULT_CASE_PREFIXES = ("C07", "C08", "C09", "C10")


def _load_mvp() -> Any:
    spec = importlib.util.spec_from_file_location("project05_afa_mvp", MVP_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load simulator from {MVP_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_endpoint_adapter() -> Any:
    spec = importlib.util.spec_from_file_location(
        "project05_afa_endpoint_adapter", ENDPOINT_ADAPTER_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load AFA endpoint adapter from {ENDPOINT_ADAPTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MVP = _load_mvp()
ENDPOINT = _load_endpoint_adapter()
ENDPOINT_CONTRACT = ENDPOINT.load_contract()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def proxy_granularity(
    config: dict[str, Any], covered_nodes: set[str]
) -> str:
    nodes = config.get("cti_nodes", [])
    edges = config.get("cti_edges", [])
    known_nodes = {node["node_id"] for node in nodes}
    covered = covered_nodes & known_nodes
    covered_edges = {
        edge.get("edge_id", f"{edge.get('source')}->{edge.get('target')}")
        for edge in edges
        if edge.get("source") in covered and edge.get("target") in covered
    }
    node_coverage = len(covered) / max(1, len(nodes))
    edge_coverage = len(covered_edges) / max(1, len(edges))
    stages = {node.get("stage", "") for node in nodes if node["node_id"] in covered}
    critical = {node["node_id"] for node in nodes if node.get("critical")}
    thresholds = MVP.granularity_thresholds(config)

    if (
        node_coverage >= thresholds["g3_node_coverage"]
        and edge_coverage >= thresholds["g3_edge_coverage"]
        and critical <= covered
    ):
        granularity = "G3_campaign"
    elif (
        node_coverage >= thresholds["g2_node_coverage"]
        and len(stages) >= int(thresholds["g2_min_stages"])
    ):
        granularity = "G2_tactic_intent"
    elif node_coverage >= thresholds["g1_node_coverage"]:
        granularity = "G1_technique"
    else:
        granularity = "G0_unknown"

    ceiling = config.get("support_ceiling", config["granularity_order"][-1])
    if MVP.granularity_index(config, granularity) > MVP.granularity_index(config, ceiling):
        return ceiling
    return granularity


def public_terminal_potential(
    config: dict[str, Any], covered_nodes: set[str]
) -> float:
    nodes = config.get("cti_nodes", [])
    edges = config.get("cti_edges", [])
    known_nodes = {node["node_id"] for node in nodes}
    covered = covered_nodes & known_nodes
    covered_edges = sum(
        edge.get("source") in covered and edge.get("target") in covered
        for edge in edges
    )
    node_coverage = len(covered) / max(1, len(nodes))
    edge_coverage = covered_edges / max(1, len(edges))
    granularity = proxy_granularity(config, covered)
    rank = MVP.granularity_index(config, granularity)
    return rank + 0.5 * node_coverage + 0.5 * edge_coverage


def channel_prior(config: dict[str, Any], channel: str) -> float:
    value = config.get("channel_reliability", {}).get(channel, 1.0)
    return min(1.0, max(0.0, float(value)))


def planner_config_for_channel_prior(
    execution_config: dict[str, Any],
    multiplier: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a planner-only prior view while preserving execution reliability."""

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
        "execution_channel_profile_sha256": ENDPOINT.canonical_sha256(
            execution_profile
        ),
        "planner_channel_prior_sha256": ENDPOINT.canonical_sha256(
            planner_profile
        ),
        "execution_channel_profile_held_constant": 1,
    }


def expected_plan_net_value(
    config: dict[str, Any],
    state: dict[str, Any],
    plan: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> float:
    if not plan:
        return 0.0
    current_nodes = set(state.get("matched_cti_node_ids", []))
    current_utility = public_terminal_potential(config, current_nodes)
    channels = sorted({MVP.acquisition_channel(action) for action in plan})
    expected_terminal = 0.0

    for outcomes in itertools.product((False, True), repeat=len(channels)):
        channel_up = dict(zip(channels, outcomes))
        probability = 1.0
        for channel, is_up in channel_up.items():
            reliability = channel_prior(config, channel)
            probability *= reliability if is_up else 1.0 - reliability
        if probability == 0.0:
            continue
        covered = set(current_nodes)
        for action in plan:
            if channel_up[MVP.acquisition_channel(action)]:
                covered.update(action.get("intended_cti_node_ids", []))
        expected_terminal += probability * public_terminal_potential(config, covered)

    total_cost = sum(float(action.get("cost", 0.0)) for action in plan)
    budget_total = max(
        0.1,
        float(state.get("budget", {}).get("budget_total", config.get("budget_total", 1.0))),
    )
    return expected_terminal - current_utility - total_cost / budget_total


def best_rollout_value_for_first(
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
    first: dict[str, Any],
) -> float:
    remaining_budget = float(state["budget"]["budget_remaining"])
    remaining = [
        action
        for action in actions
        if action["action_id"] != first["action_id"]
        and not MVP.is_stop_action(action)
        and action["action_id"] not in set(state.get("actions_taken", []))
    ]
    best = expected_plan_net_value(config, state, (first,))
    for extra_count in range(1, ROLLOUT_HORIZON):
        for suffix in itertools.permutations(remaining, extra_count):
            plan = (first, *suffix)
            if sum(float(action["cost"]) for action in plan) <= remaining_budget:
                best = max(best, expected_plan_net_value(config, state, plan))
    return best


def select_afa_voi(
    planner: str,
    config: dict[str, Any],
    state: dict[str, Any],
    actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    endpoint_view = ENDPOINT.build_endpoint_view(
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
    if planner not in {MYOPIC, ROLLOUT}:
        raise ValueError(f"Unsupported AFA planner: {planner}")

    def value(action: dict[str, Any]) -> float:
        if MVP.is_stop_action(action):
            return 0.0
        if planner == MYOPIC:
            return expected_plan_net_value(config, state, (action,))
        return best_rollout_value_for_first(config, state, actions, action)

    return max(
        candidates,
        key=lambda action: (
            value(action),
            int(MVP.is_stop_action(action)),
            -float(action.get("cost", 0.0)),
            str(action.get("action_id", "")),
        ),
    )


def resolve_case_dirs(
    cases_root: Path,
    case_prefixes: tuple[str, ...] = DEFAULT_CASE_PREFIXES,
) -> list[Path]:
    if not case_prefixes:
        raise ValueError("At least one case prefix is required")
    if len(set(case_prefixes)) != len(case_prefixes):
        raise ValueError(f"Duplicate case prefixes: {case_prefixes}")
    resolved = []
    for prefix in case_prefixes:
        matches = sorted(
            path
            for path in cases_root.glob(f"{prefix}*")
            if path.is_dir()
            and all((path / filename).is_file() for filename in MVP.CASE_FILENAMES)
        )
        if len(matches) != 1:
            raise FileNotFoundError(
                f"Expected one complete {prefix} case under {cases_root}; found {matches}"
            )
        resolved.append(matches[0])
    return resolved


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
            for planner in PLANNERS:
                selector = None
                if planner in {MYOPIC, ROLLOUT}:
                    selector = lambda cfg, st, acts, name=planner, pc=planner_config: select_afa_voi(
                        name, pc, st, acts
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
                    planner in {MYOPIC, ROLLOUT}
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


def endpoint_case_metadata(
    case_dirs: list[Path],
    channel_prior_multiplier: float = 1.0,
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
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
        planner_config, _ = planner_config_for_channel_prior(
            config, channel_prior_multiplier
        )
        identities = ENDPOINT.embedded_profile_identity(
            planner_config,
            actions,
            ENDPOINT_CONTRACT["document"],
        )
        identities["cost"] = MVP.cost_profile_identity(
            actions,
            config["case_id"],
            cost_regime,
            cost_metadata,
        )
        metadata[config["case_id"]] = ENDPOINT.case_endpoint_metadata(
            planner_config,
            claims,
            actions,
            ENDPOINT_CONTRACT,
            identities,
        )
    return metadata


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


def evaluation_manifest(
    case_dirs: list[Path],
    rows: list[dict[str, Any]],
    experiment_id: str,
    channel_prior_multiplier: float,
    output_hashes: dict[str, str],
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    input_hashes = {
        (case_dir / filename).resolve().relative_to(ROOT).as_posix(): sha256_file(
            (case_dir / filename).resolve()
        )
        for case_dir in case_dirs
        for filename in MVP.CASE_FILENAMES
    }
    statistical_unit = ENDPOINT_CONTRACT["document"]["statistical_unit"]
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
        "planners": list(PLANNERS),
        "frozen_parameters": {"rollout_horizon": ROLLOUT_HORIZON},
        "information_boundary": "public_intent_and_channel_priors_only",
        "channel_prior_intervention": {
            "multiplier": float(channel_prior_multiplier),
            "scope": "planner_belief_only",
            "execution_reliability_source": "frozen_case_config",
            "execution_profile_held_constant": True,
            "consumed_by_planners": [MYOPIC, ROLLOUT],
        },
        "statistical_unit": statistical_unit,
        "cost_regime": cost_regime,
        "cost_profile_identity_by_case": cost_profile_identities(
            case_dirs, cost_regime, cost_profile
        ),
        "endpoint_contract": {
            "contract_id": ENDPOINT_CONTRACT["document"]["contract_id"],
            "version": ENDPOINT_CONTRACT["document"]["version"],
            "sha256": ENDPOINT_CONTRACT["sha256"],
            "runtime_allowlist_enforced": True,
        },
        "case_endpoint_metadata": endpoint_case_metadata(
            case_dirs,
            channel_prior_multiplier,
            cost_regime,
            cost_profile,
        ),
        "input_sha256": input_hashes,
        "output_sha256": dict(sorted(output_hashes.items())),
        "run_mvp_sha256": sha256_file(MVP_PATH),
        "endpoint_adapter_sha256": sha256_file(ENDPOINT_ADAPTER_PATH),
        "runner_sha256": sha256_file(Path(__file__)),
        "official_external_implementation_claimed": False,
        "all_experiments_complete": False,
        "paper_or_patent_gate": "closed_until_human_and_operational_gates_are_satisfied",
        "paper_or_patent_updated": False,
    }


def paired_against_m2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    key_fields = ("case_id", "mask_strategy", "mask_intensity", "seed")
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        grouped.setdefault(key, {})[row["planner"]] = row
    output: dict[str, Any] = {}
    for planner in (MYOPIC, ROLLOUT):
        wins = ties = losses = repairs = regressions = 0
        differences: list[float] = []
        for planners in grouped.values():
            m2 = planners["project05_m2"]
            candidate = planners[planner]
            m2_success = int(m2["reached_target"])
            candidate_success = int(candidate["reached_target"])
            repairs += int(candidate_success and not m2_success)
            regressions += int(m2_success and not candidate_success)
            if not (m2_success and candidate_success):
                continue
            difference = float(candidate["cost_to_target"]) - float(m2["cost_to_target"])
            differences.append(difference)
            wins += int(difference < 0)
            ties += int(difference == 0)
            losses += int(difference > 0)
        output[planner] = {
            "success_repairs_vs_m2": repairs,
            "success_regressions_vs_m2": regressions,
            "cost_wins_vs_m2": wins,
            "cost_ties_vs_m2": ties,
            "cost_losses_vs_m2": losses,
            "mean_cost_difference_vs_m2_on_joint_success": (
                round(sum(differences) / len(differences), 4)
                if differences
                else None
            ),
        }
    return output


def write_gzip_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    path.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen AFA-VOI adapters on selected real cases."
    )
    parser.add_argument(
        "--cases-root",
        type=Path,
        default=ROOT / "09-experiments" / "real_cases",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "09-experiments" / "results" / "afa_voi_c07_c10_v0.1",
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
            "AFA endpoint-contract runs require a new or empty --output-dir; "
            "existing/frozen results are never overwritten"
        )
    case_prefixes = tuple(args.case_prefixes)
    experiment_id = args.experiment_id or (
        "project05-afa-voi-c07-c10-v0.1"
        if case_prefixes == DEFAULT_CASE_PREFIXES
        else "project05-afa-voi-"
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
    results_path = args.output_dir / "afa_voi_policy_results.csv"
    summary_path = args.output_dir / "afa_voi_policy_summary.json"
    paired_path = args.output_dir / "afa_voi_paired_vs_m2.json"
    traces_path = args.output_dir / "afa_voi_policy_traces.json.gz"
    manifest_path = args.output_dir / "evaluation_manifest.json"
    MVP.write_csv(results_path, rows)
    MVP.write_json(
        summary_path,
        MVP.summarize_stratified(rows),
    )
    MVP.write_json(
        paired_path, paired_against_m2(rows)
    )
    write_gzip_json(traces_path, traces)
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
    print(f"Wrote frozen AFA-VOI evaluation to {args.output_dir}")


if __name__ == "__main__":
    main()
