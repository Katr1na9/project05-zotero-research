import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = (
    ROOT
    / "09-experiments"
    / "results"
    / "c12_extended_policies_v0.1"
    / "summary.json"
)


class C12ExtendedPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.by_planner = {
            row["planner"]: row for row in cls.summary["planner_results"]
        }

    def test_design_keeps_one_incident_and_45_repeated_conditions(self):
        design = self.summary["design"]
        self.assertEqual(1, design["independent_incident_count"])
        self.assertEqual(45, design["repeated_condition_count"])
        self.assertEqual("G1_technique", design["target_granularity"])

    def test_frozen_models_and_shared_rows_are_identical(self):
        integrity = self.summary["integrity"]
        self.assertEqual(6, len(integrity["xgboost_train_case_ids"]))
        self.assertEqual(
            ["C12-witfoo-precinct6-f10c7270"],
            integrity["xgboost_test_case_ids"],
        )
        self.assertTrue(
            all(
                item["identical"]
                for item in integrity["model_hash_checks"].values()
            )
        )
        for family in integrity["shared_reference_row_checks"].values():
            self.assertTrue(all(family.values()))

    def test_policy_costs_and_boundaries_are_frozen(self):
        expected_costs = {
            "oracle_optimal": 0.8889,
            "project05_depth2_public": 0.8889,
            "afa_voi_rollout_h3": 0.9778,
            "project05_xgboost_policy": 0.9778,
            "project05_m3b_policy": 0.9778,
            "project05_m2": 1.4222,
            "afa_voi_myopic": 1.5111,
        }
        for planner, expected in expected_costs.items():
            with self.subTest(planner=planner):
                row = self.by_planner[planner]
                self.assertEqual(1.0, row["success_rate"])
                self.assertAlmostEqual(expected, row["mean_cost_to_target"], places=4)
                self.assertEqual(1.0, row["correct_stop_rate"])
                self.assertEqual(0.0, row["ceiling_violation_rate"])

    def test_depth2_improves_cost_without_creating_a_success_claim(self):
        paired = self.summary["paired_vs_m2"]["project05_depth2_public"]
        self.assertEqual(0, paired["success_repairs_vs_m2"])
        self.assertEqual(0, paired["success_regressions_vs_m2"])
        self.assertEqual(12, paired["cost_wins_vs_m2"])
        self.assertAlmostEqual(
            -0.5333,
            paired["mean_cost_difference_vs_m2_on_joint_success"],
            places=4,
        )


if __name__ == "__main__":
    unittest.main()
