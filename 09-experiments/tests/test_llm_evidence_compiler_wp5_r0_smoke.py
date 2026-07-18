import importlib.util
import json
import os
import tempfile
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


smoke = load_script("run_ctinexus_r0_smoke")


class CTINexusR0SmokeTests(unittest.TestCase):
    def test_environment_sanitizer_removes_all_provider_credentials(self):
        source = {
            "PATH": "fixture",
            "OPENAI_API_KEY": "secret",
            "GEMINI_API_KEY": "secret",
            "AWS_ACCESS_KEY_ID": "secret",
            "OLLAMA_BASE_URL": "http://example.test",
            "CUSTOM_BASE_URL": "http://example.test",
        }
        with tempfile.TemporaryDirectory() as directory:
            result = smoke.sanitized_environment(source, Path(directory))
        self.assertEqual("fixture", result["PATH"])
        self.assertNotIn("OPENAI_API_KEY", result)
        self.assertNotIn("GEMINI_API_KEY", result)
        self.assertNotIn("AWS_ACCESS_KEY_ID", result)
        self.assertNotIn("OLLAMA_BASE_URL", result)
        self.assertEqual("1", result["PYTHONNOUSERSITE"])
        self.assertEqual("1", result["PYTHON_DOTENV_DISABLED"])

    def test_authoritative_smoke_loaded_no_model_data_or_provider(self):
        report_path = R0_ROOT / "r0-import-smoke-v0.1.1.json"
        if not report_path.is_file():
            self.skipTest("authoritative smoke has not been executed yet")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(
            "passed_minimal_import_only_full_runtime_not_ready", report["status"]
        )
        self.assertEqual([], report["errors"])
        self.assertEqual([], report["isolation"]["network_attempts"])
        self.assertEqual([], report["smoke"]["bundled_data_accesses"])
        self.assertEqual([], report["smoke"]["full_runtime_modules_loaded"])
        self.assertFalse(report["smoke"]["provider_credentials_detected"])
        self.assertFalse(report["smoke"]["pipeline_runtime_executed"])
        self.assertFalse(report["smoke"]["model_or_embedding_loaded"])
        self.assertFalse(report["environment"]["dependency_closure_complete"])

    def test_r0_authority_forbids_pipeline_and_model(self):
        authority = json.loads(
            (R0_ROOT / "r0-authority.json").read_text(encoding="utf-8")
        )
        self.assertFalse(authority["component_pipeline_runtime_authorized"])
        self.assertFalse(authority["model_or_embedding_download_authorized"])
        self.assertFalse(authority["external_api_authorized"])
        self.assertFalse(authority["C07_C12_execution_authorized"])
        self.assertFalse(authority["controller_integration_authorized"])


if __name__ == "__main__":
    unittest.main()
