import hashlib
import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-COUNTEREXAMPLE-001"
GAMMA_PATH = ROOT / "configs" / "gamma-kernel-v0.8.yaml"
CATALOG_PATH = ROOT / "configs" / "action-catalog-kernel-v0.8.yaml"
FORBIDDEN_GENERATION_KEYS = {
    "ground_truth",
    "recoverable_claim_ids",
    "oracle_effects",
    "hidden_claim_ids",
    "true_outcome",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical_sha256(value):
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def document_hash(value):
    copy = dict(value)
    copy.pop("hash", None)
    return "sha256:" + canonical_sha256(copy)


def recursive_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from recursive_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_keys(child)


class TwinCounterexampleFixtureTests(unittest.TestCase):
    def test_fixture_contains_every_v07_required_component(self):
        required = (
            "README.md",
            "gamma_ref.yaml",
            "action_catalog_ref.yaml",
            "raw/endpoint.jsonl",
            "raw/auth.jsonl",
            "claims/case_evidence.jsonl",
            "claims/cti_background.jsonl",
            "expected/outcome.yaml",
            "expected/counterexample.json",
            "expected/action_observations.jsonl",
            "expected/resource_trace.jsonl",
        )
        for relative in required:
            self.assertTrue((FIXTURE / relative).is_file(), relative)

    def test_gamma_and_catalog_validate_and_hash_replay(self):
        gamma = load_yaml(GAMMA_PATH)
        catalog = load_yaml(CATALOG_PATH)
        gamma_schema = load_json(ROOT / "schemas" / "gamma-kernel.schema.json")
        action_schema = load_json(ROOT / "schemas" / "action-kernel.schema.json")
        for schema, value in ((gamma_schema, gamma), (action_schema, catalog)):
            errors = list(
                Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value)
            )
            self.assertEqual([], [error.message for error in errors])
        self.assertEqual(document_hash(gamma), gamma["hash"])
        self.assertEqual(document_hash(catalog), catalog["hash"])
        self.assertTrue(6 <= len(catalog["actions"]) <= 10)

        gamma_ref = load_yaml(FIXTURE / "gamma_ref.yaml")
        catalog_ref = load_yaml(FIXTURE / "action_catalog_ref.yaml")
        self.assertEqual(gamma["gamma_id"], gamma_ref["gamma_id"])
        self.assertEqual(gamma["hash"], gamma_ref["gamma_hash"])
        self.assertEqual(catalog["catalog_id"], catalog_ref["catalog_id"])
        self.assertEqual(catalog["hash"], catalog_ref["catalog_hash"])

    def test_kernel_domains_are_finite_and_heuristic_never_level_complete(self):
        gamma = load_yaml(GAMMA_PATH)
        for level, domain in gamma["result_domains"].items():
            if domain["generator"] == "from_case_entities":
                self.assertEqual("finite_case_entity_closure", domain["finiteness_basis"])
            else:
                self.assertTrue(domain["finite_candidates"], level)
            if domain["coverage_mode"] == "heuristic":
                self.fail(f"Kernel level domain {level} cannot use heuristic coverage")

    def test_actions_are_deterministic_formal_or_explicitly_heuristic_only(self):
        catalog = load_yaml(CATALOG_PATH)
        for action in catalog["actions"]:
            model = action["observation_model"]
            if model is None:
                self.assertEqual("heuristic_only", action["formal_analysis_eligibility"])
            else:
                self.assertEqual("deterministic", model["noise_model"])
                self.assertEqual("formal", action["formal_analysis_eligibility"])
            self.assertNotIn("cost", action)
            self.assertIn(
                action["feasibility"]["status"],
                {
                    "executable",
                    "not_authorized",
                    "temporarily_unavailable",
                    "retention_expired",
                    "sensor_unavailable",
                },
            )

    def test_claims_validate_and_observed_authoritative_pointers_resolve(self):
        schema = load_json(ROOT / "schemas" / "claim-ir-kernel.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        claims = load_jsonl(FIXTURE / "claims" / "case_evidence.jsonl") + load_jsonl(
            FIXTURE / "claims" / "cti_background.jsonl"
        )
        raw_records = {}
        for relative in ("raw/endpoint.jsonl", "raw/auth.jsonl"):
            for record in load_jsonl(FIXTURE / relative):
                raw_records[(relative.split("/", 1)[1], record["record_id"])] = record
        for claim in claims:
            self.assertEqual([], list(validator.iter_errors(claim)), claim["claim_id"])
            if (
                claim["modality"] == "observed"
                and claim["epistemic_role"] == "case_evidence"
                and claim["certification_authority"]["allowed"]
            ):
                pointer = claim["pointer"]
                record = raw_records[(pointer["source_id"], pointer["record_id"])]
                self.assertEqual(
                    "sha256:" + canonical_sha256(record), pointer["content_hash"]
                )

    def test_expected_checker_counterexample_and_action_resource_contracts(self):
        expected = load_yaml(FIXTURE / "expected" / "outcome.yaml")
        self.assertEqual("SAT", expected["base"])
        self.assertEqual("SAT", expected["support"])
        self.assertEqual("SAT", expected["alternative"])
        self.assertEqual("COUNTEREXAMPLE_FOUND", expected["checker_status"])
        self.assertEqual("CONTINUE", expected["system_status"])
        self.assertTrue(expected["allowed_actions"])
        self.assertTrue(expected["forbidden_actions"])

        counterexample = load_json(FIXTURE / "expected" / "counterexample.json")
        schema = load_json(ROOT / "schemas" / "counterexample.schema.json")
        self.assertEqual(
            [],
            list(
                Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
                    counterexample
                )
            ),
        )
        self.assertEqual("COUNTEREXAMPLE_FOUND", counterexample["checker_status"])

        observations = load_jsonl(FIXTURE / "expected" / "action_observations.jsonl")
        gamma = load_yaml(GAMMA_PATH)
        coverage = {row["sensor_id"]: row for row in gamma["sensor_coverage"]}
        for observation in observations:
            if observation["used_for_world_elimination"]:
                sensor = coverage[observation["sensor_id"]]
                self.assertIn(
                    sensor["absence_semantics"],
                    {"closed_world", "bounded_completeness"},
                )
                self.assertTrue(observation["completeness_conditions_satisfied"])

        attempts = load_jsonl(FIXTURE / "expected" / "resource_trace.jsonl")
        self.assertTrue(attempts)
        for attempt in attempts:
            self.assertEqual(
                {
                    "planner_decision_count",
                    "execution_attempt_count",
                    "primitive_operation_count",
                },
                set(attempt["counts"]),
            )
            self.assertNotIn("cost", attempt)
            self.assertIn("wall_seconds", attempt["resources"])
            self.assertIn("records_scanned", attempt["resources"])
            self.assertIn("bytes_scanned", attempt["resources"])

    def test_generation_artifacts_contain_no_ground_truth_or_oracle_fields(self):
        values = [
            load_yaml(GAMMA_PATH),
            load_yaml(CATALOG_PATH),
            load_json(FIXTURE / "expected" / "counterexample.json"),
        ]
        for value in values:
            self.assertTrue(
                set(recursive_keys(value)).isdisjoint(FORBIDDEN_GENERATION_KEYS)
            )


if __name__ == "__main__":
    unittest.main()
