import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "design_m3star_final_blind_power.py"
)


def load_design(testcase: unittest.TestCase):
    testcase.assertTrue(SCRIPT.is_file())
    spec = importlib.util.spec_from_file_location(
        "design_m3star_final_blind_power",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FinalBlindPowerDesignTests(unittest.TestCase):
    def test_exact_noncentral_t_sample_sizes_match_frozen_sensitivity(self):
        design = load_design(self)
        self.assertEqual(
            36,
            design.required_paired_t_n(0.05, 0.10, 0.05, 0.90)[
                "complete_independent_case_count"
            ],
        )
        self.assertEqual(
            79,
            design.required_paired_t_n(0.05, 0.15, 0.05, 0.90)[
                "complete_independent_case_count"
            ],
        )

    def test_invalid_case_reserve_rounds_up(self):
        design = load_design(self)
        self.assertEqual(93, design.recruit_count(79, 0.15))

    def test_zero_loss_bound_is_below_five_percent_at_complete_n(self):
        design = load_design(self)
        upper = design.zero_event_upper_bound(79)
        self.assertLess(upper, 0.05)
        self.assertGreater(upper, 0.03)


if __name__ == "__main__":
    unittest.main()
