import unittest

from src.checker.finite_domain import FiniteDomainChecker
from tests.unit.test_evidence_gamma_problem_compiler import (
    case_evidence,
    gamma_contract,
)


try:
    from src.counterexample.mindiff import (
        FiniteWitnessMinDiff,
        PredicateProjectionContract,
    )
    from src.scope.finite_problem import EvidenceGammaFiniteProblemCompiler
except (ImportError, ModuleNotFoundError):
    PredicateProjectionContract = None
    EvidenceGammaFiniteProblemCompiler = None


def action(action_id, dependency):
    return {
        "action_id": action_id,
        "observation_model": {"world_dependencies": [dependency]},
    }


def catalog():
    return {
        "schema_version": "0.8.0",
        "catalog_id": "unit-catalog",
        "catalog_version": "0.8.0",
        "actions": [
            action("query-credential", "credential_activity:NODE-A"),
            action("query-origin", "authentication_origin:NODE-B"),
        ],
    }


def projection_document():
    return {
        "schema_version": "0.8.0",
        "contract_id": "unit-projections",
        "catalog_id": "unit-catalog",
        "catalog_version": "0.8.0",
        "bindings": {
            "entry_host": "query-credential",
            "authentication_mode": "query-origin",
        },
    }


class PredicateProjectionContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            PredicateProjectionContract, "predicate projection contract is missing"
        )
        self.compiled = EvidenceGammaFiniteProblemCompiler().compile(
            gamma_contract(), case_evidence(), target_variable="entry_host"
        )

    def test_resolves_only_catalog_declared_dependencies(self):
        contract = PredicateProjectionContract.from_action_catalog(
            projection_document(),
            catalog(),
            witness_variables=self.compiled.problem.domains,
        )

        self.assertEqual(
            {
                "entry_host": "credential_activity:NODE-A",
                "authentication_mode": "authentication_origin:NODE-B",
            },
            dict(contract.projections),
        )

        checker_run = FiniteDomainChecker().check_candidate(
            self.compiled.problem,
            target_variable=self.compiled.target_variable,
            candidate=self.compiled.possible_lateral_source,
        )
        result = FiniteWitnessMinDiff().compare(
            checker_run,
            target_variable=self.compiled.target_variable,
            predicate_projections=contract,
        )
        self.assertEqual(
            ("authentication_origin:NODE-B", "credential_activity:NODE-A"),
            result.distinguishing_predicates,
        )

    def test_unknown_action_ambiguous_dependency_and_raw_mapping_are_rejected(self):
        unknown = projection_document()
        unknown["bindings"]["entry_host"] = "ghost-action"
        with self.assertRaises(ValueError):
            PredicateProjectionContract.from_action_catalog(
                unknown, catalog(), witness_variables=self.compiled.problem.domains
            )

        ambiguous_catalog = catalog()
        ambiguous_catalog["actions"][0]["observation_model"][
            "world_dependencies"
        ].append("undeclared-second-meaning")
        with self.assertRaises(ValueError):
            PredicateProjectionContract.from_action_catalog(
                projection_document(),
                ambiguous_catalog,
                witness_variables=self.compiled.problem.domains,
            )

        checker_run = FiniteDomainChecker().check_candidate(
            self.compiled.problem,
            target_variable=self.compiled.target_variable,
            candidate=self.compiled.possible_lateral_source,
        )
        with self.assertRaises(ValueError):
            FiniteWitnessMinDiff().compare(
                checker_run,
                target_variable=self.compiled.target_variable,
                predicate_projections={"entry_host": "ghost-predicate"},
            )


if __name__ == "__main__":
    unittest.main()
