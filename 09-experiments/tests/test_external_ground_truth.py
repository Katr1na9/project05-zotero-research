import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"


def load_script(name):
    path = EXP / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


IMPORTER = load_script("import_external_ground_truth")
VALIDATOR = load_script("validate_external_ground_truth")


class ExternalGroundTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case_dirs = VALIDATOR.discover_case_dirs(EXP / "examples", EXP / "real_cases")
        cls.case_id = json.loads((cls.case_dirs[0] / "case_config.json").read_text(encoding="utf-8"))["case_id"]

    def actor_record(self):
        return {
            "record_id": "GT-A-001",
            "case_id": self.case_id,
            "ground_truth_type": "actor_attribution",
            "actor_label": "externally-confirmed-actor",
            "label_scope": "actor",
            "confidence": 0.95,
            "provenance": {
                "source_organization": "independent-provider",
                "source_document_id": "DOC-001",
                "source_document_sha256": "a" * 64,
                "external_to_project": True,
                "independent_of_case_compilation": True,
                "adjudicated_utc": "2026-07-14T08:00:00Z",
            },
        }

    def test_empty_import_keeps_actor_accuracy_and_utility_not_identifiable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = IMPORTER.import_ground_truth(
                root / "empty", root / "out", self.case_dirs, "2026-07-14T08:00:00Z"
            )
            report = json.loads((root / "out" / "external_ground_truth_validation.json").read_text(encoding="utf-8"))
            self.assertEqual("implemented", manifest["interface_status"])
            self.assertIsNone(manifest["external_actor_accuracy"])
            self.assertIn("not_identifiable", manifest["external_actor_accuracy_status"])
            self.assertIn("not_identifiable", manifest["analyst_utility_status"])
            self.assertEqual(12, report["expected_case_count"])
            self.assertFalse(manifest["all_experiments_complete"])

    def test_external_actor_record_validates_provenance_but_incomplete_coverage_stays_unidentifiable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "in" / "actor.json"
            source.parent.mkdir()
            source.write_text(json.dumps([self.actor_record()]), encoding="utf-8")
            IMPORTER.import_ground_truth(
                source.parent, root / "out", self.case_dirs, "2026-07-14T08:00:00Z"
            )
            report = json.loads((root / "out" / "external_ground_truth_validation.json").read_text(encoding="utf-8"))
            self.assertEqual("passed", report["validation_status"])
            self.assertTrue(report["provenance_valid"])
            self.assertEqual(1, report["actor_case_count"])
            self.assertIn("not_identifiable", report["external_actor_accuracy_status"])
            self.assertIsNone(report["external_actor_accuracy"])

    def test_internal_or_nonindependent_provenance_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record = self.actor_record()
            record["provenance"]["external_to_project"] = False
            source = root / "in" / "invalid.jsonl"
            source.parent.mkdir()
            source.write_text(json.dumps(record) + "\n", encoding="utf-8")
            IMPORTER.import_ground_truth(
                source.parent, root / "out", self.case_dirs, "2026-07-14T08:00:00Z"
            )
            report = json.loads((root / "out" / "external_ground_truth_validation.json").read_text(encoding="utf-8"))
            self.assertEqual("failed", report["validation_status"])
            self.assertFalse(report["schema_valid"])


if __name__ == "__main__":
    unittest.main()
