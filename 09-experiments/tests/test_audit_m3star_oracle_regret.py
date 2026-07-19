import importlib.util
import math
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "audit_m3star_oracle_regret.py"
)
OBSERVABILITY_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "audit_m3star_observability_bound.py"
)


def load_audit(testcase: unittest.TestCase):
    testcase.assertTrue(SCRIPT.is_file())
    spec = importlib.util.spec_from_file_location(
        "audit_m3star_oracle_regret",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_observability_audit(testcase: unittest.TestCase):
    testcase.assertTrue(OBSERVABILITY_SCRIPT.is_file())
    spec = importlib.util.spec_from_file_location(
        "audit_m3star_observability_bound",
        OBSERVABILITY_SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OracleRegretClassificationTests(unittest.TestCase):
    def test_learned_head_majority_requires_two_directional_votes(self):
        audit = load_audit(self)
        candidate = {
            "action_value_probability": 0.8,
            "action_reachability_probability": 0.4,
            "action_cost_to_go": 1.0,
        }
        baseline = {
            "action_value_probability": 0.7,
            "action_reachability_probability": 0.6,
            "action_cost_to_go": 2.0,
        }
        self.assertTrue(
            audit.run_m3star._learned_head_majority_prefers(
                candidate,
                baseline,
            )
        )
        candidate["action_cost_to_go"] = 3.0
        self.assertFalse(
            audit.run_m3star._learned_head_majority_prefers(
                candidate,
                baseline,
            )
        )

    def test_equal_cost_different_first_actions_are_zero_regret(self):
        audit = load_audit(self)
        result = audit.classify_regret(
            oracle_cost=2.0,
            oracle_path=["A", "B"],
            policy_success=True,
            policy_cost=2.0,
            policy_path=["C", "D"],
        )
        self.assertEqual("zero", result["regret_status"])
        self.assertEqual(0.0, result["absolute_regret"])
        self.assertEqual(0, result["first_action_match"])

    def test_successful_higher_cost_policy_has_positive_regret(self):
        audit = load_audit(self)
        result = audit.classify_regret(
            oracle_cost=1.5,
            oracle_path=["A"],
            policy_success=True,
            policy_cost=2.0,
            policy_path=["B"],
        )
        self.assertEqual("positive", result["regret_status"])
        self.assertAlmostEqual(0.5, result["absolute_regret"])
        self.assertAlmostEqual(1.0 / 3.0, result["relative_regret"])

    def test_policy_failure_when_oracle_succeeds_is_unbounded(self):
        audit = load_audit(self)
        result = audit.classify_regret(
            oracle_cost=1.0,
            oracle_path=["A"],
            policy_success=False,
            policy_cost=0.0,
            policy_path=["STOP"],
        )
        self.assertEqual("unbounded_success_loss", result["regret_status"])
        self.assertEqual(1, result["success_loss"])
        self.assertIsNone(result["absolute_regret"])

    def test_both_unreachable_is_reported_not_treated_as_zero(self):
        audit = load_audit(self)
        result = audit.classify_regret(
            oracle_cost=math.inf,
            oracle_path=[],
            policy_success=False,
            policy_cost=0.0,
            policy_path=["STOP"],
        )
        self.assertEqual("both_unreachable", result["regret_status"])
        self.assertEqual(0, result["zero_regret"])
        self.assertIsNone(result["absolute_regret"])


class OracleRegretSummaryTests(unittest.TestCase):
    @staticmethod
    def row(state_id, depth, classification, **updates):
        row = {
            "case_id": "C-test",
            "state_id": state_id,
            "state_depth": depth,
            "prefix_action_path": "",
            "oracle_cost_to_go": 1.0,
            "oracle_action_path": "A",
            "m3star_cost_to_go": 1.0,
            "m3star_action_path": "A",
            "m3star_terminal_reason": "target_reached",
            **classification,
        }
        row.update(updates)
        return row

    def test_zero_regret_rows_issue_exact_enumerated_certificate(self):
        audit = load_audit(self)
        exact = audit.classify_regret(
            oracle_cost=1.0,
            oracle_path=["A"],
            policy_success=True,
            policy_cost=1.0,
            policy_path=["A"],
        )
        summary = audit.summarize_regret_rows(
            [self.row("s0", 0, exact), self.row("s1", 1, exact)]
        )
        self.assertEqual(
            "exact_optimal_within_enumerated_frozen_model",
            summary["certificate"]["claim_status"],
        )
        self.assertEqual(0.0, summary["certificate"]["epsilon_absolute_cost"])
        self.assertEqual(1.0, summary["overall"]["zero_regret_state_proportion"])

    def test_worst_state_and_unbounded_failure_are_not_averaged_away(self):
        audit = load_audit(self)
        positive = audit.classify_regret(
            oracle_cost=1.0,
            oracle_path=["A"],
            policy_success=True,
            policy_cost=1.25,
            policy_path=["B"],
        )
        failure = audit.classify_regret(
            oracle_cost=1.0,
            oracle_path=["A"],
            policy_success=False,
            policy_cost=0.0,
            policy_path=["STOP"],
        )
        summary = audit.summarize_regret_rows(
            [
                self.row("finite", 0, positive, m3star_cost_to_go=1.25),
                self.row(
                    "failure",
                    1,
                    failure,
                    m3star_cost_to_go=0.0,
                    m3star_action_path="STOP",
                    m3star_terminal_reason="explicit_stop",
                ),
            ]
        )
        self.assertEqual(
            "unbounded_due_to_success_loss",
            summary["certificate"]["claim_status"],
        )
        self.assertIsNone(summary["certificate"]["epsilon_absolute_cost"])
        self.assertEqual(1, summary["overall"]["success_loss_count"])
        self.assertEqual("failure", summary["worst_states"][0]["state_id"])


class ObservabilityLowerBoundTests(unittest.TestCase):
    def test_conflicting_hidden_optima_force_positive_public_policy_bound(self):
        audit = load_observability_audit(self)
        result = audit.minimax_first_action_regret(
            [1.0, 1.0],
            {
                "A": [1.0, 2.0],
                "B": [2.0, 1.0],
            },
        )
        self.assertEqual(1.0, result["lower_bound"])
        self.assertEqual(["A", "B"], result["minimax_action_ids"])

    def test_shared_optimal_action_allows_zero_public_policy_bound(self):
        audit = load_observability_audit(self)
        result = audit.minimax_first_action_regret(
            [1.0, 2.0],
            {
                "A": [1.0, 2.0],
                "B": [2.0, 3.0],
            },
        )
        self.assertEqual(0.0, result["lower_bound"])
        self.assertEqual(["A"], result["minimax_action_ids"])

    def test_action_unreachable_in_one_alias_is_not_a_minimax_candidate(self):
        audit = load_observability_audit(self)
        result = audit.minimax_first_action_regret(
            [1.0, 1.0],
            {
                "unsafe": [1.0, math.inf],
                "safe": [2.0, 2.0],
            },
        )
        self.assertEqual(1.0, result["lower_bound"])
        self.assertEqual(["safe"], result["minimax_action_ids"])


if __name__ == "__main__":
    unittest.main()
