import hashlib
import importlib.util
import inspect
import json
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"


def load_m3star(testcase: unittest.TestCase):
    path = SCRIPT_DIR / "run_m3star.py"
    testcase.assertTrue(path.is_file(), "M3* implementation module is missing")
    spec = importlib.util.spec_from_file_location("run_m3star", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_m3star_experiment(testcase: unittest.TestCase):
    path = SCRIPT_DIR / "run_m3star_experiment.py"
    testcase.assertTrue(path.is_file(), "M3* experiment runner is missing")
    spec = importlib.util.spec_from_file_location("run_m3star_experiment", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class M3StarPublicGraphTests(unittest.TestCase):
    def test_public_graph_snapshot_is_invariant_to_hidden_action_outcomes(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-boundary",
            "target_granularity": "G2_tactic_intent",
            "support_ceiling": "G3_campaign",
            "budget_total": 3,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N1", "stage": "execution", "critical": True},
                {"node_id": "N2", "stage": "collection", "critical": False},
            ],
            "cti_edges": [
                {"edge_id": "E12", "source": "N1", "target": "N2"},
            ],
            "channel_reliability": {"host_forensics": 0.8},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": ["N2"],
            "unmatched_cti_node_ids": ["N1"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": ["E12"],
            "coverage": {
                "cti_node_coverage": 0.5,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0, "collection": 1.0},
                "evidence_type_coverage": {"local_log": 0.0},
            },
            "budget": {
                "budget_total": 3.0,
                "budget_used": 0.0,
                "budget_remaining": 3.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A1"],
            "hidden_claim_ids": ["C1"],
            "run_id": "must-not-leak",
        }
        action = {
            "action_id": "A1",
            "case_id": config["case_id"],
            "action_type": "query_host_subgraph",
            "acquisition_channel": "host_forensics",
            "target": {"target_type": "host", "target_value": "h1"},
            "cost": 1.0,
            "intended_cti_node_ids": ["N1"],
            "expected_evidence_types": ["local_log"],
            "expected_stages": ["execution"],
            "expected_effects": {},
            "status": "available",
            "recoverable_claim_ids": ["C1"],
        }
        changed = deepcopy(action)
        changed["recoverable_claim_ids"] = ["C2", "C3"]

        first = m3star.public_graph_snapshot(config, state, [action])
        second = m3star.public_graph_snapshot(config, state, [changed])

        self.assertEqual(first, second)
        self.assertEqual(["N2"], first["covered_node_ids"])
        self.assertEqual(["N1"], first["unmatched_node_ids"])
        self.assertEqual([], m3star.forbidden_runtime_key_hits(first))

    def test_node_transition_features_use_graph_context_not_hidden_outcomes(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-features",
            "target_granularity": "G3_campaign",
            "support_ceiling": "G3_campaign",
            "budget_total": 4,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True},
                {"node_id": "N-covered", "stage": "discovery", "critical": False},
            ],
            "cti_edges": [
                {"edge_id": "E", "source": "N-gap", "target": "N-covered"},
            ],
            "channel_reliability": {"host_forensics": 0.75},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 1,
            "matched_cti_node_ids": ["N-covered"],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": ["E"],
            "coverage": {
                "cti_node_coverage": 0.5,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0, "discovery": 1.0},
                "evidence_type_coverage": {"local_log": 0.0},
            },
            "budget": {
                "budget_total": 4.0,
                "budget_used": 1.0,
                "budget_remaining": 3.0,
            },
            "actions_taken": ["A-prior"],
            "action_feedback": [
                {
                    "action_id": "A-prior",
                    "action_type": "query_host_subgraph",
                    "recovered_count": 0,
                }
            ],
            "remaining_action_ids": ["A-candidate"],
        }
        action = {
            "action_id": "A-candidate",
            "case_id": config["case_id"],
            "action_type": "query_host_subgraph",
            "acquisition_channel": "host_forensics",
            "target": {"target_type": "host", "target_value": "h1"},
            "cost": 2.0,
            "intended_cti_node_ids": ["N-gap"],
            "expected_evidence_types": ["local_log"],
            "expected_stages": ["execution"],
            "expected_effects": {
                "expected_granularity_gain": 1.0,
                "expected_uncertainty_reduction": 0.5,
            },
            "status": "available",
            "recoverable_claim_ids": ["C-secret"],
        }
        changed = deepcopy(action)
        changed["recoverable_claim_ids"] = []

        self.assertTrue(
            hasattr(m3star, "node_transition_feature_rows"),
            "M3* graph-conditioned transition features are missing",
        )
        first = m3star.node_transition_feature_rows(config, state, [action])
        second = m3star.node_transition_feature_rows(config, state, [changed])

        self.assertEqual(first, second)
        self.assertEqual(1, len(first))
        row = first[0]
        self.assertEqual("A-candidate", row["action_id"])
        self.assertEqual("N-gap", row["node_id"])
        self.assertEqual(1.0, row["node_is_intended"])
        self.assertEqual(1.0, row["node_is_critical"])
        self.assertEqual(1.0, row["successor_covered_ratio"])
        self.assertAlmostEqual(1 / 3, row["channel_feedback_mean"])
        self.assertEqual(
            set(m3star.GRAPH_FEATURE_COLUMNS)
            | set(m3star.ACTION_CONTEXT_FEATURE_COLUMNS),
            {key for key in row if key not in {"action_id", "node_id"}},
        )
        self.assertEqual(2.0, row["cost"])
        self.assertEqual(3.0, row["budget_remaining"])
        self.assertEqual(1.0, row["intended_gap_overlap_count"])
        self.assertEqual(1.0, row["intended_critical_gap_overlap_count"])

    def test_offline_transition_labels_are_joined_after_public_features(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-labels",
            "target_granularity": "G2_tactic_intent",
            "support_ceiling": "G3_campaign",
            "budget_total": 3,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {
                    "node_id": "N-gap",
                    "stage": "execution",
                    "critical": True,
                    "required_claim_ids": ["C-gap"],
                },
                {
                    "node_id": "N-visible",
                    "stage": "discovery",
                    "critical": False,
                    "required_claim_ids": ["C-visible"],
                },
            ],
            "cti_edges": [
                {"edge_id": "E", "source": "N-visible", "target": "N-gap"},
            ],
            "channel_reliability": {},
        }
        claims = [
            {"claim_id": "C-gap", "source_type": "local_log", "tags": ["hideable"]},
            {
                "claim_id": "C-visible",
                "source_type": "network_summary",
                "tags": ["hideable"],
            },
        ]

        def action(action_id, recoverable):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "host", "target_value": action_id},
                "cost": 1.0,
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
                "recoverable_claim_ids": recoverable,
            }

        actions = [
            action("A-hit", ["C-gap"]),
            action("A-zero", []),
        ]

        self.assertTrue(
            hasattr(m3star, "build_node_transition_rows_for_state"),
            "M3* offline transition-label builder is missing",
        )
        rows = m3star.build_node_transition_rows_for_state(
            config,
            claims,
            actions,
            visible_ids={"C-visible"},
            hidden_ids={"C-gap"},
            seed=11,
        )
        by_action = {row["action_id"]: row for row in rows}

        self.assertEqual(1, by_action["A-hit"]["label_node_resolved"])
        self.assertEqual(1, by_action["A-hit"]["label_yield_positive"])
        self.assertEqual(0, by_action["A-zero"]["label_node_resolved"])
        self.assertEqual(0, by_action["A-zero"]["label_yield_positive"])
        for row in rows:
            self.assertNotIn("recoverable_claim_ids", row)
            self.assertNotIn("hidden_claim_ids", row)
            self.assertEqual(
                set(m3star.GRAPH_FEATURE_COLUMNS)
                | set(m3star.ACTION_CONTEXT_FEATURE_COLUMNS),
                {
                    key
                    for key in row
                    if key
                    not in {
                        "case_id",
                        "action_id",
                        "node_id",
                        "label_node_resolved",
                        "label_yield_positive",
                        "label_reaches_target_after_action",
                    }
                },
            )


