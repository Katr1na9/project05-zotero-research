"""Tests for the explicit STOP / degrade action."""

import importlib.util
import tempfile
import unittest
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


class StopActionPrimitiveTests(unittest.TestCase):
    def test_ensure_stop_action_is_idempotent(self):
        config = {"case_id": "T-stop"}
        actions = [{"action_id": "A1", "action_type": "other", "cost": 1}]
        once = run_mvp.ensure_stop_action(config, actions)
        twice = run_mvp.ensure_stop_action(config, once)
        self.assertEqual(1, sum(1 for a in once if run_mvp.is_stop_action(a)))
        self.assertEqual(len(once), len(twice))
        self.assertEqual(0, once[-1]["cost"])
        self.assertEqual("decision", run_mvp.acquisition_channel(once[-1]))


class StopPlannerTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "case_id": "T-stop",
            "target_granularity": "G3_campaign",
            "support_ceiling": "G3_campaign",
            "budget_total": 4,
            "cti_nodes": [
                {
                    "node_id": "N1",
                    "stage": "execution",
                    "required_claim_ids": ["E1"],
                    "critical": True,
                },
                {
                    "node_id": "N2",
                    "stage": "collection",
                    "required_claim_ids": ["E2"],
                    "critical": True,
                },
                {
                    "node_id": "N3",
                    "stage": "exfiltration",
                    "required_claim_ids": ["E3"],
                    "critical": True,
                },
            ],
            "cti_edges": [
                {"edge_id": "X1", "source": "N1", "target": "N2"},
                {"edge_id": "X2", "source": "N2", "target": "N3"},
            ],
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "discriminative_claim_ids": [],
            "stage_mask_tags": [],
        }
        self.claims = [
            {"claim_id": "E1", "source_type": "local_log", "tags": ["hideable"]},
            {"claim_id": "E2", "source_type": "local_log", "tags": ["hideable"]},
            {"claim_id": "E3", "source_type": "local_log", "tags": ["hideable"]},
        ]

    def test_m3a_stops_when_no_action_targets_remaining_gaps(self):
        actions = [
            {
                "action_id": "off-target",
                "action_type": "recover_network_summary",
                "cost": 2,
                "recoverable_claim_ids": [],
                "intended_cti_node_ids": [],
                "expected_effects": {},
                "status": "available",
            }
        ]
        actions = run_mvp.ensure_stop_action(self.config, actions)
        state = run_mvp.build_state(
            self.config,
            self.claims,
            actions,
            "stop-test",
            0,
            "random",
            0.5,
            11,
            set(),
            {"E1", "E2", "E3"},
            set(),
            [],
            0.0,
        )
        selected = run_mvp.select_action(
            "project05_m3a_gap_compat",
            self.config,
            self.claims,
            actions,
            state,
            set(),
            {"E1", "E2", "E3"},
            [],
            11,
        )
        self.assertTrue(run_mvp.is_stop_action(selected))

    def test_episode_records_explicit_stop_and_does_not_burn_budget(self):
        actions = [
            {
                "action_id": "expensive-miss",
                "action_type": "recover_network_summary",
                "cost": 3,
                "recoverable_claim_ids": [],
                "intended_cti_node_ids": [],
                "expected_effects": {
                    "expected_coverage_delta": 0,
                    "expected_uncertainty_reduction": 0,
                    "expected_granularity_gain": 0,
                    "expected_over_attribution_risk_reduction": 0,
                    "expected_conflict_resolution": 0,
                },
                "status": "available",
            }
        ]
        result, trace = run_mvp.run_episode(
            self.config,
            self.claims,
            actions,
            "random",
            1.0,
            11,
            "project05_m3a_gap_compat",
        )
        self.assertEqual(1, result["explicit_stop"])
        self.assertEqual(0.0, float(result["budget_used"]))
        self.assertIn(run_mvp.STOP_ACTION_ID, result["actions_taken"])
        self.assertEqual(1, trace[-1].get("explicit_stop", 0))

    def test_oracle_stops_when_channel_makes_recovery_impossible(self):
        config = {
            **self.config,
            "channel_reliability": {"network_telemetry": 0.0},
            "budget_total": 2,
        }
        actions = [
            {
                "action_id": "only-net",
                "action_type": "recover_network_summary",
                "cost": 2,
                "recoverable_claim_ids": ["E1", "E2", "E3"],
                "intended_cti_node_ids": ["N1", "N2", "N3"],
                "expected_effects": {},
                "status": "available",
            }
        ]
        result, _ = run_mvp.run_episode(
            config,
            self.claims,
            actions,
            "random",
            1.0,
            11,
            "oracle_optimal",
        )
        self.assertEqual(0, result["reached_target"])
        self.assertEqual(1, result["explicit_stop"])
        self.assertEqual(1, result["correct_degrade_stop"])
        self.assertEqual(1, result["correct_stop"])

    def test_m3b_prefers_stop_over_negative_utility_action(self):
        actions = run_mvp.ensure_stop_action(
            self.config,
            [
                {
                    "action_id": "pricey",
                    "action_type": "query_host_subgraph",
                    "cost": 4,
                    "recoverable_claim_ids": ["E1"],
                    "intended_cti_node_ids": ["N1"],
                    "expected_effects": {},
                    "status": "available",
                }
            ],
        )
        state = run_mvp.build_state(
            self.config,
            self.claims,
            actions,
            "m3b-stop",
            0,
            "random",
            0.5,
            11,
            set(),
            {"E1", "E2", "E3"},
            set(),
            [],
            0.0,
        )
        # Model that predicts near-zero success for every action.
        model = {
            "feature_columns": ["intended_critical_gap_overlap_count"],
            "means": {"intended_critical_gap_overlap_count": 0.0},
            "scales": {"intended_critical_gap_overlap_count": 1.0},
            "weights": [0.0],
            "bias": -8.0,
        }
        selected = run_m3b.select_model_action(
            self.config, state, actions, model, cost_penalty=0.5
        )
        self.assertTrue(run_mvp.is_stop_action(selected))

    def test_oracle_relative_marks_justified_degrade_when_oracle_also_fails(self):
        rows = [
            {
                "case_id": "T",
                "mask_strategy": "random",
                "mask_intensity": 0.6,
                "seed": 1,
                "planner": "oracle_optimal",
                "reached_target": 0,
                "cost_to_target": "",
                "actions_taken": "STOP",
                "explicit_stop": 1,
                "ceiling_violation": 0,
                "correct_stop": 1,
                "correct_degrade_stop": 1,
            },
            {
                "case_id": "T",
                "mask_strategy": "random",
                "mask_intensity": 0.6,
                "seed": 1,
                "planner": "project05_m3a_gap_compat",
                "reached_target": 0,
                "cost_to_target": "",
                "actions_taken": "STOP",
                "explicit_stop": 1,
                "ceiling_violation": 0,
                "correct_stop": 1,
                "correct_degrade_stop": 1,
            },
        ]
        enriched = run_mvp.add_oracle_relative_metrics(rows)
        by_planner = {row["planner"]: row for row in enriched}
        self.assertEqual(1, by_planner["project05_m3a_gap_compat"]["justified_degrade_stop"])
        self.assertEqual(0, by_planner["project05_m3a_gap_compat"]["premature_stop"])
        self.assertEqual(1, by_planner["project05_m3a_gap_compat"]["correct_stop"])


