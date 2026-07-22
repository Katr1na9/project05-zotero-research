import json
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from src.cli.kernel_e2e import DeterministicKernelE2EDriver
from src.firewall.admission import ECaseAdmissionFirewall
from src.ir.observation_claim import ObservationClaimIRAdapter
from tests.integration.test_twin_kernel_e2e_p10 import twin_request
from tests.integration.twin_kernel_inputs import (
    ROOT,
    load_twin_kernel_inputs,
    twin_observation_admission_config,
    twin_observation_adapter_context,
)


class TwinFirewallAdmitDriverP11IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.inputs = load_twin_kernel_inputs()

    def test_all_twin_rows_use_production_adapter_and_frozen_firewall_boundary(self):
        claims = ObservationClaimIRAdapter().adapt_batch(
            self.inputs.observation_rows,
            self.inputs.catalog,
            twin_observation_adapter_context(),
        )
        rows = {
            row["observation_id"]: row for row in self.inputs.observation_rows
        }
        decisions = {
            claim["pointer"]["record_id"]: ECaseAdmissionFirewall().evaluate(
                claim, rows[claim["pointer"]["record_id"]]
            )
            for claim in claims
        }

        schema = json.loads(
            (ROOT / "schemas" / "claim-ir-kernel.schema.json").read_text(
                encoding="utf-8"
            )
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for claim in claims:
            self.assertEqual([], list(validator.iter_errors(claim)))
            self.assertEqual("observed", claim["modality"])
            self.assertEqual(
                claim["claim_id"].removeprefix("P11-"),
                claim["pointer"]["record_id"],
            )
            self.assertNotIn("ground_truth", json.dumps(claim))
            self.assertNotIn("hidden_claim_ids", json.dumps(claim))

        self.assertTrue(decisions["OBS-001"].allowed)
        self.assertTrue(decisions["OBS-002"].allowed)
        self.assertFalse(decisions["OBS-003"].allowed)
        self.assertIn("FW-011_CONTROL_OBSERVATION", decisions["OBS-003"].reason_codes)
        self.assertFalse(decisions["OBS-004"].allowed)
        self.assertIn("FW-010_HEURISTIC_OBSERVATION", decisions["OBS-004"].reason_codes)

    def test_e2e_adapts_evaluates_and_admits_executed_twin_observations(self):
        result = DeterministicKernelE2EDriver().run(
            twin_request(
                feedback_observation_ids=("OBS-001",),
                observation_admission=twin_observation_admission_config(
                    admit_observation_ids=("OBS-001", "OBS-002")
                ),
            )
        )

        self.assertEqual(
            ("OBS-001", "OBS-002"),
            tuple(
                claim["pointer"]["record_id"]
                for claim in result.observation_claims
            ),
        )
        self.assertTrue(
            all(decision.allowed for decision in result.firewall_decisions)
        )
        self.assertEqual(2, len(result.admission_transitions))
        self.assertEqual(
            ("OBS-001", "OBS-002"),
            tuple(
                transition.claim["pointer"]["record_id"]
                for transition in result.admission_transitions
            ),
        )
        self.assertTrue(
            all(
                transition.claim["modality"] == "observed"
                and transition.claim["admission_status"] == "admitted"
                for transition in result.admission_transitions
            )
        )
        self.assertEqual(
            "CANDIDATE_CERTIFIED",
            result.recertification_result.checker_run.checker_status.value,
        )
        self.assertEqual("CONTINUE", result.system_state.system_status.value)
        self.assertIsNone(result.system_state.certificate_id)

        fields = result.to_outcome_fields()
        self.assertEqual(
            ["P11-OBS-001", "P11-OBS-002"], fields["observation_claim_ids"]
        )
        self.assertEqual(
            ["P11-OBS-001", "P11-OBS-002"], fields["admitted_claim_ids"]
        )
        self.assertNotEqual("CERTIFIED_STOP", fields["system_status"])
        self.assertNotIn("level_certificate", fields)

    def test_e2e_can_evaluate_without_admit_and_cannot_name_unexecuted_rows(self):
        firewall_only = DeterministicKernelE2EDriver().run(
            twin_request(
                observation_admission=twin_observation_admission_config()
            )
        )

        self.assertEqual(2, len(firewall_only.observation_claims))
        self.assertTrue(
            all(decision.allowed for decision in firewall_only.firewall_decisions)
        )
        self.assertEqual((), firewall_only.admission_transitions)
        self.assertEqual("CONTINUE", firewall_only.system_state.system_status.value)
        self.assertIsNone(firewall_only.system_state.certificate_id)

        with self.assertRaises(ValueError):
            DeterministicKernelE2EDriver().run(
                twin_request(
                    observation_admission=twin_observation_admission_config(
                        admit_observation_ids=("OBS-003",)
                    )
                )
            )

    def test_default_p10_path_remains_firewall_free(self):
        result = DeterministicKernelE2EDriver().run(twin_request())

        self.assertEqual((), result.observation_claims)
        self.assertEqual((), result.firewall_decisions)
        self.assertEqual((), result.admission_transitions)
        self.assertEqual("CONTINUE", result.system_state.system_status.value)


if __name__ == "__main__":
    unittest.main()