class M3StarPlanningTests(unittest.TestCase):
    def test_learned_cost_to_go_avoids_cheap_probe_with_expensive_repair(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-learned-cost-to-go",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 5,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True}
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 5.0,
                "budget_used": 0.0,
                "budget_remaining": 5.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A-cheap-probe", "A-reliable"],
        }

        def action(action_id, cost):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": "N-gap"},
                "cost": cost,
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }

        actions = [action("A-cheap-probe", 1.0), action("A-reliable", 3.0)]

        def transition(snapshot, candidate):
            return [
                {"probability": 0.05, "resolved_node_ids": []},
                {"probability": 0.95, "resolved_node_ids": ["N-gap"]},
            ]

        plan = m3star.plan_m3star_action(
            config,
            state,
            actions,
            transition,
            horizon=1,
            action_value_predictor=lambda snapshot, candidates: {
                candidate["action_id"]: 0.5 for candidate in candidates
            },
            action_reachability_predictor=lambda snapshot, candidates: {
                candidate["action_id"]: 0.95 for candidate in candidates
            },
            action_cost_predictor=lambda snapshot, candidates: {
                "A-cheap-probe": 5.0,
                "A-reliable": 3.0,
            },
        )

        self.assertEqual("A-reliable", plan["action_id"])
        self.assertEqual(3.0, plan["action_cost_to_go"])
        self.assertEqual(3.0, plan["expected_total_cost"])

        config["channel_reliability"] = {
            "network_telemetry": 0.5,
            "host_forensics": 1.0,
        }
        actions[0]["cost"] = 2.0
        actions[0]["action_type"] = "recover_network_summary"
        actions[0]["acquisition_channel"] = "network_telemetry"
        actions[0]["expected_effects"] = {
            "expected_granularity_gain": 1.0,
            "expected_uncertainty_reduction": 0.3,
            "expected_over_attribution_risk_reduction": 0.3,
            "expected_conflict_resolution": 0.0,
            "expected_coverage_delta": 0.4,
        }
        actions[1]["acquisition_channel"] = "host_forensics"
        actions[1]["expected_effects"] = {
            "expected_granularity_gain": 1.0,
            "expected_uncertainty_reduction": 0.4,
            "expected_over_attribution_risk_reduction": 0.4,
            "expected_conflict_resolution": 0.0,
            "expected_coverage_delta": 0.4,
        }
        dominance_corrected = m3star.plan_m3star_action(
            config,
            state,
            actions,
            transition,
            horizon=1,
            action_value_predictor=lambda snapshot, candidates: {
                candidate["action_id"]: 0.5 for candidate in candidates
            },
            action_reachability_predictor=lambda snapshot, candidates: {
                candidate["action_id"]: 0.95 for candidate in candidates
            },
            action_cost_predictor=lambda snapshot, candidates: {
                "A-cheap-probe": 2.0,
                "A-reliable": 3.0,
            },
        )

        self.assertEqual("A-reliable", dominance_corrected["action_id"])
        self.assertEqual(
            "A-cheap-probe",
            dominance_corrected["pre_dominance_action_id"],
        )
        self.assertEqual(1, dominance_corrected["dominance_substitution_applied"])
        self.assertEqual(
            "strict_equivalent_action_stochastic_dominance",
            dominance_corrected["dominance_selection_reason"],
        )

        actions[1]["intended_cti_node_ids"] = []
        non_equivalent = m3star.plan_m3star_action(
            config,
            state,
            actions,
            transition,
            horizon=1,
            action_value_predictor=lambda snapshot, candidates: {
                candidate["action_id"]: 0.5 for candidate in candidates
            },
            action_reachability_predictor=lambda snapshot, candidates: {
                candidate["action_id"]: 0.95 for candidate in candidates
            },
            action_cost_predictor=lambda snapshot, candidates: {
                "A-cheap-probe": 2.0,
                "A-reliable": 3.0,
            },
        )

        self.assertEqual("A-cheap-probe", non_equivalent["action_id"])
        self.assertEqual(0, non_equivalent["dominance_substitution_applied"])

    def test_reliability_gate_minimizes_cost_before_learned_tiebreaks(self):
        m3star = load_m3star(self)
        self.assertIn(
            "action_value_predictor",
            inspect.signature(m3star.plan_m3star_action).parameters,
        )
        config = {
            "case_id": "T-m3star-value-guidance",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 2,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True}
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 2.0,
                "budget_used": 0.0,
                "budget_remaining": 2.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A-cheap", "A-value"],
        }

        def action(action_id, cost):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": "N-gap"},
                "cost": cost,
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }

        actions = [action("A-cheap", 1.0), action("A-value", 2.0)]

        def transition(snapshot, candidate):
            return [
                {"probability": 0.05, "resolved_node_ids": []},
                {"probability": 0.95, "resolved_node_ids": ["N-gap"]},
            ]

        def value(snapshot, candidates):
            return {"A-cheap": 0.1, "A-value": 0.9}

        plan = m3star.plan_m3star_action(
            config,
            state,
            actions,
            transition,
            horizon=1,
            action_value_predictor=value,
        )

        self.assertEqual("A-cheap", plan["action_id"])
        self.assertEqual(0.1, plan["action_value_probability"])

        actions[1]["cost"] = 1.0
        equal_cost = m3star.plan_m3star_action(
            config,
            state,
            actions,
            transition,
            horizon=1,
            action_value_predictor=value,
        )

        self.assertEqual("A-value", equal_cost["action_id"])
        self.assertEqual(0.9, equal_cost["action_value_probability"])

        actions[1]["cost"] = 1.0

        def tied_value(snapshot, candidates):
            return {"A-cheap": 0.45, "A-value": 0.45}

        def reachability(snapshot, candidates):
            return {"A-cheap": 0.20, "A-value": 0.95}

        tie_broken = m3star.plan_m3star_action(
            config,
            state,
            actions,
            transition,
            horizon=1,
            action_value_predictor=tied_value,
            action_reachability_predictor=reachability,
        )

        self.assertEqual("A-value", tie_broken["action_id"])
        self.assertEqual(
            0.95,
            tie_broken["action_reachability_probability"],
        )

    def test_cost_normalized_value_rejects_large_premium_for_small_margin(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-value-cost-normalization",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 3,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True}
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 3.0,
                "budget_used": 0.0,
                "budget_remaining": 3.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A-cheap", "A-expensive"],
        }

        def action(action_id, cost):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": "N-gap"},
                "cost": cost,
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }

        actions = [action("A-cheap", 1.0), action("A-expensive", 3.0)]

        def transition(snapshot, candidate):
            return [
                {"probability": 0.05, "resolved_node_ids": []},
                {"probability": 0.95, "resolved_node_ids": ["N-gap"]},
            ]

        def value(snapshot, candidates):
            return {"A-cheap": 0.45, "A-expensive": 0.50}

        plan = m3star.plan_m3star_action(
            config,
            state,
            actions,
            transition,
            horizon=1,
            action_value_predictor=value,
        )

        self.assertEqual("A-cheap", plan["action_id"])
        self.assertAlmostEqual(0.45, plan["action_value_probability"])
        self.assertAlmostEqual(0.45, plan["action_value_cost_index"])

    def test_missing_support_ceiling_defaults_to_highest_granularity(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-default-ceiling",
            "target_granularity": "G1_technique",
            "support_ceiling": None,
            "budget_total": 1,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True}
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 1.0,
                "budget_used": 0.0,
                "budget_remaining": 1.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A-gap"],
        }
        action = {
            "action_id": "A-gap",
            "case_id": config["case_id"],
            "action_type": "query_host_subgraph",
            "acquisition_channel": "host_forensics",
            "target": {"target_type": "node", "target_value": "N-gap"},
            "cost": 1.0,
            "intended_cti_node_ids": ["N-gap"],
            "expected_evidence_types": ["local_log"],
            "expected_stages": ["execution"],
            "expected_effects": {},
            "status": "available",
        }

        snapshot = m3star.public_graph_snapshot(config, state, [action])
        self.assertEqual("G3_campaign", snapshot["support_ceiling"])

        plan = m3star.plan_m3star_action(
            config,
            state,
            [action],
            lambda snapshot, candidate: [
                {"probability": 1.0, "resolved_node_ids": ["N-gap"]}
            ],
            horizon=1,
        )

        self.assertEqual("A-gap", plan["action_id"])

    def test_nonmyopic_plan_selects_unlock_action_before_immediate_decoy(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-planning",
            "target_granularity": "G3_campaign",
            "support_ceiling": "G3_campaign",
            "budget_total": 2,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "granularity_thresholds": {
                "g3_node_coverage": 0.75,
                "g3_edge_coverage": 0.5,
                "g2_node_coverage": 0.5,
                "g2_min_stages": 2,
                "g1_node_coverage": 0.25,
            },
            "cti_nodes": [
                {"node_id": "N-base", "stage": "discovery", "critical": False},
                {"node_id": "N-unlock", "stage": "execution", "critical": False},
                {"node_id": "N-goal", "stage": "collection", "critical": True},
                {"node_id": "N-decoy", "stage": "collection", "critical": False},
            ],
            "cti_edges": [
                {"edge_id": "E1", "source": "N-base", "target": "N-unlock"},
                {"edge_id": "E2", "source": "N-unlock", "target": "N-goal"},
            ],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": ["N-base"],
            "unmatched_cti_node_ids": ["N-unlock", "N-goal", "N-decoy"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": ["E1", "E2"],
            "coverage": {
                "cti_node_coverage": 0.25,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 2.0,
                "budget_used": 0.0,
                "budget_remaining": 2.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A-unlock", "A-goal", "A-decoy"],
        }

        def action(action_id, intended_node, expected_gain):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": intended_node},
                "cost": 1.0,
                "intended_cti_node_ids": [intended_node],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {
                    "expected_granularity_gain": expected_gain,
                },
                "status": "available",
            }

        actions = [
            action("A-unlock", "N-unlock", 0.1),
            action("A-goal", "N-goal", 1.0),
            action("A-decoy", "N-decoy", 3.0),
        ]

        def learned_transition(snapshot, candidate):
            covered = set(snapshot["covered_node_ids"])
            action_id = candidate["action_id"]
            resolved = []
            if action_id == "A-unlock":
                resolved = ["N-unlock"]
            elif action_id == "A-goal" and "N-unlock" in covered:
                resolved = ["N-goal"]
            elif action_id == "A-decoy":
                resolved = ["N-decoy"]
            return [{"probability": 1.0, "resolved_node_ids": resolved}]

        self.assertTrue(
            hasattr(m3star, "plan_m3star_action"),
            "M3* non-myopic planner is missing",
        )
        plan = m3star.plan_m3star_action(
            config,
            state,
            actions,
            learned_transition,
            horizon=2,
        )

        self.assertEqual("A-unlock", plan["action_id"])
        self.assertEqual(["A-unlock", "A-goal"], plan["planned_action_ids"])
        self.assertEqual(1.0, plan["target_reach_probability"])
        self.assertEqual(2.0, plan["expected_total_cost"])
        self.assertIsNone(plan["myopic_action_id"])
        self.assertEqual("A-unlock", plan["nonmyopic_action_id"])
        self.assertEqual(
            "nonmyopic_plan_selected",
            plan["horizon_selection_reason"],
        )

    def test_counterfactual_rollout_shield_blocks_tradeoff_and_releases_dominance(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-horizon-shield",
            "target_granularity": "G3_campaign",
            "support_ceiling": "G3_campaign",
            "budget_total": 2,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "granularity_thresholds": {
                "g3_node_coverage": 1.0,
                "g3_edge_coverage": 0.5,
                "g2_node_coverage": 0.5,
                "g2_min_stages": 2,
                "g1_node_coverage": 0.25,
            },
            "cti_nodes": [
                {"node_id": "N-base", "stage": "discovery", "critical": False},
                {"node_id": "N-unlock", "stage": "execution", "critical": False},
                {"node_id": "N-goal", "stage": "collection", "critical": True},
            ],
            "cti_edges": [
                {"edge_id": "E1", "source": "N-base", "target": "N-unlock"},
                {"edge_id": "E2", "source": "N-unlock", "target": "N-goal"},
            ],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": ["N-base"],
            "unmatched_cti_node_ids": ["N-unlock", "N-goal"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": ["E1", "E2"],
            "coverage": {
                "cti_node_coverage": 1.0 / 3.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 2.0,
                "budget_used": 0.0,
                "budget_remaining": 2.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A-safe", "A-unlock", "A-goal"],
        }

        def action(action_id, intended):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": action_id},
                "cost": 1.0,
                "intended_cti_node_ids": intended,
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }

        actions = [
            action("A-safe", ["N-unlock", "N-goal"]),
            action("A-unlock", ["N-unlock"]),
            action("A-goal", ["N-goal"]),
        ]

        def learned_transition(snapshot, candidate):
            action_id = candidate["action_id"]
            if action_id == "A-safe":
                return [
                    {"probability": 0.6, "resolved_node_ids": []},
                    {
                        "probability": 0.4,
                        "resolved_node_ids": ["N-unlock", "N-goal"],
                    },
                ]
            if action_id == "A-unlock":
                return [
                    {"probability": 1.0, "resolved_node_ids": ["N-unlock"]}
                ]
            resolved = (
                ["N-goal"]
                if "N-unlock" in snapshot["covered_node_ids"]
                else []
            )
            return [{"probability": 1.0, "resolved_node_ids": resolved}]

        def action_value(snapshot, candidates):
            return {
                candidate["action_id"]: (
                    0.9 if candidate["action_id"] == "A-unlock" else 0.1
                )
                for candidate in candidates
            }

        original_best_plan = m3star._best_plan
        root_rollout_memos = []

        def audited_best_plan(*args, **kwargs):
            if args[2] == 2 and not args[0].get("actions_taken"):
                root_rollout_memos.append(
                    (kwargs.get("required_action_id"), id(args[4]))
                )
            return original_best_plan(*args, **kwargs)

        m3star._best_plan = audited_best_plan
        try:
            shielded = m3star.plan_m3star_action(
                config,
                state,
                actions,
                learned_transition,
                horizon=2,
                action_value_predictor=action_value,
            )
        finally:
            m3star._best_plan = original_best_plan
        unshielded = m3star.plan_m3star_action(
            config,
            state,
            actions,
            learned_transition,
            horizon=2,
            action_value_predictor=action_value,
            myopic_safety_shield=False,
        )
        actions[0]["cost"] = 2.0
        dominant = m3star.plan_m3star_action(
            config,
            state,
            actions,
            learned_transition,
            horizon=2,
            action_value_predictor=action_value,
        )

        self.assertEqual("A-safe", shielded["action_id"])
        self.assertEqual(2, len(root_rollout_memos))
        self.assertEqual(
            root_rollout_memos[0][1],
            root_rollout_memos[1][1],
            "H3 and forced-H1 rollouts must share the same search memo",
        )
        self.assertEqual("A-unlock", shielded["nonmyopic_action_id"])
        self.assertEqual(1, shielded["effective_horizon"])
        self.assertEqual(
            "counterfactual_rollout_shield",
            shielded["horizon_selection_reason"],
        )
        self.assertEqual(
            "A-safe",
            shielded["myopic_rollout_action_id"],
        )
        self.assertAlmostEqual(
            0.4,
            shielded["myopic_rollout_target_reach_probability"],
        )
        self.assertAlmostEqual(
            1.0,
            shielded["myopic_rollout_expected_total_cost"],
        )
        self.assertEqual("A-unlock", unshielded["action_id"])
        self.assertIsNone(unshielded["myopic_rollout_action_id"])
        self.assertEqual(
            "nonmyopic_plan_selected",
            unshielded["horizon_selection_reason"],
        )
        self.assertEqual("A-unlock", dominant["action_id"])
        self.assertEqual(2, dominant["effective_horizon"])
        self.assertEqual(
            "counterfactual_rollout_dominance",
            dominant["horizon_selection_reason"],
        )
        self.assertAlmostEqual(
            0.4,
            dominant["myopic_rollout_target_reach_probability"],
        )
        self.assertAlmostEqual(
            2.0,
            dominant["myopic_rollout_expected_total_cost"],
        )
        self.assertAlmostEqual(
            0.6,
            dominant["counterfactual_probability_delta"],
        )
        self.assertAlmostEqual(
            0.0,
            dominant["counterfactual_cost_delta"],
        )

    def test_chance_constraint_prefers_lower_cost_once_reliability_target_is_met(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-chance-constraint",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 2,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True}
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 2.0,
                "budget_used": 0.0,
                "budget_remaining": 2.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A-direct", "A-probe"],
        }

        def action(action_id):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": "N-gap"},
                "cost": 1.0,
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }

        actions = [action("A-direct"), action("A-probe")]

        def learned_transition(snapshot, candidate):
            if candidate["action_id"] == "A-probe":
                probability = 0.05
            elif "A-probe" in snapshot["actions_taken"]:
                probability = 0.95
            else:
                probability = 0.90
            return [
                {"probability": 1.0 - probability, "resolved_node_ids": []},
                {"probability": probability, "resolved_node_ids": ["N-gap"]},
            ]

        plan = m3star.plan_m3star_action(
            config,
            state,
            actions,
            learned_transition,
            horizon=2,
        )

        self.assertEqual("A-direct", plan["action_id"])
        self.assertGreaterEqual(
            plan["target_reach_probability"],
            m3star.DEFAULT_TARGET_REACH_THRESHOLD,
        )
        self.assertEqual(1, plan.get("effective_horizon"))
        self.assertAlmostEqual(1.0, plan["expected_total_cost"])
        self.assertEqual("A-direct", plan["myopic_action_id"])
        self.assertIsNone(plan["nonmyopic_action_id"])
        self.assertEqual(
            "myopic_threshold_sufficient",
            plan["horizon_selection_reason"],
        )

    def test_planner_memoizes_equivalent_reachable_states(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-memo",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 3,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True}
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 3.0,
                "budget_used": 0.0,
                "budget_remaining": 3.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A1", "A2", "A3"],
        }

        def action(action_id):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": "N-gap"},
                "cost": 1.0,
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }

        calls = 0

        def no_resolution(snapshot, candidate):
            nonlocal calls
            calls += 1
            return [{"probability": 1.0, "resolved_node_ids": []}]

        plan = m3star.plan_m3star_action(
            config,
            state,
            [action("A1"), action("A2"), action("A3")],
            no_resolution,
            horizon=3,
        )

        self.assertIsNone(plan["action_id"])
        self.assertLessEqual(calls, 12)

    def test_planner_batches_all_candidate_transition_predictions_per_state(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-batch",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 1,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True}
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 1.0,
                "budget_used": 0.0,
                "budget_remaining": 1.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A1", "A2"],
        }

        def action(action_id):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": "N-gap"},
                "cost": 1.0,
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }

        class BatchedPredictor:
            def __init__(self):
                self.batch_calls = 0
                self.scalar_calls = 0

            def __call__(self, snapshot, candidate):
                self.scalar_calls += 1
                return [{"probability": 1.0, "resolved_node_ids": []}]

            def predict_many(self, snapshot, candidates):
                self.batch_calls += 1
                return {
                    candidate["action_id"]: [
                        {"probability": 1.0, "resolved_node_ids": []}
                    ]
                    for candidate in candidates
                }

        predictor = BatchedPredictor()
        m3star.plan_m3star_action(
            config,
            state,
            [action("A1"), action("A2")],
            predictor,
            horizon=1,
        )

        self.assertEqual(1, predictor.batch_calls)
        self.assertEqual(0, predictor.scalar_calls)


