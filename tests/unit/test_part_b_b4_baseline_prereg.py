from __future__ import annotations

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"
PREREGISTRATION_PATH = (
    CONFIG_DIR / "part-b-baseline-preregistration-v0.8.yaml"
)
ISOLATION_POLICY_PATH = (
    CONFIG_DIR / "part-b-baseline-isolation-policy-v0.8.yaml"
)

EXPECTED_BASELINE_IDS = [
    "NO_ACQUISITION",
    "RANDOM_FEASIBLE",
    "COVERAGE_GREEDY",
    "CMI_PROXY",
    "M1_STATIC_EXPECTED_GAIN",
    "M2_TRANSPARENT",
    "M3A_GAP_COMPATIBILITY",
    "LOGISTIC_M3B",
    "XGBOOST_ACTION_VALUE",
    "AFA_VOI_MYOPIC",
    "AFA_VOI_ROLLOUT_H3",
    "DEPTH2_PUBLIC",
    "ORACLE_EVALUATION_ONLY",
]
ALLOWED_ROLES = {"DEPLOYABLE", "REFERENCE_ONLY", "EVALUATOR_ONLY"}
FORBIDDEN_DEPLOYMENT_INPUTS = {
    "ORACLE_LABEL",
    "HIDDEN_GROUND_TRUTH",
    "HOLDOUT_LABEL",
    "REALIZED_ACTION_OUTCOME",
}
FAILURE_SEMANTICS = {
    "timeout": "UNKNOWN_NO_RANK",
    "resource_exhaustion": "UNKNOWN_NO_RANK",
    "infeasible": "SEPARATE_NO_ACTION",
    "unknown": "FAIL_CLOSED_NO_RANK",
}


