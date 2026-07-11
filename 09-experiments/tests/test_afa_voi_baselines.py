import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments" / "scripts" / "run_afa_voi_baselines.py"
MVP_PATH = ROOT / "09-experiments" / "scripts" / "run_mvp.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MVP = load(MVP_PATH, "run_mvp_for_afa_tests")


def config():
    return {
        "case_id": "toy",
        "budget_total": 3,
        "channel_reliability": {"host": 1.0},
        "granularity_order": [
            "G0_unknown",
            "G1_technique",
            "G2_tactic_intent",
            "G3_campaign",
        ],
        "support_ceiling": "G3_campaign",
        "granularity_thresholds": {
            "g3_node_coverage": 0.5,
            "g3_edge_coverage": 0.5,
            "g2_node_coverage": 0.45,
            "g2_min_stages": 2,
            "g1_node_coverage": 0.15,
        },
        "cti_nodes": [
            {"node_id": "N1", "stage": "s1", "critical": True},
            {"node_id": "N2", "stage": "s2", "critical": True},
            {"node_id": "N3", "stage": "s1", "critical": False},
            {"node_id": "N4", "stage": "s2", "critical": False},
        ],
        "cti_edges": [{"edge_id": "E1", "source": "N1", "target": "N2"}],
    }


def state():
    return {
        "matched_cti_node_ids": [],
        "budget": {"budget_total": 3, "budget_used": 0, "budget_remaining": 3},
        "actions_taken": [],
        "action_feedback": [],
    }


def action(action_id, intended, recoverable, cost=1.0, channel="host"):
    return {
        "action_id": action_id,
        "action_type": "query",
        "acquisition_channel": channel,
        "cost": cost,
        "intended_cti_node_ids": intended,
        "recoverable_claim_ids": recoverable,
        "expected_effects": {},
        "expected_stages": [],
        "expected_evidence_types": [],
        "target": {"target_type": "node", "target_value": action_id},
    }


class AfaVoiBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load(SCRIPT, "run_afa_voi_baselines") if SCRIPT.exists() else None

    def require_module(self):
        if self.module is None:
            self.skipTest("AFA-VOI implementation does not exist yet")
        return self.module

    def test_module_exists(self):
        self.assertTrue(SCRIPT.exists(), "AFA-VOI baseline has not been implemented")

    def test_hidden_recovery_does_not_affect_selection(self):
        module = self.require_module()
        actions = [
            action("A", ["N3", "N4"], ["secret-a"]),
            action("B", ["N1"], ["secret-b"]),
            MVP.make_stop_action("toy"),
        ]
        changed = copy.deepcopy(actions)
        changed[0]["recoverable_claim_ids"] = []
        changed[1]["recoverable_claim_ids"] = ["different"]
        first = module.select_afa_voi("afa_voi_myopic", config(), state(), actions)
        second = module.select_afa_voi("afa_voi_myopic", config(), state(), changed)
        self.assertEqual(first["action_id"], second["action_id"])

    def test_non_greedy_rollout_can_select_complementary_plan_member(self):
        module = self.require_module()
        actions = [
            action("A", ["N3", "N4"], ["x"]),
            action("B", ["N1"], ["y"]),
            action("C", ["N2"], ["z"]),
            MVP.make_stop_action("toy"),
        ]
        myopic = module.select_afa_voi("afa_voi_myopic", config(), state(), actions)
        rollout = module.select_afa_voi("afa_voi_rollout_h3", config(), state(), actions)
        self.assertEqual(myopic["action_id"], "A")
        self.assertIn(rollout["action_id"], {"B", "C"})

    def test_stop_wins_when_no_public_value_is_available(self):
        module = self.require_module()
        actions = [action("A", [], ["hidden"], cost=1.0), MVP.make_stop_action("toy")]
        chosen = module.select_afa_voi("afa_voi_rollout_h3", config(), state(), actions)
        self.assertEqual(chosen["action_id"], MVP.STOP_ACTION_ID)

    def test_selection_does_not_mutate_inputs(self):
        module = self.require_module()
        current_state = state()
        actions = [action("A", ["N1"], ["x"]), MVP.make_stop_action("toy")]
        expected_state = copy.deepcopy(current_state)
        expected_actions = copy.deepcopy(actions)
        module.select_afa_voi("afa_voi_rollout_h3", config(), current_state, actions)
        self.assertEqual(current_state, expected_state)
        self.assertEqual(actions, expected_actions)


if __name__ == "__main__":
    unittest.main()
