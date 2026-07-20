import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name):
    path = REPO_ROOT / "09-experiments" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


CONTRACT = load_script("m3star_final_blind_action_contract_v03")
VALIDATOR = load_script("validate_m3star_final_blind_case_bundle_v03")


def make_bundle(case_id="C021-final-blind"):
    contract_document, _path, contract_sha256 = CONTRACT.load_contract()
    claims = []
    nodes = []
    tactics = ["execution", "discovery", "persistence"]
    for index, tactic in enumerate(tactics, start=1):
        claim_id = f"Q{index}"
        node_id = f"N{index}"
        claims.append(
            {
                "claim_id": claim_id,
                "case_id": case_id,
                "mapped_tactic": [tactic],
                "tags": ["hideable", f"stage:{tactic}"],
                "source_pointer": {
                    "artifact_id": f"sealed-artifact-{index}",
                    "location": f"sealed-location-{index}",
                    "record_id": f"sealed-record-{index}",
                },
            }
        )
        nodes.append(
            {
                "node_id": node_id,
                "stage": tactic,
                "required_claim_ids": [claim_id],
                "critical": True,
            }
        )
    effects = {field: 0.0 for field in CONTRACT.EXPECTED_EFFECT_FIELDS}
    all_node_ids = sorted(node["node_id"] for node in nodes)
    actions = []
    bindings = {
        1: ["Q1"],
        5: ["Q2", "Q3"],
    }
    for index, slot in enumerate(
        contract_document["fixed_public_slot_templates"],
        start=1,
    ):
        actions.append(
            {
                "action_id": f"{case_id}-AA-{index:03d}",
                "case_id": case_id,
                "action_type": slot["action_type"],
                "acquisition_channel": slot["acquisition_channel"],
                "target": {
                    "target_type": "case",
                    "target_value": f"{case_id}:scope:{index:02d}",
                },
                "cost": None,
                "recoverable_claim_ids": bindings.get(index, []),
                "intended_cti_node_ids": all_node_ids,
                "expected_evidence_types": slot["expected_evidence_types"],
                "expected_effects": deepcopy(effects),
                "status": "available",
                "natural_language_request": slot["natural_language_request"],
            }
        )
    channels = sorted(
        {slot["acquisition_channel"] for slot in contract_document["fixed_public_slot_templates"]}
    )
    config = {
        "case_id": case_id,
        "development_only": False,
        "budget_total": None,
        "budget_status": "pending_sealed_measurement",
        "cost_regime_required": "measured",
        "measured_cost_profile_required": True,
        "mask_intensities": [0.2, 0.4, 0.6],
        "mask_strategies": ["random", "stage", "discriminative"],
        "random_seeds": [11, 23, 37, 41, 53],
        "fixed_action_order": [action["action_id"] for action in actions],
        "stage_mask_tags": [f"stage:{tactic}" for tactic in tactics],
        "discriminative_claim_ids": ["Q2"],
        "channel_reliability": {channel: None for channel in channels},
        "channel_reliability_status": CONTRACT.PENDING_RELIABILITY_STATUS,
        "cti_nodes": nodes,
        "cti_edges": [
            {"edge_id": "E1", "source": "N1", "target": "N2"},
            {"edge_id": "E2", "source": "N2", "target": "N3"},
        ],
        "action_construction": {
            "contract_id": CONTRACT.CONTRACT_ID,
            "contract_sha256": contract_sha256,
            "expected_effects_rule_id": CONTRACT.EXPECTED_EFFECTS_RULE_ID,
            "public_inventory_sealed_before_outcome_binding": True,
            "outcome_binding_fields": list(CONTRACT.OUTCOME_BINDING_FIELDS),
            "private_executor_map_sha256": "0" * 64,
            "planner_visible_inventory_sha256": (
                CONTRACT.planner_inventory_sha256(actions)
            ),
        },
    }
    return config, claims, actions


