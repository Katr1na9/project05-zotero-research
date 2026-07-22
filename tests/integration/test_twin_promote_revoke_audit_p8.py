import importlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from src.firewall.admission import ECaseAdmissionFirewall
from tests.integration.test_twin_epistemic_firewall_admission_p7 import (
    load_json,
    load_jsonl,
    observation_claim,
)


try:
    lifecycle_api = importlib.import_module("src.firewall.lifecycle")
except (ImportError, ModuleNotFoundError):
    lifecycle_api = None


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-COUNTEREXAMPLE-001"


class TwinPromoteRevokeAuditP8IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(lifecycle_api, "P8 lifecycle API is missing")

    def test_twin_admits_only_firewall_allowed_observations_with_hash_chain(self):
        observations = load_jsonl(
            FIXTURE / "expected" / "action_observations.jsonl"
        )
        claims = {
            row["observation_id"]: observation_claim(row, row_number)
            for row_number, row in enumerate(observations, start=1)
        }
        rows = {row["observation_id"]: row for row in observations}
        decisions = {
            observation_id: ECaseAdmissionFirewall().evaluate(
                claim, rows[observation_id]
            )
            for observation_id, claim in claims.items()
        }
        ledger = lifecycle_api.AppendOnlyAuditLedger()
        manager = lifecycle_api.ClaimLifecycleManager(
            ledger=ledger,
            promotion_policy={"version": "prom-0.8", "rules": []},
            promotion_policy_hash=
                "sha256:0eb3cbb8be3cf51dc9952a447e4d1f90fc89b5dc2c5e2f0edafca32c6805399a",
        )

        admitted = {}
        for offset, observation_id in enumerate(("OBS-001", "OBS-002")):
            admitted[observation_id] = manager.admit(
                claims[observation_id],
                decisions[observation_id],
                event_id=f"TWIN-P8-ADMIT-{offset + 1:03d}",
                rule_id="P7-FW-ADMISSION",
                timestamp=f"2026-01-01T10:16:0{offset}Z",
            ).claim

        for observation_id in ("OBS-003", "OBS-004"):
            with self.subTest(observation_id=observation_id):
                with self.assertRaises(
                    lifecycle_api.LifecycleTransitionRejected
                ) as caught:
                    manager.admit(
                        claims[observation_id],
                        decisions[observation_id],
                        event_id=f"TWIN-P8-DENY-{observation_id}",
                        rule_id="P7-FW-ADMISSION",
                        timestamp="2026-01-01T10:16:02Z",
                    )
                self.assertEqual(
                    "P8-001_FIREWALL_DENIED", caught.exception.reason_code
                )
                with self.assertRaises(
                    lifecycle_api.LifecycleTransitionRejected
                ) as promoted:
                    manager.promote(
                        claims[observation_id],
                        event_id=f"TWIN-P8-PROMOTE-{observation_id}",
                        rule_id="PROM-NOT-FROZEN",
                        timestamp="2026-01-01T10:16:03Z",
                        target_levels=("initial_foothold",),
                    )
                self.assertEqual(
                    "P8-007_PROMOTION_STATE_INVALID",
                    promoted.exception.reason_code,
                )

        schema = load_json(ROOT / "schemas" / "claim-ir-kernel.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for claim in admitted.values():
            self.assertEqual([], list(validator.iter_errors(claim)))
            self.assertEqual("observed", claim["modality"])
            self.assertEqual("admitted", claim["admission_status"])

        self.assertEqual(2, len(ledger.events))
        self.assertEqual([1, 2], [event.sequence for event in ledger.events])
        self.assertEqual(
            ledger.events[0].event_hash, ledger.events[1].previous_hash
        )
        self.assertTrue(ledger.verify_integrity())
        serialized = json.dumps([event.to_dict() for event in ledger.events])
        self.assertNotIn("system_status", serialized)
        self.assertNotIn("CERTIFIED_STOP", serialized)
        self.assertNotIn("certificate", serialized)

    def test_twin_frozen_empty_promotion_policy_cannot_promote_cti(self):
        cti_claim = load_jsonl(FIXTURE / "claims" / "cti_background.jsonl")[0]
        manager = lifecycle_api.ClaimLifecycleManager(
            ledger=lifecycle_api.AppendOnlyAuditLedger(),
            promotion_policy={"version": "prom-0.8", "rules": []},
            promotion_policy_hash=
                "sha256:0eb3cbb8be3cf51dc9952a447e4d1f90fc89b5dc2c5e2f0edafca32c6805399a",
        )

        with self.assertRaises(lifecycle_api.LifecycleTransitionRejected) as caught:
            manager.promote(
                cti_claim,
                event_id="TWIN-P8-PROMOTE-CTI",
                rule_id="PROM-CTI-UNREGISTERED",
                timestamp="2026-01-01T10:17:00Z",
                target_levels=("initial_foothold",),
            )

        self.assertEqual(
            "P8-006_PROMOTION_RULE_NOT_REGISTERED", caught.exception.reason_code
        )
        self.assertEqual("reported", cti_claim["modality"])
        self.assertEqual((), manager.ledger.events)


if __name__ == "__main__":
    unittest.main()
