import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "verify_m3star_blind_source_artifacts.py"
)


def load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_m3star_blind_source_artifacts", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


VERIFIER = load_verifier()


def base_catalog(relative_path: str, payload: bytes):
    return {
        "catalog_id": "curator-catalog-test",
        "status": "curator_prepared",
        "curation_team_id": "curator-independent",
        "model_development_team_id": "model-team-project05",
        "teams_are_disjoint": True,
        "curator_blind_to_model_outputs": True,
        "model_developers_blind_to_candidate_payloads": True,
        "case_credit_claimed": False,
        "artifacts": [
            {
                "source_id": "source-a",
                "artifact_id": "artifact-a",
                "relative_path": relative_path,
                "access_class": "sealed_telemetry_payload",
                "expected_size_bytes": len(payload),
                "publisher_checksum": {
                    "algorithm": "sha256",
                    "value": hashlib.sha256(payload).hexdigest(),
                },
                "opened_by_model_development": False,
                "case_credit_claimed": False,
            }
        ],
    }


class BlindSourceArtifactVerifierTests(unittest.TestCase):
    def test_valid_artifact_returns_label_free_sha256_ledger(self):
        payload = b"opaque candidate bytes\x00\x01"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source.bin").write_bytes(payload)
            report = VERIFIER.validate_catalog(
                base_catalog("source.bin", payload), root
            )

        self.assertEqual("source_artifact_hash_checks_passed", report["status"])
        self.assertEqual(1, report["artifact_count"])
        self.assertEqual(hashlib.sha256(payload).hexdigest(), report["artifacts"][0]["sha256"])
        self.assertFalse(report["file_contents_parsed"])
        self.assertFalse(report["ground_truth_opened"])
        self.assertFalse(report["case_credit_claimed"])

    def test_checksum_mismatch_is_rejected(self):
        payload = b"opaque candidate bytes"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source.bin").write_bytes(payload)
            catalog = base_catalog("source.bin", payload)
            catalog["artifacts"][0]["publisher_checksum"]["value"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "publisher checksum mismatch"):
                VERIFIER.validate_catalog(catalog, root)

    def test_relative_path_escape_is_rejected(self):
        payload = b"opaque candidate bytes"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = base_catalog("../outside.bin", payload)
            with self.assertRaisesRegex(ValueError, "must stay within artifact_root"):
                VERIFIER.validate_catalog(catalog, root)

    def test_curation_and_model_role_overlap_is_rejected(self):
        payload = b"opaque candidate bytes"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source.bin").write_bytes(payload)
            catalog = base_catalog("source.bin", payload)
            catalog["curation_team_id"] = catalog["model_development_team_id"]
            with self.assertRaisesRegex(ValueError, "must be distinct"):
                VERIFIER.validate_catalog(catalog, root)

    def test_ground_truth_custodian_artifact_is_rejected(self):
        payload = b"opaque candidate bytes"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source.bin").write_bytes(payload)
            catalog = base_catalog("source.bin", payload)
            catalog["artifacts"][0]["access_class"] = "ground_truth_custodian_only"
            with self.assertRaisesRegex(ValueError, "not available to the isolated curator"):
                VERIFIER.validate_catalog(catalog, root)


if __name__ == "__main__":
    unittest.main()
