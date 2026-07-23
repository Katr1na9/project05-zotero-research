import importlib
import unittest

from tests.integration.twin_kernel_inputs import load_twin_kernel_inputs


try:
    checker_api = importlib.import_module("src.checker.finite_domain")
except (ImportError, ModuleNotFoundError):
    checker_api = None


CHECKER_FIELDS = ("base", "support", "alternative", "checker_status")


class TwinCheckerP1IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(checker_api, "P1 finite-domain Checker API is missing")

    def test_expected_checker_outcome_is_recomputed_from_gamma_and_case_evidence(self):
        inputs = load_twin_kernel_inputs()
        compiled = inputs.compiled
        target_level = compiled.target_variable
        result_domain = inputs.gamma["result_domains"][target_level]
        self.assertEqual("from_finite_candidate_list", result_domain["generator"])
        self.assertEqual("explicit_finite_candidates", result_domain["finiteness_basis"])
        self.assertIn(
            "credential_login_implies_authentication",
            inputs.gamma["mechanism_rules"],
        )
        self.assertIn(
            "lateral_movement_requires_prior_compromise",
            inputs.gamma["mechanism_rules"],
        )

        actual = checker_api.FiniteDomainChecker().check_candidate(
            compiled.problem,
            target_variable=target_level,
            candidate=inputs.expected["candidate_q"],
        )
        expected_checker_fields = {
            key: inputs.expected[key] for key in CHECKER_FIELDS
        }

        self.assertEqual(expected_checker_fields, actual.to_outcome_fields())
        self.assertNotIn("system_status", actual.to_outcome_fields())
        self.assertEqual(
            compiled.destination_host,
            actual.alternative.witness[target_level],
        )
        self.assertEqual(
            tuple(sorted(claim["claim_id"] for claim in inputs.case_evidence)),
            compiled.source_claim_ids,
        )


if __name__ == "__main__":
    unittest.main()
