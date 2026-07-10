import importlib.util
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


run_mvp = load_module("run_mvp", "run_mvp.py")
run_m3b = load_module("run_m3b", "run_m3b.py")


class M3bPolicyTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "case_id": "T-policy",
            "target_granularity": "G2_tactic_intent",
            "budget_total": 3,
            "discriminative_claim_ids": ["E-critical"],
            "cti_nodes": [
                {
                    "node_id": "N-critical",
                    "stage": "execution",
                    "required_claim_ids": ["E-critical"],
                    "critical": True,
                },
                {
                    "node_id": "N-other",
                    "stage": "collection",
                    "required_claim_ids": ["E-other"],
                    "critical": False,
                },
            ],
            "cti_edges": [
                {
                    "edge_id": "edge-1",
                    "source": "N-critical",
                    "target": "N-other",
                }
            ],
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
        }
        self.claims = [
            {"claim_id": "E-critical", "source_type": "local_log", "tags": ["hideable"]},
            {"claim_id": "E-other", "source_type": "network_summary", "tags": ["hideable"]},
        ]
        self.actions = [
            {
                "action_id": "critical-expensive",
                "action_type": "query_host_subgraph",
                "cost": 2,
                "recoverable_claim_ids": ["E-critical"],
                "intended_cti_node_ids": ["N-critical"],
                "expected_effects": {},
            },
            {
                "action_id": "other-cheap",
                "action_type": "recover_network_summary",
                "cost": 1,
                "recoverable_claim_ids": ["E-other"],
                "intended_cti_node_ids": ["N-other"],
                "expected_effects": {},
            },
        ]
        all_ids = {claim["claim_id"] for claim in self.claims}
        self.state = run_mvp.build_state(
            self.config,
            self.claims,
            self.actions,
            "T-policy-run",
            0,
            "discriminative",
            0.5,
            11,
            all_ids - {"E-critical"},
            {"E-critical"},
            set(),
            [],
            0.0,
        )
        self.model = {
            "feature_columns": ["intended_critical_gap_overlap_count"],
            "means": {"intended_critical_gap_overlap_count": 0.0},
            "scales": {"intended_critical_gap_overlap_count": 1.0},
            "weights": [4.0],
            "bias": 0.0,
        }

    def test_select_model_action_uses_public_features_when_hidden_outcomes_change(self):
        changed = deepcopy(self.actions)
        changed[0]["recoverable_claim_ids"] = ["E-other"]
        changed[1]["recoverable_claim_ids"] = ["E-critical"]

        first = run_m3b.select_model_action(
            self.config, self.state, self.actions, self.model, cost_penalty=0.1
        )
        second = run_m3b.select_model_action(
            self.config, self.state, changed, self.model, cost_penalty=0.1
        )

        self.assertEqual("critical-expensive", first["action_id"])
        self.assertEqual(first["action_id"], second["action_id"])

    def test_select_model_action_trades_predicted_utility_against_cost(self):
        selected = run_m3b.select_model_action(
            self.config, self.state, self.actions, self.model, cost_penalty=0.6
        )

        self.assertEqual("other-cheap", selected["action_id"])

    def test_reliability_posteriors_update_only_observed_group(self):
        feedback = [
            {"action_id": "critical-expensive", "recovered_count": 0},
            {"action_id": "other-cheap", "recovered_count": 1},
        ]

        posterior = run_m3b.reliability_posteriors(self.actions, feedback)

        self.assertEqual("host_forensics", run_m3b.reliability_group(self.actions[0]))
        self.assertEqual("network_telemetry", run_m3b.reliability_group(self.actions[1]))
        self.assertEqual(1.0, posterior["host_forensics"]["alpha"])
        self.assertEqual(2.0, posterior["host_forensics"]["beta"])
        self.assertAlmostEqual(1 / 3, posterior["host_forensics"]["mean"])
        self.assertAlmostEqual(2 / 3, posterior["network_telemetry"]["mean"])

    def test_channel_failure_transfers_within_channel_not_across(self):
        network_a = {
            "action_id": "net-a",
            "action_type": "recover_network_summary",
            "cost": 2,
            "recoverable_claim_ids": ["E-critical"],
            "intended_cti_node_ids": ["N-critical"],
            "expected_effects": {},
        }
        network_b = {
            "action_id": "net-b",
            "action_type": "recover_network_summary",
            "cost": 2,
            "recoverable_claim_ids": ["E-other"],
            "intended_cti_node_ids": ["N-other"],
            "expected_effects": {},
        }
        host = {
            "action_id": "host",
            "action_type": "query_host_subgraph",
            "cost": 3,
            "recoverable_claim_ids": ["E-critical"],
            "intended_cti_node_ids": ["N-critical"],
            "expected_effects": {},
        }
        actions = [network_a, network_b, host]
        posterior = run_m3b.reliability_posteriors(
            actions,
            [{"action_id": "net-a", "recovered_count": 0}],
        )

        self.assertAlmostEqual(1 / 3, posterior["network_telemetry"]["mean"])
        self.assertNotIn("host_forensics", posterior)
        self.assertEqual(
            run_m3b.reliability_group(network_a),
            run_m3b.reliability_group(network_b),
        )

    def test_reliability_selector_ignores_hidden_outcomes_before_execution(self):
        changed = deepcopy(self.actions)
        changed[0]["recoverable_claim_ids"] = ["E-other"]
        changed[1]["recoverable_claim_ids"] = ["E-critical"]

        first = run_m3b.select_reliability_model_action(
            self.config,
            self.state,
            self.actions,
            self.model,
            cost_penalty=0.1,
        )
        second = run_m3b.select_reliability_model_action(
            self.config,
            self.state,
            changed,
            self.model,
            cost_penalty=0.1,
        )

        self.assertEqual("critical-expensive", first["action_id"])
        self.assertEqual(first["action_id"], second["action_id"])

    def test_reliability_episode_records_posterior_only_after_feedback(self):
        actions = run_m3b.inject_matched_decoys(self.config, self.actions)

        result, trace = run_m3b.run_reliability_model_episode(
            self.config,
            self.claims,
            actions,
            "discriminative",
            0.5,
            11,
            self.model,
            cost_penalty=0.1,
        )

        self.assertEqual("project05_m3b_reliability_policy", result["planner"])
        self.assertEqual("zz_decoy_critical-expensive", trace[1]["action_id"])
        self.assertEqual(0.5, trace[1]["reliability_mean_before"])
        self.assertLess(trace[1]["reliability_mean_after"], 0.5)
        self.assertIn("reliability_adjusted_utility", trace[1])
        self.assertIn("predicted_gap_probability", trace[1])

    def test_model_episode_records_public_prediction_and_reaches_target(self):
        result, trace = run_m3b.run_model_episode(
            self.config,
            self.claims,
            self.actions,
            "discriminative",
            0.5,
            11,
            self.model,
            cost_penalty=0.1,
        )

        self.assertEqual("project05_m3b_policy", result["planner"])
        self.assertEqual(1, result["reached_target"])
        self.assertEqual("critical-expensive", trace[1]["action_id"])
        self.assertGreater(trace[1]["predicted_probability"], 0.5)
        self.assertIn("model_utility", trace[1])

    def test_policy_evaluation_compares_model_against_named_baseline(self):
        rows, summary = run_m3b.evaluate_policy_case_dirs(
            [(self.config, self.claims, self.actions)],
            self.model,
            cost_penalty=0.1,
            baseline_planners=["coverage_greedy"],
            conditions=[("discriminative", 0.5, 11)],
        )

        self.assertEqual(
            {"project05_m3b_policy", "coverage_greedy"},
            {row["planner"] for row in rows},
        )
        self.assertEqual(1, summary["project05_m3b_policy"]["runs"])

    def test_matched_decoy_keeps_public_features_but_has_no_recovery(self):
        augmented = run_m3b.inject_matched_decoys(self.config, self.actions)
        original = self.actions[0]
        decoy = next(
            action for action in augmented if action["action_id"] == "zz_decoy_critical-expensive"
        )

        self.assertEqual(
            run_m3b.feature_row(self.config, self.state, original),
            run_m3b.feature_row(self.config, self.state, decoy),
        )
        self.assertEqual([], decoy["recoverable_claim_ids"])
        self.assertEqual(self.actions, augmented[: len(self.actions)])

    def test_repeated_matched_decoys_keep_public_features(self):
        augmented = run_m3b.inject_matched_decoys(
            self.config,
            self.actions,
            copies_per_action=2,
        )
        decoys = [
            action
            for action in augmented
            if action["action_id"].startswith("zz_decoy_")
        ]

        self.assertEqual(
            {"zz_decoy_01_critical-expensive", "zz_decoy_02_critical-expensive"},
            {action["action_id"] for action in decoys},
        )
        for decoy in decoys:
            self.assertEqual([], decoy["recoverable_claim_ids"])
            self.assertEqual(
                run_m3b.feature_row(self.config, self.state, self.actions[0]),
                run_m3b.feature_row(self.config, self.state, decoy),
            )

    def test_policy_experiment_writes_matched_episode_outputs(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            report = run_m3b.run_policy_experiment(
                root / "examples",
                root / "real_cases",
                output_dir,
                "label_resolves_critical_gap_node",
                cost_penalty=0.1,
                baseline_planners=["coverage_greedy", "oracle_optimal"],
            )

            self.assertIn("project05_m3b_policy", report["summary"])
            self.assertTrue((output_dir / "m3b_policy_results.csv").is_file())
            self.assertTrue((output_dir / "m3b_policy_summary.json").is_file())

    def test_decoy_stress_experiment_writes_a_separate_negative_control(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            report = run_m3b.run_decoy_stress_experiment(
                root / "examples",
                root / "real_cases",
                output_dir,
                "label_resolves_critical_gap_node",
                cost_penalty=0.1,
                baseline_planners=["project05_m3a_gap_compat", "oracle_optimal"],
            )

            self.assertEqual("matched_zero_yield_critical_action", report["intervention"])
            self.assertTrue((output_dir / "m3b_decoy_stress_results.csv").is_file())
            self.assertIn("oracle_optimal", report["summary"])

    def test_reliability_stress_writes_adaptive_and_static_results(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            report = run_m3b.run_reliability_decoy_stress_experiment(
                root / "examples",
                root / "real_cases",
                output_dir,
                "label_resolves_critical_gap_node",
                0.1,
                [
                    "coverage_greedy",
                    "project05_m2",
                    "project05_m3a_gap_compat",
                    "oracle_optimal",
                ],
                copies_per_action=2,
            )

            self.assertIn("project05_m3b_reliability_policy", report["summary"])
            self.assertIn("project05_m3b_policy", report["summary"])
            self.assertTrue(
                (output_dir / "m3b_reliability_decoy_stress_results.csv").is_file()
            )

    def test_channel_outage_stress_filters_to_offline_seeds(self):
        root = Path(__file__).resolve().parents[1]
        config = run_mvp.load_json(
            root / "real_cases" / "C04-darpa-e3-fivedirections" / "case_config.json"
        )
        conditions = run_m3b.channel_outage_conditions(config, "network_telemetry")
        self.assertTrue(conditions)
        for _, _, seed in conditions:
            self.assertFalse(
                run_mvp.channel_is_up(config, "network_telemetry", seed)
            )

    def test_channel_outage_stress_writes_results(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            report = run_m3b.run_channel_outage_stress_experiment(
                root / "examples",
                root / "real_cases",
                output_dir,
                "label_resolves_critical_gap_node",
                0.1,
                ["project05_m3a_gap_compat", "oracle_optimal"],
            )

            self.assertEqual("realised_channel_outage", report["intervention"])
            self.assertGreater(report["outage_condition_count"], 0)
            self.assertIn("project05_m3b_reliability_policy", report["summary"])
            self.assertTrue(
                (output_dir / "m3b_channel_outage_stress_results.csv").is_file()
            )


if __name__ == "__main__":
    unittest.main()
