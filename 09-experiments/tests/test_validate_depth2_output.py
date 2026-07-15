import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
SCRIPT = EXP / "scripts" / "validate_depth2_output.py"
OUTPUT = EXP / "results" / "depth2_endpoint_c07_c12_v0.3"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidateDepth2OutputTests(unittest.TestCase):
    def test_formal_c07_c12_output_passes_with_declared_boundary(self):
        validator = load(SCRIPT, "validate_depth2_output")
        report = validator.validate(OUTPUT)
        self.assertEqual("passed_with_runtime_allowlist", report["validation_status"])
        self.assertEqual(6, report["independent_case_count"])
        self.assertEqual(270, report["repeated_condition_count"])
        self.assertEqual(810, report["row_count"])
        self.assertTrue(report["output_sha256_verified"])
        self.assertTrue(report["unique_pair_keys_verified"])
        self.assertTrue(report["execution_profile_held_constant"])
        self.assertTrue(report["runtime_allowlist_enforced"])
        self.assertTrue(report["hidden_outcome_invariance_tested"])
        self.assertFalse(report["paper_or_patent_updated"])

    def test_prior_and_uniform_runtime_allowlist_outputs_pass(self):
        validator = load(SCRIPT, "validate_depth2_output_extensions")
        for name in (
            "depth2_endpoint_c07_c12_prior_x0.75_v0.3",
            "depth2_endpoint_c07_c12_prior_x1.25_v0.3",
            "depth2_endpoint_c07_c12_uniform_v0.3",
        ):
            with self.subTest(name=name):
                report = validator.validate(EXP / "results" / name)
                self.assertEqual("passed_with_runtime_allowlist", report["validation_status"])
                self.assertEqual(810, report["row_count"])
                self.assertTrue(report["runtime_allowlist_enforced"])


if __name__ == "__main__":
    unittest.main()
