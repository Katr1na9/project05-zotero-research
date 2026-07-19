import importlib.util
import json
import unittest
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
SCRIPT = EXP / "scripts" / "analyze_m3star_sixcase.py"
RESULT_DIR = (
    EXP
    / "results"
    / "m3star_measured_replay_triple_consensus_sixcase_v0.8"
)


def load_analysis():
    spec = importlib.util.spec_from_file_location(
        "analyze_m3star_sixcase",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def result_row(
    planner,
    *,
    seed,
    reached_target,
    cost_to_target,
    steps_to_target,
):
    return {
        "planner": planner,
        "case_id": "C-test",
        "mask_strategy": "random",
        "mask_intensity": "0.25",
        "seed": str(seed),
        "reached_target": str(int(reached_target)),
        "cost_to_target": "" if cost_to_target is None else str(cost_to_target),
        "steps_to_target": "" if steps_to_target is None else str(steps_to_target),
        "steps_taken": str(steps_to_target or 0),
    }


class M3StarSixCaseAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analysis = load_analysis()

    def test_case_bootstrap_is_seeded_and_resamples_case_effects(self):
        first = self.analysis.case_bootstrap(
            [-2.0, 0.0, 1.0],
            seed=20260719,
            draws=1000,
        )
        second = self.analysis.case_bootstrap(
            [-2.0, 0.0, 1.0],
            seed=20260719,
            draws=1000,
        )

        self.assertEqual(first, second)
        self.assertEqual("case_id", first["resampling_unit"])
        self.assertEqual(1000, first["draws"])
        self.assertAlmostEqual(-1.0 / 3.0, first["mean_effect"])

    def test_success_rescue_cannot_mask_cost_regression(self):
        core = self.analysis.CORE
        baseline = self.analysis.BASELINES[0]
        rows = [
            result_row(
                core,
                seed=1,
                reached_target=True,
                cost_to_target=3.0,
                steps_to_target=1,
            ),
            result_row(
                baseline,
                seed=1,
                reached_target=True,
                cost_to_target=2.0,
                steps_to_target=1,
            ),
            result_row(
                core,
                seed=2,
                reached_target=True,
                cost_to_target=1.0,
                steps_to_target=1,
            ),
            result_row(
                baseline,
                seed=2,
                reached_target=False,
                cost_to_target=None,
                steps_to_target=2,
            ),
        ]

        effects = self.analysis.paired_effects(
            rows,
            baseline,
            bootstrap_seed=20260719,
            bootstrap_draws=100,
        )
        case = effects["by_case"]["C-test"]

        self.assertEqual(0, effects["success_loss_count"])
        self.assertEqual(1, effects["success_gain_count"])
        self.assertEqual(1.0, case["mean_cost_delta_on_both_success"])
        self.assertFalse(case["cost_noninferior_without_success_loss"])
        self.assertFalse(effects["all_cases_pass_directional_pareto_gate"])

    def test_committed_development_analysis_preserves_inference_boundary(self):
        artifact = RESULT_DIR / "case_level_analysis.json"
        self.assertTrue(artifact.is_file())
        report = json.loads(artifact.read_text(encoding="utf-8"))

        self.assertEqual("case_id", report["independent_statistical_unit"])
        self.assertEqual(6, report["independent_unit_count"])
        self.assertEqual(45, report["within_case_repeated_condition_count"])
        self.assertEqual(270, report["total_paired_condition_count"])
        self.assertFalse(report["confirmatory_p_value_claim_allowed"])
        self.assertEqual(
            self.analysis.sha256(SCRIPT),
            report["analysis_script_sha256"],
        )
        self.assertEqual(
            self.analysis.sha256(RESULT_DIR / "development_policy_results.csv"),
            report["input_sha256"]["policy_results"],
        )
        self.assertEqual(
            self.analysis.sha256(RESULT_DIR / "development_summary.json"),
            report["input_sha256"]["summary"],
        )
        effects = report["paired_case_level_effects"]
        self.assertEqual(set(self.analysis.BASELINES), set(effects))
        self.assertTrue(
            all(
                row["all_cases_pass_directional_pareto_gate"]
                for row in effects.values()
            )
        )


if __name__ == "__main__":
    unittest.main()