class M3StarEpisodeTests(unittest.TestCase):
    def test_episode_replans_after_each_observation_and_audits_feedback_updates(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-episode",
            "target_granularity": "G3_campaign",
            "support_ceiling": "G3_campaign",
            "budget_total": 2,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "granularity_thresholds": {
                "g3_node_coverage": 1.0,
                "g3_edge_coverage": 1.0,
                "g2_node_coverage": 0.5,
                "g2_min_stages": 2,
                "g1_node_coverage": 0.25,
            },
            "cti_nodes": [
                {
                    "node_id": "N-base",
                    "stage": "discovery",
                    "critical": False,
                    "required_claim_ids": ["C-base"],
                },
                {
                    "node_id": "N-unlock",
                    "stage": "execution",
                    "critical": False,
                    "required_claim_ids": ["C-unlock"],
                },
                {
                    "node_id": "N-goal",
                    "stage": "collection",
                    "critical": True,
                    "required_claim_ids": ["C-goal"],
                },
            ],
            "cti_edges": [
                {"edge_id": "E1", "source": "N-base", "target": "N-unlock"},
                {"edge_id": "E2", "source": "N-unlock", "target": "N-goal"},
            ],
            "channel_reliability": {"host_forensics": 1.0},
        }
        claims = [
            {"claim_id": "C-base", "source_type": "network_summary", "tags": []},
            {"claim_id": "C-unlock", "source_type": "local_log", "tags": ["hideable"]},
            {"claim_id": "C-goal", "source_type": "local_log", "tags": ["hideable"]},
        ]

        def action(action_id, node_id, claim_id, stage):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": node_id},
                "cost": 1.0,
                "recoverable_claim_ids": [claim_id],
                "intended_cti_node_ids": [node_id],
                "expected_evidence_types": ["local_log"],
                "expected_stages": [stage],
                "expected_effects": {},
                "status": "available",
            }

        actions = [
            action("A-unlock", "N-unlock", "C-unlock", "execution"),
            action("A-goal", "N-goal", "C-goal", "collection"),
        ]

        def learned_transition(snapshot, candidate):
            covered = set(snapshot["covered_node_ids"])
            resolved = []
            if candidate["action_id"] == "A-unlock":
                resolved = ["N-unlock"]
            elif candidate["action_id"] == "A-goal" and "N-unlock" in covered:
                resolved = ["N-goal"]
            return [{"probability": 1.0, "resolved_node_ids": resolved}]

        self.assertTrue(
            hasattr(m3star, "run_m3star_episode"),
            "M3* receding-horizon episode runner is missing",
        )
        result, trace = m3star.run_m3star_episode(
            config,
            claims,
            actions,
            "random",
            1.0,
            11,
            learned_transition,
            horizon=2,
        )

        self.assertEqual(1, result["reached_target"])
        self.assertEqual("A-unlock|A-goal", result["actions_taken"])
        events = [event for event in trace if event["event"] == "action_taken"]
        self.assertEqual(2, len(events))
        first = events[0]["m3star_decision"]
        second = events[1]["m3star_decision"]
        self.assertEqual(["A-unlock", "A-goal"], first["planned_action_ids"])
        self.assertEqual(1.0, first["target_reach_probability"])
        self.assertEqual(2.0, first["expected_total_cost"])
        self.assertIsNone(first["myopic_action_id"])
        self.assertEqual("A-unlock", first["nonmyopic_action_id"])
        self.assertEqual(
            "nonmyopic_plan_selected",
            first["horizon_selection_reason"],
        )
        self.assertEqual(["A-goal"], second["planned_action_ids"])
        self.assertEqual(1.0, second["target_reach_probability"])
        self.assertEqual(1.0, second["expected_total_cost"])
        self.assertEqual("host_forensics", first["feedback_update"]["channel"])
        self.assertAlmostEqual(0.5, first["feedback_update"]["mean_before"])
        self.assertAlmostEqual(2 / 3, first["feedback_update"]["mean_after"])
        self.assertAlmostEqual(2 / 3, second["feedback_update"]["mean_before"])
        self.assertAlmostEqual(3 / 4, second["feedback_update"]["mean_after"])

    def test_episode_uses_explicit_audited_stop_when_no_plan_can_reach_target(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-stop",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 1,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {
                    "node_id": "N-gap",
                    "stage": "execution",
                    "critical": True,
                    "required_claim_ids": ["C-gap"],
                }
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        claims = [
            {"claim_id": "C-gap", "source_type": "local_log", "tags": ["hideable"]}
        ]
        actions = [
            {
                "action_id": "A-gap",
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": "N-gap"},
                "cost": 1.0,
                "recoverable_claim_ids": ["C-gap"],
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }
        ]

        def no_recovery(snapshot, candidate):
            return [{"probability": 1.0, "resolved_node_ids": []}]

        result, trace = m3star.run_m3star_episode(
            config,
            claims,
            actions,
            "random",
            1.0,
            17,
            no_recovery,
            horizon=1,
        )

        self.assertEqual(1, result["explicit_stop"])
        self.assertEqual("STOP", result["actions_taken"])
        self.assertEqual(0, result["ceiling_violation"])
        event = next(event for event in trace if event["event"] == "action_taken")
        decision = event["m3star_decision"]
        self.assertEqual("STOP", decision["selected_action_id"])
        self.assertEqual([], decision["planned_action_ids"])
        self.assertEqual(0.0, decision["target_reach_probability"])
        self.assertEqual(
            "no_positive_target_reach_plan",
            decision.get("stop_reason"),
        )

    def test_trained_transition_model_drives_episode_and_is_identified_in_audit(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-model-episode",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 1,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {
                    "node_id": "N-gap",
                    "stage": "execution",
                    "critical": True,
                    "required_claim_ids": ["C-gap"],
                }
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        claims = [
            {"claim_id": "C-gap", "source_type": "local_log", "tags": ["hideable"]}
        ]

        def action(action_id, intended, recoverable):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": action_id},
                "cost": 1.0,
                "recoverable_claim_ids": recoverable,
                "intended_cti_node_ids": intended,
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"] if intended else [],
                "expected_effects": {},
                "status": "available",
            }

        actions = [
            action("A-hit", ["N-gap"], ["C-gap"]),
            action("A-decoy", [], []),
        ]
        initial_state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {"local_log": 0.0},
            },
            "budget": {
                "budget_total": 1.0,
                "budget_used": 0.0,
                "budget_remaining": 1.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A-hit", "A-decoy"],
        }
        public_rows = m3star.node_transition_feature_rows(
            config,
            initial_state,
            actions,
        )
        rows_by_action = {row["action_id"]: row for row in public_rows}
        positive = {
            "case_id": "C-train-positive",
            **rows_by_action["A-hit"],
            "label_node_resolved": 1,
        }
        negative = {
            "case_id": "C-train-negative",
            **rows_by_action["A-decoy"],
            "label_node_resolved": 0,
        }
        training_rows = [positive.copy() for _ in range(12)] + [
            negative.copy() for _ in range(12)
        ]
        model = m3star.train_graph_transition_model(training_rows, boost_rounds=30)

        self.assertTrue(
            hasattr(m3star, "run_m3star_model_episode"),
            "M3* trained-model episode adapter is missing",
        )
        self.assertIn(
            "action_value_model",
            inspect.signature(m3star.run_m3star_model_episode).parameters,
        )

        class ConstantValueBooster:
            def predict(self, matrix):
                return [0.75] * matrix.num_row()

        class ConstantReachabilityBooster:
            def predict(self, matrix):
                return [0.80] * matrix.num_row()

        class ConstantCostBooster:
            def predict(self, matrix):
                return [1.0] * matrix.num_row()

        value_model = {
            "model_family": "m3star_graph_action_value_test_v0.1",
            "feature_columns": list(m3star.ACTION_VALUE_FEATURE_COLUMNS),
            "booster": ConstantValueBooster(),
            "reachability_booster": ConstantReachabilityBooster(),
            "cost_booster": ConstantCostBooster(),
        }
        result, trace = m3star.run_m3star_model_episode(
            config,
            claims,
            actions,
            "random",
            1.0,
            23,
            model,
            horizon=1,
            action_value_model=value_model,
        )
        no_dominance_result, no_dominance_trace = (
            m3star.run_m3star_model_episode(
                config,
                claims,
                actions,
                "random",
                1.0,
                23,
                model,
                horizon=1,
                action_value_model=value_model,
                stochastic_dominance_shield=False,
            )
        )

        self.assertEqual(1, result["reached_target"])
        self.assertEqual("A-hit", result["actions_taken"])
        self.assertEqual(model["model_family"], result["transition_model_family"])
        self.assertEqual(
            value_model["model_family"],
            result["action_value_model_family"],
        )
        self.assertEqual(
            value_model["model_family"],
            result["action_reachability_model_family"],
        )
        self.assertEqual(
            value_model["model_family"],
            result["action_cost_model_family"],
        )
        contract_document = m3star.RUNTIME_CONTRACT["document"]
        self.assertEqual(
            contract_document["contract_id"],
            result["runtime_contract_id"],
        )
        self.assertEqual(
            contract_document["version"],
            result["runtime_contract_version"],
        )
        self.assertEqual(
            m3star.RUNTIME_CONTRACT["sha256"],
            result["runtime_contract_sha256"],
        )
        event = next(event for event in trace if event["event"] == "action_taken")
        self.assertEqual(
            model["model_family"],
            event["m3star_decision"]["transition_model_family"],
        )
        self.assertEqual(
            value_model["model_family"],
            event["m3star_decision"]["action_value_model_family"],
        )
        self.assertEqual(
            contract_document["contract_id"],
            event["m3star_decision"]["runtime_contract_id"],
        )
        self.assertEqual(
            contract_document["version"],
            event["m3star_decision"]["runtime_contract_version"],
        )
        self.assertEqual(
            m3star.RUNTIME_CONTRACT["sha256"],
            event["m3star_decision"]["runtime_contract_sha256"],
        )
        self.assertEqual(
            0.75,
            event["m3star_decision"]["action_value_probability"],
        )
        self.assertEqual(
            0.80,
            event["m3star_decision"][
                "action_reachability_probability"
            ],
        )
        self.assertEqual(1.0, event["m3star_decision"]["action_cost_to_go"])
        self.assertGreater(
            event["m3star_decision"]["target_reach_probability"],
            0.5,
        )
        self.assertEqual(0, no_dominance_result["stochastic_dominance_shield"])
        self.assertEqual(0, no_dominance_result["dominance_substitution_count"])
        no_dominance_event = next(
            event
            for event in no_dominance_trace
            if event["event"] == "action_taken"
        )
        no_dominance_decision = no_dominance_event["m3star_decision"]
        self.assertEqual(
            no_dominance_decision["selected_action_id"],
            no_dominance_decision["pre_dominance_action_id"],
        )
        self.assertEqual(
            "disabled",
            no_dominance_decision["dominance_selection_reason"],
        )
        self.assertEqual(
            0,
            no_dominance_decision["dominance_substitution_applied"],
        )


