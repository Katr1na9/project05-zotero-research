import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRITING = ROOT / "08-writing"
ANNOTATION = ROOT / "09-experiments" / "annotation" / "c07_c11_v0.2"
ADJUDICATION = (
    ROOT
    / "09-experiments"
    / "annotation"
    / "distribution"
    / "c07_c11_v0.2_adjudication_v0.1"
)
PAPER = WRITING / "paper-main-draft-v0.8-human-annotation-round1-20260713.md"
AUTHORITY = WRITING / "AUTHORITATIVE-DOCUMENTS-20260713.md"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def csv_count(path: Path) -> int:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


class PaperV08AnnotationConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paper = PAPER.read_text(encoding="utf-8")
        cls.authority = AUTHORITY.read_text(encoding="utf-8")
        cls.agreement = load_json(ANNOTATION / "agreement_results.json")
        cls.calibration = load_json(ANNOTATION / "calibration_results.json")
        cls.intake = load_json(ANNOTATION / "annotation_intake_manifest.json")
        cls.status = load_json(ANNOTATION / "annotation_round_status.json")
        cls.bundle = load_json(ADJUDICATION / "bundle_manifest.json")

    def test_authority_points_to_v08_package(self):
        for name in (
            PAPER.name,
            "paper-main-authoring-record-v0.8-20260713.md",
            "reviewer-response-major-revision-v0.4-20260713.md",
            "paper-main-rigor-review-v0.6-20260713.md",
            "human-annotation-round1-results-v0.1-20260713.md",
        ):
            self.assertIn(name, self.authority)
        self.assertIn("论文 v0.8 为唯一母本", self.authority)

    def test_all_round1_items_are_paired_reviewed(self):
        self.assertEqual("complete", self.agreement["status"])
        self.assertEqual(114, self.agreement["human_labels_compared"])
        self.assertEqual(27, csv_count(ANNOTATION / "annotator_A" / "claim_annotations.csv"))
        self.assertEqual(27, csv_count(ANNOTATION / "annotator_B" / "intent_annotations.csv"))
        self.assertEqual(60, csv_count(ANNOTATION / "annotator_A" / "granularity_annotations.csv"))

    def test_paper_reports_frozen_agreement_metrics(self):
        self.assertEqual(-0.1455, self.agreement["claim_support"]["quadratic_weighted_kappa"])
        self.assertEqual(0.3673, self.agreement["public_intent"]["mean_jaccard"])
        self.assertEqual(0.4878, self.agreement["public_intent"]["micro_f1"])
        for value in ("-0.1455", "0.3673", "0.4878", "114/114"):
            self.assertIn(value, self.paper)
        self.assertIn("均未达到预注册门槛", self.paper)

    def test_calibration_waits_for_32_adjudications(self):
        self.assertEqual("awaiting_adjudication", self.calibration["status"])
        self.assertEqual(7, self.calibration["task_status"]["claim"]["disagreement_items"])
        self.assertEqual(25, self.calibration["task_status"]["intent"]["disagreement_items"])
        self.assertEqual(32, self.bundle["total_disagreement_items"])
        self.assertEqual(7, self.bundle["task_manifest"]["claim"]["item_count"])
        self.assertEqual(25, self.bundle["task_manifest"]["intent"]["item_count"])

    def test_adjudication_bundle_has_no_hidden_answers(self):
        bundle_text = "\n".join(
            path.read_text(encoding="utf-8")
            for subdir in ("public", "annotations")
            for path in (ADJUDICATION / subdir).rglob("*")
            if path.is_file()
        ).casefold()
        for forbidden in (
            "recoverable_claim_ids",
            "computed_granularity",
            "annotator_a labels",
            "annotator_b labels",
            "admin_key",
        ):
            self.assertNotIn(forbidden, bundle_text)

    def test_intake_repairs_and_granularity_provenance_flag_are_frozen(self):
        self.assertEqual(12, len(self.intake["normalizations"]))
        self.assertEqual(1, len(self.intake["provenance_flags"]))
        flag = self.intake["provenance_flags"][0]
        self.assertEqual("granularity", flag["task"])
        self.assertEqual(
            "annotator_source_files_are_byte_identical",
            flag["flag"],
        )
        self.assertEqual(
            "withheld_pending_independent-completion_confirmation",
            self.status["agreement"]["granularity"]["reporting_status"],
        )
        self.assertIn("SHA-256 完全相同", self.paper)


if __name__ == "__main__":
    unittest.main()
