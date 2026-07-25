import copy
import importlib.util
import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
R0_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "wp5" / "r0"


def load_script(name):
    path = EXPERIMENT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = load_script("validate_ctinexus_r0")


def load_artifacts():
    return (
        validator.load_json(R0_ROOT / "r0-authority.json"),
        validator.load_json(R0_ROOT / "wheel-static-audit.json"),
        validator.load_json(R0_ROOT / "r0-import-smoke-v0.1.1.json"),
        validator.load_json(R0_ROOT / "minimal-environment-lock-v0.1.1.json"),
        validator.load_json(R0_ROOT / "r0-dependency-resolution-observation.json"),
        (R0_ROOT / "minimal-pip-check-v0.1.1.txt").read_text(encoding="utf-8"),
    )


class CTINexusR0ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = load_artifacts()

    def validate(self, authority=None, static=None, smoke=None, lock=None, resolution=None, pip_check=None):
        base = self.artifacts
        return validator.validate_loaded(
            copy.deepcopy(base[0] if authority is None else authority),
            copy.deepcopy(base[1] if static is None else static),
            copy.deepcopy(base[2] if smoke is None else smoke),
            copy.deepcopy(base[3] if lock is None else lock),
            copy.deepcopy(base[4] if resolution is None else resolution),
            base[5] if pip_check is None else pip_check,
        )

    def test_authoritative_r0_passes_only_minimal_import_gate(self):
        report = validator.validate_root(R0_ROOT)
        self.assertEqual("passed_r0_minimal_import_full_runtime_blocked", report["status"])
        self.assertEqual([], report["errors"])
        self.assertTrue(report["component"]["minimal_import_passed"])
        self.assertFalse(report["component"]["full_runtime_ready"])
        self.assertFalse(report["environment"]["dependency_closure_complete"])
        self.assertEqual([], report["isolation"]["network_attempts"])
        self.assertTrue(all(value is False for value in report["authorization"].values()))

    def test_runtime_authority_fails_closed(self):
        authority = copy.deepcopy(self.artifacts[0])
        authority["component_pipeline_runtime_authorized"] = True
        report = self.validate(authority=authority)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn(
            "unauthorized_authority_flag:component_pipeline_runtime_authorized",
            report["errors"],
        )

    def test_network_attempt_fails_closed(self):
        smoke = copy.deepcopy(self.artifacts[2])
        smoke["isolation"]["network_attempts"] = ["fixture"]
        report = self.validate(smoke=smoke)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("network_attempt_observed", report["errors"])

    def test_bundled_demo_access_fails_closed(self):
        smoke = copy.deepcopy(self.artifacts[2])
        smoke["smoke"]["bundled_data_accesses"] = ["ctinexus/data/demo/fixture.json"]
        report = self.validate(smoke=smoke)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("bundled_data_access_observed", report["errors"])

    def test_minimal_lock_hash_change_fails_closed(self):
        lock = copy.deepcopy(self.artifacts[3])
        lock["packages"][0]["sha256"] = "0" * 64
        report = self.validate(lock=lock)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("minimal_lock_component_hash_mismatch", report["errors"])

    def test_unremoved_rust_cache_state_fails_closed(self):
        resolution = copy.deepcopy(self.artifacts[4])
        resolution["temporary_external_cache_side_effect"]["cleanup_status"] = "present"
        report = self.validate(resolution=resolution)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("temporary_rust_cache_not_cleaned", report["errors"])


if __name__ == "__main__":
    unittest.main()
