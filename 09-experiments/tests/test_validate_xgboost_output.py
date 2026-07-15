import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
SCRIPT = EXP / "scripts" / "validate_xgboost_output.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidateXGBoostOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load(SCRIPT, "validate_xgboost_output")

    def test_runtime_allowlist_legacy_output_passes(self):
        report = self.validator.validate(EXP / "results" / "xgboost_c07_c12_v0.3")
        self.assertEqual("passed", report["validation_status"])
        self.assertEqual("legacy", report["cost_regime"])
        self.assertEqual(6, report["independent_case_count"])
        self.assertEqual(270, report["repeated_condition_count"])
        self.assertEqual(1620, report["row_count"])
        self.assertTrue(report["runtime_allowlist_enforced"])
        self.assertTrue(report["training_test_disjoint"])

    def test_runtime_allowlist_uniform_output_passes(self):
        report = self.validator.validate(
            EXP / "results" / "xgboost_c07_c12_uniform_v0.3"
        )
        self.assertEqual("passed", report["validation_status"])
        self.assertEqual("uniform", report["cost_regime"])
        self.assertEqual(1620, report["row_count"])
        self.assertTrue(report["output_sha256_verified"])


if __name__ == "__main__":
    unittest.main()
