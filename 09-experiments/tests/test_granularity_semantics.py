import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MVP_PATH = ROOT / "09-experiments" / "scripts" / "run_mvp.py"


def load_mvp():
    spec = importlib.util.spec_from_file_location("run_mvp_semantics", MVP_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MVP = load_mvp()


def config(semantics=None, thresholds=None):
    value = {
        "granularity_order": [
            "G0_unknown",
            "G1_technique",
            "G2_tactic_intent",
            "G3_campaign",
        ],
        "support_ceiling": "G3_campaign",
        "cti_nodes": [
            {
                "node_id": "N1",
                "stage": "s1",
                "critical": True,
                "required_claim_ids": ["C1", "C2"],
            },
            {
                "node_id": "N2",
                "stage": "s2",
                "critical": False,
                "required_claim_ids": ["C3"],
            },
        ],
        "cti_edges": [{"edge_id": "E1", "source": "N1", "target": "N2"}],
    }
    if semantics is not None:
        value["node_coverage_semantics"] = semantics
    if thresholds is not None:
        value["granularity_thresholds"] = thresholds
    return value


class GranularitySemanticsTests(unittest.TestCase):
    def test_default_node_coverage_remains_or(self):
        self.assertEqual(MVP.covered_node_ids(config(), {"C1"}), {"N1"})

    def test_and_coverage_requires_every_claim(self):
        cfg = config("AND")
        self.assertEqual(MVP.covered_node_ids(cfg, {"C1"}), set())
        self.assertEqual(MVP.covered_node_ids(cfg, {"C1", "C2"}), {"N1"})

    def test_recoverable_or_audit_is_independent_of_runtime_semantics(self):
        cfg = config("AND")
        self.assertEqual(MVP.or_covered_node_ids(cfg, {"C1"}), {"N1"})

    def test_configured_thresholds_change_supportable_granularity(self):
        default = MVP.supportable_granularity(config(), {"C3"})
        strict = MVP.supportable_granularity(
            config(
                thresholds={
                    "g3_node_coverage": 1.0,
                    "g3_edge_coverage": 1.0,
                    "g2_node_coverage": 0.75,
                    "g2_min_stages": 2,
                    "g1_node_coverage": 0.75,
                }
            ),
            {"C3"},
        )
        self.assertEqual(default, "G1_technique")
        self.assertEqual(strict, "G0_unknown")

    def test_unknown_semantics_is_rejected(self):
        with self.assertRaises(ValueError):
            MVP.covered_node_ids(config("MAYBE"), {"C1"})

    def test_out_of_range_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            MVP.granularity_thresholds(
                config(thresholds={"g1_node_coverage": 1.1})
            )

    def test_nonmonotonic_node_thresholds_are_rejected(self):
        with self.assertRaises(ValueError):
            MVP.granularity_thresholds(
                config(
                    thresholds={
                        "g3_node_coverage": 0.40,
                        "g2_node_coverage": 0.50,
                        "g1_node_coverage": 0.15,
                    }
                )
            )

    def test_minimum_stage_count_must_be_a_nonnegative_integer(self):
        with self.assertRaises(ValueError):
            MVP.granularity_thresholds(
                config(thresholds={"g2_min_stages": 1.5})
            )


if __name__ == "__main__":
    unittest.main()
