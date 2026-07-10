"""Tests for the acquisition-channel reliability mechanism (P0-#1 fix).

These tests pin down the property that broke the earlier "feature leak":
an action's public *declared* target (``intended_cti_node_ids``) is no longer a
perfect predictor of what the action actually recovers, because the collection
channel that fulfils the action can be offline for an episode. They also assert
the oracle-optimality invariants that must hold no matter how channels behave.
"""

import importlib.util
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


run_mvp = load_module("run_mvp", "run_mvp.py")
run_m3b = load_module("run_m3b", "run_m3b.py")

CASE_DIRS = [
    ROOT / "examples" / "C01",
    ROOT / "examples" / "C02",
    ROOT / "examples" / "C03",
    ROOT / "real_cases" / "C04-darpa-e3-fivedirections",
    ROOT / "real_cases" / "C05-darpa-e3-cadets",
    ROOT / "real_cases" / "C06-darpa-e3-cadets-0412",
]


def first_seed(config, channel, online):
    for seed in range(200):
        if run_mvp.channel_is_up(config, channel, seed) is online:
            return seed
    raise AssertionError(f"no {'up' if online else 'down'} seed found for {channel}")


class ChannelPrimitiveTests(unittest.TestCase):
    def test_channel_derived_from_action_type_or_explicit_override(self):
        self.assertEqual(
            "network_telemetry",
            run_mvp.acquisition_channel({"action_type": "recover_network_summary"}),
        )
        self.assertEqual(
            "host_forensics",
            run_mvp.acquisition_channel({"action_type": "query_host_subgraph"}),
        )
        self.assertEqual(
            "threat_intel",
            run_mvp.acquisition_channel(
                {
                    "action_type": "recover_network_summary",
                    "acquisition_channel": "threat_intel",
                }
            ),
        )

    def test_reliability_defaults_to_one_without_a_profile(self):
        self.assertEqual(1.0, run_mvp.channel_reliability({}, "network_telemetry"))
        self.assertEqual(
            0.5,
            run_mvp.channel_reliability(
                {"channel_reliability": {"network_telemetry": 0.5}},
                "network_telemetry",
            ),
        )

    def test_channel_up_is_deterministic_and_respects_extremes(self):
        config = {
            "case_id": "T",
            "channel_reliability": {"flaky": 0.5, "dead": 0.0},
        }
        self.assertTrue(
            all(run_mvp.channel_is_up(config, "reliable", s) for s in range(50))
        )
        self.assertFalse(
            any(run_mvp.channel_is_up(config, "dead", s) for s in range(50))
        )
        self.assertEqual(
            run_mvp.channel_is_up(config, "flaky", 11),
            run_mvp.channel_is_up(config, "flaky", 11),
        )
        draws = {run_mvp.channel_is_up(config, "flaky", s) for s in range(50)}
        self.assertEqual({True, False}, draws)


class RealizedRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "case_id": "T",
            "channel_reliability": {"network_telemetry": 0.5},
        }
        self.action = {
            "action_type": "recover_network_summary",
            "recoverable_claim_ids": ["E1", "E2"],
        }

    def test_recovers_when_channel_up_and_nothing_when_down(self):
        hidden = {"E1", "E2", "E3"}
        up_seed = first_seed(self.config, "network_telemetry", True)
        down_seed = first_seed(self.config, "network_telemetry", False)
        self.assertEqual(
            {"E1", "E2"},
            run_mvp.realized_recovery(self.config, self.action, hidden, up_seed),
        )
        self.assertEqual(
            set(),
            run_mvp.realized_recovery(self.config, self.action, hidden, down_seed),
        )

    def test_backward_compatible_when_no_profile_declared(self):
        config = {"case_id": "T"}
        hidden = {"E1", "E2", "E3"}
        for seed in range(10):
            self.assertEqual(
                {"E1", "E2"},
                run_mvp.realized_recovery(config, self.action, hidden, seed),
            )


