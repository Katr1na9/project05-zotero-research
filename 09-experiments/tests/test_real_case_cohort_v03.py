import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
SCRIPTS = EXP / "scripts"
COHORT = EXP / "governance" / "cohorts" / "real-case-cohort-v0.3.json"


def load_script(name):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_script("build_real_case_cohort_v03")
VALIDATOR = load_script("validate_real_case_cohort_v03")


class RealCaseCohortV03Tests(unittest.TestCase):
    def test_real_cases_are_aliased_to_c01_c09_without_source_renames(self):
        cohort = BUILDER.build_cohort()

        self.assertEqual(
            [f"C{number:02d}" for number in range(1, 10)],
            [row["canonical_case_id"] for row in cohort["cases"]],
        )
        self.assertTrue(cohort["cases"][0]["source_case_id"].startswith("C04-"))
        self.assertTrue(cohort["cases"][-1]["source_case_id"].startswith("C12-"))
        self.assertEqual(
            "canonical_alias_only_preserve_source_ids_paths_and_files",
            cohort["renaming_policy"],
        )

    def test_hash_schemes_separate_raw_replay_from_repository_text_identity(self):
        cohort = BUILDER.build_cohort()

        self.assertIn("repository_text_hash_scheme", cohort)
        self.assertIn("replay_artifact_hash_scheme", cohort)
        self.assertEqual(
            "utf8_lf_normalized_sha256", cohort["repository_text_hash_scheme"]
        )
        self.assertEqual("raw_bytes_sha256", cohort["replay_artifact_hash_scheme"])

    def test_toy_cases_are_excluded_from_formal_and_paper_results(self):
        cohort = BUILDER.build_cohort()

        self.assertEqual(3, len(cohort["toy_exclusions"]))
        self.assertTrue(
            all(not row["formal_experiment_included"] for row in cohort["toy_exclusions"])
        )
        self.assertTrue(
            all(not row["paper_result_included"] for row in cohort["toy_exclusions"])
        )
        self.assertEqual(
            {"toy_unit_and_interface_tests_only"},
            {row["permitted_use"] for row in cohort["toy_exclusions"]},
        )

    def test_generated_frozen_cohort_replays_all_aliases_and_digest_sources(self):
        report = VALIDATOR.validate_cohort(COHORT)

        self.assertTrue(report["schema_valid"])
        self.assertTrue(report["source_alias_valid"])
        self.assertTrue(report["formal_ready"])
        self.assertEqual(9, report["canonical_case_count"])
        self.assertEqual(3, report["calibration_case_count"])
        self.assertEqual(6, report["development_case_count"])
        self.assertEqual(12, report["declared_replay_artifact_count"])
        self.assertFalse(report["artifact_byte_verification_requested"])
        self.assertEqual([], report["errors"])

    def test_tampered_source_alias_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cohort.json"
            cohort = BUILDER.build_cohort()
            cohort["cases"][0]["source_case_config_sha256"] = "0" * 64
            path.write_text(json.dumps(cohort), encoding="utf-8")

            report = VALIDATOR.validate_cohort(path)

            self.assertFalse(report["source_alias_valid"])
            self.assertTrue(
                any("source case config hash mismatch" in error for error in report["errors"])
            )

    def test_dataset_relative_and_repo_relative_output_paths_are_explicit(self):
        dataset_root = EXP / "real_data" / "darpa_tc_e5"

        self.assertEqual(
            dataset_root / "extracted" / "R05_event_table.tsv",
            BUILDER.resolve_dataset_output(dataset_root, "extracted/R05_event_table.tsv"),
        )
        self.assertEqual(
            EXP / "real_data" / "darpa_tc_e5" / "extracted" / "R04_event_table.tsv",
            BUILDER.resolve_dataset_output(
                dataset_root,
                "09-experiments/real_data/darpa_tc_e5/extracted/R04_event_table.tsv",
            ),
        )


if __name__ == "__main__":
    unittest.main()
