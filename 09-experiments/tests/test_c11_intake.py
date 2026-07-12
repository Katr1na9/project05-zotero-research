import importlib.util
import hashlib
import json
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = EXPERIMENT_DIR / "real_data" / "otrf_apt29"
MANIFEST_PATH = DATA_DIR / "manifest.json"
R08_PATH = DATA_DIR / "ground_truth" / "R08.json"
PROTOCOL_PATH = (
    EXPERIMENT_DIR.parent
    / "08-writing"
    / "c11-otrf-apt29-day1-intake-protocol-v0.1-20260712.md"
)
VALIDATOR_PATH = EXPERIMENT_DIR / "scripts" / "validate_real_manifest.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_real_manifest_c11",
    VALIDATOR_PATH,
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class C11IntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.r08 = json.loads(R08_PATH.read_text(encoding="utf-8"))

    def test_source_is_commit_pinned_and_license_recorded(self):
        self.assertEqual(
            "d9d40ef123d2c87d5d3df28c96bcab4f0faccc87",
            self.manifest["source_commit"],
        )
        self.assertEqual("MIT", self.manifest["license"]["name"])

    def test_host_and_zeek_artifacts_match_repository_metadata(self):
        sources = {
            item["source_id"]: item for item in self.manifest["sources"]
        }
        host = sources["otrf_apt29_day1_host_events"]
        zeek = sources["otrf_apt29_day1_combined_zeek"]
        self.assertEqual(13944973, host["repository_size_bytes"])
        self.assertEqual(
            "7352679a173ec0310f9d0ed587782545182dd394",
            host["repository_blob_sha1"],
        )
        self.assertEqual(1243861, zeek["repository_size_bytes"])
        self.assertEqual(
            "277c706a50a33affb4f2ee1458406cc17a6222e9",
            zeek["repository_blob_sha1"],
        )

    def test_preregistration_precedes_event_reading_and_remains_unchanged(self):
        prereg = json.loads(
            (DATA_DIR / "derived" / "R08_preregistration_record.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(prereg["event_archive_opened_before_freeze"])
        self.assertFalse(prereg["zeek_log_opened_before_freeze"])
        record = self.manifest["preinspection_record"]
        self.assertTrue(record["event_archive_opened_after_freeze"])
        self.assertTrue(record["zeek_log_opened_after_freeze"])
        root = EXPERIMENT_DIR.parent
        for frozen in prereg["frozen_files"]:
            digest = hashlib.sha256(
                (root / frozen["path"]).read_bytes()
            ).hexdigest().upper()
            self.assertEqual(frozen["sha256"], digest)
        self.assertNotIn("raw_validation", self.r08)
        self.assertNotIn("event_observations", self.r08)

    def test_structure_scan_keeps_non_overlapping_sources_separate(self):
        summary = json.loads(
            (DATA_DIR / "derived" / "R08_acquisition_summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("PASS", summary["gate_status"]["D1_source_integrity"])
        self.assertEqual(
            "PASS",
            summary["gate_status"]["D2_package_parseability"],
        )
        self.assertFalse(
            summary["structural_scan"]["host_zeek_time_overlap"]
        )
        self.assertEqual(
            {"SCRANTON": 131119, "NASHUA": 29056},
            summary["structural_scan"]["expected_host_rows"],
        )
        self.assertIn(
            "Do not merge host and Zeek",
            summary["forbidden_inference"],
        )

    def test_multiclaim_and_semantics_are_frozen(self):
        self.assertEqual("AND", self.r08["node_coverage_semantics"])
        self.assertGreaterEqual(len(self.r08["critical_nodes"]), 5)
        for node in self.r08["critical_nodes"]:
            with self.subTest(node=node["node_id"]):
                self.assertGreaterEqual(
                    len(node["required_evidence_families"]),
                    2,
                )
        self.assertEqual(
            3,
            self.r08["multiclaim_gate"][
                "minimum_critical_nodes_with_two_families"
            ],
        )

    def test_actor_label_is_not_an_attribution_endpoint(self):
        self.assertIn("not an unknown actor", self.r08["actor_label_boundary"])
        self.assertEqual("G3_campaign", self.r08["supportable_ceiling"])

    def test_manifest_cross_references_and_protocol_are_valid(self):
        self.assertEqual([], validator.validate_manifest(DATA_DIR))
        self.assertTrue(PROTOCOL_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
