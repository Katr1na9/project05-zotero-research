import copy
import importlib.util
import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp4"
    / "generated"
    / "retrieval-v0.1"
)


def load_script(name):
    path = EXPERIMENT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = load_script("validate_compiler_cti_retrieval")


def loaded_artifacts():
    manifest = validator.load_json(RESULT_ROOT / "retrieval-manifest.json")
    origins = validator.load_json(RESULT_ROOT / "source-origin-audit.json")
    exclusion = validator.load_json(RESULT_ROOT / "payload-exclusion-audit.json")
    records = validator.load_jsonl(RESULT_ROOT / "admitted-records.jsonl")
    provenance = validator.load_json(
        RESULT_ROOT / "protected-signature-lock-provenance.json"
    )
    copied_hash = validator.sha256_file(
        RESULT_ROOT / "protected-signature-lock-v0.1.json"
    )
    return manifest, origins, exclusion, records, provenance, copied_hash


class WP4RetrievalReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = loaded_artifacts()

    def validate(self, manifest=None, origins=None, exclusion=None, records=None, provenance=None, copied_hash=None):
        base = self.artifacts
        return validator.validate_loaded(
            copy.deepcopy(base[0] if manifest is None else manifest),
            copy.deepcopy(base[1] if origins is None else origins),
            copy.deepcopy(base[2] if exclusion is None else exclusion),
            copy.deepcopy(base[3] if records is None else records),
            copy.deepcopy(base[4] if provenance is None else provenance),
            copied_lock_sha256=base[5] if copied_hash is None else copied_hash,
        )

    def test_authoritative_retrieval_passes_s2_s3_but_authorizes_no_runtime(self):
        report = validator.validate_root(RESULT_ROOT)
        self.assertEqual("passed_s2_s3_ready_for_runtime_gate_review", report["status"])
        self.assertEqual([], report["errors"])
        self.assertEqual(11197, report["counts"]["admitted_records"])
        self.assertEqual(7, report["counts"]["verified_cisa_documents"])
        self.assertTrue(all(value is False for value in report["authorization"].values()))

    def test_nonclean_exclusion_audit_fails_closed(self):
        exclusion = copy.deepcopy(self.artifacts[2])
        exclusion["status"] = "passed_with_record_exclusions"
        report = self.validate(exclusion=exclusion)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("payload_exclusion_not_clean", report["errors"])

    def test_controller_eligible_record_fails_closed(self):
        records = copy.deepcopy(self.artifacts[3])
        records[0]["controller_eligible"] = True
        report = self.validate(records=records)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("admitted_record_controller_eligible:0", report["errors"])

    def test_cisa_non_government_redirect_fails_closed(self):
        origins = copy.deepcopy(self.artifacts[1])
        origins[0]["origin_retrieval"]["final_url"] = "https://example.com/report"
        report = self.validate(origins=origins)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("cisa_final_url_not_government:0", report["errors"])

    def test_lock_hash_mismatch_fails_closed(self):
        report = self.validate(copied_hash="0" * 64)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("copied_exclusion_lock_hash_mismatch", report["errors"])

    def test_runtime_authorization_in_manifest_fails_closed(self):
        manifest = copy.deepcopy(self.artifacts[0])
        manifest["authorization"]["component_runtime"] = True
        report = self.validate(manifest=manifest)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("unauthorized_runtime_flag:component_runtime", report["errors"])


if __name__ == "__main__":
    unittest.main()
