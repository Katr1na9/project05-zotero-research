import json
import unittest
from pathlib import Path


RESULT_PATH = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "nonmyopic_dqn_gate_v0.1"
    / "nonmyopic_gate_summary.json"
)


class NonMyopicGateFrozenResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(RESULT_PATH.read_text(encoding="utf-8"))

    def test_design_preserves_independent_environment_count(self):
        design = self.summary["design"]
        self.assertEqual(192, design["independent_scenario_count"])
        self.assertEqual(10, design["seed_count"])
        self.assertEqual(7680, design["episode_count"])
        self.assertEqual(4, len(design["planners"]))

    def test_gate_a_passes_on_broad_nonmyopic_conflicts(self):
        gate_a = self.summary["gate_a_nonmyopic_necessity"]
        self.assertTrue(gate_a["passed"])
        self.assertEqual(166, gate_a["conflict_scenario_count"])
        self.assertEqual(0.6208, gate_a["mean_success_advantage_dp_vs_m2"])
        self.assertEqual(0.4, gate_a["mean_depth2_repair_at_depth1"])
        self.assertEqual([1, 3, 6, 10], gate_a["conflict_distractor_counts"])
        self.assertEqual([0.5, 1.0, 2.0], gate_a["conflict_distractor_gains"])

    def test_gate_b_rejects_dqn_while_dp_remains_tractable(self):
        gate_b = self.summary["gate_b_dqn_necessity"]
        self.assertFalse(gate_b["passed"])
        self.assertEqual(0.3448, gate_b["success_advantage_dp_vs_depth2"])
        self.assertFalse(gate_b["checks"]["dp_complexity_exceeds_threshold"])
        self.assertLess(gate_b["dp_cold_start_p95_ms"], 100.0)
        self.assertEqual(23892, gate_b["dp_max_expanded_states"])
        self.assertEqual(
            "use_lightweight_nonmyopic_planning_no_dqn",
            self.summary["decision"],
        )

    def test_dp_improves_success_without_claiming_real_world_prevalence(self):
        planners = self.summary["overall_by_planner"]
        self.assertEqual(0.0948, planners["project05_m2"]["success_rate"])
        self.assertEqual(0.3708, planners["depth2_m2"]["success_rate"])
        self.assertEqual(0.7156, planners["dp_oracle"]["success_rate"])


if __name__ == "__main__":
    unittest.main()