class CamLdsActionConstructionTests(unittest.TestCase):
    def test_public_builder_accepts_no_hidden_outcome_input(self):
        config, _claims, actions = make_bundle()
        built = CONTRACT.instantiate_public_actions(
            config["case_id"],
            [node["node_id"] for node in config["cti_nodes"]],
        )
        stripped = [
            {key: value for key, value in action.items() if key != "recoverable_claim_ids"}
            for action in actions
        ]
        self.assertEqual(stripped, built)
        self.assertTrue(all("recoverable_claim_ids" not in action for action in built))
        metadata = CONTRACT.make_construction_metadata(built, "0" * 64)
        self.assertEqual(
            CONTRACT.planner_inventory_sha256(built),
            metadata["planner_visible_inventory_sha256"],
        )

    def test_valid_fixed_inventory_passes_without_model_execution(self):
        config, claims, actions = make_bundle()
        report = CONTRACT.validate_cam_lds_action_construction(
            config,
            claims,
            actions,
        )
        self.assertEqual(8, report["positive_action_count"] + report["zero_yield_action_count"])
        self.assertEqual(6, report["zero_yield_action_count"])
        self.assertTrue(report["planner_visible_inventory_matches_prebinding_seal"])
        self.assertFalse(report["outcome_binding_changes_public_rows"])
        self.assertFalse(report["legacy_expert_prior_used"])
        self.assertFalse(report["channel_reliability_calibration_frozen"])

    def test_hidden_outcome_binding_cannot_change_public_inventory(self):
        _config, _claims, actions = make_bundle()
        public = [
            {
                key: deepcopy(value)
                for key, value in action.items()
                if key != "recoverable_claim_ids"
            }
            for action in actions
        ]
        before = CONTRACT.planner_inventory_sha256(public)
        first = {
            action["action_id"]: [f"FIRST-{index}"]
            for index, action in enumerate(public)
        }
        second = {
            action["action_id"]: []
            for action in public
        }
        self.assertEqual(before, CONTRACT.planner_inventory_sha256(CONTRACT.bind_recoverable_claims(public, first)))
        self.assertEqual(before, CONTRACT.planner_inventory_sha256(CONTRACT.bind_recoverable_claims(public, second)))

    def test_prebinding_seal_detects_public_row_mutation(self):
        config, claims, actions = make_bundle()
        actions[0]["target"]["target_value"] = "private/member/path:record-17:T1059"
        with self.assertRaisesRegex(ValueError, "frozen slot template"):
            CONTRACT.validate_cam_lds_action_construction(config, claims, actions)

    def test_nonzero_subjective_expected_effect_is_rejected(self):
        config, claims, actions = make_bundle()
        actions[0]["expected_effects"]["expected_uncertainty_reduction"] = 0.2
        config["action_construction"]["planner_visible_inventory_sha256"] = (
            CONTRACT.planner_inventory_sha256(actions)
        )
        with self.assertRaisesRegex(ValueError, "frozen slot template|neutral prior"):
            CONTRACT.validate_cam_lds_action_construction(config, claims, actions)

    def test_inventory_containing_only_successes_is_rejected(self):
        config, claims, actions = make_bundle()
        for index, action in enumerate(actions):
            action["recoverable_claim_ids"] = [f"Q{index % 3 + 1}"]
        with self.assertRaisesRegex(ValueError, "zero-yield"):
            CONTRACT.validate_cam_lds_action_construction(config, claims, actions)

    def test_intended_nodes_may_not_equal_hidden_recovered_nodes(self):
        config, claims, actions = make_bundle()
        actions[0]["recoverable_claim_ids"] = ["Q1", "Q2", "Q3"]
        with self.assertRaisesRegex(ValueError, "declared intent equals"):
            CONTRACT.validate_cam_lds_action_construction(config, claims, actions)

    def test_runtime_gate_rejects_pending_channel_calibration(self):
        config, claims, actions = make_bundle()
        with self.assertRaisesRegex(ValueError, "calibration is still pending"):
            CONTRACT.validate_cam_lds_action_construction(
                config,
                claims,
                actions,
                require_frozen_action_calibration=True,
            )

    def test_static_bundle_validator_reports_action_gate_without_payload(self):
        config, claims, actions = make_bundle()
        with tempfile.TemporaryDirectory() as temporary:
            case_dir = Path(temporary) / config["case_id"]
            case_dir.mkdir()
            for name, value in (
                ("case_config.json", config),
                ("evidence_claims.json", claims),
                ("acquisition_actions.json", actions),
            ):
                (case_dir / name).write_text(json.dumps(value), encoding="utf-8")
            report = VALIDATOR.validate_case_bundle(case_dir)
        self.assertEqual(8, report["action_count"])
        self.assertEqual(6, report["zero_yield_action_count"])
        self.assertEqual(3, report["pending_channel_reliability_count"])
        self.assertTrue(report["planner_visible_inventory_matches_prebinding_seal"])
        self.assertFalse(report["planner_or_model_executed"])
        self.assertFalse(report["one_shot_evaluation_consumed"])


if __name__ == "__main__":
    unittest.main()
