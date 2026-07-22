import copy
import unittest

from src.checker.finite_domain import CheckerStatus, FiniteDomainChecker


try:
    from src.scope.finite_problem import EvidenceGammaFiniteProblemCompiler
except (ImportError, ModuleNotFoundError):
    EvidenceGammaFiniteProblemCompiler = None


def gamma_contract():
    return {
        "schema_version": "0.8.0",
        "attribution_levels": ["entry_host"],
        "result_domains": {
            "entry_host": {
                "generator": "from_finite_candidate_list",
                "finite_candidates": ["NODE-A", "NODE-B"],
                "coverage_mode": "exhaustive",
                "finiteness_basis": "explicit_finite_candidates",
            }
        },
        "mechanism_rules": [
            "credential_login_implies_authentication",
            "lateral_movement_requires_prior_compromise",
        ],
    }


def admitted_claim(claim_id, predicate, host):
    return {
        "claim_id": claim_id,
        "subject": {"entity_id": host, "entity_type": "host"},
        "predicate": predicate,
        "modality": "observed",
        "truth_status": "supported",
        "epistemic_role": "case_evidence",
        "certification_authority": {"allowed": True},
        "binding_status": "bound",
        "admission_status": "admitted",
        "lifecycle_state": "admitted",
    }


def case_evidence():
    return (
        admitted_claim("EC-AUTH", "authenticated_account", "NODE-B"),
        admitted_claim("EC-EXEC", "executed_process", "NODE-A"),
    )


class EvidenceGammaFiniteProblemCompilerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            EvidenceGammaFiniteProblemCompiler,
            "evidence/Gamma finite problem compiler is missing",
        )

    def test_compiles_worlds_from_gamma_and_admitted_evidence_values(self):
        compiled = EvidenceGammaFiniteProblemCompiler().compile(
            gamma_contract(), case_evidence(), target_variable="entry_host"
        )

        self.assertEqual(
            ("NODE-A", "NODE-B"), compiled.problem.domains["entry_host"]
        )
        self.assertEqual(
            ("lateral", "direct"),
            compiled.problem.domains[compiled.mode_variable],
        )
        self.assertEqual("NODE-A", compiled.possible_lateral_source)
        self.assertEqual("NODE-B", compiled.destination_host)
        self.assertEqual(("EC-AUTH", "EC-EXEC"), compiled.source_claim_ids)

        result = FiniteDomainChecker().check_candidate(
            compiled.problem,
            target_variable=compiled.target_variable,
            candidate=compiled.possible_lateral_source,
        )
        self.assertEqual(CheckerStatus.COUNTEREXAMPLE_FOUND, result.checker_status)
        self.assertEqual(
            "NODE-A", result.support.witness[compiled.target_variable]
        )
        self.assertEqual(
            "NODE-B", result.alternative.witness[compiled.target_variable]
        )

    def test_missing_rule_nonunique_evidence_and_oracle_fields_fail_closed(self):
        compiler = EvidenceGammaFiniteProblemCompiler()

        missing_rule = gamma_contract()
        missing_rule["mechanism_rules"].remove(
            "lateral_movement_requires_prior_compromise"
        )
        with self.assertRaises(ValueError):
            compiler.compile(
                missing_rule, case_evidence(), target_variable="entry_host"
            )

        duplicate_source = case_evidence() + (
            admitted_claim("EC-EXEC-2", "executed_process", "NODE-B"),
        )
        with self.assertRaises(ValueError):
            compiler.compile(
                gamma_contract(), duplicate_source, target_variable="entry_host"
            )

        oracle = list(copy.deepcopy(case_evidence()))
        oracle[0]["ground_truth"] = "NODE-A"
        with self.assertRaises(ValueError):
            compiler.compile(gamma_contract(), oracle, target_variable="entry_host")


if __name__ == "__main__":
    unittest.main()
