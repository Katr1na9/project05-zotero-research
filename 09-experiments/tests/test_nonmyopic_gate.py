import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "run_nonmyopic_gate.py"
)
SPEC = importlib.util.spec_from_file_location("run_nonmyopic_gate", SCRIPT_PATH)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)


class NonMyopicEnvironmentTests(unittest.TestCase):
    def test_frozen_grid_contains_192_unique_environments(self):
        scenarios = gate.scenario_grid()

        self.assertEqual(192, len(scenarios))
        self.assertEqual(192, len({scenario.scenario_id for scenario in scenarios}))
        self.assertEqual({1, 2, 3, 4}, {scenario.unlock_depth for scenario in scenarios})
        self.assertEqual({0, 1}, {scenario.budget_slack for scenario in scenarios})

    def test_depth2_repairs_single_unlock_conflict(self):
        scenario = gate.Scenario("depth1-conflict", 1, 0, 3, 1.0, 1.0)
        catalog = gate.action_catalog(scenario)
        oracle = gate.DPPolicy(scenario, catalog)

        results = {
            planner: gate.run_episode(
                scenario,
                11,
                planner,
                catalog=catalog,
                dp_policy=oracle,
            )[0]
            for planner in gate.PLANNERS
        }

        self.assertEqual(0, results["one_step_gain_cost"]["reached_target"])
        self.assertEqual(0, results["project05_m2"]["reached_target"])
        self.assertEqual(1, results["depth2_m2"]["reached_target"])
        self.assertEqual(1, results["dp_oracle"]["reached_target"])
        self.assertTrue(
            results["project05_m2"]["actions_taken"].startswith("DISTRACTOR_")
        )
        self.assertEqual("SETUP_01|PAYOFF", results["depth2_m2"]["actions_taken"])

    def test_depth2_is_insufficient_for_three_step_unlock(self):
        scenario = gate.Scenario("depth3-conflict", 3, 0, 3, 1.0, 1.0)
        catalog = gate.action_catalog(scenario)
        oracle = gate.DPPolicy(scenario, catalog)

        depth2 = gate.run_episode(
            scenario,
            11,
            "depth2_m2",
            catalog=catalog,
            dp_policy=oracle,
        )[0]
        dp = gate.run_episode(
            scenario,
            11,
            "dp_oracle",
            catalog=catalog,
            dp_policy=oracle,
        )[0]

        self.assertEqual(0, depth2["reached_target"])
        self.assertEqual(1, dp["reached_target"])
        self.assertEqual(
            "SETUP_01|SETUP_02|SETUP_03|PAYOFF",
            dp["actions_taken"],
        )

    def test_random_outcomes_are_paired_by_scenario_seed_and_action(self):
        scenario = gate.Scenario("paired-randomness", 1, 0, 1, 1.0, 0.8)
        setup = next(
            action for action in gate.action_catalog(scenario) if action["kind"] == "setup"
        )

        first = gate.realized_success(scenario, 23, setup)
        second = gate.realized_success(scenario, 23, setup)
        self.assertEqual(first, second)

    def test_small_experiment_writes_auditable_outputs(self):
        scenarios = [
            gate.Scenario("small-d1", 1, 0, 2, 1.0, 1.0),
            gate.Scenario("small-d3", 3, 0, 2, 1.0, 1.0),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            summary = gate.run_experiment(output, scenarios=scenarios, seeds=(11, 23))

            self.assertEqual(2, summary["design"]["independent_scenario_count"])
            self.assertEqual(16, summary["design"]["episode_count"])
            for filename in (
                "nonmyopic_gate_episodes.csv",
                "nonmyopic_gate_scenario_summary.csv",
                "nonmyopic_gate_dp_benchmarks.csv",
                "nonmyopic_gate_representative_traces.json",
                "nonmyopic_gate_summary.json",
            ):
                self.assertTrue((output / filename).is_file())
            reloaded = json.loads(
                (output / "nonmyopic_gate_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["decision"], reloaded["decision"])


if __name__ == "__main__":
    unittest.main()
