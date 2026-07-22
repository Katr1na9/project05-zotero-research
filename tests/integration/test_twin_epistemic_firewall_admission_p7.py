import hashlib
import importlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


try:
    firewall_api = importlib.import_module("src.firewall.admission")
except (ImportError, ModuleNotFoundError):
    firewall_api = None


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


def observation_claim(row, row_number):
    content = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
    subject_host = "H3" if "H3" in row["action_id"] else "H1"
    return {
        "schema_version": "0.8.0",
        "claim_id": f"P7-{row['observation_id']}",
        "subject": {"entity_id": subject_host, "entity_type": "host"},
        "predicate": "action_observation",
        "object": {
            "entity_id": None,
            "literal": row["observed_value"],
            "entity_type": None,
        },
        "time": {"start": None, "end": None, "precision": "bounded"},
        "location": {"host": subject_host, "tenant": "T1", "zone": None},
        "polarity": "positive",
        "modality": "observed",
        "truth_status": "supported",
        "epistemic_role": "case_evidence",
        "certification_authority": {
            "allowed": True,
            "levels": ["initial_foothold"],
            "basis_rule_id": "A-P5-OBSERVATION",
            "policy_hash": "sha256:" + "7" * 64,
        },
        "source_family": "identity",
        "source_schema": "kernel.action-observation.v0.8",
        "pointer": {
            "source_id": "action_observations.jsonl",
            "record_id": row["observation_id"],
            "byte_or_row_range": [row_number, row_number],
            "content_hash": "sha256:" + hashlib.sha256(content).hexdigest(),
        },
        "compiler": {
            "parser_id": "p5-observation-adapter",
            "parser_version": "0.8.0",
            "model_id": None,
            "prompt_or_rule_hash": "sha256:" + "8" * 64,
        },
        "binding_status": "bound",
        "admission_status": "candidate",
        "promotion_status": "none",
        "promotion_event_id": None,
        "admissible_levels": ["initial_foothold"],
        "support_claim_ids": [],
        "contradict_claim_ids": [],
        "rule_trace": ["P5-OBSERVATION-BINDING"],
        "confidence": {"extraction": 1.0, "source": 1.0, "model": None},
        "lifecycle_state": "bound",
    }


class TwinEpistemicFirewallAdmissionP7IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            firewall_api, "P7 epistemic Firewall admission API is missing"
        )

    def test_twin_observation_claims_follow_frozen_admission_boundary(self):
        observations = load_jsonl(
            FIXTURE / "expected" / "action_observations.jsonl"
        )
        schema = load_json(ROOT / "schemas" / "claim-ir-kernel.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        firewall = firewall_api.ECaseAdmissionFirewall()

        decisions = {}
        claims = {}
        for row_number, row in enumerate(observations, start=1):
            claim = observation_claim(row, row_number)
            self.assertEqual([], list(validator.iter_errors(claim)))
            claims[row["observation_id"]] = claim
            decisions[row["observation_id"]] = firewall.evaluate(claim, row)

        self.assertTrue(decisions["OBS-001"].allowed)
        self.assertTrue(decisions["OBS-002"].allowed)
        self.assertFalse(decisions["OBS-003"].allowed)
        self.assertIn(
            "FW-011_CONTROL_OBSERVATION", decisions["OBS-003"].reason_codes
        )
        self.assertFalse(decisions["OBS-004"].allowed)
        self.assertIn(
            "FW-010_HEURISTIC_OBSERVATION", decisions["OBS-004"].reason_codes
        )
        self.assertTrue(
            all(claim["modality"] == "observed" for claim in claims.values())
        )
        self.assertTrue(
            all(claim["admission_status"] == "candidate" for claim in claims.values())
        )

    def test_incomplete_and_oracle_twin_paths_are_denied_without_stop(self):
        row = load_jsonl(
            FIXTURE / "expected" / "action_observations.jsonl"
        )[0]
        claim = observation_claim(row, 1)
        incomplete = dict(row)
        incomplete["completeness_conditions_satisfied"] = False
        oracle_claim = dict(claim)
        oracle_claim["true_outcome"] = "H1"
        firewall = firewall_api.ECaseAdmissionFirewall()

        incomplete_decision = firewall.evaluate(claim, incomplete)
        oracle_decision = firewall.evaluate(oracle_claim, row)

        self.assertFalse(incomplete_decision.allowed)
        self.assertFalse(oracle_decision.allowed)
        for decision in (incomplete_decision, oracle_decision):
            fields = decision.to_outcome_fields()
            self.assertNotIn("system_status", fields)
            self.assertNotIn("CERTIFIED_STOP", json.dumps(fields))
            self.assertNotIn("certificate", fields)


if __name__ == "__main__":
    unittest.main()
