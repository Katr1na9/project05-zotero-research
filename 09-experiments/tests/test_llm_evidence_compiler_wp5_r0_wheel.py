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


audit = load_script("audit_ctinexus_r0_wheel")


class CTINexusR0WheelAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority = json.loads(
            (R0_ROOT / "r0-authority.json").read_text(encoding="utf-8")
        )
        cls.snapshot = json.loads(
            (R0_ROOT / "wheel-static-audit.json").read_text(encoding="utf-8")
        )
        cls.wheel = R0_ROOT / "downloads" / "ctinexus-0.2.1-py3-none-any.whl"

    def test_fixed_wheel_is_hash_and_license_verified(self):
        report = self.snapshot
        self.assertEqual("ready_for_minimal_no_model_import_smoke", report["status"])
        self.assertEqual([], report["errors"])
        self.assertTrue(report["package"]["license_verified_as_mit"])
        self.assertEqual(0, report["wheel"]["unsafe_path_count"])
        self.assertEqual(0, report["wheel"]["native_binary_count"])
        if self.wheel.is_file():
            live = audit.audit_wheel(self.wheel, self.authority)
            self.assertEqual(report["wheel"]["sha256"], live["wheel"]["sha256"])

    def test_bundled_examples_are_present_but_never_authorized_as_input(self):
        report = self.snapshot
        quarantine = report["bundled_data_quarantine"]
        self.assertGreater(quarantine["annotation_file_count"], 0)
        self.assertGreater(quarantine["demo_file_count"], 0)
        self.assertFalse(quarantine["bundled_data_authorized_as_project05_input"])
        self.assertFalse(quarantine["bundled_data_access_authorized_during_smoke"])

    def test_full_model_stack_is_declared_but_not_installed_by_r0(self):
        report = self.snapshot
        dependencies = "\n".join(report["package"]["declared_dependencies"]).casefold()
        self.assertIn("litellm", dependencies)
        self.assertIn("gradio", dependencies)
        self.assertIn("python-dotenv", dependencies)
        self.assertFalse(report["package"]["full_dependency_closure_installed"])
        self.assertFalse(report["minimal_smoke_install"]["dependency_closure_complete"])

    def test_hash_mismatch_fails_closed(self):
        if not self.wheel.is_file():
            self.skipTest("local verified wheel is intentionally not committed")
        authority = copy.deepcopy(self.authority)
        authority["component"]["wheel_sha256"] = "0" * 64
        report = audit.audit_wheel(self.wheel, authority)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("wheel_sha256_mismatch", report["errors"])


if __name__ == "__main__":
    unittest.main()
