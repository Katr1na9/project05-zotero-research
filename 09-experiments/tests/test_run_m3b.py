import importlib.util
import unittest
from copy import deepcopy
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
MVP_SPEC = importlib.util.spec_from_file_location(
    "run_mvp",
    SCRIPT_DIR / "run_mvp.py",
)
run_mvp = importlib.util.module_from_spec(MVP_SPEC)
assert MVP_SPEC.loader is not None
MVP_SPEC.loader.exec_module(run_mvp)

M3B_SPEC = importlib.util.spec_from_file_location(
    "run_m3b",
    SCRIPT_DIR / "run_m3b.py",
)
run_m3b = importlib.util.module_from_spec(M3B_SPEC)
assert M3B_SPEC.loader is not None
M3B_SPEC.loader.exec_module(run_m3b)


class M3bDatasetTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "case_id": "T99",
            "target_granularity": "G2_tactic_intent",
            "support_ceiling": "G3_campaign",
            "budget_total": 4,
            "mask_strategies": ["discriminative"],
            "mask_intensities": [0.5],
            "random_seeds": [11],
            "stage_mask_tags": [],
            "discriminative_claim_ids": ["E1"],
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
                    "critical": False,
                },
            ],
            "cti_edges": [
                {"edge_id": "EDGE", "source": "N1", "target": "N2"},
            ],
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
            ],
        }
        self.claims = [
            {
                "claim_id": "E1",
                "source_type": "local_log",
                "tags": ["hideable"],
            },
            {
                "claim_id": "E2",
                "source_type": "network_summary",
                "tags": ["hideable"],
            },
        ]
        self.actions = [
            {
                "action_id": "A-hit",
                "case_id": "T99",
                "action_type": "extend_log_window",
                "target": {"target_type": "process", "target_value": "p"},
                "cost": 1,
                "recoverable_claim_ids": ["E1"],
                "intended_cti_node_ids": ["N1"],
                "expected_evidence_types": ["local_log"],
                "expected_stages": ["execution"],
                "expected_effects": {
                    "expected_granularity_gain": 1,
                    "expected_uncertainty_reduction": 0.2,
                    "expected_over_attribution_risk_reduction": 0.2,
                    "expected_conflict_resolution": 0,
                    "expected_coverage_delta": 0.5,
                },
                "status": "available",
            },
            {
                "action_id": "A-miss",
                "case_id": "T99",
                "action_type": "recover_network_summary",
                "target": {"target_type": "ip", "target_value": "198.51.100.1"},
                "cost": 1,
                "recoverable_claim_ids": ["E2"],
                "intended_cti_node_ids": ["N2"],
                "expected_evidence_types": ["network_summary"],
                "expected_stages": ["command_and_control"],
                "expected_effects": {
                    "expected_granularity_gain": 1,
                    "expected_uncertainty_reduction": 0.2,
                    "expected_over_attribution_risk_reduction": 0.2,
                    "expected_conflict_resolution": 0,
                    "expected_coverage_delta": 0.5,
                },
                "status": "available",
            },
        ]

    def test_counterfactual_rows_label_node_resolution_without_hiding_features(self):
        rows = run_m3b.build_case_rows(self.config, self.claims, self.actions)
        by_action = {row["action_id"]: row for row in rows}

        self.assertEqual({"A-hit", "A-miss"}, set(by_action))
        self.assertEqual(1, by_action["A-hit"]["label_yield_positive"])
        self.assertEqual(1, by_action["A-hit"]["label_resolves_any_gap_node"])
        self.assertEqual(1, by_action["A-hit"]["label_resolves_critical_gap_node"])
        self.assertEqual(0, by_action["A-miss"]["label_yield_positive"])
        self.assertEqual(0, by_action["A-miss"]["label_resolves_any_gap_node"])

    def test_feature_row_does_not_change_when_hidden_outcomes_change(self):
        all_ids = {claim["claim_id"] for claim in self.claims}
        hidden_ids = {"E1"}
        state = run_mvp.build_state(
            self.config,
            self.claims,
            self.actions,
            "feature-boundary",
            0,
            "discriminative",
            0.5,
            11,
            all_ids - hidden_ids,
            hidden_ids,
            set(),
            [],
            0.0,
        )
        changed = deepcopy(self.actions[0])
        changed["recoverable_claim_ids"] = ["E2"]

        first = run_m3b.feature_row(self.config, state, self.actions[0])
        second = run_m3b.feature_row(self.config, state, changed)

        self.assertEqual(first, second)
        self.assertNotIn("recoverable_claim_ids", run_m3b.FEATURE_COLUMNS)
        self.assertNotIn("hidden_claim_ids", run_m3b.FEATURE_COLUMNS)

    def test_logistic_baseline_ranks_separable_positive_action_higher(self):
        rows = [
            {"x": 0.0, "label": 0, "group_id": "g1", "action_id": "low"},
            {"x": 1.0, "label": 1, "group_id": "g1", "action_id": "high"},
            {"x": 0.1, "label": 0, "group_id": "g2", "action_id": "low"},
            {"x": 0.9, "label": 1, "group_id": "g2", "action_id": "high"},
        ]

        model = run_m3b.train_logistic_baseline(
            rows,
            ["x"],
            "label",
            epochs=300,
            learning_rate=0.5,
        )
        low = run_m3b.predict_probability(model, rows[0])
        high = run_m3b.predict_probability(model, rows[1])

        self.assertLess(low, high)
        self.assertGreaterEqual(
            run_m3b.top1_label_hit_rate(model, rows, "label"),
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
