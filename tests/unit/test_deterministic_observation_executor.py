import importlib
import unittest

from src.actions.selection import ActionSelectionResult


try:
    executor_api = importlib.import_module("src.executor.deterministic")
except (ImportError, ModuleNotFoundError):
    executor_api = None


def catalog(*, noise_model="deterministic"):
    return {
        "actions": [
            {
                "action_id": "query_auth",
                "authority": {"current_status": "executable"},
                "observation_model": {
                    "noise_model": noise_model,
                    "output_domain": ["present", "absent"],
                },
                "feasibility": {"status": "executable", "reason_codes": []},
            },
            {
                "action_id": "query_archive",
                "authority": {"current_status": "not_authorized"},
                "observation_model": {
                    "noise_model": "deterministic",
                    "output_domain": ["H1", "EXTERNAL", "absent"],
                },
                "feasibility": {
                    "status": "not_authorized",
                    "reason_codes": ["missing_archive_restore_approval"],
                },
            },
        ]
    }


def observation(action_id="query_auth"):
    return {
        "observation_id": "OBS-UNIT-001",
        "action_id": action_id,
        "sensor_id": "auth-H1",
        "observed_value": "absent",
        "used_for_world_elimination": True,
        "completeness_conditions_satisfied": True,
        "observation_kind": "bounded_complete_zero_hit",
    }


def resource(action_id="query_auth", status="succeeded"):
    return {
        "attempt_id": "ATTEMPT-UNIT-001",
        "action_id": action_id,
        "status": status,
        "counts": {
            "planner_decision_count": 1,
            "execution_attempt_count": 1 if status == "succeeded" else 0,
            "primitive_operation_count": 1 if status == "succeeded" else 0,
        },
        "resources": {
            "wall_seconds": 0.1 if status == "succeeded" else 0.0,
            "cpu_seconds": 0.01 if status == "succeeded" else 0.0,
            "records_scanned": 2 if status == "succeeded" else 0,
            "bytes_scanned": 256 if status == "succeeded" else 0,
            "analyst_seconds": 0.0,
        },
    }


def selection(*allowed):
    return ActionSelectionResult(
        allowed_actions=tuple(allowed),
        forbidden_actions=(
            "oracle_reveal_true_initial_foothold",
            "use_hidden_recoverable_claim_ids",
        ),
        catalog_actions_examined=2,
    )


class DeterministicObservationExecutorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            executor_api, "P5 deterministic observation executor API is missing"
        )

    def test_replays_frozen_observation_and_resource_rows_without_system_state(self):
        tables = executor_api.FrozenExecutionTables(
            observation_rows=(observation(),),
            resource_rows=(resource(),),
        )

        result = executor_api.DeterministicObservationExecutor().execute(
            selection("query_auth"), catalog(), tables
        )

        self.assertEqual((observation(),), result.observations)
        self.assertEqual((resource(),), result.resource_traces)
        self.assertEqual((), result.failures)
        fields = result.to_output_fields()
        self.assertNotIn("system_status", fields)
        self.assertNotIn("checker_status", fields)
        self.assertNotIn("CERTIFIED_STOP", fields.values())

    def test_missing_resource_trace_is_explicit_and_keeps_observation(self):
        tables = executor_api.FrozenExecutionTables(
            observation_rows=(observation(),),
            resource_rows=(),
        )

        result = executor_api.DeterministicObservationExecutor().execute(
            selection("query_auth"), catalog(), tables
        )

        self.assertEqual((observation(),), result.observations)
        self.assertEqual((), result.resource_traces)
        self.assertEqual(1, len(result.failures))
        self.assertEqual("RESOURCE_TRACE_MISSING", result.failures[0].status)

    def test_forbidden_action_is_rejected_before_execution(self):
        tables = executor_api.FrozenExecutionTables((), ())

        with self.assertRaises(executor_api.ForbiddenActionError):
            executor_api.DeterministicObservationExecutor().execute(
                selection("oracle_reveal_true_initial_foothold"),
                catalog(),
                tables,
            )

    def test_non_deterministic_model_is_rejected(self):
        tables = executor_api.FrozenExecutionTables(
            observation_rows=(observation(),),
            resource_rows=(resource(),),
        )

        with self.assertRaises(ValueError):
            executor_api.DeterministicObservationExecutor().execute(
                selection("query_auth"),
                catalog(noise_model="stochastic"),
                tables,
            )

    def test_infeasible_action_records_failure_and_frozen_zero_attempt_trace(self):
        archive_resource = resource("query_archive", status="not_authorized")
        tables = executor_api.FrozenExecutionTables(
            observation_rows=(),
            resource_rows=(archive_resource,),
        )

        result = executor_api.DeterministicObservationExecutor().execute(
            selection("query_archive"), catalog(), tables
        )

        self.assertEqual((), result.observations)
        self.assertEqual((archive_resource,), result.resource_traces)
        self.assertEqual("not_authorized", result.failures[0].status)
        self.assertEqual(
            ("missing_archive_restore_approval",), result.failures[0].reason_codes
        )

    def test_duplicate_selected_actions_and_table_rows_are_rejected(self):
        with self.assertRaises(ValueError):
            executor_api.FrozenExecutionTables(
                observation_rows=(observation(), observation()),
                resource_rows=(),
            )

        with self.assertRaises(ValueError):
            executor_api.DeterministicObservationExecutor().execute(
                selection("query_auth", "query_auth"),
                catalog(),
                executor_api.FrozenExecutionTables((), ()),
            )


if __name__ == "__main__":
    unittest.main()
