import importlib
import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from src.checker.finite_domain import FiniteDomainChecker, FiniteDomainProblem
from src.counterexample.mindiff import FiniteWitnessMinDiff


try:
    artifact_api = importlib.import_module("src.counterexample.artifact")
except (ImportError, ModuleNotFoundError):
    artifact_api = None


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-COUNTEREXAMPLE-001"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


class TwinCounterexampleArtifactP3IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            artifact_api, "P3 counterexample artifact assembler API is missing"
        )

    def test_twin_assembly_matches_fixture_contract_and_validates_schema(self):
        gamma = load_yaml(ROOT / "configs" / "gamma-kernel-v0.8.yaml")
        frozen = load_json(FIXTURE / "expected" / "counterexample.json")
        claims = admitted_case_evidence(
            load_jsonl(FIXTURE / "claims" / "case_evidence.jsonl")
        )
        target_level = frozen["target_level"]
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
        destination_host = next(iter(authenticated_hosts))
        possible_lateral_source = next(iter(execution_hosts))

        problem = FiniteDomainProblem(
            domains={
                target_level: tuple(
                    gamma["result_domains"][target_level]["finite_candidates"]
                ),
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
            candidate=frozen["candidate_q"]["entity_id"],
        )
        mindiff = FiniteWitnessMinDiff().compare(
            checker_run,
            target_variable=target_level,
            predicate_projections={
                "authentication_mode": f"authentication_origin:{destination_host}",
                target_level: f"credential_activity:{possible_lateral_source}",
            },
        )
        metadata = artifact_api.CounterexampleArtifactMetadata(
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

        artifact = artifact_api.CounterexampleArtifactAssembler().assemble(
            checker_run, mindiff, metadata
        )

        schema = load_json(ROOT / "schemas" / "counterexample.schema.json")
        errors = list(
            Draft202012Validator(
                schema, format_checker=FormatChecker()
            ).iter_errors(artifact)
        )
        self.assertEqual([], errors)

        expected_runtime = dict(frozen)
        expected_runtime["minimization_status"] = mindiff.minimization_status.value
        self.assertEqual(expected_runtime, artifact)
        self.assertEqual(
            {
                "support_world": artifact["support_world"]["target_result"][
                    "entity_id"
                ],
                "alternative_world": artifact["alternative_world"]["target_result"][
                    "entity_id"
                ],
            },
            dict(mindiff.mindiff_disagreement),
        )
        self.assertNotIn("system_status", artifact)
        self.assertNotIn("CERTIFIED_STOP", json.dumps(artifact))


if __name__ == "__main__":
    unittest.main()
