import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments" / "scripts" / "run_m2_sensitivity.py"
MVP_PATH = ROOT / "09-experiments" / "scripts" / "run_mvp.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MVP = load(MVP_PATH, "run_mvp_for_sensitivity_tests")


def state():
    return {
        "coverage": {
            "stage_coverage": {"s1": 0.0},
            "evidence_type_coverage": {"host": 0.0},
        },
        "budget": {"budget_remaining": 4.0},
        "actions_taken": [],
        "action_feedback": [],
    }


def action():
    return {
        "action_id": "A",
        "action_type": "query",
        "cost": 2.0,
        "expected_stages": ["s1"],
        "expected_evidence_types": ["host"],
        "expected_effects": {
            "expected_granularity_gain": 0.8,
            "expected_uncertainty_reduction": 0.3,
            "expected_over_attribution_risk_reduction": 0.2,
        },
        "target": {"target_type": "node", "target_value": "N1"},
    }


class M2SensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load(SCRIPT, "run_m2_sensitivity") if SCRIPT.exists() else None

    def require_module(self):
        if self.module is None:
            self.skipTest("M2 sensitivity implementation does not exist yet")
        return self.module

    def test_module_exists(self):
        self.assertTrue(SCRIPT.exists(), "M2 sensitivity runner has not been implemented")

    def test_base_weight_score_exactly_matches_frozen_m2(self):
        module = self.require_module()
        candidate = action()
        actions = [candidate]
        expected = MVP.m2_action_score(candidate, state(), actions)
        actual = module.weighted_m2_action_score(
            candidate, state(), actions, module.BASE_WEIGHTS
        )
        self.assertAlmostEqual(actual, expected, places=12)

    def test_weight_variants_are_one_at_a_time_and_include_base(self):
        module = self.require_module()
        variants = module.weight_variants()
        self.assertEqual(len(variants), 17)
        self.assertIn("m2_base", variants)
        for name, weights in variants.items():
            changed = [key for key in module.BASE_WEIGHTS if weights[key] != module.BASE_WEIGHTS[key]]
            if name == "m2_base":
                self.assertEqual(changed, [])
            else:
                self.assertEqual(len(changed), 1)

    def test_threshold_variants_match_preregistered_values(self):
        module = self.require_module()
        variants = module.THRESHOLD_VARIANTS
        self.assertEqual(set(variants), {"lenient", "default", "conservative"})
        self.assertLess(
            variants["lenient"]["g3_node_coverage"],
            variants["default"]["g3_node_coverage"],
        )
        self.assertGreater(
            variants["conservative"]["g3_node_coverage"],
            variants["default"]["g3_node_coverage"],
        )


if __name__ == "__main__":
    unittest.main()
