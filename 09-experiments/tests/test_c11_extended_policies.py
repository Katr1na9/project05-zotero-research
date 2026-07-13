import hashlib
import json
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
ROOT = EXPERIMENT_DIR.parent
RESULT_DIR = EXPERIMENT_DIR / "results" / "c11_extended_policies_v0.1"
SUMMARY_PATH = RESULT_DIR / "c11_extended_policy_summary.json"
CASE_ID = "C11-otrf-apt29-day1-scranton-nashua"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class C11ExtendedPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = load_json(SUMMARY_PATH)
        cls.results = {
            row["planner"]: row for row in cls.summary["planner_results"]
        }

    def test_design_keeps_c11_as_one_separate_g2_chain(self):
        design = self.summary["design"]
        self.assertEqual(CASE_ID, self.summary["case_id"])
        self.assertEqual(1, design["independent_attack_chain_count"])
        self.assertEqual(45, design["repeated_condition_count_per_planner"])
        self.assertEqual("G2_tactic_intent", design["target_granularity"])
        self.assertEqual("AND", design["node_coverage_semantics"])
        self.assertIn("separate", design["aggregation_rule"])

    def test_xgboost_transfer_excludes_c11_and_reuses_identical_models(self):
        isolation = self.summary["training_isolation"]
        self.assertEqual(6, len(isolation["train_case_ids"]))
        self.assertEqual([CASE_ID], isolation["test_case_ids"])
        self.assertFalse(isolation["c11_used_for_training"])
        self.assertTrue(
            all(
                check["identical"]
                and check["reference_sha256"] == check["c11_transfer_sha256"]
                for check in isolation["model_hash_checks"].values()
            )
        )

    def test_shared_frozen_baselines_match_every_repeated_run(self):
        checks = self.summary["shared_baseline_row_checks"]
        self.assertTrue(
            all(
                matches
                for family in checks.values()
                for matches in family.values()
            )
        )

    def test_frozen_c11_policy_outcomes(self):
        expected = {
            "oracle_optimal": (1.0, 3.0),
            "project05_xgboost_policy": (1.0, 3.0667),
            "project05_m3b_policy": (1.0, 3.0667),
            "coverage_greedy": (1.0, 3.2444),
            "project05_m1": (1.0, 3.2444),
            "afa_voi_myopic": (1.0, 3.5556),
            "project05_m3a_gap_compat": (1.0, 3.5556),
            "project05_m2": (1.0, 3.6667),
            "afa_voi_rollout_h3": (1.0, 3.6889),
            "project05_depth2_public": (0.9778, 4.9091),
        }
        for planner, (success, cost) in expected.items():
            with self.subTest(planner=planner):
                row = self.results[planner]
                self.assertEqual(45, row["repeated_run_count"])
                self.assertEqual(success, row["success_rate"])
                self.assertEqual(cost, row["mean_cost_to_target"])
                self.assertEqual(0.0, row["ceiling_violation_rate"])

    def test_paired_results_preserve_success_and_cost_boundaries(self):
        paired = self.summary["paired_against_m2"]
        xgb = paired["project05_xgboost_policy"]
        self.assertEqual((10, 34, 1), (
            xgb["cost_wins_vs_m2"],
            xgb["cost_ties_vs_m2"],
            xgb["cost_losses_vs_m2"],
        ))
        self.assertEqual(-0.6, xgb["mean_cost_difference_vs_m2_on_joint_success"])

        myopic = paired["afa_voi_myopic"]
        self.assertEqual((8, 35, 2), (
            myopic["cost_wins_vs_m2"],
            myopic["cost_ties_vs_m2"],
            myopic["cost_losses_vs_m2"],
        ))
        self.assertEqual(-0.1111, myopic["mean_cost_difference_vs_m2_on_joint_success"])

        depth2 = paired["project05_depth2_public"]
        self.assertEqual(1, depth2["success_regressions_vs_m2"])
        self.assertEqual(44, depth2["joint_success_count"])
        self.assertEqual(1.3182, depth2["mean_cost_difference_vs_m2_on_joint_success"])

    def test_offline_metrics_are_not_substituted_for_sequential_utility(self):
        offline = self.summary["xgboost_offline_primary_label_test"]
        self.assertEqual(225, offline["xgboost"]["rows"])
        self.assertAlmostEqual(0.3952122571, offline["xgboost"]["average_precision"])
        self.assertAlmostEqual(0.6322479660, offline["logistic"]["average_precision"])
        self.assertAlmostEqual(
            0.4222222222,
            offline["xgboost"]["top1_label_hit_rate"],
        )

    def test_recorded_source_hashes_match(self):
        for relative_path, expected in self.summary["source_sha256"].items():
            with self.subTest(path=relative_path):
                actual = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest().upper()
                self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
