import hashlib
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
SCRIPT = EXP / "scripts" / "build_cost_pipeline_contract_v03.py"


spec = importlib.util.spec_from_file_location("test_build_cost_pipeline_contract_v03", SCRIPT)
BUILDER = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(BUILDER)


class CostPipelineContractV03Tests(unittest.TestCase):
    def test_contract_replaces_subjective_rubric_for_new_measurement_design(self):
        contract = BUILDER.build_contract()

        self.assertEqual(
            "v0.3_normative", contract["authority"]["new_cost_measurement_design"]
        )
        self.assertEqual(
            "legacy_exploratory_replay_only",
            contract["legacy_compatibility"]["case_embedded_scalar_cost"],
        )
        self.assertEqual(
            "suspended_not_construct_validity_evidence",
            contract["legacy_compatibility"]["EDAR_or_EVDA_R_rubric"],
        )
        self.assertEqual(
            "suspended_not_required_by_v0.3",
            contract["legacy_compatibility"]["two_rater_360_component_packet"],
        )

    def test_three_attempts_are_only_a_coverage_smoke_gate(self):
        contract = BUILDER.build_contract()

        self.assertEqual(
            "coverage_and_smoke_only",
            contract["experimental_design"]["coverage_gate"]["purpose"],
        )
        self.assertFalse(
            contract["experimental_design"]["coverage_gate"][
                "formal_statistical_claim_authorized"
            ]
        )
        self.assertEqual(
            "not_established_by_coverage_gate",
            contract["experimental_design"]["statistical_sufficiency"]["status"],
        )

    def test_current_readiness_cannot_claim_operational_cost_completion(self):
        readiness = BUILDER.build_contract()["readiness"]

        self.assertEqual(50, readiness["action_count"])
        self.assertEqual(7, readiness["adapter_count"])
        self.assertEqual(0, readiness["implemented_adapter_count"])
        self.assertEqual(0, readiness["eligible_adapter_count"])
        self.assertFalse(readiness["execution_authorized"])
        self.assertFalse(readiness["formal_measured_cost_profile_ready"])
        self.assertFalse(readiness["paper_or_patent_gate_open"])

    def test_real_only_cohort_and_schedule_are_bound_into_contract(self):
        design = BUILDER.build_contract()["experimental_design"]

        self.assertEqual(
            {
                "canonical_C01_C03": "calibration",
                "canonical_C04_C09": "development_repeat_validation",
                "canonical_C10_plus": "unassigned_and_sealed",
                "source_C13_plus": "sealed",
            },
            design["case_boundary"],
        )
        self.assertEqual(150, design["scheduled_primary_attempt_count"])

    def test_contract_artifact_hashes_replay(self):
        contract = BUILDER.build_contract()

        for entry in contract["canonical_pipeline"].values():
            path = ROOT / entry["path"]
            self.assertTrue(path.is_file(), entry["path"])
            self.assertEqual(
                entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )


if __name__ == "__main__":
    unittest.main()