class ShouldStopInterventionTests(unittest.TestCase):
    def test_strips_outage_claims_from_reliable_fallbacks(self):
        config = {"case_id": "T", "channel_reliability": {"network_telemetry": 0.5}}
        actions = [
            {
                "action_id": "net",
                "action_type": "recover_network_summary",
                "cost": 2,
                "recoverable_claim_ids": ["E-c2"],
                "intended_cti_node_ids": ["N-c2"],
            },
            {
                "action_id": "fallback",
                "action_type": "cti_report_lookup",
                "acquisition_channel": "threat_intel",
                "cost": 3,
                "recoverable_claim_ids": ["E-c2", "E-other"],
                "intended_cti_node_ids": ["N-c2"],
            },
        ]
        _, modified, meta = run_m3b.apply_should_stop_intervention(
            config, actions, outage_channel="network_telemetry"
        )
        by_id = {action["action_id"]: action for action in modified}
        self.assertEqual(["E-c2"], by_id["net"]["recoverable_claim_ids"])
        self.assertEqual(["E-other"], by_id["fallback"]["recoverable_claim_ids"])
        self.assertEqual(["E-c2"], meta["outage_owned_claim_ids"])
        self.assertIn("fallback", meta["stripped_action_ids"])

    def test_intervention_makes_oracle_stop_on_outage(self):
        config = {
            "case_id": "T-should-stop",
            "target_granularity": "G3_campaign",
            "support_ceiling": "G3_campaign",
            "budget_total": 6,
            "channel_reliability": {"network_telemetry": 0.0},
            "cti_nodes": [
                {
                    "node_id": "N1",
                    "stage": "execution",
                    "required_claim_ids": ["E1"],
                    "critical": True,
                },
                {
                    "node_id": "N2",
                    "stage": "command_and_control",
                    "required_claim_ids": ["E2"],
                    "critical": True,
                },
                {
                    "node_id": "N3",
                    "stage": "exfiltration",
                    "required_claim_ids": ["E3"],
                    "critical": True,
                },
            ],
            "cti_edges": [
                {"edge_id": "X1", "source": "N1", "target": "N2"},
                {"edge_id": "X2", "source": "N2", "target": "N3"},
            ],
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "discriminative_claim_ids": [],
            "stage_mask_tags": [],
        }
        claims = [
            {"claim_id": "E1", "source_type": "local_log", "tags": ["hideable"]},
            {"claim_id": "E2", "source_type": "network_summary", "tags": ["hideable"]},
            {"claim_id": "E3", "source_type": "local_log", "tags": ["hideable"]},
        ]
        actions = [
            {
                "action_id": "host",
                "action_type": "query_host_subgraph",
                "cost": 2,
                "recoverable_claim_ids": ["E1", "E3"],
                "intended_cti_node_ids": ["N1", "N3"],
                "expected_effects": {},
                "status": "available",
            },
            {
                "action_id": "net",
                "action_type": "recover_network_summary",
                "cost": 2,
                "recoverable_claim_ids": ["E2"],
                "intended_cti_node_ids": ["N2"],
                "expected_effects": {},
                "status": "available",
            },
            {
                "action_id": "fallback",
                "action_type": "ioc_enrichment",
                "acquisition_channel": "threat_intel",
                "cost": 2,
                "recoverable_claim_ids": ["E2"],
                "intended_cti_node_ids": ["N2"],
                "expected_effects": {},
                "status": "available",
            },
        ]
        config, actions, meta = run_m3b.apply_should_stop_intervention(
            config, actions, outage_channel="network_telemetry"
        )
        self.assertGreater(meta["stripped_claim_count"], 0)
        result, _ = run_mvp.run_episode(
            config,
            claims,
            actions,
            "random",
            1.0,
            11,
            "oracle_optimal",
        )
        self.assertEqual(0, result["reached_target"])
        self.assertEqual(1, result["explicit_stop"])
        self.assertEqual(1, result["correct_degrade_stop"])

    def test_should_stop_stress_writes_results(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            report = run_m3b.run_should_stop_stress_experiment(
                root / "examples",
                root / "real_cases",
                output_dir,
                "label_resolves_critical_gap_node",
                0.1,
                ["project05_m3a_gap_compat", "oracle_optimal"],
            )
            self.assertEqual(
                "outage_plus_strip_reliable_fallbacks",
                report["intervention"],
            )
            self.assertGreater(report["outage_condition_count"], 0)
            self.assertIn("oracle_optimal", report["summary"])
            # Oracle should mostly fail to reach target under true should-stop.
            self.assertLess(
                report["summary"]["oracle_optimal"]["success_rate"],
                1.0,
            )
            self.assertTrue(
                (output_dir / "m3b_should_stop_stress_results.csv").is_file()
            )


if __name__ == "__main__":
    unittest.main()
