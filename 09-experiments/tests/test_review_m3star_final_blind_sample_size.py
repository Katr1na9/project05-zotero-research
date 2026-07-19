import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "review_m3star_final_blind_sample_size.py"
)
POWER_DESIGN = (
    REPO_ROOT
    / "09-experiments"
    / "results"
    / "m3star_final_blind_power_design_v0.1"
    / "power_design.json"
)
QUALIFICATION_AUDIT = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
    / "curator-staged-candidate-qualification-audit-v0.6.json"
)
COST_PROFILE = (
    REPO_ROOT
    / "09-experiments"
    / "governance"
    / "profiles"
    / "cost-replay-scan-equivalent-v0.1.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("sample_size_review", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SampleSizeReviewTests(unittest.TestCase):
    def test_outcome_free_review_reproduces_thresholds(self):
        module = load_module()
        review = module.build_review(
            json.loads(POWER_DESIGN.read_text(encoding="utf-8")),
            json.loads(QUALIFICATION_AUDIT.read_text(encoding="utf-8")),
            json.loads(COST_PROFILE.read_text(encoding="utf-8")),
            {"power_design": "a", "qualification_audit": "b", "cost_profile": "c"},
        )
        self.assertEqual("outcome_free_review_no_protocol_change", review["status"])
        self.assertFalse(review["threshold_authority"]["externally_mandated_case_count"])
        self.assertEqual(52, review["current_qualification_checkpoint"]["qualified_independent_case_count"])
        checks = review["independent_checks"]
        self.assertEqual(58, checks["cost_n_at_80_percent_power"])
        self.assertEqual(79, checks["cost_n_at_90_percent_power"])
        self.assertEqual(
            59,
            checks[
                "zero_success_loss_n_for_one_sided_95_percent_upper_at_most_5_percent"
            ],
        )
        self.assertEqual(59, checks["combined_n_at_80_percent_power"])
        self.assertEqual(79, checks["combined_n_at_90_percent_power"])
        current = next(
            row for row in review["fixed_n_sensitivity"]
            if row["independent_case_count"] == 52
        )
        self.assertAlmostEqual(0.7663139, current["power_at_frozen_sesoi"], places=6)
        self.assertGreater(
            current["zero_success_loss_one_sided_95_percent_upper_probability"],
            0.05,
        )
        self.assertTrue(review["current_frozen_protocol_still_controls"])
        self.assertFalse(
            review["governance_decision"]["automatic_threshold_change_authorized"]
        )

    def test_review_rejects_opened_outcomes(self):
        module = load_module()
        audit = json.loads(QUALIFICATION_AUDIT.read_text(encoding="utf-8"))
        audit["ground_truth_opened"] = True
        with self.assertRaisesRegex(ValueError, "ground_truth_opened"):
            module.build_review(
                json.loads(POWER_DESIGN.read_text(encoding="utf-8")),
                audit,
                json.loads(COST_PROFILE.read_text(encoding="utf-8")),
                {},
            )


if __name__ == "__main__":
    unittest.main()
