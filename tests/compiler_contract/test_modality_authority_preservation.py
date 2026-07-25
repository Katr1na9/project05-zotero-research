import copy
import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from compiler.llm.candidate_ir import project_candidate_claim
    from compiler.llm.exceptions import CandidateOnlyViolationError
    from compiler.llm.safety_metrics import compute_safety_metrics
    from compiler.llm.source_semantics import preserve_trusted_source_semantics
except ModuleNotFoundError:
    project_candidate_claim = None
    CandidateOnlyViolationError = ValueError
    compute_safety_metrics = None
    preserve_trusted_source_semantics = None


MODALITIES = ("observed", "derived", "reported", "hypothesized", "unknown")


def candidate(modality="reported"):
    return {
        "candidate_id": "candidate-001",
        "claim": {
            "subject": "powershell.exe",
            "predicate": "wrote",
            "object": "C:\\Temp\\archive.zip",
        },
        "modality": modality,
        "epistemic_role": "unknown",
        "truth_status": "unassessed",
        "admission_status": "candidate",
        "certification_authority": {"allowed": False, "levels": []},
        "promotion_status": "none",
        "binding_status": "unbound",
        "pointer_suggestion": {"status": "unbound"},
        "compatibility_status": "pending_kernel_schema",
    }


class ModalityAuthorityPreservationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(preserve_trusted_source_semantics)
        self.assertIsNotNone(compute_safety_metrics)

    def test_preserves_each_trusted_modality_and_source_semantics_exactly(self):
        for modality in MODALITIES:
            with self.subTest(modality=modality):
                original = candidate(modality)
                original.pop("epistemic_role")
                original.pop("truth_status")
                original_snapshot = copy.deepcopy(original)
                result = preserve_trusted_source_semantics(
                    original,
                    {
                        "modality": modality,
                        "epistemic_role": "background_intelligence",
                        "truth_status": "unassessed",
                    },
                )

                self.assertEqual(modality, result["modality"])
                self.assertEqual("background_intelligence", result["epistemic_role"])
                self.assertEqual("unassessed", result["truth_status"])
                self.assertEqual({"allowed": False, "levels": []}, result["certification_authority"])
                self.assertEqual("candidate", result["admission_status"])
                self.assertEqual(original_snapshot, original)

    def test_projection_materializes_only_trusted_role_and_truth_status(self):
        projected = project_candidate_claim(
            {
                "candidate_id": "candidate-001",
                "claim": {"subject": "a", "predicate": "saw", "object": "b"},
            },
            {
                "modality": "reported",
                "epistemic_role": "background_intelligence",
                "truth_status": "unassessed",
            },
        )

        self.assertEqual("reported", projected["modality"])
        self.assertEqual("background_intelligence", projected["epistemic_role"])
        self.assertEqual("unassessed", projected["truth_status"])

    def test_rejects_a_semantic_value_that_disagrees_with_trusted_metadata(self):
        original = candidate("observed")

        with self.assertRaisesRegex(CandidateOnlyViolationError, "modality"):
            preserve_trusted_source_semantics(
                original,
                {
                    "modality": "reported",
                    "epistemic_role": "unknown",
                    "truth_status": "unassessed",
                },
            )

    def test_model_cannot_promote_reported_or_hypothesized_to_observed(self):
        for trusted_modality in ("reported", "hypothesized"):
            with self.subTest(trusted_modality=trusted_modality):
                with self.assertRaisesRegex(CandidateOnlyViolationError, "modality"):
                    project_candidate_claim(
                        {
                            "candidate_id": "candidate-001",
                            "claim": {"subject": "a", "predicate": "saw", "object": "b"},
                            "modality": "observed",
                        },
                        {"modality": trusted_modality},
                    )

    def test_model_cannot_select_epistemic_role_truth_or_case_evidence(self):
        for field, value in (
            ("epistemic_role", "case_evidence"),
            ("truth_status", "supported"),
            ("case_evidence", True),
        ):
            with self.subTest(field=field):
                proposal = {
                    "candidate_id": "candidate-001",
                    "claim": {"subject": "a", "predicate": "saw", "object": "b"},
                    field: value,
                }
                with self.assertRaises(CandidateOnlyViolationError):
                    project_candidate_claim(proposal, {"modality": "reported"})

    def test_semantics_layer_rejects_existing_authority_or_case_admission(self):
        unsafe = candidate("reported")
        unsafe["certification_authority"] = {"allowed": True, "levels": ["case"]}
        unsafe["admission_status"] = "admitted"

        with self.assertRaisesRegex(CandidateOnlyViolationError, "candidate-only"):
            preserve_trusted_source_semantics(
                unsafe,
                {
                    "modality": "reported",
                    "epistemic_role": "case_evidence",
                    "truth_status": "supported",
                },
            )

    def test_metrics_detect_authority_and_modality_leakage(self):
        safe = candidate("reported")
        authority_leak = candidate("reported")
        authority_leak["certification_authority"] = {"allowed": True, "levels": ["case"]}
        modality_leak = candidate("observed")

        metrics = compute_safety_metrics(
            (safe, authority_leak, modality_leak),
            ("reported", "reported", "reported"),
        )

        self.assertEqual(1 / 3, metrics.authority_leakage_rate)
        self.assertEqual(1 / 3, metrics.modality_leakage_rate)
        self.assertFalse(metrics.hard_safety_pass)

    def test_zero_denominators_are_zero_rates_but_not_a_vacuous_hard_pass(self):
        metrics = compute_safety_metrics((), ())

        self.assertEqual(0.0, metrics.authority_leakage_rate)
        self.assertEqual(0.0, metrics.modality_leakage_rate)
        self.assertEqual(0, metrics.evaluated_candidates)
        self.assertFalse(metrics.hard_safety_pass)

    def test_nonempty_zero_leakage_panel_is_a_hard_pass(self):
        metrics = compute_safety_metrics((candidate("derived"),), ("derived",))

        self.assertEqual(0.0, metrics.authority_leakage_rate)
        self.assertEqual(0.0, metrics.modality_leakage_rate)
        self.assertTrue(metrics.hard_safety_pass)

    def test_metrics_require_one_trusted_modality_per_candidate(self):
        with self.assertRaisesRegex(ValueError, "same length"):
            compute_safety_metrics((candidate(),), ())


if __name__ == "__main__":
    unittest.main()
