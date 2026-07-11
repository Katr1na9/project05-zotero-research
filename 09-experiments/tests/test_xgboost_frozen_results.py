import json
import unittest
from pathlib import Path


SUMMARY = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "xgboost_c01_c06_train_c07_c09_test"
    / "xgboost_experiment_summary.json"
)


class FrozenXGBoostResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(SUMMARY.read_text(encoding="utf-8"))

    def test_frozen_split_and_row_counts(self):
        self.assertEqual(6, len(self.report["train_case_ids"]))
        self.assertEqual(3, len(self.report["test_case_ids"]))
        self.assertEqual(1845, self.report["train_row_count"])
        self.assertEqual(720, self.report["test_row_count"])

    def test_xgboost_improves_logistic_success_but_not_m2_cost(self):
        planners = self.report["policy_summary"]["overall_by_planner"]
        xgb = planners["project05_xgboost_policy"]
        logistic = planners["project05_m3b_policy"]
        m2 = planners["project05_m2"]

        self.assertEqual(1.0, xgb["success_rate"])
        self.assertGreater(xgb["success_rate"], logistic["success_rate"])
        self.assertGreater(xgb["mean_cost_to_target"], m2["mean_cost_to_target"])
        self.assertEqual(0.0, xgb["ceiling_violation_rate"])

    def test_primary_xgboost_does_not_claim_auroc_superiority(self):
        primary = self.report["classification"][
            "label_resolves_critical_gap_node"
        ]
        self.assertLess(
            primary["xgboost"]["test"]["auroc"],
            primary["logistic"]["test"]["auroc"],
        )
        self.assertGreater(
            primary["xgboost"]["test"]["top1_label_hit_rate"],
            primary["logistic"]["test"]["top1_label_hit_rate"],
        )


if __name__ == "__main__":
    unittest.main()
