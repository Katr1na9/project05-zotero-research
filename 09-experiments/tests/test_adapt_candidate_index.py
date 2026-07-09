import csv
import gzip
import importlib.util
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "build_adapt_candidate_index.py"
SPEC = importlib.util.spec_from_file_location(
    "build_adapt_candidate_index",
    MODULE_PATH,
)
indexer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(indexer)


class AdaptCandidateIndexTests(unittest.TestCase):
    def test_collects_active_features_for_ground_truth_uuids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            provider_dir = Path(temp_dir)
            self.write_csv(
                provider_dir / "demo_main.csv",
                [["uuid", "label"], ["u1", "process"], ["u2", "process"]],
            )
            self.write_gzip_csv(
                provider_dir / "ProcessExec.csv.gz",
                [
                    ["Object_ID", "nginx", "sshd"],
                    ["u1", "1", "0"],
                    ["u2", "0", "1"],
                    ["benign", "1", "0"],
                ],
            )

            result = indexer.build_provider_index(
                provider_dir,
                "demo",
            )

            self.assertEqual(2, result["ground_truth_count"])
            self.assertEqual(2, result["matched_uuid_count"])
            self.assertEqual([], result["missing_uuids"])
            self.assertEqual(
                ["nginx"],
                result["processes"]["u1"]["ProcessExec"],
            )
            self.assertEqual(
                ["sshd"],
                result["processes"]["u2"]["ProcessExec"],
            )
            self.assertEqual(
                "unresolved_without_raw_time",
                result["episode_assignment"],
            )

    @staticmethod
    def write_csv(path, rows):
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerows(rows)

    @staticmethod
    def write_gzip_csv(path, rows):
        with gzip.open(
            path,
            "wt",
            encoding="utf-8",
            newline="",
        ) as handle:
            csv.writer(handle).writerows(rows)


if __name__ == "__main__":
    unittest.main()
