import importlib
import json
import unittest
from pathlib import Path

import yaml


try:
    checker_api = importlib.import_module("src.checker.finite_domain")
except (ImportError, ModuleNotFoundError):
    checker_api = None


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-COUNTEREXAMPLE-001"
CHECKER_FIELDS = ("base", "support", "alternative", "checker_status")


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


class TwinCheckerP1IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(checker_api, "P1 finite-domain Checker API is missing")

    def test_expected_checker_outcome_is_recomputed_from_gamma_and_case_evidence(self):
        gamma = load_yaml(ROOT / "configs" / "gamma-kernel-v0.8.yaml")
        expected = load_yaml(FIXTURE / "expected" / "outcome.yaml")
        claims = admitted_case_evidence(
            load_jsonl(FIXTURE / "claims" / "case_evidence.jsonl")
        )

        target_level = expected["target_level"]
        result_domain = gamma["result_domains"][target_level]
        self.assertEqual("from_finite_candidate_list", result_domain["generator"])
        self.assertEqual("explicit_finite_candidates", result_domain["finiteness_basis"])

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

        self.assertIn(
            "credential_login_implies_authentication", gamma["mechanism_rules"]
        )
        self.assertIn(
            "lateral_movement_requires_prior_compromise", gamma["mechanism_rules"]
        )

        problem = checker_api.FiniteDomainProblem(
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

        actual = checker_api.FiniteDomainChecker().check_candidate(
            problem,
            target_variable=target_level,
            candidate=expected["candidate_q"],
        )
        expected_checker_fields = {key: expected[key] for key in CHECKER_FIELDS}

        self.assertEqual(expected_checker_fields, actual.to_outcome_fields())
        self.assertNotIn("system_status", actual.to_outcome_fields())
        self.assertEqual(
            destination_host,
            actual.alternative.witness[target_level],
        )


if __name__ == "__main__":
    unittest.main()
