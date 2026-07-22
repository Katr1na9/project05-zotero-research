import importlib
import json
import unittest
from pathlib import Path

import yaml

from src.checker.finite_domain import FiniteDomainChecker, FiniteDomainProblem


try:
    mindiff_api = importlib.import_module("src.counterexample.mindiff")
except (ImportError, ModuleNotFoundError):
    mindiff_api = None


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-COUNTEREXAMPLE-001"


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path):
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def admitted_case_evidence(claims):
    return [
        claim
        for claim in claims
        if claim["epistemic_role"] == "case_evidence"
        and claim["modality"] == "observed"
        and claim["truth_status"] == "supported"
        and claim["admission_status"] == "admitted"
        and claim["certification_authority"]["allowed"]
    ]


class TwinMinDiffP2IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(mindiff_api, "P2 finite-witness MinDiff API is missing")

    def test_twin_witnesses_reproduce_frozen_disagreement_and_predicates(self):
        gamma = load_yaml(ROOT / "configs" / "gamma-kernel-v0.8.yaml")
        expected = load_yaml(FIXTURE / "expected" / "outcome.yaml")
        claims = admitted_case_evidence(
            load_jsonl(FIXTURE / "claims" / "case_evidence.jsonl")
        )

        target_level = expected["target_level"]
        result_domain = gamma["result_domains"][target_level]
        authenticated_hosts = {
            claim["subject"]["entity_id"]
            for claim in claims
            if claim["predicate"] == "authenticated_account"
        }
        execution_hosts = {
            claim["subject"]["entity_id"]
            for claim in claims
            if claim["predicate"] == "executed_process"
        }
        self.assertEqual(1, len(authenticated_hosts))
        self.assertEqual(1, len(execution_hosts))
        destination_host = next(iter(authenticated_hosts))
        possible_lateral_source = next(iter(execution_hosts))

        problem = FiniteDomainProblem(
            domains={
                target_level: tuple(result_domain["finite_candidates"]),
                "authentication_mode": ("lateral", "direct"),
            },
            constraints=(
                lambda world: (
                    world[target_level] == possible_lateral_source
                    and world["authentication_mode"] == "lateral"
                )
                or (
                    world[target_level] == destination_host
                    and world["authentication_mode"] == "direct"
                ),
            ),
        )
        checker_run = FiniteDomainChecker().check_candidate(
            problem,
            target_variable=target_level,
            candidate=expected["candidate_q"],
        )

        result = mindiff_api.FiniteWitnessMinDiff().compare(
            checker_run,
            target_variable=target_level,
            predicate_projections={
                "authentication_mode": f"authentication_origin:{destination_host}",
                target_level: f"credential_activity:{possible_lateral_source}",
            },
        )

        self.assertEqual(expected["checker_status"], result.checker_status.value)
        self.assertEqual(
            expected["mindiff_disagreement"], dict(result.mindiff_disagreement)
        )
        self.assertEqual(
            tuple(expected["distinguishing_predicates"]),
            result.distinguishing_predicates,
        )
        self.assertEqual("OPTIMAL", result.minimization_status.value)
        self.assertNotIn("system_status", result.to_outcome_fields())


if __name__ == "__main__":
    unittest.main()