class M3StarDatasetTests(unittest.TestCase):
    def test_reachable_rows_label_minimum_cost_oracle_action_offline(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-oracle-value-label",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 2,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {
                    "node_id": "N-gap",
                    "stage": "execution",
                    "critical": True,
                    "required_claim_ids": ["C-gap"],
                }
            ],
            "cti_edges": [],
            "channel_reliability": {},
            "mask_strategies": ["random"],
            "mask_intensities": [1.0],
            "random_seeds": [43],
        }
        claims = [
            {"claim_id": "C-gap", "source_type": "local_log", "tags": ["hideable"]}
        ]

        def action(action_id, cost):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": "N-gap"},
                "cost": cost,
                "recoverable_claim_ids": ["C-gap"],
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }

        rows = m3star.build_reachable_transition_rows(
            config,
            claims,
            [action("A-cheap", 1.0), action("A-expensive", 2.0)],
            max_depth=1,
        )
        by_action = {row["action_id"]: row for row in rows}

        self.assertEqual(1, by_action["A-cheap"].get("label_oracle_optimal_action"))
        self.assertEqual(0, by_action["A-expensive"].get("label_oracle_optimal_action"))
        self.assertEqual(1.0, by_action["A-cheap"].get("label_oracle_cost_via_action"))
        self.assertEqual(2.0, by_action["A-expensive"].get("label_oracle_cost_via_action"))
        for row in rows:
            public_columns = {
                "condition_id",
                "mask_strategy",
                "mask_intensity",
                "seed",
                "state_id",
                "state_depth",
                "action_path",
                "case_id",
                "action_id",
                "node_id",
                *m3star.GRAPH_FEATURE_COLUMNS,
            }
            self.assertTrue(
                {
                    "label_node_resolved",
                    "label_yield_positive",
                    "label_reaches_target_after_action",
                    "label_oracle_optimal_action",
                    "label_oracle_cost_via_action",
                }
                <= set(row) - public_columns
            )

    def test_bfs_labels_every_remaining_action_at_each_reachable_decision_state(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-bfs",
            "target_granularity": "G3_campaign",
            "support_ceiling": "G3_campaign",
            "budget_total": 2,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "granularity_thresholds": {
                "g3_node_coverage": 1.0,
                "g3_edge_coverage": 1.0,
                "g2_node_coverage": 0.5,
                "g2_min_stages": 2,
                "g1_node_coverage": 0.25,
            },
            "cti_nodes": [
                {
                    "node_id": "N1",
                    "stage": "execution",
                    "critical": False,
                    "required_claim_ids": ["C1"],
                },
                {
                    "node_id": "N2",
                    "stage": "collection",
                    "critical": True,
                    "required_claim_ids": ["C2"],
                },
            ],
            "cti_edges": [
                {"edge_id": "E12", "source": "N1", "target": "N2"}
            ],
            "channel_reliability": {},
            "mask_strategies": ["random"],
            "mask_intensities": [1.0],
            "random_seeds": [31],
        }
        claims = [
            {"claim_id": "C1", "source_type": "local_log", "tags": ["hideable"]},
            {"claim_id": "C2", "source_type": "local_log", "tags": ["hideable"]},
        ]

        def action(action_id, node_id, claim_id, stage):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": node_id},
                "cost": 1.0,
                "recoverable_claim_ids": [claim_id],
                "intended_cti_node_ids": [node_id],
                "expected_evidence_types": ["local_log"],
                "expected_stages": [stage],
                "expected_effects": {},
                "status": "available",
            }

        actions = [
            action("A1", "N1", "C1", "execution"),
            action("A2", "N2", "C2", "collection"),
        ]

        self.assertTrue(
            hasattr(m3star, "build_reachable_transition_rows"),
            "M3* multi-depth reachable-state dataset builder is missing",
        )
        rows = m3star.build_reachable_transition_rows(
            config,
            claims,
            actions,
            max_depth=2,
        )

        self.assertEqual(6, len(rows))
        self.assertEqual({0, 1}, {row["state_depth"] for row in rows})
        by_depth = {
            depth: [row for row in rows if row["state_depth"] == depth]
            for depth in (0, 1)
        }
        self.assertEqual(4, len(by_depth[0]))
        self.assertEqual(2, len(by_depth[1]))
        root_state_ids = {row["state_id"] for row in by_depth[0]}
        self.assertEqual(1, len(root_state_ids))
        self.assertEqual({"A1", "A2"}, {row["action_id"] for row in by_depth[0]})
        depth_one_states = {}
        for row in by_depth[1]:
            depth_one_states.setdefault(row["state_id"], set()).add(row["action_id"])
        self.assertEqual(2, len(depth_one_states))
        self.assertEqual({frozenset({"A1"}), frozenset({"A2"})}, {
            frozenset(action_ids) for action_ids in depth_one_states.values()
        })
        root_labels = {
            (row["action_id"], row["node_id"]): row["label_node_resolved"]
            for row in by_depth[0]
        }
        self.assertEqual(1, root_labels[("A1", "N1")])
        self.assertEqual(0, root_labels[("A1", "N2")])
        self.assertEqual(0, root_labels[("A2", "N1")])
        self.assertEqual(1, root_labels[("A2", "N2")])
        for row in rows:
            self.assertNotIn("recoverable_claim_ids", row)
            self.assertNotIn("hidden_claim_ids", row)

    def test_case_partition_is_fixed_before_mask_and_state_generation(self):
        m3star = load_m3star(self)

        def make_case(case_id):
            config = {
                "case_id": case_id,
                "target_granularity": "G1_technique",
                "support_ceiling": "G3_campaign",
                "budget_total": 1,
                "granularity_order": [
                    "G0_unknown",
                    "G1_technique",
                    "G2_tactic_intent",
                    "G3_campaign",
                ],
                "cti_nodes": [
                    {
                        "node_id": "N-gap",
                        "stage": "execution",
                        "critical": True,
                        "required_claim_ids": ["C-gap"],
                    }
                ],
                "cti_edges": [],
                "channel_reliability": {},
                "mask_strategies": ["random"],
                "mask_intensities": [1.0],
                "random_seeds": [41],
            }
            claims = [
                {
                    "claim_id": "C-gap",
                    "source_type": "local_log",
                    "tags": ["hideable"],
                }
            ]
            actions = [
                {
                    "action_id": "A-gap",
                    "case_id": case_id,
                    "action_type": "query_host_subgraph",
                    "acquisition_channel": "host_forensics",
                    "target": {"target_type": "node", "target_value": "N-gap"},
                    "cost": 1.0,
                    "recoverable_claim_ids": ["C-gap"],
                    "intended_cti_node_ids": ["N-gap"],
                    "expected_evidence_types": ["local_log"],
                    "expected_stages": ["execution"],
                    "expected_effects": {},
                    "status": "available",
                }
            ]
            return config, claims, actions

        cases = [make_case("C-train"), make_case("C-validation")]

        self.assertTrue(
            hasattr(m3star, "build_case_partitioned_transition_rows"),
            "M3* case-first train/validation dataset builder is missing",
        )
        dataset = m3star.build_case_partitioned_transition_rows(
            cases,
            train_case_ids={"C-train"},
            validation_case_ids={"C-validation"},
            max_depth=1,
        )

        self.assertEqual(
            {"C-train"},
            {row["case_id"] for row in dataset["train_rows"]},
        )
        self.assertEqual(
            {"C-validation"},
            {row["case_id"] for row in dataset["validation_rows"]},
        )
        self.assertTrue(
            all(row["dataset_partition"] == "train" for row in dataset["train_rows"])
        )
        self.assertTrue(
            all(
                row["dataset_partition"] == "validation"
                for row in dataset["validation_rows"]
            )
        )
        manifest = dataset["split_manifest"]
        self.assertEqual("case_id", manifest["split_unit"])
        self.assertEqual([], manifest["case_overlap"])
        self.assertEqual(
            ["case_split", "mask_generation", "bfs_state_expansion"],
            manifest["generation_order"],
        )
        self.assertTrue(manifest["mask_generated_after_case_split"])

    def test_case_partition_rejects_overlap_before_generating_any_masks(self):
        m3star = load_m3star(self)

        try:
            m3star.build_case_partitioned_transition_rows(
                [],
                train_case_ids={"C-overlap"},
                validation_case_ids={"C-overlap"},
                max_depth=2,
            )
        except Exception as exc:
            self.assertIsInstance(exc, ValueError)
            self.assertRegex(str(exc), "disjoint")
        else:
            self.fail("overlapping train/validation cases were accepted")


