import importlib
import unittest


try:
    checker_api = importlib.import_module("src.checker.finite_domain")
except (ImportError, ModuleNotFoundError):
    checker_api = None


TRUTH_TABLE = (
    ("UNSAT", "NOT_RUN", "NOT_RUN", "SCOPE_MISMATCH_SUSPECTED"),
    ("SAT", "UNSAT", "NOT_RUN", "REJECT_CANDIDATE"),
    ("SAT", "SAT", "SAT", "COUNTEREXAMPLE_FOUND"),
    ("SAT", "SAT", "UNSAT", "CANDIDATE_CERTIFIED"),
    ("SAT", "TIMEOUT", "NOT_RUN", "UNKNOWN"),
    ("SAT", "SAT", "TIMEOUT", "UNKNOWN"),
    ("TIMEOUT", "NOT_RUN", "NOT_RUN", "UNKNOWN"),
)


class FiniteDomainCheckerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(checker_api, "P1 finite-domain Checker API is missing")

    def test_checker_binds_all_seven_truth_table_rows(self):
        for base, support, alternative, expected in TRUTH_TABLE:
            with self.subTest(base=base, support=support, alternative=alternative):
                actual = checker_api.classify_query_results(
                    checker_api.QueryStatus(base),
                    checker_api.QueryStatus(support),
                    checker_api.QueryStatus(alternative),
                )
                self.assertEqual(expected, actual.value)

    def test_candidate_and_alternative_worlds_produce_counterexample_found(self):
        problem = checker_api.FiniteDomainProblem(
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

        result = checker_api.FiniteDomainChecker().check_candidate(
            problem,
            target_variable="initial_foothold",
            candidate="H1",
        )

        self.assertEqual(
            {
                "base": "SAT",
                "support": "SAT",
                "alternative": "SAT",
                "checker_status": "COUNTEREXAMPLE_FOUND",
            },
            result.to_outcome_fields(),
        )
        self.assertEqual("H1", result.support.witness["initial_foothold"])
        self.assertEqual("H3", result.alternative.witness["initial_foothold"])

    def test_unique_candidate_is_candidate_certified_not_system_stop(self):
        problem = checker_api.FiniteDomainProblem(
            domains={"initial_foothold": ("H1", "H3")},
            constraints=(lambda world: world["initial_foothold"] == "H1",),
        )

        result = checker_api.FiniteDomainChecker().check_candidate(
            problem,
            target_variable="initial_foothold",
            candidate="H1",
        )

        self.assertEqual("CANDIDATE_CERTIFIED", result.checker_status.value)
        self.assertEqual("UNSAT", result.alternative.status.value)
        self.assertNotIn("system_status", result.to_outcome_fields())

    def test_infeasible_candidate_is_rejected_without_alternative_query(self):
        problem = checker_api.FiniteDomainProblem(
            domains={"initial_foothold": ("H1", "H3")},
            constraints=(lambda world: world["initial_foothold"] == "H3",),
        )

        result = checker_api.FiniteDomainChecker().check_candidate(
            problem,
            target_variable="initial_foothold",
            candidate="H1",
        )

        self.assertEqual("SAT", result.base.status.value)
        self.assertEqual("UNSAT", result.support.status.value)
        self.assertEqual("NOT_RUN", result.alternative.status.value)
        self.assertEqual("REJECT_CANDIDATE", result.checker_status.value)

    def test_infeasible_base_reports_scope_mismatch_and_skips_later_queries(self):
        problem = checker_api.FiniteDomainProblem(
            domains={"initial_foothold": ("H1", "H3")},
            constraints=(lambda _world: False,),
        )

        result = checker_api.FiniteDomainChecker().check_candidate(
            problem,
            target_variable="initial_foothold",
            candidate="H1",
        )

        self.assertEqual("UNSAT", result.base.status.value)
        self.assertEqual("NOT_RUN", result.support.status.value)
        self.assertEqual("NOT_RUN", result.alternative.status.value)
        self.assertEqual("SCOPE_MISMATCH_SUSPECTED", result.checker_status.value)

    def test_resource_exhaustion_is_timeout_unknown_never_unsat(self):
        problem = checker_api.FiniteDomainProblem(
            domains={"initial_foothold": ("H1", "H3")},
            constraints=(lambda world: world["initial_foothold"] == "H3",),
        )

        result = checker_api.FiniteDomainChecker(max_assignments=1).check_candidate(
            problem,
            target_variable="initial_foothold",
            candidate="H3",
        )

        self.assertEqual("TIMEOUT", result.base.status.value)
        self.assertEqual("UNKNOWN", result.checker_status.value)
        self.assertEqual("NOT_RUN", result.support.status.value)
        self.assertEqual("NOT_RUN", result.alternative.status.value)

    def test_problem_rejects_empty_or_duplicate_domains(self):
        with self.assertRaises(ValueError):
            checker_api.FiniteDomainProblem(domains={"target": ()})
        with self.assertRaises(ValueError):
            checker_api.FiniteDomainProblem(domains={"target": ("H1", "H1")})


if __name__ == "__main__":
    unittest.main()
