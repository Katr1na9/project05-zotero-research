import importlib.util
import json
import unittest
from datetime import datetime
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
REAL_DATA_DIR = EXPERIMENT_DIR / "real_data" / "darpa_tc_e3"
E5_REAL_DATA_DIR = EXPERIMENT_DIR / "real_data" / "darpa_tc_e5"
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "validate_real_manifest.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_real_manifest",
    MODULE_PATH,
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class DarpaE3ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (REAL_DATA_DIR / "manifest.json").read_text(encoding="utf-8")
        )
        cls.cases = {
            case_id: json.loads(
                (REAL_DATA_DIR / "ground_truth" / f"{case_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            for case_id in ("R01", "R02", "R03")
        }

    def test_selected_sources_match_official_drive_files(self):
        sources = {
            source["source_id"]: source for source in self.manifest["sources"]
        }

        self.assertEqual(
            "1BeP80zUUmm4eZl0UuU43PsKNkl_xgskj",
            sources["fivedirections_e3_official_2_json"]["google_drive_id"],
        )
        self.assertEqual(
            "1AcWrYiBmgAqp7DizclKJYYJJBQbnDMfb",
            sources["cadets_e3_official_json"]["google_drive_id"],
        )

    def test_cases_are_development_only_with_valid_utc_windows(self):
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                self.assertTrue(case["development_only"])
                start = datetime.fromisoformat(
                    case["utc_window"]["start"].replace("Z", "+00:00")
                )
                end = datetime.fromisoformat(
                    case["utc_window"]["end"].replace("Z", "+00:00")
                )
                self.assertLess(start, end)

    def test_manifest_cross_references_are_valid(self):
        self.assertEqual(
            [],
            validator.validate_manifest(REAL_DATA_DIR),
        )

    def test_r03_is_the_frozen_cadets_april_12_holdout(self):
        case = self.cases["R03"]
        references = {
            item["case_id"]: item for item in self.manifest["cases"]
        }

        self.assertEqual(
            "cadets_e3_official_2_json",
            references["R03"]["source_id"],
        )
        self.assertEqual(
            {
                "start": "2018-04-12T17:30:00Z",
                "end": "2018-04-12T19:00:00Z",
            },
            case["utc_window"],
        )
        self.assertEqual("G3_campaign", case["supportable_ceiling"])

    def test_raw_data_paths_are_ignored(self):
        gitignore = (
            EXPERIMENT_DIR.parent / ".gitignore"
        ).read_text(encoding="utf-8")

        self.assertIn("09-experiments/real_data/darpa_tc_e3/raw/", gitignore)
        self.assertIn(
            "09-experiments/real_data/darpa_tc_e3/extracted/",
            gitignore,
        )

    def test_adapt_candidate_index_is_complete_but_not_episode_labeled(self):
        index = json.loads(
            (
                REAL_DATA_DIR
                / "derived"
                / "adapt_candidate_index.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(
            9,
            index["providers"]["5dir"]["matched_uuid_count"],
        )
        self.assertEqual(
            11,
            index["providers"]["cadets"]["matched_uuid_count"],
        )
        for provider in ("5dir", "cadets"):
            self.assertEqual(
                "unresolved_without_raw_time",
                index["providers"][provider]["episode_assignment"],
            )

    def test_pidsmaker_dump_ids_match_official_download_script(self):
        source = next(
            source
            for source in self.manifest["auxiliary_sources"]
            if source["source_id"] == "pidsmaker_e3_postgres_dumps"
        )
        datasets = {
            dataset["name"]: dataset
            for dataset in source["datasets"]
        }

        self.assertEqual(
            "1DGcGBhpavNmXTnCDd_s4NWBNh2n4-6nd",
            datasets["cadets_e3"]["google_drive_id"],
        )
        self.assertEqual(
            "17YHqUMbuNwP05iaOaifxvcQc2oC9pJbZ",
            datasets["fivedirections_e3"]["google_drive_id"],
        )
        self.assertEqual("oauth_required", source["download_status"])


class DarpaE5HoldoutManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (E5_REAL_DATA_DIR / "manifest.json").read_text(encoding="utf-8")
        )
        cls.case = json.loads(
            (E5_REAL_DATA_DIR / "ground_truth" / "R04.json").read_text(
                encoding="utf-8"
            )
        )

    def test_r04_is_a_true_e5_holdout_with_a_locked_window(self):
        self.assertFalse(self.case["development_only"])
        self.assertEqual("true_cross_engagement_holdout", self.case["holdout_role"])
        self.assertEqual(
            {
                "start": "2019-05-15T18:48:00Z",
                "end": "2019-05-15T19:07:00Z",
            },
            self.case["utc_window"],
        )
        self.assertEqual("G3_campaign", self.case["supportable_ceiling"])

    def test_r04_source_and_local_dump_are_provenance_tracked(self):
        sources = {
            source["source_id"]: source for source in self.manifest["sources"]
        }
        source = sources["theia_e5_pidsmaker_postgres_dump"]
        self.assertEqual("THEIA", source["performer"])
        self.assertEqual("available_local_verified", source["download_status"])
        self.assertEqual(6187437078, source["size_bytes"])
        self.assertEqual(
            "8072F8F767EC9CE680D359957F4D394DF171BD7EB6604393C2F50FA45BA8D303",
            source["sha256"],
        )

    def test_e5_manifest_cross_references_are_valid(self):
        self.assertEqual([], validator.validate_manifest(E5_REAL_DATA_DIR))


if __name__ == "__main__":
    unittest.main()