class M3StarLearningTests(unittest.TestCase):
    def test_graph_action_value_head_learns_minimum_cost_action(self):
        m3star = load_m3star(self)

        def node_row(
            state_index,
            action_id,
            cost_ratio,
            label,
            reachable,
            node_index,
        ):
            features = {column: 0.0 for column in m3star.GRAPH_FEATURE_COLUMNS}
            features["action_cost_ratio"] = cost_ratio
            features["budget_remaining_ratio"] = 1.0
            features["node_is_intended"] = 1.0
            context = {
                column: 0.0 for column in m3star.ACTION_CONTEXT_FEATURE_COLUMNS
            }
            context["cost"] = cost_ratio * 10
            context["budget_remaining"] = 10.0
            context["intended_node_count"] = 1.0
            context["intended_gap_overlap_count"] = 1.0
            context["intended_critical_gap_overlap_count"] = 1.0
            context["intended_gap_precision"] = 1.0
            context["intended_gap_recall"] = 1.0
            return {
                "case_id": f"C{state_index:02d}",
                "state_id": f"S{state_index:02d}",
                "action_id": action_id,
                "node_id": f"N{node_index}",
                **features,
                **context,
                "label_oracle_optimal_action": label,
                "label_oracle_cost_via_action": (
                    cost_ratio * 10 if reachable else ""
                ),
                "label_oracle_reachable_via_action": reachable,
            }

        node_rows = []
        for state_index in range(8):
            for node_index in range(2):
                node_rows.append(
                    node_row(state_index, "A-cheap", 0.1, 1, 1, node_index)
                )
                node_rows.append(
                    node_row(
                        state_index,
                        "A-expensive",
                        0.9,
                        0,
                        1,
                        node_index,
                    )
                )
                node_rows.append(
                    node_row(
                        state_index,
                        "A-blocked",
                        0.5,
                        0,
                        0,
                        node_index,
                    )
                )

        self.assertTrue(
            hasattr(m3star, "aggregate_action_value_rows"),
            "M3* graph action-value aggregation is missing",
        )
        action_rows = m3star.aggregate_action_value_rows(node_rows)
        self.assertEqual(24, len(action_rows))
        self.assertTrue(
            hasattr(m3star, "train_graph_action_value_model"),
            "M3* graph action-value learner is missing",
        )
        model = m3star.train_graph_action_value_model(
            action_rows,
            boost_rounds=30,
        )
        probabilities = m3star.predict_action_optimal_probabilities(
            model,
            action_rows,
        )
        reachability_probabilities = (
            m3star.predict_action_reachability_probabilities(
                model,
                action_rows,
            )
        )
        cost_predictions = m3star.predict_action_costs(model, action_rows)

        positive = [
            probability
            for probability, row in zip(probabilities, action_rows)
            if row["label_oracle_optimal_action"] == 1
        ]
        negative = [
            probability
            for probability, row in zip(probabilities, action_rows)
            if row["label_oracle_optimal_action"] == 0
        ]
        self.assertGreater(min(positive), max(negative))
        reachable_probabilities = [
            probability
            for probability, row in zip(reachability_probabilities, action_rows)
            if row["label_oracle_reachable_via_action"] == 1
        ]
        unreachable_probabilities = [
            probability
            for probability, row in zip(reachability_probabilities, action_rows)
            if row["label_oracle_reachable_via_action"] == 0
        ]
        self.assertGreater(
            min(reachable_probabilities),
            max(unreachable_probabilities),
        )
        cheap_costs = [
            prediction
            for prediction, row in zip(cost_predictions, action_rows)
            if row["action_id"] == "A-cheap"
        ]
        expensive_costs = [
            prediction
            for prediction, row in zip(cost_predictions, action_rows)
            if row["action_id"] == "A-expensive"
        ]
        self.assertLess(max(cheap_costs), min(expensive_costs))
        self.assertEqual(
            m3star.ACTION_VALUE_FEATURE_COLUMNS,
            model["feature_columns"],
        )
        self.assertEqual(
            "m3star_graph_action_value_xgboost_v0.3",
            model["model_family"],
        )
        self.assertIn("reachability_booster", model)
        self.assertIn("cost_booster", model)

    def test_joint_outcome_pruning_preserves_probability_in_audited_residual(self):
        m3star = load_m3star(self)

        self.assertTrue(
            hasattr(m3star, "factorized_node_transition_outcomes"),
            "M3* bounded factorized-outcome expansion is missing",
        )
        outcomes = m3star.factorized_node_transition_outcomes(
            [("N1", 0.8), ("N2", 0.6), ("N3", 0.4)],
            max_explicit_outcomes=3,
        )

        self.assertEqual(4, len(outcomes))
        self.assertAlmostEqual(1.0, sum(row["probability"] for row in outcomes))
        residual = [row for row in outcomes if row.get("residual_aggregation")]
        self.assertEqual(1, len(residual))
        self.assertEqual([], residual[0]["resolved_node_ids"])
        self.assertGreater(residual[0]["probability"], 0.0)
        self.assertEqual(
            residual[0]["probability"],
            residual[0]["aggregated_probability_mass"],
        )
        explicit = [row for row in outcomes if not row.get("residual_aggregation")]
        self.assertEqual(3, len(explicit))
        self.assertEqual(
            len(explicit),
            len({tuple(row["resolved_node_ids"]) for row in explicit}),
        )

    def test_model_transition_predictor_batches_without_changing_action_outcomes(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-model-batch",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 1,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True}
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 1.0,
                "budget_used": 0.0,
                "budget_remaining": 1.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A1", "A2"],
        }

        def action(action_id):
            return {
                "action_id": action_id,
                "case_id": config["case_id"],
                "action_type": "query_host_subgraph",
                "acquisition_channel": "host_forensics",
                "target": {"target_type": "node", "target_value": "N-gap"},
                "cost": 1.0,
                "intended_cti_node_ids": ["N-gap"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {},
                "status": "available",
            }

        class ConstantBooster:
            def predict(self, matrix):
                return [0.5] * matrix.num_row()

        model = {
            "feature_columns": list(m3star.GRAPH_FEATURE_COLUMNS),
            "booster": ConstantBooster(),
        }
        actions = [action("A1"), action("A2")]
        snapshot = m3star.public_graph_snapshot(config, state, actions)
        predictor = m3star.model_transition_predictor(
            model,
            max_outcome_nodes=1,
            max_explicit_outcomes=1,
        )

        self.assertTrue(
            hasattr(predictor, "predict_many"),
            "M3* model transition adapter has no batch interface",
        )
        batched = predictor.predict_many(snapshot, snapshot["actions"])
        self.assertEqual({"A1", "A2"}, set(batched))
        for candidate in snapshot["actions"]:
            self.assertEqual(
                predictor(snapshot, candidate),
                batched[candidate["action_id"]],
            )

        self.assertTrue(
            hasattr(m3star, "model_action_value_predictor"),
            "M3* action-value runtime adapter is missing",
        )
        value_model = {
            "feature_columns": list(m3star.ACTION_VALUE_FEATURE_COLUMNS),
            "booster": ConstantBooster(),
        }
        value_predictor = m3star.model_action_value_predictor(value_model)
        value_scores = value_predictor(snapshot, snapshot["actions"])
        self.assertEqual({"A1", "A2"}, set(value_scores))
        self.assertEqual({0.5}, set(value_scores.values()))

    def test_graph_transition_model_learns_node_resolution_probability(self):
        m3star = load_m3star(self)

        def row(case_id, intended, label):
            values = {column: 0.0 for column in m3star.GRAPH_FEATURE_COLUMNS}
            values["node_is_intended"] = float(intended)
            values["node_stage_expected"] = float(intended)
            values["channel_prior_reliability"] = 1.0
            values["channel_feedback_mean"] = 0.5
            return {
                "case_id": case_id,
                "action_id": f"A-{case_id}-{intended}-{label}",
                "node_id": f"N-{case_id}-{intended}-{label}",
                **values,
                "label_node_resolved": int(label),
                "label_yield_positive": int(label),
                "label_reaches_target_after_action": int(label),
            }

        rows = []
        for case_id in ("C01", "C02"):
            rows.extend(
                [
                    row(case_id, 0, 0),
                    row(case_id, 0, 0),
                    row(case_id, 1, 1),
                    row(case_id, 1, 1),
                ]
            )

        self.assertTrue(
            hasattr(m3star, "train_graph_transition_model"),
            "M3* graph transition learner is missing",
        )
        model = m3star.train_graph_transition_model(rows, boost_rounds=30)
        probabilities = m3star.predict_node_resolution_probabilities(model, rows)

        negative = [p for p, item in zip(probabilities, rows) if item["label_node_resolved"] == 0]
        positive = [p for p, item in zip(probabilities, rows) if item["label_node_resolved"] == 1]
        self.assertGreater(min(positive), max(negative))
        self.assertEqual(["C01", "C02"], model["training_case_ids"])
        self.assertEqual(m3star.GRAPH_FEATURE_COLUMNS, model["feature_columns"])

    def test_learned_node_probabilities_expand_to_stochastic_transition_outcomes(self):
        m3star = load_m3star(self)
        config = {
            "case_id": "T-m3star-outcomes",
            "target_granularity": "G1_technique",
            "support_ceiling": "G3_campaign",
            "budget_total": 2,
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
            "cti_nodes": [
                {"node_id": "N-gap", "stage": "execution", "critical": True},
            ],
            "cti_edges": [],
            "channel_reliability": {},
        }
        state = {
            "case_id": config["case_id"],
            "step_index": 0,
            "matched_cti_node_ids": [],
            "unmatched_cti_node_ids": ["N-gap"],
            "matched_cti_edge_ids": [],
            "unmatched_cti_edge_ids": [],
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {},
            },
            "budget": {
                "budget_total": 2.0,
                "budget_used": 0.0,
                "budget_remaining": 2.0,
            },
            "actions_taken": [],
            "action_feedback": [],
            "remaining_action_ids": ["A-gap"],
        }
        action = {
            "action_id": "A-gap",
            "case_id": config["case_id"],
            "action_type": "query_host_subgraph",
            "acquisition_channel": "host_forensics",
            "target": {"target_type": "node", "target_value": "N-gap"},
            "cost": 1.0,
            "intended_cti_node_ids": ["N-gap"],
            "expected_evidence_types": ["local_log"],
            "expected_stages": ["execution"],
            "expected_effects": {},
            "status": "available",
        }
        public_rows = m3star.node_transition_feature_rows(config, state, [action])
        negative = {
            "case_id": "C01",
            **public_rows[0],
            "node_is_intended": 0.0,
            "node_stage_expected": 0.0,
            "label_node_resolved": 0,
        }
        positive = {
            "case_id": "C02",
            **public_rows[0],
            "label_node_resolved": 1,
        }
        training_rows = [negative.copy() for _ in range(8)] + [
            positive.copy() for _ in range(8)
        ]
        model = m3star.train_graph_transition_model(training_rows, boost_rounds=30)
        snapshot = m3star.public_graph_snapshot(config, state, [action])

        self.assertTrue(
            hasattr(m3star, "model_transition_outcomes"),
            "M3* learned stochastic transition adapter is missing",
        )
        outcomes = m3star.model_transition_outcomes(model, snapshot, snapshot["actions"][0])

        self.assertEqual(2, len(outcomes))
        self.assertAlmostEqual(1.0, sum(item["probability"] for item in outcomes))
        self.assertEqual(
            {(), ("N-gap",)},
            {tuple(item["resolved_node_ids"]) for item in outcomes},
        )
        for outcome in outcomes:
            self.assertGreater(outcome["probability"], 0.0)
            self.assertLess(outcome["probability"], 1.0)


