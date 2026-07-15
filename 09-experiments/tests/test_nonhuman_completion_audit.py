import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
SCRIPT = EXP / "scripts" / "build_nonhuman_completion_audit.py"
OUTPUT = EXP / "results" / "nonhuman_completion_audit_v0.1"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class NonhumanCompletionAuditTests(unittest.TestCase):
    def test_frozen_completion_manifest_is_honest_about_open_external_gates(self):
        manifest = json.loads((OUTPUT / "completion_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["automatable_implementation_complete"])
        self.assertFalse(manifest["all_experiments_complete"])
        self.assertFalse(manifest["paper_or_patent_updated"])
        self.assertEqual(0, manifest["external_evidence_gates"]["operational_measurement_records"])
        self.assertEqual(72, manifest["external_evidence_gates"]["operational_actions_missing"])
        self.assertIsNone(manifest["external_evidence_gates"]["external_actor_accuracy"])
        self.assertIn(
            "not_identifiable",
            manifest["external_evidence_gates"]["external_actor_accuracy_status"],
        )
        self.assertEqual(["main"], manifest["branch_integration"]["local_branches"])
        self.assertFalse(
            manifest["branch_integration"]["independent_feature_branches_available"]
        )

    def test_completion_builder_revalidates_all_formal_outputs(self):
        module = load(SCRIPT, "build_nonhuman_completion_audit_test")
        validations = module.collect_validations()
        self.assertEqual(15, len(validations))
        self.assertTrue(
            all(
                report["validation_status"]
                in {"passed", "passed_with_runtime_allowlist"}
                for report in validations.values()
            )
        )


if __name__ == "__main__":
    unittest.main()
