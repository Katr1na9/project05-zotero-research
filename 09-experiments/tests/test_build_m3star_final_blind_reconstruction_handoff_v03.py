import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTAKE_DIR = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
)
REPORT_RELATIVE = Path(
    "04-progress/m3star-final-blind-data-intake-v0.1-20260719/"
    "curator-staged-candidate-qualification-report-v1.3.json"
)
REPORT = REPO_ROOT / REPORT_RELATIVE
HANDOFF = INTAKE_DIR / "final-blind-case-reconstruction-handoff-v0.3.json"
CREATED_UTC = "2026-07-20T08:10:00Z"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_module(
    "build_m3star_final_blind_reconstruction_handoff_v03_test",
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "build_m3star_final_blind_reconstruction_handoff_v03.py",
)
BINDING = load_module(
    "audit_m3star_blind_qualification_manifest_binding_v03_handoff_test",
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "audit_m3star_blind_qualification_manifest_binding_v03.py",
)


class FinalBlindReconstructionHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_frozen_handoff_rebuilds_exactly_from_qualification_report(self):
        expected = BUILDER.build_handoff(
            self.report,
            report_path=REPORT_RELATIVE,
            created_utc=CREATED_UTC,
        )
        observed = json.loads(HANDOFF.read_text(encoding="utf-8"))
        self.assertEqual(expected, observed)
        self.assertEqual(59, observed["qualified_case_count"])
        self.assertEqual("C013-final-blind", observed["final_case_id_first"])
        self.assertEqual("C071-final-blind", observed["final_case_id_last"])
        self.assertEqual(59, len(observed["case_assignments"]))
        self.assertEqual(14, observed["preferred_source_release_batch_count"])
        self.assertFalse(observed["ground_truth_opened"])
        self.assertFalse(observed["measured_cost_values_opened"])
        self.assertFalse(observed["model_outputs_opened"])
        self.assertFalse(observed["one_shot_evaluation_consumed"])

    def test_handoff_commitment_equals_frozen_binding_algorithm(self):
        rows = BINDING.identity_rows(
            self.report["qualified_cases"],
            "qualified_cases",
        )
        expected = BINDING.identity_commitment(rows)
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        self.assertEqual(
            expected,
            handoff["qualified_identity_commitment_sha256"],
        )

    def test_duplicate_identity_tuple_is_rejected(self):
        changed = copy.deepcopy(self.report)
        for field in BUILDER.IDENTITY_HASH_FIELDS:
            changed["qualified_cases"][1][field] = changed["qualified_cases"][0][
                field
            ]
        with self.assertRaisesRegex(ValueError, "identity tuples are not unique"):
            BUILDER.build_handoff(
                changed,
                report_path=REPORT_RELATIVE,
                created_utc=CREATED_UTC,
            )


if __name__ == "__main__":
    unittest.main()
