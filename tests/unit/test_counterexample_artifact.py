import importlib
import json
import unittest

from src.checker.finite_domain import FiniteDomainChecker, FiniteDomainProblem
from src.counterexample.mindiff import FiniteWitnessMinDiff
from tests.unit.kernel_contract_helpers import projection_contract


try:
    artifact_api = importlib.import_module("src.counterexample.artifact")
except (ImportError, ModuleNotFoundError):
    artifact_api = None


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


def metadata():
    return artifact_api.CounterexampleArtifactMetadata(
        counterexample_id="CEX-UNIT-001",
        case_id="CASE-UNIT-001",
        gamma_hash="sha256:" + "1" * 64,
        evidence_hash="sha256:" + "2" * 64,
        target_level="initial_foothold",
        result_entity_type="host",
        support_world_id="W-SUPPORT-H1",
        alternative_world_id="W-ALTERNATIVE-H3",
        support_world_predicates=(
            "credential_activity:H1",
            "authentication_origin:H3=H1",
            "compromised:H3",
        ),
        alternative_world_predicates=(
            "external_credential_login:H3",
            "authentication_origin:H3=EXTERNAL",
            "compromised:H3",
        ),
        shared_predicates=("compromised:H3",),
        critical_absence_semantics=("auth-H1:bounded_completeness",),
    )


class CounterexampleArtifactAssemblerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            artifact_api, "P3 counterexample artifact assembler API is missing"
        )

    def test_assembles_deterministic_schema_shaped_counterexample(self):
        checker_run = counterexample_run()
        mindiff = FiniteWitnessMinDiff().compare(
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

        assembler = artifact_api.CounterexampleArtifactAssembler()
        first = assembler.assemble(checker_run, mindiff, metadata())
        second = assembler.assemble(checker_run, mindiff, metadata())

        self.assertEqual(
            json.dumps(first, separators=(",", ":")),
            json.dumps(second, separators=(",", ":")),
        )
        self.assertEqual("COUNTEREXAMPLE_FOUND", first["checker_status"])
        self.assertEqual(
            {"base": "SAT", "support": "SAT", "alternative": "SAT"},
            first["core_query_results"],
        )
        self.assertEqual(
            {"entity_id": "H1", "entity_type": "host"}, first["candidate_q"]
        )
        self.assertEqual(
            ["credential_activity:H1", "authentication_origin:H3=H1"],
            first["support_only_predicates"],
        )
        self.assertEqual(
            ["external_credential_login:H3", "authentication_origin:H3=EXTERNAL"],
            first["alternative_only_predicates"],
        )
        self.assertEqual("OPTIMAL", first["minimization_status"])
        self.assertNotIn("system_status", first)
        self.assertNotIn("CERTIFIED_STOP", first.values())

    def test_timeout_is_passed_through_without_rewriting_checker_status(self):
        checker_run = counterexample_run()
        mindiff = FiniteWitnessMinDiff(max_comparisons=1).compare(
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

        artifact = artifact_api.CounterexampleArtifactAssembler().assemble(
            checker_run, mindiff, metadata()
        )

        self.assertEqual("COUNTEREXAMPLE_FOUND", artifact["checker_status"])
        self.assertEqual("TIMEOUT", artifact["minimization_status"])
        self.assertNotIn("system_status", artifact)

    def test_rejects_mindiff_from_a_different_checker_witness_pair(self):
        checker_run = counterexample_run()
        other_problem = FiniteDomainProblem(
            domains={
                "initial_foothold": ("H2", "H4"),
                "authentication_mode": ("lateral", "direct"),
            },
            constraints=(
                lambda world: (
                    world["initial_foothold"], world["authentication_mode"]
                )
                in {("H2", "lateral"), ("H4", "direct")},
            ),
        )
        other_run = FiniteDomainChecker().check_candidate(
            other_problem,
            target_variable="initial_foothold",
            candidate="H2",
        )
        other_mindiff = FiniteWitnessMinDiff().compare(
            other_run,
            target_variable="initial_foothold",
            predicate_projections=projection_contract(
                {
                    "authentication_mode": "authentication_origin:H4",
                    "initial_foothold": "credential_activity:H2",
                },
                other_run.support.witness,
            ),
        )

        with self.assertRaises(ValueError):
            artifact_api.CounterexampleArtifactAssembler().assemble(
                checker_run, other_mindiff, metadata()
            )

    def test_metadata_rejects_noncanonical_hashes_and_duplicate_predicates(self):
        with self.assertRaises(ValueError):
            artifact_api.CounterexampleArtifactMetadata(
                counterexample_id="CEX-UNIT-001",
                case_id="CASE-UNIT-001",
                gamma_hash="not-a-hash",
                evidence_hash="sha256:" + "2" * 64,
                target_level="initial_foothold",
                result_entity_type="host",
                support_world_id="W-SUPPORT-H1",
                alternative_world_id="W-ALTERNATIVE-H3",
                support_world_predicates=("p",),
                alternative_world_predicates=("q",),
                shared_predicates=(),
                critical_absence_semantics=(),
            )

        with self.assertRaises(ValueError):
            artifact_api.CounterexampleArtifactMetadata(
                counterexample_id="CEX-UNIT-001",
                case_id="CASE-UNIT-001",
                gamma_hash="sha256:" + "1" * 64,
                evidence_hash="sha256:" + "2" * 64,
                target_level="initial_foothold",
                result_entity_type="host",
                support_world_id="W-SUPPORT-H1",
                alternative_world_id="W-ALTERNATIVE-H3",
                support_world_predicates=("p", "p"),
                alternative_world_predicates=("q",),
                shared_predicates=(),
                critical_absence_semantics=(),
            )


if __name__ == "__main__":
    unittest.main()
