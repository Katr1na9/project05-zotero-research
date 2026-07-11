import importlib.util
import unittest
from copy import deepcopy
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location(
    "run_xgboost",
    SCRIPT_DIR / "run_xgboost.py",
)
run_xgboost = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_xgboost)


class XGBoostModelTests(unittest.TestCase):
    def test_frozen_parameters_are_stable(self):
        self.assertEqual(3, run_xgboost.FROZEN_PARAMS["max_depth"])
        self.assertEqual(0.05, run_xgboost.FROZEN_PARAMS["eta"])
        self.assertEqual(11, run_xgboost.FROZEN_PARAMS["seed"])
        self.assertEqual(150, run_xgboost.FROZEN_BOOST_ROUNDS)

    def test_learns_a_separable_public_feature(self):
        rows = []
        for value, label in [(0.0, 0), (0.1, 0), (0.9, 1), (1.0, 1)] * 16:
            rows.append({"gap": value, "label": label, "group_id": str(len(rows))})

        model = run_xgboost.train_xgboost(
            rows,
            ["gap"],
            "label",
            params={**run_xgboost.FROZEN_PARAMS, "min_child_weight": 0.0},
            boost_rounds=20,
        )

        low = run_xgboost.predict_probability(model, {"gap": 0.0})
        high = run_xgboost.predict_probability(model, {"gap": 1.0})
        self.assertLess(low, 0.25)
        self.assertGreater(high, 0.75)
        self.assertGreater(high - low, 0.5)

    def test_feature_contract_excludes_hidden_outcomes(self):
        forbidden = {
            "recoverable_claim_ids",
            "hidden_claim_ids",
            "actual_recovered_claims",
            "oracle_path",
        }

        self.assertFalse(forbidden & set(run_xgboost.FEATURE_COLUMNS))


class XGBoostPolicyTests(unittest.TestCase):
    def test_selector_uses_public_features_not_hidden_recovery(self):
        config = {
            "case_id": "T-XGB",
            "budget_total": 4,
            "cti_nodes": [{"node_id": "N1", "critical": True}],
        }
        state = {
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {"local_log": 0.0},
            },
            "unmatched_cti_node_ids": ["N1"],
            "budget": {"budget_remaining": 4},
            "actions_taken": [],
            "action_feedback": [],
        }
        actions = [
            self.action("A-low", 2, [], [], 0.1),
            self.action("A-high", 2, ["N1"], ["SECRET"], 1.0),
        ]
        rows = []
        for action, label in [(actions[0], 0), (actions[1], 1)] * 32:
            row = run_xgboost.run_m3b.feature_row(config, state, action)
            row.update({"label": label, "group_id": str(len(rows))})
            rows.append(row)
        model = run_xgboost.train_xgboost(
            rows,
            run_xgboost.FEATURE_COLUMNS,
            "label",
            params={**run_xgboost.FROZEN_PARAMS, "min_child_weight": 0.0},
            boost_rounds=30,
        )

        first = run_xgboost.select_xgboost_action(config, state, actions, model, 0.1)
        changed = deepcopy(actions)
        changed[0]["recoverable_claim_ids"] = ["DIFFERENT"]
        changed[1]["recoverable_claim_ids"] = []
        second = run_xgboost.select_xgboost_action(config, state, changed, model, 0.1)

        self.assertEqual("A-high", first["action_id"])
        self.assertEqual(first["action_id"], second["action_id"])

    @staticmethod
    def action(action_id, cost, intended_nodes, recoverable, gain):
        return {
            "action_id": action_id,
            "action_type": "extend_log_window",
            "cost": cost,
            "target": {"target_type": "process", "target_value": action_id},
            "intended_cti_node_ids": intended_nodes,
            "recoverable_claim_ids": recoverable,
            "expected_stages": ["execution"],
            "expected_evidence_types": ["local_log"],
            "expected_effects": {
                "expected_granularity_gain": gain,
                "expected_uncertainty_reduction": gain,
                "expected_over_attribution_risk_reduction": gain,
                "expected_conflict_resolution": 0,
                "expected_coverage_delta": gain,
            },
        }


if __name__ == "__main__":
    unittest.main()
