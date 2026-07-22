import copy
import importlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from src.firewall.admission import ECaseAdmissionFirewall
from tests.unit.test_epistemic_firewall_admission import (
    candidate_claim,
    observation,
)


try:
    lifecycle_api = importlib.import_module("src.firewall.lifecycle")
except (ImportError, ModuleNotFoundError):
    lifecycle_api = None


ROOT = Path(__file__).resolve().parents[2]
POLICY_HASH = "sha256:" + "a" * 64


def lifecycle_manager(ledger=None, *, rules=("PROM-CTI-001",)):
    return lifecycle_api.ClaimLifecycleManager(
        ledger=ledger or lifecycle_api.AppendOnlyAuditLedger(),
        promotion_policy={"version": "prom-test-0.8", "rules": list(rules)},
        promotion_policy_hash=POLICY_HASH,
    )


def reported_background_claim():
    claim = candidate_claim()
    claim.update(
        {
            "claim_id": "CLAIM-CTI-001",
            "modality": "reported",
            "truth_status": "supported",
            "epistemic_role": "background_intelligence",
            "certification_authority": {
                "allowed": False,
                "levels": [],
                "basis_rule_id": None,
                "policy_hash": None,
            },
            "source_family": "external_intel",
            "source_schema": "cti.report.v1",
            "admission_status": "admitted",
            "promotion_status": "none",
            "promotion_event_id": None,
            "admissible_levels": ["initial_foothold"],
            "lifecycle_state": "admitted",
        }
    )
    claim["pointer"] = {
        "source_id": "cti-bulletin-2025-12",
        "record_id": "paragraph-12",
        "byte_or_row_range": [12, 12],
        "content_hash": "sha256:" + "b" * 64,
    }
    return claim


class PromoteRevokeAuditTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(lifecycle_api, "P8 lifecycle API is missing")

    def assert_rejected(self, expected_code, callback):
        with self.assertRaises(lifecycle_api.LifecycleTransitionRejected) as caught:
            callback()
        self.assertEqual(expected_code, caught.exception.reason_code)

    def test_admit_requires_firewall_allow_and_appends_immutable_event(self):
        claim = candidate_claim()
        original = copy.deepcopy(claim)
        decision = ECaseAdmissionFirewall().evaluate(claim, observation())
        ledger = lifecycle_api.AppendOnlyAuditLedger()
        manager = lifecycle_manager(ledger)

        result = manager.admit(
            claim,
            decision,
            event_id="AUD-ADMIT-001",
            rule_id="P7-FW-ADMISSION",
            timestamp="2026-01-01T10:16:00Z",
        )

        admitted = result.claim
        self.assertEqual(original, claim)
        self.assertEqual("admitted", admitted["admission_status"])
        self.assertEqual("admitted", admitted["lifecycle_state"])
        self.assertEqual("observed", admitted["modality"])
        self.assertEqual("none", admitted["promotion_status"])
        self.assertEqual(1, len(ledger.events))
        self.assertEqual("ADMIT", ledger.events[0].operation)
        self.assertEqual("candidate", ledger.events[0].before["admission_status"])
        self.assertEqual("admitted", ledger.events[0].after["admission_status"])
        self.assertTrue(ledger.verify_integrity())
        self.assertIsInstance(ledger.events, tuple)
        fields = result.to_outcome_fields()
        self.assertNotIn("system_status", fields)
        self.assertNotIn("CERTIFIED_STOP", json.dumps(fields))
        self.assertNotIn("certificate", fields)

    def test_firewall_denial_cannot_admit_or_append_audit(self):
        claim = candidate_claim()
        decision = ECaseAdmissionFirewall().evaluate(
            claim,
            observation(
                observation_kind="heuristic_only",
                completeness_conditions_satisfied=False,
                used_for_world_elimination=False,
            ),
        )
        ledger = lifecycle_api.AppendOnlyAuditLedger()
        manager = lifecycle_manager(ledger)

        self.assert_rejected(
            "P8-001_FIREWALL_DENIED",
            lambda: manager.admit(
                claim,
                decision,
                event_id="AUD-DENIED-001",
                rule_id="P7-FW-ADMISSION",
                timestamp="2026-01-01T10:16:00Z",
            ),
        )

        self.assertEqual((), ledger.events)
        self.assertEqual("candidate", claim["admission_status"])

    def test_reported_background_promotion_preserves_modality_and_pointer(self):
        claim = reported_background_claim()
        pointer_before = copy.deepcopy(claim["pointer"])
        manager = lifecycle_manager()

        result = manager.promote(
            claim,
            event_id="AUD-PROMOTE-001",
            rule_id="PROM-CTI-001",
            timestamp="2026-01-01T10:17:00Z",
            target_levels=("initial_foothold",),
            requested_modality="reported",
        )

        promoted = result.claim
        self.assertEqual("reported", promoted["modality"])
        self.assertEqual(pointer_before, promoted["pointer"])
        self.assertEqual("case_evidence", promoted["epistemic_role"])
        self.assertEqual("promoted", promoted["promotion_status"])
        self.assertEqual("AUD-PROMOTE-001", promoted["promotion_event_id"])
        self.assertEqual("promoted", promoted["lifecycle_state"])
        self.assertEqual(
            ["initial_foothold"], promoted["certification_authority"]["levels"]
        )
        self.assertEqual("PROM-CTI-001", promoted["certification_authority"]["basis_rule_id"])
        schema = json.loads(
            (ROOT / "schemas" / "claim-ir-kernel.schema.json").read_text(
                encoding="utf-8"
            )
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual([], list(validator.iter_errors(promoted)))

    def test_illegal_promotions_fail_without_audit(self):
        manager = lifecycle_manager()
        claim = reported_background_claim()

        self.assert_rejected(
            "P8-008_MODALITY_CHANGE_FORBIDDEN",
            lambda: manager.promote(
                claim,
                event_id="AUD-PROMOTE-BAD-MODALITY",
                rule_id="PROM-CTI-001",
                timestamp="2026-01-01T10:17:00Z",
                target_levels=("initial_foothold",),
                requested_modality="observed",
            ),
        )

        without_pointer = copy.deepcopy(claim)
        without_pointer["pointer"] = {
            "source_id": None,
            "record_id": None,
            "byte_or_row_range": None,
            "content_hash": None,
        }
        self.assert_rejected(
            "P8-009_PROMOTION_POINTER_UNRESOLVABLE",
            lambda: manager.promote(
                without_pointer,
                event_id="AUD-PROMOTE-NO-POINTER",
                rule_id="PROM-CTI-001",
                timestamp="2026-01-01T10:17:01Z",
                target_levels=("initial_foothold",),
            ),
        )

        self.assert_rejected(
            "P8-006_PROMOTION_RULE_NOT_REGISTERED",
            lambda: manager.promote(
                claim,
                event_id="AUD-PROMOTE-NO-RULE",
                rule_id="PROM-NOT-FROZEN",
                timestamp="2026-01-01T10:17:02Z",
                target_levels=("initial_foothold",),
            ),
        )
        self.assertEqual((), manager.ledger.events)

    def test_revoke_withdraws_authority_and_preserves_promotion_history(self):
        manager = lifecycle_manager()
        promoted = manager.promote(
            reported_background_claim(),
            event_id="AUD-PROMOTE-001",
            rule_id="PROM-CTI-001",
            timestamp="2026-01-01T10:17:00Z",
            target_levels=("initial_foothold",),
        ).claim

        result = manager.revoke(
            promoted,
            event_id="AUD-REVOKE-001",
            rule_id="REVOKE-PROVENANCE-001",
            timestamp="2026-01-01T10:18:00Z",
        )

        revoked = result.claim
        self.assertEqual("reported", revoked["modality"])
        self.assertEqual("rejected", revoked["admission_status"])
        self.assertEqual("revoked", revoked["promotion_status"])
        self.assertEqual("AUD-PROMOTE-001", revoked["promotion_event_id"])
        self.assertEqual("revoked", revoked["lifecycle_state"])
        self.assertEqual(
            {
                "allowed": False,
                "levels": [],
                "basis_rule_id": None,
                "policy_hash": None,
            },
            revoked["certification_authority"],
        )
        self.assertTrue(result.recertification_required)
        self.assertEqual(2, len(manager.ledger.events))
        self.assertEqual(
            manager.ledger.events[0].event_hash,
            manager.ledger.events[1].previous_hash,
        )
        self.assertTrue(manager.ledger.verify_integrity())

    def test_hash_chain_is_deterministic_and_event_ids_are_unique(self):
        claim = candidate_claim()
        decision = ECaseAdmissionFirewall().evaluate(claim, observation())
        event_hashes = []
        for _ in range(2):
            manager = lifecycle_manager()
            result = manager.admit(
                claim,
                decision,
                event_id="AUD-DETERMINISTIC-001",
                rule_id="P7-FW-ADMISSION",
                timestamp="2026-01-01T10:16:00Z",
            )
            event_hashes.append(result.audit_event.event_hash)
        self.assertEqual(event_hashes[0], event_hashes[1])

        manager = lifecycle_manager()
        admitted = manager.admit(
            claim,
            decision,
            event_id="AUD-DUPLICATE-001",
            rule_id="P7-FW-ADMISSION",
            timestamp="2026-01-01T10:16:00Z",
        ).claim
        self.assert_rejected(
            "P8-005_DUPLICATE_EVENT_ID",
            lambda: manager.revoke(
                admitted,
                event_id="AUD-DUPLICATE-001",
                rule_id="REVOKE-TEST",
                timestamp="2026-01-01T10:18:00Z",
            ),
        )
        self.assertEqual(1, len(manager.ledger.events))


if __name__ == "__main__":
    unittest.main()
