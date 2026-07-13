import csv
import hashlib
import io
import json
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = (
    ROOT
    / "09-experiments"
    / "annotation"
    / "distribution"
    / "c07_c11_v0.2_distribution_v0.1"
)
MANIFEST_PATH = PACKAGE_DIR / "bundle_manifest.json"
LOCAL_DIR = PACKAGE_DIR / "local"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class AnnotationDistributionBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_declares_isolated_unlabeled_bundles(self):
        self.assertEqual(
            "ready_to_distribute_local",
            self.manifest["distribution_status"],
        )
        self.assertFalse(self.manifest["human_labels_present"])
        self.assertEqual(
            {"annotator_A", "annotator_B"},
            set(self.manifest["bundles"]),
        )
        self.assertTrue(
            all(not value for value in self.manifest["separation_checks"].values())
        )

    def test_local_zips_are_hash_bound_and_contain_no_answer_keys(self):
        for bundle_name, metadata in self.manifest["bundles"].items():
            path = LOCAL_DIR / metadata["filename"]
            if not path.is_file():
                self.skipTest("local-only annotation distribution ZIPs unavailable")
            with self.subTest(bundle=bundle_name):
                self.assertEqual(metadata["sha256"], sha256_file(path))
                with zipfile.ZipFile(path) as archive:
                    names = set(archive.namelist())
                    self.assertEqual(set(metadata["files"]), names)
                    self.assertEqual(
                        f"{bundle_name}\n",
                        archive.read("ANNOTATOR_ID.txt").decode("ascii"),
                    )
                    lowered = "\n".join(names).casefold()
                    self.assertNotIn("admin", lowered)
                    self.assertNotIn("agreement_results", lowered)
                    self.assertNotIn("calibration_results", lowered)
                    self.assertNotIn("recoverable_claim", lowered)
                    for public_name in (
                        "public/claim_items.jsonl",
                        "public/intent_items.jsonl",
                        "public/granularity_items.jsonl",
                        "source/claim_source_excerpts.jsonl",
                    ):
                        self.assertNotIn(
                            b'"recoverable_claim_ids"',
                            archive.read(public_name),
                        )

    def test_annotation_csvs_remain_blank_in_local_bundles(self):
        for metadata in self.manifest["bundles"].values():
            path = LOCAL_DIR / metadata["filename"]
            if not path.is_file():
                self.skipTest("local-only annotation distribution ZIPs unavailable")
            with zipfile.ZipFile(path) as archive:
                for name in (
                    "annotations/claim_annotations.csv",
                    "annotations/intent_annotations.csv",
                    "annotations/granularity_annotations.csv",
                ):
                    text = archive.read(name).decode("utf-8-sig")
                    rows = list(csv.DictReader(io.StringIO(text)))
                    for row in rows:
                        self.assertEqual("", row["reviewed"])


if __name__ == "__main__":
    unittest.main()
