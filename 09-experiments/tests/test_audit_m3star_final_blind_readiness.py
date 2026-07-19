import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "audit_m3star_final_blind_readiness.py"
)
PROTOCOL = (
    REPO_ROOT
    / "09-experiments"
    / "governance"
    / "contracts"
    / "m3star-final-blind-protocol-v0.2.json"
)
TRAINING_COST_PROFILE = (
    REPO_ROOT
    / "09-experiments"
    / "governance"
    / "profiles"
    / "cost-replay-scan-equivalent-v0.1.json"
)
FROZEN_MODEL_RESULT = (
    REPO_ROOT
    / "09-experiments"
    / "results"
    / "m3star_measured_replay_majority_sixcase_v0.9"
)


def load_auditor(testcase: unittest.TestCase):
    testcase.assertTrue(SCRIPT.is_file())
    spec = importlib.util.spec_from_file_location(
        "audit_m3star_final_blind_readiness",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FinalBlindReadinessAuditTests(unittest.TestCase):
    def test_missing_external_inputs_block_without_opening_or_consuming(self):
        auditor = load_auditor(self)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = auditor.audit_readiness(
                PROTOCOL,
                FROZEN_MODEL_RESULT,
                TRAINING_COST_PROFILE,
                root / "missing-cases",
                root / "missing-manifest.json",
                root / "missing-cost.json",
                root / "missing-ledger.json",
            )

        self.assertTrue(report["implementation_and_protocol_static_gate_pass"])
        self.assertEqual("blocked_before_preflight", report["status"])
        self.assertFalse(report["ready_for_non_consuming_preflight"])
        self.assertFalse(report["ready_for_one_shot_execution"])
        self.assertFalse(report["c13_plus_case_contents_opened"])
        self.assertFalse(report["ground_truth_opened"])
        self.assertFalse(report["consumption_ledger_created"])
        self.assertEqual(112, report["current_public_metadata_candidate_upper_bound"])
        self.assertEqual(79, report["operational_recruitment_target"])
        self.assertEqual(95, report["maximum_staged_candidate_slots"])
        self.assertEqual(11, report["tier_a_high_confidence_candidate_upper_bound"])
        self.assertEqual(
            102,
            report["current_authoritative_artifact_verified_candidate_upper_bound"],
        )
        self.assertEqual(
            6,
            report["authoritative_artifact_verified_candidate_surplus_over_target"],
        )
        self.assertEqual(
            "qualification_checkpoint_continue_acquisition",
            report["candidate_qualification_status"],
        )
        self.assertFalse(report["candidate_qualification_gate_pass"])
        self.assertEqual(95, report["candidate_upper_bound_after_resource_amendment"])
        self.assertEqual(82, report["audited_candidate_count"])
        self.assertEqual(13, report["unaudited_reserve_count"])
        self.assertEqual(48, report["actual_qualified_case_count"])
        self.assertFalse(report["qualification_acquisition_complete"])
        self.assertIsNone(report["source_search_required_after_qualification"])
        self.assertIsNone(report["source_discovery_paused_pending_qualification"])
        self.assertFalse(report["current_protocol_count_gate_met"])
        self.assertFalse(report["protocol_count_gate_amendment_required"])
        self.assertEqual(4, len(report["blockers"]))


if __name__ == "__main__":
    unittest.main()
