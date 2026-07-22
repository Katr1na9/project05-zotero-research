import copy
import importlib
import unittest

from tests.unit.policy_test_helpers import approved_policy_authority


POLICY_AUTHORITY = approved_policy_authority()


try:
    firewall_api = importlib.import_module("src.firewall.admission")
except (ImportError, ModuleNotFoundError):
    firewall_api = None


def candidate_claim():
    return {
        "schema_version": "0.8.0",
        "claim_id": "CLAIM-OBS-001",
        "subject": {"entity_id": "H3", "entity_type": "host"},
        "predicate": "action_observation",
        "object": {"entity_id": None, "literal": "H1", "entity_type": None},
        "time": {"start": None, "end": None, "precision": "bounded"},
        "location": {"host": "H3", "tenant": "T1", "zone": None},
        "polarity": "positive",
        "modality": "observed",
        "truth_status": "supported",
        "epistemic_role": "case_evidence",
        "certification_authority": {
            "allowed": True,
            "levels": ["initial_foothold"],
            "basis_rule_id": "A001",
            "policy_hash": POLICY_AUTHORITY.policy_hash,
        },
        "source_family": "identity",
        "source_schema": "kernel.action-observation.v0.8",
        "pointer": {
            "source_id": "action_observations.jsonl",
            "record_id": "OBS-001",
            "byte_or_row_range": [1, 1],
            "content_hash": "sha256:" + "2" * 64,
        },
        "compiler": {
            "parser_id": "p5-observation-adapter",
            "parser_version": "0.8.0",
            "model_id": None,
            "prompt_or_rule_hash": "sha256:" + "3" * 64,
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


def observation(**updates):
    row = {
        "observation_id": "OBS-001",
        "action_id": "query_logon_origin_H3",
        "sensor_id": "logon-origin-H3",
        "observed_value": "H1",
        "used_for_world_elimination": True,
        "completeness_conditions_satisfied": True,
        "observation_kind": "distinguishing_hit",
    }
    row.update(updates)
    return row


class EpistemicFirewallAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            firewall_api, "P7 epistemic Firewall admission API is missing"
        )

    def test_legal_observation_claim_is_allowed_without_mutation(self):
        claim = candidate_claim()
        original = copy.deepcopy(claim)

        decision = firewall_api.ECaseAdmissionFirewall(POLICY_AUTHORITY).evaluate(
            claim, observation()
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(("FW-000_ADMITTED",), decision.reason_codes)
        self.assertEqual("admitted", decision.resulting_admission_status)
        self.assertEqual("observed", decision.preserved_modality)
        self.assertEqual(original, claim)
        self.assertEqual("candidate", claim["admission_status"])
        fields = decision.to_outcome_fields()
        self.assertNotIn("system_status", fields)
        self.assertNotIn("CERTIFIED_STOP", fields.values())
        self.assertNotIn("certificate", fields)

    def test_modality_truth_role_and_authority_are_separate_denials(self):
        claim = candidate_claim()
        claim["modality"] = "reported"
        claim["truth_status"] = "unassessed"
        claim["epistemic_role"] = "background_intelligence"
        claim["certification_authority"] = {
            "allowed": False,
            "levels": [],
            "basis_rule_id": None,
            "policy_hash": None,
        }

        decision = firewall_api.ECaseAdmissionFirewall(POLICY_AUTHORITY).evaluate(
            claim, observation()
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(
            (
                "FW-002_MODALITY_NOT_OBSERVED",
                "FW-003_TRUTH_STATUS_NOT_SUPPORTED",
                "FW-004_ROLE_NOT_CASE_EVIDENCE",
                "FW-005_CERTIFICATION_AUTHORITY_INVALID",
            ),
            decision.reason_codes,
        )

    def test_pointer_binding_and_observed_value_must_match_observation(self):
        claim = candidate_claim()
        claim["pointer"]["record_id"] = "OBS-OTHER"
        claim["object"]["literal"] = "EXTERNAL"

        decision = firewall_api.ECaseAdmissionFirewall(POLICY_AUTHORITY).evaluate(
            claim, observation()
        )

        self.assertFalse(decision.allowed)
        self.assertIn("FW-007_POINTER_OBSERVATION_MISMATCH", decision.reason_codes)
        self.assertIn("FW-015_OBSERVATION_VALUE_MISMATCH", decision.reason_codes)

    def test_incomplete_pointer_is_denied(self):
        claim = candidate_claim()
        claim["pointer"]["content_hash"] = None

        decision = firewall_api.ECaseAdmissionFirewall(POLICY_AUTHORITY).evaluate(
            claim, observation()
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(("FW-006_POINTER_INCOMPLETE",), decision.reason_codes)

    def test_missing_context_and_unsupported_kind_have_distinct_codes(self):
        firewall = firewall_api.ECaseAdmissionFirewall(POLICY_AUTHORITY)

        missing = firewall.evaluate(candidate_claim(), None)
        unsupported = firewall.evaluate(
            candidate_claim(), observation(observation_kind="future_kind")
        )

        self.assertEqual(
            ("FW-016_OBSERVATION_CONTEXT_REQUIRED",), missing.reason_codes
        )
        self.assertEqual(
            ("FW-017_OBSERVATION_KIND_UNSUPPORTED",), unsupported.reason_codes
        )
        self.assertNotEqual(missing.reason_codes, unsupported.reason_codes)

    def test_control_heuristic_incomplete_and_not_eligible_observations_deny(self):
        firewall = firewall_api.ECaseAdmissionFirewall(POLICY_AUTHORITY)
        cases = (
            (
                observation(
                    observation_kind="true_empty_control",
                    used_for_world_elimination=False,
                ),
                {
                    "FW-011_CONTROL_OBSERVATION",
                    "FW-014_OBSERVATION_NOT_ELIMINATION_ELIGIBLE",
                },
            ),
            (
                observation(
                    observation_kind="heuristic_only",
                    used_for_world_elimination=False,
                    completeness_conditions_satisfied=False,
                ),
                {
                    "FW-010_HEURISTIC_OBSERVATION",
                    "FW-012_COMPLETENESS_NOT_SATISFIED",
                    "FW-014_OBSERVATION_NOT_ELIMINATION_ELIGIBLE",
                },
            ),
            (
                observation(completeness_conditions_satisfied=False),
                {"FW-012_COMPLETENESS_NOT_SATISFIED"},
            ),
        )
        for row, expected_reasons in cases:
            with self.subTest(kind=row["observation_kind"]):
                decision = firewall.evaluate(candidate_claim(), row)
                self.assertFalse(decision.allowed)
                self.assertTrue(expected_reasons.issubset(decision.reason_codes))

    def test_oracle_hidden_and_promotion_paths_fail_closed(self):
        claim = candidate_claim()
        claim["ground_truth"] = "H1"
        claim["compiler"]["hidden_claim_ids"] = ["SECRET"]
        claim["promotion_status"] = "promoted"
        claim["promotion_event_id"] = "PROM-ILLEGAL"

        decision = firewall_api.ECaseAdmissionFirewall(POLICY_AUTHORITY).evaluate(
            claim, observation()
        )

        self.assertFalse(decision.allowed)
        self.assertIn("FW-001_ORACLE_OR_HIDDEN_FIELD", decision.reason_codes)
        self.assertIn("FW-009_PROMOTION_OUT_OF_SCOPE", decision.reason_codes)

    def test_missing_or_mismatched_policy_authority_fails_closed(self):
        missing = firewall_api.ECaseAdmissionFirewall().evaluate(
            candidate_claim(), observation()
        )
        self.assertFalse(missing.allowed)
        self.assertIn("FW-018_POLICY_AUTHORITY_UNVERIFIED", missing.reason_codes)

        wrong = candidate_claim()
        wrong["certification_authority"]["policy_hash"] = "sha256:" + "9" * 64
        mismatch = firewall_api.ECaseAdmissionFirewall(POLICY_AUTHORITY).evaluate(
            wrong, observation()
        )
        self.assertFalse(mismatch.allowed)
        self.assertIn("FW-019_POLICY_BINDING_MISMATCH", mismatch.reason_codes)


if __name__ == "__main__":
    unittest.main()
