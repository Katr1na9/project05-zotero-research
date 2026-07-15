import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
SCRIPT = EXP / "scripts" / "audit_policy_prior_sensitivity.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PolicyPriorSensitivityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load(SCRIPT, "policy_prior_sensitivity_audit")
        cls.findings = cls.audit.build_findings()

    def test_afa_prior_sensitivity_is_paired_and_environment_fixed(self):
        afa = self.findings["AFA"]
        self.assertEqual(6, afa["independent_case_count"])
        self.assertEqual(270, afa["repeated_condition_count"])
        self.assertEqual(14, afa["x0.75"]["afa_voi_myopic"]["outcome_difference_count"])
        self.assertEqual(2, afa["x0.75"]["afa_voi_myopic"]["success_losses"])
        self.assertEqual(75, afa["x0.75"]["afa_voi_rollout_h3"]["action_sequence_changes"])
        self.assertEqual(0, afa["x1.25"]["afa_voi_myopic"]["outcome_difference_count"])
        self.assertEqual(0, afa["x0.75"]["project05_m2"]["outcome_difference_count"])
        self.assertTrue(afa["runtime_allowlist_enforced"])

    def test_depth2_detects_offsetting_success_flips(self):
        depth2 = self.findings["Depth2"]
        shifted = depth2["x0.75"]["project05_depth2_public"]
        self.assertEqual(52, shifted["outcome_difference_count"])
        self.assertEqual(1, shifted["success_losses"])
        self.assertEqual(1, shifted["success_gains"])
        self.assertEqual(269, shifted["candidate_success_count"])
        self.assertEqual(269, shifted["baseline_success_count"])
        self.assertEqual(0, depth2["x1.25"]["project05_depth2_public"]["outcome_difference_count"])
        self.assertFalse(depth2["runtime_allowlist_enforced"])
        self.assertTrue(depth2["hidden_outcome_invariance_tested"])

    def test_audit_preserves_statistical_and_writing_boundaries(self):
        boundary = self.findings["statistical_boundary"]
        self.assertEqual("case_or_attack_chain", boundary["independent_unit"])
        self.assertEqual("not_reported", boundary["inferential_statistics"])
        self.assertFalse(self.findings["all_experiments_complete"])
        self.assertTrue(self.findings["paper_or_patent_gate"].startswith("closed"))


if __name__ == "__main__":
    unittest.main()
