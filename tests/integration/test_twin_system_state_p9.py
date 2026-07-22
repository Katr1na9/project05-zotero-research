import importlib
import json
import unittest
from pathlib import Path

import yaml

from src.actions.selection import DistinguishingActionSelector
from src.checker.finite_domain import FiniteDomainChecker, FiniteDomainProblem
from src.executor.deterministic import (
    DeterministicObservationExecutor,
    FrozenExecutionTables,
)
from src.scope.recertify import RecertificationOrchestrator


try:
    state_api = importlib.import_module("src.scope.system_state")
except (ImportError, ModuleNotFoundError):
    state_api = None


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


def twin_checker_run(gamma, expected):
    problem = FiniteDomainProblem(
        domains={
            expected["target_level"]: tuple(
                gamma["result_domains"][expected["target_level"]][
                    "finite_candidates"
                ]
            ),
            "authentication_mode": ("lateral", "direct"),
        },
        constraints=(
            lambda world: (
                world[expected["target_level"]] == "H1"
                and world["authentication_mode"] == "lateral"
            )
            or (
                world[expected["target_level"]] == "H3"
                and world["authentication_mode"] == "direct"
            ),
        ),
    )
    return FiniteDomainChecker().check_candidate(
        problem,
        target_variable=expected["target_level"],
        candidate=expected["candidate_q"],
    )


class TwinSystemStateP9IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(state_api, "P9 system state API is missing")
        self.gamma = load_yaml(ROOT / "configs" / "gamma-kernel-v0.8.yaml")
        self.catalog = load_yaml(
            ROOT / "configs" / "action-catalog-kernel-v0.8.yaml"
        )
        self.expected = load_yaml(FIXTURE / "expected" / "outcome.yaml")
        self.artifact = load_json(FIXTURE / "expected" / "counterexample.json")

    def test_twin_counterexample_and_actions_derive_frozen_continue(self):
        checker_run = twin_checker_run(self.gamma, self.expected)
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
        checker_run = twin_checker_run(self.gamma, self.expected)
        selection = DistinguishingActionSelector().select(
            self.artifact, self.catalog
        )
        tables = FrozenExecutionTables(
            observation_rows=tuple(
                load_jsonl(FIXTURE / "expected" / "action_observations.jsonl")
            ),
            resource_rows=tuple(
                load_jsonl(FIXTURE / "expected" / "resource_trace.jsonl")
            ),
        )
        execution = DeterministicObservationExecutor().execute(
            selection, self.catalog, tables
        )
        origin_hit = tuple(
            row
            for row in execution.observations
            if row["action_id"] == "query_logon_origin_H3"
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