class DeclaredVersusActualTests(unittest.TestCase):
    def setUp(self):
        case_dir = ROOT / "examples" / "C01"
        self.config = run_mvp.load_json(case_dir / "case_config.json")
        self.claims = run_mvp.load_json(case_dir / "evidence_claims.json")
        self.actions = run_mvp.load_json(case_dir / "acquisition_actions.json")
        self.flaky = next(a for a in self.actions if a["action_id"] == "C01-AA-003")

    def test_flaky_action_declares_a_target_but_can_recover_nothing(self):
        self.assertEqual("network_telemetry", run_mvp.acquisition_channel(self.flaky))
        self.assertTrue(self.flaky["intended_cti_node_ids"])
        hidden = set(self.flaky["recoverable_claim_ids"])
        down_seed = first_seed(self.config, "network_telemetry", False)
        self.assertEqual(
            set(),
            run_mvp.realized_recovery(self.config, self.flaky, hidden, down_seed),
        )

    def test_counterfactual_label_follows_realised_channel_outcome(self):
        all_ids = {claim["claim_id"] for claim in self.claims}
        hidden = set(self.flaky["recoverable_claim_ids"])
        visible = all_ids - hidden
        up_seed = first_seed(self.config, "network_telemetry", True)
        down_seed = first_seed(self.config, "network_telemetry", False)
        up = run_m3b.counterfactual_labels(
            self.config, visible, hidden, self.flaky, up_seed
        )
        down = run_m3b.counterfactual_labels(
            self.config, visible, hidden, self.flaky, down_seed
        )
        self.assertEqual(1, up["label_yield_positive"])
        self.assertEqual(0, down["label_yield_positive"])

    def test_feature_row_exposes_channel_prior_reliability(self):
        self.assertIn("channel_prior_reliability", run_m3b.FEATURE_COLUMNS)
        state = run_mvp.build_state(
            self.config,
            self.claims,
            self.actions,
            "channel-feature",
            0,
            "random",
            0.4,
            11,
            {claim["claim_id"] for claim in self.claims},
            set(),
            set(),
            [],
            0.0,
        )
        row = run_m3b.feature_row(self.config, state, self.flaky)
        self.assertEqual(0.5, row["channel_prior_reliability"])


class OracleInvariantTests(unittest.TestCase):
    """Invariants that must hold under channel gating for every case."""

    def test_oracle_stays_a_cost_lower_bound_and_a_feasibility_upper_bound(self):
        for case_dir in CASE_DIRS:
            with self.subTest(case=case_dir.name):
                rows, _ = run_mvp.execute_case(case_dir)

                regrets = [
                    float(row["cost_regret_vs_oracle"])
                    for row in rows
                    if row["planner"] != "full_evidence"
                    and row["cost_regret_vs_oracle"] != ""
                ]
                self.assertTrue(regrets)
                self.assertGreaterEqual(min(regrets), 0.0)

                by_condition = defaultdict(dict)
                for row in rows:
                    key = (row["mask_strategy"], row["mask_intensity"], row["seed"])
                    by_condition[key][row["planner"]] = int(row["reached_target"])
                for key, reached in by_condition.items():
                    oracle_reached = reached.get("oracle_optimal", 0)
                    for planner, planner_reached in reached.items():
                        if planner in ("oracle_optimal", "full_evidence"):
                            continue
                        # No planner can reach the target unless the exact oracle
                        # (which sees realised channel states) also can.
                        self.assertLessEqual(
                            planner_reached,
                            oracle_reached,
                            f"{planner} beat oracle feasibility in "
                            f"{case_dir.name} {key}",
                        )

                oracle_success = [
                    int(row["reached_target"])
                    for row in rows
                    if row["planner"] == "oracle_optimal"
                ]
                self.assertTrue(oracle_success)
                self.assertGreater(
                    sum(oracle_success),
                    0,
                    f"oracle never reached target in {case_dir.name}",
                )


if __name__ == "__main__":
    unittest.main()
