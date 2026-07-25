import importlib
import json
import unittest
from pathlib import Path

import yaml

from src.actions.selection import DistinguishingActionSelector


try:
    executor_api = importlib.import_module("src.executor.deterministic")
except (ImportError, ModuleNotFoundError):
    executor_api = None


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-COUNTEREXAMPLE-001"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path):
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


class TwinDeterministicObservationExecutorP5IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            executor_api, "P5 deterministic observation executor API is missing"
        )

    def test_twin_allowed_actions_replay_frozen_evaluator_rows_only(self):
        artifact = load_json(FIXTURE / "expected" / "counterexample.json")
        catalog = load_yaml(ROOT / "configs" / "action-catalog-kernel-v0.8.yaml")
        selection = DistinguishingActionSelector().select(artifact, catalog)
        observation_rows = load_jsonl(
            FIXTURE / "expected" / "action_observations.jsonl"
        )
        resource_rows = load_jsonl(FIXTURE / "expected" / "resource_trace.jsonl")
        tables = executor_api.FrozenExecutionTables(
            observation_rows=tuple(observation_rows),
            resource_rows=tuple(resource_rows),
        )

        result = executor_api.DeterministicObservationExecutor().execute(
            selection, catalog, tables
        )

        selected = set(selection.allowed_actions)
        expected_observations = tuple(
            row for row in observation_rows if row["action_id"] in selected
        )
        expected_resources = tuple(
            row for row in resource_rows if row["action_id"] in selected
        )
        self.assertEqual(expected_observations, result.observations)
        self.assertEqual(expected_resources, result.resource_traces)
        self.assertEqual(
            ("query_auth_H1_1000_1015",),
            tuple(failure.action_id for failure in result.failures),
        )
        self.assertEqual("RESOURCE_TRACE_MISSING", result.failures[0].status)

        emitted_action_ids = {
            row["action_id"]
            for row in (*result.observations, *result.resource_traces)
        }
        self.assertTrue(
            emitted_action_ids.isdisjoint(selection.forbidden_actions)
        )
        fields = result.to_output_fields()
        self.assertNotIn("system_status", fields)
        self.assertNotIn("checker_status", fields)
        self.assertNotIn("CERTIFIED_STOP", json.dumps(fields))


if __name__ == "__main__":
    unittest.main()
