import copy
import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
ADAPTER_PATH = EXP / "scripts" / "afa_endpoint_adapter.py"
RUNNER_PATH = EXP / "scripts" / "run_afa_voi_baselines.py"
CONTRACT_PATH = (
    EXP / "governance" / "contracts" / "afa-endpoint-contract-v0.1.json"
)
SCHEMA_PATH = EXP / "data_schema" / "afa_endpoint_contract.schema.json"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ADAPTER = load(ADAPTER_PATH, "afa_endpoint_adapter_tests")
RUNNER = load(RUNNER_PATH, "afa_endpoint_runner_tests")


def config():
    return {
        "case_id": "toy-endpoint",
        "description": "hidden narrative",
        "budget_total": 3,
        "target_granularity": "G3_campaign",
        "support_ceiling": "G3_campaign",
        "granularity_order": [
            "G0_unknown",
            "G1_technique",
            "G2_tactic_intent",
            "G3_campaign",
        ],
        "granularity_thresholds": {
            "g3_node_coverage": 0.5,
            "g3_edge_coverage": 0.5,
            "g2_node_coverage": 0.45,
            "g2_min_stages": 2,
            "g1_node_coverage": 0.15,
            "hidden_threshold_answer": 99,
        },
        "cti_nodes": [
            {
                "node_id": "N1",
                "stage": "s1",
                "critical": True,
                "required_claim_ids": ["secret-1"],
            },
            {
                "node_id": "N2",
                "stage": "s2",
                "critical": True,
                "required_claim_ids": ["secret-2"],
            },
        ],
        "cti_edges": [
            {
                "edge_id": "E1",
                "source": "N1",
                "target": "N2",
                "required_claim_ids": ["secret-edge"],
            }
        ],
        "channel_reliability": {"host": 0.8},
        "mask_strategy": "discriminative",
        "mask_intensity": 0.5,
        "random_seed": 99,
        "discriminative_claim_ids": ["secret-1"],
        "target_case_outcome_prior": {"winner": "A"},
    }


def state():
    return {
        "case_id": "toy-endpoint",
        "run_id": "secret-run",
        "step_index": 0,
        "mask_strategy": "discriminative",
        "mask_intensity": 0.5,
        "random_seed": 99,
        "visible_claim_ids": ["visible-1"],
        "hidden_claim_ids": ["secret-1"],
        "recovered_claim_ids": [],
        "matched_cti_node_ids": [],
        "unmatched_cti_node_ids": ["N1", "N2"],
        "matched_cti_edge_ids": [],
        "unmatched_cti_edge_ids": ["E1"],
        "coverage": {"cti_node_coverage": 0.0},
        "discriminability": {"candidate_entropy": 1.0},
        "supportable_granularity": "G0_unknown",
        "budget": {"budget_total": 3, "budget_used": 0, "budget_remaining": 3},
        "actions_taken": [],
        "action_feedback": [
            {
                "action_id": "old",
                "action_type": "query",
                "recovered_count": 0,
                "channel_up": 0,
                "recovered_claim_ids": ["secret-1"],
            }
        ],
        "remaining_action_ids": ["A", "STOP"],
        "candidate_hypotheses": [
            {"label": "secret actor", "supporting_claim_ids": ["secret-1"]}
        ],
    }


def actions():
    return [
        {
            "action_id": "A",
            "case_id": "toy-endpoint",
            "action_type": "query",
            "acquisition_channel": "host",
            "target": {
                "target_type": "node",
                "target_value": "N1",
                "hidden_target_answer": "secret-1",
            },
            "cost": 1.0,
            "intended_cti_node_ids": ["N1"],
            "recoverable_claim_ids": ["secret-1"],
            "expected_evidence_types": ["host"],
            "expected_stages": ["s1"],
            "expected_effects": {"expected_granularity_gain": 999},
            "target_case_outcome_prior": 1.0,
            "status": "available",
            "natural_language_request": "query N1",
            "notes": "hidden implementation note",
        },
        {
            "action_id": "STOP",
            "case_id": "toy-endpoint",
            "action_type": "stop",
            "acquisition_channel": "decision",
            "target": {"target_type": "case", "target_value": "toy-endpoint"},
            "cost": 0.0,
            "intended_cti_node_ids": [],
            "recoverable_claim_ids": [],
            "expected_evidence_types": [],
            "expected_stages": [],
            "expected_effects": {},
            "status": "available",
            "natural_language_request": "stop",
        },
    ]


