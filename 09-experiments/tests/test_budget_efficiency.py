import importlib.util
import gzip
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location(
    "run_budget_efficiency",
    SCRIPT_DIR / "run_budget_efficiency.py",
)
budget_efficiency = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(budget_efficiency)


class BudgetScheduleTests(unittest.TestCase):
    def test_builds_tight_budgets_and_preserves_original_budget(self):
        self.assertEqual(
            [6.0, 7.0, 8.0, 9.0],
            budget_efficiency.build_budget_schedule(6.0, 9.0),
        )

    def test_caps_and_deduplicates_budgets_at_original_limit(self):
        self.assertEqual(
            [8.0, 9.0],
            budget_efficiency.build_budget_schedule(8.0, 9.0),
        )

    def test_unreachable_condition_keeps_only_original_budget(self):
        self.assertEqual(
            [9.0],
            budget_efficiency.build_budget_schedule(None, 9.0),
        )


class BudgetCurveSummaryTests(unittest.TestCase):
    def test_summarizes_success_by_planner_and_oracle_relative_budget(self):
        rows = [
            self.row("C07", "project05_m2", 0.0, 0),
            self.row("C08", "project05_m2", 0.0, 1),
            self.row("C07", "project05_m3a_gap_compat", 0.0, 1),
            self.row("C08", "project05_m3a_gap_compat", 0.0, 1),
            self.row("C07", "project05_m2", 1.0, 1),
            self.row("C08", "project05_m2", 1.0, 1),
        ]

        summary = budget_efficiency.summarize_budget_curves(rows)
        by_key = {
            (row["planner"], row["budget_offset"]): row
            for row in summary["curve_points"]
        }

        self.assertEqual(0.5, by_key[("project05_m2", 0.0)]["success_rate"])
        self.assertEqual(
            1.0,
            by_key[("project05_m3a_gap_compat", 0.0)]["success_rate"],
        )
        self.assertEqual(2, by_key[("project05_m2", 1.0)]["condition_count"])

    @staticmethod
    def row(case_id, planner, budget_offset, reached_target):
        return {
            "case_id": case_id,
            "mask_strategy": "stage",
            "mask_intensity": 0.4,
            "seed": 11,
            "planner": planner,
            "budget_offset": budget_offset,
            "reached_target": reached_target,
            "cost_to_target": 2.0 if reached_target else "",
            "budget_used": 2.0,
            "premature_stop": 0,
            "ceiling_violation": 0,
        }


class OutputTests(unittest.TestCase):
    def test_writes_complete_gzip_json_trace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trace.json.gz"
            budget_efficiency.write_json(path, [{"run": 1}])

            with gzip.open(path, "rt", encoding="utf-8") as handle:
                self.assertEqual([{"run": 1}], json.load(handle))


if __name__ == "__main__":
    unittest.main()