class M3StarExperimentRunnerTests(unittest.TestCase):
    def test_runner_exposes_frozen_runtime_contract_metadata(self):
        runner = load_m3star_experiment(self)

        metadata = runner.runtime_contract_metadata()

        self.assertEqual(
            "project05-m3star-runtime-contract-v0.2",
            metadata["contract_id"],
        )
        self.assertEqual("0.2.0", metadata["version"])
        self.assertEqual(64, len(metadata["sha256"]))
        self.assertTrue(metadata["runtime_allowlist_enforced"])

    def test_public_model_metadata_excludes_every_booster_object(self):
        runner = load_m3star_experiment(self)
        metadata = runner._public_model_metadata(
            {
                "model_family": "dual-action-head",
                "booster": object(),
                "reachability_booster": object(),
                "feature_columns": ["x"],
            }
        )

        self.assertEqual(
            {
                "model_family": "dual-action-head",
                "feature_columns": ["x"],
            },
            metadata,
        )

    def test_method_matrix_contains_dual_head_ablation_and_frozen_baselines(self):
        runner = load_m3star_experiment(self)

        self.assertEqual(
            [
                ("project05_m3star_h3_dual", 3, True, True, True),
                (
                    "project05_m3star_h3_no_dominance_dual",
                    3,
                    True,
                    True,
                    False,
                ),
                (
                    "project05_m3star_h3_unshielded_dual",
                    3,
                    True,
                    False,
                    True,
                ),
                (
                    "project05_m3star_h3_transition_only",
                    3,
                    False,
                    True,
                    True,
                ),
                ("project05_m3star_h1_dual", 1, True, True, True),
                ("project05_xgboost_policy", None, None, None, None),
                ("project05_m3b_policy", None, None, None, None),
                ("project05_m2", None, None, None, None),
                ("oracle_optimal", None, None, None, None),
            ],
            [
                (
                    spec["planner_id"],
                    spec.get("horizon"),
                    spec.get("use_action_value"),
                    spec.get("myopic_safety_shield"),
                    spec.get("stochastic_dominance_shield"),
                )
                for spec in runner.METHOD_SPECS
            ],
        )
        self.assertEqual(
            ("C07-", "C08-", "C09-", "C10-", "C11-", "C12-"),
            runner.DEVELOPMENT_EVALUATION_PREFIXES,
        )

    def test_case_partition_rejects_training_evaluation_overlap(self):
        runner = load_m3star_experiment(self)

        with self.assertRaisesRegex(ValueError, "disjoint"):
            runner.validate_case_id_partition(
                ["C01", "C02"],
                ["C02", "C07"],
            )

    def test_evaluation_subset_filter_never_changes_the_held_out_split(self):
        runner = load_m3star_experiment(self)
        held_out_cases = [
            ({"case_id": "C07-held-out"}, [], []),
            ({"case_id": "C08-held-out"}, [], []),
            ({"case_id": "C12-held-out"}, [], []),
        ]

        selected = runner.select_evaluation_subset(
            held_out_cases,
            ("C08-", "C12-"),
        )

        self.assertEqual(
            ["C08-held-out", "C12-held-out"],
            [config["case_id"] for config, _, _ in selected],
        )
        self.assertEqual(3, len(held_out_cases))
        with self.assertRaisesRegex(ValueError, "matched no held-out case"):
            runner.select_evaluation_subset(held_out_cases, ("C13-",))

    def test_paired_comparison_keeps_success_losses_separate_from_cost(self):
        runner = load_m3star_experiment(self)
        rows = [
            {
                "case_id": "C07",
                "mask_strategy": "random",
                "mask_intensity": 0.2,
                "seed": 11,
                "planner": "candidate",
                "reached_target": 1,
                "cost_to_target": 2.0,
            },
            {
                "case_id": "C07",
                "mask_strategy": "random",
                "mask_intensity": 0.2,
                "seed": 11,
                "planner": "baseline",
                "reached_target": 1,
                "cost_to_target": 3.0,
            },
            {
                "case_id": "C08",
                "mask_strategy": "random",
                "mask_intensity": 0.4,
                "seed": 23,
                "planner": "candidate",
                "reached_target": 0,
                "cost_to_target": "",
            },
            {
                "case_id": "C08",
                "mask_strategy": "random",
                "mask_intensity": 0.4,
                "seed": 23,
                "planner": "baseline",
                "reached_target": 1,
                "cost_to_target": 1.0,
            },
        ]

        comparison = runner.paired_against(
            rows,
            "candidate",
            "baseline",
        )

        self.assertEqual(2, comparison["paired_conditions"])
        self.assertEqual(1, comparison["success_loss_count"])
        self.assertEqual(0, comparison["success_gain_count"])
        self.assertEqual(1, comparison["both_success_count"])
        self.assertEqual(1, comparison["cost_win_count"])
        self.assertEqual(-1.0, comparison["total_cost_delta_on_both_success"])
        self.assertEqual(-1.0, comparison["mean_cost_delta_on_both_success"])

    def test_horizon_trace_summary_counts_first_step_divergence_and_outcome(self):
        runner = load_m3star_experiment(self)
        traces = [
            {
                "case_id": "C07",
                "planner": "project05_m3star_h3_dual",
                "result": {
                    "reached_target": 1,
                    "budget_used": 2.0,
                },
                "trace": [
                    {
                        "event": "action_taken",
                        "m3star_decision": {
                            "selected_action_id": "A-h3",
                            "myopic_action_id": "A-h1",
                            "nonmyopic_action_id": "A-h3",
                            "dominance_substitution_applied": 1,
                            "horizon_selection_reason": (
                                "nonmyopic_plan_selected"
                            ),
                        },
                    }
                ],
            }
        ]

        summary = runner.summarize_horizon_traces(traces)
        planner = summary["project05_m3star_h3_dual"]

        self.assertEqual(1, planner["episode_count"])
        self.assertEqual(1, planner["decision_count"])
        self.assertEqual(1, planner["first_step_divergence_count"])
        self.assertEqual(1, planner["any_step_divergence_count"])
        self.assertEqual(1, planner["dominance_substitution_count"])
        self.assertEqual(1, planner["dominance_substitution_episode_count"])
        self.assertEqual(
            1.0,
            planner["dominance_substitution_episode_success_rate"],
        )
        self.assertEqual(1.0, planner["divergent_episode_success_rate"])
        self.assertEqual(
            {"nonmyopic_plan_selected": 1},
            planner["horizon_selection_reason_counts"],
        )

    def test_horizon_trace_summary_separates_candidate_from_executed_divergence(self):
        runner = load_m3star_experiment(self)
        traces = [
            {
                "case_id": "C07",
                "planner": "project05_m3star_h3_dual",
                "result": {
                    "reached_target": 1,
                    "budget_used": 2.0,
                },
                "trace": [
                    {
                        "event": "action_taken",
                        "m3star_decision": {
                            "selected_action_id": "A-h1",
                            "myopic_action_id": "A-h1",
                            "nonmyopic_action_id": "A-h3",
                            "horizon_selection_reason": (
                                "counterfactual_rollout_shield"
                            ),
                        },
                    }
                ],
            }
        ]

        planner = runner.summarize_horizon_traces(traces)[
            "project05_m3star_h3_dual"
        ]

        self.assertEqual(1, planner["candidate_first_step_divergence_count"])
        self.assertEqual(1, planner["candidate_any_step_divergence_count"])
        self.assertEqual(0, planner["first_step_divergence_count"])
        self.assertEqual(0, planner["any_step_divergence_count"])
        self.assertIsNone(planner["divergent_episode_success_rate"])

    def test_core_gate_rejects_case_level_cost_regression_hidden_by_average(self):
        runner = load_m3star_experiment(self)
        overall = {
            "baseline": {
                "success_loss_count": 0,
                "mean_cost_delta_on_both_success": -0.5,
            }
        }
        by_case = {
            "baseline": {
                "C07": {
                    "success_loss_count": 0,
                    "success_gain_count": 0,
                    "both_success_count": 1,
                    "total_cost_delta_on_both_success": -1.0,
                    "mean_cost_delta_on_both_success": -1.0,
                    "budget_total": 9.0,
                },
                "C12": {
                    "success_loss_count": 0,
                    "success_gain_count": 0,
                    "both_success_count": 1,
                    "total_cost_delta_on_both_success": 0.25,
                    "mean_cost_delta_on_both_success": 0.25,
                    "budget_total": 8.0,
                },
            }
        }

        gate = runner.strict_core_gate(overall, by_case)

        self.assertTrue(gate["overall_by_baseline"]["baseline"])
        self.assertTrue(gate["case_pareto_by_baseline"]["baseline"]["C07"])
        self.assertFalse(gate["case_pareto_by_baseline"]["baseline"]["C12"])
        self.assertFalse(gate["all_core_baselines_pass"])

    def test_core_gate_accepts_success_gain_with_sub_budget_rescue_cost(self):
        runner = load_m3star_experiment(self)
        overall = {
            "baseline": {
                "success_loss_count": 0,
                "mean_cost_delta_on_both_success": -0.5,
            }
        }
        by_case = {
            "baseline": {
                "C02": {
                    "success_loss_count": 0,
                    "success_gain_count": 12,
                    "both_success_count": 29,
                    "total_cost_delta_on_both_success": 7.0,
                    "mean_cost_delta_on_both_success": 7.0 / 29.0,
                    "budget_total": 7.0,
                }
            }
        }

        gate = runner.strict_core_gate(overall, by_case)
        detail = gate["case_pareto_details_by_baseline"]["baseline"]["C02"]

        self.assertTrue(gate["case_pareto_by_baseline"]["baseline"]["C02"])
        self.assertEqual("bounded_rescue_cost", detail["acceptance_mode"])
        self.assertAlmostEqual(7.0 / 12.0, detail["incremental_cost_per_success_gain"])
        self.assertEqual(7.0, detail["rescue_cost_cap"])

    def test_core_gate_rejects_rescue_cost_at_full_episode_budget(self):
        runner = load_m3star_experiment(self)
        overall = {
            "baseline": {
                "success_loss_count": 0,
                "mean_cost_delta_on_both_success": -0.5,
            }
        }
        by_case = {
            "baseline": {
                "C06": {
                    "success_loss_count": 0,
                    "success_gain_count": 1,
                    "both_success_count": 44,
                    "total_cost_delta_on_both_success": 8.0,
                    "mean_cost_delta_on_both_success": 8.0 / 44.0,
                    "budget_total": 8.0,
                }
            }
        }

        gate = runner.strict_core_gate(overall, by_case)
        detail = gate["case_pareto_details_by_baseline"]["baseline"]["C06"]

        self.assertFalse(gate["case_pareto_by_baseline"]["baseline"]["C06"])
        self.assertEqual("rescue_cost_cap_not_met", detail["rejection_reason"])
        self.assertEqual(8.0, detail["incremental_cost_per_success_gain"])
        self.assertFalse(gate["all_core_baselines_pass"])


