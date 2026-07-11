import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments" / "scripts" / "analyze_annotation_agreement.py"


def load_module():
    spec = importlib.util.spec_from_file_location("annotation_agreement", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class AnnotationAgreementTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.exists(), "agreement analyzer is missing")
        self.module = load_module()

    def test_metric_primitives_return_one_for_identical_labels(self):
        self.assertEqual(
            self.module.quadratic_weighted_kappa(
                ["G0", "G1", "G2", "G3"],
                ["G0", "G1", "G2", "G3"],
                ["G0", "G1", "G2", "G3"],
            ),
            1.0,
        )
        self.assertEqual(
            self.module.nominal_kappa(["yes", "no"], ["yes", "no"]), 1.0
        )
        metrics = self.module.multilabel_agreement(
            [{"N1", "N2"}, set()], [{"N1", "N2"}, set()]
        )
        self.assertEqual(metrics["exact_match_rate"], 1.0)
        self.assertEqual(metrics["micro_f1"], 1.0)

    def test_blank_templates_are_reported_as_awaiting_annotations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for annotator in ("annotator_A", "annotator_B"):
                write_csv(
                    root / annotator / "claim_annotations.csv",
                    ["blind_id", "reviewed", "support_label", "source_pointer_valid"],
                    [{"blind_id": "CLM-001", "reviewed": ""}],
                )
                write_csv(
                    root / annotator / "intent_annotations.csv",
                    ["blind_id", "reviewed", "selected_node_ids_pipe"],
                    [{"blind_id": "INT-001", "reviewed": ""}],
                )
                write_csv(
                    root / annotator / "granularity_annotations.csv",
                    ["blind_id", "reviewed", "granularity_label"],
                    [{"blind_id": "GRN-001", "reviewed": ""}],
                )
            result = self.module.analyze_annotation_dir(root)
            self.assertEqual(result["status"], "awaiting_annotations")
            self.assertEqual(result["human_labels_compared"], 0)
            self.assertNotIn("weighted_kappa", str(result).casefold())

    def test_complete_annotations_produce_expected_agreement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            claim_rows = [
                {
                    "blind_id": "CLM-001",
                    "reviewed": "yes",
                    "support_label": "2_direct",
                    "source_pointer_valid": "yes",
                },
                {
                    "blind_id": "CLM-002",
                    "reviewed": "yes",
                    "support_label": "1_partial",
                    "source_pointer_valid": "no",
                },
            ]
            intent_rows = [
                {
                    "blind_id": "INT-001",
                    "reviewed": "yes",
                    "selected_node_ids_pipe": "N1|N2",
                },
                {
                    "blind_id": "INT-002",
                    "reviewed": "yes",
                    "selected_node_ids_pipe": "",
                },
            ]
            granularity_rows = [
                {
                    "blind_id": "GRN-001",
                    "reviewed": "yes",
                    "granularity_label": "G1_technique",
                },
                {
                    "blind_id": "GRN-002",
                    "reviewed": "yes",
                    "granularity_label": "G3_campaign",
                },
            ]
            for annotator in ("annotator_A", "annotator_B"):
                write_csv(root / annotator / "claim_annotations.csv", list(claim_rows[0]), claim_rows)
                write_csv(root / annotator / "intent_annotations.csv", list(intent_rows[0]), intent_rows)
                write_csv(
                    root / annotator / "granularity_annotations.csv",
                    list(granularity_rows[0]),
                    granularity_rows,
                )
            result = self.module.analyze_annotation_dir(root)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["claim_support"]["quadratic_weighted_kappa"], 1.0)
            self.assertEqual(result["public_intent"]["micro_f1"], 1.0)
            self.assertEqual(result["granularity"]["quadratic_weighted_kappa"], 1.0)

    def test_invalid_reviewed_label_is_rejected(self):
        with self.assertRaises(ValueError):
            self.module.validate_label("claim", "not-a-label")


if __name__ == "__main__":
    unittest.main()
