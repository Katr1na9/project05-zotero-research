import importlib
import unittest

from src.checker.finite_domain import FiniteDomainChecker
from tests.integration.twin_kernel_inputs import load_twin_kernel_inputs


try:
    mindiff_api = importlib.import_module("src.counterexample.mindiff")
except (ImportError, ModuleNotFoundError):
    mindiff_api = None


class TwinMinDiffP2IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(mindiff_api, "P2 finite-witness MinDiff API is missing")

    def test_twin_witnesses_reproduce_frozen_disagreement_and_predicates(self):
        inputs = load_twin_kernel_inputs()
        compiled = inputs.compiled
        target_level = compiled.target_variable
        checker_run = FiniteDomainChecker().check_candidate(
            compiled.problem,
            target_variable=target_level,
            candidate=inputs.expected["candidate_q"],
        )

        result = mindiff_api.FiniteWitnessMinDiff().compare(
            checker_run,
            target_variable=target_level,
            predicate_projections=inputs.predicate_projections,
        )

        self.assertEqual(
            inputs.expected["checker_status"], result.checker_status.value
        )
        self.assertEqual(
            inputs.expected["mindiff_disagreement"],
            dict(result.mindiff_disagreement),
        )
        self.assertEqual(
            tuple(inputs.expected["distinguishing_predicates"]),
            result.distinguishing_predicates,
        )
        self.assertEqual("OPTIMAL", result.minimization_status.value)
        self.assertNotIn("system_status", result.to_outcome_fields())


if __name__ == "__main__":
    unittest.main()
