import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments" / "scripts" / "make_paper_main_figures.py"
SPEC = importlib.util.spec_from_file_location("make_paper_main_figures", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PaperMainFigureTests(unittest.TestCase):
    def test_policy_aggregation_matches_frozen_c07_c10_results(self):
        source = (
            ROOT
            / "09-experiments"
            / "results"
            / "xgboost_c01_c06_train_c07_c10_test"
            / "xgboost_policy_results.csv"
        )
        summary = MODULE.aggregate_policy_results(source).set_index("planner")

        self.assertEqual(summary.loc["project05_m2", "cases"], 4)
        self.assertEqual(summary.loc["project05_m2", "episodes"], 180)
        self.assertAlmostEqual(summary.loc["project05_m2", "success"], 1.0, places=4)
        self.assertAlmostEqual(summary.loc["project05_m2", "mean_cost"], 4.5333, places=4)

        self.assertAlmostEqual(
            summary.loc["project05_xgboost_policy", "success"], 1.0, places=4
        )
        self.assertAlmostEqual(
            summary.loc["project05_xgboost_policy", "mean_cost"], 4.8278, places=4
        )
        self.assertAlmostEqual(
            summary.loc["project05_m3a_gap_compat", "success"], 0.95, places=4
        )

    def test_real_depth2_is_added_to_holdout_panel_data(self):
        policy_source = (
            ROOT
            / "09-experiments"
            / "results"
            / "xgboost_c01_c06_train_c07_c10_test"
            / "xgboost_policy_results.csv"
        )
        depth2_source = (
            ROOT
            / "09-experiments"
            / "results"
            / "nonmyopic_real_v0.1"
            / "nonmyopic_policy_summary.json"
        )
        summary = MODULE.add_real_depth2_result(
            MODULE.aggregate_policy_results(policy_source), depth2_source
        ).set_index("planner")
        self.assertEqual(summary.loc["project05_depth2_public", "cases"], 4)
        self.assertEqual(summary.loc["project05_depth2_public", "episodes"], 180)
        self.assertAlmostEqual(
            summary.loc["project05_depth2_public", "success"], 1.0, places=4
        )
        self.assertAlmostEqual(
            summary.loc["project05_depth2_public", "mean_cost"], 4.5556, places=4
        )


if __name__ == "__main__":
    unittest.main()
