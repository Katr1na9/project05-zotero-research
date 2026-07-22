import importlib
import unittest

from src.counterexample.artifact import CounterexampleArtifactMetadata
from src.executor.deterministic import FrozenExecutionTables
from tests.integration.twin_kernel_inputs import load_twin_kernel_inputs


try:
    driver_api = importlib.import_module("src.cli.kernel_e2e")
except (ImportError, ModuleNotFoundError):
    driver_api = None


def twin_request(*, feedback_observation_ids=(), observation_admission=None):
    inputs = load_twin_kernel_inputs()
    gamma = inputs.gamma
    catalog = inputs.catalog
    frozen = inputs.frozen_counterexample
    expected = inputs.expected
    target_level = inputs.compiled.target_variable
    metadata = CounterexampleArtifactMetadata(
        counterexample_id=frozen["counterexample_id"],
        case_id=frozen["case_id"],
        gamma_hash=frozen["gamma_hash"],
        evidence_hash=frozen["evidence_hash"],
        target_level=target_level,
        result_entity_type=frozen["candidate_q"]["entity_type"],
        support_world_id=frozen["support_world"]["world_id"],
        alternative_world_id=frozen["alternative_world"]["world_id"],
        support_world_predicates=tuple(frozen["support_world"]["predicates"]),
        alternative_world_predicates=tuple(
            frozen["alternative_world"]["predicates"]
        ),
        shared_predicates=tuple(frozen["shared_predicates"]),
        critical_absence_semantics=tuple(
            frozen["critical_absence_semantics"]
        ),
    )
    tables = FrozenExecutionTables(
        observation_rows=inputs.observation_rows,
        resource_rows=inputs.resource_rows,
    )
    return driver_api.KernelE2ERunRequest(
        gamma_contract=gamma,
        problem=inputs.compiled.problem,
        target_variable=target_level,
        candidate=expected["candidate_q"],
        predicate_projections=inputs.predicate_projections,
        artifact_metadata=metadata,
        action_catalog=catalog,
        execution_tables=tables,
        feedback_observation_ids=feedback_observation_ids,
        observation_admission=observation_admission,
        compiled_problem=inputs.compiled,
    )


class TwinKernelE2EP10IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(driver_api, "P10 deterministic E2E driver is missing")
        self.expected = load_twin_kernel_inputs().expected

    def test_twin_default_path_closes_counterexample_to_continue_chain(self):
        result = driver_api.DeterministicKernelE2EDriver().run(twin_request())

        self.assertEqual(
            "COUNTEREXAMPLE_FOUND", result.checker_run.checker_status.value
        )
        self.assertEqual(
            self.expected["mindiff_disagreement"],
            dict(result.mindiff_result.mindiff_disagreement),
        )
        self.assertEqual(
            tuple(self.expected["allowed_actions"]),
            result.action_selection.allowed_actions,
        )
        self.assertEqual(
            tuple(self.expected["forbidden_actions"]),
            result.action_selection.forbidden_actions,
        )
        self.assertEqual(
            ("OBS-001", "OBS-002"),
            tuple(row["observation_id"] for row in result.execution_result.observations),
        )
        self.assertIsNone(result.recertification_result)
        self.assertEqual((), result.feedback_observation_ids)
        self.assertEqual(
            self.expected["system_status"], result.system_state.system_status.value
        )
        self.assertIsNone(result.system_state.certificate_id)

        fields = result.to_outcome_fields()
        for field in (
            "base",
            "support",
            "alternative",
            "checker_status",
            "allowed_actions",
            "forbidden_actions",
            "system_status",
        ):
            self.assertEqual(self.expected[field], fields[field])

    def test_twin_driver_is_deterministic_for_identical_frozen_inputs(self):
        driver = driver_api.DeterministicKernelE2EDriver()

        first = driver.run(twin_request()).to_outcome_fields()
        second = driver.run(twin_request()).to_outcome_fields()

        self.assertEqual(first, second)
        self.assertNotIn("planner_decision", first)
        self.assertNotIn("probability", first)

    def test_single_hit_feedback_recertifies_candidate_but_does_not_stop(self):
        result = driver_api.DeterministicKernelE2EDriver().run(
            twin_request(feedback_observation_ids=("OBS-001",))
        )

        self.assertEqual(
            "COUNTEREXAMPLE_FOUND", result.checker_run.checker_status.value
        )
        self.assertIsNotNone(result.recertification_result)
        self.assertEqual(
            "CANDIDATE_CERTIFIED",
            result.recertification_result.checker_run.checker_status.value,
        )
        self.assertEqual(("OBS-001",), result.feedback_observation_ids)
        self.assertEqual("CONTINUE", result.system_state.system_status.value)
        self.assertTrue(result.system_state.conditional)
        self.assertIsNone(result.system_state.certificate_id)
        self.assertNotEqual(
            "CERTIFIED_STOP", result.to_outcome_fields()["system_status"]
        )

    def test_unknown_or_duplicate_feedback_ids_fail_closed(self):
        driver = driver_api.DeterministicKernelE2EDriver()
        with self.assertRaises(ValueError):
            driver.run(twin_request(feedback_observation_ids=("OBS-NOT-EXECUTED",)))
        with self.assertRaises(ValueError):
            twin_request(feedback_observation_ids=("OBS-001", "OBS-001"))


if __name__ == "__main__":
    unittest.main()
