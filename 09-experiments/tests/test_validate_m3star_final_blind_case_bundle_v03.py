import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = (
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "validate_m3star_final_blind_case_bundle_v03.py"
)
SPEC = importlib.util.spec_from_file_location(
    "validate_m3star_final_blind_case_bundle_v03",
    SCRIPT_PATH,
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def valid_bundle(case_id="C013-final-blind"):
    config = {
        "case_id": case_id,
        "development_only": False,
        "budget_total": 10,
        "mask_intensities": [0.2, 0.4, 0.6],
        "mask_strategies": ["random", "stage", "discriminative"],
        "random_seeds": [11, 23, 37, 41, 53],
        "fixed_action_order": ["A1", "A2"],
        "stage_mask_tags": ["stage:initial_access", "stage:execution"],
        "discriminative_claim_ids": ["Q2"],
        "channel_reliability": {"host": 1.0, "network": 0.9},
        "cti_nodes": [
            {
                "node_id": "N1",
                "stage": "initial_access",
                "required_claim_ids": ["Q1"],
                "critical": True,
            },
            {
                "node_id": "N2",
                "stage": "execution",
                "required_claim_ids": ["Q2"],
                "critical": True,
            },
        ],
        "cti_edges": [{"edge_id": "E1", "source": "N1", "target": "N2"}],
    }
    claims = [
        {
            "claim_id": "Q1",
            "case_id": case_id,
            "mapped_tactic": ["initial_access"],
            "tags": ["hideable", "stage:initial_access"],
            "source_pointer": {
                "artifact_id": "artifact-1",
                "location": "sealed-record-1",
                "record_id": "record-1",
            },
        },
        {
            "claim_id": "Q2",
            "case_id": case_id,
            "mapped_tactic": ["execution"],
            "tags": ["hideable", "stage:execution"],
            "source_pointer": {
                "artifact_id": "artifact-1",
                "location": "sealed-record-2",
                "record_id": "record-2",
            },
        },
    ]
    base_effects = {
        "expected_granularity_gain": 1,
        "expected_uncertainty_reduction": 0.2,
        "expected_over_attribution_risk_reduction": 0.2,
        "expected_conflict_resolution": 0,
        "expected_coverage_delta": 0.5,
    }
    actions = [
        {
            "action_id": "A1",
            "case_id": case_id,
            "action_type": "query_host_subgraph",
            "acquisition_channel": "host",
            "target": {"target_type": "host", "target_value": "sealed-host"},
            "cost": 1,
            "recoverable_claim_ids": ["Q1"],
            "intended_cti_node_ids": ["N1"],
            "expected_effects": base_effects,
            "natural_language_request": "Recover the frozen host evidence.",
        },
        {
            "action_id": "A2",
            "case_id": case_id,
            "action_type": "recover_network_summary",
            "acquisition_channel": "network",
            "target": {"target_type": "capture", "target_value": "sealed-capture"},
            "cost": 2,
            "recoverable_claim_ids": ["Q2"],
            "intended_cti_node_ids": ["N2"],
            "expected_effects": base_effects,
            "natural_language_request": "Recover the frozen network evidence.",
        },
    ]
    return config, claims, actions


class FinalBlindCaseBundleValidatorTests(unittest.TestCase):
    def write_bundle(self, root, config, claims, actions):
        case_dir = root / config["case_id"]
        case_dir.mkdir()
        write_json(case_dir / "case_config.json", config)
        write_json(case_dir / "evidence_claims.json", claims)
        write_json(case_dir / "acquisition_actions.json", actions)
        return case_dir

    def test_valid_bundle_passes_without_executing_a_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            config, claims, actions = valid_bundle()
            case_dir = self.write_bundle(Path(temporary), config, claims, actions)
            report = VALIDATOR.validate_case_bundle(case_dir, config["case_id"])
        self.assertEqual("C013-final-blind", report["case_id"])
        self.assertEqual(45, report["condition_count"])
        self.assertTrue(report["reference_closure_pass"])
        self.assertTrue(report["case_contents_opened_for_structural_validation"])
        self.assertFalse(report["case_contents_returned_in_report"])
        self.assertFalse(report["planner_or_model_executed"])
        self.assertFalse(report["planner_or_model_outputs_opened"])
        self.assertFalse(report["one_shot_evaluation_consumed"])

    def test_unknown_recoverable_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            config, claims, actions = valid_bundle()
            actions[0]["recoverable_claim_ids"] = ["UNKNOWN"]
            case_dir = self.write_bundle(Path(temporary), config, claims, actions)
            with self.assertRaisesRegex(ValueError, "unknown recoverable claims"):
                VALIDATOR.validate_case_bundle(case_dir)

    def test_claim_without_any_recovery_action_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            config, claims, actions = valid_bundle()
            actions[1]["recoverable_claim_ids"] = []
            case_dir = self.write_bundle(Path(temporary), config, claims, actions)
            with self.assertRaisesRegex(ValueError, "Every evidence claim"):
                VALIDATOR.validate_case_bundle(case_dir)

    def test_condition_count_must_remain_45(self):
        with tempfile.TemporaryDirectory() as temporary:
            config, claims, actions = valid_bundle()
            config["random_seeds"] = [11, 23]
            case_dir = self.write_bundle(Path(temporary), config, claims, actions)
            with self.assertRaisesRegex(ValueError, "exactly 45"):
                VALIDATOR.validate_case_bundle(case_dir)

    def test_case_directory_must_match_case_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            config, claims, actions = valid_bundle()
            root = Path(temporary)
            case_dir = root / "different-directory"
            case_dir.mkdir()
            write_json(case_dir / "case_config.json", config)
            write_json(case_dir / "evidence_claims.json", claims)
            write_json(case_dir / "acquisition_actions.json", actions)
            with self.assertRaisesRegex(ValueError, "directory name"):
                VALIDATOR.validate_case_bundle(case_dir)


if __name__ == "__main__":
    unittest.main()
