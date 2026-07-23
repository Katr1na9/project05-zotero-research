import importlib
import json
import unittest
from pathlib import Path

import yaml

from src.actions.selection import DistinguishingActionSelector
from src.executor.deterministic import (
    DeterministicObservationExecutor,
    FrozenExecutionTables,
)
from tests.integration.twin_kernel_inputs import load_twin_kernel_inputs


try:
    recert_api = importlib.import_module("src.scope.recertify")
except (ImportError, ModuleNotFoundError):
    recert_api = None


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


class TwinWorldEliminationRecertifyP6IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            recert_api, "P6 world-elimination/recertification API is missing"
        )

    def p5_result(self):
        inputs = load_twin_kernel_inputs()
        artifact = inputs.frozen_counterexample
        catalog = inputs.catalog
        selection = DistinguishingActionSelector().select(artifact, catalog)
        tables = FrozenExecutionTables(
            observation_rows=tuple(
                load_jsonl(FIXTURE / "expected" / "action_observations.jsonl")
            ),
            resource_rows=tuple(
                load_jsonl(FIXTURE / "expected" / "resource_trace.jsonl")
            ),
        )
        execution = DeterministicObservationExecutor().execute(
            selection, catalog, tables
        )
        return inputs, artifact, catalog, execution

    def test_full_p5_observation_batch_exposes_scope_mismatch_without_stop(self):
        inputs, artifact, catalog, execution = self.p5_result()

        result = recert_api.RecertificationOrchestrator().recertify(
            artifact,
            execution.observations,
            catalog,
            inputs.compiled,
            predicate_projections=inputs.predicate_projections,
        )

        self.assertEqual(
            ("OBS-001", "OBS-002"), result.applied_observation_ids
        )
        self.assertEqual((), result.surviving_world_ids)
        self.assertEqual(
            "SCOPE_MISMATCH_SUSPECTED", result.checker_run.checker_status.value
        )
        self.assertEqual("COUNTEREXAMPLE_FOUND", artifact["checker_status"])
        fields = result.to_outcome_fields()
        self.assertNotIn("system_status", fields)
        self.assertNotIn("CERTIFIED_STOP", json.dumps(fields))

    def test_single_distinguishing_hit_recertifies_candidate_only(self):
        inputs, artifact, catalog, execution = self.p5_result()
        origin_hit = tuple(
            row
            for row in execution.observations
            if row["action_id"] == "query_logon_origin_H3"
        )

        result = recert_api.RecertificationOrchestrator().recertify(
            artifact,
            origin_hit,
            catalog,
            inputs.compiled,
            predicate_projections=inputs.predicate_projections,
        )

        self.assertEqual(("W-SUPPORT-H1",), result.surviving_world_ids)
        self.assertEqual("CANDIDATE_CERTIFIED", result.checker_run.checker_status.value)
        self.assertIsNone(result.mindiff_result)
        self.assertNotIn("certification_scope", result.to_outcome_fields())


if __name__ == "__main__":
    unittest.main()
