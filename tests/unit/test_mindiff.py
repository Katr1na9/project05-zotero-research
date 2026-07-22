import importlib
import unittest

from src.checker.finite_domain import FiniteDomainChecker, FiniteDomainProblem
from src.counterexample.mindiff import PredicateProjectionContract
from tests.unit.kernel_contract_helpers import projection_contract


try:
    mindiff_api = importlib.import_module("src.counterexample.mindiff")
except (ImportError, ModuleNotFoundError):
    mindiff_api = None


def counterexample_run():
    problem = FiniteDomainProblem(
        domains={
            "initial_foothold": ("H1", "H3"),
            "authentication_mode": ("lateral", "direct"),
        },
        constraints=(
            lambda world: (
                world["initial_foothold"], world["authentication_mode"]
            )
            in {("H1", "lateral"), ("H3", "direct")},
        ),
    )
    return FiniteDomainChecker().check_candidate(
        problem,
        target_variable="initial_foothold",
        candidate="H1",
    )


class FiniteWitnessMinDiffTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(mindiff_api, "P2 finite-witness MinDiff API is missing")

    def test_complete_comparison_emits_deterministic_minimal_difference(self):
        checker_run = counterexample_run()
        result = mindiff_api.FiniteWitnessMinDiff().compare(
            checker_run,
            target_variable="initial_foothold",
            predicate_projections=projection_contract(
                {
                    "authentication_mode": "authentication_origin:H3",
                    "initial_foothold": "credential_activity:H1",
                },
                checker_run.support.witness,
            ),
        )

        self.assertEqual("COUNTEREXAMPLE_FOUND", result.checker_status.value)
        self.assertEqual("OPTIMAL", result.minimization_status.value)
        self.assertEqual(
            {"support_world": "H1", "alternative_world": "H3"},
            dict(result.mindiff_disagreement),
        )
        self.assertEqual(
            ("authentication_mode", "initial_foothold"),
            result.differing_variables,
        )
        self.assertEqual(
            ("authentication_origin:H3", "credential_activity:H1"),
            result.distinguishing_predicates,
        )
        self.assertEqual((), result.unprojected_variables)
        self.assertEqual(2, result.comparisons_examined)

    def test_timeout_preserves_counterexample_and_never_emits_system_state(self):
        checker_run = counterexample_run()
        result = mindiff_api.FiniteWitnessMinDiff(max_comparisons=1).compare(
            checker_run,
            target_variable="initial_foothold",
            predicate_projections=projection_contract(
                {
                    "authentication_mode": "authentication_origin:H3",
                    "initial_foothold": "credential_activity:H1",
                },
                checker_run.support.witness,
            ),
        )

        fields = result.to_outcome_fields()
        self.assertEqual("COUNTEREXAMPLE_FOUND", fields["checker_status"])
        self.assertEqual("TIMEOUT", fields["minimization_status"])
        self.assertNotIn("system_status", fields)
        self.assertNotIn("CERTIFIED_STOP", fields.values())

    def test_unprojected_differences_remain_auditable(self):
        checker_run = counterexample_run()
        result = mindiff_api.FiniteWitnessMinDiff().compare(
            checker_run,
            target_variable="initial_foothold",
            predicate_projections=projection_contract(
                {"initial_foothold": "credential_activity:H1"},
                checker_run.support.witness,
            ),
        )

        self.assertEqual(("authentication_mode",), result.unprojected_variables)
        self.assertEqual(
            ("credential_activity:H1",), result.distinguishing_predicates
        )

    def test_non_counterexample_checker_run_is_rejected(self):
        problem = FiniteDomainProblem(
            domains={"initial_foothold": ("H1", "H3")},
            constraints=(lambda world: world["initial_foothold"] == "H1",),
        )
        candidate_certified = FiniteDomainChecker().check_candidate(
            problem,
            target_variable="initial_foothold",
            candidate="H1",
        )

        with self.assertRaises(ValueError):
            mindiff_api.FiniteWitnessMinDiff().compare(
                candidate_certified,
                target_variable="initial_foothold",
                predicate_projections=PredicateProjectionContract.empty(
                    problem.domains
                ),
            )

    def test_invalid_comparison_budget_is_rejected(self):
        for value in (0, -1, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    mindiff_api.FiniteWitnessMinDiff(max_comparisons=value)


if __name__ == "__main__":
    unittest.main()