class AfaEndpointContractTests(unittest.TestCase):
    def test_contract_validates_and_distinguishes_missingness(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual([], list(validator.iter_errors(contract)))
        native = contract["missingness"]["native_missing"]
        masked = contract["missingness"]["experimentally_masked"]
        self.assertFalse(native["represented_as_hidden_claim_ids"])
        self.assertFalse(native["eligible_for_simulated_recovery"])
        self.assertTrue(masked["represented_as_hidden_claim_ids"])
        self.assertTrue(masked["eligible_for_simulated_recovery"])
        self.assertFalse(native["planner_membership_visible"])
        self.assertFalse(masked["planner_membership_visible"])

    def test_runtime_view_removes_outcomes_masks_and_node_answer_keys(self):
        view = ADAPTER.build_endpoint_view(config(), state(), actions())
        forbidden = set(
            view_contract()["planner_visibility"]["recursive_forbidden_keys"]
        )
        self.assertEqual([], ADAPTER.recursive_key_hits(view, forbidden))
        self.assertEqual(
            set(view["config"]["cti_nodes"][0]),
            {"node_id", "stage", "critical"},
        )
        self.assertNotIn("hidden_threshold_answer", view["config"]["granularity_thresholds"])
        self.assertNotIn("target_granularity", view["config"])
        self.assertNotIn("candidate_hypotheses", view["state"])
        self.assertEqual(
            view["state"]["action_feedback"],
            [{"action_id": "old", "action_type": "query", "recovered_count": 0}],
        )
        action = next(row for row in view["actions"] if row["action_id"] == "A")
        self.assertNotIn("recoverable_claim_ids", action)
        self.assertNotIn("expected_effects", action)
        self.assertNotIn("notes", action)
        self.assertEqual(
            action["target"], {"target_type": "node", "target_value": "N1"}
        )

    def test_profile_hashes_ignore_hidden_outcomes_but_track_visible_cost_and_prior(self):
        baseline = ADAPTER.build_endpoint_view(config(), state(), actions())[
            "profile_identity"
        ]
        hidden_changed_config = copy.deepcopy(config())
        hidden_changed_actions = copy.deepcopy(actions())
        hidden_changed_config["target_case_outcome_prior"] = {"winner": "B"}
        hidden_changed_actions[0]["recoverable_claim_ids"] = ["other-secret"]
        hidden_changed_actions[0]["expected_effects"] = {
            "expected_granularity_gain": -999
        }
        hidden_changed = ADAPTER.build_endpoint_view(
            hidden_changed_config, state(), hidden_changed_actions
        )["profile_identity"]
        self.assertEqual(baseline, hidden_changed)

        changed_cost_actions = copy.deepcopy(actions())
        changed_cost_actions[0]["cost"] = 2.0
        changed_cost = ADAPTER.build_endpoint_view(
            config(), state(), changed_cost_actions
        )["profile_identity"]
        self.assertNotEqual(
            baseline["cost"]["sha256"], changed_cost["cost"]["sha256"]
        )
        self.assertEqual(
            baseline["prior"]["sha256"], changed_cost["prior"]["sha256"]
        )

        changed_prior_config = copy.deepcopy(config())
        changed_prior_config["channel_reliability"]["host"] = 0.2
        changed_prior = ADAPTER.build_endpoint_view(
            changed_prior_config, state(), actions()
        )["profile_identity"]
        self.assertNotEqual(
            baseline["prior"]["sha256"], changed_prior["prior"]["sha256"]
        )

    def test_target_case_outcome_derived_profile_provenance_is_rejected(self):
        view = ADAPTER.build_endpoint_view(config(), state(), actions())
        identities = copy.deepcopy(view["profile_identity"])
        identities["prior"]["provenance"] = "target_case_outcome_derived"
        with self.assertRaisesRegex(ValueError, "not allowed"):
            ADAPTER.build_endpoint_view(
                config(), state(), actions(), profile_identity=identities
            )

    def test_stop_is_public_zero_cost_and_hidden_fields_do_not_change_selection(self):
        first = RUNNER.select_afa_voi(
            "afa_voi_myopic", config(), state(), actions()
        )
        changed_config = copy.deepcopy(config())
        changed_actions = copy.deepcopy(actions())
        changed_config["target_case_outcome_prior"] = {"force": "STOP"}
        changed_actions[0]["recoverable_claim_ids"] = []
        changed_actions[0]["expected_effects"] = {"force": -1000000}
        second = RUNNER.select_afa_voi(
            "afa_voi_myopic", changed_config, state(), changed_actions
        )
        self.assertEqual(first["action_id"], second["action_id"])

        view = ADAPTER.build_endpoint_view(config(), state(), actions())
        stop = next(row for row in view["actions"] if row["action_id"] == "STOP")
        self.assertEqual(stop["cost"], 0.0)
        self.assertEqual(stop["intended_cti_node_ids"], [])
        contract = view_contract()
        self.assertTrue(contract["stop_action"]["terminates_episode"])
        self.assertEqual(
            contract["stop_action"]["tie_break"],
            "prefer_stop_when_net_value_ties",
        )

    def test_channel_failure_feedback_hides_realized_state(self):
        contract = view_contract()
        failure = contract["channel_failure"]
        self.assertFalse(failure["realized_state_visible_before_action"])
        self.assertTrue(failure["down_channel_consumes_cost"])
        self.assertEqual(failure["down_channel_observation"], "empty_recovery")
        self.assertIn("channel_up", failure["evaluator_only_fields"])
        view = ADAPTER.build_endpoint_view(config(), state(), actions())
        self.assertNotIn(
            "channel_up", view["state"]["action_feedback"][0]
        )


def view_contract():
    return ADAPTER.load_contract(CONTRACT_PATH)["document"]


if __name__ == "__main__":
    unittest.main()
