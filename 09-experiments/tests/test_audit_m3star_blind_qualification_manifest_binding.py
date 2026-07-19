import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_SCRIPT = (
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "audit_m3star_blind_qualification_manifest_binding.py"
)
STAGED_TEST = Path(__file__).with_name(
    "test_audit_m3star_blind_staged_candidate_qualification.py"
)
AMENDMENT = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
    / "staged-acquisition-protocol-amendment-v0.2.json"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BINDING = load_module("qualification_manifest_binding", BINDING_SCRIPT)
STAGED_FIXTURE = load_module("staged_qualification_test_fixture", STAGED_TEST)


def write_json(path: Path, value):
    BINDING.write_json(path, value)


def make_files(root: Path, qualified_count: int = 79):
    amendment = BINDING.load_json(AMENDMENT)
    report = STAGED_FIXTURE.checkpoint_report(amendment, qualified_count)
    report_path = root / "qualification-report.json"
    write_json(report_path, report)
    readiness = BINDING.staged.validate_qualification_report(
        report, amendment, AMENDMENT
    )
    readiness_path = root / "qualification-readiness.json"
    write_json(readiness_path, readiness)
    case_ids = [f"C{index:03d}-blind" for index in range(13, 13 + qualified_count)]
    provenance = [
        {
            field: case[field]
            for field in BINDING.IDENTITY_HASH_FIELDS
        }
        for case in report["qualified_cases"]
    ]
    manifest = {
        "status": "frozen",
        "curation_blind_to_model_development": True,
        "ground_truth_sealed_until_execution": True,
        "all_cases_new_and_unseen": True,
        "source_and_attack_chain_deduplication_complete": True,
        "case_count": qualified_count,
        "case_ids": case_ids,
        "case_provenance": provenance,
    }
    manifest_path = root / "dataset-manifest.json"
    write_json(manifest_path, manifest)
    return report_path, readiness_path, manifest_path


class QualificationManifestBindingTests(unittest.TestCase):
    def test_exact_79_case_identity_set_binds_without_opening_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = make_files(Path(temporary))
            audit = BINDING.validate_binding(AMENDMENT, *paths)
        self.assertEqual("qualification_manifest_binding_complete", audit["status"])
        self.assertEqual(79, audit["qualified_case_count"])
        self.assertTrue(audit["identity_sets_match_exactly"])
        self.assertTrue(audit["all_qualified_cases_retained"])
        self.assertFalse(audit["telemetry_contents_opened_by_binding_audit"])

    def test_manifest_cannot_drop_a_qualified_case(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, readiness, manifest_path = make_files(Path(temporary))
            manifest = BINDING.load_json(manifest_path)
            manifest["case_ids"].pop()
            manifest["case_provenance"].pop()
            manifest["case_count"] -= 1
            write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "every qualified case"):
                BINDING.validate_binding(AMENDMENT, report, readiness, manifest_path)

    def test_manifest_cannot_substitute_a_different_capture(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, readiness, manifest_path = make_files(Path(temporary))
            manifest = BINDING.load_json(manifest_path)
            manifest["case_provenance"][0]["telemetry_capture_sha256"] = (
                STAGED_FIXTURE.digest("substituted-capture")
            )
            write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "identity set differs"):
                BINDING.validate_binding(AMENDMENT, report, readiness, manifest_path)

    def test_binding_rejects_qualification_report_with_disclosure_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            report_path, readiness, manifest = make_files(Path(temporary))
            report = BINDING.load_json(report_path)
            report["ground_truth_summary"] = "forbidden"
            write_json(report_path, report)
            with self.assertRaisesRegex(ValueError, "disclosure-safe contract"):
                BINDING.validate_binding(
                    AMENDMENT, report_path, readiness, manifest
                )


if __name__ == "__main__":
    unittest.main()
