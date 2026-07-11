import json
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = EXPERIMENT_DIR / "real_data" / "darpa_optc"
R07_PATH = DATA_DIR / "ground_truth" / "R07.json"
MANIFEST_PATH = DATA_DIR / "manifest.json"
PROTOCOL_PATH = (
    EXPERIMENT_DIR.parent
    / "08-writing"
    / "c10-optc-day3-protocol-v0.1-20260711.md"
)


class C10IntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r07 = json.loads(R07_PATH.read_text(encoding="utf-8"))
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_r07_ground_truth_is_locked_before_source_inspection(self):
        self.assertEqual("Sysclient0351.systemia.com", self.r07["target_fqdn"])
        self.assertEqual(
            {
                "start": "2019-09-25T15:20:00Z",
                "end": "2019-09-25T15:35:00Z",
            },
            self.r07["utc_window"],
        )
        self.assertEqual(
            "compiled_as_C10_event_backed_parameter_locked_test",
            self.r07["evidence_readiness"],
        )
        self.assertEqual(
            "parameter_locked_cross_day_same_corpus_fourth_case",
            self.r07["holdout_role"],
        )

    def test_manifest_points_to_the_single_required_official_file(self):
        source = next(
            item
            for item in self.manifest["sources"]
            if item["source_id"] == "optc_ecar_25sept_aia_351_375_last"
        )
        self.assertEqual(
            "1-yxi3k1Duc5Uuu_gbu1vjtdEU3FoDSIA",
            source["drive_file_id"],
        )
        self.assertEqual(
            "raw/ecar/evaluation/25Sept/AIA-351-375/"
            "AIA-351-375.ecar-last.json.gz",
            source["raw_target"],
        )
        self.assertEqual("available_local_verified", source["download_status"])
        self.assertEqual(1610345177, source["size_bytes"])
        self.assertEqual(
            "D52C3FC3439DE53123FE199374F08A7D7B2AF8E9358727BF88B2A5325A32CC75",
            source["sha256"],
        )
        self.assertEqual(
            "2019-09-25T15:20:00Z/2019-09-25T15:35:00Z",
            source["required_utc_coverage"],
        )

    def test_c10_is_not_misreported_as_an_independent_source_family(self):
        intake = self.manifest["c10_intake"]
        self.assertEqual("R07", intake["case_id"])
        self.assertIn("not a fourth independent source family", intake["warning"])
        self.assertIn("not a fourth independent source family", self.r07["notes"])
        self.assertTrue(PROTOCOL_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
