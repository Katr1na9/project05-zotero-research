import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
SCRIPT = EXP / "scripts" / "validate_afa_endpoint_output.py"
OUTPUT = EXP / "results" / "afa_endpoint_c07_c12_v0.1"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidateAfaEndpointOutputTests(unittest.TestCase):
    def test_formal_c07_c12_output_passes(self):
        validator = load(SCRIPT, "validate_afa_endpoint_output")
        report = validator.validate(OUTPUT)
        self.assertEqual("passed", report["validation_status"])
        self.assertEqual(6, report["independent_case_count"])
        self.assertEqual(270, report["repeated_condition_count"])
        self.assertEqual(1080, report["row_count"])
        self.assertTrue(report["output_sha256_verified"])
        self.assertTrue(report["unique_pair_keys_verified"])
        self.assertTrue(report["execution_profile_held_constant"])
        self.assertFalse(report["paper_or_patent_updated"])

    def test_formal_uniform_cost_output_passes(self):
        validator = load(SCRIPT, "validate_afa_endpoint_output_uniform")
        report = validator.validate(
            EXP / "results" / "afa_endpoint_c07_c12_uniform_v0.2"
        )
        self.assertEqual("passed", report["validation_status"])
        self.assertEqual(1080, report["row_count"])
        self.assertTrue(report["output_sha256_verified"])


if __name__ == "__main__":
    unittest.main()
