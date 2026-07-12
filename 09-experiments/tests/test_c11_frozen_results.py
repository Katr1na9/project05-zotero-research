import csv
import hashlib
import json
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXPERIMENT_DIR / "results"
CASE_SLUG = "c11-otrf-apt29-day1-scranton-nashua"
AND_DIR = RESULTS_DIR / "c11_holdout_v0.1"
OR_DIR = RESULTS_DIR / "c11_or_sensitivity_v0.1"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class C11FrozenResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.and_summary_path = AND_DIR / f"{CASE_SLUG}_mvp_summary.json"
        cls.or_summary_path = OR_DIR / f"{CASE_SLUG}_mvp_summary.json"
        cls.and_csv_path = AND_DIR / f"{CASE_SLUG}_mvp_results.csv"
        cls.or_csv_path = OR_DIR / f"{CASE_SLUG}_mvp_results.csv"
        cls.and_summary = load_json(cls.and_summary_path)
        cls.or_summary = load_json(cls.or_summary_path)
        cls.manifest = load_json(OR_DIR / "sensitivity_manifest.json")

    def test_primary_and_results_are_frozen(self):
        expected = {
            "oracle_optimal": (1.0, 3.0),
            "coverage_greedy": (1.0, 3.2444),
            "project05_m1": (1.0, 3.2444),
            "project05_m3a_gap_compat": (1.0, 3.5556),
            "project05_m2": (1.0, 3.6667),
            "random": (0.6, 3.4444),
        }
        for planner, (success, cost) in expected.items():
            with self.subTest(planner=planner):
                row = self.and_summary[planner]
                self.assertEqual(45, row["runs"])
                self.assertEqual(success, row["success_rate"])
                self.assertEqual(cost, row["mean_cost_to_target"])

    def test_or_sensitivity_changes_only_semantics_and_reduces_m2_cost(self):
        self.assertEqual(
            {"node_coverage_semantics": "OR"},
            self.manifest["override"],
        )
        and_m2 = self.and_summary["project05_m2"]
        or_m2 = self.or_summary["project05_m2"]
        self.assertEqual(1.0, and_m2["success_rate"])
        self.assertEqual(1.0, or_m2["success_rate"])
        self.assertEqual(3.6667, and_m2["mean_cost_to_target"])
        self.assertEqual(1.0222, or_m2["mean_cost_to_target"])
        self.assertAlmostEqual(
            -2.6445,
            or_m2["mean_cost_to_target"] - and_m2["mean_cost_to_target"],
            places=4,
        )

    def test_results_have_same_paired_design_and_no_ceiling_violations(self):
        with self.and_csv_path.open(encoding="utf-8", newline="") as handle:
            and_rows = list(csv.DictReader(handle))
        with self.or_csv_path.open(encoding="utf-8", newline="") as handle:
            or_rows = list(csv.DictReader(handle))
        self.assertEqual(630, len(and_rows))
        self.assertEqual(630, len(or_rows))
        key = lambda row: (
            row["mask_strategy"],
            row["mask_intensity"],
            row["seed"],
            row["planner"],
        )
        self.assertEqual({key(row) for row in and_rows}, {key(row) for row in or_rows})
        self.assertTrue(all(row["ceiling_violation"] == "0" for row in and_rows))
        self.assertTrue(all(row["ceiling_violation"] == "0" for row in or_rows))

    def test_recorded_output_hashes_match(self):
        hashes = self.manifest["output_hashes"]
        self.assertEqual(hashes["and_results_csv"], sha256(self.and_csv_path))
        self.assertEqual(hashes["and_summary_json"], sha256(self.and_summary_path))
        self.assertEqual(hashes["or_results_csv"], sha256(self.or_csv_path))
        self.assertEqual(hashes["or_summary_json"], sha256(self.or_summary_path))


if __name__ == "__main__":
    unittest.main()
