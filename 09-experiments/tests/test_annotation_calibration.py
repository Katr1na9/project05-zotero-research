import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "09-experiments"
    / "scripts"
    / "analyze_annotation_calibration.py"
)
BUILDER = (
    ROOT / "09-experiments" / "scripts" / "build_annotation_packets.py"
)
CASES_ROOT = ROOT / "09-experiments" / "real_cases"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
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


class AnnotationCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module(SCRIPT, "annotation_calibration_test")

    def test_blank_frozen_packet_waits_for_human_annotations(self):
        builder = load_module(BUILDER, "annotation_builder_for_calibration")
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            builder.build_packets(CASES_ROOT, root)
            result = self.module.analyze_calibration(root)
            self.assertEqual("awaiting_annotations", result["status"])
            self.assertEqual(0, result["calibrated_human_items"])
            self.assertNotIn("granularity", result)

    def test_disagreement_requires_adjudication_then_calibrates(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            admin = {
                "claim": {
                    "CLM-001": {"case_id": "C", "claim_id": "EC-1"}
                },
                "intent": {
                    "INT-001": {
                        "case_id": "C",
                        "action_id": "A-1",
                        "intended_cti_node_ids": ["N1", "N2"],
                        "recoverable_claim_ids": ["EC-1"],
                    }
                },
                "granularity": {
                    "GRN-001": {
                        "case_id": "C",
                        "computed_granularity": "G2_tactic_intent",
                    }
                },
            }
            (root / "admin").mkdir(parents=True)
            (root / "admin" / "admin_key.json").write_text(
                json.dumps(admin), encoding="utf-8"
            )
            claim_a = [{
                "blind_id": "CLM-001",
                "reviewed": "yes",
                "support_label": "2_direct",
                "source_pointer_valid": "yes",
            }]
            claim_b = [{
                "blind_id": "CLM-001",
                "reviewed": "yes",
                "support_label": "1_partial",
                "source_pointer_valid": "yes",
            }]
            intent = [{
                "blind_id": "INT-001",
                "reviewed": "yes",
                "selected_node_ids_pipe": "N1|N2",
            }]
            granularity = [{
                "blind_id": "GRN-001",
                "reviewed": "yes",
                "granularity_label": "G2_tactic_intent",
            }]
            for role, claim_rows in (
                ("annotator_A", claim_a),
                ("annotator_B", claim_b),
            ):
                write_csv(
                    root / role / "claim_annotations.csv",
                    list(claim_rows[0]),
                    claim_rows,
                )
                write_csv(
                    root / role / "intent_annotations.csv",
                    list(intent[0]),
                    intent,
                )
                write_csv(
                    root / role / "granularity_annotations.csv",
                    list(granularity[0]),
                    granularity,
                )
            write_csv(
                root / "adjudicator" / "claim_annotations.csv",
                list(claim_a[0]),
                [{**claim_a[0], "reviewed": ""}],
            )
            write_csv(
                root / "adjudicator" / "intent_annotations.csv",
                list(intent[0]),
                [{**intent[0], "reviewed": ""}],
            )
            write_csv(
                root / "adjudicator" / "granularity_annotations.csv",
                list(granularity[0]),
                [{**granularity[0], "reviewed": ""}],
            )

            pending = self.module.analyze_calibration(root)
            self.assertEqual("awaiting_adjudication", pending["status"])
            self.assertEqual(
                1,
                pending["task_status"]["claim"]["unresolved_disagreements"],
            )

            write_csv(
                root / "adjudicator" / "claim_annotations.csv",
                list(claim_a[0]),
                claim_a,
            )
            complete = self.module.analyze_calibration(root)
            self.assertEqual("complete", complete["status"])
            self.assertEqual(3, complete["calibrated_human_items"])
            self.assertEqual(
                1.0,
                complete["public_intent"]["micro_f1"],
            )
            self.assertEqual(
                1.0,
                complete["granularity"]["quadratic_weighted_kappa"],
            )
            self.assertNotIn("recoverable_claim_ids", json.dumps(complete))

    def test_missing_admin_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaises(FileNotFoundError):
                self.module.analyze_calibration(Path(output))


if __name__ == "__main__":
    unittest.main()
