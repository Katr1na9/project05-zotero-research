import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
SCRIPT = EXP / "scripts" / "audit_parameter_governance_findings.py"
SOURCE = EXP / "results" / "parameter_governance_v0.1"
CORRECTED = EXP / "results" / "parameter_governance_w6_v0.2"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ParameterGovernanceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load(SCRIPT, "parameter_governance_audit")
        cls.findings = cls.audit.build_findings(SOURCE, CORRECTED)

    def test_audit_hash_anchors_both_frozen_runs(self):
        anchors = self.findings["source_anchors"]
        self.assertEqual(64, len(anchors["parameter_governance_v0.1_manifest_sha256"]))
        self.assertEqual(64, len(anchors["corrected_w6_v0.2_manifest_sha256"]))

    def test_audit_identifies_and_corrects_w6_channel_confounding(self):
        diagnostic = self.findings["W6_channel_prior_confounding"]
        self.assertEqual(51, diagnostic["v0.1_project05_m2_losses_vs_legacy"])
        self.assertEqual(
            0,
            diagnostic[
                "v0.2_builtin_outcome_differences_channel_x0.75_vs_dev_base"
            ],
        )
        self.assertEqual(
            "planner_belief_only",
            diagnostic["v0.2_channel_prior_scope"],
        )
        self.assertTrue(diagnostic["v0.1_channel_prior_inference_invalid"])

    def test_corrected_w6_reports_case_level_effects_only(self):
        corrected = self.findings["W6_corrected_project05_m2"]
        self.assertEqual("case_or_attack_chain", corrected["analysis_unit"])
        self.assertEqual(6, corrected["independent_case_count"])
        self.assertEqual(270, corrected["repeated_condition_count"])
        self.assertEqual(3, corrected["dev_base_losses_vs_legacy"])
        self.assertEqual(3, corrected["expert_x1.25_repairs_vs_dev_base"])
        self.assertEqual(0, corrected["expert_x0.75_additional_losses_vs_dev_base"])
        self.assertEqual(["C11-otrf-apt29-day1-scranton-nashua"], corrected["cases_with_loss"])
        self.assertEqual("not_reported", corrected["inferential_statistics"])

    def test_human_and_operational_gates_remain_closed(self):
        gates = self.findings["completion_gates"]
        self.assertFalse(gates["all_experiments_complete"])
        self.assertTrue(gates["paper_or_patent_gate"].startswith("closed"))


if __name__ == "__main__":
    unittest.main()
