import importlib
import unittest

from src.actions.selection import DistinguishingActionSelector
from src.checker.finite_domain import FiniteDomainChecker
from src.executor.deterministic import (
    DeterministicObservationExecutor,
    FrozenExecutionTables,
)
from src.scope.recertify import RecertificationOrchestrator
from tests.integration.twin_kernel_inputs import load_twin_kernel_inputs


try:
    state_api = importlib.import_module("src.scope.system_state")
except (ImportError, ModuleNotFoundError):
    state_api = None


def twin_checker_run(inputs):
    return FiniteDomainChecker().check_candidate(
        inputs.compiled.problem,
        target_variable=inputs.compiled.target_variable,
        candidate=inputs.expected["candidate_q"],
    )


class TwinSystemStateP9IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(state_api, "P9 system state API is missing")
        self.inputs = load_twin_kernel_inputs()
        self.catalog = self.inputs.catalog
        self.expected = self.inputs.expected
        self.artifact = self.inputs.frozen_counterexample

    def test_twin_counterexample_and_actions_derive_frozen_continue(self):
        checker_run = twin_checker_run(self.inputs)
        selection = DistinguishingActionSelector().select(
            self.artifact, self.catalog
        )

        decision = state_api.SystemStateDeriver().derive(
            checker_run, action_selection=selection
        )

        self.assertEqual(self.expected["system_status"], decision.system_status.value)
        self.assertEqual("COUNTEREXAMPLE_FOUND", decision.effective_checker_status)
        self.assertIsNone(decision.certificate_id)
        self.assertEqual(
            {"system_status"},
            {key for key in decision.to_outcome_fields() if key == "system_status"},
        )

    def test_twin_single_hit_candidate_certification_does_not_stop(self):
        checker_run = twin_checker_run(self.inputs)
        selection = DistinguishingActionSelector().select(
            self.artifact, self.catalog
        )
        tables = FrozenExecutionTables(
            observation_rows=self.inputs.observation_rows,
            resource_rows=self.inputs.resource_rows,
        )
        execution = DeterministicObservationExecutor().execute(
            selection, self.catalog, tables
        )
        origin_hit = tuple(
            row
            for row in execution.observations
            if row["action_id"]
            == self.inputs.predicate_projections.action_bindings[
                self.inputs.compiled.mode_variable
            ]
        )
        recertification = RecertificationOrchestrator().recertify(
            self.artifact, origin_hit, self.catalog
        )

        decision = state_api.SystemStateDeriver().derive(
            checker_run, recertification_result=recertification
        )

        self.assertEqual("CANDIDATE_CERTIFIED", decision.effective_checker_status)
        self.assertEqual("CONTINUE", decision.system_status.value)
        self.assertTrue(decision.conditional)
        self.assertIsNone(decision.certificate_id)


if __name__ == "__main__":
    unittest.main()