def load_yaml(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B4 artifact: {path.relative_to(ROOT)}"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def baseline_index() -> dict[str, dict[str, object]]:
    preregistration = load_yaml(PREREGISTRATION_PATH)
    return {
        baseline["baseline_id"]: baseline
        for baseline in preregistration["baselines"]
    }


class PartBB4BaselinePreregistrationTests(unittest.TestCase):
    def test_red_03_roster_is_finite_unique_versioned_and_complete(self) -> None:
        """RED-03: the complete baseline roster is frozen and enumerable."""
        preregistration = load_yaml(PREREGISTRATION_PATH)
        self.assertEqual(
            preregistration["roster_semantics"],
            "FINITE_COMPLETE_PREREGISTRATION",
        )
        self.assertIs(preregistration["roster_frozen"], True)

        baselines = preregistration["baselines"]
        baseline_ids = [entry["baseline_id"] for entry in baselines]
        self.assertEqual(baseline_ids, EXPECTED_BASELINE_IDS)
        self.assertEqual(len(baseline_ids), len(set(baseline_ids)))
        for baseline in baselines:
            with self.subTest(baseline=baseline["baseline_id"]):
                self.assertEqual(baseline["contract_version"], "v0.8")
                self.assertIsInstance(baseline["method_name"], str)
                self.assertTrue(baseline["method_name"].strip())

    def test_red_04_each_baseline_declares_the_full_interface_boundary(self) -> None:
        """RED-04: every baseline declares inputs, outputs and failures."""
        for baseline_id, baseline in baseline_index().items():
            with self.subTest(baseline=baseline_id):
                self.assertIsInstance(baseline["method_family"], str)
                self.assertTrue(baseline["method_family"].strip())
                self.assertIn(baseline["role"], ALLOWED_ROLES)
                self.assertIn(
                    baseline["implementation_status"],
                    {
                        "UNVERIFIED_FAIL_CLOSED",
                        "CONTRACT_DEFINED_NOT_EXECUTABLE",
                    },
                )

                interface = baseline["interface_boundary"]
                self.assertIn("public_state_only", interface)
                self.assertIs(interface["action_id_only_output"], True)
                self.assertIs(interface["allows_no_action"], True)
                self.assertTrue(
                    FORBIDDEN_DEPLOYMENT_INPUTS.issubset(
                        set(interface["forbidden_deployment_inputs"])
                    )
                )

                lifecycle = baseline["training_and_tuning"]
                self.assertIsInstance(lifecycle["training_required"], bool)
                self.assertIsInstance(lifecycle["tuning_required"], bool)
                self.assertIn(
                    lifecycle["freeze_state"],
                    {
                        "FROZEN_BY_PREREGISTRATION",
                        "NOT_APPLICABLE",
                    },
                )

                decision = baseline["decision_contract"]
                self.assertIn(
                    decision["randomness_mode"],
                    {"DETERMINISTIC", "SEEDED_STOCHASTIC", "EVALUATOR_ONLY"},
                )
                self.assertIn(
                    decision["seed_policy"],
                    {"NOT_APPLICABLE", "PREDECLARED_FIXED"},
                )
                self.assertIsInstance(decision["tie_break_rule"], str)
                self.assertTrue(decision["tie_break_rule"].strip())
                self.assertEqual(
                    decision["failure_semantics"],
                    FAILURE_SEMANTICS,
                )

    def test_red_05_no_acquisition_and_oracle_roles_are_not_laundered(self) -> None:
        """RED-05: legacy B0 and evaluator-only Oracle stay isolated."""
        preregistration = load_yaml(PREREGISTRATION_PATH)
        baselines = baseline_index()

        self.assertEqual(
            preregistration["part_b_phase_b0_identifier"],
            "B0_PLANNING_AND_CONTRACTS",
        )
        self.assertEqual(
            preregistration["legacy_no_acquisition_baseline_id"],
            "NO_ACQUISITION",
        )
        self.assertNotEqual(
            preregistration["part_b_phase_b0_identifier"],
            preregistration["legacy_no_acquisition_baseline_id"],
        )

        oracle = baselines["ORACLE_EVALUATION_ONLY"]
        self.assertEqual(oracle["role"], "EVALUATOR_ONLY")
        self.assertIs(oracle["deployment_eligible"], False)
        self.assertIs(
            oracle["eligible_for_deployable_performance_ranking"],
            False,
        )
        self.assertIs(
            oracle["interface_boundary"]["public_state_only"],
            False,
        )

        for baseline_id, baseline in baselines.items():
            if baseline_id == "ORACLE_EVALUATION_ONLY":
                continue
            with self.subTest(public_baseline=baseline_id):
                self.assertIs(baseline["interface_boundary"]["public_state_only"], True)
                self.assertNotEqual(baseline["role"], "EVALUATOR_ONLY")

    def test_red_06_train_tune_evaluation_holdout_are_isolated(self) -> None:
        """RED-06: split boundaries are explicit, disjoint and directional."""
        policy = load_yaml(ISOLATION_POLICY_PATH)
        self.assertEqual(
            policy["partition_order"],
            ["TRAIN", "TUNE", "EVALUATION", "HOLDOUT"],
        )
        self.assertEqual(
            [row["partition_id"] for row in policy["partitions"]],
            ["TRAIN", "TUNE", "EVALUATION", "HOLDOUT"],
        )
        self.assertIs(policy["isolation"]["mutually_disjoint"], True)
        self.assertIs(
            policy["isolation"]["holdout_visible_before_final_freeze"],
            False,
        )
        self.assertIs(
            policy["isolation"]["evaluation_outcomes_flow_to_training"],
            False,
        )
        self.assertIs(
            policy["isolation"]["holdout_outcomes_flow_to_any_model"],
            False,
        )

    def test_red_07_roster_parameters_endpoints_and_seeds_freeze_early(self) -> None:
        """RED-07: outcome-dependent preregistration mutation is forbidden."""
        policy = load_yaml(ISOLATION_POLICY_PATH)
        freeze = policy["registration_freeze"]
        self.assertIs(freeze["must_precede_evaluation"], True)
        for field in (
            "roster_mutation_after_first_outcome",
            "parameter_mutation_after_first_outcome",
            "endpoint_mutation_after_first_outcome",
            "seed_mutation_after_first_outcome",
            "tie_break_mutation_after_first_outcome",
        ):
            with self.subTest(field=field):
                self.assertIs(freeze[field], False)

    def test_red_08_historical_results_cannot_complete_registration(self) -> None:
        """RED-08: old results, labels and outcomes cannot leak into B4."""
        policy = load_yaml(ISOLATION_POLICY_PATH)
        historical = policy["historical_artifacts"]
        self.assertIs(
            historical["may_supply_registration_parameters"],
            False,
        )
        self.assertIn(
            "09-experiments/",
            historical["forbidden_path_prefixes"],
        )
        self.assertTrue(
            {
                "HISTORICAL_RESULT",
                "REALIZED_ACTION_OUTCOME",
                "HOLDOUT_LABEL",
                "ORACLE_WORLD_ID",
            }.issubset(set(historical["prohibited_material"]))
        )
        self.assertEqual(
            historical["violation_behavior"],
            "FAIL_CLOSED_REGISTRATION_REJECTED",
        )


if __name__ == "__main__":
    unittest.main()