class M3StarRuntimeContractTests(unittest.TestCase):
    def test_frozen_contract_validates_and_matches_implementation(self):
        m3star = load_m3star(self)
        contract_path = (
            SCRIPT_DIR.parent
            / "governance"
            / "contracts"
            / "planner-runtime-contract-m3star-v0.2.json"
        )
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        schema_path = (contract_path.parent / contract["$schema"]).resolve()
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(
                schema,
                format_checker=FormatChecker(),
            ).iter_errors(contract),
            key=lambda error: list(error.absolute_path),
        )
        self.assertEqual([], [error.message for error in errors])

        feature_contract = contract["ml_feature_contract"]
        self.assertEqual(
            m3star.GRAPH_FEATURE_COLUMNS,
            feature_contract["transition_feature_columns"],
        )
        self.assertEqual(
            m3star.ACTION_VALUE_FEATURE_COLUMNS,
            feature_contract["action_feature_columns"],
        )
        self.assertFalse(feature_contract["labels_runtime_visible"])
        self.assertEqual(
            {
                "graph_transition": "label_node_resolved",
                "action_optimality": "label_oracle_optimal_action",
                "action_reachability": "label_oracle_reachable_via_action",
                "action_cost_to_go": "label_oracle_cost_via_action",
            },
            {
                name: head["offline_label"]
                for name, head in feature_contract["heads"].items()
            },
        )

        selection = contract["selection_contract"]
        dominance = selection["post_selection_stochastic_dominance"]
        self.assertEqual(
            list(m3star.DOMINANCE_EFFECT_KEYS),
            dominance["noninferior_expected_effect_fields"],
        )
        self.assertEqual(
            "alternative_cost <= source_cost / max(0.05, source_reliability)",
            dominance["risk_adjusted_cost_rule"],
        )
        self.assertTrue(dominance["replacement_must_use_precomputed_plan"])
        self.assertEqual(
            "not_independently_supported_on_legacy_development_matrix",
            selection["experimental_options"]["planning_horizon"],
        )
        self.assertEqual(
            "not_independently_supported_on_legacy_development_matrix",
            selection["experimental_options"]["myopic_safety_shield"],
        )
        self.assertEqual(
            {
                "pre_dominance_action_id",
                "dominance_substitution_applied",
                "dominance_selection_reason",
                "dominance_source_action_id",
                "dominance_target_action_id",
                "dominance_source_reliability",
                "dominance_target_reliability",
                "dominance_source_cost",
                "dominance_target_cost",
                "dominance_source_risk_adjusted_cost",
            },
            set(contract["audit_contract"]["decision_fields"]),
        )
        self.assertEqual(
            {
                "runtime_contract_id",
                "runtime_contract_version",
                "runtime_contract_sha256",
            },
            set(contract["audit_contract"]["runtime_contract_fields"]),
        )

    def test_frozen_contract_binds_complete_legacy_development_evidence(self):
        project_root = SCRIPT_DIR.parents[1]
        contract_path = (
            SCRIPT_DIR.parent
            / "governance"
            / "contracts"
            / "planner-runtime-contract-m3star-v0.2.json"
        )
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        evidence = contract["development_evidence"]
        precursor_path = contract_path.with_name(
            "planner-runtime-contract-m3star-v0.1.json"
        )
        self.assertEqual(
            evidence["runtime_contract_sha256_during_run"],
            hashlib.sha256(precursor_path.read_bytes()).hexdigest(),
        )
        result_dir = project_root / evidence["result_directory"]
        self.assertTrue(result_dir.is_dir())
        for relative_path, expected in evidence["artifact_sha256"].items():
            actual = hashlib.sha256((result_dir / relative_path).read_bytes()).hexdigest()
            self.assertEqual(expected, actual, relative_path)

        report = json.loads(
            (result_dir / "experiment_report.json").read_text(encoding="utf-8")
        )
        summary = json.loads(
            (result_dir / "development_summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(evidence["train_case_ids"], report["train_case_ids"])
        self.assertEqual(
            evidence["development_case_ids"],
            report["evaluation_case_ids"],
        )
        self.assertTrue(
            summary["legacy_debug_gate"]["all_core_baselines_pass"]
        )
        self.assertFalse(summary["legacy_debug_gate"]["formal_cost_claim_allowed"])
        self.assertFalse(evidence["formal_cost_claim_allowed"])
        self.assertTrue(
            all(
                not case_id.startswith("C13-")
                for case_id in report["held_out_case_ids"]
            )
        )


if __name__ == "__main__":
    unittest.main()
