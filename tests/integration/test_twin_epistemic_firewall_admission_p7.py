import importlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
import yaml

from src.ir.observation_claim import ObservationClaimIRAdapter
from tests.integration.twin_kernel_inputs import (
    load_json,
    load_jsonl,
    twin_observation_adapter_context,
)
from tests.unit.policy_test_helpers import approved_policy_authority


try:
    firewall_api = importlib.import_module("src.firewall.admission")
except (ImportError, ModuleNotFoundError):
    firewall_api = None


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-COUNTEREXAMPLE-001"


class TwinEpistemicFirewallAdmissionP7IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            firewall_api, "P7 epistemic Firewall admission API is missing"
        )

    def test_twin_observation_claims_follow_frozen_admission_boundary(self):
        observations = load_jsonl(
            FIXTURE / "expected" / "action_observations.jsonl"
        )
        catalog = yaml.safe_load(
            (ROOT / "configs" / "action-catalog-kernel-v0.8.yaml").read_text(
                encoding="utf-8"
            )
        )
        adapted = ObservationClaimIRAdapter().adapt_batch(
            observations, catalog, twin_observation_adapter_context()
        )
        schema = load_json(ROOT / "schemas" / "claim-ir-kernel.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        firewall = firewall_api.ECaseAdmissionFirewall(
            approved_policy_authority()
        )

        decisions = {}
        claims = {}
        for row, claim in zip(observations, adapted, strict=True):
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
        catalog = yaml.safe_load(
            (ROOT / "configs" / "action-catalog-kernel-v0.8.yaml").read_text(
                encoding="utf-8"
            )
        )
        claim = ObservationClaimIRAdapter().adapt(
            row, catalog, twin_observation_adapter_context()
        )
        incomplete = dict(row)
        incomplete["completeness_conditions_satisfied"] = False
        oracle_claim = dict(claim)
        oracle_claim["true_outcome"] = "H1"
        firewall = firewall_api.ECaseAdmissionFirewall(
            approved_policy_authority()
        )

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
